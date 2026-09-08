"""Export a case/scenario RDF graph to Neo4j as a readable property graph.

The ontology represents architecture, facts and results as RDF with heavy
reification (Assumption, CriterionEvaluation, DerivationRecord/Step). A
literal RDF-to-property-graph import (e.g. neosemantics/n10s) is possible
and gives you back the exact same graph structure, but for presenting a
scenario it is easier to browse a purpose-built graph: assets, zones,
interfaces and flows as nodes with real relationships, and evaluation
results attached to the flow/asset they concern rather than sitting behind
an extra CriterionEvaluation/DerivationRecord/DerivationStep hop each.

This script builds that purpose-built graph. It works on facts-only input
(architecture + scenario security-facts + transmission-environment — what
you have before running the orchestrator) and on facts-plus-results input
(the same, plus a Run's output graph, if you pass one — see
scripts/orchestrator.py --output) without needing to know in advance which
one you're giving it: it only creates Evaluation nodes for the
CriterionEvaluation individuals it actually finds, so with facts-only input
you correctly get a graph with no evaluations yet.

Two ways to use the result:

1. Cypher file (no Neo4j Python driver needed):
   python3 scripts/export_to_neo4j.py <ttl files...> --cypher-out build/scenario.cypher
   Then in Neo4j Browser: paste the file contents, or
   cypher-shell -u neo4j -p <password> -f build/scenario.cypher

2. Direct import (needs `pip install neo4j`, connects immediately):
   python3 scripts/export_to_neo4j.py <ttl files...> \\
       --uri bolt://localhost:7687 --user neo4j --password <password>
   Connection details can also come from environment variables
   NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD instead of flags.

Example, scenario 2 facts only:
   python3 scripts/export_to_neo4j.py \\
       cases/etcs/abox.ttl \\
       cases/etcs/classification-provenance.ttl \\
       cases/etcs/scenarios/missing-safety-code/security-facts.ttl \\
       cases/etcs/scenarios/missing-safety-code/transmission-environment.ttl \\
       --cypher-out build/missing-safety-code.cypher

Example, once you have a real Run result from your machine:
   python3 scripts/orchestrator.py \\
       cases/etcs/abox.ttl cases/etcs/classification-provenance.ttl \\
       cases/etcs/scenarios/missing-safety-code/security-facts.ttl \\
       cases/etcs/scenarios/missing-safety-code/transmission-environment.ttl \\
       --output build/missing-safety-code-result.ttl
   python3 scripts/export_to_neo4j.py \\
       build/missing-safety-code-result.ttl \\
       --cypher-out build/missing-safety-code-result.cypher
   (the result file already contains the input facts too, so it alone is
   enough once it exists — you don't need to pass the input files again)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS

CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")


def local(iri) -> str:
    return str(iri).rstrip("/").split("/")[-1].split("#")[-1]


def esc(value) -> str:
    """Escape a value for embedding in a Cypher string literal."""
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def var_name(node_id: str) -> str:
    """A valid, unquoted Cypher variable name for a node id.

    Cypher identifiers must match [A-Za-z_][A-Za-z0-9_]*; the case's IRIs use
    hyphens and dots (e.g. flow-if-ts-06-forward), which are not valid there.
    """
    safe = "".join(ch if ch.isalnum() else "_" for ch in node_id)
    if safe and safe[0].isdigit():
        safe = "n" + safe
    return f"n_{safe}"


def cypher_node(node_id: str, labels: list[str], props: dict) -> str:
    label_str = ":".join(labels)
    var = var_name(node_id)
    prop_parts = []
    for key, value in props.items():
        if value is None:
            continue
        if isinstance(value, bool):
            prop_parts.append(f"{key}: {str(value).lower()}")
        elif isinstance(value, (int, float)):
            prop_parts.append(f"{key}: {value}")
        else:
            prop_parts.append(f"{key}: '{esc(value)}'")
    prop_str = ", ".join(prop_parts)
    return f"MERGE ({var}:{label_str} {{id: '{esc(node_id)}'}}) SET {var} += {{{prop_str}}};"


def cypher_rel(source_id: str, rel_type: str, target_id: str, props: dict | None = None) -> str:
    prop_str = ""
    if props:
        parts = [f"{k}: '{esc(v)}'" if isinstance(v, str) else f"{k}: {v}" for k, v in props.items()]
        prop_str = " {" + ", ".join(parts) + "}"
    return (f"MATCH (a {{id: '{esc(source_id)}'}}), (b {{id: '{esc(target_id)}'}}) "
            f"MERGE (a)-[:{rel_type}{prop_str}]->(b);")


def build_statements(g: Graph) -> list[str]:
    statements: list[str] = []

    # --- Zones ---
    for s in g.subjects(RDF.type, CORE.Group):
        label = g.value(s, RDFS.label) or local(s)
        statements.append(cypher_node(local(s), ["Zone"], {"name": str(label)}))

    # --- Assets ---
    sc_assets = set(g.subjects(RDF.type, RAIL.SafetyCriticalAsset))

    for s in g.subjects(RDF.type, CORE.Asset):
        label = g.value(s, RDFS.label) or local(s)
        labels = ["Asset"]
        if s in sc_assets:
            labels.append("SafetyCritical")
        statements.append(cypher_node(local(s), labels, {"name": str(label)}))
        for zone in g.objects(s, CORE.memberOf):
            statements.append(cypher_rel(local(s), "MEMBER_OF", local(zone)))

    # --- Interfaces ---
    for s in g.subjects(RDF.type, CORE.Interface):
        label = g.value(s, RDFS.label) or local(s)
        statements.append(cypher_node(local(s), ["Interface"], {"name": str(label)}))

    # --- Payloads ---
    for s in g.subjects(RDF.type, RAIL.SafetyRelatedPayload):
        statements.append(cypher_node(local(s), ["Payload"], {"safetyRelated": True}))
    for s in g.subjects(RDF.type, RAIL.NonSafetyPayload):
        statements.append(cypher_node(local(s), ["Payload"], {"safetyRelated": False}))

    # --- Flows ---
    protection_props = ["authenticationEnabled", "encryptionEnabled", "integrityProtectionEnabled",
                         "safetyCodeEnabled", "sequenceProtectionEnabled",
                         "sourceDestinationIdentifierEnabled", "timeoutMechanismEnabled"]
    l1_props = ["monitoringEnabled", "networkSegmentationEnabled", "rateLimitingEnabled",
                "crossesTrustBoundary", "wirelessMedium"]
    for s in g.subjects(RDF.type, RAIL.RailwayInformationFlow):
        props = {"name": str(g.value(s, RDFS.label) or local(s))}
        for p in protection_props + l1_props:
            val = g.value(s, RAIL[p])
            if val is not None:
                props[p] = val.toPython() if hasattr(val, "toPython") else val
        statements.append(cypher_node(local(s), ["Flow"], props))
        for iface in g.objects(s, CORE.traverses):
            statements.append(cypher_rel(local(s), "TRAVERSES", local(iface)))
        for origin in g.objects(s, CORE.hasOrigin):
            statements.append(cypher_rel(local(s), "ORIGINATES_FROM", local(origin)))
        for dest in g.objects(s, CORE.hasDestination):
            statements.append(cypher_rel(local(s), "TERMINATES_AT", local(dest)))
        for payload in g.objects(s, CORE.carriesPayload):
            statements.append(cypher_rel(local(s), "CARRIES", local(payload)))

    # --- Evaluations (only present if this graph is a Run result, not facts-only) ---
    eval_count = 0
    for ev in g.subjects(RDF.type, RES.CriterionEvaluation):
        element = g.value(ev, RES.evaluationConcernsElement)
        criterion = g.value(ev, RES.evaluatesCriterion)
        outcome = g.value(ev, RES.hasEvaluationOutcome)
        if element is None or criterion is None or outcome is None:
            continue
        outcome_name = local(outcome)  # satisfied / notSatisfied / undetermined
        criterion_statement = g.value(criterion, CRIT.criterionStatement)
        eval_id = local(ev)
        labels = ["Evaluation", outcome_name[0].upper() + outcome_name[1:]]
        statements.append(cypher_node(eval_id, labels, {
            "criterion": local(criterion),
            "statement": str(criterion_statement) if criterion_statement else "",
            "outcome": outcome_name,
        }))
        statements.append(cypher_rel(local(element), "HAS_EVALUATION", eval_id))
        eval_count += 1

    return statements, eval_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", type=Path, help="Turtle files to load and export")
    parser.add_argument("--cypher-out", type=Path, default=None,
                         help="write generated Cypher statements to this file")
    parser.add_argument("--uri", default=os.environ.get("NEO4J_URI"))
    parser.add_argument("--user", default=os.environ.get("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD"))
    parser.add_argument("--clear", action="store_true",
                         help="delete all existing nodes/relationships before importing "
                              "(only with --uri; asks for confirmation)")
    args = parser.parse_args()

    g = Graph()
    for f in args.files:
        g.parse(f)
    print(f"loaded {len(g)} triples from {len(args.files)} file(s)")

    statements, eval_count = build_statements(g)
    print(f"generated {len(statements)} Cypher statements "
          f"({eval_count} evaluation nodes — 0 is expected for facts-only input)")

    if args.cypher_out:
        args.cypher_out.parent.mkdir(parents=True, exist_ok=True)
        args.cypher_out.write_text("\n".join(statements) + "\n")
        print(f"written: {args.cypher_out}")

    if args.uri:
        try:
            from neo4j import GraphDatabase
        except ImportError:
            print("`neo4j` package not installed; run `pip install neo4j` "
                  "or use --cypher-out instead.")
            return 1
        if args.clear:
            confirm = input(f"This will DELETE ALL nodes/relationships in {args.uri}. Type 'yes' to continue: ")
            if confirm.strip().lower() != "yes":
                print("aborted")
                return 1
        driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
        with driver.session() as session:
            if args.clear:
                session.run("MATCH (n) DETACH DELETE n")
            for i, stmt in enumerate(statements):
                session.run(stmt)
                if (i + 1) % 200 == 0:
                    print(f"  {i + 1}/{len(statements)}")
        driver.close()
        print(f"imported into {args.uri}")

    if not args.cypher_out and not args.uri:
        print("\nNo --cypher-out and no --uri given — nothing written. "
              "Pass one of them, or both.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
