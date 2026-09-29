# Tutorial — your first Wayang video

This walkthrough follows a real run: adding a brand-new character
(Rimau the tiger) and rendering his intro. By the end you will have an
MP4 with voices, subtitles, and a character on screen.

## What you need

- Node 24+, uv, ffmpeg/ffprobe on PATH
- This repo cloned, and `npm install` run once inside
  `vendors/remotion/engine/`
- Optional: a `REVOLAB_API_KEY` for real voices. Without it everything
  still renders, with silent audio and estimated timing (labeled in the
  build log).

All commands run from the repo root.

## 1. Pick a template

    uv run tools/wayang.py templates

Formats: `dialog` (two hosts banter), `presentation` (one presenter with
big cards), `storytelling` (narrative + emotions), `community`
(announcements). Every template renders as-is before you change a thing.

## 2. Create your project

    uv run tools/wayang.py init presentation rimau-intro

This copies the template into `projects/rimau-intro/` (gitignored - this
folder is yours). `project.yaml` is the whole video: title, characters,
script, settings.

## 3. Ask what is missing

    uv run tools/wayang.py check projects/rimau-intro

The preflight speaks plain words. `FILL:` lines are things to fix; `NOTE:`
lines are advice (for example, "no Revolab key - renders stay silent
until you set it"). The exit code tells agents the same thing: 0 ready,
1 blockers, 2 notes only.

## 4. Fill the parts that are yours

Open `projects/rimau-intro/project.yaml`. Three things matter:

1. `meta.title` - your video's name.
2. `characters` - each one needs a name and a voice:

       rimau:
         name: Rimau
         color: "#F57C00"
         position: right
         voice:
           engine: revolab
           voice_id: ali-13002bfa

   Voice ids come from your TTS provider (Revolab lists them at
   GET /v1/voices; OpenAI voices are alloy, nova, ...).

3. `script` - one block per spoken line:

       - id: 3
         character: rimau
         text: "Tengok! Saya boleh terkejut!"
         scene: 2
         pause_after: 1.0
         emotion: surprised
         visual:
           type: text
           text: "Terkejut!"
           font_size: 84
           color: "#ffffff"
           animation: bounce

   `text` is what gets spoken. `emotion` changes the character art (when
   emotion art exists). `visual` draws a big card while the line plays.

Run `check` again until it says READY.

## 5. Validate

    uv run tools/wayang.py validate projects/rimau-intro

This is the strict gate: schema plus references (speakers exist, assets
exist, theme exists). No output means it passed.

## 6. Render

    REVOLAB_API_KEY=... uv run tools/wayang.py render projects/rimau-intro

One command does everything: generates one voice wav per line (cached in
`voices/`, reused next time), maps your YAML to the engine, renders, and
then lints the result - frames are checked so a subtitle, card, or
character that failed to appear fails the build instead of shipping.

Your video: `projects/rimau-intro/out/video.mp4`.

## 7. Give your character art (optional but fun)

Without art, characters show as colored placeholder boxes. To add real
art, put PNGs in your project:

    assets/images/<character_id>/mouth_open.png
    assets/images/<character_id>/mouth_close.png

and set `settings.character.use_images: true`. With real voices the mouth
opens during speech (a lipsync schedule is computed from each line's wav at
render time) and closes in the pauses; estimate/draft renders fall back to
a fixed 0.2s alternation. Emotion art uses
`<emotion>_open.png` / `<emotion>_close.png`.

Two ways to make the art:

- Code (how the shipped mascots were made): edit
  `assets/mascots/generate_mascots.py` - SVG shapes rendered to PNG.
  See `docs/mascot-art.md`.
- Image models (gpt-image-2, Qwen, Higgsfield, ...): generate ONE base
  character, then edit only the mouth for the second frame. Both frames
  must be the same size and identical outside the mouth.

## When something fails

| message | meaning | fix |
|---|---|---|
| `FILL: character 'x' has no voice.engine` | character cannot speak | add a voice block |
| `renders stay silent with estimated timing` | no TTS key | set the key, or accept a silent preview |
| `render is shorter than the computed timeline` | internal timing drift | re-render; if it repeats, file an issue |
| `unknown theme 'x'` | typo in settings.background | pick from the listed catalog |

## Where to go next

- Background themes: `settings.background` - see
  `vendors/<engine>/assets/backgrounds/` or docs/mascot-art.md for making
  your own.
- Sound effects and image cards: `se:` and `visual.type: image` on a
  script line (see `projects/` demos or the hyperframes vendor manual).
- Series: `uv run tools/wayang.py init-series my-series --template dialog`
- Agents: point them at the root `AGENTS.md` - it routes everything.
