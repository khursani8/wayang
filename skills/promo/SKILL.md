---
name: promo
description: Turn any target repository into a finished Wayang promo video. Use when someone says "make a promo", "promote this repo", "promo video for this project", or wants to share what they built with the world. Reads the target repo directly, picks a Wayang tone preset, and drives the wayang CLI end to end - init, check, validate, tts, render, captions, chapters, share copy.
---

# /promo

You built something. Wayang turns it into a promo video with Momo and Kiki.

## What this skill does

1. Inspects the target repository to learn what it is and what it claims.
2. Plans the promo - angle, hook, storyboard, script in Bahasa Malaysia.
3. Composes a Wayang project from the plan (tone preset picks casting, background theme, pacing).
4. Delivers a rendered video through the wayang gates, into a timestamped directory with captions, chapters, and share copy.

## Parsing the invocation

| Option | Values | Default |
|---|---|---|
| `--tone` | preset name or freeform direction | inferred in step 2 |
| `--target` | path to the repo to promote | current repo |
| `--format` | `landscape`, `portrait`, `square` | `portrait` |
| `--title` | string | inferred from the target |

Tone can be a preset (`santai`, `sinematik`, `lasak`, `kedai-kopi`, `komersial`) or a freeform direction such as "macam iklan raya". When the user gives freeform direction, map it to the nearest preset for casting, background, and pacing, and preserve their wording in the plan.

## Output directory

Generate a timestamp `YYYYMMDD-HHmmss` at the start of the run. Delivery goes to `promo-output/<timestamp>-<tone>/` at the repo root. Every artifact of the run - plan, rendered video, captions, chapters, share copy - lives in that one directory. A second run never overwrites a first.

## Owner rules (non-negotiable, checked at every stage)

1. **Word bans.** The tokens `fail`, `pypi`, `kontak` never appear in video content: no script line, no display_text, no visual text, no captions, no translations. Pre-check the plan with grep before composing, and re-check the exported captions after rendering.
2. **Audio + 1s pacing.** Every script line carries `pause_after: 1.0`. Scene time is talk time plus one second. No other pause values.
3. **Framed embeds.** Image and video embeds stay as framed cards. The engine frames visual cards by default. Do not work around the framing.
4. **Mouth gate.** `settings.character.use_images: true` on every promo so the mascots render as art and the mouth check can run. Do not render placeholder boxes.

## Gates

Every stage ends in a gate. A gate that fails stops the run until it passes.

| Stage | Command | Gate |
|---|---|---|
| compose | `wayang check projects/<name>` | every FILL item resolved |
| compose | `wayang validate projects/<name>` | exit 0 |
| compose | `wayang tts projects/<name>` | exit 0 (estimate mode is fine, it says so in the log) |
| deliver | `wayang render projects/<name>` | exit 0 - this runs the duration guard (0.5s tolerance), the visibility lint, and the mouth gate |
| deliver | `wayang captions projects/<name>` then `wayang chapters projects/<name>` | files written |
| deliver | ban grep on `out/captions.srt` | no hit on `fail`, `pypi`, `kontak` |

## Step 1: Inspect the target

**Read:** [references/step-1-inspect.md](references/step-1-inspect.md)

Gate: all 8 rubric questions answered in writing.

## Step 2: Plan the promo

**Read:** [references/step-2-plan.md](references/step-2-plan.md)

Gate: `<delivery-dir>/promo-plan.md` exists with the full script and storyboard, and the word-ban grep is clean.

## Step 3: Compose the Wayang project

**Read:** [references/step-3-compose.md](references/step-3-compose.md)

Gate: `wayang validate` exit 0 and `wayang tts` exit 0.

## Step 4: Deliver

**Read:** [references/step-4-deliver.md](references/step-4-deliver.md)

Gate: rendered promo, captions, chapters, and share copy all inside the timestamped delivery directory.

## Tone system

Five tone presets ship with /promo. Each one fixes casting, background theme, pacing, and script energy. Presets are defaults, not limits.

Full definitions: [references/tones.md](references/tones.md)

| Tone | Casting | Background | One-liner |
|---|---|---|---|
| `santai` | Momo solo | studio | Warm, friendly, postable |
| `sinematik` | Momo + Kiki duo | night-sky | Trailer-scale, short epic sentences |
| `lasak` | Duo, rapid fire | batik | Fast, loud, hype reel |
| `kedai-kopi` | Kiki solo | kraft-paper | Dry, understated, quiet joke |
| `komersial` | Momo solo | whiteboard | Clean, feature-card, corporate but not boring |

Always allow a freeform direction to refine or override the preset.

## Creative laws

These apply to every promo regardless of tone.

**Short.** 6 to 9 script lines. Roughly 30 to 60 seconds rendered. Not one line more without a reason.

**Specific.** The promo must feel made for this exact repository. Use its real name, its real commands, its real claims. No generic developer-tool language.

**Show the thing.** At least one text card shows a real artifact from the repo: an actual command, an actual YAML key, an actual number. No abstract filler.

**The hook is everything.** The first line decides whether anyone keeps watching. Plan the hook before anything else.

**Bahasa Malaysia first.** Script lines are written in BM. English translations go in `translations.en` so the subtitle system can carry both.

**Readable subtitles.** Every line holds for its talk time plus one second. That is the pacing rule; it is also what keeps the promo watchable.
