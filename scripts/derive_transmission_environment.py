"""Derive the three transmission environment facts for the ETCS case.

EN 50159 classifies a transmission system by three conditions: whether the
transmission environment is under the operator's control, whether the set of
participants is fixed, and whether unauthorised access can be excluded. The
source model did not record these directly. It recorded the physical medium and
an exposure rating, from which the assessor derived the category inside the
legacy rules.

This script makes that derivation explicit and inspectable instead of leaving it
buried in a rule. The rule applied is stated once here, recorded as an assessor
judgement, and attached to every fact it produces:

  environment controlled      wired medium, and exposure not High or Very High
  participant set fixed       wired medium
  unauthorised access excluded  wired medium, and exposure Low

Anything not clearly wired, or carrying a mixed medium, yields no fact at all
rather than a guessed one, so those flows stay undetermined.

Run from the repository root:

    python3 scripts/derive_transmission_environment.py path/to/Ontology_model.xlsx
"""

from __future__ import annotations

import sys
from pathlib import Path

import openpyxl
from rdflib import Graph, Literal, Namespace, RDF, XSD


PROJECT = Path(__file__).resolve().parents[1]

CASE = Namespace("https://w3id.org/railsec-scope/case/etcs/resource/")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RSSO = Namespace("https://w3id.org/railsec-scope/ontology#")
PROV = Namespace("http://www.w3.org/ns/prov#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")

WIRED_MARKERS = ("wired", "lan", "ethernet", "bbip", "sdh", "cable", "bus", "telecom", "lst-")
MIXED_MARKERS = ("+", "/", "radio", "rf", "human", "eurobalise", "euroloop", "remote")
OPEN_EXPOSURE = {"high", "very high", "medium–high", "medium-high"}


def classify(medium: str, exposure: str) -> dict[str, bool] | None:
    """Return the three conditions, or None where the medium is not clearly wired."""
    text = (medium or "").strip().lower()
    level = (exposure or "").strip().lower()
    if not text or text == "none":
        return None
    if any(marker in text for marker in MIXED_MARKERS):
        return None
    if not any(marker in text for marker in WIRED_MARKERS):
        return None
    return {
        "environment": level not in OPEN_EXPOSURE,
        "participants": True,
        "access": level == "low",
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    workbook_path = Path(sys.argv[1])
    if not workbook_path.exists():
        print(f"workbook not found: {workbook_path}")
        return 1

    workbook = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
    sheet = workbook["Interfaces_Flat"]
    rows = list(sheet.iter_rows(values_only=True))
    columns = {header: index for index, header in enumerate(rows[0]) if header}

    case = Graph().parse(PROJECT / "cases" / "etcs" / "abox.ttl")
    index = {str(value): subject for subject, value in case.subject_objects(RSSO.stableIdentifier)}

    output = Graph()
    for prefix, namespace in (("case", CASE), ("rss-core", CORE), ("rss-crit", CRIT),
                              ("rss-rail", RAIL), ("rss-res", RES), ("prov", PROV)):
        output.bind(prefix, namespace)

    # The dataset must declare every module whose terms it uses, or the OWL 2 DL
    # profile check reports them as undeclared. assessment pulls in results,
    # which owns assertedInInstanceSet; railway owns the transmission facts.
    dataset = Namespace("https://w3id.org/railsec-scope/case/etcs/")["transmission-environment"]
    root = Namespace("https://w3id.org/railsec-scope/")
    output.add((dataset, RDF.type, OWL.Ontology))
    output.add((dataset, OWL.imports, root["assessment"]))
    output.add((dataset, OWL.imports, root["railway"]))
    output.add((dataset, OWL.versionIRI,
                Namespace("https://w3id.org/railsec-scope/case/etcs/transmission-environment/")["version/0.1.0"]))

    basis = CASE["transmission-environment-basis"]
    output.add((basis, RDF.type, CRIT.JudgementBasis))
    output.add((basis, CRIT.reasoning, Literal(
        "The source model records the physical medium and an exposure rating, not the three "
        "conditions EN 50159 uses to classify a transmission system. The assessor applies the "
        "following rule: a clearly wired medium places the participant set under the operator's "
        "control; the same medium keeps the transmission environment controlled unless exposure "
        "is rated high; and unauthorised access is excluded only where exposure is rated low. "
        "Flows whose medium is radio, mixed, human or otherwise not clearly wired receive no "
        "fact, so their category stays undetermined rather than being guessed. This rule is a "
        "judgement about a study case, not evidence about a deployed system.", lang="en")))
    output.add((basis, CRIT.revisionConditions, Literal(
        "Replace with asserted facts from the network design and physical security assessment of "
        "the specific installation. Re-examine every flow whose exposure rating changes, and any "
        "flow left without a fact.", lang="en")))

    counts = {"matched": 0, "skipped": 0, "facts": 0}
    for row in rows[1:]:
        identifier = row[columns["IF-ID"]]
        if not identifier:
            continue
        # A workbook row describes an interface; the case represents each
        # interface as a forward and a reverse flow. The medium and exposure
        # apply to both directions, so the facts attach to both.
        base = str(identifier).strip()
        targets = [index[key] for key in (f"{base}-forward", f"{base}-reverse") if key in index]
        if not targets:
            counts["skipped"] += 1
            continue
        for target in targets:
            # L1 control facts, taken directly from the workbook columns. These are
            # recorded values, not derivations, so they are written as flow
            # properties with an accompanying assumption for provenance.
            medium_text = str(row[columns["Medium"]] or "").lower()
            wireless = any(marker in medium_text for marker in ("radio", "rf", "wireless", "gsm-r", "eurobalise", "euroloop"))
            crosses = str(row[columns["Zones"]] or "").count("→") > 0 or "-" in str(row[columns["Zones"]] or "")
            for column, control_property in (
                ("hasRateLimiting", RAIL.rateLimitingEnabled),
                ("hasMonitoringAndLogging", RAIL.monitoringEnabled),
                ("hasNetworkSegmentation", RAIL.networkSegmentationEnabled),
            ):
                raw = row[columns[column]] if column in columns else None
                if raw is None or str(raw).strip() == "":
                    continue
                output.add((target, control_property, Literal(str(raw).strip().lower() == "true", datatype=XSD.boolean)))
                counts["l1"] = counts.get("l1", 0) + 1
            output.add((target, RAIL.wirelessMedium, Literal(wireless, datatype=XSD.boolean)))
            output.add((target, RAIL.crossesTrustBoundary, Literal(crosses, datatype=XSD.boolean)))

        verdict = classify(str(row[columns["Medium"]] or ""), str(row[columns["Exposure"]] or ""))
        if verdict is None:
            counts["skipped"] += 1
            continue
        counts["matched"] += 1

        for target in targets:
          local = str(target).rsplit("/", 1)[-1]
          for suffix, kind, value_property, value in (
            ("environment-control", RAIL.EnvironmentControlFact,
             RAIL.environmentControlledValue, verdict["environment"]),
            ("participant-set", RAIL.ParticipantSetFixedFact,
             RAIL.participantSetFixedValue, verdict["participants"]),
            ("access-exclusion", RAIL.UnauthorisedAccessExclusionAssumption,
             RAIL.unauthorisedAccessExcludedValue, verdict["access"]),
          ):
            fact = CASE[f"{local}-{suffix}"]
            output.add((fact, RDF.type, kind))
            output.add((fact, RAIL.transmissionAssertionSubject, target))
            output.add((fact, value_property, Literal(value, datatype=XSD.boolean)))
            # The two Fact classes require asserted-fact status; the assumption
            # class carries assumption status. The judgement that produced all
            # three is recorded on each of them either way.
            status = (CORE.assumptionStatus if kind == RAIL.UnauthorisedAccessExclusionAssumption
                      else CORE.assertedFactStatus)
            output.add((fact, CORE.hasEpistemicStatus, status))
            output.add((fact, RES.assertedInInstanceSet, CASE["instance-set"]))
            output.add((fact, PROV.wasDerivedFrom, basis))
            output.add((fact, PROV.wasAttributedTo, CASE["assessor"]))
            counts["facts"] += 1

    print(f"flows given facts : {counts['matched']}")
    print(f"flows left unstated: {counts['skipped']}")
    print(f"facts written      : {counts['facts']}")
    destination = PROJECT / "cases" / "etcs" / "transmission-environment.ttl"
    destination.write_text(output.serialize(format="turtle"), encoding="utf-8")
    print(f"\nwritten: {destination.relative_to(PROJECT)} ({len(output)} triples)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
