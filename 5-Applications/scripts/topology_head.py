#!/usr/bin/env python3
"""
topology_head.py — Cooperative Compute Topology Head Node

Starts a Ray head node on qfox-1 and provides the topology registry
for the distributed mesh. Worker nodes (laptop-1, cupfox) connect
to this head to form a unified resource pool.

Architecture:
  qfox-1    (head)  : 12 CPU, 30 GiB RAM, RTX 4070 SUPER 12 GiB VRAM
  laptop-1  (worker): 16 CPU, 14 GiB RAM, AMD Lucienne APU (ROCm)
  cupfox    (worker):  2 CPU,  4 GiB RAM, CPU-only

All nodes are connected via Tailscale mesh (100.x.x.x addresses).
"""

import ray
import os
import sys
import json
import socket
import time

# ═══════════════════════════════════════════════════════════════════════════
# §1  Topology Definition
# ═══════════════════════════════════════════════════════════════════════════

TOPOLOGY = {
    "qfox-1": {
        "tailscale_ip": "100.88.57.96",
        "role": "head",
        "cpus": 12,
        "ram_gib": 30,
        "gpu": "NVIDIA GeForce RTX 4070 SUPER",
        "gpu_vram_gib": 12,
        "accelerator": "cuda",
    },
    "nixos-laptop": {
        "tailscale_ip": "100.119.165.120",
        "role": "worker",
        "cpus": 16,
        "ram_gib": 14,
        "gpu": "AMD Lucienne APU",
        "gpu_vram_gib": 0,  # shared memory
        "accelerator": "rocm",
    },
    "microvm-racknerd": {
        "tailscale_ip": "100.101.247.127",
        "role": "worker",
        "cpus": 1,
        "ram_gib": 1,
        "gpu": None,
        "gpu_vram_gib": 0,
        "accelerator": None,
    },
    "361395-1": {
        "tailscale_ip": "100.110.163.82",
        "role": "worker",
        "cpus": 2,
        "ram_gib": 3,
        "gpu": None,
        "gpu_vram_gib": 0,
        "accelerator": None,
    },
}

HEAD_IP = TOPOLOGY["qfox-1"]["tailscale_ip"]
HEAD_PORT = 6379
DASHBOARD_PORT = 8265

# ═══════════════════════════════════════════════════════════════════════════
# §2  Head Node Initialization
# ═══════════════════════════════════════════════════════════════════════════

def start_head():
    """Initialize Ray head node bound to the Tailscale interface."""
    print(f"╔═══════════════════════════════════════════════════════════╗")
    print(f"║  Cooperative Compute Topology — Head Node                ║")
    print(f"╠═══════════════════════════════════════════════════════════╣")
    print(f"║  Head IP   : {HEAD_IP}                          ║")
    print(f"║  Ray Port  : {HEAD_PORT}                                    ║")
    print(f"║  Dashboard : http://{HEAD_IP}:{DASHBOARD_PORT}              ║")
    print(f"╚═══════════════════════════════════════════════════════════╝")

    ray.init(
        address=None,  # start a new cluster
        _node_ip_address=HEAD_IP,
        dashboard_host="0.0.0.0",
        dashboard_port=DASHBOARD_PORT,
        num_cpus=TOPOLOGY["qfox-1"]["cpus"],
        num_gpus=1,  # RTX 4070 SUPER
        include_dashboard=True,
    )

    print(f"\n✓ Ray head started. Cluster address: {HEAD_IP}:{HEAD_PORT}")
    print(f"  Dashboard: http://{HEAD_IP}:{DASHBOARD_PORT}")
    print(f"\nTo connect workers, run on each node:")
    print(f"  ray start --address='{HEAD_IP}:{HEAD_PORT}'")
    print()

    return ray.cluster_resources()


# ═══════════════════════════════════════════════════════════════════════════
# §3  Topology Status
# ═══════════════════════════════════════════════════════════════════════════

def print_topology_status():
    """Print live cluster resource status."""
    resources = ray.cluster_resources()
    available = ray.available_resources()
    nodes = ray.nodes()

    print(f"\n{'═'*60}")
    print(f"  TOPOLOGY STATUS — {len(nodes)} node(s) connected")
    print(f"{'═'*60}")

    total_cpu = resources.get("CPU", 0)
    total_gpu = resources.get("GPU", 0)
    total_mem = resources.get("memory", 0) / (1024**3)

    avail_cpu = available.get("CPU", 0)
    avail_gpu = available.get("GPU", 0)
    avail_mem = available.get("memory", 0) / (1024**3)

    print(f"  CPUs   : {avail_cpu:.0f} / {total_cpu:.0f} available")
    print(f"  GPUs   : {avail_gpu:.0f} / {total_gpu:.0f} available")
    print(f"  Memory : {avail_mem:.1f} / {total_mem:.1f} GiB available")
    print()

    for node in nodes:
        alive = "🟢" if node["Alive"] else "🔴"
        ip = node["NodeManagerAddress"]
        res = node["Resources"]
        cpus = res.get("CPU", 0)
        gpus = res.get("GPU", 0)
        mem = res.get("memory", 0) / (1024**3)

        # Identify the node by IP
        name = "unknown"
        for n, info in TOPOLOGY.items():
            if info["tailscale_ip"] == ip:
                name = n
                break

        print(f"  {alive} {name:12s} ({ip})")
        print(f"     CPU: {cpus:.0f}  GPU: {gpus:.0f}  RAM: {mem:.1f} GiB")

    print(f"{'═'*60}\n")


# ═══════════════════════════════════════════════════════════════════════════
# §4  Distributed Task Primitives
# ═══════════════════════════════════════════════════════════════════════════

@ray.remote
def cpu_task(task_id: int, data_chunk: list) -> dict:
    """Generic CPU-bound task that runs on any node in the topology."""
    import platform
    hostname = platform.node()
    result = sum(data_chunk)  # placeholder computation
    return {
        "task_id": task_id,
        "hostname": hostname,
        "chunk_size": len(data_chunk),
        "result": result,
    }


@ray.remote(num_gpus=1)
def gpu_task(task_id: int, tensor_size: int) -> dict:
    """GPU-accelerated task — will be scheduled on nodes with GPUs."""
    import torch
    import platform
    hostname = platform.node()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    t = torch.randn(tensor_size, tensor_size, device=device)
    result = torch.linalg.norm(t).item()

    return {
        "task_id": task_id,
        "hostname": hostname,
        "device": device,
        "tensor_size": tensor_size,
        "norm": result,
    }


def run_topology_test():
    """Distribute a test workload across all connected nodes."""
    print("Running topology distribution test...")

    # Create chunks that will fan out across available CPUs
    chunks = [list(range(i * 1000, (i + 1) * 1000)) for i in range(30)]
    futures = [cpu_task.remote(i, chunk) for i, chunk in enumerate(chunks)]
    results = ray.get(futures)

    # Tally which nodes handled what
    node_counts = {}
    for r in results:
        h = r["hostname"]
        node_counts[h] = node_counts.get(h, 0) + 1

    print(f"\n  Task distribution across topology:")
    for node, count in sorted(node_counts.items()):
        print(f"    {node}: {count} tasks")

    print(f"\n  Total tasks completed: {len(results)}")
    return results


# ═══════════════════════════════════════════════════════════════════════════
# §5  Entry Point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        ray.init(address=f"{HEAD_IP}:{HEAD_PORT}")
        print_topology_status()
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        ray.init(address=f"{HEAD_IP}:{HEAD_PORT}")
        print_topology_status()
        run_topology_test()
    else:
        start_head()
        print_topology_status()

        print("Head node running. Press Ctrl+C to shutdown.")
        try:
            while True:
                time.sleep(60)
                print_topology_status()
        except KeyboardInterrupt:
            print("\nShutting down head node...")
            ray.shutdown()
