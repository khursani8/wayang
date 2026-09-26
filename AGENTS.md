# content_engine — agent manual

Framework-agnostic video generation. Templates named by format
(dialog, presentation, storytelling, community). Agents drive `tools/ce.py`;
humans fill one YAML per video. Malaysian identity: Momo and Kiki mascots,
Bahasa Malaysia content.

## Layout

    AGENTS.md                    this router (deep rules live in docs/)
    docs/vendor-contract.md      what every engine must provide
    docs/project-yaml.md         canonical YAML reference
    schema/project.schema.json   strict gate for project.yaml
    templates/<format>/          working skeletons: template.yaml + art
    vendors/<engine>/            AGENTS.md (deltas) + build.sh + mapper
    tools/ce.py                  templates|init|init-series|check|validate|
                                 tts|render|lint
    projects/<name>/             your filled YAML + assets (gitignored)
    assets/                      art generator sources (mascots, backgrounds)

## Workflow

1. `uv run tools/ce.py templates`
2. `uv run tools/ce.py init <format> <name>`
3. `uv run tools/ce.py check projects/<name>` — plain-words preflight; relay
   FILL items to the user before writing more YAML
4. edit `projects/<name>/project.yaml`
5. `uv run tools/ce.py validate projects/<name>` — strict gate
6. `uv run tools/ce.py render projects/<name>` — TTS + vendor build +
   visibility lint in one command (`--skip-lint` escapes)

## Invariants

- Canonical YAML is the stable contract across engines. Timing in seconds.
  Unknown keys error; nothing is dropped silently.
- Vendors ship build.sh PROJECT_DIR OUT_DIR and emit video.mp4 +
  timeline.json + expected-seconds.txt. Guards: duration (0.5s tolerance)
  and visibility (frames probed per line). Audio source named in every log.
- Series: series.yaml is a sparse base; episodes deep-merge it (episode
  wins per key). Vendors never see series - the platform hands them a
  merged project.
- Check before render. Relay FILL items to the user in plain words.

## Pointers

- Per-engine quirks: `vendors/<engine>/AGENTS.md`
- YAML reference: `docs/project-yaml.md`
- Join as a vendor: `docs/vendor-contract.md`
- Art generators: `assets/` (mascots, background themes)
