#!/usr/bin/env python3
"""
connectome_lut_shim.py — Python shim for parallel biophysical LUT evaluation.

Loads OpenWorm C. elegans connectome data from Parquet, quantizes each dataset
into the 18-bit address space defined in CooperativeLUT.lean (6D × 8 bins = 262,144
entries), precomputes the biophysical constraint surface, and performs parallel
lawful-state lookups for mutation proposals.

Branch prediction is treated as a SIMD interface: each misprediction is a coarse-
grain stochastic computation that shrinks possibility space.

Now supports 8-way and 16-way speculative bundles, plus BTB pattern detection
with streak-based short-circuiting.

Per AGENTS.md §6.1: This is a shim. All logic lives in Lean.
This file only: JSON serialization, Parquet I/O, LUT precomputation,
parallel lookup, quantum walk simulation, Verilog generation, and result wrapping.
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

# ═══════════════════════════════════════════════════════════════════════════
# §0  Q16_16 utilities (mirror Lean FixedPoint.lean)
# ═══════════════════════════════════════════════════════════════════════════

Q16_ONE = 0x00010000


def q16_to_float(q: int) -> float:
    """Convert Q16.16 UInt32 to float."""
    if q >= 0x80000000:
        return (q - 0x100000000) / 65536.0
    return q / 65536.0


def q16_mul(a: int, b: int) -> int:
    return ((a * b) >> 16) & 0xFFFFFFFF


def q16_div(a: int, b: int) -> int:
    if b == 0:
        return 0xFFFFFFFF
    return ((a << 16) // b) & 0xFFFFFFFF


def q16_sub(a: int, b: int) -> int:
    return ((a - b) & 0xFFFFFFFF)


def q16_le(a: int, b: int) -> bool:
    a_s = a if a < 0x80000000 else a - 0x100000000
    b_s = b if b < 0x80000000 else b - 0x100000000
    return a_s <= b_s


def q16_ge(a: int, b: int) -> bool:
    a_s = a if a < 0x80000000 else a - 0x100000000
    b_s = b if b < 0x80000000 else b - 0x100000000
    return a_s >= b_s


def q16_lt(a: int, b: int) -> bool:
    a_s = a if a < 0x80000000 else a - 0x100000000
    b_s = b if b < 0x80000000 else b - 0x100000000
    return a_s < b_s


# ═══════════════════════════════════════════════════════════════════════════
# §1  Biophysical constants (mirror CooperativeLUT.lean)
# ═══════════════════════════════════════════════════════════════════════════

DRAKE_CONSTANT = 0x000000C5
DRIFT_BARRIER_CONSTANT = 0x00000042
U_BASE = 0x00000041
NE_BASE = 0x00008000
SIGMA_BASE = 0x00004000
CONNECTANCE_BASE = 0x00002000
MODULARITY_BASE = 0x00002000

ADDR_SPACE = 262144
STREAK_THRESHOLD = 4


# ═══════════════════════════════════════════════════════════════════════════
# §2  Quantized genome encoding (6D × 8 bins = 18 bits)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class QuantizedGenome:
    g_bin: int
    ne_bin: int
    u_bin: int
    sigma_bin: int
    connectance_bin: int
    modularity_bin: int

    def to_address(self) -> int:
        return (
            self.g_bin * 32768 +
            self.ne_bin * 4096 +
            self.u_bin * 512 +
            self.sigma_bin * 64 +
            self.connectance_bin * 8 +
            self.modularity_bin
        )

    @staticmethod
    def from_address(addr: int) -> "QuantizedGenome":
        return QuantizedGenome(
            g_bin=addr // 32768,
            ne_bin=(addr // 4096) % 8,
            u_bin=(addr // 512) % 8,
            sigma_bin=(addr // 64) % 8,
            connectance_bin=(addr // 8) % 8,
            modularity_bin=addr % 8,
        )


@dataclass(frozen=True)
class ConstraintEntry:
    lawful: bool
    cost: int
    drake_ok: bool
    drift_ok: bool
    error_ok: bool


def compute_constraint_entry(q: QuantizedGenome) -> ConstraintEntry:
    """Mirror of CooperativeLUT.computeConstraintEntry.
    Connectance tightens Drake budget; modularity relaxes drift barrier."""
    u_q = U_BASE * (q.u_bin + 1)
    ne_q = NE_BASE * (q.ne_bin + 1)
    sigma_q = Q16_ONE + SIGMA_BASE * (q.sigma_bin + 1)
    connectance_factor = CONNECTANCE_BASE * (q.connectance_bin + 1)
    modularity_factor = MODULARITY_BASE * (q.modularity_bin + 1)

    adjusted_drake = q16_div(DRAKE_CONSTANT, connectance_factor)
    drake_ok = q16_le(u_q, adjusted_drake)

    adjusted_drift = q16_div(DRIFT_BARRIER_CONSTANT, modularity_factor)
    un_product = q16_mul(u_q, ne_q)
    drift_ok = q16_ge(un_product, adjusted_drift)

    ln_sigma = q16_sub(sigma_q, Q16_ONE)
    error_ok = q16_lt(u_q, ln_sigma)

    cost = 0
    if not drake_ok:
        cost += q16_sub(u_q, adjusted_drake) & 0xFFFFFFFF
    if not drift_ok:
        cost += q16_sub(adjusted_drift, un_product) & 0xFFFFFFFF
    if not error_ok:
        cost += 0x00FF0000

    return ConstraintEntry(
        lawful=drake_ok and drift_ok and error_ok,
        cost=cost,
        drake_ok=drake_ok,
        drift_ok=drift_ok,
        error_ok=error_ok,
    )


# ═══════════════════════════════════════════════════════════════════════════
# §3  Precomputed biophysical LUT (262,144 entries)
# ═══════════════════════════════════════════════════════════════════════════

class BiophysicalLUT:
    """Precomputed 262,144-entry constraint surface.
    In hardware, this is a BRAM block. In Python, a list."""

    def __init__(self):
        print("[INFO] Precomputing biophysical LUT (262,144 entries)...")
        self.entries = [
            compute_constraint_entry(QuantizedGenome.from_address(addr))
            for addr in range(ADDR_SPACE)
        ]
        lawful_count = sum(1 for e in self.entries if e.lawful)
        print(f"[INFO] LUT ready: {lawful_count} lawful states ({100*lawful_count/ADDR_SPACE:.1f}%)")

    def lookup(self, addr: int) -> ConstraintEntry:
        if not (0 <= addr < ADDR_SPACE):
            return ConstraintEntry(lawful=False, cost=0xFFFFFFFF,
                                   drake_ok=False, drift_ok=False, error_ok=False)
        return self.entries[addr]


# Global singleton (precomputed once)
BIOPHYSICAL_LUT = BiophysicalLUT()


# ═══════════════════════════════════════════════════════════════════════════
# §4  Connectome state quantization from OpenWorm Parquet
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ConnectomeState:
    dataset_name: str
    edge_count: int
    cell_count: int
    quantized: QuantizedGenome

    def to_address(self) -> int:
        return self.quantized.to_address()

    def lookup(self) -> ConstraintEntry:
        return BIOPHYSICAL_LUT.lookup(self.to_address())


def quantize_edge_count(n_edges: int) -> int:
    return max(0, min(7, (n_edges // 1000) - 1))


def quantize_ne(ne: float) -> int:
    return max(0, min(7, int(ne / 0.5) - 1))


def quantize_u(u: float) -> int:
    return max(0, min(7, int(u / 0.001) - 1))


def quantize_sigma(sigma: float) -> int:
    return max(0, min(7, int((sigma - 1.0) / 0.25) - 1))


def quantize_connectance(n_edges: int, n_cells: int) -> int:
    """Edge density: E / (N*(N-1)) for directed graphs, binned 0-7."""
    if n_cells <= 1:
        return 0
    max_edges = n_cells * (n_cells - 1)
    density = n_edges / max_edges
    return max(0, min(7, int(density * 8)))


def quantize_modularity(_n_edges: int, _n_cells: int) -> int:
    """Placeholder: modularity would require community detection.
    For now, default to middle bin (3)."""
    return 3


def load_openworm_dataset(parquet_dir: Path, dataset_name: str) -> Optional[ConnectomeState]:
    conn_file = parquet_dir / f"{dataset_name}_connections.parquet"
    if not conn_file.exists():
        return None

    df = pd.read_parquet(conn_file)
    n_edges = len(df)

    ne_default = 2.5
    u_default = 0.003
    sigma_default = 1.5

    cells_file = parquet_dir / f"{dataset_name}_cells.parquet"
    n_cells = 0
    if cells_file.exists():
        cells_df = pd.read_parquet(cells_file)
        n_cells = len(cells_df)

    q = QuantizedGenome(
        g_bin=quantize_edge_count(n_edges),
        ne_bin=quantize_ne(ne_default),
        u_bin=quantize_u(u_default),
        sigma_bin=quantize_sigma(sigma_default),
        connectance_bin=quantize_connectance(n_edges, n_cells),
        modularity_bin=quantize_modularity(n_edges, n_cells),
    )

    return ConnectomeState(
        dataset_name=dataset_name,
        edge_count=n_edges,
        cell_count=n_cells,
        quantized=q,
    )


def load_all_openworm_states(parquet_dir: Path) -> List[ConnectomeState]:
    conn_files = sorted(parquet_dir.glob("*_connections.parquet"))
    states = []
    for conn_file in conn_files:
        name = conn_file.stem.replace("_connections", "")
        state = load_openworm_dataset(parquet_dir, name)
        if state:
            states.append(state)
    return states


# ═══════════════════════════════════════════════════════════════════════════
# §5  Quantum Walk: Stochastic Traversal via Speculative Evaluation
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BTBEntry:
    source: int
    target: int
    confidence: int  # 0-3
    streak: int = 0  # consecutive correct predictions


class BranchTargetBuffer:
    """Simple BTB with up to 16 entries and streak tracking."""

    def __init__(self):
        self.entries: Dict[int, BTBEntry] = {}

    def lookup(self, addr: int) -> Optional[BTBEntry]:
        return self.entries.get(addr)

    def update_hit(self, addr: int):
        if addr in self.entries:
            e = self.entries[addr]
            e.confidence = min(3, e.confidence + 1)
            e.streak = e.streak + 1

    def update_miss(self, source: int, target: int):
        if source not in self.entries:
            if len(self.entries) >= 16:
                # Evict lowest-confidence entry
                min_addr = min(self.entries, key=lambda k: self.entries[k].confidence)
                del self.entries[min_addr]
            self.entries[source] = BTBEntry(source=source, target=target, confidence=1, streak=0)

    def is_stable(self, addr: int) -> bool:
        e = self.entries.get(addr)
        return e is not None and e.streak >= STREAK_THRESHOLD


@dataclass
class SpeculativeBundle:
    primary: int
    alt1: int
    alt2: int
    alt3: int
    mask1: bool = True
    mask2: bool = True
    mask3: bool = True


@dataclass
class SpeculativeBundle8:
    primary: int
    alt1: int
    alt2: int
    alt3: int
    alt4: int
    alt5: int
    alt6: int
    alt7: int
    mask1: bool = True
    mask2: bool = True
    mask3: bool = True
    mask4: bool = True
    mask5: bool = True
    mask6: bool = True
    mask7: bool = True


@dataclass
class SpeculativeBundle16:
    primary: int
    alt1: int
    alt2: int
    alt3: int
    alt4: int
    alt5: int
    alt6: int
    alt7: int
    alt8: int
    alt9: int
    alt10: int
    alt11: int
    alt12: int
    alt13: int
    alt14: int
    alt15: int
    mask1: bool = True
    mask2: bool = True
    mask3: bool = True
    mask4: bool = True
    mask5: bool = True
    mask6: bool = True
    mask7: bool = True
    mask8: bool = True
    mask9: bool = True
    mask10: bool = True
    mask11: bool = True
    mask12: bool = True
    mask13: bool = True
    mask14: bool = True
    mask15: bool = True


def evaluate_bundle(bundle: SpeculativeBundle) -> List[Tuple[int, ConstraintEntry]]:
    candidates = [
        (True, bundle.primary),
        (bundle.mask1, bundle.alt1),
        (bundle.mask2, bundle.alt2),
        (bundle.mask3, bundle.alt3),
    ]
    results = []
    for active, addr in candidates:
        if active:
            entry = BIOPHYSICAL_LUT.lookup(addr)
            if entry.lawful:
                results.append((addr, entry))
    return results


def evaluate_bundle8(bundle: SpeculativeBundle8) -> List[Tuple[int, ConstraintEntry]]:
    candidates = [
        (True, bundle.primary),
        (bundle.mask1, bundle.alt1),
        (bundle.mask2, bundle.alt2),
        (bundle.mask3, bundle.alt3),
        (bundle.mask4, bundle.alt4),
        (bundle.mask5, bundle.alt5),
        (bundle.mask6, bundle.alt6),
        (bundle.mask7, bundle.alt7),
    ]
    results = []
    for active, addr in candidates:
        if active:
            entry = BIOPHYSICAL_LUT.lookup(addr)
            if entry.lawful:
                results.append((addr, entry))
    return results


def evaluate_bundle16(bundle: SpeculativeBundle16) -> List[Tuple[int, ConstraintEntry]]:
    candidates = [
        (True, bundle.primary),
        (bundle.mask1, bundle.alt1),
        (bundle.mask2, bundle.alt2),
        (bundle.mask3, bundle.alt3),
        (bundle.mask4, bundle.alt4),
        (bundle.mask5, bundle.alt5),
        (bundle.mask6, bundle.alt6),
        (bundle.mask7, bundle.alt7),
        (bundle.mask8, bundle.alt8),
        (bundle.mask9, bundle.alt9),
        (bundle.mask10, bundle.alt10),
        (bundle.mask11, bundle.alt11),
        (bundle.mask12, bundle.alt12),
        (bundle.mask13, bundle.alt13),
        (bundle.mask14, bundle.alt14),
        (bundle.mask15, bundle.alt15),
    ]
    results = []
    for active, addr in candidates:
        if active:
            entry = BIOPHYSICAL_LUT.lookup(addr)
            if entry.lawful:
                results.append((addr, entry))
    return results


def quantum_walk_step(current: int, btb: BranchTargetBuffer) -> Tuple[int, BranchTargetBuffer, ConstraintEntry]:
    """One step of the quantum walk (4-way bundle)."""
    entry = btb.lookup(current)
    if entry:
        prediction = entry.target
    else:
        prediction = (current + 1) % ADDR_SPACE

    bundle = SpeculativeBundle(
        primary=prediction,
        alt1=(current + 1) % ADDR_SPACE,
        alt2=(current + 8) % ADDR_SPACE,
        alt3=(current + 64) % ADDR_SPACE,
    )

    results = evaluate_bundle(bundle)
    if not results:
        btb.update_miss(current, current)
        return current, btb, BIOPHYSICAL_LUT.lookup(current)

    best_addr, best_entry = min(results, key=lambda x: x[1].cost)
    if best_addr == prediction:
        btb.update_hit(current)
    else:
        btb.update_miss(current, best_addr)

    return best_addr, btb, best_entry


def quantum_walk_step8(current: int, btb: BranchTargetBuffer) -> Tuple[int, BranchTargetBuffer, ConstraintEntry]:
    """One step of the quantum walk (8-way bundle)."""
    entry = btb.lookup(current)
    if entry:
        prediction = entry.target
    else:
        prediction = (current + 1) % ADDR_SPACE

    bundle = SpeculativeBundle8(
        primary=prediction,
        alt1=(current + 1) % ADDR_SPACE,    # modularity
        alt2=(current + 8) % ADDR_SPACE,    # connectance
        alt3=(current + 64) % ADDR_SPACE,   # sigma
        alt4=(current + 512) % ADDR_SPACE,  # u
        alt5=(current + 4096) % ADDR_SPACE, # Ne
        alt6=(current + 32768) % ADDR_SPACE, # g
        alt7=(current + 2) % ADDR_SPACE,    # fine modularity
    )

    results = evaluate_bundle8(bundle)
    if not results:
        btb.update_miss(current, current)
        return current, btb, BIOPHYSICAL_LUT.lookup(current)

    best_addr, best_entry = min(results, key=lambda x: x[1].cost)
    if best_addr == prediction:
        btb.update_hit(current)
    else:
        btb.update_miss(current, best_addr)

    return best_addr, btb, best_entry


def quantum_walk_step16(current: int, btb: BranchTargetBuffer) -> Tuple[int, BranchTargetBuffer, ConstraintEntry]:
    """One step of the quantum walk (16-way bundle)."""
    entry = btb.lookup(current)
    if entry:
        prediction = entry.target
    else:
        prediction = (current + 1) % ADDR_SPACE

    bundle = SpeculativeBundle16(
        primary=prediction,
        alt1=(current + 1) % ADDR_SPACE,
        alt2=(current + 2) % ADDR_SPACE,
        alt3=(current + 4) % ADDR_SPACE,
        alt4=(current + 8) % ADDR_SPACE,
        alt5=(current + 16) % ADDR_SPACE,
        alt6=(current + 32) % ADDR_SPACE,
        alt7=(current + 64) % ADDR_SPACE,
        alt8=(current + 128) % ADDR_SPACE,
        alt9=(current + 256) % ADDR_SPACE,
        alt10=(current + 512) % ADDR_SPACE,
        alt11=(current + 1024) % ADDR_SPACE,
        alt12=(current + 2048) % ADDR_SPACE,
        alt13=(current + 4096) % ADDR_SPACE,
        alt14=(current + 8192) % ADDR_SPACE,
        alt15=(current + 16384) % ADDR_SPACE,
    )

    results = evaluate_bundle16(bundle)
    if not results:
        btb.update_miss(current, current)
        return current, btb, BIOPHYSICAL_LUT.lookup(current)

    best_addr, best_entry = min(results, key=lambda x: x[1].cost)
    if best_addr == prediction:
        btb.update_hit(current)
    else:
        btb.update_miss(current, best_addr)

    return best_addr, btb, best_entry


def quantum_walk_step_pattern(current: int, btb: BranchTargetBuffer) -> Tuple[int, BranchTargetBuffer, ConstraintEntry]:
    """Pattern-aware quantum walk step with BTB short-circuit.
    If the BTB entry has a stable streak (≥ threshold), skip bundle
    evaluation and follow the BTB target directly."""
    entry = btb.lookup(current)
    if entry and btb.is_stable(current):
        # Stable pattern: short-circuit
        btb.update_hit(current)
        return entry.target, btb, BIOPHYSICAL_LUT.lookup(entry.target)

    # Unstable or no BTB entry: fall back to 8-way speculative evaluation
    return quantum_walk_step8(current, btb)


def run_quantum_walk(seed_addr: int, steps: int = 100, mode: str = "pattern") -> List[Tuple[int, ConstraintEntry]]:
    """Run a quantum walk for N steps from a seed address.
    mode: "4way", "8way", "16way", or "pattern" (default)."""
    btb = BranchTargetBuffer()
    trajectory = []
    current = seed_addr
    short_circuits = 0

    step_fn = {
        "4way": quantum_walk_step,
        "8way": quantum_walk_step8,
        "16way": quantum_walk_step16,
        "pattern": quantum_walk_step_pattern,
    }.get(mode, quantum_walk_step_pattern)

    for _ in range(steps):
        prev = current
        current, btb, entry = step_fn(current, btb)
        if mode == "pattern" and prev != current and btb.is_stable(prev):
            short_circuits += 1
        trajectory.append((current, entry))

    return trajectory, short_circuits


# ═══════════════════════════════════════════════════════════════════════════
# §6  JSON serialization for swarm consumption
# ═══════════════════════════════════════════════════════════════════════════

def state_to_json(state: ConnectomeState) -> dict:
    entry = state.lookup()
    return {
        "dataset": state.dataset_name,
        "edge_count": state.edge_count,
        "cell_count": state.cell_count,
        "address": state.to_address(),
        "quantized": {
            "g_bin": state.quantized.g_bin,
            "ne_bin": state.quantized.ne_bin,
            "u_bin": state.quantized.u_bin,
            "sigma_bin": state.quantized.sigma_bin,
            "connectance_bin": state.quantized.connectance_bin,
            "modularity_bin": state.quantized.modularity_bin,
        },
        "lawful": entry.lawful,
        "cost": entry.cost,
        "drake_ok": entry.drake_ok,
        "drift_ok": entry.drift_ok,
        "error_ok": entry.error_ok,
    }


def trajectory_to_json(trajectory: List[Tuple[int, ConstraintEntry]]) -> List[dict]:
    return [
        {
            "step": i,
            "address": addr,
            "lawful": entry.lawful,
            "cost": entry.cost,
            "drake_ok": entry.drake_ok,
            "drift_ok": entry.drift_ok,
            "error_ok": entry.error_ok,
        }
        for i, (addr, entry) in enumerate(trajectory)
    ]


# ═══════════════════════════════════════════════════════════════════════════
# §7  Verilog generation (hardware extraction)
# ═══════════════════════════════════════════════════════════════════════════

def generate_verilog_lut(output_path: Path):
    """Generate Verilog modules for the biophysical LUT and speculative evaluators.
    Includes 4-way, 8-way, and 16-way speculative evaluator modules."""
    lines = []
    lines.append("// Auto-generated from connectome_lut_shim.py")
    lines.append("// Biophysical Constraint LUT: 262,144 entries, 18-bit address")
    lines.append("// Each entry: {lawful(1), cost(32), drake_ok(1), drift_ok(1), error_ok(1)}")
    lines.append("")
    lines.append("module BiophysicalLUT (")
    lines.append("  input  [17:0] addr,")
    lines.append("  output        lawful,")
    lines.append("  output [31:0] cost,")
    lines.append("  output        drake_ok,")
    lines.append("  output        drift_ok,")
    lines.append("  output        error_ok")
    lines.append(");")
    lines.append("")
    lines.append("  // Entry encoding: {cost[31:0], lawful, drake_ok, drift_ok, error_ok}")
    lines.append("  // For 262K entries, use external BRAM initialization.")
    lines.append("  // This module declares the interface; initialization is via $readmemh.")
    lines.append("")
    lines.append("  reg [35:0] lut_mem [0:262143]; // 36-bit word: 32b cost + 4b flags")
    lines.append("")
    lines.append("  initial begin")
    lines.append('    $display("Loading biophysical LUT from biophysical_lut.hex...");')
    lines.append('    $readmemh("biophysical_lut.hex", lut_mem);')
    lines.append("  end")
    lines.append("")
    lines.append("  wire [35:0] entry = lut_mem[addr];")
    lines.append("  assign cost     = entry[35:4];")
    lines.append("  assign lawful   = entry[3];")
    lines.append("  assign drake_ok = entry[2];")
    lines.append("  assign drift_ok = entry[1];")
    lines.append("  assign error_ok = entry[0];")
    lines.append("")
    lines.append("endmodule")
    lines.append("")

    # 4-way evaluator
    lines.append("// Speculative evaluation unit: 4-way bundle")
    lines.append("module SpeculativeEvaluator (")
    lines.append("  input  [17:0] primary,")
    lines.append("  input  [17:0] alt1,")
    lines.append("  input  [17:0] alt2,")
    lines.append("  input  [17:0] alt3,")
    lines.append("  input         mask1,")
    lines.append("  input         mask2,")
    lines.append("  input         mask3,")
    lines.append("  output [17:0] best_addr,")
    lines.append("  output [31:0] best_cost,")
    lines.append("  output        best_lawful")
    lines.append(");")
    lines.append("")
    lines.append("  wire [31:0] cost_p, cost_1, cost_2, cost_3;")
    lines.append("  wire        law_p, law_1, law_2, law_3;")
    lines.append("")
    lines.append("  BiophysicalLUT lut_p (.addr(primary), .cost(cost_p), .lawful(law_p), .drake_ok(), .drift_ok(), .error_ok());")
    lines.append("  BiophysicalLUT lut_1 (.addr(alt1),   .cost(cost_1), .lawful(law_1), .drake_ok(), .drift_ok(), .error_ok());")
    lines.append("  BiophysicalLUT lut_2 (.addr(alt2),   .cost(cost_2), .lawful(law_2), .drake_ok(), .drift_ok(), .error_ok());")
    lines.append("  BiophysicalLUT lut_3 (.addr(alt3),   .cost(cost_3), .lawful(law_3), .drake_ok(), .drift_ok(), .error_ok());")
    lines.append("")
    lines.append("  // Priority encoder: select lowest-cost lawful address")
    lines.append("  assign best_addr   = law_p ? primary : (law_1 & mask1) ? alt1 : (law_2 & mask2) ? alt2 : (law_3 & mask3) ? alt3 : primary;")
    lines.append("  assign best_cost   = law_p ? cost_p : (law_1 & mask1) ? cost_1 : (law_2 & mask2) ? cost_2 : (law_3 & mask3) ? cost_3 : 32'hFFFFFFFF;")
    lines.append("  assign best_lawful = law_p | (law_1 & mask1) | (law_2 & mask2) | (law_3 & mask3);")
    lines.append("")
    lines.append("endmodule")
    lines.append("")

    # 8-way evaluator
    lines.append("// Speculative evaluation unit: 8-way bundle")
    lines.append("module SpeculativeEvaluator8 (")
    for i in range(8):
        lines.append(f"  input  [17:0] {'primary' if i == 0 else f'alt{i}'},")
    for i in range(1, 8):
        lines.append(f"  input         mask{i},")
    lines.append("  output [17:0] best_addr,")
    lines.append("  output [31:0] best_cost,")
    lines.append("  output        best_lawful")
    lines.append(");")
    lines.append("")
    lines.append("  wire [31:0] cost_p, cost_1, cost_2, cost_3, cost_4, cost_5, cost_6, cost_7;")
    lines.append("  wire        law_p, law_1, law_2, law_3, law_4, law_5, law_6, law_7;")
    lines.append("")
    for i, name in enumerate(["p", "1", "2", "3", "4", "5", "6", "7"]):
        addr = "primary" if i == 0 else f"alt{i}"
        lines.append(f"  BiophysicalLUT lut_{name} (.addr({addr}), .cost(cost_{name}), .lawful(law_{name}), .drake_ok(), .drift_ok(), .error_ok());")
    lines.append("")
    lines.append("  // Priority encoder: select lowest-cost lawful address (primary highest priority)")
    sel = "law_p ? primary : "
    for i in range(1, 8):
        sel += f"(law_{i} & mask{i}) ? alt{i} : "
    sel += "primary;"
    lines.append(f"  assign best_addr   = {sel}")
    sel_cost = "law_p ? cost_p : "
    for i in range(1, 8):
        sel_cost += f"(law_{i} & mask{i}) ? cost_{i} : "
    sel_cost += "32'hFFFFFFFF;"
    lines.append(f"  assign best_cost   = {sel_cost}")
    sel_law = "law_p"
    for i in range(1, 8):
        sel_law += f" | (law_{i} & mask{i})"
    sel_law += ";"
    lines.append(f"  assign best_lawful = {sel_law}")
    lines.append("")
    lines.append("endmodule")
    lines.append("")

    # 16-way evaluator
    lines.append("// Speculative evaluation unit: 16-way bundle")
    lines.append("module SpeculativeEvaluator16 (")
    for i in range(16):
        lines.append(f"  input  [17:0] {'primary' if i == 0 else f'alt{i}'},")
    for i in range(1, 16):
        lines.append(f"  input         mask{i},")
    lines.append("  output [17:0] best_addr,")
    lines.append("  output [31:0] best_cost,")
    lines.append("  output        best_lawful")
    lines.append(");")
    lines.append("")
    lines.append("  wire [31:0] cost_p, " + ", ".join([f"cost_{i}" for i in range(1, 16)]) + ";")
    lines.append("  wire        law_p, " + ", ".join([f"law_{i}" for i in range(1, 16)]) + ";")
    lines.append("")
    for i, name in enumerate(["p"] + [str(j) for j in range(1, 16)]):
        addr = "primary" if i == 0 else f"alt{i}"
        lines.append(f"  BiophysicalLUT lut_{name} (.addr({addr}), .cost(cost_{name}), .lawful(law_{name}), .drake_ok(), .drift_ok(), .error_ok());")
    lines.append("")
    lines.append("  // Priority encoder: select lowest-cost lawful address (primary highest priority)")
    sel = "law_p ? primary : "
    for i in range(1, 16):
        sel += f"(law_{i} & mask{i}) ? alt{i} : "
    sel += "primary;"
    lines.append(f"  assign best_addr   = {sel}")
    sel_cost = "law_p ? cost_p : "
    for i in range(1, 16):
        sel_cost += f"(law_{i} & mask{i}) ? cost_{i} : "
    sel_cost += "32'hFFFFFFFF;"
    lines.append(f"  assign best_cost   = {sel_cost}")
    sel_law = "law_p"
    for i in range(1, 16):
        sel_law += f" | (law_{i} & mask{i})"
    sel_law += ";"
    lines.append(f"  assign best_lawful = {sel_law}")
    lines.append("")
    lines.append("endmodule")
    lines.append("")

    # BTB pattern detector module
    lines.append("// BTB Pattern Detector with streak-based short-circuit")
    lines.append("module PatternDetector (")
    lines.append("  input         clk,")
    lines.append("  input         rst,")
    lines.append("  input  [17:0] current_addr,")
    lines.append("  input  [17:0] predicted_target,")
    lines.append("  input         hit,")
    lines.append("  output        stable,")
    lines.append("  output [17:0] stable_target")
    lines.append(");")
    lines.append("")
    lines.append("  // Simple direct-mapped BTB with streak counter (4 entries for demo)")
    lines.append("  reg [17:0] btb_source [0:3];")
    lines.append("  reg [17:0] btb_target [0:3];")
    lines.append("  reg [1:0]  btb_conf   [0:3];")
    lines.append("  reg [2:0]  btb_streak [0:3];")
    lines.append("  reg        btb_valid  [0:3];")
    lines.append("")
    lines.append("  wire [1:0] idx = current_addr[1:0]; // 2-bit index (demo: 4 entries)")
    lines.append("  wire match_found = btb_valid[idx] && (btb_source[idx] == current_addr);")
    lines.append("  wire is_stable = match_found && (btb_streak[idx] >= 3'd4);")
    lines.append("")
    lines.append("  assign stable = is_stable;")
    lines.append("  assign stable_target = btb_target[idx];")
    lines.append("")
    lines.append("  integer i;")
    lines.append("  always @(posedge clk or posedge rst) begin")
    lines.append("    if (rst) begin")
    lines.append("      for (i = 0; i < 4; i = i + 1) begin")
    lines.append("        btb_valid[i] <= 1'b0;")
    lines.append("        btb_streak[i] <= 3'd0;")
    lines.append("        btb_conf[i] <= 2'd0;")
    lines.append("      end")
    lines.append("    end else begin")
    lines.append("      if (hit && match_found) begin")
    lines.append("        // Increment confidence and streak on hit")
    lines.append("        btb_conf[idx] <= (btb_conf[idx] < 2'd3) ? btb_conf[idx] + 1 : 2'd3;")
    lines.append("        btb_streak[idx] <= btb_streak[idx] + 1;")
    lines.append("      end else if (!hit && match_found) begin")
    lines.append("        // Reset streak on miss")
    lines.append("        btb_streak[idx] <= 3'd0;")
    lines.append("      end else if (!match_found) begin")
    lines.append("        // Insert new entry")
    lines.append("        btb_valid[idx] <= 1'b1;")
    lines.append("        btb_source[idx] <= current_addr;")
    lines.append("        btb_target[idx] <= predicted_target;")
    lines.append("        btb_conf[idx] <= 2'd1;")
    lines.append("        btb_streak[idx] <= 3'd0;")
    lines.append("      end")
    lines.append("    end")
    lines.append("  end")
    lines.append("")
    lines.append("endmodule")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"[OK] Verilog module written to {output_path}")


def generate_lut_hex(output_path: Path):
    """Generate hex initialization file for the LUT BRAM.
    Format: 36-bit hex words (8 hex digits + 1 nibble for flags)."""
    lines = []
    for addr in range(ADDR_SPACE):
        entry = BIOPHYSICAL_LUT.lookup(addr)
        # Pack: cost[31:0] | lawful | drake_ok | drift_ok | error_ok
        flags = (int(entry.lawful) << 3) | (int(entry.drake_ok) << 2) | (int(entry.drift_ok) << 1) | int(entry.error_ok)
        word = (entry.cost << 4) | flags
        lines.append(f"{word:09X}")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"[OK] LUT hex file written to {output_path}")


def generate_yosys_script(output_dir: Path):
    """Generate Yosys synthesis script for iCE40 target.
    Synthesizes the 8-way speculative evaluator and reports resource usage."""
    script = """# Yosys synthesis script for CooperativeLUT iCE40 target
# Generated by connectome_lut_shim.py

# Read design
read_verilog biophysical_lut.v

# Generic synthesis (technology-independent optimization)
synth -top SpeculativeEvaluator8

# Technology mapping for iCE40
# Note: The full 262K LUT won't fit in iCE40 SPRAM (max ~128KB).
# For a real build, external SRAM or a larger FPGA (ECP5, Xilinx) is needed.
# This script targets a parameterized small-LUT version for iCE40UP5K.
synth_ice40 -top SpeculativeEvaluator8 -json speculative_evaluator8.json

# Resource report
stat

# Write BLIF for nextpnr-ice40
write_blif speculative_evaluator8.blif
"""
    script_path = output_dir / "synth_ice40.ys"
    with open(script_path, "w") as f:
        f.write(script)
    print(f"[OK] Yosys synthesis script written to {script_path}")
    return script_path


# ═══════════════════════════════════════════════════════════════════════════
# §8  CLI / main execution
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parquet_dir = Path("shared-data/data/connectomes/openworm_parquet")
    if not parquet_dir.exists():
        print(f"[ERROR] Parquet directory not found: {parquet_dir}", file=sys.stderr)
        sys.exit(1)

    print("[INFO] Loading OpenWorm connectome datasets...")
    states = load_all_openworm_states(parquet_dir)
    print(f"[INFO] Loaded {len(states)} datasets")

    # Seed states
    seed_json = [state_to_json(s) for s in states]
    print("\n=== SEED STATES (sample) ===")
    print(json.dumps(seed_json[:5], indent=2))

    trajectory = []
    short_circuits = 0
    mode_summary = {}

    # Quantum walks from first dataset
    if states:
        seed_state = states[0]
        seed_addr = seed_state.to_address()

        for mode in ["4way", "8way", "16way", "pattern"]:
            print(f"\n[INFO] Running quantum walk ({mode}) from {seed_state.dataset_name} (addr={seed_addr})...")
            traj, sc = run_quantum_walk(seed_addr, steps=50, mode=mode)
            lawful_steps = sum(1 for _, e in traj if e.lawful)
            mode_summary[mode] = {
                "lawful_steps": lawful_steps,
                "short_circuits": sc,
            }
            print(f"[INFO] {mode} complete: {lawful_steps}/50 lawful steps, {sc} short-circuits")

            if mode == "pattern":
                trajectory = traj
                short_circuits = sc

        print("\n=== QUANTUM WALK TRAJECTORY (pattern, first 10 steps) ===")
        print(json.dumps(trajectory_to_json(trajectory[:10]), indent=2))

    # Generate Verilog
    verilog_dir = Path("5-Applications/out/verilog")
    verilog_dir.mkdir(parents=True, exist_ok=True)
    generate_verilog_lut(verilog_dir / "biophysical_lut.v")
    generate_lut_hex(verilog_dir / "biophysical_lut.hex")
    generate_yosys_script(verilog_dir)

    # Run Yosys synthesis if available
    yosys_bin = Path("/usr/bin/yosys")
    if yosys_bin.exists():
        print("\n[INFO] Running Yosys synthesis for resource estimation...")
        import subprocess
        try:
            result = subprocess.run(
                [str(yosys_bin), "-s", "synth_ice40.ys"],
                cwd=verilog_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            # Extract resource stats from the 'stat' section
            # Yosys prints stats multiple times; we want the one with SB_LUT4 counts
            stats_blocks = []
            current_block = []
            in_block = False
            for line in result.stdout.splitlines():
                if "=== SpeculativeEvaluator8 ===" in line:
                    if in_block and current_block:
                        stats_blocks.append(current_block)
                    in_block = True
                    current_block = [line]
                elif in_block:
                    if line.startswith("=== ") and "SpeculativeEvaluator8" not in line:
                        in_block = False
                        stats_blocks.append(current_block)
                        current_block = []
                    else:
                        current_block.append(line)
            if current_block and in_block:
                stats_blocks.append(current_block)

            # Find the block that contains SB_LUT4
            best_block = []
            for block in stats_blocks:
                if any("SB_LUT4" in line for line in block):
                    best_block = block
                    break

            if best_block:
                print("\n=== YOSYS RESOURCE ESTIMATE (SpeculativeEvaluator8, iCE40) ===")
                for line in best_block[:25]:
                    print(line)
            else:
                print("\n=== YOSYS OUTPUT (tail) ===")
                for line in result.stdout.splitlines()[-40:]:
                    print(line)

            # Save full log
            with open(verilog_dir / "yosys.log", "w") as f:
                f.write(result.stdout)
                f.write(result.stderr)
            print(f"\n[OK] Yosys log saved to {verilog_dir / 'yosys.log'}")
        except Exception as e:
            print(f"[WARN] Yosys synthesis failed: {e}")
    else:
        print("[INFO] Yosys not found; skipping synthesis.")

    # Save full results
    out_file = Path("5-Applications/out/connectome_lut_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump({
            "seed_states": seed_json,
            "quantum_walk": trajectory_to_json(trajectory),
            "summary": {
                "total_datasets": len(states),
                "lut_entries": ADDR_SPACE,
                "lawful_lut_fraction": sum(1 for e in BIOPHYSICAL_LUT.entries if e.lawful) / ADDR_SPACE,
                "mode_comparison": mode_summary,
                "short_circuits": short_circuits,
            }
        }, f, indent=2)
    print(f"\n[OK] Full results saved to {out_file}")


if __name__ == "__main__":
    main()
