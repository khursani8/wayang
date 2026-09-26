# vendors/remotion — engine manual (AGENTS.md)

Remotion + VOICEVOX vendor for content_engine. Read this before touching the
engine. The platform contract is in the root `AGENTS.md`.

## How the engine works

- Remotion renders React components frame by frame to mp4. Composition:
  `src/index.ts` -> `Root` -> `Main`. `npm run build` = sync + render.
- Background themes: `vendors/remotion/assets/backgrounds/` holds the
  catalog (chalkboard, whiteboard, night-sky, kraft-paper, batik, notebook,
  sunrise, studio, riverbank, slate, wood-table). Select with
  `settings.background: <name>`; unknown themes error; per-project custom
  art overrides via `assets/background.png`. Generators: repo-root
  `assets/background/`.
- Background: `engine/public/background.png` is the default background
  (riverbank, synthesized by repo-root `assets/background/` generators).
  (generator: repo-root `assets/background/generate_background.py`, SVG
  sources alongside). It replaces the old flat divs in Main.tsx. A project
  can override it by shipping `assets/background.png`; project assets are
  copied over the engine defaults during build.
- Materials live under `engine/public/`: `voices/` (per-line wav),
  `images/<character_id>/` (mouth_open.png, mouth_close.png, optional
  `<emotion>_open.png`), `se/` (sound effects), `bgm/` (not wired: engine
  hardcodes bgm off).
- `scripts/sync-script.ts` maps `config/script.yaml` + `characters.yaml` +
  `defaults.yaml` -> `src/data/script.ts` (lines, durations in frames,
  `CHARACTERS`, `characterColors`). `scripts/sync-settings.ts` maps
  `video-settings.yaml` -> `src/settings.generated.ts`.
- `scripts/generate-voices.ts` calls VOICEVOX at `http://localhost:50021`
  and writes `public/voices/*.wav` + `durations.json` (frames per line).

## Entry point

    vendors/remotion/build.sh PROJECT_DIR OUT_DIR

Input file: `.merged.yaml` when present (platform-materialized series
inheritance), else `project.yaml`.

Steps: fresh workdir at `vendors/remotion/.work/<project>/` (engine source
copied, node_modules symlinked from `engine/`), project `assets/` copied into
`public/`, `scripts/map-project.mjs` converts canonical project.yaml into the
engine configs plus estimated timings, `npm run sync`, VOICEVOX pass when
reachable, `remotion render`, result copied to `OUT_DIR/video.mp4`. Idempotent:
the workdir is rebuilt from scratch every run.

## Canonical -> engine mapping

| canonical | engine | note |
|---|---|---|
| meta.language | - | informational; VOICEVOX speaks ja |
| characters.<id>.name | characters.yaml name | |
| characters.<id>.voice.speaker_id | characters.yaml speakerId | null allowed (no TTS) |
| characters.<id>.position | characters.yaml position | left or right |
| characters.<id>.color | characters.yaml color | subtitle outline + placeholder box |
| characters.<id>.flip_x | characters.yaml flipX | mirror the art |
| characters.<id>.image | public/<path> | copy your art under project assets/ and set settings.character.use_images true |
| script[].text | script.yaml text | spoken by TTS |
| script[].display_text | script.yaml displayText | subtitle override |
| script[].scene | script.yaml scene | 1..3 have named backgrounds; higher falls back |
| script[].pause_after | script.yaml pauseAfter | seconds -> frames (x fps) |
| script[].emotion | script.yaml emotion | normal, happy, surprised, thinking, sad |
| script[].visual | script.yaml visual | type text/image/none, font_size->fontSize; text cards get a dark outline by default, override with outline_color |
| script[].se | script.yaml se | src relative to public/ |
| settings.background | public/background.png | theme name from the catalog; project custom file wins; default riverbank |
| settings.* | video-settings.yaml | snake_case -> camelCase, unknown keys error |
| vendor.remotion.estimate_cps | timing estimate | chars per second, default 7.5 |

## Timing and audio honesty

Priority order for line audio: (1) platform-generated voices in
`PROJECT_DIR/voices/` with a manifest covering every line - copied into the
workdir, durations from the manifest, build log names the engines;
(2) VOICEVOX at localhost:50021 (upstream path); (3) estimate with silent
placeholder wavs. Never mixed in one project.

- With VOICEVOX up: real per-line wav files and measured frame durations.
  Build log says `TTS source: voicevox`.
- Without VOICEVOX: `map-project.mjs` estimates frames from character count
  (`estimate_cps`, adjusted by playback_rate, 24-frame floor) and writes
  silent placeholder wavs so every `<Audio>` element resolves. Build log says
  `TTS source: estimate`. The two sources are never mixed in one project.

## Capabilities and limits

- Supported: text cards, image visuals, per-line sound effects, emotions,
  left/right characters, arbitrary character ids (the engine port is
  data-driven; upstream hardcoded two).
- Not supported by this vendor: background music (engine keeps it off),
  positions other than left/right, scene ids above 3 fall back to a default
  background. Errors, never silent drops: unknown settings keys, unknown
  `vendor.remotion` keys, unknown characters, missing asset files.

## Port changes vs upstream (nyanko3141592/remotion-voicevox-template)

- Characters are data-driven: `sync-script.ts` emits `CHARACTERS` +
  `characterColors` from characters.yaml; `Main.tsx` maps over them;
  `Character.tsx`/`Subtitle.tsx` no longer hardcode zundamon/metan.
- `Root.tsx`/`Main.tsx` read resolution, fps and playbackRate from
  `settings.generated.ts` (canonical settings apply) instead of static
  `config.ts` values. Root also applies the per-line playback-rate
  adjustment when summing total frames (upstream summed raw frames, which
  left an empty tail at rate > 1) and drops the unused opening buffer
  since the first line starts at frame 0.
- `generate-voices.ts` reads speaker ids from characters.yaml and fps/rate
  from video-settings.yaml; wav duration is parsed in node (upstream shelled
  out to python3); unknown characters throw instead of being skipped.
- `Subtitle.tsx` wraps CJK lines with BudouX and other scripts with normal
  word wrap plus `text-wrap: balance` and `overflow-wrap: anywhere`, so
  Latin-script subtitles center and wrap instead of overflowing right.
  Font size never auto-shrinks; lines over ~84 visible chars (2-line
  standard, ~42/line) warn at build time via map-project.

## Environment

- Node 24, npm. A fresh clone needs a one-time `npm install` inside
  `engine/` (the build symlinks that node_modules into its workdir).
- `ffprobe` on PATH for the duration guard (skipped with a warning when
  absent).
- VOICEVOX engine at localhost:50021 optional; see timing section.
