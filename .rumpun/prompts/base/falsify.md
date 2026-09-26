# Phase: falsify (pre-register the kill criterion BEFORE execution)

## Inputs
- `experiments.yaml`.

## Task
- For each experiment, write the kill criterion BEFORE results exist (P16, structured):
  comparator, metric, direction, threshold, dataset, confidence rule.
- State the consequence: kill | revise | retain | inconclusive.

## Output contract
- Write `falsification.yaml`: {experiment_id, metric, direction, threshold, dataset,
  confidence_rule, consequence}.

## Constraints
- This file is sealed (hashed) before execute starts. It cannot be edited after results.
- A criterion of the form "it works" is invalid; give a number and a direction.
