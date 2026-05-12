# PROPRIETARY -- ALL RIGHTS RESERVED
# Copyright (c) 2026 Allaun Holdings
# This source file is proprietary and confidential.
# See THIRD_PARTY_NOTICES.txt for third-party attributions.

"""
GPU-Accelerated Eigenmass Engine

CUDA PageRank on constraint DAG, AMVR/AVMR, chiral decomposition.
"""

import json
import sqlite3
import time
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

HAS_TORCH = False
HAS_CUDA = False
try:
    import torch
    HAS_TORCH = True
    HAS_CUDA = torch.cuda.is_available()
except ImportError:
    pass


@dataclass
class EigenmassResult:
    node_count: int
    amvr: np.ndarray
    avmr: np.ndarray
    chiral_residual: np.ndarray
    chiral_state: List[str]
    eigenvalues: Optional[np.ndarray] = None
    eigenvectors: Optional[np.ndarray] = None
    convergence: int = 0
    compute_time_ms: float = 0.0


class GPUConstraintGraph:
    """GPU-accelerated constraint graph for eigenmass computation."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.device = torch.device("cuda" if HAS_CUDA else "cpu")
        self.node_map: Dict[int, int] = {}
        self.node_ids: List[int] = []
        self.adjacency: Optional[torch.Tensor] = None
        self.edge_list: List[Tuple[int, int]] = []
        self.node_count = 0

    def load_from_db(self, db_path: str = None):
        if db_path is None:
            db_path = self.db_path
        if db_path is None:
            raise ValueError("No database path provided")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        edges = []

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invariant_chains'")
        if cursor.fetchone():
            for lp in [("layer1_eq_id","layer2_eq_id"),("layer2_eq_id","layer3_eq_id"),("layer3_eq_id","layer4_eq_id")]:
                cursor.execute(f"SELECT {lp[0]} src, {lp[1]} dst FROM invariant_chains WHERE {lp[0]} IS NOT NULL AND {lp[1]} IS NOT NULL")
                for r in cursor.fetchall():
                    if r[0] and r[1]:
                        edges.append((int(r[0]), int(r[1])))

        existing_ids = set()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chiral_eigenmass'")
        if cursor.fetchone():
            cursor.execute("SELECT equation_id FROM chiral_eigenmass ORDER BY equation_id")
            existing_ids = {row[0] for row in cursor.fetchall()}

        conn.close()

        all_ids = set()
        for src, dst in edges:
            all_ids.add(src); all_ids.add(dst)
        all_ids.update(existing_ids)

        self._build_from_edges(edges, sorted(all_ids))
        return self

    def load_from_edges(self, edges: List[Tuple[int,int]], node_ids: List[int] = None):
        if node_ids is None:
            all_ids = set()
            for s,d in edges:
                all_ids.add(s); all_ids.add(d)
            node_ids = sorted(all_ids)
        self._build_from_edges(edges, node_ids)
        return self

    def _build_from_edges(self, edges: List[Tuple[int,int]], node_ids: List[int]):
        self.node_ids = list(node_ids)
        self.node_map = {eid: i for i, eid in enumerate(self.node_ids)}
        self.node_count = len(self.node_ids)
        self.edge_list = list(set(edges))

        rows, cols = [], []
        for src, dst in self.edge_list:
            if src in self.node_map and dst in self.node_map:
                rows.append(self.node_map[dst]); cols.append(self.node_map[src])

        if rows:
            idx = torch.tensor([rows, cols], dtype=torch.long, device=self.device)
            vals = torch.ones(len(rows), dtype=torch.float32, device=self.device)
            self.adjacency = torch.sparse_coo_tensor(idx, vals, (self.node_count, self.node_count)).coalesce()
        else:
            self.adjacency = torch.sparse_coo_tensor(
                torch.zeros((2,0), dtype=torch.long, device=self.device),
                torch.zeros(0, dtype=torch.float32, device=self.device),
                (self.node_count, self.node_count))

    def compute_pagerank(self, damping: float = 0.85, max_iter: int = 1000, tol: float = 1e-6):
        if self.adjacency is None or self.node_count == 0:
            return np.array([]), 0
        n = self.node_count
        adj = self.adjacency
        indices = adj.indices()
        values = adj.values()

        out_deg = torch.zeros(n, dtype=torch.float32, device=self.device)
        out_deg.scatter_add_(0, indices[1], torch.ones_like(values))
        danglers = (out_deg == 0)
        out_deg = torch.where(danglers, torch.ones_like(out_deg), out_deg)

        pr = torch.ones(n, dtype=torch.float32, device=self.device) / n
        tele = torch.ones(n, dtype=torch.float32, device=self.device) / n

        for it in range(max_iter):
            prev = pr.clone()
            rv = values * pr[indices[1]] / out_deg[indices[1]]
            pn = torch.zeros(n, dtype=torch.float32, device=self.device)
            pn.scatter_add_(0, indices[0], rv)
            ds = pr[danglers].sum() if danglers.any() else 0.0
            pn = damping * pn + damping * ds * tele + (1.0 - damping) * tele
            pn = pn / pn.sum()
            pr = pn
            if torch.abs(pr - prev).sum().item() < tol:
                return pr.cpu().numpy(), it + 1
        return pr.cpu().numpy(), max_iter

    def compute_eigenmass(self) -> EigenmassResult:
        t0 = time.time()
        n = self.node_count
        if n == 0:
            return EigenmassResult(0, np.array([]), np.array([]), np.array([]), [])

        amvr, fi = self.compute_pagerank()
        saved = self.adjacency
        if self.adjacency._nnz() > 0:
            self.adjacency = self.adjacency.transpose(0,1).coalesce()
        avmr, ri = self.compute_pagerank()
        self.adjacency = saved

        cr = np.abs(amvr - avmr)
        total = amvr + avmr + 1e-12
        ca = 1.0 - cr / total

        cs = []
        for i in range(n):
            if ca[i] > 0.9: cs.append("achiral_stable")
            elif cr[i] > 0.3: cs.append("chiral_scarred")
            elif amvr[i] > avmr[i]: cs.append("left_handed_mass_bias")
            elif avmr[i] > amvr[i]: cs.append("right_handed_vector_bias")
            else: cs.append("achiral_stable")

        evals = None; evecs = None
        if 0 < n <= 2000:
            try:
                dense = self.adjacency.to_dense().cpu()
                sym = (dense + dense.T) / 2.0
                ev, ec = torch.linalg.eigh(sym)
                evals = ev.numpy(); evecs = ec.numpy()
            except Exception:
                pass

        return EigenmassResult(n, amvr, avmr, cr, cs, evals, evecs, max(fi,ri), (time.time()-t0)*1000)

    def save_eigenmass_to_db(self, db_path: str, result: EigenmassResult):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS gpu_eigenmass (
            equation_id INTEGER PRIMARY KEY, amvr_eigenmass REAL, avmr_eigenmass REAL,
            chiral_residual REAL, chiral_state TEXT,
            compute_timestamp TEXT DEFAULT (datetime('now')))""")
        for i in range(result.node_count):
            c.execute("INSERT OR REPLACE INTO gpu_eigenmass VALUES (?,?,?,?,?,datetime('now'))",
                (self.node_ids[i], float(result.amvr[i]), float(result.avmr[i]),
                 float(result.chiral_residual[i]), result.chiral_state[i]))
        conn.commit(); conn.close()

    def get_top_chiral(self, n: int = 10) -> List[Dict]:
        r = self.compute_eigenmass()
        ti = np.argsort(-r.chiral_residual)[:n]
        return [{"equation_id": self.node_ids[i], "chiral_residual": float(r.chiral_residual[i]),
                 "amvr": float(r.amvr[i]), "avmr": float(r.avmr[i]),
                 "chiral_state": r.chiral_state[i]} for i in ti]


def compute_eigenmass_from_db(db_path: str) -> EigenmassResult:
    g = GPUConstraintGraph(db_path)
    g.load_from_db(db_path)
    return g.compute_eigenmass()


def bench_gpu_vs_cpu(db_path: str) -> EigenmassResult:
    g = GPUConstraintGraph(db_path)
    g.load_from_db(db_path)
    r = g.compute_eigenmass()
    print(f"GPU: {r.compute_time_ms:.1f}ms, {r.node_count} nodes, {r.convergence} iters")
    print(f"Device: {g.device}")
    print(f"Max chiral residual: {r.chiral_residual.max():.6f}")
    print(f"  achiral: {sum(1 for s in r.chiral_state if s=='achiral_stable')}")
    print(f"  scarred: {sum(1 for s in r.chiral_state if s=='chiral_scarred')}")
    print(f"  mass_bias: {sum(1 for s in r.chiral_state if s=='left_handed_mass_bias')}")
    print(f"  vector_bias: {sum(1 for s in r.chiral_state if s=='right_handed_vector_bias')}")
    return r
