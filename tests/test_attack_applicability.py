"""Focused contract tests for sourced L3 technique-applicability criteria."""

from __future__ import annotations

import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, XSD


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
    graph.add((FX.flow, RDF.type, CRIT.CandidateExaminationTarget))
    graph.add((FX.asset, RDF.type, RAIL.SafetyCriticalAsset))
    graph.add((FX.asset, RDF.type, CRIT.CandidateExaminationTarget))
    return graph


def add_evaluation(graph: Graph, name: str, criterion, outcome, element=FX.flow) -> None:
    evaluation = FX[name]
    graph.add((evaluation, RDF.type, RES.CriterionEvaluation))
    graph.add((evaluation, RES.evaluationConcernsElement, element))
    graph.add((evaluation, RES.evaluatesCriterion, criterion))
    graph.add((evaluation, RES.hasEvaluationOutcome, outcome))
    graph.add((evaluation, RES.producedByRun, FX.run))


def apply_rule(graph: Graph) -> None:
    query = (PROJECT / "rules" / "evaluate-attack-technique-applicability.rq").read_text(encoding="utf-8")
    graph += graph.query(query).graph


def evaluation_for(graph: Graph, criterion, element=FX.flow):
    for evaluation in graph.subjects(RES.evaluatesCriterion, criterion):
        if graph.value(evaluation, RES.evaluationConcernsElement) == element:
            return evaluation
    return None


def add_asset_applicability_criterion(graph: Graph) -> None:
    graph.add((FX.asset_attack_criterion, RDF.type, CRIT.Criterion))
    graph.add((FX.asset_attack_criterion, CRIT.evaluationStageIdentifier, Literal("attack-technique-applicability")))
    graph.add((
        FX.asset_attack_criterion,
        CRIT.stageCandidateTypeIri,
        Literal(str(RAIL.RailwayAsset), datatype=XSD.anyURI),
    ))
    graph.add((FX.asset_attack_criterion, ATTACK.assessesAttackTechnique, ATTACK_ICS.T0883))
    graph.add((FX.asset_attack_criterion, ATTACK.requiresSatisfiedEvaluationOf, RAIL_CRIT["asset-exposed-criterion"]))


class AttackApplicabilityTest(unittest.TestCase):
    def test_criteria_are_sourced_and_point_to_projected_techniques(self) -> None:
        graph = load_graph()
        expected = {
            ATTACK_CRIT["t0842-network-sniffing-confidentiality-criterion"]: ATTACK_ICS.T0842,
            ATTACK_CRIT["t0814-dos-rate-limiting-criterion"]: ATTACK_ICS.T0814,
            ATTACK_CRIT["t1692-001-command-message-authenticity-criterion"]: ATTACK_ICS["T1692.001"],
            ATTACK_CRIT["t0830-aitm-authentication-integrity-criterion"]: ATTACK_ICS.T0830,
            ATTACK_CRIT["t1691-001-block-command-message-timeliness-criterion"]: ATTACK_ICS["T1691.001"],
            ATTACK_CRIT["t1692-002-reporting-message-sequence-criterion"]: ATTACK_ICS["T1692.002"],
            ATTACK_CRIT["t0832-manipulation-of-view-sequence-criterion"]: ATTACK_ICS.T0832,
            ATTACK_CRIT["t0830-aitm-critical-integrity-criterion"]: ATTACK_ICS.T0830,
            ATTACK_CRIT["t0831-manipulation-of-control-authenticity-criterion"]: ATTACK_ICS.T0831,
            ATTACK_CRIT["t0815-denial-of-view-sequence-criterion"]: ATTACK_ICS.T0815,
            ATTACK_CRIT["t0829-loss-of-view-sequence-criterion"]: ATTACK_ICS.T0829,
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
        add_evaluation(graph, "critical-integrity", RAIL_CRIT["critical-integrity-criterion"], RES.satisfied)
        add_evaluation(graph, "critical-timeliness", RAIL_CRIT["critical-timeliness-criterion"], RES.satisfied)
        add_evaluation(graph, "critical-sequence", RAIL_CRIT["critical-sequence-criterion"], RES.notSatisfied)
        add_evaluation(graph, "authentication", RAIL_CRIT["l1-authentication-criterion"], RES.satisfied)
        add_evaluation(graph, "integrity", RAIL_CRIT["l1-integrity-criterion"], RES.satisfied)

        apply_rule(graph)

        expected = {
            "t0842-network-sniffing-confidentiality-criterion": RES.satisfied,
            "t0814-dos-rate-limiting-criterion": RES.notSatisfied,
            "t1692-001-command-message-authenticity-criterion": RES.undetermined,
            "t0830-aitm-authentication-integrity-criterion": RES.satisfied,
            "t1691-001-block-command-message-timeliness-criterion": RES.satisfied,
            "t1692-002-reporting-message-sequence-criterion": RES.notSatisfied,
            "t0832-manipulation-of-view-sequence-criterion": RES.notSatisfied,
            "t0830-aitm-critical-integrity-criterion": RES.satisfied,
            "t0831-manipulation-of-control-authenticity-criterion": RES.undetermined,
            "t0815-denial-of-view-sequence-criterion": RES.notSatisfied,
            "t0829-loss-of-view-sequence-criterion": RES.notSatisfied,
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

    def test_candidate_type_is_declared_by_the_criterion_not_hard_coded_to_flows(self) -> None:
        graph = load_graph()
        add_asset_applicability_criterion(graph)
        add_evaluation(
            graph,
            "asset-exposed",
            RAIL_CRIT["asset-exposed-criterion"],
            RES.satisfied,
            element=FX.asset,
        )

        apply_rule(graph)

        evaluation = evaluation_for(graph, FX.asset_attack_criterion, element=FX.asset)
        self.assertIsNotNone(evaluation)
        self.assertEqual(RES.satisfied, graph.value(evaluation, RES.hasEvaluationOutcome))
        step = graph.value(graph.value(evaluation, RES.hasDerivationRecord), RES.hasStep)
        self.assertEqual(FX.asset, graph.value(step, RES.generatedResult / RES.evaluationConcernsElement))


if __name__ == "__main__":
    unittest.main()
