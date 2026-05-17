#!/usr/bin/env python3
"""Bridge hyper-heuristic demo metrics into FSDU scar-differential receipts.

This is a receipt projection layer, not a solver. It reads the existing
hyper-heuristic orchestrator receipt and emits the dual-map FSDU accounting
surface:

    ahead scar   = observed speculative failure pressure
    behind scar  = conservative absorbed failure pressure
    delta scar   = ahead - behind
    commit gate  = bounded delta scar <= epsilon

The output is intended for dashboards, kanban, and follow-on replay checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "4-Infrastructure" / "shim" / "hyper_heuristic_orchestrator_receipt.json"
LOCAL_RECEIPT = ROOT / "4-Infrastructure" / "shim" / "fsdu_hyperheuristic_bridge_receipt.json"
STACK_RECEIPT = ROOT / "shared-data" / "data" / "stack_solidification" / "fsdu_hyperheuristic_bridge_receipt.json"

PROTOCOL = "fsdu_hyperheuristic_bridge_v0"
LEAN_ANCHOR = "2-Search-Space/FAMM/FAMM_FSDU.lean"
THEORY_ANCHOR = "2-Search-Space/FAMM/docs/FSDU_theory.md"

HEURISTIC_TO_SOLVER_BIAS = {
    "adaptive": "a_star",
    "balanced": "dijkstra",
    "greedy": "greedy",
    "conservative": "bfs",
    "random": "dfs",
}


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_mixture(best_heuristic: str) -> dict[str, float]:
    weights = {
        "bfs": 0.18,
        "dfs": 0.14,
        "dijkstra": 0.20,
        "a_star": 0.26,
        "greedy": 0.22,
    }
    solver = HEURISTIC_TO_SOLVER_BIAS.get(best_heuristic, "a_star")
    weights[solver] += 0.25
    total = sum(weights.values())
    return {key: round(value / total, 9) for key, value in weights.items()}


def component_alerts(success_rate: float, failure_pressure: float, heuristic_count: int) -> list[str]:
    alerts: list[str] = []
    if success_rate < 0.75:
        alerts.append("heuristicBiasFailed")
    if success_rate < 0.70:
        alerts.append("loopPressureRising")
    if failure_pressure >= 3.0:
        alerts.append("deadEndConfirmed")
    if heuristic_count >= 4 and success_rate >= 0.75:
        alerts.append("shortcutOpened")
    if not alerts:
        alerts.append("edgeCostChanged")
    return alerts


def project_component(component: dict[str, Any], epsilon: float) -> dict[str, Any]:
    demo = component.get("demo_results", {})
    success_rate = float(demo.get("success_rate", 0.0))
    operations = int(demo.get("total_operations", 0))
    best_heuristic = str(demo.get("best_heuristic", "adaptive"))
    heuristics = component.get("heuristics", [])
    heuristic_count = len(heuristics)

    failure_pressure = max(0.0, 1.0 - success_rate) * operations
    exploration_pressure = 0.01 * heuristic_count
    ahead_scar = failure_pressure + exploration_pressure

    # The behind map represents conservative absorbed error. It deliberately
    # lags the ahead map; the differential is the control signal.
    behind_scar = failure_pressure * success_rate
    scar_delta = ahead_scar - behind_scar
    abs_delta = abs(scar_delta)
    admissible = abs_delta <= epsilon

    return {
        "component": component.get("component", "UNKNOWN"),
        "description": component.get("description", ""),
        "observed": {
            "success_rate": success_rate,
            "total_operations": operations,
            "best_heuristic": best_heuristic,
            "heuristic_count": heuristic_count,
        },
        "fsdu_projection": {
            "ahead_scar": round(ahead_scar, 9),
            "behind_scar": round(behind_scar, 9),
            "scar_delta": round(scar_delta, 9),
            "abs_scar_delta": round(abs_delta, 9),
            "epsilon": epsilon,
            "admissible": admissible,
            "commit_decision": "COMMIT_ALLOWED" if admissible else "RETUNE_REQUIRED",
            "alerts": component_alerts(success_rate, failure_pressure, heuristic_count),
            "solver_mixture": normalize_mixture(best_heuristic),
        },
        "claim_boundary": "receipt_projection_not_live_path_optimality_not_compression_claim",
    }


def build_receipt(input_path: Path, epsilon: float, out_path: Path, mirror_path: Path | None) -> dict[str, Any]:
    source = json.loads(input_path.read_text(encoding="utf-8"))
    components = source.get("components_implemented", [])
    projected = [project_component(component, epsilon) for component in components]
    all_admissible = all(row["fsdu_projection"]["admissible"] for row in projected)
    max_delta = max((row["fsdu_projection"]["abs_scar_delta"] for row in projected), default=0.0)

    receipt = {
        "protocol": PROTOCOL,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_receipt": {
            "path": str(input_path),
            "sha256": sha256_path(input_path),
            "script_name": source.get("script_name"),
            "source_timestamp": source.get("timestamp"),
        },
        "lean_anchor": LEAN_ANCHOR,
        "theory_anchor": THEORY_ANCHOR,
        "equation": {
            "state": "X_t = (M_a, M_b, S_a, S_b, Theta)",
            "scar_differential": "DeltaS_t = S_a - S_b",
            "commit_gate": "commit allowed iff ||DeltaS_t|| <= epsilon",
        },
        "projection_policy": {
            "epsilon": epsilon,
            "ahead_scar": "(1 - success_rate) * total_operations + 0.01 * heuristic_count",
            "behind_scar": "(1 - success_rate) * total_operations * success_rate",
            "live_path_claim": False,
            "compression_claim": False,
            "hardware_claim": False,
        },
        "components": projected,
        "gate": {
            "decision": "ADMIT_FSDU_BRIDGE_RECEIPT" if all_admissible else "HOLD_SCAR_DIVERGENCE",
            "all_components_admissible": all_admissible,
            "component_count": len(projected),
            "max_abs_scar_delta": round(max_delta, 9),
            "epsilon": epsilon,
            "next_gate": "wire live orchestrator state snapshots into the same FSDU fields",
        },
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if mirror_path is not None:
        mirror_path.parent.mkdir(parents=True, exist_ok=True)
        mirror_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Hyper-heuristic receipt JSON")
    parser.add_argument("--epsilon", type=float, default=1.25, help="Scar differential commit envelope")
    parser.add_argument("--output", default=str(LOCAL_RECEIPT), help="Receipt output path")
    parser.add_argument("--no-mirror", action="store_true", help="Skip shared-data mirror receipt")
    args = parser.parse_args()

    mirror = None if args.no_mirror else STACK_RECEIPT
    receipt = build_receipt(Path(args.input), args.epsilon, Path(args.output), mirror)
    print(
        json.dumps(
            {
                "receipt": str(Path(args.output)),
                "mirror": None if mirror is None else str(mirror),
                "decision": receipt["gate"]["decision"],
                "component_count": receipt["gate"]["component_count"],
                "max_abs_scar_delta": receipt["gate"]["max_abs_scar_delta"],
                "epsilon": receipt["gate"]["epsilon"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
