# content_engine

Framework-agnostic video template platform. Fill one YAML, get a video.

- Templates live in `templates/` (education, community).
- Each renders through a video engine under `vendors/<engine>/`. The engine
  contract is documented per vendor in `vendors/<engine>/AGENTS.md`.
- Agents: start at `AGENTS.md`.

## Quickstart

    uv run tools/ce.py templates
    uv run tools/ce.py init education my-video
    # edit projects/my-video/project.yaml (characters, script, settings)
    uv run tools/ce.py validate projects/my-video
    uv run tools/ce.py render projects/my-video

Output: `projects/<name>/out/video.mp4`.

TTS uses VOICEVOX at localhost:50021 when it is running. Without VOICEVOX the
render uses estimated timings and silent placeholder audio; the build log
states which source was used. See `vendors/remotion/AGENTS.md`.
