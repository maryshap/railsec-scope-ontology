from __future__ import annotations

import unittest

from scripts.audit_etcs_case_data import build_report, load_graph


class EtcsCaseDataAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = build_report(load_graph())

    def test_architecture_inventory_is_present(self) -> None:
        metrics = self.report["metrics"]
        self.assertEqual(14, metrics["zones"])
        self.assertEqual(92, metrics["assets"])
        self.assertEqual(88, metrics["interfaces"])
        self.assertEqual(148, metrics["directed_flows"])
        self.assertEqual(29, metrics["functions"])
        self.assertTrue(self.report["readiness_gates"]["architecture_inventory_present"])

    def test_open_l3_inputs_are_reported_not_defaulted(self) -> None:
        self.assertFalse(self.report["readiness_gates"]["zone_semantics_ready_for_entry_points"])
        self.assertFalse(self.report["readiness_gates"]["access_evidence_ready_for_attack_paths"])
        self.assertFalse(self.report["readiness_gates"]["fail_safe_evidence_available"])
        self.assertFalse(self.report["interpretation"]["missing_is_false"])

    def test_known_payload_links_remain_visible(self) -> None:
        self.assertEqual(2, self.report["metrics"]["payload_links"])
        self.assertTrue(self.report["readiness_gates"]["payload_evidence_available"])


if __name__ == "__main__":
    unittest.main()
