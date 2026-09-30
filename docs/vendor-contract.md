# Vendor contract

What every video engine must provide to join Wayang. One file, so
vendor #3 onboards without copy-paste.

## The deal

    vendors/<engine>/build.sh PROJECT_DIR OUT_DIR

- Reads `PROJECT_DIR/project.yaml` (canonical, timing in seconds). When the
  platform materialized series inheritance, `PROJECT_DIR/.merged.yaml` is
  present instead - prefer it.
- Writes `OUT_DIR/video.mp4`, `OUT_DIR/timeline.json`
  ({"lines": [{"id", "start", "end"}...], "total"}) and
  `OUT_DIR/expected-seconds.txt`.
- Exit 0 on success. Idempotent: the workdir is rebuilt from scratch each
  run. Errors on unsupported canonical keys - never silently drops them.
- The build log names the audio engines used, or `estimate`.

## Guards the platform runs after your build

- Duration guard: ffprobe of video.mp4 vs expected-seconds.txt, 0.5s
  tolerance.
- Visibility lint: frames extracted at each line midpoint must show
  subtitle ink, text-card ink, character animation in the corner boxes;
  real-voice lines must exceed -55 dB.

## Lip sync (optional)

`PROJECT_DIR/voices/lipsync.json` may be present after the platform TTS
step: `{"fps": 30, "lines": {"01_momo": [[0.0, 0.31], ...]}}` - mouth-open
windows in seconds, relative to each voice start (keys are wav name stems).
When present, drive the mouth art from these windows; when absent
(draft/estimate renders), fall back to your fixed mouth clock.

## Background themes

Shared catalog at `assets/backgrounds/` (repo root). Resolve it relative to
your workdir. `settings.background` names a theme; a project
`assets/background.png` overrides it.

## Incremental rendering (optional)

Vendors that can render a frame range declare `range_render: true` in
capabilities.yaml and honor two environment modes in build.sh:

- `WAYANG_PLAN_ONLY=1`: run the mapper only, still write the full-project
  `OUT_DIR/timeline.json` and `OUT_DIR/expected-seconds.txt`, render nothing.
- `WAYANG_RENDER_FRAMES=A-B`: render frames A..B (inclusive) of the exact
  same full composition to `OUT_DIR/span.mp4`. Segment frames must match a
  full render's frames at those positions (same mapper output, same encode
  settings), because the platform splices them in.

The platform hashes each script line (text, visual, wav manifest entry,
lipsync windows, global settings, vendor tree), range-renders only changed
spans and splices them into the previous master at frame-aligned boundaries.
Any inconsistency falls back to a full render, logged. Duration guard and
visibility lint always run on the final output. Vendors without
`range_render` get full renders every time (note the limit under
`capabilities.degraded`).

## Environment notes per vendor

See each vendor's AGENTS.md. Remotion: Node 24, npm install in engine/,
@remotion/google-fonts. Hyperframes: Node 22+, ffmpeg, npx downloads the
CLI and Chromium on first run, GSAP from a pinned CDN.
