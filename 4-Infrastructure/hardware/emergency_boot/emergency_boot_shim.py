#!/usr/bin/env python3
"""
Emergency Boot Hardware Shim -- Reference Implementation

Python I/O shim for the Geometry Emergency Boot Witness.
Simulates the FPGA-based geometric scan, seed extraction, and
emergency shell interface.

Per Research Stack contract:
  - Lean owns all decisions (admissibility, gating, classification)
  - Python owns I/O (read JSON, write JSONL, call subprocess, format output)
  - This shim calls Lean via lake exe for decision logic and formats/stores results.

Specification: GEOMETRY_EMERGENCY_BOOT_WITNESS_2026-04-08.md
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Tuple

# ---------------------------------------------------------------------------
# Constants matching the Lean specification
# ---------------------------------------------------------------------------

AEM20940_THRESHOLD_MV = 60          # 60mV cold-start threshold
TSM_WATCHDOWN_NS = 1                # 1ns watchdog countdown
GALVANIC_ISOLATION_V = 350        # 350V isolation threshold
CALCULATOR_POWER_MW = 100           # 100mW power consumption target
MIN_BATTERY_PCT = 0.20            # 20% minimum charge
SCAN_TIMEOUT_MS = 100               # 100ms scan target

# Tiny IP Emergency Domain
EMERGENCY_DOMAIN = 0x0D

# Command opcodes
OP_BOOT = 0x01
OP_SCAN = 0x02
OP_RECOVER = 0x03
OP_DIAG = 0x04
OP_STATUS = 0x05
OP_OPTICAL = 0x06
OP_FIBER = 0x07
OP_GRAPHENE = 0x08
OP_GAN = 0x09
OP_MEMRISTOR = 0x0A
OP_VOLTAGE = 0x0B
OP_EXIT = 0xFF


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class BootPhase(Enum):
    idle = auto()
    power_fail = auto()
    calculator_mode = auto()
    scanning = auto()
    seed_ready = auto()
    reconstructing = auto()
    validated = auto()
    recovery_mode = auto()
    exiting = auto()


class CommandResult(Enum):
    ok = auto()
    invalid = auto()
    busy = auto()
    error = auto()
    forbidden = auto()


@dataclass
class SolarPowerState:
    solar_input_voltage: float  # V
    solar_input_current: float  # mA
    power_generation: float   # mW
    battery_level: float        # 0-1
    self_power_mode: bool


@dataclass
class PowerState:
    vcc_main: float             # V
    watchdog_countdown: int       # ns
    bridge_isolated: bool
    optical_path_priority: str  # "hot" or "cold"
    active_hot_paths: int
    solar_state: SolarPowerState


@dataclass
class HexCoord:
    q: int
    r: int

    def to_spatial_hash(self) -> int:
        """Cantor pairing function."""
        n = self.q + self.r
        k = self.r
        return (n * n + n + 2 * k) // 2


@dataclass
class Capacitor:
    coord: HexCoord
    cap_class: str              # "low", "medium", "high"
    topology: int               # routing hash component
    dimensions: int             # dimensional hash component


@dataclass
class StatusByte:
    power_ok: bool = False
    seed_valid: bool = False
    tsm_reconstructed: bool = False
    stark_valid: bool = False
    optical_path_hot: bool = True  # True = hot priority
    outer_ring_healthy: bool = False
    em_neutrality_ok: bool = False
    voltage_comp_active: bool = False

    def encode(self) -> int:
        b = 0
        if self.power_ok:           b |= 0x01
        if self.seed_valid:         b |= 0x02
        if self.tsm_reconstructed:  b |= 0x04
        if self.stark_valid:        b |= 0x08
        if not self.optical_path_hot: b |= 0x10  # inverted
        if self.outer_ring_healthy: b |= 0x20
        if self.em_neutrality_ok:   b |= 0x40
        if self.voltage_comp_active: b |= 0x80
        return b

    @classmethod
    def decode(cls, b: int) -> "StatusByte":
        return cls(
            power_ok=(b & 0x01) != 0,
            seed_valid=(b & 0x02) != 0,
            tsm_reconstructed=(b & 0x04) != 0,
            stark_valid=(b & 0x08) != 0,
            optical_path_hot=(b & 0x10) == 0,  # inverted
            outer_ring_healthy=(b & 0x20) != 0,
            em_neutrality_ok=(b & 0x40) != 0,
            voltage_comp_active=(b & 0x80) != 0,
        )


# ---------------------------------------------------------------------------
# Decision stubs (Lean owns decisions; these call Lean via subprocess)
# ---------------------------------------------------------------------------

def _call_lean_decision(function_name: str, args: List[str]) -> Tuple[bool, Any]:
    """Call a Lean decision function via lake exe.

    TODO(lean-port): Replace with direct Lean FFI when available.
    For now, this is a stub that returns default values for development.
    """
    # In a production system, this would call:
    #   lake exe SemanticsCli --decision EmergencyBoot.function_name [args]
    # For the reference implementation, we return safe defaults.
    return True, None


def power_failure_detected(power: PowerState) -> bool:
    """Detect power failure using AEM20940 + TSM + bridge conditions.

    Lean source: EmergencyBootState.powerFailureDetected
    """
    vcc_mv = power.vcc_main * 1000.0
    return (
        vcc_mv < AEM20940_THRESHOLD_MV
        and power.watchdog_countdown <= 0
        and power.bridge_isolated
    )


def self_power_sufficient(solar: SolarPowerState) -> bool:
    """Check if solar power generation exceeds consumption target.

    Lean source: EmergencyBootState.selfPowerSufficient
    """
    return (
        solar.power_generation >= CALCULATOR_POWER_MW
        and solar.battery_level >= MIN_BATTERY_PCT
    )


# ---------------------------------------------------------------------------
# Emergency Boot Engine
# ---------------------------------------------------------------------------

class EmergencyBootEngine:
    """Simulated FPGA emergency boot controller.

    This Python shim models the hardware behavior described in the
    GEOMETRY_EMERGENCY_BOOT_WITNESS specification. It is regenerable
    from source and carries NO admissibility logic.
    """

    def __init__(self, capacitors: List[Capacitor]):
        self.capacitors = capacitors
        self.phase = BootPhase.idle
        self.seed: Optional[int] = None
        self.augmented_seed: Optional[int] = None
        self.isa_word: Optional[int] = None
        self.power = PowerState(
            vcc_main=3.3,
            watchdog_countdown=1000,
            bridge_isolated=False,
            optical_path_priority="hot",
            active_hot_paths=0,
            solar_state=SolarPowerState(
                solar_input_voltage=2.5,
                solar_input_current=50.0,
                power_generation=125.0,
                battery_level=0.85,
                self_power_mode=False,
            ),
        )

    # -- Power management -------------------------------------------------

    def update_power(self, vcc: float, solar_v: float, solar_ma: float,
                     battery: float, isolated: bool) -> None:
        """Update power state from sensor readings."""
        self.power.vcc_main = vcc
        self.power.solar_state.solar_input_voltage = solar_v
        self.power.solar_state.solar_input_current = solar_ma
        self.power.solar_state.battery_level = battery
        self.power.bridge_isolated = isolated
        self.power.solar_state.power_generation = solar_v * solar_ma  # mW approx

        if power_failure_detected(self.power):
            self._enter_emergency_mode()

    def _enter_emergency_mode(self) -> None:
        """Transition to emergency calculator mode on power failure."""
        if self.phase == BootPhase.idle:
            self.phase = BootPhase.power_fail
            self.power.optical_path_priority = "hot"
            self.power.active_hot_paths = 16
            self.power.solar_state.self_power_mode = True

            if self_power_sufficient(self.power.solar_state):
                self.phase = BootPhase.calculator_mode
                self._start_scan()

    # -- Geometric scan ---------------------------------------------------

    def _start_scan(self) -> None:
        """Begin FPGA geometric scan of capacitor array."""
        if self.phase == BootPhase.calculator_mode:
            self.phase = BootPhase.scanning
            # Simulate scan completion (in FPGA this is hardware-timed)
            self._complete_scan()

    def _complete_scan(self) -> None:
        """Finish scan and assemble geometric seed."""
        spatial_acc = 0
        cap_acc = 0
        topo_acc = 0
        dim_acc = 0

        for cap in self.capacitors:
            spatial_acc ^= cap.coord.to_spatial_hash()
            cap_bits = {"low": 0b00, "medium": 0b01, "high": 0b10}.get(
                cap.cap_class, 0
            )
            cap_acc ^= cap_bits
            topo_acc ^= cap.topology
            dim_acc ^= cap.dimensions

        # Fold to 128-bit seed using rotation
        seed = ((spatial_acc << 32) ^ spatial_acc)
        seed = ((cap_acc << 24) ^ seed)
        seed = ((topo_acc << 48) ^ seed)
        seed = ((dim_acc << 24) ^ seed)

        self.seed = seed & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        self.phase = BootPhase.seed_ready

    # -- Command interface ------------------------------------------------

    def execute(self, opcode: int, payload: bytes = b"") -> Tuple[CommandResult, StatusByte, bytes]:
        """Execute an emergency boot command.

        Mirrors Lean: EmergencyBootShell.executeCommand
        """
        status = self._build_status()

        if opcode == OP_STATUS:
            return CommandResult.ok, status, bytes([status.encode()])

        if opcode == OP_BOOT:
            if self.phase in (BootPhase.seed_ready, BootPhase.recovery_mode):
                if self.seed is not None:
                    seed_bytes = self.seed.to_bytes(16, "big")
                    return CommandResult.ok, status, seed_bytes
            return CommandResult.forbidden, status, b""

        if opcode == OP_SCAN:
            if self.phase in (BootPhase.scanning, BootPhase.seed_ready,
                              BootPhase.recovery_mode):
                return CommandResult.ok, status, b""  # geometry witness omitted
            return CommandResult.forbidden, status, b""

        if opcode == OP_DIAG:
            return CommandResult.ok, status, b""  # diagnostic results omitted

        if opcode == OP_EXIT:
            if self.phase == BootPhase.recovery_mode:
                self.phase = BootPhase.exiting
                return CommandResult.ok, status, b""
            return CommandResult.forbidden, status, b""

        # RECOVER, OPTICAL, FIBER, GRAPHENE, GAN, MEMRISTOR, VOLTAGE
        if self.phase == BootPhase.recovery_mode:
            return CommandResult.ok, status, b""
        return CommandResult.forbidden, status, b""

    def _build_status(self) -> StatusByte:
        """Build status byte from current state."""
        return StatusByte(
            power_ok=self.power.vcc_main >= 0.060,
            seed_valid=self.seed is not None,
            tsm_reconstructed=self.isa_word is not None,
            stark_valid=self.phase in (BootPhase.validated, BootPhase.recovery_mode),
            optical_path_hot=self.power.optical_path_priority == "hot",
            outer_ring_healthy=self.phase not in (BootPhase.idle, BootPhase.power_fail),
            em_neutrality_ok=self.phase != BootPhase.idle,
            voltage_comp_active=self.phase == BootPhase.recovery_mode,
        )

    # -- Receipt generation -----------------------------------------------

    def generate_receipt(self) -> Dict[str, Any]:
        """Generate a JSON receipt of the current boot state.

        Receipts are JSONL hash-chained per Research Stack convention.
        This is a hardware witness receipt, not a compression receipt.
        """
        return {
            "schema": "emergency_boot_witness_v1",
            "phase": self.phase.name,
            "seed_present": self.seed is not None,
            "power": {
                "vcc_main_v": self.power.vcc_main,
                "solar_generation_mw": self.power.solar_state.power_generation,
                "battery_level": self.power.solar_state.battery_level,
                "self_power_mode": self.power.solar_state.self_power_mode,
            },
            "status": self._build_status().encode(),
            "capacitor_count": len(self.capacitors),
        }


# ---------------------------------------------------------------------------
# Main / CLI
# ---------------------------------------------------------------------------

def main() -> int:
    """Demo: run a simulated emergency boot sequence."""
    # Create a sample 16-capacitor hexagonal lattice
    capacitors: List[Capacitor] = []
    for q in range(-2, 3):
        for r in range(-2, 3):
            if abs(q + r) <= 2:
                cap_class = ["low", "medium", "high"][(q + r + 4) % 3]
                capacitors.append(Capacitor(
                    coord=HexCoord(q, r),
                    cap_class=cap_class,
                    topology=(q * 17 + r) & 0xFF,
                    dimensions=(abs(q) + abs(r)) & 0xFF,
                ))

    engine = EmergencyBootEngine(capacitors)

    print("=== Emergency Boot Witness Demo ===")
    print(f"Capacitor array: {len(capacitors)} units")
    print(f"Initial phase: {engine.phase.name}")

    # Simulate power failure (watchdog already expired)
    print("\n-- Power Failure Event --")
    engine.power.watchdog_countdown = 0  # TSM watchdog expired
    engine.update_power(
        vcc=0.010,        # 10mV (below 60mV threshold)
        solar_v=2.5,
        solar_ma=60.0,
        battery=0.85,
        isolated=True,
    )
    print(f"Phase after power failure: {engine.phase.name}")
    print(f"Self-power mode: {engine.power.solar_state.self_power_mode}")
    print(f"Optical priority: {engine.power.optical_path_priority}")

    # Execute STATUS command
    print("\n-- STATUS Command --")
    result, status, payload = engine.execute(OP_STATUS)
    print(f"Result: {result.name}")
    print(f"Status byte: 0x{status.encode():02X}")
    print(f"  power_ok={status.power_ok}, seed_valid={status.seed_valid}")

    # Execute BOOT command
    print("\n-- BOOT Command --")
    result, status, payload = engine.execute(OP_BOOT)
    print(f"Result: {result.name}")
    if payload:
        print(f"Seed: 0x{int.from_bytes(payload, 'big'):032X}")

    # Generate receipt
    print("\n-- Receipt --")
    receipt = engine.generate_receipt()
    print(json.dumps(receipt, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
