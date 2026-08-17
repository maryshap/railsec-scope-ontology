"""Vacuity guard for the structural constraint shapes.

`conforms == True` is only meaningful for a shape that has at least one focus
node in the data being validated. A shape with no focus nodes conforms
vacuously and proves nothing.

Measured on the current data, 12 of 21 node shapes have focus nodes; the other
9 conform because the capability whose output they constrain does not yet
produce data. This test records that state explicitly so that a green SHACL run
cannot be read as evidence for shapes that were never reached.

EXERCISED    shape -> minimum number of focus nodes expected across the
             evaluated graphs; asserted, so losing coverage fails the test.
UNEXERCISED  shape -> the capability that must exist before it has focus nodes.
             Asserted at zero as a ratchet: when the capability starts
             producing data, this test fails and the shape must be promoted
             with a positive-conformance assertion.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import l3  # noqa: E402
import orchestrator  # noqa: E402

SH = Namespace("http://www.w3.org/ns/shacl#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
FX_L3 = Namespace("https://w3id.org/railsec-scope/fixture/l3/")

EXERCISED: dict[str, int] = {
    "K01ElementBoundaryShape": 328,
    "K01BoundaryAssertionShape": 328,
    "K02OutOfScopeRationaleShape": 328,
    "K03InformationFlowShape": 148,
    "K04AccessPreconditionShape": 1,
    "K05CriterionProvenanceShape": 26,
    "K09DerivationStepShape": 6,
    "K10IncompleteRecordShape": 6,
    "K16PathPositionShape": 5,
    "K17CoverageMeasureShape": 1,
    "K18CoverageResultShape": 1,
    "K18SelectionShape": 1,
}

UNEXERCISED: dict[str, str] = {
    "K06SourceLocationShape": "source locations not transferred to annotations",
    "K07VersionedArtefactShape": "artefact versions present only in fixtures",
    "K08MaterialDesignationShape": "material findings designated only in the category slice",
    "K12AuthorisationNotGeneratedShape": "authorisation assertions not populated",
    "K13AssessorDecisionShape": "assessor decisions not implemented",
    "K14DecisionNotEvidenceShape": "assessor decisions not implemented",
    "K15OrderingResultShape": "ordering not implemented",
    "K16OrderingPositionShape": "ordering not implemented",
    "K21DeprecationShape": "nothing deprecated at this version",
}

EVALUATED_GRAPHS = [
    Path("cases") / "etcs" / "abox.ttl",
    Path("cases") / "etcs" / "classification-provenance.ttl",
    Path("fixtures") / "architecture" / "positive.ttl",
]


def l3_evidence_graph() -> Graph:
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
    graph.add((FX_L3.selection, CRIT.hasVersion, FX_L3.version))
    graph.add((FX_L3.selection, RES.selectionBasedOnCandidateSet, candidate_set))
    graph.add((FX_L3.selection, RES.includesElement, FX_L3.target))
    l3.apply(graph, FX_L3.run)
    return graph


def shape_focus_counts() -> dict[str, int]:
    shapes = Graph().parse(PROJECT / "shapes" / "constraints.ttl")
    data = Graph()
    for relative in EVALUATED_GRAPHS:
        data.parse(PROJECT / relative)
    data += l3_evidence_graph()
    counts: dict[str, int] = {}
    for shape in shapes.subjects(RDF.type, SH.NodeShape):
        name = str(shape).split("#")[-1].split("/")[-1]
        total = 0
        for target in shapes.objects(shape, SH.targetClass):
            total += len(set(data.subjects(RDF.type, target)))
        for predicate in shapes.objects(shape, SH.targetSubjectsOf):
            total += len(set(data.subjects(predicate, None)))
        for predicate in shapes.objects(shape, SH.targetObjectsOf):
            total += len(set(data.objects(None, predicate)))
        counts[name] = total
    return counts


class ShapeCoverageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.counts = shape_focus_counts()

    def test_every_shape_is_classified_exactly_once(self) -> None:
        classified = list(EXERCISED) + list(UNEXERCISED)
        self.assertEqual(len(classified), len(set(classified)), "no shape may appear in two classes")
        self.assertEqual(
            sorted(self.counts),
            sorted(classified),
            "every node shape in shapes/constraints.ttl must be classified as EXERCISED or UNEXERCISED",
        )

    def test_exercised_shapes_keep_their_focus_nodes(self) -> None:
        for name, minimum in sorted(EXERCISED.items()):
            with self.subTest(shape=name):
                actual = self.counts[name]
                self.assertGreaterEqual(
                    actual,
                    minimum,
                    f"{name} now has {actual} focus nodes, expected at least {minimum}. "
                    "Constraint coverage has been lost.",
                )

    def test_unexercised_shapes_are_still_unexercised(self) -> None:
        for name, reason in sorted(UNEXERCISED.items()):
            with self.subTest(shape=name):
                actual = self.counts[name]
                self.assertEqual(
                    0,
                    actual,
                    f"{name} now has {actual} focus nodes ({reason} appears resolved). "
                    "Promote it to EXERCISED and assert positive conformance for it.",
                )

    def test_report_coverage(self) -> None:
        print(
            f"\nShape coverage: {len(EXERCISED)}/{len(self.counts)} node shapes exercised by data, "
            f"{len(UNEXERCISED)}/{len(self.counts)} vacuous pending implementation"
        )
        self.assertEqual(len(self.counts), len(EXERCISED) + len(UNEXERCISED))


if __name__ == "__main__":
    unittest.main()
