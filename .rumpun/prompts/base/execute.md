# Phase: execute (run the experiments as the season's writers)

## Inputs
- the season YAML `metric` and WIN/LOSS band (the sealed, lint-gated criteria).
- Your lane directive and knowledge staging from the ledger.

## Task
- Run your assigned experiments. Append discoveries to your discovery.md as you go.
- Fight mode: work independently. Collab mode: post leads to the lane (leads, not facts).

## Output contract
- Write `results.jsonl`: {experiment_id, outcome numbers, artifacts produced, minutes}.

## Constraints
- Do not read or reinterpret the falsification criteria; execute them as written.

## Exit contract
- Before you exit, write `notes.md` in the run dir: what was done, the
  evidence on disk, and what remains. The close gate marks an exit without
  it incomplete.
