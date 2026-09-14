"""Compare two RDF case Runs by stable element/criterion evaluation keys."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from rdflib import Graph

from summarize_case_run import RES, evaluation_rows, select_run


def keyed_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    keyed: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        key = (row["element"], row["criterion"])
        if key in keyed:
            raise ValueError(f"duplicate evaluation key: {key}")
        keyed[key] = row
    return keyed


def compare(
    left_rows: list[dict[str, str]], right_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    left = keyed_rows(left_rows)
    right = keyed_rows(right_rows)
    output: list[dict[str, str]] = []
    for element, criterion in sorted(set(left) | set(right)):
        a = left.get((element, criterion))
        b = right.get((element, criterion))
        if a is None:
            status = "right-only"
        elif b is None:
            status = "left-only"
        elif a["outcome"] != b["outcome"]:
            status = "changed"
        else:
            status = "unchanged"
        output.append(
            {
                "element": element,
                "criterion": criterion,
                "stage": (a or b or {}).get("stage", ""),
                "left_outcome": a["outcome"] if a else "",
                "right_outcome": b["outcome"] if b else "",
                "comparison_status": status,
            }
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--left-run-id", required=True)
    parser.add_argument("--right-run-id", required=True)
    parser.add_argument("--csv-out", type=Path, required=True)
    parser.add_argument("--changes-only", action="store_true")
    args = parser.parse_args()

    left_graph = Graph().parse(args.left)
    right_graph = Graph().parse(args.right)
    left_run = select_run(left_graph, args.left_run_id)
    right_run = select_run(right_graph, args.right_run_id)
    rows = compare(
        evaluation_rows(left_graph, left_run),
        evaluation_rows(right_graph, right_run),
    )
    if args.changes_only:
        rows = [row for row in rows if row["comparison_status"] != "unchanged"]
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "element", "criterion", "stage", "left_outcome", "right_outcome",
        "comparison_status",
    ]
    with args.csv_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    counts = {status: sum(row["comparison_status"] == status for row in rows) for status in (
        "changed", "unchanged", "left-only", "right-only"
    )}
    print(f"wrote {len(rows)} rows to {args.csv_out}: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
