# Review brief: Wayang — structure health + next features

FIRST: read REPO_ANALYSIS/00-overview.md through 08-gotchas-and-quirks.md
in this repo (2018 lines of verified reference: architecture, commands,
vendors, templates, art pipeline, history, known bugs).

What Wayang is: agent-driven, Malaysian-identity video generation.
Format templates (dialog, presentation, storytelling, community,
tutorial) -> user fills ONE canonical YAML -> agents drive
tools/wayang.py (8 commands) -> pluggable vendors render (remotion:
React; hyperframes: HTML/GSAP). TTS: revolab + openai API clients,
cached per-line wavs. Guards: duration check, visibility lint
(pixel probes), timeline.json contract. Original mascots with emotions,
11 background themes, series support. Constraints: repo owns no
services (API clients only), Malaysian identity (Bahasa Malaysia,
Momo/Kiki/Rimau), renders are narrated stage scenes (hosts, cards,
subtitles) — no live footage.

## MANDATE 1 — RESTRUCTURING (if needed)

Is the current structure right for the next 10 vendors and templates?
Known open issues are listed in 08-gotchas-and-quirks.md. Propose
concrete file-level moves only (merge, move, delete, split) — with the
reason and the risk. Do not propose rewrites of working engines.

## MANDATE 2 — NEW USER-FACING FEATURES for content creation

Users: Malaysian creators + the agents serving them. Propose 5-10
features, each with: name, one-line user story, implementation sketch
(which files/layers change), effort S/M/L, priority. Favor features the
CURRENT architecture can host (narrated stage videos).

## OUTPUT

Markdown, two sections (RESTRUCTURE / FEATURES), prioritized, concrete,
max ~600 words. No questions back.
