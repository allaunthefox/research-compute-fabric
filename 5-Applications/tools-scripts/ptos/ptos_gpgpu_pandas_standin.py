#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
import os
import re
import sys
from typing import Dict, List

from jsonschema import ValidationError, validate

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover
    print("pandas is required for this stand-in analyzer.")
    print(f"Import error: {exc}")
    sys.exit(1)


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_INPUT = os.path.join(PROJECT_ROOT, "metadata_report.json")
DEFAULT_OUT_CSV = os.path.join(PROJECT_ROOT, "graph_os_risk_node_scores.csv")
DEFAULT_SCHEMA = os.path.join(PROJECT_ROOT, "schemas", "metadata_report.schema.json")


RISK_PATTERNS: Dict[str, Dict[str, object]] = {
    "human_cognitive_overdrive": {
        "weight": 3,
        "patterns": [
            "trigger_time_ms",
            "handover",
            "zero-latency",
            "snapback",
            "entrainment",
            "bio_epistemic_grounding",
            "equality_matching",
            "protective silences",
        ],
    },
    "autonomy_and_override": {
        "weight": 2,
        "patterns": [
            "force driver",
            "rehydrates archived state",
            "governance_hold",
            "triumvirate veto",
            "pending_committed",
            "circuit breaker",
        ],
    },
    "ultra_fast_systemic_coupling": {
        "weight": 2,
        "patterns": [
            "system_clock",
            "tick_s",
            "6.24e-12",
            "phase",
            "speed-of-light",
            "all computes",
            "pansubstrate",
        ],
    },
    "containment_and_access_boundary": {
        "weight": 2,
        "patterns": [
            "sandbox",
            "landlock",
            "geometry_contract_strict",
            "quorum",
            "threshold",
            "hold",
            "committed",
        ],
    },
}

SAFEGUARD_PATTERNS: Dict[str, Dict[str, object]] = {
    "governance_gate": {
        "weight": -2,
        "patterns": ["governance_hold", "triumvirate veto", "hold", "committed"],
    },
    "containment_boundary": {
        "weight": -2,
        "patterns": ["sandbox", "zk containment boundary", "landlock"],
    },
    "verification_redundancy": {
        "weight": -1,
        "patterns": ["9-nines", "parallel", "verify", "proof", "zk-stark"],
    },
}


def load_metadata(path: str) -> Dict[str, dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_schema(path: str = DEFAULT_SCHEMA) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_metadata_schema(data: Dict[str, dict], schema_path: str = DEFAULT_SCHEMA) -> None:
    schema = load_schema(schema_path)
    validate(instance=data, schema=schema)


def flatten_nodes(data: Dict[str, dict]) -> pd.DataFrame:
    if not isinstance(data, dict):
        raise ValueError("metadata input must be a JSON object keyed by node_id")
    rows: List[Dict[str, object]] = []
    for node_id, node in data.items():
        tier = node.get("tier", "")
        tags = node.get("tags", []) or []
        meta = node.get("metadata", {}) or {}
        module = meta.get("module", "")
        text_blob = " ".join(
            [
                str(module),
                " ".join(str(t) for t in tags),
                json.dumps(meta, sort_keys=True),
            ]
        ).lower()
        rows.append(
            {
                "node_id": node_id,
                "tier": tier,
                "module": module,
                "tags": ",".join(str(t) for t in tags),
                "text_blob": text_blob,
            }
        )
    return pd.DataFrame(rows)


def pattern_to_regex(pattern: str) -> str:
    # Use word boundaries for simple token-like patterns to reduce substring false positives.
    if re.fullmatch(r"[a-zA-Z0-9_]+", pattern):
        return rf"\b{re.escape(pattern)}\b"
    return re.escape(pattern)


def score_patterns(df: pd.DataFrame, catalog: Dict[str, Dict[str, object]], prefix: str) -> pd.DataFrame:
    out = df.copy()
    for name, spec in catalog.items():
        weight = int(spec["weight"])
        patterns = [str(p).lower() for p in spec["patterns"]]
        regex = "|".join(pattern_to_regex(p) for p in patterns)
        hit_col = f"{prefix}_{name}_hits"
        score_col = f"{prefix}_{name}_score"
        out[hit_col] = out["text_blob"].str.count(regex)
        out[score_col] = out[hit_col] * weight
    score_cols = [c for c in out.columns if c.startswith(f"{prefix}_") and c.endswith("_score")]
    out[f"{prefix}_total"] = out[score_cols].sum(axis=1)
    return out


def summarize(df: pd.DataFrame) -> Dict[str, object]:
    risk_cols = [c for c in df.columns if c.startswith("risk_") and c.endswith("_score")]
    guard_cols = [c for c in df.columns if c.startswith("guard_") and c.endswith("_score")]

    top_risky = (
        df.sort_values(by=["net_score", "risk_total"], ascending=[False, False])
        .head(5)[["node_id", "tier", "module", "risk_total", "guard_total", "net_score"]]
        .to_dict(orient="records")
    )

    totals = {
        "node_count": int(len(df)),
        "risk_total_sum": int(df["risk_total"].sum()),
        "guard_total_sum": int(df["guard_total"].sum()),
        "net_score_sum": int(df["net_score"].sum()),
        "high_risk_nodes": int((df["net_score"] >= 6).sum()),
        "moderate_risk_nodes": int(((df["net_score"] >= 3) & (df["net_score"] < 6)).sum()),
        "low_risk_nodes": int((df["net_score"] < 3).sum()),
    }

    by_tier = (
        df.groupby("tier", as_index=False)[["risk_total", "guard_total", "net_score"]]
        .sum()
        .sort_values("net_score", ascending=False)
        .to_dict(orient="records")
    )

    col_sums = {c: int(df[c].sum()) for c in (risk_cols + guard_cols)}

    return {
        "totals": totals,
        "by_tier": by_tier,
        "signal_totals": col_sums,
        "top_risky_nodes": top_risky,
    }


def main() -> int:
    in_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    out_csv = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_CSV

    if not os.path.exists(in_path):
        print(f"Input file not found: {in_path}")
        return 2

    data = load_metadata(in_path)
    try:
        validate_metadata_schema(data)
    except ValidationError as exc:
        print(f"Schema validation failed: {exc.message}")
        return 3

    df = flatten_nodes(data)
    df = score_patterns(df, RISK_PATTERNS, "risk")
    df = score_patterns(df, SAFEGUARD_PATTERNS, "guard")
    df["net_score"] = df["risk_total"] + df["guard_total"]

    keep_cols = [
        "node_id",
        "tier",
        "module",
        "tags",
        "risk_total",
        "guard_total",
        "net_score",
    ] + [c for c in df.columns if c.endswith("_hits")]

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df[keep_cols].to_csv(out_csv, index=False)

    summary = summarize(df)
    print(json.dumps(summary, indent=2))
    print(f"\nWrote node scores to: {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
