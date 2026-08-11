# Legacy migration decisions

`legacy-rule-triage.csv` contains one explicit keep/map/refactor/retire decision for each of the 54 rules actually returned by the legacy generator. All rows remain `domain-review-required`: the matrix controls implementation order but does not validate the legacy standard citations.

No rule is copied unchanged. `map` means preserve and re-express the assessment intent as a versioned M5 criterion/rule with proper provenance. `refactor` means move computation or import enrichment to its correct layer. A domain reviewer may change a row to `retire`, but must record the reason before the corresponding M5 criterion is released.
