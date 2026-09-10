#!/usr/bin/env python3
"""Create the controlled RDF projection of a pinned ATT&CK for ICS bundle.

Only catalogue identity is projected: active tactics, active techniques and the
ATT&CK technique-to-tactic relation. Descriptions, procedure examples,
mitigations and case applicability are deliberately excluded. Railway
applicability is produced later by sourced three-valued criteria.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ATTACK = "https://w3id.org/railsec-scope/attack#"
PROJECTION = "https://w3id.org/railsec-scope/attack/ics/19.2"
VERSION_IRI = "https://w3id.org/railsec-scope/version/19.2/attack-ics-projection"
ITEM = PROJECTION + "/"


def _literal(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _reference(obj: dict[str, Any]) -> dict[str, Any]:
    for reference in obj.get("external_references", []):
        if reference.get("source_name") == "mitre-attack" and reference.get("external_id"):
            return reference
    raise ValueError(f"ATT&CK object {obj.get('id')} has no mitre-attack external identifier")


def _active(obj: dict[str, Any], manifest: dict[str, Any]) -> bool:
    if obj.get("type") not in manifest["include_object_types"]:
        return False
    if manifest.get("exclude_revoked", True) and obj.get("revoked", False):
        return False
    if manifest.get("exclude_deprecated", True) and obj.get("x_mitre_deprecated", False):
        return False
    return True


def _load_and_verify(source: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    payload = source.read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    expected = manifest["source_sha256"].lower()
    if actual != expected:
        raise ValueError(f"source SHA-256 mismatch: expected {expected}, got {actual}")
    bundle = json.loads(payload)
    if bundle.get("type") != "bundle":
        raise ValueError("source is not a STIX bundle")
    collections = [obj for obj in bundle.get("objects", []) if obj.get("type") == "x-mitre-collection"]
    collection = next((obj for obj in collections if obj.get("id") == manifest["collection_id"]), None)
    if collection is None:
        raise ValueError("pinned ATT&CK collection identifier is absent")
    if str(collection.get("x_mitre_version")) != str(manifest["collection_version"]):
        raise ValueError("ATT&CK collection version does not match the manifest")
    return bundle


def project(source: Path, manifest_path: Path) -> str:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundle = _load_and_verify(source, manifest)
    active = [obj for obj in bundle["objects"] if _active(obj, manifest)]
    tactics = sorted((obj for obj in active if obj["type"] == "x-mitre-tactic"), key=lambda obj: _reference(obj)["external_id"])
    techniques = sorted((obj for obj in active if obj["type"] == "attack-pattern"), key=lambda obj: _reference(obj)["external_id"])
    if len(tactics) != manifest["expected_active_tactics"]:
        raise ValueError(f"active tactic count changed: expected {manifest['expected_active_tactics']}, got {len(tactics)}")
    if len(techniques) != manifest["expected_active_techniques"]:
        raise ValueError(f"active technique count changed: expected {manifest['expected_active_techniques']}, got {len(techniques)}")

    tactic_by_shortname = {obj["x_mitre_shortname"]: _reference(obj)["external_id"] for obj in tactics}
    lines = [
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix rss-attack: <https://w3id.org/railsec-scope/attack#> .",
        "@prefix rss-crit: <https://w3id.org/railsec-scope/criteria#> .",
        "",
        f"<{PROJECTION}> a owl:Ontology ;",
        f"    owl:versionIRI <{VERSION_IRI}> ;",
        "    owl:imports <https://w3id.org/railsec-scope/attack> ;",
        f"    dcterms:title {_literal('Controlled projection of MITRE ATT&CK for ICS 19.2')}@en ;",
        f"    dcterms:description {_literal(manifest['projection_policy'])}@en .",
        "",
    ]

    for tactic in tactics:
        reference = _reference(tactic)
        external_id = reference["external_id"]
        lines.extend([
            f"<{ITEM}tactic/{external_id}> a rss-attack:AttackTactic ;",
            f"    rdfs:label {_literal(tactic['name'])}@en ;",
            "    rss-crit:hasVersion rss-attack:MITREAttackICS19_2VocabularyVersion ;",
            f"    rss-attack:attackExternalIdentifier {_literal(external_id)} ;",
            "    rss-attack:cataloguedAt rss-attack:MITREAttackICS19_2Collection ;",
            f"    rdfs:seeAlso <{reference['url']}> .",
            "",
        ])

    for technique in techniques:
        reference = _reference(technique)
        external_id = reference["external_id"]
        phases = sorted({
            phase["phase_name"]
            for phase in technique.get("kill_chain_phases", [])
            if phase.get("kill_chain_name") == "mitre-ics-attack"
        })
        tactic_ids = [tactic_by_shortname[phase] for phase in phases if phase in tactic_by_shortname]
        if not tactic_ids:
            raise ValueError(f"active technique {external_id} has no active ICS tactic")
        tactic_objects = (",\n        ").join(f"<{ITEM}tactic/{tactic_id}>" for tactic_id in tactic_ids)
        lines.extend([
            f"<{ITEM}technique/{external_id}> a rss-attack:AttackTechnique ;",
            f"    rdfs:label {_literal(technique['name'])}@en ;",
            "    rss-crit:hasVersion rss-attack:MITREAttackICS19_2VocabularyVersion ;",
            f"    rss-attack:attackExternalIdentifier {_literal(external_id)} ;",
            "    rss-attack:cataloguedAt rss-attack:MITREAttackICS19_2Collection ;",
            f"    rss-attack:techniqueInTactic {tactic_objects} ;",
        ])
        lines.extend([
            f"    rdfs:seeAlso <{reference['url']}> .",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="pinned ATT&CK for ICS STIX bundle")
    parser.add_argument("--manifest", type=Path, required=True, help="projection policy and source digest")
    parser.add_argument("--output", type=Path, required=True, help="generated Turtle projection")
    args = parser.parse_args()
    content = project(args.source, args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8", newline="\n")
    print(f"projected ATT&CK ICS catalogue to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
