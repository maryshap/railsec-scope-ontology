# Conceptual Model — Gate B package

**Sections 8–15 of the requirements document. Version 1.0 candidate for Gate B closure.**

This package is a conceptualisation. It defines the entities, specialisations, relations, attributes, constraints, modules, processing ownership, derivation structure and evaluation obligations that precede formal encoding. It contains no production OWL, SWRL, SHACL or SPARQL syntax. A small isolated proof of concept has tested selected modelling and constraint-enforcement patterns; it is not the production ontology.

## Scope boundary

The intended artefact is an ontology-based framework for representing and assessing **railway system architectures across railway subsystems**. It is not an ETCS ontology. ETCS is the first and, in this study, the only full empirical case study.

The stable framework and railway profile are designed not to depend on one subsystem. This is a design property, not evidence that cross-subsystem applicability has already been empirically demonstrated. A future claim of empirical portability requires an independently sourced second architecture. Until then the defensible claim is:

> The model is designed to be subsystem-independent within the railway domain and is empirically evaluated on an ETCS case study.

Every concrete architecture is represented by a separate versioned ABox conforming to a common railway architecture instance profile. There is no generic architecture ABox. ETCS-, TCMS- and CBTC-specific architecture individuals belong to separate case datasets.

Every entity and relation below is justified by an approved requirement, operational definition or source-record schema from Gate A. A construct may not enter the production ontology merely because it existed in the legacy implementation.

---

## 8. Conceptual entities and hierarchy

### 8.1 System description

These entities describe an architecture under assessment. Architecture individuals are asserted in a case ABox; assessment-bearing classifications are never asserted there.

| Entity | Meaning | From |
|---|---|---|
| Element | Individually referable entity eligible to participate in boundary, architecture, dependency or scoping relations | Gate A §4.1 |
| Asset | Element representing a component of the described system | ORF-01 |
| Interface | Element at which assets exchange information | ORF-03 |
| InformationFlow | Directed element representing information passing between an origin and a destination | ORF-03 |
| FlowCharacteristic | Represented property of a flow held independently of a criterion that may use it | ORF-07 |
| AssetType | Classification of an asset by kind | ORF-01 |
| SystemRole | Role an asset plays in the described system | ORF-01 |
| Function | Capability the system performs; a Function is not an Element | Gate A §4.1 |
| SafetyFunction | Function whose loss carries a safety consequence | ORF-15 |
| Group | Grouping construct over assets | ORF-04 |
| GroupConnection | Directed or undirected connection between two groups | ORF-04 |
| AccessMechanism | Means by which an element can be reached | ORF-08 |
| AccessPrecondition | Condition that must hold for an access mechanism to be usable | ORF-09 |
| SecurityProperty | Property of an element or flow whose loss is assessed | ORF-16 |
| PropertyLossScenario | Pairing of an element with the loss of one security property | ORF-16–ORF-18 |
| Consequence | Outcome associated with a property-loss scenario | ORF-17 |
| ExaminationConstraint | Safety or operational constraint applying to examination of an element | ORF-24 |
| AuthorisationStatus | Controlled externally supplied status concerning permission; never a model-derived status | ORF-25 |

### 8.2 Assertions and epistemic state

| Entity | Meaning | From |
|---|---|---|
| Assertion | Individually referable statement used as architecture or assessment input, with provenance and epistemic status | ORF-09, ORF-31, ORF-35 |
| AssertedFact | Assertion presented as established | ORF-09 |
| Assumption | Assertion presented as supposed rather than established, carrying its basis | ORF-09 |
| AssertedAbsence | Assertion that a property does not hold or a relation does not obtain | ORF-35 |
| BoundaryStatusAssertion | Assertion assigning one boundary-status value to one element within one versioned instance set | ORF-05, ORF-46 |
| AuthorisationAssertion | Externally supplied assertion assigning an authorisation status to an element | ORF-25 |
| BoundaryStatusValue | Closed value vocabulary: in-scope, out-of-scope or external | ORF-05 |
| EpistemicStatusValue | Closed value vocabulary: asserted fact, assumption or asserted absence | ORF-09, ORF-35 |
| EvaluationOutcome | Closed criterion-evaluation outcome: satisfied, not satisfied or undetermined | ORF-36 |
| ComputationOutcome | Closed computation outcome: value present or not computable | ORF-41 |

Unknown is the absence of an applicable assertion within the declared input graph. It is not an individual or a false assertion. Undetermined and not-computable are outcomes recorded on results, never categories of Element.

### 8.3 Criteria, sources and measures

| Entity | Meaning | From |
|---|---|---|
| Criterion | Named, versioned logical statement determining assessment-bearing membership or factor applicability | Gate A §4.1, ORF-26 |
| AssessmentBearingCategory | Classification whose membership can affect candidacy, ordering or coverage | Gate A §4.1 |
| CandidateExaminationTarget | Principal assessment-bearing category for scoping | ORF-12 |
| EntryPoint | Assessment-bearing category of elements reachable from outside the modelled boundary | ORF-10 |
| Source | Document or resource from which one or more criteria are derived | ORF-27, Gate A §7.1 |
| SourceEdition | Specific edition or version of a Source relied upon | ORF-27, Gate A §7.1 |
| SourceLocation | Referenced location within a SourceEdition | ORF-27 |
| Interpretation | Recorded proposition explaining how one or more source locations are read, with reasoning, confidence and review status | ORF-28, Gate A §7.2 |
| JudgementBasis | Recorded reasoning supporting a criterion not derived from a source | ORF-30 |
| OrderingFactor | Named, versioned factor used in ordering candidates | ORF-20 |
| OrderingFactorSet | Identified, versioned collection of ordering factors used together | ORF-22 |
| ExternalComputationMethod | Declared, versioned method executed outside L1/L2; not itself a criterion | Gate A §4.1, ORF-12 |
| CoverageMeasure | Named, versioned measure with definition, eligibility scope and exclusions | ORF-40 |

### 8.4 Results and identified collections

| Entity | Meaning | From |
|---|---|---|
| DerivedResult | Individually referable outcome produced by a declared mechanism in a Run | ORF-31, ORF-45 |
| CriterionEvaluation | Result binding an Element, Criterion, Run and one EvaluationOutcome | ORF-12, ORF-36 |
| CategoryAssignment | Materialised record of a satisfied evaluation whose corresponding assessment-bearing membership was entailed in L1 or L2 | ORF-12, ORF-13, ORF-45 |
| CandidateSet | Identified collection of CandidateExaminationTarget assignments produced in one Run | ORF-14, ORF-42 |
| ReachabilityResult | Result recording that an element is reachable, with access mechanism and preconditions used | ORF-10, ORF-11 |
| DependencyChain | Result recording one ordered dependency path between an element and a function | ORF-19 |
| DependencyChainEntry | One positioned node in a DependencyChain | ORF-19 |
| SafetyImpactResult | Result recording which safety functions a property-loss scenario affects | ORF-18 |
| FactorValue | Result recording the value of an OrderingFactor for a candidate assignment and its basis | ORF-21 |
| OrderingResult | Versioned result produced for one CandidateSet by one factor set and method | ORF-22, ORF-23 |
| OrderingEntry | One positioned candidate assignment within one OrderingResult | ORF-23 |
| CoverageResult | Result recording a coverage value or not-computable outcome relative to a CandidateSet and Selection | ORF-41, ORF-42 |
| OutputProfile | Versioned declaration of which results are exposed as decision evidence | Gate A §4.1, ORF-31 |
| MaterialFindingDesignation | Contextual designation of a DerivedResult as a material finding under an OutputProfile | Gate A §4.1, ORF-31 |
| Run | Identified execution under declared artefact versions and environment | ORF-45, ORF-46, ORN-02a |
| RunComparison | Result identifying changed inputs and changed results between exactly two Runs | ORF-46 |

Material finding is a contextual role of a DerivedResult, not a fixed subclass list. Changing an OutputProfile does not change prior derivations; it changes which results must be exposed with complete derivation evidence in a new release context.

### 8.5 Assessor records

| Entity | Meaning | From |
|---|---|---|
| Selection | Identified, versioned collection of elements an assessor records as included in an assessment | ORF-42 |
| AssessorDecision | Identified, versioned act concerning one DerivedResult, carrying rationale and never altering the result | ORF-48 |
| Inclusion | AssessorDecision adding an element to a Selection | ORF-48 |
| Exclusion | AssessorDecision omitting a derived candidate from a Selection | ORF-48 |
| Override | AssessorDecision stating treatment different from that indicated by a DerivedResult | ORF-13, ORF-48 |
| Rationale | Individually referable reason attached to a decision or boundary exclusion | ORF-06, ORF-48 |

### 8.6 Derivation, version and execution

| Entity | Meaning | From |
|---|---|---|
| DerivationRecord | Provenance bundle linking one designated material result to the activities and entities that produced it | ORF-31 |
| DerivationStep | One identified production activity within a DerivationRecord | ORF-32 |
| Mechanism | Versioned software or reasoning mechanism executing a DerivationStep | ORF-32, ORN-01 |
| UnresolvedInput | Record of a required input encountered as unknown or not computable | ORF-33 |
| VersionedArtefact | Common conceptual superclass for artefacts required to carry version identity | ORF-45 |
| ArtefactVersion | Version identity assigned to a VersionedArtefact | ORF-45 |
| OntologyModule | Versioned authored ontology module | ORF-43–ORF-45 |
| InstanceSet | Versioned set of input assertions constituting one concrete architecture dataset | ORF-45 |
| TerminologyTerm | Individually referable ontology term for lifecycle metadata and deprecation | ORF-47 |
| Deprecation | Record retaining a deprecated term or criterion and its replacement status | ORF-47 |
| ExecutionEnvironment | Recorded hardware and software configuration for an execution | ORN-02a |
| PerformanceMeasurement | Stage-specific execution time and input-size observation from a Run | ORN-02a |
| PerformanceTarget | Versioned target defined for a fixed representative fixture and environment | ORN-02b |

### 8.7 Specialisation hierarchy

The following specialisations are part of the conceptual TBox and must not remain implicit in prose.

| More specific | More general |
|---|---|
| Asset, Interface, InformationFlow | Element |
| SafetyFunction | Function |
| AssertedFact, Assumption, AssertedAbsence, BoundaryStatusAssertion, AuthorisationAssertion | Assertion |
| CandidateExaminationTarget, EntryPoint | AssessmentBearingCategory |
| CriterionEvaluation, CategoryAssignment, CandidateSet, ReachabilityResult, DependencyChain, SafetyImpactResult, FactorValue, OrderingResult, CoverageResult, RunComparison | DerivedResult |
| Inclusion, Exclusion, Override | AssessorDecision |
| Criterion, OrderingFactor, OrderingFactorSet, ExternalComputationMethod, CoverageMeasure, OutputProfile, OntologyModule, InstanceSet, Selection, AssessorDecision, PerformanceTarget | VersionedArtefact |
| Mechanism, OrderingResult | VersionedArtefact |

Preliminary PROV-O reuse is also fixed conceptually: Assertion, Criterion, VersionedArtefact, DerivedResult, UnresolvedInput and PerformanceMeasurement align to `prov:Entity`; Run and DerivationStep align to `prov:Activity`; Mechanism aligns to an appropriate `prov:Agent` specialisation; ExternalComputationMethod aligns to `prov:Plan`; DerivationRecord aligns to `prov:Bundle`. Exact subclass, equivalence, subproperty and import choices belong to D-B8b during formalisation.

---

## 9. Conceptual relations and attributes

Relations are named by their reading, not by eventual OWL syntax. A direct binary property is retained unless an occurrence needs independent identity, context, provenance, outcome, role or position.

### 9.1 Architecture

| Relation | Domain → range | From |
|---|---|---|
| has asset type | Asset → AssetType | ORF-01 |
| plays role | Asset → SystemRole | ORF-01 |
| realises | Asset → Function | ORF-02 |
| has origin | InformationFlow → Element | ORF-03 |
| has destination | InformationFlow → Element | ORF-03 |
| traverses | InformationFlow → Interface | ORF-03 |
| has characteristic | InformationFlow → FlowCharacteristic | ORF-07 |
| member of | Asset → Group | ORF-04 |
| connects from | GroupConnection → Group | ORF-04 |
| connects to | GroupConnection → Group | ORF-04 |
| directly depends on | Element or Function → Element or Function | ORF-15 |
| applies to element | ExaminationConstraint → Element | ORF-24 |

`directly depends on` records only direct dependency edges. It is not declared transitive. L3 computes closure and concrete paths. If future approved requirements demand provenance or type on each edge, an identified DependencyLink may be introduced through a versioned Gate B change; it is not required now.

### 9.2 Assertions and boundary

| Relation | Domain → range | From |
|---|---|---|
| assertion subject | Assertion → individually referable subject | ORF-09, ORF-35 |
| assertion predicate | Assertion → represented property or statement type | ORF-09, ORF-35 |
| assertion object | Assertion → individually referable object or literal value | ORF-09, ORF-35 |
| has epistemic status | Assertion → EpistemicStatusValue | ORF-09, ORF-35 |
| status subject | BoundaryStatusAssertion → Element | ORF-05 |
| boundary status value | BoundaryStatusAssertion → BoundaryStatusValue | ORF-05 |
| asserted in instance set | Assertion → InstanceSet | ORF-45, ORF-46 |
| has exclusion rationale | BoundaryStatusAssertion → Rationale | ORF-06 |
| authorisation subject | AuthorisationAssertion → Element | ORF-25 |
| authorisation value | AuthorisationAssertion → AuthorisationStatus | ORF-25 |

`EpistemicStatusValue` is the closed vocabulary represented by the Assertion specialisations asserted fact, assumption and asserted absence. The final OWL representation must choose one non-duplicative encoding during formalisation: subclasses with inferred status values, or status values with constrained subclasses.

The three generic proposition relations above specify a conceptual assertion pattern, not a requirement to use one unconstrained universal predicate in OWL. Formalisation may implement typed assertion subclasses with specialised subject, predicate and object properties, provided the common query contract and epistemic distinction are preserved.

### 9.3 Exposure

| Relation | Domain → range | From |
|---|---|---|
| reachable by | Element → AccessMechanism | ORF-08 |
| requires precondition | AccessMechanism → AccessPrecondition | ORF-09 |
| precondition supported by | AccessPrecondition → Assertion | ORF-09 |
| reachability concerns | ReachabilityResult → Element | ORF-10 |
| used access mechanism | ReachabilityResult → AccessMechanism | ORF-11 |
| relied on precondition | ReachabilityResult → AccessPrecondition | ORF-11 |

### 9.4 Safety and consequence

| Relation | Domain → range | From |
|---|---|---|
| scenario concerns element | PropertyLossScenario → Element | ORF-16 |
| scenario concerns property | PropertyLossScenario → SecurityProperty | ORF-16 |
| has consequence | PropertyLossScenario → Consequence | ORF-17 |
| evaluates scenario | SafetyImpactResult → PropertyLossScenario | ORF-18 |
| affects function | SafetyImpactResult → SafetyFunction | ORF-18 |
| via dependency chain | SafetyImpactResult → DependencyChain | ORF-19 |
| has chain entry | DependencyChain → DependencyChainEntry | ORF-19 |
| chain node | DependencyChainEntry → Element or Function | ORF-19 |

### 9.5 Criteria and provenance

| Relation | Domain → range | From |
|---|---|---|
| determines membership of | Criterion → AssessmentBearingCategory | ORF-26 |
| determines applicability of | Criterion → OrderingFactor | Gate A §4.1 |
| derived from source location | Criterion → SourceLocation | ORF-27 |
| applies interpretation | Criterion → Interpretation | ORF-28 |
| rests on judgement | Criterion → JudgementBasis | ORF-30 |
| edition of | SourceEdition → Source | ORF-27, Gate A §7.1 |
| located in edition | SourceLocation → SourceEdition | ORF-27 |
| interprets | Interpretation → SourceLocation | ORF-28 |
| supersedes edition | SourceEdition → SourceEdition | Gate A §7.1 |
| has factor | OrderingFactorSet → OrderingFactor | ORF-22 |

A source-derived criterion may use multiple SourceLocations and Interpretations. The source-derived and judgement-based provenance branches remain mutually exclusive. Interpretive reasoning belongs to Interpretation, so applying judgement when reading a source does not convert a source-derived criterion into an unattributed judgement-based criterion.

### 9.6 Results and derivation

| Relation | Domain → range | From |
|---|---|---|
| produced by run | DerivedResult → Run | ORF-45 |
| evaluation concerns element | CriterionEvaluation → Element | ORF-36 |
| evaluates criterion | CriterionEvaluation → Criterion | ORF-36 |
| has evaluation outcome | CriterionEvaluation → EvaluationOutcome | ORF-36 |
| materialises evaluation | CategoryAssignment → CriterionEvaluation | ORF-12, ORF-13 |
| assigns category | CategoryAssignment → AssessmentBearingCategory | ORF-12 |
| has candidate assignment | CandidateSet → CategoryAssignment | ORF-14 |
| has derivation record | DerivedResult → DerivationRecord | ORF-31 |
| has step | DerivationRecord → DerivationStep | ORF-31 |
| used entity | DerivationStep → Assertion, DerivedResult or VersionedArtefact | ORF-31 |
| generated result | DerivationStep → DerivedResult | ORF-31 |
| applied criterion | DerivationStep → Criterion | ORF-31 |
| applied computation | DerivationStep → ExternalComputationMethod | ORF-12, ORF-31 |
| executed by mechanism | DerivationStep → Mechanism | ORF-32 |
| has unresolved input | DerivationRecord → UnresolvedInput | ORF-33 |
| designates result | MaterialFindingDesignation → DerivedResult | ORF-31 |
| under output profile | MaterialFindingDesignation → OutputProfile | ORF-31 |

### 9.7 Ordering and coverage

| Relation | Domain → range | From |
|---|---|---|
| factor value for candidate | FactorValue → CategoryAssignment | ORF-21 |
| value of factor | FactorValue → OrderingFactor | ORF-21 |
| value basis | FactorValue → Assertion or JudgementBasis | ORF-21 |
| orders candidate set | OrderingResult → CandidateSet | ORF-23 |
| uses factor set | OrderingResult → OrderingFactorSet | ORF-22 |
| produced by method | OrderingResult → ExternalComputationMethod | ORF-23 |
| has ordering entry | OrderingResult → OrderingEntry | ORF-23 |
| ranks assignment | OrderingEntry → CategoryAssignment | ORF-23 |
| evaluates measure | CoverageResult → CoverageMeasure | ORF-40, ORF-41 |
| measured candidate set | CoverageResult → CandidateSet | ORF-40, ORF-42 |
| measured selection | CoverageResult → Selection | ORF-40, ORF-42 |
| has computation outcome | FactorValue or CoverageResult → ComputationOutcome | ORF-41 |

### 9.8 Selection and decisions

| Relation | Domain → range | From |
|---|---|---|
| includes element | Selection → Element | ORF-42 |
| selection based on candidate set | Selection → CandidateSet | ORF-42 |
| concerns result | AssessorDecision → DerivedResult | ORF-48 |
| affects selection | AssessorDecision → Selection | ORF-48 |
| has rationale | AssessorDecision → Rationale | ORF-48 |

### 9.9 Versioning, comparison and performance

| Relation | Domain → range | From |
|---|---|---|
| has version | VersionedArtefact → ArtefactVersion | ORF-45 |
| used version | Run → ArtefactVersion | ORF-45 |
| used instance set | Run → InstanceSet | ORF-45 |
| compares run | RunComparison → Run | ORF-46 |
| changed assertion | RunComparison → Assertion | ORF-46 |
| changed result | RunComparison → DerivedResult | ORF-46 |
| deprecated by | TerminologyTerm or Criterion → Deprecation | ORF-47 |
| replaced by | Deprecation → TerminologyTerm or Criterion | ORF-47 |
| executed in environment | Run → ExecutionEnvironment | ORN-02a |
| measured run | PerformanceMeasurement → Run | ORN-02a |
| assessed against target | PerformanceMeasurement → PerformanceTarget | ORN-02b |

### 9.10 Conceptual attributes

Literal-valued information is specified conceptually here and will become datatype properties or annotations during formalisation.

| Entity | Required or permitted attributes | From |
|---|---|---|
| All individually referable records | stable identifier | ORN-03 |
| Criterion | criterion statement/expression; lifecycle status | ORF-26 |
| Source | full reference; role; access condition; reproduction restriction | Gate A §7.1, ORN-05 |
| SourceEdition | edition/version label; publication date; access date; consultation status | ORF-27, Gate A §7.1, §7.4 |
| SourceLocation | locator within edition | ORF-27 |
| Interpretation | proposition; reasoning; confidence; review status | ORF-28, Gate A §7.2 |
| JudgementBasis | reasoning; revision conditions | ORF-30, Gate A §7.3 |
| Rationale | rationale text | ORF-06, ORF-48 |
| DerivationRecord | completeness status | ORF-34 |
| DerivationStep | step position; layer identifier | ORF-31, ORF-32 |
| DependencyChainEntry | path position | ORF-19 |
| FactorValue | represented value when present | ORF-21 |
| OrderingEntry | position and optional tie identifier | ORF-23 |
| CoverageMeasure | definition; eligibility scope; exclusion declaration | ORF-40 |
| CoverageResult | represented value when present | ORF-41 |
| Run | run identifier; start/end time | ORF-45, ORN-02a |
| ArtefactVersion | version identifier | ORF-45 |
| ExecutionEnvironment | hardware configuration; operating system; runtime and dependency versions | ORN-02a |
| PerformanceMeasurement | stage; elapsed time; input size and unit | ORN-02a |
| PerformanceTarget | measured stage; threshold; representative fixture; fixed environment | ORN-02b |

---

## 10. Status models and structural constraints

### 10.1 Closed value vocabularies

Six value vocabularies are closed for validation. Extension is a versioned change requiring regression re-execution.

| Status model | Values | Applies to |
|---|---|---|
| Boundary status | in-scope, out-of-scope, external | BoundaryStatusAssertion |
| Evaluation outcome | satisfied, not satisfied, undetermined | CriterionEvaluation |
| Computation outcome | value present, not computable | FactorValue, CoverageResult |
| Epistemic status | asserted fact, assumption, asserted absence | Assertion |
| Interpretation confidence | established, reasoned, provisional | Interpretation |
| Source consultation | full, partial, secondary | SourceEdition |

### 10.2 Structural constraints

These constraints are integrity conditions over declared validation graphs and processing stages. They are not interpreted as OWL closed-world semantics.

| ID | Constraint | From |
|---|---|---|
| K-01 | For every Element in an InstanceSet, exactly one BoundaryStatusAssertion assigns exactly one BoundaryStatusValue | ORF-05 |
| K-02 | Every out-of-scope BoundaryStatusAssertion has at least one exclusion Rationale | ORF-06 |
| K-03 | Every InformationFlow has exactly one origin and exactly one destination | ORF-03 |
| K-04 | Every AccessPrecondition is supported by at least one Assertion with explicit epistemic status | ORF-09 |
| K-05 | Every Criterion follows exactly one provenance branch: one or more source locations with applicable interpretations, or one or more JudgementBasis records | ORF-27, ORF-28, ORF-30 |
| K-06 | Every SourceLocation is in one registered SourceEdition carrying consultation status | Gate A §7.1, §7.4 |
| K-07 | Every VersionedArtefact has exactly one current ArtefactVersion within a release context | ORF-45 |
| K-08 | Every result designated material under an OutputProfile has exactly one complete DerivationRecord | ORF-31 |
| K-09 | Every DerivationStep identifies one Mechanism and version and at least one applied Criterion or ExternalComputationMethod | ORF-32 |
| K-10 | Every required input encountered as unknown or not computable is represented by an UnresolvedInput in the affected DerivationRecord | ORF-33 |
| K-11 | Every CategoryAssignment materialises exactly one satisfied CriterionEvaluation and has a DerivationRecord | ORF-12, ORF-13 |
| K-12 | No AuthorisationAssertion is generated by a DerivationStep | ORF-25 |
| K-13 | Every AssessorDecision has a version, concerns exactly one DerivedResult and carries at least one Rationale | ORF-48 |
| K-14 | No AssessorDecision is used as evidential input by a DerivationStep | ORF-13 |
| K-15 | Every OrderingResult identifies one CandidateSet, one OrderingFactorSet version and one method version | ORF-22, ORF-23 |
| K-16 | A position exists only on an OrderingEntry or DependencyChainEntry, never intrinsically on a candidate or node | ORF-19, ORF-23 |
| K-17 | Every CoverageMeasure has a definition, eligibility scope and explicit exclusions, including an explicit empty exclusion set where applicable | ORF-40 |
| K-18 | Every Selection identifies the CandidateSet against which it was made, and every CoverageResult identifies a CoverageMeasure, the same CandidateSet and that Selection | ORF-40, ORF-42 |
| K-19 | No case-specific architecture individual occurs in M1–M5 terminology modules or reusable reference data | ORF-43 |
| K-20 | No subsystem-specific Criterion occurs in M1–M4 | ORF-43 |
| K-21 | A deprecated TerminologyTerm or Criterion is retained and records a replacement or explicit non-replacement | ORF-47 |
| K-22 | No published artefact reproduces protected source text; it records references and author-written interpretations | ORN-05 |
| K-23 | Every CategoryAssignment corresponds, in the same Run and version context, to assessment-bearing membership entailed by L1 or L2 | ORF-12, ORF-13, ORF-45 |
| K-24 | No L3 computation, materialiser or AssessorDecision is accepted as the semantic producer of assessment-bearing membership | ORF-12, ORF-13 |

### 10.3 Constraint-enforcement allocation

| Constraint | Authoritative enforcement |
|---|---|
| K-01 | SHACL-SPARQL over Element, InstanceSet and BoundaryStatusAssertion |
| K-02 | SHACL Core or SHACL-SPARQL conditional constraint |
| K-03–K-09 | SHACL Core, using `sh:xone` for K-05 where applicable |
| K-10 | Orchestrator capture followed by SHACL validation |
| K-11 | SHACL Core; semantic agreement separately enforced by K-23 |
| K-12 | SHACL-SPARQL, optionally supported by OWL disjointness |
| K-13–K-15 | SHACL Core |
| K-16 | SHACL-SPARQL |
| K-17–K-18 | SHACL Core |
| K-19–K-20 | Build-time SPARQL/module inspection |
| K-21 | SHACL Core |
| K-22 | Publication lint plus manual source-text review |
| K-23 | Orchestrator/SPARQL over the post-reasoning graph and Run context |
| K-24 | Orchestrator/SPARQL over named stage graphs and qualified provenance |

OWL is authoritative for class semantics, specialisation, disjointness, domains, ranges and assessment-bearing entailments. SHACL validates graph conformance. Orchestrator/SPARQL checks compare stage-specific graphs, Runs and provenance. SWRL is not used as an integrity-constraint language.

---

## 11. Module and dataset allocation

PROV-O is an imported external vocabulary, not a seventh authored module. The six authored module roles are:

| Module role | Contents | Depends on |
|---|---|---|
| M1 Core system terminology | Element kinds, Function, Group, architecture relations, access, SecurityProperty, PropertyLossScenario, Consequence and assertion framework | PROV-O only where required |
| M2 Provenance and criteria framework | Criterion, categories, sources, interpretations, judgement, versioning, factors, measures and external-method declarations | M1, PROV-O |
| M3 Results and derivation | Result kinds, evaluations, assignments, identified collections, selections, derivation, runs, comparisons and execution evidence | M1, M2, PROV-O |
| M4 Assessment and decisions | Assessor decisions and decision-to-result or decision-to-selection relations | M1, M2, M3 |
| M5 Extension family | M5-Railway shared profile plus optional subsystem/source-profile extensions such as M5-ETCS, M5-TCMS or M5-CBTC | M1, M2; M3 only if an extension introduces specialised result vocabulary |
| M6 Case-data family | One separate architecture ABox per case, conforming to the instance profile and using the required M5 extensions | M1 and applicable M5 modules |

Rules for allocation:

1. M1–M4 contain no ETCS-, TCMS- or CBTC-specific individual or Criterion.
2. M5 is a family of independently identified extension artefacts, not one monolithic replaceable file.
3. Railway-wide terminology belongs to M5-Railway; subsystem terminology belongs to its subsystem extension.
4. Criteria expressed wholly in M1–M4 vocabulary belong to M2. Railway or subsystem criteria belong to the corresponding M5 extension.
5. M6 contains case individuals and Assertions but introduces no terminology.
6. Reusable source-register and controlled-vocabulary individuals are published as reference datasets distinct from architecture case ABoxes.
7. An extension may reference and specialise approved core terms but may not modify the released core artefact.
8. Each authored module can be loaded without any M6 case dataset; dependencies remain acyclic.

The normative home module for each conceptual entity is fixed below. Subsystem extensions may introduce specialisations, but they do not relocate these terms.

| Home module | Conceptual entities |
|---|---|
| M1 | Element, Asset, Interface, InformationFlow, FlowCharacteristic, AssetType, SystemRole, Function, SafetyFunction, Group, GroupConnection, AccessMechanism, AccessPrecondition, SecurityProperty, PropertyLossScenario, Consequence, ExaminationConstraint, AuthorisationStatus, Assertion, AssertedFact, Assumption, AssertedAbsence, BoundaryStatusAssertion, AuthorisationAssertion, BoundaryStatusValue, EpistemicStatusValue, Rationale |
| M2 | Criterion, AssessmentBearingCategory, CandidateExaminationTarget, EntryPoint, Source, SourceEdition, SourceLocation, Interpretation, JudgementBasis, OrderingFactor, OrderingFactorSet, ExternalComputationMethod, CoverageMeasure, OutputProfile, VersionedArtefact, ArtefactVersion, OntologyModule, TerminologyTerm, Deprecation |
| M3 | DerivedResult, EvaluationOutcome, ComputationOutcome, CriterionEvaluation, CategoryAssignment, CandidateSet, ReachabilityResult, DependencyChain, DependencyChainEntry, SafetyImpactResult, FactorValue, OrderingResult, OrderingEntry, CoverageResult, MaterialFindingDesignation, Selection, Run, RunComparison, DerivationRecord, DerivationStep, Mechanism, UnresolvedInput, InstanceSet, ExecutionEnvironment, PerformanceMeasurement, PerformanceTarget |
| M4 | AssessorDecision, Inclusion, Exclusion, Override |
| M5 | No fixed core entity. Railway- and subsystem-specific specialisations and criteria are introduced here under the extension rules above. |
| M6 | No schema entity. M6 contains only case individuals typed with M1–M5 vocabulary. |

Each relation and attribute is defined in the home module of its domain. A relation whose range belongs to a module on which the domain module may not depend is instead defined in the lowest permitted module that imports both sides. Cross-module derivation, decision and performance relations therefore reside in M3 or M4 as indicated by their domains. The released vocabulary must expose machine-readable home-module metadata so that CQ-36 can enumerate every schema term rather than infer allocation from file location.

---

## 12. Derivation and PROV-O profile

A DerivationRecord answers, for one result designated material under one OutputProfile, what produced it, what was used, what remained unresolved and under which versions the production occurred.

| Component | Required content |
|---|---|
| Designated result | DerivedResult and MaterialFindingDesignation |
| Record identity | DerivationRecord identifier and completeness status |
| Steps | DerivationSteps with explicit position or ordering |
| Activity | Mechanism, layer and applied Criterion or ExternalComputationMethod for each step |
| Used entities | Assertions, assumptions, prior DerivedResults and VersionedArtefacts actually used |
| Generated entities | Intermediate or final DerivedResults generated by each step |
| Unresolved inputs | Every required input encountered as unknown or not computable |
| Run context | Run, InstanceSet, all contributing ArtefactVersions and ExecutionEnvironment |

PROV-O supplies the upper activity/entity/agent, use, generation, derivation and bundle vocabulary. The project profile adds criterion outcomes, unresolved inputs, step order, layer authority and completeness constraints. D-B8b will state exact mappings before M2/M3 release.

The orchestrator assembles the cross-layer DerivationRecord because no individual mechanism observes the full sequence. Each mechanism must nevertheless emit sufficient qualified usage and generation evidence for assembly.

A DerivationRecord can identify results **potentially affected** by withdrawal, reinterpretation or resolution of an input. It does not by itself prove the exact counterfactual outcome. Exact changed outcomes for CQ-08 and CQ-30 require a comparison Run or a declared counterfactual/impact-analysis method.

---

## 13. Processing and semantic authority

| Responsibility | Owner | Produced information |
|---|---|---|
| Terminology, specialisation and consistency | L1 OWL 2 DL reasoner | Class entailments, specialisation entailments and consistency verdict |
| Rule-based semantic classification | L2 declared DL-safe rule profile | Assessment-bearing class entailments not expressible in L1 alone |
| Criterion outcome determination | Criterion evaluator | CriterionEvaluation with satisfied, not satisfied or undetermined outcome under declared evaluation semantics |
| Reachability, closure and path enumeration | L3 declared computation | ReachabilityResult, DependencyChain and intermediate architecture facts |
| Factor computation and ordering | L3 declared computation | FactorValue, OrderingResult and OrderingEntry |
| Coverage computation | L3 declared computation | CoverageResult |
| Entailment materialisation | Materialiser controlled by orchestrator | CategoryAssignment corresponding to an existing L1/L2 entailment |
| Candidate-set construction | Orchestrator/SPARQL projection | CandidateSet containing materialised candidate assignments |
| Structural validation | SHACL processor | Violations of SHACL-owned K constraints |
| Cross-stage integrity | Orchestrator/SPARQL | K-10, K-23, K-24 and run comparison checks |
| Derivation assembly | Orchestrator | DerivationRecord and cross-layer sequence |
| Human scoping decision | Assessor | Selection and AssessorDecision; never a change to derived truth |

The ontology is the semantic authority: it defines the meaning of assessment concepts, the criteria that can entail assessment-bearing membership and the admissible relationship between intermediate results and classifications. External components may compute paths, measures and ordering, but they do not define category meaning.

No assessment-bearing category is semantically assigned in L3. L3 supplies declared intermediate facts or computations. Only L1/L2 entail membership. The materialiser records an existing entailment and is checked by K-23; it does not decide membership.

Undetermined is produced by the Criterion evaluator when declared evaluation semantics cannot establish either satisfaction or non-satisfaction from the available information. It is not OWL class membership and is not inferred from mere absence without evaluating whether the missing information is decisive.

---

## 14. Traceability and Gate B evaluation obligations

### 14.1 Requirement-to-concept traceability

| Requirement | Realising concepts |
|---|---|
| ORF-01 | Asset, AssetType, SystemRole; has asset type, plays role |
| ORF-02 | Function; realises |
| ORF-03 | Interface, InformationFlow; has origin, has destination, traverses; K-03 |
| ORF-04 | Group, GroupConnection; member of, connects from, connects to |
| ORF-05 | BoundaryStatusAssertion, BoundaryStatusValue, InstanceSet; K-01 |
| ORF-06 | Rationale; has exclusion rationale; K-02 |
| ORF-07 | FlowCharacteristic; has characteristic |
| ORF-08 | AccessMechanism; reachable by |
| ORF-09 | AccessPrecondition, Assertion specialisations; requires precondition, precondition supported by; K-04 |
| ORF-10 | EntryPoint, ReachabilityResult |
| ORF-11 | ReachabilityResult; used access mechanism, relied on precondition |
| ORF-12 | CriterionEvaluation, CategoryAssignment; K-11, K-23, K-24; §13 |
| ORF-13 | AssessorDecision, Override; K-11, K-14, K-23, K-24 |
| ORF-14 | CandidateSet, RunComparison |
| ORF-15 | SafetyFunction; directly depends on; L3 closure |
| ORF-16 | SecurityProperty, PropertyLossScenario |
| ORF-17 | Consequence; has consequence |
| ORF-18 | SafetyImpactResult; evaluates scenario, affects function |
| ORF-19 | DependencyChain, DependencyChainEntry; ordered chain relations; K-16 |
| ORF-20 | OrderingFactor |
| ORF-21 | FactorValue; factor value relations and basis |
| ORF-22 | OrderingFactorSet, OrderingResult; has factor, uses factor set; K-15 |
| ORF-23 | OrderingResult, OrderingEntry; ranks assignment, position, method; K-16 |
| ORF-24 | ExaminationConstraint; applies to element |
| ORF-25 | AuthorisationAssertion, AuthorisationStatus; K-12 |
| ORF-26 | Criterion; determines membership of; criterion statement |
| ORF-27 | Source, SourceEdition, SourceLocation; edition/location relations; K-05, K-06 |
| ORF-28 | Interpretation; applies interpretation, interprets |
| ORF-29 | K-05, K-06 and independent SHACL provenance validation |
| ORF-30 | JudgementBasis; rests on judgement; K-05 |
| ORF-31 | DerivationRecord, DerivationStep, OutputProfile, MaterialFindingDesignation; K-08 |
| ORF-32 | Mechanism; executed by mechanism; K-09 |
| ORF-33 | UnresolvedInput; K-10 |
| ORF-34 | DerivationRecord completeness status; K-08–K-10 |
| ORF-35 | AssertedAbsence and assertion proposition relations |
| ORF-36 | CriterionEvaluation, EvaluationOutcome |
| ORF-37 | Assertion epistemic model and Criterion evaluator semantics |
| ORF-38 | L1 consistency verdict |
| ORF-39 | K-01–K-24 and §10.3 enforcement allocation |
| ORF-40 | CoverageMeasure and its conceptual attributes; K-17 |
| ORF-41 | CoverageResult, ComputationOutcome, UnresolvedInput |
| ORF-42 | CandidateSet, Selection, CoverageResult; selection based on candidate set; K-18 |
| ORF-43 | M1–M6 allocation; K-19, K-20 |
| ORF-44 | Extension rules in §11 and unchanged core regression obligation |
| ORF-45 | VersionedArtefact, ArtefactVersion, Run, InstanceSet; K-07 |
| ORF-46 | RunComparison; compares/changed relations |
| ORF-47 | TerminologyTerm, Deprecation; K-21 |
| ORF-48 | AssessorDecision specialisations, Selection, Rationale; K-13, K-14 |
| ORN-01 | L1/L2 profile and Mechanism/version ownership in §13 |
| ORN-02a | ExecutionEnvironment, PerformanceMeasurement and stage-specific attributes |
| ORN-02b | PerformanceTarget linked to a fixed fixture/environment; numerical target is fixed during implementation profiling before performance claims |
| ORN-03 | Stable identifier attribute and non-proprietary publication requirement |
| ORN-04 | Documentation generated from released ontology, shapes and rule metadata; no additional conceptual class required |
| ORN-05 | Source metadata and K-22 |
| ORN-06 | Build/test command recording in the implementation repository; no additional conceptual class required |
| ORN-07 | Separate module/dataset licence metadata in the implementation repository; no additional conceptual class required |
| ORN-08 | Module independence rules in §11 |

### 14.2 Evaluation obligations fixed at Gate B

The following evaluation episodes must be implemented and retained as evidence. Author-designed positive and negative fixtures verify behaviour; they are not external validation or portability evidence.

| ID | Required episode | Expected evidence |
|---|---|---|
| EV-B1 | Semantic derivation | A candidate membership absent from the input ABox is entailed by L1/L2 and materialised with matching CriterionEvaluation and CategoryAssignment |
| EV-B2 | Logical inconsistency | A deliberately contradictory fixture is detected by the declared OWL reasoner with an inspectable explanation where supported |
| EV-B3 | Structural rejection | Missing/cardinality/provenance defects cause SHACL non-conformance with focus node and constraint identifier |
| EV-B4 | Layer-authority rejection | A category assertion attributed to L3 or an assessor is rejected by K-24 |
| EV-B5 | Materialisation mismatch | CategoryAssignment without matching entailment is detected by K-23 |
| EV-B6 | Incomplete derivation | A designated material result with incomplete record is rejected by K-08–K-10 |
| EV-B7 | Epistemic distinction | Unknown, asserted absence and assumption yield distinguishable query/evaluation outcomes |
| EV-B8 | Run comparison | Changed inputs and changed results are reported between two versioned Runs |
| EV-B9 | Module isolation | M1–M4 load without case data; an extension adds terminology without modifying core or breaking its regression suite |
| EV-B10 | Performance recording | Classification, rules, SHACL and external computations record separate time, environment and input size on the representative fixture |
| EV-B11 | ETCS case validation | Derived case results are compared with independently prepared ETCS assessment evidence and disagreements are analysed |

The isolated Gate B proof of concept supplies preliminary evidence only for selected parts of EV-B1, EV-B3, EV-B4 and EV-B5. Production evidence must be regenerated from the released implementation.

---

## 15. Approved modelling decisions and closure status

**D-B1 — Entailment and CategoryAssignment. Accepted.** Assessment membership is semantically entailed in L1/L2. CategoryAssignment is a mandatory, run-contextual materialisation of a satisfied CriterionEvaluation. Entailment is the source of semantic truth; K-23 checks agreement in both processing context and category.

**D-B2 — Selective relation-instance modelling. Accepted.** Assertions and relations requiring epistemic status, provenance, context or outcome are individually referable. Plain structural relations remain direct. The boundary is documented by D-B7 and Sections 8–9.

**D-B3 — PropertyLossScenario granularity. Accepted.** Consequence and safety impact attach to the element/property-loss pair, not directly to Element.

**D-B4 — Dependency closure and paths. Accepted.** Direct dependency remains a binary, non-transitive relation. L3 owns closure and concrete path enumeration. DependencyChain plus positioned entries returns the path; L1/L2 may classify using versioned L3 outputs.

**D-B5 — Material finding scope. Accepted with revision.** Material finding is a contextual designation under a versioned OutputProfile, not a fixed list of result subclasses. Every designated result requires complete derivation evidence.

**D-B6 — Closed value vocabularies. Accepted.** The six vocabularies in §10.1 are closed for validation. Additions require a version increment and regression re-execution.

**D-B7 — Relation-instance policy. Accepted.** A direct property is retained unless an occurrence needs identity, context, provenance, outcome, role or position. BoundaryStatusAssertion, CriterionEvaluation, OrderingEntry, DependencyChainEntry and MaterialFindingDesignation require first-class instances. CandidateSet is an identified collection, not an n-ary-relation pattern. Flow endpoints and direct dependency remain binary in v1.0.

**D-B8a — PROV-O reuse. Accepted.** PROV-O supplies the upper provenance vocabulary. Project terms specialise it only where assessment semantics, unresolved inputs, ordering, layer authority or completeness require extension.

**D-B8b — Detailed PROV-O mapping. Deferred implementation deliverable.** Exact mapping and import choices are completed after the conceptual hierarchy is encoded and before M2/M3 release. This deferral does not reopen D-B8a.

**D-B9 — Semantic and computational authority. Accepted.** L1/L2 own assessment meaning and entailment; L3 owns declared algorithmic intermediate results; the materialiser and orchestrator record but do not decide membership; assessor decisions affect Selection only.

**D-B10 — Integrity-constraint technology. Accepted.** OWL expresses open-world semantics, SHACL validates declared graphs and orchestrator/SPARQL enforces cross-stage agreement, run comparison and producer authority. The allocation in §10.3 is normative.

### Gate B conceptual approval and remaining exit artefacts

Approval of this conceptual package freezes:

1. the scope and claim boundary;
2. the conceptual entity hierarchy, relations and attributes;
3. the six module roles and architecture-instance policy;
4. derivation and PROV-O reuse strategy;
5. semantic/computational ownership;
6. K-01–K-24 and their enforcement mechanisms;
7. requirement traceability and EV-B1–EV-B11 evaluation obligations;
8. D-B1–D-B10 as recorded above.

Changes to these items require an explicit change record, impact analysis against requirements/CQs and reapproval of affected Gate B sections.

This approval is necessary but is not, by itself, closure of the whole Gate B defined in Gate A. Gate B closes only when the following companion artefacts also exist and pass review:

1. **Formal vocabulary baseline:** the approved hierarchy, relations and D-B8b PROV-O mappings are encoded with stable identifiers, without importing legacy terms merely for compatibility.
2. **Executable CQ suite:** CQ-01–CQ-45 are represented by executable queries or tests against that baseline, including the expected positive, negative and undetermined answer shapes fixed in Gate A.
3. **Representative fixture:** a versioned ETCS case fixture is selected from the case material, documented as an empirical case rather than a generic railway ABox, and accompanied by deliberately small positive and negative test fixtures.
4. **Integrity and entailment assets:** OWL axioms, the declared DL-safe rule mechanism, SHACL shapes and orchestrator/SPARQL checks implement the ownership allocation in §10.3 and §13.
5. **Performance target:** after the fixture and execution environment are fixed, ORN-02b receives a numerical interactive-use threshold before benchmarking or performance claims.
6. **Gate B evidence report:** EV-B1–EV-B10 are executed and retained. EV-B11 is an evaluation obligation for the ETCS study and may remain open beyond construction, but its data sources and comparison protocol must be identified before Gate B closure.

The isolated proof of concept is evidence that selected patterns are technically viable; it does not satisfy items 1–6 as a production release. Formalisation therefore begins before final Gate B closure, but it is a controlled implementation of the approved conceptual model, not a reopening of conceptualisation.
