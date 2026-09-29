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
from wayang.render_checks import (
    duration_guard,
    ffmpeg_frame,
    ffprobe_json,
    lint_project,
)
from wayang.shorts import (
    load_plan,
    render_clip,
    sample_brief,
)
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
    for char_dir in sorted(paths.mascots_frames_dir().iterdir()):
        if char_dir.is_dir():
            dest = dst / "assets" / "images" / char_dir.name
            dest.mkdir(parents=True, exist_ok=True)
            for frame in char_dir.glob("*.png"):
                shutil.copyfile(frame, dest / frame.name)
    (dst / "template.yaml").rename(dst / "project.yaml")
    if args.preset != "landscape":
        w, h = PRESETS.get(args.preset, (1920, 1080))
        pf = dst / "project.yaml"
        text = pf.read_text(encoding="utf-8")
        text = text.replace("width: 1920", f"width: {w}", 1).replace("height: 1080", f"height: {h}", 1)
        pf.write_text(text, encoding="utf-8")
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
    for char_dir in sorted(paths.mascots_frames_dir().iterdir()):
        if char_dir.is_dir():
            dest = ep_dir / "assets" / "images" / char_dir.name
            dest.mkdir(parents=True, exist_ok=True)
            for frame in char_dir.glob("*.png"):
                shutil.copyfile(frame, dest / frame.name)
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

    pronunciations = (data.get("settings") or {}).get("pronunciations") or {}
    jobs = []
    for line in lines:
        if only_line is not None and line["id"] != only_line:
            continue
        cfg = chars[line["character"]]["voice"]
        spoken = str(line.get("text", ""))
        for word, say in pronunciations.items():
            spoken = spoken.replace(word, say)
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
        jobs.append((line, cfg, fname, digest, spoken))
    if not jobs:
        manifest["engines"] = sorted({v["engine"] for v in manifest["lines"].values()})
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        log.info("TTS: all %d line voice(s) cached in %s", len(lines), voices_dir)
        return

    log.info("TTS: generating %d line voice(s) with %s", len(jobs), ", ".join(engines))
    voices_dir.mkdir(parents=True, exist_ok=True)
    for line, cfg, fname, digest, spoken in jobs:
        out = voices_dir / fname
        try:
            PROVIDERS[cfg["engine"]].synthesize(spoken, cfg, out)
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
            if not (v.get("voice_id") or v.get("voice")):
                notes.append(f"character '{cid}' has no voice picked - browse: wayang voices --engine {engine}")
    lines = data.get("script") or []
    if not lines:
        issues.append("script is empty - write at least one line")
    for line in lines:
        if line.get("character") not in chars:
            issues.append(f"script line {line.get('id')}: speaker '{line.get('character')}' is not defined in characters")
        if line.get("emotion") and (data.get("settings") or {}).get("character", {}).get("use_images"):
            cid = line["character"]
            emo = line["emotion"]
            if not (pdir / "assets" / "images" / cid / f"{emo}_close.png").is_file():
                notes.append(f"line {line.get('id')}: emotion '{emo}' has no art for '{cid}' - the base frames will show")
    settings = data.get("settings") or {}
    caps = _vendor_capabilities(vendor)
    supported_visuals = ((caps.get("supported") or {}).get("visual_types")) or []
    scenes_map = settings.get("scenes") or {}
    if scenes_map and not ((caps.get("supported") or {}).get("scene_backgrounds")):
        notes.append("per-scene backgrounds are not supported by this vendor - one background renders throughout")
    if (settings.get("bgm") or {}).get("src") and (caps.get("supported") or {}).get("bgm") is False:
        notes.append("bgm is not supported by this vendor - the track will not render")
    for line in lines:
        v = line.get("visual") or {}
        vtype = v.get("type")
        if vtype and supported_visuals and vtype not in supported_visuals:
            degraded = (caps.get("degraded") or {}).get(vtype)
            notes.append(f"line {line.get('id')}: visual '{vtype}' degrades on {vendor} - {degraded}")
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


PRESETS = {
    "landscape": (1920, 1080),
    "portrait": (1080, 1920),
    "square": (1080, 1080),
}


def cmd_presets(args):
    log.info("available geometry presets:")
    for name, (w, h) in PRESETS.items():
        log.info("  %-10s %dx%d  (init --preset %s)", name, w, h, name)


def cmd_check_templates(args):
    """Smoke gate: schema-validate every bundled template.yaml."""
    schema = json.loads(paths.schema_path().read_text(encoding="utf-8"))
    failures = 0
    for tdir in sorted(paths.templates_dir().iterdir()):
        tf = tdir / "template.yaml"
        if not tf.is_file():
            continue
        try:
            data = yaml.safe_load(tf.read_text(encoding="utf-8"))
            errors = sorted(
                Draft202012Validator(schema).iter_errors(data),
                key=lambda e: list(e.absolute_path),
            )
            for e in errors:
                where = ".".join(str(p) for p in e.absolute_path) or "<root>"
                log.error("%s: schema: %s: %s", tdir.name, where, e.message)
            if errors:
                failures += 1
                continue
            log.info("%s: OK", tdir.name)
        except yaml.YAMLError as e:
            log.error("%s: parse error: %s", tdir.name, e)
            failures += 1
    if failures:
        fail(f"template smoke gate: {failures} template(s) failed")


def cmd_captions(args):
    pdir = resolve_project(args.project)
    language = getattr(args, "language", None)
    data, _sf, _pre = load_lenient(pdir)
    if data is None:
        fail("project could not be loaded")
    secondary_language = (data.get("settings") or {}).get("subtitle", {}).get("secondary_language")
    if language:
        secondary_language = None
    windows, _from_vendor = _line_windows(data, pdir)
    text_by_id = {int(line["id"]): (line.get("display_text") or line.get("text", "")) for line in data.get("script", [])}
    if language:
        missing = [line["id"] for line in data.get("script", []) if not (line.get("translations") or {}).get(language)]
        if missing:
            fail(f"language '{language}': lines missing translations: {missing}")
    secondary_by_id = {
        int(line["id"]): ((line.get("translations") or {}).get(secondary_language))
        for line in data.get("script", [])
    } if secondary_language else {}
    srt_lines, vtt_lines = [], []
    n = 0
    for line, start, end in windows:
        lid = int(line["id"])
        if lid not in text_by_id:
            continue
        n += 1
        pair = f"{_stamp(start, ',')} --> {_stamp(end, ',')}"
        cue_text = text_by_id[lid]
        sec = secondary_by_id.get(lid)
        if sec:
            cue_text = cue_text + "\n" + sec
        srt_lines.append(f"{n}\n{pair}\n{cue_text}\n")
        vtt_lines.append(f"{pair}\n{cue_text}\n\n")
    out_dir = pdir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f".{language}" if language else ""
    (out_dir / f"captions{suffix}.srt").write_text("\n".join(srt_lines), encoding="utf-8")
    (out_dir / f"captions{suffix}.vtt").write_text("WEBVTT\n\n" + "\n".join(vtt_lines), encoding="utf-8")
    log.info(
        "captions written: %s and %s (%d cues)%s",
        out_dir / f"captions{suffix}.srt", out_dir / f"captions{suffix}.vtt", n,
        " - rename to <video>.<lang>.srt for YouTube" if language else "",
    )


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


def _contact_sheet(mp4: Path, windows, out_png: Path, tmp: Path, total: float) -> None:
    """3-wide grid of frames sampled at each line midpoint."""
    from PIL import Image

    picks = windows[:9]
    frames = []
    for i, (line, start, end) in enumerate(picks):
        f = tmp / f"sheet{i}.png"
        if ffmpeg_frame(mp4, start + (end - start) * 0.6, total, f):
            frames.append(Image.open(f).convert("RGB"))
    if not frames:
        fail("contact sheet: no frames extracted")
    fw, fh = frames[0].size
    scale = 640 / fw
    tw, th = 640, int(fh * scale)
    cols = 3
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (10, 10, 10))
    for i, fr in enumerate(frames):
        fr = fr.resize((tw, th))
        sheet.paste(fr, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out_png)


def cmd_sheet(args):
    pdir = resolve_project(args.project)
    data, _sf, _pre = load_lenient(pdir)
    if data is None:
        fail("project could not be loaded")
    mp4 = pdir / "out" / "video.mp4"
    if not mp4.is_file():
        fail(f"no render at {mp4} - run wayang render first")
    total = float(ffprobe_json(mp4)["format"]["duration"])
    windows, _from_vendor = _line_windows(data, pdir)
    tmp = pdir / "out" / ".lint"
    tmp.mkdir(parents=True, exist_ok=True)
    _contact_sheet(mp4, windows, pdir / "out" / "contact-sheet.png", tmp, total)
    log.info("contact sheet: %s", pdir / "out" / "contact-sheet.png")


def _vendor_capabilities(vendor: str) -> dict:
    """Read vendors/<engine>/capabilities.yaml; empty dict when absent."""
    cap = paths.vendor_dir(vendor) / "capabilities.yaml"
    if not cap.is_file():
        return {}
    try:
        return yaml.safe_load(cap.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}


def cmd_lint(args):
    pdir = resolve_project(args.project)
    data = validate_project(pdir)
    mp4 = pdir / "out" / "video.mp4"
    if not mp4.is_file():
        fail(f"no render found at {mp4} - run wayang render first")
    lint_project(pdir, mp4, data)


def render_one(pdir: Path, skip_lint: bool = False, draft: bool = False, language: str | None = None) -> None:
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
    if language:
        missing = [line["id"] for line in data["script"]
                   if not (line.get("translations") or {}).get(language)]
        if missing:
            fail(f"language '{language}': lines missing translations: {missing}")
        for line in data["script"]:
            line["text"] = line["translations"][language]
        for c in data["characters"].values():
            override = (c.get("voice") or {}).get("languages") or {}
            override = override.get(language) or {}
            c["voice"] = {**c["voice"], **override}
    if draft:
        log.info("draft: skipping TTS (estimate timing, silent audio)")
    else:
        run_tts(pdir, data)
    vendor = data["meta"]["vendor"]
    build = paths.vendor_dir(vendor) / "build.sh"
    if not build.is_file():
        fail(f"vendor '{vendor}' has no build.sh (expected {build})" + ("" if paths.REPO_ROOT is not None else " - run: wayang setup"))
    out = pdir / "out"
    if language:
        (pdir / ".merged.yaml").write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
    log.info("rendering via vendor '%s' (language: %s)", vendor, language or "primary")
    draft_env = dict(os.environ)
    if draft:
        draft_env["WAYANG_DRAFT"] = "1"
    proc = subprocess.run(["bash", str(build), str(pdir), str(out)], check=False, env=draft_env)
    if proc.returncode != 0:
        fail(f"vendor build.sh exited {proc.returncode}")
    log.info("done: %s", out / "video.mp4")
    duration_guard(out, vendor)
    final_mp4 = out / "video.mp4"
    if language:
        final_mp4 = out / f"video-{language}.mp4"
        (out / "video.mp4").rename(final_mp4)
        log.info("language variant: %s", final_mp4)
    if not skip_lint:
        lint_project(pdir, final_mp4, data)


def cmd_render(args):
    pdir = resolve_project(args.project)
    targets = series_episodes(pdir) if is_series_dir(pdir) else [pdir]
    if len(targets) > 1:
        log.info(
            "series: %d episode(s): %s", len(targets), ", ".join(t.name for t in targets)
        )
    for ep in targets:
        render_one(ep, skip_lint=args.skip_lint, draft=args.draft, language=args.language)


def cmd_shorts_sample(args):
    pdir = resolve_project(args.project)
    video = Path(args.video) if args.video else pdir / "out" / "video.mp4"
    out_dir = Path(args.out) if args.out else pdir / "shorts" / "brief"
    sample_brief(video, out_dir, n_frames=args.frames, bin_seconds=args.bin)
    log.info("next: read the brief, then write %s (see docs/shorts.md)", pdir / "shorts" / "plan.yaml")


def cmd_shorts_render(args):
    pdir = resolve_project(args.project)
    plan_path = Path(args.plan) if args.plan else pdir / "shorts" / "plan.yaml"
    plan, _src = load_plan(plan_path)
    clips = plan["clips"]
    if args.clip:
        clips = [c for c in clips if c["id"] == args.clip]
        if not clips:
            fail(f"no clip id '{args.clip}' in the plan")
    clips_root = pdir / "shorts" / "clips"
    results = [render_clip(Path(plan["source"]), c, clips_root / c["id"], force=args.force) for c in clips]
    ok = sum(1 for r in results if r.get("ok"))
    log.info("shorts-render: %d/%d clip(s) verified under %s", ok, len(results), clips_root)
    if ok < len(results):
        raise SystemExit(1)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="wayang", description="Wayang CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("templates", help="list bundled templates")
    p.set_defaults(func=cmd_templates)

    p = sub.add_parser("init", help="scaffold a project from a template")
    p.add_argument("--preset", default="landscape", help="landscape | portrait | square")
    p.add_argument("template")
    p.add_argument("name")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("init-series", help="scaffold a series: series.yaml + first episode")
    p.add_argument("name")
    p.add_argument("--template", default="dialog")
    p.add_argument("--first-episode", default="ep01")
    p.set_defaults(func=cmd_init_series)

    p = sub.add_parser("check", help="friendly preflight: what to fill before rendering (guidance)")
    p.add_argument("project")
    p.add_argument("--json", action="store_true", help="machine-readable report")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("validate", help="strict gate: schema + references (blocks a bad render)")
    p.add_argument("project")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("tts", help="generate line voices via configured TTS engines")
    p.add_argument("project")
    p.add_argument("--force", action="store_true", help="regenerate even when cached")
    p.add_argument("--line", type=int, default=None, help="synthesize only this line id (preview)")
    p.set_defaults(func=cmd_tts)

    p = sub.add_parser("render", help="render a project via its vendor engine")
    p.add_argument("project")
    p.add_argument("--skip-lint", action="store_true", help="skip the post-render visibility lint")
    p.add_argument("--draft", action="store_true", help="fast low-quality preview render")
    p.add_argument("--language", help="render a translated variant (uses translations + per-language voices)")
    p.set_defaults(func=cmd_render)
    p = sub.add_parser("presets", help="list geometry presets (used by init --preset)")
    p.set_defaults(func=cmd_presets)

    p = sub.add_parser("check-templates", help="smoke gate: validate every bundled template")
    p.set_defaults(func=cmd_check_templates)

    p = sub.add_parser("captions", help="export SRT/VTT captions from the render timeline")
    p.add_argument("project")
    p.add_argument("--language", help="export captions for a language variant")
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
    p = sub.add_parser("sheet", help="review contact sheet from the rendered video")
    p.add_argument("project")
    p.set_defaults(func=cmd_sheet)
    p = sub.add_parser("lint", help="check a rendered video for invisible objects")
    p.add_argument("project")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("setup", help="deploy engines + shared assets to WAYANG_HOME (installed use)")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("doctor", help="report prerequisites: tools, TTS keys, engines")
    p.add_argument("--json", action="store_true", help="machine-readable report")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("shorts-sample", help="sample a rendered video into a shorts brief (frames + audio curve)")
    p.add_argument("project")
    p.add_argument("--video", help="source video (default: <project>/out/video.mp4)")
    p.add_argument("--out", help="brief dir (default: <project>/shorts/brief)")
    p.add_argument("--frames", type=int, default=12, help="brief frames to sample (default 12)")
    p.add_argument("--bin", type=float, default=1.0, help="audio curve bin seconds (default 1.0)")
    p.set_defaults(func=cmd_shorts_sample)

    p = sub.add_parser("shorts-render", help="cut + verify portrait clips from shorts/plan.yaml")
    p.add_argument("project")
    p.add_argument("--plan", help="plan file (default: <project>/shorts/plan.yaml)")
    p.add_argument("--clip", help="render a single clip id only")
    p.add_argument("--force", action="store_true", help="re-render even verified clips")
    p.set_defaults(func=cmd_shorts_render)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
