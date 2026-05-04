#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""CarrierState Reasoning Engine — Performs semantic 'Cognitive Triage' using Local LLMs.

This engine synthesizes structural waveprobe metrics (heat, torsion, anisotropy)
into high-level 'structural reasoning' to validate autonomous remediations.
"""

import json
import os
import sys
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

try:
    from scripts.local_llm_client import LocalLLMClient
    from scripts.graphvm_canal_router import CanalRoutingReport
except ModuleNotFoundError:
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from local_llm_client import LocalLLMClient  # type: ignore
    from graphvm_canal_router import CanalRoutingReport  # type: ignore

@dataclass
class ReasoningOutcome:
    """The result of a structural reasoning pass."""
    semantic_risk_score: float  # 0 to 1
    remediation_strategy: str   # immediate | review | freeze
    reasoning_summary: str
    is_anomaly: bool
    confidence: float          # 0 to 1 (reliability of the local model)

class CarrierStateReasoningEngine:
    """Bridges GraphVM metrics to semantic reasoning via Gemma2."""

    SYSTEM_PROMPT = """You are the OmniToken CarrierState Reasoning Engine. 
You perform 'Cognitive Triage' on EVM bytecode structural analysis.
Your goal is to identify structural drift and predatory architectures.

REMEDIATION_STRATEGY ENUM (MUST USE EXACTLY ONE):
- immediate: High Heat, Low Torsion (Fast protocol flow)
- review: Medium Heat/Torsion (Ambiguous architectural intent)
- freeze: High Heat, High Torsion (Suspected structural predation)

ALWAYS RETURN JSON format with:
{
  "semantic_risk_score": float (0.0 to 1.0),
  "remediation_strategy": "immediate" | "review" | "freeze",
  "reasoning_summary": "string",
  "is_anomaly": boolean,
  "confidence": float (0.0 to 1.0)
}"""

    def __init__(self, model_name: str = "gemma2:2b"):
        self.client = LocalLLMClient(model=model_name)

    def analyze_risk(self, report: CanalRoutingReport) -> Optional[ReasoningOutcome]:
        """Send the structural metrics to Gemma2 for semantic triage."""
        if not self.client.check_health():
            return None  # Fallback to hard-coded governance

        prompt = f"""STRUCTURAL METRICS REPORT:
Contract SHA256: {report.contract_sha256[:16]}
Heat (H): {report.overall_heat:.4f} (Theta_Heat: {report.applied_tolerances.get('thresholds', {}).get('theta_heat', 0.3)})
Torsion (T): {report.overall_torsion:.4f} (Deviation from CarrierState anchor)
Anisotropy (A): {report.overall_anisotropy:.4f} (Structural bias)
Canal Cost (KOT): {report.canal_cost_kot:.1f}
Triage Score (Triage): {report.triage_score:.4f}

Current Decision: {report.routing_decision}
Reason: {report.reason}

Assess the risk of structural predation or architectural drift. Does this code maintain the 'CarrierState' integrity of a canonical router?"""

        result = self.client.generate(prompt, system=self.SYSTEM_PROMPT)
        
        if "error" in result:
            return None

        # Post-generation normalization
        raw_strategy = str(result.get("remediation_strategy", report.routing_decision)).lower()
        normalized_strategy = self._normalize_strategy(raw_strategy, report.routing_decision)

        try:
            return ReasoningOutcome(
                semantic_risk_score=result.get("semantic_risk_score", 0.5),
                remediation_strategy=normalized_strategy,
                reasoning_summary=result.get("reasoning_summary", "Autonomous reasoning logic failed to formulate summary."),
                is_anomaly=result.get("is_anomaly", False),
                confidence=result.get("confidence", 0.1)
            )
        except Exception:
            return None

    def _normalize_strategy(self, strategy: str, fallback: str) -> str:
        """Map fuzzy LLM strings back to the strict internal enum."""
        if "immediate" in strategy:
            return "immediate"
        if "freeze" in strategy or "block" in strategy or "stop" in strategy:
            return "freeze"
        if "review" in strategy or "analyze" in strategy or "examine" in strategy:
            return "review"
        return fallback

if __name__ == "__main__":
    # Test/Mock
    mock_report = CanalRoutingReport(
        contract_sha256="0abc123...",
        overall_heat=0.85,
        overall_torsion=0.92,
        overall_anisotropy=0.45,
        triage_score=0.95,
        canal_cost_kot=4500.0,
        valve_phi=0,
        routing_decision="freeze",
        reason="Heat valve failure (H=0.85 > 0.3)",
        applied_tolerances={"thresholds": {"theta_heat": 0.3}}
    )
    
    engine = CarrierStateReasoningEngine()
    print(f"[*] Analyzing with Local Gemma ({engine.client.model})...")
    outcome = engine.analyze_risk(mock_report)
    if outcome:
        print(f"[+] Reasoning result: {outcome.remediation_strategy.upper()} - Confidence: {outcome.confidence}")
        print(f"Summary: {outcome.reasoning_summary}")
    else:
        print("[!] Local Reasoning OFFLINE - Using hard governance only.")
