# Step 3: Compose the Wayang project

Author the Wayang project.yaml from the plan. Scaffold, fill, then gates in order.

## Scaffold

    cd <wayang repo root>
    wayang init presentation promo-<slug>-<tone>

The project dir must not exist before init. The scaffold copies mascot PNG frames for all characters into assets/images/.

## Fill project.yaml

Replace the scaffolded project.yaml with the plan: meta (title, template presentation, vendor hyperframes, language ms), characters per the tone preset, script from the storyboard, settings per the preset (background theme, video size per the format, character.use_images true, subtitle.secondary_language en). Every script line carries pause_after: 1.0.

Before writing YAML read the real references. docs/project-yaml.md and schema/project.schema.json are canonical. templates/presentation/template.yaml is a valid working example. projects/duo-demo/project.yaml is a valid duo example with per-character subtitle colors.

Unknown keys error. Nothing is dropped silently.

## Gates in order

    wayang check projects/promo-<slug>-<tone>
    wayang validate projects/promo-<slug>-<tone>
    wayang tts projects/promo-<slug>-<tone>

check reports FILL items in plain words. All resolved before continuing. validate is the strict gate, exit 0. tts exits 0. Without REVOLAB_API_KEY the tts log labels the render as estimate; that is the documented path. With a key it writes real wavs under voices/.

## Ban check

    grep -inE '(fail|pypi|kontak)' projects/promo-<slug>-<tone>/project.yaml && echo BAN-HIT || echo clean

If it hits, fix the YAML, re-validate, re-run the grep.

## What green looks like

check: no FILL items left. validate: exit 0. tts: exit 0 with the mode labeled in the log.
