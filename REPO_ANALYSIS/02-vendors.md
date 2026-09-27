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
