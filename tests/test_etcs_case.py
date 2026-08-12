from __future__ import annotations

import unittest
from pathlib import Path

from pyshacl import validate
from rdflib import Graph


PROJECT = Path(__file__).resolve().parents[1]


class EtcsCaseMigrationTest(unittest.TestCase):
    def test_case_is_structurally_valid_and_contains_no_legacy_iris(self) -> None:
        data = Graph().parse(PROJECT / "cases" / "etcs" / "abox.ttl")
        data.parse(PROJECT / "cases" / "etcs" / "classification-provenance.ttl")
        self.assertGreater(len(data), 4000)
        self.assertFalse(any("purl.org/ics-sec" in str(term) for triple in data for term in triple))
        shapes = Graph().parse(PROJECT / "shapes" / "constraints.ttl")
        conforms, _, report = validate(data_graph=data, shacl_graph=shapes, inference="none", advanced=True)
        self.assertTrue(conforms, report)


if __name__ == "__main__": unittest.main()
