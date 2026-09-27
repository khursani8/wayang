# campaign resume (2026-09-27)

## Newest closed season
- s5: stopped_operator, verdict WIN, implies: s6
- harvest record: /mnt/data/work/wayang/.rumpun/ledger/2026-09-27_s5-harvest.md
- evidence: /mnt/data/work/wayang/.rumpun/runs/s5/verdicts.jsonl

## Running
- nothing running

## Pending directives
- seq 0: Operator directive 2026-09-26: build content_engine MVP end to end, no questions. Education + community templates, canonical YAML schema, vendors/remotion port with AGENTS.md, tools/ce.py. Consult codex + glm-5.3 + fable before schema freeze.
- seq 1: s1 outcome 2026-09-26: content_engine MVP built and E2E-verified. education smoke-test -> projects/smoke-test/out/video.mp4 (19.5s, 1.7MB, 585 frames); community community-test -> 18.9s MP4 with arbitrary character ids. TTS honestly labeled 'estimate' (VOICEVOX not installed). Consults: codex gpt-5.5 (interchange meta-question, answered: canonical YAML is the stable contract), glm-5.3 full review (timing seconds, unknown-keys-error, no source mixing, source labeling - all adopted), fable design. codex round 2 returned empty output.
- seq 2: Operator directive 2026-09-26: TTS is user-managed API providers. Platform owns no docker/service. Add pluggable voice engines in canonical schema; implement openai (env OPENAI_API_KEY) + existing voicevox endpoint. Platform tts step generates project voices as files; remotion vendor consumes project/voices when present, falls back to estimate. More providers later.
- seq 3: revolab TTS provider added and verified end to end: real API synthesis (nada-1.0-pro, wav 24kHz), community-test rendered 6 revolab voices through the platform-voices path. Note: 'nada-1.0-flash' from the operator's curl example is not a valid model; API exposes nada-1.0-pro and aisyah-1.0-pro. openai provider remains implemented but unverified (no key).
- seq 4: Series support added to ce.py: series.yaml fragment + episodes/<ep>/project.yaml convention; deep merge (episode wins per key, dicts merge, lists replace), merge-then-validate, batch validate/tts/render in name order stopping at first failure, init-series scaffolder, meta.series/episode schema fields. Positive merge test: sparse ep02 (characters inherited, one color override) validates. Negative test: series.yaml removed -> ep02 fails with required name/voice errors, proving inheritance does the work. Batch render of eduseries (2 episodes) launched.
- seq 5: TODO (operator, 2026-09-26): background theme catalog is duplicated per vendor (vendors/remotion/assets/backgrounds + vendors/hyperframes/assets/backgrounds). Move to a single shared location (e.g. assets/backgrounds/ at repo root or vendors/shared/) that all vendors reference, then delete the per-vendor copies. Same policy for any future shared vendor assets.
- seq 6: Closure 2026-09-26: directives 0-5 all executed and verified (MVP, TTS providers, revolab, series, shared background catalog done in the structure review). This entry closes them as historical records; the append-only ledger keeps the originals. Remaining known-open: openai provider unverified against the live API (no key), mascot emotion art, hyperframes se/image-visual support, studio theme contrast.
- seq 7: Operator directive 2026-09-27: distribution requirement - after install (pipx/uv tool/global), the platform must act as a plain CLI: user runs 'wayang <command>' anywhere, no repo clone, no 'uv run tools/wayang.py'. Implies packaging refactor: CLI as an installable package, templates bundled or fetched on first run, vendors set up via a one-time setup/doctor command. Fold into the feature/restructure round.
- seq 8: Closure 2026-09-27: s4 (captions export, voices browser, line preview, stats, init-episode, Rimau cast) shipped and verified in commit 9b0c0a6. The rumpun harvest needs a spawned season run; s4 was implemented directly in-session, so this entry is its ledger closure.

## Newest audit
- none on the ledger

