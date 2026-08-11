# IRI and namespace policy

**Decision ID:** IRI-B-001  
**Status:** fixed before the first production class declaration  
**Project name:** RailSec Scope Ontology  
**Short name:** RSSO

## 1. Persistent root

The persistent root is:

```text
https://w3id.org/railsec-scope/
```

The root is intentionally independent of ETCS, a particular railway subsystem, ICS, a standard edition, an institution and a source-code host.

This URI is the target public identifier. A public release must not be issued until the corresponding w3id redirect has been registered, tested and recorded in release evidence.

## 2. Ontology and term IRIs

| Artefact | Ontology IRI | Term namespace | Prefix |
|---|---|---|---|
| Suite metadata | `https://w3id.org/railsec-scope/ontology` | `https://w3id.org/railsec-scope/ontology#` | `rsso:` |
| M1 Core | `https://w3id.org/railsec-scope/core` | `https://w3id.org/railsec-scope/core#` | `rss-core:` |
| M2 Criteria | `https://w3id.org/railsec-scope/criteria` | `https://w3id.org/railsec-scope/criteria#` | `rss-crit:` |
| M3 Results | `https://w3id.org/railsec-scope/results` | `https://w3id.org/railsec-scope/results#` | `rss-res:` |
| M4 Assessment | `https://w3id.org/railsec-scope/assessment` | `https://w3id.org/railsec-scope/assessment#` | `rss-assess:` |
| M5 Railway | `https://w3id.org/railsec-scope/railway` | `https://w3id.org/railsec-scope/railway#` | `rss-rail:` |
| M6 Case | `https://w3id.org/railsec-scope/case/{case-id}` | `https://w3id.org/railsec-scope/case/{case-id}/resource/` | case-local |
| SHACL shapes | `https://w3id.org/railsec-scope/shapes` | `https://w3id.org/railsec-scope/shapes#` | `rss-sh:` |
| Rule metadata | `https://w3id.org/railsec-scope/rules` | `https://w3id.org/railsec-scope/rules#` | `rss-rule:` |

Term local names use singular UpperCamelCase for classes and lowerCamelCase for properties. Published term IRIs are never renamed for stylistic reasons. A replaced term is deprecated and linked to its replacement under ORF-47.

Controlled terminology individuals use singular lowerCamelCase names (for example `satisfied`). Case individuals use stable, readable lower-kebab-case identifiers below the case `resource/` path. Their spelling is an identifier only: consumers must not derive semantics from it. Where a stable readable identifier cannot be minted, the importer uses an opaque source-independent identifier and records the source identifier as data.

## 3. Version IRIs

The first formalisation line is `0.1.0`. Stable ontology IRIs identify the evolving artefacts; immutable version IRIs identify releases:

```text
https://w3id.org/railsec-scope/version/0.1.0/core
https://w3id.org/railsec-scope/version/0.1.0/criteria
https://w3id.org/railsec-scope/version/0.1.0/results
https://w3id.org/railsec-scope/version/0.1.0/assessment
https://w3id.org/railsec-scope/version/0.1.0/railway
https://w3id.org/railsec-scope/case/{case-id}/version/{dataset-version}
```

Development changes retain the `0.1.0` target until a release candidate is frozen. Immutable release files are generated only at release time. Semantic changes increment the minor version before 1.0; compatible documentation or defect corrections increment the patch version.

A bump updates `owl:versionIRI`, `owl:versionInfo`, the dependency checksums and the committed inferred-hierarchy report in one reviewed change. Stable ontology IRIs do not change.

### External PROV-O dependency

The imported IRI is fixed to `http://www.w3.org/ns/prov-o`, version IRI `http://www.w3.org/ns/prov-o-20130430`. The unmodified W3C source is pinned in `imports/prov-o-source.ttl`. Because the canonical document uses annotation/object-property punning that OWLAPI rejects from OWL 2 DL, the XML catalogue resolves the import to the reviewed DL-safe projection `imports/prov-o-dl.ttl`; the projection contains only the PROV-O terms used by M1–M3.

## 4. Dataset IRIs

Case ABoxes use a separate dataset namespace and never mint terminology:

```text
https://w3id.org/railsec-scope/case/{case-id}/
https://w3id.org/railsec-scope/case/{case-id}/version/{dataset-version}
https://w3id.org/railsec-scope/case/{case-id}/resource/{local-id}
```

The ETCS case identifier does not appear in M1–M5 term IRIs. Synthetic unit fixtures use `https://w3id.org/railsec-scope/fixture/{fixture-id}/` and cannot be cited as portability evidence.

## 5. Identifier stability rules

1. No blank node is used for a record that must be cited, compared across Runs or carry provenance.
2. Source-document identifiers and externally controlled identifiers are not copied into local names without an explicit mapping.
3. Labels may change without changing IRIs; definitions and semantic axioms require impact review.
4. Imports use stable ontology IRIs. Release manifests resolve them to fixed version IRIs.
5. HTTP content negotiation and redirect behaviour are release requirements, not assumptions.
6. The legacy `http://purl.org/ics-sec#` namespace is never reused. Legacy mappings, if needed, are one-way migration artefacts outside the production modules.
