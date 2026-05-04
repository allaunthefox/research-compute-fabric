#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Verification for Phase 6: Local Gemma Integration.

This script verifies that the Soliton Reasoning Engine can successfully
communicate with the local Gemma2 model to perform semantic triage.
"""

import json
import unittest
from scripts.soliton_reasoning_engine import SolitonReasoningEngine
from scripts.graphvm_canal_router import CanalRoutingReport

class TestPhase6(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.engine = SolitonReasoningEngine(model_name="gemma2:2b")
        cls.mock_report = CanalRoutingReport(
            contract_sha256="mock_sha256_deadbeef",
            overall_heat=0.88,
            overall_torsion=0.95,
            overall_anisotropy=0.50,
            triage_score=0.98,
            canal_cost_kot=5200.0,
            valve_phi=0,
            routing_decision="freeze",
            reason="Critical structural deviance",
            applied_tolerances={"thresholds": {"theta_heat": 0.3}}
        )

    def test_reasoning_online(self):
        """Check if Gemma2 is online and responding."""
        if not self.engine.client.check_health():
            self.skipTest("Local Gemma2:2b is not online/pulled yet.")
            
        print(f"[*] Querying Local Gemma ({self.engine.client.model})...")
        outcome = self.engine.analyze_risk(self.mock_report)
        
        self.assertIsNotNone(outcome, "Reasoning engine failed to return an outcome.")
        print(f"[+] Reasoning Outcome: {outcome.remediation_strategy.upper()}")
        print(f"[*] Summary: {outcome.reasoning_summary}")
        
        self.assertIn(outcome.remediation_strategy, ["immediate", "review", "freeze"])
        self.assertGreaterEqual(outcome.semantic_risk_score, 0.0)
        self.assertLessEqual(outcome.semantic_risk_score, 1.0)

if __name__ == "__main__":
    unittest.main()
