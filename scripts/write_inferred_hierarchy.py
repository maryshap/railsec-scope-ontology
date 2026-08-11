"""Write a stable, diff-friendly named-class hierarchy report."""

from __future__ import annotations

import argparse
from pathlib import Path

from rdflib import Graph, OWL, RDFS, URIRef


ROOT = "https://w3id.org/railsec-scope/"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    graph = Graph().parse(args.input)
    rows: set[tuple[str, str]] = set()
    for child, parent in graph.subject_objects(RDFS.subClassOf):
        if isinstance(child, URIRef) and isinstance(parent, URIRef) and str(child).startswith(ROOT):
            rows.add((str(child), str(parent)))

    equivalent_pairs = {
        tuple(sorted((str(left), str(right))))
        for left, right in graph.subject_objects(OWL.equivalentClass)
        if isinstance(left, URIRef) and isinstance(right, URIRef)
        and (str(left).startswith(ROOT) or str(right).startswith(ROOT))
    }

    lines = ["child\tparent"] + [f"{child}\t{parent}" for child, parent in sorted(rows)]
    lines += ["", "equivalent_class_a\tequivalent_class_b"]
    lines += [f"{left}\t{right}" for left, right in sorted(equivalent_pairs)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
