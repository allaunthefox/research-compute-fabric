#!/usr/bin/env python3
"""Eigenprobe for Parquet/logogram efficiency outcomes.

This reads the Parquet logogram efficiency receipt and asks why the measured
byte outcomes happen. The probe builds a small feature matrix per sampled
Parquet source, decomposes the standardized covariance matrix, and records the
dominant axes plus feature correlations against the packet-vs-Parquet result.
With four fixtures this is diagnostic, not statistical proof.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "shared-data" / "data" / "parquet_logogram_efficiency" / "parquet_logogram_efficiency.json"
INPUT_RECEIPT = REPO / "shared-data" / "data" / "parquet_logogram_efficiency" / "parquet_logogram_efficiency_receipt.json"
OUT_DIR = REPO / "shared-data" / "data" / "parquet_logogram_eigenprobe"
PAYLOAD_JSON = OUT_DIR / "parquet_logogram_eigenprobe.json"
SUMMARY = OUT_DIR / "parquet_logogram_eigenprobe.md"
RECEIPT = OUT_DIR / "parquet_logogram_eigenprobe_receipt.json"
TIDDLER = (
    REPO
    / "6-Documentation"
    / "tiddlywiki-local"
    / "wiki"
    / "tiddlers"
    / "Parquet Logogram Eigenprobe.tid"
)


FEATURES = [
    "sample_rows",
    "sample_columns",
    "sample_parquet_bytes",
    "canonical_object_bytes",
    "object_to_parquet_expansion",
    "species_payload_bytes",
    "species_packet_bytes",
    "species_to_parquet_ratio",
    "schema_key_reuse_ratio",
    "hybrid_sidecar_packet_bytes",
    "hybrid_overhead_ratio",
    "prediction_cache_column_ratio",
    "ram_trace_column_ratio",
    "parquet_native_column_ratio",
    "species_atom_density",
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def verify_embedded_hash(obj: dict[str, Any], embedded_key: str, exclude_keys: set[str] | None = None) -> dict[str, Any]:
    exclude = {embedded_key, *(exclude_keys or set())}
    embedded = obj.get(embedded_key)
    recomputed = hash_obj({k: v for k, v in obj.items() if k not in exclude})
    return {
        "embedded": embedded,
        "recomputed": recomputed,
        "matches": embedded == recomputed,
    }


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def route_ratio(item: dict[str, Any], route: str) -> float:
    counts = item.get("hybrid_sidecar", {}).get("route_counts", {})
    total = sum(counts.values())
    return counts.get(route, 0) / total if total else 0.0


def source_vector(item: dict[str, Any]) -> dict[str, float]:
    sample = float(item["sample_parquet_bytes"])
    canonical = float(item["canonical_object_bytes"])
    species_payload = float(item["logogram_species_payload_bytes"])
    species_packet = float(item["species_logogram"]["packet_bytes"])
    sidecar_packet = float(item.get("hybrid_sidecar", {}).get("logogram", {}).get("packet_bytes", 0))
    atom_count = float(item["species_logogram"].get("atom_count", 0))
    return {
        "sample_rows": float(item["schema"]["sample_rows"]),
        "sample_columns": float(item["schema"]["sample_columns"]),
        "sample_parquet_bytes": sample,
        "canonical_object_bytes": canonical,
        "object_to_parquet_expansion": canonical / sample if sample else 0.0,
        "species_payload_bytes": species_payload,
        "species_packet_bytes": species_packet,
        "species_to_parquet_ratio": species_packet / sample if sample else 0.0,
        "schema_key_reuse_ratio": float(item["measured"]["schema_key_reuse_payload_gain_ratio"]),
        "hybrid_sidecar_packet_bytes": sidecar_packet,
        "hybrid_overhead_ratio": sidecar_packet / sample if sample else 0.0,
        "prediction_cache_column_ratio": route_ratio(item, "prediction_cache"),
        "ram_trace_column_ratio": route_ratio(item, "ram_trace"),
        "parquet_native_column_ratio": route_ratio(item, "parquet_native"),
        "species_atom_density": atom_count / species_payload if species_payload else 0.0,
    }


def corr(xs: np.ndarray, ys: np.ndarray) -> float:
    if np.std(xs) == 0 or np.std(ys) == 0:
        return 0.0
    return float(np.corrcoef(xs, ys)[0, 1])


def component_entry(index: int, value: float, vector: np.ndarray, explained: float, names: list[str]) -> dict[str, Any]:
    loadings = sorted(
        [{"feature": names[i], "loading": round(float(vector[i]), 6)} for i in range(len(names))],
        key=lambda item: abs(item["loading"]),
        reverse=True,
    )
    return {
        "component": index + 1,
        "eigenvalue": round(float(value), 6),
        "explained_variance_ratio": round(float(explained), 6),
        "top_loadings": loadings[:8],
    }


def build_payload() -> dict[str, Any]:
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    receipt = json.loads(INPUT_RECEIPT.read_text(encoding="utf-8")) if INPUT_RECEIPT.exists() else {}
    input_payload_verification = verify_embedded_hash(data, "payload_hash")
    input_receipt_verification = (
        verify_embedded_hash(receipt, "receipt_hash", {"generated_at_utc"})
        if receipt
        else {"embedded": None, "recomputed": None, "matches": False}
    )
    rows = []
    for item in data["sources"]:
        vector = source_vector(item)
        rows.append(
            {
                "name": item["name"],
                "source": item["source"],
                "target_gain_vs_parquet": float(item["measured"]["gain_vs_sample_parquet_ratio"]),
                "target_hybrid_materialization_avoidance": float(item["measured"].get("hybrid_materialization_avoidance_ratio", 0.0)),
                "features": vector,
            }
        )
    matrix = np.array([[row["features"][feature] for feature in FEATURES] for row in rows], dtype=float)
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    stds[stds == 0] = 1.0
    standardized = (matrix - means) / stds
    covariance = np.cov(standardized, rowvar=False)
    values, vectors = np.linalg.eigh(covariance)
    order = np.argsort(values)[::-1]
    values = values[order]
    vectors = vectors[:, order]
    total = float(values.sum()) or 1.0
    components = [
        component_entry(i, values[i], vectors[:, i], values[i] / total, FEATURES)
        for i in range(min(3, len(values)))
    ]
    target = np.array([row["target_gain_vs_parquet"] for row in rows], dtype=float)
    hybrid_target = np.array([row["target_hybrid_materialization_avoidance"] for row in rows], dtype=float)
    correlations = sorted(
        [
            {
                "feature": feature,
                "corr_gain_vs_parquet": round(corr(matrix[:, i], target), 6),
                "corr_hybrid_materialization": round(corr(matrix[:, i], hybrid_target), 6),
            }
            for i, feature in enumerate(FEATURES)
        ],
        key=lambda item: abs(item["corr_gain_vs_parquet"]),
        reverse=True,
    )
    scores = standardized @ vectors
    for row_index, row in enumerate(rows):
        row["component_scores"] = {
            f"pc{i + 1}": round(float(scores[row_index, i]), 6)
            for i in range(min(3, scores.shape[1]))
        }
    input_hashes_recompute = input_payload_verification["matches"] and input_receipt_verification["matches"]
    payload = {
        "schema": "parquet_logogram_eigenprobe_v1",
        "input_payload": rel(INPUT),
        "input_payload_hash": input_payload_verification["recomputed"],
        "input_payload_hash_embedded": input_payload_verification["embedded"],
        "input_payload_hash_recomputes": input_payload_verification["matches"],
        "input_receipt": rel(INPUT_RECEIPT),
        "input_receipt_hash": input_receipt_verification["recomputed"],
        "input_receipt_hash_embedded": input_receipt_verification["embedded"],
        "input_receipt_hash_recomputes": input_receipt_verification["matches"],
        "claim_boundary": (
            "Eigenprobe diagnostic only. Four fixture rows are enough to explain the "
            "current accounting direction, not enough for statistical generalization. "
            "All equations remain HOLD until larger fixture sweeps and negative controls."
        ),
        "feature_names": FEATURES,
        "rows": rows,
        "principal_components": components,
        "feature_target_correlations": correlations,
        "interpretation": [
            "Parquet is winning raw bytes because it already compresses the physical columnar table; WLG2 is currently a generic XML/wiki-oriented logogram packet, so large free-text/content columns inflate the species packet.",
            "The equation tables show strong schema/key reuse, so logogram species payloads beat object-row canonical forms, but that gain is not enough to beat Parquet compression.",
            "The connectome summary is the small positive case because the table is tiny, low-column, and highly structured; the sidecar/reuse signal is large relative to payload.",
            "The hybrid path is different: its cost is a small sidecar overhead over Parquet, while its gain is avoided canonical materialization plus cache/trace routing, not replacement compression.",
        ],
        "decision": (
            "ADMIT_PARQUET_LOGOGRAM_EIGENPROBE_AS_HOLD_DIAGNOSTIC"
            if input_hashes_recompute
            else "HOLD_PARQUET_LOGOGRAM_EIGENPROBE_INPUT_HASH_MISMATCH"
        ),
    }
    payload["aggregates"] = {
        "source_count": len(rows),
        "feature_count": len(FEATURES),
        "component_count": len(components),
        "top_gain_correlations": correlations[:5],
        "dominant_component": components[0] if components else None,
    }
    payload["payload_hash"] = hash_obj({k: v for k, v in payload.items() if k != "payload_hash"})
    return payload


def build_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "parquet_logogram_eigenprobe_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "payload_hash": payload["payload_hash"],
        "input_payload_hash": payload["input_payload_hash"],
        "input_payload_hash_recomputes": payload["input_payload_hash_recomputes"],
        "input_receipt_hash": payload["input_receipt_hash"],
        "input_receipt_hash_recomputes": payload["input_receipt_hash_recomputes"],
        "aggregates": payload["aggregates"],
        "decision": payload["decision"],
        "claim_boundary": payload["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Parquet Logogram Eigenprobe",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        "## Input Verification",
        "",
        f"- Payload hash recomputes: `{payload['input_payload_hash_recomputes']}`",
        f"- Receipt hash recomputes: `{payload['input_receipt_hash_recomputes']}`",
        "",
        payload["claim_boundary"],
        "",
        "## Interpretation",
        "",
    ]
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Principal Components", ""])
    for component in payload["principal_components"]:
        top = ", ".join(f"{item['feature']}={item['loading']}" for item in component["top_loadings"][:5])
        lines.append(
            f"- PC{component['component']}: eigenvalue `{component['eigenvalue']}`, "
            f"explained `{component['explained_variance_ratio']}`; {top}"
        )
    lines.extend(["", "## Target Correlations", "", "| Feature | Corr gain vs Parquet | Corr hybrid materialization |", "|---|---:|---:|"])
    for item in payload["feature_target_correlations"]:
        lines.append(f"| {item['feature']} | {item['corr_gain_vs_parquet']} | {item['corr_hybrid_materialization']} |")
    lines.extend(["", "## Source Scores", "", "| Source | Gain vs Parquet | Hybrid materialization | PC1 | PC2 | PC3 |", "|---|---:|---:|---:|---:|---:|"])
    for row in payload["rows"]:
        scores = row["component_scores"]
        lines.append(
            f"| `{row['source']}` | {row['target_gain_vs_parquet']} | {row['target_hybrid_materialization_avoidance']} | "
            f"{scores.get('pc1')} | {scores.get('pc2')} | {scores.get('pc3')} |"
        )
    lines.extend(["", "## Receipt", "", f"`{rel(RECEIPT)}`"])
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "title: Parquet Logogram Eigenprobe",
        "tags: Parquet Logogram Eigenprobe HOLD Receipt",
        "type: text/vnd.tiddlywiki",
        "",
        "! Parquet Logogram Eigenprobe",
        "",
        f"Decision: `{payload['decision']}`",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        "!! Input Verification",
        "",
        f"* Payload hash recomputes: `{payload['input_payload_hash_recomputes']}`",
        f"* Receipt hash recomputes: `{payload['input_receipt_hash_recomputes']}`",
        "",
        "!! Why The Result Happens",
        "",
    ]
    for item in payload["interpretation"]:
        lines.append(f"* {item}")
    lines.extend(["", "!! Dominant Axis", ""])
    dominant = payload["aggregates"]["dominant_component"]
    if dominant:
        lines.append(f"PC{dominant['component']} explains `{dominant['explained_variance_ratio']}` of fixture variance.")
        for item in dominant["top_loadings"][:6]:
            lines.append(f"* `{item['feature']}`: `{item['loading']}`")
    lines.extend(
        [
            "",
            "!! Boundary",
            "",
            payload["claim_boundary"],
            "",
            "!! Links",
            "",
            "* [[Parquet Logogram Efficiency]]",
            "* [[Combined Approach Equation Surface]]",
            "",
            f"Receipt: `{rel(RECEIPT)}`",
        ]
    )
    TIDDLER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    receipt = build_receipt(payload)
    PAYLOAD_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(payload, receipt)
    write_tiddler(payload, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
