# HANDOFF.md — Wayang

Read this first, then `REPO_ANALYSIS/00-overview.md` (2,000+ lines of verified
reference across six files) and `docs/` for the user-facing documentation.

## Goal

Wayang: an installable, agent-driven, Malaysian-identity video platform.
One YAML in, one narrated stage video out — mascots, voices, subtitles,
music, themed backgrounds. Two render engines behind one contract. The
owner speaks Bahasa Malaysia + English and wants plain, verified answers.

## Current state (verified 2026-09-29)

- Repo: github.com/khursani8/wayang, private, branch main, clean tree,
  HEAD `984e1ae` (PyPI metadata + tag v0.2.0). Local checkout:
  /mnt/data/work/wayang. A user clone exists at /home/sani/work/wayang.
- Installed CLI: `wayang` 0.2.0 via uv tool (reinstall with
  `uv tool install /mnt/data/work/wayang --reinstall --force` after
  source edits — uv caches the built wheel by name+version, so a version
  bump or `--reinstall` is required or the old code keeps running).
- Live projects in `projects/`: video-tutorial (42.6s English-Malay
  bilingual tutorial), rimau-intro, hf-demo, dialog-ms, est-demo,
  portrait-demo (1080x1920), wayang-tutorial (37s full-usage video).
- Season plan s2-s6: ALL resolved. Ledger: .rumpun/ (append-only).

## Architecture (one screen)

- `tools/wayang.py` — repo dev shim into the installed-style package.
- `src/wayang/cli.py` — all commands: templates, init, init-series,
  check, validate, tts, render, captions, voices, stats, init-episode,
  sheet, lint, presets, check-templates, setup, doctor.
- `src/wayang/project.py` — lenient load + series deep-merge.
- `src/wayang/render_checks.py` — duration guard, visibility lint,
  ffprobe/ffmpeg helpers.
- `src/wayang/tts_providers.py` — revolab + openai clients,
  provider_voices for browsing.
- `src/wayang/paths.py` — resource resolution (REPO_ROOT dev mode vs
  package data + WAYANG_HOME for deployed engines).
- `vendors/<engine>/` — remotion (React/Chromium) and hyperframes
  (HTML/data-*/GSAP). Contract: build.sh PROJECT_DIR OUT_DIR emitting
  video.mp4 + timeline.json (incl. declared layout boxes) +
  expected-seconds.txt. `capabilities.yaml` declares what each vendor
  renders; `wayang check` warns on degraded keys.
- `templates/<format>/` — five formats (dialog, presentation,
  storytelling, community, tutorial). Tutorial renders simulated
  terminal steps via GSAP.
- `assets/mascots/` — the SVG art generator (Momo tapir, Kiki hornbill,
  Rimau tiger; lip-flap pairs + emotion sets; canonical frames deployed
  to assets/mascots/frames/<character>/).
- `assets/background/generate_themes.py` — all 11 background themes
  including the chalkboard; writes the shared catalog in
  assets/backgrounds/ (single copy, both vendors read it).
- `assets/se/` — shared sound-effect catalog.

## What worked (keep doing this)

- Render-probe verification: extract frames at line midpoints and count
  ink pixels per contract box. Catches invisible objects that logs miss.
- Vendors emitting timeline.json with exact windows; the linter consumes
  it and never recomputes vendor timing (recomputation drifted 31% on
  estimate renders once).
- Presence-vs-theme character check (diff the corner box against the
  theme PNG). The earlier flap-parity check failed ~50% of lines on
  coin flips.
- Per-language voice overrides under
  `voice.languages.<lang>.voice_id`; the cache hash covers the spoken
  text so pronunciation edits re-synthesize.
- Spawning one writer session per season via `rumpun season start`
  (the s2 and s3 spawned writers delivered excellently).
- The version bump before reinstalling the tool: uv caches the built
  wheel by name+version; without a bump or --reinstall the old code
  keeps running and wastes a debug cycle.

## What did not work (do not repeat)

- Checking an artifact by a relative path: the Bash tool cwd sticks to
  the last cd and background tasks inherit the session cwd. Always
  `cd /mnt/data/work/wayang && ...` or use absolute paths.
- Bare `python3` on this box prints a uv banner and fails. Use
  `uv run --with <libs>` for everything Python.
- Masked exits in `cmd | tail` chains: the pipe reports tail's exit and
  a failing render slipped through once. Gate with && or check files.
- Trusting a commit message written before verification: the s5 commit
  claimed the estimate path passed when it had not. Verify renders
  before writing the claim.
- Patch scripts corrupted by heredoc escaping (`${...}`, backticks).
  Write the patch to a file with the Write tool, or line-splice by
  exact anchors read from the file first.
- Image models for lip-flap pairs: they cannot guarantee frame
  consistency. The SVG swap approach (one body, only the mouth group
  changed) is pixel-verified and is why the mascots work.

## Known-open items (the honest list)

1. OpenAI TTS provider: code-complete, never verified against the live
   API (no OPENAI_API_KEY on this box). Revolab is verified end to end.
2. BGM ducking depth: remotion dips to 25% in voice windows (frame
   callback); hyperframes segments the bed. No sidechain compression.
3. Shared mascot frames dir: templates stopped shipping art and init
   copies the cast, but the emotion-refresh list in generate_mascots.py
   (TEMPLATE_NAMES) still misses the tutorial template.
4. Portrait/square: the preset flag and render work; a dedicated
   vertical demo project does not exist yet.
5. Studio theme: strengthened once (vignette + floor band); the owner
   has not re-reviewed the contrast since.
6. Kiki sad expression: deepened (tear + downturned mouth); needs the
   owner's eyeball on /tmp/mascot-art/emotions/kiki_sad_close.png.
7. The Wayang history contains the upstream template repo name in old
   commit messages; scrubbing requires git filter-repo + force push
   (owner decided to leave it).

## Next steps (the queue)

1. s6 close-out is done; if the owner wants the last polish items:
   Kiki sad contrast (done, needs eyeball), studio theme v3, docs sweep.
2. The pending operator directive: an agent that understands long videos
   and suggests YouTube Shorts (portrait clips, which parts to clip) —
   recorded as rumpun directive 8, planned as season s7. Pipeline: frame
   + audio sampling, Claude vision analysis, clip windows + portrait
   crop plan, optional render.
3. PyPI publish: `uv publish dist/*` with the owner's token; the name
   `wayang` is free (verified 404).

## Environment traps (this machine)

- Bare `python3` prints a uv banner and fails. Use `uv run --with ...`.
- The Bash tool cwd sticks to the last cd; background tasks inherit the
  session cwd, not your last cd. Always prefix `cd /mnt/data/work/wayang &&`.
- Exported env vars do not persist between tool calls. Inline them:
  `KEY=... command`.
- Pipes mask exit codes (`cmd | tail` exits 0). Gate critical chains
  with file checks instead.
- `gh` has two accounts; the active one is switchable via
  `gh auth switch -h github.com -u khursani8`. Current: khursani8.
- The Revolab TTS key travels inline in tool calls. It is in the session
  logs — rotate it when convenient. Do not commit it.

## Command quick reference

    uv run tools/wayang.py templates
    uv run tools/wayang.py init <format> <name> [--preset portrait|square]
    uv run tools/wayang.py init-series <name> --template <format>
    uv run tools/wayang.py check projects/<name>          # preflight
    uv run tools/wayang.py validate projects/<name>       # strict gate
    uv run tools/wayang.py voices --engine revolab
    uv run tools/wayang.py tts projects/<name> [--line N]
    REVOLAB_API_KEY=... uv run tools/wayang.py render projects/<name> [--draft] [--language en]
    uv run tools/wayang.py captions projects/<name>
    uv run tools/wayang.py sheet projects/<name>
    uv run tools/wayang.py stats projects/<name> --json
    uv run tools/wayang.py lint projects/<name>
    uv run tools/wayang.py check-templates
