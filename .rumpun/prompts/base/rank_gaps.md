# Phase: rank_gaps (pick the top points worth resolving)

## Inputs
- `errors.jsonl` from analyze.

## Task
- Choose the top `top_n` gaps by expected metric impact over effort.
- Discard duplicates and cosmetic items explicitly (name what you dropped and why).

## Output contract
- Write `gaps.yaml`: list of {id, summary, source_error_ids, expected_impact, effort}.

## Constraints
- Do not invent new errors; rank what analyze produced.
