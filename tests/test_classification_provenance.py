"""K-25 — provenance of the safety-critical classification.

The classification of an asset as safety-critical carries assessment meaning and
drives every stage from 12.3 onward. It must therefore be reified as an
assumption with a judgement basis and an attributed agent, never left as a bare
rdf:type.

It is an Assumption and not an AssertedFact by design. The source workbook shows
that the value was transferred; it does not establish that the asset is
safety-critical. That determination belongs to a safety case, which is not
available. Data-transfer provenance and the justification for provisionally
accepting the transferred value are kept as separate records.

The shape is general to M6, so the synthetic fixtures must satisfy it too.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, URIRef, XSD


PROJECT = Path(__file__).resolve().parents[1]
CASE = Namespace("https://w3id.org/railsec-scope/case/etcs/resource/")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
PROV = Namespace("http://www.w3.org/ns/prov#")

RDF_TYPE_IRI = Literal("http://www.w3.org/1999/02/22-rdf-syntax-ns#type", datatype=XSD.anyURI)

EXPECTED_ASSETS = [
    "asset-ct-01", "asset-ct-02", "asset-ob-01", "asset-ob-06", "asset-ob-07",
    "asset-ob-24", "asset-ob-25", "asset-ob-26", "asset-ob-29",
]


def base_graph() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "imports" / "prov-o-dl.ttl")
    return graph


def etcs_graph() -> Graph:
    graph = base_graph()
    graph.parse(PROJECT / "cases" / "etcs" / "abox.ttl")
    graph.parse(PROJECT / "cases" / "etcs" / "classification-provenance.ttl")
    return graph


def shapes() -> Graph:
    return Graph().parse(PROJECT / "shapes" / "railway.ttl")


def conforms(graph: Graph) -> bool:
    result, _, _ = validate(data_graph=graph, shacl_graph=shapes(), inference="none", advanced=True)
    return result


def add_asset_with_assertion(graph: Graph, local: str, **omit) -> URIRef:
    """Add a safety-critical asset and its classification assertion, minus any omitted part."""
    asset = CASE[local]
    assertion = CASE[f"{local}-assertion"]
    graph.add((asset, RDF.type, RAIL.SafetyCriticalAsset))
    graph.add((assertion, RDF.type, omit.get("assertion_type", CORE.Assumption)))
    graph.add((assertion, CORE.assertionSubject, asset))
    graph.add((assertion, CORE.assertionPredicateIri, omit.get("predicate", RDF_TYPE_IRI)))
    graph.add((assertion, CORE.assertionObjectResource, omit.get("object", RAIL.SafetyCriticalAsset)))
    graph.add((assertion, CORE.hasEpistemicStatus, omit.get("status", CORE.assumptionStatus)))
    graph.add((assertion, RES.assertedInInstanceSet, CASE["instance-set"]))
    if not omit.get("drop_basis"):
        graph.add((assertion, PROV.wasDerivedFrom, CASE["safety-critical-classification-basis"]))
    if not omit.get("drop_agent"):
        graph.add((assertion, PROV.wasAttributedTo, CASE["assessor"]))
    return asset


class ClassificationProvenancePositiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = etcs_graph()

    def test_all_nine_etcs_assets_are_covered(self) -> None:
        assets = {str(a).split("/")[-1] for a in self.graph.subjects(RDF.type, RAIL.SafetyCriticalAsset)}
        self.assertEqual(set(EXPECTED_ASSETS), assets)

    def test_each_asset_has_exactly_one_classification_assumption(self) -> None:
        for local in EXPECTED_ASSETS:
            with self.subTest(asset=local):
                matches = [
                    a for a in self.graph.subjects(CORE.assertionSubject, CASE[local])
                    if (a, CORE.assertionObjectResource, RAIL.SafetyCriticalAsset) in self.graph
                ]
                self.assertEqual(1, len(matches))
                assertion = matches[0]
                self.assertIn((assertion, RDF.type, CORE.Assumption), self.graph)
                self.assertEqual(CORE.assumptionStatus, self.graph.value(assertion, CORE.hasEpistemicStatus))
                self.assertIsNotNone(self.graph.value(assertion, PROV.wasDerivedFrom))
                self.assertIsNotNone(self.graph.value(assertion, PROV.wasAttributedTo))

    def test_no_classification_is_recorded_as_an_asserted_fact(self) -> None:
        for assertion in self.graph.subjects(CORE.assertionObjectResource, RAIL.SafetyCriticalAsset):
            with self.subTest(assertion=str(assertion).split("/")[-1]):
                self.assertNotIn((assertion, RDF.type, CORE.AssertedFact), self.graph)
                self.assertNotEqual(CORE.assertedFactStatus, self.graph.value(assertion, CORE.hasEpistemicStatus))

    def test_classification_basis_does_not_cite_a_source_location(self) -> None:
        """The workbook evidences transfer, not the determination; nothing may claim otherwise."""
        basis = CASE["safety-critical-classification-basis"]
        self.assertIn((basis, RDF.type, CRIT.JudgementBasis), self.graph)
        self.assertIsNotNone(self.graph.value(basis, CRIT.reasoning))
        self.assertIsNotNone(self.graph.value(basis, CRIT.revisionConditions))
        self.assertIsNone(self.graph.value(basis, CRIT.derivedFromSource))

    def test_identity_basis_is_kept_separate_from_the_classification_basis(self) -> None:
        identity = CASE["asset-identity-basis"]
        classification = CASE["safety-critical-classification-basis"]
        self.assertNotEqual(identity, classification)
        for assertion in self.graph.subjects(CORE.assertionObjectResource, RAIL.SafetyCriticalAsset):
            with self.subTest(assertion=str(assertion).split("/")[-1]):
                self.assertNotEqual(identity, self.graph.value(assertion, PROV.wasDerivedFrom))

    def test_etcs_case_conforms(self) -> None:
        self.assertTrue(conforms(self.graph))

    def test_fixtures_conform(self) -> None:
        graph = base_graph()
        for name in ("railway-category", "railway-fail-safe", "railway-sil", "railway-access"):
            graph.parse(PROJECT / "fixtures" / name / "minimal.ttl")
        self.assertTrue(conforms(graph))


class ClassificationProvenanceNegativeTest(unittest.TestCase):
    """Each mutation must be rejected by K-25."""

    def setUp(self) -> None:
        self.graph = etcs_graph()

    def test_asset_without_any_assertion_is_rejected(self) -> None:
        self.graph.add((CASE["asset-tenth"], RDF.type, RAIL.SafetyCriticalAsset))
        self.assertFalse(conforms(self.graph))

    def test_assertion_without_judgement_basis_is_rejected(self) -> None:
        add_asset_with_assertion(self.graph, "asset-no-basis", drop_basis=True)
        self.assertFalse(conforms(self.graph))

    def test_assertion_without_attribution_is_rejected(self) -> None:
        add_asset_with_assertion(self.graph, "asset-no-agent", drop_agent=True)
        self.assertFalse(conforms(self.graph))

    def test_assertion_recorded_as_asserted_fact_is_rejected(self) -> None:
        add_asset_with_assertion(
            self.graph, "asset-as-fact",
            assertion_type=CORE.AssertedFact, status=CORE.assertedFactStatus,
        )
        self.assertFalse(conforms(self.graph))

    def test_assertion_with_the_wrong_predicate_is_rejected(self) -> None:
        add_asset_with_assertion(
            self.graph, "asset-wrong-predicate",
            predicate=Literal("http://www.w3.org/2000/01/rdf-schema#label", datatype=XSD.anyURI),
        )
        self.assertFalse(conforms(self.graph))

    def test_assertion_with_the_wrong_object_is_rejected(self) -> None:
        add_asset_with_assertion(self.graph, "asset-wrong-object", object=RAIL.SafetyRelatedAsset)
        self.assertFalse(conforms(self.graph))

    def test_assumption_carrying_asserted_fact_status_is_rejected(self) -> None:
        """Type and epistemic status must agree; a contradictory record is a defect.

        Kept separate from the AssertedFact case so that the status constraint is
        load-bearing on its own rather than shadowed by the class constraint.
        """
        add_asset_with_assertion(self.graph, "asset-contradictory-status", status=CORE.assertedFactStatus)
        self.assertFalse(conforms(self.graph))

    def test_a_correct_addition_is_accepted(self) -> None:
        """Guard against a shape that rejects everything."""
        add_asset_with_assertion(self.graph, "asset-correct")
        self.assertTrue(conforms(self.graph))


if __name__ == "__main__":
    unittest.main()
