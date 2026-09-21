from __future__ import annotations

import unittest

from scripts.audit_etcs_case_data import build_report, load_graph

from rdflib import Namespace, RDF


CASE = Namespace("https://w3id.org/railsec-scope/case/etcs/resource/")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")


class EtcsCaseDataAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = load_graph()
        cls.report = build_report(cls.graph)

    def test_architecture_inventory_is_present(self) -> None:
        metrics = self.report["metrics"]
        self.assertEqual(14, metrics["zones"])
        self.assertEqual(92, metrics["assets"])
        self.assertEqual(88, metrics["interfaces"])
        self.assertEqual(148, metrics["directed_flows"])
        self.assertEqual(29, metrics["functions"])
        self.assertTrue(self.report["readiness_gates"]["architecture_inventory_present"])

    def test_open_l3_inputs_are_reported_not_defaulted(self) -> None:
        self.assertTrue(self.report["readiness_gates"]["zone_semantics_ready_for_entry_points"])
        self.assertEqual(1, self.report["zone_class_counts"]["ExternalZone"])
        self.assertEqual(1, self.report["zone_class_counts"]["DMZZone"])
        self.assertFalse(self.report["readiness_gates"]["access_evidence_ready_for_attack_paths"])
        self.assertFalse(self.report["readiness_gates"]["fail_safe_evidence_available"])
        self.assertFalse(self.report["interpretation"]["missing_is_false"])

    def test_known_payload_links_remain_visible(self) -> None:
        self.assertEqual(4, self.report["metrics"]["payload_links"])
        self.assertTrue(self.report["readiness_gates"]["payload_evidence_available"])

    def test_reviewed_payload_directions_are_exact_and_conflict_remains_unresolved(self) -> None:
        self.assertIn(
            (CASE["flow-if-rad-03-reverse"], CORE.carriesPayload, CASE["payload-DO-04"]),
            self.graph,
        )
        self.assertIn(
            (CASE["flow-if-rad-01-forward"], CORE.carriesPayload, CASE["payload-DO-05"]),
            self.graph,
        )
        for direction in ("forward", "reverse"):
            self.assertNotIn(
                (CASE[f"flow-if-ct-01-{direction}"], CORE.carriesPayload, CASE["payload-DO-04"]),
                self.graph,
            )

    def test_new_case_facts_have_source_locations_and_asserted_fact_status(self) -> None:
        assertions = (
            "zone-z-06-external-zone-assertion",
            "zone-z-it-fw-dmz-zone-assertion",
            "flow-if-rad-03-reverse-payload-do-04-assertion",
            "flow-if-rad-01-forward-payload-do-05-assertion",
        )
        for local_name in assertions:
            assertion = CASE[local_name]
            self.assertIn((assertion, RDF.type, CORE.AssertedFact), self.graph)
            self.assertIn((assertion, CORE.hasEpistemicStatus, CORE.assertedFactStatus), self.graph)
            locations = list(self.graph.objects(assertion, Namespace("http://www.w3.org/ns/prov#").wasDerivedFrom))
            self.assertEqual(1, len(locations))
            self.assertIn((locations[0], RDF.type, CRIT.SourceLocation), self.graph)


if __name__ == "__main__":
    unittest.main()
