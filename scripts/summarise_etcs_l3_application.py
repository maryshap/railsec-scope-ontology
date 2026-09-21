"""Summarise L3 applicability and attack-path readiness for ETCS result graphs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from rdflib import Graph, Namespace, RDF, URIRef

import l3


CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
ATTACK = Namespace("https://w3id.org/railsec-scope/attack#")
RES = Namespace("https://w3id.org/railsec-scope/results#")


def _analysis_run(graph: Graph) -> URIRef:
    candidates = []
    for run in graph.subjects(RDF.type, RES.Run):
        if not isinstance(run, URIRef):
            continue
        evaluation_count = sum(
            1
            for evaluation in graph.subjects(RES.producedByRun, run)
            if (evaluation, RDF.type, RES.CriterionEvaluation) in graph
        )
        candidates.append((evaluation_count, str(run), run))
    if not candidates:
        raise ValueError("result graph contains no named Run")
    return max(candidates)[2]


def summarise(path: Path, recompute: bool = False) -> dict[str, object]:
    graph = Graph().parse(path)
    run = _analysis_run(graph)
    if recompute:
        l3.apply_attack_technique_applicability(graph, run)
        l3.apply(graph, run)

    criteria = {
        criterion
        for criterion in graph.subjects(CRIT.evaluationStageIdentifier, None)
        if str(graph.value(criterion, CRIT.evaluationStageIdentifier))
        == "attack-technique-applicability"
    }
    evaluations = {
        evaluation
        for criterion in criteria
        for evaluation in graph.subjects(RES.evaluatesCriterion, criterion)
        if graph.value(evaluation, RES.producedByRun) == run
    }
    outcomes = Counter(
        str(graph.value(evaluation, RES.hasEvaluationOutcome)).rsplit("#", 1)[-1]
        for evaluation in evaluations
    )
    elements = {
        graph.value(evaluation, RES.evaluationConcernsElement)
        for evaluation in evaluations
    }
    satisfied_techniques = {
        graph.value(criterion, ATTACK.assessesAttackTechnique)
        for evaluation in evaluations
        if graph.value(evaluation, RES.hasEvaluationOutcome) == RES.satisfied
        for criterion in [graph.value(evaluation, RES.evaluatesCriterion)]
    }
    attack_paths = {
        path_result
        for path_result in graph.subjects(RDF.type, ATTACK.AttackPathResult)
        if graph.value(path_result, RES.producedByRun) == run
    }
    by_technique: dict[str, Counter[str]] = {}
    for evaluation in evaluations:
        criterion = graph.value(evaluation, RES.evaluatesCriterion)
        technique = graph.value(criterion, ATTACK.assessesAttackTechnique)
        outcome = graph.value(evaluation, RES.hasEvaluationOutcome)
        if not isinstance(technique, URIRef) or not isinstance(outcome, URIRef):
            continue
        technique_id = str(technique).rsplit("/", 1)[-1]
        by_technique.setdefault(technique_id, Counter())[str(outcome).rsplit("#", 1)[-1]] += 1
    return {
        "scenario": str(run).rsplit("/", 1)[-1],
        "run": str(run),
        "publishable": bool(graph.value(run, RES.publishable)),
        "applicability": {
            "total": len(evaluations),
            "satisfied": outcomes["satisfied"],
            "notSatisfied": outcomes["notSatisfied"],
            "undetermined": outcomes["undetermined"],
            "flows": sum(
                isinstance(element, URIRef)
                and (element, RDF.type, RAIL.RailwayInformationFlow) in graph
                for element in elements
            ),
            "assets": sum(
                isinstance(element, URIRef)
                and (
                    (element, RDF.type, RAIL.RailwayAsset) in graph
                    or (element, RDF.type, RAIL.SafetyCriticalAsset) in graph
                )
                for element in elements
            ),
            "satisfiedTechniqueCount": len(satisfied_techniques - {None}),
            "byTechnique": {
                technique: {
                    "satisfied": counts["satisfied"],
                    "notSatisfied": counts["notSatisfied"],
                    "undetermined": counts["undetermined"],
                }
                for technique, counts in sorted(by_technique.items())
            },
        },
        "entryPoints": sum(1 for element in graph.subjects(RDF.type, CRIT.EntryPoint)),
        "reachableByFacts": sum(1 for _ in graph.triples((None, CORE.reachableBy, None))),
        "attackPaths": len(attack_paths),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", nargs="+", type=Path)
    parser.add_argument(
        "--recompute-applicability",
        action="store_true",
        help="apply the current L3 computation in memory before reporting",
    )
    args = parser.parse_args()
    report = [summarise(path, recompute=args.recompute_applicability) for path in args.results]
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
