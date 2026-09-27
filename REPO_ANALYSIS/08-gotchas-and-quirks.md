# Gotchas and quirks (learned the hard way, 2026-09-26/27)

## Environment traps on this machine

- Bare `python3` prints a uv banner and is banned. Always
  `uv run ...` (PEP 723 scripts) or `uv run --with <lib>`.
- The Bash tool shell cwd STICKS to the previous cd. Two incidents put
  build outputs and a .git inside the wrong folder. Always
  `cd /mnt/data/work/wayang && ...` or use absolute paths.
- Exported env vars do NOT persist between tool calls. Pass keys inline:
  `REVOLAB_API_KEY=... uv run tools/wayang.py render ...`
- Pipelines mask exits: `cmd | tail` reports tail's exit. Keep critical
  chains on && without pipes, or check files after.
- ffmpeg treats PNG input as video: `-ss 2 -i x.png` fails. Scale
  directly: `ffmpeg -i x.png -vf scale=W:H out.png`.

## HyperFrames authoring rules (each learned from a real broken render)

- Media (audio/video/img-with-start) WITHOUT a stable id renders SILENT
  or undiscovered. Every timed element gets an id.
- The runtime's full-frame .clip rule fills ANY unset dimension. Clips
  must be full-frame wrapper divs; position content INSIDE the wrapper.
  Violation once stretched Momo to 1920px wide, centered.
- Fonts referenced without @font-face fall back silently. The mapper
  downloads the Google font woff2 at map time.
- An unclosed div in generated HTML nests ALL later clips inside an
  overflow:hidden window - content after that point vanishes from the
  video while the duration guard stays green. Div balance is now checked
  on every render (must be 0).
- GSAP staggers on per-character spans are the safe typewriter effect;
  clip-path typing breaks when text wraps.

## Visibility lint evolution (why the checks look this way)

- Character animation check v1 compared a line-mid frame vs the tail
  frame; the 0.2s flap makes mid vs tail land on the same flap state
  ~50% of the time -> flaky failures. Replaced with presence-vs-theme:
  character box diffed against the theme PNG scaled to 1920x1080;
  present character samples ~2490 px, empty corner ~0, threshold
  charH^2/60 (evidence-based from live frames).
- Flap animation is now informational only (delta logged, not gated).
- timeline.json is REQUIRED from vendors: the linter's recomputed
  windows drifted on estimate renders (frame quantization) and probed
  past the video end. Vendors emit exact windows; linter refuses to
  guess. Missing frames count as failures, not crashes.
- Voice audibility: volumedetect mean > -55 dB for real-voice lines;
  silent estimate renders measure -91 dB (proven) and skip the check
  with a label.

## Numbers worth remembering

- Revolab synthesis: wav 24kHz mono, nada-1.0-pro default (nada-1.0-flash
  DOES NOT EXIST despite docs/examples), voices list at GET /v1/voices.
- ms voices used: momo=paan-f695215e, kiki=nur-b184422b (see also ali,
  angel, liyana, peter, salina).
- Remotion empty-tail bug (inherited from upstream): Root summed raw
  frames while playback_rate 1.2 compressed the timeline -> 17% empty
  tail. Fixed + guarded by the duration check.
- Lip flap: 0.2s alternating mouth clips (HF) / frame/5 toggle (remotion).
- Mascot pairs must be pixel-identical outside the mouth: generated from
  one SVG with only the mouth group swapped. AI image models cannot
  promise this; the pair-consistency trade-off is documented in
  docs/mascot-art.md.

## Process quirks

- The rumpun ledger is append-only: directives stay "pending" as
  historical records even when executed; closure is recorded via a new
  directive (see #6).
- The Wayang rename: GitHub repo renamed (old URLs redirect), CLI file
  renamed ce.py -> wayang.py, docs swept; the LOCAL folder kept its name
  until the operator asked, then moved to /mnt/data/work/wayang with the
  Claude history namespace migrated via copy + symlink.
- History scrubbing (removing a name from old commit messages) requires
  git filter-repo + force push; done only on explicit request. Old
  commit messages still mention the upstream template repo.

## Known stale references (found by the analysis pass 2026-09-27, NOT yet fixed)

- assets/background/generate_themes.py and generate_background.py hardcode
  output under /mnt/data/work/content_engine (pre-Wayang-rename path).
  Regenerating themes/art writes outside the repo until fixed.
- tools/wayang.py check: theme-catalog validation still points at
  vendors/<vendor>/assets/backgrounds, which no vendor ships since the
  catalog moved to assets/backgrounds - the check is currently a no-op.
- The emotion-art refresh list in generate_mascots.py (TEMPLATE_NAMES)
  does not include the tutorial template.
- Checked-in mascot SVG sources are early drafts (opaque #CFE9B8
  background); the transparent-background versions exist only as
  generated PNGs.
- assets/mascots/generate_mascots.py deploy root was fixed to
  /mnt/data/work/wayang by the Rimau agent (this one IS current).

## Platform-core gotchas (found by the analysis pass 2026-09-27, NOT yet fixed)

- wayang.py check does NOT apply series.yaml inheritance - episode
  projects report false FILL items for characters they inherit.
- init-series defaults new projects to language: "ja" (stale pre-purge
  default; repo language is ms).
- Theme-catalog validation in check points at vendors/<vendor>/assets/
  backgrounds (post-dedupe: nothing there) - the theme check is a no-op.
  The lint uses the correct root catalog; the two disagree.
- TTS cache hash bakes null values, so a provider changing its DEFAULT
  model (e.g. nada-1.0-pro) never invalidates cached voices.
- The visibility lint only checks lines present in timeline.json - script
  lines missing from the timeline pass silently.
- The duration guard lives inside each vendor build.sh, not the platform;
  contract doc says OUT_DIR receives expected-seconds.txt but build.sh
  leaves it in the workdir.
- Lint geometry is hard-coded to the default layout (charH 275, subtitle
  55%/40px, fontSize 70 for band height) - projects overriding these get
  approximate boxes.
- init-series language default and the animation delta (logged, never
  asserted) are the two softest spots in the lint.

## Vendor analysis findings (2026-09-27, NOT yet fixed)

- Remotion ESTIMATE path divides by playback_rate TWICE (map-project.mjs,
  the seconds math and the frame math): estimated lines run ~31% shorter
  than platform-voice lines for the same text. Platform-voice renders are
  unaffected. Explains earlier estimate-vs-voice duration drift.
- Neither vendor copies expected-seconds.txt to OUT_DIR, though
  docs/vendor-contract.md promises it (it stays in the workdir; the
  duration guard reads it there).
- Hyperframes mapper silently ignores unknown settings.* keys; remotion
  errors on them. Inconsistent unknown-key policy across vendors.
- Hyperframes image visuals have no file-existence gate (missing file ->
  broken img in the render); missing se file crashes the mapper uncaught.
- Remotion `scene` field is parsed but never used by the renderer.
- Hyperframes terminal minH is computed and never applied (window height
  grows with content anyway; the variable is dead).
- An empty for-loop remains in the hyperframes mapper (lines ~75-77).
- vendors/remotion/AGENTS.md still points at the removed vendor-local
  background catalog; the real one is assets/backgrounds/.

## Packaging trap (found 2026-09-27)

Templates exist in TWO places: the repo `templates/` (source of truth)
and `src/wayang/packages/templates/` (bundled into the installed wheel).
The installed CLI reads the PACKAGE copies. Editing repo templates
without re-syncing means installed users get stale templates.
Fix policy: after editing templates/, run
    cp templates/*/template.yaml src/wayang/packages/templates/<t>/template.yaml
or a build step that syncs. Same caveat will apply to any other
package-data mirror added later.
