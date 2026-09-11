# RailSec Scope Ontology

Clean formalisation workspace for the ontology-based railway security-assessment scoping framework approved at Gate B.

## Status

Pre-release formalisation baseline plus governed Phase 2 conceptual changes. The frozen Gate B source remains the baseline; every semantic extension or revision is entered in `docs/DECISIONS.md` under the admission rules in the same file. Current progress and open release blockers are tracked in `docs/STATUS.md` — that is the single place this is tracked; do not add a second one.

## Namespace

Persistent namespace root: `https://w3id.org/railsec-scope/`

The complete policy, prefix table and identifier stability rules are in `docs/IRI_POLICY.md`. Public release is blocked until the w3id redirect is registered and tested.

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

## Documentation

Seven narrative files, each covering one thing, plus one machine-readable
catalogue used by the formalisation audit:

- `docs/CONCEPTUAL_MODEL.md` — the frozen Gate B conceptual model itself (entities, relations, constraints). Start here to understand what the ontology means.
- `docs/DECISIONS.md` — every governed decision since the freeze (CR-B-001 onward), the admission policy for new terms, the conceptual change catalog, the K-constraint implementation map, the module import graph and the PROV-O mapping. One file for everything that changed and why.
- `docs/STATUS.md` — what's implemented, what's tested, and what's still an open release blocker. The only progress tracker; update it when a step lands and nowhere else.
- `docs/IRI_POLICY.md` — namespace root, prefix table, version-IRI and identifier-stability rules. Reference this when writing IRIs in any `.ttl` file.
- `docs/CODE_AND_FILES_GUIDE_UA.md` — practical guide to the codebase (UA).
- `docs/LEGACY_VS_NEW_SHORT_UA.md` — short comparison of the old and new ontology (UA).
- `docs/PUBLICATION_REVIEW.md` — K-22 manual copyright/source-text review checklist, required before release.
- `docs/CONCEPTUAL_CHANGE_CATALOG.tsv` — machine-readable admission catalogue consumed by validation; edit it together with the corresponding decision record.

## Validation

Run `scripts\validate.ps1`. It checks the full local import closure against OWL 2 DL, classifies it with HermiT, compares the inferred hierarchy with the committed report, rejects deliberate inconsistencies, audits the 76 frozen classes plus governed conceptual changes, and runs the semantic/SHACL/CQ tests. Use `-UpdateHierarchy` only after reviewing an intentional hierarchy change.
