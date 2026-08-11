from __future__ import annotations

import unittest
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
RSS_CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")


def load_case(name: str) -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "imports" / "prov-o-dl.ttl")
    graph.parse(PROJECT / "fixtures" / "criterion-slice" / f"{name}.ttl")
    return graph


def apply_candidate_rule(graph: Graph) -> int:
    query = (PROJECT / "rules" / "classify-candidate.rq").read_text(encoding="utf-8")
    inferred = graph.query(query).graph
    before = len(graph)
    graph += inferred
    return len(graph) - before


def validate_slice(graph: Graph) -> tuple[bool, str]:
    shapes = Graph().parse(PROJECT / "shapes" / "criterion-slice.ttl")
    conforms, _, report = validate(
        data_graph=graph,
        shacl_graph=shapes,
        inference="rdfs",
        advanced=True,
    )
    return bool(conforms), report


class CriterionVerticalSliceTest(unittest.TestCase):
    def test_positive_slice_entails_validates_and_answers_cq09(self) -> None:
        graph = load_case("positive")
        self.assertEqual(1, apply_candidate_rule(graph))
        element = Namespace(
            "https://w3id.org/railsec-scope/fixture/criterion-positive/"
        ).element
        self.assertIn((element, RDF.type, RSS_CRIT.CandidateExaminationTarget), graph)

        conforms, report = validate_slice(graph)
        self.assertTrue(conforms, report)
        self.assertEqual(
            0,
            len(list(graph.query((PROJECT / "queries" / "K-23-assignment-agreement.rq").read_text(encoding="utf-8")))),
        )
        answers = list(
            graph.query((PROJECT / "queries" / "cq" / "CQ-09.rq").read_text(encoding="utf-8"))
        )
        self.assertEqual(1, len(answers))
        self.assertEqual(element, answers[0].element)

    def test_negative_slice_fires_k11_k23_and_k24(self) -> None:
        graph = load_case("negative")
        self.assertEqual(0, apply_candidate_rule(graph))
        conforms, report = validate_slice(graph)
        self.assertFalse(conforms)
        self.assertIn("K-11", report)
        self.assertIn("K-24", report)
        mismatches = list(
            graph.query((PROJECT / "queries" / "K-23-assignment-agreement.rq").read_text(encoding="utf-8"))
        )
        self.assertEqual(1, len(mismatches))


if __name__ == "__main__":
    unittest.main()
