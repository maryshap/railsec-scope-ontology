"""Report ETCS case-data readiness without turning missing evidence into false."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
CASE_DIR = PROJECT / "cases" / "etcs"
CORE = Namespace("https://w3id.org/railsec-scope/core#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")

BASE_FILES = (
    CASE_DIR / "abox.ttl",
    CASE_DIR / "classification-provenance.ttl",
    CASE_DIR / "security-facts.ttl",
    CASE_DIR / "transmission-environment.ttl",
)

ZONE_CLASSES = (
    RAIL.ExternalZone,
    RAIL.DMZZone,
    RAIL.PartiallyTrustedZone,
    RAIL.MobileZone,
)


def local_name(value: object) -> str:
    text = str(value)
    return text.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def load_graph() -> Graph:
    graph = Graph()
    for path in BASE_FILES:
        graph.parse(path)
    return graph


def count_typed(graph: Graph, class_iri) -> int:
    return len(set(graph.subjects(RDF.type, class_iri)))


def count_any_typed(graph: Graph, *class_iris) -> int:
    return len(
        {
            subject
            for class_iri in class_iris
            for subject in graph.subjects(RDF.type, class_iri)
        }
    )


def build_report(graph: Graph) -> dict:
    status_counts = Counter(
        local_name(status) for status in graph.objects(None, CORE.hasEpistemicStatus)
    )
    zone_class_counts = {
        local_name(zone_class): count_typed(graph, zone_class)
        for zone_class in ZONE_CLASSES
    }
    metrics = {
        "zones": count_typed(graph, RAIL.RailwaySecurityZone),
        "assets": count_typed(graph, RAIL.RailwayAsset),
        "interfaces": count_typed(graph, CORE.Interface),
        "directed_flows": count_typed(graph, RAIL.RailwayInformationFlow),
        "functions": count_any_typed(graph, CORE.Function, CORE.SafetyFunction),
        "safety_functions": count_typed(graph, CORE.SafetyFunction),
        "safety_critical_assets": count_typed(graph, RAIL.SafetyCriticalAsset),
        "payload_links": len(set(graph.subject_objects(CORE.carriesPayload))),
        "fail_safe_dependencies": len(set(graph.subject_objects(RAIL.failSafeDependsOn))),
        "reachable_by_links": len(set(graph.subject_objects(CORE.reachableBy))),
    }
    gates = {
        "architecture_inventory_present": all(
            metrics[key] > 0 for key in ("zones", "assets", "interfaces", "directed_flows")
        ),
        "zone_semantics_ready_for_entry_points": any(zone_class_counts.values()),
        "access_evidence_ready_for_attack_paths": metrics["reachable_by_links"] > 0,
        "fail_safe_evidence_available": metrics["fail_safe_dependencies"] > 0,
        "payload_evidence_available": metrics["payload_links"] > 0,
    }
    return {
        "files": [str(path.relative_to(PROJECT)).replace("\\", "/") for path in BASE_FILES],
        "metrics": metrics,
        "zone_class_counts": zone_class_counts,
        "epistemic_status_counts": dict(sorted(status_counts.items())),
        "readiness_gates": gates,
        "interpretation": {
            "missing_is_false": False,
            "failed_gate_meaning": "missing or unreviewed evidence; preserve as unresolved",
        },
    }


def markdown(report: dict) -> str:
    metrics = report["metrics"]
    zones = report["zone_class_counts"]
    gates = report["readiness_gates"]
    lines = [
        "# ETCS case-data audit",
        "",
        "Generated from the four base ETCS evidence graphs. A failed readiness gate",
        "means that evidence is missing or unreviewed; it never means that the fact is false.",
        "",
        "## Inventory",
        "",
        "| Measure | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| `{key}` | {value} |" for key, value in metrics.items())
    lines += ["", "## Zone semantics", "", "| Zone class | Count |", "|---|---:|"]
    lines.extend(f"| `{key}` | {value} |" for key, value in zones.items())
    lines += ["", "## Readiness gates", "", "| Gate | Status |", "|---|---|"]
    lines.extend(
        f"| `{key}` | {'ready' if value else 'unresolved'} |"
        for key, value in gates.items()
    )
    lines += ["", "## Epistemic status records", "", "| Status | Count |", "|---|---:|"]
    lines.extend(
        f"| `{key}` | {value} |"
        for key, value in report["epistemic_status_counts"].items()
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    report = build_report(load_graph())
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(markdown(report), encoding="utf-8")
    if not args.json_out and not args.markdown_out:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
