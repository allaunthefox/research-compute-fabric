#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""GraphVM Canal Router — Structural classification and routing.

This module implements the Cognitive Triage and Dynamic Canal Routing
equations to evaluate the "action-worthiness" and "thermodynamic cost"
(KOT) of interacting with a contract.

Equations:
  - Triage: T(x,t) = [wU*U + wS*S + wR*R + wH*H + wT*T - wB*B] * Pi
  - Canal: d_canal(x->y,t) = ||Phi(y)-Phi(x)|| * eta * (1 + torsion) * (1 + accumulation)
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

try:
    from scripts.evm_bytecode_waveprobe import EVMBytecodeWaveprobe, EVMWaveprobeResult
except ModuleNotFoundError:
    from evm_bytecode_waveprobe import EVMBytecodeWaveprobe, EVMWaveprobeResult  # type: ignore

# ── Feature dimension ────────────────────────────────────────────────────────
FEATURE_DIM = 8

# ── DEFAULT TOLERANCES ───────────────────────────────────────────────────────
DEFAULT_TOLERANCES = {
    "graphvm": {
        "weights": {
            "urgency": 0.4,
            "salience": 0.2,
            "surprise": 0.1,
            "heat": 0.3,
            "torsion": 0.2,
            "background": 0.1
        },
        "thresholds": {
            "theta_heat": 0.30,
            "theta_canal": 1000.0,
            "theta_working_set": 0.10,
            "theta_immediate": 0.80
        }
    }
}

@dataclass
class CanalRoutingReport:
    """Formal routing decision based on structural grain."""
    contract_sha256: str
    overall_heat: float
    overall_torsion: float
    overall_anisotropy: float
    triage_score: float
    canal_cost_kot: float
    valve_phi: int  # 0 or 1
    routing_decision: str  # immediate | review | freeze
    reason: str
    applied_tolerances: Dict[str, Any]  # Snapshot of thresholds/weights used

def deep_merge_dicts(base: dict, override: dict) -> dict:
    """Recursively merge two dictionaries."""
    res = base.copy()
    for k, v in override.items():
        if k in res and isinstance(res[k], dict) and isinstance(v, dict):
            res[k] = deep_merge_dicts(res[k], v)
        else:
            res[k] = v
    return res

class GraphVMCanalRouter:
    """Integrates waveprobe metrics into a routing decision."""

    def __init__(
        self,
        target_bytecode_hex: str,
        baseline_drift_vec: Optional[List[float]] = None,
        tolerances: Optional[dict] = None,
        jurisdiction: Optional[str] = None,
    ):
        self.probe = EVMBytecodeWaveprobe(bytecode_hex=target_bytecode_hex)
        
        # Load Soliton Baseline if not provided
        if baseline_drift_vec is None:
            baseline_path = "4-Infrastructure/config/soliton_baseline.json"
            if os.path.exists(baseline_path):
                try:
                    with open(baseline_path, "r", encoding="utf-8") as f_in:
                        data = json.load(f_in)
                        self.baseline_drift = data.get("soliton_baseline_vector", [0.0] * FEATURE_DIM)
                except (json.JSONDecodeError, IOError):
                    self.baseline_drift = [0.0] * FEATURE_DIM
            else:
                self.baseline_drift = [0.0] * FEATURE_DIM
        else:
            self.baseline_drift = baseline_drift_vec
        
        # 1. Start with global defaults
        full_tols = tolerances or DEFAULT_TOLERANCES
        
        # 2. Overlay jurisdiction-specific overrides if present
        if jurisdiction and "jurisdictions" in full_tols:
            overrides = full_tols["jurisdictions"].get(jurisdiction, {})
            if overrides:
                full_tols = deep_merge_dicts(full_tols, overrides)
        
        self.tols = full_tols.get("graphvm", {})
        self.weights = self.tols.get("weights", {})
        self.thresholds = self.tols.get("thresholds", {})
        
        # Pull specific thresholds for fast access
        self.theta_heat = self.thresholds.get("theta_heat", 0.30)
        self.theta_canal = self.thresholds.get("theta_canal", 1000.0)

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(a * a for a in v2))
        if norm1 < 1e-9 or norm2 < 1e-9:
            return 0.0
        return dot / (norm1 * norm2)

    def route(self, urgency: float = 0.0, salience: float = 0.5) -> CanalRoutingReport:
        """Run waveprobe and compute triage + canal metrics."""
        result: EVMWaveprobeResult = self.probe.analyze()
        
        # 1. Aggregate Torsion across chunks
        torsion_scores: list[float] = []
        for chunk in result.chunks:
            # Torsion = 1 - cos(base_features, baseline_drift)
            sim = self._cosine_similarity(chunk.base_features, self.baseline_drift)
            torsion_scores.append(1.0 - sim)
            
        overall_torsion = sum(torsion_scores) / max(1, len(torsion_scores))
        
        # 2. Raw Surprise (R) derived from overall heat/torsion
        surprise = (result.overall_heat + overall_torsion) / 2.0
        
        # 3. Admissibility Valve (Pi)
        # Fail-closed if overall heat exceeds threshold
        valve_phi = 1 if result.overall_heat < self.theta_heat else 0
        
        # 4. Cognitive Triage (T)
        w = self.weights
        triage = (
            w.get("urgency", 0.4) * urgency +
            w.get("salience", 0.2) * salience +
            w.get("surprise", 0.1) * surprise +
            w.get("heat", 0.3) * result.overall_heat +
            w.get("torsion", 0.2) * overall_torsion
        ) * valve_phi
        
        # 5. Dynamic Canal Cost (d_canal) in KOT
        # We model "moving through" this bytecode as traversing the Phi-space length
        # weighted by structural heat and torsion.
        phi_mag = result.overall_heat  # Proxy for average feature movement magnitude
        eta = 1.0  # Gas resistance placeholder
        canal_cost = (phi_mag * 100) * eta * (1 + overall_torsion)
        
        # 6. Routing Decision
        if valve_phi == 0:
            decision = "freeze"
            reason = f"Heat valve failure (H={result.overall_heat:.3f} > {self.theta_heat})"
        elif canal_cost > self.theta_canal:
            decision = "review"
            reason = f"Canal cost ceiling (KOT={canal_cost:.1f} > {self.theta_canal})"
        elif triage > self.thresholds.get("theta_immediate", 0.8):
            decision = "immediate"
            reason = f"High triage score (T={triage:.3f})"
        else:
            decision = "review"
            reason = f"Medium triage score (T={triage:.3f})"

        return CanalRoutingReport(
            contract_sha256=result.bytecode_sha256,
            overall_heat=result.overall_heat,
            overall_torsion=overall_torsion,
            overall_anisotropy=sum(c.anisotropy for c in result.chunks) / max(1, len(result.chunks)),
            triage_score=triage,
            canal_cost_kot=canal_cost,
            valve_phi=valve_phi,
            routing_decision=decision,
            reason=reason,
            applied_tolerances={
                "thresholds": self.thresholds,
                "weights": self.weights
            }
        )

# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GraphVM Canal Router")
    parser.add_argument("bytecode", help="Hex-encoded bytecode")
    parser.add_argument("--urgency", type=float, default=0.0)
    parser.add_argument("--config", help="Path to compliance_tolerances.json")
    parser.add_argument("--jurisdiction", help="Candidate jurisdiction (e.g. 'United States')")
    args = parser.parse_args()

    tols = None
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            tols = json.load(f)

    router = GraphVMCanalRouter(args.bytecode, tolerances=tols, jurisdiction=args.jurisdiction)
    report = router.route(urgency=args.urgency)
    
    print(json.dumps({
        "contract": report.contract_sha256[:16],
        "metrics": {
            "heat": round(report.overall_heat, 6),
            "torsion": round(report.overall_torsion, 6),
            "anisotropy": round(report.overall_anisotropy, 6),
            "triage": round(report.triage_score, 6),
            "canal_cost_kot": round(report.canal_cost_kot, 2)
        },
        "valve": report.valve_phi,
        "decision": report.routing_decision,
        "reason": report.reason
    }, indent=2))
