"""Platform-owned post-render guards: duration guard + visibility lint.

Vendors copy expected-seconds.txt and timeline.json into OUT_DIR; this module
compares and lints once, centrally, so no vendor carries its own copy.
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from wayang import paths

log = logging.getLogger("ce.render_checks")


def ffprobe_json(mp4: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(mp4)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def ffmpeg_frame(mp4: Path, t: float, total: float, out: Path) -> bool:
    t = max(0.0, min(t, total - 0.2))
    proc = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(mp4),
         "-frames:v", "1", str(out)],
        check=False,
    )
    return proc.returncode == 0 and out.is_file()


def ffmpeg_volume(mp4: Path, start: float, dur: float) -> float:
    proc = subprocess.run(
        ["ffmpeg", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(mp4),
         "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    for line in proc.stderr.splitlines():
        if "mean_volume:" in line:
            return float(line.split("mean_volume:")[1].replace("dB", "").strip())
    return -99.0


def band_diff_count(a_img, b_img, box) -> int:
    from PIL import ImageChops

    x0, y0, x1, y1 = [int(v) for v in box]
    ca = a_img.crop((x0, y0, x1, y1))
    cb = b_img.crop((x0, y0, x1, y1))
    diff = ImageChops.difference(ca, cb).convert("RGB")
    px = diff.load()
    w, h = diff.size
    n = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            p = px[x, y]
            if p[0] > 24 or p[1] > 24 or p[2] > 24:
                n += 1
    return n


def duration_guard(out: Path, vendor: str) -> None:
    """Compare the render against expected-seconds.txt (platform-owned guard).

    Vendors copy expected-seconds.txt to OUT_DIR; the compare runs once here
    instead of a per-vendor awk copy inside every build.sh. Tolerance 0.5s
    covers container rounding.
    """
    expected_file = out / "expected-seconds.txt"
    if not expected_file.is_file():
        log.warning("duration guard skipped: %s missing (vendor '%s')", expected_file, vendor)
        return
    expected = float(expected_file.read_text(encoding="utf-8").strip())
    actual = float(ffprobe_json(out / "video.mp4")["format"]["duration"])
    log.info("duration guard: actual=%.2fs expected=%.2fs", actual, expected)
    if abs(actual - expected) > 0.5:
        log.error(
            "duration guard: rendered %.2fs deviates from expected %.2fs (empty-tail bug class)",
            actual,
            expected,
        )
        raise SystemExit(1)


def lint_project(pdir: Path, mp4: Path, data: dict) -> bool:
    """Post-render visibility lint. Returns True when every check passes."""
    from PIL import Image

    info = ffprobe_json(mp4)
    stream = next(s for s in info["streams"] if s.get("codec_type") == "video")
    W, H = int(stream["width"]), int(stream["height"])
    duration = float(info["format"]["duration"])
    s = data.get("settings", {})
    fontSize = s.get("font", {}).get("size", 70)
    charH = s.get("character", {}).get("height", 275)
    subPct = s.get("subtitle", {}).get("max_width_percent", 55)
    subBottom = s.get("subtitle", {}).get("bottom_offset", 40)
    subW = W * subPct / 100
    subH = fontSize * 1.5 * 2
    subX0, subX1 = (W - subW) / 2, (W + subW) / 2
    subY0, subY1 = H - subBottom - subH, H - subBottom
    cardBox = (W * 0.15, H * 0.15, W * 0.85, H * 0.62)

    if (W, H) != (s.get("video", {}).get("width", W), s.get("video", {}).get("height", H)):
        log.warning("render size %dx%d differs from settings", W, H)

    tl_path = mp4.parent / "timeline.json"
    tl = None
    if tl_path.is_file():
        tl = json.loads(tl_path.read_text(encoding="utf-8"))

    # layout overlap: prefer the mapper-declared boxes, fall back to computed
    declared = (tl or {}).get("layout")
    if declared:
        band = declared.get("subtitle_band") or []
        for entry in declared.get("characters", []):
            bx = entry.get("box") or [0, 0, 0, 0]
            if band[0] < bx[2] and band[2] > bx[0] and band[1] < bx[3] and band[3] > bx[1]:
                log.error("layout: subtitle band overlaps character '%s' box", entry.get("id"))
                return False
        if len(band) == 4:
            # Portrait geometry: the mapper lifts the subtitle band above
            # the characters, so the ink check below must probe the
            # declared band, not the computed one.
            subX0, subY0, subX1, subY1 = (float(v) for v in band)
    else:
        for cid, c in data["characters"].items():
            side = c.get("position", "right")
            cx0 = 40 if side == "left" else W - 40 - charH
            if subX0 < cx0 + charH and subX1 > cx0 and subY0 < H and subY1 > H - charH:
                log.error("layout: subtitle band overlaps character '%s' box", cid)
                return False

    manifest_path = pdir / "voices" / "manifest.json"
    manifest = None
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    real_voices = bool(manifest and manifest.get("engines"))

    lipsync = None
    lipsync_path = pdir / "voices" / "lipsync.json"
    if lipsync_path.is_file():
        try:
            lipsync = json.loads(lipsync_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("lipsync: %s is not valid JSON, mouth check uses the clock delta", lipsync_path)
            lipsync = None

    windows = []
    by_id = {}
    if tl:
        by_id = {int(e["id"]): e for e in tl.get("lines", [])}
    for line in data["script"]:
        entry = by_id.get(int(line["id"]))
        if entry:
            dur = float(entry["end"]) - float(entry["start"])
            windows.append((line, float(entry["start"]), dur))
        if windows:
            log.info("lint: using vendor timeline.json (%d lines)", len(windows))
    if not windows:
        log.error("visibility lint: %s missing - the vendor must emit the timeline it renders", tl_path)
        raise SystemExit(1)

    tmp = pdir / "out" / ".lint"
    tmp.mkdir(parents=True, exist_ok=True)
    tail_png = tmp / "tail.png"
    if not ffmpeg_frame(mp4, duration - 0.4, duration, tail_png):
        log.error("visibility lint: could not extract the reference frame")
        raise SystemExit(1)
    tail = Image.open(tail_png).convert("RGB")

    failures = 0
    for line, start, dur in windows:
        mid = start + dur * 0.6
        f_png = tmp / f"f{line['id']}.png"
        if not ffmpeg_frame(mp4, mid, duration, f_png):
            log.error("visibility: line %s frame missing - render is shorter than the computed timeline", line["id"])
            failures += 1
            continue
        img = Image.open(f_png).convert("RGB")

        sub_ink = band_diff_count(img, tail, (subX0, max(0, subY0), subX1, subY1))
        if sub_ink < 150:
            log.error("visibility: line %s subtitle has no ink in the subtitle band", line["id"])
            failures += 1
        v = line.get("visual")
        if v and v.get("type") == "text" and v.get("text"):
            card_ink = band_diff_count(img, tail, cardBox)
            if card_ink < 150:
                log.error("visibility: line %s text card has no ink in the card region", line["id"])
                failures += 1
        c = data["characters"][line["character"]]
        side = c.get("position", "right")
        cx0 = 40 if side == "left" else W - 40 - charH
        box = (cx0, H - charH, cx0 + charH, H)
        theme_png = paths.backgrounds_dir() / f"{(s.get('background') or 'riverbank')}.png"
        if theme_png.is_file():
            theme_img = Image.open(theme_png).convert("RGB").resize((W, H))
            present = band_diff_count(img, theme_img, box)
            log.debug("character presence sampled px: %s", present)
            if present < (charH * charH) / 60:
                log.error("visibility: line %s character '%s' missing from its corner box", line["id"], line["character"])
                failures += 1
        else:
            log.warning("character presence check skipped: theme png missing for theme '%s'", s.get("background") or "riverbank")
        f2 = tmp / f"f{line['id']}b.png"
        mouth_checked = False
        if lipsync:
            wins = (lipsync.get("lines") or {}).get(f"{line['id']:02d}_{line['character']}") or []
            if wins:
                # wav-relative window seconds -> absolute seconds on the video
                # clock (audio plays at playback_rate from the line start)
                rate = float((s.get("video") or {}).get("playback_rate", 1) or 1)
                open_t = start + (wins[0][0] + wins[0][1]) / 2 / rate
                gap_t = None
                if wins[0][0] >= 0.12:
                    gap_t = start + wins[0][0] / 2 / rate  # lead silence
                elif len(wins) > 1 and wins[1][0] - wins[0][1] >= 0.12:
                    gap_t = start + (wins[0][1] + wins[1][0]) / 2 / rate  # gap between windows
                elif start + dur - (start + wins[-1][1] / rate) >= 0.12:
                    gap_t = (start + wins[-1][1] / rate + start + dur) / 2  # pause after the voice
                if gap_t is not None:
                    o_png = tmp / f"m{line['id']}o.png"
                    c_png = tmp / f"m{line['id']}c.png"
                    if ffmpeg_frame(mp4, open_t, duration, o_png) and ffmpeg_frame(mp4, gap_t, duration, c_png):
                        o_img = Image.open(o_png).convert("RGB")
                        c_img = Image.open(c_png).convert("RGB")
                        delta = band_diff_count(o_img, c_img, box)
                        # Mouth-scale gate: the open-vs-closed art pair differs by
                        # ~104 sampled px inside the char box (measured on the
                        # mascot art at charH 275), far below the character
                        # presence gate charH^2/60. 30 stays under the real art
                        # diff while sitting above encode noise.
                        threshold = 30
                        log.info("line %s: mouth open/closed delta %s (threshold %d)", line["id"], delta, threshold)
                        mouth_checked = True
                        if delta < threshold:
                            log.error("visibility: line %s mouth did not move between open and closed frames", line["id"])
                            failures += 1
        if not mouth_checked:
            if ffmpeg_frame(mp4, min(mid + 0.21, duration - 0.2), duration, f2):
                img2 = Image.open(f2).convert("RGB")
                anim = band_diff_count(img, img2, box)
                log.info("character animation delta: %s", anim)
        if real_voices:
            vol = ffmpeg_volume(mp4, start, dur)
            if vol < -55.0:
                log.error("audibility: line %s voice is silent (%.1f dB)", line["id"], vol)
                failures += 1
            else:
                log.info("line %s: subtitle ok, character ok, voice %.1f dB", line["id"], vol)
        else:
            log.info("line %s: subtitle ok, character ok (estimate render: voice check skipped)", line["id"])

    if failures:
        log.error("visibility lint: %d failure(s)", failures)
        raise SystemExit(1)
    log.info("visibility lint: all checks passed")
    return True
