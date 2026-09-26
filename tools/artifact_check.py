#!/usr/bin/env python3
"""Independent artifact check (s55 w1).

Closes audit-39's usefulness-decade-1 residual: recorded verdicts establish
what evaluators wrote; they do not independently establish implementation
correctness. This tool re-verifies a named season's landed ships from
artifacts alone:

    python tools/artifact_check.py <sid> <close-commit> [--repo REPO]
                                                   [--out-dir DIR]

1. EXTRACT   git archive the close commit into a temp tree. The live tree
   is never touched (no checkout).
2. PINS      discover the season's merged pins (tests/test_<sid>_*.py) in
   the extracted tree and run them with the repo venv's python, PYTHONPATH
   bound to the extracted src. A resolution probe first proves the import
   resolves into the extracted tree, not the live one.
3. DIGESTS   recompute every claimed pack digest in the extracted tree
   (.rumpun/plugins.yml records vs an independent sha256 over the pack's
   priors/ tree, the s47 convention: sorted pack-relative POSIX paths,
   NUL separators, no trailing separator; empty tree = sha256 of empty
   input) and the season's harvest-record seal (sha256 over the record
   body, lines[4:-1], the akar.append_record convention). plugins.yml is
   read with a minimal indentation-based parser for the yaml.safe_dump
   layout (mapping -> pack name -> scalar leaves); any other shape is a
   structural refusal naming the registry.
4. SHIPS     diff the DESIGN.md ships row for <sid> against the tree:
   split into named-ship clauses (paren-aware), extract checkable claims,
   and judge each clause:
    file claim    a <path>.<suffix> token named in the clause must exist in
   the extracted tree (resolved from the tree root, then src/rumpun/,
   tools/, tests/) -- a committed-tree claim, unless runtime-framed (see
   runtime file). The classification of every file-shaped token is
   recorded in the clause evidence.
    runtime file  a file token framed as run-time output ("writes <token>",
   a runs/<sid>/ path prefix, or a close-time cue -- "at close",
   "close-time", "on close" -- in the token's top-level segment) checks
   the campaign's live runs state instead of the extracted tree:
   repo/.rumpun/runs/<sid>/, where a runs/<sid>/-prefixed or path-shaped
   token resolves below the dir and a bare token binds at the runs root
   (the finalize's output; never scratch depth). When the runs state does
   not hold the artifact but the extracted tree does (early seasons
   committed their ledger state), the claim binds committed and the
   fallback is named in the evidence. The framing is never a bailout: a
   runtime artifact absent from the runs state and the tree DELTAs
   exactly like a missing committed file.
    key tokens    lowercase word+colon tokens ("writers:", "benih:")
   searched verbatim in the tree's src/; the status and first hit are
   recorded. A colon-form miss falls back to the bare word.
    slash tokens  path-shaped tokens without a file suffix
   ("lint/engine/evolve", "musim/"): when every component resolves to a
   module file under src/rumpun/ the clause's key tokens are searched
   inside those files; otherwise the token's last component is searched
   verbatim. When the clause carries a removal marker ("was a", "dead
   path", "found and fixed", "removed", "no longer", "retired",
   "superseded", "renamed away") the legacy token's presence is recorded
   as evidence with its locations: rename back-compat keeps legacy names by
   design, so the removal claim itself is judged by the season's pins.
   Pure-numeric slash tokens ("243/243") are metrics, not surfaces.
    pins claim    "N pins" vs the pytest collected count (binding).
    suite claim   "suite N/M" is recorded verbatim and NOT re-run (the
   season's pins are the check's execution surface; a full extracted-tree
   suite rerun is a future flag).

   close-time fallback (s59): a close's own DESIGN entry postdates the
   commit being checked (the s57 refusal fired live at the s57 close), so
   when the extracted DESIGN.md has no row for <sid> but the live worktree
   DESIGN.md has one, the checker uses the live row and records the fact
   in the check record. The fallback covers ONLY the missing fresh row:
   every other artifact (files, digests, seals) binds to the extracted
   tree exactly as before, so a tampered close still yields DELTA exit 1.

   Per-clause verdict:
    DELTA  a named committed file or runtime artifact is missing, or every
   surface token absent with no removal marker, or the pins count
   disagrees.
    MATCH  all checkable claims hold. A clause with no machine-checkable
   claims is MATCH-by-prose, recorded verbatim; it is judged by the pins.

5. RECORD    a check-<sid> ledger record (the akar.append_record layout:
   header, body, sha256 trailer over the utf-8 body bytes), written
   atomically to --out-dir (default: the live ledger .rumpun/ledger).
   Append-only: an existing check-<sid> file is refused. The record
   carries: the exact commands run, the pins outcome in the extracted
   tree, the digest comparisons, the ships-row diff (each row MATCH or
   the named delta), and the honest verdict line.

Verdict line in the record and exit code:

    VERIFIED  pins green in the extracted tree, every ships clause MATCH
   or MATCH-by-prose, every digest recomputed equal.
    DELTA     any pins failure, ships DELTA, or digest mismatch (exit 1;
   the deltas are named in the record).
    structural refusal: missing close commit, unknown season id (no ships
   row in the extracted DESIGN.md), no pins file, no tests collected, the
   import probe failing to resolve into the extracted tree, or the venv
   python absent with a fallback python that cannot import pytest (issue
   #40) -- exit 2, naming the cause.
    skip: the season ships no pins lane and the ships row claims no pins
   (a legitimate pinless close) -- exit 0 with the named skip line, no
   record; a claimed-pins season with no pins file stays a structural
   refusal (a real delta). An extract with no src/ (issue #39) takes the
   same named skip: a docs-only repo has no package for the pins lane to
   import; exit 0, no record, the line names the missing src/.

stdlib only; logging, never print; git via subprocess, archive only.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import logging
import os
import re
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
from pathlib import Path

logger = logging.getLogger("artifact_check")

PINS_TIMEOUT_S = 240
GIT_TIMEOUT_S = 30
PROBE_TIMEOUT_S = 60

FILE_TOKEN_RE = re.compile(r"(?:[\w.-]+/)*[\w.-]+\.(?:py|md|yaml|yml|jsonl|toml)\b")
KEY_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9_]*:")
SLASH_TOKEN_RE = re.compile(r"(?:[\w.-]+/)+[\w.-]*")
PINS_CLAIM_RE = re.compile(r"\b(\d+) pins\b")
SUITE_CLAIM_RE = re.compile(r"\bsuite (\d+)/(\d+)\b")
REMOVAL_MARKERS: tuple[str, ...] = (
    "was a", "dead path", "found and fixed", "removed", "no longer",
    "retired", "superseded", "renamed away",
)

CLOSE_TIME_CUE_RE = re.compile(r"\b(?:close-time|at close|on close)\b")

LIVE_ROW_NOTE = (
    "ships row read from the live worktree"
    " (the close's own entry postdates the commit)"
)

NO_DESIGN_NOTE = (
    "ships row unchecked: the extract carries no DESIGN.md"
    " convention; pins, pack digests, and seals still bind"
)

MODULE_DIR = "src/rumpun"

@dataclass
class Surface:
    """One searched token and where the search found it (or not)."""

    token: str
    present: bool
    where: str = ""


@dataclass
class FileClaim:
    """One file-shaped token: its classification and where it bound."""

    token: str
    kind: str  # "committed" | "runtime" | "runtime-committed-fallback"
    present: bool
    where: str = ""


@dataclass
class ShipClause:
    """One named-ship clause and the verdict of its claims."""

    text: str
    files: list[str] = field(default_factory=list)
    file_claims: list[FileClaim] = field(default_factory=list)
    surfaces: list[Surface] = field(default_factory=list)
    verdict: str = "MATCH"
    notes: list[str] = field(default_factory=list)


@dataclass
class CheckResult:
    """Everything the record body renders from."""

    sid: str
    commit: str
    outcome: str
    n_extracted: int = 0
    commands: list[str] = field(default_factory=list)
    pins: dict[str, str] = field(default_factory=dict)
    packs: list[tuple[str, str, str, str]] = field(default_factory=list)
    seals: list[tuple[str, str, str]] = field(default_factory=list)
    ships_verbatim: str = ""
    ships_source: str = ""
    clauses: list[ShipClause] = field(default_factory=list)
    suite_claim: str = ""
    verdict: str = ""
    delta_reasons: list[str] = field(default_factory=list)

def find_repo_root(start: Path) -> Path:
    """First ancestor holding the campaign state or the engine source.

    Consumer campaigns (issue #28) run this checker inside their own
    repo: the campaign root holds .rumpun/ and no src/rumpun. Engine
    repo runs keep the src/rumpun marker. Either marker resolves the
    repo the check runs against (git history, venv, ledger).
    """
    for candidate in (start, *start.parents):
        if (candidate / ".rumpun").is_dir() or (candidate / "src" / "rumpun").is_dir():
            return candidate
    msg = f"no ancestor of {start} contains .rumpun or src/rumpun"
    raise SystemExit(msg)


def venv_python(repo: Path) -> str:
    """The repo venv's python when present, else the current interpreter.

    The fallback is probed before use (issue #40): a python that cannot
    import pytest is refused (exit 2) naming the gap. Silently running
    the pins lane under it dies "No module named pytest" exit 1 on green
    trees. The venv python is returned unprobed: repos with a real venv
    are byte-unchanged.
    """
    candidate = repo / ".venv" / "bin" / "python"
    if candidate.is_file():
        return str(candidate)
    probe = subprocess.run(
        [sys.executable, "-c", "import pytest"], capture_output=True, text=True,
        check=False,
    )
    if probe.returncode != 0:
        tail = probe.stderr.strip().splitlines()[-1] if probe.stderr.strip() else ""
        logger.error(
            "no python with pytest: %s absent and the fallback %s cannot"
            " import pytest (%s)",
            candidate, sys.executable, tail,
        )
        raise SystemExit(2)
    return sys.executable


def git_capture(args, repo, text=True):
    """One git command under GIT_TIMEOUT_S; captured streams."""
    argv = ["git", "-C", str(repo), *args]
    try:
        proc = subprocess.Popen(
            argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text,
        )
    except OSError as exc:
        logger.error("git unavailable: %s", exc)
        raise
    try:
        out, err = proc.communicate(timeout=GIT_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        msg = f"git timed out: {' '.join(argv)}"
        raise RuntimeError(msg) from None
    return proc.returncode, out, err


def git_or_die(args, repo, text=True):
    """git_capture that exits 2 on failure, naming the command."""
    code, out, err = git_capture(args, repo, text=text)
    if code != 0:
        tail = err.decode("utf-8", "replace") if isinstance(err, bytes) else err
        logger.error("git %s failed (exit %d): %s", " ".join(args), code, tail.strip()[:300])
        raise SystemExit(2)
    return out

def extract_commit(repo, commit, tree):
    """git archive COMMIT into the temp tree; returns the file count. The
    archive bytes unpack through tarfile in-process: no shell pipeline, so
    the git exit code cannot be eaten by a pipe (the s25 lesson).
    """
    started = time.monotonic()
    raw = git_or_die(["archive", str(commit)], repo, text=False)
    assert isinstance(raw, bytes)
    n = 0
    with tarfile.open(fileobj=BytesIO(raw), mode="r:") as tar:
        try:
            tar.extractall(tree, filter="data")
        except TypeError:  # pre-3.12 pythons: no filter kwarg
            tar.extractall(tree)
        n = sum(1 for p in tree.rglob("*") if p.is_file())
    logger.info("extracted %s -> %s (%d files)", str(commit)[:12], tree, n)
    logger.debug("extraction took %.1fs", time.monotonic() - started)
    return n


def read_text(path):
    """Read a text artifact; unreadable is a structural refusal (exit 2)."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.error("unreadable artifact %s: %s", path, exc)
        raise SystemExit(2) from None


def _row_lines(text, sid):
    """The raw `| <sid> | outcome | ships |` row lines of a DESIGN.md text."""
    pattern = re.compile(rf"\| {re.escape(sid)} \|.*\|.*\|")
    return [line for line in text.splitlines() if pattern.fullmatch(line.strip())]


def ships_row(design, sid, live_path=None):
    """The outcome and ships cells of <sid>'s DESIGN.md row, plus the row
    source: "" for the extracted row, LIVE_ROW_NOTE when the close-time
    fallback fired.

    A row is | <sid> | outcome | ships |. Zero rows: unknown season id.
    Several rows: the LAST (newest section), with a logged note. Zero
    extracted rows with live_path set: the close-time fallback -- the
    close's own entry postdates the commit (the s57 refusal), so the live
    worktree's row is used when it has one. The fallback covers ONLY the
    missing fresh row; files, digests, and seals keep binding to the
    extracted tree. live_path is read lazily: only when the extracted
    rows are empty.
    """
    rows = _row_lines(design, sid)
    note = ""
    if not rows and live_path is not None and live_path.is_file():
        live_rows = _row_lines(read_text(live_path), sid)
        if live_rows:
            rows = live_rows
            note = LIVE_ROW_NOTE
            logger.warning("season %s: %s", sid, LIVE_ROW_NOTE)
    if not rows:
        where = (
            "extracted nor live DESIGN.md"
            if live_path is not None
            else "extracted DESIGN.md"
        )
        msg = f"no ships row for {sid} in the {where} (unknown season id?)"
        logger.error(msg)
        raise SystemExit(2)
    if len(rows) > 1:
        logger.warning("%d ships rows for %s; using the last", len(rows), sid)
    cells = [c.strip() for c in rows[-1].strip().strip("|").split("|")]
    if len(cells) != 3:
        msg = f"ships-row parse error for {sid}: {rows[-1][:80]}"
        logger.error(msg)
        raise SystemExit(2)
    return cells[1], cells[2], note


def split_clauses(cell):
    """Top-level comma/semicolon splits; commas inside parens survive."""
    clauses = []
    depth = 0
    start = 0
    for i, ch in enumerate(cell):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch in ",;" and depth == 0:
            clauses.append(cell[start:i].strip())
            start = i + 1
    tail = cell[start:].strip()
    if tail:
        clauses.append(tail)
    return [c for c in clauses if c]

def resolve_file(tree, token):
    """A named file claim resolved against the extracted tree."""
    for rel in (token, f"{MODULE_DIR}/{token}", f"tools/{token}", f"tests/{token}"):
        if (tree / rel).is_file():
            return tree / rel
    return None


def search_files(tree, paths, token):
    """Search token verbatim in the given files; the first hit wins."""
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.warning("unreadable during surface search: %s", exc)
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if token in line:
                rel = path.relative_to(tree)
                return Surface(token, True, f"{rel}:{lineno}")
    return Surface(token, False, "")


def search_tree(tree, token):
    """Search token verbatim across the tree's src/ *.py files."""
    src = tree / "src"
    hits = sorted(src.rglob("*.py")) if src.is_dir() else []
    return search_files(tree, hits, token)


def _segment_bounds(text, pos):
    """The top-level (paren-depth-0) comma/semicolon segment around pos."""
    depth = 0
    start = 0
    for i, ch in enumerate(text[:pos]):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch in ",;" and depth == 0:
            start = i + 1
    end = len(text)
    depth = 0
    for i in range(pos, len(text)):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch in ",;" and depth == 0:
            end = i
            break
    return start, end


def runtime_framed(text, pos, token, sid):
    """Is the file-shaped token framed as run-time output?

    Runtime framings (the s61 false positive: "the engine's finalize
    writes results.jsonl"): the clause writes the token ("writes
    <token>"), the token path carries the runs/<sid>/ prefix, or the
    token's top-level segment carries a close-time cue.
    """
    if re.search(rf"\b(?:writes?|emits?)\s+{re.escape(token)}\b", text):
        return True
    if token.startswith(f"runs/{sid}/"):
        return True
    start, end = _segment_bounds(text, pos)
    return CLOSE_TIME_CUE_RE.search(text[start:end]) is not None


def resolve_runtime(runs_dir, token):
    """A runtime-framed token resolved against the live runs state.

    Returns (path, why): path is the artifact found under runs_dir (None
    when the claim does not hold), why names the reason when None. A
    runs/<sid>/-prefixed or path-shaped token resolves below runs_dir; a
    bare token binds at the runs root (the finalize's output), never at
    scratch depth.
    """
    if runs_dir is None:
        return None, "no runs state bound to the check"
    if not runs_dir.is_dir():
        return None, f"runs state {runs_dir} absent"
    rel = token
    prefix = f"runs/{runs_dir.name}/"
    if token.startswith(prefix):
        rel = token[len(prefix):]
    direct = runs_dir / rel
    if direct.is_file():
        return direct, ""
    return None, ""


def analyze_clause(text, tree, pins_collected, sid="", runs_dir=None):
    """Extract and judge one named-ship clause's checkable claims.

    runs_dir (the live repo/.rumpun/runs/<sid>/) enables the runtime-vs-
    committed file-claim classification; None binds every file token to
    the extracted tree exactly as before s63.
    """
    clause = ShipClause(text=text)
    lower = text.lower()
    removal = any(marker in lower for marker in REMOVAL_MARKERS)

    file_spans = [
        (m.start(), m.end(), m.group(0)) for m in FILE_TOKEN_RE.finditer(text)
    ]
    key_tokens = [
        m.group(0) for m in KEY_TOKEN_RE.finditer(text)
        if not any(fs <= m.start() < fe for fs, fe, _ in file_spans)
    ]
    slash_tokens = [
        m.group(0) for m in SLASH_TOKEN_RE.finditer(text)
        if not any(fs <= m.start() < fe for fs, fe, _ in file_spans)
    ]
    for start, _, token in file_spans:
        if runs_dir is not None and runtime_framed(text, start, token, sid):
            path, why = resolve_runtime(runs_dir, token)
            if path is not None:
                clause.file_claims.append(
                    FileClaim(
                        token, "runtime", True,
                        f"runs/{runs_dir.name}/{path.relative_to(runs_dir).as_posix()}",
                    )
                )
                continue
            resolved = resolve_file(tree, token)
            if resolved is not None:
                rel = resolved.relative_to(tree).as_posix()
                clause.files.append(rel)
                clause.file_claims.append(
                    FileClaim(token, "runtime-committed-fallback", True, rel)
                )
                clause.notes.append(
                    f"{token}: absent from runs/{runs_dir.name}/, bound committed"
                    " (committed-tree fallback)"
                )
                continue
            if re.search(rf"\bemits?\s+{re.escape(token)}\b", text):
                emit_site = search_tree(tree, token.rsplit("/", 1)[-1])
                if emit_site.present:
                    clause.file_claims.append(
                        FileClaim(
                            token, "runtime", True,
                            f"emit site: {emit_site.where}",
                        )
                    )
                    clause.notes.append(
                        f"{token}: emit-framed; the emit site is present in"
                        " src; the path lands in scaffolded campaigns (not"
                        " re-run)"
                    )
                    continue
            clause.verdict = "DELTA"
            note = f"missing runtime artifact: {token}"
            if why:
                note = f"{note} ({why})"
            clause.notes.append(note)
            clause.file_claims.append(FileClaim(token, "runtime", False, ""))
            continue
        resolved = resolve_file(tree, token)
        if resolved is None:
            clause.verdict = "DELTA"
            clause.notes.append(f"missing file: {token}")
            clause.file_claims.append(FileClaim(token, "committed", False, ""))
        else:
            rel = resolved.relative_to(tree).as_posix()
            clause.files.append(rel)
            clause.file_claims.append(FileClaim(token, "committed", True, rel))
    for token in key_tokens:
        surface = search_tree(tree, token)
        if not surface.present:
            surface = search_tree(tree, token.rstrip(":"))
        clause.surfaces.append(surface)
    for token in slash_tokens:
        comps = [c for c in token.strip("/").split("/") if c]
        module_paths = [resolve_file(tree, f"{c}.py") for c in comps]
        if any(c.isdigit() for c in comps):
            clause.notes.append(f"{token}: metric token, not a surface")
            continue
        if comps and all(p is not None for p in module_paths):
            rels = ", ".join(p.relative_to(tree).as_posix() for p in module_paths)
            clause.surfaces.append(Surface(token, True, f"module reading: {rels}"))
            for kt in key_tokens:
                surface = search_files(tree, module_paths, kt)
                if not surface.present:
                    surface = search_files(tree, module_paths, kt.rstrip(":"))
                clause.surfaces.append(surface)
            continue
        rel_token = token.strip("/")
        if (
            rel_token
            and token.count("/") == 1
            and all("." not in c for c in comps)
            and not (tree / rel_token).exists()
        ):
            clause.notes.append(
                f"{token}: external reference, not a tree surface"
            )
            continue
        if rel_token and (tree / rel_token).exists():
            clause.surfaces.append(
                Surface(token, True, f"committed path: {rel_token}")
            )
            continue
        probe = comps[-1] if comps else token
        surface = search_tree(tree, probe)
        clause.surfaces.append(surface)
        if not surface.present and removal:
            clause.notes.append(f"{token}: absent, consistent with the removal claim")
        elif surface.present and removal:
            clause.notes.append(
                f"{token}: legacy token still in src (evidence; the removal"
                " claim itself is judged by the pins)"
            )
        elif not surface.present and not any(s.present for s in clause.surfaces):
            clause.verdict = "DELTA"
            clause.notes.append(f"no named surface found for: {token}")
    m_pins = PINS_CLAIM_RE.search(text)
    if m_pins is not None and pins_collected is not None:
        claimed = int(m_pins.group(1))
        if claimed == pins_collected:
            clause.notes.append(f"pins claim {claimed} == collected {pins_collected}")
        else:
            clause.verdict = "DELTA"
            clause.notes.append(f"claims {claimed} pins, tree carries {pins_collected}")
    m_suite = SUITE_CLAIM_RE.search(text)
    if m_suite is not None:
        clause.notes.append(
            f"suite claim {m_suite.group(1)}/{m_suite.group(2)} recorded, not re-run"
        )
    if (
        clause.verdict == "MATCH"
        and clause.surfaces
        and not any(s.present for s in clause.surfaces)
        and not removal
    ):
        clause.verdict = "DELTA"
        clause.notes.append("every named surface token absent from the tree")
    return clause

def run_pins(tree, pin_files, python):
    """The season's pins under the repo venv, PYTHONPATH bound to the tree.

    A resolution probe runs first: it must resolve rumpun inside the
    extracted tree; anything else is a structural refusal (exit 2).
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree / "src")
    started = time.monotonic()
    probe_argv = [python, "-c", "import rumpun; print(rumpun.__file__)"]
    try:
        probe = subprocess.run(
            probe_argv, cwd=str(tree), env=env, capture_output=True, text=True,
            timeout=PROBE_TIMEOUT_S, check=False,
        )
    except subprocess.TimeoutExpired:
        logger.error("import probe timed out after %ds", PROBE_TIMEOUT_S)
        raise SystemExit(2) from None
    resolved = probe.stdout.strip()
    src_prefix = str(tree / "src")
    if probe.returncode != 0 or not resolved.startswith(src_prefix):
        logger.error(
            "import probe failed: exit %d, resolved %r (want prefix %s)",
            probe.returncode, resolved or probe.stderr.strip()[:200], src_prefix,
        )
        raise SystemExit(2)
    argv = [
        python, "-m", "pytest",
        *(str(p) for p in pin_files), "-q", "-p", "no:cacheprovider",
    ]
    proc = subprocess.Popen(
        argv, cwd=str(tree), env=env, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, start_new_session=True,
    )
    try:
        out, _ = proc.communicate(timeout=PINS_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)
        out, _ = proc.communicate()
        logger.error("pins run exceeded %ds; process group killed", PINS_TIMEOUT_S)
        return {
            "exit": "timeout", "probe": resolved,
            "collected": 0, "passed": 0, "failed": 0, "errors": 0,
            "duration": f"{time.monotonic() - started:.1f}s",
        }
    passed = re.search(r"(\d+) passed", out)
    failed = re.search(r"(\d+) failed", out)
    errors = re.search(r"(\d+) error", out)
    skipped = re.search(r"(\d+) skipped", out)
    info = {
        "exit": str(proc.returncode),
        "probe": resolved,
        "collected": sum(
            int(m.group(1)) for m in (passed, failed, errors, skipped) if m
        ),
        "passed": int(passed.group(1)) if passed else 0,
        "failed": int(failed.group(1)) if failed else 0,
        "errors": int(errors.group(1)) if errors else 0,
        "duration": f"{time.monotonic() - started:.1f}s",
        "summary": (out.strip().splitlines()[-1] if out.strip() else "")[:200],
    }
    if proc.returncode in (2, 4, 5):
        logger.error(
            "pins did not collect (pytest exit %d): %s (%s)",
            proc.returncode, [p.name for p in pin_files], info["summary"],
        )
        raise SystemExit(2)
    return info

def recompute_pack_digest(pack_dir):
    """The s47 convention, computed independently of rumpun.plugin: sha256
    over the pack's priors/ tree (sorted pack-relative POSIX paths, NUL
    separators, no trailing separator; empty or missing tree = sha256 of
    empty input)."""
    digest = hashlib.sha256()
    priors = pack_dir / "priors"
    if priors.is_dir():
        for path in sorted(p for p in priors.rglob("*") if p.is_file()):
            digest.update(path.relative_to(pack_dir).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def parse_registry(text, reg_path):
    """Minimal indentation-based read of the yaml.safe_dump layout:
    'plugins:' -> two-space '<name>:' -> four-space '<key>: <value>'.
    Any other shape is a structural refusal naming the registry."""
    plugins = {}
    current = None
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if lineno == 1 and line == "plugins:":
            current = None
            continue
        m_pack = re.fullmatch(r"  (\S.*):\s*", line)
        m_leaf = re.fullmatch(r"    (\S+): (.*)", line)
        if m_leaf and current is not None:
            plugins[current][m_leaf.group(1)] = m_leaf.group(2).strip()
        elif m_pack and current is None:
            current = m_pack.group(1)
            plugins[current] = {}
        else:
            msg = f"{reg_path}:{lineno}: unexpected registry line shape: {line[:60]}"
            logger.error(msg)
            raise SystemExit(2)
    return plugins


def digest_packs(tree):
    """Claimed pack digests vs recomputed; ([], note) when no registry."""
    reg = tree / ".rumpun" / "plugins.yml"
    if not reg.is_file():
        note = "no .rumpun/plugins.yml in the extracted tree (no pack digest claims)"
        return [], note
    plugins = parse_registry(read_text(reg), reg)
    rows = []
    for name in sorted(plugins):
        claimed = plugins[name].get("digest", "")
        pack_dir = tree / ".rumpun" / "plugins" / name
        recomputed = recompute_pack_digest(pack_dir)
        status = "MATCH" if claimed == recomputed else "DELTA"
        rows.append((name, str(claimed), recomputed, status))
    note = f"{len(rows)} pack record(s) re-digested from plugins.yml"
    return rows, note

def seal_check(tree, sid):
    """The <sid>-harvest record's sha256 seal, recomputed per akar.append_record:
    body = lines[4:-1] joined by newlines; claimed = trailing sha256 line."""
    matches = sorted((tree / ".rumpun" / "ledger").glob(f"*_{sid}-harvest.md"))
    if not matches:
        return [], f"no {sid}-harvest record in the extracted ledger"
    rows = []
    for path in matches:
        lines = read_text(path).splitlines()
        if len(lines) < 6 or not lines[-1].startswith("sha256: "):
            rows.append((path.name, "?", "record layout unreadable", "DELTA"))
            continue
        body = "\n".join(lines[4:-1])
        claimed = lines[-1][len("sha256: "):].strip()
        recomputed = hashlib.sha256(body.encode("utf-8")).hexdigest()
        status = "MATCH" if claimed == recomputed else "DELTA"
        rows.append((path.name, claimed, recomputed, status))
    note = f"{len(matches)} harvest seal(s) recomputed"
    return rows, note


def build_record(res, packs_note, seals_note):
    """The check-<sid> record: akar layout, sha256 trailer over the body."""
    body = [
        f"season: {res.sid}",
        f"close-commit: {res.commit}",
        f"outcome row: {res.outcome}",
        f"extracted: git archive -> temp tree ({res.n_extracted} files)",
        "commands run:",
        *(f"- {cmd}" for cmd in res.commands),
        f"pins: {res.pins.get('display', 'no pins run')}",
    ]
    body.extend(f"pack digest {n}: claimed {c} recomputed {r} -> {s}"
                for n, c, r, s in res.packs)
    if not res.packs:
        body.append(f"packs: {packs_note}")
    body.extend(f"seal {n}: claimed {c} recomputed {r} -> {s}"
                for n, c, r, s in res.seals)
    if not res.seals:
        body.append(f"seals: {seals_note}")
    body.append(f"ships row (verbatim): {res.ships_verbatim}")
    if res.ships_source:
        body.append(res.ships_source)
    body.append("ships diff:")
    body.append("| named ship | verdict | evidence |")
    body.append("|---|---|---|")
    for cl in res.clauses:
        parts = [f"file {f} exists (committed-tree claim)" for f in cl.files]
        parts += [
            f"file {fc.token} MISSING (committed-tree claim)"
            for fc in cl.file_claims if fc.kind == "committed" and not fc.present
        ]
        parts += [
            f"runtime artifact {fc.token} "
            f"{'PRESENT (' + fc.where + ')' if fc.present else 'MISSING'}"
            f" (runtime-checked against runs/{res.sid}/)"
            for fc in cl.file_claims if fc.kind == "runtime"
        ]
        parts += [
            f"runtime artifact {fc.token} PRESENT ({fc.where})"
            f" (absent from runs/{res.sid}/; bound committed in the extracted tree)"
            for fc in cl.file_claims if fc.kind == "runtime-committed-fallback"
        ]
        parts += [
            f"{s.token} {'PRESENT (' + s.where + ')' if s.present else 'ABSENT'}"
            for s in cl.surfaces
        ]
        parts += cl.notes
        evidence = "; ".join(parts) or "no machine-checkable claims (prose clause)"
        shown = cl.text if len(cl.text) <= 80 else cl.text[:77] + "..."
        body.append(f"| {shown} | {cl.verdict} | {evidence} |")
    if res.suite_claim:
        body.append(f"suite claim: {res.suite_claim} recorded, not re-run")
    if res.delta_reasons:
        body.append(f"deltas: {'; '.join(res.delta_reasons)}")
    body.append(f"verdict: {res.verdict}")
    body_text = "\n".join(body)
    digest = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
    header = [
        f"# akar record: check-{res.sid}",
        f"id: check-{res.sid}",
        f"date: {date.today().isoformat()}",
        f"title: independent artifact check {res.sid} @ {res.commit[:12]} ({res.verdict})",
    ]
    return "\n".join([*header, body_text, f"sha256: {digest}"]) + "\n"

def write_record(out_dir, sid, text):
    """Atomic append-only write; suffixes a superseding same-day rerun.

    The base id check-<sid> never rewrites: a same-day rerun lands as
    check-<sid>-<N> (N=2,3,...), the engine's own newest-record
    convention. Only the two header lines carry the suffixed id; the
    body and its sha256 seal are untouched.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{date.today().isoformat()}_check-{sid}"
    final = out_dir / f"{stem}.md"
    rerun = 1
    while final.exists():
        rerun += 1
        final = out_dir / f"{stem}-{rerun}.md"
    if rerun > 1:
        rid = f"check-{sid}-{rerun}"
        lines = text.splitlines()
        lines[0] = f"# akar record: {rid}"
        lines[1] = f"id: {rid}"
        text = "\n".join(lines) + "\n"
        logger.warning(
            "check-%s record exists; superseding rerun recorded as %s",
            sid,
            rid,
        )
    tmp = final.with_name(f".{final.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(final)
    return final


def main(argv=None):
    """Run the check; 0 VERIFIED, 1 DELTA, 2 structural refusal."""
    parser = argparse.ArgumentParser(
        description="independent artifact check: re-verify a season from its close commit",
    )
    parser.add_argument("sid", help="season id, e.g. s54")
    parser.add_argument("close_commit", help="season-close commit sha")
    parser.add_argument("--repo", type=Path, default=None, help="repo root")
    parser.add_argument("--out-dir", type=Path, default=None, help="record output dir")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr,
    )
    repo = args.repo or find_repo_root(Path(__file__).resolve().parent)
    python = venv_python(repo)
    result = CheckResult(sid=args.sid, commit=args.close_commit, outcome="")
    full = git_or_die(
        ["rev-parse", "--verify", f"{args.close_commit}^{{commit}}"], repo,
    )
    result.commit = full.strip()
    result.commands.append(
        f"git -C {repo} rev-parse --verify {args.close_commit}^{{commit}} -> {result.commit}"
    )
    with tempfile.TemporaryDirectory(prefix="artifact-check-") as tmp:
        tree = Path(tmp) / "tree"
        tree.mkdir()
        result.n_extracted = extract_commit(repo, result.commit, tree)
        result.commands.append(
            f"git -C {repo} archive {result.commit[:12]} -> {result.n_extracted} files"
        )
        pin_files = sorted((tree / "tests").glob(f"test_{args.sid}_*.py"))
        if not (tree / "DESIGN.md").is_file():
            # issues #36, #37: a repo with no DESIGN.md convention must not
            # take the structural refusal (exit 2) -- there it is
            # indistinguishable from tamper. With no pins lane either,
            # nothing is checkable: the s108 named skip, exit 0, no record,
            # naming the convention. With a pins lane, the SHIPS phase
            # skips and the record carries the note; pins, pack digests,
            # and seals still bind. A DESIGN.md present but missing the
            # season's row keeps the exit 2 refusal (ships_row).
            if not pin_files:
                logger.info(
                    "skip %s @ %s: no DESIGN.md convention in the extract"
                    " and no pins lane (nothing to check)",
                    args.sid, result.commit[:12],
                )
                return 0
            result.ships_source = NO_DESIGN_NOTE
            logger.warning(
                "ships phase skipped for %s @ %s: %s",
                args.sid, result.commit[:12], NO_DESIGN_NOTE,
            )
        else:
            design = read_text(tree / "DESIGN.md")
            result.outcome, result.ships_verbatim, source_note = ships_row(
                design, args.sid, live_path=repo / "DESIGN.md",
            )
            result.ships_source = source_note
        if not pin_files:
            if PINS_CLAIM_RE.search(result.ships_verbatim) is not None:
                logger.error(
                    "no pins file matching tests/test_%s_*.py in %s, "
                    "but the ships row claims pins",
                    args.sid, result.commit[:12],
                )
                raise SystemExit(2)
            logger.info(
                "skip %s @ %s: no pins lane (nothing to check); "
                "the ships row claims no pins",
                args.sid, result.commit[:12],
            )
            return 0
        if not (tree / "src").is_dir():
            # issue #39: a docs-only extract cannot resolve the package,
            # so the import probe would refuse exit 2, reading as tamper.
            # The named pins-lane skip: exit 0, no record.
            logger.info(
                "skip %s @ %s: no src/ in the extract; the pins lane has"
                " no package to import",
                args.sid, result.commit[:12],
            )
            return 0
        info = run_pins(tree, pin_files, python)
        result.pins = {
            "display": (
                f"exit {info['exit']}; {info['passed']} passed; collected {info['collected']},"
                f" passed {info['passed']}, failed {info['failed']},"
                f" errors {info['errors']}; {info['duration']};"
                f" probe resolved {info['probe']}"
            )
        }
        result.commands.append(
            f"{python} -m pytest {[p.relative_to(tree).as_posix() for p in pin_files]}"
            f" -q (exit {info['exit']})"
        )
        packs, packs_note = digest_packs(tree)
        seals, seals_note = seal_check(tree, args.sid)
        result.packs = packs
        result.seals = seals
        runs_dir = repo / ".rumpun" / "runs" / args.sid
        result.clauses = [
            analyze_clause(text, tree, info["collected"], args.sid, runs_dir)
            for text in split_clauses(result.ships_verbatim)
        ]
        m_suite = SUITE_CLAIM_RE.search(result.ships_verbatim)
        result.suite_claim = f"{m_suite.group(1)}/{m_suite.group(2)}" if m_suite else ""
        reasons = []
        if info["exit"] != "0":
            reasons.append(f"pins not green in the extracted tree (exit {info['exit']})")
        reasons += [f"pack digest {n}" for n, c, r, s in packs if s == "DELTA"]
        reasons += [f"seal {n}" for n, c, r, s in seals if s == "DELTA"]
        reasons += [
            f"ships row: {cl.notes[0] if cl.notes else cl.text[:40]}"
            for cl in result.clauses if cl.verdict == "DELTA"
        ]
        result.delta_reasons = reasons
        result.verdict = "DELTA" if reasons else "VERIFIED"
        out_dir = args.out_dir or (repo / ".rumpun" / "ledger")
        text = build_record(result, packs_note, seals_note)
        final = write_record(out_dir, args.sid, text)
        logger.info("verdict %s; record -> %s", result.verdict, final)
    if result.verdict == "VERIFIED":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
