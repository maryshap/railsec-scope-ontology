# Scenario: controlled remote attack path

## Purpose

Exercise the complete L3 path computation on the ETCS architecture without
presenting hypothetical access or protection values as deployment facts. This
is a controlled counterfactual derived from the protected baseline, not an
assessment of the real installation.

## Frozen architecture

The shared `cases/etcs/abox.ttl` and `classification-provenance.ttl` are used
unchanged. In that topology, directed flow `IF-IT-10-forward` connects the
NG-FW (`IT-01`) to the RBC (`CT-01`). The NG-FW is derived as an entry point
because it belongs to a DMZ zone. The RBC has a separately attributed,
provisional safety-critical classification.

## Scenario assumptions

Exactly two counterfactual assumptions are introduced:

1. the NG-FW is reachable by `RemoteAccess`;
2. encryption is disabled on `IF-IT-10-forward`.

The first assumption is isolated in `access-assumptions.ttl`. The second is the
only aggregate-control delta from the protected baseline. Both are attributed
to the case assessor, use the same explicit judgement basis, and must be
replaced or rejected independently when deployment evidence becomes available.
All other aggregate and detailed protection values remain protected-baseline
assumptions.

## Pre-registered expected result

- the missing encryption makes the directed flow confidentiality-vulnerable;
- ATT&CK ICS 19.2 technique T0842 Network Sniffing is applicable to that flow;
- one attack path is materialised from NG-FW to RBC using the satisfied T0842
  applicability evaluation and its L1 prerequisite evidence;
- the path has one ordered step and a complete derivation record;
- the path is linked to a safety concern because its target is provisionally
  classified as `SafetyCriticalAsset`;
- no SIL is assigned;
- no reverse path is inferred and no other protected-baseline control is
  weakened.

## Run

```text
python scripts/orchestrator.py cases/etcs/abox.ttl cases/etcs/classification-provenance.ttl cases/etcs/scenarios/controlled-remote-attack-path/security-facts.ttl cases/etcs/scenarios/controlled-remote-attack-path/transmission-environment.ttl cases/etcs/scenarios/controlled-remote-attack-path/threat-controls.ttl cases/etcs/scenarios/controlled-remote-attack-path/access-assumptions.ttl --run-id controlled-remote-attack-path --output build/controlled-remote-attack-path-result.ttl --progress
```

Only a `publishable=true` result that matches the pre-registered expectations
is final case-study evidence.
