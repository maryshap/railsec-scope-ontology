# Legacy architecture source policy

The files under the workspace `legacy_snapshot/` are retained as historical inputs. They are not imported wholesale into the ontology and are not normative sources for railway-security criteria.

## Permitted use

- `General_Architecture.pdf` and `railway_architecture_v2.docx` may support identification of ETCS M6 architecture candidates: on-board, centralised/distributed trackside, telecom, maintenance and remote-access zones; assets; interfaces; and labelled communication paths.
- `Ontology_model.xlsx` remains the machine-readable source behind the current mapped ETCS ABox. Every accepted field is governed by `mapping.csv`; rejected or unresolved fields remain in `unmapped.csv`.
- Legacy TBox, generated ABox, inferred output and rule documentation may be used to locate candidate concepts, mappings and regression questions.

## Prohibited use

- Legacy inferred classes, AHP scores and vulnerability labels are not case facts and must not be copied into M6.
- Legacy rule comments and claimed clause numbers are not accepted as normative evidence. New criteria require reviewed `SourceLocation` and `Interpretation` records; until then they remain explicitly provisional `JudgementBasis` records.
- No ETCS individual may occur in M1-M5. ETCS architecture individuals remain in the separate M6 case ontology.

## Admission procedure

For each legacy architecture item: identify the source location, map it to the railway instance profile, record epistemic status and provenance, validate the resulting M6 assertion, and only then permit the assessment pipeline to derive conclusions. Unknown mappings remain unknown; they are never replaced by a convenient default.
