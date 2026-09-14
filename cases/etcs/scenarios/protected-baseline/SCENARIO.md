# Scenario: protected-baseline

## Purpose

Idealised reference for controlled comparisons. It is not a claim about the
real ETCS deployment.

## Assertions

- all seven aggregate flow controls are true for all 148 flows;
- all five additional detailed EN 50159 Table 1 inputs are true for all flows;
- all three L1 controls and all three transmission-category conditions are true;
- `payload-DO-21` is attached to the two single-direction flows that can be
  resolved without guessing payload direction;
- topology remains identical to the shared ETCS architecture.

Aggregate control labels are deliberately not treated as proof of specific
Table 1 defences. The detailed inputs live in `threat-controls.ttl` with
scenario provenance.

## Pre-registered expected result

- every transmission-threat evaluation is `notSatisfied`, because at least one
  explicit alternative defence is true;
- downstream control weaknesses caused by those threats are not materialised;
- `undetermined` may remain where access, payload, fail-safe or architecture
  evidence is absent; the scenario idealises controls, not the architecture.

## Run

```text
python scripts/orchestrator.py cases/etcs/abox.ttl cases/etcs/classification-provenance.ttl cases/etcs/scenarios/protected-baseline/security-facts.ttl cases/etcs/scenarios/protected-baseline/transmission-environment.ttl cases/etcs/scenarios/protected-baseline/threat-controls.ttl --run-id protected-baseline --output build/protected-baseline-result.ttl --progress
```

Only a `publishable=true` result is final case-study evidence.
