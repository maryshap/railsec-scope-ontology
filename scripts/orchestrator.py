"""Step 13 — minimal Run orchestrator.

Turns the individually tested rule stages into one controlled, reproducible
analysis. A Run either satisfies every check and is publishable, or it is
refused with the reasons recorded. There is no partial success.

Sequence
--------
1. load the ontology modules, the rule registry and one instance set
2. validate the inputs before deriving anything
3. iterate reasoner -> rules to a fixed point, bounded and counted
4. refuse if the bound is reached without convergence
5. validate the derived graph
6. check that no classification was produced outside L1/L2
7. record the run, its artefact versions and its iteration count

The L3 hook is present and empty. When reachability lands it is called *inside*
the loop, because entry-point classification consumes reachability facts: an L3
call placed after the loop would leave those criteria permanently undetermined.

The description-logic reasoner is invoked through ROBOT and HermiT when both are
available. When they are not, the Run is still executed but is marked as not
publishable with the reason recorded, rather than silently producing a result
that looks reasoned and is not.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, URIRef, XSD

import l3


PROJECT = Path(__file__).resolve().parents[1]

CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RULE = Namespace("https://w3id.org/railsec-scope/rules#")
RUN = Namespace("https://w3id.org/railsec-scope/run/")

MAX_ITERATIONS = 10

# Ordered rule stages. Each consumes the results of the previous ones, so the
# order is part of the contract and is asserted by the tests.
STAGE_RULES = [
    "evaluate-transmission-category.rq",
    "classify-transmission-category.rq",
    "evaluate-transmission-threat.rq",
    "evaluate-critical-violation.rq",
    "evaluate-fail-safe-compromise.rq",
    "evaluate-sil-risk.rq",
    "evaluate-remediation-priority.rq",
    "evaluate-access-risk-asset.rq",
    "evaluate-access-path-risk.rq",
    "evaluate-control-weakness.rq",
    "classify-vulnerable-flow.rq",
    "evaluate-asset-zone-classification.rq",
    "classify-derived-membership.rq",
    "classify-candidate.rq",
]

# Categories that only L1 or L2 may confer. If an individual acquires one of
# these without a corresponding evaluation, a computation has classified
# something it is not permitted to classify.
@dataclass
class RunResult:
    """Outcome of one Run. `publishable` is false if any check failed."""

    iterations: int = 0
    converged: bool = False
    publishable: bool = False
    refusals: list[str] = field(default_factory=list)
    input_validation_conforms: bool = False
    output_validation_conforms: bool = False
    reasoner_invoked: bool = False
    graph: Graph | None = None
    run_iri: URIRef | None = None
    started: str = ""
    finished: str = ""

    def refuse(self, reason: str) -> None:
        self.refusals.append(reason)
        self.publishable = False


def _ontology_modules() -> list[Path]:
    return sorted((PROJECT / "ontology").glob("*.ttl"))


def _input_shapes() -> Graph:
    shapes = Graph()
    shapes.parse(PROJECT / "shapes" / "railway.ttl")
    return shapes


def _output_shapes() -> Graph:
    shapes = Graph()
    shapes.parse(PROJECT / "shapes" / "railway.ttl")
    shapes.parse(PROJECT / "shapes" / "criterion-slice.ttl")
    return shapes


def artefact_digest(paths: list[Path]) -> str:
    """Content digest over every artefact that contributed, for reproducibility."""
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _record_run(result: RunResult, graph: Graph, artefacts: list[Path]) -> None:
    """Write the Run record on both success and every refusal path."""
    if not result.finished:
        result.finished = datetime.now(timezone.utc).isoformat()
    graph.add((result.run_iri, RES.iterationCount, Literal(result.iterations)))
    graph.add((result.run_iri, RES.artefactDigest, Literal(artefact_digest(artefacts))))
    graph.add((result.run_iri, RES.publishable, Literal(result.publishable, datatype=XSD.boolean)))
    graph.add((result.run_iri, RES.startTime, Literal(result.started, datatype=XSD.dateTime)))
    graph.add((result.run_iri, RES.endTime, Literal(result.finished, datatype=XSD.dateTime)))
    for version in sorted(graph.subjects(RDF.type, CRIT.ArtefactVersion), key=str):
        graph.add((result.run_iri, RES.usedVersion, version))
    for reason in result.refusals:
        graph.add((result.run_iri, RES.refusalReason, Literal(reason)))


def reasoner_available() -> bool:
    return bool(shutil.which("java")) and (PROJECT / "tools" / "robot.jar").exists()


def run_reasoner(graph: Graph) -> bool:
    """Run HermiT through ROBOT and merge the entailments back.

    Returns False when the toolchain is unavailable, so the caller can refuse to
    publish rather than pretend the step ran.
    """
    if not reasoner_available():
        return False
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "input.ttl"
        target = Path(directory) / "reasoned.ttl"
        graph.serialize(destination=str(source), format="turtle")
        completed = subprocess.run(
            ["java", "-jar", str(PROJECT / "tools" / "robot.jar"), "reason",
             "--input", str(source), "--reasoner", "HermiT",
             "--equivalent-classes-allowed", "none",
             "--output", str(target)],
            capture_output=True, text=True,
        )
        if completed.returncode != 0 or not target.exists():
            return False
        graph.parse(target)
    return True


def apply_rules(graph: Graph) -> int:
    """Apply every rule stage once. Returns the number of triples added."""
    before = len(graph)
    for filename in STAGE_RULES:
        query = (PROJECT / "rules" / filename).read_text(encoding="utf-8")
        graph += graph.query(query).graph
    return len(graph) - before


def _result_iri(kind: str, *parts: URIRef | str) -> URIRef:
    material = "\u001f".join(map(str, parts)).encode("utf-8")
    return RUN[f"{kind}-{hashlib.sha256(material).hexdigest()}"]


def materialise_assignments(graph: Graph, run_iri: URIRef) -> int:
    """Record already-entailed assessment-bearing memberships.

    The materialiser does not decide membership. It requires all three inputs:
    a satisfied evaluation in this Run, a criterion/category declaration and
    the corresponding class entailment already present in the graph.
    """
    before = len(graph)
    for evaluation in sorted(graph.subjects(RDF.type, RES.CriterionEvaluation), key=str):
        if graph.value(evaluation, RES.producedByRun) != run_iri:
            continue
        if graph.value(evaluation, RES.hasEvaluationOutcome) != RES.satisfied:
            continue
        element = graph.value(evaluation, RES.evaluationConcernsElement)
        criterion = graph.value(evaluation, RES.evaluatesCriterion)
        if not isinstance(element, URIRef) or not isinstance(criterion, URIRef):
            continue
        for category in sorted(graph.objects(criterion, CRIT.determinesMembershipOf), key=str):
            if (category, RDF.type, CRIT.AssessmentBearingCategory) not in graph:
                continue
            if (element, RDF.type, category) not in graph:
                continue
            assignment = _result_iri("assignment", run_iri, evaluation, category)
            record = _result_iri("assignment-record", assignment)
            step = _result_iri("assignment-step", assignment)
            graph.add((assignment, RDF.type, RES.CategoryAssignment))
            graph.add((assignment, RES.materialisesEvaluation, evaluation))
            graph.add((assignment, RES.assignsCategory, category))
            graph.add((assignment, RES.producedByRun, run_iri))
            graph.add((assignment, RES.hasDerivationRecord, record))
            graph.add((record, RDF.type, RES.DerivationRecord))
            graph.add((record, RES.completenessStatus, Literal("complete")))
            graph.add((record, RES.hasStep, step))
            graph.add((step, RDF.type, RES.DerivationStep))
            graph.add((step, RES.stepPosition, Literal(1, datatype=XSD.positiveInteger)))
            graph.add((step, RES.layerIdentifier, Literal("materialiser")))
            graph.add((step, RES.appliedCriterion, criterion))
            graph.add((step, RES.executedByMechanism, RULE.CategoryAssignmentMaterialiser))
            graph.add((step, RES.usedEntity, evaluation))
            graph.add((step, RES.generatedResult, assignment))
    return len(graph) - before


def materialise_candidate_set(graph: Graph, run_iri: URIRef) -> int:
    """Project this Run's candidate assignments into one identified set."""
    assignments = sorted([
        assignment
        for assignment in graph.subjects(RDF.type, RES.CategoryAssignment)
        if graph.value(assignment, RES.producedByRun) == run_iri
        and graph.value(assignment, RES.assignsCategory) == CRIT.CandidateExaminationTarget
    ], key=str)
    if not assignments:
        return 0

    before = len(graph)
    candidate_set = _result_iri("candidate-set", run_iri)
    record = _result_iri("candidate-set-record", candidate_set)
    step = _result_iri("candidate-set-step", candidate_set)
    graph.add((candidate_set, RDF.type, RES.CandidateSet))
    graph.add((candidate_set, RES.producedByRun, run_iri))
    graph.add((candidate_set, RES.hasDerivationRecord, record))
    for assignment in assignments:
        graph.add((candidate_set, RES.hasCandidateAssignment, assignment))
    graph.add((record, RDF.type, RES.DerivationRecord))
    graph.add((record, RES.completenessStatus, Literal("complete")))
    graph.add((record, RES.hasStep, step))
    graph.add((step, RDF.type, RES.DerivationStep))
    graph.add((step, RES.stepPosition, Literal(1, datatype=XSD.positiveInteger)))
    graph.add((step, RES.layerIdentifier, Literal("orchestrator")))
    graph.add((step, RES.appliedComputation, RULE.CandidateSetProjectionMethod))
    graph.add((step, RES.executedByMechanism, RULE.CandidateSetProjectionMechanism))
    graph.add((step, RES.generatedResult, candidate_set))
    for assignment in assignments:
        graph.add((step, RES.usedEntity, assignment))
    return len(graph) - before


def apply_l3(graph: Graph, run_iri: URIRef) -> int:
    """Run declared L3 computations inside the fixed-point loop."""
    return l3.apply(graph, run_iri)


def guarded_category_violations(graph: Graph) -> list[str]:
    """Members of a guarded category that have no evaluation behind them."""
    violations = []
    categories = sorted(graph.subjects(RDF.type, CRIT.AssessmentBearingCategory), key=str)
    for category in categories:
        for member in graph.subjects(RDF.type, category):
            supported = any(
                graph.value(evaluation, RES.hasEvaluationOutcome) == RES.satisfied
                and category in set(
                    graph.objects(graph.value(evaluation, RES.evaluatesCriterion), CRIT.determinesMembershipOf)
                )
                for evaluation in graph.subjects(RES.evaluationConcernsElement, member)
            )
            if not supported:
                violations.append(f"{member} holds {category} with no satisfied evaluation")
    return violations


def execute(instance_files: list[Path], run_identifier: str, progress=None) -> RunResult:
    """Execute one Run over the given instance set."""
    progress = progress or (lambda _message: None)
    result = RunResult()
    result.started = datetime.now(timezone.utc).isoformat()
    result.run_iri = RUN[run_identifier]

    graph = Graph()
    load_paths = _ontology_modules() + [PROJECT / "imports" / "prov-o-dl.ttl",
                                        PROJECT / "rules" / "rules.ttl"] + list(instance_files)
    artefacts = load_paths + [
        PROJECT / "rules" / filename for filename in STAGE_RULES
    ] + [
        Path(__file__), PROJECT / "scripts" / "l3.py",
        PROJECT / "shapes" / "railway.ttl",
        PROJECT / "shapes" / "criterion-slice.ttl",
    ]
    progress(f"loading {len(load_paths)} input artefacts")
    for path in load_paths:
        progress(f"  parse {path.relative_to(PROJECT)}")
        graph.parse(path)
    progress(f"loaded graph: {len(graph)} triples")

    # The Run individual must exist before the loop: every rule binds ?run from
    # the data, so a Run recorded only at the end would produce no results at all.
    graph.add((result.run_iri, RDF.type, RES.Run))
    graph.add((result.run_iri, RES.runIdentifier, Literal(run_identifier)))

    # A Run must declare the instance sets it consumes. Stages that join on the
    # instance set produce nothing for a Run that declares none, while stages
    # that do not join on it still produce results, leaving derivations that
    # cite no upstream evaluation. Refuse rather than run half the pipeline.
    instance_sets = sorted(graph.subjects(RDF.type, RES.InstanceSet))
    if not instance_sets:
        result.refuse("no instance set present in the input; a Run must consume at least one")
        result.graph = graph
        _record_run(result, graph, artefacts)
        return result
    for instance_set in instance_sets:
        graph.add((result.run_iri, RES.usedInstanceSet, instance_set))

    # 2. validate inputs before deriving anything
    progress("input validation")
    conforms, _, report = validate(data_graph=graph, shacl_graph=_input_shapes(),
                                   inference="none", advanced=True)
    result.input_validation_conforms = conforms
    progress(f"input validation: {'conforms' if conforms else 'FAILED'}")
    if not conforms:
        result.refuse("input validation failed; no derivation attempted")
        result.graph = graph
        _record_run(result, graph, artefacts)
        return result

    # 3. bounded reasoner <-> rules <-> L3 loop
    result.publishable = True
    for iteration in range(1, MAX_ITERATIONS + 1):
        result.iterations = iteration
        before = len(graph)
        progress(f"iteration {iteration}: reasoner")
        reasoned = run_reasoner(graph)
        result.reasoner_invoked = result.reasoner_invoked or reasoned
        progress(f"iteration {iteration}: rules")
        apply_rules(graph)
        progress(f"iteration {iteration}: materialise assignments")
        materialise_assignments(graph, result.run_iri)
        progress(f"iteration {iteration}: materialise candidate set")
        materialise_candidate_set(graph, result.run_iri)
        progress(f"iteration {iteration}: L3")
        apply_l3(graph, result.run_iri)
        progress(f"iteration {iteration}: {len(graph) - before} triples added")
        if len(graph) == before:
            result.converged = True
            break

    # 4. refuse on non-convergence
    if not result.converged:
        result.refuse(f"fixed point not reached within {MAX_ITERATIONS} iterations")

    if not result.reasoner_invoked:
        result.refuse("description-logic reasoner was not invoked; entailments are unverified")

    # 5. validate the derived graph
    progress("output validation")
    conforms, _, report = validate(data_graph=graph, shacl_graph=_output_shapes(),
                                   inference="none", advanced=True)
    result.output_validation_conforms = conforms
    progress(f"output validation: {'conforms' if conforms else 'FAILED'}")
    if not conforms:
        result.refuse("output validation failed")

    # 6. no classification outside L1/L2
    progress("guarded category check")
    for violation in guarded_category_violations(graph):
        result.refuse(f"unsupported classification: {violation}")

    # 7. record the run
    progress("record run")
    _record_run(result, graph, artefacts)

    result.graph = graph
    return result


def summarise(result: RunResult) -> str:
    """One-screen report of what the Run established and what it did not."""
    graph = result.graph
    lines = [
        f"Run                : {result.run_iri}",
        f"Iterations         : {result.iterations} (converged: {result.converged})",
        f"Reasoner invoked   : {result.reasoner_invoked}",
        f"Input validation   : {'conforms' if result.input_validation_conforms else 'FAILED'}",
        f"Output validation  : {'conforms' if result.output_validation_conforms else 'FAILED'}",
        f"Publishable        : {result.publishable}",
    ]
    if result.refusals:
        lines.append("Refusals:")
        lines += [f"  - {reason}" for reason in result.refusals]
    if graph is not None:
        counts = {}
        for evaluation in graph.subjects(RDF.type, RES.CriterionEvaluation):
            outcome = graph.value(evaluation, RES.hasEvaluationOutcome)
            key = str(outcome).split("#")[-1] if outcome else "missing"
            counts[key] = counts.get(key, 0) + 1
        total = sum(counts.values())
        lines.append(f"Evaluations        : {total}")
        for key in ("satisfied", "notSatisfied", "undetermined", "missing"):
            if key in counts:
                share = 100 * counts[key] / total if total else 0
                lines.append(f"  {key:<16}: {counts[key]:>5}  ({share:.1f}%)")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help=(
            "instance-set/case files to load, in addition to the ontology "
            "modules and rules (always loaded)"
        ),
    )
    parser.add_argument("--run-id", default="cli", help="run identifier (default: cli)")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "write the full result graph (facts + derived evaluations + "
            "Run/DerivationRecord provenance) to this Turtle file"
        ),
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="print Run progress messages before each long stage",
    )
    args = parser.parse_args()

    files = args.files or [
        PROJECT / "cases" / "etcs" / "abox.ttl",
        PROJECT / "cases" / "etcs" / "classification-provenance.ttl",
    ]
    outcome = execute(
        files,
        run_identifier=args.run_id,
        progress=print if args.progress else None,
    )
    print(summarise(outcome))

    if args.output is not None and outcome.graph is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        outcome.graph.serialize(destination=str(args.output), format="turtle")
        print(f"\nresult graph written: {args.output} ({len(outcome.graph)} triples)")
    elif args.output is not None:
        print("\nno graph to write (Run was refused before any graph existed)")

    sys.exit(0 if outcome.publishable else 1)
