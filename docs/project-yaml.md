# Canonical project.yaml

One file per video. Full schema: `schema/project.schema.json`. Timing in
seconds everywhere; vendors convert to their own units.

## Sections

- `meta`: title (required), template, vendor, language, series, episode.
- `characters`: id -> {name, voice{engine,...}, color, position, flip_x}.
  Voice engines: revolab (voice_id), openai (voice, model, speed,
  instructions). Unknown keys error.
- `script`: ordered lines. text (spoken), display_text (subtitle
  override), scene, pause_after (seconds), emotion, visual (text/image/video card; video shows real footage as a framed inset), se.
- `settings`: video (width, height, fps, playback_rate - slows voice and
  pacing; 0.9 is a good tutorial pace), font, subtitle,
  character, content, background (theme name from assets/backgrounds/ or a
  project assets/background.png override).

## What you must fill

Start from a template (`wayang init`) - everything else is optional but
sensible defaults exist. The parts that are yours:

1. `meta.title`.
2. Per character: name and voice (revolab voice_id, or openai voice).
3. The script lines (text, speaker, pauses, optional visual cards).

`wayang check projects/<name>` reports every gap in plain words before you
render. `wayang validate` is the strict gate.

## Series

`wayang init-series my-series --template dialog` creates
`projects/<series>/series.yaml` (shared characters and settings) plus the
first episode. Episodes deep-merge the series file under their own project
(the episode wins per key); `render projects/<series>` renders every
episode in order.
