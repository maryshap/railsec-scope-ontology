# Scenario: missing-corruption-protection

## Purpose

Positive controlled degradation proving the chain from explicitly absent
alternative defences to a safety-related critical-integrity result.

## Change from protected baseline

On `flow-if-ts-06-forward` only:

- `safetyCodeEnabled = false` in `security-facts.ttl`;
- `cryptographicMessageProtectionEnabled = false` in `threat-controls.ttl`.

The flow carries `payload-DO-21`, explicitly typed `SafetyRelatedPayload`.

## Pre-registered expected result

1. `threat-corruption-criterion = satisfied`.
2. `critical-integrity-criterion = satisfied`.
3. Unrelated flow evaluations remain equal to protected baseline.
4. Fail-safe and SIL stages may remain `undetermined` because the shared
   architecture does not assert the required fail-safe dependency.

## Run

```text
python scripts/orchestrator.py cases/etcs/abox.ttl cases/etcs/classification-provenance.ttl cases/etcs/scenarios/missing-corruption-protection/security-facts.ttl cases/etcs/scenarios/missing-corruption-protection/transmission-environment.ttl cases/etcs/scenarios/missing-corruption-protection/threat-controls.ttl --run-id missing-corruption-protection --output build/missing-corruption-protection-result.ttl --progress
```

Only a `publishable=true` result is final case-study evidence.
