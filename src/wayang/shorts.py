"""Shorts suggester: sample a long render into a brief, then cut shorts plans.

Pipeline: `wayang shorts-sample` writes <project>/shorts/brief (frames +
audio curve + meta). The analysis step is an agent session that reads the
brief and writes <project>/shorts/plan.yaml (clip windows, portrait crop
boxes, titles). `wayang shorts-render` cuts each clip with ffmpeg and
verifies the renders with real frame probes on disk, not logs.
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


def sample_brief(video: Path, brief_dir: Path, n_frames: int = 12, bin_seconds: float = 1.0) -> dict:
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
    log.info("brief: %s (%d frames, %d audio bins)", brief_dir, n_frames, len(curve))
    return meta


def _resolve_source(raw: str, plan_path: Path) -> Path:
    """Plan source paths: cwd first, then project dir, then the plan dir."""
    cands = [Path(raw), plan_path.parent.parent / raw, plan_path.parent / raw]
    for c in cands:
        if c.is_file():
            return c
    raise SystemExit(f"plan.source video not found (tried: {', '.join(str(c) for c in cands)})")


def load_plan(plan_path: Path) -> tuple:
    """Parse + validate a shorts plan. Returns (plan, source_meta).

    A clip must carry: id, title, start, end, crop [x0,y0,x1,y1] inside the
    source frame and portrait, optional render {width,height} (even).
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
        c["crop"] = [x0, y0, x1, y1]
        c["render"] = {"width": rw, "height": rh}
    log.info("plan ok: %d clip(s), source %s", len(plan["clips"]), video)
    return plan, src


def render_clip(video: Path, clip: dict, out_dir: Path, force: bool = False) -> dict:
    """Cut one portrait clip, then verify with ffprobe + frame probes on disk.

    Skips clips that already have a passing verify.json unless force=True.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    mp4, verify_path = out_dir / "clip.mp4", out_dir / "verify.json"
    if not force and mp4.is_file() and verify_path.is_file():
        try:
            old = json.loads(verify_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            log.warning("clip %s: cached verify.json unreadable (%s) - re-rendering", clip["id"], e)
        else:
            if old.get("ok"):
                log.info("clip %s: cached verified render (use --force to redo)", clip["id"])
                return old

    x0, y0, x1, y1 = clip["crop"]
    w, h = (x1 - x0) - (x1 - x0) % 2, (y1 - y0) - (y1 - y0) % 2
    rw, rh = clip["render"]["width"], clip["render"]["height"]
    start, dur = float(clip["start"]), float(clip["end"]) - float(clip["start"])
    proc = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-i", str(video), "-t", f"{dur:.3f}",
         "-vf", f"crop={w}:{h}:{x0}:{y0},scale={rw}:{rh}:flags=lanczos,setsar=1",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(mp4)],
        check=False,
    )
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
    verify["ok"] = ok
    _atomic_write(verify_path, json.dumps(verify, indent=2) + "\n")
    if not ok:
        log.error("clip %s: verification failed: %s", clip["id"], verify)
        raise SystemExit(1)
    log.info("clip %s: %dx%d %.2fs verified (%d frame probes) -> %s",
             clip["id"], got_w, got_h, got_dur, len(verify["probes"]), out_dir)
    return verify
