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
| 12.5–12.6 | Pending | SIL/override and access-path slices |
| 13–16 | Pending | orchestrator/L3, CQ oracles, performance target and evidence episodes |

The category fixture is synthetic evidence about the implementation contract, not an EN 50159 source. Its criteria use a provisional `JudgementBasis`; release requires reviewed standard locations and interpretations.
