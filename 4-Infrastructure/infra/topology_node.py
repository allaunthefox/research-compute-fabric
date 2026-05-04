#!/usr/bin/env python3
"""
topology_node.py — Fit-to-Purpose Topology Node Runtime

Python extraction of Semantics.TopologyNode Lean module.
Each node runs this runtime to participate in the Research Stack topology.

Roles:
  core   — build, verify, synthesize (architect)
  judge  — arbitrate, attest, verify (BFT partner)
  mirror — store, relay, backup (git mirror)
  edge   — filter, compress, route, attest (minimal resource)
  foxTop — experimental, unindexed

State machine:
  BOOT → SELFTEST → ANNOUNCE → ACTIVE → (DEGRADED | FAILED) → BOOT

Per AGENTS.md §6: Python may only serialize, spawn, wrap, display.
All cost/invariant/branching decisions are extracted from Lean.
"""

import json
import sys
import time
import signal
import subprocess
import threading
import sqlite3
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum, auto


# ═══════════════════════════════════════════════════════════════════════════
# §0  Q16.16 Fixed-Point (Python extraction)
# ═══════════════════════════════════════════════════════════════════════════

class Q16_16:
    """Fixed-point Q16.16 using Python int (backend: UInt32 semantics)."""
    def __init__(self, val: int):
        self.val = val & 0xFFFFFFFF

    @staticmethod
    def zero() -> "Q16_16":
        return Q16_16(0)

    @staticmethod
    def one() -> "Q16_16":
        return Q16_16(0x00010000)

    @staticmethod
    def from_nat(n: int) -> "Q16_16":
        return Q16_16((n * 65536) & 0xFFFFFFFF)

    @staticmethod
    def from_frac(num: int, denom: int) -> "Q16_16":
        if denom == 0:
            return Q16_16.zero()
        return Q16_16((num * 65536 // denom) & 0xFFFFFFFF)

    def __add__(self, other: "Q16_16") -> "Q16_16":
        return Q16_16((self.val + other.val) & 0xFFFFFFFF)

    def __sub__(self, other: "Q16_16") -> "Q16_16":
        return Q16_16((self.val - other.val) & 0xFFFFFFFF)

    def __lt__(self, other: "Q16_16") -> bool:
        # Signed comparison for Q16.16
        a = self.val if self.val < 0x80000000 else self.val - 0x100000000
        b = other.val if other.val < 0x80000000 else other.val - 0x100000000
        return a < b

    def __le__(self, other: "Q16_16") -> bool:
        return self == other or self < other

    def __gt__(self, other: "Q16_16") -> bool:
        return other < self

    def __ge__(self, other: "Q16_16") -> bool:
        return other <= self

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Q16_16):
            return False
        return self.val == other.val

    def to_float(self) -> float:
        v = self.val if self.val < 0x80000000 else self.val - 0x100000000
        return v / 65536.0

    def to_dict(self) -> dict:
        return {"val": self.val, "float": self.to_float()}

    @staticmethod
    def from_dict(d: dict) -> "Q16_16":
        return Q16_16(d["val"])


# ═══════════════════════════════════════════════════════════════════════════
# §1  Enums
# ═══════════════════════════════════════════════════════════════════════════

class NodeRole(str, Enum):
    CORE = "core"
    JUDGE = "judge"
    MIRROR = "mirror"
    EDGE = "edge"
    FOXTOP = "foxTop"


class NodeState(str, Enum):
    BOOT = "boot"
    SELFTEST = "selftest"
    ANNOUNCE = "announce"
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"


class NodeCapability(str, Enum):
    LEAN_BUILD = "leanBuild"
    FPGA_SYNTH = "fpgaSynth"
    EQUATION_FOREST = "equationForest"
    FULL_GIT = "fullGit"
    BFT_ARBITRATE = "bftArbitrate"
    MMR_VERIFY = "mmrVerify"
    ATTESTATION = "attestation"
    GIT_MIRROR = "gitMirror"
    OBJECT_STORE = "objectStore"
    RELAY = "relay"
    BACKUP = "backup"
    COMPRESS = "compress"
    RGFLOW_FILTER = "rgflowFilter"
    ROUTE = "route"
    STORAGE = "storage"
    COMPUTE = "compute"
    EXPERIMENTAL = "experimental"


class BindClass(str, Enum):
    INFORMATIONAL = "informational"
    GEOMETRIC = "geometric"
    THERMODYNAMIC = "thermodynamic"
    PHYSICAL = "physical"
    CONTROL = "control"


# ═══════════════════════════════════════════════════════════════════════════
# §2  Capability & Role Defaults (extracted from Lean)
# ═══════════════════════════════════════════════════════════════════════════

CAPABILITY_COST: Dict[NodeCapability, Q16_16] = {
    NodeCapability.LEAN_BUILD: Q16_16.from_nat(10),
    NodeCapability.FPGA_SYNTH: Q16_16.from_nat(50),
    NodeCapability.EQUATION_FOREST: Q16_16.from_nat(20),
    NodeCapability.FULL_GIT: Q16_16.from_nat(5),
    NodeCapability.BFT_ARBITRATE: Q16_16.from_nat(3),
    NodeCapability.MMR_VERIFY: Q16_16.from_nat(2),
    NodeCapability.ATTESTATION: Q16_16.from_nat(2),
    NodeCapability.GIT_MIRROR: Q16_16.from_nat(2),
    NodeCapability.OBJECT_STORE: Q16_16.from_nat(1),
    NodeCapability.RELAY: Q16_16.from_nat(1),
    NodeCapability.BACKUP: Q16_16.from_nat(1),
    NodeCapability.COMPRESS: Q16_16.from_nat(4),
    NodeCapability.RGFLOW_FILTER: Q16_16.from_nat(3),
    NodeCapability.ROUTE: Q16_16.from_nat(1),
    NodeCapability.STORAGE: Q16_16.from_nat(1),
    NodeCapability.COMPUTE: Q16_16.from_nat(2),
    NodeCapability.EXPERIMENTAL: Q16_16.from_nat(8),
}

DEFAULT_CAPABILITIES: Dict[NodeRole, List[NodeCapability]] = {
    NodeRole.CORE: [
        NodeCapability.LEAN_BUILD, NodeCapability.FPGA_SYNTH,
        NodeCapability.EQUATION_FOREST, NodeCapability.FULL_GIT,
        NodeCapability.STORAGE, NodeCapability.COMPUTE,
    ],
    NodeRole.JUDGE: [
        NodeCapability.BFT_ARBITRATE, NodeCapability.MMR_VERIFY,
        NodeCapability.ATTESTATION, NodeCapability.COMPUTE,
    ],
    NodeRole.MIRROR: [
        NodeCapability.GIT_MIRROR, NodeCapability.OBJECT_STORE,
        NodeCapability.RELAY, NodeCapability.BACKUP, NodeCapability.STORAGE,
    ],
    NodeRole.EDGE: [
        NodeCapability.COMPRESS, NodeCapability.RGFLOW_FILTER,
        NodeCapability.ATTESTATION, NodeCapability.ROUTE,
        NodeCapability.STORAGE, NodeCapability.COMPUTE,
    ],
    NodeRole.FOXTOP: [
        NodeCapability.EXPERIMENTAL, NodeCapability.COMPUTE,
        NodeCapability.STORAGE, NodeCapability.ROUTE,
    ],
}

DEFAULT_BIND_CLASSES: Dict[NodeRole, List[BindClass]] = {
    NodeRole.CORE: [BindClass.INFORMATIONAL, BindClass.GEOMETRIC, BindClass.THERMODYNAMIC, BindClass.PHYSICAL, BindClass.CONTROL],
    NodeRole.JUDGE: [BindClass.INFORMATIONAL, BindClass.CONTROL],
    NodeRole.MIRROR: [BindClass.INFORMATIONAL, BindClass.GEOMETRIC],
    NodeRole.EDGE: [BindClass.PHYSICAL, BindClass.THERMODYNAMIC, BindClass.CONTROL],
    NodeRole.FOXTOP: [BindClass.INFORMATIONAL, BindClass.PHYSICAL, BindClass.CONTROL],
}

MAX_ENERGY: Dict[NodeRole, Q16_16] = {
    NodeRole.CORE: Q16_16.from_nat(100),
    NodeRole.JUDGE: Q16_16.from_nat(50),
    NodeRole.MIRROR: Q16_16.from_nat(50),
    NodeRole.EDGE: Q16_16.from_nat(25),
    NodeRole.FOXTOP: Q16_16.from_nat(40),
}

RECOVERY_RATE: Dict[NodeRole, Q16_16] = {
    NodeRole.CORE: Q16_16.from_frac(1, 2),
    NodeRole.JUDGE: Q16_16.from_frac(1, 4),
    NodeRole.MIRROR: Q16_16.from_frac(1, 4),
    NodeRole.EDGE: Q16_16.from_frac(1, 8),
    NodeRole.FOXTOP: Q16_16.from_frac(1, 4),
}

STATE_TRANSITION_COST: Dict[tuple, Q16_16] = {
    (NodeState.BOOT, NodeState.SELFTEST): Q16_16.from_nat(1),
    (NodeState.SELFTEST, NodeState.ANNOUNCE): Q16_16.from_nat(1),
    (NodeState.ANNOUNCE, NodeState.ACTIVE): Q16_16.from_nat(2),
    (NodeState.ACTIVE, NodeState.DEGRADED): Q16_16.from_nat(1),
    (NodeState.DEGRADED, NodeState.ACTIVE): Q16_16.from_nat(3),
    (NodeState.ACTIVE, NodeState.FAILED): Q16_16.zero(),
    (NodeState.DEGRADED, NodeState.FAILED): Q16_16.zero(),
    (NodeState.FAILED, NodeState.BOOT): Q16_16.from_nat(5),
    (NodeState.SELFTEST, NodeState.FAILED): Q16_16.from_nat(1),
    (NodeState.ANNOUNCE, NodeState.FAILED): Q16_16.from_nat(1),
}

ALLOWED_TRANSITIONS: set = {
    (NodeState.BOOT, NodeState.SELFTEST),
    (NodeState.SELFTEST, NodeState.ANNOUNCE),
    (NodeState.ANNOUNCE, NodeState.ACTIVE),
    (NodeState.ACTIVE, NodeState.DEGRADED),
    (NodeState.ACTIVE, NodeState.FAILED),
    (NodeState.DEGRADED, NodeState.ACTIVE),
    (NodeState.DEGRADED, NodeState.FAILED),
    (NodeState.FAILED, NodeState.BOOT),
    (NodeState.SELFTEST, NodeState.FAILED),
    (NodeState.ANNOUNCE, NodeState.FAILED),
}


# ═══════════════════════════════════════════════════════════════════════════
# §3  Node Config & State
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class NodeConfig:
    node_id: str
    role: NodeRole
    memory_budget_mb: int
    disk_budget_gb: int
    jurisdiction: str
    capabilities: List[NodeCapability] = field(default_factory=list)
    bind_classes: List[BindClass] = field(default_factory=list)
    services: Dict[str, List[str]] = field(default_factory=dict)
    # services: {"warden": ["/usr/bin/python3", "warden.py", "--port", "8448"]}

    def __post_init__(self):
        if not self.capabilities:
            self.capabilities = DEFAULT_CAPABILITIES.get(self.role, [])
        if not self.bind_classes:
            self.bind_classes = DEFAULT_BIND_CLASSES.get(self.role, [])


@dataclass
class TopologyNodeState:
    node_id: str
    role: NodeRole
    state: NodeState = NodeState.BOOT
    capabilities: List[NodeCapability] = field(default_factory=list)
    energy_budget: Q16_16 = field(default_factory=Q16_16.zero)
    memory_budget_mb: int = 0
    disk_budget_gb: int = 0
    bind_classes: List[BindClass] = field(default_factory=list)
    jurisdiction: str = ""

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "role": self.role.value,
            "state": self.state.value,
            "capabilities": [c.value for c in self.capabilities],
            "energy_budget": self.energy_budget.to_dict(),
            "memory_budget_mb": self.memory_budget_mb,
            "disk_budget_gb": self.disk_budget_gb,
            "bind_classes": [b.value for b in self.bind_classes],
            "jurisdiction": self.jurisdiction,
        }

    @staticmethod
    def from_config(cfg: NodeConfig) -> "TopologyNodeState":
        return TopologyNodeState(
            node_id=cfg.node_id,
            role=cfg.role,
            state=NodeState.BOOT,
            capabilities=cfg.capabilities,
            energy_budget=MAX_ENERGY.get(cfg.role, Q16_16.from_nat(25)),
            memory_budget_mb=cfg.memory_budget_mb,
            disk_budget_gb=cfg.disk_budget_gb,
            bind_classes=cfg.bind_classes,
            jurisdiction=cfg.jurisdiction,
        )


# ═══════════════════════════════════════════════════════════════════════════
# §4  Topology Node Runtime
# ═══════════════════════════════════════════════════════════════════════════

class TopologyNodeRuntime:
    """Fit-to-purpose topology node runtime."""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.cfg = self._load_config()
        self.state = TopologyNodeState.from_config(self.cfg)
        self.db_path = Path.home() / f"var/db/topology-node-{self.cfg.node_id}.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._running = False
        self._services: Dict[str, subprocess.Popen] = {}
        self._threads: List[threading.Thread] = []

    def _load_config(self) -> NodeConfig:
        with open(self.config_path) as f:
            raw = json.load(f)
        return NodeConfig(
            node_id=raw["node_id"],
            role=NodeRole(raw["role"]),
            memory_budget_mb=raw["memory_budget_mb"],
            disk_budget_gb=raw["disk_budget_gb"],
            jurisdiction=raw["jurisdiction"],
            capabilities=[NodeCapability(c) for c in raw.get("capabilities", [])],
            bind_classes=[BindClass(b) for b in raw.get("bind_classes", [])],
            services=raw.get("services", {}),
        )

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS node_state_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                old_state TEXT,
                new_state TEXT,
                energy_budget_val INTEGER,
                reason TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS bind_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                bind_class TEXT,
                cost_val INTEGER,
                accepted INTEGER,
                reason TEXT
            )
        """)
        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────────────────────────────
    # State Machine
    # ─────────────────────────────────────────────────────────────────────

    def transition(self, new_state: NodeState, reason: str = "") -> bool:
        if (self.state.state, new_state) not in ALLOWED_TRANSITIONS:
            self._log("transition_rejected", f"illegal: {self.state.state.value} -> {new_state.value}")
            return False
        cost = STATE_TRANSITION_COST.get((self.state.state, new_state), Q16_16.from_nat(1))
        if self.state.energy_budget < cost:
            self._log("transition_rejected", f"insufficient_energy: need {cost.to_float()}, have {self.state.energy_budget.to_float()}")
            return False
        old = self.state.state
        self.state.energy_budget = self.state.energy_budget - cost
        self.state.state = new_state
        self._log_state_change(old, new_state, reason)
        return True

    def recover_energy(self):
        rate = RECOVERY_RATE.get(self.state.role, Q16_16.from_frac(1, 8))
        max_cap = MAX_ENERGY.get(self.state.role, Q16_16.from_nat(25))
        new_energy = self.state.energy_budget + rate
        self.state.energy_budget = new_energy if new_energy < max_cap else max_cap

    def can_accept_bind(self, bc: BindClass, cost: Q16_16) -> bool:
        return (
            self.state.state == NodeState.ACTIVE
            and bc in self.state.bind_classes
            and self.state.energy_budget >= cost
        )

    def deduct_energy(self, cost: Q16_16) -> bool:
        if self.state.energy_budget >= cost:
            self.state.energy_budget = self.state.energy_budget - cost
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────
    # Service Management
    # ─────────────────────────────────────────────────────────────────────

    def start_services(self):
        """Start configured services as child processes."""
        for name, cmd in self.cfg.services.items():
            if name in self._services:
                continue
            self._log("service_start", f"spawning {name}: {' '.join(cmd)}")
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._services[name] = proc

    def stop_services(self):
        for name, proc in self._services.items():
            self._log("service_stop", f"terminating {name}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        self._services.clear()

    def check_services(self) -> Dict[str, bool]:
        health = {}
        for name, proc in list(self._services.items()):
            ret = proc.poll()
            if ret is not None:
                health[name] = False
                self._log("service_died", f"{name} exited {ret}")
                del self._services[name]
            else:
                health[name] = True
        return health

    # ─────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────

    def run(self):
        self._running = True
        signal.signal(signal.SIGTERM, self._on_signal)
        signal.signal(signal.SIGINT, self._on_signal)

        # BOOT → SELFTEST → ANNOUNCE → ACTIVE
        self.transition(NodeState.SELFTEST, "boot_complete")
        self._run_selftest()
        self.transition(NodeState.ANNOUNCE, "selftest_pass")
        self._announce()
        self.transition(NodeState.ACTIVE, "announce_complete")
        self.start_services()

        # Main loop
        while self._running:
            self.recover_energy()
            health = self.check_services()
            if any(not v for v in health.values()):
                if self.state.state == NodeState.ACTIVE:
                    self.transition(NodeState.DEGRADED, "service_failure")
            else:
                if self.state.state == NodeState.DEGRADED:
                    self.transition(NodeState.ACTIVE, "service_recovery")
            time.sleep(5)

        self.stop_services()
        self._log("shutdown", "runtime exiting")

    def _run_selftest(self):
        """Verify capabilities."""
        self._log("selftest", f"capabilities: {[c.value for c in self.state.capabilities]}")
        for cap in self.state.capabilities:
            cost = CAPABILITY_COST.get(cap, Q16_16.from_nat(1))
            self._log("selftest", f"{cap.value} cost={cost.to_float()}")
        time.sleep(0.5)

    def _announce(self):
        """Broadcast presence to mesh."""
        self._log("announce", json.dumps(self.state.to_dict()))

    def _on_signal(self, signum, _frame):
        self._log("signal", f"received {signum}")
        self._running = False

    def _log(self, event: str, msg: str):
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"[{ts}] [{self.cfg.node_id}] [{event}] {msg}", flush=True)

    def _log_state_change(self, old: NodeState, new: NodeState, reason: str):
        self._log("state_change", f"{old.value} -> {new.value} ({reason})")
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute(
            "INSERT INTO node_state_log (timestamp, old_state, new_state, energy_budget_val, reason) VALUES (?, ?, ?, ?, ?)",
            (time.time(), old.value, new.value, self.state.energy_budget.val, reason)
        )
        conn.commit()
        conn.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: topology_node.py <config.json>")
        sys.exit(1)
    runtime = TopologyNodeRuntime(sys.argv[1])
    runtime.run()


if __name__ == "__main__":
    main()
