⚠ claude.ai connectors are disabled because ANTHROPIC_API_KEY or another auth source is set and takes precedence over your claude.ai login · Unset it to load your organization's connectors
"glm-5.3" isn't described by this version's model catalog; update Claude Code, or map it with behavesAs on a modelPicker row (or modelOverrides, if it is a provider id of a model this version knows). Until then auto-compact keeps this session within 200k tokens (the context window it assumes); if the model accepts more, append [1m] to the model name for 1M, or set CLAUDE_CODE_MAX_CONTEXT_TOKENS to its real window; CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1 restores the previous wait-for-the-API behavior.
[claude-code:unrecognized_model] {"model":"glm-5.3","query_source":"sdk"}
# Wayang review

## RESTRUCTURE

Verdict: keep the shape. Canonical YAML plus the `build.sh` contract onboarded a second engine with zero platform changes. What breaks at 10 vendors is duplicated catalogs, hard-coded lists, and guards copied per vendor. Five moves:

- **R1 — Hygiene batch (P0, S).** `check` enumerates `vendors/*/build.sh` instead of the hard-coded `known: remotion, hyperframes` list. Theme validation reads root `assets/backgrounds/` (the vendor-local path is a no-op today). `init-series` defaults `language: ms`, not `ja`. `assets/background/generate_*.py` write repo-relative, not the pre-rename `/mnt/data/work/content_engine` path. `AGENTS.md` lists 5 formats. Files: `tools/wayang.py`, two generators, `AGENTS.md`. Risk: low, no engine files touched.
- **R2 — Vendor capabilities declared (P0, S).** Add `vendors/<engine>/capabilities.yaml` listing supported canonical keys (terminal, emotion, scene, se). `check` warns when a project uses a key the vendor degrades, for example `terminal` on remotion. Reason: agents cannot read 10 vendor manuals per project. Risk: contract addition, opt-in per vendor.
- **R3 — Duration guard moves to the platform (P1, S).** Each `build.sh` copies `expected-seconds.txt` to OUT_DIR (2 lines). `wayang.py render` runs the ffprobe compare after build. One guard instead of 10 divergent awk copies, and the contract doc stops lying. Risk: vendors ship one more file.
- **R4 — Lint geometry from settings (P1, M).** `lint_project` already receives the merged document but uses hard-coded fontSize 70, charH 275, 55%/40px. Read `settings.*` with those values as fallback. Prerequisite for vertical and custom-geometry projects to be checked honestly. Risk: projects overriding settings today were checked against approximate boxes, some may newly fail.
- **R5 — Template smoke gate (P2, S).** CI or `check --templates` validates every `templates/*/template.yaml` against schema and theme catalog. Templates drift silently today (tutorial missing from the mascot deploy list). Risk: none, read-only.

Declined: shared `work/` root (rejected in 5ecfebc, still right), splitting `wayang.py` (8 commands fit one file), any engine rewrite.

## FEATURES

| Feature | User story | Layers | Effort | Pri |
|---|---|---|---|---|
| `voices` | I browse Malaysian voice ids before writing YAML | `tts_providers.py` (GET /v1/voices) + CLI | S | P0 |
| Line preview | I hear line 3 in Momo's voice before paying for all lines | `tts --line N`, per-line cache isolates it | S | P0 |
| `stats` | I see duration, per-host talk time, and TTS cost band before spending credits | new CLI cmd, manifest or `estimate_cps`, `--json` | S | P0 |
| BGM bed | One music track under my whole video | `settings.bgm {src, volume}`: schema, remotion (`bgmConfig` exists, hardcoded null), hyperframes full-duration clip | M | P1 |
| Title and end cards | Every video opens on my title and closes branded, no script edits | both mappers emit one card frame before line 1 and after the last | M | P1 |
| Vertical 9:16 | I post to TikTok/Reels, not only YouTube | `settings.video` preset + stacked-host layout in both engines + R4 | L | P1 |
| Scene backgrounds | My background changes between intro and main sections | per-scene theme map, mappers copy N themes, engines swap by current scene. Revives the parsed-but-unused `scene` key | M | P2 |
| Shared se catalog | I write `se: {ref: chime}` like a theme name, no file copying | `assets/se/` + resolution in both mappers + `check` | S | P2 |
| Draft render | I check pacing in 60 seconds, not 6 minutes | `render --draft` at 960x540, fps 12, output `out-draft/`, voices reused from cache | S | P2 |

P0 rows are platform-only, no engine changes. BGM audibility check is unaffected, music only raises measured volume.

🌸 **YOUR MOVE:** Green-light R1 + R2 as one hygiene commit?
