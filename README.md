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

The repo owns no services. TTS is API-based and user-configured:
`voicevox` (your own endpoint, default localhost:50021, override with
VOICEVOX_HOST) and `openai` (needs OPENAI_API_KEY). `ce.py tts` writes one
wav per script line into `projects/<name>/voices/`; renders use those files
when complete, VOICEVOX next, estimated timing with silent audio last. The
build log states which source was used. New engines go in
`tools/tts_providers.py` plus the schema enum.
