# Independent expert-assessment comparison

This directory is reserved for ETCS case-study evidence used by EV-B11. Do not
copy ontology-derived conclusions into the expert input table.

1. Freeze the expert report and record its title/version/date and case boundary.
2. Transcribe each finding into `expert-findings-template.csv`, preserving the
   report's wording and risk scale.
3. Resolve report identifiers to stable ETCS case IRIs in a separate mapping
   review. Record ambiguity instead of guessing.
4. Pre-register which ontology criteria can be compared with each finding.
5. Run the ontology independently, then create the comparison matrix.
6. Classify agreement, ontology-only, expert-only, partial, undetermined and
   not-comparable outcomes, with a reason for every row.

The original report may be confidential and does not have to be committed. In
that case commit only a redacted evidence register and cryptographic digest if
permitted, while keeping the source locator usable by authorised reviewers.

Risk scores are not compared numerically until their scales, aggregation rules
and units of analysis have been shown to be compatible.
