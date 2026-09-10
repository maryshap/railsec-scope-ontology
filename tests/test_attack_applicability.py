"""Focused contract tests for sourced L3 technique-applicability criteria."""

from __future__ import annotations

import unittest
from pathlib import Path

from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
FX = Namespace("https://w3id.org/railsec-scope/fixture/attack-applicability/")
ATTACK = Namespace("https://w3id.org/railsec-scope/attack#")
ATTACK_CRIT = Namespace("https://w3id.org/railsec-scope/criteria/attack/")
ATTACK_ICS = Namespace("https://w3id.org/railsec-scope/attack/ics/19.2/technique/")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RAIL_CRIT = Namespace("https://w3id.org/railsec-scope/criteria/railway/")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RULE = Namespace("https://w3id.org/railsec-scope/rules#")


def load_graph() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "imports" / "attack-ics-19.2.ttl")
    graph.parse(PROJECT / "rules" / "rules.ttl")
    graph.add((FX.run, RDF.type, RES.Run))
    graph.add((FX.flow, RDF.type, RAIL.RailwayInformationFlow))
    return graph


def add_evaluation(graph: Graph, name: str, criterion, outcome) -> None:
    evaluation = FX[name]
    graph.add((evaluation, RDF.type, RES.CriterionEvaluation))
    graph.add((evaluation, RES.evaluationConcernsElement, FX.flow))
    graph.add((evaluation, RES.evaluatesCriterion, criterion))
    graph.add((evaluation, RES.hasEvaluationOutcome, outcome))
    graph.add((evaluation, RES.producedByRun, FX.run))


def apply_rule(graph: Graph) -> None:
    query = (PROJECT / "rules" / "evaluate-attack-technique-applicability.rq").read_text(encoding="utf-8")
    graph += graph.query(query).graph


def evaluation_for(graph: Graph, criterion):
    for evaluation in graph.subjects(RES.evaluatesCriterion, criterion):
        if graph.value(evaluation, RES.evaluationConcernsElement) == FX.flow:
            return evaluation
    return None


class AttackApplicabilityTest(unittest.TestCase):
    def test_four_criteria_are_sourced_and_point_to_projected_techniques(self) -> None:
        graph = load_graph()
        expected = {
            ATTACK_CRIT["t0842-network-sniffing-confidentiality-criterion"]: ATTACK_ICS.T0842,
            ATTACK_CRIT["t0814-dos-rate-limiting-criterion"]: ATTACK_ICS.T0814,
            ATTACK_CRIT["t1692-001-command-message-authenticity-criterion"]: ATTACK_ICS["T1692.001"],
            ATTACK_CRIT["t0830-aitm-authentication-integrity-criterion"]: ATTACK_ICS.T0830,
        }
        self.assertEqual(expected, {
            criterion: graph.value(criterion, ATTACK.assessesAttackTechnique)
            for criterion in graph.subjects(CRIT.evaluationStageIdentifier, None)
            if str(graph.value(criterion, CRIT.evaluationStageIdentifier)) == "attack-technique-applicability"
        })
        for criterion, technique in expected.items():
            with self.subTest(criterion=criterion):
                location = graph.value(criterion, CRIT.derivedFromSourceLocation)
                interpretation = graph.value(criterion, CRIT.appliesInterpretation)
                self.assertIn((location, RDF.type, CRIT.SourceLocation), graph)
                self.assertIn((interpretation, RDF.type, CRIT.Interpretation), graph)
                self.assertIsNone(graph.value(criterion, CRIT.restsOnJudgement))
                self.assertIn((technique, RDF.type, ATTACK.AttackTechnique), graph)

    def test_outcomes_follow_same_flow_and_run_prerequisites(self) -> None:
        graph = load_graph()
        add_evaluation(graph, "confidentiality", RAIL_CRIT["l1-confidentiality-criterion"], RES.satisfied)
        add_evaluation(graph, "rate-limiting", RAIL_CRIT["l1-rate-limiting-criterion"], RES.notSatisfied)
        add_evaluation(graph, "critical-authenticity", RAIL_CRIT["critical-authenticity-criterion"], RES.undetermined)
        add_evaluation(graph, "authentication", RAIL_CRIT["l1-authentication-criterion"], RES.satisfied)
        add_evaluation(graph, "integrity", RAIL_CRIT["l1-integrity-criterion"], RES.satisfied)

        apply_rule(graph)

        expected = {
            "t0842-network-sniffing-confidentiality-criterion": RES.satisfied,
            "t0814-dos-rate-limiting-criterion": RES.notSatisfied,
            "t1692-001-command-message-authenticity-criterion": RES.undetermined,
            "t0830-aitm-authentication-integrity-criterion": RES.satisfied,
        }
        for local_name, expected_outcome in expected.items():
            evaluation = evaluation_for(graph, ATTACK_CRIT[local_name])
            with self.subTest(criterion=local_name):
                self.assertIsNotNone(evaluation)
                self.assertEqual(expected_outcome, graph.value(evaluation, RES.hasEvaluationOutcome))
                step = graph.value(graph.value(evaluation, RES.hasDerivationRecord), RES.hasStep)
                self.assertEqual("L3", str(graph.value(step, RES.layerIdentifier)))
                self.assertEqual(RULE.EvaluateAttackTechniqueApplicability, graph.value(step, RES.executedByMechanism))

        unknown = evaluation_for(graph, ATTACK_CRIT["t1692-001-command-message-authenticity-criterion"])
        record = graph.value(unknown, RES.hasDerivationRecord)
        self.assertEqual("incomplete", str(graph.value(record, RES.completenessStatus)))
        unresolved = graph.value(record, RES.hasUnresolvedInput)
        self.assertIn((unresolved, RDF.type, RES.UnresolvedInput), graph)

    def test_missing_conjunct_and_conflicting_evidence_remain_undetermined(self) -> None:
        graph = load_graph()
        add_evaluation(graph, "authentication", RAIL_CRIT["l1-authentication-criterion"], RES.satisfied)
        add_evaluation(graph, "confidentiality-positive", RAIL_CRIT["l1-confidentiality-criterion"], RES.satisfied)
        add_evaluation(graph, "confidentiality-negative", RAIL_CRIT["l1-confidentiality-criterion"], RES.notSatisfied)

        apply_rule(graph)

        for local_name in (
            "t0830-aitm-authentication-integrity-criterion",
            "t0842-network-sniffing-confidentiality-criterion",
        ):
            evaluation = evaluation_for(graph, ATTACK_CRIT[local_name])
            self.assertEqual(RES.undetermined, graph.value(evaluation, RES.hasEvaluationOutcome))
            record = graph.value(evaluation, RES.hasDerivationRecord)
            self.assertIsNotNone(graph.value(record, RES.hasUnresolvedInput))


if __name__ == "__main__":
    unittest.main()
