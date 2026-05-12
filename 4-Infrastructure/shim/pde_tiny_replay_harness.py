#!/usr/bin/env python3
"""Tiny PDE-style replay harness.

This is the first local replay fixture for the PDEBench route surface. It uses
deterministic built-in micro-fixtures only: no external PDEBench data is
downloaded, vendored, or scored.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "pde_tiny_replay"
RECEIPT = OUT_DIR / "pde_tiny_replay_receipt.json"
TABLE = OUT_DIR / "pde_tiny_replay_table.jsonl"


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    route_surface: str
    law_family: str
    grid_n: int
    steps: int
    shift_per_step: int
    truth_boundary: str
    candidate_boundary: str
    initial_support: list[int]
    negative_control: bool


FIXTURES = [
    Fixture(
        fixture_id="advection_periodic_exact_shift_admit",
        route_surface="PDEBench",
        law_family="linear_advection_integer_cfl",
        grid_n=64,
        steps=48,
        shift_per_step=1,
        truth_boundary="periodic",
        candidate_boundary="periodic",
        initial_support=[0, 3, 7, 15, 31],
        negative_control=False,
    ),
    Fixture(
        fixture_id="advection_wrong_boundary_negative",
        route_surface="PDEBench",
        law_family="linear_advection_integer_cfl",
        grid_n=64,
        steps=48,
        shift_per_step=1,
        truth_boundary="periodic",
        candidate_boundary="zero_outflow",
        initial_support=[0, 3, 7, 15, 31],
        negative_control=True,
    ),
    Fixture(
        fixture_id="advection_short_exact_hold_diagnostic",
        route_surface="PDEBench",
        law_family="linear_advection_integer_cfl",
        grid_n=8,
        steps=2,
        shift_per_step=1,
        truth_boundary="periodic",
        candidate_boundary="periodic",
        initial_support=[0, 3],
        negative_control=False,
    ),
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def initial_state(grid_n: int, support: list[int]) -> list[int]:
    values = [0] * grid_n
    for index in support:
        values[index % grid_n] = 1
    return values


def step_advection(values: list[int], shift: int, boundary: str) -> list[int]:
    out = [0] * len(values)
    for index, value in enumerate(values):
        target = index + shift
        if boundary == "periodic":
            out[target % len(values)] = value
        elif boundary == "zero_outflow":
            if 0 <= target < len(values):
                out[target] = value
        else:
            raise ValueError(f"unsupported boundary {boundary}")
    return out


def trajectory(fixture: Fixture, boundary: str) -> list[list[int]]:
    rows = [initial_state(fixture.grid_n, fixture.initial_support)]
    for _ in range(fixture.steps):
        rows.append(step_advection(rows[-1], fixture.shift_per_step, boundary))
    return rows


def mismatch_rows(truth: list[list[int]], candidate: list[list[int]]) -> list[dict[str, int]]:
    mismatches: list[dict[str, int]] = []
    for t_index, (truth_row, candidate_row) in enumerate(zip(truth, candidate)):
        for x_index, (truth_value, candidate_value) in enumerate(zip(truth_row, candidate_row)):
            if truth_value != candidate_value:
                mismatches.append(
                    {
                        "t": t_index,
                        "x": x_index,
                        "truth": truth_value,
                        "candidate": candidate_value,
                    }
                )
    return mismatches


def run_fixture(fixture: Fixture) -> dict[str, Any]:
    truth = trajectory(fixture, fixture.truth_boundary)
    candidate = trajectory(fixture, fixture.candidate_boundary)
    mismatches = mismatch_rows(truth, candidate)
    replay_valid = not mismatches
    residual_declared = True

    encoded_payload = {
        "law_family": fixture.law_family,
        "grid_n": fixture.grid_n,
        "steps": fixture.steps,
        "shift_per_step": fixture.shift_per_step,
        "boundary": fixture.candidate_boundary,
        "initial_support": fixture.initial_support,
    }
    explicit_payload = {
        "trajectory": truth,
    }
    residual_payload = {"mismatches": mismatches}

    encoded_bytes = len(stable_json(encoded_payload).encode("utf-8"))
    explicit_bytes = len(stable_json(explicit_payload).encode("utf-8"))
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
        "law_family": fixture.law_family,
        "truth_boundary": fixture.truth_boundary,
        "candidate_boundary": fixture.candidate_boundary,
        "negative_control": fixture.negative_control,
        "grid_n": fixture.grid_n,
        "steps": fixture.steps,
        "shift_per_step": fixture.shift_per_step,
        "initial_support": fixture.initial_support,
        "trajectory_hash": sha256_text(stable_json(truth)),
        "candidate_hash": sha256_text(stable_json(candidate)),
        "mismatch_count": len(mismatches),
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
        "schema": "pde_tiny_replay_receipt_v1",
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
            "Tiny PDE-style replay fixture only. It tests deterministic local "
            "advection replay, wrong-boundary negative controls, residual "
            "accounting, and byte-law diagnostics; it is not PDEBench data ingest, "
            "not a PDEBench benchmark score, and not a compression benchmark."
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
