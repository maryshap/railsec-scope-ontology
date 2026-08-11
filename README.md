# RailSec Scope Ontology

Clean formalisation workspace for the ontology-based railway security-assessment scoping framework approved at Gate B.

## Status

Pre-release formalisation baseline plus governed Phase 2 conceptual changes. The frozen Gate B source remains the baseline; every semantic extension or revision is entered in `docs/GATE_B_CHANGE_RECORD.md` and `docs/CONCEPTUAL_CHANGE_CATALOG.tsv` under the admission rules in `docs/CONCEPTUAL_CHANGE_POLICY.md`.

## Namespace

Persistent namespace root: `https://w3id.org/railsec-scope/`

The complete policy is in `docs/IRI_POLICY.md`. Public release is blocked until the w3id redirect is registered and tested.

## Repository structure

```text
ontology/       OWL TBox and RBox modules
shapes/         SHACL integrity constraints
rules/          DL-safe classification rule artefacts and metadata
profiles/       railway architecture instance profile
fixtures/       minimal positive/negative fixtures and the selected ETCS fixture
queries/        executable competency-question queries
tests/          semantic, structural and regression tests
scripts/        deterministic build and validation entry points
docs/           design records, mappings and evidence
build/          generated outputs; never a source of truth
```

In this project, **OWL RBox** means property axioms. Rules are maintained separately in `rules/`.

## Validation

Run `scripts\validate.ps1`. It checks the full local import closure against OWL 2 DL, classifies it with HermiT, compares the inferred hierarchy with the committed report, rejects deliberate inconsistencies, audits the 76 frozen classes plus governed conceptual changes, and runs the semantic/SHACL/CQ tests. Use `-UpdateHierarchy` only after reviewing an intentional hierarchy change.

## Internal author guides

- `docs/CODE_AND_FILES_GUIDE_UA.md` — detailed Ukrainian guide to every current file, folder and implementation status.
- `docs/LEGACY_VS_NEW_SHORT_UA.md` — short Ukrainian comparison of the legacy and new ontologies.
