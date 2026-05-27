#!/usr/bin/env python3
"""swarm_network_capacity.py — Network Resource Capacity Monitor (legacy shim).

Cleanups:
- Removed hardcoded hostname→resource maps.
- Reads node inventory from 4-Infrastructure/auto/config/nodes.yaml (controller source of truth).

NOTE: This is a legacy monitoring surface; treat results as advisory.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TailscaleNode:
    ip: str
    hostname: str
    owner: str
    os: str
    status: str  # online, offline, idle
    last_seen: Optional[str]
    tags: List[str]

    def is_online(self) -> bool:
        return self.status in {"online", "idle"}


@dataclass
class NodeResources:
    node_id: str
    cpu_cores: int
    memory_gb: float
    storage_gb: float
    bandwidth_mbps: float
    gpu_count: int
    ene_enabled: bool
    utilization_percent: float


def _load_nodes_inventory(path: Path) -> Dict[str, Any]:
    """Load nodes.yaml.

    Tries PyYAML; if missing, raises a clear error.
    """
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "nodes.yaml parsing requires PyYAML. Install with: pip install pyyaml"
        ) from exc

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "nodes" not in data:
        raise ValueError(f"Invalid nodes inventory file: {path}")
    return data


class SwarmNetworkCapacity:
    def __init__(self, inventory_path: Path):
        self.inventory_path = inventory_path
        self.inventory = _load_nodes_inventory(inventory_path)
        self.tailscale_nodes: List[TailscaleNode] = []
        self.ene_nodes: List[str] = []
        self.local_ip: Optional[str] = None

    def discover_tailscale_mesh(self) -> List[TailscaleNode]:
        print("\n[1] Discovering Tailscale mesh nodes...")
        try:
            result = subprocess.run(
                ["tailscale", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            lines = result.stdout.strip().split("\n")
            nodes: List[TailscaleNode] = []

            for line in lines:
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 4:
                    ip = parts[0]
                    hostname = parts[1]
                    owner = parts[2]
                    os_type = parts[3]
                    status_parts = " ".join(parts[4:]) if len(parts) > 4 else ""

                    if "offline" in status_parts.lower():
                        status = "offline"
                    elif "idle" in status_parts.lower():
                        status = "idle"
                    else:
                        status = "online"

                    last_seen = None
                    if "last seen" in status_parts:
                        match = re.search(r"last seen ([^,]+)", status_parts)
                        if match:
                            last_seen = match.group(1)

                    tags: List[str] = []
                    if "tagged-devices" in line:
                        tags.append("tagged-devices")

                    nodes.append(
                        TailscaleNode(
                            ip=ip,
                            hostname=hostname,
                            owner=owner,
                            os=os_type,
                            status=status,
                            last_seen=last_seen,
                            tags=tags,
                        )
                    )

            self.tailscale_nodes = nodes

            try:
                ip_result = subprocess.run(
                    ["tailscale", "ip", "-4"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self.local_ip = ip_result.stdout.strip()
            except Exception:
                pass

            print(f"  Found: {len(nodes)} Tailscale nodes")
            online = sum(1 for n in nodes if n.is_online())
            print(f"  Online: {online}/{len(nodes)}")

            for node in nodes:
                status_icon = "online" if node.is_online() else "offline"
                print(f"    [{status_icon}] {node.hostname} ({node.ip})")

            return nodes

        except Exception as e:
            print(f"  ⚠️  Error discovering mesh: {e}")
            return []

    def check_ene_deployment(self) -> List[str]:
        """Check which nodes have ENE deployed.

        For now this still uses a heuristic: nodes with role including 'compute'
        or 'service-host' are assumed to be candidates. Real checks should be via
        SSH/probes.
        """
        print("\n[2] Checking ENE deployment status (heuristic)...")
        nodes = self.inventory.get("nodes", {})
        ene_nodes: List[str] = []
        for node_id, spec in nodes.items():
            roles = spec.get("roles", []) if isinstance(spec, dict) else []
            if any(r in roles for r in ["compute", "service-host", "control-plane"]):
                ene_nodes.append(node_id)
        self.ene_nodes = sorted(set(ene_nodes))

        print(f"  ENE candidates: {len(self.ene_nodes)}")
        for n in self.ene_nodes[:20]:
            print(f"    ✅ {n}")
        return self.ene_nodes

    def estimate_node_resources(self, node: TailscaleNode) -> Optional[NodeResources]:
        """Estimate node resources.

        nodes.yaml currently doesn't track CPU/RAM explicitly; so this function
        returns conservative defaults. Once resources are added to nodes.yaml,
        this function will use them directly.
        """
        specs = self.inventory.get("nodes", {}).get(node.hostname) or {}
        cpu = int(specs.get("cpu", 2)) if isinstance(specs, dict) else 2
        ram = float(specs.get("ram", 4)) if isinstance(specs, dict) else 4.0
        storage = float(specs.get("storage", 100)) if isinstance(specs, dict) else 100.0
        gpu = int(specs.get("gpu", 0)) if isinstance(specs, dict) else 0
        bw = float(specs.get("bw", 100)) if isinstance(specs, dict) else 100.0

        return NodeResources(
            node_id=node.hostname,
            cpu_cores=cpu,
            memory_gb=ram,
            storage_gb=storage,
            bandwidth_mbps=bw,
            gpu_count=gpu,
            ene_enabled=node.hostname in self.ene_nodes,
            utilization_percent=0.0,
        )

    def calculate_total_capacity(self) -> Dict[str, float]:
        print("\n[3] Calculating total network capacity...")

        total_cpu = 0
        total_ram = 0.0
        total_storage = 0.0
        total_gpu = 0
        total_bw = 0.0

        for node in self.tailscale_nodes:
            if not node.is_online():
                continue

            resources = self.estimate_node_resources(node)
            if resources:
                total_cpu += resources.cpu_cores
                total_ram += resources.memory_gb
                total_storage += resources.storage_gb
                total_gpu += resources.gpu_count
                total_bw += resources.bandwidth_mbps

        capacity: Dict[str, float] = {
            "cpu_cores": float(total_cpu),
            "memory_gb": total_ram,
            "storage_gb": total_storage,
            "gpu_count": float(total_gpu),
            "bandwidth_mbps": total_bw,
            "online_nodes": float(sum(1 for n in self.tailscale_nodes if n.is_online())),
            "total_nodes": float(len(self.tailscale_nodes)),
        }

        print(f"  CPU Cores: {int(total_cpu)}")
        print(f"  Memory: {total_ram:.1f} GB")
        print(f"  Storage: {total_storage:.1f} GB")
        print(f"  GPUs: {int(total_gpu)}")
        print(f"  Bandwidth: {total_bw:.0f} Mbps")

        return capacity

    def check_current_utilization(self) -> Dict[str, float]:
        print("\n[4] Checking current utilization (local node only)...")

        try:
            result = subprocess.run(["cat", "/proc/loadavg"], capture_output=True, text=True, timeout=5)
            load_parts = result.stdout.strip().split()
            load_1min = float(load_parts[0]) if load_parts else 0.0

            cpu_util = min(100.0, (load_1min / 16) * 100)

            mem_result = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5)
            mem_lines = mem_result.stdout.split("\n")
            mem_used = 0
            mem_total = 1
            for line in mem_lines:
                if line.startswith("Mem:"):
                    parts = line.split()
                    mem_total = int(parts[1])
                    mem_used = int(parts[2])
                    break

            mem_util = (mem_used / mem_total) * 100 if mem_total > 0 else 0

            print(f"  Local CPU: {cpu_util:.1f}%")
            print(f"  Local Memory: {mem_util:.1f}%")

            return {"cpu_percent": cpu_util, "memory_percent": mem_util, "local_node_only": True}
        except Exception:
            return {"cpu_percent": 0.0, "memory_percent": 0.0, "local_node_only": True}

    def generate_capacity_report(self) -> Dict[str, Any]:
        print("\n" + "=" * 70)
        print("SWARM NETWORK CAPACITY REPORT")
        print("=" * 70)

        self.discover_tailscale_mesh()
        self.check_ene_deployment()
        capacity = self.calculate_total_capacity()
        utilization = self.check_current_utilization()

        report: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "inventory_path": str(self.inventory_path),
            "network": {
                "total_nodes": len(self.tailscale_nodes),
                "online_nodes": int(capacity["online_nodes"]),
                "offline_nodes": len(self.tailscale_nodes) - int(capacity["online_nodes"]),
                "ene_candidates": len(self.ene_nodes),
            },
            "capacity": capacity,
            "utilization": {
                "cpu_percent": utilization.get("cpu_percent", 0.0),
                "memory_percent": utilization.get("memory_percent", 0.0),
                "note": "Local only - full mesh monitoring requires probes",
            },
            "recommendations": [
                "Add cpu/ram/storage/gpu/bw fields to nodes.yaml to remove conservative defaults.",
                "Replace ENE deployment heuristic with SSH/probe checks.",
            ],
        }

        return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("4-Infrastructure/auto/config/nodes.yaml"),
        help="Path to nodes.yaml",
    )
    args = parser.parse_args(argv)

    monitor = SwarmNetworkCapacity(args.inventory)
    report = monitor.generate_capacity_report()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
