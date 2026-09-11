"""Guards for the ATT&CK ICS railway-profile coverage register."""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
PROFILE = PROJECT / "imports" / "attack-ics-19.2-railway-profile.tsv"
PROJECTION = PROJECT / "imports" / "attack-ics-19.2.ttl"
CRITERIA = PROJECT / "ontology" / "criteria-attack.ttl"


def profile_rows() -> list[dict[str, str]]:
    with PROFILE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def projected_technique_ids() -> set[str]:
    text = PROJECTION.read_text(encoding="utf-8")
    return set(re.findall(r"/technique/([^>]+)> a rss-attack:AttackTechnique", text))


def implemented_criterion_map() -> dict[str, str]:
    text = CRITERIA.read_text(encoding="utf-8")
    pairs = re.findall(
        r"rssca:([a-z0-9-]+) a rss-crit:Criterion ;.*?"
        r"rss-attack:assessesAttackTechnique <https://w3id\.org/railsec-scope/attack/ics/19\.2/technique/([^>]+)>",
        text,
        flags=re.DOTALL,
    )
    by_technique: dict[str, list[str]] = {}
    for criterion, technique_id in pairs:
        by_technique.setdefault(technique_id, []).append(criterion)
    return {technique_id: ";".join(sorted(criteria)) for technique_id, criteria in by_technique.items()}


class AttackRailwayProfileTest(unittest.TestCase):
    def test_every_projected_technique_has_exactly_one_profile_row(self) -> None:
        rows = profile_rows()
        ids = [row["technique_id"] for row in rows]
        self.assertEqual(97, len(rows))
        self.assertEqual(sorted(projected_technique_ids()), sorted(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_implemented_applicability_criteria_are_marked_in_the_profile(self) -> None:
        rows = {row["technique_id"]: row for row in profile_rows()}
        implemented = implemented_criterion_map()
        self.assertGreaterEqual(len(implemented), 4)
        for technique_id, criterion in implemented.items():
            self.assertEqual("implemented-criterion", rows[technique_id]["profile_disposition"])
            self.assertEqual(criterion, rows[technique_id]["implemented_criterion"])
            self.assertTrue(rows[technique_id]["profile_scope"])
        self.assertEqual(set(implemented), {
            row["technique_id"]
            for row in rows.values()
            if row["profile_disposition"] == "implemented-criterion"
        })

    def test_minimal_attack_path_profile_has_implemented_initial_access_technique(self) -> None:
        rows = {row["technique_id"]: row for row in profile_rows()}
        self.assertEqual("implemented-criterion", rows["T0886"]["profile_disposition"])
        self.assertEqual("minimal-railway-attack-path-profile", rows["T0886"]["profile_scope"])
        self.assertEqual("initial-access/lateral-movement", rows["T0886"]["attack_path_role"])
        self.assertEqual(
            "t0886-remote-services-dmz-entry-point-criterion;"
            "t0886-remote-services-external-entry-point-criterion",
            rows["T0886"]["implemented_criterion"],
        )
        self.assertIn("Railway applicability is evaluated", rows["T0886"]["notes"])

    def test_minimal_attack_path_profile_covers_the_required_chain_roles(self) -> None:
        roles = {
            row["attack_path_role"]
            for row in profile_rows()
            if row["profile_scope"] == "minimal-railway-attack-path-profile"
        }
        self.assertIn("initial-access/lateral-movement", roles)
        self.assertIn("traffic-position/lateral-movement", roles)
        self.assertTrue(any(role.startswith("manipulation-") for role in roles))
        self.assertTrue(any(role.endswith("-impact") or role == "availability-impact" for role in roles))

    def test_unadmitted_techniques_do_not_claim_railway_applicability_or_irrelevance(self) -> None:
        implemented_ids = set(implemented_criterion_map())
        for row in profile_rows():
            if row["technique_id"] in implemented_ids or row["profile_disposition"] == "selected-pending-criterion":
                continue
            with self.subTest(technique=row["technique_id"]):
                self.assertEqual("not-admitted-current-profile", row["profile_disposition"])
                self.assertEqual("outside-current-profile-boundary", row["profile_scope"])
                self.assertEqual("", row["implemented_criterion"])
                self.assertIn("No railway applicability or irrelevance is asserted", row["notes"])


if __name__ == "__main__":
    unittest.main()
