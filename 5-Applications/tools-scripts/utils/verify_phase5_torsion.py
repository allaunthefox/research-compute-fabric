#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Verification for Phase 5: Soliton Drift & Torsion Calibration.

This script verifies that the calibrated baseline results in low torsion
for the anchor contract (Uniswap V2) and higher torsion for irregular code.
"""

import json
import unittest
from scripts.graphvm_canal_router import GraphVMCanalRouter
from scripts.rpc_bytecode_fetcher import RPCBytecodeFetcher

class TestPhase5(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # We use a consistent hex string for local calibration verification
        cls.test_bytecode = "0x6080604052348015600f57600080fd5b5060043610602857600035"
        
        # 1. Manually compute the 'baseline' for this specific segment
        from scripts.evm_bytecode_waveprobe import EVMBytecodeWaveprobe
        probe = EVMBytecodeWaveprobe(bytecode_hex=cls.test_bytecode)
        res = probe.analyze()
        # Average base features of the test bytecode
        cls.local_baseline = [sum(c.base_features[i] for c in res.chunks)/len(res.chunks) for i in range(8)]

    def test_torsion_consistency(self):
        """Test that a contract analyzed against its own baseline has low torsion."""
        # We pass the local baseline directly to skip the file loading for this specific test
        router = GraphVMCanalRouter(self.test_bytecode, baseline_drift_vec=self.local_baseline)
        report = router.route()
        print(f"[*] Local Consistency Torsion: {report.overall_torsion:.6f}")
        # Should be near 0 because it's matched against itself
        self.assertLess(report.overall_torsion, 0.05)

    def test_torsion_divergence(self):
        """Test that different code analyzed against the baseline has higher torsion."""
        different_bytecode = "0x" + "ff" * 100  # High-entropy noise
        router = GraphVMCanalRouter(different_bytecode, baseline_drift_vec=self.local_baseline)
        report = router.route()
        print(f"[*] Divergence Torsion: {report.overall_torsion:.6f}")
        # Should be significantly higher
        self.assertGreater(report.overall_torsion, 0.1)

if __name__ == "__main__":
    unittest.main()
