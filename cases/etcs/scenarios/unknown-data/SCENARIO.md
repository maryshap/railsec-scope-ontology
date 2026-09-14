# Scenario: unknown-data

## Purpose

Demonstrate that missing evidence produces `undetermined`, not an inferred
absence of protection.

## Change from protected baseline

The `sequenceNumberEnabled` assertion and its assumption record are omitted for
`flow-if-ts-06-forward`. Every other control remains identical to baseline.

## Pre-registered expected result

- `threat-deletion-criterion = undetermined` on the selected flow;
- repetition and resequencing remain `notSatisfied` because timestamp is true;
- no missing fact is interpreted as `false`;
- every other flow result remains equal to protected baseline.

## Run

```text
python scripts/orchestrator.py cases/etcs/abox.ttl cases/etcs/classification-provenance.ttl cases/etcs/scenarios/unknown-data/security-facts.ttl cases/etcs/scenarios/unknown-data/transmission-environment.ttl cases/etcs/scenarios/unknown-data/threat-controls.ttl --run-id unknown-data --output build/unknown-data-result.ttl --progress
```

Only a `publishable=true` result is final case-study evidence.
