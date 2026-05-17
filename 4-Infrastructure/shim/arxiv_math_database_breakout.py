#!/usr/bin/env python3
"""Break out math-bearing structure from the local arXiv Kaggle metadata zip.

This streams the JSONL member inside /home/allaun/Documents/ingest/kaggledataset.zip
without extracting it.  The archive contains paper metadata/abstracts, not the
full LaTeX source corpus, so equation signals here are abstract/title markers
and category/domain routes rather than full equation recovery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVE = Path("/home/allaun/Documents/ingest/kaggledataset.zip")
OUT_DIR = REPO / "shared-data" / "data" / "math_research_databases"
SUMMARY = OUT_DIR / "arxiv_math_breakout_summary.json"
CATEGORY_CSV = OUT_DIR / "arxiv_math_breakout_categories.csv"
MARKER_CSV = OUT_DIR / "arxiv_math_breakout_symbol_markers.csv"
SAMPLES_JSONL = OUT_DIR / "arxiv_math_breakout_samples.jsonl"
RECEIPT = OUT_DIR / "arxiv_math_breakout_receipt.json"


MATH_PREFIXES = (
    "math",
    "stat",
    "cs.",
    "nlin",
    "q-bio",
    "q-fin",
    "quant-ph",
    "hep-th",
    "math-ph",
)

LATEX_COMMAND_RE = re.compile(r"\\[A-Za-z]+")
INLINE_MATH_RE = re.compile(r"\$[^$]{1,160}\$")
SYMBOL_RE = re.compile(r"(?:[A-Za-z]\^\{?[-+0-9A-Za-z]+}?|[A-Za-z]_\{?[-+0-9A-Za-z]+}?|[=<>≤≥∈∑∫∞⊗⊕±≈≃≅])")


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def categories_of(record: dict[str, Any]) -> list[str]:
    raw = record.get("categories")
    if not isinstance(raw, str):
        return []
    return [part for part in raw.split() if part]


def is_math_bearing(categories: list[str]) -> bool:
    return any(cat.startswith(MATH_PREFIXES) for cat in categories)


def text_field(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    return value if isinstance(value, str) else ""


def marker_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    commands = LATEX_COMMAND_RE.findall(text)
    inline = INLINE_MATH_RE.findall(text)
    symbols = SYMBOL_RE.findall(text)
    counts["latex_command"] = len(commands)
    counts["inline_math_span"] = len(inline)
    counts["symbolic_token"] = len(symbols)
    for command in commands[:200]:
        counts[f"cmd:{command}"] += 1
    return counts


def csv_escape(value: Any) -> str:
    text = str(value).replace('"', '""')
    return f'"{text}"'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    parser.add_argument("--max-records", type=int, default=200_000)
    parser.add_argument("--sample-records", type=int, default=100)
    parser.add_argument("--math-only", action="store_true", default=True)
    args = parser.parse_args()

    archive = Path(args.archive).expanduser().resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    archive_hash = sha256_file(archive)

    total_seen = 0
    selected_seen = 0
    category_counts: Counter[str] = Counter()
    primary_category_counts: Counter[str] = Counter()
    marker_totals: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    year_counts: Counter[str] = Counter()
    version_counts: Counter[int] = Counter()
    category_pair_counts: Counter[tuple[str, str]] = Counter()
    samples: list[dict[str, Any]] = []
    category_marker_totals: dict[str, Counter[str]] = defaultdict(Counter)

    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        json_members = [info for info in infos if info.filename.endswith(".json")]
        selected_member = json_members[0] if json_members else infos[0]
        with zf.open(selected_member) as handle:
            for raw_line in handle:
                if args.max_records and total_seen >= args.max_records:
                    break
                total_seen += 1
                record = json.loads(raw_line)
                cats = categories_of(record)
                if args.math_only and not is_math_bearing(cats):
                    continue
                selected_seen += 1
                primary = cats[0] if cats else "uncategorized"
                category_counts.update(cats)
                primary_category_counts[primary] += 1
                for left, right in zip(cats, cats[1:]):
                    category_pair_counts[(left, right)] += 1

                versions = record.get("versions")
                if isinstance(versions, list):
                    version_counts[len(versions)] += 1
                    if versions and isinstance(versions[0], dict):
                        created = str(versions[0].get("created", ""))
                        if len(created) >= 4:
                            year_counts[created[-4:]] += 1

                has_doi = bool(record.get("doi"))
                has_journal = bool(record.get("journal-ref"))
                status_counts["has_doi" if has_doi else "missing_doi"] += 1
                status_counts["has_journal_ref" if has_journal else "missing_journal_ref"] += 1

                combined = "\n".join([text_field(record, "title"), text_field(record, "abstract")])
                markers = marker_counts(combined)
                marker_totals.update(markers)
                category_marker_totals[primary].update(markers)

                if len(samples) < args.sample_records:
                    sample = {
                        "id": record.get("id"),
                        "title": record.get("title"),
                        "primary_category": primary,
                        "categories": cats,
                        "version_count": len(versions) if isinstance(versions, list) else 0,
                        "has_doi": has_doi,
                        "has_journal_ref": has_journal,
                        "abstract_sha256": sha256_text(text_field(record, "abstract")),
                        "marker_counts": {
                            key: markers[key]
                            for key in ("latex_command", "inline_math_span", "symbolic_token")
                        },
                    }
                    sample["packet_hash"] = sha256_text(stable_json(sample))
                    samples.append(sample)

    category_lines = ["category,count,primary_count,latex_command,inline_math_span,symbolic_token"]
    for category, count in category_counts.most_common():
        marker = category_marker_totals.get(category, Counter())
        category_lines.append(
            ",".join(
                [
                    csv_escape(category),
                    str(count),
                    str(primary_category_counts.get(category, 0)),
                    str(marker.get("latex_command", 0)),
                    str(marker.get("inline_math_span", 0)),
                    str(marker.get("symbolic_token", 0)),
                ]
            )
        )
    CATEGORY_CSV.write_text("\n".join(category_lines) + "\n", encoding="utf-8")

    marker_lines = ["marker,count"]
    for marker, count in marker_totals.most_common(500):
        marker_lines.append(f"{csv_escape(marker)},{count}")
    MARKER_CSV.write_text("\n".join(marker_lines) + "\n", encoding="utf-8")

    SAMPLES_JSONL.write_text("\n".join(stable_json(s) for s in samples) + "\n", encoding="utf-8")

    summary = {
        "schema": "arxiv_math_breakout_summary_v1",
        "archive_path": str(archive),
        "archive_sha256": archive_hash,
        "max_records": args.max_records,
        "total_records_scanned": total_seen,
        "math_bearing_records": selected_seen,
        "math_bearing_fraction": selected_seen / total_seen if total_seen else 0,
        "category_count": len(category_counts),
        "top_categories": category_counts.most_common(40),
        "top_primary_categories": primary_category_counts.most_common(40),
        "top_category_pairs": [[list(pair), count] for pair, count in category_pair_counts.most_common(40)],
        "marker_totals": dict(marker_totals),
        "top_markers": marker_totals.most_common(80),
        "doi_status": dict(status_counts),
        "top_years": year_counts.most_common(40),
        "version_count_distribution": dict(sorted(version_counts.items())),
        "sample_records": str(SAMPLES_JSONL.relative_to(REPO)),
        "category_csv": str(CATEGORY_CSV.relative_to(REPO)),
        "marker_csv": str(MARKER_CSV.relative_to(REPO)),
        "decision": "HOLD",
        "claim_boundary": (
            "Breakout uses arXiv metadata titles/abstracts/categories only. "
            "It estimates math-bearing route density and symbolic abstract markers, "
            "not full equation extraction from LaTeX sources."
        ),
    }
    summary["packet_hash"] = sha256_text(stable_json(summary))
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema": "arxiv_math_breakout_receipt_v1",
        "summary": str(SUMMARY.relative_to(REPO)),
        "archive_path": summary["archive_path"],
        "archive_sha256": summary["archive_sha256"],
        "total_records_scanned": total_seen,
        "math_bearing_records": selected_seen,
        "math_bearing_fraction": summary["math_bearing_fraction"],
        "category_count": summary["category_count"],
        "latex_command_count": marker_totals.get("latex_command", 0),
        "inline_math_span_count": marker_totals.get("inline_math_span", 0),
        "symbolic_token_count": marker_totals.get("symbolic_token", 0),
        "sample_record_count": len(samples),
        "packet_hash": summary["packet_hash"],
        "decision": summary["decision"],
        "claim_boundary": summary["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
