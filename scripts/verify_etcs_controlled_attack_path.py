"""Verify the pre-registered result of the controlled ETCS L3 scenario."""

from __future__ import annotations

import argparse
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, URIRef


ATTACK = Namespace("https://w3id.org/railsec-scope/attack#")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
CASE = Namespace("https://w3id.org/railsec-scope/case/etcs/resource/")
RUN = Namespace("https://w3id.org/railsec-scope/run/")
T0842 = URIRef("https://w3id.org/railsec-scope/attack/ics/19.2/technique/T0842")


def _only(values, description: str):
    values = list(values)
    if len(values) != 1:
        raise AssertionError(f"expected exactly one {description}, found {len(values)}")
    return values[0]


def verify(graph: Graph, run: URIRef, *, require_publishable: bool = True) -> dict[str, int]:
    """Raise AssertionError unless the graph matches the registered scenario result."""
    if require_publishable and graph.value(run, RES.publishable) != Literal(True):
        raise AssertionError("the controlled scenario Run is not publishable")

    paths = [
        path
        for path in graph.subjects(RDF.type, ATTACK.AttackPathResult)
        if graph.value(path, RES.producedByRun) == run
    ]
    path = _only(paths, "AttackPathResult for this Run")
    if graph.value(path, ATTACK.startsFromEntryPoint) != CASE["asset-it-01"]:
        raise AssertionError("the attack path does not start at NG-FW (IT-01)")
    if graph.value(path, ATTACK.attackPathConcernsTarget) != CASE["asset-ct-01"]:
        raise AssertionError("the attack path does not target RBC (CT-01)")
    if graph.value(path, CRIT.hasVersion) is None:
        raise AssertionError("the attack path has no L3 mechanism version")

    steps = sorted(
        graph.objects(path, ATTACK.hasAttackPathStep),
        key=lambda step: int(graph.value(step, ATTACK.attackPathStepPosition)),
    )
    step = _only(steps, "AttackPathStep")
    if graph.value(step, ATTACK.attackPathStepPosition).toPython() != 1:
        raise AssertionError("the attack-path step is not in position 1")
    if graph.value(step, ATTACK.stepConcernsElement) != CASE["flow-if-it-10-forward"]:
        raise AssertionError("the attack-path step does not concern IF-IT-10-forward")
    if graph.value(step, ATTACK.stepUsesTechnique) != T0842:
        raise AssertionError("the attack-path step does not use ATT&CK ICS T0842")

    applicability = graph.value(step, ATTACK.supportedByApplicabilityEvaluation)
    if not isinstance(applicability, URIRef):
        raise AssertionError("the path step has no applicability evidence")
    if graph.value(applicability, RES.hasEvaluationOutcome) != RES.satisfied:
        raise AssertionError("the path step applicability evidence is not satisfied")
    criterion = graph.value(applicability, RES.evaluatesCriterion)
    if graph.value(criterion, ATTACK.assessesAttackTechnique) != T0842:
        raise AssertionError("the applicability evidence does not assess T0842")

    record = graph.value(path, RES.hasDerivationRecord)
    if not isinstance(record, URIRef) or graph.value(record, RES.completenessStatus) != Literal("complete"):
        raise AssertionError("the attack path has no complete DerivationRecord")
    derivation_steps = list(graph.objects(record, RES.hasStep))
    derivation_step = _only(derivation_steps, "attack-path derivation step")
    if applicability not in set(graph.objects(derivation_step, RES.usedEntity)):
        raise AssertionError("the attack-path derivation does not use its applicability evidence")

    required = list(graph.objects(criterion, ATTACK.requiresSatisfiedEvaluationOf))
    required_criterion = _only(required, "T0842 prerequisite criterion")
    prerequisite_evaluations = [
        evaluation
        for evaluation in graph.subjects(RES.evaluatesCriterion, required_criterion)
        if graph.value(evaluation, RES.producedByRun) == run
        and graph.value(evaluation, RES.evaluationConcernsElement) == CASE["flow-if-it-10-forward"]
        and graph.value(evaluation, RES.hasEvaluationOutcome) == RES.satisfied
    ]
    prerequisite = _only(prerequisite_evaluations, "satisfied T0842 prerequisite evaluation")
    if prerequisite not in set(graph.objects(derivation_step, RES.usedEntity)):
        raise AssertionError("the path derivation does not use the satisfied L1 prerequisite")

    impacts = [
        impact
        for impact in graph.subjects(ATTACK.safetyImpactFromAttackPath, path)
        if graph.value(impact, RES.producedByRun) == run
    ]
    safety_critical_impacts = [
        impact
        for impact in impacts
        if graph.value(impact, ATTACK.safetyImpactKind) == Literal("safety-critical-asset")
        and graph.value(impact, ATTACK.safetyImpactConcernsElement) == CASE["asset-ct-01"]
    ]
    _only(safety_critical_impacts, "safety-critical target impact")
    if any(graph.value(item, RAIL.hasSafetyIntegrityLevel) is not None for item in [path, *impacts]):
        raise AssertionError("L3 assigned a SIL to an attack-path result")

    reverse_paths = [
        candidate
        for candidate in graph.subjects(RDF.type, ATTACK.AttackPathResult)
        if graph.value(candidate, RES.producedByRun) == run
        and graph.value(candidate, ATTACK.startsFromEntryPoint) == CASE["asset-ct-01"]
        and graph.value(candidate, ATTACK.attackPathConcernsTarget) == CASE["asset-it-01"]
    ]
    if reverse_paths:
        raise AssertionError("a reverse attack path was inferred without directed evidence")

    return {
        "attack_paths": len(paths),
        "steps": len(steps),
        "safety_impacts": len(impacts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--run-id", default="controlled-remote-attack-path")
    parser.add_argument("--allow-non-publishable", action="store_true")
    args = parser.parse_args()

    counts = verify(
        Graph().parse(args.result),
        RUN[args.run_id],
        require_publishable=not args.allow_non_publishable,
    )
    print(
        "controlled ETCS attack path verified: "
        f"{counts['attack_paths']} path, {counts['steps']} step, "
        f"{counts['safety_impacts']} safety impact(s)"
    )


if __name__ == "__main__":
    main()
