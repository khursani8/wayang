#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "jsonschema>=4.20"]
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
    src = ROOT / "templates" / args.template
    if not (src / "template.yaml").is_file():
        fail(f"unknown template: {args.template}")
    dst = ROOT / "projects" / args.name
    if dst.exists():
        fail(f"projects/{args.name} already exists")
    shutil.copytree(src, dst)
    (dst / "template.yaml").rename(dst / "project.yaml")
    log.info(
        "created projects/%s - edit project.yaml, then: uv run tools/ce.py validate projects/%s",
        args.name,
        args.name,
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
        if c["voice"]["engine"] != "voicevox":
            fail(f"character {cid}: unsupported voice engine '{c['voice']['engine']}'")
        img = c.get("image")
        if img and not (pdir / img).is_file():
            fail(f"character {cid}: image missing: {img}")
    vendor = data["meta"]["vendor"]
    build = ROOT / "vendors" / vendor / "build.sh"
    if not build.is_file():
        fail(f"vendor '{vendor}' has no build.sh (expected {build})")
    return data


def cmd_validate(args):
    resolve_project(args.project)
    validate_project(resolve_project(args.project))


def cmd_render(args):
    pdir = resolve_project(args.project)
    data = validate_project(pdir)
    vendor = data["meta"]["vendor"]
    build = ROOT / "vendors" / vendor / "build.sh"
    out = pdir / "out"
    log.info("rendering via vendor '%s'", vendor)
    proc = subprocess.run(["bash", str(build), str(pdir), str(out)], check=False)
    if proc.returncode != 0:
        fail(f"vendor build.sh exited {proc.returncode}")
    log.info("done: %s", out / "video.mp4")


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

    p = sub.add_parser("render", help="render a project via its vendor")
    p.add_argument("project")
    p.set_defaults(func=cmd_render)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
