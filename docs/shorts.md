# Shorts suggester

Turn one rendered landscape video into vertical shorts: sample it into a
brief, let an agent session pick moments, cut the clips.

## Pipeline

    wayang shorts-sample <project>          # 1. sample -> brief dir
    <agent session reads the brief>         # 2. analysis (agent, not CLI)
    <agent writes shorts/plan.yaml>         #    clip windows, crops, titles
    wayang shorts-render <project>          # 3. cut + verify clips

## 1. shorts-sample

    wayang shorts-sample projects/my-video --frames 12 --bin 1.0

Writes `<project>/shorts/brief/`:

    meta.json           video path, duration, size, fps, sample rate
    audio-curve.json    RMS dB per bin (asetnsamples+astats, silence = -99)
    frames/frame-N.jpg  evenly spaced 640px jpgs (timestamped in meta order)

Resumable: existing non-empty frames are reused.

## 2. Analysis session (agent)

Read the brief: every frame, the audio curve, plus out/timeline.json when
the source is a Wayang render (exact per-line speech windows). Write
`<project>/shorts/plan.yaml`:

    source: /abs/path/to/video.mp4
    clips:
      - id: intro-hook
        title: "Dari kosong ke video siap!"
        start: 0.0
        end: 5.146
        crop: [x0, y0, x1, y1]     # portrait box in source pixels
        render: {width: 1080, height: 1920}

Validation (shorts-render rejects the plan otherwise): window inside the
source, crop inside the frame and portrait (height > width), title
non-empty, render size positive and even.

## 3. shorts-render

    wayang shorts-render projects/my-video [--clip intro-hook] [--force]

Cuts each clip (crop -> scale -> libx264 + aac, faststart) into
`<project>/shorts/clips/<id>/clip.mp4` and verifies every render with
real probes on disk: ffprobe dimensions + duration (0.5s tolerance) and
frame extracts at 10% / 50% / 90% of the clip. Results live in each
clip dir as verify.json + probe-*.png. Verified clips are cached;
`--force` re-renders.

## Crop geometry note

A 9:16 crop from 1080p is at most 608px wide. Wide center cards and the
1056px subtitle band clip at the edges; content parked in the frame
corners (mascots) cannot share the window with centered content. Plan
crops around the dominant element, or render the source portrait-first.
