"""Step 12.4 — fail-safe compromise (M5-R05)."""

from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
FX = Namespace("https://w3id.org/railsec-scope/fixture/railway-category/")
TH = Namespace("https://w3id.org/railsec-scope/fixture/railway-threat/")
FS = Namespace("https://w3id.org/railsec-scope/fixture/railway-fail-safe/")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RULE = Namespace("https://w3id.org/railsec-scope/rules#")

VIOLATIONS = [RAIL.criticalAuthenticityViolation, RAIL.criticalIntegrityViolation]
STAGE_RULES = [
    "evaluate-transmission-category.rq",
    "evaluate-transmission-threat.rq",
    "evaluate-critical-violation.rq",
    "evaluate-fail-safe-compromise.rq",
]

EXPECTED = {
    **{(FS["compromised-asset"], violation): RES.satisfied for violation in VIOLATIONS},
    **{(FS["protected-asset"], violation): RES.notSatisfied for violation in VIOLATIONS},
    **{(FS["unknown-asset"], violation): RES.undetermined for violation in VIOLATIONS},
    **{(FS["missing-dependency-asset"], violation): RES.undetermined for violation in VIOLATIONS},
}


def load_graph() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "imports" / "prov-o-dl.ttl")
    graph.parse(PROJECT / "rules" / "rules.ttl")
    for fixture in ["railway-category", "railway-threat", "railway-critical", "railway-fail-safe"]:
        graph.parse(PROJECT / "fixtures" / fixture / "minimal.ttl")
    return graph


def apply_rule(graph: Graph, filename: str) -> int:
    inferred = graph.query((PROJECT / "rules" / filename).read_text(encoding="utf-8")).graph
    before = len(graph)
    graph += inferred
    return len(graph) - before


def apply_stages(graph: Graph) -> None:
    for filename in STAGE_RULES:
        apply_rule(graph, filename)


def fail_safe_outcomes(graph: Graph) -> dict:
    outcomes = {}
    for evaluation in graph.subjects(RDF.type, RES.CriterionEvaluation):
        criterion = graph.value(evaluation, RES.evaluatesCriterion)
        violation = graph.value(criterion, RAIL.assessesFailSafeCompromiseFrom)
        if violation is not None:
            asset = graph.value(evaluation, RES.evaluationConcernsElement)
            outcomes[(asset, violation)] = graph.value(evaluation, RES.hasEvaluationOutcome)
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

class Phase2FailSafeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = load_graph()
        apply_stages(cls.graph)
        cls.outcomes = fail_safe_outcomes(cls.graph)

    def test_fixture_asserts_no_fail_safe_results(self) -> None:
        fixture = Graph().parse(PROJECT / "fixtures" / "railway-fail-safe" / "minimal.ttl")
        self.assertEqual(0, len(list(fixture.subjects(RDF.type, RES.CriterionEvaluation))))

    def test_expected_three_valued_outcomes(self) -> None:
        self.assertEqual(EXPECTED, self.outcomes)

    def test_non_safety_critical_asset_is_not_a_candidate(self) -> None:
        self.assertFalse(any(asset == FS["ordinary-asset"] for asset, _ in self.outcomes))

    def test_unknown_upstream_critical_result_propagates(self) -> None:
        for violation in VIOLATIONS:
            self.assertEqual(RES.undetermined, self.outcomes[(FS["unknown-asset"], violation)])

    def test_missing_fail_safe_dependency_is_not_treated_as_absence(self) -> None:
        for violation in VIOLATIONS:
            self.assertEqual(RES.undetermined, self.outcomes[(FS["missing-dependency-asset"], violation)])

    def test_rule_requires_upstream_critical_evaluation(self) -> None:
        graph = load_graph()
        apply_rule(graph, "evaluate-transmission-category.rq")
        apply_rule(graph, "evaluate-transmission-threat.rq")
        self.assertEqual(0, apply_rule(graph, "evaluate-fail-safe-compromise.rq"))

    def test_provenance_cites_matching_critical_evaluation(self) -> None:
        evaluation = evaluation_for(self.graph, FS["compromised-asset"], RAIL.assessesFailSafeCompromiseFrom, RAIL.criticalIntegrityViolation)
        record = self.graph.value(evaluation, RES.hasDerivationRecord)
        step = self.graph.value(record, RES.hasStep)
        self.assertEqual(RULE.EvaluateFailSafeCompromise, self.graph.value(step, RES.executedByMechanism))
        used = list(self.graph.objects(step, RES.usedEntity))
        self.assertTrue(used)
        self.assertTrue(any(self.graph.value(item, RES.evaluationConcernsElement) == FX["cat3-flow"] for item in used))

    def test_no_legacy_fail_safe_class_is_materialised(self) -> None:
        self.assertFalse(any(str(term).endswith("FailSafeVulnerability") for term in self.graph.objects(None, RDF.type)))

    def test_generic_coverage_keeps_both_unknown_paths(self) -> None:
        coverage = {
            str(row.stage): row
            for row in self.graph.query((PROJECT / "queries" / "evaluation-stage-coverage.rq").read_text(encoding="utf-8"))
        }
        stage = coverage["fail-safe-compromise"]
        self.assertEqual(4, int(stage.totalCandidates))
        self.assertEqual(2, int(stage.determinedCandidates))
        self.assertEqual(2, int(stage.undeterminedCandidates))
        self.assertEqual(Decimal(1) / Decimal(2), Decimal(str(stage.stageCoverage)))

    def test_criteria_are_provisional_and_do_not_claim_source_locations(self) -> None:
        criteria = list(self.graph.subjects(RAIL.assessesFailSafeCompromiseFrom, None))
        self.assertEqual(2, len(criteria))
        for criterion in criteria:
            basis = self.graph.value(criterion, CRIT.restsOnJudgement)
            self.assertIsNotNone(basis)
            self.assertIsNone(self.graph.value(criterion, CRIT.derivedFromSourceLocation))
            self.assertIn("implementation history", str(self.graph.value(basis, CRIT.reasoning)))

    def test_rule_reaches_a_fixed_point(self) -> None:
        before = len(self.graph)
        apply_stages(self.graph)
        self.assertEqual(before, len(self.graph))

    def test_result_conforms_to_shapes(self) -> None:
        shapes = Graph().parse(PROJECT / "shapes" / "railway.ttl")
        shapes.parse(PROJECT / "shapes" / "criterion-slice.ttl")
        conforms, _, report = validate(data_graph=self.graph, shacl_graph=shapes, inference="none", advanced=True)
        self.assertTrue(conforms, report)

    def test_traceability_shape_rejects_missing_upstream_link(self) -> None:
        graph = Graph()
        graph += self.graph
        evaluation = evaluation_for(self.graph, FS["compromised-asset"], RAIL.assessesFailSafeCompromiseFrom, RAIL.criticalIntegrityViolation)
        step = graph.value(graph.value(evaluation, RES.hasDerivationRecord), RES.hasStep)
        for used in list(graph.objects(step, RES.usedEntity)):
            graph.remove((step, RES.usedEntity, used))
        shapes = Graph().parse(PROJECT / "shapes" / "railway.ttl")
        conforms, _, _ = validate(data_graph=graph, shacl_graph=shapes, inference="none", advanced=True)
        self.assertFalse(conforms)

    def test_dependency_shape_rejects_a_false_determined_result(self) -> None:
        graph = Graph()
        graph += self.graph
        evaluation = evaluation_for(self.graph, FS["missing-dependency-asset"], RAIL.assessesFailSafeCompromiseFrom, RAIL.criticalIntegrityViolation)
        graph.remove((evaluation, RES.hasEvaluationOutcome, RES.undetermined))
        graph.add((evaluation, RES.hasEvaluationOutcome, RES.satisfied))
        shapes = Graph().parse(PROJECT / "shapes" / "railway.ttl")
        conforms, _, _ = validate(data_graph=graph, shacl_graph=shapes, inference="none", advanced=True)
        self.assertFalse(conforms)


if __name__ == "__main__":
    unittest.main()
