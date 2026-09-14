"""Declared L3 computations for Phase 2 Step 13.

L3 owns paths and numbers, never assessment-bearing category membership.  The
first implemented computation is deterministic reachability from an EntryPoint
assignment over directed vulnerable-flow edges.  One shortest, lexicographically
stable witness path is retained per entry/mechanism/target combination.
"""

from __future__ import annotations

import hashlib
from collections import deque
from decimal import Decimal

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD


CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RULE = Namespace("https://w3id.org/railsec-scope/rules#")
L3 = Namespace("https://w3id.org/railsec-scope/l3/")
PROV = Namespace("http://www.w3.org/ns/prov#")


def _iri(kind: str, *parts: URIRef | str) -> URIRef:
    material = "\u001f".join(map(str, parts)).encode("utf-8")
    return L3[f"{kind}-{hashlib.sha256(material).hexdigest()}"]


def _vulnerable_types(graph: Graph) -> set[URIRef]:
    types = {RAIL.VulnerableFlow}
    changed = True
    while changed:
        changed = False
        for child, parent in graph.subject_objects(RDFS.subClassOf):
            if isinstance(child, URIRef) and parent in types and child not in types:
                types.add(child)
                changed = True
    return types


def _entry_assignments(graph: Graph, run_iri: URIRef) -> list[tuple[URIRef, URIRef]]:
    entries: list[tuple[URIRef, URIRef]] = []
    for assignment in graph.subjects(RDF.type, RES.CategoryAssignment):
        if graph.value(assignment, RES.producedByRun) != run_iri:
            continue
        if graph.value(assignment, RES.assignsCategory) != CRIT.EntryPoint:
            continue
        evaluation = graph.value(assignment, RES.materialisesEvaluation)
        entry = graph.value(evaluation, RES.evaluationConcernsElement) if evaluation else None
        if isinstance(entry, URIRef):
            entries.append((entry, assignment))
    return sorted(set(entries), key=lambda pair: (str(pair[0]), str(pair[1])))


def _edges(graph: Graph) -> dict[URIRef, list[tuple[URIRef, URIRef]]]:
    vulnerable = _vulnerable_types(graph)
    adjacency: dict[URIRef, list[tuple[URIRef, URIRef]]] = {}
    for flow in graph.subjects(RDF.type, None):
        if not isinstance(flow, URIRef):
            continue
        if not any((flow, RDF.type, flow_type) in graph for flow_type in vulnerable):
            continue
        origin = graph.value(flow, CORE.hasOrigin)
        destination = graph.value(flow, CORE.hasDestination)
        if isinstance(origin, URIRef) and isinstance(destination, URIRef):
            adjacency.setdefault(origin, []).append((destination, flow))
    for origin in adjacency:
        adjacency[origin].sort(key=lambda edge: (str(edge[0]), str(edge[1])))
    return adjacency


def _shortest_paths(
    adjacency: dict[URIRef, list[tuple[URIRef, URIRef]]], entry: URIRef
) -> list[tuple[URIRef, list[URIRef], list[URIRef]]]:
    queue = deque([(entry, [entry], [])])
    visited = {entry}
    paths: list[tuple[URIRef, list[URIRef], list[URIRef]]] = []
    while queue:
        node, nodes, flows = queue.popleft()
        for target, flow in adjacency.get(node, []):
            if target in visited:
                continue
            visited.add(target)
            target_nodes = nodes + [target]
            target_flows = flows + [flow]
            paths.append((target, target_nodes, target_flows))
            queue.append((target, target_nodes, target_flows))
    return paths


def _add_result(
    graph: Graph,
    run_iri: URIRef,
    entry: URIRef,
    entry_assignment: URIRef,
    mechanism: URIRef,
    target: URIRef,
    nodes: list[URIRef],
    flows: list[URIRef],
) -> None:
    result = _iri("reachability", run_iri, entry, mechanism, target)
    chain = _iri("chain", run_iri, entry, mechanism, target)
    record = _iri("record", result)
    step = _iri("step", result)

    graph.add((result, RDF.type, RES.ReachabilityResult))
    graph.add((result, RES.reachabilityConcerns, target))
    graph.add((result, RES.usedAccessMechanism, mechanism))
    graph.add((result, RES.producedByRun, run_iri))
    graph.add((result, RES.hasDerivationRecord, record))
    for precondition in sorted(graph.objects(mechanism, CORE.requiresPrecondition), key=str):
        graph.add((result, RES.reliedOnPrecondition, precondition))

    graph.add((chain, RDF.type, RES.DependencyChain))
    graph.add((chain, RES.producedByRun, run_iri))
    graph.add((chain, RES.hasDerivationRecord, record))
    for position, node in enumerate(nodes, start=1):
        entry_iri = _iri("chain-entry", chain, str(position))
        graph.add((chain, RES.hasChainEntry, entry_iri))
        graph.add((entry_iri, RDF.type, RES.DependencyChainEntry))
        graph.add((entry_iri, RES.chainNode, node))
        graph.add((entry_iri, RES.pathPosition, Literal(position, datatype=XSD.positiveInteger)))

    graph.add((record, RDF.type, RES.DerivationRecord))
    graph.add((record, RES.completenessStatus, Literal("complete")))
    graph.add((record, RES.hasStep, step))
    graph.add((step, RDF.type, RES.DerivationStep))
    graph.add((step, RES.stepPosition, Literal(1, datatype=XSD.positiveInteger)))
    graph.add((step, RES.layerIdentifier, Literal("L3")))
    graph.add((step, RES.appliedComputation, RULE.L3ReachabilityMethod))
    graph.add((step, RES.executedByMechanism, RULE.L3ReachabilityMechanism))
    graph.add((step, RES.usedEntity, entry_assignment))
    graph.add((step, RES.generatedResult, result))
    graph.add((step, RES.generatedResult, chain))
    for flow in flows:
        graph.add((step, PROV.used, flow))


def _candidate_elements(graph: Graph, candidate_set: URIRef) -> set[URIRef]:
    elements: set[URIRef] = set()
    for assignment in graph.objects(candidate_set, RES.hasCandidateAssignment):
        evaluation = graph.value(assignment, RES.materialisesEvaluation)
        element = graph.value(evaluation, RES.evaluationConcernsElement) if evaluation else None
        if isinstance(element, URIRef):
            elements.add(element)
    return elements


def _candidate_assignments(graph: Graph, candidate_set: URIRef) -> list[URIRef]:
    return sorted(
        [item for item in graph.objects(candidate_set, RES.hasCandidateAssignment) if isinstance(item, URIRef)],
        key=str,
    )


def _factor_sets(graph: Graph) -> list[URIRef]:
    return sorted(graph.subjects(RDF.type, CRIT.OrderingFactorSet), key=str)


def _factor_weight(graph: Graph, factor: URIRef) -> Decimal | None:
    value = graph.value(factor, CRIT.factorWeight)
    if value is None:
        return None
    return Decimal(str(value))


def _evaluation_for_factor(
    graph: Graph, run_iri: URIRef, element: URIRef, factor: URIRef
) -> URIRef | None:
    for evaluation in sorted(graph.subjects(RDF.type, RES.CriterionEvaluation), key=str):
        if graph.value(evaluation, RES.producedByRun) != run_iri:
            continue
        if graph.value(evaluation, RES.evaluationConcernsElement) != element:
            continue
        criterion = graph.value(evaluation, RES.evaluatesCriterion)
        if criterion and (criterion, CRIT.determinesApplicabilityOf, factor) in graph:
            return evaluation
    return None


def _add_factor_value(
    graph: Graph,
    run_iri: URIRef,
    assignment: URIRef,
    factor: URIRef,
    evaluation: URIRef,
) -> Decimal | None:
    result = _iri("factor-value", run_iri, assignment, factor)
    record = _iri("factor-record", result)
    step = _iri("factor-step", result)
    outcome = graph.value(evaluation, RES.hasEvaluationOutcome)
    weight = _factor_weight(graph, factor)

    graph.add((result, RDF.type, RES.FactorValue))
    graph.add((result, RES.factorValueForCandidate, assignment))
    graph.add((result, RES.valueOfFactor, factor))
    graph.add((result, RES.valueBasis, evaluation))
    graph.add((result, RES.producedByRun, run_iri))
    graph.add((result, RES.hasDerivationRecord, record))
    graph.add((record, RDF.type, RES.DerivationRecord))
    graph.add((record, RES.hasStep, step))
    graph.add((step, RDF.type, RES.DerivationStep))
    graph.add((step, RES.stepPosition, Literal(1, datatype=XSD.positiveInteger)))
    graph.add((step, RES.layerIdentifier, Literal("L3")))
    graph.add((step, RES.appliedComputation, RULE.AHPRiskOrderingMethod))
    graph.add((step, RES.executedByMechanism, RULE.AHPRiskOrderingMechanism))
    graph.add((step, RES.usedEntity, assignment))
    graph.add((step, RES.usedEntity, factor))
    graph.add((step, RES.usedEntity, evaluation))
    graph.add((step, RES.generatedResult, result))

    if outcome == RES.satisfied and weight is not None:
        graph.add((result, RES.hasComputationOutcome, RES.valuePresent))
        graph.add((result, RES.representedValue, Literal(weight, datatype=XSD.decimal)))
        graph.add((record, RES.completenessStatus, Literal("complete")))
        return weight
    if outcome == RES.notSatisfied:
        graph.add((result, RES.hasComputationOutcome, RES.valuePresent))
        graph.add((result, RES.representedValue, Literal(Decimal("0"), datatype=XSD.decimal)))
        graph.add((record, RES.completenessStatus, Literal("complete")))
        return Decimal("0")

    unresolved = _iri("unresolved-factor", result)
    graph.add((result, RES.hasComputationOutcome, RES.notComputable))
    graph.add((record, RES.completenessStatus, Literal("incomplete")))
    graph.add((record, RES.hasUnresolvedInput, unresolved))
    graph.add((unresolved, RDF.type, RES.UnresolvedInput))
    return None


def _add_ordering(
    graph: Graph,
    run_iri: URIRef,
    candidate_set: URIRef,
    factor_set: URIRef,
    scores: dict[URIRef, Decimal | None],
) -> None:
    ordering = _iri("ordering", run_iri, candidate_set, factor_set, RULE.AHPRiskOrderingMethod)
    record = _iri("ordering-record", ordering)
    step = _iri("ordering-step", ordering)
    graph.add((ordering, RDF.type, RES.OrderingResult))
    graph.add((ordering, RES.producedByRun, run_iri))
    graph.add((ordering, RES.ordersCandidateSet, candidate_set))
    graph.add((ordering, RES.usesFactorSet, factor_set))
    graph.add((ordering, RES.producedByMethod, RULE.AHPRiskOrderingMethod))
    graph.add((ordering, CRIT.hasVersion, RULE.phase2RuleVersion))
    graph.add((ordering, RES.hasDerivationRecord, record))
    graph.add((record, RDF.type, RES.DerivationRecord))
    graph.add((record, RES.hasStep, step))
    graph.add((step, RDF.type, RES.DerivationStep))
    graph.add((step, RES.stepPosition, Literal(1, datatype=XSD.positiveInteger)))
    graph.add((step, RES.layerIdentifier, Literal("L3")))
    graph.add((step, RES.appliedComputation, RULE.AHPRiskOrderingMethod))
    graph.add((step, RES.executedByMechanism, RULE.AHPRiskOrderingMechanism))
    graph.add((step, RES.usedEntity, candidate_set))
    graph.add((step, RES.usedEntity, factor_set))
    graph.add((step, RES.generatedResult, ordering))

    complete = all(value is not None for value in scores.values())
    graph.add((record, RES.completenessStatus, Literal("complete" if complete else "incomplete")))
    if not complete:
        unresolved = _iri("unresolved-ordering", ordering)
        graph.add((record, RES.hasUnresolvedInput, unresolved))
        graph.add((unresolved, RDF.type, RES.UnresolvedInput))

    ranked = sorted(
        scores,
        key=lambda assignment: (
            scores[assignment] is None,
            -(scores[assignment] or Decimal("0")),
            str(assignment),
        ),
    )
    for position, assignment in enumerate(ranked, start=1):
        entry = _iri("ordering-entry", ordering, assignment)
        graph.add((ordering, RES.hasOrderingEntry, entry))
        graph.add((entry, RDF.type, RES.OrderingEntry))
        graph.add((entry, RES.ranksAssignment, assignment))
        graph.add((entry, RES.orderingPosition, Literal(position, datatype=XSD.positiveInteger)))
        score = scores[assignment]
        if score is None:
            graph.add((entry, RES.tieIdentifier, Literal("not-computable")))
        else:
            graph.add((entry, RES.tieIdentifier, Literal(str(score))))


def apply_ordering(graph: Graph, run_iri: URIRef) -> int:
    """Compute declared AHP factor values and one ordering per CandidateSet."""
    before = len(graph)
    factor_sets = _factor_sets(graph)
    candidate_sets = sorted(
        [
            item for item in graph.subjects(RDF.type, RES.CandidateSet)
            if graph.value(item, RES.producedByRun) == run_iri
        ],
        key=str,
    )
    for candidate_set in candidate_sets:
        assignments = _candidate_assignments(graph, candidate_set)
        if not assignments:
            continue
        for factor_set in factor_sets:
            factors = sorted(graph.objects(factor_set, CRIT.hasFactor), key=str)
            scores: dict[URIRef, Decimal | None] = {}
            for assignment in assignments:
                evaluation = graph.value(assignment, RES.materialisesEvaluation)
                element = graph.value(evaluation, RES.evaluationConcernsElement) if evaluation else None
                if not isinstance(element, URIRef):
                    continue
                score = Decimal("0")
                computable = True
                for factor in factors:
                    if not isinstance(factor, URIRef):
                        continue
                    factor_evaluation = _evaluation_for_factor(graph, run_iri, element, factor)
                    if factor_evaluation is None:
                        continue
                    value = _add_factor_value(graph, run_iri, assignment, factor, factor_evaluation)
                    if value is None:
                        computable = False
                    else:
                        score += value
                scores[assignment] = score if computable else None
            if scores:
                _add_ordering(graph, run_iri, candidate_set, factor_set, scores)
    return len(graph) - before


def _add_coverage(graph: Graph, run_iri: URIRef, candidate_set: URIRef, selection: URIRef) -> None:
    result = _iri("coverage", run_iri, candidate_set, selection, RULE.SelectionCoverageMeasure)
    record = _iri("coverage-record", result)
    step = _iri("coverage-step", result)
    candidates = _candidate_elements(graph, candidate_set)
    selected = {item for item in graph.objects(selection, RES.includesElement) if isinstance(item, URIRef)}

    graph.add((result, RDF.type, RES.CoverageResult))
    graph.add((result, RES.producedByRun, run_iri))
    graph.add((result, RES.evaluatesMeasure, RULE.SelectionCoverageMeasure))
    graph.add((result, RES.measuredCandidateSet, candidate_set))
    graph.add((result, RES.measuredSelection, selection))
    graph.add((result, RES.hasDerivationRecord, record))
    graph.add((record, RDF.type, RES.DerivationRecord))
    graph.add((record, RES.hasStep, step))
    graph.add((step, RDF.type, RES.DerivationStep))
    graph.add((step, RES.stepPosition, Literal(1, datatype=XSD.positiveInteger)))
    graph.add((step, RES.layerIdentifier, Literal("L3")))
    graph.add((step, RES.appliedComputation, RULE.SelectionCoverageMethod))
    graph.add((step, RES.executedByMechanism, RULE.SelectionCoverageMechanism))
    graph.add((step, RES.usedEntity, candidate_set))
    graph.add((step, RES.usedEntity, selection))
    graph.add((step, RES.usedEntity, RULE.SelectionCoverageMeasure))
    graph.add((step, RES.generatedResult, result))

    if candidates:
        value = Decimal(len(candidates & selected)) / Decimal(len(candidates))
        graph.add((result, RES.hasComputationOutcome, RES.valuePresent))
        graph.add((result, RES.representedValue, Literal(value, datatype=XSD.decimal)))
        graph.add((record, RES.completenessStatus, Literal("complete")))
    else:
        unresolved = _iri("unresolved-empty-candidate-set", result)
        graph.add((result, RES.hasComputationOutcome, RES.notComputable))
        graph.add((record, RES.completenessStatus, Literal("incomplete")))
        graph.add((record, RES.hasUnresolvedInput, unresolved))
        graph.add((unresolved, RDF.type, RES.UnresolvedInput))


def apply_coverage(graph: Graph, run_iri: URIRef) -> int:
    """Compute coverage only for explicit Selections over this Run's sets."""
    before = len(graph)
    candidate_sets = {
        item for item in graph.subjects(RDF.type, RES.CandidateSet)
        if graph.value(item, RES.producedByRun) == run_iri
    }
    for selection in sorted(graph.subjects(RDF.type, RES.Selection), key=str):
        candidate_set = graph.value(selection, RES.selectionBasedOnCandidateSet)
        if candidate_set in candidate_sets:
            _add_coverage(graph, run_iri, candidate_set, selection)
    return len(graph) - before


def apply(graph: Graph, run_iri: URIRef) -> int:
    """Add deterministic reachability/path evidence and return triples added."""
    before = len(graph)
    adjacency = _edges(graph)
    for entry, assignment in _entry_assignments(graph, run_iri):
        mechanisms = sorted(graph.objects(entry, CORE.reachableBy), key=str)
        for mechanism in mechanisms:
            if not isinstance(mechanism, URIRef):
                continue
            for target, nodes, flows in _shortest_paths(adjacency, entry):
                _add_result(
                    graph, run_iri, entry, assignment, mechanism,
                    target, nodes, flows,
                )
    apply_ordering(graph, run_iri)
    apply_coverage(graph, run_iri)
    return len(graph) - before
