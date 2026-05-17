#!/usr/bin/env python3
"""
topology.py — Cooperative Compute Topology over Tailscale Mesh

A lightweight distributed compute fabric that works over DERP-relayed
Tailscale connections by using SSH as the transport layer rather than
requiring direct bidirectional TCP (which Ray/gRPC need but DERP can't
reliably provide).

Architecture:
  - Head node (qfox-1) orchestrates task dispatch
  - Worker nodes (laptop-1, cupfox) execute tasks via SSH
  - Results stream back through the SSH channel
  - PyTorch tensors serialize via pickle over SSH pipes

This is a true topology: the head node sees all workers as a unified
resource pool and schedules tasks based on node capabilities.

Usage:
  python3 topology.py status    — show topology health
  python3 topology.py test      — run distributed test workload
  python3 topology.py run <script.py> — distribute script across topology
"""

import subprocess
import sys
import json
import time
import os
import tempfile
import concurrent.futures
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# §1  Node Definitions
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Node:
    name: str
    tailscale_ip: str
    ssh_user: str
    cpus: int
    ram_gib: float
    gpu: Optional[str]
    gpu_vram_gib: float
    accelerator: Optional[str]  # "cuda", "rocm", or None
    role: str  # "head" or "worker"
    python_bin: str = "python3"
    is_local: bool = False

    @property
    def ssh_target(self) -> str:
        return f"{self.ssh_user}@{self.tailscale_ip}"

    def weight(self, total_cpus: int) -> float:
        """Proportional compute weight in the topology."""
        return self.cpus / total_cpus if total_cpus > 0 else 0.0


TOPOLOGY = [
    Node(
        name="qfox-1",
        tailscale_ip="100.88.57.96",
        ssh_user="allaun",
        cpus=12,
        ram_gib=30.0,
        gpu="NVIDIA GeForce RTX 4070 SUPER",
        gpu_vram_gib=12.0,
        accelerator="cuda",
        role="head",
        is_local=True,
    ),
    Node(
        name="laptop-1",
        tailscale_ip="100.101.198.87",
        ssh_user="allaun",
        cpus=16,
        ram_gib=14.0,
        gpu="AMD Lucienne APU",
        gpu_vram_gib=0.0,
        accelerator="rocm",
        role="worker",
    ),
    Node(
        name="cupfox",
        tailscale_ip="100.126.151.57",
        ssh_user="root",
        cpus=2,
        ram_gib=4.0,
        gpu=None,
        gpu_vram_gib=0.0,
        accelerator=None,
        role="worker",
    ),
]


def get_topology() -> list[Node]:
    return TOPOLOGY


def total_cpus() -> int:
    return sum(n.cpus for n in TOPOLOGY)


def total_ram() -> float:
    return sum(n.ram_gib for n in TOPOLOGY)


# ═══════════════════════════════════════════════════════════════════════════
# §2  SSH Execution Layer
# ═══════════════════════════════════════════════════════════════════════════

SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=5",
    "-o", "BatchMode=yes",
]


def ssh_exec(node: Node, cmd: str, timeout: int = 30) -> dict:
    """Execute a command on a remote node via SSH. Returns result dict."""
    if node.is_local:
        full_cmd = ["bash", "-c", cmd]
    else:
        full_cmd = ["ssh"] + SSH_OPTS + [node.ssh_target, cmd]

    t0 = time.time()
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - t0
        return {
            "node": node.name,
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "elapsed_s": round(elapsed, 3),
        }
    except subprocess.TimeoutExpired:
        return {
            "node": node.name,
            "success": False,
            "stdout": "",
            "stderr": f"SSH timeout after {timeout}s",
            "returncode": -1,
            "elapsed_s": timeout,
        }
    except Exception as e:
        return {
            "node": node.name,
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "elapsed_s": time.time() - t0,
        }


def ssh_exec_python(node: Node, script: str, timeout: int = 60) -> dict:
    """Execute a Python script on a remote node."""
    # Escape the script for safe transmission over SSH
    escaped = script.replace("'", "'\\''")
    cmd = f"{node.python_bin} -c '{escaped}'"
    return ssh_exec(node, cmd, timeout=timeout)


# ═══════════════════════════════════════════════════════════════════════════
# §3  Topology Health & Status
# ═══════════════════════════════════════════════════════════════════════════

def check_node_health(node: Node) -> dict:
    """Probe a node for health status."""
    probe_script = """
import json, platform, os
try:
    import torch
    torch_ver = torch.__version__
    cuda = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda else None
except:
    torch_ver = None; cuda = False; gpu_name = None

info = {
    "hostname": platform.node(),
    "cpus": os.cpu_count(),
    "torch": torch_ver,
    "cuda": cuda,
    "gpu": gpu_name,
}
print(json.dumps(info))
"""
    result = ssh_exec_python(node, probe_script, timeout=15)
    health = {
        "node": node.name,
        "ip": node.tailscale_ip,
        "reachable": result["success"],
        "latency_ms": round(result["elapsed_s"] * 1000),
    }
    if result["success"]:
        try:
            info = json.loads(result["stdout"])
            health.update(info)
        except json.JSONDecodeError:
            health["raw"] = result["stdout"]
    else:
        health["error"] = result["stderr"]
    return health


def print_status():
    """Print live topology status."""
    print(f"╔{'═'*62}╗")
    print(f"║  {'Cooperative Compute Topology — Status':^60}║")
    print(f"╠{'═'*62}╣")

    # Probe all nodes in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TOPOLOGY)) as pool:
        futures = {pool.submit(check_node_health, node): node for node in TOPOLOGY}
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # Sort by topology order
    results.sort(key=lambda r: [n.name for n in TOPOLOGY].index(r["node"]))

    active_cpus = 0
    active_ram = 0.0
    active_nodes = 0

    for health in results:
        node = next(n for n in TOPOLOGY if n.name == health["node"])
        alive = "🟢" if health["reachable"] else "🔴"
        role = "HEAD" if node.role == "head" else "WORK"
        lat = f"{health['latency_ms']}ms" if health["reachable"] else "timeout"
        gpu_str = health.get("gpu") or node.gpu or "—"
        torch_str = health.get("torch") or "—"

        print(f"║  {alive} {node.name:12s} [{role}]  {node.tailscale_ip:16s}  {lat:>7s}  ║")
        print(f"║     CPU: {node.cpus:2d}  RAM: {node.ram_gib:5.1f} GiB  GPU: {gpu_str[:30]:30s}║")
        print(f"║     torch: {torch_str:10s}  accel: {node.accelerator or '—':5s}               ║")
        print(f"╟{'─'*62}╢")

        if health["reachable"]:
            active_cpus += node.cpus
            active_ram += node.ram_gib
            active_nodes += 1

    total_c = total_cpus()
    total_r = total_ram()
    print(f"║  TOTAL: {active_nodes}/{len(TOPOLOGY)} nodes  "
          f"{active_cpus}/{total_c} CPUs  "
          f"{active_ram:.0f}/{total_r:.0f} GiB RAM             ║")
    print(f"╚{'═'*62}╝")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# §4  Distributed Task Execution
# ═══════════════════════════════════════════════════════════════════════════

def distribute_task(task_script: str, nodes: list[Node] = None,
                    timeout: int = 120) -> list[dict]:
    """Execute a Python script across all (or specified) topology nodes."""
    if nodes is None:
        nodes = TOPOLOGY

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(nodes)) as pool:
        futures = {}
        for node in nodes:
            f = pool.submit(ssh_exec_python, node, task_script, timeout)
            futures[f] = node

        results = []
        for future in concurrent.futures.as_completed(futures):
            node = futures[future]
            result = future.result()
            results.append(result)
            status = "✓" if result["success"] else "✗"
            print(f"  [{status}] {node.name}: {result['elapsed_s']:.1f}s")

    return results


def get_live_nodes(nodes: list[Node] = None) -> list[Node]:
    """Return only reachable nodes from the topology."""
    if nodes is None:
        nodes = TOPOLOGY
    live = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(nodes)) as pool:
        futures = {pool.submit(ssh_exec, n, f"{n.python_bin} -c 'print(1)'", timeout=10): n for n in nodes}
        for f in concurrent.futures.as_completed(futures):
            n = futures[f]
            if f.result()["success"]:
                live.append(n)
    return live


def distribute_chunked(data: list, task_fn_source: str,
                       nodes: list[Node] = None,
                       timeout: int = 120) -> list[dict]:
    """
    Split data proportionally across LIVE nodes based on CPU weight,
    then execute task_fn_source on each chunk.

    task_fn_source should define a function `process(chunk)` that
    returns a JSON-serializable result.
    """
    if nodes is None:
        nodes = get_live_nodes()

    tc = sum(n.cpus for n in nodes)
    chunks = []
    offset = 0
    for i, node in enumerate(nodes):
        chunk_size = len(data) * node.cpus // tc
        if i == len(nodes) - 1:
            chunk_size = len(data) - offset  # last node gets remainder
        chunks.append(data[offset:offset + chunk_size])
        offset += chunk_size

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(nodes)) as pool:
        futures = {}
        for node, chunk in zip(nodes, chunks):
            script = f"""
import json
chunk = {json.dumps(chunk)}
{task_fn_source}
result = process(chunk)
print(json.dumps(result))
"""
            f = pool.submit(ssh_exec_python, node, script, timeout)
            futures[f] = (node, len(chunk))

        for future in concurrent.futures.as_completed(futures):
            node, chunk_len = futures[future]
            result = future.result()
            status = "✓" if result["success"] else "✗"
            print(f"  [{status}] {node.name}: {chunk_len} items, {result['elapsed_s']:.1f}s")
            results.append(result)

    return results


# ═══════════════════════════════════════════════════════════════════════════
# §5  Test Workload
# ═══════════════════════════════════════════════════════════════════════════

def run_test():
    """Distribute a test computation across the topology."""
    print(f"\n{'─'*60}")
    print(f"  Topology Test — Distributed Computation")
    print(f"{'─'*60}\n")

    # Test 1: Simple probe on all nodes
    print("  [1/3] Probing all nodes...")
    probe = """
import platform, os, json
print(json.dumps({"host": platform.node(), "cpus": os.cpu_count(), "pid": os.getpid()}))
"""
    results = distribute_task(probe)
    for r in results:
        if r["success"]:
            print(f"        {r['node']}: {r['stdout']}")

    # Test 2: CPU-bound work distributed by weight (live nodes only)
    live = get_live_nodes()
    live_names = [n.name for n in live]
    print(f"\n  [2/3] Distributing CPU workload (30000 items across {len(live)} live nodes: {live_names})...")
    data = list(range(30000))
    task = """
def process(chunk):
    # Sum of squares — CPU bound
    total = sum(x*x for x in chunk)
    import platform
    return {"host": platform.node(), "items": len(chunk), "sum_sq": total}
"""
    results = distribute_chunked(data, task, nodes=live)
    total_sum = 0
    for r in results:
        if r["success"]:
            info = json.loads(r["stdout"])
            total_sum += info["sum_sq"]
            print(f"        {info['host']}: {info['items']} items → sum²={info['sum_sq']}")
    expected = sum(x*x for x in data)
    match = "✓ MATCH" if total_sum == expected else f"✗ MISMATCH ({total_sum} != {expected})"
    print(f"        Combined: {total_sum}  {match}")

    # Test 3: GPU availability check
    print(f"\n  [3/3] GPU availability scan...")
    gpu_probe = """
import json
try:
    import torch
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        mem = torch.cuda.get_device_properties(0).total_mem / (1024**3)
        print(json.dumps({"gpu": name, "vram_gib": round(mem, 1), "ready": True}))
    else:
        print(json.dumps({"gpu": None, "ready": False}))
except:
    print(json.dumps({"gpu": None, "ready": False, "error": "no torch"}))
"""
    results = distribute_task(gpu_probe)
    for r in results:
        if r["success"]:
            info = json.loads(r["stdout"])
            if info.get("ready"):
                print(f"        {r['node']}: 🟢 {info['gpu']} ({info['vram_gib']} GiB VRAM)")
            else:
                print(f"        {r['node']}: ⚪ CPU-only")

    print(f"\n{'─'*60}")
    print(f"  Topology test complete.")
    print(f"{'─'*60}\n")


# ═══════════════════════════════════════════════════════════════════════════
# §6  Entry Point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        print_status()
    elif cmd == "test":
        print_status()
        run_test()
    elif cmd == "run" and len(sys.argv) > 2:
        script_path = sys.argv[2]
        with open(script_path) as f:
            script = f.read()
        print_status()
        print(f"\nDistributing {script_path} across topology...")
        results = distribute_task(script)
        for r in results:
            print(f"\n{'='*40} {r['node']} {'='*40}")
            print(r["stdout"] if r["success"] else r["stderr"])
    elif cmd == "nodes":
        for n in TOPOLOGY:
            print(json.dumps(asdict(n), indent=2))
    else:
        print(__doc__)
