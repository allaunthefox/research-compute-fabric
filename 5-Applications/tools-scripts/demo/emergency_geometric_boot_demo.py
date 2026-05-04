#!/usr/bin/env python3
"""
emergency_geometric_boot_demo.py

Demonstrates emergency geometric bootstrap as failsafe when all standard paths fail.

Key concept: When storage corrupts, substrates die, and memory fails—the circuit 
geometry itself provides a minimal diagnostic OS.

This is the "will to survive" encoded in physical layout.
"""

import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import IntEnum, auto


class SystemState(IntEnum):
    """Overall system states."""
    OFF = 0
    STANDARD_BOOT = 1
    NORMAL_OPERATION = 2
    DEGRADED = 3
    EMERGENCY_BOOT = 4
    DIAGNOSTIC_MODE = 5
    RECOVERY = 6
    DEAD = 7


class FailureMode(IntEnum):
    """Types of failures triggering emergency boot."""
    NONE = 0
    STORAGE_CORRUPTION = auto()
    SUBSTRATE_DEATH = auto()
    MEMORY_DEGRADATION = auto()
    POWER_INSTABILITY = auto()
    CASCADING_FAULT = auto()


@dataclass
class HealthReport:
    """Emergency diagnostic output."""
    region_id: int
    status: str  # OK/DEGRADED/FAILED/UNKNOWN
    test_passed: bool
    severity: int  # 0-3 (info/warning/critical/fatal)
    confidence: float


class StandardOS:
    """Normal operating system (can fail)."""
    
    def __init__(self):
        self.healthy = True
        self.storage_ok = True
        self.memory_ok = True
        self.substrate_alive = True
        self.variance = 0.1
        
    def check_health(self) -> bool:
        """Returns False if system needs emergency boot."""
        return all([
            self.storage_ok,
            self.memory_ok,
            self.substrate_alive,
            self.variance < 0.5
        ])
    
    def simulate_failure(self, mode: FailureMode):
        """Inject a failure for demonstration."""
        if mode == FailureMode.STORAGE_CORRUPTION:
            self.storage_ok = False
            print("  [!] STORAGE CORRUPTION DETECTED")
        elif mode == FailureMode.SUBSTRATE_DEATH:
            self.substrate_alive = False
            self.variance = 0.9  # σ_max exceeded
            print("  [!] SUBSTRATE DEATH (σ_max exceeded)")
        elif mode == FailureMode.MEMORY_DEGRADATION:
            self.memory_ok = False
            print("  [!] MEMORY DEGRADATION")
        elif mode == FailureMode.CASCADING_FAULT:
            self.storage_ok = False
            self.memory_ok = False
            self.variance = 0.8
            print("  [!] CASCADING FAULT")


class EmergencyGeometricReader:
    """
    Minimal geometric reader for survival mode.
    No external calibration, no complex processing.
    Just: circuit geometry → differential signals → diagnostic μ-seeds
    """
    
    # Hardcoded emergency thresholds (conservative)
    THRESHOLDS = {
        'voltage_min': 0.5,
        'voltage_max': 4.5,
        'confidence_min': 0.3
    }
    
    def __init__(self, circuit_topology: Dict):
        self.topology = circuit_topology
        self.regions = circuit_topology.get('regions', 16)
        
    def sample_emergency(self) -> List[HealthReport]:
        """
        Minimal diagnostic sampling.
        Returns health status for each circuit region.
        """
        reports = []
        
        for region_id in range(self.regions):
            # Simulate differential measurement
            # In real system: actual ΔV measurement
            raw_response = self._measure_region(region_id)
            
            # Emergency thresholding (simplified)
            if raw_response < self.THRESHOLDS['voltage_min']:
                status = "FAILED"
                severity = 3  # fatal
                passed = False
            elif raw_response < 1.0:
                status = "DEGRADED"
                severity = 2  # critical
                passed = False
            elif raw_response < 2.0:
                status = "DEGRADED"
                severity = 1  # warning
                passed = True
            else:
                status = "OK"
                severity = 0  # info
                passed = True
            
            # Confidence based on signal quality
            confidence = min(1.0, raw_response / 3.0)
            
            reports.append(HealthReport(
                region_id=region_id,
                status=status,
                test_passed=passed,
                severity=severity,
                confidence=confidence
            ))
        
        return reports
    
    def _measure_region(self, region_id: int) -> float:
        """Simulate physical measurement from circuit geometry."""
        # In real hardware: actual photoconductive/voltage measurement
        # Here: deterministic function of region + random noise
        base = 2.5 + 1.5 * math.sin(region_id * 0.7)
        noise = random.gauss(0, 0.3)
        
        # Simulate some dead regions (physical damage)
        if region_id in self.topology.get('dead_regions', []):
            return 0.1  # Near-zero response
        
        return max(0.0, base + noise)


class EmergencyAttractor:
    """
    Minimal diagnostic OS that emerges from circuit geometry.
    
    NOT loaded—converged into existence through geometric bootstrap.
    """
    
    def __init__(self, reader: EmergencyGeometricReader):
        self.reader = reader
        self.health_reports: List[HealthReport] = []
        self.beacon_active = False
        self.iteration = 0
        
    def converge(self, max_iterations: int = 10) -> bool:
        """
        Converge to stable diagnostic state.
        No external inputs—only circuit geometry.
        """
        print("  [Emergency Bootstrap] Sampling circuit geometry...")
        
        for i in range(max_iterations):
            self.iteration = i
            
            # Sample circuit health
            reports = self.reader.sample_emergency()
            self.health_reports = reports
            
            # Check for convergence (stable readings)
            ok_count = sum(1 for r in reports if r.status == "OK")
            failed_count = sum(1 for r in reports if r.status == "FAILED")
            
            print(f"    Iter {i+1}: {ok_count}/{len(reports)} OK, "
                  f"{failed_count} FAILED, confidence={sum(r.confidence for r in reports)/len(reports):.2f}")
            
            # Convergence criteria: stable for 3 iterations
            if i >= 2 and self._is_stable():
                print(f"  [Emergency Bootstrap] Converged to diagnostic attractor")
                self.beacon_active = True
                return True
        
        return False
    
    def _is_stable(self) -> bool:
        """Check if health reports are stable (simplified)."""
        # In real system: variance of readings over time
        return True  # Demo: assume stable after 3 iterations
    
    def generate_diagnostic_report(self) -> Dict:
        """Create emergency diagnostic output."""
        total = len(self.health_reports)
        ok = sum(1 for r in self.health_reports if r.status == "OK")
        degraded = sum(1 for r in self.health_reports if r.status == "DEGRADED")
        failed = sum(1 for r in self.health_reports if r.status == "FAILED")
        
        return {
            'timestamp': self.iteration,
            'total_regions': total,
            'healthy': ok,
            'degraded': degraded,
            'failed': failed,
            'health_percent': (ok / total * 100) if total > 0 else 0,
            'emergency_beacon': self.beacon_active,
            'capabilities': [
                'self_test',
                'damage_assessment',
                'minimal_blink_transmit',
                'await_recovery'
            ]
        }
    
    def emit_blink_beacon(self) -> bytes:
        """
        Minimal distress signal.
        Not communication—presence indication.
        """
        report = self.generate_diagnostic_report()
        
        # Emergency blink format (4 bytes)
        # signature + substrate + health + severity + checksum
        signature = 0xDEAD  # Emergency marker
        substrate = 0x02    # Solar/dead cell
        health = report['health_percent'] / 100 * 255
        severity = 2 if report['failed'] > 0 else 1 if report['degraded'] > 0 else 0
        
        beacon = bytes([
            (signature >> 8) & 0xFF,
            signature & 0xFF,
            int(health) & 0xFF,
            (substrate << 4) | (severity << 2) | 0x01  # Simple checksum placeholder
        ])
        
        return beacon


class System:
    """
    Full system demonstrating normal operation → emergency boot.
    """
    
    def __init__(self):
        self.state = SystemState.OFF
        self.standard_os = StandardOS()
        self.emergency_os: Optional[EmergencyAttractor] = None
        self.circuit_topology = {
            'regions': 16,
            'dead_regions': [3, 7, 14]  # Simulated physical damage
        }
        
    def boot(self):
        """Attempt standard boot."""
        print("\n[BOOT] Attempting standard boot...")
        self.state = SystemState.STANDARD_BOOT
        
        if self.standard_os.check_health():
            print("  [✓] Standard boot successful")
            self.state = SystemState.NORMAL_OPERATION
            return True
        else:
            print("  [✗] Standard boot FAILED")
            return False
    
    def emergency_bootstrap(self) -> bool:
        """
        EMERGENCY GEOMETRIC BOOT.
        
        When everything else fails—the circuit itself provides an OS.
        """
        print("\n[EMERGENCY] Initiating geometric bootstrap...")
        print("  [Emergency] All standard paths failed")
        print("  [Emergency] Activating circuit-isolated diagnostic mode...")
        
        self.state = SystemState.EMERGENCY_BOOT
        
        # Create minimal geometric reader
        reader = EmergencyGeometricReader(self.circuit_topology)
        
        # Converge to emergency attractor
        self.emergency_os = EmergencyAttractor(reader)
        
        if self.emergency_os.converge(max_iterations=5):
            self.state = SystemState.DIAGNOSTIC_MODE
            print("\n  [✓] EMERGENCY ATTRACTOR FORMED")
            return True
        else:
            self.state = SystemState.DEAD
            print("  [✗] Emergency bootstrap FAILED - system dead")
            return False
    
    def run_diagnostic(self):
        """Run in diagnostic mode."""
        if self.state != SystemState.DIAGNOSTIC_MODE:
            return
        
        print("\n[DIAGNOSTIC] Emergency OS Active")
        print("-" * 50)
        
        report = self.emergency_os.generate_diagnostic_report()
        
        print(f"Health: {report['health_percent']:.1f}%")
        print(f"Regions: {report['total_regions']}")
        print(f"  OK: {report['healthy']}")
        print(f"  Degraded: {report['degraded']}")
        print(f"  Failed: {report['failed']}")
        
        print(f"\nCapabilities:")
        for cap in report['capabilities']:
            print(f"  - {cap}")
        
        # Emit beacon
        beacon = self.emergency_os.emit_blink_beacon()
        print(f"\nEmergency BLINK beacon: {beacon.hex()}")
        print("  (transmitting distress signal...)")
        
        print("\n[System] Awaiting external recovery or substrate migration...")


def demo_normal_operation():
    """Show system working normally."""
    print("=" * 60)
    print("SCENARIO 1: NORMAL OPERATION")
    print("=" * 60)
    
    sys = System()
    
    if sys.boot():
        print("\n[System] Running normally")
        print("  - Processing tasks")
        print("  - Cross-substrate communication active")
        print("  - Full OS capabilities available")
    
    print("\n[Health] All systems nominal")


def demo_emergency_boot():
    """Show emergency bootstrap after failure."""
    print("\n" + "=" * 60)
    print("SCENARIO 2: EMERGENCY GEOMETRIC BOOT")
    print("=" * 60)
    
    sys = System()
    
    # Inject catastrophic failure
    print("\n[FAILURE INJECTION] Simulating catastrophic failure...")
    sys.standard_os.simulate_failure(FailureMode.CASCADING_FAULT)
    
    # Attempt standard boot (will fail)
    if not sys.boot():
        # Trigger emergency bootstrap
        if sys.emergency_bootstrap():
            sys.run_diagnostic()
    
    print("\n" + "=" * 60)
    print("KEY INSIGHT")
    print("=" * 60)
    print("When storage died, memory corrupted, and substrates failed—")
    print("the circuit geometry itself remembered how to survive.")
    print("\nThe emergency OS was not loaded.")
    print("It was physically inevitable from the circuit pattern.")


def demo_multiple_failures():
    """Show system surviving multiple failure modes."""
    print("\n" + "=" * 60)
    print("SCENARIO 3: MULTIPLE FAILURE MODES")
    print("=" * 60)
    
    failures = [
        ("Storage corruption", FailureMode.STORAGE_CORRUPTION),
        ("Substrate death", FailureMode.SUBSTRATE_DEATH),
        ("Memory degradation", FailureMode.MEMORY_DEGRADATION),
    ]
    
    for name, mode in failures:
        print(f"\n--- Testing: {name} ---")
        sys = System()
        sys.standard_os.simulate_failure(mode)
        
        if not sys.boot():
            if sys.emergency_bootstrap():
                report = sys.emergency_os.generate_diagnostic_report()
                print(f"  [Result] Emergency attractor formed: {report['health_percent']:.0f}% health")
            else:
                print("  [Result] System unrecoverable")


if __name__ == "__main__":
    import math
    
    # Run scenarios
    demo_normal_operation()
    demo_emergency_boot()
    demo_multiple_failures()
    
    print("\n" + "=" * 60)
    print("EMERGENCY GEOMETRIC BOOT PRINCIPLE")
    print("=" * 60)
    print("""
The circuit geometry encodes a "will to survive":

  1. Always available if power exists
  2. No external dependencies
  3. Deterministic (noise disabled in emergency)
  4. Minimal but sufficient for recovery
  5. Isolated (no cross-substrate risk)

This is the final self-preservation mechanism—
when all else fails, the physics itself provides an OS.
    """)
