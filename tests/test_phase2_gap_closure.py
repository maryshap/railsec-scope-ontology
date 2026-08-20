"""Ontology-complete gap closure for the remaining implement-now legacy rules."""

from __future__ import annotations

import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
FX = Namespace("https://w3id.org/railsec-scope/fixture/gap-closure/")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")


def load_graph() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "rules" / "rules.ttl")
    graph.add((FX.run, RDF.type, RES.Run))
    return graph


def apply_rule(graph: Graph, filename: str) -> int:
    inferred = graph.query((PROJECT / "rules" / filename).read_text(encoding="utf-8")).graph
    before = len(graph)
    graph += inferred
    return len(graph) - before


def outcome(graph: Graph, element, predicate, value):
    for evaluation in graph.subjects(RDF.type, RES.CriterionEvaluation):
        if graph.value(evaluation, RES.evaluationConcernsElement) != element:
            continue
        criterion = graph.value(evaluation, RES.evaluatesCriterion)
        if graph.value(criterion, predicate) == value:
            return graph.value(evaluation, RES.hasEvaluationOutcome)
    return None


class Phase2GapClosureTest(unittest.TestCase):
    def test_confidentiality_weakness_materialises_only_from_satisfied_evaluation(self) -> None:
        graph = load_graph()
        graph.add((FX.flow, RDF.type, RAIL.RailwayInformationFlow))
        graph.add((FX.flow, RAIL.crossesTrustBoundary, Literal(True)))
        graph.add((FX.flow, RAIL.encryptionEnabled, Literal(False)))

        apply_rule(graph, "evaluate-control-weakness.rq")
        apply_rule(graph, "classify-vulnerable-flow.rq")

        self.assertEqual(RES.satisfied, outcome(graph, FX.flow, RAIL.assessesControlWeakness, RAIL.missingEncryption))
        self.assertIn((FX.flow, RDF.type, RAIL.ConfidentialityVulnerableFlow), graph)

    def test_zone_criteria_cover_exposure_context_and_entry_points(self) -> None:
        graph = load_graph()
        graph.add((FX.external_asset, RDF.type, RAIL.RailwayAsset))
        graph.add((FX.external_asset, CORE.memberOf, FX.external_zone))
        graph.add((FX.external_zone, RDF.type, RAIL.ExternalZone))
        graph.add((FX.dmz_asset, RDF.type, RAIL.RailwayAsset))
        graph.add((FX.dmz_asset, CORE.memberOf, FX.dmz_zone))
        graph.add((FX.dmz_zone, RDF.type, RAIL.DMZZone))
        graph.add((FX.unknown_asset, RDF.type, RAIL.RailwayAsset))

        apply_rule(graph, "evaluate-asset-zone-classification.rq")
        apply_rule(graph, "classify-derived-membership.rq")

        self.assertIn((FX.external_asset, RDF.type, RAIL.ExposedAsset), graph)
        self.assertIn((FX.external_asset, RDF.type, RAIL.Category3AssetContext), graph)
        self.assertIn((FX.external_asset, RDF.type, CRIT.EntryPoint), graph)
        self.assertIn((FX.dmz_asset, RDF.type, RAIL.PartiallyExposedAsset), graph)
        self.assertIn((FX.dmz_asset, RDF.type, CRIT.EntryPoint), graph)
        self.assertEqual(
            RES.undetermined,
            outcome(graph, FX.unknown_asset, CRIT.determinesMembershipOf, RAIL.ExposedAsset),
        )

    def test_mobile_fail_safe_compromise_yields_high_priority_remediation(self) -> None:
        graph = load_graph()
        graph.add((FX.mobile_asset, RDF.type, RAIL.SafetyCriticalAsset))
        graph.add((FX.mobile_asset, CORE.memberOf, FX.mobile_zone))
        graph.add((FX.mobile_zone, RDF.type, RAIL.MobileZone))
        graph.add((FX.fail_safe_eval, RDF.type, RES.CriterionEvaluation))
        graph.add((FX.fail_safe_eval, RES.evaluationConcernsElement, FX.mobile_asset))
        graph.add((FX.fail_safe_eval, RES.evaluatesCriterion, FX.fail_safe_criterion))
        graph.add((FX.fail_safe_eval, RES.hasEvaluationOutcome, RES.satisfied))
        graph.add((FX.fail_safe_eval, RES.producedByRun, FX.run))
        graph.add((FX.fail_safe_criterion, RAIL.assessesFailSafeCompromiseFrom, RAIL.criticalIntegrityViolation))

        apply_rule(graph, "evaluate-remediation-priority.rq")

        self.assertEqual(
            RES.satisfied,
            outcome(graph, FX.mobile_asset, RAIL.assessesRemediationPriority, RAIL.highPriorityRemediation),
        )

    def test_critical_payload_specific_rules_are_not_satisfied_by_generic_safety_payload(self) -> None:
        graph = load_graph()
        graph.add((FX.flow, RDF.type, RAIL.RailwayInformationFlow))
        graph.add((FX.flow, CORE.carriesPayload, FX.generic_safety_payload))
        graph.add((FX.generic_safety_payload, RDF.type, RAIL.SafetyRelatedPayload))
        for threat in (RAIL.DelayThreat, RAIL.ResequencingThreat):
            graph.add((FX[f"{str(threat).split('#')[-1]}-eval"], RDF.type, RES.CriterionEvaluation))
            graph.add((FX[f"{str(threat).split('#')[-1]}-eval"], RES.evaluationConcernsElement, FX.flow))
            graph.add((FX[f"{str(threat).split('#')[-1]}-eval"], RES.evaluatesCriterion, FX[f"{str(threat).split('#')[-1]}-criterion"]))
            graph.add((FX[f"{str(threat).split('#')[-1]}-eval"], RES.hasEvaluationOutcome, RES.satisfied))
            graph.add((FX[f"{str(threat).split('#')[-1]}-eval"], RES.producedByRun, FX.run))
            graph.add((FX[f"{str(threat).split('#')[-1]}-criterion"], RAIL.assessesTransmissionThreat, threat))

        apply_rule(graph, "evaluate-critical-violation.rq")

        self.assertEqual(
            RES.undetermined,
            outcome(graph, FX.flow, RAIL.assessesCriticalViolation, RAIL.criticalTimelinessViolation),
        )
        graph = load_graph()
        graph.add((FX.flow, RDF.type, RAIL.RailwayInformationFlow))
        graph.add((FX.flow, CORE.carriesPayload, FX.emergency_payload))
        graph.add((FX.emergency_payload, RDF.type, RAIL.EmergencyCommandData))
        graph.add((FX["DelayThreat-eval"], RDF.type, RES.CriterionEvaluation))
        graph.add((FX["DelayThreat-eval"], RES.evaluationConcernsElement, FX.flow))
        graph.add((FX["DelayThreat-eval"], RES.evaluatesCriterion, FX["DelayThreat-criterion"]))
        graph.add((FX["DelayThreat-eval"], RES.hasEvaluationOutcome, RES.satisfied))
        graph.add((FX["DelayThreat-eval"], RES.producedByRun, FX.run))
        graph.add((FX["DelayThreat-criterion"], RAIL.assessesTransmissionThreat, RAIL.DelayThreat))
        apply_rule(graph, "evaluate-critical-violation.rq")
        self.assertEqual(
            RES.satisfied,
            outcome(graph, FX.flow, RAIL.assessesCriticalViolation, RAIL.criticalTimelinessViolation),
        )


if __name__ == "__main__":
    unittest.main()
