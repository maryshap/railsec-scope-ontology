"""Audit formal terms against the frozen Gate B entity and module tables."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from rdflib import Graph, Namespace, OWL, RDF, RDFS


PROJECT = Path(__file__).resolve().parents[1]
GATE_B = PROJECT.parent / "doc2 gateB conceptual model v1 0.md"
ONTOLOGY_DIR = PROJECT / "ontology"
CHANGE_CATALOGUE = PROJECT / "docs" / "CONCEPTUAL_CHANGE_CATALOG.tsv"

MODULE_FILES = {
    "M1": "core.ttl",
    "M2": "criteria.ttl",
    "M3": "results.ttl",
    "M4": "assessment.ttl",
}

MODULE_NAMESPACES = {
    "M1": Namespace("https://w3id.org/railsec-scope/core#"),
    "M2": Namespace("https://w3id.org/railsec-scope/criteria#"),
    "M3": Namespace("https://w3id.org/railsec-scope/results#"),
    "M4": Namespace("https://w3id.org/railsec-scope/assessment#"),
}


def parse_gate_b() -> tuple[set[str], dict[str, list[str]]]:
    text = GATE_B.read_text(encoding="utf-8")
    entities: set[str] = set()
    in_entity_catalogue = False
    for line in text.splitlines():
        if re.match(r"^### 8\.[1-6]", line):
            in_entity_catalogue = True
            continue
        if line.startswith("### 8.7"):
            in_entity_catalogue = False
        if in_entity_catalogue:
            match = re.match(r"^\| ([^|]+) \| [^|]+ \| [^|]+ \|$", line)
            if match and match.group(1).strip() != "Entity":
                name = match.group(1).strip()
                if not set(name) <= {"-"}:
                    entities.add(name)

    allocation: dict[str, list[str]] = {}
    for module, value in re.findall(r"^\| (M[1-4]) \| (.+) \|$", text, re.MULTILINE):
        allocation[module] = [item.strip() for item in value.split(",")]

    allocated = [name for names in allocation.values() for name in names]
    if set(allocated) != entities or len(allocated) != len(set(allocated)):
        raise RuntimeError("Frozen Gate B entity catalogue and module allocation disagree")
    return entities, allocation


def parse_conceptual_changes() -> list[dict[str, str]]:
    if not CHANGE_CATALOGUE.exists():
        return []
    lines = CHANGE_CATALOGUE.read_text(encoding="utf-8").splitlines()
    header = "term\thome_module\tterm_kind\tchange_kind\tnamed_parent\tparticipates_in_k_or_cq\tchange_record"
    if not lines or lines[0] != header:
        raise RuntimeError("Conceptual change catalogue has an invalid header")
    changes: list[dict[str, str]] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        term, module, term_kind, change_kind, named_parent, participates, change_record = line.split("\t")
        if module not in MODULE_FILES or term_kind not in {"class", "objectProperty", "datatypeProperty", "individual"}:
            raise RuntimeError(f"Invalid conceptual change row: {line}")
        if change_kind not in {"extension", "revision"} or participates not in {"true", "false"} or not change_record.startswith("CR-B-"):
            raise RuntimeError(f"Invalid conceptual change governance fields: {line}")
        if change_kind == "extension" and (named_parent == "-" or participates == "true"):
            raise RuntimeError(f"Extension violates admission policy and must be a revision: {line}")
        changes.append({
            "term": term, "module": module, "term_kind": term_kind,
            "change_kind": change_kind, "named_parent": named_parent,
            "participates": participates, "change_record": change_record,
        })
    return changes


def audit(selected: list[str]) -> int:
    entities, allocation = parse_gate_b()
    changes = parse_conceptual_changes()
    class_changes = {
        module: {change["term"] for change in changes if change["module"] == module and change["term_kind"] == "class"}
        for module in MODULE_FILES
    }
    failures: list[str] = []
    print(f"Frozen entity catalogue: {len(entities)}")

    for module in selected:
        path = ONTOLOGY_DIR / MODULE_FILES[module]
        if not path.exists():
            failures.append(f"{module}: missing file {path.name}")
            continue
        graph = Graph().parse(path)
        frozen_expected = set(allocation[module])
        expected = frozen_expected | class_changes[module]
        namespace = MODULE_NAMESPACES[module]
        actual = {
            str(subject)[len(str(namespace)) :]
            for subject in graph.subjects(RDF.type, OWL.Class)
            if str(subject).startswith(str(namespace))
        }
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        legacy = sorted({str(term) for triple in graph for term in triple if "purl.org/ics-sec" in str(term)})
        print(
            f"{module}: {len(graph)} triples; "
            f"expected classes={len(expected)} ({len(frozen_expected)} frozen + {len(class_changes[module])} governed changes); "
            f"encoded classes={len(actual)}"
        )
        if missing:
            failures.append(f"{module}: missing classes: {', '.join(missing)}")
        if extra:
            failures.append(f"{module}: unapproved classes: {', '.join(extra)}")
        if legacy:
            failures.append(f"{module}: legacy namespace present: {', '.join(legacy)}")

    kind_to_type = {
        "class": OWL.Class,
        "objectProperty": OWL.ObjectProperty,
        "datatypeProperty": OWL.DatatypeProperty,
        "individual": OWL.NamedIndividual,
    }
    for change in changes:
        graph = Graph().parse(ONTOLOGY_DIR / MODULE_FILES[change["module"]])
        term = MODULE_NAMESPACES[change["module"]][change["term"]]
        if (term, RDF.type, kind_to_type[change["term_kind"]]) not in graph:
            failures.append(f"{change['module']}: governed {change['term_kind']} is not declared: {change['term']}")
        if change["change_kind"] == "extension":
            parent = MODULE_NAMESPACES[change["module"]][change["named_parent"]]
            if (term, RDFS.subClassOf, parent) not in graph:
                failures.append(f"{change['module']}: extension lacks declared approved parent {change['named_parent']}: {change['term']}")

    if failures:
        print("AUDIT FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("AUDIT PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--module",
        action="append",
        choices=sorted(MODULE_FILES),
        help="Audit one or more modules; default is every formal module.",
    )
    args = parser.parse_args()
    return audit(args.module or sorted(MODULE_FILES))


if __name__ == "__main__":
    raise SystemExit(main())
