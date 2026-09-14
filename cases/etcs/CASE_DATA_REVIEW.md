# ETCS source and data review

## Review boundary

This review concerns the case-specific ETCS evidence graphs. It does not reopen
the L1-L3 ontology design and does not promote a missing fact to `false`.

The current architecture inventory contains 14 zones, 92 railway assets, 88
interfaces, 148 directed information flows and 29 functions. Its dataset-level
source is `Ontology_model.xlsx`, recorded in `abox.ttl` by SHA-256 digest. The
field admission policy is retained in `mapping.csv` and `unmapped.csv`.

The deployment/configuration identifier, architecture-document editions and
observation date have not yet been frozen in a case evidence register. Until
that is done, this is a reconstructed reference architecture rather than a
claim about one operational deployment at a stated date.

## Evidence disposition

| Evidence family | Current state | Decision |
|---|---|---|
| Architecture inventory | structurally present and mapped | retain; freeze source editions and case boundary |
| Boundary assertions | present at dataset level | review the workbook-derived transformation and record its scope |
| Safety-critical classifications | nine provisional assessor judgements with provenance | retain as assumptions until a safety case or hazard analysis is available |
| Security controls | migrated, predominantly assessor-status observations | retain; do not describe them as measured deployment controls without source review |
| Transmission environment | asserted and assessor-status inputs coexist | retain epistemic status and report its effect on evaluations |
| Safety-related payload direction | two links resolved; three remain ambiguous | acquire directional evidence or preserve as unresolved |
| Safety functions | present; implementation links are available for a subset of assets | review against architecture/safety documentation |
| Fail-safe dependencies | no `failSafeDependsOn` assertion | acquire evidence or retain downstream results as `undetermined` |
| Railway zone semantics | zones are only typed `RailwaySecurityZone` | classify zones from a reviewed source/judgement before ETCS entry-point evaluation |
| Entry access mechanisms | no `reachableBy` assertion on an entry asset | acquire remote/maintenance/supplier access evidence before materialising ETCS attack paths |
| Detailed EN 50159 alternatives | available only as explicit synthetic scenario assumptions | do not import the idealised values into the realistic episode |

## L3 consequence

Flow-level ATT&CK applicability can be evaluated wherever its required L1-L2
evidence exists. Asset-level entry-point applicability is not yet a valid ETCS
case result: the architecture names an external-network zone and a firewall/DMZ
zone, but does not yet record reviewed `ExternalZone`/`DMZZone` classifications.
Treating generic zone membership as evidence of absence would create a false
negative.

Attack-path traversal additionally requires an explicit access mechanism on a
derived entry point. Because no case asset currently has `reachableBy`, an
empty ETCS attack-path result would mean “required access evidence absent”, not
“the architecture has no attack path”.

## Resolution rule

Every open item must be resolved in one of three auditable ways:

1. add an asserted fact with a stable source locator;
2. add an explicitly attributed assessor judgement with revision conditions;
3. retain it as unresolved and identify the evaluations/results it prevents.

No item may be resolved by selecting the value that creates the most useful
demonstration.

Run `scripts/audit_etcs_case_data.py` to regenerate the machine-readable and
human-readable readiness summary.
