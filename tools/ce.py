#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "jsonschema>=4.20", "pillow>=10.0"]
# ///
"""content_engine CLI: templates, init, validate, render."""
import argparse
import json
import logging
import shutil
import subprocess
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from tts_providers import PROVIDERS, ProviderError, line_hash, wav_seconds


def deep_merge(base: dict, overlay: dict) -> dict:
    """Overlay wins per key; dicts recurse; lists and scalars replace."""
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def find_series_file(pdir: Path):
    """Nearest series.yaml above an episode dir (up to two levels)."""
    for cand in (pdir.parent / "series.yaml", pdir.parent.parent / "series.yaml"):
        if cand.is_file():
            return cand
    return None


def is_series_dir(pdir: Path) -> bool:
    return (pdir / "series.yaml").is_file() or (pdir / "episodes").is_dir()


def series_episodes(sdir: Path) -> list:
    epi = sdir / "episodes"
    if not epi.is_dir():
        return []
    return sorted(d for d in epi.iterdir() if (d / "project.yaml").is_file())

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "project.schema.json"
log = logging.getLogger("ce")


def fail(msg: str):
    log.error(msg)
    raise SystemExit(1)


def resolve_project(value: str) -> Path:
    """Accept either a bare name under projects/ or a path relative to ROOT."""
    as_given = ROOT / value
    under_projects = ROOT / "projects" / value
    if as_given.is_dir():
        return as_given
    if under_projects.is_dir():
        return under_projects
    fail(f"project not found: {value} (looked at {as_given} and {under_projects})")
    raise AssertionError  # unreachable


def cmd_templates(args):
    for d in sorted((ROOT / "templates").iterdir()):
        if (d / "template.yaml").is_file():
            log.info(d.name)


def cmd_init(args):
    name = args.name
    name = name.removeprefix("projects/")
    src = ROOT / "templates" / args.template
    if not (src / "template.yaml").is_file():
        fail(f"unknown template: {args.template}")
    dst = ROOT / "projects" / args.name
    if dst.exists():
        fail(f"projects/{args.name} already exists")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    (dst / "template.yaml").rename(dst / "project.yaml")
    log.info(
        "created projects/%s - edit project.yaml, then: uv run tools/ce.py validate projects/%s",
        args.name,
        args.name,
    )


def cmd_init_series(args):
    src = ROOT / "templates" / args.template
    if not (src / "template.yaml").is_file():
        fail(f"unknown template: {args.template}")
    sdir = ROOT / "projects" / args.name
    if sdir.exists():
        fail(f"projects/{args.name} already exists")
    template = yaml.safe_load((src / "template.yaml").read_text(encoding="utf-8"))
    (sdir / "episodes").mkdir(parents=True)
    series = {
        "meta": {
            "title": template["meta"]["title"],
            "template": args.template,
            "vendor": template["meta"]["vendor"],
            "language": template["meta"].get("language", "ja"),
            "description": f"shared base for the {args.name} series; episodes inherit and override",
        },
        "characters": template.get("characters", {}),
        "settings": template.get("settings", {}),
    }
    header = (
        "# series.yaml - shared base for every episode in this series.\n"
        "# Episodes deep-merge this under their own project.yaml:\n"
        "# episode values win per key, dicts merge, lists (script) are episode-only.\n"
        "# This file is a fragment: it is never validated on its own.\n"
    )
    (sdir / "series.yaml").write_text(
        header + yaml.safe_dump(series, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    ep_dir = sdir / "episodes" / args.first_episode
    shutil.copytree(src, ep_dir)
    (ep_dir / "template.yaml").rename(ep_dir / "project.yaml")
    log.info(
        "series projects/%s: series.yaml + episodes/%s (add more: ce.py init %s <series>/episodes/<ep>)",
        args.name,
        args.first_episode,
        args.template,
    )


def load_project(pdir: Path) -> dict:
    pf = pdir / "project.yaml"
    if not pf.is_file():
        fail(f"{pf} missing")
    try:
        data = yaml.safe_load(pf.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        fail(f"project.yaml parse error: {e}")
    if not isinstance(data, dict):
        fail("project.yaml must be a mapping")
    series_file = find_series_file(pdir)
    if series_file is not None:
        try:
            series = yaml.safe_load(series_file.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            fail(f"series config parse error ({series_file}): {e}")
        if not isinstance(series, dict):
            fail(f"series config must be a mapping: {series_file}")
        shared = len((series.get("characters") or {}).keys())
        data = deep_merge(series, data)
        log.info("merged series config %s (%d shared character(s))", series_file, shared)
    return data


def validate_project(pdir: Path) -> dict:
    data = load_project(pdir)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(data),
        key=lambda e: list(e.absolute_path),
    )
    if errors:
        for e in errors:
            where = ".".join(str(p) for p in e.absolute_path) or "<root>"
            log.error("schema: %s: %s", where, e.message)
        raise SystemExit(1)

    chars = data["characters"]
    for line in data["script"]:
        cid = line["character"]
        if cid not in chars:
            fail(f"script id {line['id']}: unknown character '{cid}'")
        visual = line.get("visual") or {}
        if visual.get("type") == "image" and visual.get("src") and not (pdir / visual["src"]).is_file():
            fail(f"script id {line['id']}: visual image missing: {visual['src']}")
        se = line.get("se")
        if se and not (pdir / se["src"]).is_file():
            fail(f"script id {line['id']}: sound effect missing: {se['src']}")
    for cid, c in chars.items():
        if c["voice"]["engine"] not in PROVIDERS:
            fail(f"character {cid}: unsupported voice engine '{c['voice']['engine']}' (known: {', '.join(sorted(PROVIDERS))})")
        img = c.get("image")
        if img and not (pdir / img).is_file():
            fail(f"character {cid}: image missing: {img}")
    vendor = data["meta"]["vendor"]
    build = ROOT / "vendors" / vendor / "build.sh"
    if not build.is_file():
        fail(f"vendor '{vendor}' has no build.sh (expected {build})")
    return data


def run_tts(pdir: Path, data: dict, force: bool = False) -> None:
    """Write one wav per script line into pdir/voices. All-or-nothing per project."""
    lines = data["script"]
    chars = data["characters"]
    voices_dir = pdir / "voices"
    manifest_path = voices_dir / "manifest.json"
    manifest = {"lines": {}, "engines": []}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["lines"] = manifest.get("lines", {})

    engines = sorted({chars[line["character"]]["voice"]["engine"] for line in lines})
    unavailable = []
    for engine in engines:
        ok, why = PROVIDERS[engine].available()
        if not ok:
            unavailable.append(f"{engine}: {why}")
    if unavailable:
        for why in unavailable:
            log.warning("TTS engine %s", why)
        log.warning("no TTS this run: vendor renders with estimated timing and silent audio")
        return

    jobs = []
    for line in lines:
        cfg = chars[line["character"]]["voice"]
        fname = f"{line['id']:02d}_{line['character']}.wav"
        digest = line_hash(line["text"], cfg["engine"], PROVIDERS[cfg["engine"]].config_hash(cfg))
        cached = manifest["lines"].get(fname)
        if not force and cached and cached.get("hash") == digest and (voices_dir / fname).is_file():
            continue
        jobs.append((line, cfg, fname, digest))
    if not jobs:
        manifest["engines"] = sorted({v["engine"] for v in manifest["lines"].values()})
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        log.info("TTS: all %d line voice(s) cached in %s", len(lines), voices_dir)
        return

    log.info("TTS: generating %d line voice(s) with %s", len(jobs), ", ".join(engines))
    voices_dir.mkdir(parents=True, exist_ok=True)
    for line, cfg, fname, digest in jobs:
        out = voices_dir / fname
        try:
            PROVIDERS[cfg["engine"]].synthesize(line["text"], cfg, out)
        except ProviderError as e:
            log.error("TTS failed for %s: %s", fname, e)
            raise SystemExit(1)
        seconds = wav_seconds(out)
        manifest["lines"][fname] = {"hash": digest, "seconds": round(seconds, 3), "engine": cfg["engine"]}
        log.info("TTS %s: %.2fs (%s)", fname, seconds, cfg["engine"])
    manifest["engines"] = sorted({v["engine"] for v in manifest["lines"].values()})
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_tts(args):
    pdir = resolve_project(args.project)
    targets = series_episodes(pdir) if is_series_dir(pdir) else [pdir]
    for ep in targets:
        log.info("tts %s", ep.name)
        run_tts(ep, validate_project(ep), force=args.force)


def cmd_validate(args):
    pdir = resolve_project(args.project)
    targets = series_episodes(pdir) if is_series_dir(pdir) else [pdir]
    for ep in targets:
        log.info("validating %s", ep.name)
        validate_project(ep)


# ---- visibility lint (post-render, vendor-agnostic) ----
# Layout contract every vendor must draw within:
#   characters: bottom corners, box charH tall/wide, 40px inset
#   subtitle:   bottom-center, max_width_percent wide, bottom_offset up,
#               at most 2 lines (fontSize * 1.5 * 2)
#   text card:  upper-center region (15%..85% x, 15%..62% y)
# The linter extracts frames from the rendered file and checks each object's
# box for ink, so an invisible object fails the build instead of shipping.

def _ffprobe_json(mp4: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(mp4)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def _ffmpeg_frame(mp4: Path, t: float, total: float, out: Path) -> bool:
    t = max(0.0, min(t, total - 0.2))
    proc = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(mp4),
         "-frames:v", "1", str(out)],
        check=False,
    )
    return proc.returncode == 0 and out.is_file()


def _ffmpeg_volume(mp4: Path, start: float, dur: float) -> float:
    proc = subprocess.run(
        ["ffmpeg", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(mp4),
         "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    for line in proc.stderr.splitlines():
        if "mean_volume:" in line:
            return float(line.split("mean_volume:")[1].replace("dB", "").strip())
    return -99.0


def _band_diff_count(a_img, b_img, box) -> int:
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


def lint_project(pdir: Path, mp4: Path, data: dict) -> bool:
    """Post-render visibility lint. Returns True when every check passes."""
    from PIL import Image

    info = _ffprobe_json(mp4)
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

    # layout overlap: subtitle band vs character corner boxes
    for cid, c in data["characters"].items():
        side = c.get("position", "right")
        cx0 = 40 if side == "left" else W - 40 - charH
        if subX0 < cx0 + charH and subX1 > cx0 and subY0 < H and subY1 > H - charH:
            log.error("layout: subtitle band overlaps character '%s' box", cid)
            return False

    vendor = data["meta"]["vendor"]
    rate = s.get("video", {}).get("playback_rate", 1.0) if vendor == "remotion" else 1.0
    cps = ((data.get("vendor") or {}).get(vendor) or {}).get("estimate_cps", 7.5)
    manifest_path = pdir / "voices" / "manifest.json"
    manifest = None
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    real_voices = bool(manifest and manifest.get("engines"))

    windows = []
    tl_path = mp4.parent / "timeline.json"
    if tl_path.is_file():
        tl = json.loads(tl_path.read_text(encoding="utf-8"))
        by_id = {int(entry["id"]): entry for entry in tl.get("lines", [])}
        for line in data["script"]:
            entry = by_id.get(int(line["id"]))
            if entry:
                dur = float(entry["end"]) - float(entry["start"])
                windows.append((line, float(entry["start"]), dur))
        if windows:
            log.info("lint: using vendor timeline.json (%d lines)", len(windows))
    if not windows:
        t = 0.0
        for line in data["script"]:
            fname = f"{line['id']:02d}_{line['character']}.wav"
            if manifest and fname in (manifest.get("lines") or {}):
                dur = float(manifest["lines"][fname]["seconds"])
            else:
                dur = max(0.8, len(str(line["text"]).replace(" ", "")) / (cps * rate))
            windows.append((line, t, dur))
            t += dur + (line.get("pause_after", 0.5))

    tmp = pdir / "out" / ".lint"
    tmp.mkdir(parents=True, exist_ok=True)
    tail_png = tmp / "tail.png"
    if not _ffmpeg_frame(mp4, duration - 0.4, duration, tail_png):
        log.error("visibility lint: could not extract the reference frame")
        raise SystemExit(1)
    tail = Image.open(tail_png).convert("RGB")

    failures = 0
    for line, start, dur in windows:
        mid = start + dur * 0.6
        f_png = tmp / f"f{line['id']}.png"
        if not _ffmpeg_frame(mp4, mid, duration, f_png):
            log.error("visibility: line %s frame missing - render is shorter than the computed timeline", line["id"])
            failures += 1
            continue
        img = Image.open(f_png).convert("RGB")

        sub_ink = _band_diff_count(img, tail, (subX0, max(0, subY0), subX1, subY1))
        if sub_ink < 150:
            log.error("visibility: line %s subtitle has no ink in the subtitle band", line["id"])
            failures += 1
        v = line.get("visual")
        if v and v.get("type") == "text" and v.get("text"):
            card_ink = _band_diff_count(img, tail, cardBox)
            if card_ink < 150:
                log.error("visibility: line %s text card has no ink in the card region", line["id"])
                failures += 1
        c = data["characters"][line["character"]]
        side = c.get("position", "right")
        cx0 = 40 if side == "left" else W - 40 - charH
        move = _band_diff_count(img, tail, (cx0, H - charH, cx0 + charH, H))
        if move < 80:
            log.error("visibility: line %s character '%s' shows no animation in its corner box", line["id"], line["character"])
            failures += 1
        if real_voices:
            vol = _ffmpeg_volume(mp4, start, dur)
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


def cmd_lint(args):
    pdir = resolve_project(args.project)
    data = validate_project(pdir)
    mp4 = pdir / "out" / "video.mp4"
    if not mp4.is_file():
        fail(f"no render found at {mp4} - run ce.py render first")
    lint_project(pdir, mp4, data)


def render_one(pdir: Path, skip_lint: bool = False) -> None:
    data = validate_project(pdir)
    # The vendor consumes one canonical file. When series inheritance applied,
    # materialize the merged doc so the vendor never needs to know about series.
    merged_path = pdir / ".merged.yaml"
    if find_series_file(pdir) is not None:
        merged_path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
    elif merged_path.exists():
        merged_path.unlink()
    run_tts(pdir, data)
    vendor = data["meta"]["vendor"]
    build = ROOT / "vendors" / vendor / "build.sh"
    out = pdir / "out"
    log.info("rendering via vendor '%s'", vendor)
    proc = subprocess.run(["bash", str(build), str(pdir), str(out)], check=False)
    if proc.returncode != 0:
        fail(f"vendor build.sh exited {proc.returncode}")
    log.info("done: %s", out / "video.mp4")
    if not skip_lint:
        lint_project(pdir, out / "video.mp4", data)


def cmd_render(args):
    pdir = resolve_project(args.project)
    targets = series_episodes(pdir) if is_series_dir(pdir) else [pdir]
    if len(targets) > 1:
        log.info(
            "series: %d episode(s): %s", len(targets), ", ".join(t.name for t in targets)
        )
    for ep in targets:
        render_one(ep, skip_lint=args.skip_lint)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="ce", description="content_engine CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("templates", help="list templates")
    p.set_defaults(func=cmd_templates)

    p = sub.add_parser("init", help="scaffold a project from a template")
    p.add_argument("template")
    p.add_argument("name")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", help="validate a project")
    p.add_argument("project")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("lint", help="check a rendered video for invisible objects")
    p.add_argument("project")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("init-series", help="scaffold a series: series.yaml + first episode")
    p.add_argument("name")
    p.add_argument("--template", default="dialog")
    p.add_argument("--first-episode", default="ep01")
    p.set_defaults(func=cmd_init_series)

    p = sub.add_parser("tts", help="generate line voices via configured TTS engines")
    p.add_argument("project")
    p.add_argument("--force", action="store_true", help="regenerate even when cached")
    p.set_defaults(func=cmd_tts)

    p = sub.add_parser("render", help="render a project via its vendor")
    p.add_argument("project")
    p.add_argument("--skip-lint", action="store_true", help="skip the post-render visibility lint")
    p.set_defaults(func=cmd_render)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
