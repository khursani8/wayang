# Wayang

Fill one YAML file, get a narrated video: mascots, voices, subtitles,
music, themed backgrounds. Two render engines behind one contract.

- Templates by format: `dialog` (two hosts), `presentation` (one
  presenter, big cards), `storytelling` (narrative + emotions),
  `community` (announcements), `tutorial` (terminal walkthroughs),
  `shorts` (native vertical 1080x1920).
- Mascots: Momo the tapir and Kiki the hornbill, lip-synced from the
  voice audio frame by frame. Rimau the tiger shows how to add your own
  character (`docs/mascot-art.md`).
- Voices: Revolab (default) or OpenAI, one wav per line, cached per line
  text so rerenders only spend on changed lines.
- Backgrounds: 11 synthesized themes (chalkboard, batik, night-sky,
  studio, kraft-paper, ...) or your own PNG.
- Verticals: `wayang shorts-render --rerender` renders shorts natively
  from the `shorts` template. No crops.

## Install

    uv tool install git+https://github.com/khursani8/wayang
    wayang setup        # one-time: deploys render engines to ~/.wayang
    wayang doctor       # verifies the environment

Requires Node 24+ (rendering), uv, and ffmpeg/ffprobe. From a repo
clone, prefix every command with `uv run tools/` instead
(`uv run tools/wayang.py templates`).

## Use with an AI agent

Wayang was built to be driven by an agent. The repo ships `AGENTS.md`,
a manual any coding agent (Claude Code, Cursor, ...) can follow — point
your agent at the repo and give it one line:

    Make a 30-second community announcement about our Merdeka sale in
    Bahasa Malaysia. Voice: Momo. Render it and cut a vertical short
    of the hook.

The agent runs the loop itself:

    wayang init community merdeka        # scaffold from the template
    wayang check projects/merdeka        # plain-words list of what to fill
    # agent edits projects/merdeka/project.yaml
    wayang validate projects/merdeka     # strict gate
    wayang render projects/merdeka       # voices, video, guards, lint
    wayang shorts-sample projects/merdeka
    wayang shorts-render projects/merdeka --rerender

Keep instructions short and let the tool talk back. A good instruction
names five things and nothing more: template, length, language, voice,
message. `check` prints the gaps in plain words, the render log names
the audio source, and the lint fails loudly if anything is missing from
the final picture — so the agent self-corrects without you in the loop.
Iterating is cheap: edit one line of the YAML and render again; cached
voices and segment caching make small changes fast.

## Quickstart

    wayang templates
    wayang init tutorial my-video
    # edit projects/my-video/project.yaml (characters, script, settings)
    wayang check projects/my-video      # what to fill, in plain words
    wayang render projects/my-video     # add REVOLAB_API_KEY for real voices

Output: `projects/my-video/out/video.mp4`. Extras: `wayang captions`
(srt + vtt), `wayang chapters` (YouTube chapter stamps),
`wayang sheet` (contact sheet), `wayang voices` (audition the catalog),
`wayang init --wizard` (answers in, project.yaml out).

## Shorts

    wayang shorts-sample projects/my-video
    # an agent session reads shorts/brief and writes shorts/plan.yaml
    wayang shorts-render projects/my-video --rerender

Windows and titles come from the plan; the picture comes from a native
1080x1920 render dressed in the `shorts` template. See
`docs/shorts.md`.

## TTS

The repo owns no services. Voices are API clients configured per
character: `revolab` (REVOLAB_API_KEY) or `openai` (OPENAI_API_KEY).
Without a key, renders fall back to estimated timing with silent audio,
labeled in the log. New providers: a class in
`src/wayang/tts_providers.py` plus the schema enum.

## Series

    wayang init-series my-series --template dialog

`series.yaml` is the shared base; episodes deep-merge it (episode wins
per key). `wayang render projects/my-series` renders every episode in
order.

## How a render runs

The project validates against `schema/project.schema.json`, voices come
from cache, the vendor's `build.sh` renders, then two guards run on the
real output: a duration guard (rendered length vs the computed timeline)
and a visibility lint (frames probed per line: subtitle present,
character present, voice audible, mouth actually moving). Details:
`AGENTS.md` (agent manual), `docs/tutorial.md` (beginners),
`docs/project-yaml.md` (YAML reference), `docs/vendor-contract.md`
(join as an engine).
