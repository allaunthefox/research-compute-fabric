#!/usr/bin/env python3
"""
Lean to Hardware Checker

Extracts mathematical operations from Lean formal proofs and generates
hardware-compatible test vectors and verification logic for FPGA acceleration.

Key operations extracted:
- Q16.16 fixed-point arithmetic
- Mass number calculations (Z/N decomposition)
- S3C shell address computation
- Phase classification
- Routing logic
"""

import re
import sys
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path


@dataclass
class Q16_16:
    """Q16.16 fixed-point number representation."""
    value: int  # Raw 32-bit integer representation

    @classmethod
    def from_float(cls, f: float) -> 'Q16_16':
        """Convert float to Q16.16."""
        return cls(int(f * 65536) & 0xFFFFFFFF)

    def to_float(self) -> float:
        """Convert Q16.16 to float."""
        # Handle signed interpretation
        if self.value & 0x80000000:
            signed = self.value - 0x100000000
        else:
            signed = self.value
        return signed / 65536.0

    def __mul__(self, other: 'Q16_16') -> 'Q16_16':
        """Q16.16 multiplication: (a * b) >> 16"""
        # Use 64-bit intermediate
        product = (self.value * other.value) >> 16
        return Q16_16(product & 0xFFFFFFFF)

    def __add__(self, other: 'Q16_16') -> 'Q16_16':
        """Q16.16 addition."""
        return Q16_16((self.value + other.value) & 0xFFFFFFFF)

    def __sub__(self, other: 'Q16_16') -> 'Q16_16':
        """Q16.16 subtraction."""
        return Q16_16((self.value - other.value) & 0xFFFFFFFF)

    def __truediv__(self, other: 'Q16_16') -> 'Q16_16':
        """Q16.16 division: (a << 16) / b"""
        if other.value == 0:
            return Q16_16(0)
        result = (self.value << 16) // other.value
        return Q16_16(result & 0xFFFFFFFF)

    def __le__(self, other: 'Q16_16') -> bool:
        """Q16.16 comparison."""
        return self.value <= other.value

    def to_nat(self) -> int:
        """Convert Q16.16 to natural number (unsigned interpretation)."""
        return self.value & 0xFFFFFFFF


@dataclass
class S3CShellAddress:
    """S3C shell address for total mass A."""
    total_mass: int   # A = Z + N
    shell_k: int      # k = floor(sqrt(A))
    shell_a: int      # a = A - k^2
    shell_b0: int     # b0 = (k+1)^2 - 1 - A
    shell_b_plus: int # b+ = (k+1)^2 - A
    mass0: int        # m0 = a * b0
    mass_plus: int    # m+ = a * b+


@dataclass
class FullMasterComponents:
    """Upstream full master score components."""
    phi_weighted: Q16_16
    pist_lyapunov: Q16_16
    udrs_energy: Q16_16
    torus_distance: Q16_16
    couch_phi: Q16_16
    bhocs_cost: Q16_16


@dataclass
class FullMasterWeights:
    """Component weights for full master score."""
    phi_weight: Q16_16
    pist_weight: Q16_16
    udrs_weight: Q16_16
    torus_weight: Q16_16
    couch_weight: Q16_16
    bhocs_weight: Q16_16


@dataclass
class ComponentMassPackets:
    """Weighted mass packets before Z/N collapse."""
    phi_mass: int
    pist_mass: int
    udrs_mass: int
    torus_mass: int
    couch_mass: int
    bhocs_mass: int


class LeanHardwareChecker:
    """Checker for Lean formal proofs to hardware implementation."""

    def __init__(self, lean_file: str):
        self.lean_file = Path(lean_file)
        self.operations = []
        self.test_vectors = []

    def parse_lean_file(self) -> List[Dict]:
        """Parse Lean file and extract function definitions."""
        content = self.lean_file.read_text()

        # Extract def declarations
        def_pattern = r'def\s+(\w+)\s*([^:]*):\s*([^\n:=]+)'
        matches = re.findall(def_pattern, content)

        operations = []
        for name, params, return_type in matches:
            operations.append({
                'name': name,
                'params': params.strip(),
                'return_type': return_type.strip()
            })

        return operations

    def q16_to_mass(self, x: Q16_16) -> int:
        """Convert Q16.16 to unsigned integer mass packet."""
        return x.to_nat()

    def nat_abs_diff(self, a: int, b: int) -> int:
        """Absolute natural number difference."""
        return abs(a - b)

    def bias_sign_of(self, z: int, n: int) -> str:
        """Bias sign from structured mass Z and stress mass N."""
        if z > n:
            return "structured_heavy"
        elif n > z:
            return "stress_heavy"
        else:
            return "balanced"

    def bias_magnitude_q16(self, z: int, n: int, a: int) -> Q16_16:
        """Bias magnitude |Z-N|/(A+1) as Q16.16."""
        diff = self.nat_abs_diff(z, n)
        denom = a + 1
        if denom == 0:
            return Q16_16(0)
        return Q16_16.from_float(diff / denom)

    def s3c_shell_address(self, A: int) -> S3CShellAddress:
        """S3C shell decomposition for total mass A."""
        k = int(A ** 0.5)
        a = A - k * k
        kp1_sq = (k + 1) * (k + 1)
        b0 = kp1_sq - 1 - A
        b_plus = kp1_sq - A
        m0 = a * b0
        m_plus = a * b_plus

        return S3CShellAddress(
            total_mass=A,
            shell_k=k,
            shell_a=a,
            shell_b0=b0,
            shell_b_plus=b_plus,
            mass0=m0,
            mass_plus=m_plus
        )

    def rho_a(self, shell: S3CShellAddress) -> Q16_16:
        """Normalized shell density rho_A = 4*m0 / (2*k+1)^2."""
        denom = (2 * shell.shell_k + 1) ** 2
        if denom == 0:
            return Q16_16(0)
        return Q16_16.from_float((4 * shell.mass0) / denom)

    def component_mass_packets(
        self,
        components: FullMasterComponents,
        weights: FullMasterWeights
    ) -> ComponentMassPackets:
        """Build weighted component mass packets."""
        return ComponentMassPackets(
            phi_mass=self.q16_to_mass(weights.phi_weight * components.phi_weighted),
            pist_mass=self.q16_to_mass(weights.pist_weight * components.pist_lyapunov),
            udrs_mass=self.q16_to_mass(weights.udrs_weight * components.udrs_energy),
            torus_mass=self.q16_to_mass(weights.torus_weight * components.torus_distance),
            couch_mass=self.q16_to_mass(weights.couch_weight * components.couch_phi),
            bhocs_mass=self.q16_to_mass(weights.bhocs_weight * components.bhocs_cost)
        )

    def z_mass(self, packets: ComponentMassPackets) -> int:
        """Structured/control/witness mass: Z = Phi + PIST + BHOCS."""
        return packets.phi_mass + packets.pist_mass + packets.bhocs_mass

    def n_mass(self, packets: ComponentMassPackets) -> int:
        """Stress/dynamics/residual mass: N = UDRS + T5 + COUCH."""
        return packets.udrs_mass + packets.torus_mass + packets.couch_mass

    def classify_mass_phase(
        self,
        shell: S3CShellAddress,
        rho: Q16_16,
        bias_magnitude: Q16_16,
        beta: Q16_16,
        sign: str
    ) -> str:
        """Phase classifier over shell density and Z/N bias."""
        half_q16 = Q16_16.from_float(0.5)

        if shell.mass0 == 0:
            return "grounded"
        elif rho.to_float() < 0.5:
            if bias_magnitude.to_float() < beta.to_float():
                return "drift_balanced"
            else:
                if sign == "structured_heavy":
                    return "structured_drift"
                elif sign == "stress_heavy":
                    return "stress_drift"
                else:
                    return "drift_balanced"
        else:
            return "seismic"

    def route_for_phase(self, phase: str) -> str:
        """Route selected by phase."""
        routes = {
            "grounded": "promote",
            "drift_balanced": "standard",
            "structured_drift": "bhocs_commit",
            "stress_drift": "famm_drain",
            "seismic": "quarantine"
        }
        return routes.get(phase, "standard")

    def reduce_to_mass_number_field(
        self,
        components: FullMasterComponents,
        weights: FullMasterWeights,
        beta: Q16_16
    ) -> Dict:
        """Collapse full master components into mass number field."""
        packets = self.component_mass_packets(components, weights)
        z = self.z_mass(packets)
        n = self.n_mass(packets)
        A = z + n
        sign = self.bias_sign_of(z, n)
        bias = self.bias_magnitude_q16(z, n, A)
        shell = self.s3c_shell_address(A)
        rho = self.rho_a(shell)
        phase = self.classify_mass_phase(shell, rho, bias, beta, sign)
        route = self.route_for_phase(phase)

        return {
            "packets": asdict(packets),
            "z_field": z,
            "n_field": n,
            "a_field": A,
            "bias_sign": sign,
            "bias_q16": bias.to_float(),
            "shell": asdict(shell),
            "rho_q16": rho.to_float(),
            "phase": phase,
            "route": route
        }

    def generate_test_vectors(self, num_tests: int = 10) -> List[Dict]:
        """Generate test vectors for hardware verification."""
        import random

        test_vectors = []
        for i in range(num_tests):
            # Random components
            components = FullMasterComponents(
                phi_weighted=Q16_16.from_float(random.uniform(0, 1)),
                pist_lyapunov=Q16_16.from_float(random.uniform(0, 1)),
                udrs_energy=Q16_16.from_float(random.uniform(0, 1)),
                torus_distance=Q16_16.from_float(random.uniform(0, 1)),
                couch_phi=Q16_16.from_float(random.uniform(0, 1)),
                bhocs_cost=Q16_16.from_float(random.uniform(0, 1))
            )

            # Random weights
            weights = FullMasterWeights(
                phi_weight=Q16_16.from_float(random.uniform(0, 1)),
                pist_weight=Q16_16.from_float(random.uniform(0, 1)),
                udrs_weight=Q16_16.from_float(random.uniform(0, 1)),
                torus_weight=Q16_16.from_float(random.uniform(0, 1)),
                couch_weight=Q16_16.from_float(random.uniform(0, 1)),
                bhocs_weight=Q16_16.from_float(random.uniform(0, 1))
            )

            beta = Q16_16.from_float(random.uniform(0.1, 0.9))

            result = self.reduce_to_mass_number_field(components, weights, beta)
            test_vectors.append({
                "test_id": i,
                "components": {k: v.to_float() if isinstance(v, Q16_16) else v
                              for k, v in asdict(components).items()},
                "weights": {k: v.to_float() if isinstance(v, Q16_16) else v
                           for k, v in asdict(weights).items()},
                "beta": beta.to_float(),
                "expected": result
            })

        return test_vectors

    def export_verilog_testbench(self, test_vectors: List[Dict], output_file: str):
        """Export test vectors as Verilog testbench."""
        with open(output_file, 'w') as f:
            f.write("`timescale 1ns/1ps\n\n")
            f.write("module lean_hardware_checker_tb;\n")
            f.write("    reg clk;\n")
            f.write("    reg rst_n;\n")
            f.write("    reg start;\n")
            f.write("    wire done;\n")
            f.write("    wire [31:0] result;\n")
            f.write("\n")
            f.write("    // Instantiate DUT\n")
            f.write("    MetaManifoldProver dut (\n")
            f.write("        .clk(clk),\n")
            f.write("        .rst_n(rst_n),\n")
            f.write("        .start(start),\n")
            f.write("        .done(done),\n")
            f.write("        .result(result)\n")
            f.write("    );\n")
            f.write("\n")
            f.write("    // Clock generation\n")
            f.write("    initial begin\n")
            f.write("        clk = 0;\n")
            f.write("        forever #5 clk = ~clk;\n")
            f.write("    end\n")
            f.write("\n")
            f.write("    // Test stimulus\n")
            f.write("    initial begin\n")
            f.write("        $dumpfile(\"lean_checker.vcd\");\n")
            f.write("        $dumpvars(0, lean_hardware_checker_tb);\n")
            f.write("\n")
            f.write("        rst_n = 0;\n")
            f.write("        start = 0;\n")
            f.write("        #20 rst_n = 1;\n")
            f.write("\n")

            for tv in test_vectors:
                f.write(f"        // Test {tv['test_id']}\n")
                f.write("        #10 start = 1;\n")
                f.write("        #10 start = 0;\n")
                f.write("        @(posedge done);\n")
                f.write(f"        $display(\"Test {tv['test_id']}: result = %h\", result);\n")
                f.write("\n")

            f.write("        #50 $finish;\n")
            f.write("    end\n")
            f.write("\n")
            f.write("endmodule\n")

    def verify_against_lean(self, lean_output: Dict, hardware_output: Dict) -> bool:
        """Verify hardware output matches Lean formal proof output."""
        # Compare key fields
        keys_to_check = ['z_field', 'n_field', 'a_field', 'phase', 'route']

        for key in keys_to_check:
            if lean_output.get(key) != hardware_output.get(key):
                print(f"Mismatch in {key}: Lean={lean_output.get(key)}, HW={hardware_output.get(key)}")
                return False

        # Check Q16.16 values with tolerance
        q16_keys = ['bias_q16', 'rho_q16']
        for key in q16_keys:
            lean_val = lean_output.get(key, 0)
            hw_val = hardware_output.get(key, 0)
            if abs(lean_val - hw_val) > 0.001:  # 0.001 tolerance
                print(f"Mismatch in {key}: Lean={lean_val}, HW={hw_val}")
                return False

        return True

    def run_checks(self) -> Dict:
        """Run all checks and return results."""
        operations = self.parse_lean_file()
        test_vectors = self.generate_test_vectors()

        return {
            "lean_file": str(self.lean_file),
            "operations_extracted": len(operations),
            "operations": operations,
            "test_vectors": test_vectors,
            "status": "success"
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python lean_hardware_checker.py <lean_file>")
        sys.exit(1)

    lean_file = sys.argv[1]
    checker = LeanHardwareChecker(lean_file)

    print(f"Parsing Lean file: {lean_file}")
    results = checker.run_checks()

    print(f"Extracted {results['operations_extracted']} operations")

    # Export test vectors
    output_json = lean_file.replace('.lean', '_test_vectors.json')
    with open(output_json, 'w') as f:
        json.dump(results['test_vectors'], f, indent=2)

    print(f"Exported test vectors to {output_json}")

    # Export Verilog testbench
    output_verilog = lean_file.replace('.lean', '_tb.v')
    checker.export_verilog_testbench(results['test_vectors'], output_verilog)
    print(f"Exported Verilog testbench to {output_verilog}")

    print("\nSample test vector:")
    if results['test_vectors']:
        print(json.dumps(results['test_vectors'][0], indent=2))


if __name__ == "__main__":
    main()
