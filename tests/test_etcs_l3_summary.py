"""Contract test for the reproducible ETCS L3 application summary."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, XSD


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from summarise_etcs_l3_application import summarise  # noqa: E402


FX = Namespace("https://w3id.org/railsec-scope/fixture/etcs-l3-summary/")
ATTACK = Namespace("https://w3id.org/railsec-scope/attack#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")


class EtcsL3SummaryTest(unittest.TestCase):
    def test_summary_recomputes_generic_flow_applicability_without_mutating_source(self) -> None:
        graph = Graph()
        graph.add((FX.run, RDF.type, RES.Run))
        graph.add((FX.run, RES.publishable, Literal(True, datatype=XSD.boolean)))
        graph.add((FX.flow, RDF.type, RAIL.RailwayInformationFlow))
        graph.add((FX.criterion, RDF.type, CRIT.Criterion))
        graph.add((FX.criterion, CRIT.evaluationStageIdentifier, Literal("attack-technique-applicability")))
        graph.add((
            FX.criterion,
            CRIT.stageCandidateTypeIri,
            Literal(str(RAIL.RailwayInformationFlow), datatype=XSD.anyURI),
        ))
        graph.add((FX.criterion, ATTACK.assessesAttackTechnique, FX.technique))
        graph.add((FX.criterion, ATTACK.requiresSatisfiedEvaluationOf, FX.prerequisite))
        graph.add((FX.prerequisite_evaluation, RDF.type, RES.CriterionEvaluation))
        graph.add((FX.prerequisite_evaluation, RES.evaluationConcernsElement, FX.flow))
        graph.add((FX.prerequisite_evaluation, RES.evaluatesCriterion, FX.prerequisite))
        graph.add((FX.prerequisite_evaluation, RES.hasEvaluationOutcome, RES.satisfied))
        graph.add((FX.prerequisite_evaluation, RES.producedByRun, FX.run))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.ttl"
            graph.serialize(destination=path, format="turtle")
            report = summarise(path, recompute=True)
            unchanged = Graph().parse(path)

        self.assertEqual(1, report["applicability"]["total"])
        self.assertEqual(1, report["applicability"]["satisfied"])
        self.assertEqual(1, report["applicability"]["flows"])
        self.assertEqual(0, report["attackPaths"])
        self.assertEqual(len(graph), len(unchanged))


if __name__ == "__main__":
    unittest.main()
