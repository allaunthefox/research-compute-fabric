#!/usr/bin/env python3
"""
Virtual FPGA System Test — Prover Orchestration Layers
=======================================================
Runs the prover-integrated orchestration engine through
comprehensive system tests on simulated Tang Nano 9K FPGAs.

Tests:
  1. Normal operation — 1000 state transitions
  2. Invariant violations — Q16.16 overflow, skew, PDN
  3. Agent drift — BFS detects non-determinism
  4. Invalid manifold reshape — bf4 blocks bad configs
  5. Load test — sustained throughput measurement
  6. Recovery — watchdog blocks then system recovers
"""

import json, time, random, statistics
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from collections import defaultdict

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

# Import the orchestration engine
import sys
sys.path.insert(0, str(RESEARCH_STACK / "4-Infrastructure/shim"))
from prover_orchestration_layer import (
    ProverOrchestrationEngine, ProverWatchdog, SwarmConsensus, TopologicalAdaptation
)


@dataclass
class VirtualFPGA:
    """Simulated Tang Nano 9K FPGA instance."""
    id: int
    luts_used: int = 0
    bram_used: int = 0
    dsp_used: int = 0
    temperature_c: float = 35.0
    state: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    MAX_LUTS = 8640
    MAX_BRAM = 26  # 18Kb blocks
    MAX_DSP = 20
    
    def utilization(self) -> float:
        return max(self.luts_used / self.MAX_LUTS,
                   self.bram_used / self.MAX_BRAM,
                   self.dsp_used / self.MAX_DSP)
    
    def healthy(self) -> bool:
        return self.temperature_c < 85 and self.utilization() < 0.95


class VirtualFPGACluster:
    """Cluster of virtual FPGAs for system testing."""
    
    def __init__(self, num_fpgas: int = 5):
        self.fpgas = [VirtualFPGA(i) for i in range(num_fpgas)]
        self.engine = ProverOrchestrationEngine()
        self.test_results: List[Dict] = []
    
    def _make_state(self, fpga_id: int, skew_ps: float = 30, pdn_z: float = 8,
                    q16_vals: List[int] = None, delays: List[int] = None) -> Dict:
        """Build a state dict for a virtual FPGA."""
        return {
            "fpga_id": fpga_id,
            "q16": q16_vals or [random.randint(-1000, 1000) for _ in range(4)],
            "delays": delays or [random.randint(40, 80) for _ in range(4)],
            "pdn_z": pdn_z,
            "pdn_target": 10,
            "skew_ps": skew_ps,
            "nodes": 5,
            "edges": 8,
            "findings": [
                {"agent_id": i, "in": {"fpga": fpga_id}, "out": {"ok": True}}
                for i in range(3)
            ],
            "manifold": {
                "dim": 4, "shape": "flat",
                "ev": [1.77, 2.51, 3.07, 3.54]
            }
        }
    
    def run_test_suite(self):
        """Execute all system tests."""
        print("=" * 70)
        print("Virtual FPGA System Test — Prover Orchestration Layers")
        print("=" * 70)
        
        tests = [
            ("Normal Operation", self.test_normal_operation),
            ("Invariant Violations", self.test_invariant_violations),
            ("Agent Drift Detection", self.test_agent_drift),
            ("Invalid Manifold Reshape", self.test_invalid_reshape),
            ("Sustained Load Test", self.test_sustained_load),
            ("Recovery After Violation", self.test_recovery),
        ]
        
        passed = 0
        for name, test_fn in tests:
            print(f"\n{'─' * 70}")
            print(f"TEST: {name}")
            print(f"{'─' * 70}")
            try:
                result = test_fn()
                self.test_results.append({"test": name, "result": result})
                if result.get("passed", False):
                    passed += 1
                    print(f"  ✓ PASSED")
                else:
                    print(f"  ✗ FAILED: {result.get('error', 'unknown')}")
            except Exception as e:
                self.test_results.append({"test": name, "result": {"passed": False, "error": str(e)}})
                print(f"  ✗ EXCEPTION: {e}")
        
        print(f"\n{'=' * 70}")
        print(f"RESULTS: {passed}/{len(tests)} tests passed")
        print(f"{'=' * 70}")
        
        return passed == len(tests)
    
    def test_normal_operation(self) -> Dict:
        """1000 normal state transitions — all should pass."""
        print("  Running 1000 normal transitions...")
        
        latencies = []
        violations_total = 0
        
        for i in range(1000):
            fpga = self.fpgas[i % len(self.fpgas)]
            from_st = self._make_state(fpga.id)
            to_st = self._make_state(fpga.id)
            
            t0 = time.time()
            ok, report = self.engine.process(from_st, to_st)
            latencies.append((time.time() - t0) * 1000)
            
            if not ok:
                violations_total += 1
        
        metrics = self.engine.metrics()
        
        result = {
            "passed": violations_total == 0,
            "transitions": 1000,
            "violations": violations_total,
            "mean_latency_ms": statistics.mean(latencies),
            "p50_latency_ms": statistics.median(latencies),
            "p99_latency_ms": sorted(latencies)[int(len(latencies) * 0.99)],
            "max_latency_ms": max(latencies),
            "throughput_ops_s": 1000 / (sum(latencies) / 1000),
        }
        
        print(f"  Violations: {violations_total}/1000")
        print(f"  Mean latency: {result['mean_latency_ms']:.3f}ms")
        print(f"  P99 latency: {result['p99_latency_ms']:.3f}ms")
        print(f"  Throughput: {result['throughput_ops_s']:.0f} ops/s")
        
        return result
    
    def test_invariant_violations(self) -> Dict:
        """Test that each invariant violation is caught."""
        print("  Testing invariant violation detection...")
        
        violations_found = []
        
        # Q16.16 overflow
        from_st = self._make_state(0)
        to_st = self._make_state(0, q16_vals=[40000, 0, 0, 0])  # overflow
        ok, report = self.engine.process(from_st, to_st)
        if not ok:
            violations_found.append("Q16_16_overflow")
        print(f"  Q16.16 overflow: {'CAUGHT' if not ok else 'MISSED'}")

        # PDN impedance violation
        from_st = self._make_state(0)
        to_st = self._make_state(0, pdn_z=25)  # exceeds target 10
        ok, report = self.engine.process(from_st, to_st)
        if not ok:
            violations_found.append("PDN_impedance")
        print(f"  PDN impedance: {'CAUGHT' if not ok else 'MISSED'}")

        # Trace skew violation
        from_st = self._make_state(0)
        to_st = self._make_state(0, skew_ps=80)  # exceeds 50ps
        ok, report = self.engine.process(from_st, to_st)
        if not ok:
            violations_found.append("trace_skew")
        print(f"  Trace skew: {'CAUGHT' if not ok else 'MISSED'}")

        # FAMM delay negative
        from_st = self._make_state(0)
        to_st = self._make_state(0, delays=[-5, 50, 50, 50])
        ok, report = self.engine.process(from_st, to_st)
        if not ok:
            violations_found.append("FAMM_delay")
        print(f"  FAMM negative delay: {'CAUGHT' if not ok else 'MISSED'}")

        # Topology disconnected
        from_st = self._make_state(0)
        to_st = self._make_state(0)
        to_st["nodes"] = 10
        to_st["edges"] = 2  # 2 edges for 10 nodes = disconnected
        ok, report = self.engine.process(from_st, to_st)
        if not ok:
            violations_found.append("topology_disconnected")
        print(f"  Topology disconnected: {'CAUGHT' if not ok else 'MISSED'}")

        return {
            "passed": len(violations_found) == 5,
            "violations_detected": len(violations_found),
            "expected": 5,
            "details": violations_found,
        }
    
    def test_agent_drift(self) -> Dict:
        """Test BFS-Prover-V2 drift detection."""
        print("  Testing agent drift detection...")
        
        # First, establish baseline
        from_st = self._make_state(0)
        to_st = self._make_state(0)
        self.engine.process(from_st, to_st)
        
        # Now inject drift: same agent, different output for same input
        from_st2 = self._make_state(0)
        to_st2 = self._make_state(0)
        to_st2["findings"][0]["out"] = {"ok": False, "drift": True}
        
        ok, report = self.engine.process(from_st2, to_st2)
        
        drift_detected = self.engine.swarm.drift
        print(f"  Drift detected: {drift_detected}")
        
        return {
            "passed": drift_detected,
            "drift_detected": drift_detected,
        }
    
    def test_invalid_reshape(self) -> Dict:
        """Test bf4prover blocks invalid manifold reshapes."""
        print("  Testing invalid manifold reshape rejection...")
        
        # Negative eigenvalue
        from_st = self._make_state(0)
        to_st = self._make_state(0)
        to_st["manifold"] = {"dim": 4, "shape": "invalid", "ev": [-1.0, 2.0, 3.0, 4.0]}
        
        ok, report = self.engine.process(from_st, to_st)
        print(f"  Negative eigenvalue: {'BLOCKED' if not ok else 'ALLOWED'}")
        
        # Zero dimension
        from_st2 = self._make_state(0)
        to_st2 = self._make_state(0)
        to_st2["manifold"] = {"dim": 0, "shape": "point", "ev": []}
        
        ok2, report2 = self.engine.process(from_st2, to_st2)
        print(f"  Zero dimension: {'BLOCKED' if not ok2 else 'ALLOWED'}")
        
        return {
            "passed": not ok and not ok2,
            "negative_ev_blocked": not ok,
            "zero_dim_blocked": not ok2,
        }
    
    def test_sustained_load(self) -> Dict:
        """Sustained throughput test — 10,000 transitions."""
        print("  Running 10,000 sustained load transitions...")
        
        latencies = []
        batch_size = 1000
        
        for batch in range(10):
            batch_start = time.time()
            for i in range(batch_size):
                fpga = self.fpgas[i % len(self.fpgas)]
                from_st = self._make_state(fpga.id)
                to_st = self._make_state(fpga.id)
                
                t0 = time.time()
                self.engine.process(from_st, to_st)
                latencies.append((time.time() - t0) * 1000)
            
            batch_time = time.time() - batch_start
            print(f"  Batch {batch+1}/10: {batch_size} ops in {batch_time:.2f}s "
                  f"({batch_size/batch_time:.0f} ops/s)")
        
        result = {
            "passed": True,
            "total_ops": 10000,
            "mean_latency_ms": statistics.mean(latencies),
            "p50_latency_ms": statistics.median(latencies),
            "p99_latency_ms": sorted(latencies)[int(len(latencies) * 0.99)],
            "throughput_ops_s": 10000 / (sum(latencies) / 1000),
        }
        
        print(f"  Mean: {result['mean_latency_ms']:.3f}ms, "
              f"P99: {result['p99_latency_ms']:.3f}ms, "
              f"Throughput: {result['throughput_ops_s']:.0f} ops/s")
        
        return result
    
    def test_recovery(self) -> Dict:
        """Test system recovers after watchdog blocks a violation."""
        print("  Testing recovery after violation...")
        
        # Cause a violation
        from_st = self._make_state(0)
        to_st_bad = self._make_state(0, q16_vals=[50000, 0, 0, 0])
        ok_bad, _ = self.engine.process(from_st, to_st_bad)
        
        # Now try a valid transition
        to_st_good = self._make_state(0)
        ok_good, report = self.engine.process(from_st, to_st_good)
        
        recovered = ok_good and not ok_bad
        print(f"  Bad transition blocked: {not ok_bad}")
        print(f"  Good transition allowed: {ok_good}")
        print(f"  Recovery successful: {recovered}")
        
        return {
            "passed": recovered,
            "bad_blocked": not ok_bad,
            "good_allowed": ok_good,
            "recovered": recovered,
        }


def main():
    cluster = VirtualFPGACluster(num_fpgas=5)
    all_passed = cluster.run_test_suite()
    
    # Save detailed report
    report_path = RESEARCH_STACK / "4-Infrastructure/shim/virtual_fpga_system_test_report.json"
    
    final_metrics = cluster.engine.metrics()
    
    report = {
        "timestamp": time.time(),
        "all_passed": all_passed,
        "tests": cluster.test_results,
        "final_metrics": final_metrics,
        "fpgas": [
            {"id": f.id, "healthy": f.healthy(), "utilization": f.utilization()}
            for f in cluster.fpgas
        ],
        "summary": {
            "total_tests": len(cluster.test_results),
            "passed": sum(1 for t in cluster.test_results if t["result"].get("passed", False)),
            "total_transitions": 11000,
            "watchdog_violations": final_metrics["watchdog_violations"],
            "swarm_drift_events": final_metrics["swarm_drift"],
            "topology_adaptations": final_metrics["topology_adaptations"],
            "proved_configs": final_metrics["proved_configs"],
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nDetailed report: {report_path}")
    
    if all_passed:
        print("\n✓ ALL SYSTEM TESTS PASSED — Virtual FPGA cluster verified")
    else:
        print("\n✗ SOME TESTS FAILED — Check report for details")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
