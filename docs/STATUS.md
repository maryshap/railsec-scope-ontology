# Status

Single source of truth for implementation, ontology, case-study and release
status. These are separate states and must not be collapsed into one claim.

## Current state

| State | Status | Meaning |
|---|---|---|
| Phase 2 implementation | **Complete for the admitted scope** | Canonical Steps 9–16 are implemented with executable evidence. |
| Ontology | **L1–L2 complete for scoping; L3 attack layer in progress** | M1–M5 and the admitted L1–L2 criteria/rules are present. M7 provides the governed attack schema and a checksum-pinned ATT&CK for ICS 19.2 projection; railway applicability criteria and attack-path computation remain to be completed. |
| ETCS case study | **Structurally migrated; fact completion in progress** | The architecture and initial security facts are usable, but unknown inputs still produce legitimate `undetermined` results. |
| Public release | **Not ready** | Source interpretation review, case evidence, persistent IRI setup and publication review remain. |

## Phase 2 closure

Canonical Steps 9–16 are closed for the admitted ontology-construction scope:

- M5 railway vocabulary, three-valued criteria and sourced rule blocks;
- explicit unknown boundary/category handling and honest stage coverage;
- synthetic positive, negative and unknown fixtures;
- bounded Run orchestration and run-scoped results;
- L3 reachability, witness paths, AHP factor values, weighted ordering and explicit-selection coverage;
- all 45 competency questions classified in the value-oracle matrix;
- a predeclared 900-second validation target for the declared CI environment;
- EV-B1–EV-B11 indexed as the Phase 2 evidence package, with independent ETCS comparison evidence explicitly carried forward.

The historical working labels “Step 14b”, “Step 14c” and “Step 15 control
weakness” remain useful descriptions, but do not renumber canonical Steps
14–16. They delivered the reusable railway criteria module, ETCS transmission
environment facts and the L1 control-weakness assessment.

## Criteria and legacy-rule disposition

The current `migration/legacy-rule-triage.csv` is the operational register:

- 33 rules are implemented with recorded sources and explicit assessor-policy boundaries where a standard informs but does not entail the project rule;
- 12 are deferred to explicitly named future capabilities, including the ATT&CK layer, reachability/external computation and organisational scope;
- 9 are not admitted as ontology rules because they duplicate the railway threat taxonomy, lie outside the declared scope, or belong to ETL rather than reasoning;
- no rule remains in an untriaged “implement now” state.

Deferred and non-admitted rows are visible scope decisions, not hidden Phase 2
implementation gaps.

## Executable coverage

- Competency questions: 27/45 have value oracles, 5/45 are empty by design and 13/45 are explicitly deferred pending producing capabilities.
- SHACL: 15/21 node shapes have focus nodes across the current evidence graphs; 6/21 remain registered as vacuous pending their producing capabilities.
- The pre-CR-B-024 ETCS L1 control run produced 1,480 evaluations. Its control-weakness counts remain regression evidence, but transmission-threat counts must be regenerated because EN 50159:2010 alternative-defence and category semantics changed.

These numbers are regression evidence for the current data, not a claim that
the ETCS case study is complete.

## Next work: ontology completion

1. Regenerate the ETCS scenario results under the corrected EN 50159:2010 semantics; this is case-study evidence, not additional ontology design.
2. Populate the ETCS ABox through explicit scenarios over one stable architecture: protected baseline, controlled protection changes, unknown-data cases and an expert-report comparison case.
3. Build the deferred L3 attack/reachability capabilities only after their scope and evidence sources are approved; do not treat them as missing facts in the current ABox.

## Public-release blockers

1. Complete and provenance-tag the ETCS facts required by the selected scenario criteria.
2. Obtain independent expert evidence and define the comparison protocol for EV-B11.
3. Review the workbook-derived boundary mapping and other remaining case-specific assessor assumptions.
4. Register and test the w3id redirect.
5. Complete K-22 copyright/source-text review and the final publication review.

The nine ETCS `SafetyCriticalAsset` classifications already have an attributed
`JudgementBasis` in `cases/etcs/classification-provenance.ttl`; this is not an
open blocker. They remain assumptions until a safety case supplies stronger
evidence.
