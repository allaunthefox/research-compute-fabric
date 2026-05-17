# PROPRIETARY -- ALL RIGHTS RESERVED
# Copyright (c) 2026 Allaun Holdings
# See THIRD_PARTY_NOTICES.txt for third-party attributions.

"""
NUVMAP Projection Engine

Projects the eigenmass basis (from GPU constraint graph) into a
non-uniform address surface. High-eigenmass modes get dense allocation;
low-eigenmass modes get sparse/hashed/lossy allocation.

Key equation:
  q_i proportional to E_i / (R_i + epsilon)

Where:
  E_i = lambda_k * |v_k(i)| * S_i * L_i / (R_i + epsilon)
  S_i = structural integrity factor
  L_i = Landauer threshold factor
  R_i = residual risk
  epsilon = regularization
"""

import hashlib
import json
import math
import sqlite3
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NUVMAPCell:
    """A single NUVMAP address cell."""
    u_i: int                     # address coordinate
    v_i: int                     # spectral coordinate (eigenmode index)
    k_i: int                     # dominant eigenmode
    E_i: float                   # eigenmass
    R_i: float                   # residual risk
    chi_i: float                 # chiral residual
    S_i: float = 1.0             # structural integrity
    L_i: float = 1.0             # Landauer threshold factor
    q_i: int = 0                 # qubit allocation
    admissible: bool = True      # passes all gates
    equation_id: int = 0         # source equation
    fingerprint: str = ""        # CFF fingerprint


@dataclass
class NUVMAPSurface:
    """The full NUVMAP address surface."""
    cells: List[NUVMAPCell] = field(default_factory=list)
    total_qubits: int = 0
    bekenstein_bound: float = 0.0
    area_utilization: float = 0.0  # fraction of bound used
    root_fingerprint: str = ""
    timestamp: str = ""


class NUVMAPProjectionEngine:
    """
    Projects eigenmass data into a NUVMAP address surface.

    Follows the pipeline from eigenmass_quantum_implications.md:
      1. Accept eigenmass (AMVR, AVMR, chiral_residual) per equation
      2. Compute E_i = lambda_k * |v_k(i)| * S_i * L_i / (R_i + epsilon)
      3. Allocate qubits: q_i proportional to E_i / (R_i + epsilon)
      4. Check admissibility: chi_i <= chi_max AND R_i <= R_max
      5. Compute Bekenstein bound: I(NUVMAP) proportional to sum(lambda_k)
    """

    def __init__(self, total_qubit_budget: int = 0,
                 chi_max: float = 0.5, R_max: float = 0.5,
                 landauer_threshold: float = 0.1):
        self.total_qubit_budget = total_qubit_budget
        self.chi_max = chi_max
        self.R_max = R_max
        self.landauer_threshold = landauer_threshold
        self.epsilon = 1e-12
        self.surface = NUVMAPSurface()

    def project(self, eigenmass_data: List[Dict],
                eigenvalue: Optional[float] = None) -> NUVMAPSurface:
        """
        Project eigenmass data into a NUVMAP surface.

        eigenmass_data: list of dicts with keys:
            equation_id, amvr, avmr, chiral_residual, chiral_state

        Returns populated NUVMAPSurface.
        """
        if not eigenmass_data:
            return self.surface

        n = len(eigenmass_data)
        cells = []

        max_eigenmass = max(
            (d.get("amvr", 0.0) + d.get("avmr", 0.0)) / 2.0
            for d in eigenmass_data
        ) or 1.0

        total_R = 0.0

        for i, d in enumerate(eigenmass_data):
            amvr = d.get("amvr", 0.0)
            avmr = d.get("avmr", 0.0)
            cr = d.get("chiral_residual", 0.0)
            eq_id = d.get("equation_id", 0)
            cs = d.get("chiral_state", "achiral_stable")

            raw_eigenmass = (amvr + avmr) / 2.0
            E_norm = raw_eigenmass / max_eigenmass

            R_i = max(0.01, 1.0 - E_norm)
            if cs == "chiral_scarred":
                R_i *= 1.5

            S_i = 1.0 if cs in ("achiral_stable",) else (
                0.7 if cs in ("left_handed_mass_bias", "right_handed_vector_bias")
                else 0.3
            )

            L_i = 1.0 if E_norm > self.landauer_threshold else E_norm / self.landauer_threshold

            # E_i = lambda_k * |v_k(i)| * S_i * L_i / (R_i + epsilon)
            if eigenvalue is not None:
                lam = eigenvalue
                v_abs = E_norm
            else:
                lam = 1.0
                v_abs = E_norm

            E_i = (lam * v_abs * S_i * L_i) / (R_i + self.epsilon)

            chi_i = cr

            is_max_ok = R_i <= self.R_max
            is_chi_ok = chi_i <= self.chi_max
            admissible = is_max_ok and is_chi_ok

            total_R += R_i

            fp_payload = f"{eq_id}\x00{amvr}\x00{avmr}\x00{cr}\x00{cs}"
            fp = hashlib.sha256(fp_payload.encode()).hexdigest()

            cells.append(NUVMAPCell(
                u_i=i, v_i=i, k_i=i,
                E_i=E_i, R_i=R_i, chi_i=chi_i,
                S_i=S_i, L_i=L_i,
                q_i=0, admissible=admissible,
                equation_id=eq_id, fingerprint=fp,
            ))

        # --- Qubit allocation proportional to E_i / (R_i + epsilon) ---
        total_weight = sum(c.E_i / (c.R_i + self.epsilon) for c in cells) or 1.0

        if self.total_qubit_budget > 0:
            budget = self.total_qubit_budget
        else:
            # Auto-allocate: at least 1 qubit per admissible cell, proportional beyond that
            budget = sum(c.E_i * 100 for c in cells if c.admissible)

        budget = max(budget, len([c for c in cells if c.admissible]))

        for c in cells:
            if c.admissible:
                weight = c.E_i / (c.R_i + self.epsilon)
                raw_q = int(budget * weight / total_weight)
                c.q_i = max(1, raw_q) if raw_q > 0 else 1
            else:
                c.q_i = 0

        total_qubits = sum(c.q_i for c in cells)

        # Bekenstein-like bound: I proportional to sum(lambda_k) <= A / (4*l^2)
        bekenstein = sum(c.E_i for c in cells) / (len(cells) or 1)

        area_utilization = total_qubits / (bekenstein + self.epsilon) if bekenstein > 0 else 0.0

        self.surface = NUVMAPSurface(
            cells=cells,
            total_qubits=total_qubits,
            bekenstein_bound=bekenstein,
            area_utilization=area_utilization,
            root_fingerprint=self._compute_surface_root(cells),
            timestamp=datetime.utcnow().isoformat(),
        )

        return self.surface

    @staticmethod
    def _compute_surface_root(cells: List[NUVMAPCell]) -> str:
        """Compute root fingerprint over the entire NUVMAP surface."""
        payload = "|".join(
            f"{c.u_i}:{c.E_i:.8f}:{c.chi_i:.8f}:{c.q_i}"
            for c in sorted(cells, key=lambda x: x.u_i)
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def project_from_db(self, db_path: str) -> NUVMAPSurface:
        """Build NUVMAP projection from a physics_equations database."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Try gpu_eigenmass first, then chiral_eigenmass
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gpu_eigenmass'")
        has_gpu = bool(cursor.fetchone())

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chiral_eigenmass'")
        has_chiral = bool(cursor.fetchone())

        data = []
        if has_gpu:
            cursor.execute("""
                SELECT equation_id, amvr_eigenmass as amvr, avmr_eigenmass as avmr,
                       chiral_residual, chiral_state
                FROM gpu_eigenmass ORDER BY equation_id
            """)
        elif has_chiral:
            cursor.execute("""
                SELECT equation_id, amvr_eigenmass as amvr, avmr_eigenmass as avmr,
                       chiral_residual, chiral_state
                FROM chiral_eigenmass ORDER BY equation_id
            """)
        else:
            conn.close()
            return self.surface

        for row in cursor.fetchall():
            data.append({
                "equation_id": row["equation_id"],
                "amvr": row["amvr"],
                "avmr": row["avmr"],
                "chiral_residual": row["chiral_residual"],
                "chiral_state": row["chiral_state"],
            })

        conn.close()
        return self.project(data)

    def save_to_db(self, db_path: str):
        """Save the NUVMAP surface to the database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nuvmap_surface (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equation_id INTEGER, u_i INTEGER, v_i INTEGER, k_i INTEGER,
                E_i REAL, R_i REAL, chi_i REAL, S_i REAL, L_i REAL,
                q_i INTEGER, admissible INTEGER, fingerprint TEXT,
                surface_root TEXT, created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (equation_id) REFERENCES equations(id)
            )
        """)

        surface_root = self.surface.root_fingerprint

        for c in self.surface.cells:
            cursor.execute("""
                INSERT OR REPLACE INTO nuvmap_surface
                (equation_id, u_i, v_i, k_i, E_i, R_i, chi_i, S_i, L_i,
                 q_i, admissible, fingerprint, surface_root)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c.equation_id, c.u_i, c.v_i, c.k_i,
                c.E_i, c.R_i, c.chi_i, c.S_i, c.L_i,
                c.q_i, int(c.admissible), c.fingerprint,
                surface_root,
            ))

        conn.commit()
        conn.close()

    def quantum_storage_admissible(self, node_i: int, tau: float,
                                   chi_max: float = None) -> bool:
        """
        Implements the Lean-safe gate from the quantum implications doc:

        QuantumStorageAdmissible_i(k, tau, chi_max) iff:
          lambda_k * |v_k(i)| * S_i * L_i <= tau * (R_i + epsilon)
          AND chi_i <= chi_max
          AND receipt_i.valid
        """
        if chi_max is None:
            chi_max = self.chi_max

        if node_i < 0 or node_i >= len(self.surface.cells):
            return False

        c = self.surface.cells[node_i]

        lhs = c.E_i * (c.R_i + self.epsilon)
        rhs = tau * (c.R_i + self.epsilon)

        gate1 = lhs <= rhs
        gate2 = c.chi_i <= chi_max
        gate3 = c.admissible

        return gate1 and gate2 and gate3

    def get_density_map(self) -> Dict[str, List[float]]:
        """Return the eigenmass density distribution."""
        if not self.surface.cells:
            return {"E_i": [], "q_i": [], "chi_i": [], "R_i": []}

        return {
            "E_i": [c.E_i for c in self.surface.cells],
            "q_i": [c.q_i for c in self.surface.cells],
            "chi_i": [c.chi_i for c in self.surface.cells],
            "R_i": [c.R_i for c in self.surface.cells],
            "equation_ids": [c.equation_id for c in self.surface.cells],
        }

    def summary(self) -> Dict:
        s = self.surface
        admissible = [c for c in s.cells if c.admissible]
        return {
            "num_cells": len(s.cells),
            "num_admissible": len(admissible),
            "num_rejected": len(s.cells) - len(admissible),
            "total_qubits": s.total_qubits,
            "avg_qubits_per_cell": s.total_qubits / max(len(admissible), 1),
            "bekenstein_bound": round(s.bekenstein_bound, 4),
            "area_utilization": f"{s.area_utilization:.2%}",
            "max_eigenmass": max((c.E_i for c in s.cells), default=0),
            "max_chiral": max((c.chi_i for c in s.cells), default=0),
            "surface_root": s.root_fingerprint[:32] + "...",
        }


def build_nuvmap_from_eigenmass(eigenmass_data: List[Dict],
                                qubit_budget: int = 0) -> NUVMAPSurface:
    """Convenience: one-shot NUVMAP projection from eigenmass data."""
    engine = NUVMAPProjectionEngine(total_qubit_budget=qubit_budget)
    return engine.project(eigenmass_data)


def build_nuvmap_from_db(db_path: str,
                         qubit_budget: int = 0) -> NUVMAPSurface:
    """Convenience: one-shot NUVMAP projection from database."""
    engine = NUVMAPProjectionEngine(total_qubit_budget=qubit_budget)
    return engine.project_from_db(db_path)
