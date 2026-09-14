from __future__ import annotations

import sys
import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, URIRef


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from summarize_case_run import evaluation_rows, markdown_summary, select_run  # noqa: E402


CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
EX = Namespace("https://example.test/")


class CaseRunSummaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = Graph()
        for run, identifier in ((EX.current, "current"), (EX.foreign, "foreign")):
            self.graph.add((run, RDF.type, RES.Run))
            self.graph.add((run, RES.runIdentifier, Literal(identifier)))
        self.graph.add((EX.criterion, CRIT.evaluationStageIdentifier, Literal("example-stage")))
        for evaluation, run, outcome in (
            (EX.current_evaluation, EX.current, RES.undetermined),
            (EX.foreign_evaluation, EX.foreign, RES.satisfied),
        ):
            self.graph.add((evaluation, RDF.type, RES.CriterionEvaluation))
            self.graph.add((evaluation, RES.producedByRun, run))
            self.graph.add((evaluation, RES.evaluatesCriterion, EX.criterion))
            self.graph.add((evaluation, RES.evaluationConcernsElement, EX.element))
            self.graph.add((evaluation, RES.hasEvaluationOutcome, outcome))

    def test_selects_exact_run_identifier(self) -> None:
        self.assertEqual(EX.current, select_run(self.graph, "current"))

    def test_rows_exclude_other_runs(self) -> None:
        rows = evaluation_rows(self.graph, EX.current)
        self.assertEqual(1, len(rows))
        self.assertEqual("undetermined", rows[0]["outcome"])

    def test_non_publishable_summary_carries_warning(self) -> None:
        self.graph.add((EX.current, RES.publishable, Literal(False)))
        summary = markdown_summary(self.graph, EX.current, evaluation_rows(self.graph, EX.current))
        self.assertIn("diagnostic evidence only", summary)
        self.assertIn("| example-stage | 0 | 0 | 1 | 0 | 1 | 0.0% |", summary)


if __name__ == "__main__":
    unittest.main()
