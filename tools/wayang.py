#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "jsonschema>=4.20", "pillow>=10.0"]
# ///
"""Repo dev entry: run the packaged CLI against repo resources.

Keeps every in-repo command working: uv run tools/wayang.py <command>.
Resources (templates/schema/backgrounds/vendors) resolve from the repo tree,
so in-repo edits apply without repackaging.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from wayang import paths

paths.REPO_ROOT = REPO

from wayang.cli import main

if __name__ == "__main__":
    main()
