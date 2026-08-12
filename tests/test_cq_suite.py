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

import unittest
from pathlib import Path

from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery


PROJECT = Path(__file__).resolve().parents[1]

ANSWERED: dict[str, int] = {
    "CQ-01": 328,
    "CQ-03": 141,
    "CQ-04": 33,
    "CQ-22": 1,
    "CQ-28": 1,
    "CQ-31": 1,
    "CQ-36": 1391,  # +17: nine classification assumptions, four identity assumptions, two bases, one agent, one instance-set reference
    "CQ-41": 92,
    "CQ-43": 35,
}

EMPTY_BY_DESIGN: dict[str, str] = {
    "CQ-19": "ORF-25: no authorisation status may be produced by a definition, rule or computation",
    "CQ-27": "ORF-34: no material finding may have an incomplete derivation record in a valid release",
    "CQ-32": "ORF-39: no instance may violate a declared structural constraint",
    "CQ-39": "ORF-47: no term or criterion is deprecated at this version",
}

PENDING: dict[str, str] = {
    "CQ-02": "boundary exclusion rationale not populated",
    "CQ-05": "L3 reachability not implemented (ReachabilityResult)",
    "CQ-06": "L3 reachability not implemented",
    "CQ-07": "L3 reachability not implemented",
    "CQ-08": "L3 reachability and RunComparison not implemented",
    "CQ-09": "candidate criterion not implemented beyond the vertical slice",
    "CQ-10": "candidate criterion not implemented beyond the vertical slice",
    "CQ-11": "safety impact rules not implemented (SafetyImpactResult)",
    "CQ-12": "L3 dependency chains not implemented (DependencyChain)",
    "CQ-13": "candidate and reachability criteria not implemented",
    "CQ-14": "assessor decisions not populated (Override)",
    "CQ-15": "ordering not implemented (OrderingResult)",
    "CQ-16": "ordering not implemented (FactorValue)",
    "CQ-17": "ordering not implemented",
    "CQ-18": "examination constraints not populated",
    "CQ-20": "criterion provenance not transferred to annotations (SourceLocation)",
    "CQ-21": "interpretation records not created",
    "CQ-23": "criterion provenance not transferred to annotations",
    "CQ-24": "derivation records produced only inside the category slice",
    "CQ-25": "derivation records produced only inside the category slice",
    "CQ-26": "unresolved inputs not recorded on derivation records",
    "CQ-29": "asserted absence not populated",
    "CQ-30": "unresolved inputs not recorded",
    "CQ-33": "coverage measures not declared (CoverageMeasure)",
    "CQ-34": "coverage results not produced (CoverageResult)",
    "CQ-35": "selections not represented (Selection)",
    "CQ-37": "subsystem extension not present",
    "CQ-38": "RunComparison not implemented",
    "CQ-40": "run version records not produced",
    "CQ-42": "flow characteristics not populated",
    "CQ-44": "property-loss consequences not populated",
    "CQ-45": "ordering not implemented",
}

ALL_CQ = [f"CQ-{n:02d}" for n in range(1, 46)]


def representative_graph() -> Graph:
    graph = Graph().parse(PROJECT / "cases" / "etcs" / "abox.ttl")
    graph.parse(PROJECT / "cases" / "etcs" / "classification-provenance.ttl")
    graph.parse(PROJECT / "fixtures" / "criterion-slice" / "positive.ttl")
    return graph


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
                rows = run(self.graph, name)
                self.assertEqual(expected, len(rows), f"{name} returned {len(rows)} rows, expected {expected}. If intended, update the count deliberately.")

    def test_questions_empty_by_design_return_nothing(self) -> None:
        for name, reason in sorted(EMPTY_BY_DESIGN.items()):
            with self.subTest(cq=name):
                rows = run(self.graph, name)
                self.assertEqual(0, len(rows), f"{name} must be empty: {reason}. Got {len(rows)} rows.")

    def test_pending_questions_are_still_pending(self) -> None:
        for name, reason in sorted(PENDING.items()):
            with self.subTest(cq=name):
                rows = run(self.graph, name)
                self.assertEqual(0, len(rows), f"{name} now returns {len(rows)} rows ({reason} appears resolved). Promote it to ANSWERED with an asserted row count.")


class CompetencyQuestionCoverageTest(unittest.TestCase):
    def test_registry_totals_are_consistent(self) -> None:
        print(f"\nCQ coverage: {len(ANSWERED)}/45 answered with a value oracle, {len(EMPTY_BY_DESIGN)}/45 empty by design, {len(PENDING)}/45 pending implementation")
        self.assertEqual(len(ALL_CQ), len(ANSWERED) + len(EMPTY_BY_DESIGN) + len(PENDING))


if __name__ == "__main__":
    unittest.main()
