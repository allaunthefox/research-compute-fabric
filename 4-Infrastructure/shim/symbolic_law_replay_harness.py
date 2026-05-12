#!/usr/bin/env python3
"""Tiny symbolic-law replay harness.

This is the first replay fixture for the SRBench/Feynman route surface. It uses
small built-in ground-truth laws and deliberate mutations to test deterministic
replay, residual accounting, and HOLD/ADMIT separation without downloading any
external dataset.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "symbolic_law_replay"
RECEIPT = OUT_DIR / "symbolic_law_replay_receipt.json"
TABLE = OUT_DIR / "symbolic_law_replay_table.jsonl"

getcontext().prec = 40


ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a**b,
}
ALLOWED_UNARY = {
    ast.UAdd: lambda a: a,
    ast.USub: lambda a: -a,
}
ALLOWED_FUNCS = {
    "sin": Decimal,
    "cos": Decimal,
}


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    route_surface: str
    truth_formula: str
    candidate_formula: str
    variables: list[str]
    samples: list[dict[str, str]]
    negative_control: bool


FIXTURES = [
    Fixture(
        fixture_id="feynman_newton_gravity_admit",
        route_surface="SRBench / Feynman",
        truth_formula="G*m1*m2/(r**2)",
        candidate_formula="G*m1*m2/(r**2)",
        variables=["G", "m1", "m2", "r"],
        samples=[
            {"G": "6.67430e-11", "m1": "5.972e24", "m2": "7.348e22", "r": "3.844e8"},
            {"G": "6.67430e-11", "m1": "1.989e30", "m2": "5.972e24", "r": "1.496e11"},
            {"G": "6.67430e-11", "m1": "1.0e5", "m2": "2.0e5", "r": "3000"},
        ],
        negative_control=False,
    ),
    Fixture(
        fixture_id="feynman_newton_gravity_negative",
        route_surface="SRBench / Feynman",
        truth_formula="G*m1*m2/(r**2)",
        candidate_formula="G*m1*m2/r",
        variables=["G", "m1", "m2", "r"],
        samples=[
            {"G": "6.67430e-11", "m1": "5.972e24", "m2": "7.348e22", "r": "3.844e8"},
            {"G": "6.67430e-11", "m1": "1.989e30", "m2": "5.972e24", "r": "1.496e11"},
            {"G": "6.67430e-11", "m1": "1.0e5", "m2": "2.0e5", "r": "3000"},
        ],
        negative_control=True,
    ),
    Fixture(
        fixture_id="feynman_kinetic_energy_admit",
        route_surface="DLMF / Feynman",
        truth_formula="0.5*m*(v**2)",
        candidate_formula="0.5*m*(v**2)",
        variables=["m", "v"],
        samples=[
            {"m": "1.0", "v": "3.0"},
            {"m": "2.5", "v": "4.0"},
            {"m": "0.125", "v": "12.0"},
        ],
        negative_control=False,
    ),
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def decimal_from_node(node: ast.AST, env: dict[str, Decimal]) -> Decimal:
    if isinstance(node, ast.Expression):
        return decimal_from_node(node.body, env)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Decimal(str(node.value))
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise ValueError(f"unknown variable {node.id}")
        return env[node.id]
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_BINOPS:
            raise ValueError(f"unsupported operator {op_type.__name__}")
        return ALLOWED_BINOPS[op_type](decimal_from_node(node.left, env), decimal_from_node(node.right, env))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_UNARY:
            raise ValueError(f"unsupported unary operator {op_type.__name__}")
        return ALLOWED_UNARY[op_type](decimal_from_node(node.operand, env))
    raise ValueError(f"unsupported expression node {type(node).__name__}")


def evaluate(formula: str, sample: dict[str, str]) -> Decimal:
    tree = ast.parse(formula, mode="eval")
    env = {key: Decimal(value) for key, value in sample.items()}
    return decimal_from_node(tree, env)


def normalize_decimal(value: Decimal) -> str:
    if value == 0:
        return "0"
    return format(value.normalize(), "E")


def run_fixture(fixture: Fixture) -> dict[str, Any]:
    rows = []
    absolute_errors: list[Decimal] = []
    for idx, sample in enumerate(fixture.samples):
        truth = evaluate(fixture.truth_formula, sample)
        candidate = evaluate(fixture.candidate_formula, sample)
        error = abs(truth - candidate)
        absolute_errors.append(error)
        rows.append(
            {
                "sample_index": idx,
                "sample": sample,
                "truth": normalize_decimal(truth),
                "candidate": normalize_decimal(candidate),
                "absolute_error": normalize_decimal(error),
            }
        )

    max_error = max(absolute_errors) if absolute_errors else Decimal(0)
    replay_valid = max_error == 0
    residual_declared = True
    encoded_payload = {
        "formula": fixture.candidate_formula,
        "variables": fixture.variables,
        "sample_count": len(fixture.samples),
    }
    explicit_payload = {
        "truth_values": [row["truth"] for row in rows],
    }
    encoded_bytes = len(stable_json(encoded_payload).encode("utf-8"))
    explicit_bytes = len(stable_json(explicit_payload).encode("utf-8"))
    residual_bytes = 0 if replay_valid else len(stable_json({"errors": [row["absolute_error"] for row in rows]}).encode("utf-8"))
    total_candidate_bytes = encoded_bytes + residual_bytes
    byte_gain = explicit_bytes - total_candidate_bytes

    # This fixture only admits exact deterministic replay. Byte gain is reported
    # as a diagnostic because the sample is intentionally tiny.
    status = "ADMIT_FIXTURE" if replay_valid and residual_declared and not fixture.negative_control else "HOLD"
    if byte_gain <= 0:
        status = "HOLD_DIAGNOSTIC"
    if fixture.negative_control and replay_valid:
        status = "FAIL_NEGATIVE_CONTROL"

    result = {
        "fixture_id": fixture.fixture_id,
        "route_surface": fixture.route_surface,
        "truth_formula": fixture.truth_formula,
        "candidate_formula": fixture.candidate_formula,
        "formula_hash": sha256_text(fixture.candidate_formula),
        "negative_control": fixture.negative_control,
        "rows": rows,
        "max_absolute_error": normalize_decimal(max_error),
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
    receipt = {
        "schema": "symbolic_law_replay_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixture_count": len(results),
        "table": rel(TABLE),
        "status_counts": {status: sum(1 for result in results if result["status"] == status) for status in sorted({result["status"] for result in results})},
        "results": results,
        "decision": "HOLD",
        "claim_boundary": (
            "Tiny symbolic-law replay fixture only. It tests deterministic evaluation, "
            "negative-control behavior, and residual accounting; it is not an SRBench score, "
            "not an external dataset ingest, and not a compression benchmark."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json({k: v for k, v in receipt.items() if k != "receipt_hash"}))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": rel(RECEIPT), "table": rel(TABLE), "receipt_hash": receipt["receipt_hash"], "status_counts": receipt["status_counts"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
