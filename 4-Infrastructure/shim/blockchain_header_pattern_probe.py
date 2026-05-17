#!/usr/bin/env python3
"""Probe numeric predictability in Bitcoin header JSONL streams.

The probe emits compression-route diagnostics only. It does not forecast price,
claim chain semantics, or prove Hutter improvement. The useful object is the
residual: if a declared predictor leaves small residuals, the stream may be a
good candidate for a receipt-bearing residual codec or logogram route.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, TextIO


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data/data/blockchain_corpus"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def iter_records(handle: TextIO, max_records: int | None) -> Iterable[dict[str, Any]]:
    count = 0
    for line in handle:
        if not line.strip():
            continue
        yield json.loads(line)
        count += 1
        if max_records is not None and count >= max_records:
            break


def signed_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def hex_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value), 16)
    except (TypeError, ValueError):
        return None


def deltas(values: list[int]) -> list[int]:
    return [b - a for a, b in zip(values, values[1:])]


def residuals(values: list[int], mode: str) -> list[int]:
    if len(values) < 2:
        return []
    if mode == "previous":
        return deltas(values)
    if mode == "linear_delta":
        first = deltas(values)
        return deltas(first)
    raise ValueError(mode)


def entropy_bits(values: list[int]) -> float:
    if not values:
        return 0.0
    total = len(values)
    counts = Counter(values)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def median_abs(values: list[int]) -> float:
    return float(statistics.median(abs(value) for value in values)) if values else 0.0


def summarize_residual(field: str, mode: str, raw_values: list[int], resids: list[int]) -> dict[str, Any]:
    raw_entropy = entropy_bits(raw_values)
    resid_entropy = entropy_bits(resids)
    unique_raw = len(set(raw_values))
    unique_resid = len(set(resids))
    improvement = raw_entropy - resid_entropy
    return {
        "field": field,
        "predictor": mode,
        "sample_count": len(raw_values),
        "residual_count": len(resids),
        "raw_unique": unique_raw,
        "residual_unique": unique_resid,
        "raw_entropy_bits_per_symbol": round(raw_entropy, 6),
        "residual_entropy_bits_per_symbol": round(resid_entropy, 6),
        "entropy_delta_bits_per_symbol": round(improvement, 6),
        "median_abs_residual": round(median_abs(resids), 6),
        "zero_residual_share": round(sum(1 for item in resids if item == 0) / len(resids), 6) if resids else 0.0,
        "route_candidate": (
            "ADMIT_RESIDUAL_ROUTE_CANDIDATE"
            if improvement > 0 and unique_resid <= unique_raw
            else "HOLD_RESIDUAL_ROUTE"
        ),
    }


def longest_run(values: list[Any]) -> dict[str, Any]:
    if not values:
        return {"value": None, "length": 0}
    best_value = values[0]
    best_length = 1
    current_value = values[0]
    current_length = 1
    for value in values[1:]:
        if value == current_value:
            current_length += 1
        else:
            if current_length > best_length:
                best_value = current_value
                best_length = current_length
            current_value = value
            current_length = 1
    if current_length > best_length:
        best_value = current_value
        best_length = current_length
    return {"value": best_value, "length": best_length}


def build_probe(records: list[dict[str, Any]], source_label: str) -> dict[str, Any]:
    heights = [signed_int(row.get("height")) for row in records]
    times = [signed_int(row.get("time")) for row in records]
    mediantimes = [signed_int(row.get("mediantime")) for row in records]
    ntx = [signed_int(row.get("nTx")) for row in records]
    nonces = [signed_int(row.get("nonce")) for row in records]
    chainwork = [hex_int(row.get("chainwork")) for row in records]
    bits = [row.get("bits") for row in records]
    versions = [signed_int(row.get("version")) for row in records]

    numeric = {
        "height": [value for value in heights if value is not None],
        "time": [value for value in times if value is not None],
        "mediantime": [value for value in mediantimes if value is not None],
        "nTx": [value for value in ntx if value is not None],
        "nonce": [value for value in nonces if value is not None],
        "chainwork": [value for value in chainwork if value is not None],
        "version": [value for value in versions if value is not None],
    }
    summaries = []
    for field, values in numeric.items():
        if len(values) < 3:
            continue
        summaries.append(summarize_residual(field, "previous", values, residuals(values, "previous")))
        summaries.append(summarize_residual(field, "linear_delta", values, residuals(values, "linear_delta")))

    summaries.sort(key=lambda item: item["entropy_delta_bits_per_symbol"], reverse=True)
    bits_values = [value for value in bits if value is not None]
    version_values = [value for value in versions if value is not None]
    height_values = numeric["height"]
    continuity_breaks = []
    for previous, current in zip(height_values, height_values[1:]):
        if current != previous + 1:
            continuity_breaks.append({"previous": previous, "current": current})

    payload = {
        "schema": "blockchain_header_pattern_probe_v0",
        "created_utc": now_iso(),
        "source_label": source_label,
        "claim_boundary": "Numeric residual and route-prior diagnostic only. This does not forecast price, prove consensus validity, claim compression gain, or claim Hutter Prize progress.",
        "record_count": len(records),
        "height_range": {
            "start": height_values[0] if height_values else None,
            "end": height_values[-1] if height_values else None,
            "continuity_break_count": len(continuity_breaks),
            "continuity_break_examples": continuity_breaks[:10],
        },
        "categorical_runs": {
            "bits_unique": len(set(bits_values)),
            "bits_longest_run": longest_run(bits_values),
            "version_unique": len(set(version_values)),
            "version_longest_run": longest_run(version_values),
        },
        "residual_summaries": summaries,
        "top_route_candidates": [
            item for item in summaries if item["route_candidate"] == "ADMIT_RESIDUAL_ROUTE_CANDIDATE"
        ][:10],
        "hutter_feedback_rule": (
            "Only fields with declared predictors, lower residual entropy, and replayable "
            "height-contiguous provenance may be promoted into a Hutter/logogram fixture. "
            "Compression gain remains HOLD until byte-exact codec baselines exist."
        ),
    }
    payload["payload_hash"] = sha256_text(stable_json({k: v for k, v in payload.items() if k != "payload_hash"}))
    payload["decision"] = (
        "ADMIT_HEADER_PATTERN_ROUTE_PRIORS"
        if payload["height_range"]["continuity_break_count"] == 0 and payload["top_route_candidates"]
        else "HOLD_HEADER_PATTERN_ROUTE_PRIORS"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="-", help="Bitcoin header JSONL path or '-' for stdin")
    parser.add_argument("--source-label", default=None)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    if args.source == "-":
        records = list(iter_records(sys.stdin, args.max_records))
        source_label = args.source_label or "stdin"
    else:
        path = Path(args.source)
        with path.open("r", encoding="utf-8") as handle:
            records = list(iter_records(handle, args.max_records))
        source_label = args.source_label or str(path)

    payload = build_probe(records, source_label)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
