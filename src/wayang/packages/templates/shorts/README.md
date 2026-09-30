# shorts template

Vertical-first 1080x1920 for YouTube Shorts. Not a reflowed landscape
frame: the composition stacks top to bottom.

Layout language (hyperframes portrait branch, driven by these settings):

- Hook and payoff text cards sit in the upper third (`8%..40%` height,
  `8%` side margins) so the first frame reads as a short.
- Subtitles sit in the lower third: `font.size 72`, `max_width_percent 86`
  (>= 40px side margins at 1080 wide), lifted above the mascot by the
  mapper's overlap rule.
- The mascot occupies a mid-lower corner slot (`character.height 380`,
  56px inset in portrait), clear of the subtitle band.
- Terminal cards render narrow and stacked mid-frame (88% width, larger
  type in portrait).
- Video-in-video embeds always carry a frame (white border, rounded
  corners, shadow). `visual.frame: false` is only for full-bleed embeds.

Use it two ways:

1. Native vertical project: `wayang init shorts <name>`, fill the script,
   `wayang tts`, `wayang render`. The plan windows then trim directly.
2. Vertical shorts from any landscape project: `wayang shorts-sample`,
   author `shorts/plan.yaml`, then
   `wayang shorts-render <project> --rerender`. The portrait master under
   `shorts/portrait-master/` re-renders the parent's script, voices and
   timing through this template's settings, then the plan windows are
   trimmed natively (crop boxes ignored).

Keep lines short: two subtitle lines max, `pause_after: 1.0`.
