"""One-time generator for the explicit 54-rule migration decision matrix."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT.parent / "legacy_snapshot" / "railway-security-ontology" / "rules_generator.py"
OUTPUT = PROJECT / "migration" / "legacy-rule-triage.csv"


def load_rules():
    spec = importlib.util.spec_from_file_location("legacy_rules", SOURCE)
    if spec is None or spec.loader is None: raise RuntimeError(f"Cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_layer1_rules() + module.get_layer2_rules() + module.get_layer4_rules()


def decision(rule):
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


def main() -> int:
    rules = load_rules()
    if len(rules) != 54: raise RuntimeError(f"Expected 54 rules, found {len(rules)}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["legacy_rule", "legacy_layer", "decision", "target", "description", "claimed_source", "head_predicates", "rationale", "review_status"])
        for rule in rules:
            action, target, rationale = decision(rule)
            writer.writerow([rule.id, rule.layer.name, action, target, rule.description, rule.standard_source, ",".join(atom.predicate for atom in rule.head), rationale, "domain-review-required"])
    return 0


if __name__ == "__main__": raise SystemExit(main())
