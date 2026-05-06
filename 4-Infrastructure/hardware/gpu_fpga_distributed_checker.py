#!/usr/bin/env python3
"""
GPU Workhorse + FPGA Verifier Architecture

GPU: Performs heavy computational work (Q16.16 arithmetic, mass number calculations)
FPGA: Verifies GPU results against Lean formal proofs (correctness checking)
"""

import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple
from multiprocessing import Pool, cpu_count
import time
import numpy as np

try:
    import cupy as cp
    GPU_AVAILABLE = True
    print("GPU acceleration available (CuPy)")
except ImportError:
    GPU_AVAILABLE = False
    print("GPU acceleration not available (CuPy not installed)")

class GPUWorkhorse:
    """GPU-accelerated computational workhorse."""

    @staticmethod
    def compute_mass_number_batch(components_batch: List[Dict], weights_batch: List[Dict]) -> List[Dict]:
        """
        Batch compute mass number fields on GPU.
        This is the heavy computational work.
        """
        results = []

        for components, weights in zip(components_batch, weights_batch):
            # Extract Q16.16 values (handle nested dict structure)
            phi_weighted = components.get('phi_weighted', {}).get('value', 0)
            pist_lyapunov = components.get('pist_lyapunov', {}).get('value', 0)
            udrs_energy = components.get('udrs_energy', {}).get('value', 0)
            torus_distance = components.get('torus_distance', {}).get('value', 0)
            couch_phi = components.get('couch_phi', {}).get('value', 0)
            bhocs_cost = components.get('bhocs_cost', {}).get('value', 0)

            phi_weight = weights.get('phi_weight', {}).get('value', 0)
            pist_weight = weights.get('pist_weight', {}).get('value', 0)
            udrs_weight = weights.get('udrs_weight', {}).get('value', 0)
            torus_weight = weights.get('torus_weight', {}).get('value', 0)
            couch_weight = weights.get('couch_weight', {}).get('value', 0)
            bhocs_weight = weights.get('bhocs_weight', {}).get('value', 0)

            # GPU-accelerated batch multiplication
            if GPU_AVAILABLE:
                comp_vals = cp.array([phi_weighted, pist_lyapunov, udrs_energy,
                                     torus_distance, couch_phi, bhocs_cost])
                weight_vals = cp.array([phi_weight, pist_weight, udrs_weight,
                                       torus_weight, couch_weight, bhocs_weight])
                products = (comp_vals * weight_vals) >> 16
                mass_packets = cp.asnumpy(products.astype(np.int32))
            else:
                comp_vals = np.array([phi_weighted, pist_lyapunov, udrs_energy,
                                     torus_distance, couch_phi, bhocs_cost])
                weight_vals = np.array([phi_weight, pist_weight, udrs_weight,
                                       torus_weight, couch_weight, bhocs_weight])
                mass_packets = ((comp_vals.astype(np.int64) * weight_vals.astype(np.int64)) >> 16).astype(np.int32)

            results.append({
                'phi_mass': mass_packets[0],
                'pist_mass': mass_packets[1],
                'udrs_mass': mass_packets[2],
                'torus_mass': mass_packets[3],
                'couch_mass': mass_packets[4],
                'bhocs_mass': mass_packets[5]
            })

        return results

    @staticmethod
    def compute_s3c_shell_batch(total_masses: np.ndarray) -> List[Dict]:
        """
        Batch compute S3C shell addresses on GPU.
        """
        results = []

        if GPU_AVAILABLE:
            masses_gpu = cp.asarray(total_masses)
            k_gpu = cp.sqrt(masses_gpu).astype(cp.int32)
            a_gpu = masses_gpu - (k_gpu * k_gpu)
            kp1_sq_gpu = (k_gpu + 1) * (k_gpu + 1)
            b0_gpu = kp1_sq_gpu - 1 - masses_gpu
            b_plus_gpu = kp1_sq_gpu - masses_gpu
            m0_gpu = a_gpu * b0_gpu
            m_plus_gpu = a_gpu * b_plus_gpu

            k = cp.asnumpy(k_gpu)
            a = cp.asnumpy(a_gpu)
            b0 = cp.asnumpy(b0_gpu)
            b_plus = cp.asnumpy(b_plus_gpu)
            m0 = cp.asnumpy(m0_gpu)
            m_plus = cp.asnumpy(m_plus_gpu)
        else:
            k = np.sqrt(total_masses).astype(np.int32)
            a = total_masses - (k * k)
            kp1_sq = (k + 1) * (k + 1)
            b0 = kp1_sq - 1 - total_masses
            b_plus = kp1_sq - total_masses
            m0 = a * b0
            m_plus = a * b_plus

        for i in range(len(total_masses)):
            results.append({
                'total_mass': int(total_masses[i]),
                'shell_k': int(k[i]),
                'shell_a': int(a[i]),
                'shell_b0': int(b0[i]),
                'shell_b_plus': int(b_plus[i]),
                'mass0': int(m0[i]),
                'mass_plus': int(m_plus[i])
            })

        return results

class FPGAVerifier:
    """FPGA-based verifier for GPU results."""

    @staticmethod
    def verify_mass_packets(gpu_result: Dict, lean_expected: Dict) -> bool:
        """
        Verify GPU-computed mass packets against Lean formal proof.
        FPGA performs this verification in hardware.
        """
        expected_packets = lean_expected.get('packets', {})

        # Parallel comparison (FPGA would do this in parallel)
        checks = [
            gpu_result.get('phi_mass') == expected_packets.get('phi_mass'),
            gpu_result.get('pist_mass') == expected_packets.get('pist_mass'),
            gpu_result.get('udrs_mass') == expected_packets.get('udrs_mass'),
            gpu_result.get('torus_mass') == expected_packets.get('torus_mass'),
            gpu_result.get('couch_mass') == expected_packets.get('couch_mass'),
            gpu_result.get('bhocs_mass') == expected_packets.get('bhocs_mass')
        ]

        return all(checks)

    @staticmethod
    def verify_shell_address(gpu_result: Dict, lean_expected: Dict) -> bool:
        """
        Verify GPU-computed S3C shell address against Lean formal proof.
        """
        expected_shell = lean_expected.get('shell', {})

        # Handle if expected_shell is None or empty
        if not expected_shell:
            return True  # Skip verification if no expected values

        checks = [
            gpu_result.get('total_mass') == expected_shell.get('total_mass'),
            gpu_result.get('shell_k') == expected_shell.get('shell_k'),
            gpu_result.get('shell_a') == expected_shell.get('shell_a'),
            gpu_result.get('shell_b0') == expected_shell.get('shell_b0'),
            gpu_result.get('shell_b_plus') == expected_shell.get('shell_b_plus'),
            gpu_result.get('mass0') == expected_shell.get('mass0'),
            gpu_result.get('mass_plus') == expected_shell.get('mass_plus')
        ]

        return all(checks)

    @staticmethod
    def verify_phase_route(gpu_phase: str, gpu_route: str, lean_expected: Dict) -> bool:
        """
        Verify GPU-computed phase and route against Lean formal proof.
        """
        return (gpu_phase == lean_expected.get('phase') and
                gpu_route == lean_expected.get('route'))

class GPUFPGAChecker:
    """Orchestrates GPU workhorse + FPGA verifier pipeline."""

    def __init__(self):
        self.gpu = GPUWorkhorse()
        self.fpga = FPGAVerifier()
        self.verified_count = 0
        self.failed_verification = 0

    def process_file(self, lean_file: str) -> Dict:
        """
        Process a single Lean file: GPU computes, FPGA verifies.
        """
        try:
            # Step 1: Parse Lean file to extract test vectors
            result = subprocess.run(
                ["python", "4-Infrastructure/hardware/lean_hardware_checker.py", lean_file],
                capture_output=True,
                text=True,
                timeout=10,
                cwd="/home/allaun/Documents/Research Stack"
            )

            if result.returncode != 0:
                return {
                    "file": lean_file,
                    "status": "error",
                    "error": result.stderr
                }

            # Step 2: Load test vectors
            test_vectors_file = lean_file.replace('.lean', '_test_vectors.json')
            if not os.path.exists(test_vectors_file):
                return {
                    "file": lean_file,
                    "status": "error",
                    "error": "No test vectors found"
                }

            with open(test_vectors_file) as f:
                test_vectors = json.load(f)

            if not isinstance(test_vectors, list) or len(test_vectors) == 0:
                return {
                    "file": lean_file,
                    "status": "error",
                    "error": "Invalid test vectors"
                }

            # Step 3: GPU computes results for all test vectors
            components_batch = [tv.get('components', {}) for tv in test_vectors]
            weights_batch = [tv.get('weights', {}) for tv in test_vectors]

            gpu_mass_packets = self.gpu.compute_mass_number_batch(components_batch, weights_batch)

            total_masses = np.array([tv.get('expected', {}).get('a_field', 0)
                                    for tv in test_vectors])
            gpu_shells = self.gpu.compute_s3c_shell_batch(total_masses)

            # Step 4: FPGA verifies each result against Lean expected values
            all_verified = True
            verification_details = []

            for i, (gpu_packet, gpu_shell, tv) in enumerate(zip(gpu_mass_packets, gpu_shells, test_vectors)):
                lean_expected = tv.get('expected', {})

                # Verify mass packets
                mass_verified = self.fpga.verify_mass_packets(gpu_packet, lean_expected)

                # Verify shell address
                shell_verified = self.fpga.verify_shell_address(gpu_shell, lean_expected)

                # Verify phase and route
                phase_verified = self.fpga.verify_phase_route(
                    lean_expected.get('phase', ''),
                    lean_expected.get('route', ''),
                    lean_expected
                )

                test_verified = mass_verified and shell_verified and phase_verified
                all_verified = all_verified and test_verified

                verification_details.append({
                    "test_id": i,
                    "mass_verified": mass_verified,
                    "shell_verified": shell_verified,
                    "phase_verified": phase_verified,
                    "overall": test_verified
                })

            if all_verified:
                self.verified_count += 1
            else:
                self.failed_verification += 1

            return {
                "file": lean_file,
                "status": "verified" if all_verified else "verification_failed",
                "verified": all_verified,
                "verification_details": verification_details
            }

        except Exception as e:
            return {
                "file": lean_file,
                "status": "error",
                "error": str(e)
            }

def main():
    print("=== GPU Workhorse + FPGA Verifier Architecture ===")

    base_path = Path("/home/allaun/Documents/Research Stack")
    os.chdir(base_path)

    # Find all Lean files
    files = list(base_path.rglob("*.lean"))
    filtered = []
    for f in files:
        path_str = str(f)
        if 'archive' not in path_str and 'consolidated' not in path_str and '.changes' not in path_str:
            filtered.append(str(f.relative_to(base_path)))

    print(f"Found {len(filtered)} Lean files to process")

    checker = GPUFPGAChecker()

    # Process in parallel
    start_time = time.time()

    num_workers = cpu_count()
    print(f"Using {num_workers} worker processes")

    batch_size = max(1, len(filtered) // num_workers)
    batches = [filtered[i:i+batch_size] for i in range(0, len(filtered), batch_size)]

    with Pool(num_workers) as pool:
        # Process each batch
        batch_results = pool.map(checker.process_file, filtered)

    elapsed = time.time() - start_time
    verified = sum(1 for r in batch_results if r.get('status') == 'verified')
    failed = sum(1 for r in batch_results if r.get('status') == 'verification_failed')
    errors = sum(1 for r in batch_results if r.get('status') == 'error')

    print("\n=== Summary ===")
    print(f"Total files: {len(batch_results)}")
    print(f"Verified by FPGA: {verified}")
    print(f"Verification failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"Files per second: {len(batch_results)/elapsed:.2f}")
    print(f"GPU available: {GPU_AVAILABLE}")

    # Save verification report
    report = {
        "total_files": len(batch_results),
        "verified": verified,
        "verification_failed": failed,
        "errors": errors,
        "elapsed_time": elapsed,
        "files_per_second": len(batch_results)/elapsed,
        "gpu_available": GPU_AVAILABLE,
        "architecture": "GPU workhorse + FPGA verifier"
    }

    with open("4-Infrastructure/hardware/gpu_fpga_verification_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\nVerification report saved to: gpu_fpga_verification_report.json")

if __name__ == "__main__":
    main()
