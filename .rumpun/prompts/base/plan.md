# Phase: plan (experiment that tests each hypothesis)

## Inputs
- `hypotheses.yaml`.

## Task
- One experiment per hypothesis: what runs, on what data, measured how.
- Cheapest experiment that can kill the hypothesis first.

## Output contract
- Write `experiments.yaml`: {hypothesis_id, command/steps, data, metric_readout}.

## Constraints
- Experiments must run in this season's runs/ workspace. No network calls outside declared routes.
