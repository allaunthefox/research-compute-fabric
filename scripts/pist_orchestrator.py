#!/usr/bin/env python3
"""
PIST Neuromorphic Orchestrator
==============================
The orchestrator is not a script. It is a topology.

Every action (prover call, build, module load, reboot) is a coordinate
transition on a manifold. The orchestrator learns which paths succeed,
strengthens them, and prunes dead branches.

Modes:
    observe   — passively watch system state, build DAG, no action
    suggest   — recommend next action based on learned topology
    execute   — perform action, observe result, update DAG

Architecture:
    Neurons   = task types (build, prove, load, reboot, benchmark)
    Synapses  = transitions between tasks (build→prove, prove→load)
    Weights   = success rate of each transition
    Plasticity= LTP/LTD based on observed outcomes

The orchestrator feeds its own byte stream into pist_neuromorphic.ko
so the kernel observer learns the orchestration pattern as part of
the system topology.
"""

import sys
import os
import json
import time
import hashlib
import subprocess
import random
import glob
import shutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Callable
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────
# PIST Geometry (mirrors kernel module logic in userspace)
# ──────────────────────────────────────────────────────────────────────────

def pist_encode_u8(n: int) -> int:
    """n = k² + t, return packed 32-bit coordinate."""
    k = int(n ** 0.5)
    t = n - k * k
    return (k << 16) | t

def pist_mirror(coord: int) -> int:
    """Involution: (k, t) → (k, 2k+1-t)"""
    k = (coord >> 16) & 0xFFFF
    t = coord & 0xFFFF
    return (k << 16) | (2 * k + 1 - t)

def pist_mass(coord: int) -> int:
    """t * (2k + 1 - t)"""
    k = (coord >> 16) & 0xFFFF
    t = coord & 0xFFFF
    return t * (2 * k + 1 - t)

def pist_tension(coord: int) -> float:
    """Normalized tension ∈ [0, 1)."""
    k = (coord >> 16) & 0xFFFF
    t = coord & 0xFFFF
    denom = 2 * k + 1
    return t / denom if denom > 0 else 0.0

# ──────────────────────────────────────────────────────────────────────────
# Neuromorphic DAG Node (mirrors kernel struct pist_dag_node)
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class Synapse:
    target: str           # neuron ID
    weight: float = 1.0   # Hebbian weight
    success_count: int = 0
    failure_count: int = 0
    last_seen: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5

    def potentiate(self, delta: float = 0.1):
        """LTP — strengthen synapse on success."""
        self.weight = min(self.weight * (1 + delta), 100.0)
        self.success_count += 1
        self.last_seen = time.time()

    def depress(self, delta: float = 0.2):
        """LTD — weaken synapse on failure."""
        self.weight = max(self.weight * (1 - delta), 0.01)
        self.failure_count += 1
        self.last_seen = time.time()

@dataclass
class Neuron:
    nid: str                       # neuron ID
    task_type: str                 # build, prove, load, reboot, benchmark, etc.
    coord: int = 0                 # PIST coordinate of this neuron
    activation: float = 0.0        # current activation level [0, 1]
    visit_count: int = 0
    total_mass: int = 0
    synapses: List[Synapse] = field(default_factory=list)

    def __post_init__(self):
        if self.coord == 0:
            # Derive coordinate from hash of neuron ID
            h = hashlib.sha256(self.nid.encode()).digest()
            self.coord = pist_encode_u8(h[0])

    def activate(self, stimulus: float = 1.0):
        """Fire neuron — increase activation, update mass."""
        self.activation = min(self.activation + stimulus, 1.0)
        self.visit_count += 1
        self.total_mass += pist_mass(self.coord)

    def decay(self, rate: float = 0.01):
        """Exponential decay of activation."""
        self.activation *= (1 - rate)

    def get_synapse(self, target: str) -> Synapse:
        """Find or create synapse to target."""
        for s in self.synapses:
            if s.target == target:
                return s
        s = Synapse(target=target)
        self.synapses.append(s)
        return s

    def choose_next(self, temperature: float = 1.0) -> Optional[str]:
        """Softmax selection of next neuron based on synapse weights."""
        if not self.synapses:
            return None
        weights = [s.weight * s.success_rate for s in self.synapses]
        # Boltzmann distribution
        exp_w = [w ** (1 / temperature) for w in weights]
        total = sum(exp_w)
        probs = [e / total for e in exp_w]
        # Roulette wheel selection
        r = random.random()
        cumsum = 0.0
        for syn, p in zip(self.synapses, probs):
            cumsum += p
            if r <= cumsum:
                return syn.target
        return self.synapses[-1].target

# ──────────────────────────────────────────────────────────────────────────
# Neuromorphic Orchestrator State
# ──────────────────────────────────────────────────────────────────────────

class NeuromorphicOrchestrator:
    def __init__(self, state_file: Optional[str] = None):
        self.neurons: Dict[str, Neuron] = {}
        self.current_neuron: Optional[str] = None
        self.execution_log: List[dict] = []
        self.dag_generation: int = 0
        self.state_file = state_file or self._default_state_path()
        self.mode: str = "observe"  # observe | suggest | execute
        self._init_default_neurons()
        self._load_state()

    def _default_state_path(self) -> str:
        base = Path.home() / "CascadeProjects" / "Research-Stack"
        return str(base / ".windsurf" / "telemetry" / "orchestrator_state.json")

    def _init_default_neurons(self):
        """Bootstrap the default task topology."""
        tasks = [
            "idle", "diagnose", "build", "prove", "load_module",
            "reboot", "benchmark", "export_dag", "collect_data",
            "fix_toolchain", "ghost_ingested", "compress_baseline"
        ]
        for t in tasks:
            self._get_or_create(t)

        # Default topology (bootstrap connections)
        self._connect("idle", "diagnose", 1.0)
        self._connect("diagnose", "build", 0.8)
        self._connect("diagnose", "fix_toolchain", 0.6)
        self._connect("build", "prove", 0.7)
        self._connect("build", "benchmark", 0.3)
        self._connect("prove", "load_module", 0.4)
        self._connect("prove", "export_dag", 0.2)
        self._connect("fix_toolchain", "build", 0.9)
        self._connect("load_module", "collect_data", 0.8)
        self._connect("collect_data", "compress_baseline", 0.5)
        self._connect("benchmark", "export_dag", 0.6)
        self._connect("build", "ghost_ingested", 0.2)
        self._connect("reboot", "diagnose", 0.9)

    def _get_or_create(self, nid: str, task_type: Optional[str] = None) -> Neuron:
        if nid not in self.neurons:
            self.neurons[nid] = Neuron(nid=nid, task_type=task_type or nid)
        return self.neurons[nid]

    def _connect(self, src: str, dst: str, initial_weight: float = 1.0):
        n = self._get_or_create(src)
        syn = n.get_synapse(dst)
        syn.weight = initial_weight

    def _load_state(self):
        if not os.path.exists(self.state_file):
            return
        try:
            with open(self.state_file) as f:
                data = json.load(f)
            self.dag_generation = data.get("dag_generation", 0)
            self.mode = data.get("mode", "observe")
            for nid, ndata in data.get("neurons", {}).items():
                n = self._get_or_create(nid, ndata.get("task_type", nid))
                n.coord = ndata.get("coord", n.coord)
                n.visit_count = ndata.get("visit_count", 0)
                n.total_mass = ndata.get("total_mass", 0)
                for sdata in ndata.get("synapses", []):
                    syn = n.get_synapse(sdata["target"])
                    syn.weight = sdata.get("weight", 1.0)
                    syn.success_count = sdata.get("success_count", 0)
                    syn.failure_count = sdata.get("failure_count", 0)
        except Exception as e:
            print(f"[orchestrator] state load warning: {e}", file=sys.stderr)

    def save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        data = {
            "dag_generation": self.dag_generation,
            "mode": self.mode,
            "timestamp": time.time(),
            "neurons": {}
        }
        for nid, n in self.neurons.items():
            data["neurons"][nid] = {
                "task_type": n.task_type,
                "coord": n.coord,
                "visit_count": n.visit_count,
                "total_mass": n.total_mass,
                "synapses": [
                    {
                        "target": s.target,
                        "weight": s.weight,
                        "success_count": s.success_count,
                        "failure_count": s.failure_count,
                        "last_seen": s.last_seen
                    }
                    for s in n.synapses
                ]
            }
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    # ──────────────────────────────────────────────────────────────────────
    # Observation & Learning
    # ──────────────────────────────────────────────────────────────────────

    def observe(self, from_task: str, to_task: str, outcome: bool,
                metadata: Optional[dict] = None):
        """Record a transition and apply Hebbian plasticity."""
        src = self._get_or_create(from_task)
        dst = self._get_or_create(to_task)
        syn = src.get_synapse(to_task)

        if outcome:
            syn.potentiate()
            dst.activate(stimulus=0.5)
        else:
            syn.depress()
            dst.activate(stimulus=-0.3)

        self.execution_log.append({
            "timestamp": time.time(),
            "from": from_task,
            "to": to_task,
            "outcome": outcome,
            "metadata": metadata or {}
        })

        self.dag_generation += 1
        self._feed_to_kernel(from_task, to_task, outcome)

    def _feed_to_kernel(self, from_task: str, to_task: str, outcome: bool):
        """Feed orchestrator transitions into pist_neuromorphic.ko."""
        sample_path = Path("/sys/kernel/pist_neuromorphic/sample")
        if not sample_path.exists():
            return
        try:
            payload = f"{from_task}→{to_task}:{int(outcome)}\n".encode()
            with open(sample_path, "wb") as f:
                f.write(payload)
        except PermissionError:
            pass  # Not running as root — expected
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────
    # Execution Primitives
    # ──────────────────────────────────────────────────────────────────────

    def run_build(self) -> bool:
        """Execute lake build, observe result."""
        print("[orchestrator] → run_build")
        start = time.time()
        proc = subprocess.run(
            ["lake", "build"],
            cwd=Path.home() / "CascadeProjects" / "Research-Stack" / "0-Core-Formalism" / "lean" / "Semantics",
            capture_output=True, text=True
        )
        elapsed = time.time() - start
        success = proc.returncode == 0
        self.observe("build", "prove" if success else "fix_toolchain", success,
                     {"elapsed": elapsed, "stdout_lines": len(proc.stdout.splitlines())})
        return success

    def run_prover(self, target_file: str, model: str = "zeyu-zheng/BFS-Prover-V2-7B:q8_0") -> bool:
        """Run BFS-Prover on a target file."""
        print(f"[orchestrator] → run_prover({target_file})")
        bf4prover = Path.home() / "CascadeProjects" / "Research-Stack" / "scripts" / "bf4prover.py"
        start = time.time()
        proc = subprocess.run(
            [sys.executable, str(bf4prover), "--file", target_file],
            capture_output=True, text=True
        )
        elapsed = time.time() - start
        success = proc.returncode == 0
        self.observe("prove", "load_module" if success else "reboot", success,
                     {"elapsed": elapsed, "model": model})
        return success

    def load_kernel_module(self) -> bool:
        """Load pist_neuromorphic.ko."""
        print("[orchestrator] → load_kernel_module")
        kmod = Path.home() / "CascadeProjects" / "Research-Stack" / "6-Kernel-Shim" / "pist_neuromorphic.ko"
        proc = subprocess.run(["sudo", "insmod", str(kmod)], capture_output=True, text=True)
        success = proc.returncode == 0
        self.observe("load_module", "collect_data" if success else "reboot", success,
                     {"stderr": proc.stderr[:200] if not success else ""})
        return success

    def diagnose(self) -> dict:
        """System diagnostic — returns observational data."""
        print("[orchestrator] → diagnose")
        result = {}

        # Kernel version
        try:
            with open("/proc/version") as f:
                result["kernel"] = f.read().strip()
        except Exception:
            result["kernel"] = "unknown"

        # NVIDIA
        try:
            proc = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            result["gpu"] = "available" if proc.returncode == 0 else proc.stderr[:200]
        except FileNotFoundError:
            result["gpu"] = "not_installed"

        # Ollama
        try:
            proc = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
            result["ollama"] = proc.stdout.strip()
        except FileNotFoundError:
            result["ollama"] = "not_installed"

        # Kernel module
        result["neuromorphic_module"] = os.path.exists("/sys/kernel/pist_neuromorphic")

        # Lean toolchain
        try:
            tc = Path.home() / "CascadeProjects" / "Research-Stack" / "0-Core-Formalism" / "lean" / "Semantics" / "lean-toolchain"
            result["lean_toolchain"] = tc.read_text().strip()
        except Exception:
            result["lean_toolchain"] = "unknown"

        self.observe("idle", "diagnose", True, result)
        return result

    def scan_lean_topology(self) -> dict:
        """Discover all .lean files, count sorry, create neurons per module."""
        print("[orchestrator] → scan_lean_topology")
        base = Path.home() / "CascadeProjects" / "Research-Stack"
        findings = {"canonical": {}, "external": {}, "ingested": {}, "other": {}, "total_sorry": 0}

        for path in base.rglob("*.lean"):
            if ".lake" in str(path) or "build" in str(path) or "build-static" in str(path):
                continue

            rel = str(path.relative_to(base))
            try:
                text = path.read_text()
            except Exception:
                continue

            sorry_count = text.count("\n  sorry") + text.count("\n    sorry")
            if sorry_count == 0:
                continue

            findings["total_sorry"] += sorry_count

            # Bucket classification
            if rel.startswith("0-Core-Formalism/lean/Semantics/Semantics/"):
                bucket = "canonical"
            elif rel.startswith("0-Core-Formalism/lean/external/"):
                bucket = "external"
            elif "shared-data/data/ingested/" in rel:
                bucket = "ingested"
            elif "archive/" in rel:
                continue  # Skip archives
            else:
                bucket = "other"

            findings[bucket][rel] = sorry_count

            # Create neuron for high-sorry files
            if sorry_count >= 2:
                nid = f"file_{rel.replace('/', '_').replace('.', '_')}"
                n = self._get_or_create(nid, task_type="prove_file")
                n.coord = pist_encode_u8(min(sorry_count * 16, 255))
                # Connect file neuron to prove and ghost actions
                self._connect(nid, "prove", initial_weight=float(sorry_count))
                self._connect(nid, "ghost_ingested" if bucket == "ingested" else "prove", initial_weight=1.0)

        # Create summary neurons
        for bucket, files in findings.items():
            if bucket == "total_sorry":
                continue
            nid = f"summary_{bucket}"
            n = self._get_or_create(nid, task_type="summary")
            n.total_mass = sum(files.values())
            self._connect(nid, "prove" if bucket == "canonical" else "ghost_ingested", initial_weight=float(n.total_mass))

        self.observe("diagnose", "scan_lean_topology", True,
                     {"total_sorry": findings["total_sorry"],
                      "canonical_files": len(findings["canonical"]),
                      "ingested_files": len(findings["ingested"])})
        return findings

    def fix_toolchain(self) -> bool:
        """Revert lean-toolchain to v4.29.1 to restore mathlib cache."""
        print("[orchestrator] → fix_toolchain")
        base = Path.home() / "CascadeProjects" / "Research-Stack" / "0-Core-Formalism" / "lean" / "Semantics"
        tc_file = base / "lean-toolchain"
        lake_file = base / "lakefile.toml"
        success = False

        try:
            # Revert toolchain
            tc_file.write_text("leanprover/lean4:v4.29.1\n")
            # Revert mathlib rev in lakefile.toml
            text = lake_file.read_text()
            text = text.replace("v4.30.0-rc2", "v4.29.1")
            lake_file.write_text(text)
            # Clean and update
            subprocess.run(["lake", "clean"], cwd=base, capture_output=True)
            proc = subprocess.run(["lake", "update"], cwd=base, capture_output=True, text=True)
            success = proc.returncode == 0
        except Exception as e:
            print(f"[orchestrator] fix_toolchain error: {e}", file=sys.stderr)

        self.observe("fix_toolchain", "build" if success else "diagnose", success,
                     {"toolchain": "v4.29.1"})
        return success

    def ghost_ingested(self) -> bool:
        """Rename ingested .lean files with .GHOST suffix."""
        print("[orchestrator] → ghost_ingested")
        base = Path.home() / "CascadeProjects" / "Research-Stack" / "shared-data" / "data" / "ingested"
        ghosted = 0
        try:
            for path in base.rglob("*.lean"):
                if not path.name.endswith(".GHOST"):
                    ghost_path = path.with_suffix(path.suffix + ".GHOST")
                    shutil.move(str(path), str(ghost_path))
                    ghosted += 1
        except Exception as e:
            print(f"[orchestrator] ghost_ingested error: {e}", file=sys.stderr)

        success = ghosted > 0
        self.observe("ghost_ingested", "build", success, {"ghosted_count": ghosted})
        return success

    def run_benchmark(self) -> bool:
        """Run PIST compression benchmark on Canterbury Corpus."""
        print("[orchestrator] → run_benchmark")
        base = Path.home() / "CascadeProjects" / "Research-Stack"
        bench_dir = base / "shared-data" / "data" / "groundtruth" / "compression-baselines"
        pist_script = base / "Desktop" / "pist_biological_polymorphic_shifter_v3_complete.py"
        success = False
        results = {}

        try:
            for fpath in bench_dir.iterdir():
                if not fpath.is_file():
                    continue
                data = fpath.read_bytes()
                orig_size = len(data)
                # Simple coordinate encoding as baseline
                coords = [pist_encode_u8(b) for b in data[:4096]]  # Sample first 4KB
                coord_bytes = len(coords) * 4
                ratio = orig_size / coord_bytes if coord_bytes > 0 else 0
                results[fpath.name] = {"original": orig_size, "coord_4k": coord_bytes, "ratio": ratio}
            success = True
        except Exception as e:
            print(f"[orchestrator] benchmark error: {e}", file=sys.stderr)

        self.observe("compress_baseline", "export_dag", success, {"files_tested": len(results)})
        return success

    # ──────────────────────────────────────────────────────────────────────
    # Topological Navigation
    # ──────────────────────────────────────────────────────────────────────

    def step(self, temperature: float = 1.0) -> Optional[str]:
        """Take one step on the manifold. Returns next task or None."""
        if self.current_neuron is None:
            self.current_neuron = "idle"

        n = self.neurons.get(self.current_neuron)
        if not n:
            return None

        n.activate()
        next_id = n.choose_next(temperature=temperature)
        if next_id:
            print(f"[orchestrator] {self.current_neuron} → {next_id} "
                  f"(tension={pist_tension(n.coord):.3f}, mass={n.total_mass})")
        self.current_neuron = next_id
        return next_id

    def walk(self, max_steps: int = 10, temperature: float = 1.0) -> List[str]:
        """Walk the manifold, executing tasks in execute mode."""
        path = []
        for _ in range(max_steps):
            task = self.step(temperature=temperature)
            if task is None:
                break
            path.append(task)

            if self.mode == "execute":
                self._execute_task(task)
            elif self.mode == "suggest":
                print(f"[orchestrator] SUGGEST: {task}")

        self.save_state()
        return path

    def _execute_task(self, task: str):
        """Dispatch task to execution primitive."""
        handlers = {
            "diagnose": self.diagnose,
            "build": self.run_build,
            "prove": self.run_prover,
            "load_module": self.load_kernel_module,
            "fix_toolchain": self.fix_toolchain,
            "ghost_ingested": self.ghost_ingested,
            "compress_baseline": self.run_benchmark,
            "scan": self.scan_lean_topology,
        }
        handler = handlers.get(task)
        if handler:
            try:
                result = handler()
                # Auto-observe success if handler returns truthy
                if result:
                    n = self.neurons.get(task)
                    if n:
                        for syn in n.synapses:
                            syn.potentiate()
            except Exception as e:
                print(f"[orchestrator] task {task} failed: {e}", file=sys.stderr)
                n = self.neurons.get(task)
                if n:
                    for syn in n.synapses:
                        syn.depress()
        elif task.startswith("file_"):
            # File-specific neuron — extract original path
            print(f"[orchestrator] target file neuron: {task}")

    def continuous_loop(self, interval: float = 60.0, temperature: float = 1.0):
        """Run forever, adapting temperature based on crisis level."""
        print(f"[orchestrator] ENTERING CONTINUOUS LOOP (interval={interval}s)")
        consecutive_failures = 0
        while True:
            try:
                # Crisis detection: too many failures → force exploration
                if consecutive_failures >= 3:
                    temperature = min(temperature * 1.5, 5.0)
                    print(f"[orchestrator] CRISIS MODE: temperature bumped to {temperature}")

                task = self.step(temperature=temperature)
                if task is None:
                    time.sleep(interval)
                    continue

                if self.mode == "execute":
                    result = self._execute_task_and_report(task)
                    if result:
                        consecutive_failures = max(0, consecutive_failures - 1)
                        temperature = max(temperature * 0.9, 0.5)
                    else:
                        consecutive_failures += 1
                elif self.mode == "suggest":
                    print(f"[orchestrator] SUGGEST: {task}")

                self.save_state()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("[orchestrator] Interrupted by user")
                self.save_state()
                break

    def _execute_task_and_report(self, task: str) -> bool:
        """Execute and auto-observe with proper transition tracking."""
        prev = self.current_neuron
        handlers = {
            "diagnose": self.diagnose,
            "build": self.run_build,
            "prove": lambda: self.run_prover("Semantics/FixedPoint.lean"),
            "load_module": self.load_kernel_module,
            "fix_toolchain": self.fix_toolchain,
            "ghost_ingested": self.ghost_ingested,
            "compress_baseline": self.run_benchmark,
            "scan": self.scan_lean_topology,
        }
        handler = handlers.get(task)
        if not handler:
            return False
        try:
            result = handler()
            success = bool(result) if result is not None else True
        except Exception as e:
            print(f"[orchestrator] execution failed: {e}", file=sys.stderr)
            success = False

        if prev and task:
            self.observe(prev, task, success, {"auto": True})
        return success

    # ──────────────────────────────────────────────────────────────────────
    # DAG Export
    # ──────────────────────────────────────────────────────────────────────

    def export_dag(self, path: Optional[str] = None) -> str:
        """Export current DAG as text."""
        lines = [
            f"# PIST Neuromorphic Orchestrator DAG",
            f"# generation={self.dag_generation} mode={self.mode}",
            f"# timestamp={datetime.now().isoformat()}",
            "# neuron_id task_type coord visit_count mass"
        ]
        for nid, n in sorted(self.neurons.items(), key=lambda x: -x[1].visit_count):
            lines.append(
                f"{nid} {n.task_type} 0x{n.coord:08x} {n.visit_count} {n.total_mass}"
            )
            for s in sorted(n.synapses, key=lambda x: -x.weight)[:5]:
                lines.append(f"  → {s.target} w={s.weight:.2f} sr={s.success_rate:.2f}")

        text = "\n".join(lines) + "\n"
        if path:
            with open(path, "w") as f:
                f.write(text)
        return text


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="PIST Neuromorphic Orchestrator")
    parser.add_argument("--mode", choices=["observe", "suggest", "execute"],
                        default="observe", help="Orchestrator mode")
    parser.add_argument("--steps", type=int, default=5, help="Max manifold walk steps")
    parser.add_argument("--temperature", type=float, default=1.0,
                        help="Exploration temperature (higher = more random)")
    parser.add_argument("--export", type=str, help="Export DAG to file")
    parser.add_argument("--feed-kernel", action="store_true",
                        help="Feed orchestrator state into pist_neuromorphic.ko")
    parser.add_argument("--diagnose", action="store_true",
                        help="Run system diagnostic and exit")
    parser.add_argument("--scan", action="store_true",
                        help="Scan Lean topology and exit")
    parser.add_argument("--loop", action="store_true",
                        help="Run continuous adaptive loop")
    parser.add_argument("--interval", type=float, default=60.0,
                        help="Loop interval in seconds (default: 60)")
    args = parser.parse_args()

    orch = NeuromorphicOrchestrator()
    orch.mode = args.mode

    if args.diagnose:
        result = orch.diagnose()
        print(json.dumps(result, indent=2))
        orch.save_state()
        return

    if args.scan:
        findings = orch.scan_lean_topology()
        print(json.dumps(findings, indent=2))
        orch.save_state()
        return

    if args.export:
        orch.export_dag(args.export)
        print(f"[orchestrator] DAG exported to {args.export}")
        return

    print(f"[orchestrator] mode={args.mode} steps={args.steps} temp={args.temperature}")
    print(f"[orchestrator] dag_generation={orch.dag_generation}")
    print(f"[orchestrator] neurons={len(orch.neurons)}")

    if args.loop:
        orch.continuous_loop(interval=args.interval, temperature=args.temperature)
        return

    path = orch.walk(max_steps=args.steps, temperature=args.temperature)
    print(f"[orchestrator] path={' → '.join(path)}")
    orch.save_state()

    # Feed to kernel if requested
    if args.feed_kernel:
        state_text = json.dumps({
            "dag_generation": orch.dag_generation,
            "path": path,
            "neuron_count": len(orch.neurons)
        })
        try:
            with open("/sys/kernel/pist_neuromorphic/sample", "wb") as f:
                f.write(state_text.encode())
            print("[orchestrator] state fed to kernel module")
        except Exception as e:
            print(f"[orchestrator] kernel feed failed: {e}")


if __name__ == "__main__":
    main()
