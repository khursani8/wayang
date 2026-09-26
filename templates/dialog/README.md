# dialog template
Two hosts in Q&A banter: one asks, one explains. Short lines, 2-3
scenes, big text cards at key moments.
walk through a topic in 2-3 scenes with big text cards.

Fill order:
1. `characters`: rename ids, set `name`, `color`, `position`, and VOICEVOX
   `speaker_id` per character.
2. `script`: one entry per spoken line. `text` is spoken, `display_text`
   overrides the subtitle text. `scene` groups lines, `visual` draws a big
   text card for that line.
3. `settings`: keep defaults unless you need other resolution or pacing.

Character art (optional): put PNGs under `assets/images/<character_id>/`
(`mouth_open.png`, `mouth_close.png`, optional `<emotion>_open.png`), copy
`flip_x: true` if the art faces the wrong way, and set
`settings.character.use_images: true`.
