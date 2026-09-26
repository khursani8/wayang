# How the mascot art is made, and how to make your own

The shipped characters (Momo the tapir, Kiki the hornbill) are NOT made by
an image model. They are drawn as SVG vector shapes by a Python script and
rendered to PNG.

## How the defaults exist

- Generator: `assets/mascots/generate_mascots.py`
- Sources: `assets/mascots/momo_open.svg`, `momo_close.svg`, `kiki_open.svg`,
  `kiki_close.svg`
- Renderer: cairosvg (Python), 1024x1024 PNG output

Each character is one SVG template. The open and close variants share
everything except the mouth group, so the two frames of a lip flap are
pixel-identical outside the mouth. That guarantee is why the code approach
was chosen: an image model cannot promise it.

Regenerate after editing:

    uv run --with cairosvg --with pillow assets/mascots/generate_mascots.py

The script self-checks: transparent corners, mouth-only pixel diff between
pairs, margins and centering.

## Make your own character with the generator

1. Copy a character section in `generate_mascots.py` and reshape the SVG
   (body, colors, eyes). Keep the mouth group swappable.
2. Render, then place the PNGs in your project:
   `assets/images/<character_id>/mouth_open.png` and `mouth_close.png`
3. Set `settings.character.use_images: true` in project.yaml.

Optional emotion art uses the same naming: `<emotion>_open.png`,
`<emotion>_close.png` (happy, surprised, thinking, sad).

## Using an image model instead (gpt-image-2, Qwen Image, Higgsfield, ...)

You can, and it usually looks richer. The trade-off: image models generate
a new picture every time, so two separate generations never align. The lip
flap needs the two frames identical except the mouth.

Workflow that works:

1. Generate ONE base character, front-facing, full body, plain background:
   "chibi malayan tapir mascot, full body, standing, facing viewer, flat
   vector style, thick outlines, transparent background"
2. Get the closed-mouth look: inpaint/edit the mouth area only ("close the
   mouth"), or generate the open-mouth image and edit it to closed. One
   edit pass, not a second generation.
3. Export both states at the same size (1024x1024 is fine) as
   `mouth_open.png` and `mouth_close.png`.
4. Optional emotion variants: inpaint the face per emotion, always from
   the same base frame.
5. Drop the files into `assets/images/<character_id>/` and set
   `use_images: true`.

Requirements the renderer enforces: PNG, same canvas size for every frame
of a character, file names exactly `mouth_open.png` / `mouth_close.png`,
art facing the viewer (or set `flip_x: true`).

## Backgrounds

Same story: `assets/background/` generates the theme PNGs as SVG (deterministic,
self-checked). Edit the shapes or add a theme there; drop a custom
`assets/background.png` into a project for a one-off.
