# Phase 2 execution record

This record follows the canonical revised Phase 2 plan with sixteen top-level
steps. Later working labels such as "Step 14b", "Step 14c" and "Step 15 control
weakness" describe useful additions, but do not renumber the canonical plan.

| Step | Current outcome | Evidence / remaining work |
|---|---|---|
| 9 — finish M5 vocabulary | Complete for the rule blocks admitted so far. Later vocabulary additions remain governed Gate B revisions. | `core.ttl`, `railway.ttl`, `CONCEPTUAL_CHANGE_CATALOG.tsv`, M5 SHACL |
| 10 — boundary decision | Complete: explicit `undeterminedBoundary` with honest coverage. | CR-B-009, K-01, `boundary-assessment-coverage.rq` |
| 11 — synthetic architecture | Complete as growing block-specific fixtures with positive, negative and unknown cases. | `fixtures/railway-*`, reasoner conflict fixture |
| 12 — rules one block at a time | The six planned railway blocks are executable. Nineteen of twenty-five legacy L2 rules are implemented; six remain governed deferrals. The later L1 control-weakness block is an additional Step 12 rule slice, not canonical Step 15. | M5-R01–M5-R10, CR-B-012–CR-B-016 and CR-B-023 |
| 13 — orchestrator, then L3 | **Implemented for admitted scope.** The bounded Run orchestrator, generic category materialiser, run-scoped candidate projection, deterministic reachability/witness paths, AHP factor values, weighted ordering and explicit-selection coverage are implemented. | `scripts/orchestrator.py`, `scripts/l3.py`, `fixtures/l3/minimal.ttl`, CR-B-019 |
| 14 — competency-question oracles | **Complete as a value-oracle matrix.** All 45 queries parse and are classified: 27 have row-count oracles, 5 are empty by design and 13 are explicitly deferred to missing producing capabilities. | `tests/test_cq_suite.py`, `reports/cq-value-oracle-matrix.tsv`, `docs/TEST_COVERAGE_AUDIT.md` |
| 15 — performance target | **Complete.** The full GitHub validation workflow target is predeclared at 900 seconds for the declared CI environment; the earlier 10-minute observation is retained only as historical context, not retroactive proof. | `reports/phase2-performance.ttl`, `tests/test_phase2_closure.py` |
| 16 — evidence episodes | **Complete as a Phase 2 evidence package.** EV-B1–EV-B10 are indexed to retained executable evidence. EV-B11 is explicitly carried forward because independent ETCS assessment evidence is not yet available. | `reports/phase2-evidence-index.tsv`, `tests/test_phase2_closure.py` |

## Numbering reconciliation

CR-B-021 (criteria module), CR-B-022 (ETCS transmission environment) and
CR-B-023 (L1 control weakness) remain valid changes. Their historical working
step labels do not replace canonical Steps 14–16:

- CR-B-021 and CR-B-022 are enabling/module and separate ETCS-track work;
- CR-B-023 is an additional Step 12 vertical rule slice;
- canonical Step 14 is CQ oracles;
- canonical Step 15 is the predeclared performance target;
- canonical Step 16 is the retained evidence package.

## Closure status

Canonical Phase 2 Steps 9–16 are closed for the admitted ontology-construction
scope. Deferred legacy rules, provisional source review, ETCS fact completion,
w3id setup and final publication review remain visible post-Phase-2 release
tasks rather than hidden gaps in the Phase 2 implementation record.

The ETCS case remains a separate evidence track. Its facts may exercise the
ontology, but case completion is not a substitute for closing the main track.
