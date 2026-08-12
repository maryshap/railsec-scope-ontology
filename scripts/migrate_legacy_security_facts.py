"""Migrate the security facts of the legacy ABox into the ETCS case.

The legacy model recorded, for each of its 88 information flows, seven
protection properties, the transmission medium and channel type, and the data
objects carried. Those are assessor decisions already taken; this script moves
them, it does not make new ones.

Two rules govern the transfer.

**Nothing is invented.** A flow is migrated only when its legacy identifier
matches a stable identifier in the case. A property absent from the legacy data
stays absent here, so the reasoning returns undetermined rather than a value
this script guessed.

**Nothing is presented as established.** Every migrated statement is an
Assumption attributed to a judgement basis recording that the legacy workbook
evidences the transfer, not the determination. This mirrors the treatment of the
safety-critical classification.

Run from the repository root:

    python3 scripts/migrate_legacy_security_facts.py path/to/legacy/ABox.ttl
"""

from __future__ import annotations

import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, URIRef, XSD


PROJECT = Path(__file__).resolve().parents[1]

LEGACY = Namespace("http://example.org/icssec#")
CASE = Namespace("https://w3id.org/railsec-scope/case/etcs/resource/")
CORE = Namespace("https://w3id.org/railsec-scope/core#")
CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RAIL = Namespace("https://w3id.org/railsec-scope/railway#")
RES = Namespace("https://w3id.org/railsec-scope/results#")
RSSO = Namespace("https://w3id.org/railsec-scope/ontology#")
PROV = Namespace("http://www.w3.org/ns/prov#")

# Legacy protection property -> the property the rules read.
PROTECTION_MAP = {
    LEGACY.hasSequenceNumber: RAIL.sequenceProtectionEnabled,
    LEGACY.hasTimeoutMechanism: RAIL.timeoutMechanismEnabled,
    LEGACY.hasSourceDestinationID: RAIL.sourceDestinationIdentifierEnabled,
    LEGACY.hasSafetyCode: RAIL.safetyCodeEnabled,
    LEGACY.hasMessageAuthentication: RAIL.authenticationEnabled,
    LEGACY.hasCryptographicProtection: RAIL.encryptionEnabled,
    LEGACY.hasIntegrityProtection: RAIL.integrityProtectionEnabled,
}


def index_by_stable_identifier(case: Graph) -> dict[str, URIRef]:
    return {str(value): subject for subject, value in case.subject_objects(RSSO.stableIdentifier)}


def boolean(value) -> bool | None:
    text = str(value).strip().lower()
    if text in {"true", "yes", "1"}:
        return True
    if text in {"false", "no", "0"}:
        return False
    return None


def migrate(legacy_path: Path) -> Graph:
    legacy = Graph().parse(legacy_path)
    case = Graph().parse(PROJECT / "cases" / "etcs" / "abox.ttl")
    index = index_by_stable_identifier(case)

    output = Graph()
    output.bind("case", CASE)
    output.bind("rss-core", CORE)
    output.bind("rss-crit", CRIT)
    output.bind("rss-rail", RAIL)
    output.bind("rss-res", RES)
    output.bind("prov", PROV)

    basis = CASE["legacy-security-fact-basis"]
    output.add((basis, RDF.type, CRIT.JudgementBasis))
    output.add((basis, CRIT.reasoning, Literal(
        "Transmission and protection facts were transferred from the legacy assessment model, "
        "where they were recorded per information flow. The legacy model evidences that these "
        "values were assessed at that time; it does not evidence them against a controlled "
        "engineering baseline, and it carried no provenance of its own. Each value is retained "
        "provisionally so that scoping can proceed, and is recorded as an assumption rather than "
        "an established fact.", lang="en")))
    output.add((basis, CRIT.revisionConditions, Literal(
        "Replace with asserted facts carrying source locations once configuration or design "
        "documentation for the deployed system is available. Re-examine any flow whose protocol "
        "or medium changes, and any value the legacy model left unstated.", lang="en")))

    counts = {"flows": 0, "protection": 0, "payload": 0,
              "payload_unclassified": 0, "skipped": 0}

    for flow in sorted(legacy.subjects(RDF.type, LEGACY.InformationFlow)):
        identifier = legacy.value(flow, LEGACY.hasId)
        if identifier is None:
            counts["skipped"] += 1
            continue
        target = index.get(str(identifier))
        if target is None:
            counts["skipped"] += 1
            continue
        counts["flows"] += 1
        local = str(identifier).replace("/", "-")

        for legacy_property, target_property in PROTECTION_MAP.items():
            raw = legacy.value(flow, legacy_property)
            if raw is None:
                continue
            value = boolean(raw)
            if value is None:
                continue
            output.add((target, target_property, Literal(value, datatype=XSD.boolean)))
            assertion = CASE[f"{local}-{target_property.split('#')[-1]}-assumption"]
            output.add((assertion, RDF.type, CORE.Assumption))
            output.add((assertion, CORE.assertionSubject, target))
            output.add((assertion, CORE.assertionPredicateIri,
                        Literal(str(target_property), datatype=XSD.anyURI)))
            output.add((assertion, CORE.assertionObjectLiteral, Literal(value, datatype=XSD.boolean)))
            output.add((assertion, CORE.hasEpistemicStatus, CORE.assumptionStatus))
            output.add((assertion, RES.assertedInInstanceSet, CASE["instance-set"]))
            output.add((assertion, PROV.wasDerivedFrom, basis))
            output.add((assertion, PROV.wasAttributedTo, CASE["assessor"]))
            counts["protection"] += 1

        # Transmission environment is deliberately not transferred.
        #
        # The legacy model recorded the medium, not whether the transmission
        # environment is under the operator's control. Deriving the second from
        # the first would be a new determination, and the model requires it to
        # be an EnvironmentControlFact carrying asserted-fact status, that is,
        # presented as established. Rather than assert as established something
        # this migration inferred, the environment is left unstated and the
        # transmission-category criteria return undetermined for every flow.
        # Resolving this needs the network design, not the legacy model.

        # Payload classification is transferred only where the legacy rule set
        # itself relied on it. The legacy critical-violation rules keyed on
        # control command and position status data, so classifying those as
        # safety-related moves an existing decision. The remaining legacy data
        # kinds were never used that way, and their absence from those rules is
        # not evidence that they are non-safety, so they are left unclassified
        # and the dependent criteria return undetermined.
        for data_object in sorted(legacy.objects(flow, LEGACY.transfersData)):
            safety_related = any(
                (data_object, RDF.type, kind) in legacy
                for kind in (LEGACY.ControlCommandData, LEGACY.PositionStatusData)
            )
            if not safety_related:
                counts["payload_unclassified"] += 1
                continue
            payload = CASE[f"payload-{str(legacy.value(data_object, LEGACY.hasId) or '').replace('/', '-')}"]
            output.add((payload, RDF.type, RAIL.SafetyRelatedPayload))
            output.add((target, CORE.carriesPayload, payload))
            counts["payload"] += 1

    print(f"flows matched         : {counts['flows']}")
    print(f"flows skipped         : {counts['skipped']}")
    print(f"protection facts      : {counts['protection']}")
    print(f"payload links         : {counts['payload']}")
    print(f"payload left unclassified: {counts['payload_unclassified']}")
    return output


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    legacy_path = Path(sys.argv[1])
    if not legacy_path.exists():
        print(f"legacy file not found: {legacy_path}")
        return 1
    graph = migrate(legacy_path)
    destination = PROJECT / "cases" / "etcs" / "security-facts.ttl"
    graph.serialize(destination=str(destination), format="turtle")
    print(f"\nwritten: {destination.relative_to(PROJECT)} ({len(graph)} triples)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
