# vendors/hyperframes — engine manual (AGENTS.md)

HyperFrames vendor for Wayang: HTML/CSS compositions rendered
deterministically by the HyperFrames CLI. The shared interface is
docs/vendor-contract.md; this file holds hyperframes-specific deltas only.

## How the engine works

- A composition is one `index.html`: a root element with
  `data-composition-id`, `data-width`, `data-height`, `data-duration`
  (total seconds), and timed children with `class="clip"`, `data-start`,
  `data-duration` (seconds). The producer injects the HyperFrames runtime;
  GSAP loads from a pinned CDN only to register an empty timeline.
- Rendering is deterministic: no wall clock, no unseeded randomness, all
  assets local before frame 0. `npx hyperframes render` (bundled Puppeteer
  Chromium + system ffmpeg) captures frame by frame.
- Requirements: Node 22+, ffmpeg, network for the first `npx` download and
  the Chromium fetch.

## Entry point

    vendors/hyperframes/build.sh PROJECT_DIR OUT_DIR

Workdir: `vendors/hyperframes/.work/<project>/` (fresh each run).
Input: `.merged.yaml` when the platform materialized series inheritance,
else `project.yaml`.

## Canonical -> engine mapping

| canonical | composition | note |
|---|---|---|
| meta.language | - | informational |
| characters.<id>.name/color/position | placeholder box or art position | left or right |
| characters.<id>.voice | platform-generated voices/<NN>_<id>.wav | see timing |
| script[].text / display_text | subtitle div per line | outlined, bottom-centered, wraps at word boundaries |
| script[].scene | - | scenes are not a concept here; visuals play per line |
| script[].pause_after | subtitle/card tail | seconds, natural speed |
| script[].emotion | - | needs emotion art variants; otherwise invisible |
| script[].visual.type text | centered text card per line | dark outline by default, override with outline_color |
| script[].visual.type image | centered image card | src relative to the project; asset ships in the project |
| script[].se | per-line audio clip | src relative to the project; duration probed; data-volume honored |
| settings.background | background.png | theme from the shared catalog, riverbank default; project custom file wins |
| settings.font / subtitle / character | css | font, subtitle placement, character height, use_images |
| vendor.hyperframes.estimate_cps | timing estimate | chars per second, default 7.5 |

## Timing and audio honesty

Priority order for line audio: (1) platform-generated voices in
`PROJECT_DIR/voices/` with a manifest covering every line - real wav
playback, durations from the manifest, build log names the engines;
(2) estimate from character count (`estimate_cps`), silent. Never mixed.
`playback_rate` is ignored by this vendor (audio plays at natural speed).

Lip flap: while a character speaks, mouth_open/mouth_close art alternates
every 0.2s (needs `settings.character.use_images: true` and art under
`assets/images/<id>/`); placeholder boxes do not flap.

## Duration guard

`expected-seconds.txt` records the computed timeline (sum of line audio
and pauses plus a 2s tail). build.sh ffprobes the render and fails on
more than 0.5s deviation - the same regression guard as the remotion
vendor.

## Environment

- Node 22+, ffmpeg, network. First run downloads the hyperframes CLI via
  npx and Chromium for the capture browser.
