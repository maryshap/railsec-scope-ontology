# Railway architecture instance profile

This is the contract for any case dataset loaded as M6. Conformance means that the dataset can be processed; it does not mean that the architecture is secure or that the data is complete enough for every criterion.

## Validation graph contract

- One validation graph represents exactly one `InstanceSet` version.
- Every architecture `Element` in that graph is explicitly typed and has exactly one `BoundaryStatusAssertion` in that same `InstanceSet`.
- Case IRIs use `https://w3id.org/railsec-scope/case/{case-id}/resource/{local-id}` and never mint schema terms.
- The graph records its `ArtefactVersion`, source mapping and generating/import `Run`.
- Unknown criterion inputs are absent and lead to `undetermined` evaluations. Boundary status is the deliberate exception: an explicitly reviewed but unresolved element carries `undeterminedBoundary`, distinct from a missing assertion. Assumptions and asserted absences are distinct Assertion individuals with explicit epistemic status.

## Minimum architecture capability

A conforming profile can represent Assets and their types/roles/functions; Interfaces and InformationFlows with one origin and destination; Groups and connections; access mechanisms and supported preconditions; boundary and authorisation assertions; property-loss scenarios, consequences and direct dependencies; and examination constraints.

Optional records become mandatory when used by a criterion. For example, a criterion that examines a flow characteristic requires the corresponding `FlowCharacteristic` assertion. Missing decisive information produces an `undetermined` evaluation and an `UnresolvedInput`, not a false assertion.

## Processing stages

1. Validate asserted structure (SHACL, without domain/range inference).
2. Classify the OWL 2 DL graph with HermiT.
3. Execute declared monotonic DL-safe L2 rules over named individuals; rules may create three-valued `CriterionEvaluation` records.
4. Repeat reasoner and rules to a triple-set fixed point, warning above three rounds and failing at ten.
5. Materialise only already-entailed category memberships and enforce K-23/K-24 plus post-rule SHACL.
6. Run L3 computations, selection and coverage without treating them as semantic producers of membership.

The minimal positive contract fixture is `fixtures/architecture/positive.ttl`; `fixtures/k-constraints/negative-all.ttl` proves structural rejection. Both are synthetic test artefacts, not portability evidence.
