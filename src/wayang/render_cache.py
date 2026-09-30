"""Segment-cached incremental rendering.

Docker-style layer cache over the vendor render: after every successful
render, out/render-cache.json records one hash per script line covering
everything that determines that line's frames and audio (line YAML, its wav
manifest entry, its lipsync windows, global settings, the vendor tree). The
next render reuses unchanged lines from the previous master and
range-renders only the changed spans (vendor capabilities.range_render),
splicing at frame-aligned cell boundaries. A cell spans a line's window
plus its trailing pause, so splices land inside silence gaps. Any
inconsistency falls back to a full render, logged. Guards always run on the
final output; the cache never skips them.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import time
from pathlib import Path

from wayang import paths
from wayang.render_checks import ffprobe_json

log = logging.getLogger("ce.render_cache")

CACHE_NAME = "render-cache.json"


class _Fallback(Exception):
    """Abandon the incremental attempt with a logged reason."""


def _fail_inc(reason: str):
    raise _Fallback(reason)


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_TREE_JUNK = ("node_modules", ".work", "out", ".omc", ".ruff_cache",
              ".git", "__pycache__", ".dashboard")


def _vendor_tree_hash(vdir: Path) -> str:
    """Content hash of the vendor implementation. A mapper or engine edit
    invalidates every cached line. Build outputs, dependency trees and tool
    state (omc/ruff caches, which mutate while other agents work) are
    excluded so the hash tracks engine sources only."""
    h = hashlib.sha256()
    if not vdir.is_dir():
        return "missing"
    for p in sorted(vdir.rglob("*")):
        rel = p.relative_to(vdir)
        if any(part in _TREE_JUNK for part in rel.parts):
            continue
        if p.is_file() and not p.suffix == ".log":
            h.update(str(rel).encode("utf-8") + b"\0")
            h.update(p.read_bytes() + b"\0")
    return h.hexdigest()[:16]


def global_hash(data: dict, vendor: str) -> str:
    """Hash of everything that affects every line: meta, settings,
    characters, the vendor implementation itself."""
    payload = {
        "meta": data.get("meta"),
        "settings": data.get("settings"),
        "characters": data.get("characters"),
        "vendor": vendor,
        "vendor_tree": _vendor_tree_hash(paths.vendor_dir(vendor)),
    }
    return _sha_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))[:16]


def line_hashes(data: dict, pdir: Path, ghash: str) -> dict[str, str]:
    """Per-line hash: global inputs + the line's own YAML + its wav manifest
    entry (text hash and seconds) + its lipsync windows."""
    vdir = pdir / "voices"
    manifest: dict = {}
    mpath = vdir / "manifest.json"
    if mpath.is_file():
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
    lipsync: dict = {}
    lpath = vdir / "lipsync.json"
    if lpath.is_file():
        lipsync = json.loads(lpath.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for line in data["script"]:
        key = f"{line['id']:02d}_{line['character']}"
        payload = {
            "global": ghash,
            "line": line,
            "wav": (manifest.get("lines") or {}).get(f"{key}.wav"),
            "lipsync": (lipsync.get("lines") or {}).get(key),
        }
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        out[str(line["id"])] = _sha_bytes(blob)[:16]
    return out


def cache_path(pdir: Path) -> Path:
    return pdir / "out" / CACHE_NAME


def load_cache(pdir: Path) -> dict | None:
    p = cache_path(pdir)
    if not p.is_file():
        return None
    try:
        cache = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log.warning("render cache: %s unreadable - ignoring", p)
        return None
    return cache if isinstance(cache, dict) else None


def write_cache(pdir: Path, cache: dict) -> None:
    p = cache_path(pdir)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)


def record(pdir: Path, data: dict, full_seconds: float | None, inc: dict | None) -> dict | None:
    """Write the cache after a successful render (guards already passed)."""
    out = pdir / "out"
    master = out / "video.mp4"
    tl_path = out / "timeline.json"
    if not (master.is_file() and tl_path.is_file()):
        return None
    vendor = data["meta"]["vendor"]
    fps = int(((data.get("settings") or {}).get("video") or {}).get("fps", 30) or 30)
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    info = ffprobe_json(master)
    vs = next(s for s in info["streams"] if s.get("codec_type") == "video")
    frames = int(vs.get("nb_frames") or round(float(info["format"]["duration"]) * fps))
    ghash = global_hash(data, vendor)
    hashes = line_hashes(data, pdir, ghash)
    prev = load_cache(pdir) or {}
    lines = {}
    for entry in tl["lines"]:
        lid = str(entry["id"])
        if lid in hashes:
            lines[lid] = {
                "hash": hashes[lid],
                "start": float(entry["start"]),
                "end": float(entry["end"]),
            }
    if inc:
        for spec in inc.get("spans", []):
            first_s, _, last_s = str(spec["lines"]).partition("-")
            first, last = int(first_s), int(last_s) if last_s else int(first_s)
            for lid in lines:
                if first <= int(lid) <= last:
                    lines[lid]["segment"] = spec["segment"]
    cache = {
        "version": 1,
        "vendor": vendor,
        "fps": fps,
        "global_hash": ghash,
        "master": {
            "sha256": _sha_file(master),
            "frames": frames,
            "duration": round(float(info["format"]["duration"]), 3),
        },
        "lines": lines,
        "last_full_seconds": (
            round(full_seconds, 1) if full_seconds is not None else prev.get("last_full_seconds")
        ),
    }
    if inc:
        cache["last_incremental"] = {
            "spans": inc.get("spans", []),
            "rendered_frames": inc.get("rendered_frames", 0),
            "seconds": round(inc.get("seconds", 0.0), 1),
        }
    write_cache(pdir, cache)
    log.info(
        "render cache: written (%d line(s), master %d frames)", len(lines), frames
    )
    return cache


# ---------------------------------------------------------------- pieces ---


def _keyframes(mp4: Path, fps: int) -> set[int]:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_packets",
         "-show_entries", "packet=pts_time,flags", "-of", "json", str(mp4)],
        capture_output=True, text=True, check=True,
    )
    kfs = set()
    for pkt in json.loads(proc.stdout).get("packets", []):
        if "K" in (pkt.get("flags") or "") and pkt.get("pts_time") is not None:
            kfs.add(int(round(float(pkt["pts_time"]) * fps)))
    return kfs


def _count_frames(mp4: Path, fps: int) -> int:
    info = ffprobe_json(mp4)
    vs = next(s for s in info["streams"] if s.get("codec_type") == "video")
    nb = str(vs.get("nb_frames") or "")
    if nb.isdigit():
        return int(nb)
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
         "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(mp4)],
        capture_output=True, text=True, check=True,
    )
    return int(proc.stdout.strip() or 0)


def _video_params(info: dict) -> dict:
    vs = next(s for s in info["streams"] if s.get("codec_type") == "video")
    astream = next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)
    tb = vs.get("time_base") or "1/15360"
    num, _, den = tb.partition("/")
    # mp4 convention: time_base = 1/timescale, so the track timescale is the
    # denominator (tb 1/90000 -> 90000 ticks/s).
    try:
        timescale = round(int(den) / int(num)) if int(num) else 15360
    except (ValueError, ZeroDivisionError):
        timescale = 15360
    level = int(vs.get("level") or 40)
    refs = vs.get("refs")
    return {
        "profile": (vs.get("profile") or "high").lower(),
        "level": f"{level // 10}.{level % 10}",
        "pix_fmt": vs.get("pix_fmt") or "yuv420p",
        "timescale": max(1, timescale),
        "sample_rate": int((astream or {}).get("sample_rate") or 48000),
        "channels": int((astream or {}).get("channels") or 2),
        "refs": int(refs) if refs else None,
    }


def _ffmpeg(args: list[str], dest: Path) -> bool:
    proc = subprocess.run(["ffmpeg", "-y", "-v", "error", *args, str(dest)], check=False)
    return proc.returncode == 0 and dest.is_file()


def _reencode_piece(master: Path, a: int, b: int, fps: int, vp: dict,
                    seg_dir: Path, name: str) -> Path:
    """Re-encode frames [a, b) of the master; encoder params pinned to the
    master stream so the part stays concat-compatible. Frame-exact."""
    piece = seg_dir / f"piece-{name}.mp4"
    x264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-profile:v", vp["profile"], "-level", vp["level"],
            "-pix_fmt", vp["pix_fmt"], "-r", str(fps)]
    if vp["refs"]:
        x264 += ["-x264-params", f"ref={vp['refs']}"]
    args = ["-ss", f"{a / fps:.6f}", "-i", str(master), "-frames:v", str(b - a),
            "-map", "0:v:0", "-map", "0:a:0?", *x264,
            "-c:a", "aac", "-ar", str(vp["sample_rate"]), "-ac", str(vp["channels"]),
            "-video_track_timescale", str(vp["timescale"])]
    if not _ffmpeg(args, piece):
        _fail_inc(f"ffmpeg failed re-encoding piece {name}")
    got = _count_frames(piece, fps)
    if got != b - a:
        _fail_inc(f"piece {name} has {got} frames, expected {b - a}")
    return piece


def _copy_piece(master: Path, a: int, b: int, fps: int, vp: dict,
                seg_dir: Path, name: str) -> Path:
    """Stream-copy frames [a, b): bit-exact bytes from the master. The start
    must be a keyframe; -frames:v cuts the end packet-exact."""
    piece = seg_dir / f"piece-{name}.mp4"
    args = ["-ss", f"{a / fps:.6f}", "-i", str(master), "-frames:v", str(b - a),
            "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            "-video_track_timescale", str(vp["timescale"])]
    if not _ffmpeg(args, piece):
        _fail_inc(f"ffmpeg failed copying piece {name}")
    got = _count_frames(piece, fps)
    if got != b - a:
        _fail_inc(f"piece {name} copy has {got} frames, expected {b - a}")
    return piece


def _extract_piece(master: Path, a: int, b: int, kfs: set[int], fps: int,
                   vp: dict, seg_dir: Path, name: str) -> list[Path]:
    """Cut frames [a, b) of the master into 1-2 concat parts. The copy must
    start on a keyframe, so at most one partial GOP at the start is
    re-encoded; everything from the next keyframe to b is stream-copied
    bit-exact. A later concat part always starts on a fresh keyframe
    (re-encode IDR or vendor frame 0), so the piece end never needs one."""
    ka = min((k for k in kfs if a <= k < b), default=b)
    parts: list[Path] = []
    if ka > a:
        parts.append(_reencode_piece(master, a, ka, fps, vp, seg_dir, f"{name}-a"))
    if ka < b:
        try:
            parts.append(_copy_piece(master, ka, b, fps, vp, seg_dir, f"{name}-m"))
        except _Fallback as e:
            log.info("render cache: %s - re-encoding %s [%d,%d)", e, name, ka, b)
            parts.append(_reencode_piece(master, ka, b, fps, vp, seg_dir, f"{name}-m"))
    return parts


def _concat(pieces: list[Path], dest: Path, vp: dict) -> None:
    for piece in pieces:
        if not piece.is_file():
            _fail_inc(f"concat piece missing: {piece}")
    lst = dest.parent / f".{dest.name}.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in pieces), encoding="utf-8")
    try:
        proc = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-c", "copy", "-video_track_timescale", str(vp["timescale"]), str(dest)],
            capture_output=True, text=True, check=False,
        )
    finally:
        lst.unlink(missing_ok=True)
    # The concat demuxer can exit 0 after partial output (e.g. one input
    # unreadable), so stderr is checked too.
    if proc.returncode != 0 or proc.stderr.strip() or not dest.is_file():
        _fail_inc(f"concat of pieces failed: {proc.stderr.strip()[:200]}")


def _normalize_piece(piece: Path, vp: dict, seg_dir: Path) -> Path:
    """Remux a piece with canonical start timestamps/timescale so concat
    offset arithmetic cannot collide at boundaries."""
    norm = seg_dir / f"{piece.stem}-norm.mp4"
    args = ["-i", str(piece), "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            "-video_track_timescale", str(vp["timescale"])]
    if not _ffmpeg(args, norm):
        _fail_inc(f"normalizing piece {piece.name} failed")
    return norm


def _splice(pieces: list[Path], dest: Path, vp: dict, seg_dir: Path, fps: int) -> str:
    """Concat the parts into dest, bit-exact when possible. Returns the tier
    used: copy | normalized | re-encode."""
    try:
        _concat(pieces, dest, vp)
        _decode_check(dest)
        return "copy"
    except _Fallback as e:
        log.info("render cache: copy concat rejected (%s) - normalizing pieces", str(e)[:160])
    norm = [_normalize_piece(p, vp, seg_dir) for p in pieces]
    _concat(norm, dest, vp)
    try:
        _decode_check(dest)
        return "normalized"
    except _Fallback as e:
        log.info("render cache: normalized concat still rejected (%s) - one re-encode pass", str(e)[:160])
    lst = dest.parent / f".{dest.name}.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in pieces), encoding="utf-8")
    x264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-profile:v", vp["profile"], "-level", vp["level"],
            "-pix_fmt", vp["pix_fmt"], "-r", str(fps)]
    args = ["-f", "concat", "-safe", "0", "-i", str(lst), *x264,
            "-c:a", "aac", "-ar", str(vp["sample_rate"]), "-ac", str(vp["channels"])]
    try:
        proc = subprocess.run(["ffmpeg", "-y", "-v", "error", *args, str(dest)], check=False)
    finally:
        lst.unlink(missing_ok=True)
    if proc.returncode != 0 or not dest.is_file():
        _fail_inc("re-encode concat failed")
    _decode_check(dest)
    return "re-encode"


def _decode_check(mp4: Path) -> None:
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(mp4), "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0 or proc.stderr.strip():
        _fail_inc(f"spliced master does not decode cleanly: {proc.stderr.strip()[:300]}")


# ------------------------------------------------------------- orchestration


def _contiguous_spans(changed: list[int], order: list[int]) -> list[list[int]]:
    idx = {lid: i for i, lid in enumerate(order)}
    marks = sorted(idx[lid] for lid in changed)
    spans: list[list[int]] = []
    run = [marks[0]]
    for m in marks[1:]:
        if m == run[-1] + 1:
            run.append(m)
        else:
            spans.append(run)
            run = [m]
    spans.append(run)
    return [[order[i] for i in s] for s in spans]


def _run_vendor(build: Path, pdir: Path, out: Path, env_extra: dict) -> bool:
    env = dict(os.environ, **env_extra)
    proc = subprocess.run(["bash", str(build), str(pdir), str(out)], check=False, env=env)
    return proc.returncode == 0


def try_incremental(pdir: Path, data: dict, caps: dict, build: Path) -> dict | None:
    """Attempt a splice render. Returns a summary dict when out/video.mp4
    was produced incrementally, None on a logged full-render fallback."""
    try:
        return _try_incremental(pdir, data, caps, build)
    except _Fallback as e:
        log.info("render cache: full-render fallback (%s)", e)
        return None
    except Exception:
        log.exception("render cache: incremental attempt crashed")
        return None


def _try_incremental(pdir: Path, data: dict, caps: dict, build: Path) -> dict | None:
    out = pdir / "out"
    master = out / "video.mp4"
    vendor = data["meta"]["vendor"]
    cache = load_cache(pdir)
    if cache is None:
        _fail_inc("no render-cache.json yet")
    if cache.get("vendor") != vendor:
        _fail_inc(f"cache belongs to vendor '{cache.get('vendor')}'")
    if cache.get("version") != 1 or not isinstance(cache.get("lines"), dict):
        _fail_inc("cache format not understood")
    if not master.is_file():
        _fail_inc("previous master out/video.mp4 missing")
    if _sha_file(master) != (cache.get("master") or {}).get("sha256"):
        _fail_inc("master sha256 mismatch (video changed outside a cached render)")

    fps = int(((data.get("settings") or {}).get("video") or {}).get("fps", 30) or 30)
    if int(cache.get("fps", fps)) != fps:
        _fail_inc("fps changed since the cached render")

    ghash = global_hash(data, vendor)
    new_hashes = line_hashes(data, pdir, ghash)
    old_lines: dict = cache["lines"]
    if set(old_lines) != set(new_hashes):
        _fail_inc("script line set changed")
    order = [int(k) for k in old_lines]  # insertion order == script order at write time
    changed = [i for i in order if old_lines[str(i)]["hash"] != new_hashes[str(i)]]
    if not changed:
        log.info("render cache: 0 of %d line(s) changed - reusing %s unchanged", len(order), master)
        return {"spans": [], "rendered_frames": 0, "seconds": 0.0, "unchanged_reuse": True}
    spans = _contiguous_spans(changed, order)
    if len(spans) == 1 and len(spans[0]) == len(order):
        _fail_inc("every line changed")
    supported = caps.get("supported") or {}
    if not (supported.get("range_render") or caps.get("range_render")):
        _fail_inc(f"vendor '{vendor}' cannot range-render (capabilities.range_render unset)")

    # Fresh timing from the vendor mapper, no frames rendered.
    if not _run_vendor(build, pdir, out, {"WAYANG_PLAN_ONLY": "1"}):
        _fail_inc("vendor plan-only run failed")
    tl = json.loads((out / "timeline.json").read_text(encoding="utf-8"))
    total_new = int(round(float(tl["total"]) * fps))
    new_cells = {int(e["id"]): int(round(float(e["start"]) * fps)) for e in tl["lines"]}
    new_order = [int(e["id"]) for e in tl["lines"]]
    if new_order != order:
        _fail_inc("timeline line order differs from the cache")
    old_cells = {i: int(round(float(old_lines[str(i)]["start"]) * fps)) for i in order}
    old_total = int((cache.get("master") or {}).get("frames") or 0)

    info = ffprobe_json(master)
    vp = _video_params(info)
    master_frames = _count_frames(master, fps)
    if master_frames != old_total:
        _fail_inc(f"master has {master_frames} frames, cache says {old_total}")
    kfs = _keyframes(master, fps)

    seg_dir = out / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    pieces: list[Path] = []
    span_meta: list[dict] = []
    rendered_frames = 0
    cursor_new = 0
    cursor_old = 0
    for span in spans:
        first, last = span[0], span[-1]
        after = order[order.index(last) + 1] if last != order[-1] else None
        a_new = new_cells[first]
        b_new = new_cells[after] if after is not None else total_new
        a_old = old_cells[first]
        b_old = old_cells[after] if after is not None else old_total
        if a_new != a_old:
            _fail_inc(f"line {first} moved although nothing before it changed")
        if a_new > cursor_new:
            if (a_new - cursor_new) != (a_old - cursor_old):
                _fail_inc("unchanged region length mismatch")
            pieces.extend(_extract_piece(master, cursor_old, a_old, kfs, fps, vp, seg_dir, f"head-{first}"))
        seg = seg_dir / f"span-{first:03d}-{last:03d}.mp4"
        (out / "span.mp4").unlink(missing_ok=True)  # never splice a stale span
        if not _run_vendor(build, pdir, out, {"WAYANG_RENDER_FRAMES": f"{a_new}-{b_new - 1}"}):
            _fail_inc(f"vendor span render failed (frames {a_new}-{b_new - 1})")
        raw = out / "span.mp4"
        if not raw.is_file():
            _fail_inc("vendor span render wrote no span.mp4")
        raw.replace(seg)
        seg_frames = _count_frames(seg, fps)
        if seg_frames != b_new - a_new:
            _fail_inc(f"span segment has {seg_frames} frames, expected {b_new - a_new}")
        pieces.append(seg)
        span_meta.append({
            "lines": str(first) if first == last else f"{first}-{last}",
            "frames": f"{a_new}-{b_new - 1}",
            "segment": str(seg.relative_to(out)),
        })
        rendered_frames += b_new - a_new
        cursor_new = b_new
        cursor_old = b_old
    if total_new > cursor_new:
        if (total_new - cursor_new) != (old_total - cursor_old):
            _fail_inc("tail region length mismatch")
        pieces.extend(_extract_piece(master, cursor_old, old_total, kfs, fps, vp, seg_dir, "tail"))

    spliced = out / ".video.spliced.mp4"
    spliced.unlink(missing_ok=True)
    tier = _splice(pieces, spliced, vp, seg_dir, fps)
    got = _count_frames(spliced, fps)
    if got != total_new:
        _fail_inc(f"spliced master has {got} frames, expected {total_new}")
    _decode_check(spliced)
    prev_master = out / ".video.prev.mp4"
    prev_master.unlink(missing_ok=True)
    master.replace(prev_master)
    spliced.replace(master)
    prev_master.unlink()

    seconds = time.monotonic() - t0
    reused = len(order) - len(changed)
    baseline = cache.get("last_full_seconds")
    est = f", est. time saved ~{max(0.0, baseline - seconds):.0f}s vs last full render ({baseline:.0f}s)" if baseline else ""
    log.info(
        "render cache: %d line(s) reused, %d span(s) re-rendered (%s; %d/%d frames), splice %.1fs (%s)%s",
        reused, len(spans), ", ".join(f"lines {m['lines']} frames {m['frames']}" for m in span_meta),
        rendered_frames, total_new, seconds, tier, est,
    )
    return {"spans": span_meta, "rendered_frames": rendered_frames, "seconds": seconds, "tier": tier}
