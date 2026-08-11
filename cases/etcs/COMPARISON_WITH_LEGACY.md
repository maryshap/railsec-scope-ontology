# ETCS migration comparison

The new case was generated from the workbook through `mapping.csv`; no legacy ABox triples or `http://purl.org/ics-sec#` IRIs were copied.

| Check | Legacy pipeline | New baseline | Explanation |
|---|---:|---:|---|
| Input representation | 424 named individuals in the stored ABox | 4,123 asserted triples from 14 zones, 92 assets, 88 interface rows, 29 functions and 17 trust assumptions | The new model creates explicit Interface/InformationFlow and BoundaryStatusAssertion records, so counts are not directly comparable. |
| Rule inventory | 54 loaded; 12 zero-firing | 1 proven generic L2 rule; M5 domain rules not released | All 54 legacy rules have explicit map/refactor decisions, but every row still requires domain/source review. |
| Inferred output | 7,320 triples; L1/L2/L3/L4 mixed in a custom evaluator | OWL 2 DL/HermiT closure plus separated L2/SHACL/orchestrator stages | A raw triple-count equality would conceal the architecture change and is not an acceptance criterion. |
| AHP | 7 weights; CR 0.055118..., stale expected value 0.033 | Not migrated | Ordering belongs to versioned OrderingFactor/FactorValue/OrderingResult artefacts and is deferred until its factors are reviewed. |

The present ETCS ABox passes OWL 2 DL profile, HermiT consistency and structural SHACL validation. Classification-result equality is intentionally not claimed: the M5 criteria and old AHP factor model are not yet domain-approved. `unmapped.csv` accounts for workbook sections that would otherwise be silently lost.
