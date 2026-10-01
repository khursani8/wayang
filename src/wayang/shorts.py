"""Shorts suggester: sample a long render into a brief, then cut shorts plans.

Pipeline: `wayang shorts-sample` writes <project>/shorts/brief (frames +
audio curve + meta). The analysis step is an agent session that reads the
brief and writes <project>/shorts/plan.yaml (clip windows, portrait crop
boxes, titles). `wayang shorts-render` cuts each clip with ffmpeg and
verifies the renders with real frame probes on disk, not logs. With
`--rerender` it first re-renders a portrait master through the project
vendor, then trims the windows natively (plan crop keys are ignored).
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

from wayang.render_checks import ffmpeg_frame, ffprobe_json

log = logging.getLogger("ce.shorts")

PROBE_POSITIONS = (0.1, 0.5, 0.9)


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def probe_source(video: Path) -> dict:
    if not video.is_file():
        raise SystemExit(f"shorts: video not found: {video}")
    info = ffprobe_json(video)
    stream = next(s for s in info["streams"] if s.get("codec_type") == "video")
    audio = next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)
    return {
        "path": str(video.resolve()),
        "duration": float(info["format"]["duration"]),
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "fps": stream.get("r_frame_rate", "30/1"),
        "sample_rate": int(audio["sample_rate"]) if audio else None,
    }


def audio_curve(video: Path, src: dict, bin_seconds: float) -> list:
    """RMS dB per bin in one ffmpeg pass (asetnsamples + astats).

    Digital-silence bins report -inf and are kept as -99.0 so the curve has
    one entry per bin and the analysis can see true silence.
    """
    rate = src["sample_rate"]
    if not rate:
        log.warning("audio curve skipped: source has no audio stream")
        return []
    n = max(64, int(rate * bin_seconds))
    af = (
        f"asetnsamples=n={n}:p=0,astats=metadata=1:reset=1,"
        "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-"
    )
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-af", af, "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        log.error("audio curve failed:\n%s", proc.stderr.strip()[-800:])
        raise SystemExit(1)
    curve, t = [], None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("frame:") and "pts_time:" in line:
            t = float(line.split("pts_time:")[1])
        elif "RMS_level=" in line and t is not None:
            raw = line.split("=", 1)[1].strip()
            db = -99.0 if raw in ("-inf", "nan", "") else float(raw)
            curve.append({"start": round(t, 3), "end": round(t + bin_seconds, 3), "rms_db": db})
            t = None
    return curve


def sample_brief(video: Path, brief_dir: Path, n_frames: int = 12, bin_seconds: float = 1.0,
                 pdir: Path | None = None, window: float = 5.0, stride: float = 1.0) -> dict:
    """Write <brief_dir> with frames/, audio-curve.json, meta.json.

    Resumable: existing non-empty frame jpegs are reused, json is written
    atomically at the end of each pass.
    """
    src = probe_source(video)
    brief_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = brief_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    picks = [src["duration"] * (i + 0.5) / n_frames for i in range(n_frames)]
    for i, t in enumerate(picks):
        name = f"frame-{i:04d}.jpg"
        out = frames_dir / name
        if out.is_file() and out.stat().st_size > 0:
            log.info("frame %d/%d: t=%.2fs (cached)", i + 1, n_frames, t)
            continue
        proc = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", src["path"],
             "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "4", str(out)],
            check=False,
        )
        if proc.returncode != 0 or not (out.is_file() and out.stat().st_size > 0):
            log.error("shorts-sample: frame %d (t=%.2fs) failed", i, t)
            raise SystemExit(1)
        log.info("frame %d/%d: t=%.2fs", i + 1, n_frames, t)

    curve = audio_curve(Path(src["path"]), src, bin_seconds)
    meta = {
        **src,
        "sampled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "frames": n_frames,
        "audio_bin_seconds": bin_seconds,
    }
    _atomic_write(brief_dir / "meta.json", json.dumps(meta, indent=2) + "\n")
    _atomic_write(brief_dir / "audio-curve.json", json.dumps(curve, indent=2) + "\n")
    scores: dict | None = None
    if pdir is not None:
        wins, src_label = script_windows(pdir)
        scores = window_scores(wins, curve, src["duration"], window=window, stride=stride)
        scores["script_source"] = src_label
        _atomic_write(brief_dir / "window-scores.json", json.dumps(scores, indent=2) + "\n")
    log.info(
        "brief: %s (%d frames, %d audio bins%s)",
        brief_dir, n_frames, len(curve),
        ", top window %.1f-%.1fs score %.2f" % (
            scores["windows"][0]["start"], scores["windows"][0]["end"],
            scores["windows"][0]["score"]) if scores and scores["windows"] else "",
    )
    return meta


def script_windows(pdir: Path) -> tuple[list, str]:
    """Script line windows on the source clock, for brief window scoring.

    out/timeline.json is exact when the sampled video is that project's
    render. Otherwise windows are reconstructed from the voices manifest
    (or a cps estimate) with the mapper's timing formula: approximate,
    and the brief records which source was used.
    """
    script_text: dict[int, str] = {}
    script_char: dict[int, str] = {}
    pause_after: dict[int, float] = {}
    data = None
    project_file = pdir / "project.yaml"
    if project_file.is_file():
        data = yaml.safe_load(project_file.read_text(encoding="utf-8")) or {}
    for line in (data or {}).get("script") or []:
        try:
            lid = int(line["id"])
        except (KeyError, TypeError, ValueError):
            continue
        script_text[lid] = str(line.get("text") or "")
        script_char[lid] = str(line.get("character") or "")
        try:
            pause_after[lid] = float(line.get("pause_after", 0.5))
        except (TypeError, ValueError):
            pause_after[lid] = 0.5

    tl_path = pdir / "out" / "timeline.json"
    if tl_path.is_file():
        try:
            tl = json.loads(tl_path.read_text(encoding="utf-8"))
            lines = tl.get("lines") or []
        except json.JSONDecodeError as e:
            log.warning("timeline.json unreadable (%s), falling back to estimate", e)
            lines = []
        if lines:
            return (
                [
                    {
                        "id": int(e["id"]),
                        "start": float(e["start"]),
                        "end": float(e["end"]),
                        "text": script_text.get(int(e["id"]), ""),
                    }
                    for e in lines
                    if int(e["id"]) in script_text
                ],
                "timeline.json",
            )

    settings = (data or {}).get("settings") or {}
    vendor = ((data or {}).get("vendor") or {}).get("hyperframes") or {}
    cps = float(vendor.get("estimate_cps", 7.5))
    rate = float(((settings.get("video") or {}).get("playback_rate", 1)) or 1)
    opening = 3.0 if settings.get("title_card") else 0.0
    manifest: dict = {}
    mf = pdir / "voices" / "manifest.json"
    if mf.is_file():
        try:
            manifest = (json.loads(mf.read_text(encoding="utf-8")).get("lines")) or {}
        except json.JSONDecodeError as e:
            log.warning("voices manifest unreadable (%s), scoring uses cps estimate", e)
            manifest = {}
    wins, t = [], opening
    for lid in sorted(script_text):
        nospace = script_text[lid].replace(" ", "").replace("\n", "")
        key = f"{lid:02d}_{script_char[lid]}.wav"
        if key in manifest and "seconds" in manifest[key]:
            raw = float(manifest[key]["seconds"])
            source = "manifest"
        else:
            raw = max(0.8, len(nospace) / cps)
            source = "estimate"
        dur = raw / rate
        wins.append({"id": lid, "start": round(t, 3), "end": round(t + dur, 3), "text": script_text[lid]})
        t += dur + pause_after[lid] / rate
    return wins, source


def window_scores(wins: list, curve: list, duration: float,
                  window: float = 5.0, stride: float = 1.0) -> dict:
    """Per-window highlight score: loudness peak + speech density + script
    exclamations, 0-10. The brief ranks candidate shorts windows before the
    analysis session applies judgment on boundaries and titles."""
    rows = []
    t0 = 0.0
    while t0 + window <= duration + 1e-6:
        t1 = t0 + window
        peaks = [b["rms_db"] for b in curve
                 if b["start"] >= t0 - 1e-6 and b["end"] <= t1 + 1e-6]
        peak = max(peaks) if peaks else -99.0
        density = (sum(1 for p in peaks if p > -45.0) / len(peaks)) if peaks else 0.0
        excl = 0
        lids: list = []
        for w in wins:
            if w["start"] < t1 and w["end"] > t0:
                lids.append(w["id"])
                excl += w["text"].count("!") + w["text"].count("?")
        loud = max(0.0, min(1.0, (peak + 40.0) / 20.0))
        exn = min(1.0, (excl / window) / 0.5)
        score = round(10 * (0.4 * loud + 0.3 * density + 0.3 * exn), 2)
        rows.append({
            "start": round(t0, 2), "end": round(t1, 2), "score": score,
            "loudness_peak_db": round(peak, 1), "speech_density": round(density, 2),
            "exclamations": excl, "script_line_ids": lids,
        })
        t0 += stride
    rows.sort(key=lambda r: -r["score"])
    return {
        "window_seconds": window, "stride": stride,
        "weights": {"loudness_peak": 0.4, "speech_density": 0.3, "script_exclamations": 0.3},
        "loudness_zero_db": -40.0, "speech_floor_db": -45.0,
        "script_source": None,
        "windows": rows,
    }


def _resolve_source(raw: str, plan_path: Path) -> Path:
    """Plan source paths: cwd first, then project dir, then the plan dir."""
    cands = [Path(raw), plan_path.parent.parent / raw, plan_path.parent / raw]
    for c in cands:
        if c.is_file():
            return c
    raise SystemExit(f"plan.source video not found (tried: {', '.join(str(c) for c in cands)})")


def load_plan(plan_path: Path, rerender: bool = False) -> tuple:
    """Parse + validate a shorts plan. Returns (plan, source_meta).

    A clip must carry: id, title, start, end inside the source window and
    optional render {width,height} (even). crop [x0,y0,x1,y1] inside the
    source frame and portrait is required in crop mode; rerender mode
    ignores it (windows are trimmed out of a portrait master instead).
    """
    if not plan_path.is_file():
        raise SystemExit(f"shorts plan not found: {plan_path}")
    try:
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SystemExit(f"plan parse error: {e}")
    if not isinstance(plan, dict) or not isinstance(plan.get("clips"), list) or not plan["clips"]:
        raise SystemExit("plan must be a mapping with a non-empty 'clips' list")
    if not plan.get("source"):
        raise SystemExit("plan.source (the sampled video path) missing")
    video = _resolve_source(str(plan["source"]), plan_path)
    src = probe_source(video)
    plan["source"] = src["path"]
    W, H, dur = src["width"], src["height"], src["duration"]

    for c in plan["clips"]:
        cid = str(c.get("id", "")).strip()
        if not cid:
            raise SystemExit("every clip needs a non-empty id")
        c["id"] = cid
        if not isinstance(c.get("title"), str) or not c["title"].strip():
            raise SystemExit(f"clip {cid}: title missing")
        try:
            start, end = float(c["start"]), float(c["end"])
        except (KeyError, TypeError, ValueError) as e:
            raise SystemExit(f"clip {cid}: start/end must be numbers ({e})")
        if not (0 <= start < end <= dur + 1e-6):
            raise SystemExit(f"clip {cid}: window {start}-{end}s outside source (0-{dur:.2f}s)")
        if rerender:
            if c.get("crop") is not None:
                log.debug("clip %s: crop ignored in rerender mode", cid)
        else:
            box = c.get("crop")
            if not (isinstance(box, list) and len(box) == 4):
                raise SystemExit(f"clip {cid}: crop must be [x0, y0, x1, y1]")
            try:
                x0, y0, x1, y1 = (int(v) for v in box)
            except (TypeError, ValueError) as e:
                raise SystemExit(f"clip {cid}: crop values must be numbers ({e})")
            if not (0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H):
                raise SystemExit(f"clip {cid}: crop {box} outside the {W}x{H} frame")
            if (y1 - y0) <= (x1 - x0):
                raise SystemExit(f"clip {cid}: crop {x1 - x0}x{y1 - y0} is not portrait")
        render = c.get("render") or {}
        try:
            rw, rh = int(render.get("width", 1080)), int(render.get("height", 1920))
        except (TypeError, ValueError) as e:
            raise SystemExit(f"clip {cid}: render width/height must be numbers ({e})")
        if rw <= 0 or rh <= 0 or rw % 2 or rh % 2:
            raise SystemExit(f"clip {cid}: render {rw}x{rh} must be positive even dimensions")
        if not rerender:
            c["crop"] = [x0, y0, x1, y1]
        c["render"] = {"width": rw, "height": rh}
    log.info("plan ok: %d clip(s), source %s", len(plan["clips"]), video)
    return plan, src


def render_clip(video: Path, clip: dict, out_dir: Path, force: bool = False,
                rerender: bool = False, master: str | None = None) -> dict:
    """Cut one portrait clip, then verify with ffprobe + frame probes on disk.

    Crop mode cuts the window out of a landscape master (crop -> scale).
    Rerender mode trims the window out of an already-portrait master:
    no crop filter, no scale. Skips clips that already have a passing
    verify.json for the same mode unless force=True.
    """
    mode = "rerender" if rerender else "crop"
    out_dir.mkdir(parents=True, exist_ok=True)
    mp4, verify_path = out_dir / "clip.mp4", out_dir / "verify.json"
    if not force and mp4.is_file() and verify_path.is_file():
        try:
            old = json.loads(verify_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            log.warning("clip %s: cached verify.json unreadable (%s) - re-rendering", clip["id"], e)
        else:
            if old.get("ok") and old.get("mode", "crop") == mode:
                log.info("clip %s: cached verified render (use --force to redo)", clip["id"])
                return old

    rw, rh = clip["render"]["width"], clip["render"]["height"]
    start, dur = float(clip["start"]), float(clip["end"]) - float(clip["start"])
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-i", str(video), "-t", f"{dur:.3f}"]
    if not rerender:
        x0, y0, x1, y1 = clip["crop"]
        w, h = (x1 - x0) - (x1 - x0) % 2, (y1 - y0) - (y1 - y0) % 2
        cmd += ["-vf", f"crop={w}:{h}:{x0}:{y0},scale={rw}:{rh}:flags=lanczos,setsar=1"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(mp4)]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0 or not mp4.is_file():
        log.error("clip %s: ffmpeg render failed:\n%s", clip["id"], proc.stderr.strip()[-800:])
        raise SystemExit(1)

    info = ffprobe_json(mp4)
    stream = next(s for s in info["streams"] if s.get("codec_type") == "video")
    got_w, got_h = int(stream["width"]), int(stream["height"])
    got_dur = float(info["format"]["duration"])
    verify = {
        "clip": clip["id"],
        "title": clip["title"],
        "mp4": str(mp4),
        "mode": mode,
        "expected": {"width": rw, "height": rh, "duration": round(dur, 3)},
        "got": {"width": got_w, "height": got_h, "duration": round(got_dur, 3)},
        "portrait": got_h > got_w,
        "probes": [],
    }
    ok = verify["portrait"] and (got_w, got_h) == (rw, rh) and abs(got_dur - dur) <= 0.5
    for pos in PROBE_POSITIONS:
        t = max(0.0, min(pos * dur, got_dur - 0.2))
        png = out_dir / f"probe-{int(pos * 100)}.png"
        good = ffmpeg_frame(mp4, t, got_dur, png)
        verify["probes"].append({"t": round(t, 3), "png": str(png), "ok": good})
        ok = ok and good
    if rerender:
        verify["master"] = str(master or video)
    verify["ok"] = ok
    _atomic_write(verify_path, json.dumps(verify, indent=2) + "\n")
    if not ok:
        log.error("clip %s: verification failed: %s", clip["id"], verify)
        raise SystemExit(1)
    log.info("clip %s: %dx%d %.2fs verified (%d frame probes) -> %s",
             clip["id"], got_w, got_h, got_dur, len(verify["probes"]), out_dir)
    return verify
