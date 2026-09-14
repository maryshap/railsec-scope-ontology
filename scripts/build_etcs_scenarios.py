"""Build deterministic ETCS scenario files that are derived from case facts."""

from __future__ import annotations

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
    }

    copy_scenario_pair("missing-safety-code", "missing-corruption-protection")
    copy_scenario_pair("protected-baseline", "unknown-data")
    copy_scenario_pair("missing-safety-code", "combined-degradation")
    for scenario, (reasoning, overrides, omitted) in scenarios.items():
        destination = SCENARIOS / scenario / "threat-controls.ttl"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            threat_controls_text(scenario, reasoning, overrides, omitted),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
