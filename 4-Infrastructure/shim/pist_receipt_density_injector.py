#!/usr/bin/env python3
"""PIST -> RRC receipt-density backfill injector.

NOTE (ontology migration):

This file is a **legacy shim**. It exists to keep historical backfill workflows
running while the AVM rewrite is underway.

**Target architecture:** Lean-only AVM ISA + backend shims.
- Lean defines all semantics.
- Shims do JSON/RDS I/O only.

This script still contains scoring math in Python (float-based) and therefore
MUST be treated as a non-authoritative conversion surface.

Rules until ported:
- Output is always `promotion = not_promoted`.
- Output must carry an explicit `strip_receipt` section explaining:
  - which constructs were computed in shim space
  - what must be ported to Lean/AVM

TODO(lean-port): Replace all scoring and warning decisions with Lean/AVM.

PARTIAL BOUNDARY: scoring logic ported to Lean; Python execution path not yet replaced.
  Ported (Lean is authoritative):
    - spectral_quality   → Semantics.RRC.ReceiptDensity.spectralQuality
    - shape_agreement    → Semantics.RRC.ReceiptDensity.shapeAgreement
    - axis_score         → Semantics.RRC.ReceiptDensity.axisScore
    - status_score       → Semantics.RRC.ReceiptDensity.statusScore
    - compute_density    → Semantics.RRC.ReceiptDensity.computeDensity
  Still executing in Python (must be replaced with Lean bindserver call):
    - spectral_quality(), shape_agreement(), axis_score(), status_score(), compute_density()
    - build_record(), align_payload() orchestration
    - stable_hash() canonical payload definition
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIM_DIR = Path(__file__).resolve().parent
if str(SHIM_DIR) not in sys.path:
    sys.path.insert(0, str(SHIM_DIR))

DEFAULT_RRC_FILE = REPO_ROOT / "6-Documentation/docs/rrc_equation_classification.md"
DEFAULT_PIST_REPORT = REPO_ROOT / "shared-data/rrc_pist_exact_validation.json"
DEFAULT_OUT = REPO_ROOT / "shared-data/rrc_receipt_density_backfill.json"
DEFAULT_RDS_TABLE = "ene.rrc_receipt_density"

ONTOLOGY_VERSION = "shim-ontology-migration-v1"

TARGET_AXES = {
    "projection_declared",
    "negative_control_strength",
    "witness_declared",
    "scale_band_declared",
    "shape_closure",
}

STATUS_BASE = {
    "BLOCKED": 0.0,
    "HOLD": 0.12,
    "CANDIDATE": 0.45,
    "REVIEWED": 0.78,
    "VERIFIED": 0.84,
}

SHAPE_DOMAIN = {
    "CognitiveLoadField": "analysis",
    "SignalShapedRouteCompiler": "topology",
    "ProjectableGeometryTopology": "geometry",
    "CadForceProbeReceipt": "physics",
    "LogogramProjection": "symbolic",
    "HoldForUnlawfulOrUnderspecifiedShape": "unknown",
}


@dataclass(frozen=True)
class RRCEquationRow:
    equation_id: str
    rrc_shape: str
    status: str
    top_axes: list[str]


@dataclass(frozen=True)
class ReceiptDensityRecord:
    receipt_version: str
    equation_id: str
    rrc_shape: str
    domain: str
    source_status: str
    receipt_density: float
    confidence: float
    density_components: dict[str, float]
    shape_prediction: dict[str, Any]
    top_axes: list[str]
    status: str
    promotion: str
    source: str
    receipt_hash: str
    warnings: list[str]


def stable_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def clamp01(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(1.0, value))


def parse_axis_list(raw: str) -> list[str]:
    return [part.strip().strip("`") for part in raw.split(",") if part.strip()]


def is_table_noise(equation: str, shape: str, status: str) -> bool:
    bad = {"", "---", "Equation", "RRC shape", "Status"}
    if equation in bad or shape in bad or status in bad:
        return True
    return bool(re.fullmatch(r"-+", equation)) or bool(re.fullmatch(r"-+", shape))


def parse_rrc_table(path: Path) -> list[RRCEquationRow]:
    if not path.exists():
        raise FileNotFoundError(f"RRC classification file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if "## Sample Projections" not in text:
        raise ValueError(f"No '## Sample Projections' section found in {path}")

    sample_section = text.split("## Sample Projections", 1)[1]
    sample_section = sample_section.split("\n## ", 1)[0]

    rows: list[RRCEquationRow] = []
    for line in sample_section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip().strip("`") for p in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        equation, shape, status, axes = parts[:4]
        if is_table_noise(equation, shape, status):
            continue
        rows.append(
            RRCEquationRow(
                equation_id=equation,
                rrc_shape=shape,
                status=status,
                top_axes=parse_axis_list(axes),
            )
        )
    return rows


def load_pist_predictions(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    predictions = data.get("predictions", [])
    out: dict[str, dict[str, Any]] = {}
    for pred in predictions:
        equation = str(pred.get("equation", ""))
        ground_truth = str(pred.get("ground_truth", ""))
        if is_table_noise(equation, ground_truth, pred.get("proxy_pred", "")):
            continue
        out[equation] = pred
    return out


def spectral_quality(pred: dict[str, Any] | None) -> float:
    if not pred:
        return 0.0

    rank = float(pred.get("rank_estimate") or 0.0)
    gap = float(pred.get("spectral_gap") or 0.0)
    crossing_density = float(pred.get("crossing_density") or 0.0)
    entropy = float(pred.get("strand_entropy") or 0.0)
    lap_zero = float(pred.get("laplacian_zero_count") or 0.0)

    rank_score = clamp01(rank / 8.0)
    gap_score = clamp01(gap)
    entropy_score = clamp01(entropy / 3.0)
    density_score = clamp01(crossing_density / 0.5)
    lap_score = 1.0 if lap_zero >= 1.0 else 0.45
    hash_score = 1.0 if pred.get("canonical_hash") and pred.get("matrix_hash") else 0.0

    return round(
        clamp01(
            0.24 * rank_score
            + 0.18 * gap_score
            + 0.18 * entropy_score
            + 0.12 * density_score
            + 0.12 * lap_score
            + 0.16 * hash_score
        ),
        6,
    )


def shape_agreement(row: RRCEquationRow, pred: dict[str, Any] | None) -> float:
    if not pred:
        return 0.0
    exact = pred.get("exact_pred")
    proxy = pred.get("proxy_pred")
    if exact == row.rrc_shape:
        return 1.0
    if proxy == row.rrc_shape:
        return 0.82
    if exact or proxy:
        return 0.35
    return 0.0


def axis_score(row: RRCEquationRow) -> float:
    if not row.top_axes:
        return 0.0
    hits = len(TARGET_AXES.intersection(row.top_axes))
    return round(clamp01(hits / 4.0), 6)


def status_score(row: RRCEquationRow) -> float:
    return STATUS_BASE.get(row.status.upper(), 0.2)


def compute_density(row: RRCEquationRow, pred: dict[str, Any] | None) -> tuple[float, float, dict[str, float], list[str]]:
    warnings: list[str] = []
    s_status = status_score(row)
    s_axes = axis_score(row)
    s_spectral = spectral_quality(pred)
    s_shape = shape_agreement(row, pred)

    if pred is None:
        warnings.append("missing_pist_prediction")
    elif s_shape < 0.5:
        warnings.append("pist_shape_disagreement")

    density = clamp01(
        0.26 * s_status
        + 0.24 * s_axes
        + 0.26 * s_spectral
        + 0.24 * s_shape
    )

    confidence = clamp01(
        0.20 * s_status
        + 0.20 * s_axes
        + 0.28 * s_spectral
        + 0.32 * s_shape
    )

    components = {
        "status_score": round(s_status, 6),
        "axis_score": round(s_axes, 6),
        "spectral_quality": round(s_spectral, 6),
        "shape_agreement": round(s_shape, 6),
    }
    return round(density, 6), round(confidence, 6), components, warnings


def build_record(row: RRCEquationRow, pred: dict[str, Any] | None) -> ReceiptDensityRecord:
    density, confidence, components, warnings = compute_density(row, pred)
    shape_prediction = {
        "ground_truth_hint": row.rrc_shape,
        "proxy_pred": pred.get("proxy_pred") if pred else None,
        "exact_pred": pred.get("exact_pred") if pred else None,
        "matrix_hash": pred.get("matrix_hash") if pred else None,
        "canonical_hash": pred.get("canonical_hash") if pred else None,
        "spectral_gap": pred.get("spectral_gap") if pred else None,
        "rank_estimate": pred.get("rank_estimate") if pred else None,
        "laplacian_zero_count": pred.get("laplacian_zero_count") if pred else None,
    }

    unsigned_payload = {
        "equation_id": row.equation_id,
        "rrc_shape": row.rrc_shape,
        "source_status": row.status,
        "receipt_density": density,
        "confidence": confidence,
        "shape_prediction": shape_prediction,
        "top_axes": row.top_axes,
        "promotion": "not_promoted",
        "source": "pist_receipt_density_injector_v1",
        "ontology_version": ONTOLOGY_VERSION,
    }
    receipt_hash = stable_hash(unsigned_payload)

    return ReceiptDensityRecord(
        receipt_version="pist-receipt-density-v1",
        equation_id=row.equation_id,
        rrc_shape=row.rrc_shape,
        domain=SHAPE_DOMAIN.get(row.rrc_shape, "unknown"),
        source_status=row.status,
        receipt_density=density,
        confidence=confidence,
        density_components=components,
        shape_prediction=shape_prediction,
        top_axes=row.top_axes,
        status="CANDIDATE" if density > 0.0 else "HOLD",
        promotion="not_promoted",
        source="pist_receipt_density_injector_v1",
        receipt_hash=receipt_hash,
        warnings=warnings,
    )


def summarize(records: list[ReceiptDensityRecord], total_rows: int, prediction_count: int) -> dict[str, Any]:
    by_shape = Counter(r.rrc_shape for r in records)
    by_status = Counter(r.status for r in records)
    warning_counts: Counter[str] = Counter()
    for r in records:
        warning_counts.update(r.warnings)

    densities = [r.receipt_density for r in records]
    confidences = [r.confidence for r in records]
    populated = sum(1 for r in records if r.receipt_density > 0.0)

    return {
        "receipt_version": "pist-receipt-density-v1",
        "ontology_version": ONTOLOGY_VERSION,
        "shim_role": "legacy_scoring_surface_pending_avm",
        "input_rows": total_rows,
        "records": len(records),
        "pist_predictions_loaded": prediction_count,
        "receipt_density_populated": populated,
        "receipt_density_missing": len(records) - populated,
        "coverage": round(populated / len(records), 6) if records else 0.0,
        "mean_receipt_density": round(sum(densities) / len(densities), 6) if densities else 0.0,
        "min_receipt_density": round(min(densities), 6) if densities else 0.0,
        "max_receipt_density": round(max(densities), 6) if densities else 0.0,
        "mean_confidence": round(sum(confidences) / len(confidences), 6) if confidences else 0.0,
        "by_shape": dict(sorted(by_shape.items())),
        "by_status": dict(sorted(by_status.items())),
        "warning_counts": dict(sorted(warning_counts.items())),
        "promotion_policy": "no automatic promotion; density populates routing evidence only",
        "float_policy": {
            "status": "legacy_float_math_present",
            "reason": "shim computes density components using Python float; must be ported to Lean/AVM",
        },
    }


def emit_jsonl(records: Iterable[ReceiptDensityRecord], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(asdict(record), sort_keys=True) + "\n")


def split_qualified_table(table: str) -> tuple[str, str]:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?", table):
        raise ValueError(f"Unsafe SQL table identifier: {table!r}")
    if "." in table:
        schema, name = table.split(".", 1)
    else:
        schema, name = "public", table
    return schema, name


def quote_ident(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier!r}")
    return '"' + identifier.replace('"', '""') + '"'


def create_sidecar_table(cur: Any, table: str) -> None:
    schema, name = split_qualified_table(table)
    q_schema = quote_ident(schema)
    q_name = quote_ident(name)
    full = f"{q_schema}.{q_name}"
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {q_schema}")
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {full} (
          equation_id TEXT PRIMARY KEY,
          rrc_shape TEXT NOT NULL,
          domain TEXT NOT NULL,
          source_status TEXT NOT NULL,
          receipt_density DOUBLE PRECISION NOT NULL,
          receipt_density_source TEXT NOT NULL,
          receipt_density_hash TEXT NOT NULL,
          receipt_density_status TEXT NOT NULL,
          receipt_density_warnings JSONB NOT NULL,
          confidence DOUBLE PRECISION NOT NULL,
          top_axes JSONB NOT NULL,
          shape_prediction JSONB NOT NULL,
          density_components JSONB NOT NULL,
          promotion TEXT NOT NULL CHECK (promotion = 'not_promoted'),
          payload JSONB NOT NULL,
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def upsert_sidecar_records(conn: Any, records: list[ReceiptDensityRecord], table: str) -> dict[str, Any]:
    schema, name = split_qualified_table(table)
    full = f"{quote_ident(schema)}.{quote_ident(name)}"
    now = datetime.now(timezone.utc).isoformat()
    rows = [asdict(r) for r in records]
    with conn.cursor() as cur:
        create_sidecar_table(cur, table)
        for row in rows:
            cur.execute(
                f"""
                INSERT INTO {full} (
                  equation_id,
                  rrc_shape,
                  domain,
                  source_status,
                  receipt_density,
                  receipt_density_source,
                  receipt_density_hash,
                  receipt_density_status,
                  receipt_density_warnings,
                  confidence,
                  top_axes,
                  shape_prediction,
                  density_components,
                  promotion,
                  payload,
                  updated_at
                ) VALUES (
                  %(equation_id)s,
                  %(rrc_shape)s,
                  %(domain)s,
                  %(source_status)s,
                  %(receipt_density)s,
                  %(source)s,
                  %(receipt_hash)s,
                  %(status)s,
                  %(warnings_json)s::jsonb,
                  %(confidence)s,
                  %(top_axes_json)s::jsonb,
                  %(shape_prediction_json)s::jsonb,
                  %(density_components_json)s::jsonb,
                  %(promotion)s,
                  %(payload_json)s::jsonb,
                  %(updated_at)s
                )
                ON CONFLICT (equation_id) DO UPDATE SET
                  rrc_shape = EXCLUDED.rrc_shape,
                  domain = EXCLUDED.domain,
                  source_status = EXCLUDED.source_status,
                  receipt_density = EXCLUDED.receipt_density,
                  receipt_density_source = EXCLUDED.receipt_density_source,
                  receipt_density_hash = EXCLUDED.receipt_density_hash,
                  receipt_density_status = EXCLUDED.receipt_density_status,
                  receipt_density_warnings = EXCLUDED.receipt_density_warnings,
                  confidence = EXCLUDED.confidence,
                  top_axes = EXCLUDED.top_axes,
                  shape_prediction = EXCLUDED.shape_prediction,
                  density_components = EXCLUDED.density_components,
                  promotion = EXCLUDED.promotion,
                  payload = EXCLUDED.payload,
                  updated_at = EXCLUDED.updated_at
                """,
                {
                    **row,
                    "warnings_json": json.dumps(row["warnings"], sort_keys=True),
                    "top_axes_json": json.dumps(row["top_axes"], sort_keys=True),
                    "shape_prediction_json": json.dumps(row["shape_prediction"], sort_keys=True),
                    "density_components_json": json.dumps(row["density_components"], sort_keys=True),
                    "payload_json": json.dumps(row, sort_keys=True),
                    "updated_at": now,
                },
            )
    conn.commit()
    return {
        "enabled": True,
        "mode": "sidecar",
        "table": table,
        "records_upserted": len(records),
        "promotion_policy": "not_promoted only",
    }


def write_rds(records: list[ReceiptDensityRecord], table: str, connect_timeout: int | None) -> dict[str, Any]:
    try:
        from rds_connect import connect_rds
    except ImportError as exc:
        raise RuntimeError(
            "--write-rds requires 4-Infrastructure/shim/rds_connect.py to be importable"
        ) from exc

    overrides: dict[str, Any] = {}
    if connect_timeout is not None:
        overrides["connect_timeout"] = connect_timeout
    conn = connect_rds(**overrides)
    try:
        return upsert_sidecar_records(conn, records, table)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate RRC receipt-density records from PIST outputs.")
    parser.add_argument("--rrc-file", type=Path, default=DEFAULT_RRC_FILE)
    parser.add_argument("--pist-report", type=Path, default=DEFAULT_PIST_REPORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--jsonl-out", type=Path, default=None, help="Optional JSONL output path for DB import.")
    parser.add_argument("--fail-on-missing-pist", action="store_true", help="Exit nonzero if any row lacks a PIST prediction.")
    parser.add_argument("--write-rds", action="store_true", help="Opt-in RDS write. Defaults to false / audit JSON only.")
    parser.add_argument("--rds-table", default=DEFAULT_RDS_TABLE, help=f"Qualified sidecar table. Default: {DEFAULT_RDS_TABLE}")
    parser.add_argument("--connect-timeout", type=int, default=10, help="RDS connection timeout override passed to rds_connect.connect_rds.")
    args = parser.parse_args(argv)

    rows = parse_rrc_table(args.rrc_file)
    predictions = load_pist_predictions(args.pist_report)

    records = [build_record(row, predictions.get(row.equation_id)) for row in rows]
    summary = summarize(records, total_rows=len(rows), prediction_count=len(predictions))

    rds_result = None
    if args.write_rds:
        rds_result = write_rds(records, table=args.rds_table, connect_timeout=args.connect_timeout)
        summary["rds_write"] = rds_result
    else:
        summary["rds_write"] = {"enabled": False, "reason": "--write-rds not set"}

    payload = {
        "summary": summary,
        "strip_receipt": {
            "ontology_version": ONTOLOGY_VERSION,
            "shim_role": "legacy_scoring_surface_pending_avm",
            "computed_in_shim": [
                "receipt_density",
                "confidence",
                "density_components",
                "warnings",
            ],
            "must_port_to_lean_avm": [
                "compute_density",
                "spectral_quality",
                "shape_agreement",
                "axis_score",
                "status_score",
                "warning assignment",
            ],
            "float_policy": "legacy_float_math_present; reject once AVM port is active",
        },
        "inputs": {
            "rrc_file": str(args.rrc_file),
            "pist_report": str(args.pist_report),
        },
        "claim_boundary": {
            "receipt_density_means": "routing evidence is populated (legacy shim surface)",
            "receipt_density_does_not_mean": "mathematical proof or promotion",
            "promotion_policy": "not_promoted for every generated record",
            "rds_policy": "--write-rds upserts sidecar receipt-density metadata only via rds_connect.connect_rds",
        },
        "records": [asdict(r) for r in records],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.jsonl_out is not None:
        args.jsonl_out.parent.mkdir(parents=True, exist_ok=True)
        emit_jsonl(records, args.jsonl_out)

    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Wrote audit JSON: {args.out}", file=sys.stderr)
    if args.jsonl_out is not None:
        print(f"Wrote JSONL import file: {args.jsonl_out}", file=sys.stderr)
    if rds_result is not None:
        print(f"RDS write complete: {rds_result}", file=sys.stderr)

    if args.fail_on_missing_pist and summary["warning_counts"].get("missing_pist_prediction", 0) > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
