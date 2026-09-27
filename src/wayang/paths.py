"""Resource resolution for Wayang.

Two run modes:
- repo dev: tools/wayang.py sets paths.REPO_ROOT; every resource is read from
  the repo tree, so in-repo edits apply without repackaging.
- installed: templates/schema/backgrounds/engine sources come from package
  data; engines deploy to WAYANG_HOME (env WAYANG_HOME > ~/.wayang) via
  `wayang setup`, and vendor mappers read WAYANG_HOME/assets/backgrounds.

User projects always resolve against the current working directory.
"""
from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

# Set only by the repo shim (tools/wayang.py). When set, every resource
# resolves inside the repo instead of package data / WAYANG_HOME.
REPO_ROOT: Path | None = None


def wayang_home() -> Path:
    """Platform home for deployed engines and shared assets."""
    env = os.environ.get("WAYANG_HOME")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".wayang"


def _pkg_dir(*parts: str) -> Path:
    """Path into bundled package data.

    Wheels install unpacked on disk, so the traversable is a real directory.
    Zip installs are unsupported by design (npm/npx engines need real files).
    """
    p = Path(str(resources.files("wayang.packages").joinpath(*parts)))
    if not p.is_dir():
        raise RuntimeError(f"package data missing: wayang.packages/{'/'.join(parts)} at {p}")
    return p


def templates_dir() -> Path:
    if REPO_ROOT is not None:
        return REPO_ROOT / "templates"
    return _pkg_dir("templates")


def schema_path() -> Path:
    if REPO_ROOT is not None:
        return REPO_ROOT / "schema" / "project.schema.json"
    return _pkg_dir("schema", "project.schema.json")


def backgrounds_dir() -> Path:
    if REPO_ROOT is not None:
        return REPO_ROOT / "assets" / "backgrounds"
    return _pkg_dir("backgrounds")


def vendors_root() -> Path:
    """Where engines are looked up: the repo in dev, WAYANG_HOME when installed."""
    if REPO_ROOT is not None:
        return REPO_ROOT / "vendors"
    return wayang_home() / "vendors"


def vendor_dir(engine: str) -> Path:
    return vendors_root() / engine


def bundled_vendors_dir() -> Path:
    """Source of engine trees for setup: repo vendors in dev, package data otherwise."""
    if REPO_ROOT is not None:
        return REPO_ROOT / "vendors"
    return _pkg_dir("vendors")


def known_engines() -> list[str]:
    root = vendors_root()
    if root.is_dir():
        return sorted(d.name for d in root.iterdir() if (d / "build.sh").is_file())
    return []


def bundled_engines() -> list[str]:
    """Engine names available for setup/doctor (repo trees or package data)."""
    root = bundled_vendors_dir()
    if root.is_dir():
        return sorted(d.name for d in root.iterdir() if (d / "build.sh").is_file())
    return []
