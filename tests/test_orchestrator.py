"""Step 13 — Run orchestrator.

Checks the contract a Run must satisfy, not merely that it executes:

- results are run-scoped, so two Runs over the same inputs do not collide
- the same inputs produce the same derivation, which is what conditional
  reproducibility means in practice
- non-convergence is a refusal, not a recorded number
- an absent reasoner is a refusal, not a silent omission
- a Run that consumes no instance set is refused before deriving anything
- no guarded category is conferred without a satisfied evaluation behind it
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

from rdflib import BNode, Graph, RDF, URIRef


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import orchestrator  # noqa: E402
from orchestrator import CRIT, RES, RUN  # noqa: E402


FIXTURES = [
    PROJECT / "fixtures" / name / "minimal.ttl"
    for name in ("railway-category", "railway-threat", "railway-critical",
                 "railway-fail-safe", "railway-sil", "railway-access")
]


def canonical(graph: Graph, run_iri: URIRef) -> set:
    """Named triples of a run with every trace of the run identity neutralised.

    Result IRIs embed a digest of the run IRI, so both the IRI and the digest
    have to be masked. Blank nodes are excluded: they carry no run-dependent
    information here, and their identifiers are assigned per parse, so
    comparing them would test the serialiser rather than the derivation.
    """
    marker = str(run_iri)
    digest = hashlib.md5(marker.encode("utf-8")).hexdigest()

    def mask(term) -> str:
        return str(term).replace(marker, "RUN").replace(digest, "DIGEST")

    return {
        (mask(s), str(p), mask(o))
        for s, p, o in graph
        if s != run_iri and isinstance(s, URIRef) and not isinstance(o, BNode)
    }


class OrchestratorContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = orchestrator.execute(FIXTURES, "test-run")

    def test_it_converges_within_the_bound(self) -> None:
        self.assertTrue(self.result.converged)
        self.assertLessEqual(self.result.iterations, orchestrator.MAX_ITERATIONS)

    def test_it_derives_evaluations_in_all_three_values(self) -> None:
        outcomes = {
            self.result.graph.value(evaluation, RES.hasEvaluationOutcome)
            for evaluation in self.result.graph.subjects(RDF.type, RES.CriterionEvaluation)
        }
        for expected in (RES.satisfied, RES.notSatisfied, RES.undetermined):
            with self.subTest(outcome=str(expected).split("#")[-1]):
                self.assertIn(expected, outcomes)

    def test_input_and_output_validation_both_conform(self) -> None:
        self.assertTrue(self.result.input_validation_conforms)
        self.assertTrue(self.result.output_validation_conforms)

    def test_the_run_records_its_iteration_count_and_digest(self) -> None:
        graph, run = self.result.graph, self.result.run_iri
        self.assertEqual(self.result.iterations, int(graph.value(run, RES.iterationCount)))
        self.assertIsNotNone(graph.value(run, RES.artefactDigest))
        self.assertIsNotNone(graph.value(run, RES.startTime))
        self.assertIsNotNone(graph.value(run, RES.endTime))
        self.assertTrue(list(graph.objects(run, RES.usedVersion)))

    def test_it_declares_the_instance_sets_it_consumed(self) -> None:
        used = list(self.result.graph.objects(self.result.run_iri, RES.usedInstanceSet))
        self.assertTrue(used, "a Run must declare its instance sets or stages join on nothing")

    def test_no_guarded_category_is_conferred_without_an_evaluation(self) -> None:
        self.assertEqual([], orchestrator.guarded_category_violations(self.result.graph))

    def test_an_absent_reasoner_is_a_refusal_not_a_silence(self) -> None:
        """The Run must not be publishable merely because the toolchain is missing."""
        if not self.result.reasoner_invoked:
            self.assertFalse(self.result.publishable)
            self.assertTrue(any("reasoner" in reason for reason in self.result.refusals))


class RunScopingTest(unittest.TestCase):
    """Results must be scoped to their Run, or ORF-45 and ORF-46 cannot hold."""

    def test_two_runs_do_not_share_result_identifiers(self) -> None:
        """Results of two different Runs must not collide.

        Only results belonging to the orchestrator's own Run are compared. The
        fixtures declare a Run of their own, and its results are identical in
        both executions by design: that is the same Run computed twice, not a
        collision between different ones.
        """
        first = orchestrator.execute(FIXTURES, "run-one")
        second = orchestrator.execute(FIXTURES, "run-two")

        def own_results(result) -> set:
            """Results the orchestrator Run produced, identified by attribution.

            Selecting by attribution rather than by the digest in the IRI is
            deliberate: filtering on the digest would silently exclude any
            result that lost its run scoping, which is exactly the defect this
            test exists to catch.
            """
            return {
                evaluation
                for evaluation in result.graph.subjects(RDF.type, RES.CriterionEvaluation)
                if result.run_iri in set(result.graph.objects(evaluation, RES.producedByRun))
            }

        first_ids, second_ids = own_results(first), own_results(second)
        self.assertTrue(first_ids, "the orchestrator Run produced no results of its own")
        self.assertEqual(set(), first_ids & second_ids, "run-scoped results must not collide")

    def test_every_evaluation_carries_exactly_one_outcome(self) -> None:
        result = orchestrator.execute(FIXTURES, "run-outcomes")
        for evaluation in result.graph.subjects(RDF.type, RES.CriterionEvaluation):
            with self.subTest(evaluation=str(evaluation).split("/")[-1]):
                outcomes = list(result.graph.objects(evaluation, RES.hasEvaluationOutcome))
                self.assertEqual(1, len(outcomes))


class DeterminismTest(unittest.TestCase):
    def test_the_same_inputs_produce_the_same_derivation(self) -> None:
        first = orchestrator.execute(FIXTURES, "determinism-a")
        second = orchestrator.execute(FIXTURES, "determinism-b")
        self.assertEqual(first.iterations, second.iterations)
        self.assertEqual(
            canonical(first.graph, first.run_iri),
            canonical(second.graph, second.run_iri),
            "two Runs over identical inputs must derive identical graphs",
        )


class RefusalTest(unittest.TestCase):
    def test_a_run_without_an_instance_set_is_refused_before_deriving(self) -> None:
        result = orchestrator.execute([PROJECT / "fixtures" / "orchestrator" / "no-instance-set.ttl"], "no-set")
        self.assertFalse(result.publishable)
        self.assertTrue(any("instance set" in reason for reason in result.refusals))
        self.assertEqual(0, len(list(result.graph.subjects(RDF.type, RES.CriterionEvaluation))))
        self.assertIsNotNone(result.graph.value(result.run_iri, RES.artefactDigest))
        self.assertIsNotNone(result.graph.value(result.run_iri, RES.endTime))

    def test_non_convergence_is_refused_rather_than_reported(self) -> None:
        original = orchestrator.MAX_ITERATIONS
        try:
            orchestrator.MAX_ITERATIONS = 1
            result = orchestrator.execute(FIXTURES, "bounded")
            self.assertFalse(result.converged)
            self.assertFalse(result.publishable)
            self.assertTrue(any("fixed point" in reason for reason in result.refusals))
        finally:
            orchestrator.MAX_ITERATIONS = original

    def test_input_validation_failure_stops_before_derivation(self) -> None:
        bad = PROJECT / "fixtures" / "k-constraints"
        candidates = sorted(bad.glob("*negative*.ttl")) if bad.exists() else []
        if not candidates:
            self.skipTest("no negative fixture available")
        result = orchestrator.execute([candidates[0]], "bad-input")
        self.assertFalse(result.publishable)


if __name__ == "__main__":
    unittest.main()
