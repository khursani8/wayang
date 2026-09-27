# REPO_ANALYSIS — index

Generated 2026-09-27 by parallel agents + fable. Reference for owner Q&A.

| file | covers |
|---|---|
| 01-platform-core.md | tools/wayang.py CLI (all commands), schema, TTS providers, visibility lint, guards, series |
| 02-vendors.md | remotion + hyperframes vendors: pipelines, mappings, engine internals, differences |
| 03-templates-content-docs.md | 4 template formats, mascot cast, art pipeline, theme catalog, docs set |
| 04-history-decisions.md | commit chronology, campaign directives, three-model reviews, decisions |
| 08-gotchas-and-quirks.md | environment traps, bug classes found+fixed, thresholds, authoring rules |

## The platform in one paragraph

Wayang (formerly content_engine): Malaysian-identity video generation.
Pick a format template (dialog, presentation, storytelling, community,
tutorial), fill one canonical YAML (meta, characters, script, settings,
vendor), render through a pluggable engine. Ships with original mascots
(Momo tapir, Kiki hornbill, Rimau tiger), Bahasa Malaysia samples,
Revolab/OpenAI TTS, 11 background themes, series support, a duration
guard and a visibility lint. Two engines: remotion (React) and
hyperframes (HTML), onboarded via one contract doc.

## The command loop

    uv run tools/wayang.py templates
    uv run tools/wayang.py init <format> <name>
    uv run tools/wayang.py check projects/<name>       # plain-words preflight
    # edit projects/<name>/project.yaml
    uv run tools/wayang.py validate projects/<name>
    REVOLAB_API_KEY=... uv run tools/wayang.py render projects/<name>
    uv run tools/wayang.py lint projects/<name>        # re-run visibility lint

## Key facts quick table

- Repo: github.com/khursani8/wayang (private), branch main
- CLI: tools/wayang.py (renamed from ce.py)
- Engines: remotion (React/Chromium), hyperframes (HTML/data-*/GSAP)
- TTS: revolab (REVOLAB_API_KEY), openai (OPENAI_API_KEY, unverified live)
- Themes: 11 in assets/backgrounds/ (riverbank is default)
- Mascots: Momo (tapir, paan voice), Kiki (hornbill, nur), Rimau (tiger, ali)
- Guards: duration 0.5s tolerance; visibility lint (subtitle/card/character
  presence vs theme; voice > -55 dB); timeline.json required from vendors
