"""Map the inspected legacy ETCS workbook extract into a new M6 ABox."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef, XSD


CASE_ROOT = "https://w3id.org/railsec-scope/case/etcs/"
CASE = Namespace(CASE_ROOT + "resource/")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RSSO = Namespace("https://w3id.org/railsec-scope/ontology#")
DCTERMS = Namespace("http://purl.org/dc/terms/")


def records(sheet: list[list], id_header: str, pattern: str) -> list[dict]:
    header = [str(value or "") for value in sheet[0]]
    output = []
    for row in sheet[1:]:
        item = {header[index]: value for index, value in enumerate(row) if index < len(header)}
        identifier = str(item.get(id_header) or "").strip()
        if re.match(pattern, identifier): output.append(item)
    return output


def tokens(value) -> list[str]:
    return [part.strip() for part in re.split(r"[,;]", str(value or "")) if part.strip()]


def local(kind: str, identifier: str) -> URIRef:
    return CASE[f"{kind}-{identifier.lower().replace('_', '-').replace(' ', '-')}"]


def add_element_boundary(graph: Graph, element: URIRef, identifier: str, status: URIRef, instance_set: URIRef) -> None:
    assertion = local("boundary", identifier)
    graph.add((element, RDF.type, CORE.Element))
    graph.add((assertion, RDF.type, CORE.BoundaryStatusAssertion))
    graph.add((assertion, CORE.statusSubject, element))
    graph.add((assertion, CORE.boundaryStatusValue, status))
    graph.add((assertion, CORE.hasEpistemicStatus, CORE.assertedFactStatus))
    graph.add((assertion, RES.assertedInInstanceSet, instance_set))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("extract", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "cases" / "etcs")
    args = parser.parse_args()
    workbook = json.loads(args.extract.read_text(encoding="utf-8"))
    sheets = workbook["sheets"]

    zones = records(sheets["Zones"]["values"], "ZoneID", r"^Z-")
    assets = records(sheets["Assets_Flat"]["values"], "AssetID", r"^[A-Z]+-")
    interfaces = records(sheets["Interfaces_Flat"]["values"], "IF-ID", r"^IF-")
    functions = records(sheets["Functions_Flat"]["values"], "FN-ID", r"^FN-")
    assumptions = records(sheets["TrustAssumptions_Flat"]["values"], "TrustAssumptionID", r"^TA-")

    graph = Graph()
    for prefix, namespace in (("case", CASE), ("rss-core", CORE), ("rss-crit", CRIT), ("rss-res", RES), ("rss-rail", RAIL), ("rsso", RSSO), ("dcterms", DCTERMS)):
        graph.bind(prefix, namespace)
    ontology = URIRef(CASE_ROOT.rstrip("/"))
    graph.add((ontology, RDF.type, OWL.Ontology))
    graph.add((ontology, OWL.imports, URIRef("https://w3id.org/railsec-scope/assessment")))
    graph.add((ontology, OWL.imports, URIRef("https://w3id.org/railsec-scope/railway")))
    graph.add((ontology, OWL.versionIRI, URIRef(CASE_ROOT + "version/0.1.0")))

    version = CASE["instance-version-0.1.0"]
    instance_set = CASE["instance-set"]
    run = CASE["import-run"]
    graph.add((version, RDF.type, CRIT.ArtefactVersion)); graph.add((version, CRIT.versionIdentifier, Literal("0.1.0")))
    graph.add((instance_set, RDF.type, RES.InstanceSet)); graph.add((instance_set, CRIT.hasVersion, version))
    graph.add((run, RDF.type, RES.Run)); graph.add((run, RES.usedInstanceSet, instance_set)); graph.add((run, RES.runIdentifier, Literal("etcs-workbook-import-0.1.0")))
    graph.add((instance_set, DCTERMS.source, Literal("Ontology_model.xlsx SHA-256 9563FA315813F7EAE9881494B5C627CB61FA47830FF13C97B3D9145B4CE573BC")))

    zone_types = {str(row["ZoneID"]): str(row.get("ZoneType") or "") for row in zones}
    for row in zones:
        identifier = str(row["ZoneID"]); zone = local("zone", identifier)
        graph.add((zone, RDF.type, RAIL.RailwaySecurityZone)); graph.add((zone, RDF.type, CORE.Group))
        graph.add((zone, RSSO.stableIdentifier, Literal(identifier))); graph.add((zone, RDFS.label, Literal(str(row.get("ZoneName") or identifier))))

    asset_nodes: dict[str, URIRef] = {}
    for row in assets:
        identifier = str(row["AssetID"]); asset = local("asset", identifier); asset_nodes[identifier] = asset
        graph.add((asset, RDF.type, RAIL.RailwayAsset)); graph.add((asset, RDF.type, CORE.Asset))
        classification = str(row.get("AssetClass") or "")
        mapped_class = {"SafetyCritical": RAIL.SafetyCriticalAsset, "SafetyRelated": RAIL.SafetyRelatedAsset, "Operational": RAIL.OperationalAsset}.get(classification)
        if mapped_class: graph.add((asset, RDF.type, mapped_class))
        graph.add((asset, RSSO.stableIdentifier, Literal(identifier))); graph.add((asset, RDFS.label, Literal(str(row.get("AssetName") or identifier))))
        primary = str(row.get("PrimaryZoneID") or "")
        for zone_id in [primary, str(row.get("SecondaryZoneID") or "")]:
            if zone_id in zone_types: graph.add((asset, CORE.memberOf, local("zone", zone_id)))
        type_name = str(row.get("AssetType") or "").strip()
        if type_name:
            type_node = local("asset-type", re.sub(r"[^a-zA-Z0-9]+", "-", type_name).strip("-"))
            graph.add((type_node, RDF.type, CORE.AssetType)); graph.add((type_node, RDFS.label, Literal(type_name)))
            graph.add((asset, CORE.hasAssetType, type_node))
        status = CORE.external if zone_types.get(primary) == "External" else CORE.inScope
        add_element_boundary(graph, asset, f"asset-{identifier}", status, instance_set)

    for row in interfaces:
        identifier = str(row["IF-ID"]); interface = local("interface", identifier)
        graph.add((interface, RDF.type, CORE.Interface)); graph.add((interface, RSSO.stableIdentifier, Literal(identifier)))
        graph.add((interface, RDFS.label, Literal(str(row.get("From â†’ To") or identifier))))
        from_id, to_id = str(row.get("FromAssetID") or ""), str(row.get("ToAssetID") or "")
        from_zone, to_zone = str(row.get("FromZoneID") or ""), str(row.get("ToZoneID") or "")
        status = CORE.external if zone_types.get(from_zone) == "External" and zone_types.get(to_zone) == "External" else CORE.inScope
        add_element_boundary(graph, interface, f"interface-{identifier}", status, instance_set)
        if from_id not in asset_nodes or to_id not in asset_nodes: continue
        directions = [("forward", from_id, to_id)]
        if str(row.get("Direction") or "").lower() == "bi": directions.append(("reverse", to_id, from_id))
        for suffix, origin_id, destination_id in directions:
            flow_id = f"{identifier}-{suffix}"; flow = local("flow", flow_id)
            graph.add((flow, RDF.type, RAIL.RailwayInformationFlow)); graph.add((flow, RDF.type, CORE.InformationFlow))
            graph.add((flow, RSSO.stableIdentifier, Literal(flow_id))); graph.add((flow, CORE.hasOrigin, asset_nodes[origin_id])); graph.add((flow, CORE.hasDestination, asset_nodes[destination_id])); graph.add((flow, CORE.traverses, interface))
            add_element_boundary(graph, flow, f"flow-{flow_id}", status, instance_set)

    function_nodes = {str(row["FN-ID"]): local("function", str(row["FN-ID"])) for row in functions}
    for row in functions:
        identifier = str(row["FN-ID"]); function = function_nodes[identifier]
        safety = str(row.get("FunctionSafetyClass") or "") in {"SafetyCritical", "SafetyRelated"}
        graph.add((function, RDF.type, CORE.SafetyFunction if safety else CORE.Function))
        graph.add((function, RSSO.stableIdentifier, Literal(identifier))); graph.add((function, RDFS.label, Literal(str(row.get("Name") or identifier))))
        for asset_id in tokens(row.get("ImplementedByAssetIDs")):
            if asset_id in asset_nodes: graph.add((asset_nodes[asset_id], CORE.realises, function))
        for dependency in tokens(row.get("DependsOn")):
            if dependency in function_nodes: graph.add((function, CORE.directlyDependsOn, function_nodes[dependency]))

    element_lookup = {**asset_nodes}
    element_lookup.update({str(row["IF-ID"]): local("interface", str(row["IF-ID"])) for row in interfaces})
    for row in assumptions:
        identifier = str(row["TrustAssumptionID"]); assumption = local("assumption", identifier)
        graph.add((assumption, RDF.type, CORE.Assumption)); graph.add((assumption, CORE.hasEpistemicStatus, CORE.assumptionStatus)); graph.add((assumption, RES.assertedInInstanceSet, instance_set))
        graph.add((assumption, CORE.assertionPredicateIri, Literal(str(RAIL.trusted), datatype=XSD.anyURI))); graph.add((assumption, CORE.assertionObjectLiteral, Literal(True)))
        for scoped in tokens(row.get("ScopeElementID_Normalized")):
            if scoped in element_lookup: graph.add((assumption, CORE.assertionSubject, element_lookup[scoped]))
        graph.add((assumption, RDFS.comment, Literal(str(row.get("AssumptionDescription") or ""))))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    graph.serialize(args.output_dir / "abox.ttl", format="turtle")

    mapping_rows = [
        ("Zones", "Zone row", "rss-rail:RailwaySecurityZone + rss-core:Group", "one case Group per ZoneID"),
        ("Assets_Flat", "Asset row", "rss-rail:RailwayAsset", "AssetClass mapped only to explicit M5 safety/operational subclasses"),
        ("Assets_Flat", "Primary/SecondaryZoneID", "rss-core:memberOf", "both memberships retained"),
        ("Assets_Flat", "boundary status", "BoundaryStatusAssertion", "External primary zone => external; otherwise inScope; domain review required"),
        ("Interfaces_Flat", "Interface row", "rss-core:Interface + InformationFlow", "bi creates forward and reverse flows; uni creates forward flow"),
        ("Functions_Flat", "Function row", "rss-core:Function/SafetyFunction", "SafetyCritical and SafetyRelated map to SafetyFunction"),
        ("Functions_Flat", "ImplementedByAssetIDs", "rss-core:realises", "only resolvable AssetIDs emitted"),
        ("TrustAssumptions_Flat", "Assumption row", "rss-core:Assumption", "generic proposition pattern; unknown scopes retained in unmapped report"),
    ]
    with (args.output_dir / "mapping.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n"); writer.writerow(["source_sheet", "source_field", "target", "transformation"]); writer.writerows(mapping_rows)

    unmapped = [
        ("DataObjects_Flat", "all", "No Gate B DataObject entity; preserve source workbook and add only after an approved extension decision."),
        ("Actors & Roles", "all", "Actor is not a Gate B entity; do not collapse actors into SystemRole without review."),
        ("Interfaces_Flat", "security flag columns", "Deferred until M5 characteristic vocabulary and epistemic mapping are domain-reviewed."),
        ("Assets_Flat", "SecurityLevel", "Legacy security level is not SIL and is not mapped to SafetyIntegrityLevel."),
    ]
    with (args.output_dir / "unmapped.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n"); writer.writerow(["source_sheet", "source_field", "reason"]); writer.writerows(unmapped)
    print(f"ETCS ABox: {len(graph)} triples; zones={len(zones)} assets={len(assets)} interfaces={len(interfaces)} functions={len(functions)} assumptions={len(assumptions)}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
