from __future__ import annotations

import unittest
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace


PROJECT = Path(__file__).resolve().parents[1]
FX = Namespace("https://w3id.org/railsec-scope/fixture/governance/")
GOV = Namespace("https://w3id.org/railsec-scope/governance#")


def load_fixture() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "imports" / "prov-o-dl.ttl")
    graph.parse(PROJECT / "fixtures" / "governance" / "minimal.ttl")
    return graph


def validate_governance(graph: Graph) -> tuple[bool, str]:
    shapes = Graph().parse(PROJECT / "shapes" / "governance.ttl")
    conforms, _, report = validate(
        data_graph=graph,
        shacl_graph=shapes,
        inference="rdfs",
        advanced=True,
    )
    return bool(conforms), report


class GovernanceExtensionTest(unittest.TestCase):
    def test_minimal_governance_context_conforms(self) -> None:
        conforms, report = validate_governance(load_fixture())
        self.assertTrue(conforms, report)

    def test_authorisation_needs_an_explicit_issuer_and_basis(self) -> None:
        graph = load_fixture()
        graph.remove((FX.authorisation, GOV.authorisationIssuedBy, None))
        graph.remove((FX.authorisation, GOV.authorisationSupportedBy, FX["operational-control"]))
        conforms, report = validate_governance(graph)
        self.assertFalse(conforms)
        self.assertIn("GOV-02", report)

    def test_authorisation_basis_must_concern_the_authorised_asset(self) -> None:
        graph = load_fixture()
        graph.remove((FX.authorisation, GOV.authorisationSupportedBy, FX["operational-control"]))
        graph.add((FX.authorisation, GOV.authorisationSupportedBy, FX["maintenance-responsibility"]))
        graph.remove((FX["maintenance-responsibility"], GOV.responsibilityAssignmentSubject, FX.asset))
        graph.add((FX["maintenance-responsibility"], GOV.responsibilityAssignmentSubject, FX["other-asset"]))
        conforms, report = validate_governance(graph)
        self.assertFalse(conforms)
        self.assertIn("GOV-02", report)

    def test_operational_constraint_needs_context_and_evidence(self) -> None:
        graph = load_fixture()
        graph.remove((FX["maintenance-window"], GOV.constraintAppliesToAssessment, None))
        graph.remove((FX["maintenance-window"], GOV.constraintEvidence, None))
        conforms, report = validate_governance(graph)
        self.assertFalse(conforms)
        self.assertIn("GOV-03", report)

    def test_module_is_registered_for_owl_validation(self) -> None:
        catalog = (PROJECT / "catalog-v001.xml").read_text(encoding="utf-8")
        validation = (PROJECT / "ontology" / "validation.ttl").read_text(encoding="utf-8")
        self.assertIn("railsec-scope/governance", catalog)
        self.assertIn("railsec-scope/governance", validation)


if __name__ == "__main__":
    unittest.main()
