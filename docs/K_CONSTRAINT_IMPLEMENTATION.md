# K-constraint implementation map

| Constraint | Authority | Executable artefact |
|---|---|---|
| K-01–K-10 | SHACL Core/SPARQL; K-10 follows orchestrator capture | `shapes/constraints.ttl` |
| K-11 | SHACL Core | `shapes/criterion-slice.ttl` |
| K-12–K-18 | SHACL Core/SPARQL | `shapes/constraints.ttl` |
| K-19–K-20 | build-time module inspection | `scripts/publication_lint.py` |
| K-21 | SHACL Core | `shapes/constraints.ttl` |
| K-22 | automated guard plus mandatory manual review | `scripts/publication_lint.py`, `docs/PUBLICATION_REVIEW.md` |
| K-23 | post-L2 entailment/assignment agreement | `queries/K-23-assignment-agreement.rq` |
| K-24 | stage-authority query plus SHACL regression slice | `queries/K-24-layer-authority.rq`, `shapes/criterion-slice.ttl` |

The positive architecture fixture and the two negative fixture groups are executed by `tests/`. Structural validation deliberately runs before RDFS/OWL inference so that a property domain cannot silently turn an incorrectly typed position owner into a conforming record.
