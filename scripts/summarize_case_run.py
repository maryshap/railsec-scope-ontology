"""Create a human-readable, run-scoped summary of an RDF result graph."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

from rdflib import Graph, Namespace, RDF, URIRef


CRIT = Namespace("https://w3id.org/railsec-scope/criteria#")
RES = Namespace("https://w3id.org/railsec-scope/results#")


def local(term) -> str:
    return str(term).rstrip("/").split("/")[-1].split("#")[-1]


def select_run(graph: Graph, run_identifier: str) -> URIRef:
    matches = {
        run
        for run in graph.subjects(RDF.type, RES.Run)
        if str(graph.value(run, RES.runIdentifier)) == run_identifier
    }
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one Run with runIdentifier={run_identifier!r}; "
            f"found {len(matches)}"
        )
    return next(iter(matches))


def evaluation_rows(graph: Graph, run: URIRef) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for evaluation in sorted(graph.subjects(RDF.type, RES.CriterionEvaluation), key=str):
        if graph.value(evaluation, RES.producedByRun) != run:
            continue
        criterion = graph.value(evaluation, RES.evaluatesCriterion)
        outcome = graph.value(evaluation, RES.hasEvaluationOutcome)
        element = graph.value(evaluation, RES.evaluationConcernsElement)
        stage = graph.value(criterion, CRIT.evaluationStageIdentifier) if criterion else None
        records = list(graph.objects(evaluation, RES.hasDerivationRecord))
        statuses = {
            str(status)
            for record in records
            for status in graph.objects(record, RES.completenessStatus)
        }
        rows.append(
            {
                "evaluation": str(evaluation),
                "stage": str(stage or "unclassified"),
                "criterion": str(criterion or ""),
                "element": str(element or ""),
                "outcome": local(outcome) if outcome else "missing",
                "derivation_status": ",".join(sorted(statuses)) or "missing",
            }
        )
    return rows


def markdown_summary(graph: Graph, run: URIRef, rows: list[dict[str, str]]) -> str:
    publishable = graph.value(run, RES.publishable)
    refusals = sorted(str(reason) for reason in graph.objects(run, RES.refusalReason))
    overall = Counter(row["outcome"] for row in rows)
    by_stage: dict[str, Counter] = defaultdict(Counter)
    unknown_by_criterion: Counter = Counter()
    derivations: Counter = Counter(row["derivation_status"] for row in rows)
    for row in rows:
        by_stage[row["stage"]][row["outcome"]] += 1
        if row["outcome"] == "undetermined":
            unknown_by_criterion[local(row["criterion"])] += 1

    lines = [
        f"# Case Run: {graph.value(run, RES.runIdentifier)}",
        "",
        f"- Run IRI: `{run}`",
        f"- Publishable: `{publishable}`",
        f"- Iterations: `{graph.value(run, RES.iterationCount)}`",
        f"- Artefact digest: `{graph.value(run, RES.artefactDigest)}`",
        f"- Evaluations for this Run only: `{len(rows)}`",
        f"- Outcomes: satisfied `{overall['satisfied']}`, notSatisfied "
        f"`{overall['notSatisfied']}`, undetermined `{overall['undetermined']}`, "
        f"missing `{overall['missing']}`",
        "",
    ]
    if refusals:
        lines += ["## Refusals", ""] + [f"- {reason}" for reason in refusals] + [""]
    if str(publishable).lower() != "true":
        lines += [
            "> This Run is diagnostic evidence only and must not be reported as a "
            "final case-study result.",
            "",
        ]

    lines += [
        "## Outcomes by stage",
        "",
        "| Stage | Satisfied | Not satisfied | Undetermined | Missing | Total | Determined coverage |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for stage in sorted(by_stage):
        counts = by_stage[stage]
        total = sum(counts.values())
        determined = counts["satisfied"] + counts["notSatisfied"]
        coverage = determined / total if total else 0.0
        lines.append(
            f"| {stage} | {counts['satisfied']} | {counts['notSatisfied']} | "
            f"{counts['undetermined']} | {counts['missing']} | {total} | {coverage:.1%} |"
        )

    lines += ["", "## Most frequent undetermined criteria", ""]
    if unknown_by_criterion:
        lines += ["| Criterion | Count |", "|---|---:|"]
        lines += [
            f"| {criterion} | {count} |"
            for criterion, count in sorted(
                unknown_by_criterion.items(), key=lambda item: (-item[1], item[0])
            )
        ]
    else:
        lines.append("No undetermined evaluations.")

    lines += ["", "## Derivation-record status", "", "| Status | Evaluations |", "|---|---:|"]
    lines += [f"| {status} | {count} |" for status, count in sorted(derivations.items())]
    lines.append("")
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [
            "evaluation", "stage", "criterion", "element", "outcome", "derivation_status"
        ])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, help="Turtle result graph written by orchestrator.py")
    parser.add_argument("--run-id", required=True, help="exact rss-res:runIdentifier to summarise")
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--csv-out", type=Path)
    args = parser.parse_args()

    graph = Graph().parse(args.result)
    try:
        run = select_run(graph, args.run_id)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    rows = evaluation_rows(graph, run)
    summary = markdown_summary(graph, run, rows)
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(summary, encoding="utf-8")
    else:
        print(summary)
    if args.csv_out:
        write_csv(args.csv_out, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
