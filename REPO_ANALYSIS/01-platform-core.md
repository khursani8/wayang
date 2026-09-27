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
