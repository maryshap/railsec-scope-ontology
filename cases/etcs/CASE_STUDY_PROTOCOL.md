# ETCS case-study protocol

## Claim boundary

This is the first empirical application of the railway scope and attack-path
ontology. It evaluates one documented ETCS architecture; it does not establish
that every ETCS deployment has the same assets, controls, weaknesses or risks.

The case study is complete only when the architecture evidence, scenario
assumptions, derived results and external comparison evidence remain
distinguishable. A green ontology CI run alone is necessary but not sufficient.

## Completion criteria

### 1. Case definition and source traceability

- the deployment/system boundary, version and observation date are stated;
- every architecture, control, environment, payload, access, safety-function
  and fail-safe-dependency assertion has a source, an explicitly identified
  assessor judgement/assumption, or is recorded as unresolved;
- `mapping.csv` and `unmapped.csv` account for every imported source field;
- sensitive or unavailable evidence is referenced by a stable evidence ID
  rather than silently omitted;
- no derived conclusion is asserted as an ABox input fact.

### 2. Data sufficiency review

- coverage is reported for every applicable L1, L2 and declared L3 stage;
- every `undetermined` family is traced to a named missing/ambiguous input;
- unresolved payload directions, access facts, safety-function links and
  fail-safe dependencies are either sourced or retained as limitations;
- the domain expert reviews the architecture boundary and safety-relevant
  classifications.

`Undetermined` is not a failed test and must not be converted to `false`.

### 3. Reproducible analysis episodes

The same frozen architecture is analysed through separately versioned scenario
fact sets:

1. `realistic-legacy`: migrated evidence, including its genuine unknowns;
2. `protected-baseline`: an explicitly idealised control baseline;
3. a single-control degradation with a predicted derivation chain;
4. an `unknown-data` scenario proving the epistemic distinction;
5. a combined degradation scenario;
6. an expert-evidence scenario, created only after the independent assessment
   has been encoded without consulting ontology results.

Every episode must have a unique Run identifier, artefact digest, input and
output validation status, reasoner status, fixed-point status, result file,
human-readable summary and recorded execution environment. A final evidence
episode requires `publishable=true`.

### 4. Expected-result and comparison checks

- protected baseline and each controlled degradation have pre-registered
  expected changes before their result is inspected;
- changing one scenario fact cannot mutate the shared architecture;
- comparisons identify changed inputs, changed evaluations and unchanged
  controls;
- results are explained as criterion evaluations and derivation chains, not as
  unexplained labels;
- Neo4j is a presentation view of retained RDF results, never the source of
  truth or the evaluation engine.

### 5. Independent expert validation (EV-B11)

The expert risk assessment must be prepared or frozen independently of the
ontology output. Each expert finding receives a stable ID, evidence locator,
affected architecture element(s), finding category, consequence and the
expert's original likelihood/impact/risk wording.

Before comparing outcomes, a mapping protocol fixes:

- the common unit of comparison (asset, directed flow, interface, path or
  system-level finding);
- terminology mappings and aggregation rules;
- which ontology outcome/criterion is capable of matching each finding type;
- how partial, broader/narrower and non-comparable findings are represented.

Each comparison is classified as:

- `agreement` — both identify the same scoped concern;
- `ontology-only` — the ontology derives a concern absent from the report;
- `expert-only` — the report identifies a concern not derived by the ontology;
- `partial` — overlap exists but scope, direction or consequence differs;
- `undetermined` — ontology input evidence is insufficient;
- `not-comparable` — the finding is outside the ontology's declared claim.

The analysis must explain disagreements. It must not treat the expert report as
infallible ground truth, and it must not calculate precision/recall unless the
report is demonstrably exhaustive for the same boundary and finding universe.

### 6. Final retained evidence

- frozen input graphs and their source register;
- scenario manifests and expected-result statements;
- publishable RDF Run outputs and stage summaries;
- scenario-to-scenario comparison tables;
- expert comparison matrix and disagreement analysis;
- representative derivation traces and visualisations;
- limitations, threats to validity and reproducibility instructions;
- green OWL 2 DL, reasoner, SHACL, unit/regression and CI evidence.

## Current status

| Area | Current evidence | Status |
|---|---|---|
| Architecture migration | `abox.ttl`, `mapping.csv`, `unmapped.csv` | structurally available; domain/source review remains |
| Safety classification | `classification-provenance.ttl` | provisional assessor judgement; review remains |
| Realistic security/environment facts | `security-facts.ttl`, `transmission-environment.ttl` | available with documented unknowns |
| Controlled scenarios | protected baseline and missing safety code | facts available; final publishable Runs absent |
| Payload direction | `PAYLOAD_DIRECTION_TODO.md` | three directional mappings unresolved |
| Access/fail-safe evidence | case-wide gaps visible in evaluations | source acquisition/review required |
| Result reporting | RDF output exists for an earlier local Run | non-publishable and contaminated by a fixed run-isolation defect; regenerate |
| Expert comparison | EV-B11 protocol defined here | expert evidence not yet supplied |
| Final case-study claim | all sections above | open |

## Decision rule

The ETCS case study may be called complete when every completion criterion is
either supported by retained evidence or explicitly bounded as a limitation
that does not invalidate the stated research claim. It may not be called
complete merely because a graph can be visualised or because the core ontology
test suite passes.
