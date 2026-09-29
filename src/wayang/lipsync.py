"""Amplitude-driven lip sync: mouth open/close windows computed from the wavs.

compute() measures per-frame RMS with ffmpeg astats and derives open windows
relative to the voice start in three passes: a peak-relative hysteresis gate
finds voiced spans (mouth closed in silence and pauses), local RMS minima
inside each span split it at word/phrase boundaries, and any window still
longer than MAX_OPEN_S is subdivided so the mouth flaps on flat envelopes
(TTS wavs are compressed to a ~6 dB band and carry no word silences).
write_schedule() materializes voices/lipsync.json for the vendors after TTS.
Vendors fall back to their fixed mouth clock whenever the schedule is absent
(draft/estimate renders have no real wavs).

Runnable directly for testing:

    uv run src/wayang/lipsync.py <project_dir>
"""
from __future__ import annotations

import json
import logging
import math
import os
import subprocess
import sys
from pathlib import Path

log = logging.getLogger("ce.lipsync")

OPEN_BELOW_PEAK_DB = 25.0  # base span opens when RMS_level > peak_db - 25
CLOSE_BELOW_PEAK_DB = 32.0  # base span closes when RMS_level < peak_db - 32
SPLIT_BELOW_SPAN_PEAK_DB = 6.0  # valley split when RMS < span_peak - 6
SPLIT_MIN_FRAMES = 2  # ... for at least this many consecutive frames
MAX_OPEN_S = 0.35  # windows longer than this get subdivided
SPLIT_GAP_S = 0.07  # closed gap inserted by the subdivision
MIN_OPEN_S = 0.06
MIN_GAP_S = 0.08
MIN_CLIP_S = 0.02  # windows shorter than this are render noise


def _probe(wav: Path) -> tuple[int, float]:
    """Return (sample_rate, duration_seconds) via ffprobe."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate:format=duration",
         "-of", "default=noprint_wrappers=1", str(wav)],
        capture_output=True, text=True, check=True,
    )
    rate, duration = 24000, 0.0
    for line in out.stdout.splitlines():
        key, _, val = line.partition("=")
        val = val.strip()
        if key.strip() == "sample_rate" and val:
            rate = int(val)
        elif key.strip() == "duration" and val:
            duration = float(val)
    return rate, duration


def _frame_rms(wav: Path, rate: int, fps: int) -> list[float]:
    """RMS level in dB per 1/fps-second frame, via ffmpeg astats metadata."""
    samples = max(1, round(rate / fps))
    af = (
        f"asetnsamples=n={samples},"
        f"astats=metadata=1:reset={samples},"
        "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-"
    )
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-i", str(wav), "-af", af, "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg astats failed on {wav}: {proc.stderr.strip()[-400:]}")
    values: list[float] = []
    for line in proc.stdout.splitlines():
        key, _, val = line.partition("=")
        if key != "lavfi.astats.Overall.RMS_level":
            continue
        try:
            values.append(float(val))
        except ValueError:  # -inf variants or garbage: treat as silence
            values.append(float("-inf"))
    return values


def compute(wav: Path, fps: int) -> list[list[float]]:
    """Open windows [[start, end], ...] in seconds relative to the voice start."""
    rate, duration = _probe(wav)
    values = _frame_rms(wav, rate, fps)
    finite = [v for v in values if v > float("-inf")]
    if not finite:
        log.debug("lipsync: %s is silent, no windows", wav.name)
        return []
    peak_db = max(finite)
    open_thr = peak_db - OPEN_BELOW_PEAK_DB
    close_thr = peak_db - CLOSE_BELOW_PEAK_DB

    step = 1.0 / fps
    n = min(len(values), max(1, round(duration * fps)))

    # Pass 1: base voiced spans via hysteresis, as inclusive frame ranges.
    spans: list[list[int]] = []
    state_open = False
    start = 0
    for i in range(n):
        v = values[i]
        if not state_open and v > open_thr:
            state_open = True
            start = i
        elif state_open and v < close_thr:
            spans.append([start, i - 1])
            state_open = False
    if state_open:
        spans.append([start, n - 1])

    # Pass 2: split each span at local minima (word/phrase boundaries):
    # runs of >= SPLIT_MIN_FRAMES frames below span_peak - 6 dB become closed
    # gaps, widened to the min-gap floor so the cleanup cannot merge them back.
    gap_frames = max(SPLIT_MIN_FRAMES, math.ceil(MIN_GAP_S * fps))
    windows: list[list[float]] = []
    for i0, i1 in spans:
        span_thr = max(values[i0 : i1 + 1]) - SPLIT_BELOW_SPAN_PEAK_DB
        cuts = []
        i = i0
        while i <= i1:
            if values[i] < span_thr:
                j = i
                while j + 1 <= i1 and values[j + 1] < span_thr:
                    j += 1
                if j - i + 1 >= SPLIT_MIN_FRAMES:
                    cuts.append((i, j))
                i = j + 1
            else:
                i += 1
        cursor = i0
        for a, b in cuts:
            b = min(i1, max(b, a + gap_frames - 1))
            if a - cursor >= 1:
                windows.append([cursor * step, a * step])
            cursor = max(cursor, b + 1)
        if i1 >= cursor:
            windows.append([cursor * step, (i1 + 1) * step])

    # Pass 3 cleanup: merge sub-minimum gaps, drop sub-minimum opens.
    merged: list[list[float]] = []
    for w in windows:
        if merged and w[0] - merged[-1][1] < MIN_GAP_S:
            merged[-1][1] = max(merged[-1][1], w[1])
        else:
            merged.append(w)
    windows = [w for w in merged if w[1] - w[0] >= MIN_OPEN_S]

    # Pass 4: cap open length. Flat envelopes (compressed TTS) never dip at
    # word boundaries, so anything still longer than MAX_OPEN_S is chopped on
    # the frame grid with SPLIT_GAP_S closed gaps; segments never fall below
    # MIN_OPEN_S, and the inserted gaps are the last structural change.
    gap = max(1, round(SPLIT_GAP_S * fps)) / fps
    final: list[list[float]] = []
    for s, e in windows:
        span_len = e - s
        if span_len <= MAX_OPEN_S:
            final.append([s, e])
            continue
        nseg = math.ceil((span_len + gap) / (MAX_OPEN_S + gap))
        seg = (span_len - (nseg - 1) * gap) / nseg
        for k in range(nseg):
            ks = s + k * (seg + gap)
            ke = e if k == nseg - 1 else ks + seg
            final.append([ks, ke])

    return [
        [round(max(0.0, a), 3), round(min(duration, b), 3)]
        for a, b in final
        if min(duration, b) - max(0.0, a) >= MIN_CLIP_S
    ]


def write_schedule(pdir: Path, fps: int) -> Path | None:
    """Write pdir/voices/lipsync.json when real platform voices exist.

    Returns the schedule path, or None on the draft/estimate path (missing
    manifest, empty engines, or any listed wav absent).
    """
    manifest_path = pdir / "voices" / "manifest.json"
    if not manifest_path.is_file():
        log.debug("lipsync: no voices manifest, skipping schedule")
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("lines") or {}
    if not manifest.get("engines") or not entries:
        log.debug("lipsync: manifest lists no engines, skipping schedule")
        return None
    lines: dict[str, list[list[float]]] = {}
    for fname in entries:
        wav = pdir / "voices" / fname
        if not wav.is_file():
            log.debug("lipsync: %s missing, skipping schedule", wav)
            return None
        lines[Path(fname).stem] = compute(wav, fps)
    out = pdir / "voices" / "lipsync.json"
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps({"fps": fps, "lines": lines}), encoding="utf-8")
    os.replace(tmp, out)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <project_dir>")
    import yaml

    pdir = Path(sys.argv[1])
    doc = yaml.safe_load((pdir / "project.yaml").read_text(encoding="utf-8")) or {}
    fps = int(((doc.get("settings") or {}).get("video") or {}).get("fps", 30) or 30)
    schedule = write_schedule(pdir, fps)
    if schedule is None:
        raise SystemExit("no schedule (voices/manifest.json missing or incomplete)")
    payload = json.loads(schedule.read_text(encoding="utf-8"))
    log.info("lipsync: %d line(s) -> %s (fps %d)", len(payload["lines"]), schedule, payload["fps"])
    print(json.dumps(payload["lines"], indent=1))
