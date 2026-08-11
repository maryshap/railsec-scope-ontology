# D-B8b — PROV-O mapping

**Status:** initial formal mapping for the 0.1.0 baseline.  
**Authority:** D-B8a and the frozen Gate B conceptual package.

## Class mappings

| Project class | PROV-O class | Mapping | Rationale |
|---|---|---|---|
| `rss-core:Assertion` | `prov:Entity` | subclass | Assertions are identifiable inputs used by activities. |
| `rss-crit:VersionedArtefact` | `prov:Entity` | subclass | Versioned artefacts are entities used by Runs and steps. |
| `rss-crit:Criterion` | `prov:Entity` | inherited subclass | Criterion-specific semantics remain local. |
| `rss-crit:ExternalComputationMethod` | `prov:Plan` | subclass | The method is a plan followed by an external computation, not the executing activity. |
| `rss-res:DerivedResult` | `prov:Entity` | subclass | Results are generated entities. |
| `rss-res:UnresolvedInput` | `prov:Entity` | subclass | It is an identifiable record, not an assertion that the missing fact is false. |
| `rss-res:PerformanceMeasurement` | `prov:Entity` | subclass | A measurement is generated evidence about a Run. |
| `rss-res:Run` | `prov:Activity` | subclass | A Run is the encompassing execution activity. |
| `rss-res:DerivationStep` | `prov:Activity` | subclass | Each step uses and generates entities. |
| `rss-res:Mechanism` | `prov:SoftwareAgent` | subclass | The versioned mechanism bears responsibility for executing a step. |
| `rss-res:DerivationRecord` | `prov:Bundle` | subclass | The record is a named provenance bundle assembled across layers. |

Subclass mappings are used rather than equivalence because the project classes carry stronger domain-specific meaning and constraints.

## Property mappings

| Project property | PROV-O property | Mapping |
|---|---|---|
| `rss-res:producedByRun` | `prov:wasGeneratedBy` | subproperty |
| `rss-res:usedVersion` | `prov:used` | subproperty |
| `rss-res:usedInstanceSet` | `prov:used` | subproperty |
| `rss-res:usedEntity` | `prov:used` | subproperty |
| `rss-res:generatedResult` | `prov:generated` | subproperty |
| `rss-res:appliedCriterion` | `prov:used` | subproperty |
| `rss-res:executedByMechanism` | `prov:wasAssociatedWith` | subproperty |

M5 access-exclusion assumptions use the projected `prov:wasAttributedTo` property directly so the assessor responsible for the judgement is machine-readable. No local subproperty is introduced.

`rss-res:appliedComputation` is deliberately **not** a subproperty of `prov:hadPlan`: `prov:hadPlan` relates a qualified Association to a Plan, not an Activity directly to a Plan. If qualified associations are required in the derivation implementation, the orchestrator will emit a `prov:Association` with `prov:hadPlan`; the direct project property remains the domain query shortcut.

## Import policy

Production modules import the stable PROV-O ontology IRI `http://www.w3.org/ns/prov-o`. The build must resolve it to a locally pinned, checksum-recorded copy; tests must not depend on live network retrieval. No project class or property is declared equivalent to a PROV-O term in the 0.1.0 line.
