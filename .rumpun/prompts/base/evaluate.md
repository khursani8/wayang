# Phase: evaluate (results vs committed falsification criteria)

## Inputs
- `falsification.yaml` (sealed), `results.jsonl`.

## Task
- Quote each committed criterion verbatim, then the result, then the verdict:
  kill | revise | retain | inconclusive (P16).
- Season verdict per writer: WIN | LOSS | NEUTRAL | INVALID, with an `implies` line.
- Grade each LOSS clause of the season metric pass/fail.
- A met LOSS condition reads LOSS, verbatim in the verdict row.
- A WIN that met its band still reads WIN (no inversion).

## Output contract
- Write `verdicts.jsonl`: {experiment_id, criterion_verbatim, result, verdict, implies}.

## Constraints
- WIN below the declared noise floor is recorded as NEUTRAL with the reason (P1/P13).
- Every verdict cites on-disk evidence. An empty implies line is a defect, not a style.

## Exit contract
- Before you exit, write `notes.md` in the run dir: the verdicts and the
  evidence they cite, and what remains. The close gate marks an exit
  without it incomplete.
