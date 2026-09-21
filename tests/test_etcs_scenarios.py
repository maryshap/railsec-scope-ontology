from __future__ import annotations

import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, XSD


PROJECT = Path(__file__).resolve().parents[1]
CASE_DIR = PROJECT / "cases" / "etcs"
SCENARIOS = CASE_DIR / "scenarios"
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
CASE = Namespace("https://w3id.org/railsec-scope/case/etcs/resource/")
RUN = Namespace("https://w3id.org/railsec-scope/run/")

AGGREGATE_CONTROLS = (
    RAIL.authenticationEnabled,
    RAIL.encryptionEnabled,
    RAIL.integrityProtectionEnabled,
    RAIL.safetyCodeEnabled,
    RAIL.sequenceProtectionEnabled,
    RAIL.sourceDestinationIdentifierEnabled,
    RAIL.timeoutMechanismEnabled,
)
DETAILED_CONTROLS = (
    RAIL.sequenceNumberEnabled,
    RAIL.timestampEnabled,
    RAIL.feedbackMessageEnabled,
    RAIL.identificationProcedureEnabled,
    RAIL.cryptographicMessageProtectionEnabled,
)
CONTROLS = AGGREGATE_CONTROLS + DETAILED_CONTROLS


def scenario_graph(name: str) -> Graph:
    graph = Graph()
    for filename in ("security-facts.ttl", "transmission-environment.ttl", "threat-controls.ttl"):
        graph.parse(SCENARIOS / name / filename)
    access_assumptions = SCENARIOS / name / "access-assumptions.ttl"
    if access_assumptions.exists():
        graph.parse(access_assumptions)
    return graph


def control_matrix(graph: Graph, flows: set) -> dict[tuple, frozenset]:
    return {
        (flow, control): frozenset(graph.objects(flow, control))
        for flow in flows
        for control in CONTROLS
    }


class EtcsScenarioContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        architecture = Graph().parse(CASE_DIR / "abox.ttl")
        cls.flows = set(architecture.subjects(RDF.type, RAIL.RailwayInformationFlow))
        cls.graphs = {
            name: scenario_graph(name)
            for name in (
                "protected-baseline",
                "missing-safety-code",
                "missing-corruption-protection",
                "unknown-data",
                "combined-degradation",
                "controlled-remote-attack-path",
            )
        }

    def test_representative_architecture_contains_148_directed_flows(self) -> None:
        self.assertEqual(148, len(self.flows))

    def test_protected_baseline_fully_states_all_rule_inputs(self) -> None:
        graph = self.graphs["protected-baseline"]
        for flow in self.flows:
            for control in CONTROLS:
                with self.subTest(flow=str(flow).split("/")[-1], control=str(control).split("#")[-1]):
                    self.assertEqual({True}, {value.toPython() for value in graph.objects(flow, control)})

    def test_each_controlled_scenario_has_only_its_preregistered_delta(self) -> None:
        baseline = control_matrix(self.graphs["protected-baseline"], self.flows)
        target = CASE["flow-if-ts-06-forward"]
        expected = {
            "missing-safety-code": {(target, RAIL.safetyCodeEnabled)},
            "missing-corruption-protection": {
                (target, RAIL.safetyCodeEnabled),
                (target, RAIL.cryptographicMessageProtectionEnabled),
            },
            "unknown-data": {(target, RAIL.sequenceNumberEnabled)},
            "combined-degradation": {
                (target, RAIL.safetyCodeEnabled),
                (target, RAIL.cryptographicMessageProtectionEnabled),
                (CASE["flow-if-ts-03-forward"], RAIL.sequenceNumberEnabled),
                (CASE["flow-if-ts-03-forward"], RAIL.timestampEnabled),
            },
            "controlled-remote-attack-path": {
                (CASE["flow-if-it-10-forward"], RAIL.encryptionEnabled),
            },
        }
        for name, expected_delta in expected.items():
            actual = control_matrix(self.graphs[name], self.flows)
            delta = {key for key in baseline if baseline[key] != actual[key]}
            with self.subTest(scenario=name):
                self.assertEqual(expected_delta, delta)

    def test_missing_corruption_scenario_explicitly_disables_both_alternatives(self) -> None:
        graph = self.graphs["missing-corruption-protection"]
        target = CASE["flow-if-ts-06-forward"]
        self.assertEqual(False, graph.value(target, RAIL.safetyCodeEnabled).toPython())
        self.assertEqual(False, graph.value(target, RAIL.cryptographicMessageProtectionEnabled).toPython())

    def test_unknown_scenario_omits_evidence_instead_of_asserting_false(self) -> None:
        graph = self.graphs["unknown-data"]
        target = CASE["flow-if-ts-06-forward"]
        self.assertEqual([], list(graph.objects(target, RAIL.sequenceNumberEnabled)))
        self.assertEqual(True, graph.value(target, RAIL.timestampEnabled).toPython())

    def test_no_scenario_asserts_conflicting_functional_control_values(self) -> None:
        for name, graph in self.graphs.items():
            for flow in self.flows:
                for control in CONTROLS:
                    with self.subTest(scenario=name, flow=str(flow), control=str(control)):
                        self.assertLessEqual(len(set(graph.objects(flow, control))), 1)

    def test_controlled_attack_path_assumptions_are_explicit_and_minimal(self) -> None:
        graph = self.graphs["controlled-remote-attack-path"]
        entry = CASE["asset-it-01"]
        target_flow = CASE["flow-if-it-10-forward"]
        remote_access = RAIL.RemoteAccess
        self.assertEqual({remote_access}, set(graph.objects(entry, CORE.reachableBy)))
        self.assertEqual(False, graph.value(target_flow, RAIL.encryptionEnabled).toPython())
        assumptions = {
            subject
            for subject in graph.subjects(RDF.type, CORE.Assumption)
            if graph.value(subject, CORE.assertionSubject) in {entry, target_flow}
            and graph.value(subject, CORE.assertionPredicateIri) in {
                Literal("https://w3id.org/railsec-scope/core#reachableBy", datatype=XSD.anyURI),
                Literal(str(RAIL.encryptionEnabled), datatype=XSD.anyURI),
            }
        }
        self.assertEqual(2, len(assumptions))


class EtcsScenarioBehaviourTest(unittest.TestCase):
    """Execute the relevant L2 slice on real ETCS scenario inputs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.results = {
            name: cls.run_transmission_slice(name)
            for name in (
                "protected-baseline",
                "missing-safety-code",
                "missing-corruption-protection",
                "unknown-data",
                "combined-degradation",
                "controlled-remote-attack-path",
            )
        }

    @staticmethod
    def run_transmission_slice(name: str) -> tuple[Graph, object]:
        graph = Graph()
        for module in sorted((PROJECT / "ontology").glob("*.ttl")):
            graph.parse(module)
        graph.parse(PROJECT / "imports" / "prov-o-dl.ttl")
        graph.parse(PROJECT / "rules" / "rules.ttl")
        graph.parse(CASE_DIR / "abox.ttl")
        graph.parse(CASE_DIR / "classification-provenance.ttl")
        for filename in ("security-facts.ttl", "transmission-environment.ttl", "threat-controls.ttl"):
            graph.parse(SCENARIOS / name / filename)
        run = RUN[f"scenario-contract-{name}"]
        graph.add((run, RDF.type, RES.Run))
        graph.add((run, RES.runIdentifier, Literal(f"scenario-contract-{name}")))
        graph.add((run, RES.usedInstanceSet, CASE["instance-set"]))
        for filename in (
            "evaluate-transmission-category.rq",
            "classify-transmission-category.rq",
            "evaluate-transmission-threat.rq",
            "evaluate-critical-violation.rq",
            "evaluate-control-weakness.rq",
        ):
            query = (PROJECT / "rules" / filename).read_text(encoding="utf-8")
            graph += graph.query(query, initBindings={"run": run}).graph
        return graph, run

    @staticmethod
    def outcome(graph: Graph, run, flow, criterion):
        evaluations = [
            evaluation
            for evaluation in graph.subjects(RES.evaluationConcernsElement, flow)
            if graph.value(evaluation, RES.producedByRun) == run
            and graph.value(evaluation, RES.evaluatesCriterion) == criterion
        ]
        if len(evaluations) != 1:
            raise AssertionError(f"expected one evaluation, found {len(evaluations)}")
        return graph.value(evaluations[0], RES.hasEvaluationOutcome)

    def test_protected_baseline_has_no_satisfied_transmission_threat(self) -> None:
        graph, run = self.results["protected-baseline"]
        outcomes = {
            graph.value(evaluation, RES.hasEvaluationOutcome)
            for evaluation in graph.subjects(RDF.type, RES.CriterionEvaluation)
            if graph.value(evaluation, RES.producedByRun) == run
            and str(graph.value(evaluation, RES.evaluatesCriterion)).startswith(
                "https://w3id.org/railsec-scope/criteria/railway/threat-"
            )
        }
        self.assertEqual({RES.notSatisfied}, outcomes)

    def test_missing_safety_code_is_blocked_by_the_explicit_alternative(self) -> None:
        graph, run = self.results["missing-safety-code"]
        self.assertEqual(
            RES.notSatisfied,
            self.outcome(
                graph,
                run,
                CASE["flow-if-ts-06-forward"],
                Namespace("https://w3id.org/railsec-scope/criteria/railway/")["threat-corruption-criterion"],
            ),
        )

    def test_missing_all_corruption_protection_reaches_critical_integrity(self) -> None:
        graph, run = self.results["missing-corruption-protection"]
        criteria = Namespace("https://w3id.org/railsec-scope/criteria/railway/")
        target = CASE["flow-if-ts-06-forward"]
        self.assertEqual(RES.satisfied, self.outcome(graph, run, target, criteria["threat-corruption-criterion"]))
        self.assertEqual(RES.satisfied, self.outcome(graph, run, target, criteria["critical-integrity-criterion"]))

    def test_absent_sequence_number_evidence_is_undetermined(self) -> None:
        graph, run = self.results["unknown-data"]
        criterion = Namespace("https://w3id.org/railsec-scope/criteria/railway/")["threat-deletion-criterion"]
        self.assertEqual(
            RES.undetermined,
            self.outcome(graph, run, CASE["flow-if-ts-06-forward"], criterion),
        )

    def test_combined_scenario_retains_independent_threat_chains(self) -> None:
        graph, run = self.results["combined-degradation"]
        criteria = Namespace("https://w3id.org/railsec-scope/criteria/railway/")
        corruption_flow = CASE["flow-if-ts-06-forward"]
        sequence_flow = CASE["flow-if-ts-03-forward"]
        for criterion_name in (
            "threat-repetition-criterion",
            "threat-deletion-criterion",
            "threat-resequencing-criterion",
        ):
            with self.subTest(criterion=criterion_name):
                self.assertEqual(
                    RES.satisfied,
                    self.outcome(graph, run, sequence_flow, criteria[criterion_name]),
                )
        self.assertEqual(
            RES.satisfied,
            self.outcome(graph, run, corruption_flow, criteria["critical-integrity-criterion"]),
        )
        self.assertEqual(
            RES.undetermined,
            self.outcome(graph, run, sequence_flow, criteria["critical-sequence-criterion"]),
        )

    def test_controlled_attack_path_has_its_l3_confidentiality_prerequisite(self) -> None:
        graph, run = self.results["controlled-remote-attack-path"]
        self.assertEqual(
            RES.satisfied,
            self.outcome(
                graph,
                run,
                CASE["flow-if-it-10-forward"],
                Namespace("https://w3id.org/railsec-scope/criteria/railway/")[
                    "l1-confidentiality-criterion"
                ],
            ),
        )


if __name__ == "__main__":
    unittest.main()
