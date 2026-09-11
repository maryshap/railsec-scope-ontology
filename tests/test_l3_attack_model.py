"""Small structural guards for the governed L3 attack-model foundation."""

from __future__ import annotations

import unittest
from pathlib import Path

from rdflib import Graph, Namespace, OWL, RDF, RDFS


PROJECT = Path(__file__).resolve().parents[1]
ATTACK = Namespace("https://w3id.org/railsec-scope/attack#")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RES = Namespace("https://w3id.org/railsec-scope/results#")


class L3AttackModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = Graph().parse(PROJECT / "ontology" / "attack.ttl")

    def test_attack_vocabulary_is_versioned_and_separate_from_case_data(self) -> None:
        self.assertIn((ATTACK.AttackTechnique, RDFS.subClassOf, CRIT.VersionedArtefact), self.graph)
        self.assertIn((ATTACK.AttackTactic, RDFS.subClassOf, CRIT.VersionedArtefact), self.graph)
        self.assertEqual([], list(self.graph.subjects(RDF.type, ATTACK.AttackTechnique)))

    def test_technique_applicability_is_assessed_by_a_criterion(self) -> None:
        self.assertIn((ATTACK.assessesAttackTechnique, RDFS.domain, CRIT.Criterion), self.graph)
        self.assertIn((ATTACK.assessesAttackTechnique, RDFS.range, ATTACK.AttackTechnique), self.graph)
        self.assertNotIn((ATTACK.assessesAttackTechnique, RDFS.subPropertyOf, CRIT.determinesMembershipOf), self.graph)

    def test_attack_path_is_a_run_derived_result_with_positioned_steps(self) -> None:
        self.assertIn((ATTACK.AttackPathResult, RDFS.subClassOf, RES.DerivedResult), self.graph)
        self.assertIn((ATTACK.hasAttackPathStep, RDFS.domain, ATTACK.AttackPathResult), self.graph)
        self.assertIn((ATTACK.hasAttackPathStep, RDFS.range, ATTACK.AttackPathStep), self.graph)
        self.assertIn((ATTACK.stepConcernsElement, RDFS.range, CORE.Element), self.graph)
        self.assertIn((ATTACK.supportedByApplicabilityEvaluation, RDFS.range, RES.CriterionEvaluation), self.graph)

    def test_attack_paths_can_be_linked_to_safety_impacts_without_sil(self) -> None:
        self.assertIn((ATTACK.safetyImpactFromAttackPath, RDFS.domain, RES.SafetyImpactResult), self.graph)
        self.assertIn((ATTACK.safetyImpactFromAttackPath, RDFS.range, ATTACK.AttackPathResult), self.graph)
        self.assertIn((ATTACK.safetyImpactConcernsElement, RDFS.range, CORE.Element), self.graph)
        self.assertIn((ATTACK.safetyImpactConcernsPayload, RDFS.range, CORE.Payload), self.graph)
        self.assertIn((ATTACK.safetyImpactKind, RDFS.range, Namespace("http://www.w3.org/2001/XMLSchema#").string), self.graph)

    def test_technique_profiles_can_record_preconditions_and_effects_without_case_data(self) -> None:
        self.assertIn((ATTACK.AttackTechniqueProfile, RDFS.subClassOf, CRIT.VersionedArtefact), self.graph)
        self.assertIn((ATTACK.profileForTechnique, RDFS.range, ATTACK.AttackTechnique), self.graph)
        self.assertIn((ATTACK.profileUsesApplicabilityCriterion, RDFS.range, CRIT.Criterion), self.graph)
        self.assertIn((ATTACK.preconditionRequiresEvaluationOf, RDFS.range, CRIT.Criterion), self.graph)
        self.assertIn((ATTACK.preconditionRequiresAccessMechanism, RDFS.range, CORE.AccessMechanism), self.graph)
        self.assertIn((ATTACK.effectCreatesAttackState, RDFS.range, ATTACK.AttackState), self.graph)
        self.assertIn((ATTACK.effectAffectsSecurityProperty, RDFS.range, CORE.SecurityProperty), self.graph)
        self.assertEqual([], list(self.graph.subjects(RDF.type, ATTACK.AttackTechniqueProfile)))

    def test_every_attack_property_has_domain_and_range(self) -> None:
        for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
            for prop in self.graph.subjects(RDF.type, kind):
                with self.subTest(property=prop):
                    self.assertTrue(list(self.graph.objects(prop, RDFS.domain)))
                    self.assertTrue(list(self.graph.objects(prop, RDFS.range)))

    def test_attack_ics_source_is_pinned_to_a_specific_release(self) -> None:
        self.assertIn((ATTACK.MITREAttackICS19_2, RDF.type, CRIT.SourceEdition), self.graph)
        self.assertIn(
            (ATTACK.MITREAttackICS19_2Collection, CRIT.locatedInEdition, ATTACK.MITREAttackICS19_2),
            self.graph,
        )


if __name__ == "__main__":
    unittest.main()
