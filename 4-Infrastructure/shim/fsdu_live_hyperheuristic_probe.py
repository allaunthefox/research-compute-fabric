#!/usr/bin/env python3
"""Run a live seeded hyper-heuristic snapshot and project it into FSDU.

Unlike fsdu_hyperheuristic_bridge.py, this probe does not read the static
orchestrator receipt. It executes the orchestrator in-process, captures the
actual component histories, and emits a dual-map scar receipt from that live
snapshot. It remains a software witness only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path
from typing import Any, Callable

from hyper_heuristic_orchestrator import (
    ComponentType,
    FAMMHyperHeuristics,
    FPGABuildHyperHeuristics,
    GPUSchedulingHyperHeuristics,
    HeuristicType,
    HyperHeuristicOrchestrator,
    PISTHyperHeuristics,
    ShimSelectionHyperHeuristics,
)


ROOT = Path(__file__).resolve().parents[2]
LOCAL_RECEIPT = ROOT / "4-Infrastructure" / "shim" / "fsdu_live_hyperheuristic_probe_receipt.json"
STACK_RECEIPT = ROOT / "shared-data" / "data" / "stack_solidification" / "fsdu_live_hyperheuristic_probe_receipt.json"
PROTOCOL = "fsdu_live_hyperheuristic_probe_v0"


HEURISTIC_TO_SOLVER = {
    "adaptive": "a_star",
    "balanced": "dijkstra",
    "conservative": "bfs",
    "greedy": "greedy",
    "random": "dfs",
}


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def add_result_accounting(result: dict[str, Any], cost: float, reward: float, success: bool | None = None) -> dict[str, Any]:
    out = dict(result)
    if success is not None:
        out["success"] = bool(success)
    out["cost"] = round(float(cost), 6)
    out["reward"] = round(float(reward), 6)
    return out


def run_component(
    orchestrator: HyperHeuristicOrchestrator,
    component: ComponentType,
    operations: int,
    context_fn: Callable[[int], dict[str, Any]],
    dispatch_fn: Callable[[HeuristicType, dict[str, Any]], dict[str, Any]],
) -> list[dict[str, Any]]:
    events = []
    for op_index in range(operations):
        context = context_fn(op_index)
        result, heuristic = orchestrator.select_and_execute(component, dispatch_fn, context)
        events.append(
            {
                "op": op_index,
                "component": component.value,
                "heuristic": heuristic.value,
                "success": False if result is None else bool(result.get("success", True)),
                "result_hash": sha256_text(stable_json(result)),
            }
        )
    return events


def famm_context(i: int) -> dict[str, Any]:
    return {
        "bank": {"cells": {0: {"delay": 5.0, "delay_weight": 1.0}, 1: {"delay": 3.0, "delay_weight": 0.5}}},
        "address": i % 2,
        "target_delay": 2.0 + (i % 7),
        "max_delay": 6.0,
        "tolerance": 1.25,
    }


def famm_dispatch(ht: HeuristicType, ctx: dict[str, Any]) -> dict[str, Any]:
    if ht == HeuristicType.GREEDY:
        result = FAMMHyperHeuristics.greedy_minimize(ht, ctx)
    elif ht == HeuristicType.BALANCED:
        result = FAMMHyperHeuristics.frustration_balance(ht, ctx)
    elif ht == HeuristicType.ADAPTIVE:
        result = FAMMHyperHeuristics.adaptive_weight(ht, ctx)
    else:
        result = FAMMHyperHeuristics.greedy_minimize(ht, ctx)
    miss = abs(float(result.get("adjusted_delay", 0.0)) - float(ctx["target_delay"]))
    success = bool(result.get("success", True)) and miss <= float(ctx["tolerance"])
    return add_result_accounting(result, cost=miss * 4.0, reward=1.0 - miss, success=success)


def pist_context(i: int) -> dict[str, Any]:
    return {"pos": {"k": i % 5, "t": (i * 3) % 13}, "phase": "seismic" if i % 3 == 0 else "grounded"}


def pist_dispatch(ht: HeuristicType, ctx: dict[str, Any]) -> dict[str, Any]:
    if ht == HeuristicType.GREEDY:
        result = PISTHyperHeuristics.linear_move(ht, ctx)
    elif ht == HeuristicType.ADAPTIVE:
        result = PISTHyperHeuristics.adaptive_move(ht, ctx)
    else:
        result = PISTHyperHeuristics.resonance_jump(ht, ctx)
    new_t = int(result["new_pos"]["t"])
    k = int(result["new_pos"]["k"])
    success = 0 <= new_t <= (2 * k + 1)
    cost = 0.0 if success else abs(new_t - (2 * k + 1)) + abs(min(0, new_t))
    return add_result_accounting(result, cost=cost, reward=1.0 if success else -cost, success=success)


def shim_context(i: int) -> dict[str, Any]:
    domains = ["math", "compression", "hardware", "general", "unknown"]
    performance_history = {
        "math": {"math_prover_prior_metaprobe.py": 0.9, "intense_math_modeling_router.py": 0.7},
        "compression": {"compression_signal_shaping_synthesis.py": 0.8},
    }
    return {"domain": domains[i % len(domains)], "task_type": "optimization", "performance_history": performance_history}


def shim_dispatch(ht: HeuristicType, ctx: dict[str, Any]) -> dict[str, Any]:
    if ht == HeuristicType.GREEDY:
        result = ShimSelectionHyperHeuristics.select_by_domain(ht, ctx)
    elif ht == HeuristicType.ADAPTIVE:
        result = ShimSelectionHyperHeuristics.select_adaptive(ht, ctx)
    else:
        result = ShimSelectionHyperHeuristics.select_by_performance(ht, ctx)
    selected = result.get("selected_shim", "")
    success = selected != "default_shim.py"
    return add_result_accounting(result, cost=0.0 if success else 15.0, reward=1.0 if success else -3.0, success=success)


def gpu_context(i: int) -> dict[str, Any]:
    task_queue = [
        {"name": f"gpu_task_{i}_{j}", "priority": (i + j) % 10, "memory_required": 1000 + ((i + 2) * (j + 1) * 700) % 7000}
        for j in range(3)
    ]
    return {
        "task_queue": task_queue,
        "gpu_memory": 12000,
        "gpu_count": 1,
        "current_memory_usage": i * 650,
        "gpu_states": [{"load": 0.3 + (i % 5) * 0.1, "memory": 6000}],
    }


def gpu_dispatch(ht: HeuristicType, ctx: dict[str, Any]) -> dict[str, Any]:
    if ht == HeuristicType.GREEDY:
        result = GPUSchedulingHyperHeuristics.round_robin(ht, ctx)
    elif ht == HeuristicType.BALANCED:
        result = GPUSchedulingHyperHeuristics.priority_based(ht, ctx)
    elif ht == HeuristicType.ADAPTIVE:
        result = GPUSchedulingHyperHeuristics.memory_aware(ht, ctx)
    else:
        result = GPUSchedulingHyperHeuristics.load_balancing(ht, ctx)
    assigned = result.get("assigned", [])
    failed = len([row for row in assigned if row.get("gpu_id") is None])
    return add_result_accounting(result, cost=failed * 10.0, reward=1.0 - failed, success=failed == 0)


def fpga_context(i: int) -> dict[str, Any]:
    modules = [f"module_{j}" for j in range(5)]
    changed_files = [f"{module}.v" for j, module in enumerate(modules) if (i + j) % 3 == 0]
    return {
        "modules": modules,
        "changed_files": changed_files,
        "build_cache": {file_name: f"cached_{file_name}" for idx, file_name in enumerate(changed_files) if idx % 2 == 0},
        "dependency_graph": {f"module_{j}": [f"module_{k}" for k in range(j)] if j > 0 else [] for j in range(5)},
        "available_cores": 4,
        "resource_budget": {"LUT": 9000, "FF": 18000, "BRAM": 18},
        "module_resources": {f"module_{j}": {"LUT": 1000 * (j + 1), "FF": 2000 * (j + 1), "BRAM": j + 1} for j in range(5)},
        "critical_paths": [["module_0", "module_2", "module_4"], ["module_1", "module_3"]],
    }


def fpga_dispatch(ht: HeuristicType, ctx: dict[str, Any]) -> dict[str, Any]:
    if ht == HeuristicType.GREEDY:
        result = FPGABuildHyperHeuristics.incremental_build(ht, ctx)
        pressure = len(result.get("modules_to_rebuild", []))
        success = pressure <= 2
    elif ht == HeuristicType.BALANCED:
        result = FPGABuildHyperHeuristics.parallel_synthesis(ht, ctx)
        pressure = len(result.get("dependent_modules", []))
        success = pressure <= 4
    elif ht == HeuristicType.ADAPTIVE:
        result = FPGABuildHyperHeuristics.resource_aware(ht, ctx)
        pressure = len(result.get("deferred", []))
        success = bool(result.get("success", False))
    else:
        result = FPGABuildHyperHeuristics.timing_driven(ht, ctx)
        pressure = len(result.get("critical_modules", []))
        success = pressure <= 4
    return add_result_accounting(result, cost=pressure * 8.0, reward=1.0 - pressure, success=success)


def live_mixture(events: list[dict[str, Any]]) -> dict[str, float]:
    weights = {"bfs": 0.0, "dfs": 0.0, "dijkstra": 0.0, "a_star": 0.0, "greedy": 0.0}
    for event in events:
        solver = HEURISTIC_TO_SOLVER.get(event["heuristic"], "a_star")
        weights[solver] += 1.0
    total = sum(weights.values()) or 1.0
    return {key: round(value / total, 9) for key, value in weights.items()}


def alerts_for(success_rate: float, avg_cost: float, switch_count: int) -> list[str]:
    alerts = []
    if success_rate < 0.8:
        alerts.append("heuristicBiasFailed")
    if success_rate < 0.65:
        alerts.append("loopPressureRising")
    if avg_cost > 5.0:
        alerts.append("deadEndConfirmed")
    if switch_count > 0:
        alerts.append("edgeCostChanged")
    if not alerts:
        alerts.append("shortcutOpened")
    return alerts


def project_live_component(component: str, report: dict[str, Any], events: list[dict[str, Any]], raw_events: list[dict[str, Any]], epsilon: float) -> dict[str, Any]:
    runs = len(raw_events)
    successes = sum(1 for event in raw_events if event["success"])
    success_rate = successes / max(1, runs)
    metric_rows = []
    for row in raw_events:
        metric_rows.append(row)
    global_entries = [row for row in raw_events]
    failure_count = runs - successes

    # Use global_metrics for cost/reward because select_and_execute records the
    # accounting result there.
    avg_cost = 0.0
    avg_reward = 0.0
    if global_entries:
        avg_cost = sum(float(row["cost"]) for row in global_entries) / len(global_entries)
        avg_reward = sum(float(row["reward"]) for row in global_entries) / len(global_entries)

    switch_count = int(report["switch_count"])
    exploration_rate = float(report["exploration_rate"])
    ahead_scar = failure_count + avg_cost / 10.0 + switch_count + exploration_rate * runs
    behind_scar = failure_count * success_rate + max(0.0, avg_cost / 20.0)
    scar_delta = ahead_scar - behind_scar
    abs_delta = abs(scar_delta)
    admissible = abs_delta <= epsilon
    return {
        "component": component,
        "live_snapshot": {
            "successes": successes,
            "total_operations": runs,
            "success_rate": round(success_rate, 9),
            "avg_cost": round(avg_cost, 9),
            "avg_reward": round(avg_reward, 9),
            "switch_count": switch_count,
            "exploration_rate": round(exploration_rate, 9),
            "current_heuristic": report["current_heuristic"],
        },
        "fsdu_projection": {
            "ahead_scar": round(ahead_scar, 9),
            "behind_scar": round(behind_scar, 9),
            "scar_delta": round(scar_delta, 9),
            "abs_scar_delta": round(abs_delta, 9),
            "epsilon": epsilon,
            "admissible": admissible,
            "commit_decision": "COMMIT_ALLOWED" if admissible else "RETUNE_REQUIRED",
            "alerts": alerts_for(success_rate, avg_cost, switch_count),
            "solver_mixture": live_mixture(events),
        },
    }


def run_live_probe(seed: int, epsilon: float) -> dict[str, Any]:
    random.seed(seed)
    orchestrator = HyperHeuristicOrchestrator()
    event_index: dict[str, list[dict[str, Any]]] = {}

    suites = [
        (ComponentType.FAMM_DELAY, 20, famm_context, famm_dispatch),
        (ComponentType.PIST_MOVE, 15, pist_context, pist_dispatch),
        (ComponentType.SHIM_SELECTION, 12, shim_context, shim_dispatch),
        (ComponentType.GPU_SCHEDULING, 15, gpu_context, gpu_dispatch),
        (ComponentType.FPGA_BUILD, 12, fpga_context, fpga_dispatch),
    ]
    for component, ops, context_fn, dispatch_fn in suites:
        event_index[component.value] = run_component(orchestrator, component, ops, context_fn, dispatch_fn)

    report = orchestrator.get_performance_report()
    raw_global: dict[str, list[dict[str, Any]]] = {}
    for key, rows in orchestrator.global_metrics.items():
        component, heuristic = key.rsplit("_", 1)
        raw_global.setdefault(component, [])
        for row in rows:
            raw_global[component].append({"heuristic": heuristic, **row})

    components = []
    for component, component_report in report["components"].items():
        components.append(project_live_component(component, component_report, event_index[component], raw_global.get(component, []), epsilon))

    all_admissible = all(row["fsdu_projection"]["admissible"] for row in components)
    max_delta = max((row["fsdu_projection"]["abs_scar_delta"] for row in components), default=0.0)
    return {
        "protocol": PROTOCOL,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seed": seed,
        "epsilon": epsilon,
        "claim_boundary": "live_software_snapshot_not_live_path_optimality_not_hardware_claim",
        "lean_anchor": "2-Search-Space/FAMM/FAMM_FSDU.lean",
        "equation": {
            "state": "X_t = (M_a, M_b, S_a, S_b, Theta)",
            "scar_differential": "DeltaS_t = S_a - S_b",
            "commit_gate": "commit allowed iff ||DeltaS_t|| <= epsilon",
        },
        "orchestrator_report_hash": sha256_text(stable_json(report)),
        "event_index_hash": sha256_text(stable_json(event_index)),
        "components": components,
        "gate": {
            "decision": "ADMIT_LIVE_FSDU_SNAPSHOT" if all_admissible else "HOLD_LIVE_SCAR_DIVERGENCE",
            "all_components_admissible": all_admissible,
            "component_count": len(components),
            "max_abs_scar_delta": round(max_delta, 9),
            "epsilon": epsilon,
            "next_gate": "feed these snapshots into the dashboard/API surface and compare across seeds",
        },
        "raw_event_sample": {key: rows[:5] for key, rows in event_index.items()},
    }


def write_receipt(receipt: dict[str, Any], output: Path, mirror: Path | None) -> None:
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if mirror is not None:
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260510)
    parser.add_argument("--epsilon", type=float, default=2.0)
    parser.add_argument("--output", default=str(LOCAL_RECEIPT))
    parser.add_argument("--no-mirror", action="store_true")
    args = parser.parse_args()

    receipt = run_live_probe(seed=args.seed, epsilon=args.epsilon)
    mirror = None if args.no_mirror else STACK_RECEIPT
    write_receipt(receipt, Path(args.output), mirror)
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
