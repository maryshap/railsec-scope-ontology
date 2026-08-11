"""Step 12.6 — access risk (M5-R07, M5-R08), legacy v3 R2.6.1-R2.6.4.

Two subjects. Assets carry privileged maintenance and supplier access risk;
flows carry high-risk maintenance paths and remote access risk. An unstated
access inventory is never read as absence of access.

R2.6.1 is re-subjected from the maintenance actor to the safety-critical asset,
because actors and roles are not in the approved model. Recorded in CR-B-016.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
FX = Namespace("https://w3id.org/railsec-scope/fixture/railway-category/")
FS = Namespace("https://w3id.org/railsec-scope/fixture/railway-fail-safe/")
AC = Namespace("https://w3id.org/railsec-scope/fixture/railway-access/")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RULE = Namespace("https://w3id.org/railsec-scope/rules#")

STAGE_RULES = [
    "evaluate-transmission-category.rq",
    "evaluate-transmission-threat.rq",
    "evaluate-critical-violation.rq",
    "evaluate-fail-safe-compromise.rq",
    "evaluate-sil-risk.rq",
    "evaluate-access-risk-asset.rq",
    "evaluate-access-path-risk.rq",
]

EXPECTED = {
    # Asset access risk. compromised-asset records both mechanisms, protected-asset
    # records an inventory containing neither, unknown-asset records none at all.
    (FS["compromised-asset"], RAIL.privilegedMaintenanceAccessRisk): RES.satisfied,
    (FS["compromised-asset"], RAIL.privilegedSupplierAccessRisk): RES.satisfied,
    (FS["protected-asset"], RAIL.privilegedMaintenanceAccessRisk): RES.notSatisfied,
    (FS["protected-asset"], RAIL.privilegedSupplierAccessRisk): RES.notSatisfied,
    (FS["unknown-asset"], RAIL.privilegedMaintenanceAccessRisk): RES.undetermined,
    (FS["unknown-asset"], RAIL.privilegedSupplierAccessRisk): RES.undetermined,
    # Flow access risk.
    (FX["cat3-flow"], RAIL.highRiskMaintenancePath): RES.satisfied,
    (FX["cat2-flow"], RAIL.highRiskMaintenancePath): RES.notSatisfied,
    (FX["cat3-flow"], RAIL.remoteAccessRisk): RES.satisfied,
    (FX["cat2-flow"], RAIL.remoteAccessRisk): RES.satisfied,
    (FX["unknown-flow"], RAIL.remoteAccessRisk): RES.undetermined,
    (FX["unknown-flow"], RAIL.highRiskMaintenancePath): RES.undetermined,
    # Origin has maintenance access but the destination is not safety-critical.
    (AC["non-critical-path-flow"], RAIL.highRiskMaintenancePath): RES.notSatisfied,
    (AC["non-critical-path-flow"], RAIL.remoteAccessRisk): RES.notSatisfied,
}


def load_graph() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "imports" / "prov-o-dl.ttl")
    graph.parse(PROJECT / "rules" / "rules.ttl")
    for name in ("railway-category", "railway-threat", "railway-critical",
                 "railway-fail-safe", "railway-sil", "railway-access"):
        graph.parse(PROJECT / "fixtures" / name / "minimal.ttl")
    return graph


def apply_stages(graph: Graph) -> None:
    for filename in STAGE_RULES:
        graph += graph.query((PROJECT / "rules" / filename).read_text(encoding="utf-8")).graph


def access_outcomes(graph: Graph) -> dict:
    outcomes = {}
    for evaluation in graph.subjects(RDF.type, RES.CriterionEvaluation):
        criterion = graph.value(evaluation, RES.evaluatesCriterion)
        risk = graph.value(criterion, RAIL.assessesAccessRisk)
        if risk is not None:
            element = graph.value(evaluation, RES.evaluationConcernsElement)
            outcomes[(element, risk)] = graph.value(evaluation, RES.hasEvaluationOutcome)
    return outcomes


class Phase2AccessRiskTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = load_graph()
        apply_stages(cls.graph)
        cls.outcomes = access_outcomes(cls.graph)

    def test_no_access_evaluation_is_asserted_in_the_fixture(self) -> None:
        fixture = Graph().parse(PROJECT / "fixtures" / "railway-access" / "minimal.ttl")
        self.assertEqual(0, len(list(fixture.subjects(RDF.type, RES.CriterionEvaluation))))

    def test_every_expected_outcome_is_produced(self) -> None:
        for key, expected in EXPECTED.items():
            with self.subTest(element=str(key[0]).split("/")[-1], risk=str(key[1]).split("#")[-1]):
                self.assertEqual(expected, self.outcomes.get(key))

    def test_unstated_access_inventory_is_undetermined(self) -> None:
        """An asset with no reachableBy statement must not be read as unreachable."""
        for risk in (RAIL.privilegedMaintenanceAccessRisk, RAIL.privilegedSupplierAccessRisk):
            with self.subTest(risk=str(risk).split("#")[-1]):
                self.assertEqual(RES.undetermined, self.outcomes[(FS["unknown-asset"], risk)])

    def test_stated_inventory_without_the_mechanism_is_negative(self) -> None:
        """protected-asset records remote access only, so maintenance is genuinely absent."""
        self.assertEqual(RES.notSatisfied, self.outcomes[(FS["protected-asset"], RAIL.privilegedMaintenanceAccessRisk)])

    def test_remote_access_risk_propagates_undetermined_threats(self) -> None:
        self.assertEqual(RES.undetermined, self.outcomes[(FX["unknown-flow"], RAIL.remoteAccessRisk)])

    def test_maintenance_path_requires_a_safety_critical_destination(self) -> None:
        """Origin access alone is not sufficient; the destination condition must hold."""
        self.assertEqual(RES.notSatisfied, self.outcomes[(AC["non-critical-path-flow"], RAIL.highRiskMaintenancePath)])

    def test_maintenance_path_requires_maintenance_access_on_the_origin(self) -> None:
        """cat2-flow terminates at a safety-critical asset but its origin has no maintenance access."""
        self.assertEqual(RES.notSatisfied, self.outcomes[(FX["cat2-flow"], RAIL.highRiskMaintenancePath)])

    def test_no_element_is_typed_with_a_risk_class(self) -> None:
        for risk in (RAIL.privilegedMaintenanceAccessRisk, RAIL.privilegedSupplierAccessRisk,
                     RAIL.highRiskMaintenancePath, RAIL.remoteAccessRisk):
            with self.subTest(risk=str(risk).split("#")[-1]):
                self.assertEqual([], list(self.graph.subjects(RDF.type, risk)))

    def test_each_evaluation_has_a_derivation_record(self) -> None:
        for (element, risk) in EXPECTED:
            with self.subTest(element=str(element).split("/")[-1], risk=str(risk).split("#")[-1]):
                evaluation = next(
                    e for e in self.graph.subjects(RDF.type, RES.CriterionEvaluation)
                    if self.graph.value(e, RES.evaluationConcernsElement) == element
                    and self.graph.value(self.graph.value(e, RES.evaluatesCriterion), RAIL.assessesAccessRisk) == risk
                )
                step = self.graph.value(self.graph.value(evaluation, RES.hasDerivationRecord), RES.hasStep)
                self.assertIn(self.graph.value(step, RES.executedByMechanism),
                              (RULE.EvaluateAssetAccessRisk, RULE.EvaluateAccessPathRisk))
                self.assertEqual("L2", str(self.graph.value(step, RES.layerIdentifier)))

    def test_completeness_status_matches_the_outcome(self) -> None:
        for (element, risk), outcome in self.outcomes.items():
            with self.subTest(element=str(element).split("/")[-1], risk=str(risk).split("#")[-1]):
                evaluation = next(
                    e for e in self.graph.subjects(RDF.type, RES.CriterionEvaluation)
                    if self.graph.value(e, RES.evaluationConcernsElement) == element
                    and self.graph.value(self.graph.value(e, RES.evaluatesCriterion), RAIL.assessesAccessRisk) == risk
                )
                record = self.graph.value(evaluation, RES.hasDerivationRecord)
                expected = "incomplete" if outcome == RES.undetermined else "complete"
                self.assertEqual(expected, str(self.graph.value(record, RES.completenessStatus)))

    def test_criteria_rest_on_a_recorded_judgement(self) -> None:
        for criterion in self.graph.subjects(RAIL.assessesAccessRisk, None):
            with self.subTest(criterion=str(criterion).split("/")[-1]):
                self.assertIsNone(self.graph.value(criterion, CRIT.derivedFromSource))
                self.assertIsNotNone(self.graph.value(criterion, CRIT.restsOnJudgement))

    def test_rule_application_reaches_a_fixed_point(self) -> None:
        before = len(self.graph)
        apply_stages(self.graph)
        self.assertEqual(before, len(self.graph))

    def test_result_conforms_to_structural_shapes(self) -> None:
        shapes = Graph().parse(PROJECT / "shapes" / "railway.ttl")
        shapes.parse(PROJECT / "shapes" / "criterion-slice.ttl")
        conforms, _, report = validate(data_graph=self.graph, shacl_graph=shapes, inference="none", advanced=True)
        self.assertTrue(conforms, report)


if __name__ == "__main__":
    unittest.main()
