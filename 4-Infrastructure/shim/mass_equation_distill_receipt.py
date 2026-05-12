#!/usr/bin/env python3
"""Emit a receipt for the unified mass-equation distill artifact.

This is a coverage and claim-boundary receipt, not a theorem verifier.  It
records what the mass-equation parquet contains, what it excludes, and the
hashes needed to treat the artifact as an input to later OMCF/PIST routing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.compute as pc
import pyarrow.parquet as pq


REPO = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO / "3-Mathematical-Models/equations_parquet_tagged/mass_equations_unified.parquet"
DEFAULT_TIMESTAMPED = (
    REPO / "3-Mathematical-Models/equations_parquet_tagged/mass_equations_20260504_134248.parquet"
)
DEFAULT_COMPRESSED = (
    REPO / "3-Mathematical-Models/equations_compressed/mass_equations_20260504_134248.compressed"
)
DEFAULT_RECEIPT = (
    REPO / "3-Mathematical-Models/equations_parquet_tagged/mass_equations_unified_receipt.json"
)
DEFAULT_SUMMARY = (
    REPO / "3-Mathematical-Models/equations_parquet_tagged/mass_equations_unified_receipt.md"
)

CLAIM_BOUNDARY = (
    "Mass-equation distill coverage receipt. This records extracted/tagged "
    "equation surfaces and structural features for routing, compression, and "
    "candidate-law selection. It is not a theorem verification result, not a "
    "complete all-mathematics corpus claim, not a benchmark result, and not a "
    "claim that every row is semantically a physical mass law."
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def value_counts(table: Any, column: str, limit: int = 20) -> list[dict[str, Any]]:
    if column not in table.column_names:
        return []
    counts = pc.value_counts(table[column]).to_pylist()
    normalized = [
        {"value": "" if item["values"] is None else item["values"], "count": int(item["counts"])}
        for item in counts
    ]
    normalized.sort(key=lambda row: (-row["count"], str(row["value"])))
    return normalized[:limit]


def bool_sum(table: Any, column: str) -> int | None:
    if column not in table.column_names:
        return None
    return int(pc.sum(table[column].cast("int64")).as_py() or 0)


def unique_count(table: Any, column: str) -> int | None:
    if column not in table.column_names:
        return None
    return int(pc.count_distinct(table[column]).as_py() or 0)


def null_count(table: Any, column: str) -> int | None:
    if column not in table.column_names:
        return None
    return int(pc.sum(pc.is_null(table[column]).cast("int64")).as_py() or 0)


def equation_hash_stats(table: Any) -> dict[str, Any]:
    if "equation" not in table.column_names:
        return {"available": False}
    hashes: Counter[str] = Counter()
    duplicate_rows = 0
    for value in table["equation"].to_pylist():
        text = "" if value is None else str(value)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        hashes[digest] += 1
        if hashes[digest] > 1:
            duplicate_rows += 1
    return {
        "available": True,
        "unique_equation_hashes": len(hashes),
        "duplicate_equation_rows_by_hash": duplicate_rows,
        "top_duplicate_hashes": [
            {"sha256": digest, "count": count}
            for digest, count in hashes.most_common(10)
            if count > 1
        ],
    }


def compressed_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    raw = path.read_bytes()[:4096]
    metadata: dict[str, Any] = {"exists": True, "path": rel(path), "bytes": path.stat().st_size}
    if len(raw) >= 4:
        n = int.from_bytes(raw[:4], "big")
        if 0 < n <= len(raw) - 4:
            try:
                metadata["header"] = json.loads(raw[4 : 4 + n].decode("utf-8"))
            except Exception as exc:  # pragma: no cover - diagnostic only
                metadata["header_parse_error"] = f"{type(exc).__name__}: {exc}"
    return metadata


def build_receipt(input_path: Path, timestamped_path: Path, compressed_path: Path) -> dict[str, Any]:
    parquet = pq.ParquetFile(input_path)
    table = pq.read_table(input_path)

    feature_columns = [
        "has_operator",
        "has_derivative",
        "has_integral",
        "has_sum",
        "has_product",
        "has_fraction",
        "has_matrix",
        "has_vector",
        "has_function_call",
        "has_subscript",
        "has_superscript",
        "has_sqrt",
        "is_short",
        "is_medium",
        "is_long",
    ]
    numeric_columns = ["confidence", "length", "num_operators", "num_variables"]

    receipt: dict[str, Any] = {
        "schema": "mass_equation_distill_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runner": rel(Path(__file__)),
        "claim_boundary": CLAIM_BOUNDARY,
        "decision": "COVERAGE_RECEIPT_ONLY",
        "primary_artifact": {
            "path": rel(input_path),
            "bytes": input_path.stat().st_size,
            "sha256": sha256_file(input_path),
            "rows": parquet.metadata.num_rows,
            "row_groups": parquet.metadata.num_row_groups,
            "columns": table.column_names,
        },
        "related_artifacts": {
            "timestamped_mass_parquet": {
                "path": rel(timestamped_path),
                "exists": timestamped_path.exists(),
                "bytes": timestamped_path.stat().st_size if timestamped_path.exists() else None,
                "sha256": sha256_file(timestamped_path),
                "rows": pq.ParquetFile(timestamped_path).metadata.num_rows
                if timestamped_path.exists()
                else None,
            },
            "compressed_mass_equations": {
                **compressed_metadata(compressed_path),
                "sha256": sha256_file(compressed_path),
            },
        },
        "coverage": {
            "source_type_counts": value_counts(table, "source_type"),
            "domain_counts": value_counts(table, "domain"),
            "category_counts": value_counts(table, "category"),
            "unified_pattern_counts": value_counts(table, "unified_pattern"),
            "pattern_counts": value_counts(table, "pattern"),
            "unique_counts": {
                column: unique_count(table, column)
                for column in ["equation_id", "equation", "source", "title", "doi", "category", "domain"]
                if column in table.column_names
            },
            "null_counts": {
                column: null_count(table, column)
                for column in ["equation_id", "equation", "source", "title", "doi", "category", "domain"]
                if column in table.column_names
            },
        },
        "feature_counts": {
            column: bool_sum(table, column)
            for column in feature_columns
            if column in table.column_names
        },
        "numeric_summary": {},
        "equation_hash_stats": equation_hash_stats(table),
        "exclusions": [
            "No proof replay or Lean build was run by this receipt.",
            "No byte-exact compression benchmark is claimed.",
            "Rows are extracted/tagged equation surfaces, not authoritative mathematical truth.",
            "The source coverage observed here is arXiv-only for the unified parquet.",
            "Domain value 'unknown' remains unresolved and must not be promoted as typed coverage.",
            "The compressed artifact is an older timestamped mass-equation artifact, not a compressed form of every unified row unless a separate replay receipt proves it.",
        ],
        "admission_notes": [
            "Suitable as a routing prior for OMCF/PIST candidate-law discovery.",
            "Suitable as a corpus for mass-pattern feature statistics.",
            "Not suitable as a final total-math distill claim without source inventory, replay, and negative controls.",
        ],
    }

    for column in numeric_columns:
        if column in table.column_names:
            arr = table[column]
            receipt["numeric_summary"][column] = {
                "min": pc.min(arr).as_py(),
                "max": pc.max(arr).as_py(),
                "mean": pc.mean(arr).as_py(),
            }

    stable_receipt = dict(receipt)
    stable_receipt.pop("generated_at_utc", None)
    receipt_preimage = json.dumps(stable_receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    receipt["receipt_hash_sha256"] = hashlib.sha256(receipt_preimage.encode("utf-8")).hexdigest()
    return receipt


def write_summary(receipt: dict[str, Any], path: Path) -> None:
    primary = receipt["primary_artifact"]
    related = receipt["related_artifacts"]
    lines = [
        "# Mass Equation Distill Receipt",
        "",
        f"Schema: `{receipt['schema']}`  ",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash_sha256']}`",
        "",
        "## Claim Boundary",
        "",
        receipt["claim_boundary"],
        "",
        "## Primary Artifact",
        "",
        f"- Path: `{primary['path']}`",
        f"- Rows: `{primary['rows']}`",
        f"- Bytes: `{primary['bytes']}`",
        f"- SHA256: `{primary['sha256']}`",
        "",
        "## Coverage Snapshot",
        "",
        "Top domains:",
    ]
    for row in receipt["coverage"]["domain_counts"][:8]:
        lines.append(f"- `{row['value']}`: {row['count']}")
    lines.extend(["", "Top categories:"])
    for row in receipt["coverage"]["category_counts"][:8]:
        lines.append(f"- `{row['value']}`: {row['count']}")
    lines.extend(["", "Feature counts:"])
    for key, value in receipt["feature_counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Related Artifacts",
            "",
            f"- Timestamped parquet: `{related['timestamped_mass_parquet']['path']}` "
            f"({related['timestamped_mass_parquet']['rows']} rows)",
            f"- Compressed artifact: `{related['compressed_mass_equations'].get('path')}`",
            "",
            "## Exclusions",
            "",
        ]
    )
    for item in receipt["exclusions"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--timestamped", type=Path, default=DEFAULT_TIMESTAMPED)
    parser.add_argument("--compressed", type=Path, default=DEFAULT_COMPRESSED)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    receipt = build_receipt(args.input, args.timestamped, args.compressed)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt, args.summary)
    print(json.dumps({"receipt": rel(args.receipt), "summary": rel(args.summary), "hash": receipt["receipt_hash_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
