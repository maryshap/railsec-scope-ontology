# ETCS scenarios

## Mechanism

Every scenario shares the stable architecture layer and forks only the
situational-facts layer:

**Shared, never forked:**
- `cases/etcs/abox.ttl` — architecture: assets, zones, flows, interfaces, payload objects.
- `cases/etcs/classification-provenance.ttl` — safety-critical asset classifications.

**Forked per scenario, one full copy each (not a diff/overlay):**
- `security-facts.ttl` — per-interface protection controls.
- `transmission-environment.ttl` — per-flow L1 controls and EN 50159 category conditions.

RDF/OWL has no built-in "override" semantics: if a base file asserts
`authenticationEnabled false` for an interface and a second file asserts
`true` for the same interface, both facts end up in the graph at once —
not a replacement. That is why each scenario is a self-contained pair of
files, not a small delta loaded on top of the original
`cases/etcs/security-facts.ttl`. A scenario run passes exactly one
security-facts file and one transmission-environment file, never the
original plus a scenario file together.

The original `cases/etcs/security-facts.ttl` and
`cases/etcs/transmission-environment.ttl` are untouched and remain what
they always were: the real data migrated from the legacy workbook
(Step 14/14c). They are not renamed or moved, so nothing that already
references them (`scripts/validate.ps1`, the migration/derivation
scripts, existing tests) needs to change. Treat them as the implicit
"realistic-legacy" scenario if you want to compare against real data
rather than a synthetic one.

## Running a scenario

```
python scripts/orchestrator.py \
  cases/etcs/abox.ttl \
  cases/etcs/classification-provenance.ttl \
  cases/etcs/scenarios/<name>/security-facts.ttl \
  cases/etcs/scenarios/<name>/transmission-environment.ttl
```

## Adding a new scenario

1. Create `cases/etcs/scenarios/<name>/`.
2. Fork `security-facts.ttl` and/or `transmission-environment.ttl` from
   whichever existing scenario is the right starting point — usually
   `protected-baseline`, not the real legacy data, if the scenario is
   meant to isolate a single changed fact.
3. Give every changed fact its own `JudgementBasis` distinct from any
   other scenario's, so scenario provenance never gets confused with
   real data provenance or with another scenario's provenance at the
   query level, not only by which file it lives in.
4. Write `SCENARIO.md`: what changed from the parent scenario, why, and
   what result it's meant to demonstrate.
5. Do not touch topology facts (`crossesTrustBoundary`, `wirelessMedium`,
   anything in `abox.ttl`) to manufacture a result — those describe the
   architecture, not a protection state layered over it. If a scenario
   needs a topology change, that is a different case, not a scenario.

## Scenarios in this directory

| Scenario | Status | Forks from |
|---|---|---|
| `protected-baseline` | facts generated, not yet run end-to-end | idealised — all controls true |
| `missing-authentication` | not started | protected-baseline, minus one fact |
| `unknown-data` | not started | protected-baseline, minus one flow's facts entirely |

## Known constraint affecting the next scenario

`failSafeDependsOn` — the architecture property the fail-safe-compromise
rule (M5-R05) needs to fire — does not occur anywhere in
`cases/etcs/abox.ttl`. No asset in this case has it asserted. This means
a "missing-authentication" scenario cannot currently demonstrate a
cascade all the way through fail-safe/SIL, regardless of which flow is
picked: those stages will return `undetermined` for a missing
architecture dependency, not `notSatisfied`/`satisfied`. The chain that
*is* demonstrable stops at critical-violation elevation (M5-R04). This
is worth showing as-is — an honest `undetermined` caused by a real,
named architectural gap is a legitimate finding, not a failure — rather
than adding a `failSafeDependsOn` fact that has no source just to make
the demo reach further.
