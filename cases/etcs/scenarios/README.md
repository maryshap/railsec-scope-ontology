# ETCS scenarios

## Mechanism

Every scenario shares the stable architecture layer and forks only the
situational-facts layer.

Shared, never forked:

- `cases/etcs/abox.ttl` — assets, zones, flows, interfaces and payload objects;
- `cases/etcs/classification-provenance.ttl` — safety-critical classifications.

Forked per scenario as full files, not RDF overlays:

- `security-facts.ttl` — aggregate IEC 62443/legacy protection controls;
- `transmission-environment.ttl` — L1 controls and EN 50159 category inputs;
- `threat-controls.ttl` — detailed EN 50159 Table 1 alternatives consumed by
  transmission-threat criteria.
- `access-assumptions.ttl` — optional, scenario-only entry-access assumptions;
  never part of the shared architecture.

RDF has no override semantics. Loading both `true` and `false` for a functional
control property creates a contradiction; it does not replace the old value.
Each Run must therefore load exactly one complete scenario set and must never
load `cases/etcs/security-facts.ttl` together with a scenario security file.

The original `cases/etcs/security-facts.ttl` and
`cases/etcs/transmission-environment.ttl` retain migrated deployment evidence
and its unknowns. Together they form the implicit `realistic-legacy` episode.

Detailed scenario inputs are generated deterministically:

```text
python scripts/build_etcs_scenarios.py
```

Regeneration proves repeatability, not that a synthetic assumption describes a
real deployment.

## Running a scenario

```text
python scripts/orchestrator.py \
  cases/etcs/abox.ttl \
  cases/etcs/classification-provenance.ttl \
  cases/etcs/scenarios/<name>/security-facts.ttl \
  cases/etcs/scenarios/<name>/transmission-environment.ttl \
  cases/etcs/scenarios/<name>/threat-controls.ttl \
  [cases/etcs/scenarios/<name>/access-assumptions.ttl] \
  --run-id <name> --output build/<name>-result.ttl --progress
```

Use `scripts/summarize_case_run.py` to turn the retained RDF result into a
stage table. Only a Run with `publishable=true` is final evidence.

## Scenario register

| Scenario | Status | Purpose |
|---|---|---|
| `realistic-legacy` | publishable Run confirmed in workflow run 34896016005 | migrated deployment evidence with its genuine unknowns and no invented detailed controls |
| `protected-baseline` | publishable Run confirmed in workflow run 34896016005 | idealised reference with all admitted controls true |
| `missing-safety-code` | publishable Run confirmed in workflow run 34896016005 | one absent defence while an alternative remains true |
| `missing-corruption-protection` | publishable Run confirmed in workflow run 34896016005 | all corruption alternatives absent on one safety-related flow |
| `unknown-data` | publishable Run confirmed in workflow run 34896016005 | one required fact absent, demonstrating `undetermined` |
| `combined-degradation` | publishable Run confirmed in workflow run 34896016005 | two independent degradations after single-change episodes |
| `controlled-remote-attack-path` | pre-registered; awaiting publishable workflow result | minimal one-hop L3 counterfactual from NG-FW to safety-critical RBC |
| `expert-evidence` | awaiting independent source | comparison with the frozen expert risk assessment |

## Scenario authoring rules

1. Pre-register changed facts and expected evaluation changes before output is
   inspected.
2. Give assumptions their own `JudgementBasis` and instance-set attribution.
3. Do not change topology to manufacture a finding. A topology change is a
   different architecture case, not a protection scenario.
4. Keep unknown values absent or explicitly epistemic; never encode them as
   `false`.
5. Compare only evaluations produced by the selected Run.

## Known case-wide constraint

`failSafeDependsOn` is absent from `cases/etcs/abox.ttl`. Therefore fail-safe
and downstream SIL-risk evaluations can remain `undetermined` even in a
correctly controlled scenario. This is an evidence-acquisition obligation, not
permission to invent a dependency for a more dramatic result.
