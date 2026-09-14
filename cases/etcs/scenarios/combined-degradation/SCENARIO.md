# Scenario: combined-degradation

## Purpose

Show that two independent control degradations are retained as separate,
traceable derivation chains in one Run.

## Change from protected baseline

- `flow-if-ts-06-forward`: safety code and cryptographic message protection
  are false;
- `flow-if-ts-03-forward`: sequence number and timestamp are false.

No other direct control value changes.

## Pre-registered expected result

- on `flow-if-ts-06-forward`, corruption threat and critical integrity are
  `satisfied`;
- on `flow-if-ts-03-forward`, repetition, deletion and resequencing threats are
  `satisfied`;
- delay remains `notSatisfied` because timeout is true;
- critical sequence remains `undetermined` because the carried payload is not
  sourced as `PositionStatusData`;
- unrelated flows remain equal to protected baseline.

## Run

```text
python scripts/orchestrator.py cases/etcs/abox.ttl cases/etcs/classification-provenance.ttl cases/etcs/scenarios/combined-degradation/security-facts.ttl cases/etcs/scenarios/combined-degradation/transmission-environment.ttl cases/etcs/scenarios/combined-degradation/threat-controls.ttl --run-id combined-degradation --output build/combined-degradation-result.ttl --progress
```

Only a `publishable=true` result is final case-study evidence.
