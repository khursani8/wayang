# Shorts

Vertical 1080x1920 clips from a rendered project. Shorts are re-rendered
natively from the dedicated `shorts` template — the picture is never
cropped out of the landscape master.

## Pipeline

    wayang shorts-sample <project>             # 1. sample -> brief dir
    <agent session reads the brief>            # 2. analysis (agent, not CLI)
    <agent writes shorts/plan.yaml>            # 3. clip windows + titles
    wayang shorts-render <project> --rerender  # 4. native render + verify

## 1. shorts-sample

    wayang shorts-sample projects/my-video --frames 12 --bin 1.0 \
        --window 5.0 --stride 1.0

Writes `<project>/shorts/brief/`:

    meta.json             video path, duration, size, fps, sample rate
    audio-curve.json      RMS dB per bin (asetnsamples+astats, silence = -99)
    window-scores.json    every window scored, sorted best first (see below)
    frames/frame-N.jpg    evenly spaced 640px jpgs (timestamped in meta order)

Resumable: existing non-empty frames are reused.

### Highlight score

`window-scores.json` carries a 0-10 score per sliding window (default 5s,
stride 1s, tune with `--window` / `--stride`):

    score = 10 * (0.40 * loudness + 0.30 * speech density + 0.30 * exclamations)

- loudness: window peak RMS dB mapped from -40 dB (0) to -20 dB (1)
- speech density: fraction of audio bins above -45 dB
- exclamations: `!` and `?` marks in the script lines covering the window,
  per second, saturated at 0.5/s

Script line windows come from `out/timeline.json` when the sampled video is
that project's render (exact), otherwise from the voices manifest or a cps
estimate (approximate; `script_source` in the file says which).

## 2. Analysis session (agent)

Rank candidate windows by `window-scores.json` first: the score is the
brief's systematic ranking (loudness peaks, speech density, script
exclamations). Then apply judgment: snap boundaries to speech gaps in the
audio curve and the timeline, watch the frames for visual hooks, write
titles. The score ranks the candidates; the frames and the timeline decide
the exact cut.

Read the brief: every frame, the audio curve, the window scores, plus
out/timeline.json when the source is a Wayang render (exact per-line speech
windows). Write `<project>/shorts/plan.yaml`:

    source: /abs/path/to/video.mp4
    mode: rerender
    clips:
      - id: intro-hook
        title: "Satu YAML, satu video penuh!"
        start: 0.0
        end: 5.1
        render: {width: 1080, height: 1920}

Validation (shorts-render rejects the plan otherwise): window inside the
source, title non-empty, render size positive and even. `crop` is
optional and ignored in rerender mode (still required for the legacy
crop path).

## 3. shorts-render --rerender

Builds `shorts/portrait-master/`: the parent's script text, line ids,
characters, voices, and timing stay verbatim; the layout comes from the
`shorts` template (hook cards upper third, large subtitle zone, vertical
character slot). The master renders through the project's vendor (cached
voices, no TTS spend), then each plan window is trimmed into
`<project>/shorts/clips/<id>/clip.mp4` and verified with real probes:
ffprobe dimensions + duration (0.5s tolerance) and frame extracts at
10% / 50% / 90%. Results live in each clip dir as verify.json (with
`"mode": "rerender"` and the master path) + probe-*.png. Verified clips
are cached; `--force` re-renders; `--clip <id>` limits the run.

The lint on the master carries the same gates as any render, including
the mouth gate (lip sync) and the subtitle band check.

### Per-speaker subtitles

Multi-character projects can style each speaker's primary subtitle:
`settings.subtitle.per_character` maps a character id to `{color,
font_size}` (falls back to the global font color when a speaker has no
entry). The declared subtitle band covers the largest configured size.

### Produced layout variants

`settings.layout.variant: two-panel` (portrait only) produces a
two-panel vertical: the full scene (background, visual card, terminal,
embed, subtitle, corner art) renders in the top panel; below it a dark
panel carries the meta.title as a title card plus a close-up of the
speaking character, enlarged, with the same lip-sync schedule as the
corner art. timeline.json declares the panel geometry under
`layout.panels` for probing.

## Embeds

A script line with `visual: {type: video, src: ...}` shows real footage
inside the render as a framed card (border, rounded corners, shadow) —
video-in-video is always framed, never a floating inset. The embed box
is declared in timeline.json and probed by the lint.

## Legacy crop path

`shorts-render` without `--rerender` cuts the plan windows out of the
landscape master through `crop: [x0, y0, x1, y1]` boxes. A 9:16 crop
from 1080p is at most 608px wide: wide cards and the subtitle band clip
at the edges. Kept for old plans; new plans should use `--rerender`.
