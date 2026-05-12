#!/usr/bin/env python3
"""Clean-room density primitives inspired by Kaggle notebook ideas.

This module does not vendor Kaggle notebook code. It reimplements the useful
ideas as Research Stack primitives:

* typed carrier narrowing with explicit precision policy
* column/shard projection plans for external stores
* coverage-map routing with residual jumps
* lossy bottleneck accounting with mandatory residual policy
* inference-appliance admission checks

The original Kaggle sources are cited as idea sources in the emitted receipt.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "kaggle_density_priors"
RECEIPT = OUT_DIR / "kaggle_density_cleanroom_primitives_receipt.json"

IDEA_SOURCES = [
    {
        "title": "Ubiquant Market Prediction chunked dtype reduction notebook excerpt",
        "url": "https://www.kaggle.com/competitions/ubiquant-market-prediction",
        "use": "idea source for typed carrier narrowing and chunked materialization",
    },
    {
        "title": "Ubiquant Parquet dataset",
        "url": "https://www.kaggle.com/robikscube/ubiquant-parquet",
        "use": "idea source for columnar projection and shard-local loading",
    },
    {
        "title": "Pixel Travel Map",
        "url": "https://www.kaggle.com/code/oxzplvifi/pixel-travel-map",
        "use": "idea source for binary coverage maps and hole-avoidant routing",
    },
    {
        "title": "Improved baseline Santa 2022",
        "url": "https://www.kaggle.com/code/crodoc/82409-improved-baseline-santa-2022",
        "use": "idea source for path-planning baseline comparison",
    },
    {
        "title": "Mercedes neural compression autoencoder notebook",
        "url": "https://www.kaggle.com/code/remidi/neural-compression-auto-encoder-lb-0-55",
        "use": "idea source for bottleneck coordinates and projection families",
    },
    {
        "title": "AIMO3 Eagle3 speculative decoding notebook",
        "url": "https://www.kaggle.com/code/khoinguyennguyen/eagle3-specdecoding-optional-context-compression",
        "use": "idea source for inference appliance routing and context handoff",
    },
]


INTEGER_DTYPES = [
    ("int8", -(2**7), 2**7 - 1),
    ("int16", -(2**15), 2**15 - 1),
    ("int32", -(2**31), 2**31 - 1),
    ("int64", -(2**63), 2**63 - 1),
]

UNSIGNED_DTYPES = [
    ("uint8", 0, 2**8 - 1),
    ("uint16", 0, 2**16 - 1),
    ("uint32", 0, 2**32 - 1),
    ("uint64", 0, 2**64 - 1),
]

FLOAT_DTYPES = [
    ("float16", 65504.0, "lossy_for_many_decimal_payloads"),
    ("float32", 3.4028235e38, "usual_low_memory_scientific_surface"),
    ("float64", 1.7976931348623157e308, "maximal_standard_float_surface"),
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


@dataclass(frozen=True)
class NumericFieldStats:
    name: str
    kind: str
    minimum: float
    maximum: float
    nullable: bool = False


@dataclass(frozen=True)
class DTypeDecision:
    field: str
    dtype: str
    decision: str
    residual_policy: str
    reason: str


def choose_integer_dtype(minimum: int, maximum: int, prefer_unsigned: bool = True) -> str:
    table = UNSIGNED_DTYPES if prefer_unsigned and minimum >= 0 else INTEGER_DTYPES
    for dtype, low, high in table:
        if low <= minimum and maximum <= high:
            return dtype
    return "uint64" if prefer_unsigned and minimum >= 0 else "int64"


def choose_float_dtype(minimum: float, maximum: float, precision_policy: str) -> tuple[str, str]:
    limit = max(abs(minimum), abs(maximum))
    if precision_policy == "exact_replay":
        return "float64", "exact replay requested; keep widest standard float carrier"
    if precision_policy == "bounded_residual_ok":
        for dtype, max_abs, note in FLOAT_DTYPES:
            if limit <= max_abs:
                return dtype, note
    if limit <= FLOAT_DTYPES[1][1]:
        return "float32", "default conservative low-memory carrier"
    return "float64", "range exceeds float32 carrier"


def plan_dtype(stats: NumericFieldStats, precision_policy: str = "bounded_residual_ok") -> DTypeDecision:
    if stats.kind == "integer":
        dtype = choose_integer_dtype(int(stats.minimum), int(stats.maximum))
        return DTypeDecision(
            field=stats.name,
            dtype=dtype,
            decision="ACCEPT",
            residual_policy="none_required_for_integer_range_downcast",
            reason=f"value range [{stats.minimum}, {stats.maximum}] fits {dtype}",
        )
    if stats.kind == "float":
        dtype, reason = choose_float_dtype(stats.minimum, stats.maximum, precision_policy)
        decision = "ACCEPT" if dtype == "float64" or precision_policy == "bounded_residual_ok" else "HOLD"
        residual = "required_if_downcast_changes_replay" if dtype != "float64" else "none_for_carrier_width"
        return DTypeDecision(stats.name, dtype, decision, residual, reason)
    return DTypeDecision(
        field=stats.name,
        dtype="category_dictionary",
        decision="HOLD",
        residual_policy="dictionary_and_unknown_category_sidecar_required",
        reason="non-numeric field requires explicit dictionary receipt",
    )


@dataclass(frozen=True)
class ColumnProjectionPlan:
    table_id: str
    columns: tuple[str, ...]
    shard_key: str | None = None
    shard_value: str | None = None

    def receipt(self) -> dict[str, Any]:
        payload = asdict(self)
        return {
            "schema": "column_projection_plan_v1",
            "payload": payload,
            "plan_hash": sha256_text(stable_json(payload)),
            "decision": "ACCEPT" if self.columns else "HOLD",
            "residual_policy": "unselected_columns_are_external_store_references",
        }


@dataclass(frozen=True)
class GridPoint:
    x: int
    y: int


@dataclass(frozen=True)
class CoverageStep:
    start: GridPoint
    end: GridPoint
    kind: str
    cost: float


class CoverageMapRouter:
    """Small deterministic coverage router with hole-avoidant down preference."""

    def __init__(self, width: int, height: int, start: GridPoint):
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if not (0 <= start.x < width and 0 <= start.y < height):
            raise ValueError("start must be inside grid")
        self.width = width
        self.height = height
        self.current = start
        self.unvisited = {(x, y) for x in range(width) for y in range(height)}
        self.unvisited.discard((start.x, start.y))

    def neighbors(self, point: GridPoint) -> Iterable[GridPoint]:
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            x = point.x + dx
            y = point.y + dy
            if 0 <= x < self.width and 0 <= y < self.height:
                yield GridPoint(x, y)

    def nearest_unvisited(self) -> GridPoint | None:
        if not self.unvisited:
            return None
        x0, y0 = self.current.x, self.current.y
        x, y = min(self.unvisited, key=lambda p: (abs(p[0] - x0) + abs(p[1] - y0), p[1], p[0]))
        return GridPoint(x, y)

    def next_step(self) -> CoverageStep | None:
        if not self.unvisited:
            return None
        start = self.current
        down = GridPoint(start.x, start.y - 1)
        if (down.x, down.y) in self.unvisited:
            end = down
            kind = "down_first_local"
            cost = 1.0
        else:
            local = [p for p in self.neighbors(start) if (p.x, p.y) in self.unvisited]
            if local:
                end = min(local, key=lambda p: (p.y, abs(p.x - start.x), p.x))
                kind = "least_cost_local"
                cost = math.dist((start.x, start.y), (end.x, end.y))
            else:
                end = self.nearest_unvisited()
                if end is None:
                    return None
                kind = "residual_jump_to_nearest_unvisited"
                cost = abs(end.x - start.x) + abs(end.y - start.y)
        self.unvisited.discard((end.x, end.y))
        self.current = end
        return CoverageStep(start, end, kind, cost)


@dataclass(frozen=True)
class BottleneckPlan:
    source_dimensions: int
    latent_dimensions: int
    reconstruction_declared: bool
    residual_declared: bool

    def decision(self) -> str:
        if self.latent_dimensions <= 0 or self.latent_dimensions >= self.source_dimensions:
            return "HOLD"
        if not (self.reconstruction_declared and self.residual_declared):
            return "HOLD"
        return "ACCEPT"

    def receipt(self) -> dict[str, Any]:
        payload = asdict(self)
        return {
            "schema": "bottleneck_plan_v1",
            "payload": payload,
            "compression_ratio_nominal": self.source_dimensions / max(self.latent_dimensions, 1),
            "decision": self.decision(),
            "residual_policy": "required_for_lossless_replay",
            "plan_hash": sha256_text(stable_json(payload)),
        }


@dataclass(frozen=True)
class InferenceAppliancePlan:
    offline_wheelhouse: bool
    deterministic_tool_sandbox: bool
    answer_range: tuple[int, int]
    consensus_attempts: int
    context_handoff_enabled: bool
    context_handoff_schema_declared: bool

    def decision(self) -> str:
        low, high = self.answer_range
        if not self.offline_wheelhouse:
            return "HOLD"
        if not self.deterministic_tool_sandbox:
            return "HOLD"
        if low < 0 or high < low:
            return "HOLD"
        if self.consensus_attempts < 1:
            return "HOLD"
        if self.context_handoff_enabled and not self.context_handoff_schema_declared:
            return "HOLD"
        return "ACCEPT"

    def receipt(self) -> dict[str, Any]:
        payload = asdict(self)
        return {
            "schema": "inference_appliance_plan_v1",
            "payload": payload,
            "decision": self.decision(),
            "residual_policy": "handoff_summary_required_when_context_is_reset",
            "plan_hash": sha256_text(stable_json(payload)),
        }


def build_receipt() -> dict[str, Any]:
    dtype_examples = [
        plan_dtype(NumericFieldStats("time_id", "integer", 0, 1219)),
        plan_dtype(NumericFieldStats("target", "float", -9.5, 12.1), precision_policy="exact_replay"),
        plan_dtype(NumericFieldStats("feature_f0", "float", -18.0, 47.1), precision_policy="bounded_residual_ok"),
        plan_dtype(NumericFieldStats("row_id", "object", 0, 0)),
    ]
    router = CoverageMapRouter(4, 4, GridPoint(0, 3))
    steps = [asdict(router.next_step()) for _ in range(5)]
    projection = ColumnProjectionPlan("ubiquant_low_mem", ("time_id", "investment_id", "target"), "investment_id", "529")
    bottleneck = BottleneckPlan(304, 12, reconstruction_declared=True, residual_declared=True)
    appliance = InferenceAppliancePlan(
        offline_wheelhouse=True,
        deterministic_tool_sandbox=True,
        answer_range=(0, 99999),
        consensus_attempts=8,
        context_handoff_enabled=True,
        context_handoff_schema_declared=True,
    )
    receipt = {
        "schema": "kaggle_density_cleanroom_primitives_receipt_v1",
        "implementation": str(Path(__file__).relative_to(REPO)),
        "idea_sources": IDEA_SOURCES,
        "license_boundary": (
            "Original Kaggle notebook code is not vendored or relicensed here. "
            "This file is an original Research Stack implementation of abstract "
            "route laws inspired by the cited sources."
        ),
        "dtype_examples": [asdict(item) for item in dtype_examples],
        "projection_example": projection.receipt(),
        "coverage_steps_example": steps,
        "bottleneck_example": bottleneck.receipt(),
        "inference_appliance_example": appliance.receipt(),
        "decision": "ACCEPT",
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = build_receipt()
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
