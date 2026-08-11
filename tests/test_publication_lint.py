from __future__ import annotations

import unittest

from rdflib import Graph, Literal, Namespace, RDF

from scripts.publication_lint import CRIT, lint_graphs


class PublicationLintTest(unittest.TestCase):
    def test_negative_fixtures_fire_k19_k20_k22(self) -> None:
        core = Graph()
        case = Namespace("https://w3id.org/railsec-scope/case/bad/resource/")
        railway = Namespace("https://w3id.org/railsec-scope/railway#")
        core.add((case.asset, RDF.type, railway.RailwayAsset))
        criteria = Graph()
        criteria.add((railway.badCriterion, RDF.type, CRIT.Criterion))
        criteria.add((railway.badCriterion, CRIT.criterionStatement, Literal("word " * 251)))
        violations = "\n".join(lint_graphs({"core.ttl": core, "criteria.ttl": criteria}))
        for identifier in ("K-19", "K-20", "K-22"):
            with self.subTest(identifier=identifier): self.assertIn(identifier, violations)


if __name__ == "__main__":
    unittest.main()
