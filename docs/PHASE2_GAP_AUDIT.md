# Phase 2 gap audit

**Audit basis:** the revised sixteen-step implementation plan and the current
`main` after PR #5.

## Result

Steps 9–12 are implemented for their admitted scope. Step 13 is incomplete and
Steps 14–16 are open. The implementation previously called “Step 15” passed CI,
but it is an additional L1 control-weakness rule slice, not the performance
target defined by canonical Step 15.

## Step 13 gaps

| Capability | Present | Gap |
|---|---|---|
| Run orchestration | Yes | None for the minimal contract |
| bounded reasoner/rules loop | Yes | None for the minimal contract |
| L3 hook inside the loop | Yes | Executes declared computations and remains inside fixed-point iteration |
| reachability closure | Yes | Run-scoped results from L1/L2 EntryPoint assignments over vulnerable directed flows |
| dependency paths | Yes | Deterministic shortest witness chains with positioned entries |
| candidate-set projection | Yes | Built only from materialised candidate assignments in the same Run |
| factor computation | No | Needs declared factors and evidence basis |
| weighted ordering | No | Needs an admitted, versioned method; legacy AHP must not be copied silently |
| selection/coverage | Yes | Runs only for an explicit `Selection`; an assessor choice is never invented |
| L3 provenance | Yes | Results identify Run, versioned method/mechanism and derivation records |

### Ordering decision still required

The ontology can represent `OrderingFactor`, `OrderingFactorSet`, `FactorValue`,
`OrderingResult` and a versioned `ExternalComputationMethod`. It deliberately
does not select factor weights or an aggregation algorithm. Therefore “replace
AHP” is a domain/method admission decision, not a missing Python loop.

The implementation may safely proceed with reachability/path closure and the
generic ordering interface. A production factor set and its weights must be
recorded as a versioned method decision before any ordering result is claimed.

## Step 14 gaps

- 21/45 CQs have value oracles after the Step 13 reachability/coverage fixture;
- 5/45 are empty by design;
- 19/45 remain explicit pending capabilities.

Pending questions must be promoted only when their producing capability exists
and a positive/negative/undetermined fixture has an asserted expected answer.

## Step 15 gap

The vocabulary for `PerformanceTarget`, fixture identifier, measured stage and
threshold exists. No target individual exists. The recorded 180-second ETCS
threat observation is a measurement and cannot retroactively become the target.
A new fixed synthetic fixture/environment and a numerical threshold must be
committed before the benchmark is executed.

## Step 16 gap

EV-B1–EV-B11 are obligations, not merely test names. Some earlier fixtures cover
parts of EV-B1–EV-B7 and EV-B9, but retained outputs and an evidence index do not
exist. EV-B10 depends on Step 15. EV-B11 may stay open beyond ontology
construction, but its ETCS evidence sources and comparison protocol must be
identified before Gate B closure.

## Additional release/domain gaps outside Phase 2 implementation closure

- normative source review for provisional criteria;
- six deferred legacy L2 rules and the decision to implement or retire each;
- ETCS case fact completeness and provenance;
- boundary-derivation domain approval;
- w3id redirect, copyright/source-text review and final publication review.

These remain visible blockers, but they must not be confused with canonical
Steps 13–16.
