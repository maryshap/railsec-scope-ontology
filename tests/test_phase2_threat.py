from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
CAT = Namespace("https://w3id.org/railsec-scope/fixture/railway-category/")
TH = Namespace("https://w3id.org/railsec-scope/fixture/railway-threat/")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RULE = Namespace("https://w3id.org/railsec-scope/rules#")

THREATS = [
    RAIL.RepetitionThreat,
    RAIL.DeletionThreat,
    RAIL.InsertionThreat,
    RAIL.ResequencingThreat,
    RAIL.CorruptionThreat,
    RAIL.DelayThreat,
    RAIL.MasqueradeThreat,
]


def load_graph() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "imports" / "prov-o-dl.ttl")
    graph.parse(PROJECT / "rules" / "rules.ttl")
    graph.parse(PROJECT / "fixtures" / "railway-category" / "minimal.ttl")
    graph.parse(PROJECT / "fixtures" / "railway-threat" / "minimal.ttl")
    return graph


def apply_rule(graph: Graph, filename: str) -> int:
    inferred = graph.query((PROJECT / "rules" / filename).read_text(encoding="utf-8")).graph
    before = len(graph)
    graph += inferred
    return len(graph) - before


def threat_outcomes(graph: Graph) -> dict[tuple, object]:
    outcomes = {}
    for evaluation in graph.subjects(RDF.type, RES.CriterionEvaluation):
        criterion = graph.value(evaluation, RES.evaluatesCriterion)
        threat = graph.value(criterion, RAIL.assessesTransmissionThreat)
        if threat is not None:
            flow = graph.value(evaluation, RES.evaluationConcernsElement)
            outcomes[(flow, threat)] = graph.value(evaluation, RES.hasEvaluationOutcome)
    return outcomes



def evaluation_for(graph, element, criterion_predicate, criterion_value):
    """Locate an evaluation by what it is about rather than by its IRI shape.

    Result IRIs are run-scoped, so hard-coding them couples a test to the
    identifier construction. Selecting on the element and the criterion keeps
    the test about behaviour.
    """
    for candidate in graph.subjects(RES.evaluationConcernsElement, element):
        criterion = graph.value(candidate, RES.evaluatesCriterion)
        if criterion is not None and (criterion, criterion_predicate, criterion_value) in graph:
            return candidate
    raise AssertionError(f"no evaluation for {element} under {criterion_value}")

class Phase2TransmissionThreatTest(unittest.TestCase):
    def test_seven_threats_propagate_category_unknowns(self) -> None:
        graph = load_graph()
        self.assertGreater(apply_rule(graph, "evaluate-transmission-category.rq"), 0)
        self.assertGreater(apply_rule(graph, "classify-transmission-category.rq"), 0)
        self.assertGreater(apply_rule(graph, "evaluate-transmission-threat.rq"), 0)
        self.assertEqual(0, apply_rule(graph, "evaluate-transmission-threat.rq"))

        outcomes = threat_outcomes(graph)
        self.assertEqual(6 * 7, len(outcomes))

        for threat in THREATS:
            self.assertEqual(RES.notSatisfied, outcomes[(CAT["cat1-flow"], threat)])
            self.assertEqual(RES.undetermined, outcomes[(CAT["unknown-flow"], threat)])
            self.assertEqual(RES.undetermined, outcomes[(CAT["no-input-flow"], threat)])
            self.assertEqual(RES.notSatisfied, outcomes[(TH["protected-cat3-flow"], threat)])

        for threat in THREATS:
            self.assertEqual(RES.satisfied, outcomes[(CAT["cat3-flow"], threat)])
        for threat in set(THREATS) - {RAIL.InsertionThreat, RAIL.MasqueradeThreat}:
            self.assertEqual(RES.satisfied, outcomes[(CAT["cat2-flow"], threat)])
        for threat in {RAIL.InsertionThreat, RAIL.MasqueradeThreat}:
            self.assertEqual(RES.notSatisfied, outcomes[(CAT["cat2-flow"], threat)])

        for flow in [CAT["cat1-flow"], CAT["cat2-flow"], CAT["cat3-flow"], TH["protected-cat3-flow"]]:
            for threat in THREATS:
                self.assertNotIn((flow, RDF.type, threat), graph, "Threat exposure must remain an evaluation, not direct flow typing")

        evaluation = evaluation_for(graph, CAT["cat3-flow"], RAIL.assessesTransmissionThreat, RAIL.MasqueradeThreat)
        record = graph.value(evaluation, RES.hasDerivationRecord)
        step = graph.value(record, RES.hasStep)
        self.assertIn((step, RES.executedByMechanism, RULE.EvaluateTransmissionThreat), graph)
        category_evaluation = evaluation_for(
            graph, CAT["cat3-flow"], CRIT.determinesMembershipOf, RAIL.Category3Transmission
        )
        self.assertIn((step, RES.usedEntity, category_evaluation), graph)

        coverage = {
            str(row.stage): row
            for row in graph.query((PROJECT / "queries" / "evaluation-stage-coverage.rq").read_text(encoding="utf-8"))
        }
        threat_coverage = coverage["transmission-threat"]
        self.assertEqual(6, int(threat_coverage.totalCandidates))
        self.assertEqual(4, int(threat_coverage.determinedCandidates))
        self.assertEqual(2, int(threat_coverage.undeterminedCandidates))
        self.assertEqual(Decimal(2) / Decimal(3), Decimal(str(threat_coverage.stageCoverage)))

        shapes = Graph().parse(PROJECT / "shapes" / "railway.ttl")
        shapes.parse(PROJECT / "shapes" / "criterion-slice.ttl")
        conforms, _, report = validate(data_graph=graph, shacl_graph=shapes, inference="none", advanced=True)
        self.assertTrue(conforms, report)

    def test_threat_criteria_have_source_locations_and_judgement_basis(self) -> None:
        graph = load_graph()
        for criterion in graph.subjects(RAIL.assessesTransmissionThreat, None):
            basis = graph.value(criterion, CRIT.restsOnJudgement)
            self.assertIsNotNone(basis)
            self.assertIsNotNone(graph.value(criterion, CRIT.derivedFromSourceLocation))
            self.assertIsNotNone(graph.value(criterion, CRIT.appliesInterpretation))
            self.assertIn("legacy documents are implementation history", str(graph.value(basis, CRIT.reasoning)))


if __name__ == "__main__":
    unittest.main()
