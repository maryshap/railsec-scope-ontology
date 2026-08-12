"""Vacuity guard for the structural constraint shapes.

`conforms == True` is only meaningful for a shape that has at least one focus
node in the data being validated. A shape with no focus nodes conforms
vacuously and proves nothing.

Measured on the current data, 4 of 21 node shapes have focus nodes; the other
17 conform because the capability whose output they constrain does not yet
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

import unittest
from pathlib import Path

from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
SH = Namespace("http://www.w3.org/ns/shacl#")

EXERCISED: dict[str, int] = {
    "K01ElementBoundaryShape": 328,
    "K01BoundaryAssertionShape": 328,
    "K02OutOfScopeRationaleShape": 328,
    "K03InformationFlowShape": 148,
}

UNEXERCISED: dict[str, str] = {
    "K04AccessPreconditionShape": "access preconditions not populated",
    "K05CriterionProvenanceShape": "criteria not yet carried in the case data",
    "K06SourceLocationShape": "source locations not transferred to annotations",
    "K07VersionedArtefactShape": "artefact versions present only in fixtures",
    "K08MaterialDesignationShape": "material findings designated only in the category slice",
    "K09DerivationStepShape": "derivation steps produced only in the category slice",
    "K10IncompleteRecordShape": "derivation records produced only in the category slice",
    "K12AuthorisationNotGeneratedShape": "authorisation assertions not populated",
    "K13AssessorDecisionShape": "assessor decisions not implemented",
    "K14DecisionNotEvidenceShape": "assessor decisions not implemented",
    "K15OrderingResultShape": "ordering not implemented",
    "K16OrderingPositionShape": "ordering not implemented",
    "K16PathPositionShape": "L3 dependency chains not implemented",
    "K17CoverageMeasureShape": "coverage measures not declared",
    "K18CoverageResultShape": "coverage results not produced",
    "K18SelectionShape": "selections not represented",
    "K21DeprecationShape": "nothing deprecated at this version",
}

EVALUATED_GRAPHS = [
    Path("cases") / "etcs" / "abox.ttl",
    Path("cases") / "etcs" / "classification-provenance.ttl",
    Path("fixtures") / "architecture" / "positive.ttl",
]


def shape_focus_counts() -> dict[str, int]:
    shapes = Graph().parse(PROJECT / "shapes" / "constraints.ttl")
    data = Graph()
    for relative in EVALUATED_GRAPHS:
        data.parse(PROJECT / relative)
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
