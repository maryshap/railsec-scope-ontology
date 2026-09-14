from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from compare_case_runs import compare  # noqa: E402


def row(element: str, criterion: str, outcome: str) -> dict[str, str]:
    return {
        "evaluation": f"evaluation-{element}-{criterion}",
        "stage": "stage",
        "criterion": criterion,
        "element": element,
        "outcome": outcome,
        "derivation_status": "complete",
    }


class CompareCaseRunsTest(unittest.TestCase):
    def test_classifies_changed_unchanged_and_one_sided_results(self) -> None:
        result = compare(
            [row("a", "c1", "satisfied"), row("b", "c2", "notSatisfied"), row("c", "c3", "satisfied")],
            [row("a", "c1", "notSatisfied"), row("b", "c2", "notSatisfied"), row("d", "c4", "undetermined")],
        )
        statuses = {(item["element"], item["comparison_status"]) for item in result}
        self.assertEqual(
            {("a", "changed"), ("b", "unchanged"), ("c", "left-only"), ("d", "right-only")},
            statuses,
        )

    def test_duplicate_stable_key_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            compare([row("a", "c", "satisfied"), row("a", "c", "notSatisfied")], [])


if __name__ == "__main__":
    unittest.main()
