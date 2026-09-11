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
        self.assertEqual(set(implemented), {
            row["technique_id"]
            for row in rows.values()
            if row["profile_disposition"] == "implemented-criterion"
        })

    def test_unimplemented_techniques_do_not_claim_railway_applicability(self) -> None:
        implemented_ids = set(implemented_criterion_map())
        for row in profile_rows():
            if row["technique_id"] in implemented_ids:
                continue
            with self.subTest(technique=row["technique_id"]):
                self.assertEqual("source-review-required", row["profile_disposition"])
                self.assertEqual("", row["implemented_criterion"])
                self.assertIn("No railway applicability is asserted", row["notes"])


if __name__ == "__main__":
    unittest.main()
