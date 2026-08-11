from __future__ import annotations

import unittest
from pathlib import Path

from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery


PROJECT = Path(__file__).resolve().parents[1]


class CompetencyQuestionSuiteTest(unittest.TestCase):
    def test_all_45_queries_exist_and_parse(self) -> None:
        files = sorted((PROJECT / "queries" / "cq").glob("CQ-*.rq"))
        self.assertEqual([f"CQ-{number:02d}.rq" for number in range(1, 46)], [path.name for path in files])
        for path in files:
            with self.subTest(query=path.name): prepareQuery(path.read_text(encoding="utf-8"))

    def test_all_45_queries_execute_against_representative_fixtures(self) -> None:
        graph = Graph().parse(PROJECT / "cases" / "etcs" / "abox.ttl")
        graph.parse(PROJECT / "fixtures" / "criterion-slice" / "positive.ttl")
        for path in sorted((PROJECT / "queries" / "cq").glob("CQ-*.rq")):
            with self.subTest(query=path.name):
                result = graph.query(path.read_text(encoding="utf-8"))
                if result.type == "SELECT": list(result)


if __name__ == "__main__": unittest.main()
