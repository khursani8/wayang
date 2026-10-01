# Step 4: Deliver

Render through the gates and assemble the timestamped delivery directory.

## Render (gates run inside)

    wayang render projects/promo-<slug>-<tone>

render runs the duration guard (0.5s tolerance), the visibility lint, and the mouth gate. Exit 0 and every lint line green.

Without a TTS key the render is an estimate render: the log labels the voice check as skipped and the mouth gate uses the clock fallback. That is the documented estimate path, exit 0.

## Captions and chapters

    wayang captions projects/promo-<slug>-<tone>
    wayang chapters projects/promo-<slug>-<tone>

## Assemble the delivery directory

    out=projects/promo-<slug>-<tone>/out
    cp "$out/video.mp4" "$DELIVERY/promo.mp4"
    cp "$out/captions.srt" "$out/captions.vtt" "$out/chapters.txt" "$DELIVERY/"
    cp projects/promo-<slug>-<tone>/project.yaml "$DELIVERY/project.yaml"

## Share copy

Write share-copy.md in the delivery directory: one to three sentences, one Bahasa Malaysia sentence and one English sentence, plus the tagline. Share copy follows the word bans and uses the target repo's real name.

## Final verification

    ls -la "$DELIVERY"
    ffprobe -v error -show_entries format=duration -of csv=p=0 "$DELIVERY/promo.mp4"
    grep -inE '(fail|pypi|kontak)' "$DELIVERY/captions.srt" "$DELIVERY/captions.vtt" && echo BAN-HIT || echo clean

Compare the ffprobe duration against out/expected-seconds.txt, within 0.5s.

## Gate

The delivery directory contains promo.mp4, captions.srt, captions.vtt, chapters.txt, share-copy.md, promo-plan.md, project.yaml. All gates exit 0.
