"""Step 12.3 — safety-critical elevation (M5-R04).

Elevation consumes an upstream transmission-threat CriterionEvaluation and the
payload carried by the flow. Both inputs can be unknown, and each unknown must
produce undetermined rather than a negative conclusion.
"""

from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
FX = Namespace("https://w3id.org/railsec-scope/fixture/railway-category/")
TH = Namespace("https://w3id.org/railsec-scope/fixture/railway-threat/")
CV = Namespace("https://w3id.org/railsec-scope/fixture/railway-critical/")
PROV = Namespace("http://www.w3.org/ns/prov#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RULE = Namespace("https://w3id.org/railsec-scope/rules#")

VIOLATIONS = [RAIL.criticalAuthenticityViolation, RAIL.criticalIntegrityViolation]

STAGE_RULES = [
    "evaluate-transmission-category.rq",
    "evaluate-transmission-threat.rq",
    "evaluate-critical-violation.rq",
]

EXPECTED = {
    (FX["cat3-flow"], RAIL.criticalAuthenticityViolation): RES.satisfied,
    (FX["cat3-flow"], RAIL.criticalIntegrityViolation): RES.satisfied,
    (FX["cat2-flow"], RAIL.criticalAuthenticityViolation): RES.notSatisfied,
    (FX["cat2-flow"], RAIL.criticalIntegrityViolation): RES.notSatisfied,
    (FX["cat1-flow"], RAIL.criticalAuthenticityViolation): RES.notSatisfied,
    (FX["cat1-flow"], RAIL.criticalIntegrityViolation): RES.notSatisfied,
    (TH["protected-cat3-flow"], RAIL.criticalAuthenticityViolation): RES.notSatisfied,
    (TH["protected-cat3-flow"], RAIL.criticalIntegrityViolation): RES.notSatisfied,
    (CV["no-payload-flow"], RAIL.criticalAuthenticityViolation): RES.undetermined,
    (CV["no-payload-flow"], RAIL.criticalIntegrityViolation): RES.undetermined,
    (FX["unknown-flow"], RAIL.criticalAuthenticityViolation): RES.undetermined,
    (FX["unknown-flow"], RAIL.criticalIntegrityViolation): RES.undetermined,
    (FX["no-input-flow"], RAIL.criticalAuthenticityViolation): RES.undetermined,
    (FX["no-input-flow"], RAIL.criticalIntegrityViolation): RES.undetermined,
}


def load_graph() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "imports" / "prov-o-dl.ttl")
    graph.parse(PROJECT / "rules" / "rules.ttl")
    graph.parse(PROJECT / "fixtures" / "railway-category" / "minimal.ttl")
    graph.parse(PROJECT / "fixtures" / "railway-threat" / "minimal.ttl")
    graph.parse(PROJECT / "fixtures" / "railway-critical" / "minimal.ttl")
    return graph


def apply_rule(graph: Graph, filename: str) -> int:
    inferred = graph.query((PROJECT / "rules" / filename).read_text(encoding="utf-8")).graph
    before = len(graph)
    graph += inferred
    return len(graph) - before


def apply_stages(graph: Graph) -> None:
    for filename in STAGE_RULES:
        apply_rule(graph, filename)


def elevation_outcomes(graph: Graph) -> dict:
    outcomes = {}
    for evaluation in graph.subjects(RDF.type, RES.CriterionEvaluation):
        criterion = graph.value(evaluation, RES.evaluatesCriterion)
        violation = graph.value(criterion, RAIL.assessesCriticalViolation)
        if violation is not None:
            flow = graph.value(evaluation, RES.evaluationConcernsElement)
            outcomes[(flow, violation)] = graph.value(evaluation, RES.hasEvaluationOutcome)
    return outcomes


class Phase2CriticalElevationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = load_graph()
        apply_stages(cls.graph)
        cls.outcomes = elevation_outcomes(cls.graph)

    def test_no_elevation_is_asserted_in_the_fixture(self) -> None:
        fixture = Graph().parse(PROJECT / "fixtures" / "railway-critical" / "minimal.ttl")
        self.assertEqual(0, len(list(fixture.subjects(RDF.type, RES.CriterionEvaluation))))

    def test_every_expected_outcome_is_produced(self) -> None:
        for key, expected in EXPECTED.items():
            with self.subTest(flow=str(key[0]).split("/")[-1], violation=str(key[1]).split("#")[-1]):
                self.assertEqual(expected, self.outcomes.get(key))

    def test_no_unexpected_elevation_evaluations(self) -> None:
        self.assertEqual(sorted(map(str, EXPECTED)), sorted(map(str, self.outcomes)))

    def test_undetermined_threat_propagates(self) -> None:
        for violation in VIOLATIONS:
            self.assertEqual(RES.undetermined, self.outcomes[(FX["unknown-flow"], violation)])

    def test_unknown_payload_propagates(self) -> None:
        for violation in VIOLATIONS:
            self.assertEqual(RES.undetermined, self.outcomes[(CV["no-payload-flow"], violation)])

    def test_safety_payload_alone_does_not_elevate(self) -> None:
        for violation in VIOLATIONS:
            self.assertEqual(RES.notSatisfied, self.outcomes[(TH["protected-cat3-flow"], violation)])

    def test_no_flow_is_typed_with_a_violation_term(self) -> None:
        for violation in VIOLATIONS:
            self.assertEqual([], list(self.graph.subjects(RDF.type, violation)))

    def test_every_elevation_cites_the_matching_threat_evaluation(self) -> None:
        for evaluation in self.graph.subjects(RDF.type, RES.CriterionEvaluation):
            criterion = self.graph.value(evaluation, RES.evaluatesCriterion)
            threat = self.graph.value(criterion, RAIL.elevatesTransmissionThreat)
            if threat is None:
                continue
            flow = self.graph.value(evaluation, RES.evaluationConcernsElement)
            run = self.graph.value(evaluation, RES.producedByRun)
            step = self.graph.value(self.graph.value(evaluation, RES.hasDerivationRecord), RES.hasStep)
            matching = []
            for used in self.graph.objects(step, RES.usedEntity):
                used_criterion = self.graph.value(used, RES.evaluatesCriterion)
                if (
                    self.graph.value(used, RES.evaluationConcernsElement) == flow
                    and self.graph.value(used, RES.producedByRun) == run
                    and self.graph.value(used_criterion, RAIL.assessesTransmissionThreat) == threat
                ):
                    matching.append(used)
            self.assertTrue(matching)
            self.assertEqual(RULE.EvaluateCriticalViolation, self.graph.value(step, RES.executedByMechanism))

    def test_known_payload_is_recorded_in_provenance(self) -> None:
        evaluation = FX["cat3-flow/evaluation/critical/criticalAuthenticityViolation"]
        step = self.graph.value(self.graph.value(evaluation, RES.hasDerivationRecord), RES.hasStep)
        self.assertIn((step, PROV.used, CV["safety-payload"]), self.graph)

    def test_completeness_status_matches_the_outcome(self) -> None:
        for (flow, violation), outcome in self.outcomes.items():
            evaluation = next(
                e
                for e in self.graph.subjects(RDF.type, RES.CriterionEvaluation)
                if self.graph.value(e, RES.evaluationConcernsElement) == flow
                and self.graph.value(self.graph.value(e, RES.evaluatesCriterion), RAIL.assessesCriticalViolation) == violation
            )
            record = self.graph.value(evaluation, RES.hasDerivationRecord)
            expected = "incomplete" if outcome == RES.undetermined else "complete"
            self.assertEqual(expected, str(self.graph.value(record, RES.completenessStatus)))

    def test_generic_stage_coverage_keeps_unknowns_in_the_denominator(self) -> None:
        coverage = {
            str(row.stage): row
            for row in self.graph.query((PROJECT / "queries" / "evaluation-stage-coverage.rq").read_text(encoding="utf-8"))
        }
        critical = coverage["critical-violation"]
        self.assertEqual(7, int(critical.totalCandidates))
        self.assertEqual(4, int(critical.determinedCandidates))
        self.assertEqual(3, int(critical.undeterminedCandidates))
        self.assertEqual(Decimal(4) / Decimal(7), Decimal(str(critical.stageCoverage)))

    def test_critical_criteria_have_source_locations_and_judgement_basis(self) -> None:
        criteria = list(self.graph.subjects(RAIL.assessesCriticalViolation, None))
        self.assertEqual(2, len(criteria))
        for criterion in criteria:
            basis = self.graph.value(criterion, CRIT.restsOnJudgement)
            self.assertIsNotNone(basis)
            self.assertIsNotNone(self.graph.value(criterion, CRIT.derivedFromSourceLocation))
            self.assertIsNotNone(self.graph.value(criterion, CRIT.appliesInterpretation))
            self.assertIn("exact source location", str(self.graph.value(basis, CRIT.reasoning)))

    def test_rule_requires_an_upstream_threat_evaluation(self) -> None:
        graph = load_graph()
        apply_rule(graph, "evaluate-transmission-category.rq")
        self.assertEqual(0, apply_rule(graph, "evaluate-critical-violation.rq"))

    def test_rule_application_reaches_a_fixed_point(self) -> None:
        before = len(self.graph)
        apply_stages(self.graph)
        self.assertEqual(before, len(self.graph), "re-applying the stages must add nothing")

    def test_result_conforms_to_structural_shapes(self) -> None:
        shapes = Graph().parse(PROJECT / "shapes" / "railway.ttl")
        shapes.parse(PROJECT / "shapes" / "criterion-slice.ttl")
        conforms, _, report = validate(data_graph=self.graph, shacl_graph=shapes, inference="none", advanced=True)
        self.assertTrue(conforms, report)

    def test_traceability_shape_rejects_a_missing_upstream_link(self) -> None:
        graph = Graph()
        graph += self.graph
        evaluation = FX["cat3-flow/evaluation/critical/criticalAuthenticityViolation"]
        step = graph.value(graph.value(evaluation, RES.hasDerivationRecord), RES.hasStep)
        for used in list(graph.objects(step, RES.usedEntity)):
            graph.remove((step, RES.usedEntity, used))

        shapes = Graph().parse(PROJECT / "shapes" / "railway.ttl")
        conforms, _, _ = validate(data_graph=graph, shacl_graph=shapes, inference="none", advanced=True)
        self.assertFalse(conforms)


if __name__ == "__main__":
    unittest.main()
