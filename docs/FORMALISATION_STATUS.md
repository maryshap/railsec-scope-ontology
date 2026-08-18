# Formalisation status

**Baseline:** 0.1.0 development line  
**Conceptual source:** frozen Gate B v1.0 candidate

## Implemented and verified

- Step 0: namespace/IRI decision, acyclic import graph, pinned PROV-O source/DL projection, ROBOT OWLAPI profile validation, HermiT consistency/classification, committed inferred hierarchy, CI.
- Step 1: the frozen Gate B baseline of 76 M1–M4 classes is formalised in full. Classes admitted since the freeze are recorded in the conceptual change catalog rather than counted here, so this figure stays comparable to the gate. Every own object and datatype property carries a domain and a range; this is asserted as an invariant by `tests/test_documentation_integrity.py` rather than stated as a count, which would go stale at the next admitted revision. Sibling disjointness and value closure hold; CR-B-001/002 resolve the two known defects.
- Step 2: CriterionEvaluation vertical slice with exact OWL cardinalities, L2-R01, K-11/K-23/K-24, positive/negative fixtures and asserted CQ-09 result.
- Step 3: the generated 76-row entity matrix records module, named superclasses, property participation, restriction count, disjointness and K-allocation.
- Step 4: K-01–K-24 have allocated executable SHACL/query/lint artefacts; negative evidence proves every local shape and automated build guard fires. K-22 still requires the recorded manual publication review.
- Step 5: railway architecture instance profile and minimal conforming/non-conforming fixtures.
- Step 6: 54/54 legacy rules have explicit `map` or `refactor` decisions. M5 contains the reviewed structural scaffold for transmission categories, seven threat types, railway asset safety classes, SIL values, access and fail-safe dependency.
- Step 7: CQ-01–CQ-45 all exist and parse. The coverage registry records 9 value-oracle CQs, 4 empty-by-design CQs and 32 explicitly pending CQs; CQ-09 has a full vertical-slice regression.
- Step 8: the legacy workbook was inspected sheet-by-sheet and mapped (not copied) into a 4,123-triple ETCS M6 ABox. It passes OWL 2 DL, HermiT and structural SHACL; unmapped source fields and legacy-result differences are accounted for.
- Phase 2 Step 9: the first M5 executable slice separates architecture facts, attributed access-exclusion assumptions, three-valued CriterionEvaluation records and entailed EN 50159 category membership. Payload, threat and eight channel-defence terms are present; safeguard/threat links are documentation annotations only.
- Phase 2 Step 10: `undeterminedBoundary` is explicit and boundary-assessment coverage retains it in the denominator.
- Phase 2 Step 11/12: a minimal synthetic fixture covers Category 1, Category 2, Category 3 and an undetermined category outcome. It will grow with subsequent rule blocks rather than being designed upfront.
- Phase 2 prerequisite for Step 12.2: generic evaluation-stage coverage reports candidate/determined/undetermined counts; the current category fixture proves 3/5 determined. A no-input flow produces three undetermined evaluations, and a two-category flow is rejected by HermiT.
- Phase 2 Step 12.2: the seven transmission threats are evaluated independently from upstream category evaluations. The synthetic fixture proves simultaneous threats without direct multi-typing, protected and non-applicable outcomes, and propagation of unknown category status; 4/6 threat-stage candidates are determined.
- Phase 2 Step 12.3: safety-critical elevation (M5-R04) implements legacy R2.3.1 and R2.3.2, the two Block 2.3 rules expressible with the approved payload distinction. It consumes upstream threat evaluations and payload classification, propagates both unknown inputs as `undetermined`, and never types a flow directly with a violation. Legacy R2.3.3 and R2.3.4 require an unapproved payload-vocabulary revision (CR-B-013).
- Phase 2 Step 12.4: fail-safe compromise (M5-R05) implements legacy R2.4.1 and R2.4.2 as three-valued evaluations of safety-critical assets. It consumes incoming critical-violation evaluations and explicit `realises` / `failSafeDependsOn` architecture facts; unknown upstream results or dependencies remain `undetermined`. Legacy R2.4.3 is deferred because mobile-zone and remediation-priority vocabulary is not approved (CR-B-014).

- Phase 2 Step 12.5: maximum SIL risk (M5-R06). Legacy v3 R2.5.3 implemented as an asset evaluation aggregating the fail-safe stage; an asset with no upstream evaluation receives no result rather than a default. Eleven tests, three mutation checks. R2.5.1 and R2.5.2 are blocked on an absent attack technique vocabulary (CR-B-015).

- Phase 2 Step 12.6: access risk (M5-R07, M5-R08). Legacy v3 R2.6.1-R2.6.4 implemented across two subjects; R2.6.1 is re-subjected from the maintenance actor to the safety-critical asset because actors and roles are not in the approved model. Thirteen tests, five mutation checks (CR-B-016).

- Phase 2 Step 12.7: classification provenance (K-25). All nine ETCS safety-critical assets and the five synthetic fixture assets now carry reified classification assumptions with a judgement basis and an attributed agent. Fifteen tests, five shape mutation checks. The classification remains an assumption: no safety case was available, and no source was invented (CR-B-017).

- Phase 2 Step 13: Run orchestrator. Executes the stages as one controlled analysis with bounded iteration, refusal semantics and run-scoped results. Exposed and fixed two defects invisible to single-Run stage tests: colliding result identifiers across Runs, and asymmetric instance-set joins producing derivations that cite results never created. Determinism is now evidenced by test rather than claimed (CR-B-019).

## Canonical Phase 2 numbering correction

The revised sixteen-step plan remains authoritative. Later working labels did
not renumber its final steps: CR-B-021/022 are enabling and ETCS-track changes,
and CR-B-023 is an additional Step 12 L1 rule slice. Canonical Step 13 remains
implemented for the admitted scope: reachability, witness paths, candidate projection, AHP factor values, weighted ordering and selection coverage are now implemented; canonical Step 14 is CQ
oracles (27 answered, 5 empty by design, 13 pending after railway source locations were formalised); canonical Step 15 is a
predeclared performance target; canonical Step 16 is the retained EV-B1–EV-B11
evidence package. See `PHASE2_EXECUTION.md` and `PHASE2_GAP_AUDIT.md`.

## Release blockers (not hidden as implementation completion)

1. Deferred legacy rules still need implement/retire/future-version decisions before ontology completion.
2. The 13 pending CQs still need their producing capability or an explicit non-ontology-scope decision; the registry makes this gap visible but does not close it.
3. The workbook-derived boundary mapping (External primary zone → `external`, otherwise `inScope`) needs domain approval.
4. DataObjects, Actors/Roles, interface security flags and the old AHP model remain explicitly unmapped, with reasons in `cases/etcs/unmapped.csv`.
5. K-22 manual copyright/source-text review and w3id redirect registration remain release actions.
6. Railway criteria now carry source-location and interpretation records, but standards that were only available through legacy/project evidence retain secondary consultation status until publication review.
7. Threat, safety-critical elevation, fail-safe, SIL-risk, access-risk and control-weakness criteria are executable; remaining ontology-completion work is the deferred-rule boundary and any admitted vocabulary additions.
8. The ETCS ABox explicitly types nine assets as `SafetyCriticalAsset`, but none of those classifications has a supporting `AssertedFact` or `JudgementBasis`. Because Steps 12.3–12.6 depend on that classification, this provenance gap must be resolved before the ETCS case is executed by the orchestrator; no source or judgement is fabricated as a default.
