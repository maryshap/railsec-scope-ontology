"""Step 12.5 — maximum SIL risk (M5-R06), legacy v3 R2.5.3.

The stage aggregates the fail-safe compromise evaluations of a safety-critical
asset. It is the fifth link in the chain, so it also serves as the end-to-end
proof that an unknown asserted at the transmission stage still reaches the last
stage as undetermined rather than as a negative conclusion.

  compromised-asset         fail-safe satisfied            -> satisfied
  protected-asset           fail-safe notSatisfied         -> notSatisfied
  unknown-asset             upstream category unknown      -> undetermined
  missing-dependency-asset  fail-safe dependency unstated  -> undetermined
  no-upstream-asset         no fail-safe evaluation at all -> no result

Legacy v3 R2.5.1 and R2.5.2 are not implemented: they require an attack
technique vocabulary that the approved model does not contain.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
FS = Namespace("https://w3id.org/railsec-scope/fixture/railway-fail-safe/")
SIL = Namespace("https://w3id.org/railsec-scope/fixture/railway-sil/")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RULE = Namespace("https://w3id.org/railsec-scope/rules#")
RSSCR = Namespace("https://w3id.org/railsec-scope/criteria/railway/")

STAGE_RULES = [
    "evaluate-transmission-category.rq",
    "evaluate-transmission-threat.rq",
    "evaluate-critical-violation.rq",
    "evaluate-fail-safe-compromise.rq",
    "evaluate-sil-risk.rq",
]

EXPECTED = {
    FS["compromised-asset"]: RES.satisfied,
    FS["protected-asset"]: RES.notSatisfied,
    FS["unknown-asset"]: RES.undetermined,
    FS["missing-dependency-asset"]: RES.undetermined,
}


def load_graph() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "imports" / "prov-o-dl.ttl")
    graph.parse(PROJECT / "rules" / "rules.ttl")
    for name in ("railway-category", "railway-threat", "railway-critical", "railway-fail-safe", "railway-sil"):
        graph.parse(PROJECT / "fixtures" / name / "minimal.ttl")
    return graph


def apply_stages(graph: Graph) -> None:
    for filename in STAGE_RULES:
        graph += graph.query((PROJECT / "rules" / filename).read_text(encoding="utf-8")).graph


def sil_outcomes(graph: Graph) -> dict:
    outcomes = {}
    for evaluation in graph.subjects(RDF.type, RES.CriterionEvaluation):
        criterion = graph.value(evaluation, RES.evaluatesCriterion)
        if graph.value(criterion, RAIL.assessesSILRisk) is not None:
            asset = graph.value(evaluation, RES.evaluationConcernsElement)
            outcomes[asset] = graph.value(evaluation, RES.hasEvaluationOutcome)
    return outcomes


class Phase2SILRiskTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = load_graph()
        apply_stages(cls.graph)
        cls.outcomes = sil_outcomes(cls.graph)

    def test_no_sil_evaluation_is_asserted_in_the_fixture(self) -> None:
        fixture = Graph().parse(PROJECT / "fixtures" / "railway-sil" / "minimal.ttl")
        self.assertEqual(0, len(list(fixture.subjects(RDF.type, RES.CriterionEvaluation))))

    def test_every_expected_outcome_is_produced(self) -> None:
        for asset, expected in EXPECTED.items():
            with self.subTest(asset=str(asset).split("/")[-1]):
                self.assertEqual(expected, self.outcomes.get(asset))

    def test_asset_without_upstream_evaluation_receives_no_result(self) -> None:
        """An absent upstream stage must not produce a default conclusion."""
        self.assertNotIn(SIL["no-upstream-asset"], self.outcomes)

    def test_no_unexpected_sil_evaluations(self) -> None:
        self.assertEqual(sorted(map(str, EXPECTED)), sorted(map(str, self.outcomes)))

    def test_undetermined_reaches_the_final_stage(self) -> None:
        """End-to-end: an unknown at the transmission stage is still undetermined here."""
        self.assertEqual(RES.undetermined, self.outcomes[FS["unknown-asset"]])

    def test_no_asset_is_typed_with_a_risk_class(self) -> None:
        self.assertEqual([], list(self.graph.subjects(RDF.type, RAIL.maximumSILRisk)))

    def test_each_evaluation_cites_the_fail_safe_input(self) -> None:
        for asset in EXPECTED:
            with self.subTest(asset=str(asset).split("/")[-1]):
                evaluation = next(
                    e for e in self.graph.subjects(RDF.type, RES.CriterionEvaluation)
                    if self.graph.value(e, RES.evaluationConcernsElement) == asset
                    and self.graph.value(self.graph.value(e, RES.evaluatesCriterion), RAIL.assessesSILRisk) is not None
                )
                step = self.graph.value(self.graph.value(evaluation, RES.hasDerivationRecord), RES.hasStep)
                self.assertEqual(RULE.EvaluateSILRisk, self.graph.value(step, RES.executedByMechanism))
                used = list(self.graph.objects(step, RES.usedEntity))
                self.assertTrue(used, "the derivation step must cite the fail-safe evaluation it consumed")

    def test_completeness_status_matches_the_outcome(self) -> None:
        for asset, outcome in self.outcomes.items():
            with self.subTest(asset=str(asset).split("/")[-1]):
                evaluation = next(
                    e for e in self.graph.subjects(RDF.type, RES.CriterionEvaluation)
                    if self.graph.value(e, RES.evaluationConcernsElement) == asset
                    and self.graph.value(self.graph.value(e, RES.evaluatesCriterion), RAIL.assessesSILRisk) is not None
                )
                record = self.graph.value(evaluation, RES.hasDerivationRecord)
                expected = "incomplete" if outcome == RES.undetermined else "complete"
                self.assertEqual(expected, str(self.graph.value(record, RES.completenessStatus)))

    def test_criterion_does_not_claim_normative_legacy_authority(self) -> None:
        criterion = RSSCR["sil-maximum-risk-criterion"]
        self.assertIsNone(self.graph.value(criterion, Namespace("https://w3id.org/railsec-scope/criteria#").derivedFromSource))
        basis = self.graph.value(criterion, Namespace("https://w3id.org/railsec-scope/criteria#").restsOnJudgement)
        self.assertIsNotNone(basis, "a criterion without a source must rest on a recorded judgement")

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
