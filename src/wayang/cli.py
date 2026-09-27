"""Wayang CLI: templates, init, check, validate, tts, render, setup, doctor."""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import stat
import subprocess
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from wayang import paths
from wayang.project import (
    deep_merge,
    find_series_file,
    is_series_dir,
    load_lenient,
    series_episodes,
)
from wayang.render_checks import duration_guard, lint_project
from wayang.tts_providers import (
    PROVIDERS,
    ProviderError,
    line_hash,
    provider_voices,
    wav_seconds,
)

log = logging.getLogger("ce")


def fail(msg: str):
    log.error(msg)
    raise SystemExit(1)


def resolve_project(value: str) -> Path:
    """Accept either a bare name under projects/ or a path relative to cwd."""
    cwd = Path.cwd()
    as_given = cwd / value
    under_projects = cwd / "projects" / value
    if as_given.is_dir():
        return as_given
    if under_projects.is_dir():
        return under_projects
    fail(f"project not found: {value} (looked at {as_given} and {under_projects})")
    raise AssertionError  # unreachable


def cmd_templates(args):
    for d in sorted(paths.templates_dir().iterdir()):
        if (d / "template.yaml").is_file():
            log.info(d.name)


def cmd_init(args):
    name = args.name
    name = name.removeprefix("projects/")
    src = paths.templates_dir() / args.template
    if not (src / "template.yaml").is_file():
        fail(f"unknown template: {args.template}")
    dst = Path.cwd() / "projects" / name
    if dst.exists():
        fail(f"projects/{name} already exists")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    (dst / "template.yaml").rename(dst / "project.yaml")
    log.info(
        "created projects/%s - edit project.yaml, then: wayang validate projects/%s",
        name,
        name,
    )


def cmd_init_series(args):
    src = paths.templates_dir() / args.template
    if not (src / "template.yaml").is_file():
        fail(f"unknown template: {args.template}")
    sdir = Path.cwd() / "projects" / args.name
    if sdir.exists():
        fail(f"projects/{args.name} already exists")
    template = yaml.safe_load((src / "template.yaml").read_text(encoding="utf-8"))
    (sdir / "episodes").mkdir(parents=True)
    series = {
        "meta": {
            "title": template["meta"]["title"],
            "template": args.template,
            "vendor": template["meta"]["vendor"],
            "language": template["meta"].get("language", "ms"),
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
        "series projects/%s: series.yaml + episodes/%s (add more: wayang init %s <series>/episodes/<ep>)",
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
    if series_file is None and (pdir / "series.yaml").is_file():
        series_file = pdir / "series.yaml"
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
    schema = json.loads(paths.schema_path().read_text(encoding="utf-8"))
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
    build = paths.vendor_dir(vendor) / "build.sh"
    if not build.is_file():
        hint = "" if paths.REPO_ROOT is not None else " - engines not deployed yet? run: wayang setup"
        fail(f"vendor '{vendor}' has no build.sh (expected {build}){hint}")
    return data


def run_tts(pdir: Path, data: dict, force: bool = False, only_line: int | None = None) -> None:
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
            log.warning("TTS engine unavailable: %s", why)
        log.warning("no TTS this run: vendor renders with estimated timing and silent audio")
        return

    jobs = []
    for line in lines:
        if only_line is not None and line["id"] != only_line:
            continue
        cfg = chars[line["character"]]["voice"]
        fname = f"{line['id']:02d}_{line['character']}.wav"
        provider = PROVIDERS[cfg["engine"]]
        digest = line_hash(line["text"], cfg["engine"], provider.config_hash(cfg))
        cached = manifest["lines"].get(fname)
        if not force and cached and (voices_dir / fname).is_file():
            if cached.get("hash") == digest:
                continue
            # One-time migration: caches hashed before effective params used
            # raw cfg (model=None). The same defaults were applied at
            # synthesis, so a legacy-hash hit upgrades without re-synthesis.
            legacy = line_hash(line["text"], cfg["engine"], {k: cfg.get(k) for k in provider.config_hash(cfg)})
            if cached.get("hash") == legacy:
                cached["hash"] = digest
                log.info("cache-hash upgraded to effective params: %s", fname)
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


def cmd_check(args):
    """Preflight guidance: what to fill before rendering, in plain words.
    Exit 0 ready, 1 blockers, 2 notes only."""
    pdir = resolve_project(args.project)
    data, _series_file, pre_issues = load_lenient(pdir)
    if data is None:
        for msg in pre_issues:
            fail(msg)
        fail("project.yaml could not be loaded")
    issues, notes = [], []
    for msg in pre_issues:
        log.warning("FILL: %s", msg)
    for section in ("meta", "characters", "script", "settings"):
        if section not in data:
            issues.append(f"no [{section}] section - copy it from templates/<format>/template.yaml")
    meta = data.get("meta") or {}
    if not str(meta.get("title", "")).strip():
        issues.append("meta.title is empty - name your video")
    vendor = meta.get("vendor", "remotion")
    build = paths.vendor_dir(vendor) / "build.sh"
    if not build.is_file():
        known = paths.known_engines()
        if known:
            issues.append(f"vendor '{vendor}' does not exist (known: {', '.join(known)})")
        else:
            issues.append("no engines deployed yet - run: wayang setup")
    chars = data.get("characters") or {}
    if not chars:
        issues.append("no characters - every script line needs a speaker")
    for cid, c in chars.items():
        if not str(c.get("name", "")).strip():
            issues.append(f"character '{cid}' has no name")
        v = c.get("voice") or {}
        engine = v.get("engine")
        if not engine:
            issues.append(f"character '{cid}' has no voice.engine - how should it sound?")
        elif engine not in PROVIDERS:
            issues.append(f"character '{cid}': voice engine '{engine}' is unknown (known: {', '.join(PROVIDERS.keys())})")
        else:
            ok, why = PROVIDERS[engine].available()
            if not ok:
                notes.append(f"character '{cid}' speaks via {engine}: {why} - renders stay silent with estimated timing until you set the key")
    lines = data.get("script") or []
    if not lines:
        issues.append("script is empty - write at least one line")
    for line in lines:
        if line.get("character") not in chars:
            issues.append(f"script line {line.get('id')}: speaker '{line.get('character')}' is not defined in characters")
        if not str(line.get("text", "")).strip():
            issues.append(f"script line {line.get('id')}: text is empty")
    settings = data.get("settings") or {}
    if settings.get("background") is not None:
        catalog_dir = paths.backgrounds_dir()
        if catalog_dir.is_dir():
            catalog = sorted(p.stem for p in catalog_dir.glob("*.png"))
            if settings["background"] not in catalog:
                issues.append(f"settings.background '{settings['background']}' is not a theme here (available: {', '.join(catalog)})")
    if settings.get("character", {}).get("use_images"):
        for cid in chars:
            if not (pdir / "assets" / "images" / cid / "mouth_close.png").is_file():
                notes.append(f"character '{cid}' has use_images but no art at assets/images/{cid}/ - placeholder box will show")
    manifest_file = pdir / "voices" / "manifest.json"
    if manifest_file.is_file():
        cached = len(json.loads(manifest_file.read_text(encoding="utf-8")).get("lines", {}))
        notes.append(f"{cached} line voice(s) cached in voices/ - they are reused on render")
    for msg in issues:
        log.warning("FILL: %s", msg)
    for msg in notes:
        log.info("NOTE: %s", msg)
    if args.json:
        print(json.dumps({"ready": not issues, "issues": issues, "notes": notes}))
    if issues:
        log.warning("NOT READY: %d item(s) to fill above - then: wayang validate && wayang render", len(issues))
        raise SystemExit(1)
    if notes:
        log.warning("READY with %d note(s) - see NOTE lines above", len(notes))
        raise SystemExit(2)
    log.info("READY")


def _tool_status(name: str, argv: list) -> tuple:
    path = shutil.which(name)
    if path is None:
        return False, "not found on PATH"
    try:
        out = subprocess.run(argv, capture_output=True, text=True, check=False)
    except OSError as e:
        return False, f"failed to run: {e}"
    text = (out.stdout or out.stderr).strip().splitlines()
    return True, (text[0] if text else path)


def cmd_doctor(args):
    """Report prerequisites: tools, TTS keys, deployed engines, shared assets."""
    rows = []

    def add(status: str, item: str, detail: str):
        rows.append((status, item, detail))

    try:
        v = pkg_version("wayang")
    except PackageNotFoundError:
        v = "dev (uninstalled)"
    add("ok", "wayang", v)

    home = paths.wayang_home()
    if home.is_dir():
        add("ok", "WAYANG_HOME", str(home))
    else:
        add("warn", "WAYANG_HOME", f"{home} does not exist yet (created by: wayang setup)")

    for tool, argv in (
        ("node", ["node", "--version"]),
        ("npm", ["npm", "--version"]),
        ("ffmpeg", ["ffmpeg", "-version"]),
        ("ffprobe", ["ffprobe", "-version"]),
    ):
        good, detail = _tool_status(tool, argv)
        add("ok" if good else "missing", tool, detail)

    for env_name, hint in (
        ("REVOLAB_API_KEY", "voices render silent (estimated timing) without it; get a key at revolab.ai, then: export REVOLAB_API_KEY=..."),
        ("OPENAI_API_KEY", "optional provider, unverified against the live API; export OPENAI_API_KEY=... to use it"),
    ):
        if os.environ.get(env_name):
            add("ok", env_name, "set")
        else:
            add("warn", env_name, f"not set - {hint}")

    for engine in paths.bundled_engines():
        vd = paths.vendor_dir(engine)
        if not (vd / "build.sh").is_file():
            add("missing", f"engine '{engine}'", f"not deployed at {vd} - run: wayang setup")
            continue
        detail = f"deployed at {vd}"
        nm = vd / "engine" / "node_modules"
        if (vd / "engine" / "package.json").is_file() and not nm.is_dir():
            add("missing", f"engine '{engine}'", f"package.json present but node_modules missing at {nm} - re-run: wayang setup")
        else:
            add("ok", f"engine '{engine}'", detail)

    bg = paths.backgrounds_dir()
    n_bg = len(list(bg.glob("*.png"))) if bg.is_dir() else 0
    add("ok" if n_bg else "missing", "backgrounds", f"{n_bg} theme(s) at {bg}")

    blockers = [r for r in rows if r[0] == "missing"]
    warns = [r for r in rows if r[0] == "warn"]
    for status, item, detail in rows:
        tag = {"ok": "OK", "warn": "WARN", "missing": "MISSING"}[status]
        emit = {"ok": log.info, "warn": log.warning, "missing": log.error}[status]
        emit("%-7s %s: %s", tag, item, detail)
    if args.json:
        print(json.dumps({
            "healthy": not blockers and not warns,
            "renderable": not blockers,
            "blockers": [f"{i}: {d}" for _, i, d in blockers],
            "warnings": [f"{i}: {d}" for _, i, d in warns],
        }))
    if blockers:
        log.error("doctor: %d blocker(s) - see MISSING lines", len(blockers))
        raise SystemExit(1)
    if warns:
        log.warning("doctor: renderable, %d optional item(s) missing - see WARN lines", len(warns))
        raise SystemExit(2)
    log.info("doctor: all prerequisites present")


def cmd_setup(args):
    """Deploy engines and shared assets to WAYANG_HOME (installed use)."""
    if paths.REPO_ROOT is not None:
        log.info(
            "repo dev mode: engines are already live at %s - setup is only for installed use",
            paths.vendors_root(),
        )
        return
    home = paths.wayang_home()
    src_vendors = paths.bundled_vendors_dir()
    log.info("setup: WAYANG_HOME=%s", home)
    (home / "vendors").mkdir(parents=True, exist_ok=True)
    bg_dst = home / "assets" / "backgrounds"
    bg_dst.mkdir(parents=True, exist_ok=True)
    n_bg = 0
    for png in paths.backgrounds_dir().glob("*.png"):
        shutil.copy2(png, bg_dst / png.name)
        n_bg += 1
    log.info("setup: %d background theme(s) -> %s", n_bg, bg_dst)
    engines = sorted(d.name for d in src_vendors.iterdir() if (d / "build.sh").is_file())
    for engine in engines:
        dst = home / "vendors" / engine
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src_vendors / engine, dst)
        build = dst / "build.sh"
        build.chmod(build.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        log.info("setup: engine '%s' deployed -> %s", engine, dst)
    engine_pkg = home / "vendors" / "remotion" / "engine"
    if (engine_pkg / "package.json").is_file():
        if shutil.which("npm") is None:
            log.error("npm not found on PATH - install node/npm, then re-run wayang setup")
            raise SystemExit(1)
        log.info("setup: npm install in %s (one-time, needs network)", engine_pkg)
        proc = subprocess.run(["npm", "install", "--no-fund", "--no-audit"], cwd=str(engine_pkg), check=False)
        if proc.returncode != 0:
            log.error("npm install failed (exit %d) - fix the network or npm, then re-run wayang setup", proc.returncode)
            raise SystemExit(1)
    else:
        log.warning("setup: remotion engine package.json missing at %s - engine incomplete", engine_pkg)
    missing = [e for e in engines if not (home / "vendors" / e / "build.sh").is_file()]
    if missing:
        log.error("setup incomplete, missing engines: %s", ", ".join(missing))
        raise SystemExit(1)
    log.info("setup complete - next: wayang doctor, then render from any directory")


def cmd_validate(args):
    pdir = resolve_project(args.project)
    targets = series_episodes(pdir) if is_series_dir(pdir) else [pdir]
    for ep in targets:
        log.info("validating %s", ep.name)
        validate_project(ep)


def cmd_tts(args):
    pdir = resolve_project(args.project)
    targets = series_episodes(pdir) if is_series_dir(pdir) else [pdir]
    for ep in targets:
        log.info("tts %s", ep.name)
        run_tts(ep, validate_project(ep), force=args.force, only_line=args.line)


def cmd_captions(args):
    pdir = resolve_project(args.project)
    data, _sf, _pre = load_lenient(pdir)
    if data is None:
        fail("project could not be loaded")
    windows, _from_vendor = _line_windows(data, pdir)
    text_by_id = {int(l["id"]): (l.get("display_text") or l.get("text", "")) for l in data.get("script", [])}
    srt_lines, vtt_lines = [], []
    n = 0
    for line, start, end in windows:
        lid = int(line["id"])
        if lid not in text_by_id:
            continue
        n += 1
        pair = f"{_stamp(start, ',')} --> {_stamp(end, ',')}"
        srt_lines.append(f"{n}\n{pair}\n{text_by_id[lid]}\n")
        vtt_lines.append(f"{pair}\n{text_by_id[lid]}\n\n")
    out_dir = pdir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "captions.srt").write_text("\n".join(srt_lines), encoding="utf-8")
    (out_dir / "captions.vtt").write_text("WEBVTT\n\n" + "\n".join(vtt_lines), encoding="utf-8")
    log.info("captions written: %s and %s (%d cues)", out_dir / "captions.srt", out_dir / "captions.vtt", n)


def cmd_voices(args):
    entries, err = provider_voices(args.engine)
    if err:
        fail(err)
    for e in entries or []:
        log.info("%s | %s | %s", e.get("id"), e.get("language", "-"), e.get("note", ""))


def cmd_stats(args):
    pdir = resolve_project(args.project)
    data, _sf, _pre = load_lenient(pdir)
    if data is None:
        fail("project could not be loaded")
    windows, _from_vendor = _line_windows(data, pdir)
    per_char = {}
    total = 0.0
    for line, start, end in windows:
        per_char[line["character"]] = per_char.get(line["character"], 0.0) + (end - start)
        total += end - start
    manifest_file = pdir / "voices" / "manifest.json"
    voices_cached = 0
    if manifest_file.is_file():
        voices_cached = len(json.loads(manifest_file.read_text(encoding="utf-8")).get("lines", {}))
    report = {
        "lines": len(windows),
        "estimated_voice_seconds": round(total, 2),
        "per_character_seconds": {k: round(v, 2) for k, v in sorted(per_char.items())},
        "voices_cached": voices_cached,
        "tts_calls_needed": max(0, len(windows) - voices_cached),
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        log.info("stats: %d line(s), ~%.1fs voice time", report["lines"], report["estimated_voice_seconds"])
        for k, v in report["per_character_seconds"].items():
            log.info("  %s: %.1fs", k, v)
        log.info("  voices cached: %d, tts calls needed: %d", voices_cached, report["tts_calls_needed"])


def cmd_init_episode(args):
    sdir = Path.cwd() / "projects" / args.series
    series_file = sdir / "series.yaml"
    if not series_file.is_file():
        fail(f"no series at projects/{args.series} (series.yaml missing)")
    series = yaml.safe_load(series_file.read_text(encoding="utf-8")) or {}
    ep_dir = sdir / "episodes" / args.name
    if ep_dir.exists():
        fail(f"episode exists: {ep_dir}")
    ep_dir.mkdir(parents=True)
    smeta = series.get("meta") or {}
    episodes_dir = sdir / "episodes"
    episode_no = len([d for d in episodes_dir.iterdir() if d.is_dir()]) + 1
    meta = {
        "title": args.name.replace("-", " ").title(),
        "template": smeta.get("template", "dialog"),
        "vendor": smeta.get("vendor", "remotion"),
        "language": smeta.get("language", "ms"),
        "series": args.series,
        "episode": episode_no,
    }
    project = {"meta": meta, "characters": {}, "script": []}
    first_char = next(iter(series.get("characters") or {}), None)
    if first_char:
        project["script"] = [{"id": 1, "character": first_char, "text": "TODO: tulis baris pertama anda", "scene": 1}]
    (ep_dir / "project.yaml").write_text(
        yaml.safe_dump(project, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    log.info(
        "episode created: projects/%s/episodes/%s (watak diwarisi dari series.yaml - edit script, then check)",
        args.series,
        args.name,
    )

def _line_windows(data: dict, pdir):
    """Per-line (line, start, end). Vendor timeline.json wins over estimates."""
    tl_path = pdir / "out" / "timeline.json"
    if tl_path.is_file():
        tl = json.loads(tl_path.read_text(encoding="utf-8"))
        by_id = {int(e["id"]): e for e in tl.get("lines", [])}
        out = []
        for line in data.get("script", []):
            entry = by_id.get(int(line["id"]))
            if entry:
                out.append((line, float(entry["start"]), float(entry["end"])))
        if out:
            return out, True
    vendor = data["meta"].get("vendor", "remotion")
    cps = ((data.get("vendor") or {}).get(vendor) or {}).get("estimate_cps", 7.5)
    rate = data.get("settings", {}).get("video", {}).get("playback_rate", 1.0) if vendor == "remotion" else 1.0
    t = 0.0
    out = []
    for line in data.get("script", []):
        dur = max(0.8, len(str(line.get("text", "")).replace(" ", "")) / (cps * rate))
        out.append((line, t, t + dur))
        t += dur + line.get("pause_after", 0.5)
    return out, False


def _stamp(t: float, sep: str) -> str:
    cs = max(0, round(t * 1000))
    h, rem = divmod(cs, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def cmd_lint(args):
    pdir = resolve_project(args.project)
    data = validate_project(pdir)
    mp4 = pdir / "out" / "video.mp4"
    if not mp4.is_file():
        fail(f"no render found at {mp4} - run wayang render first")
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
    build = paths.vendor_dir(vendor) / "build.sh"
    if not build.is_file():
        fail(f"vendor '{vendor}' has no build.sh (expected {build})" + ("" if paths.REPO_ROOT is not None else " - run: wayang setup"))
    out = pdir / "out"
    log.info("rendering via vendor '%s'", vendor)
    proc = subprocess.run(["bash", str(build), str(pdir), str(out)], check=False)
    if proc.returncode != 0:
        fail(f"vendor build.sh exited {proc.returncode}")
    log.info("done: %s", out / "video.mp4")
    duration_guard(out, vendor)
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
    parser = argparse.ArgumentParser(prog="wayang", description="Wayang CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("templates", help="list bundled templates")
    p.set_defaults(func=cmd_templates)

    p = sub.add_parser("init", help="scaffold a project from a template")
    p.add_argument("template")
    p.add_argument("name")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("init-series", help="scaffold a series: series.yaml + first episode")
    p.add_argument("name")
    p.add_argument("--template", default="dialog")
    p.add_argument("--first-episode", default="ep01")
    p.set_defaults(func=cmd_init_series)

    p = sub.add_parser("check", help="preflight: what to fill before rendering")
    p.add_argument("project")
    p.add_argument("--json", action="store_true", help="machine-readable report")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("validate", help="validate a project")
    p.add_argument("project")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("tts", help="generate line voices via configured TTS engines")
    p.add_argument("project")
    p.add_argument("--force", action="store_true", help="regenerate even when cached")
    p.set_defaults(func=cmd_tts)

    p = sub.add_parser("render", help="render a project via its vendor engine")
    p.add_argument("project")
    p.add_argument("--skip-lint", action="store_true", help="skip the post-render visibility lint")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("captions", help="export SRT/VTT captions from the render timeline")
    p.add_argument("project")
    p.set_defaults(func=cmd_captions)

    p = sub.add_parser("voices", help="browse voice ids for a TTS engine")
    p.add_argument("--engine", default="revolab")
    p.set_defaults(func=cmd_voices)

    p = sub.add_parser("stats", help="duration and talk-time estimate")
    p.add_argument("project")
    p.add_argument("--json", action="store_true", help="machine-readable report")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("init-episode", help="scaffold the next episode of a series")
    p.add_argument("series")
    p.add_argument("name")
    p.set_defaults(func=cmd_init_episode)
    p = sub.add_parser("lint", help="check a rendered video for invisible objects")
    p.add_argument("project")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("setup", help="deploy engines + shared assets to WAYANG_HOME (installed use)")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("doctor", help="report prerequisites: tools, TTS keys, engines")
    p.add_argument("--json", action="store_true", help="machine-readable report")
    p.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
