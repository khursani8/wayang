# Vendor contract

What every video engine must provide to join content_engine. One file, so
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

## Background themes

Shared catalog at `assets/backgrounds/` (repo root). Resolve it relative to
your workdir. `settings.background` names a theme; a project
`assets/background.png` overrides it.

## Environment notes per vendor

See each vendor's AGENTS.md. Remotion: Node 24, npm install in engine/,
@remotion/google-fonts. Hyperframes: Node 22+, ffmpeg, npx downloads the
CLI and Chromium on first run, GSAP from a pinned CDN.
