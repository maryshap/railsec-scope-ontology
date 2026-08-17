"""Phase 2 Step 13 L3 reachability and path evidence."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import l3  # noqa: E402
import orchestrator  # noqa: E402


FX = Namespace("https://w3id.org/railsec-scope/fixture/l3/")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RES = Namespace("https://w3id.org/railsec-scope/results#")


def fixture_graph() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "rules" / "rules.ttl")
    graph.parse(PROJECT / "fixtures" / "l3" / "minimal.ttl")
    return graph


class L3ReachabilityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = fixture_graph()
        query = (PROJECT / "rules" / "classify-candidate.rq").read_text(encoding="utf-8")
        self.graph += self.graph.query(query).graph
        orchestrator.materialise_assignments(self.graph, FX.run)
        orchestrator.materialise_candidate_set(self.graph, FX.run)

    def test_materialiser_records_but_does_not_decide_membership(self) -> None:
        self.assertIn((FX.entry, RDF.type, CRIT.EntryPoint), self.graph)
        self.assertIn((FX.target, RDF.type, CRIT.CandidateExaminationTarget), self.graph)
        assignments = {
            self.graph.value(item, RES.assignsCategory)
            for item in self.graph.subjects(RDF.type, RES.CategoryAssignment)
            if self.graph.value(item, RES.producedByRun) == FX.run
        }
        self.assertEqual({CRIT.EntryPoint, CRIT.CandidateExaminationTarget}, assignments)

    def test_reachability_uses_only_vulnerable_edges(self) -> None:
        added = l3.apply(self.graph, FX.run)
        self.assertGreater(added, 0)
        reached = {
            self.graph.value(result, RES.reachabilityConcerns)
            for result in self.graph.subjects(RDF.type, RES.ReachabilityResult)
        }
        self.assertEqual({FX.middle, FX.target}, reached)
        self.assertNotIn(FX["not-reached"], reached)

    def test_paths_are_positioned_and_access_evidence_is_propagated(self) -> None:
        l3.apply(self.graph, FX.run)
        target_result = next(
            result for result in self.graph.subjects(RDF.type, RES.ReachabilityResult)
            if self.graph.value(result, RES.reachabilityConcerns) == FX.target
        )
        self.assertIn((target_result, RES.usedAccessMechanism, FX["remote-access"]), self.graph)
        self.assertIn((target_result, RES.reliedOnPrecondition, FX["network-access"]), self.graph)

        chains = []
        for chain in self.graph.subjects(RDF.type, RES.DependencyChain):
            entries = sorted(
                (
                    int(self.graph.value(entry, RES.pathPosition)),
                    self.graph.value(entry, RES.chainNode),
                )
                for entry in self.graph.objects(chain, RES.hasChainEntry)
            )
            if entries[-1][1] == FX.target:
                chains.append(entries)
        self.assertEqual([[(1, FX.entry), (2, FX.middle), (3, FX.target)]], chains)

    def test_l3_is_idempotent_and_never_classifies(self) -> None:
        l3.apply(self.graph, FX.run)
        self.assertEqual(0, l3.apply(self.graph, FX.run))
        for step in self.graph.subjects(RES.layerIdentifier, None):
            if str(self.graph.value(step, RES.layerIdentifier)) == "L3":
                for generated in self.graph.objects(step, RES.generatedResult):
                    self.assertNotIn((generated, RDF.type, RES.CategoryAssignment), self.graph)

    def test_candidate_set_and_explicit_selection_coverage(self) -> None:
        candidate_set = next(
            item for item in self.graph.subjects(RDF.type, RES.CandidateSet)
            if self.graph.value(item, RES.producedByRun) == FX.run
        )
        selection = FX.selection
        self.graph.add((selection, RDF.type, RES.Selection))
        self.graph.add((selection, CRIT.hasVersion, FX.version))
        self.graph.add((selection, RES.selectionBasedOnCandidateSet, candidate_set))
        self.graph.add((selection, RES.includesElement, FX.target))

        l3.apply_coverage(self.graph, FX.run)
        coverage = next(self.graph.subjects(RDF.type, RES.CoverageResult))
        self.assertEqual(RES.valuePresent, self.graph.value(coverage, RES.hasComputationOutcome))
        self.assertEqual(1.0, float(self.graph.value(coverage, RES.representedValue)))
        self.assertEqual(candidate_set, self.graph.value(coverage, RES.measuredCandidateSet))
        self.assertEqual(selection, self.graph.value(coverage, RES.measuredSelection))


if __name__ == "__main__":
    unittest.main()
