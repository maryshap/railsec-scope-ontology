# Phase 2 execution record

| Step | Current outcome | Evidence |
|---|---|---|
| 9 — M5 vocabulary | First complete vocabulary baseline implemented; `Payload` recorded as a conceptual revision | `core.ttl`, `railway.ttl`, `CONCEPTUAL_CHANGE_CATALOG.tsv`, M5 SHACL |
| 10 — boundary decision | Implemented as explicit `undeterminedBoundary` with honest coverage | CR-B-009, K-01 shape, `boundary-assessment-coverage.rq` and regression fixture |
| 11 — synthetic architecture | Minimal category skeleton implemented; grows per rule block | `fixtures/railway-category/minimal.ttl` |
| 12.1 — transmission category | Implemented as evaluation then classification; generic stage coverage is 3/5 in the minimal fixture | category rules, `evaluation-stage-coverage.rq`, no-category and HermiT category-conflict fixtures |
| 12.2 — transmission threats | Implemented provisionally as seven three-valued evaluations; 4/6 fixture flows are determined and category unknowns propagate | `evaluate-transmission-threat.rq`, threat fixture, CR-B-012 and regression test |
| 12.3 — safety-critical elevation | Implemented provisionally for the two mappings expressible with the approved payload distinction; threat or payload unknowns propagate | `evaluate-critical-violation.rq`, critical fixture, CR-B-013 and regression test |
| 12.4 — fail-safe compromise | Implemented provisionally for legacy R2.4.1/R2.4.2 as asset evaluations; R2.4.3 remains deferred pending zone/remediation vocabulary | `evaluate-fail-safe-compromise.rq`, fail-safe fixture, CR-B-014 and regression test |
| 12.5 — maximum SIL risk | Implemented provisionally for legacy v3 R2.5.3 as an asset evaluation aggregating fail-safe compromise; R2.5.1/R2.5.2 deferred pending an attack technique vocabulary | `evaluate-sil-risk.rq`, SIL fixture, CR-B-015 and regression test |
| 12.6 — access risk | Implemented provisionally for legacy v3 R2.6.1-R2.6.4 as asset and flow evaluations; an unstated access inventory is undetermined, and remote access risk consumes threat evaluations | `evaluate-access-risk-asset.rq`, `evaluate-access-path-risk.rq`, access fixture, CR-B-016 and regression test |
| ETCS provenance prerequisite | Pending: all nine explicit `SafetyCriticalAsset` classifications lack a supporting `AssertedFact`/`JudgementBasis`; they must be sourced or reclassified before the ETCS case is used by Steps 12.3–12.6 | `cases/etcs/abox.ttl`, `cases/etcs/LEGACY_ARCHITECTURE_SOURCES.md` |
| 13 — Run orchestrator | Minimal Run implemented: bounded reasoner/rules loop with refusal on non-convergence, input and output validation, guarded-category check, run-scoped results and evidenced determinism. L3 hook present inside the loop and empty | `scripts/orchestrator.py`, CR-B-019 and contract tests |
| 14–16 | Pending | L3 reachability and coverage, CQ oracles, performance target and evidence episodes |

The category fixture is synthetic evidence about the implementation contract, not an EN 50159 source. Its criteria use a provisional `JudgementBasis`; release requires reviewed standard locations and interpretations.
