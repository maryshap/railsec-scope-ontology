"""Build-time module-isolation (K-19/K-20) and publication (K-22) lint."""

from __future__ import annotations

import argparse
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, URIRef


CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
PROJECT_ROOT = "https://w3id.org/railsec-scope/"
RAILWAY = PROJECT_ROOT + "railway#"


def lint_graphs(graphs: dict[str, Graph]) -> list[str]:
    violations: list[str] = []
    terminology = {name: graph for name, graph in graphs.items() if name in {"core.ttl", "criteria.ttl", "results.ttl", "assessment.ttl", "railway.ttl"}}
    for name, graph in terminology.items():
        for subject in set(graph.subjects()):
            if isinstance(subject, URIRef) and ("/case/" in str(subject) or "/fixture/" in str(subject)):
                violations.append(f"K-19 {name}: case/fixture individual in terminology module: {subject}")

    for name in ("core.ttl", "criteria.ttl", "results.ttl", "assessment.ttl"):
        graph = terminology.get(name, Graph())
        for triple in graph:
            if any(isinstance(term, URIRef) and str(term).startswith(RAILWAY) for term in triple):
                violations.append(f"K-20 {name}: railway/subsystem term occurs in M1-M4: {triple}")

    protected_text_predicates = {CRIT.criterionStatement, CRIT.interpretationProposition}
    for name, graph in graphs.items():
        for predicate in protected_text_predicates:
            for subject, value in graph.subject_objects(predicate):
                if isinstance(value, Literal) and len(str(value).split()) > 250:
                    violations.append(f"K-22 {name}: unusually long source-sensitive literal on {subject}")
    return sorted(set(violations))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    graphs = {path.name: Graph().parse(path) for path in sorted((args.root / "ontology").glob("*.ttl"))}
    violations = lint_graphs(graphs)
    if violations:
        print("PUBLICATION LINT FAILED")
        for violation in violations: print(f"- {violation}")
        return 1
    print("PUBLICATION LINT PASSED (K-19, K-20, automated K-22 guard)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
