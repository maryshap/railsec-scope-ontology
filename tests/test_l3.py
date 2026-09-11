"""Phase 2 Step 13 L3 reachability and path evidence."""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import l3  # noqa: E402
import orchestrator  # noqa: E402


FX = Namespace("https://w3id.org/railsec-scope/fixture/l3/")
ATTACK = Namespace("https://w3id.org/railsec-scope/attack#")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RULE = Namespace("https://w3id.org/railsec-scope/rules#")


def fixture_graph() -> Graph:
    graph = Graph()
    for path in sorted((PROJECT / "ontology").glob("*.ttl")):
        graph.parse(path)
    graph.parse(PROJECT / "rules" / "rules.ttl")
    graph.parse(PROJECT / "fixtures" / "l3" / "minimal.ttl")
    return graph


def add_attack_evaluation(
    graph: Graph,
    flow,
    criterion,
    technique,
    evaluation,
    outcome,
    prerequisite_criterion=None,
    prerequisite_evaluation=None,
) -> None:
    graph.add((technique, RDF.type, ATTACK.AttackTechnique))
    graph.add((criterion, RDF.type, CRIT.Criterion))
    graph.add((criterion, ATTACK.assessesAttackTechnique, technique))
    if prerequisite_criterion is not None and prerequisite_evaluation is not None:
        graph.add((criterion, ATTACK.requiresSatisfiedEvaluationOf, prerequisite_criterion))
        graph.add((prerequisite_criterion, RDF.type, CRIT.Criterion))
        graph.add((prerequisite_evaluation, RDF.type, RES.CriterionEvaluation))
        graph.add((prerequisite_evaluation, RES.evaluationConcernsElement, flow))
        graph.add((prerequisite_evaluation, RES.evaluatesCriterion, prerequisite_criterion))
        graph.add((prerequisite_evaluation, RES.hasEvaluationOutcome, RES.satisfied))
        graph.add((prerequisite_evaluation, RES.producedByRun, FX.run))
    graph.add((evaluation, RDF.type, RES.CriterionEvaluation))
    graph.add((evaluation, RES.evaluationConcernsElement, flow))
    graph.add((evaluation, RES.evaluatesCriterion, criterion))
    graph.add((evaluation, RES.hasEvaluationOutcome, outcome))
    graph.add((evaluation, RES.producedByRun, FX.run))


class L3ReachabilityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = fixture_graph()
        query = (PROJECT / "rules" / "classify-candidate.rq").read_text(encoding="utf-8")
        self.graph += self.graph.query(query).graph
        orchestrator.materialise_assignments(self.graph, FX.run)
        orchestrator.materialise_candidate_set(self.graph, FX.run)

    def test_materialiser_records_but_does_not_decide_membership(self) -> None:
        self.assertIn((FX.entry, RDF.type, CRIT.EntryPoint), self.graph)
        self.assertIn((FX.target, RDF.type, CRIT.CandidateExaminationTarget), self.graph)
        assignments = {
            self.graph.value(item, RES.assignsCategory)
            for item in self.graph.subjects(RDF.type, RES.CategoryAssignment)
            if self.graph.value(item, RES.producedByRun) == FX.run
        }
        self.assertEqual({CRIT.EntryPoint, CRIT.CandidateExaminationTarget}, assignments)

    def test_reachability_uses_only_vulnerable_edges(self) -> None:
        added = l3.apply(self.graph, FX.run)
        self.assertGreater(added, 0)
        reached = {
            self.graph.value(result, RES.reachabilityConcerns)
            for result in self.graph.subjects(RDF.type, RES.ReachabilityResult)
        }
        self.assertEqual({FX.middle, FX.target}, reached)
        self.assertNotIn(FX["not-reached"], reached)

    def test_paths_are_positioned_and_access_evidence_is_propagated(self) -> None:
        l3.apply(self.graph, FX.run)
        target_result = next(
            result for result in self.graph.subjects(RDF.type, RES.ReachabilityResult)
            if self.graph.value(result, RES.reachabilityConcerns) == FX.target
        )
        self.assertIn((target_result, RES.usedAccessMechanism, FX["remote-access"]), self.graph)
        self.assertIn((target_result, RES.reliedOnPrecondition, FX["network-access"]), self.graph)

        chains = []
        for chain in self.graph.subjects(RDF.type, RES.DependencyChain):
            entries = sorted(
                (
                    int(self.graph.value(entry, RES.pathPosition)),
                    self.graph.value(entry, RES.chainNode),
                )
                for entry in self.graph.objects(chain, RES.hasChainEntry)
            )
            if entries[-1][1] == FX.target:
                chains.append(entries)
        self.assertEqual([[(1, FX.entry), (2, FX.middle), (3, FX.target)]], chains)

    def test_l3_is_idempotent_and_never_classifies(self) -> None:
        l3.apply(self.graph, FX.run)
        self.assertEqual(0, l3.apply(self.graph, FX.run))
        for step in self.graph.subjects(RES.layerIdentifier, None):
            if str(self.graph.value(step, RES.layerIdentifier)) == "L3":
                for generated in self.graph.objects(step, RES.generatedResult):
                    self.assertNotIn((generated, RDF.type, RES.CategoryAssignment), self.graph)

    def test_candidate_set_and_explicit_selection_coverage(self) -> None:
        candidate_set = next(
            item for item in self.graph.subjects(RDF.type, RES.CandidateSet)
            if self.graph.value(item, RES.producedByRun) == FX.run
        )
        selection = FX.selection
        self.graph.add((selection, RDF.type, RES.Selection))
        self.graph.add((selection, CRIT.hasVersion, FX.version))
        self.graph.add((selection, RES.selectionBasedOnCandidateSet, candidate_set))
        self.graph.add((selection, RES.includesElement, FX.target))

        l3.apply_coverage(self.graph, FX.run)
        coverage = next(self.graph.subjects(RDF.type, RES.CoverageResult))
        self.assertEqual(RES.valuePresent, self.graph.value(coverage, RES.hasComputationOutcome))
        self.assertEqual(Decimal("0.3333333333333333333333333333"), self.graph.value(coverage, RES.representedValue).toPython())
        self.assertEqual(candidate_set, self.graph.value(coverage, RES.measuredCandidateSet))
        self.assertEqual(selection, self.graph.value(coverage, RES.measuredSelection))

    def test_ahp_ordering_produces_factor_values_and_positions(self) -> None:
        l3.apply_ordering(self.graph, FX.run)
        values = {
            self.graph.value(value, RES.valueOfFactor): self.graph.value(value, RES.representedValue).toPython()
            for value in self.graph.subjects(RDF.type, RES.FactorValue)
            if self.graph.value(self.graph.value(value, RES.factorValueForCandidate), RES.materialisesEvaluation)
            == FX["first-hop-candidate-evaluation"]
        }
        self.assertEqual(
            {
                Namespace("https://w3id.org/railsec-scope/rules#").AHPAuthenticationFactor: Decimal("0.3517"),
                Namespace("https://w3id.org/railsec-scope/rules#").AHPIntegrityFactor: Decimal("0.2513"),
            },
            values,
        )

        ordering = next(self.graph.subjects(RDF.type, RES.OrderingResult))
        ranked = sorted(
            (
                int(self.graph.value(entry, RES.orderingPosition)),
                self.graph.value(
                    self.graph.value(entry, RES.ranksAssignment),
                    RES.materialisesEvaluation,
                ),
            )
            for entry in self.graph.objects(ordering, RES.hasOrderingEntry)
        )
        self.assertEqual(
            [
                (1, FX["first-hop-candidate-evaluation"]),
                (2, FX["second-hop-candidate-evaluation"]),
                (3, FX["candidate-evaluation"]),
            ],
            ranked,
        )

    def test_attack_path_requires_satisfied_technique_evidence_for_every_hop(self) -> None:
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-attack-criterion"],
            FX["network-sniffing"],
            FX["first-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["first-hop-weakness-criterion"],
            prerequisite_evaluation=FX["first-hop-weakness-evaluation"],
        )

        l3.apply(self.graph, FX.run)

        targets = {
            self.graph.value(path, ATTACK.attackPathConcernsTarget)
            for path in self.graph.subjects(RDF.type, ATTACK.AttackPathResult)
        }
        self.assertEqual({FX.middle}, targets)

    def test_attack_path_is_not_materialised_without_prerequisite_evidence(self) -> None:
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-attack-criterion"],
            FX["network-sniffing"],
            FX["first-hop-attack-evaluation"],
            RES.satisfied,
        )
        add_attack_evaluation(
            self.graph,
            FX["second-hop"],
            FX["second-hop-attack-criterion"],
            FX["command-message"],
            FX["second-hop-attack-evaluation"],
            RES.satisfied,
        )

        l3.apply(self.graph, FX.run)

        self.assertEqual([], list(self.graph.subjects(RDF.type, ATTACK.AttackPathResult)))

    def test_attack_path_is_not_materialised_from_undetermined_prerequisite(self) -> None:
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-attack-criterion"],
            FX["network-sniffing"],
            FX["first-hop-attack-evaluation"],
            RES.satisfied,
        )
        self.graph.add((FX["first-hop-attack-criterion"], ATTACK.requiresSatisfiedEvaluationOf, FX["first-hop-weakness-criterion"]))
        self.graph.add((FX["first-hop-weakness-criterion"], RDF.type, CRIT.Criterion))
        self.graph.add((FX["first-hop-weakness-evaluation"], RDF.type, RES.CriterionEvaluation))
        self.graph.add((FX["first-hop-weakness-evaluation"], RES.evaluationConcernsElement, FX["first-hop"]))
        self.graph.add((FX["first-hop-weakness-evaluation"], RES.evaluatesCriterion, FX["first-hop-weakness-criterion"]))
        self.graph.add((FX["first-hop-weakness-evaluation"], RES.hasEvaluationOutcome, RES.undetermined))
        self.graph.add((FX["first-hop-weakness-evaluation"], RES.producedByRun, FX.run))

        l3.apply(self.graph, FX.run)

        self.assertEqual([], list(self.graph.subjects(RDF.type, ATTACK.AttackPathResult)))

    def test_reachability_and_attack_paths_are_stable_in_the_presence_of_cycles(self) -> None:
        self.graph.add((FX["cycle-hop"], RDF.type, RAIL.VulnerableFlow))
        self.graph.add((FX["cycle-hop"], CORE.hasOrigin, FX.target))
        self.graph.add((FX["cycle-hop"], CORE.hasDestination, FX.entry))
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-attack-criterion"],
            FX["network-sniffing"],
            FX["first-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["first-hop-weakness-criterion"],
            prerequisite_evaluation=FX["first-hop-weakness-evaluation"],
        )
        add_attack_evaluation(
            self.graph,
            FX["second-hop"],
            FX["second-hop-attack-criterion"],
            FX["command-message"],
            FX["second-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["second-hop-weakness-criterion"],
            prerequisite_evaluation=FX["second-hop-weakness-evaluation"],
        )
        add_attack_evaluation(
            self.graph,
            FX["cycle-hop"],
            FX["cycle-hop-attack-criterion"],
            FX["remote-services"],
            FX["cycle-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["cycle-hop-weakness-criterion"],
            prerequisite_evaluation=FX["cycle-hop-weakness-evaluation"],
        )

        l3.apply(self.graph, FX.run)

        for chain in self.graph.subjects(RDF.type, RES.DependencyChain):
            nodes = [
                self.graph.value(entry, RES.chainNode)
                for entry in self.graph.objects(chain, RES.hasChainEntry)
            ]
            with self.subTest(chain=chain):
                self.assertEqual(len(nodes), len(set(nodes)))
                self.assertNotIn(FX.entry, nodes[1:])

    def test_attack_path_steps_are_ordered_and_exclude_negative_techniques(self) -> None:
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-attack-criterion"],
            FX["network-sniffing"],
            FX["first-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["first-hop-weakness-criterion"],
            prerequisite_evaluation=FX["first-hop-weakness-evaluation"],
        )
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-negative-criterion"],
            FX["not-applicable-technique"],
            FX["first-hop-negative-evaluation"],
            RES.notSatisfied,
        )
        add_attack_evaluation(
            self.graph,
            FX["second-hop"],
            FX["second-hop-attack-criterion"],
            FX["command-message"],
            FX["second-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["second-hop-weakness-criterion"],
            prerequisite_evaluation=FX["second-hop-weakness-evaluation"],
        )

        l3.apply(self.graph, FX.run)

        target_path = next(
            path for path in self.graph.subjects(RDF.type, ATTACK.AttackPathResult)
            if self.graph.value(path, ATTACK.attackPathConcernsTarget) == FX.target
        )
        self.assertEqual([FX.entry], list(self.graph.objects(target_path, ATTACK.startsFromEntryPoint)))
        self.assertEqual([FX.target], list(self.graph.objects(target_path, ATTACK.attackPathConcernsTarget)))
        self.assertEqual(FX.run, self.graph.value(target_path, RES.producedByRun))
        self.assertEqual(RULE.phase3RuleVersion, self.graph.value(target_path, CRIT.hasVersion))
        reachability_result = self.graph.value(target_path, ATTACK.followsReachabilityResult)
        self.assertIn((reachability_result, RDF.type, RES.ReachabilityResult), self.graph)
        steps = sorted(
            (
                int(self.graph.value(step, ATTACK.attackPathStepPosition)),
                self.graph.value(step, ATTACK.stepConcernsElement),
                self.graph.value(step, ATTACK.stepUsesTechnique),
                self.graph.value(step, ATTACK.supportedByApplicabilityEvaluation),
            )
            for step in self.graph.objects(target_path, ATTACK.hasAttackPathStep)
        )
        self.assertEqual(
            [
                (1, FX["first-hop"], FX["network-sniffing"], FX["first-hop-attack-evaluation"]),
                (2, FX["second-hop"], FX["command-message"], FX["second-hop-attack-evaluation"]),
            ],
            steps,
        )
        used_techniques = {item[2] for item in steps}
        self.assertNotIn(FX["not-applicable-technique"], used_techniques)

        record = self.graph.value(target_path, RES.hasDerivationRecord)
        self.assertIn((record, RDF.type, RES.DerivationRecord), self.graph)
        self.assertEqual("complete", str(self.graph.value(record, RES.completenessStatus)))
        derivation_step = self.graph.value(record, RES.hasStep)
        self.assertEqual(RULE.AttackPathTraversalMethod, self.graph.value(derivation_step, RES.appliedComputation))
        self.assertEqual(RULE.AttackPathTraversalMechanism, self.graph.value(derivation_step, RES.executedByMechanism))
        used_evidence = set(self.graph.objects(derivation_step, RES.usedEntity))
        self.assertIn(FX["first-hop-attack-evaluation"], used_evidence)
        self.assertIn(FX["second-hop-attack-evaluation"], used_evidence)
        self.assertIn(FX["first-hop-weakness-evaluation"], used_evidence)
        self.assertIn(FX["second-hop-weakness-evaluation"], used_evidence)
        self.assertIn(reachability_result, used_evidence)

    def test_multiple_satisfied_techniques_on_one_flow_are_materialised_deterministically(self) -> None:
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-attack-criterion"],
            FX["network-sniffing"],
            FX["first-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["first-hop-weakness-criterion"],
            prerequisite_evaluation=FX["first-hop-weakness-evaluation"],
        )
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-second-attack-criterion"],
            FX["remote-services"],
            FX["first-hop-second-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["first-hop-second-weakness-criterion"],
            prerequisite_evaluation=FX["first-hop-second-weakness-evaluation"],
        )
        add_attack_evaluation(
            self.graph,
            FX["second-hop"],
            FX["second-hop-attack-criterion"],
            FX["command-message"],
            FX["second-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["second-hop-weakness-criterion"],
            prerequisite_evaluation=FX["second-hop-weakness-evaluation"],
        )

        l3.apply(self.graph, FX.run)

        target_path = next(
            path for path in self.graph.subjects(RDF.type, ATTACK.AttackPathResult)
            if self.graph.value(path, ATTACK.attackPathConcernsTarget) == FX.target
        )
        steps = sorted(
            (
                int(self.graph.value(step, ATTACK.attackPathStepPosition)),
                self.graph.value(step, ATTACK.stepConcernsElement),
                self.graph.value(step, ATTACK.stepUsesTechnique),
            )
            for step in self.graph.objects(target_path, ATTACK.hasAttackPathStep)
        )
        self.assertEqual(
            [
                (1, FX["first-hop"], FX["network-sniffing"]),
                (2, FX["first-hop"], FX["remote-services"]),
                (3, FX["second-hop"], FX["command-message"]),
            ],
            steps,
        )

    def test_branching_uses_deterministic_directed_shortest_path_choice(self) -> None:
        self.graph.add((FX["alt-middle"], RDF.type, CORE.Asset))
        self.graph.add((FX["aaa-entry-to-alt"], RDF.type, RAIL.VulnerableFlow))
        self.graph.add((FX["aaa-entry-to-alt"], CORE.hasOrigin, FX.entry))
        self.graph.add((FX["aaa-entry-to-alt"], CORE.hasDestination, FX["alt-middle"]))
        self.graph.add((FX["alt-to-target"], RDF.type, RAIL.VulnerableFlow))
        self.graph.add((FX["alt-to-target"], CORE.hasOrigin, FX["alt-middle"]))
        self.graph.add((FX["alt-to-target"], CORE.hasDestination, FX.target))
        add_attack_evaluation(
            self.graph,
            FX["aaa-entry-to-alt"],
            FX["alt-first-attack-criterion"],
            FX["network-sniffing"],
            FX["alt-first-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["alt-first-weakness-criterion"],
            prerequisite_evaluation=FX["alt-first-weakness-evaluation"],
        )
        add_attack_evaluation(
            self.graph,
            FX["alt-to-target"],
            FX["alt-second-attack-criterion"],
            FX["command-message"],
            FX["alt-second-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["alt-second-weakness-criterion"],
            prerequisite_evaluation=FX["alt-second-weakness-evaluation"],
        )
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-attack-criterion"],
            FX["later-branch-technique"],
            FX["first-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["first-hop-weakness-criterion"],
            prerequisite_evaluation=FX["first-hop-weakness-evaluation"],
        )
        add_attack_evaluation(
            self.graph,
            FX["second-hop"],
            FX["second-hop-attack-criterion"],
            FX["remote-services"],
            FX["second-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["second-hop-weakness-criterion"],
            prerequisite_evaluation=FX["second-hop-weakness-evaluation"],
        )

        l3.apply(self.graph, FX.run)

        target_path = next(
            path for path in self.graph.subjects(RDF.type, ATTACK.AttackPathResult)
            if self.graph.value(path, ATTACK.attackPathConcernsTarget) == FX.target
        )
        ordered_flows = [
            self.graph.value(step, ATTACK.stepConcernsElement)
            for step in sorted(
                self.graph.objects(target_path, ATTACK.hasAttackPathStep),
                key=lambda step: int(self.graph.value(step, ATTACK.attackPathStepPosition)),
            )
        ]
        self.assertEqual([FX["aaa-entry-to-alt"], FX["alt-to-target"]], ordered_flows)

    def test_attack_path_safety_impacts_link_paths_to_concerns_without_assigning_sil(self) -> None:
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-attack-criterion"],
            FX["network-sniffing"],
            FX["first-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["first-hop-weakness-criterion"],
            prerequisite_evaluation=FX["first-hop-weakness-evaluation"],
        )
        add_attack_evaluation(
            self.graph,
            FX["second-hop"],
            FX["second-hop-attack-criterion"],
            FX["command-message"],
            FX["second-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["second-hop-weakness-criterion"],
            prerequisite_evaluation=FX["second-hop-weakness-evaluation"],
        )
        self.graph.add((FX.target, RDF.type, RAIL.SafetyCriticalAsset))
        self.graph.add((FX["safety-function"], RDF.type, CORE.SafetyFunction))
        self.graph.add((FX["safety-function"], CORE.directlyDependsOn, FX.target))
        self.graph.add((FX["fail-safe-function"], RDF.type, CORE.SafetyFunction))
        self.graph.add((FX["fail-safe-function"], RAIL.failSafeDependsOn, FX.target))
        self.graph.add((FX["safety-payload"], RDF.type, RAIL.SafetyRelatedPayload))
        self.graph.add((FX["second-hop"], CORE.carriesPayload, FX["safety-payload"]))

        l3.apply(self.graph, FX.run)

        target_path = next(
            path for path in self.graph.subjects(RDF.type, ATTACK.AttackPathResult)
            if self.graph.value(path, ATTACK.attackPathConcernsTarget) == FX.target
        )
        impacts = [
            impact for impact in self.graph.subjects(RDF.type, RES.SafetyImpactResult)
            if self.graph.value(impact, ATTACK.safetyImpactFromAttackPath) == target_path
        ]
        self.assertEqual(
            {
                "safety-critical-asset",
                "safety-function-dependency",
                "fail-safe-dependency",
                "safety-related-payload",
            },
            {str(self.graph.value(impact, ATTACK.safetyImpactKind)) for impact in impacts},
        )
        self.assertIn(
            FX["safety-function"],
            {
                self.graph.value(impact, RES.affectsFunction)
                for impact in impacts
                if str(self.graph.value(impact, ATTACK.safetyImpactKind)) == "safety-function-dependency"
            },
        )
        self.assertIn(
            FX["fail-safe-function"],
            {
                self.graph.value(impact, RES.affectsFunction)
                for impact in impacts
                if str(self.graph.value(impact, ATTACK.safetyImpactKind)) == "fail-safe-dependency"
            },
        )
        payload_impact = next(
            impact for impact in impacts
            if str(self.graph.value(impact, ATTACK.safetyImpactKind)) == "safety-related-payload"
        )
        self.assertEqual(FX["second-hop"], self.graph.value(payload_impact, ATTACK.safetyImpactConcernsElement))
        self.assertEqual(FX["safety-payload"], self.graph.value(payload_impact, ATTACK.safetyImpactConcernsPayload))

        for impact in impacts:
            self.assertEqual(FX.run, self.graph.value(impact, RES.producedByRun))
            self.assertEqual(RULE.phase3RuleVersion, self.graph.value(impact, CRIT.hasVersion))
            record = self.graph.value(impact, RES.hasDerivationRecord)
            self.assertEqual("complete", str(self.graph.value(record, RES.completenessStatus)))
            step = self.graph.value(record, RES.hasStep)
            self.assertEqual(RULE.AttackPathSafetyImpactMethod, self.graph.value(step, RES.appliedComputation))
            self.assertEqual(RULE.AttackPathSafetyImpactMechanism, self.graph.value(step, RES.executedByMechanism))
            self.assertIn(target_path, set(self.graph.objects(step, RES.usedEntity)))

        self.assertEqual([], list(self.graph.triples((None, RAIL.hasSafetyIntegrityLevel, None))))
        self.assertEqual([], list(self.graph.triples((None, RAIL.assignedSafetyIntegrityLevel, None))))

    def test_attack_path_ordering_prioritises_safety_impact_without_assigning_sil(self) -> None:
        add_attack_evaluation(
            self.graph,
            FX["first-hop"],
            FX["first-hop-attack-criterion"],
            FX["network-sniffing"],
            FX["first-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["first-hop-weakness-criterion"],
            prerequisite_evaluation=FX["first-hop-weakness-evaluation"],
        )
        add_attack_evaluation(
            self.graph,
            FX["second-hop"],
            FX["second-hop-attack-criterion"],
            FX["command-message"],
            FX["second-hop-attack-evaluation"],
            RES.satisfied,
            prerequisite_criterion=FX["second-hop-weakness-criterion"],
            prerequisite_evaluation=FX["second-hop-weakness-evaluation"],
        )
        self.graph.add((FX.target, RDF.type, RAIL.SafetyCriticalAsset))
        self.graph.add((FX["safety-function"], RDF.type, CORE.SafetyFunction))
        self.graph.add((FX["safety-function"], CORE.directlyDependsOn, FX.target))
        self.graph.add((FX["safety-payload"], RDF.type, RAIL.SafetyRelatedPayload))
        self.graph.add((FX["second-hop"], CORE.carriesPayload, FX["safety-payload"]))

        l3.apply(self.graph, FX.run)

        target_path = next(
            path for path in self.graph.subjects(RDF.type, ATTACK.AttackPathResult)
            if self.graph.value(path, ATTACK.attackPathConcernsTarget) == FX.target
        )
        middle_path = next(
            path for path in self.graph.subjects(RDF.type, ATTACK.AttackPathResult)
            if self.graph.value(path, ATTACK.attackPathConcernsTarget) == FX.middle
        )
        ordering = next(self.graph.subjects(RES.producedByMethod, RULE.AttackPathOrderingMethod))
        entries = sorted(
            (
                int(self.graph.value(entry, RES.orderingPosition)),
                self.graph.value(entry, ATTACK.ranksAttackPath),
                int(self.graph.value(entry, ATTACK.attackPathSafetyImpactCount)),
                int(self.graph.value(entry, ATTACK.attackPathStepCount)),
                Decimal(str(self.graph.value(entry, ATTACK.attackPathPriorityScore))),
            )
            for entry in self.graph.objects(ordering, RES.hasOrderingEntry)
        )
        self.assertEqual(target_path, entries[0][1])
        self.assertEqual(middle_path, entries[1][1])
        self.assertGreater(entries[0][2], entries[1][2])
        self.assertLess(entries[1][3], entries[0][3])
        self.assertGreater(entries[0][4], entries[1][4])
        record = self.graph.value(ordering, RES.hasDerivationRecord)
        step = self.graph.value(record, RES.hasStep)
        self.assertEqual(RULE.AttackPathOrderingMethod, self.graph.value(step, RES.appliedComputation))
        self.assertEqual(RULE.AttackPathOrderingMechanism, self.graph.value(step, RES.executedByMechanism))
        self.assertIn(target_path, set(self.graph.objects(step, RES.usedEntity)))

        self.assertEqual([], list(self.graph.triples((None, RAIL.hasSafetyIntegrityLevel, None))))
        self.assertEqual([], list(self.graph.triples((None, RAIL.assignedSafetyIntegrityLevel, None))))


if __name__ == "__main__":
    unittest.main()
