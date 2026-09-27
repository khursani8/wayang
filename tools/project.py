"""Shared project loading for Wayang.

Series inheritance lives here so every consumer (check, validate, render,
lint) merges identically: series.yaml is a sparse base, the episode wins
per key, dicts recurse, lists and scalars replace.
"""
from pathlib import Path

import yaml


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


def load_lenient(pdir: Path):
    """Returns (data_or_None, series_file_or_None, issues).

    Lenient loading for the preflight: parse errors and missing series
    files come back as issues instead of raising.
    """
    issues = []
    data = None
    pf = pdir / "project.yaml"
    if not pf.is_file():
        issues.append(f"{pf} missing")
        return None, None, issues
    try:
        data = yaml.safe_load(pf.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        issues.append(f"project.yaml parse error: {e}")
        return None, None, issues
    if not isinstance(data, dict):
        issues.append("project.yaml must be a mapping")
        return None, None, issues
    series_file = find_series_file(pdir)
    if series_file is not None:
        try:
            series = yaml.safe_load(series_file.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            issues.append(f"series config parse error ({series_file}): {e}")
            return None, series_file, issues
        if not isinstance(series, dict):
            issues.append(f"series config must be a mapping: {series_file}")
            return None, series_file, issues
        shared = len((series.get("characters") or {}).keys())
        data = deep_merge(series, data)
        logging = __import__("logging")
        logging.getLogger("ce").info(
            "merged series config %s (%d shared character(s))", series_file, shared
        )
    return data, series_file, issues
