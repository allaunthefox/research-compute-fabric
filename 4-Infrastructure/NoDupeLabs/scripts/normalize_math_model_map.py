#!/usr/bin/env python3
"""
Normalize and validate MATH_MODEL_MAP.tsv.

The map has appeared in two row shapes:

12-column canonical row:
    #, Model_Name, Family, Equation, Variables, Purpose, Location,
    Implemented, Status, Cross_Refs, Domain_Type, Bind_Class

10-column compact row:
    Model_Name, Family, Equation, Variables, Purpose, Location,
    Implemented, Status, Domain_Type, Bind_Class

This tool preserves content while expanding compact rows into the canonical
12-column schema by adding a stable row index and an empty Cross_Refs field.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

CANONICAL_HEADER = [
    "#",
    "Model_Name",
    "Family",
    "Equation",
    "Variables",
    "Purpose",
    "Location",
    "Implemented",
    "Status",
    "Cross_Refs",
    "Domain_Type",
    "Bind_Class",
]

COMPACT_HEADER = [
    "Model_Name",
    "Family",
    "Equation",
    "Variables",
    "Purpose",
    "Location",
    "Implemented",
    "Status",
    "Domain_Type",
    "Bind_Class",
]


@dataclass
class RowIssue:
    line_number: int
    width: int
    model_name: str
    issue: str


def split_tsv_line(line: str) -> List[str]:
    return next(csv.reader([line], delimiter="\t"))


def normalize_rows(input_path: Path) -> tuple[list[list[str]], list[RowIssue], dict]:
    raw_lines = input_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not raw_lines:
        raise ValueError("input is empty")

    first = split_tsv_line(raw_lines[0])
    if first != CANONICAL_HEADER:
        # Accept header with literal first cell '#'.
        if len(first) != len(CANONICAL_HEADER) or first[0] != "#":
            raise ValueError(f"unexpected header width/content: {first}")

    normalized: list[list[str]] = [CANONICAL_HEADER]
    issues: list[RowIssue] = []
    compact_count = 0
    canonical_count = 0
    malformed_count = 0

    next_index = 0
    for line_number, line in enumerate(raw_lines[1:], start=2):
        if not line.strip():
            continue
        cells = split_tsv_line(line)
        model_name = cells[1] if len(cells) == 12 else cells[0] if cells else ""

        if len(cells) == 12:
            canonical_count += 1
            normalized.append(cells)
            try:
                next_index = max(next_index, int(cells[0]) + 1)
            except Exception:
                # Preserve non-numeric canonical index but do not let it poison compact numbering.
                pass
        elif len(cells) == 10:
            compact_count += 1
            # Compact rows omit leading # and Cross_Refs.
            expanded = [str(next_index)] + cells[:8] + [""] + cells[8:]
            normalized.append(expanded)
            next_index += 1
            issues.append(RowIssue(line_number, len(cells), model_name, "compact_10_column_row_expanded_to_12"))
        else:
            malformed_count += 1
            issues.append(RowIssue(line_number, len(cells), model_name, "malformed_width_not_10_or_12"))
            # Preserve in a lossy but visible way rather than silently dropping.
            padded = cells[:12] + [""] * max(0, 12 - len(cells))
            normalized.append(padded[:12])

    summary = {
        "input_path": str(input_path),
        "row_count_excluding_header": len(normalized) - 1,
        "canonical_12_column_rows": canonical_count,
        "compact_10_column_rows_expanded": compact_count,
        "malformed_rows": malformed_count,
        "issue_count": len(issues),
        "rule": "Compact 10-column rows are expanded by adding a leading row index and empty Cross_Refs column.",
    }
    return normalized, issues, summary


def write_tsv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to MATH_MODEL_MAP.tsv")
    parser.add_argument("--output", type=Path, default=Path("research-stack/models/MATH_MODEL_MAP.normalized.tsv"))
    parser.add_argument("--report", type=Path, default=Path("research-stack/models/MATH_MODEL_MAP.normalization_report.json"))
    parser.add_argument("--abstract-only", type=Path, default=None, help="Optional output for normalized Abstract_CoT rows only")
    args = parser.parse_args()

    rows, issues, summary = normalize_rows(args.input)
    write_tsv(args.output, rows)

    abstract_rows = [rows[0]] + [r for r in rows[1:] if len(r) > 1 and r[1].startswith("Abstract_CoT_")]
    if args.abstract_only:
        write_tsv(args.abstract_only, abstract_rows)
        summary["abstract_cot_rows"] = len(abstract_rows) - 1
        summary["abstract_only_output"] = str(args.abstract_only)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({
        "summary": summary,
        "issues": [asdict(i) for i in issues],
    }, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
