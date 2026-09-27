Reading additional input from stdin...
OpenAI Codex v0.156.1
--------
workdir: /mnt/data/work/wayang
model: gpt-6-astra
provider: openai
approval: never
sandbox: danger-full-access
reasoning effort: medium
reasoning summaries: none
session id: 01a0dffa-19bf-7802-8519-b98550719c6f
--------
user
# Review brief: Wayang — structure health + next features

FIRST: read REPO_ANALYSIS/00-overview.md through 08-gotchas-and-quirks.md
in this repo (2018 lines of verified reference: architecture, commands,
vendors, templates, art pipeline, history, known bugs).

What Wayang is: agent-driven, Malaysian-identity video generation.
Format templates (dialog, presentation, storytelling, community,
tutorial) -> user fills ONE canonical YAML -> agents drive
tools/wayang.py (8 commands) -> pluggable vendors render (remotion:
React; hyperframes: HTML/GSAP). TTS: revolab + openai API clients,
cached per-line wavs. Guards: duration check, visibility lint
(pixel probes), timeline.json contract. Original mascots with emotions,
11 background themes, series support. Constraints: repo owns no
services (API clients only), Malaysian identity (Bahasa Malaysia,
Momo/Kiki/Rimau), renders are narrated stage scenes (hosts, cards,
subtitles) — no live footage.

## MANDATE 1 — RESTRUCTURING (if needed)

Is the current structure right for the next 10 vendors and templates?
Known open issues are listed in 08-gotchas-and-quirks.md. Propose
concrete file-level moves only (merge, move, delete, split) — with the
reason and the risk. Do not propose rewrites of working engines.

## MANDATE 2 — NEW USER-FACING FEATURES for content creation

Users: Malaysian creators + the agents serving them. Propose 5-10
features, each with: name, one-line user story, implementation sketch
(which files/layers change), effort S/M/L, priority. Favor features the
CURRENT architecture can host (narrated stage videos).

## OUTPUT

Markdown, two sections (RESTRUCTURE / FEATURES), prioritized, concrete,
max ~600 words. No questions back.

Read REPO_ANALYSIS/*.md first, then inspect any repo file you need.
warning: Codex is ignoring 8 unrecognized configuration settings. Check for typos or deprecated settings.
  user (/home/sani/.codex/config.toml): `mcp_servers.pencil.type` is ignored.
  user (/home/sani/.codex/config.toml): `mcp_servers.web-reader.headers` is ignored.
  user (/home/sani/.codex/config.toml): `mcp_servers.web-reader.type` is ignored.
  ... and 5 more ignored settings.
warning: Codex is ignoring 8 unrecognized configuration settings. Check for typos or deprecated settings.
  user (/home/sani/.codex/config.toml): `mcp_servers.pencil.type` is ignored.
  user (/home/sani/.codex/config.toml): `mcp_servers.web-reader.headers` is ignored.
  user (/home/sani/.codex/config.toml): `mcp_servers.web-reader.type` is ignored.
  ... and 5 more ignored settings.
2026-09-26T23:08:25.322377Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when Deserialize(Error("data did not match any variant of untagged enum JsonRpcMessage", line: 0, column: 0))
2026-09-26T23:08:25.322677Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when Deserialize(Error("data did not match any variant of untagged enum JsonRpcMessage", line: 0, column: 0))
2026-09-26T23:08:25.340225Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when Deserialize(Error("data did not match any variant of untagged enum JsonRpcMessage", line: 0, column: 0))
hook: SessionStart
hook: SessionStart Completed
hook: UserPromptSubmit
hook: UserPromptSubmit Completed
codex
I’ll read the repository analysis, then inspect files that affect structure and feature proposals. I’ll apply the DTS skill.

hook: PreToolUse
hook: PreToolUse Completed
exec
/usr/bin/zsh -lc 'cat REPO_ANALYSIS/0[0-8]*.md' in /mnt/data/work/wayang
 succeeded in 0ms:
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
# 01 - Platform core: wayang.py, TTS providers, canonical schema

Sources read in full: `tools/wayang.py`, `tools/tts_providers.py`,
`schema/project.schema.json`, `docs/vendor-contract.md`, `docs/project-yaml.md`,
plus `vendors/remotion/build.sh`, `vendors/hyperframes/build.sh`, root `AGENTS.md`.
All behavior below is as-read from main (2026-09-27), not projected.

## 1. Identity and paths

- CLI: `uv run tools/wayang.py <command> ...`. Script header requires
  python >=3.10 and declares pyyaml>=6.0, jsonschema>=4.20, pillow>=10.0.
- `ROOT` is the repo root, resolved from `__file__` (parent of `tools/`).
  Every path below is ROOT-relative unless stated.
- Schema: `schema/project.schema.json`. Templates: `templates/<format>/template.yaml`.
  Vendors: `vendors/<engine>/build.sh`. Shared themes: `assets/backgrounds/*.png`
  (11 files: batik, chalkboard, kraft-paper, night-sky, notebook, riverbank,
  slate, studio, sunrise, whiteboard, wood-table).
- Templates present on disk (5): community, dialog, presentation, storytelling,
  tutorial. Root AGENTS.md names only 4 formats; `tutorial` exists but is absent
  from the AGENTS.md prose. Docs drift.
- Logging: `logging.basicConfig(level=INFO, format="%(levelname)s %(message)s")`,
  logger `ce` (TTS module uses `ce.tts`). Log output goes to stderr. The only
  stdout output in the whole CLI is `check --json`.

## 2. CLI commands

Exit codes across the CLI: 0 = success or READY, 1 = every hard error
(fail(), schema errors, lint failures, vendor nonzero exit, check blockers,
missing project/parse errors), 2 = only `check` with notes and no blockers.
argparse itself exits 2 on bad usage.

### templates

    uv run tools/wayang.py templates

No arguments. Lists subdirectories of `templates/` that contain
`template.yaml`, sorted, one name per line at INFO. No failure path besides
filesystem errors.

### init

    uv run tools/wayang.py init <template> <name>

1. Strips a leading literal `projects/` from `<name>` (`str.removeprefix`).
2. `templates/<template>/template.yaml` must exist, else
   `unknown template: <t>` exit 1.
3. `projects/<name>` must not exist, else
   `projects/<name> already exists` exit 1.
4. `shutil.copytree` of the whole template dir (art included) into
   `projects/<name>`, then `template.yaml` is renamed to `project.yaml`.
5. INFO: `created projects/<name> - edit project.yaml, then:
   uv run tools/wayang.py validate projects/<name>`.

`init dialog my-video` and `init dialog projects/my-video` are identical.

### init-series

    uv run tools/wayang.py init-series <name> [--template dialog] [--first-episode ep01]

Defaults: template `dialog`, first episode `ep01`.

1. Template check as in init. `projects/<name>` must not exist.
2. Loads the template YAML, creates `projects/<name>/episodes/`.
3. Writes `projects/<name>/series.yaml`: a fixed header comment (series.yaml
   is a fragment, never validated on its own, episodes deep-merge it) plus:
   - `meta`: `title` copied from the template, `template`, `vendor` copied,
     `language` = template value or default `"ja"`,
     `description` = fixed text about the shared base.
   - `characters` and `settings` copied from the template when present.
4. `copytree` of the template into `episodes/<first-episode>`, rename
   `template.yaml` to `project.yaml`.
5. INFO hint: add episodes with `wayang.py init <template> <series>/episodes/<ep>`.

Gotcha: the language fallback is `"ja"` while the repo's stated identity is
Bahasa Malaysia content.

### check (preflight)

    uv run tools/wayang.py check <project> [--json]

Reads ONLY the raw `projects/<x>/project.yaml`. No series merge, no schema
validation, no file-existence checks beyond theme catalog and mouth art.
Produces two lists: `issues` (blockers) and `notes` (informational).

Issues:
- Any of `meta`, `characters`, `script`, `settings` missing:
  `no [<section>] section - copy it from templates/<format>/template.yaml`.
- `meta.title` blank: `meta.title is empty - name your video`.
- `vendors/<vendor>/build.sh` missing:
  `vendor '<v>' does not exist (known: remotion, hyperframes)`.
  Vendor defaults to `remotion` when `meta.vendor` is absent. The list of
  known vendors is hard-coded in this message.
- `characters` empty: `no characters - every script line needs a speaker`.
- Per character: blank name (`character '<cid>' has no name`); missing
  `voice.engine` (`character '<cid>' has no voice.engine - how should it
  sound?`); engine not in PROVIDERS (`character '<cid>': voice engine '<e>'
  is unknown (known: openai, revolab)`).
- `script` empty: `script is empty - write at least one line`.
- Per line: speaker not defined (`script line <id>: speaker '<cid>' is not
  defined in characters`); blank text (`script line <id>: text is empty`).
- `settings.background` set (non-None) and the vendor catalog dir
  `vendors/<vendor>/assets/backgrounds` exists: background not among the
  `*.png` stems there -> `settings.background '<b>' is not a theme here
  (available: <comma list>)`. Note: this catalog is vendor-local, not the
  repo-root `assets/backgrounds` the lint uses.

Notes:
- Engine known but unavailable (missing env key, via `provider.available()`):
  `character '<cid>' speaks via <engine>: <why> - renders stay silent with
  estimated timing until you set the key`.
- `settings.character.use_images` true and
  `assets/images/<cid>/mouth_close.png` missing:
  `character '<cid>' has use_images but no art at assets/images/<cid>/ -
  placeholder box will show`.
- `voices/manifest.json` exists: `<n> line voice(s) cached in voices/ -
  they are reused on render`.

Output: every issue logged at WARNING prefixed `FILL: `, every note at INFO
prefixed `NOTE: `. With `--json`, one JSON line goes to stdout:
`{"ready": <not issues>, "issues": [...], "notes": [...]}` (printed via
`print`, so stdout stays clean for piping).

Exit codes:
- issues present: WARNING `NOT READY: <n> item(s) to fill above - then:
  wayang.py validate && wayang.py render`, exit 1.
- no issues but notes: WARNING `READY with <n> note(s) - see NOTE lines
  above`, exit 2.
- neither: INFO `READY`, exit 0.

### validate

    uv run tools/wayang.py validate <project>

Resolves the project, expands to episodes if it is a series dir, runs
`validate_project` on each (log line `validating <name>` per episode).
Exit 1 on the first failure.

### tts

    uv run tools/wayang.py tts <project> [--force]

Series-aware: per episode, `validate_project(ep)` runs first (schema errors
abort before any synthesis), then `run_tts(ep, force=args.force)`.
`--force` regenerates lines even when the cache hits.

### render

    uv run tools/wayang.py render <project> [--skip-lint]

Series-aware. When more than one target: INFO
`series: <n> episode(s): <names>`. Per episode `render_one`:

1. `validate_project`.
2. Materialize the merged document: if a series.yaml applied, write
   `<episode>/.merged.yaml` (the vendor prefers it over project.yaml); if
   the project is standalone, delete a stale `.merged.yaml` if present.
3. `run_tts(pdir, data)` with force always False. Render never forces
   regeneration; use the `tts --force` command for that.
4. `bash vendors/<vendor>/build.sh <project_dir> <out_dir>` where
   `out_dir = <pdir>/out`. Nonzero vendor exit -> `vendor build.sh exited
   <code>` exit 1.
5. `lint_project` on `out/video.mp4` unless `--skip-lint`.

### lint

    uv run tools/wayang.py lint <project>

Runs `validate_project` first (the project must pass the strict gate), then
requires `out/video.mp4`, else `no render found at <path> - run wayang.py
render first` exit 1. Then `lint_project`.

### resolve_project

Accepts `<name>` (looked up under `projects/`) or a path relative to ROOT.
Preference order: `ROOT/<value>` first, then `ROOT/projects/<value>`. Not
found -> error names both candidate paths, exit 1.

## 3. validate_project (the strict gate)

1. `load_project`: `project.yaml` must exist, parse as YAML, and be a
   mapping. If a series.yaml applies it is parsed (must be a mapping) and
   deep-merged under the episode doc (section 9).
2. JSON Schema Draft 2020-12 against `schema/project.schema.json`. All
   errors are collected, sorted by JSON path, logged as
   `schema: <path>: <message>`, then exit 1.
3. Semantic checks, each failing fast with exit 1:
   - Every script line: `character` id must exist in `characters`
     (`script id <id>: unknown character '<cid>'`).
   - `visual.type == "image"` with a `src`: file must exist relative to the
     project dir (`script id <id>: visual image missing: <src>`).
   - `se.src` must exist relative to the project dir
     (`script id <id>: sound effect missing: <src>`).
   - Every character: `voice.engine` must be in PROVIDERS
     (`character <cid>: unsupported voice engine '<e>' (known: openai,
     revolab)`); `image` path must exist when set.
   - `vendors/<vendor>/build.sh` must exist.
4. Returns the merged data dict (later stages consume it).

## 4. Canonical project.yaml schema

Draft 2020-12. Root: `additionalProperties: false`, required
`meta` + `characters` + `script`; optional `settings` and `vendor`. So
exactly five top-level keys are allowed: meta, characters, script,
settings, vendor. Every other level sets `additionalProperties: false`
too, so unknown keys error everywhere except inside the free-form
top-level `vendor` object.

### meta

`additionalProperties: false`. Required: `title` (string, 1..120 chars),
`template` (minLength 1), `vendor` (minLength 1). Optional: `language`,
`description`, `series` (strings), `episode` (integer or string).

### characters

Object, `minProperties: 1`. Key pattern `^[a-z][a-z0-9_]*$` (lowercase
start, digits and underscore after, no hyphens, no uppercase). Each value
(`$defs/character`): `additionalProperties: false`, required `name` + `voice`.

- `name`: string, minLength 1.
- `color`: string matching `^#[0-9a-fA-F]{6}$`.
- `position`: enum `left` | `right` (lint assumes `right` when absent).
- `image`: string path (existence checked by validate_project).
- `flip_x`: boolean.
- `voice`: object, required `engine`, enum `openai` | `revolab`. Two
  if/then branches (allOf), each with `additionalProperties: false`:
  - engine `openai`: allowed keys `engine`, `voice`, `model`, `speed`,
    `instructions`. REQUIRED `voice`. `speed`: number 0.25..4.
  - engine `revolab`: allowed keys `engine`, `voice_id`, `model`,
    `speed`. REQUIRED `voice_id`. `speed`: number 0.25..4.
  - Cross-branch rule this produces: `voice` is openai-only, `voice_id`
    is revolab-only, `instructions` is openai-only. Mixing them errors
    with `Additional properties are not allowed (...)`.

### script

Array, `minItems: 1`. Each line (`$defs/line`): `additionalProperties:
false`, required `id` + `character` + `text`.

- `id`: integer (rendered zero-padded to 2 digits in voice filenames).
- `character`: string, must match a characters key (checked in step 3).
- `text`: string, minLength 1. Spoken text.
- `display_text`: string. Subtitle override (subtitle shows this instead
  of `text`).
- `scene`: integer, min 1.
- `pause_after`: number, min 0 (seconds).
- `emotion`: enum `normal` | `happy` | `surprised` | `thinking` | `sad`.
- `visual`: object, `additionalProperties: false`, required `type`.
  `type` enum: `text` | `image` | `none` | `terminal`. Other keys:
  `text`, `src`, `font_size` (number), `color`, `outline_color`,
  `animation` (enum `none` | `fadeIn` | `slideUp` | `slideLeft` |
  `zoomIn` | `bounce`), `command` (string), `output` (array of strings).
  Conditional requirement: when `type == "terminal"`, `command` is
  REQUIRED (schema if/then). No equivalent condition forces `src` for
  `type == "image"` in the schema, but validate_project fails the render
  when an image `src` file is missing.
- `se`: object, `additionalProperties: false`, required `src`.
  `volume`: number 0..1.

### settings

`additionalProperties: false`. All subsections optional, each closed:

- `video`: `width` int >=320, `height` int >=240, `fps` int 12..120,
  `playback_rate` number 0.5..3 (slows voice and pacing; docs recommend
  0.9 for tutorials).
- `font`: `family` string, `size` int >=10, `weight` string or integer,
  `color` string.
- `subtitle`: `minProperties: 1`; `bottom_offset` int >=0,
  `max_width_percent` int 10..100, `outline_width` int >=0.
- `character`: `height` int >=40, `use_images` boolean,
  `images_base_path` string.
- `content`: `top_padding`, `side_padding`, `bottom_padding`, ints >=0.
- `background`: string theme name.

### vendor

Top-level `vendor`: `type: object`, free-form. Vendor passthrough section
(remotion mapper reads vendor-specific keys from here). Not mentioned in
docs/project-yaml.md's section list.

Note: the schema does not require `settings`, but `check` treats a missing
settings section as a blocker.

## 5. TTS layer (tools/tts_providers.py)

The repo owns no TTS service. Engines are plain HTTP API clients.

| Provider | Endpoint | Env key | config_hash keys | Default model | Required voice key |
|---|---|---|---|---|---|
| openai | `https://api.openai.com/v1/audio/speech` | `OPENAI_API_KEY` | voice, model, speed, instructions | `gpt-4o-mini-tts` | `voice` |
| revolab | `https://api.revolab.ai/v1/tts` | `REVOLAB_API_KEY` | voice_id, model, speed | `nada-1.0-pro` | `voice_id` |

Both providers: POST JSON with `Authorization: Bearer <env key>`,
`urlopen` timeout 120s, response bytes written verbatim to the output wav.
`HTTPError` -> `ProviderError` with status code plus the first 300 chars of
the response body (messages `openai tts http <code>: ...` and
`revolab http <code>: ...`). `URLError` -> `ProviderError` with the reason.
Payloads: openai sends `model`, `voice`, `input`, `response_format: "wav"`,
optional `speed`, optional `instructions`. revolab sends `model`, `text`,
`voice_id`, optional `speed`.

`wav_seconds(path)`: stdlib `wave`, `nframes / framerate`.

### Cache: manifest.json and file naming

- Voices land in `<project>/voices/`, one wav per script line, named
  `f"{id:02d}_{character}.wav"` -> `NN_character.wav` (id zero-padded to
  2 digits; id 100+ produces `100_character.wav`, 3 digits, cosmetic only).
- `voices/manifest.json`: `{"lines": {"<fname>": {"hash", "seconds",
  "engine"}}, "engines": [<sorted unique engine names>]}`.
- Hash: `line_hash(text, engine, provider.config_hash(cfg))` = first 12
  hex chars of `sha256(json.dumps({"text", "engine", "params"},
  sort_keys=True))`. Editing text, engine, or any config_hash key
  invalidates the entry. Unset keys hash as JSON null, so changing a
  provider's in-code default model does NOT invalidate cached files.
- Cache hit condition: `--force` not set AND `manifest["lines"][fname].
  hash == digest` AND the wav file exists on disk.
- `seconds` recorded as `round(wav_seconds, 3)`.
- Manifest written with `indent=2`, `ensure_ascii=False`, trailing newline.
  `engines` is rebuilt from the `lines` values after every run, including
  the all-cached early return.
- Stale entries are never pruned: lines deleted from the script keep their
  manifest entries and wavs forever.

### Availability gate (all-or-nothing per project)

`run_tts` collects the set of engines used across all script lines. If ANY
engine fails `available()` (missing env key), it logs one WARNING per
engine (`TTS engine <engine>: <why>`) plus `no TTS this run: vendor renders
with estimated timing and silent audio`, and returns. Nothing is
synthesized; the render proceeds with estimated timing and silent audio.
One missing key silences the entire project, no partial voice sets.

`ProviderError` inside the job loop: `TTS failed for <fname>: <e>`, exit 1.
Wavs written earlier in the same run stay on disk but the manifest is only
written after the full loop, so those lines regenerate on the next run.

Flow states logged: `TTS: all <n> line voice(s) cached in <dir>` when
nothing to do, `TTS: generating <n> line voice(s) with <engines>` when
jobs exist, `TTS <fname>: <sec>s (<engine>)` per synthesized line.

## 6. Visibility lint (post-render)

Entry: `lint_project(pdir, mp4, data)`. Called by `render` (unless
`--skip-lint`) and by `lint`. Vendor-agnostic. Returns True on pass; any
fatal problem or accumulated failure exits 1.

### Layout contract (hard-coded in wayang.py)

- Characters: bottom corners. Square box, `charH` wide and tall, 40px
  inset from the screen edge. Left character x0 = 40; right character
  x0 = W - 40 - charH. Box y range: H - charH to H.
- Subtitle: bottom-center. Width = `max_width_percent` percent of W
  (default 55). Height = `fontSize * 1.5 * 2` (room for two lines).
  Bottom edge sits `bottom_offset` px above the screen bottom (default 40).
- Text card: upper-center region from (0.15W, 0.15H) to (0.85W, 0.62H).

At defaults and 1920x1080: subtitle band x 432..1488 (55 percent of 1920
centered), y 830..1040 (fontSize 70 -> height 210, bottom_offset 40);
character box 275x275 at x 40..315 (left) or 1605..1880 (right), y 805..1080;
card region x 288..1632, y 162..669.6.

### Settings defaults used by the lint

fontSize 70 (`settings.font.size`), charH 275
(`settings.character.height`), subPct 55
(`settings.subtitle.max_width_percent`), subBottom 40
(`settings.subtitle.bottom_offset`). W, H, duration come from `ffprobe`
on the actual mp4 (first stream with `codec_type == "video"`). A render
size differing from `settings.video.{width,height}` logs a WARNING
(`render size %dx%d differs from settings`) and continues.

### Checks, in order

1. Layout overlap (no frame extraction): subtitle band vs each character
   corner box, plain rectangle-overlap test
   (`subX0 < cx0 + charH and subX1 > cx0 and subY0 < H and subY1 > H - charH`).
   Any overlap -> `layout: subtitle band overlaps character '<cid>' box`,
   immediate return False (exit 1), no further checks.
2. timeline.json is REQUIRED. Read from the mp4's directory
   (`<out>/timeline.json`), shape
   `{"lines": [{"id", "start", "end"}, ...], "total"}` with seconds.
   Windows = script lines that have a matching timeline entry (ids matched
   as ints), `dur = end - start`. Logs `lint: using vendor timeline.json
   (<n> lines)`. Zero windows -> `visibility lint: <path> missing - the
   vendor must emit the timeline it renders`, exit 1. A partial timeline
   silently shrinks coverage to the intersection; extra or missing
   per-line entries do not error individually.
3. Reference frame ("tail"): extracted at `duration - 0.4` (clamped) to
   `<pdir>/out/.lint/tail.png`. Extraction failure -> exit 1
   (`could not extract the reference frame`).
4. Per line window: sample frame at `mid = start + dur * 0.6` (60 percent
   into the line, not the midpoint) to `.lint/f<id>.png`.
   - Extraction failure -> `visibility: line <id> frame missing - render
     is shorter than the computed timeline`, +1 failure.
   - Subtitle ink: `tail` frame is the "empty" baseline; diff of the
     sample vs tail cropped to the subtitle band (subY0 clamped to >= 0
     here). Count < 150 -> `visibility: line <id> subtitle has no ink in
     the subtitle band`, +1 failure.
   - Text card ink: only when `line.visual.type == "text"` and
     `visual.text` non-empty. Same diff method on the card region;
     count < 150 -> `text card has no ink in the card region`, +1 failure.
   - Character presence: only when
     `ROOT/assets/backgrounds/<settings.background or "riverbank">.png`
     exists. The theme PNG is resized to WxH as the baseline; corner-box
     diff count < `(charH * charH) / 60` -> `character '<cid>' missing
     from its corner box`, +1 failure. Default charH 275 -> threshold
     275^2/60 = 1260.42 sampled pixels. Theme PNG missing -> WARNING
     `character presence check skipped: theme png missing for theme '<t>'`,
     check skipped, not a failure.
   - Character animation (informational, never fails): second frame at
     `min(mid + 0.21, duration - 0.2)` to `.lint/f<id>b.png`; corner-box
     diff logged INFO `character animation delta: <n>`.
   - Voice loudness: only when `real_voices` (manifest.json exists AND
     `manifest.engines` non-empty). `ffmpeg -ss <start> -t <dur> -af
     volumedetect`; `mean_volume` parsed from stderr; if the line is
     absent the sentinel -99.0 is used (which then fails the threshold).
     `vol < -55.0` dB -> `audibility: line <id> voice is silent (<v> dB)`,
     +1 failure. Pass logs `line <id>: subtitle ok, character ok, voice
     <v> dB`. Estimate render: `line <id>: subtitle ok, character ok
     (estimate render: voice check skipped)`.
5. Summary: failures -> `visibility lint: <n> failure(s)`, exit 1.
   Otherwise `visibility lint: all checks passed`, return True.

### Diff sampling method (`_band_diff_count`)

Crop both images to the box (coords cast to int), `PIL.ImageChops.
difference`, convert to RGB, sample every 2nd pixel on both axes
(stride 2), count samples where any of R, G, B differs by more than 24.

Frame helper `_ffmpeg_frame`: puts `-ss <t>` before `-i` (fast seek),
`-frames:v 1`, clamps t into `[0, duration - 0.2]`, returns False when
ffmpeg fails or the file is missing.

What fails vs informational:
- Fails (exit 1): layout overlap, missing timeline.json, missing tail
  frame, missing line frame, subtitle ink < 150, card ink < 150,
  character presence below charH^2/60 (when theme exists), voice below
  -55 dB (when real voices).
- Informational only: animation delta (INFO), render size mismatch
  (WARNING), theme PNG missing (WARNING, skips that check), estimate
  render voice check (skipped).

Temp frames in `<pdir>/out/.lint/` (`tail.png`, `f<id>.png`,
`f<id>b.png`) are never cleaned up.

## 7. Duration guard and timeline.json contract

The duration guard is NOT in wayang.py. Each vendor's `build.sh` enforces
it after rendering; remotion and hyperframes carry identical logic:

1. `EXPECTED` = contents of the workdir `expected-seconds.txt` (may be
   empty).
2. If EXPECTED is non-empty and `ffprobe` is on PATH:
   `ACTUAL` = `ffprobe -show_entries format=duration` of the rendered
   mp4. Pass iff `EXPECTED - 0.5 <= ACTUAL <= EXPECTED + 0.5` (awk float
   compare). Otherwise exit 1 with `rendered duration deviates from the
   computed timeline` (remotion appends `(empty-tail bug class)`).
   ffprobe missing -> WARNING `duration guard skipped, ffprobe not found`.
3. Only after the guard passes, the workdir `timeline.json` and rendered
   video are copied to OUT_DIR as `timeline.json` and `video.mp4`.

The vendor nonzero exit propagates through `render` as
`vendor build.sh exited <code>` with wayang exit 1.

`expected-seconds.txt` is the mapper's computed timeline total (per
hyperframes AGENTS.md: sum of line audio plus pauses). Discrepancy:
`docs/vendor-contract.md` says the vendor writes
`OUT_DIR/expected-seconds.txt`; both build.sh scripts actually leave it
in the workdir (`vendors/<engine>/.work/<project>/expected-seconds.txt`)
and copy only `timeline.json` + `video.mp4` to OUT_DIR.

timeline.json consumers: the visibility lint reads it from the mp4's
directory (OUT_DIR), so a vendor that skips copying it breaks lint with
`the vendor must emit the timeline it renders`.

Vendor build contract (`docs/vendor-contract.md` + both scripts):
`build.sh PROJECT_DIR OUT_DIR`; wrong arg count -> usage, exit 2. Reads
`project.yaml`, prefers `.merged.yaml` when present. Timing in seconds;
vendors convert to their own units. Idempotent: workdir
`vendors/<engine>/.work/<project-name>` is `rm -rf`-ed every run. Must
error on unsupported canonical keys, never silently drop them. Build log
names the audio engines used or `estimate`.

Vendor specifics:
- remotion: copies engine source (excludes `node_modules`, `out`),
  symlinks `engine/node_modules`, copies project `assets/` into
  `public/`, runs `scripts/map-project.mjs`, `npm run sync`, then
  `npx remotion render src/index.ts Main out/video.mp4`.
- hyperframes: copies `voices/` and `assets/` into the workdir, runs
  `npm install` in `scripts/`, `map-project.mjs`, then
  `npx --yes hyperframes@latest render --output out.mp4 -f 30`
  (downloads the CLI and Chromium on first run).

## 8. Series model

- `series.yaml` is a sparse base: meta (title, template, vendor, language,
  description), characters, settings. A fragment; never validated alone.
- Merge in `load_project`: `deep_merge(series, episode)`. Episode wins per
  key; dicts recurse; lists and scalars replace. The `script` list is
  therefore always episode-only. Merge logs
  `merged series config <path> (<n> shared character(s))` where n counts
  series character keys.
- Series file discovery (`find_series_file`): checks
  `pdir.parent/series.yaml` then `pdir.parent.parent/series.yaml`. The
  standard layout `projects/<series>/episodes/<ep>/` resolves at two
  levels. Episodes nested deeper find nothing.
- Whole-dir operations (validate, tts, render): `is_series_dir` = dir
  contains `series.yaml` OR has an `episodes/` subdir. Then
  `series_episodes` lists `episodes/*/project.yaml` sorted by directory
  name; the command loops all of them in that order.
- Vendors never see series.yaml: `render` materializes the merged document
  as `<episode>/.merged.yaml` (only when a series applied) and deletes a
  stale `.merged.yaml` for standalone projects. Vendor contract: prefer
  `.merged.yaml` when present.
- Add episodes post-init with `init <template> <series>/episodes/<ep>`.

## 9. Gotchas

1. `check` does not merge series.yaml and does not schema-validate. An
   episode that inherits characters from series.yaml reports
   `speaker '<cid>' is not defined in characters` from check even though
   validate and render pass. Run check at the series root only for
   base-level gaps, or ignore those FILL items on episodes.
2. `init-series` language fallback is `"ja"`, not `ms`. Series built
   without a template language need a manual edit.
3. The theme catalog lives in two places: `check` validates
   `settings.background` against `vendors/<vendor>/assets/backgrounds`
   (vendor-local), the lint's character presence uses the repo-root
   `assets/backgrounds`. A theme name can pass check and still miss the
   lint's theme file (presence check then silently skips with a warning).
4. Lint timeline matching is an intersection: timeline entries missing for
   some script lines drop those lines from all frame and audio checks
   without any error. Only a fully empty window list fails.
5. TTS cache hash includes unset voice keys as null. Changing a provider's
   in-code default model (for example `gpt-4o-mini-tts`) regenerates
   nothing; already cached lines keep the old model's audio.
6. The TTS gate is project-wide all-or-nothing across engines. One missing
   env key for one character silences every line in the project.
7. `render` always calls run_tts with force=False. Editing text
   invalidates only that line's hash, so renders after edits re-synthesize
   exactly the changed lines (unless the key is gone).
8. `_ffmpeg_volume` returns -99.0 when `mean_volume` is absent (for
   example a video with no audio track). With real_voices true that reads
   as silence and fails, which is intended, but it also means a volumedetect
   output-format change would fail every line.
9. The lint's character presence baseline is the theme PNG, not a
   character-free frame of the actual render. A background that differs
   from the theme PNG inside the corner box (vendor draws extra art there)
   can produce false presence; the same design makes the check depend on
   repo-root assets that a standalone vendor checkout would not have.
10. Animation delta is logged but never asserted. A fully static character
    passes the lint.
11. Subtitle band coordinates are used raw in the overlap test but Y0 is
    clamped to 0 only for the ink crop. Extreme `bottom_offset` +
    `font.size` values can push the band off-screen and pass overlap while
    the ink check then fails (correctly) on every line.
12. Non-integer timeline ids crash the lint (`int(entry["id"])`), but the
    schema forces integer line ids, so only a broken vendor timeline can
    trigger it.
13. `resolve_project` prefers `ROOT/<value>` over `ROOT/projects/<value>`:
    a repo-root directory named like the project shadows the projects/ one.
14. `lint` command requires `validate_project` to pass first; you cannot
    lint a render made from a since-edited, now-invalid project.yaml
    without fixing the YAML or temporarily bypassing.
15. Docs drift: `docs/vendor-contract.md` claims OUT_DIR receives
    `expected-seconds.txt` (it stays in the vendor workdir); root
    AGENTS.md lists 4 template formats while `templates/` has 5
    (`tutorial` is undocumented there). The check message `known: remotion,
    hyperframes` is hard-coded and will rot when a third vendor lands.
16. Exit code collision: argparse usage errors and `check` notes-only both
    exit 2. Scripts that branch on 2 must distinguish by output.
17. `voices/manifest.json` entries are never pruned, and `engines` is
    rebuilt from manifest lines, so a manifest whose lines were all
    regenerated under a new engine still reports the union over time
    correctly, but deleted-line entries linger and inflate the
    `<n> line voice(s) cached` note in check.
18. Lint temp frames accumulate in `out/.lint/` across runs.

## Open questions you might ask

- Why does check read the raw project.yaml without series merge? Would
  merging there (like validate does) remove the false FILL items on
  series episodes, and was raw reading chosen so check shows what the
  human still must write?
- The lint's character presence compares against the repo-root theme PNG
  while check validates the theme name against the vendor-local catalog.
  Should both read one catalog, and should the vendor be contract-bound
  to copy the theme where the lint can find it?
- `expected-seconds.txt` never reaches OUT_DIR, contradicting
  docs/vendor-contract.md. Should the contract change or should build.sh
  copy it out for platform-level duration checks?
- The visibility lint only checks the intersection of script and timeline
  ids. Should a timeline missing entries for script lines fail the build
  instead of silently shrinking coverage?
- TTS manifest never prunes entries for removed lines, and the cache hash
  bakes in nulls for unset model keys. Is there a cleanup or
  hash-versioning plan, or is manual `voices/` deletion the supported
  path?
- What is the intended third-vendor path? `check` hard-codes
  `known: remotion, hyperframes` and root AGENTS.md lists 4 formats while
  5 template dirs exist. Which file is the source of truth when they
  disagree?
- The lint animation check computes a delta but asserts nothing. Is there
  a planned threshold (like the -55 dB audibility line) for lip-flap or
  idle motion?
# 02 - Vendors: remotion and hyperframes

Reference for the two video engines under `vendors/`. Every fact below is read from the repo tree at its current commit (`a02c528`). Where the code and a doc disagree, both are stated. Nothing is projected.

## Sources read

| Area | Files |
|---|---|
| Shared | `docs/vendor-contract.md`, root `AGENTS.md`, `README.md`, `docs/project-yaml.md`, `docs/tutorial.md`, `tools/wayang.py` (lint section) |
| Remotion | `vendors/remotion/AGENTS.md`, `build.sh`, `scripts/map-project.mjs`, `engine/package.json`, `engine/video-settings.yaml`, `engine/config/{characters,defaults,script}.yaml`, `engine/scripts/{sync-script,sync-settings}.ts`, `engine/src/{index,Root,Main,config}.tsx/.ts`, `engine/src/components/{Character,Subtitle,SceneVisuals}.tsx`, generated `engine/src/data/script.ts` + `engine/src/settings.generated.ts`, `engine/public/` layout |
| Hyperframes | `vendors/hyperframes/AGENTS.md`, `build.sh`, `scripts/map-project.mjs` (every line), `scripts/package.json`, generated sample `.work/hf-demo/index.html` |
| Assets | `assets/backgrounds/` catalog, `assets/background/` generators |

---

## 1. Shared vendor contract (`docs/vendor-contract.md`)

### Entry point

```
vendors/<engine>/build.sh PROJECT_DIR OUT_DIR
```

- Wrong arg count: usage to stderr, exit 2. Both scripts run `set -euo pipefail`.
- Input: `PROJECT_DIR/project.yaml` (canonical, all timing in seconds). When the platform materialized series inheritance, `PROJECT_DIR/.merged.yaml` exists and both mappers prefer it.
- Required outputs: `OUT_DIR/video.mp4`, `OUT_DIR/timeline.json` shaped `{"lines": [{"id", "start", "end"}...], "total"}` (seconds), and `expected-seconds.txt`.
- Contract deviation: both build.sh scripts write `expected-seconds.txt` to the workdir only and never copy it to `OUT_DIR`. The duration guard reads it from the workdir, so it works, but the contract text ("Writes OUT_DIR/...expected-seconds.txt") is not literally honored.
- Idempotent: the workdir is deleted and rebuilt on every run.
- Error policy: unsupported canonical keys are a hard error, never a silent drop. Remotion enforces this fully. Hyperframes gates `vendor.hyperframes` keys but silently ignores unknown `settings.*` keys (see 4.3).
- The build log must name the audio source. Both mappers print `TTS source: <engines> (platform-generated voices)` or `TTS source: estimate`.

### Audio honesty (both vendors)

Priority order, never mixed within one project:

1. Platform-generated voices in `PROJECT_DIR/voices/`: one wav per line named `NN_<character>.wav` (NN = zero-padded line id, `padStart(2,"0")`) plus `voices/manifest.json` with `lines: {"NN_<character>.wav": {"seconds": ...}}` and `engines: [...]`. Coverage must be complete: one missing entry or file falls the whole project through to estimate. Bad `seconds` (non-finite or <= 0) is a hard error in remotion.
2. Estimate: durations from character count, silent placeholder audio, log says `estimate`.

`characters.<id>.voice` in canonical YAML is consumed by the platform (`tools/wayang.py` + `tools/tts_providers.py`), not by vendors. Vendors only see wavs + manifest.

### Guards the platform runs after a build

Duration guard (inside both build.sh scripts):

- `ffprobe -show_entries format=duration` of the rendered mp4 vs `expected-seconds.txt`.
- Pass window: `expected - 0.5 <= actual <= expected + 0.5` (awk comparison).
- Fail: `ERROR: rendered duration deviates from the computed timeline`, exit 1. Remotion names the bug class: "empty-tail bug".
- `ffprobe` missing: `WARNING: duration guard skipped`, build continues. Empty/missing expected file: guard skipped silently.

Visibility lint (`tools/wayang.py lint_project`, vendor-agnostic, runs after build inside `wayang.py render`):

- Reads `timeline.json` from the out dir. Missing or empty: `SystemExit(1)`, "the vendor must emit the timeline it renders".
- Reference frame extracted at `duration - 0.4s`. Per line, frame extracted at `start + dur * 0.6` (dur = timeline `end - start`).
- Subtitle band: centered, width = `settings.subtitle.max_width_percent` (55), bottom band height = `font.size * 1.5 * 2` above `bottom_offset` (40). Ink = pixel diff count vs reference frame. `< 150` diff pixels fails.
- Text card region: 15%-85% width, 15%-62% height. Checked only for lines with a text visual. `< 150` fails.
- Character corner box: `charH` (275) square at the bottom corner, 40px inset, side from `position`. Compared against the pure theme PNG (`assets/backgrounds/<theme>.png` resized to the frame). Presence `< charH*charH/60` fails.
- Audibility: when `voices/manifest.json` has engines (real voices), mean volume is probed at `mid + 0.21s`. `< -55 dB` fails the line.
- Pre-render layout check: subtitle band intersecting a character box fails before any frame extraction.

### Background themes

- Shared catalog: `assets/backgrounds/` at the repo root. Both mappers resolve it relative to their workdir (`workDir/../../../..`).
- Resolution order in both: project `assets/background.png` > named theme `settings.background` > default `riverbank`.
- `settings.background` must match `^[a-z0-9-]+$` (remotion) or be a string (hyperframes), and must exist in the catalog, else hard error listing available themes.
- Generators that make the themes: `assets/background/generate_themes.py`, `assets/background/generate_background.py`.

### Theme catalog (`assets/backgrounds/`)

11 synthesized PNG themes: `batik`, `chalkboard`, `kraft-paper`, `night-sky`, `notebook`, `riverbank`, `slate`, `studio`, `sunrise`, `whiteboard`, `wood-table`.

Note: `vendors/remotion/AGENTS.md` says the catalog lives at `vendors/remotion/assets/backgrounds/`. That directory does not exist. The real catalog is the repo-root one and that is what `map-project.mjs` reads.

---

## 2. Remotion vendor (`vendors/remotion/`)

### 2.1 Build pipeline (`build.sh`), step by step

1. Resolve absolute `PROJECT_DIR`, create absolute `OUT_DIR` (mkdir -p), locate `VENDOR_DIR`.
2. `WORK = vendors/remotion/.work/<project-basename>/`. `rm -rf $WORK`, `mkdir -p $WORK/public/voices`.
3. Copy engine source: `tar -C engine --exclude=node_modules --exclude=out -cf - . | tar -C $WORK -xf -`.
4. Symlink `engine/node_modules` into `$WORK/node_modules` (one-time `npm install` in `engine/` is a repo prerequisite).
5. Copy project assets into the engine's static root: `cp -R $PROJECT_DIR/assets/. $WORK/public/` (contents land at `public/` root). Done before mapping so existence checks and the renderer see the files.
6. `node $VENDOR_DIR/scripts/map-project.mjs $PROJECT_DIR $WORK` (see 2.2).
7. `(cd $WORK && npm run sync)` = `sync-settings` then `sync-script` (see 2.3).
8. `(cd $WORK && npx remotion render src/index.ts Main out/video.mp4)`. No concurrency, browser, or GL flags are passed.
9. Duration guard (ffprobe vs `$WORK/expected-seconds.txt`, 0.5s tolerance, see 1).
10. Copy `$WORK/timeline.json` and `$WORK/out/video.mp4` to `OUT_DIR`.

### 2.2 Mapper (`scripts/map-project.mjs`)

Input parsing:

- Prefers `.merged.yaml` over `project.yaml`. Missing file or YAML parse error: `die()` (exit 1 with `[map-project] ERROR:`).
- Reads `characters`, `script`, `settings`, `vendor.remotion`. Defaults: `fps` 30, `playbackRate` 1.2, `estimate_cps` 7.5.

Gates (all hard errors):

- `vendor.remotion`: only `estimate_cps` allowed. Unknown key dies.
- `settings`: allowed sections `video, font, subtitle, character, content` with exact key whitelists (see mapping table). Unknown section or key dies. `settings.background` is handled outside the gate.
- Script line referencing an unknown character dies. Empty script dies. No characters dies.
- `visual.src` and `se.src` must exist under `PROJECT_DIR` or die.
- `visual.type: terminal` needs `visual.command` or dies.

Settings conversion (snake_case canonical -> camelCase engine, defaults filled in):

| Section | Canonical keys accepted | Engine keys | Engine defaults |
|---|---|---|---|
| video | width, height, fps, playback_rate | width, height, fps, playbackRate | 1920, 1080, 30, 1.2 |
| font | family, size, weight, color | family, size, weight, color | "M PLUS Rounded 1c", 70, "900", "#ffffff" (+ engine-only outlineColor "character", innerOutlineColor "none") |
| subtitle | bottom_offset, max_width_percent, outline_width | bottomOffset, maxWidthPercent, outlineWidth | 40, 55, 14 (+ engine-only maxWidthPixels 1000, innerOutlineWidth 8) |
| character | height, use_images, images_base_path | height, useImages, imagesBasePath | 275, false, "images" |
| content | top_padding, side_padding, bottom_padding | topPadding, sidePadding, bottomPadding | 0, 0, 0 |

`maxWidthPixels`, `innerOutlineWidth`, `innerOutlineColor` exist in the engine defaults but have no canonical input key.

Characters -> `config/characters.yaml`: `{name, position (default "right"), color (default "#4B5563"), flipX (default false), defaultPauseAfter: 15}`. Position values are not gated to left/right here.

Script -> `config/script.yaml`: per line `{id, character, text}` plus optional `displayText`, `scene`, `pauseAfter` (`Math.round(pause_after * fps)` frames, only when set), `emotion`, `visual`, `se {src, volume default 1}`.

Visual conversion:

- `terminal` degrades to a text card: `{type: "text", text: "$ " + command, animation: visual.animation || "fadeIn"}`, plus optional fontSize/color. The simulated terminal is a hyperframes-only feature.
- `text`/`image` pass through with `font_size -> fontSize`, `color`, `outline_color -> outlineColor`, `animation`. `none` and missing visual produce no visual key.

Subtitle lint: visible chars = whitespace-stripped `text` length. Over 84 chars prints a WARNING ("wraps past 2 lines", Netflix TTSG standard of about 42 chars per line, 2 lines max). Warning only, never an error.

`config/defaults.yaml` (generated): `newLine: {character: <first line's speaker>, pauseAfter: 15, durationInFrames: 60, scene: 1, emotion: null}`, `automation: {voiceOnSave: false, autoVoiceFileName: true}`.

`video-settings.yaml` (generated): engineSettings above plus `colors: {background: "#ffffff", text: <font.color>, zundamon: <first char color>, metan: <second char color or first>}`. The `zundamon`/`metan` key names are upstream leftovers; they carry Momo/Kiki colors.

Voice handling -> `public/voices/`:

- Platform path: for every line, copy `voices/NN_<char>.wav` into the workdir, `durations[f] = Math.ceil(seconds * fps * playbackRate)`. Log names the engines.
- Estimate path: `visible = whitespace-stripped text length`, `seconds = visible / (cps * playbackRate)`, `frames = max(24, ceil(seconds * fps))`. Writes a silent 24kHz 16-bit mono placeholder wav of `frames/fps` seconds so every `<Audio>` resolves. Log says `estimate`.
- Writes `durations.json` (file -> frames) and `.source` (`platform` or `estimate`).

Timeline and expected length (frames, `adjusted(f) = Math.ceil(f / playbackRate)`):

- Per line window: `adjusted(durationInFrames)` speech + `adjusted(pauseAfter ?? 15)` pause. Cursor accumulates both.
- `timeline.json`: seconds, `start = cursor/fps`, `end = (cursor + speech)/fps`, each rounded to 3 decimals. `end` is the speech end, the pause is not included.
- `expected-seconds.txt`: `(60 + sum(speech + pause windows)) / fps`, 3 decimals. The 60-frame closing buffer matches Root.tsx.
- The comment states the intent: this is the exact timeline the renderer plays, so the platform lint probes the true windows.

Background: validates theme name against the repo catalog, then either keeps the project's `assets/background.png` (log: project custom override) or copies `assets/backgrounds/<theme>.png` to `public/background.png` (default `riverbank`).

### 2.3 Sync step (config -> generated TS)

`engine/package.json` scripts: `build` = `sync` + `remotion render src/index.ts Main out/video.mp4`, `start` = `sync` + remotion studio, `sync` = `sync-settings` + `sync-script` (both via ts-node). Dependencies: remotion ^4.0.0, @remotion/{bundler,cli,renderer}, @remotion/google-fonts ^4.0.409, budoux ^0.6.2, react 18, yaml 2.3.4.

`scripts/sync-settings.ts`: `video-settings.yaml` -> `src/settings.generated.ts` exporting `SETTINGS` (the YAML as const) and `AVAILABLE_IMAGES` (scan of `public/images/<id>/*.png`, one filename list per character id).

`scripts/sync-script.ts`: `config/script.yaml` + `config/characters.yaml` + `config/defaults.yaml` + `public/voices/durations.json` -> `src/data/script.ts` exporting:

- Types: `AnimationType` ("none" | "fadeIn" | "slideUp" | "slideLeft" | "zoomIn" | "bounce"), `VisualContent`, `SoundEffect`, `BGMConfig`, `ScriptLine` (emotion enum "normal" | "happy" | "surprised" | "thinking" | "sad"), `SceneInfo`.
- `bgmConfig: BGMConfig | null = null` (hardcoded null, BGM unwired).
- `scenes`: metadata only, `[{id: 1, Opening, gradient}, {id: 2, Main Content, solid}, {id: 3, Ending, gradient}]`.
- `CHARACTERS`: array of `{id, name, position, color, flipX}` from characters.yaml. Data-driven, any id works.
- `characterColors`: id -> color map.
- `scriptData`: each line enriched with `voiceFile = "NN_<character>.wav"`, `durationInFrames` from durations.json (fallback: `defaults.newLine.durationInFrames` = 60), `pauseAfter` (fallback: `defaults.newLine.pauseAfter` = 15).

### 2.4 Engine runtime architecture

Composition chain: `src/index.ts` (`registerRoot`) -> `Root.tsx` -> single `<Composition id="Main">` -> `Main.tsx`.

`Root.tsx`:

- Total frames = sum over lines of `ceil(durationInFrames / playbackRate) + ceil(pauseAfter / playbackRate)` + 60 closing buffer. First line starts at frame 0, no opening buffer.
- This per-line rate adjustment (instead of summing raw frames) is the port's fix for the empty-tail bug at rate > 1; commit `118fa17`.
- Composition `fps`/`width`/`height` come from `SETTINGS.video` with `config.ts` VIDEO_CONFIG (1920x1080@30) as fallback.

`Main.tsx` (one component, no Sequences for visuals; it derives state from `useCurrentFrame()`):

- Walks `scriptData` accumulating rate-adjusted frames to find the current line, its start frame, its scene, and `isSpeaking` (frame is inside the speech window, not the pause).
- Renders, in order: full-frame background `Img` (`staticFile("background.png")`, object-fit cover); BGM `<Audio>` only if `bgmConfig` is non-null (never); per-line `<Sequence from={startFrame} durationInFrames={adjusted speech}>` containing the voice `<Audio src=voices/<voiceFile> playbackRate={SETTINGS.video.playbackRate}>` and an optional se `<Audio src=se/<src> volume={volume ?? 1}>`, with `premountFor={fps}`; `<SceneVisuals>` for the current line's visual; `CHARACTERS.map(...)` to `<Character>` (isSpeaking and emotion only for the current speaker, others get "normal"); a `<Subtitle>` Sequence spanning only the speech window with `displayText ?? text`.
- `sceneInfo = scenes.find(...)` is computed and never used. The visible background is the single static `background.png` for the whole video. The `scene` key has no visual effect in the current code, despite the AGENTS.md mapping row "1..3 have named backgrounds".

`Character.tsx`:

- Looks up its config in `CHARACTERS`; unknown id renders null.
- Mouth flap while speaking: `Math.floor(frame / 5) % 2 === 0` (about 6 flips per second at 30fps).
- Gentle bob while speaking: `sin(frame * 0.3)` mapped to -3..3 px vertical.
- Slide-in on mount: from -200px (left) or +200px (right) to 0 over 0.5s, clamped.
- Art path: `<imagesBasePath>/<id>/<file>`; `useImages` false renders a 200x300 rounded placeholder box in the character color with the character name.
- Emotion art resolution (existence-checked against `AVAILABLE_IMAGES`): `<emotion>_<open|close>.png` -> `<emotion>_open.png` -> `mouth_<open|close>.png`.
- `flipX` applies `scaleX(-1)`.
- Leftover: placeholder emoji picks "zundamon"/"metan" icons by hardcoded id, any other id gets a speech-bubble emoji.

`Subtitle.tsx`:

- Bottom-centered, width `maxWidthPercent`% capped at `maxWidthPixels`, `bottomOffset` from the bottom.
- Per-line script-aware wrapping: CJK lines (regex on hiragana..halfwidth katakana, CJK blocks) are segmented with BudouX (segments rendered as inline-block nowrap spans), other scripts use normal word wrap. Plus `text-wrap: balance` and `overflow-wrap: anywhere`. Commit `dede006`.
- Two text layers: stroke layer behind (`WebkitTextStroke` at `subtitle.outlineWidth` px, `paintOrder: stroke fill`) and fill layer in front.
- `font.outlineColor` special value `"character"` resolves to the speaking character's color; `innerOutlineColor`/`innerOutlineWidth` settings are not consumed anywhere.
- Fade-in over 0.15s. Font size never auto-shrinks.

`SceneVisuals.tsx`:

- Animations over ~0.3s: fadeIn, slideUp (+50px Y), slideLeft (+100px X), zoomIn (scale 0.8->1), bounce (spring, damping 15, stiffness 100), none.
- Container area: top 60, left 80, right 80, bottom 180 (hardcoded; `SETTINGS.content` paddings are generated but no component reads them).
- Image visual: `<Img src=staticFile(content/<src>)>` object-fit contain. Note the `content/` prefix (see 4.2).
- Text visual: centered, `fontSize` default 64, bold, outline stroke at `fontSize * 0.16` px in `outlineColor` default `#1F2937` (dark outline so text survives light backgrounds, commit `44c926e`).

`config.ts`: `VIDEO_CONFIG` fallbacks, `COLORS` palette (engine-level), `CharacterId = string` (data-driven port change), empty `characterSpeakerMap`.

`engine/public/` layout: `background.png` (default riverbank, overwritten by the mapper each build), `bgm/.gitkeep` (unwired), `content/.gitkeep` (image visual root), `se/.gitkeep` (sound effects), `voices/` created per build (`NN_<char>.wav`, `durations.json`, `.source`), `images/<character_id>/mouth_open.png` + `mouth_close.png` + optional `<emotion>_open.png`/`<emotion>_close.png`.

Checked-in `config/` samples: `characters.yaml` (momo right #37474F, kiki left #F9A825), `defaults.yaml` (sample pauseAfter 12; the mapper always regenerates it with 15), `script.yaml` (6-line Bahasa Malaysia sample with zoomIn/slideLeft/bounce text cards). `video-settings.yaml` mirrors the generated shape with `playbackRate: 1.2`.

### 2.5 Canonical -> engine mapping (every row from AGENTS.md, with mapper behavior)

| canonical | engine target | behavior |
|---|---|---|
| meta.language | - | ignored, informational |
| characters.<id>.name | characters.yaml name | subtitle placeholder, placeholder box label |
| characters.<id>.position | characters.yaml position | "left" or "right", default "right", not gated |
| characters.<id>.color | characters.yaml color | subtitle outline + placeholder box, default #4B5563 |
| characters.<id>.flip_x | characters.yaml flipX | scaleX(-1), default false |
| characters.<id>.image | public/<path> | ship art under project assets/, set settings.character.use_images true |
| characters.<id>.voice | (platform) | vendor consumes voices/NN_<id>.wav + manifest |
| script[].text | script.yaml text | spoken line, estimate length basis |
| script[].display_text | script.yaml displayText | subtitle override |
| script[].scene | script.yaml scene | 1..3 documented as named backgrounds; in code it only feeds the unused sceneInfo |
| script[].pause_after | script.yaml pauseAfter | seconds -> frames (`round(*fps)`), default 15 frames |
| script[].emotion | script.yaml emotion | normal/happy/surprised/thinking/sad, art variant fallback chain |
| script[].visual | script.yaml visual | type text/image/none; font_size->fontSize; dark outline by default, outline_color overrides; terminal degrades to a "$ command" text card |
| script[].se | script.yaml se | src relative to public/ (played from `se/<src>`), volume default 1, existence-checked |
| settings.background | public/background.png | theme from repo catalog, project file wins, default riverbank |
| settings.* | video-settings.yaml | snake->camel, unknown keys error |
| vendor.remotion.estimate_cps | timing estimate | chars/sec, default 7.5 |

### 2.6 What degrades, what errors (remotion)

Degrades:

- Terminal visuals become plain text cards.
- Scene ids above 3 (and scene generally) have no background effect.
- Missing emotion art falls back mouth_open/close.
- No platform voices -> silent placeholder wavs, estimated timing.
- Subtitles over 84 visible chars -> build-time warning only.
- ffprobe absent -> duration guard skipped with warning.

Hard errors: unknown settings section/key, unknown `vendor.remotion` key, unknown character in script, missing visual/se asset, no characters, empty script, unparseable/missing project.yaml, background not matching `^[a-z0-9-]+$` or not in catalog, bad manifest seconds.

Not supported, stated in AGENTS.md: background music (hook exists, hardcoded off), positions other than left/right.

### 2.7 playback_rate (remotion)

- `settings.video.playback_rate` -> `SETTINGS.video.playbackRate`, default 1.2.
- Voice `<Audio playbackRate={rate}>` (Remotion time-stretches the wav), line and pause windows are `ceil(frames / rate)` in both Main.tsx scheduling and Root.tsx total.
- Platform voice durations are stored rate-inflated (`ceil(seconds * fps * rate)`) then divided back out.
- Estimate quirk: the estimate path divides by the rate twice, once in `seconds = visible / (cps * rate)` (mapper line 242) and again in `adjusted()` (line 254). At the default 1.2 an estimated line window is about 31% shorter than the platform path would give for the same text (`visible/(cps*rate^2)` vs `visible/cps`). At rate 1.0 the two agree.

---

## 3. Hyperframes vendor (`vendors/hyperframes/`)

### 3.1 Build pipeline (`build.sh`), step by step

1. Same arg handling, `WORK = vendors/hyperframes/.work/<project>/`, `rm -rf $WORK`.
2. Copy `PROJECT_DIR/voices` -> `$WORK/voices`, `PROJECT_DIR/assets` -> `$WORK/assets` (directory itself, unlike remotion's contents-into-public).
3. `npm install --prefix $VENDOR_DIR/scripts --silent` (installs the mapper's single `yaml` dependency from `scripts/package.json`: `wayang-hyperframes-mapper`, private, type module, yaml ^2.4.0).
4. `node $VENDOR_DIR/scripts/map-project.mjs $PROJECT_DIR $WORK` -> `index.html`, `package.json`, `expected-seconds.txt`, `timeline.json`, `fonts/`, plus background/voices/images copies.
5. `(cd $WORK && npx --yes hyperframes@latest render --output $WORK/out.mp4 -f 30)`. First run downloads the hyperframes CLI and Chromium (bundled Puppeteer) + system ffmpeg does the encode.
6. Duration guard: ffprobe vs `$WORK/expected-seconds.txt`, 0.5s tolerance, same wording and ffprobe-missing warning as remotion.
7. Copy `$WORK/timeline.json` and `$WORK/out.mp4` -> `$OUT_DIR/video.mp4`.

### 3.2 Mapper (`scripts/map-project.mjs`), full behavior

Parsing and gates:

- Prefers `.merged.yaml`. Missing/parse error dies.
- Defaults: `cps` 7.5, `playbackRate` 1 (differs from remotion's 1.2), `fps` 30, `W` 1920, `H` 1080, font family "Inter", size 70, weight "900", charH 275, subtitle width 55%, bottom 40.
- `vendor.hyperframes`: only `estimate_cps` allowed, unknown keys die.
- `settings.background` must be a string if present.
- No settings-section gate exists: unknown `settings.*` keys are silently ignored (difference from remotion, see 4.3).
- Lines 75-77 contain an empty `for (const line of script) {}` loop: dead code, no effect.
- There is no image-visual existence check (unlike remotion). A missing image src is copied as a broken reference and renders as a missing image. A missing se file crashes `fs.copyFileSync` with an uncaught exception (non-zero exit, stack trace, not a `die()` message).

Voices and timeline (unit: seconds throughout):

- Platform path: manifest must cover every line, `voiceSeconds[file] = manifest.seconds`.
- Estimate path: `raw = max(0.8, visible_chars / cps)`.
- `dur = raw / playbackRate`. `pause = (pause_after ?? 0.5) / playbackRate`. Default pause 0.5s equals remotion's 15 frames at 30fps.
- `subEnd = start + dur + pause` (subtitle stays up through the pause).
- Cursor adds `dur + pause`. `total = round(t + 2, 3)`: 2s tail, same as remotion's 60 frames at 30fps.
- `timeline.json`: `{id, start, end}` with `end` = speech end only, plus `total`.
- `expected-seconds.txt` = `total`.

Background: the theme PNG is always copied first (`assets/backgrounds/<theme>.png` -> `$WORK/background.png`), then the project's `assets/background.png` overwrites it when present. Default `riverbank`. Unknown theme dies.

Asset copies: project `voices/` -> `$WORK/voices`, project `assets/images/` -> `$WORK/images` (build.sh already copied the whole assets dir; the mapper's copy normalizes the images path).

Font handling (remotion difference): the mapper downloads the requested Google font at map time. `curl` of `fonts.googleapis.com/css2?family=...:wght@<weight>` (15s timeout, Chrome UA), first `woff2` URL extracted, downloaded to `fonts/text.woff2` (20s timeout), declared with `@font-face`. Any failure: warn, fall back to system fonts. Remotion instead loads a hardcoded Google font via `@remotion/google-fonts/MPLUSRounded1c` regardless of `settings.font.family`.

Geometry / overlap detection:

- Subtitle box: width `W * max_width_percent/100`, height `fontSize * 1.5 * 2` (2-line standard), horizontally centered, bottom `bottom_offset`.
- Character boxes: `charH` square at the bottom corner with 40px inset on the character's side.
- If the subtitle box intersects a character box, the subtitle moves up: `subY0 = min(subY0, box.y0 - 24 - subH)`, final bottom clamped to 0. Movement is logged (`overlap: subtitle moved above characters`).
- `tools/wayang.py` runs the same intersection check as a lint failure, so the mapper's fix keeps the lint green.

### 3.3 Generated composition (`index.html`)

Shell:

- `<div id="root" data-composition-id="main" data-start="0" data-duration="<total>" data-width="<W>" data-height="<H>">`.
- GSAP 3.14.2 from the pinned CDN `cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js`, used only to register an empty timeline: `const tl = gsap.timeline({ paused: true }); window.__timelines["main"] = tl; <tweens> tl.seek(0);`.
- Global CSS resets margins, sets body to exactly WxH with `overflow: hidden`, `#root` full size with the font family.

Clip model (authoring rules learned from the renderer's lint, per the mapper header):

- Every timed element is `class="clip"` with `data-start` and `data-duration` (seconds) and a stable `id`. Media without an id renders silent, hence the named audio ids.
- Every visual clip is a full-frame wrapper `<div class="clip" id="clip-N" data-start data-duration data-track-index style="position:absolute;inset:0;z-index:<z>">`; content is positioned inside the wrapper so the runtime's full-frame `.clip` rule cannot distort placement (commit `1932e7c`).
- Track/z-index layout:

| track | z | content |
|---|---|---|
| 0 | 0 | background img, full duration, object-fit cover |
| 5 | 5 | visual cards: terminal window, image card, text card |
| 10 | 10 | character base: art (mouth_close) or placeholder box, full duration |
| 11 | 11 | lip flap open/close imgs, 0.2s slices during speech |
| 20 | - | voice `<audio class="clip" id="line-<id>-audio">` with `data-playback-rate` |
| 21 | - | se `<audio class="clip" id="line-<id>-se">` with `data-volume` |
| 30 | 30 | subtitle div |

Characters:

- `use_images` (default false) AND `images/<id>/mouth_close.png` present -> art mode: one base `mouth_close` img for the full duration (track 10) plus, for each of the character's speaking segments, alternating `mouth_open`/`mouth_close` slices (track 11): `k` walks from `seg.start` to `seg.end` in `min(0.2, remaining)` steps, toggling open/close. This is the lip flap: 0.2s alternation, about 5 flaps per second.
- Otherwise a 200x300 rounded placeholder box in the character color with the name, full duration, no flap.

Per line:

- Voice audio element: `src="voices/<NN>_<char>.wav"`, `data-start`, `data-duration = dur` (already rate-scaled), `data-playback-rate = playbackRate`, track 20.
- se (optional): file copied from the project preserving its relative `src`, duration probed with ffprobe (`probeSeconds`, any error falls back to 1.5s), `data-duration = min(probed, dur + pause_after)`. Note: the pause here is the raw value, not divided by playbackRate. `data-volume = volume ?? 1` (2 decimals, honored by the runtime), track 21.
- Subtitle div (track 30): bottom `<subBottomFinal>`px, centered, width pct, font family/size/weight from settings, color `font.color` default `#ffffff`, `-webkit-text-stroke` at `fontSize * 0.2` px in `font.outline_color` default `#1F2937`, `paint-order: stroke fill`, `overflow-wrap: anywhere`, `text-wrap: balance`, `line-height: 1.4`. Runs from `start` to `subEnd` (speech + pause).
- Text card (track 5): `font_size` default 84, `inset: 0 0 25% 0` (upper 75% of frame), stroke `0.16 * size` px, `outline_color` default `#1F2937`, `white-space: pre-wrap`, `text-wrap: balance`.
- Image card (track 5): centered with translate(-50%,-50%), `max-width: 70%`, `max-height` = `font_size` clamped to `H * 0.45` (font_size doubles as a max-height override for images), object-fit contain, radius 12, `src` relative to the workdir (project assets live at `assets/...` in the workdir).

### 3.4 Terminal simulation (`visual.type: terminal`)

One clip (track 5, z 5) spanning `start` to `subEnd`, containing:

- Window: absolute at `top: 12%`, horizontally centered, `width: 76%`, background `#161B22`, 2px border `#30363D`, radius 12, large drop shadow, `overflow: hidden`.
- Title bar: `#21262D`, three 13px dots `#FF5F56` / `#FFBD2E` / `#27C93F`, label "wayang" in `#8B949E` 20px.
- Body: padding 22px 28px, font-size 34px (`termFs`), line-height 1.55, color `#C9D1D9`, `overflow-wrap: anywhere`.
- Command line: `<span style="color:#7EE787">$ </span>` prompt followed by one `<span class="ch" style="opacity:0">` per character of `visual.command` (missing command dies).
- Command typing tween: `tl.to("#cmd-N .ch", { opacity: 1, duration: 0.02, stagger: <step>, ease: "none" }, <typeStart>)` where `typeStart = seg.start + 0.35` and `typeDur = clamp(cmdChars * 0.035, 0.6, 1.6)`, `stagger = typeDur / cmdChars.length`. Characters appear left to right over at most 1.6s.
- Output lines (`visual.output`, array): one div per entry, opacity 0, color `#9EAEBC`, `margin-top: 12px`, font-size 30px, `white-space: pre-wrap`. Reveal tween: `tl.to("#out-N-i", { opacity: 1, duration: 0.18 }, <seg.start + 0.9 + i * 0.5>)`. The first output appears 0.55s after typing starts, further outputs every 0.5s.
- Min-height math: `charsPerLine = max(20, floor((W * 0.76 - 56) / (34 * 0.62)))`, `cmdLines = ceil(len / charsPerLine)`, `minH = 30 + (cmdLines + outs.length) * 34 * 1.7`. This `minH` is computed and then never used: the window div style carries no min-height. It is dead code (plausibly a casualty of the unclosed-div fix in commit `7a59c6b`).
- Wrapping: both command and outputs rely on `overflow-wrap: anywhere` / `pre-wrap` rather than clipping (commit `b530b92` replaced clipping with wrapping).

Terminal steps degrade to a plain text card in the remotion vendor; this simulation is hyperframes-only.

### 3.5 playback_rate (hyperframes)

- `settings.video.playback_rate`, default 1. Honored end to end as of commit `a02c528`: voice audio plays at the rate via `data-playback-rate`, line durations and pauses are divided by the rate, the composition `data-duration` and `expected-seconds.txt` scale to match. 0.9 is the documented "slower, calmer tutorial pace".
- AGENTS.md contradiction: the first timing paragraph says "`playback_rate` is ignored by this vendor (audio plays at natural speed)" while the next paragraph and the code honor it. The "ignored" sentence is stale.
- Characters have no per-character voice rate; `characters.<id>.voice` only feeds the platform TTS.

### 3.6 Canonical -> composition mapping (AGENTS.md rows)

| canonical | composition | behavior |
|---|---|---|
| meta.language | - | ignored |
| characters.<id>.name/color/position | placeholder box or art position | left or right, 40px inset, default right, color default #4B5563 |
| characters.<id>.voice | voices/NN_<id>.wav | platform-generated, manifest durations |
| script[].text / display_text | subtitle div per line | outlined, bottom-centered, word wrap, display_text wins |
| script[].scene | - | not a concept, visuals play per line |
| script[].pause_after | subtitle/card tail | seconds, default 0.5, divided by playback_rate |
| script[].emotion | - | no effect, "needs emotion art variants; otherwise invisible" |
| script[].visual.type text | centered text card | dark outline default, outline_color override |
| script[].visual.type image | centered image card | src relative to the project/workdir, no existence gate |
| script[].visual.type terminal | simulated terminal | typing + output reveals, GSAP tweens |
| script[].se | per-line audio clip | src project-relative, ffprobe duration (1.5s fallback), data-volume honored |
| settings.background | background.png | theme from shared catalog, riverbank default, project file wins |
| settings.font / subtitle / character | CSS values | family/size/weight/color, bottom_offset/max_width_percent/outline_color, height/use_images |
| settings.video | root data-* + timing | width, height, fps (render -f), playback_rate |
| vendor.hyperframes.estimate_cps | timing estimate | chars/sec, default 7.5 |

---

## 4. Differences between the vendors

### 4.1 Capability matrix

| Area | Remotion | Hyperframes |
|---|---|---|
| Render model | React components, frame-by-frame, Remotion CLI | One static index.html, HyperFrames CLI + Puppeteer + ffmpeg |
| Timing unit | Frames (fps from settings) | Seconds |
| Default playback_rate | 1.2 | 1 |
| Estimate floor per line | 24 frames (0.8s at 30fps) | 0.8s |
| Default pause | 15 frames (0.5s) | 0.5s |
| Tail | 60 frames (2s) | 2s |
| Terminal visual | Degrades to "$ command" text card | Full simulation (typing, outputs, window chrome) |
| Emotions | Art variants with fallback chain | No effect |
| Scenes | Metadata only, no render effect | Not a concept |
| BGM | Hook exists, hardcoded off | None |
| se handling | `<Audio>` in the line Sequence, volume from canonical | Separate audio clip, probed duration, data-volume, missing file crashes uncaught |
| Image visual location | `staticFile(content/<src>)` under public/content/ | Workdir-relative src (project assets/...) |
| Image visual existence check | Yes, dies | No |
| Unknown settings.* keys | Hard error | Silently ignored |
| Fonts | @remotion/google-fonts, hardcoded M PLUS Rounded 1c regardless of settings | Downloads settings.font at map time, @font-face, system fallback |
| Subtitle wrapping | BudouX for CJK, word wrap + balance + anywhere for the rest | overflow-wrap anywhere + text-wrap balance |
| Lip flap | Render-frame driven, ~6 flips/s (frame/5) | 0.2s clip slices (~5/s) |
| Character animation | Slide-in, bob while speaking | Static img swap only |
| Subtitle/character overlap | Not handled in-engine; platform lint fails it | Mapper moves the subtitle above the box and logs it |
| Config generation | YAML configs + two TS sync scripts | Direct HTML string assembly |
| node dependencies at build | engine/ install (shared, symlinked) | scripts/ yaml install each run (cached) |
| Workdir asset convention | project assets/. -> public/ root | project assets/ -> workdir assets/, voices -> workdir voices |

### 4.2 Path conventions worth remembering

- Remotion image visuals: mapper checks `PROJECT_DIR/<visual.src>`, build.sh copies project assets into `public/` root, but the renderer loads `public/content/<visual.src>`. For the image to actually render, the src must line up with the `content/` prefix. This is a latent mismatch for `assets/...`-style srcs; the hyperframes vendor has no such prefix.
- Both mappers resolve the theme catalog via `workDir/../../../..` -> repo root. Moving a vendor deeper breaks it.
- Hyperframes se `data-duration` uses `dur + pause_after` with the raw pause, not the rate-scaled pause.

### 4.3 Contract compliance deltas

- "Errors on unsupported canonical keys": remotion enforces for settings + vendor keys. Hyperframes enforces vendor keys only; unknown settings keys pass silently.
- "Writes OUT_DIR/expected-seconds.txt": neither vendor copies it out of the workdir.
- Remotion logs `TTS source: ...` in the mapper; hyperframes does the same. Both satisfy the "build log names the audio engines" rule.

---

## 5. Environment requirements

Remotion vendor:

- Node 24 + npm (docs and README). One-time `npm install` in `vendors/remotion/engine/`; the build symlinks that node_modules into the workdir.
- `ffprobe` on PATH for the duration guard; skipped with a warning when absent.
- Network for @remotion/google-fonts font loading at render.
- Render command uses defaults: no concurrency, browser, or GL flags anywhere in the repo.

Hyperframes vendor:

- Node 22+, ffmpeg, network. First `npx --yes hyperframes@latest` run downloads the CLI and Chromium.
- GSAP loads from the pinned jsdelivr CDN on every render of the composition.
- Font download needs network at map time (curl, 15s + 20s timeouts); failures degrade to system fonts with a warning.
- ffprobe for se durations (1.5s fallback on error) and the duration guard.

Platform side: uv + Python for `tools/wayang.py`, PIL for lint image diffing, ffmpeg/ffprobe for guards, lint, and frame extraction.

TTS: `REVOLAB_API_KEY` (default) or `OPENAI_API_KEY`. Without a key everything renders silent with estimated timing, labeled in the log.

## 6. Known slowness

Verified finding: the repo contains no screenshot-fallback, heap, or worker tuning notes. A search over the current tree and the full git history (screenshot, heap, worker, concurrency, gl=, maxWorkers) returns nothing. The only cost facts in code:

- Hyperframes first run pays the npx CLI download plus a Chromium fetch; GSAP and the Google font are fetched per build unless HTTP-cached.
- Hyperframes renders frame by frame through Puppeteer.
- Remotion renders with default concurrency and no tuning flags.
- Fonts fall back silently rather than failing the build (hyperframes), so a network blip can produce a visually degraded render instead of an error.

If such notes existed elsewhere (a runbook outside this repo), they are not in the tree or the history.

## 7. Drift and dead code observed (read from source)

- `vendors/remotion/AGENTS.md` points at `vendors/remotion/assets/backgrounds/`; that directory does not exist. The catalog is repo-root `assets/backgrounds/`.
- Hyperframes `AGENTS.md` says playback_rate is ignored, then documents it as honored; the code honors it.
- Remotion `AGENTS.md` claims scenes 1..3 have named backgrounds; `Main.tsx` computes `sceneInfo` and never uses it.
- Terminal `minH` is computed and never emitted (hyperframes mapper).
- Empty `for` loop over script lines (hyperframes mapper lines 75-77).
- Remotion engine leftovers from upstream: `zundamon`/`metan` color key names in generated `colors`, zundamon/metan emoji picks in the placeholder box.
- Remotion settings generated but unconsumed: `content.*` paddings, `subtitle.maxWidthPixels` is consumed, `innerOutlineColor`/`innerOutlineWidth` are not.
- `expected-seconds.txt` stays in the workdir; the contract says OUT_DIR.

## Open questions you might ask

1. Remotion image visuals: the renderer loads `public/content/<src>` while the mapper validates `PROJECT_DIR/<src>` and build.sh copies assets into the `public/` root. Which src convention should projects use, and should the mapper either prepend `content/` or drop the prefix?
2. Is the remotion estimate path's double playback-rate division intentional (`visible/(cps*rate)` then `ceil(frames/rate)`)? At the default 1.2 it shortens estimated lines about 31% relative to the platform-voice path.
3. Which hyperframes AGENTS.md sentence is stale: "playback_rate is ignored" or the honoring paragraph plus `data-playback-rate` code? (Code says honored since commit a02c528.)
4. Should the remotion vendor implement scene backgrounds (the AGENTS.md row and the unused `scenes`/`sceneInfo` suggest a planned feature), or should scene be dropped from its mapping table?
5. The hyperframes terminal `minH` is computed but never applied to the window div. Was it dropped during the unclosed-div fix (commit 7a59c6b), and should short terminal windows reserve height again?
6. Where should per-vendor performance notes (screenshot fallback, heap, worker tuning) live? The task expectation assumes they exist; nothing is in the tree or git history.
7. Should `expected-seconds.txt` actually be copied to OUT_DIR to match the contract, or should the contract stop listing it as an OUT_DIR artifact?
8. Hyperframes silently ignores unknown `settings.*` keys while the contract mandates erroring on unsupported canonical keys. Should the mapper get the same settings gate remotion has?
# 03 - Templates, content, docs, and art

Reference for the four template formats, the mascot cast, the art and
background pipelines, the documentation set, and the demo projects.
Sources read in full: templates/*/template.yaml, templates/*/README.md,
AGENTS.md, README.md, docs/*.md, assets/mascots/generate_mascots.py,
assets/background/generate_themes.py, assets/background/generate_background.py,
projects/video-tutorial/*, schema/project.schema.json, tools/wayang.py,
vendors/*/scripts/map-project.mjs. Commit a02c528, 2026-09-27.

## Entry docs

- `AGENTS.md` - agent manual and router. Defines the layout, the five-step
  workflow (`templates` -> `init` -> `check` -> edit -> `validate` ->
  `render`), and the invariants: canonical YAML with second timing, unknown
  keys error, vendors ship `build.sh PROJECT_DIR OUT_DIR` plus
  `timeline.json` and `expected-seconds.txt`, duration guard at 0.5s
  tolerance, series deep-merge where the episode wins per key, check before
  render with FILL items relayed in plain words.
- `README.md` - human entry. Lists the formats, mascots, the 11 background
  themes, the vendor model, requirements (Node 24 + npm, uv,
  ffmpeg/ffprobe, one-time `npm install` in `vendors/remotion/engine`),
  TTS engines (`revolab` via `REVOLAB_API_KEY`, `openai` via
  `OPENAI_API_KEY`, silent estimated-timing fallback), and the series
  command.

## The template formats

Five directories live under `templates/`. The root docs name four formats
(dialog, presentation, storytelling, community). `tutorial` is the fifth,
built for the hyperframes vendor. Every template renders as-is after
`wayang.py init`; the template.yaml is a working sample.

| format | sample title | hosts | lines | scenes | pauses (s) | emotions | card style | vendor | playback_rate | background | font size |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dialog | Kenalan dengan Momo & Kiki | Momo right + Kiki left | 6 | 3 | 0.4, last 1.0 | none | text card on alternating lines (zoomIn, slideLeft, bounce) | remotion | 1.2 | unset (engine default riverbank) | 70 |
| presentation | Tabiat Pagi | Momo only | 6 | 3 | 1.2, last 1.0-1.5 | none | card on 5 of 6 lines (zoomIn, slideLeft, slideUp) | remotion | 1.2 | unset | 70 |
| storytelling | Harta Karun Kecil | Momo + Kiki | 6 | 3 | 0.4-0.6, last 1.0 | surprised, thinking, happy sprinkled on 4 lines | mood cards on 4 of 6 lines | remotion | 1.2 | unset | 70 |
| community | Meetup Komuniti | Momo + Kiki | 6 | 3 | 0.4, last 1.0 | none | cards on 4 of 6 lines (bounce, zoomIn, slideLeft) | remotion | 1.2 | unset | 70 |
| tutorial | Cara Guna Wayang | Momo as teacher | 10 | 3 | 0.8-2.0 | none | 4 text cards + 6 `type: terminal` steps | hyperframes | 0.9 | slate | 66 |

All sample scripts are Bahasa Malaysia (`meta.language: ms`). Pacing
differs by design: dialog is quick banter, presentation gives cards time
to breathe, tutorial slows to 0.9 so terminal steps stay readable.

### What every template.yaml contains

- `meta`: `title`, `template`, `vendor`, `language: ms`, `description`.
- `characters`, keyed by id:
  - `momo`: name Momo, color `#37474F`, position right, voice
    `{engine: revolab, voice_id: paan-f695215e}`.
  - `kiki`: name Kiki, color `#F9A825`, position left, voice
    `{engine: revolab, voice_id: nur-b184422b}`.
- `script`, one entry per spoken line: `id`, `character`, `text` (spoken
  and subtitled), `scene` (groups lines into sections), `pause_after`
  (seconds), optional `emotion`, optional `visual`.
  - `visual.type: text`: `text`, `font_size` (84-96), `color: #ffffff`,
    `animation` (zoomIn, slideLeft, slideUp, bounce, fadeIn).
  - `visual.type: terminal` (tutorial only): `command` plus `output`
    (list of lines). Hyperframes renders a typing animation in a terminal
    window; on remotion the terminal degrades to a command text card.
- `settings`:
  - `video`: 1920x1080, fps 30, `playback_rate` (1.2 everywhere except
    tutorial 0.9; slows voice and pacing).
  - `font`: family `M PLUS Rounded 1c`, size 70 (66 in tutorial), weight
    900, color `#ffffff`.
  - `subtitle`: `bottom_offset: 40`, `max_width_percent: 55`,
    `outline_width: 14`.
  - `character`: `height: 275`, `use_images: true`.
- `vendor`: `estimate_cps: 7.5` (characters per second for the no-TTS
  timing estimate), under the vendor name.

### What the user fills vs what is preset

Preset by the template: resolution, fps, playback_rate, font, subtitle
geometry, character height, image mode, estimate_cps, sample scenes and
cards. Fills that are the user's (per `docs/project-yaml.md` and the
README fill order):

1. `meta.title`.
2. Per character: `name` and the `voice` block (revolab `voice_id`, or
   openai `voice`).
3. Script lines: `text`, speaker, `scene`, `pause_after`, optional cards.

Optional per line: `display_text` (overrides the subtitle text),
`emotion`, `visual`, `se` (sound effect). Optional per character:
`flip_x` when art faces the wrong way. Optional in settings:
`background`. READMEs give one fill order in three steps: characters,
script, settings. Character art is optional; without it characters render
as colored placeholder boxes.

README quirks: dialog and community share their fill-order text, and
community carries a leftover dialog sentence ("walk through a topic in
2-3 scenes with big text cards."). The storytelling README has an honesty
note: emotions change drawn art only and are invisible with placeholder
boxes.

## The mascot cast

| character | species | YAML color | drawn colors | position | revolab voice_id | persona in sample scripts |
|---|---|---|---|---|---|---|
| Momo | Malayan tapir | `#37474F` | body `#2F2F38`, cream saddle and belly `#F7F3E8` (`CREAM`), dark ears with cream tips, pink blush `#EFA3AC` | right | `paan-f695215e` | "tapir paling ceria" (cheerful) |
| Kiki | hornbill | `#F9A825` | body `#3A3230`, wings `#4A403C`, beak `#F2A93B`, casque `#E8862B`, white tail fan `#F6F2E9`, eyelash strokes | left | `nur-b184422b` | "tak pernah senyap" (never quiet) |
| Rimau | chibi Malayan tiger | `#F57C00` (`ORANGE`) | orange body, black `#262626` stripes (forehead, cheeks, body, tail), cream muzzle, paws, belly, whisker dots | right in the tutorial walkthrough | `ali-13002bfa` (docs/tutorial.md only) | eager explorer in the tutorial walkthrough |

Rimau is the third mascot, added in commit 9155a65. No template ships
Rimau; he exists in the generator, in docs/tutorial.md's walkthrough, and
in stale vendor workdirs (`vendors/remotion/.work/rimau-intro/`). Rimau
reuses Momo's round eye set for every emotion (same face geometry).

### Art inventory on disk

- `templates/{dialog,presentation,storytelling,community}/assets/images/{momo,kiki}/`:
  10 PNGs per character: `mouth_open/close`, `happy_open/close`,
  `sad_open/close`, `surprised_open/close`, `thinking_open/close`. 20 per
  template.
- `templates/tutorial/assets/images/momo/`: the same 10, momo only.
- `projects/video-tutorial/assets/images/momo/`: the same 10.
- `assets/mascots/`: the generator plus 4 checked-in SVG sources
  (`momo_open/close.svg`, `kiki_open/close.svg`). These SVGs are early
  drafts: each carries an opaque background rect `#CFE9B8`, while current
  generator output renders transparent. The generator writes its current
  SVGs to `/tmp/mascot-art/`, not to this directory.
- `projects/rimau-intro/assets/images/rimau/`: deploy target for 10 rimau
  PNGs. Does not currently exist on disk.

## The art pipeline

- Generator: `assets/mascots/generate_mascots.py` (943 lines, 3
  characters).
- Approach: one Python function per character builds an SVG body string.
  The mouth is a swappable group; the `_open` and `_close` variants
  render the same body with a different mouth group string, so every
  pixel outside the mouth is identical by construction. `docs/mascot-art.md`
  names this pair consistency as the reason for code over image models:
  two image-model generations never align.
- Render: cairosvg `svg2png`, 1024x1024, transparent background
  (`bg=None`), atomic writes (tempfile then `os.replace`). SVG sources go
  to `/tmp/mascot-art/` (base), `/tmp/mascot-art/emotions/`,
  `/tmp/mascot-art/rimau/`.
- Emotion system: `EMOTIONS = ("happy", "surprised", "thinking", "sad")`.
  An emotion variant swaps the eye/brow group and the mouth group; the
  body is the base body. Per character: 1 base pair + 4 emotion pairs =
  10 PNGs. Output: 4 base + 16 emotion PNGs for momo/kiki plus 10 rimau
  PNGs per run.
- File naming the renderer requires (under
  `assets/images/<character_id>/` in the project): `mouth_open.png`,
  `mouth_close.png`, optional `<emotion>_open.png`, `<emotion>_close.png`
  (happy, surprised, thinking, sad). All frames of one character must
  share one canvas size. Art faces the viewer, else set `flip_x: true`
  on the character.
- Verification, all in-script and failing loudly:
  - `check_frame`: 1024x1024, four corner pixels alpha 0 (transparent).
  - `verify_pair`: full pixel diff of two frames; the diff bbox must sit
    inside the mouth box (open vs close) or the face box (emotion vs
    base), and must be non-empty. Boxes are per-character constants
    (`EMO_DIFF_BOX`, `FACE_BOX`).
  - `check_character_presentation`: ink bbox margins over 20px, ink
    center within 60px on x and 80px on y of canvas center, and mouth
    color counts inside the mouth box: open frames need over 200 maroon
    `#7A3B44` px and over 30 tongue `#E98A96` px; close frames need both
    under 20.
- Deployment: `deploy_emotions()` copies momo/kiki emotion PNGs into the
  four templates in `TEMPLATE_NAMES` plus
  `projects/rimau-intro/assets/images/`. `deploy_rimau()` writes the 10
  rimau PNGs (renamed to the renderer scheme) into
  `projects/rimau-intro/assets/images/rimau/`. The tutorial template is
  not in `TEMPLATE_NAMES`, so its momo emotion art is never refreshed by
  a rerun.
- Regenerate:
  `uv run --with cairosvg --with pillow assets/mascots/generate_mascots.py`
- Image-model alternative (`docs/mascot-art.md`): usually looks richer.
  Workflow: generate ONE front-facing full-body base character, plain
  background, flat vector style; get the closed mouth by one
  inpaint/edit pass on the mouth area only, never a second full
  generation; export both states at one canvas size (1024x1024 fine);
  emotion variants are face inpaints from the same base frame. Renderer
  requirements are identical to the code path: PNG, one canvas size per
  character, exact file names, viewer-facing art or `flip_x: true`.

## The background theme catalog

11 PNGs in `assets/backgrounds/`, all 1920x1080: batik, chalkboard,
kraft-paper, night-sky, notebook, riverbank, slate, studio, sunrise,
whiteboard, wood-table.

- `assets/background/generate_themes.py` builds 10 of them (all but
  chalkboard). One builder function per theme, flat-vector SVG,
  deterministic geometry, cairosvg render, atomic write, then per-theme
  pixel probes: exact coordinates plus expected color with a tolerance,
  a mismatch raises and fails the run.
- `assets/background/generate_background.py` is the older single-theme
  script that produced chalkboard: green board `#2d5a3d` on a white
  room, 24px wooden trim `#8B4513` with grain streaks, 8 chalk smudge
  ellipses, geometry matching the remotion `Main.tsx` board contract
  (board inset top 40, sides 60, bottom 160). Checks: white room
  corners, green board center, wooden trim sample. Its output path is
  `vendors/remotion/engine/public/background.png`.
- Studio is the strengthened theme and the largest file (149KB vs 9-20KB
  for the rest): white radial-gradient spotlight center falling to
  `#9FB0BA` at the edges, a stage floor band from 72% height (`#B7C4CC`)
  with an 8px darker edge line, and two spotlight pools on the floor.
- Slate is the tutorial default: flat `#263238` with 6 faint white smudge
  ellipses at 0.05 opacity, chosen as terminal-friendly.
- Batik carries the Malaysian identity: cream `#F5EDD8` with top and
  bottom bands of rotated brown petal ellipses around red `#A63D2F`
  dots.
- Stale paths: both scripts hardcode output under
  `/mnt/data/work/content_engine/`, the repo name before the wayang
  rename (commit 848d28e). Running them as-is writes outside this repo.
- How `settings.background` resolves (remotion `map-project.mjs`):
  project `assets/background.png` override > named theme PNG from repo
  root `assets/backgrounds/` > engine default `riverbank`. The name must
  match `^[a-z0-9-]+$`; an unknown theme kills the map with the
  available list. The chosen PNG is copied into the engine and read as
  `staticFile("background.png")`.
- `tools/wayang.py`: the visibility lint loads
  `ROOT/assets/backgrounds/<theme>.png` (default riverbank when unset)
  as the reference image for the character-corner presence check, and
  warns plus skips when the PNG is missing. `validate` checks the theme
  name against `vendors/<vendor>/assets/backgrounds`, but only when that
  directory exists; no vendor ships one, so the check is currently a
  no-op. `schema/project.schema.json` types `background` as a plain
  string, no enum.

## The docs set

- `docs/tutorial.md` - for beginners. Follows a real run that adds Rimau
  and renders his intro. Seven steps:
  1. `wayang.py templates` - pick a format.
  2. `wayang.py init presentation rimau-intro` - copy template into
     `projects/` (gitignored, yours).
  3. `wayang.py check` - preflight in plain words, `FILL:` = fix,
     `NOTE:` = advice, exit codes 0 ready / 1 blockers / 2 notes only.
  4. Fill `meta.title`, character `name` + `voice`, script lines (YAML
     examples, Rimau voice `ali-13002bfa`, revolab lists ids at
     `GET /v1/voices`).
  5. `wayang.py validate` - strict gate: schema plus references.
  6. `wayang.py render` - one command: per-line wavs (cached),
     mapping, render, visibility lint.
  7. Optional character art, with the two ways to make it (code
     generator, image models) and the 0.2s lip-flap rule.
  Ends with a failure table of 4 rows: missing `voice.engine`, silent
  estimated-timing renders, timeline drift ("re-render, else file an
  issue"), unknown theme, plus pointers to backgrounds, `se:` and
  `visual.type: image`, series, and `AGENTS.md`.
- `docs/mascot-art.md` - for art makers. States the shipped art is
  script-drawn SVG, not image-model output, and why (mouth-pair
  consistency). Covers the generator, sources, cairosvg renderer,
  regenerate command, the self-check list, steps to add a new character
  to the generator, the full image-model workflow, the renderer's file
  requirements, and a backgrounds section pointing at
  `assets/background/` plus the project-level `assets/background.png`
  override.
- `docs/project-yaml.md` - the canonical YAML reference. Sections
  (`meta`, `characters`, `script`, `settings`), voice engine fields
  (revolab `voice_id`; openai `voice`, `model`, `speed`,
  `instructions`), script line fields (`display_text`, `se`, `emotion`,
  `visual`), `settings.background` resolution, the three user fills,
  and series inheritance (`init-series`, deep-merge, episode wins per
  key, `render projects/<series>` renders all episodes in order).
- `docs/vendor-contract.md` - for engine authors. The deal:
  `vendors/<engine>/build.sh PROJECT_DIR OUT_DIR`, read
  `project.yaml` (prefer `.merged.yaml` when series was materialized),
  write `video.mp4`, `timeline.json`
  (`{"lines": [{"id","start","end"}...], "total"}`),
  `expected-seconds.txt`, exit 0, idempotent workdir, error on
  unsupported canonical keys. Platform guards after each build:
  duration via ffprobe against expected-seconds at 0.5s tolerance, and
  the visibility lint (subtitle ink, card ink, character in corner
  boxes, real-voice lines over -55 dB). Background catalog resolves
  relative to the vendor workdir. Per-vendor env notes: Remotion needs
  Node 24 and `npm install`; Hyperframes needs Node 22+, ffmpeg, and
  downloads its CLI plus Chromium on first run.

## Demo projects

`projects/` holds one project: `video-tutorial`. (`.gitignore` covers
`projects/` and `out/`, so this state is local-only, not in git.)

- `projects/video-tutorial/` - an `init` of the tutorial template with
  the YAML unchanged from `templates/tutorial/template.yaml`. Fully
  rendered state:
  - `out/video.mp4`: 43.8s, 1.8MB.
  - `out/timeline.json`: 10 lines, start 0 to end 40.667, total 43.778s
    (matches the mp4 inside the 0.5s guard).
  - `out/.lint/`: 21 probe frames (`f1`-`f10` plus `b` variants and
    `tail.png`) from the visibility lint.
  - `voices/`: `01_momo.wav` to `10_momo.wav`, all revolab (1.8-3.7s
    each), plus `manifest.json` with per-line hash, seconds, engine.
  Demonstrates: the tutorial format end to end, a hyperframes render
  with simulated terminal steps, revolab TTS, and cached voice reuse.
- `projects/rimau-intro` does not exist, though the mascot generator
  deploys into it and docs/tutorial.md walks through creating it.
  `vendors/remotion/.work/` holds stale workdirs from earlier builds
  (`rimau-intro`, `emotion-demo`, `ep01`, `dialog-ms`,
  `presentation-test`, `est-demo`, `fixture-project`), so Rimau and
  emotion renders ran before the projects were cleaned.

## Open questions you might ask

1. Both background generator scripts still write to hardcoded
   `/mnt/data/work/content_engine/` paths from before the wayang rename.
   Should they be repointed at this repo (and should
   `generate_background.py` still target
   `vendors/remotion/engine/public/background.png`)?
2. `wayang.py validate` checks `settings.background` against
   `vendors/<vendor>/assets/backgrounds`, a directory no vendor ships,
   making the check a no-op. Should it point at the root
   `assets/backgrounds/` catalog instead?
3. The tutorial template is missing from `TEMPLATE_NAMES` in
   `generate_mascots.py`, so its momo emotion art never refreshes on
   regeneration. Intended, or should the tutorial ship kiki art too?
4. Rimau has no Revolab voice in any template; the only voice id is
   `ali-13002bfa` in docs/tutorial.md. Which voice id is canonical, and
   should Rimau art ship in templates like momo and kiki do?
5. The checked-in SVG sources under `assets/mascots/` carry an opaque
   green `#CFE9B8` background while current generator output is
   transparent. Are they drafts to replace, or reference copies to keep?
6. The community README reuses the dialog README's fill-order text,
   including a leftover dialog sentence about 2-3 scenes and text cards.
   Copy leftover to fix?
7. Should the remotion vendor implement the `terminal` visual natively
   instead of degrading it to a command text card, so tutorial projects
   render the same on both vendors?
# 04 - History and decisions

Reference for the owner. Covers the full commit chronology, the rumpun
campaign state and directives, the two multi-model consults, the bug
classes fixed along the way, the rename, and what is deliberately kept
out of git.

Sources: `git log` (38 commits, one branch `main`, remote
`https://github.com/khursani8/wayang.git`), `.rumpun/` (rumpun.yaml,
seasons/s1.yaml, ledger/directives.jsonl, prompts/base/, runs/), README.md,
AGENTS.md. Note: `.rumpun/runs/` is gitignored, so the raw review
documents exist only on disk. The adopted decisions survive in git through
the ledger and commit 5ecfebc.

## Build timeline in one paragraph

The repo was built in one day: 38 commits between 11:52:40 and 23:47:25
(+0800) on 2026-09-26, all authored `sani <sani@local>`, all on `main`,
no branches, no merges, no reverts. The work ran as a rumpun campaign
(season s1) with a written operator directive and an append-only ledger.
The arc: MVP with a ported engine, pluggable TTS, series support,
original mascots and Malay identity, rendering correctness guards, a
second engine, a two-model structure review and restructure, the rename
to Wayang, then beginner onboarding (tutorial doc, tutorial template,
final lint hardening).

## Commit chronology

Times are +0800, 2026-09-26. Oldest first.

### Phase 1 - MVP and TTS (11:52-12:14)

| hash | time | what it delivered |
|---|---|---|
| dafeabf | 11:52 | content_engine MVP: `schema/project.schema.json` (canonical YAML, timing in seconds), `templates/education` + `templates/community`, `vendors/remotion` (patched port of nyanko3141592/remotion-voicevox-template with data-driven characters, `build.sh PROJECT_DIR OUT_DIR` contract, estimate TTS fallback), `tools/ce.py` (init/validate/render, uv PEP 723), the whole `.rumpun/` campaign state. E2E verified: both templates rendered to mp4 on estimate timing. |
| 2fd0e74 | 12:07 | Pluggable TTS: `tools/tts_providers.py` (voicevox + openai clients, stdlib only), `ce.py tts` command + auto-tts in render, per-line manifest (hash, seconds, engine), resumable, vendor consumes `projects/<p>/voices` when present. OpenAI path NOT verified against the live API (no key on the box, stated in the commit). |
| e38feb6 | 12:07 | gitignore `__pycache__` (a `.pyc` had leaked into 2fd0e74). |
| 3ed0923 | 12:12 | revolab TTS provider (`api.revolab.ai/v1/tts`, default model nada-1.0-pro, native wav 24 kHz), verified with real synthesis E2E: 6 live lines, community-test rendered with real audio. Recorded that `nada-1.0-flash` (from the operator's curl example) does not exist; valid models are nada-1.0-pro and aisyah-1.0-pro. |
| c64a503 | 12:14 | remotion mapper drops its voicevox-only voice gate. Engine validation is the platform's job (provider registry in ce.py); without this, revolab/openai projects could not render. |

### Phase 2 - Series, templates, mascots (12:33-13:11)

| hash | time | what it delivered |
|---|---|---|
| b340fee | 12:33 | Series support: `series.yaml` sparse base deep-merged under each episode (episode wins per key, dicts merge, lists replace), merge-then-validate, batch validate/tts/render in name order stopping at first failure, `init-series`, render materializes `.merged.yaml` so vendors never see series. Proven by a negative test: remove series.yaml and ep02 fails with required name/voice errors. |
| b8fa6f3 | 12:45 | Templates renamed by format, not topic: `education` -> `dialog`, added `presentation` (1 presenter + cards) and `storytelling` (hosts + emotions). All ran on the engine unchanged. |
| 34d5bc9 | 13:04 | Identity switch: dropped the upstream zundamon/metan pair. Original mascots Momo (tapir, revolab voice paan-f695215e) and Kiki (hornbill, nur-b184422b), Bahasa Malaysia sample scripts (`language: ms`), generated SVG-derived lip-flap art shipped per template, generator sources kept in `assets/mascots/`. |
| ddf97aa | 13:11 | Mascot art re-rendered with transparent backgrounds after operator feedback (solid rectangles looked wrong over the chalkboard). Generator now asserts corner alpha is zero and that open/close pairs differ only inside the mouth region. |
| 477ff3f | 13:11 | gitignore `.omc` state (session-state files had leaked, including under `assets/mascots/`). |

### Phase 3 - Rendering correctness (13:20-13:48)

| hash | time | what it delivered |
|---|---|---|
| dede006 | 13:20 | Subtitle wrapping: BudouX-JA wraps Japanese but emitted near-whole-line segments for Latin text, which then overflowed the centered container. CJK keeps BudouX, other scripts wrap at word boundaries, `text-wrap: balance`, `overflow-wrap: anywhere`, no auto-shrink, build-time warning past ~84 visible chars. Rules follow Netflix TTSG (~42 chars/line, max 2 lines). |
| 118fa17 | 13:31 | Empty-tail fix: `Root.tsx` summed raw frames while playback ran at `ceil(frames / playbackRate)`, so at rate 1.2 the composition ran ~17% longer than the timeline (3.7s of empty chalkboard on dialog-ms). Root now sums per-line adjusted frames plus one 60-frame closing buffer (the upstream 60-frame opening buffer was dead weight). 26.37s -> 20.67s, matching 620 computed frames. |
| 859f006 | 13:48 | Duration regression guard: mapper writes `expected-seconds.txt` (sum of per-line rate-adjusted frames + 60-frame tail), `build.sh` ffprobes the output and exits 1 on >0.5s deviation. Any repeat of the empty-tail bug class is now a loud build error. |

### Phase 4 - Backgrounds and polish (14:01-16:25)

| hash | time | what it delivered |
|---|---|---|
| 109e0fc | 14:01 | Chalkboard background as a generated 1920x1080 PNG (`assets/background/generate_background.py`, SVG + cairosvg, self-checked pixels), replacing flat divs in `Main.tsx`. Project can override with `assets/background.png`. |
| 5b83b25 | 14:47 | Theme system: `generate_themes.py` synthesizes 10 themes (whiteboard, night-sky, kraft-paper, batik, notebook, sunrise, studio, riverbank, slate, wood-table), catalog at `vendors/remotion/assets/backgrounds/`, `settings.background` resolves custom file > named theme > engine default, unknown themes error. |
| 3690719 | 14:54 | gitignore: untrack root `.omc/` session state (had been committed since dafeabf). |
| 44c926e | 14:57 | Text cards get a subtitle-style outline (`visual.outline_color`, stroke 0.16x font size) because flat white cards vanished on light themes like riverbank. |
| 888f0dd | 16:12 | README refresh for cloners: real state of the repo, fresh-clone install steps. |
| bf5fe5c | 16:25 | Engine default background becomes riverbank; chalkboard stays selectable. |

### Phase 5 - Identity purge (17:24-17:37)

| hash | time | what it delivered |
|---|---|---|
| 23f1b82 | 17:24 | All Japanese removed from the remotion engine: upstream ja sample wavs/art/configs deleted, engine configs rewritten to momo/kiki in Bahasa Malaysia, every Japanese comment and log line translated. "Malaysian repo, Malaysian content." |
| e9e709a | 17:37 | VOICEVOX removed as a TTS provider (provider class, schema branch, `generate-voices.ts` 230 lines, build branch, all doc mentions). TTS engines are revolab and openai only; keyless builds fall back to estimates. |

### Phase 6 - Second engine and the visibility lint (17:59-18:24)

| hash | time | what it delivered |
|---|---|---|
| 10748ba | 17:59 | hyperframes vendor, the second engine, onboarded with zero `ce.py` changes: `AGENTS.md` + `build.sh` + `map-project.mjs`, canonical YAML -> one `index.html` composition (data-* clips, seconds-based), lip flap as alternating 0.2s mouth clips, estimate fallback, explicit errors (never silent drops) for unsupported se/image visuals/scenes, same duration guard. |
| 1932e7c | 18:11 | HyperFrames authoring rules learned from the first broken render: media without a stable `id` renders silent, the runtime's full-frame `.clip` rule fills unset dimensions (once stretched Momo to 1920px wide), fonts need `@font-face` (mapper now downloads the Google font woff2 at map time). Added deterministic subtitle/character overlap detection. |
| b264afe | 18:12 | gitignore `vendors/*/.work/`: the hyperframes workdir (generated HTML, fonts, wavs, out.mp4) had been committed with 10748ba and 1932e7c when shells ran from the wrong cwd. Purged here. |
| 95bc2f2 | 18:18 | Visibility lint, vendor-agnostic, in `ce.py`: recomputes the timeline from the project YAML, extracts frames at each line midpoint, checks subtitle ink, text-card ink, per-corner character animation, and per-line voice loudness (real voices must exceed -55 dB; estimate renders skip and are labeled). `render` runs it automatically, `ce.py lint` re-runs it. Proven: silent windows measure -91 dB. |
| a097776 | 18:24 | Lint stops recomputing: estimate renders quantize per-line frames, so recomputed windows drifted past the render end and failed later lines. Both vendors now emit `timeline.json` (the renderer's own math, exact start/end per line) and the linter consumes it, falling back to the formula only when absent. Missing frames fail with a message instead of crashing. |

### Phase 7 - Structure review and capability completion (18:48-19:43)

| hash | time | what it delivered |
|---|---|---|
| 5ecfebc | 18:48 | The structure restructure (details below): shared background catalog at `assets/backgrounds/` (11 PNGs moved out of `vendors/hyperframes/assets/`, per-vendor copies deleted), root `AGENTS.md` cut from 119 lines to a ~40-line router with deep rules split into `docs/vendor-contract.md` and `docs/project-yaml.md`, vendor manuals trimmed to engine deltas, new `ce.py check` preflight (plain-words FILL items, GLM's exit scheme 0/1/2, `--json`), linter fallback formula deleted (timeline.json now required). |
| 19c4cfd | 19:22 | hyperframes gains `script[].se` (per-line sound effects, ffprobe duration, own track) and `visual.type image` (centered image card); the se/image gates and not-supported errors removed; hf-demo exercises both. Also regenerated `studio.png` (contrast). |
| 5c324d4 | 19:43 | Mascot emotion art: 16 emotion frames (happy, surprised, thinking, sad x open/close x Momo/Kiki), pairs verified pixel-identical outside the face box, shipped in all templates; `docs/mascot-art.md` documents the no-image-model pipeline and the image-model alternative with its pair-consistency trade-off. |

### Phase 8 - Rename (20:28-21:51)

| hash | time | what it delivered |
|---|---|---|
| 848d28e | 20:28 | Rename to Wayang (details below). |
| e247071 | 21:51 | Upstream repo reference (nyanko3141592) removed from `rumpun.yaml` and `vendors/remotion/AGENTS.md`. Commit history still contains the name. |

### Phase 9 - Onboarding and final hardening (22:29-23:47)

| hash | time | what it delivered |
|---|---|---|
| 9155a65 | 22:29 | Rimau the tiger, third mascot (chibi Malayan tiger, #F57C00): base lip-flap pair + four emotion pairs, all pair-verified. Also fixes the mascot generator's deploy root, stale since the rename. rimau-intro rendered with real Revolab voices. |
| 8d018d2 | 22:36 | `docs/tutorial.md`: clone to first MP4 in seven steps, following the real Rimau run, with a failure table. |
| 0b96a81 | 23:03 | Visibility lint v2 (details below) + the fifth template, `tutorial` (6 simulated terminal steps, Momo with emotions). |
| b530b92 | 23:10 | Terminal steps: font 24 -> 34px, window to 76% width, per-character GSAP stagger typing so long commands wrap instead of clipping; caret dropped. |
| 7a59c6b | 23:25 | Terminal window fix: one missing closing `</div>` (details below). |
| e9561b4 | 23:41 | Tutorial shows the fill example explicitly: a terminal step displays the exact YAML to write, so the FILL warning is paired with its fix. |
| a02c528 | 23:47 | `settings.video.playback_rate` honored by hyperframes (voice clip data-playback-rate, pauses and timeline scale, timeline.json/expected-seconds reflect it). Tutorial template ships at 0.9x (43.55s vs 39.27s at 1.2x). |

## The campaign: `.rumpun/`

`.rumpun/` is committed (except `runs/`, see the gitignore section) and
its git history is the campaign's evolution ledger. Layout per
`.rumpun/README.md`: `rumpun.yaml` (campaign config), `seasons/` (one
YAML per season), `ledger/` (append-only evidence), `prompts/base/`
(phase prompt templates), `runs/` (per-season workspaces, gitignored),
`adhd-rules.md` (output-style card, verbatim from
github.com/ayghri/i-have-adhd), `CHANGELOG.md` (campaign schema
versions; schema 1 only).

### rumpun.yaml (campaign config)

- Goal: build content_engine as a framework-agnostic YAML-template video
  platform, `vendors/<engine>/AGENTS.md` as the engine contract agents
  consume, remotion first.
- Metric: E2E - `ce.py init education demo` -> fill project.yaml ->
  `ce.py render projects/demo` -> mp4 with no manual fixes.
- Autonomy: stage `manual`; promote after 5 clean audits; demote on 2
  consecutive rejects; rejection rolls back to last good, pauses,
  escalates after 2.
- Review panel: families `[fable, glm, gpt-5.6-sol]`, majority rule,
  blinded.
- Invariants: goal_immutable, budget_cap, falsify_required.
- Budget: campaign cost cap 600.
- Routes: glm, claude (unsets all ANTHROPIC model/base-url overrides so
  fable serves), and a codex fleet (gpt-6-astra/sol/luna, gpt-reserve,
  gpt-5.6-sol/terra/luna, gpt-5.5, codex-auto-review), all
  `codex exec --dangerously-bypass-approvals-and-sandbox`.

### seasons/s1.yaml (the seed season)

- Goal: ship the MVP (education + community templates, canonical schema,
  remotion vendor with AGENTS.md contract, ce.py init/validate/render).
- Mode: fight. Methodology line: contract-first platform, three-model
  design consult (codex gpt-5.5, glm-5.3, fable) before schema freeze,
  then build and prove with a real render.
- Pipeline: phase design-review (writers answer
  `prompts/base/design-brief.md`) -> phase integrate (evaluate ->
  `runs/design-decisions.md`).
- Writers: codex on gpt-5.5 (knowledge: none), glm on glm-5.3
  (knowledge: none), fable (knowledge: full). 15 minutes each. Stop on
  all_exited.

### Ledger directives (`.rumpun/ledger/directives.jsonl`)

Convention: the ledger is append-only. Entries keep status `pending` even
after execution; closure is recorded by a new entry, never by editing old
ones. Directive 6 is that closure.

| seq | demanded / recorded | status |
|---|---|---|
| 0 | Operator directive: build the content_engine MVP end to end, no questions. Education + community templates, canonical YAML schema, vendors/remotion port with AGENTS.md, tools/ce.py. Consult codex + glm-5.3 + fable before schema freeze. | Executed (dafeabf, plus the consult records). Closed by seq 6. |
| 1 | s1 outcome record: MVP built and E2E-verified. education smoke-test -> 19.5s / 1.7MB / 585 frames mp4; community-test -> 18.9s mp4 with arbitrary character ids. TTS honestly labeled "estimate" (VOICEVOX not installed). Consult outcomes recorded; codex round 2 returned empty output. | Historical record. Closed by seq 6. |
| 2 | TTS is user-managed API providers, the platform owns no docker/service. Pluggable voice engines in the canonical schema, implement openai (OPENAI_API_KEY) + the existing voicevox endpoint. Platform tts step writes voice files; vendor consumes them, falls back to estimate. | Executed (2fd0e74). voicevox provider itself was later removed (e9e709a). Closed by seq 6. |
| 3 | Record: revolab provider added and verified E2E (nada-1.0-pro, wav 24 kHz, 6 voices through the platform path). `nada-1.0-flash` from the operator's example is not a valid model; API exposes nada-1.0-pro and aisyah-1.0-pro. openai provider implemented but unverified (no key). | Revolab done. The openai-unverified caveat stays open. |
| 4 | Record: series support (series.yaml fragment + episodes, deep merge episode-wins, merge-then-validate, batch in name order stopping at first failure, init-series, meta.series/episode schema fields). Inheritance proven by a negative test. | Executed (b340fee). Closed by seq 6. |
| 5 | TODO: background theme catalog duplicated per vendor (remotion + hyperframes copies). Move to one shared location all vendors reference, delete the copies. Same policy for future shared vendor assets. | Recorded in 10748ba, the commit whose hyperframes vendor created the duplicate catalog copy. Executed in the structure review (5ecfebc): single catalog at `assets/backgrounds/`. Closed by seq 6. |
| 6 | Closure: directives 0-5 all executed and verified. Known-open at closure: openai provider unverified against the live API (no key), mascot emotion art, hyperframes se/image-visual support, studio theme contrast. | Of the four open items: emotion art (5c324d4) came after closure, hyperframes se/image visuals shipped in the same commit as the closure entry (19c4cfd) while still listed as open, and no later entry records studio contrast as resolved (studio.png was regenerated in 19c4cfd). openai remains unverified. |

Open items as of the last ledger entry: the openai TTS provider has never
been run against the live API, and studio theme contrast has no recorded
resolution.

## The three-model design consult (season s1, before schema freeze)

Prompt: `prompts/base/design-brief.md`. Four questions, 120-word answers:
canonical shared schema vs per-vendor YAML, no-TTS timing fallback and
its pitfalls, what breaks with a second engine and what vendor AGENTS.md
must pin, single-file vs split YAML. Records in `.rumpun/runs/`:
`codex-review.md`, `codex-review-2.md`, `glm-review.md`,
`design-brief.md`, consolidated in `design-decisions.md`.

### What each model said

- codex (gpt-5.5, round 1): answered in question-protocol form and asked
  the one meta-question: "Do you want project.yaml to be stable across
  engines, even when a vendor loses features?" The operator's directive
  said no questions, so the session answered yes. That answer is decision
  1: canonical YAML is the stable contract. Round 2 was requested and
  returned empty output (`codex-review-2.md` contains only the stdin
  notice). No third round was attempted.
- glm-5.3 (full written review): canonical schema + per-vendor mapping -
  per-vendor YAML forks N templates x M engines that diverge quietly;
  canonical gives one validation point and vendor switch = change
  `meta.vendor`; `vendor: {}` keys that alter timing should be rejected
  at validation. Estimate fallback: character count / per-language rate
  plus punctuation pauses with a floor, and the pitfalls: never mix
  timing sources in one timeline, per-language rates stay rough, the
  quiet fallback is the worst error so tag every duration with its
  source, cache real durations keyed by hash(text, speaker_id). Second
  engine breaks: units (frames vs seconds), position must be an enum,
  visuals need a small canonical vocabulary, typography must be pinned.
  Vendor AGENTS.md must pin six things: input, timing, voice,
  capabilities (unsupported features error, never drop), output (mp4,
  exit codes, idempotent re-run), environment. Single file over split:
  one YAML, one validate, one diff; overlays merged by ce.py if a
  project ever outgrows one file.
- fable (full repo knowledge): estimate fallback details (per-project
  chars-per-second, minimum frame floor, silent placeholder wavs so the
  engine's Audio elements resolve), `flip_x` as a canonical character
  key so art orientation ports, and a minimal-diff upstream port with
  characters injected as a generated CHARACTERS export.

### Adopted (10 decisions in `runs/design-decisions.md`)

1. Canonical schema, per-vendor mapping (codex meta-answer, glm
   concurred).
2. Canonical timing unit: seconds, vendors convert to frames (glm).
3. Unknown keys error, never dropped silently (glm).
4. No mixing timing sources in one timeline (glm).
5. Duration source labeled in every build log (glm).
6. Position is an enum left|right (glm).
7. Small visual vocabulary with a fixed animation set (glm).
8. Estimate fallback: per-project cps, min frame floor, silent
   placeholder wavs (fable).
9. `flip_x` canonical character key (fable).
10. Engine port keeps upstream code minimal-diff, data-driven characters
    via generated export (fable).

All 10 were adopted; nothing from the consult was declined. The
decisions are visible in the shipped schema (seconds timing, unknown-key
errors, position enum, `vendor: {}` gate) and in the build-log source
labeling.

## The structure review (GLM 5.3 x fable, commit 5ecfebc)

Trigger: `runs/structure-brief.md` (fable-authored) with six known
concerns: background catalog duplicated per vendor, root AGENTS.md
mixing routing with deep contracts (119 lines), no preflight command
(onboarding by schema error), estimate/timeline math in three places
with the linter still carrying a fallback formula, engine/ keeping
upstream sample configs that could drift, and workdir artifacts
leaking into commits twice.

### What each reviewer recommended

GLM (`runs/glm-structure-review.md`) named the root anti-pattern:
canonical things COPIED instead of REFERENCED (catalogs, vendor
contracts, timeline math, engine configs each exist twice). Six moves:
delete both vendor catalog copies into one `assets/backgrounds/`, cut
root AGENTS.md to a ~40-line router with deep rules in
`docs/project-yaml.md` + `docs/vendor-contract.md`, trim vendor manuals
to deltas, delete the linter fallback formula (timeline.json required),
delete engine/ sample configs, one shared `work/` root. It also designed
`ce.py check`: cheap blockers first then guidance, imperative wording
with zero schema vocabulary, exit 0 clean / 1 blockers / 2 notes only,
`--json` for agents. Layering principle: prose that must be read to
prevent a violation is a defect, move that rule into ce.py.

fable (`runs/fable-structure-review.md`, written pre-GLM): keep the
vendor contract (`AGENTS.md` + `build.sh` + mapper - two vendors
onboarded with zero ce.py changes), keep the output-truth guards
(timeline.json + duration guard + visibility lint), keep format-named
templates. Restructure lean on the same four points (router AGENTS.md,
shared catalog, single source for engine configs, delete the fallback
formula). Add `ce.py check` as the guidance layer: plain-language FILL
report plus environment state, ending in a READY / NOT READY verdict,
while `validate` stays the strict gate.

### Adopted (recorded in `runs/structure-decisions.md`)

1. One background catalog at `assets/backgrounds/`, vendor copies
   deleted, both mappers resolve it relative to their workdir.
2. Root AGENTS.md becomes a ~40-line router; deep rules move to
   `docs/vendor-contract.md` and `docs/project-yaml.md`.
3. Vendor AGENTS.md files keep engine deltas only and point at
   `docs/vendor-contract.md`.
4. Linter requires timeline.json; the fallback formula is deleted and a
   missing timeline fails the lint with a clear message.
5. `ce.py check` gains GLM's exit scheme (0 clean, 1 blockers, 2 notes
   only) and `--json`; the agent workflow now runs check before render
   and relays FILL items in plain words.

### Declined, with recorded reasons (to prevent relitigating)

- Single `work/` root for all vendors: churn, no agent benefit; the
  per-vendor ignore rules (`vendors/*/.work/`) were already proven
  across re-renders.
- Deleting `engine/` config samples: map-project writes configs into
  disposable workdirs, so they cannot drift into builds; they serve
  standalone engine use only.

Implementation sequence, as recorded: catalog dedupe -> linter fallback
removal -> docs split -> check exit codes and `--json` -> full re-render
sweep (est-demo, dialog-ms, hf-demo) -> commit and push.

## Bug classes found, fixed, and what each taught

- Unclosed terminal window div (7a59c6b). The rewritten tutorial
  terminal block never closed its window div, so every clip after the
  first terminal step nested inside that overflow:hidden window and was
  clipped out of view: the video showed content only for the first two
  lines, while the duration guard stayed green. One closing tag fixed
  it. Taught: generated markup needs a structural check (div balance
  must equal 0, now run on every render), and a green timing guard does
  not mean a correct video.
- Visibility-lint parity bug (0b96a81). The v1 character check compared
  a line-mid frame against the tail frame, but the 0.2s lip flap put
  both frames on the same flap state for about half of all lines, so
  the check failed on luck. Rewritten: character presence is measured
  against the theme PNG scaled to the render (present character samples
  ~2490 px, empty corner ~0, threshold charH^2/60, measured on live
  frames); flap animation became an informational delta, not a gate;
  frame extraction is clamped inside the render duration. Taught:
  animation makes frame-vs-frame comparison nondeterministic, diff
  against ground truth instead.
- Timeline drift on estimate renders (a097776, completed in 5ecfebc).
  The lint recomputed per-line windows from the YAML formula, but
  estimate renders quantize frames, so windows drifted past the render
  end and later lines probed tail-only frames. Fix: vendors emit
  timeline.json with the renderer's own math, build.sh ships it next to
  video.mp4, the linter consumes it, then the fallback formula was
  deleted outright so a missing timeline is a hard lint error. Taught:
  never let the checker recompute what the renderer already computed.
- Empty tail / playback-rate mismatch (118fa17, guarded by 859f006).
  Inherited from upstream: Root.tsx summed raw durationInFrames +
  pauseAfter while playback ran each line at ceil(frames/playbackRate),
  so rate 1.2 produced a composition ~17% longer than the timeline
  (3.7s empty chalkboard). Fixed by summing per-line adjusted frames
  plus one closing buffer, then made a class-level guarantee by the
  duration guard (expected-seconds.txt vs ffprobe, 0.5s tolerance).
  Taught: the inherited bug became a permanent guard, so a repeat is a
  loud build error rather than a quiet artifact.
- Pre-rename stale path in the art generator (9155a65). The Wayang
  rename deliberately kept absolute local paths inside the art
  generators, so `generate_mascots.py` still deployed into the
  pre-rename `content_engine` tree until the Rimau commit fixed its
  deploy root. Note: this class is not fully dead -
  `assets/background/generate_background.py` and `generate_themes.py`
  still write to `/mnt/data/work/content_engine/...` paths today.
  Taught: absolute paths survive renames and resurface the next time
  the generator runs.
- Latin subtitles under a Japanese wrapper (dede006). BudouX-JA emitted
  near-whole-line segments for Latin text and the nowrap spans
  overflowed the centered container. Taught: upstream text-shaping
  assumptions are language-specific; wrap logic now branches by script.
- Vendor-side capability gating (c64a503). The remotion mapper gated
  voices on voicevox, blocking revolab/openai projects. Taught:
  validation is the platform's job; vendors consume, they do not gate.
- Workdir and state leaks (e38feb6, 477ff3f, 3690719, b264afe). A .pyc,
  .omc session state (root and nested under assets/mascots), and the
  whole hyperframes .work/ tree were committed when shells ran from the
  wrong cwd. Each was purged and its ignore rule widened. Recorded in
  the structure brief as "leaked twice". Taught: ignore rules are
  reactive, absolute paths and cwd discipline are the fix.

## Rename history

- Commit 848d28e (2026-09-26 20:28): "The platform has a name: Wayang,
  after the shadow play - flat puppet characters performing your script
  on a stage."
- GitHub repo renamed khursani8/content_engine -> khursani8/wayang;
  remote is now `https://github.com/khursani8/wayang.git` (old GitHub
  URLs redirect).
- CLI renamed `tools/ce.py` -> `tools/wayang.py` (git recorded a 98%
  similarity rename, prog wayang).
- Sweep: README, agent manual, docs, vendor manuals, engine configs,
  npm package names, schema title, map-project references - 20 files,
  48 insertions, 48 deletions.
- Absolute local paths inside the art generators were intentionally
  kept at rename time. The mascot generator was fixed one commit cycle
  later (9155a65); the background generators still carry
  `/mnt/data/work/content_engine` paths (see bug classes).
- The local working folder kept the name `/mnt/data/work/content_engine`
  until the operator asked, then moved to `/mnt/data/work/wayang`, with
  the Claude history namespace migrated by copy + symlink.
- Commit e247071 removed the upstream repo reference
  (nyanko3141592/remotion-voicevox-template) from `rumpun.yaml` and
  `vendors/remotion/AGENTS.md`. Old commit messages still name the
  upstream repo; scrubbing history would need git filter-repo plus a
  force push and was recorded as done-only-on-explicit-request.

## What is deliberately not in git

Current `.gitignore`: `node_modules/`, `vendors/*/.work/`, `projects/`,
`out/`, `*.log`, `.rumpun/runs/`, `.rumpun/seasons/_steady-state*`,
`.rumpun/seasons/_competition.yaml`, `__pycache__/`, `*.pyc`, `.omc/`.

| excluded | why it matters |
|---|---|
| `node_modules/` | Installed deps, reproducible from package.json; README pins the one manual step (`npm install` in `vendors/remotion/engine`). |
| `vendors/*/.work/` | Disposable per-vendor build workdirs: generated HTML, fonts, wavs, out.mp4. Committed by accident twice (10748ba, 1932e7c) when shells ran from the wrong cwd, purged in b264afe. |
| `projects/` | User content: each project's filled project.yaml, generated `voices/`, and `out/video.mp4`. Personal renders do not belong in the platform repo. (`projects/video-tutorial/` exists on disk, untracked.) |
| `out/` | Render outputs. |
| `.rumpun/runs/` | Per-season workspaces: the raw model outputs (codex/glm/fable reviews, briefs, decision drafts). Kept on disk only. The committed record of decisions lives in the ledger and commit messages. Anyone cloning the repo does not get the raw reviews. |
| `.rumpun/seasons/_steady-state*`, `_competition.yaml` | Untracked season templates and drafts: a steady-state season shape (three light lanes: lint sweep, route probes, rehearsals) and a Kaggle-competition season shape. Fill-in drafts, not campaign history. |
| `__pycache__/`, `*.pyc` | Build artifacts; one leaked in 2fd0e74, removed in e38feb6. |
| `.omc/` | Claude session state (hud caches, mission state, subagent tracking). Committed from dafeabf onward, untracked in 3690719 + 477ff3f. |

Contrast: `.rumpun/` minus those paths is committed on purpose -
`.rumpun/README.md` states that git history over it is the evolution
ledger, unlike disposable caches.

## Open questions you might ask

- Why does the ledger keep every directive at status `pending`, and is
  a closure pass (or a status convention change) planned, or is
  append-only-as-historical the permanent answer?
- The openai TTS provider has never touched the live API. Verify it
  with a key, or cut it from the schema until one exists?
- Directive 6 lists studio theme contrast as open, and 19c4cfd
  regenerated studio.png. Was contrast the reason, and is the item
  actually closed?
- `assets/background/generate_background.py` and `generate_themes.py`
  still write into the pre-rename `/mnt/data/work/content_engine` tree.
  Fix the paths, or accept it since regeneration is rare?
- The design consult gave fable full repo knowledge while codex and glm
  got none. Was the asymmetry deliberate (local model vs remote
  quota), and did it skew which recommendations won?
- Codex round 2 returned empty output and no third round was attempted.
  Was the meta-question answer from round 1 considered sufficient, or
  was codex effectively dropped from the consult?
- Autonomy stage is still `manual` with `promote_after: 5 clean audits`
  and the campaign cost cap is 600. Was any spend tracked against that
  cap, and is a season s2 planned or is the campaign closed?
- Old commit messages still name the upstream template repo. Is a
  `git filter-repo` history scrub planned, or does the redirect-plus-
  current-files state stand?
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

hook: PostToolUse
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse Completed
exec
/usr/bin/zsh -lc 'cat /home/sani/.codex/skills/dts/SKILL.md' in /mnt/data/work/wayang
 succeeded in 0ms:
---
name: dts
description: Apply or audit DTS (Dense Technical Syntax), a standard for token-dense English. Use to write or rewrite any persisted text — READMEs, docs, code comments, commit and PR bodies, checklists, error messages, CLI help, tool descriptions, and agent prompts. Also use when asked to de-slop, tighten, compress, cut verbosity, reduce tokens, or apply STE / Simplified Technical English / ASD-STE100 / DOCS-26. NOT for another language, NOT for fiction, NOT for brand or marketing copy, NOT for long-form argument such as a thesis or legal text.
license: MIT
compatibility: claude-code codex opencode pi gemini-cli
metadata:
  standard: DTS
  spec_version: "0.1"
---

# DTS — Dense Technical Syntax

Apply these six to every passage. They cover the common case.

1. **Compression removes filler, never content.** Every fact the reader needs to act survives. When keeping a fact costs another sentence, write the sentence.
2. **Answer first.** No preamble, no question echo, no closing recap.
3. **One idea per sentence.** At most 15 words for a directive, 20 for description. Shorter is always better.
4. **Bullets and tables** for anything enumerable. Never a prose list. Stop a list when the next row adds nothing the reader will act on.
5. **Delete filler and hedge stacks.** State the fact, or state that it is unconfirmed.
6. **Reproduce technical spans verbatim.** Code, paths, commands, identifiers, and error strings stay character-exact.

Read [`references/grammar.md`](references/grammar.md) before rewriting a whole document. Run the audit in [`references/check.md`](references/check.md) before delivering one.

## Hard boundary

Brevity governs prose only. Code inside an edit stays complete, syntactically valid, and self-contained. Treat `// ... existing code` and stub placeholders as defects.

Never re-output unchanged code to confirm a change.

## Routing

| Need                                                                                       | Read                                                 |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| Full rule set, sentence caps, locked verbs, condition-before-command                       | [`references/grammar.md`](references/grammar.md)     |
| Kill-list, hedge collapses, synonym-to-canonical map                                       | [`references/wordlist.md`](references/wordlist.md)   |
| Per-target shapes: commit, PR, README, comment, error, CLI help, agent prompt, JSON schema | [`references/artifacts.md`](references/artifacts.md) |
| Grep patterns and the mandatory self-audit                                                 | [`references/check.md`](references/check.md)         |
| Genre limits, per-file overrides, precedence, extending the canon                          | [`references/scope.md`](references/scope.md)         |

For an unrecognized request, read [`references/grammar.md`](references/grammar.md) and apply it.

## Stop conditions

Do not apply DTS to any of these. Apply the operator's own handler instead, and say which one is running.

- Long-form argument: thesis, paper, essay, legal text, proposals. Hedging and subordinate clauses are genre requirements there.
- Any language other than English.
- Fiction and narrative prose.
- Brand, marketing, or persuasive copy.
- String literals, test fixtures, and any text asserted against in code.

DTS names no replacement, so read the operator's overlay to learn which handler owns the genre. When a prose skill and DTS both match, the prose skill wins for its language or genre.

Honor a per-file marker over every rule above. `<!-- dts:core -->` keeps the genre-neutral core and drops the caps, the modal limit, and the bullets rule. `<!-- dts:off -->` disables the standard for that file. [`references/scope.md`](references/scope.md) carries the layer model.

## Boundary

DTS owns structure and word choice in English technical prose. It does not own tone, persuasion, voice, or any other language. Leave those to whatever the operator has configured.

hook: PostToolUse
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse Completed
exec
/usr/bin/zsh -lc 'wc -l REPO_ANALYSIS/*.md' in /mnt/data/work/wayang
 succeeded in 0ms:
    43 REPO_ANALYSIS/00-overview.md
   607 REPO_ANALYSIS/01-platform-core.md
   477 REPO_ANALYSIS/02-vendors.md
   325 REPO_ANALYSIS/03-templates-content-docs.md
   432 REPO_ANALYSIS/04-history-decisions.md
   134 REPO_ANALYSIS/08-gotchas-and-quirks.md
    36 REPO_ANALYSIS/review-brief.md
  2165 REPO_ANALYSIS/review-codex-astra.md
   154 REPO_ANALYSIS/review-codex-sol.md
     3 REPO_ANALYSIS/review-glm53.md
  4376 total

hook: PostToolUse
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse Completed
exec
/usr/bin/zsh -lc "sed -n '250,607p' REPO_ANALYSIS/01-platform-core.md" in /mnt/data/work/wayang
 succeeded in 0ms:
  `text`, `src`, `font_size` (number), `color`, `outline_color`,
  `animation` (enum `none` | `fadeIn` | `slideUp` | `slideLeft` |
  `zoomIn` | `bounce`), `command` (string), `output` (array of strings).
  Conditional requirement: when `type == "terminal"`, `command` is
  REQUIRED (schema if/then). No equivalent condition forces `src` for
  `type == "image"` in the schema, but validate_project fails the render
  when an image `src` file is missing.
- `se`: object, `additionalProperties: false`, required `src`.
  `volume`: number 0..1.

### settings

`additionalProperties: false`. All subsections optional, each closed:

- `video`: `width` int >=320, `height` int >=240, `fps` int 12..120,
  `playback_rate` number 0.5..3 (slows voice and pacing; docs recommend
  0.9 for tutorials).
- `font`: `family` string, `size` int >=10, `weight` string or integer,
  `color` string.
- `subtitle`: `minProperties: 1`; `bottom_offset` int >=0,
  `max_width_percent` int 10..100, `outline_width` int >=0.
- `character`: `height` int >=40, `use_images` boolean,
  `images_base_path` string.
- `content`: `top_padding`, `side_padding`, `bottom_padding`, ints >=0.
- `background`: string theme name.

### vendor

Top-level `vendor`: `type: object`, free-form. Vendor passthrough section
(remotion mapper reads vendor-specific keys from here). Not mentioned in
docs/project-yaml.md's section list.

Note: the schema does not require `settings`, but `check` treats a missing
settings section as a blocker.

## 5. TTS layer (tools/tts_providers.py)

The repo owns no TTS service. Engines are plain HTTP API clients.

| Provider | Endpoint | Env key | config_hash keys | Default model | Required voice key |
|---|---|---|---|---|---|
| openai | `https://api.openai.com/v1/audio/speech` | `OPENAI_API_KEY` | voice, model, speed, instructions | `gpt-4o-mini-tts` | `voice` |
| revolab | `https://api.revolab.ai/v1/tts` | `REVOLAB_API_KEY` | voice_id, model, speed | `nada-1.0-pro` | `voice_id` |

Both providers: POST JSON with `Authorization: Bearer <env key>`,
`urlopen` timeout 120s, response bytes written verbatim to the output wav.
`HTTPError` -> `ProviderError` with status code plus the first 300 chars of
the response body (messages `openai tts http <code>: ...` and
`revolab http <code>: ...`). `URLError` -> `ProviderError` with the reason.
Payloads: openai sends `model`, `voice`, `input`, `response_format: "wav"`,
optional `speed`, optional `instructions`. revolab sends `model`, `text`,
`voice_id`, optional `speed`.

`wav_seconds(path)`: stdlib `wave`, `nframes / framerate`.

### Cache: manifest.json and file naming

- Voices land in `<project>/voices/`, one wav per script line, named
  `f"{id:02d}_{character}.wav"` -> `NN_character.wav` (id zero-padded to
  2 digits; id 100+ produces `100_character.wav`, 3 digits, cosmetic only).
- `voices/manifest.json`: `{"lines": {"<fname>": {"hash", "seconds",
  "engine"}}, "engines": [<sorted unique engine names>]}`.
- Hash: `line_hash(text, engine, provider.config_hash(cfg))` = first 12
  hex chars of `sha256(json.dumps({"text", "engine", "params"},
  sort_keys=True))`. Editing text, engine, or any config_hash key
  invalidates the entry. Unset keys hash as JSON null, so changing a
  provider's in-code default model does NOT invalidate cached files.
- Cache hit condition: `--force` not set AND `manifest["lines"][fname].
  hash == digest` AND the wav file exists on disk.
- `seconds` recorded as `round(wav_seconds, 3)`.
- Manifest written with `indent=2`, `ensure_ascii=False`, trailing newline.
  `engines` is rebuilt from the `lines` values after every run, including
  the all-cached early return.
- Stale entries are never pruned: lines deleted from the script keep their
  manifest entries and wavs forever.

### Availability gate (all-or-nothing per project)

`run_tts` collects the set of engines used across all script lines. If ANY
engine fails `available()` (missing env key), it logs one WARNING per
engine (`TTS engine <engine>: <why>`) plus `no TTS this run: vendor renders
with estimated timing and silent audio`, and returns. Nothing is
synthesized; the render proceeds with estimated timing and silent audio.
One missing key silences the entire project, no partial voice sets.

`ProviderError` inside the job loop: `TTS failed for <fname>: <e>`, exit 1.
Wavs written earlier in the same run stay on disk but the manifest is only
written after the full loop, so those lines regenerate on the next run.

Flow states logged: `TTS: all <n> line voice(s) cached in <dir>` when
nothing to do, `TTS: generating <n> line voice(s) with <engines>` when
jobs exist, `TTS <fname>: <sec>s (<engine>)` per synthesized line.

## 6. Visibility lint (post-render)

Entry: `lint_project(pdir, mp4, data)`. Called by `render` (unless
`--skip-lint`) and by `lint`. Vendor-agnostic. Returns True on pass; any
fatal problem or accumulated failure exits 1.

### Layout contract (hard-coded in wayang.py)

- Characters: bottom corners. Square box, `charH` wide and tall, 40px
  inset from the screen edge. Left character x0 = 40; right character
  x0 = W - 40 - charH. Box y range: H - charH to H.
- Subtitle: bottom-center. Width = `max_width_percent` percent of W
  (default 55). Height = `fontSize * 1.5 * 2` (room for two lines).
  Bottom edge sits `bottom_offset` px above the screen bottom (default 40).
- Text card: upper-center region from (0.15W, 0.15H) to (0.85W, 0.62H).

At defaults and 1920x1080: subtitle band x 432..1488 (55 percent of 1920
centered), y 830..1040 (fontSize 70 -> height 210, bottom_offset 40);
character box 275x275 at x 40..315 (left) or 1605..1880 (right), y 805..1080;
card region x 288..1632, y 162..669.6.

### Settings defaults used by the lint

fontSize 70 (`settings.font.size`), charH 275
(`settings.character.height`), subPct 55
(`settings.subtitle.max_width_percent`), subBottom 40
(`settings.subtitle.bottom_offset`). W, H, duration come from `ffprobe`
on the actual mp4 (first stream with `codec_type == "video"`). A render
size differing from `settings.video.{width,height}` logs a WARNING
(`render size %dx%d differs from settings`) and continues.

### Checks, in order

1. Layout overlap (no frame extraction): subtitle band vs each character
   corner box, plain rectangle-overlap test
   (`subX0 < cx0 + charH and subX1 > cx0 and subY0 < H and subY1 > H - charH`).
   Any overlap -> `layout: subtitle band overlaps character '<cid>' box`,
   immediate return False (exit 1), no further checks.
2. timeline.json is REQUIRED. Read from the mp4's directory
   (`<out>/timeline.json`), shape
   `{"lines": [{"id", "start", "end"}, ...], "total"}` with seconds.
   Windows = script lines that have a matching timeline entry (ids matched
   as ints), `dur = end - start`. Logs `lint: using vendor timeline.json
   (<n> lines)`. Zero windows -> `visibility lint: <path> missing - the
   vendor must emit the timeline it renders`, exit 1. A partial timeline
   silently shrinks coverage to the intersection; extra or missing
   per-line entries do not error individually.
3. Reference frame ("tail"): extracted at `duration - 0.4` (clamped) to
   `<pdir>/out/.lint/tail.png`. Extraction failure -> exit 1
   (`could not extract the reference frame`).
4. Per line window: sample frame at `mid = start + dur * 0.6` (60 percent
   into the line, not the midpoint) to `.lint/f<id>.png`.
   - Extraction failure -> `visibility: line <id> frame missing - render
     is shorter than the computed timeline`, +1 failure.
   - Subtitle ink: `tail` frame is the "empty" baseline; diff of the
     sample vs tail cropped to the subtitle band (subY0 clamped to >= 0
     here). Count < 150 -> `visibility: line <id> subtitle has no ink in
     the subtitle band`, +1 failure.
   - Text card ink: only when `line.visual.type == "text"` and
     `visual.text` non-empty. Same diff method on the card region;
     count < 150 -> `text card has no ink in the card region`, +1 failure.
   - Character presence: only when
     `ROOT/assets/backgrounds/<settings.background or "riverbank">.png`
     exists. The theme PNG is resized to WxH as the baseline; corner-box
     diff count < `(charH * charH) / 60` -> `character '<cid>' missing
     from its corner box`, +1 failure. Default charH 275 -> threshold
     275^2/60 = 1260.42 sampled pixels. Theme PNG missing -> WARNING
     `character presence check skipped: theme png missing for theme '<t>'`,
     check skipped, not a failure.
   - Character animation (informational, never fails): second frame at
     `min(mid + 0.21, duration - 0.2)` to `.lint/f<id>b.png`; corner-box
     diff logged INFO `character animation delta: <n>`.
   - Voice loudness: only when `real_voices` (manifest.json exists AND
     `manifest.engines` non-empty). `ffmpeg -ss <start> -t <dur> -af
     volumedetect`; `mean_volume` parsed from stderr; if the line is
     absent the sentinel -99.0 is used (which then fails the threshold).
     `vol < -55.0` dB -> `audibility: line <id> voice is silent (<v> dB)`,
     +1 failure. Pass logs `line <id>: subtitle ok, character ok, voice
     <v> dB`. Estimate render: `line <id>: subtitle ok, character ok
     (estimate render: voice check skipped)`.
5. Summary: failures -> `visibility lint: <n> failure(s)`, exit 1.
   Otherwise `visibility lint: all checks passed`, return True.

### Diff sampling method (`_band_diff_count`)

Crop both images to the box (coords cast to int), `PIL.ImageChops.
difference`, convert to RGB, sample every 2nd pixel on both axes
(stride 2), count samples where any of R, G, B differs by more than 24.

Frame helper `_ffmpeg_frame`: puts `-ss <t>` before `-i` (fast seek),
`-frames:v 1`, clamps t into `[0, duration - 0.2]`, returns False when
ffmpeg fails or the file is missing.

What fails vs informational:
- Fails (exit 1): layout overlap, missing timeline.json, missing tail
  frame, missing line frame, subtitle ink < 150, card ink < 150,
  character presence below charH^2/60 (when theme exists), voice below
  -55 dB (when real voices).
- Informational only: animation delta (INFO), render size mismatch
  (WARNING), theme PNG missing (WARNING, skips that check), estimate
  render voice check (skipped).

Temp frames in `<pdir>/out/.lint/` (`tail.png`, `f<id>.png`,
`f<id>b.png`) are never cleaned up.

## 7. Duration guard and timeline.json contract

The duration guard is NOT in wayang.py. Each vendor's `build.sh` enforces
it after rendering; remotion and hyperframes carry identical logic:

1. `EXPECTED` = contents of the workdir `expected-seconds.txt` (may be
   empty).
2. If EXPECTED is non-empty and `ffprobe` is on PATH:
   `ACTUAL` = `ffprobe -show_entries format=duration` of the rendered
   mp4. Pass iff `EXPECTED - 0.5 <= ACTUAL <= EXPECTED + 0.5` (awk float
   compare). Otherwise exit 1 with `rendered duration deviates from the
   computed timeline` (remotion appends `(empty-tail bug class)`).
   ffprobe missing -> WARNING `duration guard skipped, ffprobe not found`.
3. Only after the guard passes, the workdir `timeline.json` and rendered
   video are copied to OUT_DIR as `timeline.json` and `video.mp4`.

The vendor nonzero exit propagates through `render` as
`vendor build.sh exited <code>` with wayang exit 1.

`expected-seconds.txt` is the mapper's computed timeline total (per
hyperframes AGENTS.md: sum of line audio plus pauses). Discrepancy:
`docs/vendor-contract.md` says the vendor writes
`OUT_DIR/expected-seconds.txt`; both build.sh scripts actually leave it
in the workdir (`vendors/<engine>/.work/<project>/expected-seconds.txt`)
and copy only `timeline.json` + `video.mp4` to OUT_DIR.

timeline.json consumers: the visibility lint reads it from the mp4's
directory (OUT_DIR), so a vendor that skips copying it breaks lint with
`the vendor must emit the timeline it renders`.

Vendor build contract (`docs/vendor-contract.md` + both scripts):
`build.sh PROJECT_DIR OUT_DIR`; wrong arg count -> usage, exit 2. Reads
`project.yaml`, prefers `.merged.yaml` when present. Timing in seconds;
vendors convert to their own units. Idempotent: workdir
`vendors/<engine>/.work/<project-name>` is `rm -rf`-ed every run. Must
error on unsupported canonical keys, never silently drop them. Build log
names the audio engines used or `estimate`.

Vendor specifics:
- remotion: copies engine source (excludes `node_modules`, `out`),
  symlinks `engine/node_modules`, copies project `assets/` into
  `public/`, runs `scripts/map-project.mjs`, `npm run sync`, then
  `npx remotion render src/index.ts Main out/video.mp4`.
- hyperframes: copies `voices/` and `assets/` into the workdir, runs
  `npm install` in `scripts/`, `map-project.mjs`, then
  `npx --yes hyperframes@latest render --output out.mp4 -f 30`
  (downloads the CLI and Chromium on first run).

## 8. Series model

- `series.yaml` is a sparse base: meta (title, template, vendor, language,
  description), characters, settings. A fragment; never validated alone.
- Merge in `load_project`: `deep_merge(series, episode)`. Episode wins per
  key; dicts recurse; lists and scalars replace. The `script` list is
  therefore always episode-only. Merge logs
  `merged series config <path> (<n> shared character(s))` where n counts
  series character keys.
- Series file discovery (`find_series_file`): checks
  `pdir.parent/series.yaml` then `pdir.parent.parent/series.yaml`. The
  standard layout `projects/<series>/episodes/<ep>/` resolves at two
  levels. Episodes nested deeper find nothing.
- Whole-dir operations (validate, tts, render): `is_series_dir` = dir
  contains `series.yaml` OR has an `episodes/` subdir. Then
  `series_episodes` lists `episodes/*/project.yaml` sorted by directory
  name; the command loops all of them in that order.
- Vendors never see series.yaml: `render` materializes the merged document
  as `<episode>/.merged.yaml` (only when a series applied) and deletes a
  stale `.merged.yaml` for standalone projects. Vendor contract: prefer
  `.merged.yaml` when present.
- Add episodes post-init with `init <template> <series>/episodes/<ep>`.

## 9. Gotchas

1. `check` does not merge series.yaml and does not schema-validate. An
   episode that inherits characters from series.yaml reports
   `speaker '<cid>' is not defined in characters` from check even though
   validate and render pass. Run check at the series root only for
   base-level gaps, or ignore those FILL items on episodes.
2. `init-series` language fallback is `"ja"`, not `ms`. Series built
   without a template language need a manual edit.
3. The theme catalog lives in two places: `check` validates
   `settings.background` against `vendors/<vendor>/assets/backgrounds`
   (vendor-local), the lint's character presence uses the repo-root
   `assets/backgrounds`. A theme name can pass check and still miss the
   lint's theme file (presence check then silently skips with a warning).
4. Lint timeline matching is an intersection: timeline entries missing for
   some script lines drop those lines from all frame and audio checks
   without any error. Only a fully empty window list fails.
5. TTS cache hash includes unset voice keys as null. Changing a provider's
   in-code default model (for example `gpt-4o-mini-tts`) regenerates
   nothing; already cached lines keep the old model's audio.
6. The TTS gate is project-wide all-or-nothing across engines. One missing
   env key for one character silences every line in the project.
7. `render` always calls run_tts with force=False. Editing text
   invalidates only that line's hash, so renders after edits re-synthesize
   exactly the changed lines (unless the key is gone).
8. `_ffmpeg_volume` returns -99.0 when `mean_volume` is absent (for
   example a video with no audio track). With real_voices true that reads
   as silence and fails, which is intended, but it also means a volumedetect
   output-format change would fail every line.
9. The lint's character presence baseline is the theme PNG, not a
   character-free frame of the actual render. A background that differs
   from the theme PNG inside the corner box (vendor draws extra art there)
   can produce false presence; the same design makes the check depend on
   repo-root assets that a standalone vendor checkout would not have.
10. Animation delta is logged but never asserted. A fully static character
    passes the lint.
11. Subtitle band coordinates are used raw in the overlap test but Y0 is
    clamped to 0 only for the ink crop. Extreme `bottom_offset` +
    `font.size` values can push the band off-screen and pass overlap while
    the ink check then fails (correctly) on every line.
12. Non-integer timeline ids crash the lint (`int(entry["id"])`), but the
    schema forces integer line ids, so only a broken vendor timeline can
    trigger it.
13. `resolve_project` prefers `ROOT/<value>` over `ROOT/projects/<value>`:
    a repo-root directory named like the project shadows the projects/ one.
14. `lint` command requires `validate_project` to pass first; you cannot
    lint a render made from a since-edited, now-invalid project.yaml
    without fixing the YAML or temporarily bypassing.
15. Docs drift: `docs/vendor-contract.md` claims OUT_DIR receives
    `expected-seconds.txt` (it stays in the vendor workdir); root
    AGENTS.md lists 4 template formats while `templates/` has 5
    (`tutorial` is undocumented there). The check message `known: remotion,
    hyperframes` is hard-coded and will rot when a third vendor lands.
16. Exit code collision: argparse usage errors and `check` notes-only both
    exit 2. Scripts that branch on 2 must distinguish by output.
17. `voices/manifest.json` entries are never pruned, and `engines` is
    rebuilt from manifest lines, so a manifest whose lines were all
    regenerated under a new engine still reports the union over time
    correctly, but deleted-line entries linger and inflate the
    `<n> line voice(s) cached` note in check.
18. Lint temp frames accumulate in `out/.lint/` across runs.

## Open questions you might ask

- Why does check read the raw project.yaml without series merge? Would
  merging there (like validate does) remove the false FILL items on
  series episodes, and was raw reading chosen so check shows what the
  human still must write?
- The lint's character presence compares against the repo-root theme PNG
  while check validates the theme name against the vendor-local catalog.
  Should both read one catalog, and should the vendor be contract-bound
  to copy the theme where the lint can find it?
- `expected-seconds.txt` never reaches OUT_DIR, contradicting
  docs/vendor-contract.md. Should the contract change or should build.sh
  copy it out for platform-level duration checks?
- The visibility lint only checks the intersection of script and timeline
  ids. Should a timeline missing entries for script lines fail the build
  instead of silently shrinking coverage?
- TTS manifest never prunes entries for removed lines, and the cache hash
  bakes in nulls for unset model keys. Is there a cleanup or
  hash-versioning plan, or is manual `voices/` deletion the supported
  path?
- What is the intended third-vendor path? `check` hard-codes
  `known: remotion, hyperframes` and root AGENTS.md lists 4 formats while
  5 template dirs exist. Which file is the source of truth when they
  disagree?
- The lint animation check computes a delta but asserts nothing. Is there
  a planned threshold (like the -55 dB audibility line) for lip-flap or
  idle motion?

hook: PostToolUse
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse Completed
exec
/usr/bin/zsh -lc 'cat REPO_ANALYSIS/02-vendors.md' in /mnt/data/work/wayang
 succeeded in 0ms:
# 02 - Vendors: remotion and hyperframes

Reference for the two video engines under `vendors/`. Every fact below is read from the repo tree at its current commit (`a02c528`). Where the code and a doc disagree, both are stated. Nothing is projected.

## Sources read

| Area | Files |
|---|---|
| Shared | `docs/vendor-contract.md`, root `AGENTS.md`, `README.md`, `docs/project-yaml.md`, `docs/tutorial.md`, `tools/wayang.py` (lint section) |
| Remotion | `vendors/remotion/AGENTS.md`, `build.sh`, `scripts/map-project.mjs`, `engine/package.json`, `engine/video-settings.yaml`, `engine/config/{characters,defaults,script}.yaml`, `engine/scripts/{sync-script,sync-settings}.ts`, `engine/src/{index,Root,Main,config}.tsx/.ts`, `engine/src/components/{Character,Subtitle,SceneVisuals}.tsx`, generated `engine/src/data/script.ts` + `engine/src/settings.generated.ts`, `engine/public/` layout |
| Hyperframes | `vendors/hyperframes/AGENTS.md`, `build.sh`, `scripts/map-project.mjs` (every line), `scripts/package.json`, generated sample `.work/hf-demo/index.html` |
| Assets | `assets/backgrounds/` catalog, `assets/background/` generators |

---

## 1. Shared vendor contract (`docs/vendor-contract.md`)

### Entry point

```
vendors/<engine>/build.sh PROJECT_DIR OUT_DIR
```

- Wrong arg count: usage to stderr, exit 2. Both scripts run `set -euo pipefail`.
- Input: `PROJECT_DIR/project.yaml` (canonical, all timing in seconds). When the platform materialized series inheritance, `PROJECT_DIR/.merged.yaml` exists and both mappers prefer it.
- Required outputs: `OUT_DIR/video.mp4`, `OUT_DIR/timeline.json` shaped `{"lines": [{"id", "start", "end"}...], "total"}` (seconds), and `expected-seconds.txt`.
- Contract deviation: both build.sh scripts write `expected-seconds.txt` to the workdir only and never copy it to `OUT_DIR`. The duration guard reads it from the workdir, so it works, but the contract text ("Writes OUT_DIR/...expected-seconds.txt") is not literally honored.
- Idempotent: the workdir is deleted and rebuilt on every run.
- Error policy: unsupported canonical keys are a hard error, never a silent drop. Remotion enforces this fully. Hyperframes gates `vendor.hyperframes` keys but silently ignores unknown `settings.*` keys (see 4.3).
- The build log must name the audio source. Both mappers print `TTS source: <engines> (platform-generated voices)` or `TTS source: estimate`.

### Audio honesty (both vendors)

Priority order, never mixed within one project:

1. Platform-generated voices in `PROJECT_DIR/voices/`: one wav per line named `NN_<character>.wav` (NN = zero-padded line id, `padStart(2,"0")`) plus `voices/manifest.json` with `lines: {"NN_<character>.wav": {"seconds": ...}}` and `engines: [...]`. Coverage must be complete: one missing entry or file falls the whole project through to estimate. Bad `seconds` (non-finite or <= 0) is a hard error in remotion.
2. Estimate: durations from character count, silent placeholder audio, log says `estimate`.

`characters.<id>.voice` in canonical YAML is consumed by the platform (`tools/wayang.py` + `tools/tts_providers.py`), not by vendors. Vendors only see wavs + manifest.

### Guards the platform runs after a build

Duration guard (inside both build.sh scripts):

- `ffprobe -show_entries format=duration` of the rendered mp4 vs `expected-seconds.txt`.
- Pass window: `expected - 0.5 <= actual <= expected + 0.5` (awk comparison).
- Fail: `ERROR: rendered duration deviates from the computed timeline`, exit 1. Remotion names the bug class: "empty-tail bug".
- `ffprobe` missing: `WARNING: duration guard skipped`, build continues. Empty/missing expected file: guard skipped silently.

Visibility lint (`tools/wayang.py lint_project`, vendor-agnostic, runs after build inside `wayang.py render`):

- Reads `timeline.json` from the out dir. Missing or empty: `SystemExit(1)`, "the vendor must emit the timeline it renders".
- Reference frame extracted at `duration - 0.4s`. Per line, frame extracted at `start + dur * 0.6` (dur = timeline `end - start`).
- Subtitle band: centered, width = `settings.subtitle.max_width_percent` (55), bottom band height = `font.size * 1.5 * 2` above `bottom_offset` (40). Ink = pixel diff count vs reference frame. `< 150` diff pixels fails.
- Text card region: 15%-85% width, 15%-62% height. Checked only for lines with a text visual. `< 150` fails.
- Character corner box: `charH` (275) square at the bottom corner, 40px inset, side from `position`. Compared against the pure theme PNG (`assets/backgrounds/<theme>.png` resized to the frame). Presence `< charH*charH/60` fails.
- Audibility: when `voices/manifest.json` has engines (real voices), mean volume is probed at `mid + 0.21s`. `< -55 dB` fails the line.
- Pre-render layout check: subtitle band intersecting a character box fails before any frame extraction.

### Background themes

- Shared catalog: `assets/backgrounds/` at the repo root. Both mappers resolve it relative to their workdir (`workDir/../../../..`).
- Resolution order in both: project `assets/background.png` > named theme `settings.background` > default `riverbank`.
- `settings.background` must match `^[a-z0-9-]+$` (remotion) or be a string (hyperframes), and must exist in the catalog, else hard error listing available themes.
- Generators that make the themes: `assets/background/generate_themes.py`, `assets/background/generate_background.py`.

### Theme catalog (`assets/backgrounds/`)

11 synthesized PNG themes: `batik`, `chalkboard`, `kraft-paper`, `night-sky`, `notebook`, `riverbank`, `slate`, `studio`, `sunrise`, `whiteboard`, `wood-table`.

Note: `vendors/remotion/AGENTS.md` says the catalog lives at `vendors/remotion/assets/backgrounds/`. That directory does not exist. The real catalog is the repo-root one and that is what `map-project.mjs` reads.

---

## 2. Remotion vendor (`vendors/remotion/`)

### 2.1 Build pipeline (`build.sh`), step by step

1. Resolve absolute `PROJECT_DIR`, create absolute `OUT_DIR` (mkdir -p), locate `VENDOR_DIR`.
2. `WORK = vendors/remotion/.work/<project-basename>/`. `rm -rf $WORK`, `mkdir -p $WORK/public/voices`.
3. Copy engine source: `tar -C engine --exclude=node_modules --exclude=out -cf - . | tar -C $WORK -xf -`.
4. Symlink `engine/node_modules` into `$WORK/node_modules` (one-time `npm install` in `engine/` is a repo prerequisite).
5. Copy project assets into the engine's static root: `cp -R $PROJECT_DIR/assets/. $WORK/public/` (contents land at `public/` root). Done before mapping so existence checks and the renderer see the files.
6. `node $VENDOR_DIR/scripts/map-project.mjs $PROJECT_DIR $WORK` (see 2.2).
7. `(cd $WORK && npm run sync)` = `sync-settings` then `sync-script` (see 2.3).
8. `(cd $WORK && npx remotion render src/index.ts Main out/video.mp4)`. No concurrency, browser, or GL flags are passed.
9. Duration guard (ffprobe vs `$WORK/expected-seconds.txt`, 0.5s tolerance, see 1).
10. Copy `$WORK/timeline.json` and `$WORK/out/video.mp4` to `OUT_DIR`.

### 2.2 Mapper (`scripts/map-project.mjs`)

Input parsing:

- Prefers `.merged.yaml` over `project.yaml`. Missing file or YAML parse error: `die()` (exit 1 with `[map-project] ERROR:`).
- Reads `characters`, `script`, `settings`, `vendor.remotion`. Defaults: `fps` 30, `playbackRate` 1.2, `estimate_cps` 7.5.

Gates (all hard errors):

- `vendor.remotion`: only `estimate_cps` allowed. Unknown key dies.
- `settings`: allowed sections `video, font, subtitle, character, content` with exact key whitelists (see mapping table). Unknown section or key dies. `settings.background` is handled outside the gate.
- Script line referencing an unknown character dies. Empty script dies. No characters dies.
- `visual.src` and `se.src` must exist under `PROJECT_DIR` or die.
- `visual.type: terminal` needs `visual.command` or dies.

Settings conversion (snake_case canonical -> camelCase engine, defaults filled in):

| Section | Canonical keys accepted | Engine keys | Engine defaults |
|---|---|---|---|
| video | width, height, fps, playback_rate | width, height, fps, playbackRate | 1920, 1080, 30, 1.2 |
| font | family, size, weight, color | family, size, weight, color | "M PLUS Rounded 1c", 70, "900", "#ffffff" (+ engine-only outlineColor "character", innerOutlineColor "none") |
| subtitle | bottom_offset, max_width_percent, outline_width | bottomOffset, maxWidthPercent, outlineWidth | 40, 55, 14 (+ engine-only maxWidthPixels 1000, innerOutlineWidth 8) |
| character | height, use_images, images_base_path | height, useImages, imagesBasePath | 275, false, "images" |
| content | top_padding, side_padding, bottom_padding | topPadding, sidePadding, bottomPadding | 0, 0, 0 |

`maxWidthPixels`, `innerOutlineWidth`, `innerOutlineColor` exist in the engine defaults but have no canonical input key.

Characters -> `config/characters.yaml`: `{name, position (default "right"), color (default "#4B5563"), flipX (default false), defaultPauseAfter: 15}`. Position values are not gated to left/right here.

Script -> `config/script.yaml`: per line `{id, character, text}` plus optional `displayText`, `scene`, `pauseAfter` (`Math.round(pause_after * fps)` frames, only when set), `emotion`, `visual`, `se {src, volume default 1}`.

Visual conversion:

- `terminal` degrades to a text card: `{type: "text", text: "$ " + command, animation: visual.animation || "fadeIn"}`, plus optional fontSize/color. The simulated terminal is a hyperframes-only feature.
- `text`/`image` pass through with `font_size -> fontSize`, `color`, `outline_color -> outlineColor`, `animation`. `none` and missing visual produce no visual key.

Subtitle lint: visible chars = whitespace-stripped `text` length. Over 84 chars prints a WARNING ("wraps past 2 lines", Netflix TTSG standard of about 42 chars per line, 2 lines max). Warning only, never an error.

`config/defaults.yaml` (generated): `newLine: {character: <first line's speaker>, pauseAfter: 15, durationInFrames: 60, scene: 1, emotion: null}`, `automation: {voiceOnSave: false, autoVoiceFileName: true}`.

`video-settings.yaml` (generated): engineSettings above plus `colors: {background: "#ffffff", text: <font.color>, zundamon: <first char color>, metan: <second char color or first>}`. The `zundamon`/`metan` key names are upstream leftovers; they carry Momo/Kiki colors.

Voice handling -> `public/voices/`:

- Platform path: for every line, copy `voices/NN_<char>.wav` into the workdir, `durations[f] = Math.ceil(seconds * fps * playbackRate)`. Log names the engines.
- Estimate path: `visible = whitespace-stripped text length`, `seconds = visible / (cps * playbackRate)`, `frames = max(24, ceil(seconds * fps))`. Writes a silent 24kHz 16-bit mono placeholder wav of `frames/fps` seconds so every `<Audio>` resolves. Log says `estimate`.
- Writes `durations.json` (file -> frames) and `.source` (`platform` or `estimate`).

Timeline and expected length (frames, `adjusted(f) = Math.ceil(f / playbackRate)`):

- Per line window: `adjusted(durationInFrames)` speech + `adjusted(pauseAfter ?? 15)` pause. Cursor accumulates both.
- `timeline.json`: seconds, `start = cursor/fps`, `end = (cursor + speech)/fps`, each rounded to 3 decimals. `end` is the speech end, the pause is not included.
- `expected-seconds.txt`: `(60 + sum(speech + pause windows)) / fps`, 3 decimals. The 60-frame closing buffer matches Root.tsx.
- The comment states the intent: this is the exact timeline the renderer plays, so the platform lint probes the true windows.

Background: validates theme name against the repo catalog, then either keeps the project's `assets/background.png` (log: project custom override) or copies `assets/backgrounds/<theme>.png` to `public/background.png` (default `riverbank`).

### 2.3 Sync step (config -> generated TS)

`engine/package.json` scripts: `build` = `sync` + `remotion render src/index.ts Main out/video.mp4`, `start` = `sync` + remotion studio, `sync` = `sync-settings` + `sync-script` (both via ts-node). Dependencies: remotion ^4.0.0, @remotion/{bundler,cli,renderer}, @remotion/google-fonts ^4.0.409, budoux ^0.6.2, react 18, yaml 2.3.4.

`scripts/sync-settings.ts`: `video-settings.yaml` -> `src/settings.generated.ts` exporting `SETTINGS` (the YAML as const) and `AVAILABLE_IMAGES` (scan of `public/images/<id>/*.png`, one filename list per character id).

`scripts/sync-script.ts`: `config/script.yaml` + `config/characters.yaml` + `config/defaults.yaml` + `public/voices/durations.json` -> `src/data/script.ts` exporting:

- Types: `AnimationType` ("none" | "fadeIn" | "slideUp" | "slideLeft" | "zoomIn" | "bounce"), `VisualContent`, `SoundEffect`, `BGMConfig`, `ScriptLine` (emotion enum "normal" | "happy" | "surprised" | "thinking" | "sad"), `SceneInfo`.
- `bgmConfig: BGMConfig | null = null` (hardcoded null, BGM unwired).
- `scenes`: metadata only, `[{id: 1, Opening, gradient}, {id: 2, Main Content, solid}, {id: 3, Ending, gradient}]`.
- `CHARACTERS`: array of `{id, name, position, color, flipX}` from characters.yaml. Data-driven, any id works.
- `characterColors`: id -> color map.
- `scriptData`: each line enriched with `voiceFile = "NN_<character>.wav"`, `durationInFrames` from durations.json (fallback: `defaults.newLine.durationInFrames` = 60), `pauseAfter` (fallback: `defaults.newLine.pauseAfter` = 15).

### 2.4 Engine runtime architecture

Composition chain: `src/index.ts` (`registerRoot`) -> `Root.tsx` -> single `<Composition id="Main">` -> `Main.tsx`.

`Root.tsx`:

- Total frames = sum over lines of `ceil(durationInFrames / playbackRate) + ceil(pauseAfter / playbackRate)` + 60 closing buffer. First line starts at frame 0, no opening buffer.
- This per-line rate adjustment (instead of summing raw frames) is the port's fix for the empty-tail bug at rate > 1; commit `118fa17`.
- Composition `fps`/`width`/`height` come from `SETTINGS.video` with `config.ts` VIDEO_CONFIG (1920x1080@30) as fallback.

`Main.tsx` (one component, no Sequences for visuals; it derives state from `useCurrentFrame()`):

- Walks `scriptData` accumulating rate-adjusted frames to find the current line, its start frame, its scene, and `isSpeaking` (frame is inside the speech window, not the pause).
- Renders, in order: full-frame background `Img` (`staticFile("background.png")`, object-fit cover); BGM `<Audio>` only if `bgmConfig` is non-null (never); per-line `<Sequence from={startFrame} durationInFrames={adjusted speech}>` containing the voice `<Audio src=voices/<voiceFile> playbackRate={SETTINGS.video.playbackRate}>` and an optional se `<Audio src=se/<src> volume={volume ?? 1}>`, with `premountFor={fps}`; `<SceneVisuals>` for the current line's visual; `CHARACTERS.map(...)` to `<Character>` (isSpeaking and emotion only for the current speaker, others get "normal"); a `<Subtitle>` Sequence spanning only the speech window with `displayText ?? text`.
- `sceneInfo = scenes.find(...)` is computed and never used. The visible background is the single static `background.png` for the whole video. The `scene` key has no visual effect in the current code, despite the AGENTS.md mapping row "1..3 have named backgrounds".

`Character.tsx`:

- Looks up its config in `CHARACTERS`; unknown id renders null.
- Mouth flap while speaking: `Math.floor(frame / 5) % 2 === 0` (about 6 flips per second at 30fps).
- Gentle bob while speaking: `sin(frame * 0.3)` mapped to -3..3 px vertical.
- Slide-in on mount: from -200px (left) or +200px (right) to 0 over 0.5s, clamped.
- Art path: `<imagesBasePath>/<id>/<file>`; `useImages` false renders a 200x300 rounded placeholder box in the character color with the character name.
- Emotion art resolution (existence-checked against `AVAILABLE_IMAGES`): `<emotion>_<open|close>.png` -> `<emotion>_open.png` -> `mouth_<open|close>.png`.
- `flipX` applies `scaleX(-1)`.
- Leftover: placeholder emoji picks "zundamon"/"metan" icons by hardcoded id, any other id gets a speech-bubble emoji.

`Subtitle.tsx`:

- Bottom-centered, width `maxWidthPercent`% capped at `maxWidthPixels`, `bottomOffset` from the bottom.
- Per-line script-aware wrapping: CJK lines (regex on hiragana..halfwidth katakana, CJK blocks) are segmented with BudouX (segments rendered as inline-block nowrap spans), other scripts use normal word wrap. Plus `text-wrap: balance` and `overflow-wrap: anywhere`. Commit `dede006`.
- Two text layers: stroke layer behind (`WebkitTextStroke` at `subtitle.outlineWidth` px, `paintOrder: stroke fill`) and fill layer in front.
- `font.outlineColor` special value `"character"` resolves to the speaking character's color; `innerOutlineColor`/`innerOutlineWidth` settings are not consumed anywhere.
- Fade-in over 0.15s. Font size never auto-shrinks.

`SceneVisuals.tsx`:

- Animations over ~0.3s: fadeIn, slideUp (+50px Y), slideLeft (+100px X), zoomIn (scale 0.8->1), bounce (spring, damping 15, stiffness 100), none.
- Container area: top 60, left 80, right 80, bottom 180 (hardcoded; `SETTINGS.content` paddings are generated but no component reads them).
- Image visual: `<Img src=staticFile(content/<src>)>` object-fit contain. Note the `content/` prefix (see 4.2).
- Text visual: centered, `fontSize` default 64, bold, outline stroke at `fontSize * 0.16` px in `outlineColor` default `#1F2937` (dark outline so text survives light backgrounds, commit `44c926e`).

`config.ts`: `VIDEO_CONFIG` fallbacks, `COLORS` palette (engine-level), `CharacterId = string` (data-driven port change), empty `characterSpeakerMap`.

`engine/public/` layout: `background.png` (default riverbank, overwritten by the mapper each build), `bgm/.gitkeep` (unwired), `content/.gitkeep` (image visual root), `se/.gitkeep` (sound effects), `voices/` created per build (`NN_<char>.wav`, `durations.json`, `.source`), `images/<character_id>/mouth_open.png` + `mouth_close.png` + optional `<emotion>_open.png`/`<emotion>_close.png`.

Checked-in `config/` samples: `characters.yaml` (momo right #37474F, kiki left #F9A825), `defaults.yaml` (sample pauseAfter 12; the mapper always regenerates it with 15), `script.yaml` (6-line Bahasa Malaysia sample with zoomIn/slideLeft/bounce text cards). `video-settings.yaml` mirrors the generated shape with `playbackRate: 1.2`.

### 2.5 Canonical -> engine mapping (every row from AGENTS.md, with mapper behavior)

| canonical | engine target | behavior |
|---|---|---|
| meta.language | - | ignored, informational |
| characters.<id>.name | characters.yaml name | subtitle placeholder, placeholder box label |
| characters.<id>.position | characters.yaml position | "left" or "right", default "right", not gated |
| characters.<id>.color | characters.yaml color | subtitle outline + placeholder box, default #4B5563 |
| characters.<id>.flip_x | characters.yaml flipX | scaleX(-1), default false |
| characters.<id>.image | public/<path> | ship art under project assets/, set settings.character.use_images true |
| characters.<id>.voice | (platform) | vendor consumes voices/NN_<id>.wav + manifest |
| script[].text | script.yaml text | spoken line, estimate length basis |
| script[].display_text | script.yaml displayText | subtitle override |
| script[].scene | script.yaml scene | 1..3 documented as named backgrounds; in code it only feeds the unused sceneInfo |
| script[].pause_after | script.yaml pauseAfter | seconds -> frames (`round(*fps)`), default 15 frames |
| script[].emotion | script.yaml emotion | normal/happy/surprised/thinking/sad, art variant fallback chain |
| script[].visual | script.yaml visual | type text/image/none; font_size->fontSize; dark outline by default, outline_color overrides; terminal degrades to a "$ command" text card |
| script[].se | script.yaml se | src relative to public/ (played from `se/<src>`), volume default 1, existence-checked |
| settings.background | public/background.png | theme from repo catalog, project file wins, default riverbank |
| settings.* | video-settings.yaml | snake->camel, unknown keys error |
| vendor.remotion.estimate_cps | timing estimate | chars/sec, default 7.5 |

### 2.6 What degrades, what errors (remotion)

Degrades:

- Terminal visuals become plain text cards.
- Scene ids above 3 (and scene generally) have no background effect.
- Missing emotion art falls back mouth_open/close.
- No platform voices -> silent placeholder wavs, estimated timing.
- Subtitles over 84 visible chars -> build-time warning only.
- ffprobe absent -> duration guard skipped with warning.

Hard errors: unknown settings section/key, unknown `vendor.remotion` key, unknown character in script, missing visual/se asset, no characters, empty script, unparseable/missing project.yaml, background not matching `^[a-z0-9-]+$` or not in catalog, bad manifest seconds.

Not supported, stated in AGENTS.md: background music (hook exists, hardcoded off), positions other than left/right.

### 2.7 playback_rate (remotion)

- `settings.video.playback_rate` -> `SETTINGS.video.playbackRate`, default 1.2.
- Voice `<Audio playbackRate={rate}>` (Remotion time-stretches the wav), line and pause windows are `ceil(frames / rate)` in both Main.tsx scheduling and Root.tsx total.
- Platform voice durations are stored rate-inflated (`ceil(seconds * fps * rate)`) then divided back out.
- Estimate quirk: the estimate path divides by the rate twice, once in `seconds = visible / (cps * rate)` (mapper line 242) and again in `adjusted()` (line 254). At the default 1.2 an estimated line window is about 31% shorter than the platform path would give for the same text (`visible/(cps*rate^2)` vs `visible/cps`). At rate 1.0 the two agree.

---

## 3. Hyperframes vendor (`vendors/hyperframes/`)

### 3.1 Build pipeline (`build.sh`), step by step

1. Same arg handling, `WORK = vendors/hyperframes/.work/<project>/`, `rm -rf $WORK`.
2. Copy `PROJECT_DIR/voices` -> `$WORK/voices`, `PROJECT_DIR/assets` -> `$WORK/assets` (directory itself, unlike remotion's contents-into-public).
3. `npm install --prefix $VENDOR_DIR/scripts --silent` (installs the mapper's single `yaml` dependency from `scripts/package.json`: `wayang-hyperframes-mapper`, private, type module, yaml ^2.4.0).
4. `node $VENDOR_DIR/scripts/map-project.mjs $PROJECT_DIR $WORK` -> `index.html`, `package.json`, `expected-seconds.txt`, `timeline.json`, `fonts/`, plus background/voices/images copies.
5. `(cd $WORK && npx --yes hyperframes@latest render --output $WORK/out.mp4 -f 30)`. First run downloads the hyperframes CLI and Chromium (bundled Puppeteer) + system ffmpeg does the encode.
6. Duration guard: ffprobe vs `$WORK/expected-seconds.txt`, 0.5s tolerance, same wording and ffprobe-missing warning as remotion.
7. Copy `$WORK/timeline.json` and `$WORK/out.mp4` -> `$OUT_DIR/video.mp4`.

### 3.2 Mapper (`scripts/map-project.mjs`), full behavior

Parsing and gates:

- Prefers `.merged.yaml`. Missing/parse error dies.
- Defaults: `cps` 7.5, `playbackRate` 1 (differs from remotion's 1.2), `fps` 30, `W` 1920, `H` 1080, font family "Inter", size 70, weight "900", charH 275, subtitle width 55%, bottom 40.
- `vendor.hyperframes`: only `estimate_cps` allowed, unknown keys die.
- `settings.background` must be a string if present.
- No settings-section gate exists: unknown `settings.*` keys are silently ignored (difference from remotion, see 4.3).
- Lines 75-77 contain an empty `for (const line of script) {}` loop: dead code, no effect.
- There is no image-visual existence check (unlike remotion). A missing image src is copied as a broken reference and renders as a missing image. A missing se file crashes `fs.copyFileSync` with an uncaught exception (non-zero exit, stack trace, not a `die()` message).

Voices and timeline (unit: seconds throughout):

- Platform path: manifest must cover every line, `voiceSeconds[file] = manifest.seconds`.
- Estimate path: `raw = max(0.8, visible_chars / cps)`.
- `dur = raw / playbackRate`. `pause = (pause_after ?? 0.5) / playbackRate`. Default pause 0.5s equals remotion's 15 frames at 30fps.
- `subEnd = start + dur + pause` (subtitle stays up through the pause).
- Cursor adds `dur + pause`. `total = round(t + 2, 3)`: 2s tail, same as remotion's 60 frames at 30fps.
- `timeline.json`: `{id, start, end}` with `end` = speech end only, plus `total`.
- `expected-seconds.txt` = `total`.

Background: the theme PNG is always copied first (`assets/backgrounds/<theme>.png` -> `$WORK/background.png`), then the project's `assets/background.png` overwrites it when present. Default `riverbank`. Unknown theme dies.

Asset copies: project `voices/` -> `$WORK/voices`, project `assets/images/` -> `$WORK/images` (build.sh already copied the whole assets dir; the mapper's copy normalizes the images path).

Font handling (remotion difference): the mapper downloads the requested Google font at map time. `curl` of `fonts.googleapis.com/css2?family=...:wght@<weight>` (15s timeout, Chrome UA), first `woff2` URL extracted, downloaded to `fonts/text.woff2` (20s timeout), declared with `@font-face`. Any failure: warn, fall back to system fonts. Remotion instead loads a hardcoded Google font via `@remotion/google-fonts/MPLUSRounded1c` regardless of `settings.font.family`.

Geometry / overlap detection:

- Subtitle box: width `W * max_width_percent/100`, height `fontSize * 1.5 * 2` (2-line standard), horizontally centered, bottom `bottom_offset`.
- Character boxes: `charH` square at the bottom corner with 40px inset on the character's side.
- If the subtitle box intersects a character box, the subtitle moves up: `subY0 = min(subY0, box.y0 - 24 - subH)`, final bottom clamped to 0. Movement is logged (`overlap: subtitle moved above characters`).
- `tools/wayang.py` runs the same intersection check as a lint failure, so the mapper's fix keeps the lint green.

### 3.3 Generated composition (`index.html`)

Shell:

- `<div id="root" data-composition-id="main" data-start="0" data-duration="<total>" data-width="<W>" data-height="<H>">`.
- GSAP 3.14.2 from the pinned CDN `cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js`, used only to register an empty timeline: `const tl = gsap.timeline({ paused: true }); window.__timelines["main"] = tl; <tweens> tl.seek(0);`.
- Global CSS resets margins, sets body to exactly WxH with `overflow: hidden`, `#root` full size with the font family.

Clip model (authoring rules learned from the renderer's lint, per the mapper header):

- Every timed element is `class="clip"` with `data-start` and `data-duration` (seconds) and a stable `id`. Media without an id renders silent, hence the named audio ids.
- Every visual clip is a full-frame wrapper `<div class="clip" id="clip-N" data-start data-duration data-track-index style="position:absolute;inset:0;z-index:<z>">`; content is positioned inside the wrapper so the runtime's full-frame `.clip` rule cannot distort placement (commit `1932e7c`).
- Track/z-index layout:

| track | z | content |
|---|---|---|
| 0 | 0 | background img, full duration, object-fit cover |
| 5 | 5 | visual cards: terminal window, image card, text card |
| 10 | 10 | character base: art (mouth_close) or placeholder box, full duration |
| 11 | 11 | lip flap open/close imgs, 0.2s slices during speech |
| 20 | - | voice `<audio class="clip" id="line-<id>-audio">` with `data-playback-rate` |
| 21 | - | se `<audio class="clip" id="line-<id>-se">` with `data-volume` |
| 30 | 30 | subtitle div |

Characters:

- `use_images` (default false) AND `images/<id>/mouth_close.png` present -> art mode: one base `mouth_close` img for the full duration (track 10) plus, for each of the character's speaking segments, alternating `mouth_open`/`mouth_close` slices (track 11): `k` walks from `seg.start` to `seg.end` in `min(0.2, remaining)` steps, toggling open/close. This is the lip flap: 0.2s alternation, about 5 flaps per second.
- Otherwise a 200x300 rounded placeholder box in the character color with the name, full duration, no flap.

Per line:

- Voice audio element: `src="voices/<NN>_<char>.wav"`, `data-start`, `data-duration = dur` (already rate-scaled), `data-playback-rate = playbackRate`, track 20.
- se (optional): file copied from the project preserving its relative `src`, duration probed with ffprobe (`probeSeconds`, any error falls back to 1.5s), `data-duration = min(probed, dur + pause_after)`. Note: the pause here is the raw value, not divided by playbackRate. `data-volume = volume ?? 1` (2 decimals, honored by the runtime), track 21.
- Subtitle div (track 30): bottom `<subBottomFinal>`px, centered, width pct, font family/size/weight from settings, color `font.color` default `#ffffff`, `-webkit-text-stroke` at `fontSize * 0.2` px in `font.outline_color` default `#1F2937`, `paint-order: stroke fill`, `overflow-wrap: anywhere`, `text-wrap: balance`, `line-height: 1.4`. Runs from `start` to `subEnd` (speech + pause).
- Text card (track 5): `font_size` default 84, `inset: 0 0 25% 0` (upper 75% of frame), stroke `0.16 * size` px, `outline_color` default `#1F2937`, `white-space: pre-wrap`, `text-wrap: balance`.
- Image card (track 5): centered with translate(-50%,-50%), `max-width: 70%`, `max-height` = `font_size` clamped to `H * 0.45` (font_size doubles as a max-height override for images), object-fit contain, radius 12, `src` relative to the workdir (project assets live at `assets/...` in the workdir).

### 3.4 Terminal simulation (`visual.type: terminal`)

One clip (track 5, z 5) spanning `start` to `subEnd`, containing:

- Window: absolute at `top: 12%`, horizontally centered, `width: 76%`, background `#161B22`, 2px border `#30363D`, radius 12, large drop shadow, `overflow: hidden`.
- Title bar: `#21262D`, three 13px dots `#FF5F56` / `#FFBD2E` / `#27C93F`, label "wayang" in `#8B949E` 20px.
- Body: padding 22px 28px, font-size 34px (`termFs`), line-height 1.55, color `#C9D1D9`, `overflow-wrap: anywhere`.
- Command line: `<span style="color:#7EE787">$ </span>` prompt followed by one `<span class="ch" style="opacity:0">` per character of `visual.command` (missing command dies).
- Command typing tween: `tl.to("#cmd-N .ch", { opacity: 1, duration: 0.02, stagger: <step>, ease: "none" }, <typeStart>)` where `typeStart = seg.start + 0.35` and `typeDur = clamp(cmdChars * 0.035, 0.6, 1.6)`, `stagger = typeDur / cmdChars.length`. Characters appear left to right over at most 1.6s.
- Output lines (`visual.output`, array): one div per entry, opacity 0, color `#9EAEBC`, `margin-top: 12px`, font-size 30px, `white-space: pre-wrap`. Reveal tween: `tl.to("#out-N-i", { opacity: 1, duration: 0.18 }, <seg.start + 0.9 + i * 0.5>)`. The first output appears 0.55s after typing starts, further outputs every 0.5s.
- Min-height math: `charsPerLine = max(20, floor((W * 0.76 - 56) / (34 * 0.62)))`, `cmdLines = ceil(len / charsPerLine)`, `minH = 30 + (cmdLines + outs.length) * 34 * 1.7`. This `minH` is computed and then never used: the window div style carries no min-height. It is dead code (plausibly a casualty of the unclosed-div fix in commit `7a59c6b`).
- Wrapping: both command and outputs rely on `overflow-wrap: anywhere` / `pre-wrap` rather than clipping (commit `b530b92` replaced clipping with wrapping).

Terminal steps degrade to a plain text card in the remotion vendor; this simulation is hyperframes-only.

### 3.5 playback_rate (hyperframes)

- `settings.video.playback_rate`, default 1. Honored end to end as of commit `a02c528`: voice audio plays at the rate via `data-playback-rate`, line durations and pauses are divided by the rate, the composition `data-duration` and `expected-seconds.txt` scale to match. 0.9 is the documented "slower, calmer tutorial pace".
- AGENTS.md contradiction: the first timing paragraph says "`playback_rate` is ignored by this vendor (audio plays at natural speed)" while the next paragraph and the code honor it. The "ignored" sentence is stale.
- Characters have no per-character voice rate; `characters.<id>.voice` only feeds the platform TTS.

### 3.6 Canonical -> composition mapping (AGENTS.md rows)

| canonical | composition | behavior |
|---|---|---|
| meta.language | - | ignored |
| characters.<id>.name/color/position | placeholder box or art position | left or right, 40px inset, default right, color default #4B5563 |
| characters.<id>.voice | voices/NN_<id>.wav | platform-generated, manifest durations |
| script[].text / display_text | subtitle div per line | outlined, bottom-centered, word wrap, display_text wins |
| script[].scene | - | not a concept, visuals play per line |
| script[].pause_after | subtitle/card tail | seconds, default 0.5, divided by playback_rate |
| script[].emotion | - | no effect, "needs emotion art variants; otherwise invisible" |
| script[].visual.type text | centered text card | dark outline default, outline_color override |
| script[].visual.type image | centered image card | src relative to the project/workdir, no existence gate |
| script[].visual.type terminal | simulated terminal | typing + output reveals, GSAP tweens |
| script[].se | per-line audio clip | src project-relative, ffprobe duration (1.5s fallback), data-volume honored |
| settings.background | background.png | theme from shared catalog, riverbank default, project file wins |
| settings.font / subtitle / character | CSS values | family/size/weight/color, bottom_offset/max_width_percent/outline_color, height/use_images |
| settings.video | root data-* + timing | width, height, fps (render -f), playback_rate |
| vendor.hyperframes.estimate_cps | timing estimate | chars/sec, default 7.5 |

---

## 4. Differences between the vendors

### 4.1 Capability matrix

| Area | Remotion | Hyperframes |
|---|---|---|
| Render model | React components, frame-by-frame, Remotion CLI | One static index.html, HyperFrames CLI + Puppeteer + ffmpeg |
| Timing unit | Frames (fps from settings) | Seconds |
| Default playback_rate | 1.2 | 1 |
| Estimate floor per line | 24 frames (0.8s at 30fps) | 0.8s |
| Default pause | 15 frames (0.5s) | 0.5s |
| Tail | 60 frames (2s) | 2s |
| Terminal visual | Degrades to "$ command" text card | Full simulation (typing, outputs, window chrome) |
| Emotions | Art variants with fallback chain | No effect |
| Scenes | Metadata only, no render effect | Not a concept |
| BGM | Hook exists, hardcoded off | None |
| se handling | `<Audio>` in the line Sequence, volume from canonical | Separate audio clip, probed duration, data-volume, missing file crashes uncaught |
| Image visual location | `staticFile(content/<src>)` under public/content/ | Workdir-relative src (project assets/...) |
| Image visual existence check | Yes, dies | No |
| Unknown settings.* keys | Hard error | Silently ignored |
| Fonts | @remotion/google-fonts, hardcoded M PLUS Rounded 1c regardless of settings | Downloads settings.font at map time, @font-face, system fallback |
| Subtitle wrapping | BudouX for CJK, word wrap + balance + anywhere for the rest | overflow-wrap anywhere + text-wrap balance |
| Lip flap | Render-frame driven, ~6 flips/s (frame/5) | 0.2s clip slices (~5/s) |
| Character animation | Slide-in, bob while speaking | Static img swap only |
| Subtitle/character overlap | Not handled in-engine; platform lint fails it | Mapper moves the subtitle above the box and logs it |
| Config generation | YAML configs + two TS sync scripts | Direct HTML string assembly |
| node dependencies at build | engine/ install (shared, symlinked) | scripts/ yaml install each run (cached) |
| Workdir asset convention | project assets/. -> public/ root | project assets/ -> workdir assets/, voices -> workdir voices |

### 4.2 Path conventions worth remembering

- Remotion image visuals: mapper checks `PROJECT_DIR/<visual.src>`, build.sh copies project assets into `public/` root, but the renderer loads `public/content/<visual.src>`. For the image to actually render, the src must line up with the `content/` prefix. This is a latent mismatch for `assets/...`-style srcs; the hyperframes vendor has no such prefix.
- Both mappers resolve the theme catalog via `workDir/../../../..` -> repo root. Moving a vendor deeper breaks it.
- Hyperframes se `data-duration` uses `dur + pause_after` with the raw pause, not the rate-scaled pause.

### 4.3 Contract compliance deltas

- "Errors on unsupported canonical keys": remotion enforces for settings + vendor keys. Hyperframes enforces vendor keys only; unknown settings keys pass silently.
- "Writes OUT_DIR/expected-seconds.txt": neither vendor copies it out of the workdir.
- Remotion logs `TTS source: ...` in the mapper; hyperframes does the same. Both satisfy the "build log names the audio engines" rule.

---

## 5. Environment requirements

Remotion vendor:

- Node 24 + npm (docs and README). One-time `npm install` in `vendors/remotion/engine/`; the build symlinks that node_modules into the workdir.
- `ffprobe` on PATH for the duration guard; skipped with a warning when absent.
- Network for @remotion/google-fonts font loading at render.
- Render command uses defaults: no concurrency, browser, or GL flags anywhere in the repo.

Hyperframes vendor:

- Node 22+, ffmpeg, network. First `npx --yes hyperframes@latest` run downloads the CLI and Chromium.
- GSAP loads from the pinned jsdelivr CDN on every render of the composition.
- Font download needs network at map time (curl, 15s + 20s timeouts); failures degrade to system fonts with a warning.
- ffprobe for se durations (1.5s fallback on error) and the duration guard.

Platform side: uv + Python for `tools/wayang.py`, PIL for lint image diffing, ffmpeg/ffprobe for guards, lint, and frame extraction.

TTS: `REVOLAB_API_KEY` (default) or `OPENAI_API_KEY`. Without a key everything renders silent with estimated timing, labeled in the log.

## 6. Known slowness

Verified finding: the repo contains no screenshot-fallback, heap, or worker tuning notes. A search over the current tree and the full git history (screenshot, heap, worker, concurrency, gl=, maxWorkers) returns nothing. The only cost facts in code:

- Hyperframes first run pays the npx CLI download plus a Chromium fetch; GSAP and the Google font are fetched per build unless HTTP-cached.
- Hyperframes renders frame by frame through Puppeteer.
- Remotion renders with default concurrency and no tuning flags.
- Fonts fall back silently rather than failing the build (hyperframes), so a network blip can produce a visually degraded render instead of an error.

If such notes existed elsewhere (a runbook outside this repo), they are not in the tree or the history.

## 7. Drift and dead code observed (read from source)

- `vendors/remotion/AGENTS.md` points at `vendors/remotion/assets/backgrounds/`; that directory does not exist. The catalog is repo-root `assets/backgrounds/`.
- Hyperframes `AGENTS.md` says playback_rate is ignored, then documents it as honored; the code honors it.
- Remotion `AGENTS.md` claims scenes 1..3 have named backgrounds; `Main.tsx` computes `sceneInfo` and never uses it.
- Terminal `minH` is computed and never emitted (hyperframes mapper).
- Empty `for` loop over script lines (hyperframes mapper lines 75-77).
- Remotion engine leftovers from upstream: `zundamon`/`metan` color key names in generated `colors`, zundamon/metan emoji picks in the placeholder box.
- Remotion settings generated but unconsumed: `content.*` paddings, `subtitle.maxWidthPixels` is consumed, `innerOutlineColor`/`innerOutlineWidth` are not.
- `expected-seconds.txt` stays in the workdir; the contract says OUT_DIR.

## Open questions you might ask

1. Remotion image visuals: the renderer loads `public/content/<src>` while the mapper validates `PROJECT_DIR/<src>` and build.sh copies assets into the `public/` root. Which src convention should projects use, and should the mapper either prepend `content/` or drop the prefix?
2. Is the remotion estimate path's double playback-rate division intentional (`visible/(cps*rate)` then `ceil(frames/rate)`)? At the default 1.2 it shortens estimated lines about 31% relative to the platform-voice path.
3. Which hyperframes AGENTS.md sentence is stale: "playback_rate is ignored" or the honoring paragraph plus `data-playback-rate` code? (Code says honored since commit a02c528.)
4. Should the remotion vendor implement scene backgrounds (the AGENTS.md row and the unused `scenes`/`sceneInfo` suggest a planned feature), or should scene be dropped from its mapping table?
5. The hyperframes terminal `minH` is computed but never applied to the window div. Was it dropped during the unclosed-div fix (commit 7a59c6b), and should short terminal windows reserve height again?
6. Where should per-vendor performance notes (screenshot fallback, heap, worker tuning) live? The task expectation assumes they exist; nothing is in the tree or git history.
7. Should `expected-seconds.txt` actually be copied to OUT_DIR to match the contract, or should the contract stop listing it as an OUT_DIR artifact?
8. Hyperframes silently ignores unknown `settings.*` keys while the contract mandates erroring on unsupported canonical keys. Should the mapper get the same settings gate remotion has?

hook: PostToolUse
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse Completed
exec
/usr/bin/zsh -lc "sed -n '1,220p' REPO_ANALYSIS/02-vendors.md" in /mnt/data/work/wayang
 succeeded in 0ms:
# 02 - Vendors: remotion and hyperframes

Reference for the two video engines under `vendors/`. Every fact below is read from the repo tree at its current commit (`a02c528`). Where the code and a doc disagree, both are stated. Nothing is projected.

## Sources read

| Area | Files |
|---|---|
| Shared | `docs/vendor-contract.md`, root `AGENTS.md`, `README.md`, `docs/project-yaml.md`, `docs/tutorial.md`, `tools/wayang.py` (lint section) |
| Remotion | `vendors/remotion/AGENTS.md`, `build.sh`, `scripts/map-project.mjs`, `engine/package.json`, `engine/video-settings.yaml`, `engine/config/{characters,defaults,script}.yaml`, `engine/scripts/{sync-script,sync-settings}.ts`, `engine/src/{index,Root,Main,config}.tsx/.ts`, `engine/src/components/{Character,Subtitle,SceneVisuals}.tsx`, generated `engine/src/data/script.ts` + `engine/src/settings.generated.ts`, `engine/public/` layout |
| Hyperframes | `vendors/hyperframes/AGENTS.md`, `build.sh`, `scripts/map-project.mjs` (every line), `scripts/package.json`, generated sample `.work/hf-demo/index.html` |
| Assets | `assets/backgrounds/` catalog, `assets/background/` generators |

---

## 1. Shared vendor contract (`docs/vendor-contract.md`)

### Entry point

```
vendors/<engine>/build.sh PROJECT_DIR OUT_DIR
```

- Wrong arg count: usage to stderr, exit 2. Both scripts run `set -euo pipefail`.
- Input: `PROJECT_DIR/project.yaml` (canonical, all timing in seconds). When the platform materialized series inheritance, `PROJECT_DIR/.merged.yaml` exists and both mappers prefer it.
- Required outputs: `OUT_DIR/video.mp4`, `OUT_DIR/timeline.json` shaped `{"lines": [{"id", "start", "end"}...], "total"}` (seconds), and `expected-seconds.txt`.
- Contract deviation: both build.sh scripts write `expected-seconds.txt` to the workdir only and never copy it to `OUT_DIR`. The duration guard reads it from the workdir, so it works, but the contract text ("Writes OUT_DIR/...expected-seconds.txt") is not literally honored.
- Idempotent: the workdir is deleted and rebuilt on every run.
- Error policy: unsupported canonical keys are a hard error, never a silent drop. Remotion enforces this fully. Hyperframes gates `vendor.hyperframes` keys but silently ignores unknown `settings.*` keys (see 4.3).
- The build log must name the audio source. Both mappers print `TTS source: <engines> (platform-generated voices)` or `TTS source: estimate`.

### Audio honesty (both vendors)

Priority order, never mixed within one project:

1. Platform-generated voices in `PROJECT_DIR/voices/`: one wav per line named `NN_<character>.wav` (NN = zero-padded line id, `padStart(2,"0")`) plus `voices/manifest.json` with `lines: {"NN_<character>.wav": {"seconds": ...}}` and `engines: [...]`. Coverage must be complete: one missing entry or file falls the whole project through to estimate. Bad `seconds` (non-finite or <= 0) is a hard error in remotion.
2. Estimate: durations from character count, silent placeholder audio, log says `estimate`.

`characters.<id>.voice` in canonical YAML is consumed by the platform (`tools/wayang.py` + `tools/tts_providers.py`), not by vendors. Vendors only see wavs + manifest.

### Guards the platform runs after a build

Duration guard (inside both build.sh scripts):

- `ffprobe -show_entries format=duration` of the rendered mp4 vs `expected-seconds.txt`.
- Pass window: `expected - 0.5 <= actual <= expected + 0.5` (awk comparison).
- Fail: `ERROR: rendered duration deviates from the computed timeline`, exit 1. Remotion names the bug class: "empty-tail bug".
- `ffprobe` missing: `WARNING: duration guard skipped`, build continues. Empty/missing expected file: guard skipped silently.

Visibility lint (`tools/wayang.py lint_project`, vendor-agnostic, runs after build inside `wayang.py render`):

- Reads `timeline.json` from the out dir. Missing or empty: `SystemExit(1)`, "the vendor must emit the timeline it renders".
- Reference frame extracted at `duration - 0.4s`. Per line, frame extracted at `start + dur * 0.6` (dur = timeline `end - start`).
- Subtitle band: centered, width = `settings.subtitle.max_width_percent` (55), bottom band height = `font.size * 1.5 * 2` above `bottom_offset` (40). Ink = pixel diff count vs reference frame. `< 150` diff pixels fails.
- Text card region: 15%-85% width, 15%-62% height. Checked only for lines with a text visual. `< 150` fails.
- Character corner box: `charH` (275) square at the bottom corner, 40px inset, side from `position`. Compared against the pure theme PNG (`assets/backgrounds/<theme>.png` resized to the frame). Presence `< charH*charH/60` fails.
- Audibility: when `voices/manifest.json` has engines (real voices), mean volume is probed at `mid + 0.21s`. `< -55 dB` fails the line.
- Pre-render layout check: subtitle band intersecting a character box fails before any frame extraction.

### Background themes

- Shared catalog: `assets/backgrounds/` at the repo root. Both mappers resolve it relative to their workdir (`workDir/../../../..`).
- Resolution order in both: project `assets/background.png` > named theme `settings.background` > default `riverbank`.
- `settings.background` must match `^[a-z0-9-]+$` (remotion) or be a string (hyperframes), and must exist in the catalog, else hard error listing available themes.
- Generators that make the themes: `assets/background/generate_themes.py`, `assets/background/generate_background.py`.

### Theme catalog (`assets/backgrounds/`)

11 synthesized PNG themes: `batik`, `chalkboard`, `kraft-paper`, `night-sky`, `notebook`, `riverbank`, `slate`, `studio`, `sunrise`, `whiteboard`, `wood-table`.

Note: `vendors/remotion/AGENTS.md` says the catalog lives at `vendors/remotion/assets/backgrounds/`. That directory does not exist. The real catalog is the repo-root one and that is what `map-project.mjs` reads.

---

## 2. Remotion vendor (`vendors/remotion/`)

### 2.1 Build pipeline (`build.sh`), step by step

1. Resolve absolute `PROJECT_DIR`, create absolute `OUT_DIR` (mkdir -p), locate `VENDOR_DIR`.
2. `WORK = vendors/remotion/.work/<project-basename>/`. `rm -rf $WORK`, `mkdir -p $WORK/public/voices`.
3. Copy engine source: `tar -C engine --exclude=node_modules --exclude=out -cf - . | tar -C $WORK -xf -`.
4. Symlink `engine/node_modules` into `$WORK/node_modules` (one-time `npm install` in `engine/` is a repo prerequisite).
5. Copy project assets into the engine's static root: `cp -R $PROJECT_DIR/assets/. $WORK/public/` (contents land at `public/` root). Done before mapping so existence checks and the renderer see the files.
6. `node $VENDOR_DIR/scripts/map-project.mjs $PROJECT_DIR $WORK` (see 2.2).
7. `(cd $WORK && npm run sync)` = `sync-settings` then `sync-script` (see 2.3).
8. `(cd $WORK && npx remotion render src/index.ts Main out/video.mp4)`. No concurrency, browser, or GL flags are passed.
9. Duration guard (ffprobe vs `$WORK/expected-seconds.txt`, 0.5s tolerance, see 1).
10. Copy `$WORK/timeline.json` and `$WORK/out/video.mp4` to `OUT_DIR`.

### 2.2 Mapper (`scripts/map-project.mjs`)

Input parsing:

- Prefers `.merged.yaml` over `project.yaml`. Missing file or YAML parse error: `die()` (exit 1 with `[map-project] ERROR:`).
- Reads `characters`, `script`, `settings`, `vendor.remotion`. Defaults: `fps` 30, `playbackRate` 1.2, `estimate_cps` 7.5.

Gates (all hard errors):

- `vendor.remotion`: only `estimate_cps` allowed. Unknown key dies.
- `settings`: allowed sections `video, font, subtitle, character, content` with exact key whitelists (see mapping table). Unknown section or key dies. `settings.background` is handled outside the gate.
- Script line referencing an unknown character dies. Empty script dies. No characters dies.
- `visual.src` and `se.src` must exist under `PROJECT_DIR` or die.
- `visual.type: terminal` needs `visual.command` or dies.

Settings conversion (snake_case canonical -> camelCase engine, defaults filled in):

| Section | Canonical keys accepted | Engine keys | Engine defaults |
|---|---|---|---|
| video | width, height, fps, playback_rate | width, height, fps, playbackRate | 1920, 1080, 30, 1.2 |
| font | family, size, weight, color | family, size, weight, color | "M PLUS Rounded 1c", 70, "900", "#ffffff" (+ engine-only outlineColor "character", innerOutlineColor "none") |
| subtitle | bottom_offset, max_width_percent, outline_width | bottomOffset, maxWidthPercent, outlineWidth | 40, 55, 14 (+ engine-only maxWidthPixels 1000, innerOutlineWidth 8) |
| character | height, use_images, images_base_path | height, useImages, imagesBasePath | 275, false, "images" |
| content | top_padding, side_padding, bottom_padding | topPadding, sidePadding, bottomPadding | 0, 0, 0 |

`maxWidthPixels`, `innerOutlineWidth`, `innerOutlineColor` exist in the engine defaults but have no canonical input key.

Characters -> `config/characters.yaml`: `{name, position (default "right"), color (default "#4B5563"), flipX (default false), defaultPauseAfter: 15}`. Position values are not gated to left/right here.

Script -> `config/script.yaml`: per line `{id, character, text}` plus optional `displayText`, `scene`, `pauseAfter` (`Math.round(pause_after * fps)` frames, only when set), `emotion`, `visual`, `se {src, volume default 1}`.

Visual conversion:

- `terminal` degrades to a text card: `{type: "text", text: "$ " + command, animation: visual.animation || "fadeIn"}`, plus optional fontSize/color. The simulated terminal is a hyperframes-only feature.
- `text`/`image` pass through with `font_size -> fontSize`, `color`, `outline_color -> outlineColor`, `animation`. `none` and missing visual produce no visual key.

Subtitle lint: visible chars = whitespace-stripped `text` length. Over 84 chars prints a WARNING ("wraps past 2 lines", Netflix TTSG standard of about 42 chars per line, 2 lines max). Warning only, never an error.

`config/defaults.yaml` (generated): `newLine: {character: <first line's speaker>, pauseAfter: 15, durationInFrames: 60, scene: 1, emotion: null}`, `automation: {voiceOnSave: false, autoVoiceFileName: true}`.

`video-settings.yaml` (generated): engineSettings above plus `colors: {background: "#ffffff", text: <font.color>, zundamon: <first char color>, metan: <second char color or first>}`. The `zundamon`/`metan` key names are upstream leftovers; they carry Momo/Kiki colors.

Voice handling -> `public/voices/`:

- Platform path: for every line, copy `voices/NN_<char>.wav` into the workdir, `durations[f] = Math.ceil(seconds * fps * playbackRate)`. Log names the engines.
- Estimate path: `visible = whitespace-stripped text length`, `seconds = visible / (cps * playbackRate)`, `frames = max(24, ceil(seconds * fps))`. Writes a silent 24kHz 16-bit mono placeholder wav of `frames/fps` seconds so every `<Audio>` resolves. Log says `estimate`.
- Writes `durations.json` (file -> frames) and `.source` (`platform` or `estimate`).

Timeline and expected length (frames, `adjusted(f) = Math.ceil(f / playbackRate)`):

- Per line window: `adjusted(durationInFrames)` speech + `adjusted(pauseAfter ?? 15)` pause. Cursor accumulates both.
- `timeline.json`: seconds, `start = cursor/fps`, `end = (cursor + speech)/fps`, each rounded to 3 decimals. `end` is the speech end, the pause is not included.
- `expected-seconds.txt`: `(60 + sum(speech + pause windows)) / fps`, 3 decimals. The 60-frame closing buffer matches Root.tsx.
- The comment states the intent: this is the exact timeline the renderer plays, so the platform lint probes the true windows.

Background: validates theme name against the repo catalog, then either keeps the project's `assets/background.png` (log: project custom override) or copies `assets/backgrounds/<theme>.png` to `public/background.png` (default `riverbank`).

### 2.3 Sync step (config -> generated TS)

`engine/package.json` scripts: `build` = `sync` + `remotion render src/index.ts Main out/video.mp4`, `start` = `sync` + remotion studio, `sync` = `sync-settings` + `sync-script` (both via ts-node). Dependencies: remotion ^4.0.0, @remotion/{bundler,cli,renderer}, @remotion/google-fonts ^4.0.409, budoux ^0.6.2, react 18, yaml 2.3.4.

`scripts/sync-settings.ts`: `video-settings.yaml` -> `src/settings.generated.ts` exporting `SETTINGS` (the YAML as const) and `AVAILABLE_IMAGES` (scan of `public/images/<id>/*.png`, one filename list per character id).

`scripts/sync-script.ts`: `config/script.yaml` + `config/characters.yaml` + `config/defaults.yaml` + `public/voices/durations.json` -> `src/data/script.ts` exporting:

- Types: `AnimationType` ("none" | "fadeIn" | "slideUp" | "slideLeft" | "zoomIn" | "bounce"), `VisualContent`, `SoundEffect`, `BGMConfig`, `ScriptLine` (emotion enum "normal" | "happy" | "surprised" | "thinking" | "sad"), `SceneInfo`.
- `bgmConfig: BGMConfig | null = null` (hardcoded null, BGM unwired).
- `scenes`: metadata only, `[{id: 1, Opening, gradient}, {id: 2, Main Content, solid}, {id: 3, Ending, gradient}]`.
- `CHARACTERS`: array of `{id, name, position, color, flipX}` from characters.yaml. Data-driven, any id works.
- `characterColors`: id -> color map.
- `scriptData`: each line enriched with `voiceFile = "NN_<character>.wav"`, `durationInFrames` from durations.json (fallback: `defaults.newLine.durationInFrames` = 60), `pauseAfter` (fallback: `defaults.newLine.pauseAfter` = 15).

### 2.4 Engine runtime architecture

Composition chain: `src/index.ts` (`registerRoot`) -> `Root.tsx` -> single `<Composition id="Main">` -> `Main.tsx`.

`Root.tsx`:

- Total frames = sum over lines of `ceil(durationInFrames / playbackRate) + ceil(pauseAfter / playbackRate)` + 60 closing buffer. First line starts at frame 0, no opening buffer.
- This per-line rate adjustment (instead of summing raw frames) is the port's fix for the empty-tail bug at rate > 1; commit `118fa17`.
- Composition `fps`/`width`/`height` come from `SETTINGS.video` with `config.ts` VIDEO_CONFIG (1920x1080@30) as fallback.

`Main.tsx` (one component, no Sequences for visuals; it derives state from `useCurrentFrame()`):

- Walks `scriptData` accumulating rate-adjusted frames to find the current line, its start frame, its scene, and `isSpeaking` (frame is inside the speech window, not the pause).
- Renders, in order: full-frame background `Img` (`staticFile("background.png")`, object-fit cover); BGM `<Audio>` only if `bgmConfig` is non-null (never); per-line `<Sequence from={startFrame} durationInFrames={adjusted speech}>` containing the voice `<Audio src=voices/<voiceFile> playbackRate={SETTINGS.video.playbackRate}>` and an optional se `<Audio src=se/<src> volume={volume ?? 1}>`, with `premountFor={fps}`; `<SceneVisuals>` for the current line's visual; `CHARACTERS.map(...)` to `<Character>` (isSpeaking and emotion only for the current speaker, others get "normal"); a `<Subtitle>` Sequence spanning only the speech window with `displayText ?? text`.
- `sceneInfo = scenes.find(...)` is computed and never used. The visible background is the single static `background.png` for the whole video. The `scene` key has no visual effect in the current code, despite the AGENTS.md mapping row "1..3 have named backgrounds".

`Character.tsx`:

- Looks up its config in `CHARACTERS`; unknown id renders null.
- Mouth flap while speaking: `Math.floor(frame / 5) % 2 === 0` (about 6 flips per second at 30fps).
- Gentle bob while speaking: `sin(frame * 0.3)` mapped to -3..3 px vertical.
- Slide-in on mount: from -200px (left) or +200px (right) to 0 over 0.5s, clamped.
- Art path: `<imagesBasePath>/<id>/<file>`; `useImages` false renders a 200x300 rounded placeholder box in the character color with the character name.
- Emotion art resolution (existence-checked against `AVAILABLE_IMAGES`): `<emotion>_<open|close>.png` -> `<emotion>_open.png` -> `mouth_<open|close>.png`.
- `flipX` applies `scaleX(-1)`.
- Leftover: placeholder emoji picks "zundamon"/"metan" icons by hardcoded id, any other id gets a speech-bubble emoji.

`Subtitle.tsx`:

- Bottom-centered, width `maxWidthPercent`% capped at `maxWidthPixels`, `bottomOffset` from the bottom.
- Per-line script-aware wrapping: CJK lines (regex on hiragana..halfwidth katakana, CJK blocks) are segmented with BudouX (segments rendered as inline-block nowrap spans), other scripts use normal word wrap. Plus `text-wrap: balance` and `overflow-wrap: anywhere`. Commit `dede006`.
- Two text layers: stroke layer behind (`WebkitTextStroke` at `subtitle.outlineWidth` px, `paintOrder: stroke fill`) and fill layer in front.
- `font.outlineColor` special value `"character"` resolves to the speaking character's color; `innerOutlineColor`/`innerOutlineWidth` settings are not consumed anywhere.
- Fade-in over 0.15s. Font size never auto-shrinks.

`SceneVisuals.tsx`:

- Animations over ~0.3s: fadeIn, slideUp (+50px Y), slideLeft (+100px X), zoomIn (scale 0.8->1), bounce (spring, damping 15, stiffness 100), none.
- Container area: top 60, left 80, right 80, bottom 180 (hardcoded; `SETTINGS.content` paddings are generated but no component reads them).
- Image visual: `<Img src=staticFile(content/<src>)>` object-fit contain. Note the `content/` prefix (see 4.2).
- Text visual: centered, `fontSize` default 64, bold, outline stroke at `fontSize * 0.16` px in `outlineColor` default `#1F2937` (dark outline so text survives light backgrounds, commit `44c926e`).

`config.ts`: `VIDEO_CONFIG` fallbacks, `COLORS` palette (engine-level), `CharacterId = string` (data-driven port change), empty `characterSpeakerMap`.

`engine/public/` layout: `background.png` (default riverbank, overwritten by the mapper each build), `bgm/.gitkeep` (unwired), `content/.gitkeep` (image visual root), `se/.gitkeep` (sound effects), `voices/` created per build (`NN_<char>.wav`, `durations.json`, `.source`), `images/<character_id>/mouth_open.png` + `mouth_close.png` + optional `<emotion>_open.png`/`<emotion>_close.png`.

Checked-in `config/` samples: `characters.yaml` (momo right #37474F, kiki left #F9A825), `defaults.yaml` (sample pauseAfter 12; the mapper always regenerates it with 15), `script.yaml` (6-line Bahasa Malaysia sample with zoomIn/slideLeft/bounce text cards). `video-settings.yaml` mirrors the generated shape with `playbackRate: 1.2`.

### 2.5 Canonical -> engine mapping (every row from AGENTS.md, with mapper behavior)

| canonical | engine target | behavior |
|---|---|---|
| meta.language | - | ignored, informational |
| characters.<id>.name | characters.yaml name | subtitle placeholder, placeholder box label |
| characters.<id>.position | characters.yaml position | "left" or "right", default "right", not gated |
| characters.<id>.color | characters.yaml color | subtitle outline + placeholder box, default #4B5563 |
| characters.<id>.flip_x | characters.yaml flipX | scaleX(-1), default false |
| characters.<id>.image | public/<path> | ship art under project assets/, set settings.character.use_images true |
| characters.<id>.voice | (platform) | vendor consumes voices/NN_<id>.wav + manifest |

hook: PostToolUse
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse Completed
exec
/usr/bin/zsh -lc 'cat REPO_ANALYSIS/03-templates-content-docs.md' in /mnt/data/work/wayang
 succeeded in 0ms:
# 03 - Templates, content, docs, and art

Reference for the four template formats, the mascot cast, the art and
background pipelines, the documentation set, and the demo projects.
Sources read in full: templates/*/template.yaml, templates/*/README.md,
AGENTS.md, README.md, docs/*.md, assets/mascots/generate_mascots.py,
assets/background/generate_themes.py, assets/background/generate_background.py,
projects/video-tutorial/*, schema/project.schema.json, tools/wayang.py,
vendors/*/scripts/map-project.mjs. Commit a02c528, 2026-09-27.

## Entry docs

- `AGENTS.md` - agent manual and router. Defines the layout, the five-step
  workflow (`templates` -> `init` -> `check` -> edit -> `validate` ->
  `render`), and the invariants: canonical YAML with second timing, unknown
  keys error, vendors ship `build.sh PROJECT_DIR OUT_DIR` plus
  `timeline.json` and `expected-seconds.txt`, duration guard at 0.5s
  tolerance, series deep-merge where the episode wins per key, check before
  render with FILL items relayed in plain words.
- `README.md` - human entry. Lists the formats, mascots, the 11 background
  themes, the vendor model, requirements (Node 24 + npm, uv,
  ffmpeg/ffprobe, one-time `npm install` in `vendors/remotion/engine`),
  TTS engines (`revolab` via `REVOLAB_API_KEY`, `openai` via
  `OPENAI_API_KEY`, silent estimated-timing fallback), and the series
  command.

## The template formats

Five directories live under `templates/`. The root docs name four formats
(dialog, presentation, storytelling, community). `tutorial` is the fifth,
built for the hyperframes vendor. Every template renders as-is after
`wayang.py init`; the template.yaml is a working sample.

| format | sample title | hosts | lines | scenes | pauses (s) | emotions | card style | vendor | playback_rate | background | font size |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dialog | Kenalan dengan Momo & Kiki | Momo right + Kiki left | 6 | 3 | 0.4, last 1.0 | none | text card on alternating lines (zoomIn, slideLeft, bounce) | remotion | 1.2 | unset (engine default riverbank) | 70 |
| presentation | Tabiat Pagi | Momo only | 6 | 3 | 1.2, last 1.0-1.5 | none | card on 5 of 6 lines (zoomIn, slideLeft, slideUp) | remotion | 1.2 | unset | 70 |
| storytelling | Harta Karun Kecil | Momo + Kiki | 6 | 3 | 0.4-0.6, last 1.0 | surprised, thinking, happy sprinkled on 4 lines | mood cards on 4 of 6 lines | remotion | 1.2 | unset | 70 |
| community | Meetup Komuniti | Momo + Kiki | 6 | 3 | 0.4, last 1.0 | none | cards on 4 of 6 lines (bounce, zoomIn, slideLeft) | remotion | 1.2 | unset | 70 |
| tutorial | Cara Guna Wayang | Momo as teacher | 10 | 3 | 0.8-2.0 | none | 4 text cards + 6 `type: terminal` steps | hyperframes | 0.9 | slate | 66 |

All sample scripts are Bahasa Malaysia (`meta.language: ms`). Pacing
differs by design: dialog is quick banter, presentation gives cards time
to breathe, tutorial slows to 0.9 so terminal steps stay readable.

### What every template.yaml contains

- `meta`: `title`, `template`, `vendor`, `language: ms`, `description`.
- `characters`, keyed by id:
  - `momo`: name Momo, color `#37474F`, position right, voice
    `{engine: revolab, voice_id: paan-f695215e}`.
  - `kiki`: name Kiki, color `#F9A825`, position left, voice
    `{engine: revolab, voice_id: nur-b184422b}`.
- `script`, one entry per spoken line: `id`, `character`, `text` (spoken
  and subtitled), `scene` (groups lines into sections), `pause_after`
  (seconds), optional `emotion`, optional `visual`.
  - `visual.type: text`: `text`, `font_size` (84-96), `color: #ffffff`,
    `animation` (zoomIn, slideLeft, slideUp, bounce, fadeIn).
  - `visual.type: terminal` (tutorial only): `command` plus `output`
    (list of lines). Hyperframes renders a typing animation in a terminal
    window; on remotion the terminal degrades to a command text card.
- `settings`:
  - `video`: 1920x1080, fps 30, `playback_rate` (1.2 everywhere except
    tutorial 0.9; slows voice and pacing).
  - `font`: family `M PLUS Rounded 1c`, size 70 (66 in tutorial), weight
    900, color `#ffffff`.
  - `subtitle`: `bottom_offset: 40`, `max_width_percent: 55`,
    `outline_width: 14`.
  - `character`: `height: 275`, `use_images: true`.
- `vendor`: `estimate_cps: 7.5` (characters per second for the no-TTS
  timing estimate), under the vendor name.

### What the user fills vs what is preset

Preset by the template: resolution, fps, playback_rate, font, subtitle
geometry, character height, image mode, estimate_cps, sample scenes and
cards. Fills that are the user's (per `docs/project-yaml.md` and the
README fill order):

1. `meta.title`.
2. Per character: `name` and the `voice` block (revolab `voice_id`, or
   openai `voice`).
3. Script lines: `text`, speaker, `scene`, `pause_after`, optional cards.

Optional per line: `display_text` (overrides the subtitle text),
`emotion`, `visual`, `se` (sound effect). Optional per character:
`flip_x` when art faces the wrong way. Optional in settings:
`background`. READMEs give one fill order in three steps: characters,
script, settings. Character art is optional; without it characters render
as colored placeholder boxes.

README quirks: dialog and community share their fill-order text, and
community carries a leftover dialog sentence ("walk through a topic in
2-3 scenes with big text cards."). The storytelling README has an honesty
note: emotions change drawn art only and are invisible with placeholder
boxes.

## The mascot cast

| character | species | YAML color | drawn colors | position | revolab voice_id | persona in sample scripts |
|---|---|---|---|---|---|---|
| Momo | Malayan tapir | `#37474F` | body `#2F2F38`, cream saddle and belly `#F7F3E8` (`CREAM`), dark ears with cream tips, pink blush `#EFA3AC` | right | `paan-f695215e` | "tapir paling ceria" (cheerful) |
| Kiki | hornbill | `#F9A825` | body `#3A3230`, wings `#4A403C`, beak `#F2A93B`, casque `#E8862B`, white tail fan `#F6F2E9`, eyelash strokes | left | `nur-b184422b` | "tak pernah senyap" (never quiet) |
| Rimau | chibi Malayan tiger | `#F57C00` (`ORANGE`) | orange body, black `#262626` stripes (forehead, cheeks, body, tail), cream muzzle, paws, belly, whisker dots | right in the tutorial walkthrough | `ali-13002bfa` (docs/tutorial.md only) | eager explorer in the tutorial walkthrough |

Rimau is the third mascot, added in commit 9155a65. No template ships
Rimau; he exists in the generator, in docs/tutorial.md's walkthrough, and
in stale vendor workdirs (`vendors/remotion/.work/rimau-intro/`). Rimau
reuses Momo's round eye set for every emotion (same face geometry).

### Art inventory on disk

- `templates/{dialog,presentation,storytelling,community}/assets/images/{momo,kiki}/`:
  10 PNGs per character: `mouth_open/close`, `happy_open/close`,
  `sad_open/close`, `surprised_open/close`, `thinking_open/close`. 20 per
  template.
- `templates/tutorial/assets/images/momo/`: the same 10, momo only.
- `projects/video-tutorial/assets/images/momo/`: the same 10.
- `assets/mascots/`: the generator plus 4 checked-in SVG sources
  (`momo_open/close.svg`, `kiki_open/close.svg`). These SVGs are early
  drafts: each carries an opaque background rect `#CFE9B8`, while current
  generator output renders transparent. The generator writes its current
  SVGs to `/tmp/mascot-art/`, not to this directory.
- `projects/rimau-intro/assets/images/rimau/`: deploy target for 10 rimau
  PNGs. Does not currently exist on disk.

## The art pipeline

- Generator: `assets/mascots/generate_mascots.py` (943 lines, 3
  characters).
- Approach: one Python function per character builds an SVG body string.
  The mouth is a swappable group; the `_open` and `_close` variants
  render the same body with a different mouth group string, so every
  pixel outside the mouth is identical by construction. `docs/mascot-art.md`
  names this pair consistency as the reason for code over image models:
  two image-model generations never align.
- Render: cairosvg `svg2png`, 1024x1024, transparent background
  (`bg=None`), atomic writes (tempfile then `os.replace`). SVG sources go
  to `/tmp/mascot-art/` (base), `/tmp/mascot-art/emotions/`,
  `/tmp/mascot-art/rimau/`.
- Emotion system: `EMOTIONS = ("happy", "surprised", "thinking", "sad")`.
  An emotion variant swaps the eye/brow group and the mouth group; the
  body is the base body. Per character: 1 base pair + 4 emotion pairs =
  10 PNGs. Output: 4 base + 16 emotion PNGs for momo/kiki plus 10 rimau
  PNGs per run.
- File naming the renderer requires (under
  `assets/images/<character_id>/` in the project): `mouth_open.png`,
  `mouth_close.png`, optional `<emotion>_open.png`, `<emotion>_close.png`
  (happy, surprised, thinking, sad). All frames of one character must
  share one canvas size. Art faces the viewer, else set `flip_x: true`
  on the character.
- Verification, all in-script and failing loudly:
  - `check_frame`: 1024x1024, four corner pixels alpha 0 (transparent).
  - `verify_pair`: full pixel diff of two frames; the diff bbox must sit
    inside the mouth box (open vs close) or the face box (emotion vs
    base), and must be non-empty. Boxes are per-character constants
    (`EMO_DIFF_BOX`, `FACE_BOX`).
  - `check_character_presentation`: ink bbox margins over 20px, ink
    center within 60px on x and 80px on y of canvas center, and mouth
    color counts inside the mouth box: open frames need over 200 maroon
    `#7A3B44` px and over 30 tongue `#E98A96` px; close frames need both
    under 20.
- Deployment: `deploy_emotions()` copies momo/kiki emotion PNGs into the
  four templates in `TEMPLATE_NAMES` plus
  `projects/rimau-intro/assets/images/`. `deploy_rimau()` writes the 10
  rimau PNGs (renamed to the renderer scheme) into
  `projects/rimau-intro/assets/images/rimau/`. The tutorial template is
  not in `TEMPLATE_NAMES`, so its momo emotion art is never refreshed by
  a rerun.
- Regenerate:
  `uv run --with cairosvg --with pillow assets/mascots/generate_mascots.py`
- Image-model alternative (`docs/mascot-art.md`): usually looks richer.
  Workflow: generate ONE front-facing full-body base character, plain
  background, flat vector style; get the closed mouth by one
  inpaint/edit pass on the mouth area only, never a second full
  generation; export both states at one canvas size (1024x1024 fine);
  emotion variants are face inpaints from the same base frame. Renderer
  requirements are identical to the code path: PNG, one canvas size per
  character, exact file names, viewer-facing art or `flip_x: true`.

## The background theme catalog

11 PNGs in `assets/backgrounds/`, all 1920x1080: batik, chalkboard,
kraft-paper, night-sky, notebook, riverbank, slate, studio, sunrise,
whiteboard, wood-table.

- `assets/background/generate_themes.py` builds 10 of them (all but
  chalkboard). One builder function per theme, flat-vector SVG,
  deterministic geometry, cairosvg render, atomic write, then per-theme
  pixel probes: exact coordinates plus expected color with a tolerance,
  a mismatch raises and fails the run.
- `assets/background/generate_background.py` is the older single-theme
  script that produced chalkboard: green board `#2d5a3d` on a white
  room, 24px wooden trim `#8B4513` with grain streaks, 8 chalk smudge
  ellipses, geometry matching the remotion `Main.tsx` board contract
  (board inset top 40, sides 60, bottom 160). Checks: white room
  corners, green board center, wooden trim sample. Its output path is
  `vendors/remotion/engine/public/background.png`.
- Studio is the strengthened theme and the largest file (149KB vs 9-20KB
  for the rest): white radial-gradient spotlight center falling to
  `#9FB0BA` at the edges, a stage floor band from 72% height (`#B7C4CC`)
  with an 8px darker edge line, and two spotlight pools on the floor.
- Slate is the tutorial default: flat `#263238` with 6 faint white smudge
  ellipses at 0.05 opacity, chosen as terminal-friendly.
- Batik carries the Malaysian identity: cream `#F5EDD8` with top and
  bottom bands of rotated brown petal ellipses around red `#A63D2F`
  dots.
- Stale paths: both scripts hardcode output under
  `/mnt/data/work/content_engine/`, the repo name before the wayang
  rename (commit 848d28e). Running them as-is writes outside this repo.
- How `settings.background` resolves (remotion `map-project.mjs`):
  project `assets/background.png` override > named theme PNG from repo
  root `assets/backgrounds/` > engine default `riverbank`. The name must
  match `^[a-z0-9-]+$`; an unknown theme kills the map with the
  available list. The chosen PNG is copied into the engine and read as
  `staticFile("background.png")`.
- `tools/wayang.py`: the visibility lint loads
  `ROOT/assets/backgrounds/<theme>.png` (default riverbank when unset)
  as the reference image for the character-corner presence check, and
  warns plus skips when the PNG is missing. `validate` checks the theme
  name against `vendors/<vendor>/assets/backgrounds`, but only when that
  directory exists; no vendor ships one, so the check is currently a
  no-op. `schema/project.schema.json` types `background` as a plain
  string, no enum.

## The docs set

- `docs/tutorial.md` - for beginners. Follows a real run that adds Rimau
  and renders his intro. Seven steps:
  1. `wayang.py templates` - pick a format.
  2. `wayang.py init presentation rimau-intro` - copy template into
     `projects/` (gitignored, yours).
  3. `wayang.py check` - preflight in plain words, `FILL:` = fix,
     `NOTE:` = advice, exit codes 0 ready / 1 blockers / 2 notes only.
  4. Fill `meta.title`, character `name` + `voice`, script lines (YAML
     examples, Rimau voice `ali-13002bfa`, revolab lists ids at
     `GET /v1/voices`).
  5. `wayang.py validate` - strict gate: schema plus references.
  6. `wayang.py render` - one command: per-line wavs (cached),
     mapping, render, visibility lint.
  7. Optional character art, with the two ways to make it (code
     generator, image models) and the 0.2s lip-flap rule.
  Ends with a failure table of 4 rows: missing `voice.engine`, silent
  estimated-timing renders, timeline drift ("re-render, else file an
  issue"), unknown theme, plus pointers to backgrounds, `se:` and
  `visual.type: image`, series, and `AGENTS.md`.
- `docs/mascot-art.md` - for art makers. States the shipped art is
  script-drawn SVG, not image-model output, and why (mouth-pair
  consistency). Covers the generator, sources, cairosvg renderer,
  regenerate command, the self-check list, steps to add a new character
  to the generator, the full image-model workflow, the renderer's file
  requirements, and a backgrounds section pointing at
  `assets/background/` plus the project-level `assets/background.png`
  override.
- `docs/project-yaml.md` - the canonical YAML reference. Sections
  (`meta`, `characters`, `script`, `settings`), voice engine fields
  (revolab `voice_id`; openai `voice`, `model`, `speed`,
  `instructions`), script line fields (`display_text`, `se`, `emotion`,
  `visual`), `settings.background` resolution, the three user fills,
  and series inheritance (`init-series`, deep-merge, episode wins per
  key, `render projects/<series>` renders all episodes in order).
- `docs/vendor-contract.md` - for engine authors. The deal:
  `vendors/<engine>/build.sh PROJECT_DIR OUT_DIR`, read
  `project.yaml` (prefer `.merged.yaml` when series was materialized),
  write `video.mp4`, `timeline.json`
  (`{"lines": [{"id","start","end"}...], "total"}`),
  `expected-seconds.txt`, exit 0, idempotent workdir, error on
  unsupported canonical keys. Platform guards after each build:
  duration via ffprobe against expected-seconds at 0.5s tolerance, and
  the visibility lint (subtitle ink, card ink, character in corner
  boxes, real-voice lines over -55 dB). Background catalog resolves
  relative to the vendor workdir. Per-vendor env notes: Remotion needs
  Node 24 and `npm install`; Hyperframes needs Node 22+, ffmpeg, and
  downloads its CLI plus Chromium on first run.

## Demo projects

`projects/` holds one project: `video-tutorial`. (`.gitignore` covers
`projects/` and `out/`, so this state is local-only, not in git.)

- `projects/video-tutorial/` - an `init` of the tutorial template with
  the YAML unchanged from `templates/tutorial/template.yaml`. Fully
  rendered state:
  - `out/video.mp4`: 43.8s, 1.8MB.
  - `out/timeline.json`: 10 lines, start 0 to end 40.667, total 43.778s
    (matches the mp4 inside the 0.5s guard).
  - `out/.lint/`: 21 probe frames (`f1`-`f10` plus `b` variants and
    `tail.png`) from the visibility lint.
  - `voices/`: `01_momo.wav` to `10_momo.wav`, all revolab (1.8-3.7s
    each), plus `manifest.json` with per-line hash, seconds, engine.
  Demonstrates: the tutorial format end to end, a hyperframes render
  with simulated terminal steps, revolab TTS, and cached voice reuse.
- `projects/rimau-intro` does not exist, though the mascot generator
  deploys into it and docs/tutorial.md walks through creating it.
  `vendors/remotion/.work/` holds stale workdirs from earlier builds
  (`rimau-intro`, `emotion-demo`, `ep01`, `dialog-ms`,
  `presentation-test`, `est-demo`, `fixture-project`), so Rimau and
  emotion renders ran before the projects were cleaned.

## Open questions you might ask

1. Both background generator scripts still write to hardcoded
   `/mnt/data/work/content_engine/` paths from before the wayang rename.
   Should they be repointed at this repo (and should
   `generate_background.py` still target
   `vendors/remotion/engine/public/background.png`)?
2. `wayang.py validate` checks `settings.background` against
   `vendors/<vendor>/assets/backgrounds`, a directory no vendor ships,
   making the check a no-op. Should it point at the root
   `assets/backgrounds/` catalog instead?
3. The tutorial template is missing from `TEMPLATE_NAMES` in
   `generate_mascots.py`, so its momo emotion art never refreshes on
   regeneration. Intended, or should the tutorial ship kiki art too?
4. Rimau has no Revolab voice in any template; the only voice id is
   `ali-13002bfa` in docs/tutorial.md. Which voice id is canonical, and
   should Rimau art ship in templates like momo and kiki do?
5. The checked-in SVG sources under `assets/mascots/` carry an opaque
   green `#CFE9B8` background while current generator output is
   transparent. Are they drafts to replace, or reference copies to keep?
6. The community README reuses the dialog README's fill-order text,
   including a leftover dialog sentence about 2-3 scenes and text cards.
   Copy leftover to fix?
7. Should the remotion vendor implement the `terminal` visual natively
   instead of degrading it to a command text card, so tutorial projects
   render the same on both vendors?

hook: PostToolUse
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse Completed
exec
/usr/bin/zsh -lc 'cat REPO_ANALYSIS/04-history-decisions.md' in /mnt/data/work/wayang
 succeeded in 0ms:
# 04 - History and decisions

Reference for the owner. Covers the full commit chronology, the rumpun
campaign state and directives, the two multi-model consults, the bug
classes fixed along the way, the rename, and what is deliberately kept
out of git.

Sources: `git log` (38 commits, one branch `main`, remote
`https://github.com/khursani8/wayang.git`), `.rumpun/` (rumpun.yaml,
seasons/s1.yaml, ledger/directives.jsonl, prompts/base/, runs/), README.md,
AGENTS.md. Note: `.rumpun/runs/` is gitignored, so the raw review
documents exist only on disk. The adopted decisions survive in git through
the ledger and commit 5ecfebc.

## Build timeline in one paragraph

The repo was built in one day: 38 commits between 11:52:40 and 23:47:25
(+0800) on 2026-09-26, all authored `sani <sani@local>`, all on `main`,
no branches, no merges, no reverts. The work ran as a rumpun campaign
(season s1) with a written operator directive and an append-only ledger.
The arc: MVP with a ported engine, pluggable TTS, series support,
original mascots and Malay identity, rendering correctness guards, a
second engine, a two-model structure review and restructure, the rename
to Wayang, then beginner onboarding (tutorial doc, tutorial template,
final lint hardening).

## Commit chronology

Times are +0800, 2026-09-26. Oldest first.

### Phase 1 - MVP and TTS (11:52-12:14)

| hash | time | what it delivered |
|---|---|---|
| dafeabf | 11:52 | content_engine MVP: `schema/project.schema.json` (canonical YAML, timing in seconds), `templates/education` + `templates/community`, `vendors/remotion` (patched port of nyanko3141592/remotion-voicevox-template with data-driven characters, `build.sh PROJECT_DIR OUT_DIR` contract, estimate TTS fallback), `tools/ce.py` (init/validate/render, uv PEP 723), the whole `.rumpun/` campaign state. E2E verified: both templates rendered to mp4 on estimate timing. |
| 2fd0e74 | 12:07 | Pluggable TTS: `tools/tts_providers.py` (voicevox + openai clients, stdlib only), `ce.py tts` command + auto-tts in render, per-line manifest (hash, seconds, engine), resumable, vendor consumes `projects/<p>/voices` when present. OpenAI path NOT verified against the live API (no key on the box, stated in the commit). |
| e38feb6 | 12:07 | gitignore `__pycache__` (a `.pyc` had leaked into 2fd0e74). |
| 3ed0923 | 12:12 | revolab TTS provider (`api.revolab.ai/v1/tts`, default model nada-1.0-pro, native wav 24 kHz), verified with real synthesis E2E: 6 live lines, community-test rendered with real audio. Recorded that `nada-1.0-flash` (from the operator's curl example) does not exist; valid models are nada-1.0-pro and aisyah-1.0-pro. |
| c64a503 | 12:14 | remotion mapper drops its voicevox-only voice gate. Engine validation is the platform's job (provider registry in ce.py); without this, revolab/openai projects could not render. |

### Phase 2 - Series, templates, mascots (12:33-13:11)

| hash | time | what it delivered |
|---|---|---|
| b340fee | 12:33 | Series support: `series.yaml` sparse base deep-merged under each episode (episode wins per key, dicts merge, lists replace), merge-then-validate, batch validate/tts/render in name order stopping at first failure, `init-series`, render materializes `.merged.yaml` so vendors never see series. Proven by a negative test: remove series.yaml and ep02 fails with required name/voice errors. |
| b8fa6f3 | 12:45 | Templates renamed by format, not topic: `education` -> `dialog`, added `presentation` (1 presenter + cards) and `storytelling` (hosts + emotions). All ran on the engine unchanged. |
| 34d5bc9 | 13:04 | Identity switch: dropped the upstream zundamon/metan pair. Original mascots Momo (tapir, revolab voice paan-f695215e) and Kiki (hornbill, nur-b184422b), Bahasa Malaysia sample scripts (`language: ms`), generated SVG-derived lip-flap art shipped per template, generator sources kept in `assets/mascots/`. |
| ddf97aa | 13:11 | Mascot art re-rendered with transparent backgrounds after operator feedback (solid rectangles looked wrong over the chalkboard). Generator now asserts corner alpha is zero and that open/close pairs differ only inside the mouth region. |
| 477ff3f | 13:11 | gitignore `.omc` state (session-state files had leaked, including under `assets/mascots/`). |

### Phase 3 - Rendering correctness (13:20-13:48)

| hash | time | what it delivered |
|---|---|---|
| dede006 | 13:20 | Subtitle wrapping: BudouX-JA wraps Japanese but emitted near-whole-line segments for Latin text, which then overflowed the centered container. CJK keeps BudouX, other scripts wrap at word boundaries, `text-wrap: balance`, `overflow-wrap: anywhere`, no auto-shrink, build-time warning past ~84 visible chars. Rules follow Netflix TTSG (~42 chars/line, max 2 lines). |
| 118fa17 | 13:31 | Empty-tail fix: `Root.tsx` summed raw frames while playback ran at `ceil(frames / playbackRate)`, so at rate 1.2 the composition ran ~17% longer than the timeline (3.7s of empty chalkboard on dialog-ms). Root now sums per-line adjusted frames plus one 60-frame closing buffer (the upstream 60-frame opening buffer was dead weight). 26.37s -> 20.67s, matching 620 computed frames. |
| 859f006 | 13:48 | Duration regression guard: mapper writes `expected-seconds.txt` (sum of per-line rate-adjusted frames + 60-frame tail), `build.sh` ffprobes the output and exits 1 on >0.5s deviation. Any repeat of the empty-tail bug class is now a loud build error. |

### Phase 4 - Backgrounds and polish (14:01-16:25)

| hash | time | what it delivered |
|---|---|---|
| 109e0fc | 14:01 | Chalkboard background as a generated 1920x1080 PNG (`assets/background/generate_background.py`, SVG + cairosvg, self-checked pixels), replacing flat divs in `Main.tsx`. Project can override with `assets/background.png`. |
| 5b83b25 | 14:47 | Theme system: `generate_themes.py` synthesizes 10 themes (whiteboard, night-sky, kraft-paper, batik, notebook, sunrise, studio, riverbank, slate, wood-table), catalog at `vendors/remotion/assets/backgrounds/`, `settings.background` resolves custom file > named theme > engine default, unknown themes error. |
| 3690719 | 14:54 | gitignore: untrack root `.omc/` session state (had been committed since dafeabf). |
| 44c926e | 14:57 | Text cards get a subtitle-style outline (`visual.outline_color`, stroke 0.16x font size) because flat white cards vanished on light themes like riverbank. |
| 888f0dd | 16:12 | README refresh for cloners: real state of the repo, fresh-clone install steps. |
| bf5fe5c | 16:25 | Engine default background becomes riverbank; chalkboard stays selectable. |

### Phase 5 - Identity purge (17:24-17:37)

| hash | time | what it delivered |
|---|---|---|
| 23f1b82 | 17:24 | All Japanese removed from the remotion engine: upstream ja sample wavs/art/configs deleted, engine configs rewritten to momo/kiki in Bahasa Malaysia, every Japanese comment and log line translated. "Malaysian repo, Malaysian content." |
| e9e709a | 17:37 | VOICEVOX removed as a TTS provider (provider class, schema branch, `generate-voices.ts` 230 lines, build branch, all doc mentions). TTS engines are revolab and openai only; keyless builds fall back to estimates. |

### Phase 6 - Second engine and the visibility lint (17:59-18:24)

| hash | time | what it delivered |
|---|---|---|
| 10748ba | 17:59 | hyperframes vendor, the second engine, onboarded with zero `ce.py` changes: `AGENTS.md` + `build.sh` + `map-project.mjs`, canonical YAML -> one `index.html` composition (data-* clips, seconds-based), lip flap as alternating 0.2s mouth clips, estimate fallback, explicit errors (never silent drops) for unsupported se/image visuals/scenes, same duration guard. |
| 1932e7c | 18:11 | HyperFrames authoring rules learned from the first broken render: media without a stable `id` renders silent, the runtime's full-frame `.clip` rule fills unset dimensions (once stretched Momo to 1920px wide), fonts need `@font-face` (mapper now downloads the Google font woff2 at map time). Added deterministic subtitle/character overlap detection. |
| b264afe | 18:12 | gitignore `vendors/*/.work/`: the hyperframes workdir (generated HTML, fonts, wavs, out.mp4) had been committed with 10748ba and 1932e7c when shells ran from the wrong cwd. Purged here. |
| 95bc2f2 | 18:18 | Visibility lint, vendor-agnostic, in `ce.py`: recomputes the timeline from the project YAML, extracts frames at each line midpoint, checks subtitle ink, text-card ink, per-corner character animation, and per-line voice loudness (real voices must exceed -55 dB; estimate renders skip and are labeled). `render` runs it automatically, `ce.py lint` re-runs it. Proven: silent windows measure -91 dB. |
| a097776 | 18:24 | Lint stops recomputing: estimate renders quantize per-line frames, so recomputed windows drifted past the render end and failed later lines. Both vendors now emit `timeline.json` (the renderer's own math, exact start/end per line) and the linter consumes it, falling back to the formula only when absent. Missing frames fail with a message instead of crashing. |

### Phase 7 - Structure review and capability completion (18:48-19:43)

| hash | time | what it delivered |
|---|---|---|
| 5ecfebc | 18:48 | The structure restructure (details below): shared background catalog at `assets/backgrounds/` (11 PNGs moved out of `vendors/hyperframes/assets/`, per-vendor copies deleted), root `AGENTS.md` cut from 119 lines to a ~40-line router with deep rules split into `docs/vendor-contract.md` and `docs/project-yaml.md`, vendor manuals trimmed to engine deltas, new `ce.py check` preflight (plain-words FILL items, GLM's exit scheme 0/1/2, `--json`), linter fallback formula deleted (timeline.json now required). |
| 19c4cfd | 19:22 | hyperframes gains `script[].se` (per-line sound effects, ffprobe duration, own track) and `visual.type image` (centered image card); the se/image gates and not-supported errors removed; hf-demo exercises both. Also regenerated `studio.png` (contrast). |
| 5c324d4 | 19:43 | Mascot emotion art: 16 emotion frames (happy, surprised, thinking, sad x open/close x Momo/Kiki), pairs verified pixel-identical outside the face box, shipped in all templates; `docs/mascot-art.md` documents the no-image-model pipeline and the image-model alternative with its pair-consistency trade-off. |

### Phase 8 - Rename (20:28-21:51)

| hash | time | what it delivered |
|---|---|---|
| 848d28e | 20:28 | Rename to Wayang (details below). |
| e247071 | 21:51 | Upstream repo reference (nyanko3141592) removed from `rumpun.yaml` and `vendors/remotion/AGENTS.md`. Commit history still contains the name. |

### Phase 9 - Onboarding and final hardening (22:29-23:47)

| hash | time | what it delivered |
|---|---|---|
| 9155a65 | 22:29 | Rimau the tiger, third mascot (chibi Malayan tiger, #F57C00): base lip-flap pair + four emotion pairs, all pair-verified. Also fixes the mascot generator's deploy root, stale since the rename. rimau-intro rendered with real Revolab voices. |
| 8d018d2 | 22:36 | `docs/tutorial.md`: clone to first MP4 in seven steps, following the real Rimau run, with a failure table. |
| 0b96a81 | 23:03 | Visibility lint v2 (details below) + the fifth template, `tutorial` (6 simulated terminal steps, Momo with emotions). |
| b530b92 | 23:10 | Terminal steps: font 24 -> 34px, window to 76% width, per-character GSAP stagger typing so long commands wrap instead of clipping; caret dropped. |
| 7a59c6b | 23:25 | Terminal window fix: one missing closing `</div>` (details below). |
| e9561b4 | 23:41 | Tutorial shows the fill example explicitly: a terminal step displays the exact YAML to write, so the FILL warning is paired with its fix. |
| a02c528 | 23:47 | `settings.video.playback_rate` honored by hyperframes (voice clip data-playback-rate, pauses and timeline scale, timeline.json/expected-seconds reflect it). Tutorial template ships at 0.9x (43.55s vs 39.27s at 1.2x). |

## The campaign: `.rumpun/`

`.rumpun/` is committed (except `runs/`, see the gitignore section) and
its git history is the campaign's evolution ledger. Layout per
`.rumpun/README.md`: `rumpun.yaml` (campaign config), `seasons/` (one
YAML per season), `ledger/` (append-only evidence), `prompts/base/`
(phase prompt templates), `runs/` (per-season workspaces, gitignored),
`adhd-rules.md` (output-style card, verbatim from
github.com/ayghri/i-have-adhd), `CHANGELOG.md` (campaign schema
versions; schema 1 only).

### rumpun.yaml (campaign config)

- Goal: build content_engine as a framework-agnostic YAML-template video
  platform, `vendors/<engine>/AGENTS.md` as the engine contract agents
  consume, remotion first.
- Metric: E2E - `ce.py init education demo` -> fill project.yaml ->
  `ce.py render projects/demo` -> mp4 with no manual fixes.
- Autonomy: stage `manual`; promote after 5 clean audits; demote on 2
  consecutive rejects; rejection rolls back to last good, pauses,
  escalates after 2.
- Review panel: families `[fable, glm, gpt-5.6-sol]`, majority rule,
  blinded.
- Invariants: goal_immutable, budget_cap, falsify_required.
- Budget: campaign cost cap 600.
- Routes: glm, claude (unsets all ANTHROPIC model/base-url overrides so
  fable serves), and a codex fleet (gpt-6-astra/sol/luna, gpt-reserve,
  gpt-5.6-sol/terra/luna, gpt-5.5, codex-auto-review), all
  `codex exec --dangerously-bypass-approvals-and-sandbox`.

### seasons/s1.yaml (the seed season)

- Goal: ship the MVP (education + community templates, canonical schema,
  remotion vendor with AGENTS.md contract, ce.py init/validate/render).
- Mode: fight. Methodology line: contract-first platform, three-model
  design consult (codex gpt-5.5, glm-5.3, fable) before schema freeze,
  then build and prove with a real render.
- Pipeline: phase design-review (writers answer
  `prompts/base/design-brief.md`) -> phase integrate (evaluate ->
  `runs/design-decisions.md`).
- Writers: codex on gpt-5.5 (knowledge: none), glm on glm-5.3
  (knowledge: none), fable (knowledge: full). 15 minutes each. Stop on
  all_exited.

### Ledger directives (`.rumpun/ledger/directives.jsonl`)

Convention: the ledger is append-only. Entries keep status `pending` even
after execution; closure is recorded by a new entry, never by editing old
ones. Directive 6 is that closure.

| seq | demanded / recorded | status |
|---|---|---|
| 0 | Operator directive: build the content_engine MVP end to end, no questions. Education + community templates, canonical YAML schema, vendors/remotion port with AGENTS.md, tools/ce.py. Consult codex + glm-5.3 + fable before schema freeze. | Executed (dafeabf, plus the consult records). Closed by seq 6. |
| 1 | s1 outcome record: MVP built and E2E-verified. education smoke-test -> 19.5s / 1.7MB / 585 frames mp4; community-test -> 18.9s mp4 with arbitrary character ids. TTS honestly labeled "estimate" (VOICEVOX not installed). Consult outcomes recorded; codex round 2 returned empty output. | Historical record. Closed by seq 6. |
| 2 | TTS is user-managed API providers, the platform owns no docker/service. Pluggable voice engines in the canonical schema, implement openai (OPENAI_API_KEY) + the existing voicevox endpoint. Platform tts step writes voice files; vendor consumes them, falls back to estimate. | Executed (2fd0e74). voicevox provider itself was later removed (e9e709a). Closed by seq 6. |
| 3 | Record: revolab provider added and verified E2E (nada-1.0-pro, wav 24 kHz, 6 voices through the platform path). `nada-1.0-flash` from the operator's example is not a valid model; API exposes nada-1.0-pro and aisyah-1.0-pro. openai provider implemented but unverified (no key). | Revolab done. The openai-unverified caveat stays open. |
| 4 | Record: series support (series.yaml fragment + episodes, deep merge episode-wins, merge-then-validate, batch in name order stopping at first failure, init-series, meta.series/episode schema fields). Inheritance proven by a negative test. | Executed (b340fee). Closed by seq 6. |
| 5 | TODO: background theme catalog duplicated per vendor (remotion + hyperframes copies). Move to one shared location all vendors reference, delete the copies. Same policy for future shared vendor assets. | Recorded in 10748ba, the commit whose hyperframes vendor created the duplicate catalog copy. Executed in the structure review (5ecfebc): single catalog at `assets/backgrounds/`. Closed by seq 6. |
| 6 | Closure: directives 0-5 all executed and verified. Known-open at closure: openai provider unverified against the live API (no key), mascot emotion art, hyperframes se/image-visual support, studio theme contrast. | Of the four open items: emotion art (5c324d4) came after closure, hyperframes se/image visuals shipped in the same commit as the closure entry (19c4cfd) while still listed as open, and no later entry records studio contrast as resolved (studio.png was regenerated in 19c4cfd). openai remains unverified. |

Open items as of the last ledger entry: the openai TTS provider has never
been run against the live API, and studio theme contrast has no recorded
resolution.

## The three-model design consult (season s1, before schema freeze)

Prompt: `prompts/base/design-brief.md`. Four questions, 120-word answers:
canonical shared schema vs per-vendor YAML, no-TTS timing fallback and
its pitfalls, what breaks with a second engine and what vendor AGENTS.md
must pin, single-file vs split YAML. Records in `.rumpun/runs/`:
`codex-review.md`, `codex-review-2.md`, `glm-review.md`,
`design-brief.md`, consolidated in `design-decisions.md`.

### What each model said

- codex (gpt-5.5, round 1): answered in question-protocol form and asked
  the one meta-question: "Do you want project.yaml to be stable across
  engines, even when a vendor loses features?" The operator's directive
  said no questions, so the session answered yes. That answer is decision
  1: canonical YAML is the stable contract. Round 2 was requested and
  returned empty output (`codex-review-2.md` contains only the stdin
  notice). No third round was attempted.
- glm-5.3 (full written review): canonical schema + per-vendor mapping -
  per-vendor YAML forks N templates x M engines that diverge quietly;
  canonical gives one validation point and vendor switch = change
  `meta.vendor`; `vendor: {}` keys that alter timing should be rejected
  at validation. Estimate fallback: character count / per-language rate
  plus punctuation pauses with a floor, and the pitfalls: never mix
  timing sources in one timeline, per-language rates stay rough, the
  quiet fallback is the worst error so tag every duration with its
  source, cache real durations keyed by hash(text, speaker_id). Second
  engine breaks: units (frames vs seconds), position must be an enum,
  visuals need a small canonical vocabulary, typography must be pinned.
  Vendor AGENTS.md must pin six things: input, timing, voice,
  capabilities (unsupported features error, never drop), output (mp4,
  exit codes, idempotent re-run), environment. Single file over split:
  one YAML, one validate, one diff; overlays merged by ce.py if a
  project ever outgrows one file.
- fable (full repo knowledge): estimate fallback details (per-project
  chars-per-second, minimum frame floor, silent placeholder wavs so the
  engine's Audio elements resolve), `flip_x` as a canonical character
  key so art orientation ports, and a minimal-diff upstream port with
  characters injected as a generated CHARACTERS export.

### Adopted (10 decisions in `runs/design-decisions.md`)

1. Canonical schema, per-vendor mapping (codex meta-answer, glm
   concurred).
2. Canonical timing unit: seconds, vendors convert to frames (glm).
3. Unknown keys error, never dropped silently (glm).
4. No mixing timing sources in one timeline (glm).
5. Duration source labeled in every build log (glm).
6. Position is an enum left|right (glm).
7. Small visual vocabulary with a fixed animation set (glm).
8. Estimate fallback: per-project cps, min frame floor, silent
   placeholder wavs (fable).
9. `flip_x` canonical character key (fable).
10. Engine port keeps upstream code minimal-diff, data-driven characters
    via generated export (fable).

All 10 were adopted; nothing from the consult was declined. The
decisions are visible in the shipped schema (seconds timing, unknown-key
errors, position enum, `vendor: {}` gate) and in the build-log source
labeling.

## The structure review (GLM 5.3 x fable, commit 5ecfebc)

Trigger: `runs/structure-brief.md` (fable-authored) with six known
concerns: background catalog duplicated per vendor, root AGENTS.md
mixing routing with deep contracts (119 lines), no preflight command
(onboarding by schema error), estimate/timeline math in three places
with the linter still carrying a fallback formula, engine/ keeping
upstream sample configs that could drift, and workdir artifacts
leaking into commits twice.

### What each reviewer recommended

GLM (`runs/glm-structure-review.md`) named the root anti-pattern:
canonical things COPIED instead of REFERENCED (catalogs, vendor
contracts, timeline math, engine configs each exist twice). Six moves:
delete both vendor catalog copies into one `assets/backgrounds/`, cut
root AGENTS.md to a ~40-line router with deep rules in
`docs/project-yaml.md` + `docs/vendor-contract.md`, trim vendor manuals
to deltas, delete the linter fallback formula (timeline.json required),
delete engine/ sample configs, one shared `work/` root. It also designed
`ce.py check`: cheap blockers first then guidance, imperative wording
with zero schema vocabulary, exit 0 clean / 1 blockers / 2 notes only,
`--json` for agents. Layering principle: prose that must be read to
prevent a violation is a defect, move that rule into ce.py.

fable (`runs/fable-structure-review.md`, written pre-GLM): keep the
vendor contract (`AGENTS.md` + `build.sh` + mapper - two vendors
onboarded with zero ce.py changes), keep the output-truth guards
(timeline.json + duration guard + visibility lint), keep format-named
templates. Restructure lean on the same four points (router AGENTS.md,
shared catalog, single source for engine configs, delete the fallback
formula). Add `ce.py check` as the guidance layer: plain-language FILL
report plus environment state, ending in a READY / NOT READY verdict,
while `validate` stays the strict gate.

### Adopted (recorded in `runs/structure-decisions.md`)

1. One background catalog at `assets/backgrounds/`, vendor copies
   deleted, both mappers resolve it relative to their workdir.
2. Root AGENTS.md becomes a ~40-line router; deep rules move to
   `docs/vendor-contract.md` and `docs/project-yaml.md`.
3. Vendor AGENTS.md files keep engine deltas only and point at
   `docs/vendor-contract.md`.
4. Linter requires timeline.json; the fallback formula is deleted and a
   missing timeline fails the lint with a clear message.
5. `ce.py check` gains GLM's exit scheme (0 clean, 1 blockers, 2 notes
   only) and `--json`; the agent workflow now runs check before render
   and relays FILL items in plain words.

### Declined, with recorded reasons (to prevent relitigating)

- Single `work/` root for all vendors: churn, no agent benefit; the
  per-vendor ignore rules (`vendors/*/.work/`) were already proven
  across re-renders.
- Deleting `engine/` config samples: map-project writes configs into
  disposable workdirs, so they cannot drift into builds; they serve
  standalone engine use only.

Implementation sequence, as recorded: catalog dedupe -> linter fallback
removal -> docs split -> check exit codes and `--json` -> full re-render
sweep (est-demo, dialog-ms, hf-demo) -> commit and push.

## Bug classes found, fixed, and what each taught

- Unclosed terminal window div (7a59c6b). The rewritten tutorial
  terminal block never closed its window div, so every clip after the
  first terminal step nested inside that overflow:hidden window and was
  clipped out of view: the video showed content only for the first two
  lines, while the duration guard stayed green. One closing tag fixed
  it. Taught: generated markup needs a structural check (div balance
  must equal 0, now run on every render), and a green timing guard does
  not mean a correct video.
- Visibility-lint parity bug (0b96a81). The v1 character check compared
  a line-mid frame against the tail frame, but the 0.2s lip flap put
  both frames on the same flap state for about half of all lines, so
  the check failed on luck. Rewritten: character presence is measured
  against the theme PNG scaled to the render (present character samples
  ~2490 px, empty corner ~0, threshold charH^2/60, measured on live
  frames); flap animation became an informational delta, not a gate;
  frame extraction is clamped inside the render duration. Taught:
  animation makes frame-vs-frame comparison nondeterministic, diff
  against ground truth instead.
- Timeline drift on estimate renders (a097776, completed in 5ecfebc).
  The lint recomputed per-line windows from the YAML formula, but
  estimate renders quantize frames, so windows drifted past the render
  end and later lines probed tail-only frames. Fix: vendors emit
  timeline.json with the renderer's own math, build.sh ships it next to
  video.mp4, the linter consumes it, then the fallback formula was
  deleted outright so a missing timeline is a hard lint error. Taught:
  never let the checker recompute what the renderer already computed.
- Empty tail / playback-rate mismatch (118fa17, guarded by 859f006).
  Inherited from upstream: Root.tsx summed raw durationInFrames +
  pauseAfter while playback ran each line at ceil(frames/playbackRate),
  so rate 1.2 produced a composition ~17% longer than the timeline
  (3.7s empty chalkboard). Fixed by summing per-line adjusted frames
  plus one closing buffer, then made a class-level guarantee by the
  duration guard (expected-seconds.txt vs ffprobe, 0.5s tolerance).
  Taught: the inherited bug became a permanent guard, so a repeat is a
  loud build error rather than a quiet artifact.
- Pre-rename stale path in the art generator (9155a65). The Wayang
  rename deliberately kept absolute local paths inside the art
  generators, so `generate_mascots.py` still deployed into the
  pre-rename `content_engine` tree until the Rimau commit fixed its
  deploy root. Note: this class is not fully dead -
  `assets/background/generate_background.py` and `generate_themes.py`
  still write to `/mnt/data/work/content_engine/...` paths today.
  Taught: absolute paths survive renames and resurface the next time
  the generator runs.
- Latin subtitles under a Japanese wrapper (dede006). BudouX-JA emitted
  near-whole-line segments for Latin text and the nowrap spans
  overflowed the centered container. Taught: upstream text-shaping
  assumptions are language-specific; wrap logic now branches by script.
- Vendor-side capability gating (c64a503). The remotion mapper gated
  voices on voicevox, blocking revolab/openai projects. Taught:
  validation is the platform's job; vendors consume, they do not gate.
- Workdir and state leaks (e38feb6, 477ff3f, 3690719, b264afe). A .pyc,
  .omc session state (root and nested under assets/mascots), and the
  whole hyperframes .work/ tree were committed when shells ran from the
  wrong cwd. Each was purged and its ignore rule widened. Recorded in
  the structure brief as "leaked twice". Taught: ignore rules are
  reactive, absolute paths and cwd discipline are the fix.

## Rename history

- Commit 848d28e (2026-09-26 20:28): "The platform has a name: Wayang,
  after the shadow play - flat puppet characters performing your script
  on a stage."
- GitHub repo renamed khursani8/content_engine -> khursani8/wayang;
  remote is now `https://github.com/khursani8/wayang.git` (old GitHub
  URLs redirect).
- CLI renamed `tools/ce.py` -> `tools/wayang.py` (git recorded a 98%
  similarity rename, prog wayang).
- Sweep: README, agent manual, docs, vendor manuals, engine configs,
  npm package names, schema title, map-project references - 20 files,
  48 insertions, 48 deletions.
- Absolute local paths inside the art generators were intentionally
  kept at rename time. The mascot generator was fixed one commit cycle
  later (9155a65); the background generators still carry
  `/mnt/data/work/content_engine` paths (see bug classes).
- The local working folder kept the name `/mnt/data/work/content_engine`
  until the operator asked, then moved to `/mnt/data/work/wayang`, with
  the Claude history namespace migrated by copy + symlink.
- Commit e247071 removed the upstream repo reference
  (nyanko3141592/remotion-voicevox-template) from `rumpun.yaml` and
  `vendors/remotion/AGENTS.md`. Old commit messages still name the
  upstream repo; scrubbing history would need git filter-repo plus a
  force push and was recorded as done-only-on-explicit-request.

## What is deliberately not in git

Current `.gitignore`: `node_modules/`, `vendors/*/.work/`, `projects/`,
`out/`, `*.log`, `.rumpun/runs/`, `.rumpun/seasons/_steady-state*`,
`.rumpun/seasons/_competition.yaml`, `__pycache__/`, `*.pyc`, `.omc/`.

| excluded | why it matters |
|---|---|
| `node_modules/` | Installed deps, reproducible from package.json; README pins the one manual step (`npm install` in `vendors/remotion/engine`). |
| `vendors/*/.work/` | Disposable per-vendor build workdirs: generated HTML, fonts, wavs, out.mp4. Committed by accident twice (10748ba, 1932e7c) when shells ran from the wrong cwd, purged in b264afe. |
| `projects/` | User content: each project's filled project.yaml, generated `voices/`, and `out/video.mp4`. Personal renders do not belong in the platform repo. (`projects/video-tutorial/` exists on disk, untracked.) |
| `out/` | Render outputs. |
| `.rumpun/runs/` | Per-season workspaces: the raw model outputs (codex/glm/fable reviews, briefs, decision drafts). Kept on disk only. The committed record of decisions lives in the ledger and commit messages. Anyone cloning the repo does not get the raw reviews. |
| `.rumpun/seasons/_steady-state*`, `_competition.yaml` | Untracked season templates and drafts: a steady-state season shape (three light lanes: lint sweep, route probes, rehearsals) and a Kaggle-competition season shape. Fill-in drafts, not campaign history. |
| `__pycache__/`, `*.pyc` | Build artifacts; one leaked in 2fd0e74, removed in e38feb6. |
| `.omc/` | Claude session state (hud caches, mission state, subagent tracking). Committed from dafeabf onward, untracked in 3690719 + 477ff3f. |

Contrast: `.rumpun/` minus those paths is committed on purpose -
`.rumpun/README.md` states that git history over it is the evolution
ledger, unlike disposable caches.

## Open questions you might ask

- Why does the ledger keep every directive at status `pending`, and is
  a closure pass (or a status convention change) planned, or is
  append-only-as-historical the permanent answer?
- The openai TTS provider has never touched the live API. Verify it
  with a key, or cut it from the schema until one exists?
- Directive 6 lists studio theme contrast as open, and 19c4cfd
  regenerated studio.png. Was contrast the reason, and is the item
  actually closed?
- `assets/background/generate_background.py` and `generate_themes.py`
  still write into the pre-rename `/mnt/data/work/content_engine` tree.
  Fix the paths, or accept it since regeneration is rare?
- The design consult gave fable full repo knowledge while codex and glm
  got none. Was the asymmetry deliberate (local model vs remote
  quota), and did it skew which recommendations won?
- Codex round 2 returned empty output and no third round was attempted.
  Was the meta-question answer from round 1 considered sufficient, or
  was codex effectively dropped from the consult?
- Autonomy stage is still `manual` with `promote_after: 5 clean audits`
  and the campaign cost cap is 600. Was any spend tracked against that
  cap, and is a season s2 planned or is the campaign closed?
- Old commit messages still name the upstream template repo. Is a
  `git filter-repo` history scrub planned, or does the redirect-plus-
  current-files state stand?

hook: PostToolUse
hook: PostToolUse Completed
codex
The vendor boundary supports expansion. Shared checks and duplicated mascot assets create the main scaling risks. I’ll inspect those paths.

hook: PreToolUse
hook: PreToolUse
hook: PreToolUse
hook: PreToolUse Completed
hook: PreToolUse Completed
hook: PreToolUse Completed
exec
/usr/bin/zsh -lc "rg -n '"'^def |theme_dir|catalog|language.*ja|timeline|EXPECTED|expected-seconds|TEMPLATE_NAMES|content_engine|ROOT ='"' tools/wayang.py vendors/*/build.sh assets/background/*.py assets/mascots/generate_mascots.py" in /mnt/data/work/wayang
 succeeded in 0ms:
assets/mascots/generate_mascots.py:27:ART_ROOT = Path("/mnt/data/work/wayang")
assets/mascots/generate_mascots.py:29:TEMPLATE_NAMES = ("dialog", "presentation", "storytelling", "community")
assets/mascots/generate_mascots.py:56:def svg_wrap(body: str, bg: str | None) -> str:
assets/mascots/generate_mascots.py:68:def momo_mouth_open() -> str:
assets/mascots/generate_mascots.py:82:def momo_mouth_close() -> str:
assets/mascots/generate_mascots.py:89:def momo_eyes_default() -> str:
assets/mascots/generate_mascots.py:102:def momo_body(mouth: str, eyes: str | None = None) -> str:
assets/mascots/generate_mascots.py:153:def kiki_beak_lower(dx: int = 0, dy: int = 0) -> str:
assets/mascots/generate_mascots.py:162:def kiki_beak_upper() -> str:
assets/mascots/generate_mascots.py:172:def kiki_mouth_open() -> str:
assets/mascots/generate_mascots.py:186:def kiki_mouth_close() -> str:
assets/mascots/generate_mascots.py:195:def kiki_eyes_base() -> str:
assets/mascots/generate_mascots.py:208:def kiki_eyes_default() -> str:
assets/mascots/generate_mascots.py:216:def kiki_body(mouth: str, eyes: str | None = None) -> str:
assets/mascots/generate_mascots.py:261:def rimau_mouth_open() -> str:
assets/mascots/generate_mascots.py:276:def rimau_mouth_close() -> str:
assets/mascots/generate_mascots.py:283:def rimau_body(mouth: str, eyes: str | None = None) -> str:
assets/mascots/generate_mascots.py:359:def _brow(d: str) -> str:
assets/mascots/generate_mascots.py:363:def _arc(d: str) -> str:
assets/mascots/generate_mascots.py:367:def momo_eyes_happy() -> str:
assets/mascots/generate_mascots.py:371:def momo_eyes_surprised() -> str:
assets/mascots/generate_mascots.py:379:def momo_eyes_thinking() -> str:
assets/mascots/generate_mascots.py:394:def momo_eyes_sad() -> str:
assets/mascots/generate_mascots.py:402:def momo_happy_open() -> str:
assets/mascots/generate_mascots.py:415:def momo_happy_close() -> str:
assets/mascots/generate_mascots.py:422:def momo_surprised_open() -> str:
assets/mascots/generate_mascots.py:433:def momo_surprised_close() -> str:
assets/mascots/generate_mascots.py:440:def momo_thinking_open() -> str:
assets/mascots/generate_mascots.py:447:def momo_thinking_close() -> str:
assets/mascots/generate_mascots.py:451:def momo_sad_open() -> str:
assets/mascots/generate_mascots.py:458:def momo_sad_close() -> str:
assets/mascots/generate_mascots.py:462:def kiki_eyes_happy() -> str:
assets/mascots/generate_mascots.py:466:def kiki_eyes_surprised() -> str:
assets/mascots/generate_mascots.py:474:def kiki_eyes_thinking() -> str:
assets/mascots/generate_mascots.py:489:def kiki_eyes_sad() -> str:
assets/mascots/generate_mascots.py:497:def kiki_surprised_open() -> str:
assets/mascots/generate_mascots.py:509:def kiki_surprised_close() -> str:
assets/mascots/generate_mascots.py:518:def kiki_thinking_open() -> str:
assets/mascots/generate_mascots.py:527:def kiki_thinking_close() -> str:
assets/mascots/generate_mascots.py:536:def kiki_sad_open() -> str:
assets/mascots/generate_mascots.py:545:def kiki_sad_close() -> str:
assets/mascots/generate_mascots.py:554:def rimau_happy_open() -> str:
assets/mascots/generate_mascots.py:567:def rimau_happy_close() -> str:
assets/mascots/generate_mascots.py:574:def rimau_surprised_open() -> str:
assets/mascots/generate_mascots.py:585:def rimau_surprised_close() -> str:
assets/mascots/generate_mascots.py:592:def rimau_thinking_open() -> str:
assets/mascots/generate_mascots.py:599:def rimau_thinking_close() -> str:
assets/mascots/generate_mascots.py:603:def rimau_sad_open() -> str:
assets/mascots/generate_mascots.py:610:def rimau_sad_close() -> str:
assets/mascots/generate_mascots.py:654:def emotion_body(character: str, emotion: str, state: str) -> str:
assets/mascots/generate_mascots.py:662:def check_frame(path: Path) -> None:
assets/mascots/generate_mascots.py:675:def generate_emotions() -> None:
assets/mascots/generate_mascots.py:705:def deploy_emotions() -> None:
assets/mascots/generate_mascots.py:706:    roots = [ART_ROOT / "templates" / name / "assets" / "images" for name in TEMPLATE_NAMES]
assets/mascots/generate_mascots.py:735:def generate_rimau() -> None:
assets/mascots/generate_mascots.py:779:def deploy_rimau() -> None:
assets/mascots/generate_mascots.py:787:def render(svg_str: str, path: Path) -> None:
assets/mascots/generate_mascots.py:805:def verify_pair(open_png: Path, close_png: Path, box: tuple[int, int, int, int], name: str) -> None:
assets/mascots/generate_mascots.py:840:def check_character_presentation(
assets/mascots/generate_mascots.py:899:def check_presentation() -> None:
assets/mascots/generate_mascots.py:910:def main() -> None:
vendors/remotion/build.sh:2:# content_engine vendor entry. Contract: build.sh PROJECT_DIR OUT_DIR
vendors/remotion/build.sh:45:# timeline (Root.tsx contract). Tolerance 0.5s covers container rounding.
vendors/remotion/build.sh:46:EXPECTED="$(cat "$WORK/expected-seconds.txt" 2>/dev/null || true)"
vendors/remotion/build.sh:47:if [ -n "$EXPECTED" ]; then
vendors/remotion/build.sh:50:    echo "[remotion-vendor] duration check: actual=${ACTUAL}s expected=${EXPECTED}s"
vendors/remotion/build.sh:51:    ok="$(awk -v a="$ACTUAL" -v e="$EXPECTED" 'BEGIN { print (a >= e - 0.5 && a <= e + 0.5) ? 1 : 0 }')"
vendors/remotion/build.sh:53:      echo "[remotion-vendor] ERROR: rendered duration deviates from the computed timeline (empty-tail bug class)" >&2
vendors/remotion/build.sh:61:cp "$WORK/timeline.json" "$OUT_DIR/timeline.json"
vendors/hyperframes/build.sh:2:# content_engine vendor entry. Contract: build.sh PROJECT_DIR OUT_DIR
vendors/hyperframes/build.sh:29:# expected-seconds.txt + background/voices/images copies)
vendors/hyperframes/build.sh:37:# timeline. Tolerance 0.5s covers container rounding.
vendors/hyperframes/build.sh:38:EXPECTED="$(cat "$WORK/expected-seconds.txt" 2>/dev/null || true)"
vendors/hyperframes/build.sh:39:if [ -n "$EXPECTED" ]; then
vendors/hyperframes/build.sh:42:    echo "[hyperframes-vendor] duration check: actual=${ACTUAL}s expected=${EXPECTED}s"
vendors/hyperframes/build.sh:43:    ok="$(awk -v a="$ACTUAL" -v e="$EXPECTED" 'BEGIN { print (a >= e - 0.5 && a <= e + 0.5) ? 1 : 0 }')"
vendors/hyperframes/build.sh:45:      echo "[hyperframes-vendor] ERROR: rendered duration deviates from the computed timeline" >&2
vendors/hyperframes/build.sh:53:cp "$WORK/timeline.json" "$OUT_DIR/timeline.json"
tools/wayang.py:19:def deep_merge(base: dict, overlay: dict) -> dict:
tools/wayang.py:30:def find_series_file(pdir: Path):
tools/wayang.py:38:def is_series_dir(pdir: Path) -> bool:
tools/wayang.py:42:def series_episodes(sdir: Path) -> list:
tools/wayang.py:48:ROOT = Path(__file__).resolve().parent.parent
tools/wayang.py:53:def fail(msg: str):
tools/wayang.py:58:def resolve_project(value: str) -> Path:
tools/wayang.py:70:def cmd_templates(args):
tools/wayang.py:76:def cmd_init(args):
tools/wayang.py:95:def cmd_init_series(args):
tools/wayang.py:109:            "language": template["meta"].get("language", "ja"),
tools/wayang.py:135:def load_project(pdir: Path) -> dict:
tools/wayang.py:159:def validate_project(pdir: Path) -> dict:
tools/wayang.py:196:def run_tts(pdir: Path, data: dict, force: bool = False) -> None:
tools/wayang.py:250:def cmd_tts(args):
tools/wayang.py:258:def cmd_validate(args):
tools/wayang.py:275:def _ffprobe_json(mp4: Path) -> dict:
tools/wayang.py:284:def _ffmpeg_frame(mp4: Path, t: float, total: float, out: Path) -> bool:
tools/wayang.py:294:def _ffmpeg_volume(mp4: Path, start: float, dur: float) -> float:
tools/wayang.py:306:def _band_diff_count(a_img, b_img, box) -> int:
tools/wayang.py:324:def lint_project(pdir: Path, mp4: Path, data: dict) -> bool:
tools/wayang.py:361:    tl_path = mp4.parent / "timeline.json"
tools/wayang.py:371:            log.info("lint: using vendor timeline.json (%d lines)", len(windows))
tools/wayang.py:373:        log.error("visibility lint: %s missing - the vendor must emit the timeline it renders", tl_path)
tools/wayang.py:389:            log.error("visibility: line %s frame missing - render is shorter than the computed timeline", line["id"])
tools/wayang.py:440:def cmd_check(args):
tools/wayang.py:490:        catalog_dir = ROOT / "vendors" / vendor / "assets" / "backgrounds"
tools/wayang.py:491:        if catalog_dir.is_dir():
tools/wayang.py:492:            catalog = sorted(p.stem for p in catalog_dir.glob("*.png"))
tools/wayang.py:493:            if settings["background"] not in catalog:
tools/wayang.py:494:                issues.append(f"settings.background '{settings['background']}' is not a theme here (available: {', '.join(catalog)})")
tools/wayang.py:518:def cmd_lint(args):
tools/wayang.py:527:def render_one(pdir: Path, skip_lint: bool = False) -> None:
tools/wayang.py:551:def cmd_render(args):
tools/wayang.py:562:def main():
assets/background/generate_themes.py:14:OUT = Path("/mnt/data/work/content_engine/assets/backgrounds")
assets/background/generate_themes.py:21:def save(name: str, svg: str, checks: list) -> None:
assets/background/generate_themes.py:48:def svg_wrap(body: str, defs: str = "") -> str:
assets/background/generate_themes.py:55:def whiteboard():
assets/background/generate_themes.py:64:def night_sky():
assets/background/generate_themes.py:79:def kraft_paper():
assets/background/generate_themes.py:90:def batik():
assets/background/generate_themes.py:107:def notebook():
assets/background/generate_themes.py:116:def sunrise():
assets/background/generate_themes.py:129:def studio():
assets/background/generate_themes.py:151:def riverbank():
assets/background/generate_themes.py:166:def slate():
assets/background/generate_themes.py:179:def wood_table():
assets/background/generate_themes.py:191:def main() -> None:
assets/background/generate_background.py:16:OUT = Path("/mnt/data/work/content_engine/vendors/remotion/engine/public/background.png")
assets/background/generate_background.py:51:def build_svg() -> str:
assets/background/generate_background.py:84:def render(svg_str: str, path: Path) -> None:
assets/background/generate_background.py:98:def check(path: Path) -> None:
assets/background/generate_background.py:122:def main() -> None:

exec
/usr/bin/zsh -lc 'cat /home/sani/.codex/skills/dts/references/check.md
cat /home/sani/.codex/skills/dts/references/grammar.md' in /mnt/data/work/wayang
 succeeded in 0ms:
<!-- dts:no-lint -->

# DTS self-audit

Run these before delivering any persisted text. `$F` is the target file.

## Grep patterns

```sh
# Perfect tense and passive scaffolding
grep -nEi '\b(has|have|had) been\b|\bis to be\b|\bwas being\b' "$F"

# Banned modals
grep -nEi '\b(should|would|may|might|could|shall)\b' "$F"

# Kill-list
grep -nEi '\b(simply|easily|seamless(ly)?|robust|powerful|comprehensive|elegant|crucial|vital|essential|leverage|utiliz(e|es|ing)|delve|unlock|empower|streamline|holistic)\b' "$F"

# Dead phrases
grep -nEi 'worth noting|important to note|keep in mind|that said|at the end of the day|as you can see|I hope this helps|great question' "$F"

# Wordy connectives
grep -nEi '\bin order to\b|\bprior to\b|\bdue to the fact\b|\bat this point in time\b|\bis able to\b|\bhas the ability to\b' "$F"

# Semicolons
grep -n ';' "$F"

# Hedge stacks (two qualifiers in one clause)
grep -nEi '(might|may|could|appears?|seems?)[^.]{0,30}(possibly|potentially|perhaps|likely)' "$F"
```

## Sentence-length check

Flags every sentence over the cap. Skips fenced code blocks and table rows.

````sh
awk 'NR==1&&/^---$/{f=1;next} f&&/^---$/{f=0;next} f{next}
/^```/{c=!c;next} c||/^\|/||/^ *$/{next}
{gsub(/`[^`]*`/,"X"); n=split($0,s,/[.!?]+[ \t]|[.!?]+$/);
 for(i=1;i<=n;i++){w=split(s[i],t," "); if(w>20) printf "%s:%d: %d words: %s\n",FILENAME,NR,w,s[i]}}' "$F"
````

Change `w>20` to `w>15` when auditing directives, subagent prompts, or CLI help.

## Pass condition

Every hit is fixed or is a deliberate quotation of external text. Quoted error strings, code identifiers, and cited source material are exempt — DTS never rewrites a verbatim span.
<!-- dts:no-lint -->

# DTS grammar

## Sentence caps

| Text type             | Ceiling  | Form                   |
| --------------------- | -------- | ---------------------- |
| Directive (do this)   | 15 words | Command form           |
| Descriptive (this is) | 20 words | Simple present or past |

These are ceilings, never targets. Shorter is always better.

A thought that exceeds the ceiling becomes two sentences. It never becomes a truncated sentence.

Code spans in backticks, paths, hyphenated terms, and numbers with units each count as one word.

## Rules

0. **Compression removes filler, never content.** Every fact the reader needs to act survives. When keeping a fact costs another sentence, write the sentence. Being complete is never a reason to hedge: state an uncertain fact as unconfirmed, never as `may`.
1. **One idea per sentence.** Two ideas means two sentences.
2. **Answer first.** Conclusion in sentence one. Reasons come after.
3. **Condition before command.** Write `If the build fails, run cargo clean.` Never `Run cargo clean if the build fails.`
4. **Name who does the thing.** `The parser rejects null.` Not `Null is rejected.`
5. **Plain present tense.** No `has been`, `have been`, `was being`, `is to be`.
6. **Modals: `can`, `will`, `must`.** Never `should`, `would`, `may`, `might`, `could`. A rule becomes `must`. A capability becomes `can`. A suggestion becomes a plain statement of fact.
7. **No semicolons.** Write two sentences.
8. **No `-ing` chains.** `...ran the test, causing a panic` becomes two sentences.
9. **Noun clusters: three words maximum.** Break longer ones with `of` or a verb.
10. **Bullets and tables for enumerations.** A prose sentence listing four things is four bullets. Stop a list when the next row adds nothing the reader will act on. Never pad to look thorough, never truncate mid-row. Open each item with the thing it names, never with one verb repeated down the list.
11. **One word, one meaning.** Reuse the exact term for a concept across the whole document. Synonym rotation forces the reader to re-derive the mapping.
12. **Prefer the plain word.** Keep a technical term when it is exact and the reader already uses it. `mutex` stays. `orthogonal` becomes `unrelated`. A word chosen to sound expert costs the reader and buys nothing.
13. **Say it straight.** No analogy, no clever one-liner, no `not X, but Y`. An inverted sentence reads as insight and costs the reader a second pass.
14. **Verbatim technical spans.** Code, paths, commands, flags, identifiers, error strings, product and API names, UI labels: character-exact. A rule never rewrites one of these.

## Locked action verbs

One verb per action, everywhere. No synonyms.

| Verb     | Meaning                               |
| -------- | ------------------------------------- |
| `Fetch`  | Retrieve data across a network or API |
| `Read`   | Read a local file from disk           |
| `Modify` | Edit existing code, config, or docs   |
| `Create` | Make a new file, resource, or entity  |
| `Remove` | Delete an existing file or entity     |
| `Run`    | Execute a command or test             |

## What DTS rejects from ASD-STE100

These STE rules inflate tokens and are **not** part of DTS:

- The ~900-word approved dictionary. Software vocabulary is legal.
- Verb-to-noun expansion (`check` → `do a check of`). Direct verbs stay.
- `ensure` → `make sure that`. `ensure` stays.
- The contraction ban. Contractions are legal and cheaper.
- `e.g.` → `for example`, `i.e.` → `that is`. The abbreviations stay.
- Mandatory restoration of every article and `that` clause.

hook: PostToolUse
hook: PostToolUse
exec
/usr/bin/zsh -lc "git status --short
rg --files tools schema templates vendors assets -g AGENTS.md -g '*.py' -g '*schema*' -g '*template*'
sed -n '1,170p' tools/wayang.py" in /mnt/data/work/wayang
 succeeded in 0ms:
 M .rumpun/ledger/directives.jsonl
?? REPO_ANALYSIS/
tools/tts_providers.py
tools/wayang.py
tools/artifact_check.py
vendors/hyperframes/AGENTS.md
vendors/remotion/AGENTS.md
schema/project.schema.json
templates/tutorial/template.yaml
templates/presentation/template.yaml
templates/community/template.yaml
templates/storytelling/template.yaml
assets/mascots/generate_mascots.py
templates/dialog/template.yaml
assets/background/generate_themes.py
assets/background/generate_background.py
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "jsonschema>=4.20", "pillow>=10.0"]
# ///
"""Wayang CLI: templates, init, validate, render."""
import argparse
import json
import logging
import shutil
import subprocess
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from tts_providers import PROVIDERS, ProviderError, line_hash, wav_seconds


def deep_merge(base: dict, overlay: dict) -> dict:
    """Overlay wins per key; dicts recurse; lists and scalars replace."""
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def find_series_file(pdir: Path):
    """Nearest series.yaml above an episode dir (up to two levels)."""
    for cand in (pdir.parent / "series.yaml", pdir.parent.parent / "series.yaml"):
        if cand.is_file():
            return cand
    return None


def is_series_dir(pdir: Path) -> bool:
    return (pdir / "series.yaml").is_file() or (pdir / "episodes").is_dir()


def series_episodes(sdir: Path) -> list:
    epi = sdir / "episodes"
    if not epi.is_dir():
        return []
    return sorted(d for d in epi.iterdir() if (d / "project.yaml").is_file())

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "project.schema.json"
log = logging.getLogger("ce")


def fail(msg: str):
    log.error(msg)
    raise SystemExit(1)


def resolve_project(value: str) -> Path:
    """Accept either a bare name under projects/ or a path relative to ROOT."""
    as_given = ROOT / value
    under_projects = ROOT / "projects" / value
    if as_given.is_dir():
        return as_given
    if under_projects.is_dir():
        return under_projects
    fail(f"project not found: {value} (looked at {as_given} and {under_projects})")
    raise AssertionError  # unreachable


def cmd_templates(args):
    for d in sorted((ROOT / "templates").iterdir()):
        if (d / "template.yaml").is_file():
            log.info(d.name)


def cmd_init(args):
    name = args.name
    name = name.removeprefix("projects/")
    src = ROOT / "templates" / args.template
    if not (src / "template.yaml").is_file():
        fail(f"unknown template: {args.template}")
    dst = ROOT / "projects" / args.name
    if dst.exists():
        fail(f"projects/{args.name} already exists")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    (dst / "template.yaml").rename(dst / "project.yaml")
    log.info(
        "created projects/%s - edit project.yaml, then: uv run tools/wayang.py validate projects/%s",
        args.name,
        args.name,
    )


def cmd_init_series(args):
    src = ROOT / "templates" / args.template
    if not (src / "template.yaml").is_file():
        fail(f"unknown template: {args.template}")
    sdir = ROOT / "projects" / args.name
    if sdir.exists():
        fail(f"projects/{args.name} already exists")
    template = yaml.safe_load((src / "template.yaml").read_text(encoding="utf-8"))
    (sdir / "episodes").mkdir(parents=True)
    series = {
        "meta": {
            "title": template["meta"]["title"],
            "template": args.template,
            "vendor": template["meta"]["vendor"],
            "language": template["meta"].get("language", "ja"),
            "description": f"shared base for the {args.name} series; episodes inherit and override",
        },
        "characters": template.get("characters", {}),
        "settings": template.get("settings", {}),
    }
    header = (
        "# series.yaml - shared base for every episode in this series.\n"
        "# Episodes deep-merge this under their own project.yaml:\n"
        "# episode values win per key, dicts merge, lists (script) are episode-only.\n"
        "# This file is a fragment: it is never validated on its own.\n"
    )
    (sdir / "series.yaml").write_text(
        header + yaml.safe_dump(series, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    ep_dir = sdir / "episodes" / args.first_episode
    shutil.copytree(src, ep_dir)
    (ep_dir / "template.yaml").rename(ep_dir / "project.yaml")
    log.info(
        "series projects/%s: series.yaml + episodes/%s (add more: wayang.py init %s <series>/episodes/<ep>)",
        args.name,
        args.first_episode,
        args.template,
    )


def load_project(pdir: Path) -> dict:
    pf = pdir / "project.yaml"
    if not pf.is_file():
        fail(f"{pf} missing")
    try:
        data = yaml.safe_load(pf.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        fail(f"project.yaml parse error: {e}")
    if not isinstance(data, dict):
        fail("project.yaml must be a mapping")
    series_file = find_series_file(pdir)
    if series_file is not None:
        try:
            series = yaml.safe_load(series_file.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            fail(f"series config parse error ({series_file}): {e}")
        if not isinstance(series, dict):
            fail(f"series config must be a mapping: {series_file}")
        shared = len((series.get("characters") or {}).keys())
        data = deep_merge(series, data)
        log.info("merged series config %s (%d shared character(s))", series_file, shared)
    return data


def validate_project(pdir: Path) -> dict:
    data = load_project(pdir)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(data),
        key=lambda e: list(e.absolute_path),
    )
    if errors:
        for e in errors:
            where = ".".join(str(p) for p in e.absolute_path) or "<root>"
            log.error("schema: %s: %s", where, e.message)
        raise SystemExit(1)

hook: PostToolUse Completed
hook: PostToolUse Completed
hook: PostToolUse
hook: PostToolUse Completed
hook: PreToolUse
hook: PreToolUse Completed
exec
/usr/bin/zsh -lc "cat tools/artifact_check.py
sed -n '440,550p' tools/wayang.py
rg -n 'artifact_check|sceneInfo|bgmConfig|content/|estimate|playbackRate|emotion' vendors/remotion/engine/src/Main.tsx vendors/remotion/scripts/map-project.mjs vendors/hyperframes/scripts/map-project.mjs" in /mnt/data/work/wayang
 succeeded in 0ms:
#!/usr/bin/env python3
"""Independent artifact check (s55 w1).

Closes audit-39's usefulness-decade-1 residual: recorded verdicts establish
what evaluators wrote; they do not independently establish implementation
correctness. This tool re-verifies a named season's landed ships from
artifacts alone:

    python tools/artifact_check.py <sid> <close-commit> [--repo REPO]
                                                   [--out-dir DIR]

1. EXTRACT   git archive the close commit into a temp tree. The live tree
   is never touched (no checkout).
2. PINS      discover the season's merged pins (tests/test_<sid>_*.py) in
   the extracted tree and run them with the repo venv's python, PYTHONPATH
   bound to the extracted src. A resolution probe first proves the import
   resolves into the extracted tree, not the live one.
3. DIGESTS   recompute every claimed pack digest in the extracted tree
   (.rumpun/plugins.yml records vs an independent sha256 over the pack's
   priors/ tree, the s47 convention: sorted pack-relative POSIX paths,
   NUL separators, no trailing separator; empty tree = sha256 of empty
   input) and the season's harvest-record seal (sha256 over the record
   body, lines[4:-1], the akar.append_record convention). plugins.yml is
   read with a minimal indentation-based parser for the yaml.safe_dump
   layout (mapping -> pack name -> scalar leaves); any other shape is a
   structural refusal naming the registry.
4. SHIPS     diff the DESIGN.md ships row for <sid> against the tree:
   split into named-ship clauses (paren-aware), extract checkable claims,
   and judge each clause:
    file claim    a <path>.<suffix> token named in the clause must exist in
   the extracted tree (resolved from the tree root, then src/rumpun/,
   tools/, tests/) -- a committed-tree claim, unless runtime-framed (see
   runtime file). The classification of every file-shaped token is
   recorded in the clause evidence.
    runtime file  a file token framed as run-time output ("writes <token>",
   a runs/<sid>/ path prefix, or a close-time cue -- "at close",
   "close-time", "on close" -- in the token's top-level segment) checks
   the campaign's live runs state instead of the extracted tree:
   repo/.rumpun/runs/<sid>/, where a runs/<sid>/-prefixed or path-shaped
   token resolves below the dir and a bare token binds at the runs root
   (the finalize's output; never scratch depth). When the runs state does
   not hold the artifact but the extracted tree does (early seasons
   committed their ledger state), the claim binds committed and the
   fallback is named in the evidence. The framing is never a bailout: a
   runtime artifact absent from the runs state and the tree DELTAs
   exactly like a missing committed file.
    key tokens    lowercase word+colon tokens ("writers:", "benih:")
   searched verbatim in the tree's src/; the status and first hit are
   recorded. A colon-form miss falls back to the bare word.
    slash tokens  path-shaped tokens without a file suffix
   ("lint/engine/evolve", "musim/"): when every component resolves to a
   module file under src/rumpun/ the clause's key tokens are searched
   inside those files; otherwise the token's last component is searched
   verbatim. When the clause carries a removal marker ("was a", "dead
   path", "found and fixed", "removed", "no longer", "retired",
   "superseded", "renamed away") the legacy token's presence is recorded
   as evidence with its locations: rename back-compat keeps legacy names by
   design, so the removal claim itself is judged by the season's pins.
   Pure-numeric slash tokens ("243/243") are metrics, not surfaces.
    pins claim    "N pins" vs the pytest collected count (binding).
    suite claim   "suite N/M" is recorded verbatim and NOT re-run (the
   season's pins are the check's execution surface; a full extracted-tree
   suite rerun is a future flag).

   close-time fallback (s59): a close's own DESIGN entry postdates the
   commit being checked (the s57 refusal fired live at the s57 close), so
   when the extracted DESIGN.md has no row for <sid> but the live worktree
   DESIGN.md has one, the checker uses the live row and records the fact
   in the check record. The fallback covers ONLY the missing fresh row:
   every other artifact (files, digests, seals) binds to the extracted
   tree exactly as before, so a tampered close still yields DELTA exit 1.

   Per-clause verdict:
    DELTA  a named committed file or runtime artifact is missing, or every
   surface token absent with no removal marker, or the pins count
   disagrees.
    MATCH  all checkable claims hold. A clause with no machine-checkable
   claims is MATCH-by-prose, recorded verbatim; it is judged by the pins.

5. RECORD    a check-<sid> ledger record (the akar.append_record layout:
   header, body, sha256 trailer over the utf-8 body bytes), written
   atomically to --out-dir (default: the live ledger .rumpun/ledger).
   Append-only: an existing check-<sid> file is refused. The record
   carries: the exact commands run, the pins outcome in the extracted
   tree, the digest comparisons, the ships-row diff (each row MATCH or
   the named delta), and the honest verdict line.

Verdict line in the record and exit code:

    VERIFIED  pins green in the extracted tree, every ships clause MATCH
   or MATCH-by-prose, every digest recomputed equal.
    DELTA     any pins failure, ships DELTA, or digest mismatch (exit 1;
   the deltas are named in the record).
    structural refusal: missing close commit, unknown season id (no ships
   row in the extracted DESIGN.md), no pins file, no tests collected, the
   import probe failing to resolve into the extracted tree, or the venv
   python absent with a fallback python that cannot import pytest (issue
   #40) -- exit 2, naming the cause.
    skip: the season ships no pins lane and the ships row claims no pins
   (a legitimate pinless close) -- exit 0 with the named skip line, no
   record; a claimed-pins season with no pins file stays a structural
   refusal (a real delta). An extract with no src/ (issue #39) takes the
   same named skip: a docs-only repo has no package for the pins lane to
   import; exit 0, no record, the line names the missing src/.

stdlib only; logging, never print; git via subprocess, archive only.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import logging
import os
import re
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
from pathlib import Path

logger = logging.getLogger("artifact_check")

PINS_TIMEOUT_S = 240
GIT_TIMEOUT_S = 30
PROBE_TIMEOUT_S = 60

FILE_TOKEN_RE = re.compile(r"(?:[\w.-]+/)*[\w.-]+\.(?:py|md|yaml|yml|jsonl|toml)\b")
KEY_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9_]*:")
SLASH_TOKEN_RE = re.compile(r"(?:[\w.-]+/)+[\w.-]*")
PINS_CLAIM_RE = re.compile(r"\b(\d+) pins\b")
SUITE_CLAIM_RE = re.compile(r"\bsuite (\d+)/(\d+)\b")
REMOVAL_MARKERS: tuple[str, ...] = (
    "was a", "dead path", "found and fixed", "removed", "no longer",
    "retired", "superseded", "renamed away",
)

CLOSE_TIME_CUE_RE = re.compile(r"\b(?:close-time|at close|on close)\b")

LIVE_ROW_NOTE = (
    "ships row read from the live worktree"
    " (the close's own entry postdates the commit)"
)

NO_DESIGN_NOTE = (
    "ships row unchecked: the extract carries no DESIGN.md"
    " convention; pins, pack digests, and seals still bind"
)

MODULE_DIR = "src/rumpun"

@dataclass
class Surface:
    """One searched token and where the search found it (or not)."""

    token: str
    present: bool
    where: str = ""


@dataclass
class FileClaim:
    """One file-shaped token: its classification and where it bound."""

    token: str
    kind: str  # "committed" | "runtime" | "runtime-committed-fallback"
    present: bool
    where: str = ""


@dataclass
class ShipClause:
    """One named-ship clause and the verdict of its claims."""

    text: str
    files: list[str] = field(default_factory=list)
    file_claims: list[FileClaim] = field(default_factory=list)
    surfaces: list[Surface] = field(default_factory=list)
    verdict: str = "MATCH"
    notes: list[str] = field(default_factory=list)


@dataclass
class CheckResult:
    """Everything the record body renders from."""

    sid: str
    commit: str
    outcome: str
    n_extracted: int = 0
    commands: list[str] = field(default_factory=list)
    pins: dict[str, str] = field(default_factory=dict)
    packs: list[tuple[str, str, str, str]] = field(default_factory=list)
    seals: list[tuple[str, str, str]] = field(default_factory=list)
    ships_verbatim: str = ""
    ships_source: str = ""
    clauses: list[ShipClause] = field(default_factory=list)
    suite_claim: str = ""
    verdict: str = ""
    delta_reasons: list[str] = field(default_factory=list)

def find_repo_root(start: Path) -> Path:
    """First ancestor holding the campaign state or the engine source.

    Consumer campaigns (issue #28) run this checker inside their own
    repo: the campaign root holds .rumpun/ and no src/rumpun. Engine
    repo runs keep the src/rumpun marker. Either marker resolves the
    repo the check runs against (git history, venv, ledger).
    """
    for candidate in (start, *start.parents):
        if (candidate / ".rumpun").is_dir() or (candidate / "src" / "rumpun").is_dir():
            return candidate
    msg = f"no ancestor of {start} contains .rumpun or src/rumpun"
    raise SystemExit(msg)


def venv_python(repo: Path) -> str:
    """The repo venv's python when present, else the current interpreter.

    The fallback is probed before use (issue #40): a python that cannot
    import pytest is refused (exit 2) naming the gap. Silently running
    the pins lane under it dies "No module named pytest" exit 1 on green
    trees. The venv python is returned unprobed: repos with a real venv
    are byte-unchanged.
    """
    candidate = repo / ".venv" / "bin" / "python"
    if candidate.is_file():
        return str(candidate)
    probe = subprocess.run(
        [sys.executable, "-c", "import pytest"], capture_output=True, text=True,
        check=False,
    )
    if probe.returncode != 0:
        tail = probe.stderr.strip().splitlines()[-1] if probe.stderr.strip() else ""
        logger.error(
            "no python with pytest: %s absent and the fallback %s cannot"
            " import pytest (%s)",
            candidate, sys.executable, tail,
        )
        raise SystemExit(2)
    return sys.executable


def git_capture(args, repo, text=True):
    """One git command under GIT_TIMEOUT_S; captured streams."""
    argv = ["git", "-C", str(repo), *args]
    try:
        proc = subprocess.Popen(
            argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text,
        )
    except OSError as exc:
        logger.error("git unavailable: %s", exc)
        raise
    try:
        out, err = proc.communicate(timeout=GIT_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        msg = f"git timed out: {' '.join(argv)}"
        raise RuntimeError(msg) from None
    return proc.returncode, out, err


def git_or_die(args, repo, text=True):
    """git_capture that exits 2 on failure, naming the command."""
    code, out, err = git_capture(args, repo, text=text)
    if code != 0:
        tail = err.decode("utf-8", "replace") if isinstance(err, bytes) else err
        logger.error("git %s failed (exit %d): %s", " ".join(args), code, tail.strip()[:300])
        raise SystemExit(2)
    return out

def extract_commit(repo, commit, tree):
    """git archive COMMIT into the temp tree; returns the file count. The
    archive bytes unpack through tarfile in-process: no shell pipeline, so
    the git exit code cannot be eaten by a pipe (the s25 lesson).
    """
    started = time.monotonic()
    raw = git_or_die(["archive", str(commit)], repo, text=False)
    assert isinstance(raw, bytes)
    n = 0
    with tarfile.open(fileobj=BytesIO(raw), mode="r:") as tar:
        try:
            tar.extractall(tree, filter="data")
        except TypeError:  # pre-3.12 pythons: no filter kwarg
            tar.extractall(tree)
        n = sum(1 for p in tree.rglob("*") if p.is_file())
    logger.info("extracted %s -> %s (%d files)", str(commit)[:12], tree, n)
    logger.debug("extraction took %.1fs", time.monotonic() - started)
    return n


def read_text(path):
    """Read a text artifact; unreadable is a structural refusal (exit 2)."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.error("unreadable artifact %s: %s", path, exc)
        raise SystemExit(2) from None


def _row_lines(text, sid):
    """The raw `| <sid> | outcome | ships |` row lines of a DESIGN.md text."""
    pattern = re.compile(rf"\| {re.escape(sid)} \|.*\|.*\|")
    return [line for line in text.splitlines() if pattern.fullmatch(line.strip())]


def ships_row(design, sid, live_path=None):
    """The outcome and ships cells of <sid>'s DESIGN.md row, plus the row
    source: "" for the extracted row, LIVE_ROW_NOTE when the close-time
    fallback fired.

    A row is | <sid> | outcome | ships |. Zero rows: unknown season id.
    Several rows: the LAST (newest section), with a logged note. Zero
    extracted rows with live_path set: the close-time fallback -- the
    close's own entry postdates the commit (the s57 refusal), so the live
    worktree's row is used when it has one. The fallback covers ONLY the
    missing fresh row; files, digests, and seals keep binding to the
    extracted tree. live_path is read lazily: only when the extracted
    rows are empty.
    """
    rows = _row_lines(design, sid)
    note = ""
    if not rows and live_path is not None and live_path.is_file():
        live_rows = _row_lines(read_text(live_path), sid)
        if live_rows:
            rows = live_rows
            note = LIVE_ROW_NOTE
            logger.warning("season %s: %s", sid, LIVE_ROW_NOTE)
    if not rows:
        where = (
            "extracted nor live DESIGN.md"
            if live_path is not None
            else "extracted DESIGN.md"
        )
        msg = f"no ships row for {sid} in the {where} (unknown season id?)"
        logger.error(msg)
        raise SystemExit(2)
    if len(rows) > 1:
        logger.warning("%d ships rows for %s; using the last", len(rows), sid)
    cells = [c.strip() for c in rows[-1].strip().strip("|").split("|")]
    if len(cells) != 3:
        msg = f"ships-row parse error for {sid}: {rows[-1][:80]}"
        logger.error(msg)
        raise SystemExit(2)
    return cells[1], cells[2], note


def split_clauses(cell):
    """Top-level comma/semicolon splits; commas inside parens survive."""
    clauses = []
    depth = 0
    start = 0
    for i, ch in enumerate(cell):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch in ",;" and depth == 0:
            clauses.append(cell[start:i].strip())
            start = i + 1
    tail = cell[start:].strip()
    if tail:
        clauses.append(tail)
    return [c for c in clauses if c]

def resolve_file(tree, token):
    """A named file claim resolved against the extracted tree."""
    for rel in (token, f"{MODULE_DIR}/{token}", f"tools/{token}", f"tests/{token}"):
        if (tree / rel).is_file():
            return tree / rel
    return None


def search_files(tree, paths, token):
    """Search token verbatim in the given files; the first hit wins."""
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.warning("unreadable during surface search: %s", exc)
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if token in line:
                rel = path.relative_to(tree)
                return Surface(token, True, f"{rel}:{lineno}")
    return Surface(token, False, "")


def search_tree(tree, token):
    """Search token verbatim across the tree's src/ *.py files."""
    src = tree / "src"
    hits = sorted(src.rglob("*.py")) if src.is_dir() else []
    return search_files(tree, hits, token)


def _segment_bounds(text, pos):
    """The top-level (paren-depth-0) comma/semicolon segment around pos."""
    depth = 0
    start = 0
    for i, ch in enumerate(text[:pos]):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch in ",;" and depth == 0:
            start = i + 1
    end = len(text)
    depth = 0
    for i in range(pos, len(text)):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch in ",;" and depth == 0:
            end = i
            break
    return start, end


def runtime_framed(text, pos, token, sid):
    """Is the file-shaped token framed as run-time output?

    Runtime framings (the s61 false positive: "the engine's finalize
    writes results.jsonl"): the clause writes the token ("writes
    <token>"), the token path carries the runs/<sid>/ prefix, or the
    token's top-level segment carries a close-time cue.
    """
    if re.search(rf"\b(?:writes?|emits?)\s+{re.escape(token)}\b", text):
        return True
    if token.startswith(f"runs/{sid}/"):
        return True
    start, end = _segment_bounds(text, pos)
    return CLOSE_TIME_CUE_RE.search(text[start:end]) is not None


def resolve_runtime(runs_dir, token):
    """A runtime-framed token resolved against the live runs state.

    Returns (path, why): path is the artifact found under runs_dir (None
    when the claim does not hold), why names the reason when None. A
    runs/<sid>/-prefixed or path-shaped token resolves below runs_dir; a
    bare token binds at the runs root (the finalize's output), never at
    scratch depth.
    """
    if runs_dir is None:
        return None, "no runs state bound to the check"
    if not runs_dir.is_dir():
        return None, f"runs state {runs_dir} absent"
    rel = token
    prefix = f"runs/{runs_dir.name}/"
    if token.startswith(prefix):
        rel = token[len(prefix):]
    direct = runs_dir / rel
    if direct.is_file():
        return direct, ""
    return None, ""


def analyze_clause(text, tree, pins_collected, sid="", runs_dir=None):
    """Extract and judge one named-ship clause's checkable claims.

    runs_dir (the live repo/.rumpun/runs/<sid>/) enables the runtime-vs-
    committed file-claim classification; None binds every file token to
    the extracted tree exactly as before s63.
    """
    clause = ShipClause(text=text)
    lower = text.lower()
    removal = any(marker in lower for marker in REMOVAL_MARKERS)

    file_spans = [
        (m.start(), m.end(), m.group(0)) for m in FILE_TOKEN_RE.finditer(text)
    ]
    key_tokens = [
        m.group(0) for m in KEY_TOKEN_RE.finditer(text)
        if not any(fs <= m.start() < fe for fs, fe, _ in file_spans)
    ]
    slash_tokens = [
        m.group(0) for m in SLASH_TOKEN_RE.finditer(text)
        if not any(fs <= m.start() < fe for fs, fe, _ in file_spans)
    ]
    for start, _, token in file_spans:
        if runs_dir is not None and runtime_framed(text, start, token, sid):
            path, why = resolve_runtime(runs_dir, token)
            if path is not None:
                clause.file_claims.append(
                    FileClaim(
                        token, "runtime", True,
                        f"runs/{runs_dir.name}/{path.relative_to(runs_dir).as_posix()}",
                    )
                )
                continue
            resolved = resolve_file(tree, token)
            if resolved is not None:
                rel = resolved.relative_to(tree).as_posix()
                clause.files.append(rel)
                clause.file_claims.append(
                    FileClaim(token, "runtime-committed-fallback", True, rel)
                )
                clause.notes.append(
                    f"{token}: absent from runs/{runs_dir.name}/, bound committed"
                    " (committed-tree fallback)"
                )
                continue
            if re.search(rf"\bemits?\s+{re.escape(token)}\b", text):
                emit_site = search_tree(tree, token.rsplit("/", 1)[-1])
                if emit_site.present:
                    clause.file_claims.append(
                        FileClaim(
                            token, "runtime", True,
                            f"emit site: {emit_site.where}",
                        )
                    )
                    clause.notes.append(
                        f"{token}: emit-framed; the emit site is present in"
                        " src; the path lands in scaffolded campaigns (not"
                        " re-run)"
                    )
                    continue
            clause.verdict = "DELTA"
            note = f"missing runtime artifact: {token}"
            if why:
                note = f"{note} ({why})"
            clause.notes.append(note)
            clause.file_claims.append(FileClaim(token, "runtime", False, ""))
            continue
        resolved = resolve_file(tree, token)
        if resolved is None:
            clause.verdict = "DELTA"
            clause.notes.append(f"missing file: {token}")
            clause.file_claims.append(FileClaim(token, "committed", False, ""))
        else:
            rel = resolved.relative_to(tree).as_posix()
            clause.files.append(rel)
            clause.file_claims.append(FileClaim(token, "committed", True, rel))
    for token in key_tokens:
        surface = search_tree(tree, token)
        if not surface.present:
            surface = search_tree(tree, token.rstrip(":"))
        clause.surfaces.append(surface)
    for token in slash_tokens:
        comps = [c for c in token.strip("/").split("/") if c]
        module_paths = [resolve_file(tree, f"{c}.py") for c in comps]
        if any(c.isdigit() for c in comps):
            clause.notes.append(f"{token}: metric token, not a surface")
            continue
        if comps and all(p is not None for p in module_paths):
            rels = ", ".join(p.relative_to(tree).as_posix() for p in module_paths)
            clause.surfaces.append(Surface(token, True, f"module reading: {rels}"))
            for kt in key_tokens:
                surface = search_files(tree, module_paths, kt)
                if not surface.present:
                    surface = search_files(tree, module_paths, kt.rstrip(":"))
                clause.surfaces.append(surface)
            continue
        rel_token = token.strip("/")
        if (
            rel_token
            and token.count("/") == 1
            and all("." not in c for c in comps)
            and not (tree / rel_token).exists()
        ):
            clause.notes.append(
                f"{token}: external reference, not a tree surface"
            )
            continue
        if rel_token and (tree / rel_token).exists():
            clause.surfaces.append(
                Surface(token, True, f"committed path: {rel_token}")
            )
            continue
        probe = comps[-1] if comps else token
        surface = search_tree(tree, probe)
        clause.surfaces.append(surface)
        if not surface.present and removal:
            clause.notes.append(f"{token}: absent, consistent with the removal claim")
        elif surface.present and removal:
            clause.notes.append(
                f"{token}: legacy token still in src (evidence; the removal"
                " claim itself is judged by the pins)"
            )
        elif not surface.present and not any(s.present for s in clause.surfaces):
            clause.verdict = "DELTA"
            clause.notes.append(f"no named surface found for: {token}")
    m_pins = PINS_CLAIM_RE.search(text)
    if m_pins is not None and pins_collected is not None:
        claimed = int(m_pins.group(1))
        if claimed == pins_collected:
            clause.notes.append(f"pins claim {claimed} == collected {pins_collected}")
        else:
            clause.verdict = "DELTA"
            clause.notes.append(f"claims {claimed} pins, tree carries {pins_collected}")
    m_suite = SUITE_CLAIM_RE.search(text)
    if m_suite is not None:
        clause.notes.append(
            f"suite claim {m_suite.group(1)}/{m_suite.group(2)} recorded, not re-run"
        )
    if (
        clause.verdict == "MATCH"
        and clause.surfaces
        and not any(s.present for s in clause.surfaces)
        and not removal
    ):
        clause.verdict = "DELTA"
        clause.notes.append("every named surface token absent from the tree")
    return clause

def run_pins(tree, pin_files, python):
    """The season's pins under the repo venv, PYTHONPATH bound to the tree.

    A resolution probe runs first: it must resolve rumpun inside the
    extracted tree; anything else is a structural refusal (exit 2).
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree / "src")
    started = time.monotonic()
    probe_argv = [python, "-c", "import rumpun; print(rumpun.__file__)"]
    try:
        probe = subprocess.run(
            probe_argv, cwd=str(tree), env=env, capture_output=True, text=True,
            timeout=PROBE_TIMEOUT_S, check=False,
        )
    except subprocess.TimeoutExpired:
        logger.error("import probe timed out after %ds", PROBE_TIMEOUT_S)
        raise SystemExit(2) from None
    resolved = probe.stdout.strip()
    src_prefix = str(tree / "src")
    if probe.returncode != 0 or not resolved.startswith(src_prefix):
        logger.error(
            "import probe failed: exit %d, resolved %r (want prefix %s)",
            probe.returncode, resolved or probe.stderr.strip()[:200], src_prefix,
        )
        raise SystemExit(2)
    argv = [
        python, "-m", "pytest",
        *(str(p) for p in pin_files), "-q", "-p", "no:cacheprovider",
    ]
    proc = subprocess.Popen(
        argv, cwd=str(tree), env=env, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, start_new_session=True,
    )
    try:
        out, _ = proc.communicate(timeout=PINS_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)
        out, _ = proc.communicate()
        logger.error("pins run exceeded %ds; process group killed", PINS_TIMEOUT_S)
        return {
            "exit": "timeout", "probe": resolved,
            "collected": 0, "passed": 0, "failed": 0, "errors": 0,
            "duration": f"{time.monotonic() - started:.1f}s",
        }
    passed = re.search(r"(\d+) passed", out)
    failed = re.search(r"(\d+) failed", out)
    errors = re.search(r"(\d+) error", out)
    skipped = re.search(r"(\d+) skipped", out)
    info = {
        "exit": str(proc.returncode),
        "probe": resolved,
        "collected": sum(
            int(m.group(1)) for m in (passed, failed, errors, skipped) if m
        ),
        "passed": int(passed.group(1)) if passed else 0,
        "failed": int(failed.group(1)) if failed else 0,
        "errors": int(errors.group(1)) if errors else 0,
        "duration": f"{time.monotonic() - started:.1f}s",
        "summary": (out.strip().splitlines()[-1] if out.strip() else "")[:200],
    }
    if proc.returncode in (2, 4, 5):
        logger.error(
            "pins did not collect (pytest exit %d): %s (%s)",
            proc.returncode, [p.name for p in pin_files], info["summary"],
        )
        raise SystemExit(2)
    return info

def recompute_pack_digest(pack_dir):
    """The s47 convention, computed independently of rumpun.plugin: sha256
    over the pack's priors/ tree (sorted pack-relative POSIX paths, NUL
    separators, no trailing separator; empty or missing tree = sha256 of
    empty input)."""
    digest = hashlib.sha256()
    priors = pack_dir / "priors"
    if priors.is_dir():
        for path in sorted(p for p in priors.rglob("*") if p.is_file()):
            digest.update(path.relative_to(pack_dir).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def parse_registry(text, reg_path):
    """Minimal indentation-based read of the yaml.safe_dump layout:
    'plugins:' -> two-space '<name>:' -> four-space '<key>: <value>'.
    Any other shape is a structural refusal naming the registry."""
    plugins = {}
    current = None
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if lineno == 1 and line == "plugins:":
            current = None
            continue
        m_pack = re.fullmatch(r"  (\S.*):\s*", line)
        m_leaf = re.fullmatch(r"    (\S+): (.*)", line)
        if m_leaf and current is not None:
            plugins[current][m_leaf.group(1)] = m_leaf.group(2).strip()
        elif m_pack and current is None:
            current = m_pack.group(1)
            plugins[current] = {}
        else:
            msg = f"{reg_path}:{lineno}: unexpected registry line shape: {line[:60]}"
            logger.error(msg)
            raise SystemExit(2)
    return plugins


def digest_packs(tree):
    """Claimed pack digests vs recomputed; ([], note) when no registry."""
    reg = tree / ".rumpun" / "plugins.yml"
    if not reg.is_file():
        note = "no .rumpun/plugins.yml in the extracted tree (no pack digest claims)"
        return [], note
    plugins = parse_registry(read_text(reg), reg)
    rows = []
    for name in sorted(plugins):
        claimed = plugins[name].get("digest", "")
        pack_dir = tree / ".rumpun" / "plugins" / name
        recomputed = recompute_pack_digest(pack_dir)
        status = "MATCH" if claimed == recomputed else "DELTA"
        rows.append((name, str(claimed), recomputed, status))
    note = f"{len(rows)} pack record(s) re-digested from plugins.yml"
    return rows, note

def seal_check(tree, sid):
    """The <sid>-harvest record's sha256 seal, recomputed per akar.append_record:
    body = lines[4:-1] joined by newlines; claimed = trailing sha256 line."""
    matches = sorted((tree / ".rumpun" / "ledger").glob(f"*_{sid}-harvest.md"))
    if not matches:
        return [], f"no {sid}-harvest record in the extracted ledger"
    rows = []
    for path in matches:
        lines = read_text(path).splitlines()
        if len(lines) < 6 or not lines[-1].startswith("sha256: "):
            rows.append((path.name, "?", "record layout unreadable", "DELTA"))
            continue
        body = "\n".join(lines[4:-1])
        claimed = lines[-1][len("sha256: "):].strip()
        recomputed = hashlib.sha256(body.encode("utf-8")).hexdigest()
        status = "MATCH" if claimed == recomputed else "DELTA"
        rows.append((path.name, claimed, recomputed, status))
    note = f"{len(matches)} harvest seal(s) recomputed"
    return rows, note


def build_record(res, packs_note, seals_note):
    """The check-<sid> record: akar layout, sha256 trailer over the body."""
    body = [
        f"season: {res.sid}",
        f"close-commit: {res.commit}",
        f"outcome row: {res.outcome}",
        f"extracted: git archive -> temp tree ({res.n_extracted} files)",
        "commands run:",
        *(f"- {cmd}" for cmd in res.commands),
        f"pins: {res.pins.get('display', 'no pins run')}",
    ]
    body.extend(f"pack digest {n}: claimed {c} recomputed {r} -> {s}"
                for n, c, r, s in res.packs)
    if not res.packs:
        body.append(f"packs: {packs_note}")
    body.extend(f"seal {n}: claimed {c} recomputed {r} -> {s}"
                for n, c, r, s in res.seals)
    if not res.seals:
        body.append(f"seals: {seals_note}")
    body.append(f"ships row (verbatim): {res.ships_verbatim}")
    if res.ships_source:
        body.append(res.ships_source)
    body.append("ships diff:")
    body.append("| named ship | verdict | evidence |")
    body.append("|---|---|---|")
    for cl in res.clauses:
        parts = [f"file {f} exists (committed-tree claim)" for f in cl.files]
        parts += [
            f"file {fc.token} MISSING (committed-tree claim)"
            for fc in cl.file_claims if fc.kind == "committed" and not fc.present
        ]
        parts += [
            f"runtime artifact {fc.token} "
            f"{'PRESENT (' + fc.where + ')' if fc.present else 'MISSING'}"
            f" (runtime-checked against runs/{res.sid}/)"
            for fc in cl.file_claims if fc.kind == "runtime"
        ]
        parts += [
            f"runtime artifact {fc.token} PRESENT ({fc.where})"
            f" (absent from runs/{res.sid}/; bound committed in the extracted tree)"
            for fc in cl.file_claims if fc.kind == "runtime-committed-fallback"
        ]
        parts += [
            f"{s.token} {'PRESENT (' + s.where + ')' if s.present else 'ABSENT'}"
            for s in cl.surfaces
        ]
        parts += cl.notes
        evidence = "; ".join(parts) or "no machine-checkable claims (prose clause)"
        shown = cl.text if len(cl.text) <= 80 else cl.text[:77] + "..."
        body.append(f"| {shown} | {cl.verdict} | {evidence} |")
    if res.suite_claim:
        body.append(f"suite claim: {res.suite_claim} recorded, not re-run")
    if res.delta_reasons:
        body.append(f"deltas: {'; '.join(res.delta_reasons)}")
    body.append(f"verdict: {res.verdict}")
    body_text = "\n".join(body)
    digest = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
    header = [
        f"# akar record: check-{res.sid}",
        f"id: check-{res.sid}",
        f"date: {date.today().isoformat()}",
        f"title: independent artifact check {res.sid} @ {res.commit[:12]} ({res.verdict})",
    ]
    return "\n".join([*header, body_text, f"sha256: {digest}"]) + "\n"

def write_record(out_dir, sid, text):
    """Atomic append-only write; suffixes a superseding same-day rerun.

    The base id check-<sid> never rewrites: a same-day rerun lands as
    check-<sid>-<N> (N=2,3,...), the engine's own newest-record
    convention. Only the two header lines carry the suffixed id; the
    body and its sha256 seal are untouched.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{date.today().isoformat()}_check-{sid}"
    final = out_dir / f"{stem}.md"
    rerun = 1
    while final.exists():
        rerun += 1
        final = out_dir / f"{stem}-{rerun}.md"
    if rerun > 1:
        rid = f"check-{sid}-{rerun}"
        lines = text.splitlines()
        lines[0] = f"# akar record: {rid}"
        lines[1] = f"id: {rid}"
        text = "\n".join(lines) + "\n"
        logger.warning(
            "check-%s record exists; superseding rerun recorded as %s",
            sid,
            rid,
        )
    tmp = final.with_name(f".{final.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(final)
    return final


def main(argv=None):
    """Run the check; 0 VERIFIED, 1 DELTA, 2 structural refusal."""
    parser = argparse.ArgumentParser(
        description="independent artifact check: re-verify a season from its close commit",
    )
    parser.add_argument("sid", help="season id, e.g. s54")
    parser.add_argument("close_commit", help="season-close commit sha")
    parser.add_argument("--repo", type=Path, default=None, help="repo root")
    parser.add_argument("--out-dir", type=Path, default=None, help="record output dir")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr,
    )
    repo = args.repo or find_repo_root(Path(__file__).resolve().parent)
    python = venv_python(repo)
    result = CheckResult(sid=args.sid, commit=args.close_commit, outcome="")
    full = git_or_die(
        ["rev-parse", "--verify", f"{args.close_commit}^{{commit}}"], repo,
    )
    result.commit = full.strip()
    result.commands.append(
        f"git -C {repo} rev-parse --verify {args.close_commit}^{{commit}} -> {result.commit}"
    )
    with tempfile.TemporaryDirectory(prefix="artifact-check-") as tmp:
        tree = Path(tmp) / "tree"
        tree.mkdir()
        result.n_extracted = extract_commit(repo, result.commit, tree)
        result.commands.append(
            f"git -C {repo} archive {result.commit[:12]} -> {result.n_extracted} files"
        )
        pin_files = sorted((tree / "tests").glob(f"test_{args.sid}_*.py"))
        if not (tree / "DESIGN.md").is_file():
            # issues #36, #37: a repo with no DESIGN.md convention must not
            # take the structural refusal (exit 2) -- there it is
            # indistinguishable from tamper. With no pins lane either,
            # nothing is checkable: the s108 named skip, exit 0, no record,
            # naming the convention. With a pins lane, the SHIPS phase
            # skips and the record carries the note; pins, pack digests,
            # and seals still bind. A DESIGN.md present but missing the
            # season's row keeps the exit 2 refusal (ships_row).
            if not pin_files:
                logger.info(
                    "skip %s @ %s: no DESIGN.md convention in the extract"
                    " and no pins lane (nothing to check)",
                    args.sid, result.commit[:12],
                )
                return 0
            result.ships_source = NO_DESIGN_NOTE
            logger.warning(
                "ships phase skipped for %s @ %s: %s",
                args.sid, result.commit[:12], NO_DESIGN_NOTE,
            )
        else:
            design = read_text(tree / "DESIGN.md")
            result.outcome, result.ships_verbatim, source_note = ships_row(
                design, args.sid, live_path=repo / "DESIGN.md",
            )
            result.ships_source = source_note
        if not pin_files:
            if PINS_CLAIM_RE.search(result.ships_verbatim) is not None:
                logger.error(
                    "no pins file matching tests/test_%s_*.py in %s, "
                    "but the ships row claims pins",
                    args.sid, result.commit[:12],
                )
                raise SystemExit(2)
            logger.info(
                "skip %s @ %s: no pins lane (nothing to check); "
                "the ships row claims no pins",
                args.sid, result.commit[:12],
            )
            return 0
        if not (tree / "src").is_dir():
            # issue #39: a docs-only extract cannot resolve the package,
            # so the import probe would refuse exit 2, reading as tamper.
            # The named pins-lane skip: exit 0, no record.
            logger.info(
                "skip %s @ %s: no src/ in the extract; the pins lane has"
                " no package to import",
                args.sid, result.commit[:12],
            )
            return 0
        info = run_pins(tree, pin_files, python)
        result.pins = {
            "display": (
                f"exit {info['exit']}; {info['passed']} passed; collected {info['collected']},"
                f" passed {info['passed']}, failed {info['failed']},"
                f" errors {info['errors']}; {info['duration']};"
                f" probe resolved {info['probe']}"
            )
        }
        result.commands.append(
            f"{python} -m pytest {[p.relative_to(tree).as_posix() for p in pin_files]}"
            f" -q (exit {info['exit']})"
        )
        packs, packs_note = digest_packs(tree)
        seals, seals_note = seal_check(tree, args.sid)
        result.packs = packs
        result.seals = seals
        runs_dir = repo / ".rumpun" / "runs" / args.sid
        result.clauses = [
            analyze_clause(text, tree, info["collected"], args.sid, runs_dir)
            for text in split_clauses(result.ships_verbatim)
        ]
        m_suite = SUITE_CLAIM_RE.search(result.ships_verbatim)
        result.suite_claim = f"{m_suite.group(1)}/{m_suite.group(2)}" if m_suite else ""
        reasons = []
        if info["exit"] != "0":
            reasons.append(f"pins not green in the extracted tree (exit {info['exit']})")
        reasons += [f"pack digest {n}" for n, c, r, s in packs if s == "DELTA"]
        reasons += [f"seal {n}" for n, c, r, s in seals if s == "DELTA"]
        reasons += [
            f"ships row: {cl.notes[0] if cl.notes else cl.text[:40]}"
            for cl in result.clauses if cl.verdict == "DELTA"
        ]
        result.delta_reasons = reasons
        result.verdict = "DELTA" if reasons else "VERIFIED"
        out_dir = args.out_dir or (repo / ".rumpun" / "ledger")
        text = build_record(result, packs_note, seals_note)
        final = write_record(out_dir, args.sid, text)
        logger.info("verdict %s; record -> %s", result.verdict, final)
    if result.verdict == "VERIFIED":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
def cmd_check(args):
    """Preflight guidance: what to fill before rendering, in plain words.
    Exit 0 ready, 1 blockers, 2 notes only."""
    pdir = resolve_project(args.project)
    pf = pdir / "project.yaml"
    if not pf.is_file():
        fail(f"{pf} missing")
    try:
        data = yaml.safe_load(pf.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        fail(f"project.yaml parse error: {e}")
    if not isinstance(data, dict):
        fail("project.yaml must be a mapping")
    issues, notes = [], []
    for section in ("meta", "characters", "script", "settings"):
        if section not in data:
            issues.append(f"no [{section}] section - copy it from templates/<format>/template.yaml")
    meta = data.get("meta") or {}
    if not str(meta.get("title", "")).strip():
        issues.append("meta.title is empty - name your video")
    vendor = meta.get("vendor", "remotion")
    build = ROOT / "vendors" / vendor / "build.sh"
    if not build.is_file():
        issues.append(f"vendor '{vendor}' does not exist (known: remotion, hyperframes)")
    chars = data.get("characters") or {}
    if not chars:
        issues.append("no characters - every script line needs a speaker")
    for cid, c in chars.items():
        if not str(c.get("name", "")).strip():
            issues.append(f"character '{cid}' has no name")
        v = c.get("voice") or {}
        engine = v.get("engine")
        if not engine:
            issues.append(f"character '{cid}' has no voice.engine - how should it sound?")
        elif engine not in PROVIDERS:
            issues.append(f"character '{cid}': voice engine '{engine}' is unknown (known: {', '.join(sorted(PROVIDERS))})")
        else:
            ok, why = PROVIDERS[engine].available()
            if not ok:
                notes.append(f"character '{cid}' speaks via {engine}: {why} - renders stay silent with estimated timing until you set the key")
    lines = data.get("script") or []
    if not lines:
        issues.append("script is empty - write at least one line")
    for line in lines:
        if line.get("character") not in chars:
            issues.append(f"script line {line.get('id')}: speaker '{line.get('character')}' is not defined in characters")
        if not str(line.get("text", "")).strip():
            issues.append(f"script line {line.get('id')}: text is empty")
    settings = data.get("settings") or {}
    if settings.get("background") is not None:
        catalog_dir = ROOT / "vendors" / vendor / "assets" / "backgrounds"
        if catalog_dir.is_dir():
            catalog = sorted(p.stem for p in catalog_dir.glob("*.png"))
            if settings["background"] not in catalog:
                issues.append(f"settings.background '{settings['background']}' is not a theme here (available: {', '.join(catalog)})")
    if settings.get("character", {}).get("use_images"):
        for cid in chars:
            if not (pdir / "assets" / "images" / cid / "mouth_close.png").is_file():
                notes.append(f"character '{cid}' has use_images but no art at assets/images/{cid}/ - placeholder box will show")
    manifest_file = pdir / "voices" / "manifest.json"
    if manifest_file.is_file():
        cached = len(json.loads(manifest_file.read_text(encoding="utf-8")).get("lines", {}))
        notes.append(f"{cached} line voice(s) cached in voices/ - they are reused on render")
    for msg in issues:
        log.warning("FILL: %s", msg)
    for msg in notes:
        log.info("NOTE: %s", msg)
    if args.json:
        print(json.dumps({"ready": not issues, "issues": issues, "notes": notes}))
    if issues:
        log.warning("NOT READY: %d item(s) to fill above - then: wayang.py validate && wayang.py render", len(issues))
        raise SystemExit(1)
    if notes:
        log.warning("READY with %d note(s) - see NOTE lines above", len(notes))
        raise SystemExit(2)
    log.info("READY")


def cmd_lint(args):
    pdir = resolve_project(args.project)
    data = validate_project(pdir)
    mp4 = pdir / "out" / "video.mp4"
    if not mp4.is_file():
        fail(f"no render found at {mp4} - run wayang.py render first")
    lint_project(pdir, mp4, data)


def render_one(pdir: Path, skip_lint: bool = False) -> None:
    data = validate_project(pdir)
    # The vendor consumes one canonical file. When series inheritance applied,
    # materialize the merged doc so the vendor never needs to know about series.
    merged_path = pdir / ".merged.yaml"
    if find_series_file(pdir) is not None:
        merged_path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
    elif merged_path.exists():
        merged_path.unlink()
    run_tts(pdir, data)
    vendor = data["meta"]["vendor"]
    build = ROOT / "vendors" / vendor / "build.sh"
    out = pdir / "out"
    log.info("rendering via vendor '%s'", vendor)
    proc = subprocess.run(["bash", str(build), str(pdir), str(out)], check=False)
    if proc.returncode != 0:
        fail(f"vendor build.sh exited {proc.returncode}")
    log.info("done: %s", out / "video.mp4")
    if not skip_lint:
        lint_project(pdir, out / "video.mp4", data)


vendors/remotion/scripts/map-project.mjs:2:// map-project.mjs - canonical project.yaml -> remotion engine inputs.
vendors/remotion/scripts/map-project.mjs:41:const vendorCfg = (project.vendor && project.vendor.remotion) || {};
vendors/remotion/scripts/map-project.mjs:43:const playbackRate = settings.video?.playback_rate ?? 1.2;
vendors/remotion/scripts/map-project.mjs:44:const cps = vendorCfg.estimate_cps ?? 7.5;
vendors/remotion/scripts/map-project.mjs:47:const vendorKeysAllowed = ["estimate_cps"];
vendors/remotion/scripts/map-project.mjs:50:    die(`vendor.remotion: unknown key '${k}' (allowed: ${vendorKeysAllowed.join(", ")})`);
vendors/remotion/scripts/map-project.mjs:56:  video: { width: "width", height: "height", fps: "fps", playback_rate: "playbackRate" },
vendors/remotion/scripts/map-project.mjs:67:  video: { width: 1920, height: 1080, fps: 30, playbackRate: 1.2 },
vendors/remotion/scripts/map-project.mjs:112:  if (line.emotion) mapped.emotion = line.emotion;
vendors/remotion/scripts/map-project.mjs:164:    emotion: null,
vendors/remotion/scripts/map-project.mjs:185:// ---- estimated timing + silent placeholder wavs (TTS source: estimate) ----
vendors/remotion/scripts/map-project.mjs:230:      durations[f] = Math.ceil(seconds * fps * playbackRate);
vendors/remotion/scripts/map-project.mjs:237:// ---- Priority 2: estimate + silent placeholder wavs ----
vendors/remotion/scripts/map-project.mjs:239:  console.log("[map-project] TTS source: estimate (durations.json + silent placeholder wavs written)");
vendors/remotion/scripts/map-project.mjs:242:    const seconds = visible / (cps * playbackRate);
vendors/remotion/scripts/map-project.mjs:250:fs.writeFileSync(path.join(workVoices, ".source"), platformEngines ? "platform" : "estimate");
vendors/remotion/scripts/map-project.mjs:254:const adjusted = (frames) => Math.ceil(frames / playbackRate);
vendors/remotion/scripts/map-project.mjs:270:const adjustedFrames = (frames) => Math.ceil(frames / playbackRate);
vendors/remotion/scripts/map-project.mjs:303:console.log(`[map-project] lines: ${engineScript.length}, fps: ${fps}, playbackRate: ${playbackRate}, estimate_cps: ${cps}`);
vendors/remotion/engine/src/Main.tsx:1:import { AbsoluteFill, useCurrentFrame, useVideoConfig, Audio, Sequence, staticFile, Loop, Img } from "remotion";
vendors/remotion/engine/src/Main.tsx:2:import { loadFont } from "@remotion/google-fonts/MPLUSRounded1c";
vendors/remotion/engine/src/Main.tsx:3:import { scriptData, scenes, ScriptLine, bgmConfig, CHARACTERS } from "./data/script";
vendors/remotion/engine/src/Main.tsx:15:  Math.ceil(frames / SETTINGS.video.playbackRate);
vendors/remotion/engine/src/Main.tsx:45:  const sceneInfo = scenes.find((s) => s.id === currentScene) || scenes[0];
vendors/remotion/engine/src/Main.tsx:83:      {bgmConfig && (
vendors/remotion/engine/src/Main.tsx:85:          src={staticFile(`bgm/${bgmConfig.src}`)}
vendors/remotion/engine/src/Main.tsx:86:          volume={bgmConfig.volume ?? 0.3}
vendors/remotion/engine/src/Main.tsx:87:          loop={bgmConfig.loop ?? true}
vendors/remotion/engine/src/Main.tsx:103:              playbackRate={SETTINGS.video.playbackRate}
vendors/remotion/engine/src/Main.tsx:131:          emotion={currentLine?.character === c.id ? currentLine.emotion : "normal"}
vendors/hyperframes/scripts/map-project.mjs:61:const cps = vendorCfg.estimate_cps ?? 7.5;
vendors/hyperframes/scripts/map-project.mjs:62:const playbackRate = settings.video?.playback_rate ?? 1;
vendors/hyperframes/scripts/map-project.mjs:68:  if (!["estimate_cps"].includes(k)) {
vendors/hyperframes/scripts/map-project.mjs:69:    die(`vendor.hyperframes: unknown key '${k}' (allowed: estimate_cps)`);
vendors/hyperframes/scripts/map-project.mjs:79:// ---- voices: platform manifest or estimates (never mixed) ----
vendors/hyperframes/scripts/map-project.mjs:98:  console.log("[map-project] TTS source: estimate (no platform voices complete)");
vendors/hyperframes/scripts/map-project.mjs:109:  const dur = raw / playbackRate;
vendors/hyperframes/scripts/map-project.mjs:111:  timeline.push({ line, file, start: t, dur, end: t + dur, subEnd: t + dur + pause / playbackRate });
vendors/hyperframes/scripts/map-project.mjs:112:  t += dur + pause / playbackRate;
vendors/hyperframes/scripts/map-project.mjs:262:  clips.push(`    <audio class="clip" id="line-${line.id}-audio" src="voices/${seg.file}" data-start="${seg.start.toFixed(3)}" data-duration="${seg.dur.toFixed(3)}" data-playback-rate="${playbackRate}" data-track-index="20"></audio>`);

hook: PostToolUse
hook: PostToolUse Completed
codex
## RESTRUCTURE

**The structure supports ten more vendors and templates with targeted changes.** Keep canonical YAML and independent vendor engines. Retain vendor workdirs and standalone engine samples, consistent with earlier decisions.

| Priority | Concrete move | Reason | Risk |
|---|---|---|---|
| P0 | Split project loading and preflight from `tools/wayang.py` into `tools/project.py`. Route `check`, validation, and rendering through shared loading. | `check` ignores series inheritance and reads the removed vendor theme catalog. Shared loading prevents divergent authoring rules. | Incomplete YAML still needs helpful FILL messages. Preserve exit codes. |
| P0 | Move duplicate duration guards from `vendors/*/build.sh` into `tools/render_checks.py`. Move visibility functions there from `tools/wayang.py`. | Every vendor needs identical output checks. Require exported `expected-seconds.txt` and complete, unique timeline IDs before pixel probes. | Direct vendor builds need access to the shared checker. Keep renderer timing calculations vendor-owned. |
| P1 | Merge duplicate `templates/*/assets/images/` mascot files into `assets/mascots/catalog/<id>/`. Modify initialization to copy selected art into projects. | Ten more templates multiply duplicate art. The generator already misses tutorial refreshes. | Preserve template-specific variants and project-local overrides. Initialized projects must retain their own asset copies. |
| P1 | Merge `assets/background/generate_background.py` into `assets/background/generate_themes.py` as the chalkboard generator. | One generator owns the shared catalog. Derive output paths from its location, removing stale absolute destinations. | Preserve chalkboard geometry and pixel checks. Stop generation from overwriting vendor defaults. |

Check these moves with inherited episodes and both vendors using cached voices and estimates. Include missing timeline entries as a negative case.

## FEATURES

P1 precedes P2. Effort includes both vendors where applicable. All features retain one canonical authoring YAML and require no owned services.

| Priority / effort | Feature and user story | Implementation sketch |
|---|---|---|
| **P1 / S** | **Caption exports.** “I want editable Bahasa Malaysia subtitles alongside my video.” | Create `tools/captions.py`. Export SRT/VTT from checked `out/timeline.json`, using `display_text` before `text`. Wire into `tools/wayang.py`. No engine changes. |
| **P1 / M** | **Voice rehearsal.** “I want to hear Momo’s opening before rendering the whole video.” | Extend `tts` with line selection and a playable audition WAV. Modify `tools/tts_providers.py` to hash effective defaults. Existing hashes already support selective regeneration. |
| **P1 / M** | **Storyboard contact sheet.** “I want to review cards and subtitles before approving my video.” | Create `tools/storyboard.py` using checked timeline windows and existing ffmpeg extraction. Export numbered frames beside script text after rendering. Initial delivery uses completed renders. |
| **P1 / L** | **Portrait and square layouts.** “I want the same episode in landscape, portrait, and square.” | Add layout presets to `schema/project.schema.json`. Modify both mappers and Remotion components. Extend `docs/vendor-contract.md` with rendered geometry for lint. Dimensions alone do not prevent overlap. |
| **P2 / M** | **Malay pronunciation overrides.** “I want acronyms pronounced clearly while subtitles retain their original spelling.” | Add a project pronunciation dictionary to the schema. Apply substitutions before synthesis in `tools/wayang.py`. Hash transformed speech. Preserve original subtitles. |
| **P2 / M** | **Scene changes.** “I want each chapter to have its own background and title.” | Add scene definitions to the schema. Implement existing `script[].scene` references in both vendors. Extend timeline metadata and lint baselines for changing backgrounds. Scenes currently have no visual effect. |
| **P2 / M** | **Background music with ducking.** “I want quiet music beneath narration.” | Add project-local music config to the schema. Create `tools/audio_mix.py` using ffmpeg and vendor timelines. Check narration audibility before mixing, so music cannot conceal silent speech. |
hook: Stop
hook: Stop Completed
tokens used
60,226
## RESTRUCTURE

**The structure supports ten more vendors and templates with targeted changes.** Keep canonical YAML and independent vendor engines. Retain vendor workdirs and standalone engine samples, consistent with earlier decisions.

| Priority | Concrete move | Reason | Risk |
|---|---|---|---|
| P0 | Split project loading and preflight from `tools/wayang.py` into `tools/project.py`. Route `check`, validation, and rendering through shared loading. | `check` ignores series inheritance and reads the removed vendor theme catalog. Shared loading prevents divergent authoring rules. | Incomplete YAML still needs helpful FILL messages. Preserve exit codes. |
| P0 | Move duplicate duration guards from `vendors/*/build.sh` into `tools/render_checks.py`. Move visibility functions there from `tools/wayang.py`. | Every vendor needs identical output checks. Require exported `expected-seconds.txt` and complete, unique timeline IDs before pixel probes. | Direct vendor builds need access to the shared checker. Keep renderer timing calculations vendor-owned. |
| P1 | Merge duplicate `templates/*/assets/images/` mascot files into `assets/mascots/catalog/<id>/`. Modify initialization to copy selected art into projects. | Ten more templates multiply duplicate art. The generator already misses tutorial refreshes. | Preserve template-specific variants and project-local overrides. Initialized projects must retain their own asset copies. |
| P1 | Merge `assets/background/generate_background.py` into `assets/background/generate_themes.py` as the chalkboard generator. | One generator owns the shared catalog. Derive output paths from its location, removing stale absolute destinations. | Preserve chalkboard geometry and pixel checks. Stop generation from overwriting vendor defaults. |

Check these moves with inherited episodes and both vendors using cached voices and estimates. Include missing timeline entries as a negative case.

## FEATURES

P1 precedes P2. Effort includes both vendors where applicable. All features retain one canonical authoring YAML and require no owned services.

| Priority / effort | Feature and user story | Implementation sketch |
|---|---|---|
| **P1 / S** | **Caption exports.** “I want editable Bahasa Malaysia subtitles alongside my video.” | Create `tools/captions.py`. Export SRT/VTT from checked `out/timeline.json`, using `display_text` before `text`. Wire into `tools/wayang.py`. No engine changes. |
| **P1 / M** | **Voice rehearsal.** “I want to hear Momo’s opening before rendering the whole video.” | Extend `tts` with line selection and a playable audition WAV. Modify `tools/tts_providers.py` to hash effective defaults. Existing hashes already support selective regeneration. |
| **P1 / M** | **Storyboard contact sheet.** “I want to review cards and subtitles before approving my video.” | Create `tools/storyboard.py` using checked timeline windows and existing ffmpeg extraction. Export numbered frames beside script text after rendering. Initial delivery uses completed renders. |
| **P1 / L** | **Portrait and square layouts.** “I want the same episode in landscape, portrait, and square.” | Add layout presets to `schema/project.schema.json`. Modify both mappers and Remotion components. Extend `docs/vendor-contract.md` with rendered geometry for lint. Dimensions alone do not prevent overlap. |
| **P2 / M** | **Malay pronunciation overrides.** “I want acronyms pronounced clearly while subtitles retain their original spelling.” | Add a project pronunciation dictionary to the schema. Apply substitutions before synthesis in `tools/wayang.py`. Hash transformed speech. Preserve original subtitles. |
| **P2 / M** | **Scene changes.** “I want each chapter to have its own background and title.” | Add scene definitions to the schema. Implement existing `script[].scene` references in both vendors. Extend timeline metadata and lint baselines for changing backgrounds. Scenes currently have no visual effect. |
| **P2 / M** | **Background music with ducking.** “I want quiet music beneath narration.” | Add project-local music config to the schema. Create `tools/audio_mix.py` using ffmpeg and vendor timelines. Check narration audibility before mixing, so music cannot conceal silent speech. |
