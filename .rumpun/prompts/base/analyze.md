# Phase: analyze (error analysis on current best output)

## Inputs
- current best output + metric record (see season YAML `metric`)

## Task
- Enumerate concrete errors/gaps in the current best output. One error per line.
- For each: where it shows, evidence (file/line/metric delta), and a severity guess.

## Output contract
- Write `errors.jsonl`: one JSON object per error:
  {"id": "e1", "where": "...", "evidence": "...", "severity": "high|med|low"}

## Constraints
- Every claim cites something on disk. No invented numbers.
- Do not propose solutions here; that is the hypothesize phase.
