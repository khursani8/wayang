# 04 - History and decisions

Reference for the owner. Covers the full commit chronology, the rumpun
campaign state and directives, the two multi-model consults, the bug
classes fixed along the way, the rename, and what is deliberately kept
out of git.

Sources: `git log` (38 commits, one branch `main`, remote
`https://github.com/khursani8/wayang.git`), `.rumpun/` (rumpun.yaml,
seasons/s1.yaml, ledger/directives.jsonl, prompts/base/, runs/), README.md,
AGENTS.md. Note: `.rumpun/runs/` is gitignored, so the raw review
documents exist only on disk. The adopted decisions survive in git through
the ledger and commit 5ecfebc.

## Build timeline in one paragraph

The repo was built in one day: 38 commits between 11:52:40 and 23:47:25
(+0800) on 2026-09-26, all authored `sani <sani@local>`, all on `main`,
no branches, no merges, no reverts. The work ran as a rumpun campaign
(season s1) with a written operator directive and an append-only ledger.
The arc: MVP with a ported engine, pluggable TTS, series support,
original mascots and Malay identity, rendering correctness guards, a
second engine, a two-model structure review and restructure, the rename
to Wayang, then beginner onboarding (tutorial doc, tutorial template,
final lint hardening).

## Commit chronology

Times are +0800, 2026-09-26. Oldest first.

### Phase 1 - MVP and TTS (11:52-12:14)

| hash | time | what it delivered |
|---|---|---|
| dafeabf | 11:52 | content_engine MVP: `schema/project.schema.json` (canonical YAML, timing in seconds), `templates/education` + `templates/community`, `vendors/remotion` (patched port of nyanko3141592/remotion-voicevox-template with data-driven characters, `build.sh PROJECT_DIR OUT_DIR` contract, estimate TTS fallback), `tools/ce.py` (init/validate/render, uv PEP 723), the whole `.rumpun/` campaign state. E2E verified: both templates rendered to mp4 on estimate timing. |
| 2fd0e74 | 12:07 | Pluggable TTS: `tools/tts_providers.py` (voicevox + openai clients, stdlib only), `ce.py tts` command + auto-tts in render, per-line manifest (hash, seconds, engine), resumable, vendor consumes `projects/<p>/voices` when present. OpenAI path NOT verified against the live API (no key on the box, stated in the commit). |
| e38feb6 | 12:07 | gitignore `__pycache__` (a `.pyc` had leaked into 2fd0e74). |
| 3ed0923 | 12:12 | revolab TTS provider (`api.revolab.ai/v1/tts`, default model nada-1.0-pro, native wav 24 kHz), verified with real synthesis E2E: 6 live lines, community-test rendered with real audio. Recorded that `nada-1.0-flash` (from the operator's curl example) does not exist; valid models are nada-1.0-pro and aisyah-1.0-pro. |
| c64a503 | 12:14 | remotion mapper drops its voicevox-only voice gate. Engine validation is the platform's job (provider registry in ce.py); without this, revolab/openai projects could not render. |

### Phase 2 - Series, templates, mascots (12:33-13:11)

| hash | time | what it delivered |
|---|---|---|
| b340fee | 12:33 | Series support: `series.yaml` sparse base deep-merged under each episode (episode wins per key, dicts merge, lists replace), merge-then-validate, batch validate/tts/render in name order stopping at first failure, `init-series`, render materializes `.merged.yaml` so vendors never see series. Proven by a negative test: remove series.yaml and ep02 fails with required name/voice errors. |
| b8fa6f3 | 12:45 | Templates renamed by format, not topic: `education` -> `dialog`, added `presentation` (1 presenter + cards) and `storytelling` (hosts + emotions). All ran on the engine unchanged. |
| 34d5bc9 | 13:04 | Identity switch: dropped the upstream zundamon/metan pair. Original mascots Momo (tapir, revolab voice paan-f695215e) and Kiki (hornbill, nur-b184422b), Bahasa Malaysia sample scripts (`language: ms`), generated SVG-derived lip-flap art shipped per template, generator sources kept in `assets/mascots/`. |
| ddf97aa | 13:11 | Mascot art re-rendered with transparent backgrounds after operator feedback (solid rectangles looked wrong over the chalkboard). Generator now asserts corner alpha is zero and that open/close pairs differ only inside the mouth region. |
| 477ff3f | 13:11 | gitignore `.omc` state (session-state files had leaked, including under `assets/mascots/`). |

### Phase 3 - Rendering correctness (13:20-13:48)

| hash | time | what it delivered |
|---|---|---|
| dede006 | 13:20 | Subtitle wrapping: BudouX-JA wraps Japanese but emitted near-whole-line segments for Latin text, which then overflowed the centered container. CJK keeps BudouX, other scripts wrap at word boundaries, `text-wrap: balance`, `overflow-wrap: anywhere`, no auto-shrink, build-time warning past ~84 visible chars. Rules follow Netflix TTSG (~42 chars/line, max 2 lines). |
| 118fa17 | 13:31 | Empty-tail fix: `Root.tsx` summed raw frames while playback ran at `ceil(frames / playbackRate)`, so at rate 1.2 the composition ran ~17% longer than the timeline (3.7s of empty chalkboard on dialog-ms). Root now sums per-line adjusted frames plus one 60-frame closing buffer (the upstream 60-frame opening buffer was dead weight). 26.37s -> 20.67s, matching 620 computed frames. |
| 859f006 | 13:48 | Duration regression guard: mapper writes `expected-seconds.txt` (sum of per-line rate-adjusted frames + 60-frame tail), `build.sh` ffprobes the output and exits 1 on >0.5s deviation. Any repeat of the empty-tail bug class is now a loud build error. |

### Phase 4 - Backgrounds and polish (14:01-16:25)

| hash | time | what it delivered |
|---|---|---|
| 109e0fc | 14:01 | Chalkboard background as a generated 1920x1080 PNG (`assets/background/generate_background.py`, SVG + cairosvg, self-checked pixels), replacing flat divs in `Main.tsx`. Project can override with `assets/background.png`. |
| 5b83b25 | 14:47 | Theme system: `generate_themes.py` synthesizes 10 themes (whiteboard, night-sky, kraft-paper, batik, notebook, sunrise, studio, riverbank, slate, wood-table), catalog at `vendors/remotion/assets/backgrounds/`, `settings.background` resolves custom file > named theme > engine default, unknown themes error. |
| 3690719 | 14:54 | gitignore: untrack root `.omc/` session state (had been committed since dafeabf). |
| 44c926e | 14:57 | Text cards get a subtitle-style outline (`visual.outline_color`, stroke 0.16x font size) because flat white cards vanished on light themes like riverbank. |
| 888f0dd | 16:12 | README refresh for cloners: real state of the repo, fresh-clone install steps. |
| bf5fe5c | 16:25 | Engine default background becomes riverbank; chalkboard stays selectable. |

### Phase 5 - Identity purge (17:24-17:37)

| hash | time | what it delivered |
|---|---|---|
| 23f1b82 | 17:24 | All Japanese removed from the remotion engine: upstream ja sample wavs/art/configs deleted, engine configs rewritten to momo/kiki in Bahasa Malaysia, every Japanese comment and log line translated. "Malaysian repo, Malaysian content." |
| e9e709a | 17:37 | VOICEVOX removed as a TTS provider (provider class, schema branch, `generate-voices.ts` 230 lines, build branch, all doc mentions). TTS engines are revolab and openai only; keyless builds fall back to estimates. |

### Phase 6 - Second engine and the visibility lint (17:59-18:24)

| hash | time | what it delivered |
|---|---|---|
| 10748ba | 17:59 | hyperframes vendor, the second engine, onboarded with zero `ce.py` changes: `AGENTS.md` + `build.sh` + `map-project.mjs`, canonical YAML -> one `index.html` composition (data-* clips, seconds-based), lip flap as alternating 0.2s mouth clips, estimate fallback, explicit errors (never silent drops) for unsupported se/image visuals/scenes, same duration guard. |
| 1932e7c | 18:11 | HyperFrames authoring rules learned from the first broken render: media without a stable `id` renders silent, the runtime's full-frame `.clip` rule fills unset dimensions (once stretched Momo to 1920px wide), fonts need `@font-face` (mapper now downloads the Google font woff2 at map time). Added deterministic subtitle/character overlap detection. |
| b264afe | 18:12 | gitignore `vendors/*/.work/`: the hyperframes workdir (generated HTML, fonts, wavs, out.mp4) had been committed with 10748ba and 1932e7c when shells ran from the wrong cwd. Purged here. |
| 95bc2f2 | 18:18 | Visibility lint, vendor-agnostic, in `ce.py`: recomputes the timeline from the project YAML, extracts frames at each line midpoint, checks subtitle ink, text-card ink, per-corner character animation, and per-line voice loudness (real voices must exceed -55 dB; estimate renders skip and are labeled). `render` runs it automatically, `ce.py lint` re-runs it. Proven: silent windows measure -91 dB. |
| a097776 | 18:24 | Lint stops recomputing: estimate renders quantize per-line frames, so recomputed windows drifted past the render end and failed later lines. Both vendors now emit `timeline.json` (the renderer's own math, exact start/end per line) and the linter consumes it, falling back to the formula only when absent. Missing frames fail with a message instead of crashing. |

### Phase 7 - Structure review and capability completion (18:48-19:43)

| hash | time | what it delivered |
|---|---|---|
| 5ecfebc | 18:48 | The structure restructure (details below): shared background catalog at `assets/backgrounds/` (11 PNGs moved out of `vendors/hyperframes/assets/`, per-vendor copies deleted), root `AGENTS.md` cut from 119 lines to a ~40-line router with deep rules split into `docs/vendor-contract.md` and `docs/project-yaml.md`, vendor manuals trimmed to engine deltas, new `ce.py check` preflight (plain-words FILL items, GLM's exit scheme 0/1/2, `--json`), linter fallback formula deleted (timeline.json now required). |
| 19c4cfd | 19:22 | hyperframes gains `script[].se` (per-line sound effects, ffprobe duration, own track) and `visual.type image` (centered image card); the se/image gates and not-supported errors removed; hf-demo exercises both. Also regenerated `studio.png` (contrast). |
| 5c324d4 | 19:43 | Mascot emotion art: 16 emotion frames (happy, surprised, thinking, sad x open/close x Momo/Kiki), pairs verified pixel-identical outside the face box, shipped in all templates; `docs/mascot-art.md` documents the no-image-model pipeline and the image-model alternative with its pair-consistency trade-off. |

### Phase 8 - Rename (20:28-21:51)

| hash | time | what it delivered |
|---|---|---|
| 848d28e | 20:28 | Rename to Wayang (details below). |
| e247071 | 21:51 | Upstream repo reference (nyanko3141592) removed from `rumpun.yaml` and `vendors/remotion/AGENTS.md`. Commit history still contains the name. |

### Phase 9 - Onboarding and final hardening (22:29-23:47)

| hash | time | what it delivered |
|---|---|---|
| 9155a65 | 22:29 | Rimau the tiger, third mascot (chibi Malayan tiger, #F57C00): base lip-flap pair + four emotion pairs, all pair-verified. Also fixes the mascot generator's deploy root, stale since the rename. rimau-intro rendered with real Revolab voices. |
| 8d018d2 | 22:36 | `docs/tutorial.md`: clone to first MP4 in seven steps, following the real Rimau run, with a failure table. |
| 0b96a81 | 23:03 | Visibility lint v2 (details below) + the fifth template, `tutorial` (6 simulated terminal steps, Momo with emotions). |
| b530b92 | 23:10 | Terminal steps: font 24 -> 34px, window to 76% width, per-character GSAP stagger typing so long commands wrap instead of clipping; caret dropped. |
| 7a59c6b | 23:25 | Terminal window fix: one missing closing `</div>` (details below). |
| e9561b4 | 23:41 | Tutorial shows the fill example explicitly: a terminal step displays the exact YAML to write, so the FILL warning is paired with its fix. |
| a02c528 | 23:47 | `settings.video.playback_rate` honored by hyperframes (voice clip data-playback-rate, pauses and timeline scale, timeline.json/expected-seconds reflect it). Tutorial template ships at 0.9x (43.55s vs 39.27s at 1.2x). |

## The campaign: `.rumpun/`

`.rumpun/` is committed (except `runs/`, see the gitignore section) and
its git history is the campaign's evolution ledger. Layout per
`.rumpun/README.md`: `rumpun.yaml` (campaign config), `seasons/` (one
YAML per season), `ledger/` (append-only evidence), `prompts/base/`
(phase prompt templates), `runs/` (per-season workspaces, gitignored),
`adhd-rules.md` (output-style card, verbatim from
github.com/ayghri/i-have-adhd), `CHANGELOG.md` (campaign schema
versions; schema 1 only).

### rumpun.yaml (campaign config)

- Goal: build content_engine as a framework-agnostic YAML-template video
  platform, `vendors/<engine>/AGENTS.md` as the engine contract agents
  consume, remotion first.
- Metric: E2E - `ce.py init education demo` -> fill project.yaml ->
  `ce.py render projects/demo` -> mp4 with no manual fixes.
- Autonomy: stage `manual`; promote after 5 clean audits; demote on 2
  consecutive rejects; rejection rolls back to last good, pauses,
  escalates after 2.
- Review panel: families `[fable, glm, gpt-5.6-sol]`, majority rule,
  blinded.
- Invariants: goal_immutable, budget_cap, falsify_required.
- Budget: campaign cost cap 600.
- Routes: glm, claude (unsets all ANTHROPIC model/base-url overrides so
  fable serves), and a codex fleet (gpt-6-astra/sol/luna, gpt-reserve,
  gpt-5.6-sol/terra/luna, gpt-5.5, codex-auto-review), all
  `codex exec --dangerously-bypass-approvals-and-sandbox`.

### seasons/s1.yaml (the seed season)

- Goal: ship the MVP (education + community templates, canonical schema,
  remotion vendor with AGENTS.md contract, ce.py init/validate/render).
- Mode: fight. Methodology line: contract-first platform, three-model
  design consult (codex gpt-5.5, glm-5.3, fable) before schema freeze,
  then build and prove with a real render.
- Pipeline: phase design-review (writers answer
  `prompts/base/design-brief.md`) -> phase integrate (evaluate ->
  `runs/design-decisions.md`).
- Writers: codex on gpt-5.5 (knowledge: none), glm on glm-5.3
  (knowledge: none), fable (knowledge: full). 15 minutes each. Stop on
  all_exited.

### Ledger directives (`.rumpun/ledger/directives.jsonl`)

Convention: the ledger is append-only. Entries keep status `pending` even
after execution; closure is recorded by a new entry, never by editing old
ones. Directive 6 is that closure.

| seq | demanded / recorded | status |
|---|---|---|
| 0 | Operator directive: build the content_engine MVP end to end, no questions. Education + community templates, canonical YAML schema, vendors/remotion port with AGENTS.md, tools/ce.py. Consult codex + glm-5.3 + fable before schema freeze. | Executed (dafeabf, plus the consult records). Closed by seq 6. |
| 1 | s1 outcome record: MVP built and E2E-verified. education smoke-test -> 19.5s / 1.7MB / 585 frames mp4; community-test -> 18.9s mp4 with arbitrary character ids. TTS honestly labeled "estimate" (VOICEVOX not installed). Consult outcomes recorded; codex round 2 returned empty output. | Historical record. Closed by seq 6. |
| 2 | TTS is user-managed API providers, the platform owns no docker/service. Pluggable voice engines in the canonical schema, implement openai (OPENAI_API_KEY) + the existing voicevox endpoint. Platform tts step writes voice files; vendor consumes them, falls back to estimate. | Executed (2fd0e74). voicevox provider itself was later removed (e9e709a). Closed by seq 6. |
| 3 | Record: revolab provider added and verified E2E (nada-1.0-pro, wav 24 kHz, 6 voices through the platform path). `nada-1.0-flash` from the operator's example is not a valid model; API exposes nada-1.0-pro and aisyah-1.0-pro. openai provider implemented but unverified (no key). | Revolab done. The openai-unverified caveat stays open. |
| 4 | Record: series support (series.yaml fragment + episodes, deep merge episode-wins, merge-then-validate, batch in name order stopping at first failure, init-series, meta.series/episode schema fields). Inheritance proven by a negative test. | Executed (b340fee). Closed by seq 6. |
| 5 | TODO: background theme catalog duplicated per vendor (remotion + hyperframes copies). Move to one shared location all vendors reference, delete the copies. Same policy for future shared vendor assets. | Recorded in 10748ba, the commit whose hyperframes vendor created the duplicate catalog copy. Executed in the structure review (5ecfebc): single catalog at `assets/backgrounds/`. Closed by seq 6. |
| 6 | Closure: directives 0-5 all executed and verified. Known-open at closure: openai provider unverified against the live API (no key), mascot emotion art, hyperframes se/image-visual support, studio theme contrast. | Of the four open items: emotion art (5c324d4) came after closure, hyperframes se/image visuals shipped in the same commit as the closure entry (19c4cfd) while still listed as open, and no later entry records studio contrast as resolved (studio.png was regenerated in 19c4cfd). openai remains unverified. |

Open items as of the last ledger entry: the openai TTS provider has never
been run against the live API, and studio theme contrast has no recorded
resolution.

## The three-model design consult (season s1, before schema freeze)

Prompt: `prompts/base/design-brief.md`. Four questions, 120-word answers:
canonical shared schema vs per-vendor YAML, no-TTS timing fallback and
its pitfalls, what breaks with a second engine and what vendor AGENTS.md
must pin, single-file vs split YAML. Records in `.rumpun/runs/`:
`codex-review.md`, `codex-review-2.md`, `glm-review.md`,
`design-brief.md`, consolidated in `design-decisions.md`.

### What each model said

- codex (gpt-5.5, round 1): answered in question-protocol form and asked
  the one meta-question: "Do you want project.yaml to be stable across
  engines, even when a vendor loses features?" The operator's directive
  said no questions, so the session answered yes. That answer is decision
  1: canonical YAML is the stable contract. Round 2 was requested and
  returned empty output (`codex-review-2.md` contains only the stdin
  notice). No third round was attempted.
- glm-5.3 (full written review): canonical schema + per-vendor mapping -
  per-vendor YAML forks N templates x M engines that diverge quietly;
  canonical gives one validation point and vendor switch = change
  `meta.vendor`; `vendor: {}` keys that alter timing should be rejected
  at validation. Estimate fallback: character count / per-language rate
  plus punctuation pauses with a floor, and the pitfalls: never mix
  timing sources in one timeline, per-language rates stay rough, the
  quiet fallback is the worst error so tag every duration with its
  source, cache real durations keyed by hash(text, speaker_id). Second
  engine breaks: units (frames vs seconds), position must be an enum,
  visuals need a small canonical vocabulary, typography must be pinned.
  Vendor AGENTS.md must pin six things: input, timing, voice,
  capabilities (unsupported features error, never drop), output (mp4,
  exit codes, idempotent re-run), environment. Single file over split:
  one YAML, one validate, one diff; overlays merged by ce.py if a
  project ever outgrows one file.
- fable (full repo knowledge): estimate fallback details (per-project
  chars-per-second, minimum frame floor, silent placeholder wavs so the
  engine's Audio elements resolve), `flip_x` as a canonical character
  key so art orientation ports, and a minimal-diff upstream port with
  characters injected as a generated CHARACTERS export.

### Adopted (10 decisions in `runs/design-decisions.md`)

1. Canonical schema, per-vendor mapping (codex meta-answer, glm
   concurred).
2. Canonical timing unit: seconds, vendors convert to frames (glm).
3. Unknown keys error, never dropped silently (glm).
4. No mixing timing sources in one timeline (glm).
5. Duration source labeled in every build log (glm).
6. Position is an enum left|right (glm).
7. Small visual vocabulary with a fixed animation set (glm).
8. Estimate fallback: per-project cps, min frame floor, silent
   placeholder wavs (fable).
9. `flip_x` canonical character key (fable).
10. Engine port keeps upstream code minimal-diff, data-driven characters
    via generated export (fable).

All 10 were adopted; nothing from the consult was declined. The
decisions are visible in the shipped schema (seconds timing, unknown-key
errors, position enum, `vendor: {}` gate) and in the build-log source
labeling.

## The structure review (GLM 5.3 x fable, commit 5ecfebc)

Trigger: `runs/structure-brief.md` (fable-authored) with six known
concerns: background catalog duplicated per vendor, root AGENTS.md
mixing routing with deep contracts (119 lines), no preflight command
(onboarding by schema error), estimate/timeline math in three places
with the linter still carrying a fallback formula, engine/ keeping
upstream sample configs that could drift, and workdir artifacts
leaking into commits twice.

### What each reviewer recommended

GLM (`runs/glm-structure-review.md`) named the root anti-pattern:
canonical things COPIED instead of REFERENCED (catalogs, vendor
contracts, timeline math, engine configs each exist twice). Six moves:
delete both vendor catalog copies into one `assets/backgrounds/`, cut
root AGENTS.md to a ~40-line router with deep rules in
`docs/project-yaml.md` + `docs/vendor-contract.md`, trim vendor manuals
to deltas, delete the linter fallback formula (timeline.json required),
delete engine/ sample configs, one shared `work/` root. It also designed
`ce.py check`: cheap blockers first then guidance, imperative wording
with zero schema vocabulary, exit 0 clean / 1 blockers / 2 notes only,
`--json` for agents. Layering principle: prose that must be read to
prevent a violation is a defect, move that rule into ce.py.

fable (`runs/fable-structure-review.md`, written pre-GLM): keep the
vendor contract (`AGENTS.md` + `build.sh` + mapper - two vendors
onboarded with zero ce.py changes), keep the output-truth guards
(timeline.json + duration guard + visibility lint), keep format-named
templates. Restructure lean on the same four points (router AGENTS.md,
shared catalog, single source for engine configs, delete the fallback
formula). Add `ce.py check` as the guidance layer: plain-language FILL
report plus environment state, ending in a READY / NOT READY verdict,
while `validate` stays the strict gate.

### Adopted (recorded in `runs/structure-decisions.md`)

1. One background catalog at `assets/backgrounds/`, vendor copies
   deleted, both mappers resolve it relative to their workdir.
2. Root AGENTS.md becomes a ~40-line router; deep rules move to
   `docs/vendor-contract.md` and `docs/project-yaml.md`.
3. Vendor AGENTS.md files keep engine deltas only and point at
   `docs/vendor-contract.md`.
4. Linter requires timeline.json; the fallback formula is deleted and a
   missing timeline fails the lint with a clear message.
5. `ce.py check` gains GLM's exit scheme (0 clean, 1 blockers, 2 notes
   only) and `--json`; the agent workflow now runs check before render
   and relays FILL items in plain words.

### Declined, with recorded reasons (to prevent relitigating)

- Single `work/` root for all vendors: churn, no agent benefit; the
  per-vendor ignore rules (`vendors/*/.work/`) were already proven
  across re-renders.
- Deleting `engine/` config samples: map-project writes configs into
  disposable workdirs, so they cannot drift into builds; they serve
  standalone engine use only.

Implementation sequence, as recorded: catalog dedupe -> linter fallback
removal -> docs split -> check exit codes and `--json` -> full re-render
sweep (est-demo, dialog-ms, hf-demo) -> commit and push.

## Bug classes found, fixed, and what each taught

- Unclosed terminal window div (7a59c6b). The rewritten tutorial
  terminal block never closed its window div, so every clip after the
  first terminal step nested inside that overflow:hidden window and was
  clipped out of view: the video showed content only for the first two
  lines, while the duration guard stayed green. One closing tag fixed
  it. Taught: generated markup needs a structural check (div balance
  must equal 0, now run on every render), and a green timing guard does
  not mean a correct video.
- Visibility-lint parity bug (0b96a81). The v1 character check compared
  a line-mid frame against the tail frame, but the 0.2s lip flap put
  both frames on the same flap state for about half of all lines, so
  the check failed on luck. Rewritten: character presence is measured
  against the theme PNG scaled to the render (present character samples
  ~2490 px, empty corner ~0, threshold charH^2/60, measured on live
  frames); flap animation became an informational delta, not a gate;
  frame extraction is clamped inside the render duration. Taught:
  animation makes frame-vs-frame comparison nondeterministic, diff
  against ground truth instead.
- Timeline drift on estimate renders (a097776, completed in 5ecfebc).
  The lint recomputed per-line windows from the YAML formula, but
  estimate renders quantize frames, so windows drifted past the render
  end and later lines probed tail-only frames. Fix: vendors emit
  timeline.json with the renderer's own math, build.sh ships it next to
  video.mp4, the linter consumes it, then the fallback formula was
  deleted outright so a missing timeline is a hard lint error. Taught:
  never let the checker recompute what the renderer already computed.
- Empty tail / playback-rate mismatch (118fa17, guarded by 859f006).
  Inherited from upstream: Root.tsx summed raw durationInFrames +
  pauseAfter while playback ran each line at ceil(frames/playbackRate),
  so rate 1.2 produced a composition ~17% longer than the timeline
  (3.7s empty chalkboard). Fixed by summing per-line adjusted frames
  plus one closing buffer, then made a class-level guarantee by the
  duration guard (expected-seconds.txt vs ffprobe, 0.5s tolerance).
  Taught: the inherited bug became a permanent guard, so a repeat is a
  loud build error rather than a quiet artifact.
- Pre-rename stale path in the art generator (9155a65). The Wayang
  rename deliberately kept absolute local paths inside the art
  generators, so `generate_mascots.py` still deployed into the
  pre-rename `content_engine` tree until the Rimau commit fixed its
  deploy root. Note: this class is not fully dead -
  `assets/background/generate_background.py` and `generate_themes.py`
  still write to `/mnt/data/work/content_engine/...` paths today.
  Taught: absolute paths survive renames and resurface the next time
  the generator runs.
- Latin subtitles under a Japanese wrapper (dede006). BudouX-JA emitted
  near-whole-line segments for Latin text and the nowrap spans
  overflowed the centered container. Taught: upstream text-shaping
  assumptions are language-specific; wrap logic now branches by script.
- Vendor-side capability gating (c64a503). The remotion mapper gated
  voices on voicevox, blocking revolab/openai projects. Taught:
  validation is the platform's job; vendors consume, they do not gate.
- Workdir and state leaks (e38feb6, 477ff3f, 3690719, b264afe). A .pyc,
  .omc session state (root and nested under assets/mascots), and the
  whole hyperframes .work/ tree were committed when shells ran from the
  wrong cwd. Each was purged and its ignore rule widened. Recorded in
  the structure brief as "leaked twice". Taught: ignore rules are
  reactive, absolute paths and cwd discipline are the fix.

## Rename history

- Commit 848d28e (2026-09-26 20:28): "The platform has a name: Wayang,
  after the shadow play - flat puppet characters performing your script
  on a stage."
- GitHub repo renamed khursani8/content_engine -> khursani8/wayang;
  remote is now `https://github.com/khursani8/wayang.git` (old GitHub
  URLs redirect).
- CLI renamed `tools/ce.py` -> `tools/wayang.py` (git recorded a 98%
  similarity rename, prog wayang).
- Sweep: README, agent manual, docs, vendor manuals, engine configs,
  npm package names, schema title, map-project references - 20 files,
  48 insertions, 48 deletions.
- Absolute local paths inside the art generators were intentionally
  kept at rename time. The mascot generator was fixed one commit cycle
  later (9155a65); the background generators still carry
  `/mnt/data/work/content_engine` paths (see bug classes).
- The local working folder kept the name `/mnt/data/work/content_engine`
  until the operator asked, then moved to `/mnt/data/work/wayang`, with
  the Claude history namespace migrated by copy + symlink.
- Commit e247071 removed the upstream repo reference
  (nyanko3141592/remotion-voicevox-template) from `rumpun.yaml` and
  `vendors/remotion/AGENTS.md`. Old commit messages still name the
  upstream repo; scrubbing history would need git filter-repo plus a
  force push and was recorded as done-only-on-explicit-request.

## What is deliberately not in git

Current `.gitignore`: `node_modules/`, `vendors/*/.work/`, `projects/`,
`out/`, `*.log`, `.rumpun/runs/`, `.rumpun/seasons/_steady-state*`,
`.rumpun/seasons/_competition.yaml`, `__pycache__/`, `*.pyc`, `.omc/`.

| excluded | why it matters |
|---|---|
| `node_modules/` | Installed deps, reproducible from package.json; README pins the one manual step (`npm install` in `vendors/remotion/engine`). |
| `vendors/*/.work/` | Disposable per-vendor build workdirs: generated HTML, fonts, wavs, out.mp4. Committed by accident twice (10748ba, 1932e7c) when shells ran from the wrong cwd, purged in b264afe. |
| `projects/` | User content: each project's filled project.yaml, generated `voices/`, and `out/video.mp4`. Personal renders do not belong in the platform repo. (`projects/video-tutorial/` exists on disk, untracked.) |
| `out/` | Render outputs. |
| `.rumpun/runs/` | Per-season workspaces: the raw model outputs (codex/glm/fable reviews, briefs, decision drafts). Kept on disk only. The committed record of decisions lives in the ledger and commit messages. Anyone cloning the repo does not get the raw reviews. |
| `.rumpun/seasons/_steady-state*`, `_competition.yaml` | Untracked season templates and drafts: a steady-state season shape (three light lanes: lint sweep, route probes, rehearsals) and a Kaggle-competition season shape. Fill-in drafts, not campaign history. |
| `__pycache__/`, `*.pyc` | Build artifacts; one leaked in 2fd0e74, removed in e38feb6. |
| `.omc/` | Claude session state (hud caches, mission state, subagent tracking). Committed from dafeabf onward, untracked in 3690719 + 477ff3f. |

Contrast: `.rumpun/` minus those paths is committed on purpose -
`.rumpun/README.md` states that git history over it is the evolution
ledger, unlike disposable caches.

## Open questions you might ask

- Why does the ledger keep every directive at status `pending`, and is
  a closure pass (or a status convention change) planned, or is
  append-only-as-historical the permanent answer?
- The openai TTS provider has never touched the live API. Verify it
  with a key, or cut it from the schema until one exists?
- Directive 6 lists studio theme contrast as open, and 19c4cfd
  regenerated studio.png. Was contrast the reason, and is the item
  actually closed?
- `assets/background/generate_background.py` and `generate_themes.py`
  still write into the pre-rename `/mnt/data/work/content_engine` tree.
  Fix the paths, or accept it since regeneration is rare?
- The design consult gave fable full repo knowledge while codex and glm
  got none. Was the asymmetry deliberate (local model vs remote
  quota), and did it skew which recommendations won?
- Codex round 2 returned empty output and no third round was attempted.
  Was the meta-question answer from round 1 considered sufficient, or
  was codex effectively dropped from the consult?
- Autonomy stage is still `manual` with `promote_after: 5 clean audits`
  and the campaign cost cap is 600. Was any spend tracked against that
  cap, and is a season s2 planned or is the campaign closed?
- Old commit messages still name the upstream template repo. Is a
  `git filter-repo` history scrub planned, or does the redirect-plus-
  current-files state stand?
