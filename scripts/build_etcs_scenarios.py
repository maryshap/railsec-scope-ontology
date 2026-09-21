"""Build deterministic ETCS scenario files that are derived from case facts."""

from __future__ import annotations

import re
from pathlib import Path

from rdflib import Graph, Namespace, RDF


PROJECT = Path(__file__).resolve().parents[1]
CASE_DIR = PROJECT / "cases" / "etcs"
SCENARIOS = CASE_DIR / "scenarios"
CORE = Namespace("https://w3id.org/railsec-scope/core#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")

DETAILED_THREAT_CONTROLS = (
    "sequenceNumberEnabled",
    "timestampEnabled",
    "feedbackMessageEnabled",
    "identificationProcedureEnabled",
    "cryptographicMessageProtectionEnabled",
)


def flow_ids() -> list[str]:
    graph = Graph().parse(CASE_DIR / "abox.ttl")
    return sorted(
        str(flow).split("#")[-1].split("/")[-1]
        for flow in graph.subjects(RDF.type, RAIL.RailwayInformationFlow)
    )


def threat_controls_text(
    scenario: str,
    reasoning: str,
    overrides: dict[tuple[str, str], bool] | None = None,
    omitted: set[tuple[str, str]] | None = None,
) -> str:
    overrides = overrides or {}
    omitted = omitted or set()
    basis = f"scenario-{scenario}-threat-control-basis"
    blocks = [
        "@prefix case: <https://w3id.org/railsec-scope/case/etcs/resource/> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "@prefix rss-core: <https://w3id.org/railsec-scope/core#> .",
        "@prefix rss-crit: <https://w3id.org/railsec-scope/criteria#> .",
        "@prefix rss-rail: <https://w3id.org/railsec-scope/railway#> .",
        "@prefix rss-res: <https://w3id.org/railsec-scope/results#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        f"<https://w3id.org/railsec-scope/case/etcs/scenario/{scenario}/threat-controls> a owl:Ontology ;",
        "    owl:imports <https://w3id.org/railsec-scope/assessment>,",
        "        <https://w3id.org/railsec-scope/railway> ;",
        f"    owl:versionIRI <https://w3id.org/railsec-scope/case/etcs/scenario/{scenario}/threat-controls/version/0.1.0> .",
        "",
        f"case:{basis} a rss-crit:JudgementBasis ;",
        f'    rss-crit:reasoning "{reasoning}"@en ;',
        '    rss-crit:revisionConditions "Scenario assumption only; never promote to deployment evidence without an independent source."@en .',
        "",
    ]

    for flow in flow_ids():
        values = [
            (prop, overrides.get((flow, prop), True))
            for prop in DETAILED_THREAT_CONTROLS
            if (flow, prop) not in omitted
        ]
        if values:
            blocks.append(f"case:{flow}")
            for index, (prop, value) in enumerate(values):
                punctuation = " ." if index == len(values) - 1 else " ;"
                blocks.append(f"    rss-rail:{prop} {str(value).lower()}{punctuation}")
            blocks.append("")
        for prop, value in values:
            blocks += [
                f"case:{flow}-{prop}-{scenario}-assumption a rss-core:Assumption ;",
                "    prov:wasAttributedTo case:assessor ;",
                f"    prov:wasDerivedFrom case:{basis} ;",
                f"    rss-core:assertionObjectLiteral {str(value).lower()} ;",
                f'    rss-core:assertionPredicateIri "{RAIL[prop]}"^^xsd:anyURI ;',
                f"    rss-core:assertionSubject case:{flow} ;",
                "    rss-core:hasEpistemicStatus rss-core:assumptionStatus ;",
                "    rss-res:assertedInInstanceSet case:instance-set .",
                "",
            ]
    return "\n".join(blocks)


def copy_scenario_pair(source: str, target: str) -> None:
    target_dir = SCENARIOS / target
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in ("security-facts.ttl", "transmission-environment.ttl"):
        text = (SCENARIOS / source / name).read_text(encoding="utf-8")
        text = text.replace(f"scenario/{source}/", f"scenario/{target}/")
        (target_dir / name).write_text(text, encoding="utf-8")


def build_controlled_remote_attack_path() -> None:
    """Build the minimal counterfactual needed to exercise an ETCS L3 path."""
    scenario = "controlled-remote-attack-path"
    flow = "flow-if-it-10-forward"
    basis = "scenario-controlled-remote-attack-path-basis"
    copy_scenario_pair("protected-baseline", scenario)

    destination = SCENARIOS / scenario / "security-facts.ttl"
    text = destination.read_text(encoding="utf-8")

    direct_pattern = re.compile(
        rf"(case:{flow} rss-rail:authenticationEnabled true ;\n"
        rf"    rss-rail:encryptionEnabled )true( ;\n)"
    )
    text, direct_count = direct_pattern.subn(r"\1false\2", text)

    assertion_pattern = re.compile(
        rf"(case:{flow}-encryptionEnabled-protected-assumption a rss-core:Assumption ;\n"
        rf"    prov:wasAttributedTo case:assessor ;\n"
        rf"    prov:wasDerivedFrom )case:scenario-protected-baseline-basis( ;\n"
        rf"    rss-core:assertionObjectLiteral )true( ;)"
    )
    text, assertion_count = assertion_pattern.subn(
        rf"case:{flow}-encryptionEnabled-{scenario}-assumption a rss-core:Assumption ;\n"
        rf"    prov:wasAttributedTo case:assessor ;\n"
        rf"    prov:wasDerivedFrom case:{basis}\2false\3",
        text,
    )
    if direct_count != 1 or assertion_count != 1:
        raise RuntimeError(
            "controlled attack-path aggregate override did not match exactly once: "
            f"direct={direct_count}, assertion={assertion_count}"
        )
    destination.write_text(text, encoding="utf-8")

    access = f"""@prefix case: <https://w3id.org/railsec-scope/case/etcs/resource/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rss-core: <https://w3id.org/railsec-scope/core#> .
@prefix rss-crit: <https://w3id.org/railsec-scope/criteria#> .
@prefix rss-rail: <https://w3id.org/railsec-scope/railway#> .
@prefix rss-res: <https://w3id.org/railsec-scope/results#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://w3id.org/railsec-scope/case/etcs/scenario/{scenario}/access-assumptions> a owl:Ontology ;
    owl:imports <https://w3id.org/railsec-scope/assessment>,
        <https://w3id.org/railsec-scope/railway> ;
    owl:versionIRI <https://w3id.org/railsec-scope/case/etcs/scenario/{scenario}/access-assumptions/version/0.1.0> .

case:{basis} a rss-crit:JudgementBasis ;
    rss-crit:reasoning "Controlled counterfactual for exercising the L3 attack-path computation: NG-FW (IT-01) is assumed reachable through remote access, and encryption is assumed absent only on directed flow IF-IT-10-forward from NG-FW to RBC. Neither statement is deployment evidence. All other protection values remain those of the protected baseline."@en ;
    rss-crit:revisionConditions "Replace or reject each assumption independently when controlled architecture, remote-access configuration or interface-security evidence becomes available. Never promote this scenario basis to a fact about the deployed ETCS system."@en .

case:asset-it-01 rss-core:reachableBy rss-rail:RemoteAccess .

case:asset-it-01-remote-access-{scenario}-assumption a rss-core:Assumption ;
    rdfs:label "Controlled remote-access assumption for NG-FW"@en ;
    prov:wasAttributedTo case:assessor ;
    prov:wasDerivedFrom case:{basis} ;
    rss-core:assertionObjectResource rss-rail:RemoteAccess ;
    rss-core:assertionPredicateIri "https://w3id.org/railsec-scope/core#reachableBy"^^xsd:anyURI ;
    rss-core:assertionSubject case:asset-it-01 ;
    rss-core:hasEpistemicStatus rss-core:assumptionStatus ;
    rss-res:assertedInInstanceSet case:instance-set .
"""
    (SCENARIOS / scenario / "access-assumptions.ttl").write_text(access, encoding="utf-8")


def main() -> None:
    scenarios = {
        "protected-baseline": (
            "Idealised baseline: every detailed EN 50159 Table 1 protection input is assumed true.",
            {},
            set(),
        ),
        "missing-safety-code": (
            "All detailed EN 50159 alternatives remain true; the separate security-facts file removes only the safety code.",
            {},
            set(),
        ),
        "missing-corruption-protection": (
            "The safety code is false in security-facts and the alternative cryptographic message protection is also assumed false for flow-if-ts-06-forward.",
            {("flow-if-ts-06-forward", "cryptographicMessageProtectionEnabled"): False},
            set(),
        ),
        "unknown-data": (
            "Idealised controls are retained except that sequence-number evidence is deliberately absent for one flow.",
            {},
            {("flow-if-ts-06-forward", "sequenceNumberEnabled")},
        ),
        "combined-degradation": (
            "Two independent degradations: all corruption alternatives are false on flow-if-ts-06-forward, while sequence number and timestamp are false on flow-if-ts-03-forward.",
            {
                ("flow-if-ts-06-forward", "cryptographicMessageProtectionEnabled"): False,
                ("flow-if-ts-03-forward", "sequenceNumberEnabled"): False,
                ("flow-if-ts-03-forward", "timestampEnabled"): False,
            },
            set(),
        ),
        "controlled-remote-attack-path": (
            "All detailed EN 50159 controls remain true; the separate security-facts and access-assumptions files introduce only the two pre-registered L3 counterfactuals.",
            {},
            set(),
        ),
    }

    copy_scenario_pair("missing-safety-code", "missing-corruption-protection")
    copy_scenario_pair("protected-baseline", "unknown-data")
    copy_scenario_pair("missing-safety-code", "combined-degradation")
    build_controlled_remote_attack_path()
    for scenario, (reasoning, overrides, omitted) in scenarios.items():
        destination = SCENARIOS / scenario / "threat-controls.ttl"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            threat_controls_text(scenario, reasoning, overrides, omitted),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
