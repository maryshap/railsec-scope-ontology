# Scenario: protected-baseline

## Purpose

Reference point for scenario comparison. Not a claim about the real ETCS deployment.

## What this scenario asserts

**Regenerated as 0.2.0.** The first version (0.1.0) attached these facts to
Interface individuals, inheriting the same attachment defect fixed in the
real case data by `CARRIESPAYLOAD_FLOW_FIX.md` — it would have produced
`undetermined` everywhere regardless of scenario intent, because the rules
read these properties off flows, not interfaces. 0.2.0 attaches every fact
to the 148 `RailwayInformationFlow` individuals directly.

- All 7 per-flow protection-control properties (`authenticationEnabled`, `encryptionEnabled`, `integrityProtectionEnabled`, `safetyCodeEnabled`, `sequenceProtectionEnabled`, `sourceDestinationIdentifierEnabled`, `timeoutMechanismEnabled`) are `true` for all 148 flows.
- `payload-DO-21` is attached to `flow-if-ts-03-forward` and `flow-if-ts-06-forward` — both single-flow interfaces, no direction assumption needed.
- All 3 L1 controls (`monitoringEnabled`, `networkSegmentationEnabled`, `rateLimitingEnabled`) are `true` for all 148 flows.
- All 3 EN 50159 category conditions are `true` for all 148 flows — unlike the real data, where only 52/88 interfaces had a supportable determination.

## What this scenario does not touch

`crossesTrustBoundary` and `wirelessMedium` are topology facts, not controls. They are carried over unchanged from `cases/etcs/transmission-environment.ttl`. A scenario cannot legitimately move an asset across a zone boundary or turn a radio link into a wired one — only the protection state applied over that topology is hypothetical here.

## Provenance

Every fact in this scenario derives from `case:scenario-protected-baseline-basis` or `case:scenario-protected-baseline-transmission-basis`, not from `case:legacy-security-fact-basis` or `case:transmission-environment-basis`. This keeps the idealised scenario facts structurally distinguishable from real migrated data at a query level, not just by filename.

## How to run

```
python scripts/orchestrator.py cases/etcs/abox.ttl cases/etcs/classification-provenance.ttl cases/etcs/scenarios/protected-baseline/security-facts.ttl cases/etcs/scenarios/protected-baseline/transmission-environment.ttl
```

## Expected shape of the result (not yet confirmed by a run in this environment — see note)

Per the original design note: mostly `notSatisfied` weakness/violation evaluations, few or zero `satisfied`, `undetermined` should not disappear (payload classification is still only transferred for 5 of 88 interfaces, so category/threat/critical-violation stages will still return `undetermined` for most flows regardless of protection state — that gap is architectural, not fixed by this scenario).

**This has not been executed end-to-end here.** `pyshacl` advanced-mode validation plus the bounded reasoner/rule loop did not complete within this session's time limit on the full ~13k-triple combined graph. The files parse correctly and pass the completeness check (88/88 interfaces × 7/7 true, 148/148 flows fully covered), but the actual evaluation counts need to come from a run on your own machine/CI, which is presumably already fast enough for `security-facts.ttl` at this scale since it validates today.
