"""Generate the frozen 76-entity formalisation matrix from the executable ontology."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from rdflib import Graph, Namespace, OWL, RDF, RDFS, URIRef

from audit_formalisation import parse_gate_b


ROOT = "https://w3id.org/railsec-scope/"
RSSO = Namespace(ROOT + "ontology#")
MODULES = {
    ROOT + "core#": "M1",
    ROOT + "criteria#": "M2",
    ROOT + "results#": "M3",
    ROOT + "assessment#": "M4",
}
REQ_TO_K = {
    "ORF-03": {"K-03"}, "ORF-05": {"K-01"}, "ORF-06": {"K-02"},
    "ORF-09": {"K-04"}, "ORF-12": {"K-11", "K-23", "K-24"},
    "ORF-13": {"K-11", "K-14", "K-23", "K-24"}, "ORF-22": {"K-15"},
    "ORF-23": {"K-15", "K-16"}, "ORF-25": {"K-12"},
    "ORF-27": {"K-05", "K-06"}, "ORF-28": {"K-05"}, "ORF-30": {"K-05"},
    "ORF-31": {"K-08"}, "ORF-32": {"K-09"}, "ORF-33": {"K-10"},
    "ORF-40": {"K-17", "K-18"}, "ORF-42": {"K-18"}, "ORF-43": {"K-19", "K-20"},
    "ORF-45": {"K-07"}, "ORF-47": {"K-21"}, "ORF-48": {"K-13", "K-14"},
    "ORN-05": {"K-22"},
}


def short(term: URIRef) -> str:
    value = str(term)
    return value.rsplit("#", 1)[-1] if "#" in value else value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    graph = Graph()
    for path in sorted((project / "ontology").glob("*.ttl")):
        graph.parse(path)

    frozen_entities, _ = parse_gate_b()
    classes = sorted(
        {term for term in graph.subjects(RDF.type, OWL.Class) if isinstance(term, URIRef) and any(str(term).startswith(ns) for ns in MODULES) and short(term) in frozen_entities},
        key=str,
    )
    domains: dict[URIRef, list[str]] = defaultdict(list)
    ranges: dict[URIRef, list[str]] = defaultdict(list)
    for prop in set(graph.subjects(RDF.type, OWL.ObjectProperty)) | set(graph.subjects(RDF.type, OWL.DatatypeProperty)):
        for domain in graph.objects(prop, RDFS.domain):
            if isinstance(domain, URIRef): domains[domain].append(short(prop))
        for range_ in graph.objects(prop, RDFS.range):
            if isinstance(range_, URIRef): ranges[range_].append(short(prop))

    disjoint: dict[URIRef, set[str]] = defaultdict(set)
    for left, right in graph.subject_objects(OWL.disjointWith):
        if isinstance(left, URIRef) and isinstance(right, URIRef):
            disjoint[left].add(short(right)); disjoint[right].add(short(left))
    for node in graph.subjects(RDF.type, OWL.AllDisjointClasses):
        head = graph.value(node, OWL.members)
        members = list(graph.items(head)) if head else []
        for member in members:
            if isinstance(member, URIRef): disjoint[member].update(short(x) for x in members if x != member and isinstance(x, URIRef))

    rows = ["entity\thome_module\tnamed_superclasses\tdomain_properties\trange_properties\trestriction_count\tdisjoint_with\tk_constraints"]
    for cls in classes:
        namespace = next(ns for ns in MODULES if str(cls).startswith(ns))
        supers = sorted(short(x) for x in graph.objects(cls, RDFS.subClassOf) if isinstance(x, URIRef))
        restrictions = sum(1 for x in graph.objects(cls, RDFS.subClassOf) if (x, RDF.type, OWL.Restriction) in graph)
        constraints: set[str] = set()
        for requirement in graph.objects(cls, RSSO.requirement):
            constraints.update(REQ_TO_K.get(str(requirement), set()))
        rows.append("\t".join([
            short(cls), MODULES[namespace], ",".join(supers), ",".join(sorted(domains[cls])),
            ",".join(sorted(ranges[cls])), str(restrictions), ",".join(sorted(disjoint[cls])), ",".join(sorted(constraints)),
        ]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
