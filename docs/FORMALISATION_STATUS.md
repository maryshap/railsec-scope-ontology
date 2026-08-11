# Formalisation status

**Baseline:** 0.1.0 development line  
**Conceptual source:** frozen Gate B v1.0 candidate

## Implemented and verified

- Step 0: namespace/IRI decision, acyclic import graph, pinned PROV-O source/DL projection, ROBOT OWLAPI profile validation, HermiT consistency/classification, committed inferred hierarchy, CI.
- Step 1: 76/76 M1–M4 classes; all 90 original project object properties and 42 original datatype properties have domains/ranges; sibling disjointness and value closure; CR-B-001/002 resolve the two known defects.
- Step 2: CriterionEvaluation vertical slice with exact OWL cardinalities, L2-R01, K-11/K-23/K-24, positive/negative fixtures and asserted CQ-09 result.
- Step 3: the generated 76-row entity matrix records module, named superclasses, property participation, restriction count, disjointness and K-allocation.
- Step 4: K-01–K-24 have allocated executable SHACL/query/lint artefacts; negative evidence proves every local shape and automated build guard fires. K-22 still requires the recorded manual publication review.
- Step 5: railway architecture instance profile and minimal conforming/non-conforming fixtures.
- Step 6: 54/54 legacy rules have explicit `map` or `refactor` decisions. M5 contains the reviewed structural scaffold for transmission categories, seven threat types, railway asset safety classes, SIL values, access and fail-safe dependency.
- Step 7: CQ-01–CQ-45 all exist, parse and execute against representative fixtures. CQ-09 has a full expected-answer regression.
- Step 8: the legacy workbook was inspected sheet-by-sheet and mapped (not copied) into a 4,123-triple ETCS M6 ABox. It passes OWL 2 DL, HermiT and structural SHACL; unmapped source fields and legacy-result differences are accounted for.
- Phase 2 Step 9: the first M5 executable slice separates architecture facts, attributed access-exclusion assumptions, three-valued CriterionEvaluation records and entailed EN 50159 category membership. Payload, threat and eight channel-defence terms are present; safeguard/threat links are documentation annotations only.
- Phase 2 Step 10: `undeterminedBoundary` is explicit and boundary-assessment coverage retains it in the denominator.
- Phase 2 Step 11/12: a minimal synthetic fixture covers Category 1, Category 2, Category 3 and an undetermined category outcome. It will grow with subsequent rule blocks rather than being designed upfront.
- Phase 2 prerequisite for Step 12.2: generic evaluation-stage coverage reports candidate/determined/undetermined counts; the current category fixture proves 3/5 determined. A no-input flow produces three undetermined evaluations, and a two-category flow is rejected by HermiT.

## Release blockers (not hidden as implementation completion)

1. Every legacy-rule triage row is `domain-review-required`; M5 criterion/rule content cannot be released from unverified standard citations.
2. CQ-01–CQ-45 still need their complete Gate A P/N/U expected-answer fixture matrix; parsing and smoke execution alone are not scientific validation.
3. The workbook-derived boundary mapping (External primary zone → `external`, otherwise `inScope`) needs domain approval.
4. DataObjects, Actors/Roles, interface security flags and the old AHP model remain explicitly unmapped, with reasons in `cases/etcs/unmapped.csv`.
5. K-22 manual copyright/source-text review and w3id redirect registration remain release actions.
6. The synthetic EN 50159 category criteria currently rest on an explicit provisional JudgementBasis. Exact standard edition, source locations and reviewed interpretations are still required before release.
7. Threat, safety-critical elevation, fail-safe, SIL/override and access-path rule blocks, followed by the orchestrator/L3 implementation, remain Phase 2 work.
