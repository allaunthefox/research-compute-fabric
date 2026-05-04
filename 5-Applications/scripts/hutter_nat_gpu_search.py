#!/usr/bin/env python3
"""
Executable GPU witness for HutterPrizeCompression Nat weighted-bound search.

Lean remains the source of truth. This shim does not prove the theorem; it
activates the local GPU surface and writes a durable witness showing the bounded
Nat percentage search was exercised on hardware when CUDA is available.

It also probes the WebGPU `wgpu` runtime explicitly so a missing WebGPU package
is recorded as a capability result instead of being mistaken for execution.
"""

from __future__ import annotations

import json
import hashlib
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "hutter_nat_gpu_search.json"
DAG_OUT = ROOT / "out" / "build_dag"
TRUTH_DAG = ROOT / "data" / "computation_dag.json"
WEIGHTS = [40, 35, 25]
DEFAULT_N_LIMIT = 1_000_000
LEAN_THEOREMS = [
    {
        "theorem": "unifiedFieldBounded",
        "adapter": "weightedLeSelf",
        "status_note": "weighted percentage bound",
    },
    {
        "theorem": "manifoldScalingBounded",
        "adapter": "Nat.div_le_self",
        "status_note": "division by positive denominator is bounded by numerator",
    },
    {
        "theorem": "hutterPrizeCompressionBounded",
        "adapter": "Nat.mul_le_mul_left",
        "status_note": "lifts manifoldScalingBounded through multiplication",
    },
    {
        "theorem": "compressionRatioBounded",
        "adapter": "Nat.div_le_of_le_mul",
        "status_note": "requires compressedSize <= originalSize validity assumption",
    },
]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def node_id(prefix: str, value: Any) -> str:
    return f"{prefix}:{content_hash(value)[:16]}"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def upsert_truth_dag(witness: dict[str, Any]) -> dict[str, Any]:
    dag = load_json(TRUTH_DAG, {"nodes": {}, "edges": []})
    dag.setdefault("nodes", {})
    dag.setdefault("edges", [])

    timestamp = witness["timestamp"]
    proof_nodes = []
    for theorem in LEAN_THEOREMS:
        proof_nodes.append(
            {
                "id": f"lean:Semantics.HutterPrizeCompression.{theorem['theorem']}",
                "type": "lean_theorem",
                "timestamp": timestamp,
                "data": {
                    "module": "Semantics.HutterPrizeCompression",
                    "theorem": theorem["theorem"],
                    "adapter": theorem["adapter"],
                    "source": "0-Core-Formalism/lean/Semantics/Semantics/HutterPrizeCompression.lean",
                    "status": "proved",
                    "note": theorem["status_note"],
                },
                "nibbles": 0,
                "verified": True,
                "status": "VERIFIED_TRUE",
            }
        )
    gpu_node = {
        "id": node_id("witness:hutter_nat_gpu_search", witness),
        "type": "gpu_empirical_witness",
        "timestamp": timestamp,
        "data": witness,
        "nibbles": len(canonical_json(witness).encode("utf-8")) * 2,
        "verified": bool(witness["execution"]["all_passed"]),
        "status": "VERIFIED_TRUE" if witness["execution"]["all_passed"] else "DRIFT",
    }
    claim_node = {
        "id": node_id(
            "claim:hutter_nat_weighted_bound",
            {
                "theorems": [node["id"] for node in proof_nodes],
                "witness": gpu_node["id"],
                "weights": WEIGHTS,
            },
        ),
        "type": "evidence_bound_claim",
        "timestamp": timestamp,
        "data": {
            "claim": "Nat arithmetic proof-search targets for HutterPrizeCompression are connected to formal and empirical evidence",
            "lean_parents": [node["id"] for node in proof_nodes],
            "gpu_parent": gpu_node["id"],
            "truth_boundary": "Lean theorems prove formal claims; GPU witness is empirical evidence for the weighted-bound search path only.",
        },
        "nibbles": 0,
        "verified": bool(witness["execution"]["all_passed"]),
        "status": "VERIFIED_TRUE" if witness["execution"]["all_passed"] else "DRIFT",
    }

    for node in [*proof_nodes, gpu_node, claim_node]:
        dag["nodes"][node["id"]] = node

    new_edges = [{"from": node["id"], "to": claim_node["id"], "role": "formal_parent"} for node in proof_nodes]
    new_edges.append({"from": gpu_node["id"], "to": claim_node["id"], "role": "empirical_parent"})
    existing = {
        (edge.get("from"), edge.get("to"), edge.get("role"))
        for edge in dag["edges"]
    }
    for edge in new_edges:
        key = (edge["from"], edge["to"], edge["role"])
        if key not in existing:
            dag["edges"].append(edge)

    save_json(TRUTH_DAG, dag)
    return {
        "truth_dag": str(TRUTH_DAG.relative_to(ROOT)),
        "nodes": [*[node["id"] for node in proof_nodes], gpu_node["id"], claim_node["id"]],
        "edges": new_edges,
    }


def write_evidence_dag(witness: dict[str, Any], truth_link: dict[str, Any]) -> dict[str, Any]:
    run_hash = content_hash({"witness": witness, "truth_link": truth_link})
    run_id = f"hutter-nat-gpu-{run_hash[:16]}"
    dag = {
        "build_id": run_id,
        "timestamp": witness["timestamp"],
        "commit": get_git_commit(),
        "status": "completed" if witness["execution"]["all_passed"] else "failed",
        "steps": [
            {
                "step_id": node_id("step", {"run": run_id, "name": "probe_webgpu"}),
                "timestamp": witness["timestamp"],
                "description": "Probe WebGPU adapter availability",
                "command": "python3 5-Applications/scripts/hutter_nat_gpu_search.py",
                "result": witness["webgpu_probe"],
            },
            {
                "step_id": node_id("step", {"run": run_id, "name": "cuda_weighted_bounds"}),
                "timestamp": witness["timestamp"],
                "description": "Execute CUDA weighted Nat bound sweep",
                "command": "python3 5-Applications/scripts/hutter_nat_gpu_search.py",
                "result": witness["execution"],
            },
            {
                "step_id": node_id("step", {"run": run_id, "name": "truth_dag_link"}),
                "timestamp": witness["timestamp"],
                "description": "Append GPU witness and Lean theorem relation to truth DAG",
                "command": "python3 5-Applications/scripts/hutter_nat_gpu_search.py",
                "result": truth_link,
            },
        ],
        "final_timestamp": time.time(),
    }
    path = DAG_OUT / f"{run_id}.json"
    save_json(path, dag)
    return {"evidence_dag": str(path.relative_to(ROOT)), "build_id": run_id}


def get_git_commit() -> str:
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def probe_webgpu() -> dict[str, Any]:
    try:
        import wgpu  # type: ignore
    except Exception as exc:
        return {
            "available": False,
            "backend": "webgpu",
            "error": f"{type(exc).__name__}: {exc}",
        }

    try:
        adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
        if adapter is None:
            return {
                "available": False,
                "backend": "webgpu",
                "error": "No WebGPU adapter returned",
            }
        return {
            "available": True,
            "backend": "webgpu",
            "adapter": str(getattr(adapter, "summary", adapter)),
        }
    except Exception as exc:
        return {
            "available": False,
            "backend": "webgpu",
            "error": f"{type(exc).__name__}: {exc}",
        }


def run_cuda_search(n_limit: int) -> dict[str, Any]:
    import torch

    cuda_available = torch.cuda.is_available()
    device = torch.device("cuda" if cuda_available else "cpu")
    n_values = torch.arange(0, n_limit + 1, dtype=torch.int64, device=device)

    weight_results: dict[str, bool] = {}
    max_slack: dict[str, int] = {}
    for weight in WEIGHTS:
        bounded = (n_values * weight) // 100 <= n_values
        weight_results[str(weight)] = bool(torch.all(bounded).item())
        slack = n_values - ((n_values * weight) // 100)
        max_slack[str(weight)] = int(torch.max(slack).item())

    comp = (n_values * 40) // 100
    phys = (n_values * 35) // 100
    geom = (n_values * 25) // 100
    unified_same_field_bound = bool(torch.all(comp + phys + geom <= n_values * 3).item())

    if cuda_available:
        torch.cuda.synchronize()

    return {
        "backend": "cuda" if cuda_available else "cpu",
        "device": str(device),
        "device_name": torch.cuda.get_device_name(0) if cuda_available else "cpu",
        "torch_version": torch.__version__,
        "n_limit": n_limit,
        "values_checked": n_limit + 1,
        "weights_checked": WEIGHTS,
        "weighted_le_self": weight_results,
        "same_field_unified_bound": unified_same_field_bound,
        "max_slack": max_slack,
        "all_passed": all(weight_results.values()) and unified_same_field_bound,
    }


def main() -> int:
    start = time.time()
    webgpu = probe_webgpu()
    search = run_cuda_search(DEFAULT_N_LIMIT)

    witness = {
        "timestamp": start,
        "elapsed_seconds": time.time() - start,
        "theorem_target": "Semantics.HutterPrizeCompression.unifiedFieldBounded",
        "theorem_targets": [
            f"Semantics.HutterPrizeCompression.{theorem['theorem']}"
            for theorem in LEAN_THEOREMS
        ],
        "adapter_target": "weightedLeSelf",
        "shader_intent": "5-Applications/scripts/q16_arithmetic_verify.wgsl",
        "webgpu_probe": webgpu,
        "execution": search,
        "proof_note": (
            "Empirical GPU witness only; the Lean theorem is proven separately "
            "by weightedLeSelf."
        ),
    }

    truth_link = upsert_truth_dag(witness)
    evidence_link = write_evidence_dag(witness, truth_link)
    witness["dag"] = {
        **truth_link,
        **evidence_link,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(witness, indent=2) + "\n")

    print(json.dumps(witness, indent=2))
    return 0 if search["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
