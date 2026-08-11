from __future__ import annotations

import unittest
from pathlib import Path

from pyshacl import validate
from rdflib import Graph


PROJECT = Path(__file__).resolve().parents[1]


class AllocatedConstraintShapesTest(unittest.TestCase):
    def test_minimal_architecture_profile_conforms(self) -> None:
        data = Graph().parse(PROJECT / "fixtures" / "architecture" / "positive.ttl")
        shapes = Graph().parse(PROJECT / "shapes" / "constraints.ttl")
        conforms, _, report = validate(data_graph=data, shacl_graph=shapes, inference="none", advanced=True)
        self.assertTrue(conforms, report)

    def test_negative_fixture_proves_each_local_shape_fires(self) -> None:
        data = Graph()
        for path in sorted((PROJECT / "ontology").glob("*.ttl")):
            data.parse(path)
        data.parse(PROJECT / "fixtures" / "k-constraints" / "negative-all.ttl")
        shapes = Graph().parse(PROJECT / "shapes" / "constraints.ttl")
        # Structural constraints validate the asserted stage graph before OWL
        # domain/range inference can silently type a malformed position owner.
        conforms, _, report = validate(data_graph=data, shacl_graph=shapes, inference="none", advanced=True)
        self.assertFalse(conforms)
        for number in list(range(1, 11)) + list(range(12, 19)) + [21]:
            identifier = f"K-{number:02d}"
            with self.subTest(identifier=identifier):
                self.assertIn(identifier, report)


if __name__ == "__main__":
    unittest.main()
