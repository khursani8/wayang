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
