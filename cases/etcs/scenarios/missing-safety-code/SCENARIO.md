# Scenario: missing-safety-code

## Purpose

Demonstrate the EN 50159 alternatives semantics: one absent defence does not
prove exposure when another admitted defence is explicitly present.

## Change from protected baseline

Exactly one aggregate fact changes on `flow-if-ts-06-forward`:
`safetyCodeEnabled = false`. The detailed scenario file retains
`cryptographicMessageProtectionEnabled = true`.

## Pre-registered expected result

1. `threat-corruption-criterion = notSatisfied` on the selected flow because
   the alternative cryptographic defence is true.
2. `critical-integrity-criterion = notSatisfied` because the upstream threat
   is not satisfied.
3. Results on every other flow remain equal to protected baseline.
4. Existing case-wide fail-safe/access unknowns remain visible.

The positive counterpart is `missing-corruption-protection`, where both
corruption alternatives are explicitly false.

## Run

```text
python scripts/orchestrator.py cases/etcs/abox.ttl cases/etcs/classification-provenance.ttl cases/etcs/scenarios/missing-safety-code/security-facts.ttl cases/etcs/scenarios/missing-safety-code/transmission-environment.ttl cases/etcs/scenarios/missing-safety-code/threat-controls.ttl --run-id missing-safety-code --output build/missing-safety-code-result.ttl --progress
```

Only a `publishable=true` result is final case-study evidence.
