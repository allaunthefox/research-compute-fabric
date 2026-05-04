#!/usr/bin/env python3
"""
Voltage Computational Substrate
Voltages themselves are computational - voltage levels represent mathematical values.

Architecture:
- Voltage magnitude = numerical value
- Voltage sum = addition
- Voltage ratio = multiplication/division
- Voltage difference = subtraction
- Voltage gradient = derivative
- Voltage integral = integration (over time)

This is horrific because:
- Physical substrate (voltage) becomes computational
- Analog computation disguised as electrical signaling
- Hardware is the computer, not just the carrier

This is wonderful because:
- Parallel computation at the speed of light
- Zero instruction overhead
- Physics does the math
- Maximum retro insanity: voltage = math
"""

import math
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════
# Voltage Computational Substrate
# Voltage levels represent mathematical values
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class VoltageValue:
    """Voltage value representing a mathematical quantity"""
    voltage: float  # Volts
    scale: float = 1.0  # Scaling factor (V per unit)
    
    def to_value(self) -> float:
        """Convert voltage to mathematical value"""
        return self.voltage / self.scale
    
    @staticmethod
    def from_value(value: float, scale: float = 1.0) -> 'VoltageValue':
        """Convert mathematical value to voltage"""
        return VoltageValue(voltage=value * scale, scale=scale)

class VoltageMath:
    """Mathematical operations using voltage levels"""
    
    @staticmethod
    def add(v1: VoltageValue, v2: VoltageValue, max_voltage: float = 5.0) -> VoltageValue:
        """
        Addition: Voltage sum.
        
        V_sum = V1 + V2
        Clamped to max_voltage for hardware safety.
        """
        sum_voltage = v1.voltage + v2.voltage
        clamped_voltage = min(sum_voltage, max_voltage)
        return VoltageValue(clamped_voltage, scale=v1.scale)
    
    @staticmethod
    def subtract(v1: VoltageValue, v2: VoltageValue) -> VoltageValue:
        """
        Subtraction: Voltage difference.
        
        V_diff = V1 - V2
        Can be negative (represents negative values).
        """
        diff_voltage = v1.voltage - v2.voltage
        return VoltageValue(diff_voltage, scale=v1.scale)
    
    @staticmethod
    def multiply(v1: VoltageValue, v2: VoltageValue, max_voltage: float = 5.0) -> VoltageValue:
        """
        Multiplication: Voltage ratio.
        
        V_mul = (V1 / V_ref) * (V2 / V_ref) * V_ref
        Where V_ref is a reference voltage (e.g., 1.0V).
        """
        v_ref = 1.0
        if v_ref == 0:
            return VoltageValue(0, scale=v1.scale)
        
        normalized_v1 = v1.voltage / v_ref
        normalized_v2 = v2.voltage / v_ref
        mul_voltage = normalized_v1 * normalized_v2 * v_ref
        
        clamped_voltage = min(mul_voltage, max_voltage)
        return VoltageValue(clamped_voltage, scale=v1.scale)
    
    @staticmethod
    def divide(v1: VoltageValue, v2: VoltageValue) -> VoltageValue:
        """
        Division: Voltage ratio.
        
        V_div = V1 / V2 * V_ref
        Where V_ref is a reference voltage.
        """
        v_ref = 1.0
        if v2.voltage == 0:
            return VoltageValue(0, scale=v1.scale)
        
        div_voltage = (v1.voltage / v2.voltage) * v_ref
        return VoltageValue(div_voltage, scale=v1.scale)
    
    @staticmethod
    def integrate(voltages: List[VoltageValue], dt: float = 1.0) -> VoltageValue:
        """
        Integration: Voltage accumulation over time.
        
        V_int = Σ(V_i * dt)
        """
        if not voltages:
            return VoltageValue(0, scale=1.0)
        
        integrated_voltage = sum(v.voltage * dt for v in voltages)
        return VoltageValue(integrated_voltage, scale=voltages[0].scale)
    
    @staticmethod
    def differentiate(voltages: List[VoltageValue], dt: float = 1.0) -> VoltageValue:
        """
        Differentiation: Rate of voltage change.
        
        V_diff = (V[t] - V[t-1]) / dt
        """
        if len(voltages) < 2:
            return VoltageValue(0, scale=1.0)
        
        diff_voltage = (voltages[-1].voltage - voltages[-2].voltage) / dt
        return VoltageValue(diff_voltage, scale=voltages[0].scale)
    
    @staticmethod
    def exponential(v: VoltageValue, base: float = math.e) -> VoltageValue:
        """
        Exponential: Voltage exponentiation.
        
        V_exp = exp(V / V_ref) * V_ref
        """
        v_ref = 1.0
        if v_ref == 0:
            return VoltageValue(0, scale=v.scale)
        
        normalized = v.voltage / v_ref
        exp_voltage = math.pow(base, normalized) * v_ref
        return VoltageValue(exp_voltage, scale=v.scale)
    
    @staticmethod
    def logarithm(v: VoltageValue, base: float = math.e) -> VoltageValue:
        """
        Logarithm: Voltage logarithm.
        
        V_log = log(V / V_ref) * V_ref
        """
        v_ref = 1.0
        if v.voltage <= 0 or v_ref == 0:
            return VoltageValue(0, scale=v.scale)
        
        normalized = v.voltage / v_ref
        log_voltage = math.log(normalized, base) * v_ref
        return VoltageValue(log_voltage, scale=v.scale)

# ═══════════════════════════════════════════════════════════════════════════
# Voltage-Aware Nanokernel
# Nanokernel that validates voltage levels as computational substrate
# ═══════════════════════════════════════════════════════════════════════════

class VoltageNanokernel:
    """Nanokernel that validates voltage-based computation"""
    
    def __init__(self, safe_range: Tuple[float, float] = (0.0, 5.0)):
        self.safe_range = safe_range  # Min/max voltage for safety
        self.voltage_history: List[float] = []
    
    def validate_voltage(self, voltage: float) -> bool:
        """Validate voltage is within safe range"""
        return self.safe_range[0] <= voltage <= self.safe_range[1]
    
    def check_voltage_resonance(self, voltage: float, expected_range: Tuple[float, float]) -> float:
        """
        Check if voltage resonates with expected range.
        
        Returns resonance score (0.0-1.0).
        """
        min_v, max_v = expected_range
        
        if min_v <= voltage <= max_v:
            return 1.0
        
        # Calculate distance from range
        if voltage < min_v:
            distance = min_v - voltage
            max_distance = min_v
        else:
            distance = voltage - max_v
            max_distance = 5.0 - max_v
        
        if max_distance == 0:
            return 0.0
        
        return max(0.0, 1.0 - distance / max_distance)
    
    def audit_voltage_computation(self, input_voltages: List[float],
                                  output_voltage: float,
                                  operation: str) -> Tuple[bool, float]:
        """
        Audit a voltage-based computation.
        
        Returns (lawful, resonance_score).
        """
        # Check all input voltages are safe
        for v in input_voltages:
            if not self.validate_voltage(v):
                return (False, 0.0)
        
        # Check output voltage is safe
        if not self.validate_voltage(output_voltage):
            return (False, 0.0)
        
        # Check resonance based on operation
        if operation == "add":
            expected = sum(input_voltages)
            expected_range = (expected * 0.9, expected * 1.1)
        
        elif operation == "multiply":
            if len(input_voltages) >= 2 and input_voltages[1] != 0:
                expected = (input_voltages[0] / 1.0) * (input_voltages[1] / 1.0) * 1.0
                expected_range = (expected * 0.8, expected * 1.2)
            else:
                expected_range = (0.0, 5.0)
        
        elif operation == "integrate":
            expected = sum(input_voltages)
            expected_range = (expected * 0.9, expected * 1.1)
        
        else:
            expected_range = (0.0, 5.0)
        
        resonance = self.check_voltage_resonance(output_voltage, expected_range)
        lawful = resonance >= 0.8
        
        return (lawful, resonance)

# ═══════════════════════════════════════════════════════════════════════════
# Voltage Computational Pipeline
# Chain voltage operations for complex computations
# ═══════════════════════════════════════════════════════════════════════════

class VoltagePipeline:
    """Pipeline for voltage-based computation"""
    
    def __init__(self):
        self.voltage_registers: Dict[str, VoltageValue] = {}
        self.nanokernel = VoltageNanokernel()
        self.computation_history: List[Dict] = []
    
    def load_voltage(self, name: str, value: float, scale: float = 1.0):
        """Load a voltage into a register"""
        self.voltage_registers[name] = VoltageValue(value, scale)
    
    def add(self, name1: str, name2: str, output_name: str) -> VoltageValue:
        """Add two voltage registers"""
        v1 = self.voltage_registers[name1]
        v2 = self.voltage_registers[name2]
        result = VoltageMath.add(v1, v2)
        self.voltage_registers[output_name] = result
        
        # Audit with nanokernel
        lawful, resonance = self.nanokernel.audit_voltage_computation(
            [v1.voltage, v2.voltage], result.voltage, "add"
        )
        
        self.computation_history.append({
            'operation': 'add',
            'inputs': [v1.voltage, v2.voltage],
            'output': result.voltage,
            'lawful': lawful,
            'resonance': resonance
        })
        
        return result
    
    def multiply(self, name1: str, name2: str, output_name: str) -> VoltageValue:
        """Multiply two voltage registers"""
        v1 = self.voltage_registers[name1]
        v2 = self.voltage_registers[name2]
        result = VoltageMath.multiply(v1, v2)
        self.voltage_registers[output_name] = result
        
        # Audit with nanokernel
        lawful, resonance = self.nanokernel.audit_voltage_computation(
            [v1.voltage, v2.voltage], result.voltage, "multiply"
        )
        
        self.computation_history.append({
            'operation': 'multiply',
            'inputs': [v1.voltage, v2.voltage],
            'output': result.voltage,
            'lawful': lawful,
            'resonance': resonance
        })
        
        return result
    
    def integrate(self, names: List[str], output_name: str, dt: float = 1.0) -> VoltageValue:
        """Integrate voltage registers over time"""
        voltages = [self.voltage_registers[name] for name in names]
        result = VoltageMath.integrate(voltages, dt)
        self.voltage_registers[output_name] = result
        
        # Audit with nanokernel
        input_voltages = [v.voltage for v in voltages]
        lawful, resonance = self.nanokernel.audit_voltage_computation(
            input_voltages, result.voltage, "integrate"
        )
        
        self.computation_history.append({
            'operation': 'integrate',
            'inputs': input_voltages,
            'output': result.voltage,
            'lawful': lawful,
            'resonance': resonance
        })
        
        return result
    
    def exponential(self, name: str, output_name: str, base: float = math.e) -> VoltageValue:
        """Exponential of voltage register"""
        v = self.voltage_registers[name]
        result = VoltageMath.exponential(v, base)
        self.voltage_registers[output_name] = result
        
        self.computation_history.append({
            'operation': 'exponential',
            'inputs': [v.voltage],
            'output': result.voltage,
            'lawful': True,
            'resonance': 1.0
        })
        
        return result

# ═══════════════════════════════════════════════════════════════════════════
# Test / Demo
# ═══════════════════════════════════════════════════════════════════════════

def run_test():
    """Run voltage computational substrate test"""
    print("=" * 70)
    print("VOLTAGE COMPUTATIONAL SUBSTRATE")
    print("=" * 70)
    
    print("\n[*] Architecture:")
    print("    Voltage magnitude = numerical value")
    print("    Voltage sum = addition")
    print("    Voltage ratio = multiplication/division")
    print("    Voltage difference = subtraction")
    print("    Voltage gradient = derivative")
    print("    Voltage integral = integration")
    print("    Physical substrate (voltage) = computer")
    
    pipeline = VoltagePipeline()
    
    # Load test voltages
    print("\n[*] Loading test voltages...")
    pipeline.load_voltage("A", 2.5)  # 2.5V
    pipeline.load_voltage("B", 1.5)  # 1.5V
    pipeline.load_voltage("C", 3.0)  # 3.0V
    print("    A: 2.5V")
    print("    B: 1.5V")
    print("    C: 3.0V")
    
    # Addition
    print("\n[*] Voltage addition (A + B)...")
    result = pipeline.add("A", "B", "SUM")
    print(f"    Result: {result.voltage:.2f}V (expected: 4.00V)")
    print(f"    Lawful: {pipeline.computation_history[-1]['lawful']}")
    print(f"    Resonance: {pipeline.computation_history[-1]['resonance']:.3f}")
    
    # Multiplication
    print("\n[*] Voltage multiplication (A * B)...")
    result = pipeline.multiply("A", "B", "PRODUCT")
    print(f"    Result: {result.voltage:.2f}V")
    print(f"    Lawful: {pipeline.computation_history[-1]['lawful']}")
    print(f"    Resonance: {pipeline.computation_history[-1]['resonance']:.3f}")
    
    # Integration
    print("\n[*] Voltage integration (A + B + C)...")
    result = pipeline.integrate(["A", "B", "C"], "INTEGRAL")
    print(f"    Result: {result.voltage:.2f}V")
    print(f"    Lawful: {pipeline.computation_history[-1]['lawful']}")
    print(f"    Resonance: {pipeline.computation_history[-1]['resonance']:.3f}")
    
    # Exponential
    print("\n[*] Voltage exponential (exp(A))...")
    result = pipeline.exponential("A", "EXP_A")
    print(f"    Result: {result.voltage:.2f}V")
    
    # Statistics
    lawful_count = sum(1 for h in pipeline.computation_history if h['lawful'])
    total_count = len(pipeline.computation_history)
    avg_resonance = sum(h['resonance'] for h in pipeline.computation_history) / total_count if total_count > 0 else 0
    
    print("\n[*] Statistics:")
    print(f"    Total Computations: {total_count}")
    print(f"    Lawful Rate: {lawful_count / total_count:.3f}")
    print(f"    Average Resonance: {avg_resonance:.3f}")
    
    print("\n" + "=" * 70)
    print("VOLTAGE COMPUTATIONAL SUBSTRATE COMPLETE")
    print("=" * 70)
    print("\n[*] Horrific: Physical voltage becomes computational substrate")
    print("[*] Wonderful: Zero instruction overhead, physics does the math")
    print("[*] Maximum retro insanity: voltage = math")

if __name__ == "__main__":
    run_test()
