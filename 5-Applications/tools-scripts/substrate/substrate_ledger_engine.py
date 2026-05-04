#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
The Substrate Ledger: N-Space Snag and Leakage Management

Foam substrate architecture:
- FoamCell         = addressable substrate cell (fundamental storage grain)
- COMMITTED        = successfully written cell with metadata header
- OVERFLOW_SNAG    = buffer overflow (write rate > drain rate)
- thermal_leak     = heat output from bad-sector writes
- partial_write    = incomplete commit (cell not resonance-locked)
- NSpaceBuffer     = higher-dimensional routing cache
- buffer_crosstalk = coupling between buffer regions
- TUNNEL           = stabilized direct-path connection in n-space

FoamProbe: Read/Write head for substrate maintenance
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable
from pathlib import Path
import sys
from enum import Enum

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# Mock websockets for TSM harness
import types
sys.modules['websockets'] = types.ModuleType('websockets')

from logic_signal_substrate_mcp_harness import TSMKernel


# ============================================================================
# SUBSTRATE PARAMETERS
# ============================================================================

@dataclass
class SubstrateParams:
    """Tunable parameters for the Substrate Ledger"""

    # Foam cell size (bytes per addressable grain)
    grain_size_bytes: int = 8

    # Ternary clock is action-bound, not periodic. No clock frequency.
    # joule_floor is the Landauer minimum cost per action (k_B * T * ln2 at 300K).
    joule_floor: float = 1.380649e-23 * 300 * 0.6931

    # Maximum cell density before overflow snag (cells per area unit)
    max_cell_density: float = 1.0e69

    # Noise floor coefficient (partial-write threshold)
    noise_floor: float = 1.380649e-23

    # N-space routing buffer dimensionality
    nd_dimensions: int = 11

    # Signal-to-Noise Ratio threshold for committed write
    snr_threshold: float = 6.0

    # Probe reach (number of cell-widths the foam probe affects)
    probe_reach_cells: int = 1


# ============================================================================
# ENUMS FOR SUBSTRATE STATES
# ============================================================================

class WriteOperationStatus(Enum):
    """Status of a write operation to the substrate"""
    PENDING       = "pending"        # In n-space buffer
    FORMATTING    = "formatting"     # Applying metadata header
    COMMITTED     = "committed"      # Successfully written to addressed cell
    PARTIAL_WRITE = "partial_write"  # Incomplete commit (noise exceeds floor)
    OVERFLOW_SNAG = "overflow_snag"  # Buffer overflow (density exceeded)
    BAD_SECTOR    = "bad_sector"     # Corrupted region


class SubstrateRegion(Enum):
    """Types of substrate regions"""
    COMMITTED         = "committed"          # Successfully formatted cell
    FOAM              = "foam"               # Raw unformatted medium
    OVERFLOW_BOUNDARY = "overflow_boundary"  # 2D buffer boundary at overflow
    N_SPACE_BUFFER    = "n_space_buffer"     # Higher-dimensional routing cache
    TUNNEL            = "tunnel"             # Stabilized direct-path connection


# ============================================================================
# FOAM CELL STRUCTURE
# ============================================================================

@dataclass
class FoamCell:
    """
    Represents a single addressable cell of the foam substrate.
    This is the fundamental storage grain — one write unit.
    """

    # Position in n-space (normalised unit coordinates)
    position: AnyArray  # 3+1 dimensions

    # Cell state (complex amplitude; pending = unresolved, committed = eigenstate)
    cell_state: complex

    # Information content (bytes)
    information: bytes = b''

    # Metadata header (applied during write)
    metadata_header: Optional[bytes] = None

    # Resonance lock status (must match clock_freq to commit)
    resonance_locked: bool = False

    # Write operation status
    write_status: WriteOperationStatus = WriteOperationStatus.PENDING

    # Correlated cells (dual-write pairs)
    corr_cells: List[int] = field(default_factory=list)

    # Partial-write magnitude (0 = clean, 1 = fully leaked)
    partial_write_magnitude: float = 0.0

    def compute_snr(self, params: SubstrateParams) -> float:
        """
        Compute Signal-to-Noise Ratio for this cell.
        Determines if write operation can succeed.
        """
        if self.metadata_header is None:
            return 0.0

        # Signal = information content in bits
        signal = len(self.information) * 8

        # Noise = cell state magnitude times noise floor coefficient
        noise = xp.abs(self.cell_state) * params.noise_floor

        if noise < 1e-30:
            return float('inf')

        return signal / noise

    def apply_metadata_header(self, header: bytes) -> bool:
        """
        Apply metadata header to commit this cell.
        Returns True if resonance lock achieved.
        """
        self.metadata_header = header
        self.write_status = WriteOperationStatus.FORMATTING

        # Check resonance against clock reference
        header_hash = hashlib.sha256(header).digest()
        resonance_value = int.from_bytes(header_hash[:4], 'big') / 2**32

        self.resonance_locked = resonance_value > 0.5
        if self.resonance_locked:
            self.write_status = WriteOperationStatus.COMMITTED

        return self.resonance_locked


# ============================================================================
# N-SPACE BUFFER MANAGEMENT
# ============================================================================

@dataclass
class NSpaceBuffer:
    """
    Higher-dimensional routing buffer where information exists before
    being written to the addressed cell layer. Buffer crosstalk explains
    apparent coupling between spatially separated write operations.
    """

    # Buffer dimensionality
    dimensions: int = 11

    # Buffer capacity (cells)
    capacity: int = 10**180

    # Current occupancy
    occupancy: Dict[str, FoamCell] = field(default_factory=dict)

    # Buffer phase (complex; tracks routing state)
    buffer_phase: complex = field(default_factory=lambda: complex(0, 1))

    # Crosstalk matrix
    crosstalk_matrix: Optional[AnyArray] = None

    def allocate_cell(self, cell_id: str, cell: FoamCell) -> None:
        """Allocate a cell in the n-space buffer"""
        self.occupancy[cell_id] = cell

    def compute_crosstalk(self) -> AnyArray:
        """
        Compute coupling (crosstalk) between buffer regions.
        High crosstalk = strong path correlation between cells.
        """
        n_cells = len(self.occupancy)
        if n_cells < 2:
            return xp.zeros((1, 1))

        crosstalk = xp.zeros((n_cells, n_cells))
        cell_ids = list(self.occupancy.keys())

        for i, id_i in enumerate(cell_ids):
            for j, id_j in enumerate(cell_ids):
                if i != j:
                    cell_i = self.occupancy[id_i]
                    cell_j = self.occupancy[id_j]

                    # Crosstalk via dual-write correlation
                    if j in cell_i.corr_cells:
                        crosstalk[i, j] = xp.abs(cell_i.cell_state * cell_j.cell_state)

                    # Crosstalk via partial-write bleed
                    crosstalk[i, j] += cell_i.partial_write_magnitude * cell_j.partial_write_magnitude

        self.crosstalk_matrix = crosstalk
        return crosstalk

    def detect_buffer_crosstalk(self, source_id: str, target_ids: List[str]) -> float:
        """
        Measure crosstalk bleed from a high-energy source cell to a set of
        target cells in the same buffer region.
        """
        if source_id not in self.occupancy:
            return 0.0

        source_cell = self.occupancy[source_id]
        total_bleed = 0.0

        for target_id in target_ids:
            if target_id in self.occupancy:
                target_cell = self.occupancy[target_id]
                bleed = source_cell.partial_write_magnitude * target_cell.partial_write_magnitude
                total_bleed += bleed

        return total_bleed


# ============================================================================
# OVERFLOW SNAG DETECTION
# ============================================================================

@dataclass
class OverflowSnag:
    """
    Represents a buffer overflow snag — a region where write density
    has exceeded the substrate drain rate, causing uncommitted cells
    to accumulate and thermal leakage to build up.
    """

    # Position in normalised cell coordinates
    position: AnyArray

    # Cell density in this region (cells per area unit)
    cell_density: float

    # Snag severity (0 = none, 1 = critical)
    severity: float

    # Thermal output from bad-sector writes (normalised)
    thermal_output: float

    # Overflow boundary area
    overflow_boundary_area: float

    # Write attempts per drain cycle
    write_attempts_per_cycle: float

    def compute_thermal_output(self, params: SubstrateParams) -> float:
        """
        Compute normalised thermal output from overflow writes.
        thermal_output = cell_density / max_cell_density (clamped 0-1).
        """
        thermal = min(1.0, self.cell_density / max(params.max_cell_density, 1.0))
        self.thermal_output = thermal
        return thermal


# ============================================================================
# THE Ψ_REPAIR EQUATION (SOLITON FRAMEWORK)
# ============================================================================

class SubstrateLedgerEngine:
    """
    Main engine for managing the Substrate Ledger.

    Ψ_repair = ∫(M_header ⊗ R_resonance) · δ(ω - ω₀) dt
    """

    def __init__(self, kernel: TSMKernel):
        self.kernel = kernel
        self.params = SubstrateParams()

        # Foam cells (the addressable cell layer)
        self.foam_cells: Dict[str, FoamCell] = {}

        # N-space routing buffer
        self.nspace_buffer = NSpaceBuffer()

        # Overflow snags
        self.snags: List[OverflowSnag] = []

        # Successful write operations
        self.committed_writes: List[Dict] = []

        # Partial-write events
        self.partial_write_events: List[Dict] = []

    def initialize_foam_region(self, num_cells: int = 1000) -> None:
        """Initialize a region of foam substrate"""
        for i in range(num_cells):
            position = xp.random.rand(4)   # normalised unit coordinates
            cell = FoamCell(
                position=position,
                cell_state=complex(xp.random.rand(), xp.random.rand()),
                information=hashlib.sha256(bytes([i])).digest()[:8]
            )
            cell_id = f"cell_{i}"
            self.foam_cells[cell_id] = cell
            self.nspace_buffer.allocate_cell(cell_id, cell)

    def apply_metadata_header(self, cell_id: str, header: bytes) -> WriteOperationStatus:
        """Apply metadata header to commit a cell (write operation)"""
        if cell_id not in self.foam_cells:
            return WriteOperationStatus.BAD_SECTOR

        cell = self.foam_cells[cell_id]

        # Compute SNR before write
        snr = cell.compute_snr(self.params)

        if snr < self.params.snr_threshold:
            # Partial write — cell not resonance-locked
            cell.partial_write_magnitude = 1.0 - snr / self.params.snr_threshold
            cell.write_status = WriteOperationStatus.PARTIAL_WRITE

            self.partial_write_events.append({
                "cell_id": cell_id,
                "snr": snr,
                "partial_write_magnitude": cell.partial_write_magnitude,
                "timestamp": time.time()
            })

            return WriteOperationStatus.PARTIAL_WRITE

        # Apply header and attempt resonance lock
        success = cell.apply_metadata_header(header)

        if success:
            self.committed_writes.append({
                "cell_id": cell_id,
                "header_hash": hashlib.sha256(header).hexdigest(),
                "timestamp": time.time()
            })
            return WriteOperationStatus.COMMITTED
        else:
            return WriteOperationStatus.PENDING

    def detect_overflow_snag(self, region_center: AnyArray, region_radius: float) -> Optional[OverflowSnag]:
        """
        Detect overflow snags in a region.
        Occurs when cell density exceeds the substrate drain rate.
        """
        cells_in_region = []
        for cell_id, cell in self.foam_cells.items():
            distance = xp.linalg.norm(cell.position[:3] - region_center[:3])
            if distance < region_radius:
                cells_in_region.append(cell)

        if len(cells_in_region) < 10:
            return None

        total_info = sum(len(c.information) * 8 for c in cells_in_region)
        area = 4 * xp.pi * region_radius**2
        cell_density = total_info / area

        if cell_density > self.params.max_cell_density:
            severity = min(1.0, cell_density / self.params.max_cell_density)

            snag = OverflowSnag(
                position=region_center,
                cell_density=cell_density,
                severity=severity,
                thermal_output=0.0,
                overflow_boundary_area=area,
                write_attempts_per_cycle=len(cells_in_region) * self.params.clock_freq_hz
            )

            snag.compute_thermal_output(self.params)
            self.snags.append(snag)
            return snag

        return None

    def psi_repair_equation(self, cell_ids: List[str]) -> Dict:
        """
        Solve the Ψ_repair equation for formatting foam cells.

        Ψ_repair = ∫(M_header ⊗ R_resonance) · δ(ω - ω₀) dt

        Returns repair success metrics.
        """
        M_header = xp.zeros(len(cell_ids))
        for i, cell_id in enumerate(cell_ids):
            if cell_id in self.foam_cells:
                cell = self.foam_cells[cell_id]
                if cell.metadata_header:
                    header_hash = hashlib.sha256(cell.metadata_header).digest()
                    M_header[i] = int.from_bytes(header_hash[:4], 'big') / 2**32

        R_resonance = xp.zeros(len(cell_ids))
        for i, cell_id in enumerate(cell_ids):
            if cell_id in self.foam_cells:
                cell = self.foam_cells[cell_id]
                if cell.resonance_locked:
                    R_resonance[i] = 1.0

        delta_resonance = xp.zeros(len(cell_ids))
        for i, cell_id in enumerate(cell_ids):
            if cell_id in self.foam_cells:
                cell = self.foam_cells[cell_id]
                freq_match = xp.abs(cell.compute_snr(self.params) - self.params.snr_threshold)
                delta_resonance[i] = xp.exp(-freq_match**2 / 0.1)

        tensor_product = M_header * R_resonance
        psi_repair = xp.sum(tensor_product * delta_resonance)
        psi_repair /= len(cell_ids)

        return {
            "psi_repair": float(psi_repair),
            "M_header_magnitude": float(xp.sum(M_header)),
            "R_resonance_magnitude": float(xp.sum(R_resonance)),
            "delta_match": float(xp.sum(delta_resonance)),
            "formatted_cells": int(xp.sum(R_resonance)),
            "total_cells": len(cell_ids)
        }

    def foam_probe_operation(self, target_cell_ids: List[str], resonance_frequency: float) -> Dict:
        """
        Operate the Foam Probe for substrate maintenance.

        The probe creates a Local Formatting Zone by:
        1. Injecting resonance to lock cells
        2. Pulling overflow snags
        3. Stabilizing direct-path tunnel connections
        """
        import struct

        results = {
            "resonance_injected": resonance_frequency,
            "cells_targeted": len(target_cell_ids),
            "cells_locked": 0,
            "snags_pulled": 0,
            "tunnels_stabilized": 0,
            "partial_write_reduced": 0.0
        }

        initial_leakage = sum(
            self.foam_cells[cid].partial_write_magnitude
            for cid in target_cell_ids
            if cid in self.foam_cells
        )

        # Phase 1: Resonance injection
        for cell_id in target_cell_ids:
            if cell_id not in self.foam_cells:
                continue

            resonance_header = hashlib.sha256(
                struct.pack('<d', resonance_frequency) +
                struct.pack('<d', self.params.clock_freq_hz)
            ).digest()

            status = self.apply_metadata_header(cell_id, resonance_header)

            if status == WriteOperationStatus.COMMITTED:
                results["cells_locked"] += 1

        # Phase 2: Snag pulling (reduce overflow severity)
        for snag in self.snags:
            distance_to_target = min(
                xp.linalg.norm(snag.position - self.foam_cells[cid].position[:3])
                for cid in target_cell_ids
                if cid in self.foam_cells
            )

            if distance_to_target < self.params.probe_reach_cells:
                snag.severity *= 0.5
                snag.thermal_output *= 0.5
                results["snags_pulled"] += 1

        # Phase 3: Partial-write reduction
        final_leakage = sum(
            self.foam_cells[cid].partial_write_magnitude
            for cid in target_cell_ids
            if cid in self.foam_cells
        )

        results["partial_write_reduced"] = initial_leakage - final_leakage

        # Phase 4: Detect stabilised tunnel connections (high-crosstalk pairs)
        crosstalk = self.nspace_buffer.compute_crosstalk()
        high_crosstalk_pairs = xp.argwhere(crosstalk > 0.5)

        for pair in high_crosstalk_pairs:
            if len(pair) > 1:
                results["tunnels_stabilized"] += 1

        return results

    def compute_substrate_health(self) -> Dict:
        """Compute overall health metrics for the substrate ledger"""
        total_cells = len(self.foam_cells)
        committed = sum(1 for c in self.foam_cells.values() if c.write_status == WriteOperationStatus.COMMITTED)
        partial = sum(1 for c in self.foam_cells.values() if c.write_status == WriteOperationStatus.PARTIAL_WRITE)
        snags = len(self.snags)

        crosstalk = self.nspace_buffer.compute_crosstalk()
        avg_crosstalk = xp.mean(crosstalk) if crosstalk.size > 0 else 0.0

        return {
            "total_cells": total_cells,
            "committed_writes": committed,
            "commitment_rate": committed / max(total_cells, 1),
            "partial_write_events": partial,
            "partial_write_rate": partial / max(total_cells, 1),
            "overflow_snags": snags,
            "avg_crosstalk": float(avg_crosstalk),
            "max_crosstalk": float(xp.max(crosstalk)) if crosstalk.size > 0 else 0.0,
            "substrate_health": committed / max(total_cells, 1) - snags * 0.1 - partial * 0.05
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Demonstrate the Substrate Ledger model"""

    print("=" * 70)
    print("  THE SUBSTRATE LEDGER: N-SPACE SNAG AND LEAKAGE MANAGEMENT")
    print("=" * 70)
    print()

    kernel = TSMKernel()
    engine = SubstrateLedgerEngine(kernel)

    print("[PHASE 1] INITIALIZE FOAM REGION")
    engine.initialize_foam_region(num_cells=100)
    print(f"  Initialized {len(engine.foam_cells)} foam cells")
    print(f"  N-space buffer occupancy: {len(engine.nspace_buffer.occupancy)} cells")
    print()

    print("[PHASE 2] ATTEMPT WRITE OPERATIONS (Metadata Header Application)")

    for i, cell_id in enumerate(list(engine.foam_cells.keys())[:50]):
        header = hashlib.sha256(bytes([i])).digest()
        engine.apply_metadata_header(cell_id, header)

    health = engine.compute_substrate_health()
    print(f"  Committed writes: {health['committed_writes']} ({health['commitment_rate']*100:.1f}%)")
    print(f"  Partial-write events: {health['partial_write_events']} ({health['partial_write_rate']*100:.1f}%)")
    print()

    print("[PHASE 3] DETECT OVERFLOW SNAGS")

    center = xp.array([0.5, 0.5, 0.5])
    snag = engine.detect_overflow_snag(center, 1e-36)

    if snag:
        print(f"  ⚠ OVERFLOW SNAG DETECTED")
        print(f"    Cell density: {snag.cell_density:.2e} bits/unit²")
        print(f"    Severity: {snag.severity*100:.1f}%")
        print(f"    Thermal output: {snag.thermal_output:.4f}")
        print(f"    Overflow boundary area: {snag.overflow_boundary_area:.2e}")
    else:
        print("  No overflow snags detected in region")
    print()

    print("[PHASE 4] SOLVE Ψ_REPAIR EQUATION")
    print("  Ψ_repair = ∫(M_header ⊗ R_resonance) · δ(ω - ω₀) dt")

    cell_ids = list(engine.foam_cells.keys())[:50]
    repair_result = engine.psi_repair_equation(cell_ids)

    print(f"  Ψ_repair magnitude: {repair_result['psi_repair']:.4f}")
    print(f"  M_header magnitude: {repair_result['M_header_magnitude']:.2f}")
    print(f"  R_resonance magnitude: {repair_result['R_resonance_magnitude']:.2f}")
    print(f"  δ(ω-ω₀) match: {repair_result['delta_match']:.2f}")
    print(f"  Formatted cells: {repair_result['formatted_cells']}/{repair_result['total_cells']}")
    print()

    print("[PHASE 5] FOAM PROBE OPERATION (Substrate Maintenance)")

    probe_result = engine.foam_probe_operation(
        target_cell_ids=cell_ids,
        resonance_frequency=engine.params.clock_freq_hz
    )

    print(f"  Resonance injected: {probe_result['resonance_injected']:.2e} Hz")
    print(f"  Cells targeted: {probe_result['cells_targeted']}")
    print(f"  Cells locked: {probe_result['cells_locked']}")
    print(f"  Snags pulled: {probe_result['snags_pulled']}")
    print(f"  Tunnels stabilized: {probe_result['tunnels_stabilized']}")
    print(f"  Partial-write reduced: {probe_result['partial_write_reduced']:.4f}")
    print()

    print("[PHASE 6] N-SPACE CROSSTALK (Buffer Coupling)")

    if len(list(engine.foam_cells.keys())) > 10:
        source_cell = list(engine.foam_cells.keys())[0]
        target_cells = list(engine.foam_cells.keys())[1:10]
        crosstalk_signal = engine.nspace_buffer.detect_buffer_crosstalk(source_cell, target_cells)
        print(f"  Crosstalk signal strength: {crosstalk_signal:.6f}")

    crosstalk = engine.nspace_buffer.compute_crosstalk()
    print(f"  Average crosstalk: {xp.mean(crosstalk):.6f}")
    print(f"  Max crosstalk: {xp.max(crosstalk):.6f}")
    print(f"  (High crosstalk = strong buffer path coupling)")
    print()

    print("[PHASE 7] FINAL SUBSTRATE HEALTH ASSESSMENT")
    final_health = engine.compute_substrate_health()

    print(f"  Total cells: {final_health['total_cells']}")
    print(f"  Commitment rate: {final_health['commitment_rate']*100:.1f}%")
    print(f"  Partial-write rate: {final_health['partial_write_rate']*100:.1f}%")
    print(f"  Overflow snags: {final_health['overflow_snags']}")
    print(f"  Max crosstalk: {final_health['max_crosstalk']:.4f}")
    print(f"  SUBSTRATE HEALTH SCORE: {final_health['substrate_health']*100:.1f}%")
    print()

    results = {
        "substrate_params": {
            "grain_size_bytes": engine.params.grain_size_bytes,
            "clock_freq_hz": engine.params.clock_freq_hz,
            "snr_threshold": engine.params.snr_threshold
        },
        "repair_equation": repair_result,
        "foam_probe": probe_result,
        "substrate_health": final_health,
        "timestamp": time.time()
    }

    output_path = ROOT / "out" / "substrate_ledger_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[+] Results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
