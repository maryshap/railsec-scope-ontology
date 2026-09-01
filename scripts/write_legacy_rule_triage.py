"""One-time generator for the explicit 54-rule migration decision matrix."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT.parent / "legacy_snapshot" / "railway-security-ontology" / "rules_generator.py"
OUTPUT = PROJECT / "migration" / "legacy-rule-triage.csv"

IMPLEMENTED = {
    "R1.1.1", "R1.1.2", "R1.1.3", "R1.1.4", "R1.1.5",
    "R1.1.6",
    "R1.2.1", "R1.2.2",
    "R2.1.1", "R2.1.2", "R2.1.3",
    "R2.1.4",
    "R2.2.1", "R2.2.2", "R2.2.3", "R2.2.4", "R2.2.5", "R2.2.6", "R2.2.7",
    "R2.3.1", "R2.3.2", "R2.3.3", "R2.3.4",
    "R2.4.1", "R2.4.2", "R2.4.3",
    "R2.5.3",
    "R2.6.1", "R2.6.2", "R2.6.3", "R2.6.4",
    "R4.1.1", "R4.1.2",
}

IMPLEMENT_NOW = set()

FUTURE_L3 = {"R2.5.1", "R2.5.2", "R4.1.4"}
FUTURE_COMPUTATION = {"R1.3.1", "R4.2.1", "R4.2.2", "R4.3.1", "R4.3.2", "R4.3.3a", "R4.3.3b", "R4.3.4", "R4.3.5"}
RETIRED_OR_OUT_OF_SCOPE = {"R1.0.1", "R1.4.1", "R1.4.2", "R1.4.3", "R1.4.4", "R1.4.5", "R1.4.6", "R1.5.1", "R1.5.2"}


def load_rules():
    spec = importlib.util.spec_from_file_location("legacy_rules", SOURCE)
    if spec is None or spec.loader is None: raise RuntimeError(f"Cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_layer1_rules() + module.get_layer2_rules() + module.get_layer4_rules()


def decision(rule):
    if rule.id in IMPLEMENTED:
        return "implemented", "M5/RBox implemented criterion or computation", "Covered by the Phase 2 RSSO criteria/rule pipeline; legacy predicate names are not retained."
    if rule.id in IMPLEMENT_NOW:
        return "implement-now", "Ontology-complete gap closure", "Clean source and small vocabulary delta; implement as sourced criterion/vocabulary before declaring ontology complete."
    if rule.id in FUTURE_L3:
        return "future-version", "L3/ATT&CK layer", "Normatively plausible, but semantically belongs to the future ATT&CK/L3 technique layer rather than Phase 2 L1/L2 criteria."
    if rule.id in FUTURE_COMPUTATION:
        return "future-version", "External computation / ordering follow-up", "Requires reachability closure, numeric comparison, or ordering computation; do not encode as a simple DL/SPARQL criterion."
    if rule.id in RETIRED_OR_OUT_OF_SCOPE:
        return "retire-or-out-of-scope", "Not admitted as a Phase 2 ontology rule", "Outside the approved standards scope, duplicated by admitted railway threat taxonomy, or better handled as ETL/provenance enrichment."
    if rule.id == "R1.0.1":
        return "refactor", "M6 import mapping", "Move inherited-zone enrichment to explicit ETL assertions with provenance."
    if rule.id.startswith("R4.2"):
        return "refactor", "L3 ReachabilityResult computation", "Path closure is external computation; L1/L2 may consume its declared results."
    if rule.id.startswith("R4.3"):
        return "refactor", "M2 OrderingFactor + M3 FactorValue", "Replace hard-coded score classes with versioned factors, values and ordering evidence."
    if rule.id == "R1.3.1":
        return "refactor", "M5 criterion over declared comparison input", "Numeric comparison must use a declared evaluator/computation and materialised input."
    if rule.id.startswith("R4.1"):
        return "map", "M5 EntryPoint criterion", "Retain classification intent as a versioned DL-safe M5 criterion."
    if rule.id.startswith("R2."):
        return "map", "M5 railway criterion", "Map the railway intent; rewrite against RSSO terms and complete source/interpretation records."
    return "map", "M5 ICS-security criterion", "Map the generic security intent into the extension; do not copy legacy predicates or source comments."


def review_status(rule_id: str, action: str) -> str:
    if action == "implemented":
        return "implemented-source-recorded"
    if action == "implement-now":
        return "source-identified-open-implementation"
    if rule_id in RETIRED_OR_OUT_OF_SCOPE:
        return "triaged-not-admitted"
    return "triaged-deferred"


def main() -> int:
    rules = load_rules()
    if len(rules) != 54: raise RuntimeError(f"Expected 54 rules, found {len(rules)}")
    classified = IMPLEMENTED | IMPLEMENT_NOW | FUTURE_L3 | FUTURE_COMPUTATION | RETIRED_OR_OUT_OF_SCOPE
    seen = {rule.id for rule in rules}
    missing = sorted(classified - seen)
    if missing: raise RuntimeError(f"Classified rules not found in legacy generator: {missing}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["legacy_rule", "legacy_layer", "decision", "target", "description", "claimed_source", "head_predicates", "rationale", "review_status"])
        for rule in rules:
            action, target, rationale = decision(rule)
            writer.writerow([rule.id, rule.layer.name, action, target, rule.description, rule.standard_source, ",".join(atom.predicate for atom in rule.head), rationale, review_status(rule.id, action)])
    return 0


if __name__ == "__main__": raise SystemExit(main())
