"""Guards against silent drift between the ontology, the reports and the docs.

Each check here replaces a claim that was previously stated as a number in prose
and could go stale without anyone noticing. A number in a document is only as
good as the test that fails when it stops being true.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from rdflib import Graph, OWL, RDF, RDFS


PROJECT = Path(__file__).resolve().parents[1]
BASE = "https://w3id.org/railsec-scope/"
M1_TO_M4 = ["core.ttl", "criteria.ttl", "results.ttl", "assessment.ttl"]

# Properties intentionally left without a domain, with the reason. Anything else
# missing a domain or range is a defect.
DOMAINLESS_BY_DESIGN: dict[str, str] = {
    "stableIdentifier": (
        "Metadata module property. Declaring a domain would name a class from a "
        "domain module, which the metadata module does not import; the reference "
        "would be to an undeclared class and would take the ontology out of "
        "OWL 2 DL. Module independence is preferred over the domain declaration."
    ),
}


def own(term) -> bool:
    return str(term).startswith(BASE)


def load(files) -> Graph:
    graph = Graph()
    for name in files:
        graph.parse(PROJECT / "ontology" / name)
    return graph


def all_modules() -> Graph:
    return load(sorted(p.name for p in (PROJECT / "ontology").glob("*.ttl")))


class PropertyInvariantTest(unittest.TestCase):
    """Replaces the prose claim that N object and M datatype properties have domains and ranges."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = all_modules()

    def test_every_own_property_has_a_domain(self) -> None:
        for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
            for prop in sorted(p for p in self.graph.subjects(RDF.type, kind) if own(p)):
                name = str(prop).split("#")[-1].split("/")[-1]
                if name in DOMAINLESS_BY_DESIGN:
                    continue
                with self.subTest(property=name):
                    self.assertTrue(list(self.graph.objects(prop, RDFS.domain)), f"{name} has no rdfs:domain")

    def test_every_own_property_has_a_range(self) -> None:
        for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
            for prop in sorted(p for p in self.graph.subjects(RDF.type, kind) if own(p)):
                name = str(prop).split("#")[-1].split("/")[-1]
                with self.subTest(property=name):
                    self.assertTrue(list(self.graph.objects(prop, RDFS.range)), f"{name} has no rdfs:range")


class EntityMatrixDriftTest(unittest.TestCase):
    """Every M1-M4 class is either in the frozen matrix or recorded as an admitted change.

    Payload entered the ontology after the Gate B freeze and was invisible to the
    matrix generator, which filters on the frozen entity list. That is the drift
    this test exists to catch.
    """

    def test_no_m1_to_m4_class_is_unaccounted_for(self) -> None:
        graph = load(M1_TO_M4)
        classes = {str(c).split("#")[-1] for c in graph.subjects(RDF.type, OWL.Class) if own(c)}
        matrix_rows = (PROJECT / "reports" / "entity-formalisation-matrix.tsv").read_text(encoding="utf-8").splitlines()[1:]
        in_matrix = {row.split("\t")[0].split(":")[-1] for row in matrix_rows if row.strip()}
        catalog_rows = (PROJECT / "docs" / "CONCEPTUAL_CHANGE_CATALOG.tsv").read_text(encoding="utf-8").splitlines()[1:]
        in_catalog = {row.split("\t")[0].split("(")[0].strip() for row in catalog_rows if row.strip()}
        unaccounted = sorted(classes - in_matrix - in_catalog)
        self.assertEqual(
            [], unaccounted,
            "these M1-M4 classes appear in neither the entity matrix nor the conceptual change catalog: "
            f"{unaccounted}. Either regenerate the matrix or register the term as an admitted change.",
        )

    def test_matrix_contains_no_class_absent_from_the_ontology(self) -> None:
        graph = load(M1_TO_M4)
        classes = {str(c).split("#")[-1] for c in graph.subjects(RDF.type, OWL.Class) if own(c)}
        matrix_rows = (PROJECT / "reports" / "entity-formalisation-matrix.tsv").read_text(encoding="utf-8").splitlines()[1:]
        in_matrix = {row.split("\t")[0].split(":")[-1] for row in matrix_rows if row.strip()}
        self.assertEqual([], sorted(in_matrix - classes))


class DocumentReferenceTest(unittest.TestCase):
    """Every repository path named in a document must exist.

    A document that cites a file which was renamed or deleted asserts something
    the repository cannot support, which is the same defect class as a criterion
    citing a source it does not have.
    """

    PATTERN = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_/.-]*\.(?:csv|tsv|ttl|rq|rdf|py|md|yml|yaml))`")
    EXTERNAL = {"prov-o.ttl", "prov.ttl"}

    def test_every_referenced_file_exists(self) -> None:
        missing = []
        for document in sorted((PROJECT / "docs").glob("*.md")) + sorted(PROJECT.glob("*.md")):
            for match in self.PATTERN.findall(document.read_text(encoding="utf-8")):
                if Path(match).name in self.EXTERNAL:
                    continue
                if (PROJECT / match).exists():
                    continue
                if any(PROJECT.rglob(Path(match).name)):
                    continue
                missing.append(f"{document.name} -> {match}")
        self.assertEqual([], sorted(missing), f"documents reference files that do not exist: {missing}")


if __name__ == "__main__":
    unittest.main()
