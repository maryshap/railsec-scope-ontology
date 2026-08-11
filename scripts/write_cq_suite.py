"""Generate the Gate A CQ-01..CQ-45 SPARQL query suite."""

from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "queries" / "cq"
PREFIXES = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX rss-assess: <https://w3id.org/railsec-scope/assessment#>
PREFIX rss-core: <https://w3id.org/railsec-scope/core#>
PREFIX rss-crit: <https://w3id.org/railsec-scope/criteria#>
PREFIX rss-res: <https://w3id.org/railsec-scope/results#>
PREFIX rsso: <https://w3id.org/railsec-scope/ontology#>
"""

Q = {
1: "SELECT ?element ?status WHERE { ?a a rss-core:BoundaryStatusAssertion; rss-core:statusSubject ?element; rss-core:boundaryStatusValue ?status . } ORDER BY ?status ?element",
2: "SELECT ?element ?rationale WHERE { ?a rss-core:statusSubject ?element; rss-core:boundaryStatusValue rss-core:outOfScope; rss-core:hasExclusionRationale ?rationale . }",
3: "SELECT ?flow ?origin ?destination WHERE { ?flow a rss-core:InformationFlow; rss-core:hasOrigin ?origin; rss-core:hasDestination ?destination . ?origin rss-core:memberOf ?g1 . ?destination rss-core:memberOf ?g2 . FILTER(?g1 != ?g2) }",
4: "SELECT ?asset ?function WHERE { ?asset rss-core:realises ?function . }",
5: "SELECT ?element ?result ?record WHERE { ?result a rss-res:ReachabilityResult; rss-res:reachabilityConcerns ?element; rss-res:hasDerivationRecord ?record . }",
6: "SELECT ?element ?mechanism ?precondition WHERE { ?r a rss-res:ReachabilityResult; rss-res:reachabilityConcerns ?element; rss-res:usedAccessMechanism ?mechanism . OPTIONAL { ?r rss-res:reliedOnPrecondition ?precondition } }",
7: "SELECT ?element ?precondition ?assumption WHERE { ?r rss-res:reachabilityConcerns ?element; rss-res:reliedOnPrecondition ?precondition . ?precondition rss-core:preconditionSupportedBy ?assumption . ?assumption a rss-core:Assumption . }",
8: "SELECT ?comparison ?reachability ?candidateAssignment WHERE { ?comparison a rss-res:RunComparison . OPTIONAL { ?comparison rss-res:changedResult ?reachability . ?reachability a rss-res:ReachabilityResult } OPTIONAL { ?comparison rss-res:changedResult ?candidateAssignment . ?candidateAssignment a rss-res:CategoryAssignment } }",
9: "SELECT DISTINCT ?element ?criterion WHERE { ?element a rss-crit:CandidateExaminationTarget . ?evaluation a rss-res:CriterionEvaluation; rss-res:evaluationConcernsElement ?element; rss-res:evaluatesCriterion ?criterion; rss-res:hasEvaluationOutcome rss-res:satisfied . }",
10: "SELECT ?candidate ?criterion ?statement WHERE { ?evaluation rss-res:evaluationConcernsElement ?candidate; rss-res:evaluatesCriterion ?criterion; rss-res:hasEvaluationOutcome rss-res:satisfied . ?criterion rss-crit:criterionStatement ?statement . }",
11: "SELECT ?element ?property ?function WHERE { ?scenario rss-core:scenarioConcernsElement ?element; rss-core:scenarioConcernsProperty ?property . ?result a rss-res:SafetyImpactResult; rss-res:evaluatesScenario ?scenario; rss-res:affectsFunction ?function . }",
12: "SELECT ?chain ?position ?node WHERE { ?chain a rss-res:DependencyChain; rss-res:hasChainEntry ?entry . ?entry rss-res:pathPosition ?position; rss-res:chainNode ?node . } ORDER BY ?chain ?position",
13: "SELECT DISTINCT ?candidate ?basis WHERE { ?candidate a rss-crit:CandidateExaminationTarget . { ?r a rss-res:ReachabilityResult; rss-res:reachabilityConcerns ?candidate . BIND(\"exposure\" AS ?basis) } UNION { ?evaluation rss-res:evaluationConcernsElement ?candidate; rss-res:evaluatesCriterion ?criterion . ?criterion rdfs:label ?label . FILTER(CONTAINS(LCASE(STR(?label)), \"safety\")) BIND(\"safety\" AS ?basis) } }",
14: "SELECT ?decision ?result ?rationale WHERE { ?decision a rss-assess:Override; rss-assess:concernsResult ?result; rss-assess:hasRationale ?rationale . }",
15: "SELECT ?ordering ?factorSet ?factor ?version WHERE { ?ordering a rss-res:OrderingResult; rss-res:usesFactorSet ?factorSet . ?factorSet rss-crit:hasFactor ?factor; rss-crit:hasVersion ?version . }",
16: "SELECT ?candidate ?factor ?value ?basis WHERE { ?fv a rss-res:FactorValue; rss-res:factorValueForCandidate ?candidate; rss-res:valueOfFactor ?factor; rss-res:representedValue ?value . OPTIONAL { ?fv rss-res:valueBasis ?basis } }",
17: "SELECT ?assignment ?firstPosition ?secondPosition WHERE { ?first a rss-res:OrderingResult; rss-res:hasOrderingEntry ?e1 . ?second a rss-res:OrderingResult; rss-res:hasOrderingEntry ?e2 . FILTER(?first != ?second) ?e1 rss-res:ranksAssignment ?assignment; rss-res:orderingPosition ?firstPosition . ?e2 rss-res:ranksAssignment ?assignment; rss-res:orderingPosition ?secondPosition . FILTER(?firstPosition != ?secondPosition) }",
18: "SELECT ?element ?constraint WHERE { ?constraint a rss-core:ExaminationConstraint; rss-core:appliesToElement ?element . }",
19: "SELECT ?assertion ?step WHERE { ?assertion a rss-core:AuthorisationAssertion . ?step rss-res:generatedResult ?assertion . }",
20: "SELECT ?criterion ?source ?edition ?location WHERE { ?criterion rss-crit:derivedFromSourceLocation ?location . ?location rss-crit:locatedInEdition ?edition . ?edition rss-crit:editionOf ?source . }",
21: "SELECT ?criterion ?interpretation ?proposition WHERE { ?criterion rss-crit:appliesInterpretation ?interpretation . ?interpretation rss-crit:interpretationProposition ?proposition . }",
22: "SELECT ?criterion (BOUND(?judgement) AS ?judgementBased) WHERE { ?criterion a rss-crit:Criterion . OPTIONAL { ?criterion rss-crit:restsOnJudgement ?judgement } FILTER NOT EXISTS { ?criterion rss-crit:derivedFromSourceLocation ?location } }",
23: "SELECT ?source ?criterion ?result WHERE { ?edition rss-crit:editionOf ?source . ?location rss-crit:locatedInEdition ?edition . ?criterion rss-crit:derivedFromSourceLocation ?location . OPTIONAL { ?step rss-res:appliedCriterion ?criterion; rss-res:generatedResult ?result } }",
24: "SELECT ?result ?input ?criterion WHERE { ?result rss-res:hasDerivationRecord ?record . ?record rss-res:hasStep ?step . OPTIONAL { ?step rss-res:usedEntity ?input } OPTIONAL { ?step rss-res:appliedCriterion ?criterion } }",
25: "SELECT ?result ?step ?mechanism ?version WHERE { ?result rss-res:hasDerivationRecord/rss-res:hasStep ?step . ?step rss-res:executedByMechanism ?mechanism . ?mechanism rss-crit:hasVersion ?version . }",
26: "SELECT ?result ?unresolved WHERE { ?result rss-res:hasDerivationRecord ?record . ?record rss-res:hasUnresolvedInput ?unresolved . }",
27: "SELECT ?result ?record WHERE { ?designation a rss-res:MaterialFindingDesignation; rss-res:designatesResult ?result . OPTIONAL { ?result rss-res:hasDerivationRecord ?record } FILTER(!BOUND(?record) || NOT EXISTS { ?record rss-res:completenessStatus \"complete\" }) }",
28: "SELECT ?element ?criterion ?outcome WHERE { ?evaluation a rss-res:CriterionEvaluation; rss-res:evaluationConcernsElement ?element; rss-res:evaluatesCriterion ?criterion; rss-res:hasEvaluationOutcome ?outcome . }",
29: "SELECT ?element ?predicate ?objectResource ?objectLiteral WHERE { ?assertion a rss-core:AssertedAbsence; rss-core:assertionSubject ?element; rss-core:assertionPredicateIri ?predicate . OPTIONAL { ?assertion rss-core:assertionObjectResource ?objectResource } OPTIONAL { ?assertion rss-core:assertionObjectLiteral ?objectLiteral } }",
30: "SELECT ?unresolved ?result WHERE { ?result rss-res:hasDerivationRecord ?record . ?record rss-res:hasUnresolvedInput ?unresolved . }",
31: "ASK { FILTER NOT EXISTS { ?instance rdf:type owl:Nothing } }",
32: "SELECT ?instance ?constraint ?message WHERE { ?result a sh:ValidationResult; sh:focusNode ?instance; sh:sourceConstraintComponent ?constraint . OPTIONAL { ?result sh:resultMessage ?message } }",
33: "SELECT ?measure ?definition ?scope ?exclusions WHERE { ?measure a rss-crit:CoverageMeasure; rss-crit:measureDefinition ?definition; rss-crit:eligibilityScope ?scope; rss-crit:exclusionDeclaration ?exclusions . }",
34: "SELECT ?result ?value ?outcome ?unresolved WHERE { ?result a rss-res:CoverageResult; rss-res:hasComputationOutcome ?outcome . OPTIONAL { ?result rss-res:representedValue ?value } OPTIONAL { ?result rss-res:hasDerivationRecord/rss-res:hasUnresolvedInput ?unresolved } }",
35: "SELECT ?selection ?element ?difference WHERE { { ?selection a rss-res:Selection; rss-res:selectionBasedOnCandidateSet/rss-res:hasCandidateAssignment/rss-res:materialisesEvaluation/rss-res:evaluationConcernsElement ?element . FILTER NOT EXISTS { ?selection rss-res:includesElement ?element } BIND(\"candidate-not-selected\" AS ?difference) } UNION { ?selection rss-res:includesElement ?element . FILTER NOT EXISTS { ?selection rss-res:selectionBasedOnCandidateSet/rss-res:hasCandidateAssignment/rss-res:materialisesEvaluation/rss-res:evaluationConcernsElement ?element } BIND(\"selected-not-candidate\" AS ?difference) } }",
36: "SELECT ?term ?allocation WHERE { ?term a ?type . FILTER(isIRI(?term)) BIND(IF(STRSTARTS(STR(?term), \"https://w3id.org/railsec-scope/railway#\"), \"extension\", IF(CONTAINS(STR(?term), \"/case/\"), \"case\", \"core\")) AS ?allocation) }",
37: "SELECT ?extensionTerm ?predicate ?coreTerm WHERE { ?extensionTerm ?predicate ?coreTerm . FILTER(STRSTARTS(STR(?extensionTerm), \"https://w3id.org/railsec-scope/railway#\") && STRSTARTS(STR(?coreTerm), \"https://w3id.org/railsec-scope/core#\")) }",
38: "SELECT ?comparison ?run ?changedInput ?changedResult WHERE { ?comparison a rss-res:RunComparison; rss-res:comparesRun ?run . OPTIONAL { ?comparison rss-res:changedAssertion ?changedInput } OPTIONAL { ?comparison rss-res:changedResult ?changedResult } }",
39: "SELECT ?deprecated ?deprecation ?replacement ?explicitNonReplacement WHERE { ?deprecated rss-crit:deprecatedBy ?deprecation . OPTIONAL { ?deprecation rss-crit:replacedBy ?replacement } OPTIONAL { ?deprecation rss-crit:explicitNonReplacement ?explicitNonReplacement } }",
40: "SELECT ?result ?run ?version ?identifier WHERE { ?result rss-res:producedByRun ?run . ?run rss-res:usedVersion ?version . OPTIONAL { ?version rss-crit:versionIdentifier ?identifier } }",
41: "SELECT ?asset ?type ?role WHERE { ?asset a rss-core:Asset . OPTIONAL { ?asset rss-core:hasAssetType ?type } OPTIONAL { ?asset rss-core:playsRole ?role } }",
42: "SELECT ?flow ?characteristic WHERE { ?flow a rss-core:InformationFlow; rss-core:hasCharacteristic ?characteristic . }",
43: "SELECT DISTINCT ?function ?dependency ?direct WHERE { { ?function a rss-core:SafetyFunction; rss-core:directlyDependsOn ?dependency . BIND(true AS ?direct) } UNION { ?function a rss-core:SafetyFunction; rss-core:directlyDependsOn ?middle . ?middle rss-core:directlyDependsOn+ ?dependency . BIND(false AS ?direct) } }",
44: "SELECT ?element ?property ?consequence WHERE { ?scenario rss-core:scenarioConcernsElement ?element; rss-core:scenarioConcernsProperty ?property; rss-core:hasConsequence ?consequence . }",
45: "SELECT ?assignment ?ordering ?method ?methodVersion WHERE { ?ordering a rss-res:OrderingResult; rss-res:hasOrderingEntry/rss-res:ranksAssignment ?assignment; rss-res:producedByMethod ?method . ?method rss-crit:hasVersion ?methodVersion . }",
}


def main() -> int:
    if set(Q) != set(range(1, 46)): raise RuntimeError("CQ suite must contain exactly CQ-01..CQ-45")
    OUT.mkdir(parents=True, exist_ok=True)
    for number, body in Q.items():
        (OUT / f"CQ-{number:02d}.rq").write_text(PREFIXES + "\n" + body + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {len(Q)} competency queries to {OUT}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
