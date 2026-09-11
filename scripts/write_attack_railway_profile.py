#!/usr/bin/env python3
"""Write the reviewed railway profile register for ATT&CK ICS 19.2.

The register is deliberately not an applicability map. It records which
projected ATT&CK techniques already have sourced railway applicability
criteria, which techniques are selected for the current minimal railway attack
path profile, and which projected catalogue techniques are not admitted to the
current profile boundary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]

FIELDS = [
    "technique_id",
    "name",
    "tactic_ids",
    "source_url",
    "profile_disposition",
    "profile_scope",
    "attack_path_role",
    "implemented_criterion",
    "review_basis",
    "next_action",
    "notes",
]

MINIMAL_PROFILE_ROLES = {
    "T0886": "initial-access/lateral-movement",
    "T0842": "collection/reconnaissance",
    "T0830": "traffic-position/lateral-movement",
    "T1692.001": "manipulation-command-authenticity",
    "T1692.002": "manipulation-reporting-sequence",
    "T0831": "manipulation-control",
    "T0832": "manipulation-view",
    "T0814": "availability-impact",
    "T0815": "view-impact",
    "T0829": "view-impact",
    "T1691.001": "command-availability-impact",
}


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


def _load_source(source: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    payload = source.read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    expected = manifest["source_sha256"].lower()
    if actual != expected:
        raise ValueError(f"source SHA-256 mismatch: expected {expected}, got {actual}")
    return json.loads(payload)


def implemented_criteria(criteria_path: Path) -> dict[str, list[str]]:
    text = criteria_path.read_text(encoding="utf-8")
    pairs = re.findall(
        r"rssca:([a-z0-9-]+) a rss-crit:Criterion ;.*?"
        r"rss-attack:assessesAttackTechnique <https://w3id\.org/railsec-scope/attack/ics/19\.2/technique/([^>]+)>",
        text,
        flags=re.DOTALL,
    )
    by_technique: dict[str, list[str]] = {}
    for criterion, technique_id in pairs:
        by_technique.setdefault(technique_id, []).append(criterion)
    return {technique_id: sorted(criteria) for technique_id, criteria in sorted(by_technique.items())}


def profile_rows(source: Path, manifest_path: Path, criteria_path: Path) -> list[dict[str, str]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundle = _load_source(source, manifest)
    implemented_by_technique = implemented_criteria(criteria_path)
    objects = bundle["objects"]
    active = [obj for obj in objects if _active(obj, manifest)]
    tactics = {
        obj["x_mitre_shortname"]: _reference(obj)["external_id"]
        for obj in active
        if obj["type"] == "x-mitre-tactic"
    }
    techniques = sorted(
        (obj for obj in active if obj["type"] == "attack-pattern"),
        key=lambda obj: _reference(obj)["external_id"],
    )
    if len(techniques) != manifest["expected_active_techniques"]:
        raise ValueError(
            "active technique count changed: "
            f"expected {manifest['expected_active_techniques']}, got {len(techniques)}"
        )

    rows: list[dict[str, str]] = []
    for technique in techniques:
        reference = _reference(technique)
        technique_id = reference["external_id"]
        tactic_ids = ",".join(
            sorted(
                tactics[phase["phase_name"]]
                for phase in technique.get("kill_chain_phases", [])
                if phase.get("kill_chain_name") == "mitre-ics-attack"
                and phase.get("phase_name") in tactics
            )
        )
        implemented = implemented_by_technique.get(technique_id, [])
        role = MINIMAL_PROFILE_ROLES.get(technique_id, "")
        if implemented:
            disposition = "implemented-criterion"
            profile_scope = "minimal-railway-attack-path-profile" if role else "admitted-implemented-supporting-profile"
            attack_path_role = role or "supporting-applicability-criterion"
            review_basis = "ATT&CK source location plus sourced L1/L2 prerequisite criterion"
            next_action = "Use in three-valued L3 applicability evaluation"
            notes = "Railway applicability is evaluated by ontology/criteria-attack.ttl."
        elif role:
            disposition = "selected-pending-criterion"
            profile_scope = "minimal-railway-attack-path-profile"
            attack_path_role = role
            review_basis = "ATT&CK catalogue identity plus current L3 profile boundary"
            next_action = (
                "Add a sourced three-valued applicability Criterion before this technique "
                "can materialise an AttackPathStep."
            )
            notes = (
                "Selected to complete the initial-access/lateral-movement part of the "
                "minimal railway attack-path profile; no applicability is asserted yet."
            )
        else:
            disposition = "not-admitted-current-profile"
            profile_scope = "outside-current-profile-boundary"
            attack_path_role = ""
            review_basis = "ATT&CK catalogue identity only; no project railway applicability decision"
            next_action = (
                "Do not use for L3 path materialisation unless a future profile revision "
                "adds sourced railway applicability semantics."
            )
            notes = "No railway applicability or irrelevance is asserted by catalogue inclusion."
        rows.append(
            {
                "technique_id": technique_id,
                "name": technique["name"],
                "tactic_ids": tactic_ids,
                "source_url": reference.get("url", ""),
                "profile_disposition": disposition,
                "profile_scope": profile_scope,
                "attack_path_role": attack_path_role,
                "implemented_criterion": ";".join(implemented),
                "review_basis": review_basis,
                "next_action": next_action,
                "notes": notes,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=PROJECT / "build" / "attack-ics-19.2.json",
        help="pinned ATT&CK for ICS STIX bundle",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT / "imports" / "attack-ics-19.2-projection.json",
        help="projection policy and source digest",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT / "imports" / "attack-ics-19.2-railway-profile.tsv",
        help="review register to write",
    )
    parser.add_argument(
        "--criteria",
        type=Path,
        default=PROJECT / "ontology" / "criteria-attack.ttl",
        help="sourced attack applicability criteria",
    )
    args = parser.parse_args()

    rows = profile_rows(args.source, args.manifest, args.criteria)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, dialect="excel-tab", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} ATT&CK railway-profile records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
