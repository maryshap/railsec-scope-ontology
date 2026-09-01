"""Phase 2 closure evidence for canonical Steps 15 and 16."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
PHASE2 = Namespace("https://w3id.org/railsec-scope/evidence/phase2/")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RES = Namespace("https://w3id.org/railsec-scope/results#")


class Phase2PerformanceTargetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = Graph().parse(PROJECT / "reports" / "phase2-performance.ttl")

    def test_step15_declares_one_predeclared_target(self) -> None:
        targets = list(self.graph.subjects(RDF.type, RES.PerformanceTarget))
        self.assertEqual([PHASE2["full-validation-target"]], targets)
        target = targets[0]
        self.assertEqual("full-validate-workflow", str(self.graph.value(target, RES.measuredStage)))
        self.assertEqual(900.0, float(self.graph.value(target, RES.thresholdSeconds)))
        self.assertIsNotNone(self.graph.value(target, RES.representativeFixtureIdentifier))
        self.assertIsNotNone(self.graph.value(target, CRIT.hasVersion))

    def test_historical_observation_is_not_retroactively_assessed(self) -> None:
        measurement = PHASE2["historical-ci-observation-before-target"]
        self.assertIn((measurement, RDF.type, RES.PerformanceMeasurement), self.graph)
        self.assertEqual([], list(self.graph.objects(measurement, RES.assessedAgainstTarget)))
        self.assertGreater(float(self.graph.value(measurement, RES.elapsedTimeSeconds)), 0.0)

    def test_execution_environment_is_recorded(self) -> None:
        environment = PHASE2["github-actions-windows-latest"]
        self.assertIn((environment, RDF.type, RES.ExecutionEnvironment), self.graph)
        self.assertIsNotNone(self.graph.value(environment, RES.operatingSystem))
        self.assertIsNotNone(self.graph.value(environment, RES.runtimeVersions))


class Phase2EvidenceIndexTest(unittest.TestCase):
    def test_step16_indexes_all_evidence_episodes(self) -> None:
        with (PROJECT / "reports" / "phase2-evidence-index.tsv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual([f"EV-B{number}" for number in range(1, 12)], [row["episode"] for row in rows])
        allowed = {"retained", "deferred", "carried-forward"}
        for row in rows:
            with self.subTest(episode=row["episode"]):
                self.assertIn(row["status"], allowed)
                self.assertTrue(row["artifact"])
                self.assertTrue(row["evidence"])
        retained = {row["episode"] for row in rows if row["status"] == "retained"}
        self.assertGreaterEqual(len(retained), 9)
        self.assertEqual("carried-forward", rows[-1]["status"])


if __name__ == "__main__":
    unittest.main()
