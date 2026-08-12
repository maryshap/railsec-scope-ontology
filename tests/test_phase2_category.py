from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, OWL, RDF


PROJECT = Path(__file__).resolve().parents[1]
FX = Namespace("https://w3id.org/railsec-scope/fixture/railway-category/")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RSSO = Namespace("https://w3id.org/railsec-scope/ontology#")


def load_ontology() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "imports" / "prov-o-dl.ttl")
    graph.parse(PROJECT / "rules" / "rules.ttl")
    return graph


def apply_rule(graph: Graph, filename: str) -> int:
    inferred = graph.query((PROJECT / "rules" / filename).read_text(encoding="utf-8")).graph
    before = len(graph)
    graph += inferred
    return len(graph) - before


class Phase2TransmissionCategoryTest(unittest.TestCase):
    def test_category_is_derived_through_three_valued_evaluations(self) -> None:
        fixture_path = PROJECT / "fixtures" / "railway-category" / "minimal.ttl"
        fixture_only = Graph().parse(fixture_path)
        # Criteria live in the module, not in the fixture, so the stage coverage
        # is read against fixture plus module. Every stage declared for railway
        # flows now appears; this test concerns the transmission-category stage.
        fixture_only.parse(PROJECT / "ontology" / "criteria-railway.ttl")
        coverage_query = (PROJECT / "queries" / "evaluation-stage-coverage.rq").read_text(encoding="utf-8")
        stages = {str(row.stage): row for row in fixture_only.query(coverage_query)}
        self.assertIn("transmission-category", stages)
        row = stages["transmission-category"]
        self.assertEqual(5, int(row.totalCandidates))
        self.assertEqual(0, int(row.determinedCandidates))
        self.assertEqual(5, int(row.undeterminedCandidates))
        categories = [RAIL.Category1Transmission, RAIL.Category2Transmission, RAIL.Category3Transmission]
        for flow in [FX["cat1-flow"], FX["cat2-flow"], FX["cat3-flow"], FX["unknown-flow"], FX["no-input-flow"]]:
            for category in categories:
                self.assertNotIn((flow, RDF.type, category), fixture_only, "Input fixture must not assert a derived category")

        graph = load_ontology()
        graph += fixture_only
        self.assertGreater(apply_rule(graph, "evaluate-transmission-category.rq"), 0)
        self.assertGreater(apply_rule(graph, "classify-transmission-category.rq"), 0)
        self.assertEqual(0, apply_rule(graph, "evaluate-transmission-category.rq"))
        self.assertEqual(0, apply_rule(graph, "classify-transmission-category.rq"))

        expected_memberships = {
            FX["cat1-flow"]: RAIL.Category1Transmission,
            FX["cat2-flow"]: RAIL.Category2Transmission,
            FX["cat3-flow"]: RAIL.Category3Transmission,
        }
        for flow, expected in expected_memberships.items():
            self.assertIn((flow, RDF.type, expected), graph)
            for category in set(categories) - {expected}:
                self.assertNotIn((flow, RDF.type, category), graph)
        for category in categories:
            self.assertNotIn((FX["unknown-flow"], RDF.type, category), graph)
            self.assertNotIn((FX["no-input-flow"], RDF.type, category), graph)

        outcomes = {}
        for evaluation in graph.subjects(RDF.type, RES.CriterionEvaluation):
            flow = graph.value(evaluation, RES.evaluationConcernsElement)
            criterion = graph.value(evaluation, RES.evaluatesCriterion)
            category = graph.value(criterion, Namespace("https://w3id.org/railsec-scope/criteria#").determinesMembershipOf)
            outcomes[(flow, category)] = graph.value(evaluation, RES.hasEvaluationOutcome)
        expected_outcomes = {
            FX["cat1-flow"]: [RES.satisfied, RES.notSatisfied, RES.notSatisfied],
            FX["cat2-flow"]: [RES.notSatisfied, RES.satisfied, RES.notSatisfied],
            FX["cat3-flow"]: [RES.notSatisfied, RES.notSatisfied, RES.satisfied],
            FX["unknown-flow"]: [RES.notSatisfied, RES.undetermined, RES.undetermined],
            FX["no-input-flow"]: [RES.undetermined, RES.undetermined, RES.undetermined],
        }
        for flow, flow_outcomes in expected_outcomes.items():
            for category, outcome in zip(categories, flow_outcomes):
                self.assertEqual(outcome, outcomes[(flow, category)])

        cat2_evaluation = FX["cat2-flow/evaluation/Category2Transmission"]
        record = graph.value(cat2_evaluation, RES.hasDerivationRecord)
        step = graph.value(record, RES.hasStep)
        self.assertIn((step, RES.usedEntity, FX["cat2-access"]), graph)
        self.assertIn((step, RES.usedEntity, FX["cat2-control"]), graph)
        self.assertIn((step, RES.usedEntity, FX["cat2-fixed"]), graph)

        coverage_by_stage = {str(row.stage): row for row in graph.query(coverage_query)}
        self.assertIn("transmission-category", coverage_by_stage)
        coverage = coverage_by_stage["transmission-category"]
        self.assertEqual(5, int(coverage.totalCandidates))
        self.assertEqual(3, int(coverage.determinedCandidates))
        self.assertEqual(2, int(coverage.undeterminedCandidates))
        self.assertEqual(Decimal("0.6"), Decimal(str(coverage.stageCoverage)))

        shapes = Graph().parse(PROJECT / "shapes" / "railway.ttl")
        shapes.parse(PROJECT / "shapes" / "criterion-slice.ttl")
        conforms, _, report = validate(data_graph=graph, shacl_graph=shapes, inference="none", advanced=True)
        self.assertTrue(conforms, report)

    def test_access_exclusion_requires_attributed_assumption(self) -> None:
        data = load_ontology()
        data.parse(PROJECT / "fixtures" / "railway-category" / "invalid-access-assumption.ttl")
        shapes = Graph().parse(PROJECT / "shapes" / "railway.ttl")
        conforms, _, report = validate(data_graph=data, shacl_graph=shapes, inference="none", advanced=True)
        self.assertFalse(conforms)
        self.assertIn("responsible assessor", report)

    def test_threat_links_are_annotations_not_reasoning_axioms(self) -> None:
        graph = Graph().parse(PROJECT / "ontology" / "ontology.ttl")
        graph.parse(PROJECT / "ontology" / "railway.ttl")
        self.assertIn((RSSO.documentsAddressedThreat, RDF.type, OWL.AnnotationProperty), graph)
        self.assertIn((RAIL.integrityProtectionEnabled, RSSO.documentsAddressedThreat, RAIL.CorruptionThreat), graph)
        self.assertIn(
            (
                RAIL.encryptionEnabled,
                RSSO.sourceLocatorNote,
                Literal("IEC 62443-3-3 FR4 — confidentiality; outside the EN 50159 safety-communication threat set", lang="en"),
            ),
            graph,
        )
        self.assertFalse(any(graph.triples((RAIL.encryptionEnabled, RSSO.documentsAddressedThreat, None))))
        self.assertNotIn((RAIL.documentsAddressedThreat, RDF.type, OWL.ObjectProperty), graph)
        self.assertFalse(any(graph.triples((None, RAIL.hasTransmissionCategory, None))))

    def test_boundary_coverage_keeps_undetermined_in_denominator(self) -> None:
        graph = Graph().parse(PROJECT / "fixtures" / "boundary-coverage" / "mixed.ttl")
        query = (PROJECT / "queries" / "boundary-assessment-coverage.rq").read_text(encoding="utf-8")
        rows = list(graph.query(query))
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual(3, int(row.totalElements))
        self.assertEqual(2, int(row.determinedElements))
        self.assertEqual(1, int(row.undeterminedElements))
        self.assertEqual(Decimal(2) / Decimal(3), Decimal(str(row.boundaryAssessmentCoverage)))

        shapes = Graph().parse(PROJECT / "shapes" / "constraints.ttl")
        conforms, _, report = validate(data_graph=graph, shacl_graph=shapes, inference="none", advanced=True)
        self.assertTrue(conforms, report)


if __name__ == "__main__":
    unittest.main()
