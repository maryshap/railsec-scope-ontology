# Scenario: missing-safety-code

## Purpose

Demonstrate a single-control degradation and trace exactly how far the
consequence propagates through the rule stages — including where it stops
and why, named precisely rather than left vague.

## What changed from protected-baseline

Exactly one fact: `safetyCodeEnabled` set to `false` on
`flow-if-ts-06-forward` (IXL/Interlocking → Euroloop). Every other fact is
inherited unchanged from `protected-baseline` (0.2.0).

## Why this flow

- `IF-TS-06` has exactly one flow traversing it (`flow-if-ts-06-forward`),
  so attaching its payload needed no direction assumption — unlike
  `IF-CT-01`, the original candidate, whose two flows leave payload
  direction genuinely unresolved (see `PAYLOAD_DIRECTION_TODO.md`).
- The flow carries `payload-DO-21`, a `SafetyRelatedPayload`.
- Its origin, `asset-ct-02` (IXL/Interlocking), is one of the nine
  safety-critical assets — relevant context even though the fail-safe stage
  won't be reached in this scenario (see below).

## Expected propagation, stage by stage

1. **Transmission-threat.** `safetyCodeEnabled = false` →
   `CorruptionThreat` evaluation should be `satisfied` for this flow
   (`threat-corruption-criterion`).
2. **Critical-violation (M5-R04).** `CorruptionThreat` elevates to
   `criticalIntegrityViolation` when the threat is satisfied and the
   payload is safety-related — both hold here — so this should be
   `satisfied` (`critical-integrity-criterion`, R2.3.2, implemented).
3. **Fail-safe-compromise.** Should be `undetermined`, not because
   anything is wrong with this scenario, but because `failSafeDependsOn` is
   asserted for no asset anywhere in `cases/etcs/abox.ttl` — a known,
   separate, case-wide architecture gap, not a defect in this scenario. See
   `cases/etcs/scenarios/README.md` → "Known constraint affecting the next
   scenario".
4. **SIL-risk.** Also `undetermined`, purely as a downstream consequence of
   3 — there is no compromise evaluation for it to consume.

If this scenario is presented anywhere (paper, review, demo), stages 3–4
should be shown as `undetermined` **with their stated reason**, not omitted
and not treated as a shortcoming of this scenario specifically.

## What this scenario deliberately does not attempt

The reference attack diagram this scenario was checked against also shows
a missing-sequence-protection / replay path. `sequenceProtectionEnabled` is
correctly detected as absent-equivalent at the transmission-threat stage
(`ResequencingThreat`/`RepetitionThreat` would be `satisfied` if that
property were also flipped here), but no criterion currently elevates
either threat to a `CriterionEvaluation` of type `CriticalViolationType` —
that elevation (legacy R2.3.4) is recorded as deferred in
`docs/DECISIONS.md` (CR-B-013), not implemented. This scenario only flips
`safetyCodeEnabled`, not `sequenceProtectionEnabled`, so as not to imply a
result the rule set cannot currently produce.

## How to run

```
python scripts/orchestrator.py cases/etcs/abox.ttl cases/etcs/classification-provenance.ttl cases/etcs/scenarios/missing-safety-code/security-facts.ttl cases/etcs/scenarios/missing-safety-code/transmission-environment.ttl
```

## Not yet executed here

Same limitation as `protected-baseline`: the full reasoner/rule fixed-point
did not complete inside this session's time limit. The expected
propagation above is a prediction from reading the rule files directly
(`evaluate-transmission-threat.rq`, `evaluate-critical-violation.rq`), not
a confirmed result. Run it and check the prediction against the actual
output before using this scenario's numbers anywhere — that check is
exactly the point of running it, not a formality.
