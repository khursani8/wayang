# content_engine — agent manual

Platform for template-driven video generation. A user picks a template, fills
one canonical YAML file, and a video engine renders it. The platform owns
structure and contracts only. It contains no engine code.

## Layout

    AGENTS.md                    this manual
    schema/project.schema.json   canonical project YAML schema
    templates/<name>/            template.yaml skeleton + assets/ + README.md
    vendors/<engine>/            AGENTS.md (engine contract) + build.sh + engine/
    tools/ce.py                  CLI: templates | init | validate | render
    projects/<name>/             filled copies of templates (gitignored)
    .rumpun/                     campaign management (rumpun CLI, season s1)

## Canonical project.yaml

One file per project. Sections: meta, characters, script, settings, vendor.
Full rules: `schema/project.schema.json` and `templates/<name>/template.yaml`
comments. Core rules:

- `meta.vendor` names the engine that renders this project. `meta.template`
  names the template it came from.
- Characters, script order, and timing semantics are canonical. Changing
  vendor must not require rewriting the YAML.
- Timing units: seconds everywhere in canonical YAML. The vendor converts to
  engine units.
- `vendor:` holds engine-specific keys. Each vendor documents its keys in its
  AGENTS.md. Unknown or unsupported keys must error, never be dropped.

## Vendor contract

Every vendor ships:

1. `vendors/<engine>/AGENTS.md` — the engine manual for agents: how the engine
   works, where materials go, how rendering runs, what the mapping from
   canonical YAML is, capability limits.
2. `vendors/<engine>/build.sh PROJECT_DIR OUT_DIR` — deterministic entry:
   reads `PROJECT_DIR/project.yaml`, produces `OUT_DIR/video.mp4`, exit 0 on
   success. Idempotent: safe to re-run. The build log must state the audio
   source used: `voicevox` or `estimate`.
3. Unknown canonical keys that the engine cannot honor must error. A vendor
   may warn+skip styling it supports no equivalent for, only if its AGENTS.md
   says so.

## TTS providers (platform)

The repo owns no services. TTS engines are API clients the user configures:

- `voicevox`: your own VOICEVOX endpoint (default http://localhost:50021,
  override with VOICEVOX_HOST).
- `openai`: OpenAI text-to-speech API, needs OPENAI_API_KEY.
- `revolab`: api.revolab.ai text-to-speech, needs REVOLAB_API_KEY.
  Model default nada-1.0-pro; voice ids from GET /v1/voices.

`ce.py tts <project>` (also run by `ce.py render`) writes one wav per script
line into `projects/<name>/voices/` plus `manifest.json` (hash, seconds,
engine). Re-runs skip unchanged lines. Availability gate is all-or-nothing per
project: if a configured engine has no key or is unreachable, the step warns
and skips, and the vendor renders with estimated timing. An API error while
credentials are present fails the run. Real TTS and silent estimates are
never mixed in one timeline.

Add a provider: implement it in `tools/tts_providers.py`, add the engine to
the `voice.engine` enum in `schema/project.schema.json`, and cover its keys
in a schema `if/then` branch.

## Agent workflow

1. `uv run tools/ce.py templates` — list templates.
2. `uv run tools/ce.py init <template> <project-name>` — scaffold
   `projects/<name>/project.yaml` plus assets.
3. User or agent edits project.yaml (characters, script, visuals).
4. `uv run tools/ce.py validate projects/<name>` — schema + semantic checks.
5. `uv run tools/ce.py render projects/<name>` — dispatches to
   `vendors/<vendor>/build.sh`, streams build output.

## Honesty rules

- The build log always labels audio: `voicevox` (real TTS) or `estimate`
  (estimated timing, silent placeholder audio). Never present an estimate
  render as TTS-timed.
