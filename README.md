# content_engine

Framework-agnostic video template platform: fill one YAML, get a video.

- Templates are named by format: `dialog` (two-host banter), `presentation`
  (one presenter + big cards), `storytelling` (narrative + emotions),
  `community` (announcements).
- Shipped mascots: Momo the tapir and Kiki the hornbill, with Bahasa
  Malaysia sample scripts and Revolab voices.
- Backgrounds are synthesized themes (chalkboard, whiteboard, night-sky,
  kraft-paper, batik, notebook, sunrise, studio, riverbank, slate,
  wood-table). Pick one with `settings.background`; or drop your own
  `assets/background.png` into the project.
- Video engines live under `vendors/<engine>/` (remotion, hyperframes),
  each with an AGENTS.md
  manual and a `build.sh PROJECT_DIR OUT_DIR` entry. The platform contract
  is the root `AGENTS.md`.

## Requirements

- Node 24 + npm (rendering), uv (CLI), ffmpeg/ffprobe (duration guard).
- First time only: `npm install` inside `vendors/remotion/engine`.
- A TTS key for real voices: `REVOLAB_API_KEY` (shipped config) or
  `OPENAI_API_KEY`. Without a key, builds fall back to estimated timing
  with silent audio, labeled in the log.

## Quickstart

    uv run tools/ce.py templates
    uv run tools/ce.py init dialog my-video
    # edit projects/my-video/project.yaml (characters, script, settings)
    uv run tools/ce.py check projects/my-video      # what to fill, in plain words
    uv run tools/ce.py validate projects/my-video
    REVOLAB_API_KEY=... uv run tools/ce.py render projects/my-video

Output: `projects/<name>/out/video.mp4`.

## TTS

The repo owns no services. TTS engines are API clients you configure:
`revolab` (needs REVOLAB_API_KEY; default model nada-1.0-pro, voice ids
from GET /v1/voices) and `openai` (needs OPENAI_API_KEY). `ce.py tts` writes one wav per script line into
`projects/<name>/voices/`; renders reuse cached lines, prefer those files,
then estimates. New engines: add a provider class in
`tools/tts_providers.py` plus the schema enum.

## Series

    uv run tools/ce.py init-series my-series --template dialog

creates `projects/my-series/series.yaml` (shared characters and settings)
plus the first episode. Episodes inherit from series.yaml and override per
key. Render every episode in order with
`uv run tools/ce.py render projects/my-series`.

## How a render runs

`ce.py` validates the project against `schema/project.schema.json`,
generates cached voices, then dispatches to the vendor's `build.sh`, which
maps the YAML to engine inputs and renders. The build log labels the audio
source, and a duration guard fails the build if the rendered length drifts
from the computed timeline, and a visibility lint extracts frames to
confirm every subtitle, card, character and voice is actually present. Details in `AGENTS.md` (agents) and
`vendors/remotion/AGENTS.md` (the remotion engine).
