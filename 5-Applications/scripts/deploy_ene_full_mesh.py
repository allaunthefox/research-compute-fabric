#!/usr/bin/env python3
"""deploy_ene_full_mesh.py — Deploy ENE to Full Tailscale Mesh (legacy shim).

Cleanups:
- Removed hardcoded node lists; reads nodes from 4-Infrastructure/auto/config/nodes.yaml.

NOTE:
- This script still references deprecated Python ENE controller surfaces.
- Treat as an orchestration stub pending the Rust ENE crate.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure" / "infra"))

try:
    from ene_distributed_node import ENEMeshController  # type: ignore
except ImportError:
    ENEMeshController = None


def _load_nodes_inventory(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("nodes.yaml parsing requires PyYAML (pip install pyyaml)") from exc

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "nodes" not in data:
        raise ValueError(f"Invalid nodes inventory file: {path}")
    return data


class FullMeshDeployment:
    def __init__(self, inventory_path: Path):
        if ENEMeshController is None:
            raise RuntimeError(
                "Python ENE mesh controller is removed; use the Rust ENE crate under 1-Distributed-Systems/ene instead."
            )
        self.inventory_path = inventory_path
        self.inventory = _load_nodes_inventory(inventory_path)
        self.controller = ENEMeshController()
        self.mesh_nodes: Dict[str, Any] = {}

    def step1_spawn_inventory_nodes(self) -> Dict[str, Any]:
        print("\n[STEP 1] Spawning ENE nodes from inventory...")
        nodes = self.inventory.get("nodes", {})
        spawned = 0

        for node_id in sorted(nodes.keys()):
            node = self.controller.spawn_node(f"ene_{node_id}")
            self.mesh_nodes[node_id] = {"node": node, "status": "active"}
            spawned += 1
            print(f"  ✅ {node_id}")

        return {"step": 1, "nodes_spawned": spawned}

    def step2_auto_replicate(self) -> Dict[str, Any]:
        print("\n[STEP 2] Auto-replication (stub)...")
        if not self.mesh_nodes:
            return {"step": 2, "error": "no nodes spawned"}

        source_node = list(self.mesh_nodes.values())[0]["node"]
        deployed = []
        failed = []
        for node_id, data in self.mesh_nodes.items():
            remote = data["node"]
            try:
                time.sleep(0.1)
                remote.auto_replicate([source_node.node_id])
                deployed.append(node_id)
            except Exception as e:
                failed.append((node_id, str(e)))

        return {"step": 2, "deployed": deployed, "failed": failed}

    def deploy_full_mesh(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        results["step1"] = self.step1_spawn_inventory_nodes()
        results["step2"] = self.step2_auto_replicate()
        results["inventory"] = str(self.inventory_path)
        results["mesh_size"] = len(self.mesh_nodes)
        results["status"] = "operational" if self.mesh_nodes else "failed"
        return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("4-Infrastructure/auto/config/nodes.yaml"),
        help="Path to nodes.yaml",
    )
    args = parser.parse_args(argv)

    deployment = FullMeshDeployment(args.inventory)
    result = deployment.deploy_full_mesh()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
