#!/usr/bin/env python3
"""Tiny The Well-style schema probe.

This is a metadata-only replay fixture for The Well route surface. It does not
download, vendor, or score The Well data. It checks whether a field-dynamics
packet can preserve axes, field rank, boundary metadata, and dtype/shape
receipts before any HDF5 slice is admitted.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "the_well_tiny_probe"
RECEIPT = OUT_DIR / "the_well_tiny_schema_probe_receipt.json"
TABLE = OUT_DIR / "the_well_tiny_schema_probe_table.jsonl"


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    route_surface: str
    actual_schema: dict[str, Any]
    candidate_schema: dict[str, Any]
    negative_control: bool


BASE_SCHEMA = {
    "container": "hdf5",
    "dataset_family": "the_well_style_micro_fixture",
    "spatial_axes": ["x", "y"],
    "time_axis": "t",
    "grid_shape": [16, 16],
    "time_steps": 8,
    "fields": [
        {
            "name": "density",
            "rank": "scalar",
            "shape": ["t", "x", "y"],
            "dtype": "float32",
            "boundary": "periodic",
            "units": "normalized",
        },
        {
            "name": "velocity",
            "rank": "vector",
            "components": ["vx", "vy"],
            "shape": ["t", "x", "y", "component"],
            "dtype": "float32",
            "boundary": "periodic",
            "units": "normalized",
        },
    ],
    "split": "tiny_local_probe",
    "source_bytes_vendored": 0,
}


def with_field_rank(schema: dict[str, Any], field_name: str, rank: str) -> dict[str, Any]:
    clone = json.loads(json.dumps(schema))
    for field in clone["fields"]:
        if field["name"] == field_name:
            field["rank"] = rank
    return clone


def without_boundary(schema: dict[str, Any], field_name: str) -> dict[str, Any]:
    clone = json.loads(json.dumps(schema))
    for field in clone["fields"]:
        if field["name"] == field_name:
            field.pop("boundary", None)
    return clone


FIXTURES = [
    Fixture(
        fixture_id="well_schema_scalar_vector_admit",
        route_surface="The Well",
        actual_schema=BASE_SCHEMA,
        candidate_schema=BASE_SCHEMA,
        negative_control=False,
    ),
    Fixture(
        fixture_id="well_schema_wrong_rank_negative",
        route_surface="The Well",
        actual_schema=BASE_SCHEMA,
        candidate_schema=with_field_rank(BASE_SCHEMA, "velocity", "scalar"),
        negative_control=True,
    ),
    Fixture(
        fixture_id="well_schema_missing_boundary_hold",
        route_surface="The Well",
        actual_schema=BASE_SCHEMA,
        candidate_schema=without_boundary(BASE_SCHEMA, "density"),
        negative_control=False,
    ),
]


REQUIRED_TOP_LEVEL = {"container", "spatial_axes", "time_axis", "grid_shape", "time_steps", "fields"}
REQUIRED_FIELD_KEYS = {"name", "rank", "shape", "dtype", "boundary"}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def schema_errors(actual: dict[str, Any], candidate: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for key in sorted(REQUIRED_TOP_LEVEL):
        if key not in candidate:
            errors.append({"path": key, "error": "missing_required_key"})

    actual_fields = {field.get("name"): field for field in actual.get("fields", [])}
    candidate_fields = {field.get("name"): field for field in candidate.get("fields", [])}
    for name, actual_field in actual_fields.items():
        candidate_field = candidate_fields.get(name)
        if candidate_field is None:
            errors.append({"path": f"fields.{name}", "error": "missing_field"})
            continue
        for key in sorted(REQUIRED_FIELD_KEYS):
            if key not in candidate_field:
                errors.append({"path": f"fields.{name}.{key}", "error": "missing_required_key"})
                continue
            if candidate_field[key] != actual_field.get(key):
                errors.append(
                    {
                        "path": f"fields.{name}.{key}",
                        "error": "value_mismatch",
                        "actual": actual_field.get(key),
                        "candidate": candidate_field[key],
                    }
                )

    for key in ["container", "spatial_axes", "time_axis", "grid_shape", "time_steps"]:
        if key in candidate and candidate[key] != actual.get(key):
            errors.append({"path": key, "error": "value_mismatch", "actual": actual.get(key), "candidate": candidate[key]})
    return errors


def explicit_field_cell_count(schema: dict[str, Any]) -> int:
    grid_cells = 1
    for value in schema["grid_shape"]:
        grid_cells *= int(value)
    total = 0
    for field in schema["fields"]:
        components = len(field.get("components", [field["name"]]))
        total += int(schema["time_steps"]) * grid_cells * components
    return total


def run_fixture(fixture: Fixture) -> dict[str, Any]:
    errors = schema_errors(fixture.actual_schema, fixture.candidate_schema)
    replay_valid = not errors
    residual_declared = True

    encoded_payload = {
        "schema": fixture.candidate_schema,
        "route_surface": fixture.route_surface,
    }
    explicit_payload = {
        "cell_count": explicit_field_cell_count(fixture.actual_schema),
        "dtype": "float32",
        "uncompressed_float_cells": "omitted_metadata_probe",
    }
    residual_payload = {"schema_errors": errors}
    encoded_bytes = len(stable_json(encoded_payload).encode("utf-8"))
    explicit_bytes = len(stable_json(explicit_payload).encode("utf-8")) + explicit_field_cell_count(fixture.actual_schema) * 4
    residual_bytes = 0 if replay_valid else len(stable_json(residual_payload).encode("utf-8"))
    total_candidate_bytes = encoded_bytes + residual_bytes
    byte_gain = explicit_bytes - total_candidate_bytes

    if fixture.negative_control and replay_valid:
        status = "FAIL_NEGATIVE_CONTROL"
    elif replay_valid and residual_declared and byte_gain > 0 and not fixture.negative_control:
        status = "ADMIT_FIXTURE"
    else:
        status = "HOLD_DIAGNOSTIC"

    result = {
        "fixture_id": fixture.fixture_id,
        "route_surface": fixture.route_surface,
        "negative_control": fixture.negative_control,
        "actual_schema_hash": sha256_text(stable_json(fixture.actual_schema)),
        "candidate_schema_hash": sha256_text(stable_json(fixture.candidate_schema)),
        "schema_error_count": len(errors),
        "schema_errors": errors,
        "field_cell_count": explicit_field_cell_count(fixture.actual_schema),
        "replay_valid": replay_valid,
        "residual_declared": residual_declared,
        "encoded_bytes": encoded_bytes,
        "explicit_bytes": explicit_bytes,
        "residual_bytes": residual_bytes,
        "byte_gain": byte_gain,
        "status": status,
    }
    result["result_hash"] = sha256_text(stable_json({k: v for k, v in result.items() if k != "result_hash"}))
    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [run_fixture(fixture) for fixture in FIXTURES]
    with TABLE.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, sort_keys=True) + "\n")

    status_values = sorted({result["status"] for result in results})
    receipt = {
        "schema": "the_well_tiny_schema_probe_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixture_count": len(results),
        "table": rel(TABLE),
        "status_counts": {
            status: sum(1 for result in results if result["status"] == status)
            for status in status_values
        },
        "results": results,
        "decision": "HOLD",
        "claim_boundary": (
            "Tiny The Well-style metadata probe only. It tests field rank, axis, "
            "boundary, dtype, schema hash, residual, and byte-law accounting; it "
            "does not download The Well, does not vendor HDF5 data, and does not "
            "claim any benchmark result."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json({k: v for k, v in receipt.items() if k != "receipt_hash"}))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "table": rel(TABLE),
                "receipt_hash": receipt["receipt_hash"],
                "status_counts": receipt["status_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
