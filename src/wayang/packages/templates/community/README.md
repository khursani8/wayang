# community template
Casual announcement format for community posts: two hosts, big text
cards, short lines. Same fill order as the dialog template.
walk through a topic in 2-3 scenes with big text cards.

Fill order:
1. `characters`: rename ids, set `name`, `color`, `position`, and a
   `voice` (for example `engine: revolab` plus a `voice_id`).
2. `script`: one entry per spoken line. `text` is spoken, `display_text`
   overrides the subtitle text. `scene` groups lines, `visual` draws a big
   text card for that line.
3. `settings`: keep defaults unless you need other resolution or pacing.

Character art (optional): put PNGs under `assets/images/<character_id>/`
(`mouth_open.png`, `mouth_close.png`, optional `<emotion>_open.png`), copy
`flip_x: true` if the art faces the wrong way, and set
`settings.character.use_images: true`.
