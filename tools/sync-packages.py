#!/usr/bin/env python3
"""Refresh src/wayang/packages/ (wheel runtime data) from the live repo.

The wheel ships src/wayang/packages as package data; paths.py resolves
templates, schema, backgrounds, vendors and mascots/frames from it in
installed mode. This tool rebuilds that copy so `uv tool install` yields
a working installed CLI:

    uv run tools/sync-packages.py

Synced targets (each replaced wholesale):
    templates/                  <- templates/
    schema/project.schema.json  <- schema/project.schema.json
    backgrounds/                <- assets/backgrounds/*.png
    mascots/frames/             <- assets/mascots/frames/
    vendors/                    <- vendors/ minus junk subtrees

node_modules, .work, dist, __pycache__, .git, .omc and .ruff_cache
directories are pruned
during the copy so dev engine trees (multi-GB) never enter the wheel.

Replace strategy: copy into <target>.tmp-sync beside the target, then
remove the old subtree and rename the new one in (a plain rm+rename
swap, not a cross-filesystem os.replace). Idempotent: rerunning
rebuilds the same content.
"""

from __future__ import annotations

import logging
import os
import shutil
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger("sync_packages")

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "src" / "wayang" / "packages"

PRUNED_DIRS = {
    "node_modules",
    ".work",
    "dist",
    "__pycache__",
    ".git",
    ".omc",
    ".ruff_cache",
}


def _prune_junk(_directory: str, names: list[str]) -> list[str]:
    """shutil.copytree ignore hook: drop junk dirs anywhere in the tree."""
    return [n for n in names if n in PRUNED_DIRS]


def _png_only(_directory: str, names: list[str]) -> list[str]:
    """shutil.copytree ignore hook: keep *.png entries, drop the rest."""
    return [n for n in names if Path(n).suffix != ".png"]


def _tree_stats(root: Path) -> tuple[int, int]:
    files = [p for p in root.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def sync_dir(
    src: Path,
    target: Path,
    ignore: Callable[[str, list[str]], list[str]] | None = None,
) -> tuple[int, int]:
    """Replace target subtree with a pruned copy of src; return (files, bytes)."""
    if not src.is_dir():
        raise SystemExit(f"sync-packages: source missing: {src}")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.parent / (target.name + ".tmp-sync")
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(src, tmp, ignore=ignore)
    nfiles, nbytes = _tree_stats(tmp)
    if nfiles == 0:
        shutil.rmtree(tmp)
        raise SystemExit(f"sync-packages: source empty after filters: {src}")
    if target.exists():
        shutil.rmtree(target)
    tmp.rename(target)
    return nfiles, nbytes


def sync_file(src: Path, target: Path) -> tuple[int, int]:
    """Atomically replace one file; return (files, bytes)."""
    if not src.is_file():
        raise SystemExit(f"sync-packages: source missing: {src}")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp-sync")
    shutil.copy2(src, tmp)
    os.replace(tmp, target)
    return 1, target.stat().st_size


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not PKG.is_dir():
        logger.error("package data dir missing: %s", PKG)
        return 1
    results = [
        (
            "templates",
            *sync_dir(REPO / "templates", PKG / "templates", ignore=_prune_junk),
        ),
        (
            "schema/project.schema.json",
            *sync_file(
                REPO / "schema" / "project.schema.json",
                PKG / "schema" / "project.schema.json",
            ),
        ),
        (
            "backgrounds",
            *sync_dir(
                REPO / "assets" / "backgrounds", PKG / "backgrounds", ignore=_png_only
            ),
        ),
        (
            "mascots/frames",
            *sync_dir(
                REPO / "assets" / "mascots" / "frames",
                PKG / "mascots" / "frames",
                ignore=_prune_junk,
            ),
        ),
        ("vendors", *sync_dir(REPO / "vendors", PKG / "vendors", ignore=_prune_junk)),
    ]
    logger.info("synced src/wayang/packages/:")
    for label, nfiles, nbytes in results:
        logger.info("  %-24s %5d file(s)  %12d byte(s)", label, nfiles, nbytes)
    logger.info(
        "  %-24s %5d file(s)  %12d byte(s)",
        "TOTAL",
        sum(r[1] for r in results),
        sum(r[2] for r in results),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
