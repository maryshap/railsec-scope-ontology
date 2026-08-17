"""Competency-question suite.

Every CQ is classified into exactly one expectation class, so the suite reports
what is established rather than that the files parse.

ANSWERED         the query returns a checked number of rows on the
                 representative fixture; the count is asserted, so a silent
                 change in the fixture or the rules fails the test.
EMPTY_BY_DESIGN  an empty result is the correct answer; a non-empty result is
                 a defect.
PENDING          the capability the query interrogates is not implemented, so
                 no data exists for it to return. Asserted empty as a ratchet:
                 as soon as the capability produces data the test fails,
                 forcing promotion to ANSWERED with a value oracle. PENDING is
                 a recorded gap, not a pass.
"""

from __future__ import annotations

import sys
import unittest
from functools import lru_cache
from pathlib import Path

from rdflib import Graph, Namespace, RDF
from rdflib.plugins.sparql import prepareQuery


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import l3  # noqa: E402
import orchestrator  # noqa: E402

FX_L3 = Namespace("https://w3id.org/railsec-scope/fixture/l3/")
RES = Namespace("https://w3id.org/railsec-scope/results#")

ANSWERED: dict[str, int] = {
    "CQ-01": 328,
    "CQ-03": 141,
    "CQ-04": 33,
    "CQ-05": 2,
    "CQ-06": 2,
    "CQ-07": 2,
    "CQ-09": 1,
    "CQ-10": 1,
    "CQ-12": 5,
    "CQ-13": 1,
    "CQ-15": 7,
    "CQ-16": 4,
    "CQ-22": 1,
    "CQ-24": 10,
    "CQ-25": 8,
    "CQ-28": 1,
    "CQ-31": 1,
    "CQ-33": 1,
    "CQ-34": 1,
    "CQ-36": 1391,  # +17: nine classification assumptions, four identity assumptions, two bases, one agent, one instance-set reference
    "CQ-40": 10,
    "CQ-41": 92,
    "CQ-43": 35,
    "CQ-45": 3,
}

EMPTY_BY_DESIGN: dict[str, str] = {
    "CQ-19": "ORF-25: no authorisation status may be produced by a definition, rule or computation",
    "CQ-27": "ORF-34: no material finding may have an incomplete derivation record in a valid release",
    "CQ-32": "ORF-39: no instance may violate a declared structural constraint",
    "CQ-35": "the explicit L3 fixture Selection matches its CandidateSet exactly",
    "CQ-39": "ORF-47: no term or criterion is deprecated at this version",
}

PENDING: dict[str, str] = {
    "CQ-02": "boundary exclusion rationale not populated",
    "CQ-08": "L3 reachability and RunComparison not implemented",
    "CQ-11": "safety impact rules not implemented (SafetyImpactResult)",
    "CQ-14": "assessor decisions not populated (Override)",
    "CQ-17": "cross-ordering comparison fixture not implemented",
    "CQ-18": "examination constraints not populated",
    "CQ-20": "criterion provenance not transferred to annotations (SourceLocation)",
    "CQ-21": "interpretation records not created",
    "CQ-23": "criterion provenance not transferred to annotations",
    "CQ-26": "unresolved inputs not recorded on derivation records",
    "CQ-29": "asserted absence not populated",
    "CQ-30": "unresolved inputs not recorded",
    "CQ-37": "subsystem extension not present",
    "CQ-38": "RunComparison not implemented",
    "CQ-42": "flow characteristics not populated",
    "CQ-44": "property-loss consequences not populated",
}

ALL_CQ = [f"CQ-{n:02d}" for n in range(1, 46)]


def representative_graph() -> Graph:
    graph = Graph().parse(PROJECT / "cases" / "etcs" / "abox.ttl")
    graph.parse(PROJECT / "cases" / "etcs" / "classification-provenance.ttl")
    graph.parse(PROJECT / "fixtures" / "criterion-slice" / "positive.ttl")
    return graph


@lru_cache(maxsize=1)
def l3_oracle_graph() -> Graph:
    """Purpose-built Step 13 graph; kept separate from ETCS row-count oracles."""
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "rules" / "rules.ttl")
    graph.parse(PROJECT / "fixtures" / "l3" / "minimal.ttl")

    classifier = (PROJECT / "rules" / "classify-candidate.rq").read_text(encoding="utf-8")
    graph += graph.query(classifier).graph
    orchestrator.materialise_assignments(graph, FX_L3.run)
    orchestrator.materialise_candidate_set(graph, FX_L3.run)

    candidate_set = next(
        item for item in graph.subjects(RDF.type, RES.CandidateSet)
        if graph.value(item, RES.producedByRun) == FX_L3.run
    )
    graph.add((FX_L3.selection, RDF.type, RES.Selection))
    graph.add((FX_L3.selection, Namespace("https://w3id.org/railsec-scope/criteria#").hasVersion, FX_L3.version))
    graph.add((FX_L3.selection, RES.selectionBasedOnCandidateSet, candidate_set))
    graph.add((FX_L3.selection, RES.includesElement, FX_L3.target))
    graph.add((FX_L3.selection, RES.includesElement, FX_L3["first-hop"]))
    graph.add((FX_L3.selection, RES.includesElement, FX_L3["second-hop"]))
    l3.apply(graph, FX_L3.run)
    return graph


L3_ORACLE_CQS = {
    "CQ-05", "CQ-06", "CQ-07", "CQ-09", "CQ-10", "CQ-12", "CQ-13",
    "CQ-15", "CQ-16", "CQ-24", "CQ-25", "CQ-33", "CQ-34", "CQ-35", "CQ-40", "CQ-45",
}


def graph_for(name: str, default: Graph) -> Graph:
    return l3_oracle_graph() if name in L3_ORACLE_CQS else default


def run(graph: Graph, name: str) -> list:
    return list(graph.query((PROJECT / "queries" / "cq" / f"{name}.rq").read_text(encoding="utf-8")))


class CompetencyQuestionRegistryTest(unittest.TestCase):
    def test_every_question_is_classified_exactly_once(self) -> None:
        classified = list(ANSWERED) + list(EMPTY_BY_DESIGN) + list(PENDING)
        self.assertEqual(len(classified), len(set(classified)), "no CQ may appear in two classes")
        self.assertEqual(ALL_CQ, sorted(classified), "every CQ must appear in exactly one expectation class")

    def test_every_classified_question_has_a_query_file(self) -> None:
        self.assertEqual(ALL_CQ, sorted(path.stem for path in (PROJECT / "queries" / "cq").glob("CQ-*.rq")))

    def test_all_queries_parse(self) -> None:
        for name in ALL_CQ:
            with self.subTest(cq=name):
                prepareQuery((PROJECT / "queries" / "cq" / f"{name}.rq").read_text(encoding="utf-8"))


class CompetencyQuestionAnswerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = representative_graph()

    def test_answered_questions_return_the_expected_number_of_rows(self) -> None:
        for name, expected in sorted(ANSWERED.items()):
            with self.subTest(cq=name):
                rows = run(graph_for(name, self.graph), name)
                self.assertEqual(expected, len(rows), f"{name} returned {len(rows)} rows, expected {expected}. If intended, update the count deliberately.")

    def test_questions_empty_by_design_return_nothing(self) -> None:
        for name, reason in sorted(EMPTY_BY_DESIGN.items()):
            with self.subTest(cq=name):
                rows = run(graph_for(name, self.graph), name)
                self.assertEqual(0, len(rows), f"{name} must be empty: {reason}. Got {len(rows)} rows.")

    def test_pending_questions_are_still_pending(self) -> None:
        for name, reason in sorted(PENDING.items()):
            with self.subTest(cq=name):
                rows = run(graph_for(name, self.graph), name)
                self.assertEqual(0, len(rows), f"{name} now returns {len(rows)} rows ({reason} appears resolved). Promote it to ANSWERED with an asserted row count.")


class CompetencyQuestionCoverageTest(unittest.TestCase):
    def test_registry_totals_are_consistent(self) -> None:
        print(f"\nCQ coverage: {len(ANSWERED)}/45 answered with a value oracle, {len(EMPTY_BY_DESIGN)}/45 empty by design, {len(PENDING)}/45 pending implementation")
        self.assertEqual(len(ALL_CQ), len(ANSWERED) + len(EMPTY_BY_DESIGN) + len(PENDING))


if __name__ == "__main__":
    unittest.main()
