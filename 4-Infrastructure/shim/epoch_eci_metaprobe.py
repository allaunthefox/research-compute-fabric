#!/usr/bin/env python3
"""Epoch ECI benchmark-data metaprobe for local model-training context.

This imports Epoch AI's public ECI benchmark table as an external capability
prior. It does not score our local model unless we run those benchmarks. It
summarizes benchmark coverage and emits curriculum records for the physics-math
router to understand which external capability axes exist.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_URL = "https://epoch.ai/data/eci_benchmarks.csv"


def fetch_text(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Research-Stack-ECI-Metaprobe/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def read_rows(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    return [{key: str(value or "") for key, value in row.items()} for row in reader]


def normalized_entropy(values: list[str]) -> float:
    values = [value for value in values if value]
    if not values:
        return 0.0
    counts = Counter(values)
    total = sum(counts.values())
    h = -sum((count / total) * math.log2(count / total) for count in counts.values())
    max_h = math.log2(len(counts)) if len(counts) > 1 else 1.0
    return h / max_h


def infer_columns(rows: list[dict[str, str]]) -> dict[str, str | None]:
    if not rows:
        return {}
    columns = list(rows[0].keys())
    lowered = {col.lower(): col for col in columns}
    def find(*needles: str) -> str | None:
        for col in columns:
            lc = col.lower()
            if all(needle in lc for needle in needles):
                return col
        return None
    return {
        "model": find("model"),
        "benchmark": find("benchmark"),
        "score": find("score") or lowered.get("performance"),
        "release_date": find("date") or find("release"),
        "organization": find("organization") or find("developer") or find("creator"),
    }


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    cols = infer_columns(rows)
    summary: dict[str, Any] = {
        "row_count": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "inferred_columns": cols,
    }
    for name, col in cols.items():
        if not col:
            continue
        values = [row.get(col, "") for row in rows]
        counts = Counter(value for value in values if value)
        summary[f"{name}_unique"] = len(counts)
        summary[f"top_{name}s"] = counts.most_common(12)
        summary[f"{name}_entropy"] = normalized_entropy(values)
    benchmark_name_col = "benchmark" if rows and "benchmark" in rows[0] else None
    benchmark_id_col = "benchmark_id" if rows and "benchmark_id" in rows[0] else cols.get("benchmark")
    if benchmark_name_col and benchmark_id_col:
        id_to_name: dict[str, str] = {}
        for row in rows:
            benchmark_id = row.get(benchmark_id_col, "")
            benchmark_name = row.get(benchmark_name_col, "")
            if benchmark_id and benchmark_name and benchmark_id not in id_to_name:
                id_to_name[benchmark_id] = benchmark_name
        summary["benchmark_id_to_name_sample"] = dict(list(sorted(id_to_name.items()))[:24])
        summary["top_benchmark_names"] = [
            [id_to_name.get(str(benchmark_id), str(benchmark_id)), count]
            for benchmark_id, count in summary.get("top_benchmarks", [])
        ]
    for flag in ("is_math", "is_coding"):
        if rows and flag in rows[0]:
            true_count = sum(1 for row in rows if row.get(flag, "").lower() == "true")
            summary[f"{flag}_true_rows"] = true_count
    return summary


def curriculum_records(summary: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    top_benchmarks = summary.get("top_benchmark_names") or summary.get("top_benchmarks", [])
    prompt = {
        "task": "use_external_capability_prior",
        "source": "Epoch Capabilities Index benchmark table",
        "benchmark_count_hint": summary.get("benchmark_unique"),
        "top_benchmarks": top_benchmarks[:8],
        "math_rows": summary.get("is_math_true_rows"),
        "coding_rows": summary.get("is_coding_true_rows"),
        "instruction": "Explain how to use ECI as an external metaprobe axis without replacing local receipts.",
    }
    answer = {
        "selected": True,
        "use_as": "external_capability_prior",
        "claim_boundary": "benchmark-context-only",
        "decision": "Use ECI benchmark domains to choose evaluation axes for the physics-math router; do not treat ECI as proof of local model correctness.",
        "metaprobe_rule": "Local SFT, Ollama JSON, Lean evidence, and Tang receipts remain separate audit channels.",
    }
    records.append({
        "messages": [
            {"role": "system", "content": "You are a physics-math compression router. Return compact JSON with evidence boundaries."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
        ]
    })
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--cache", type=Path, default=Path("4-Infrastructure/shim/epoch_eci_benchmarks.csv"))
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/epoch_eci_metaprobe_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/epoch_eci_curriculum.jsonl"))
    parser.add_argument("--use-cache", action="store_true")
    args = parser.parse_args()

    if args.use_cache and args.cache.exists():
        text = args.cache.read_text(encoding="utf-8", errors="replace")
        source_mode = "cache"
    else:
        text = fetch_text(args.url)
        args.cache.parent.mkdir(parents=True, exist_ok=True)
        args.cache.write_text(text, encoding="utf-8")
        source_mode = "download"
    rows = read_rows(text)
    summary = summarize(rows)
    receipt = {
        "schema": "epoch_eci_metaprobe_receipt_v1",
        "claim_boundary": "ECI is an external benchmark/capability prior, not proof of local model behavior.",
        "source_url": args.url,
        "source_mode": source_mode,
        "cache": str(args.cache),
        "summary": summary,
        "lawful": summary.get("row_count", 0) > 0 and bool(summary.get("columns")),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(summary):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
