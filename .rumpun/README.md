# rumpun project state (this directory: .rumpun/)

Everything the swarm needs lives here, out of the host repo's way:
- rumpun.yaml — campaign config: goal, autonomy stages, budget cap, routes.
- seasons/ — one YAML per season; s1 is the seed.
- ledger/ — append-only evidence ledger (committed).
- adhd-rules.md — the i-have-adhd output rules card (verbatim from github.com/ayghri/i-have-adhd).
- prompts/base/ — phase prompt templates; season overrides in prompts/sN/.
- runs/ — per-season workspaces (gitignored).

This directory is COMMITTED except runs/: git history over it is the
evolution ledger. Unlike .omc-style caches it is not disposable.

## First season
1. Fill campaign.goal and campaign.metric in rumpun.yaml.
2. Fill goal/metric in seasons/s1.yaml.
3. rumpun lint .rumpun/seasons/s1.yaml
4. rumpun graph .rumpun/seasons/s1.yaml
5. rumpun models — probe spawnable routes; --write fills rumpun.yaml.
6. rumpun season start — run the season (not yet implemented, build order step 3).
