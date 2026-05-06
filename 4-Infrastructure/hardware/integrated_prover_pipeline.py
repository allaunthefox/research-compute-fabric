#!/usr/bin/env python3
"""
Integrated Prover Pipeline with GPU+FPGA Architecture

Combines:
- GPU workhorse for Q16.16 arithmetic and mass number calculations
- FPGA verifier for hardware verification
- Goedel-Prover-V2 for formal proof generation
- bf4prover for sorry block repair
- bfs_prover for AVM trace auditing
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
except ImportError:
    GPU_AVAILABLE = False

# Import from existing modules
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.append(str(Path(__file__).parent.parent.parent / "5-Applications" / "scripts"))

class IntegratedProverPipeline:
    """Unified pipeline combining GPU, FPGA, and multiple provers."""

    def __init__(self):
        self.base_path = Path("/home/allaun/Documents/Research Stack")
        self.gpu_available = GPU_AVAILABLE
        self.ollama_url = "http://localhost:11434/api/generate"

    def run_goedel_prover(self, lean_file: str) -> Dict:
        """Run Goedel-Prover-V2 on a Lean file."""
        goedel_path = self.base_path / "ai-math-discovery-systems" / "Goedel-Prover-V2"
        inference_script = goedel_path / "src" / "inference.py"

        if not inference_script.exists():
            return {
                "file": lean_file,
                "prover": "Goedel-Prover-V2",
                "status": "error",
                "error": "Goedel-Prover-V2 inference script not found"
            }

        try:
            result = subprocess.run(
                ["python", str(inference_script), lean_file],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(goedel_path)
            )

            return {
                "file": lean_file,
                "prover": "Goedel-Prover-V2",
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                "file": lean_file,
                "prover": "Goedel-Prover-V2",
                "status": "error",
                "error": str(e)
            }

    def run_bf4prover(self, lean_file: str) -> Dict:
        """Run bf4prover on a Lean file."""
        bf4prover_script = self.base_path / "scripts" / "bf4prover.py"

        if not bf4prover_script.exists():
            return {
                "file": lean_file,
                "prover": "bf4prover",
                "status": "error",
                "error": "bf4prover script not found"
            }

        try:
            result = subprocess.run(
                ["python", str(bf4prover_script), lean_file, "--dry-run"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.base_path)
            )

            return {
                "file": lean_file,
                "prover": "bf4prover",
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                "file": lean_file,
                "prover": "bf4prover",
                "status": "error",
                "error": str(e)
            }

    def run_bfs_prover_audit(self) -> Dict:
        """Run bfs_prover bridge for AVM trace auditing."""
        bfs_script = self.base_path / "5-Applications" / "scripts" / "bfs_prover_bridge.py"

        if not bfs_script.exists():
            return {
                "prover": "bfs_prover",
                "status": "error",
                "error": "bfs_prover bridge script not found"
            }

        try:
            result = subprocess.run(
                ["python", str(bfs_script)],
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(self.base_path)
            )

            return {
                "prover": "bfs_prover",
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                "prover": "bfs_prover",
                "status": "error",
                "error": str(e)
            }

    def run_gpu_fpga_checker(self, lean_file: str) -> Dict:
        """Run the GPU workhorse + FPGA verifier."""
        checker_script = self.base_path / "4-Infrastructure" / "hardware" / "gpu_fpga_distributed_checker.py"

        if not checker_script.exists():
            return {
                "file": lean_file,
                "prover": "GPU+FPGA",
                "status": "error",
                "error": "GPU+FPGA checker script not found"
            }

        try:
            # Import and run the checker
            import importlib.util
            spec = importlib.util.spec_from_file_location("gpu_fpga_checker", checker_script)
            checker_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(checker_module)

            result = checker_module.GPUFPGAChecker().process_file(lean_file)

            return {
                "file": lean_file,
                "prover": "GPU+FPGA",
                "status": result.get('status', 'error'),
                "verified": result.get('verified', False),
                "details": result.get('verification_details', [])
            }
        except Exception as e:
            return {
                "file": lean_file,
                "prover": "GPU+FPGA",
                "status": "error",
                "error": str(e)
            }

    def classify_file_for_prover(self, lean_file: str) -> str:
        """
        Classify which prover should handle this file.
        - Files with sorry blocks: bf4prover
        - Files needing formal proofs: Goedel-Prover-V2
        - Files with Q16.16 arithmetic: GPU+FPGA
        - AVM trace files: bfs_prover
        """
        file_lower = lean_file.lower()

        # Check for sorry blocks
        file_path = self.base_path / lean_file
        if file_path.exists():
            with open(file_path, 'r') as f:
                content = f.read()
                if 'sorry' in content and 'TODO' in content:
                    return 'bf4prover'

        # Check for Q16.16 arithmetic patterns
        if 'mass' in file_lower or 'q16' in file_lower or 'shell' in file_lower:
            return 'gpu_fpga'

        # Check for theorem/lemma heavy files
        if 'theorem' in file_lower or 'lemma' in file_lower:
            return 'goedel'

        # Default to GPU+FPGA
        return 'gpu_fpga'

    def process_file(self, lean_file: str) -> Dict:
        """Process a single file with the appropriate prover."""
        prover_type = self.classify_file_for_prover(lean_file)

        if prover_type == 'bf4prover':
            return self.run_bf4prover(lean_file)
        elif prover_type == 'goedel':
            return self.run_goedel_prover(lean_file)
        elif prover_type == 'gpu_fpga':
            return self.run_gpu_fpga_checker(lean_file)
        else:
            return {
                "file": lean_file,
                "prover": "unknown",
                "status": "error",
                "error": f"Unknown prover type: {prover_type}"
            }

def main():
    print("=== Integrated Prover Pipeline with GPU+FPGA Architecture ===")

    pipeline = IntegratedProverPipeline()
    base_path = pipeline.base_path
    os.chdir(base_path)

    # Find all Lean files
    files = list(base_path.rglob("*.lean"))
    filtered = []
    for f in files:
        path_str = str(f)
        if 'archive' not in path_str and 'consolidated' not in path_str and '.changes' not in path_str:
            filtered.append(str(f.relative_to(base_path)))

    print(f"Found {len(filtered)} Lean files to process")
    print(f"GPU available: {pipeline.gpu_available}")

    # Process in parallel
    start_time = time.time()

    num_workers = cpu_count()
    print(f"Using {num_workers} worker processes")

    # Process a sample first to test
    sample_size = min(100, len(filtered))
    sample_files = filtered[:sample_size]

    print(f"Processing sample of {sample_size} files...")

    with Pool(num_workers) as pool:
        results = pool.map(pipeline.process_file, sample_files)

    # Run bfs_prover audit separately (it's not file-based)
    print("\nRunning bfs_prover AVM audit...")
    bfs_result = pipeline.run_bfs_prover_audit()

    elapsed = time.time() - start_time

    # Analyze results
    goedel_count = sum(1 for r in results if r.get('prover') == 'Goedel-Prover-V2')
    bf4_count = sum(1 for r in results if r.get('prover') == 'bf4prover')
    gpu_fpga_count = sum(1 for r in results if r.get('prover') == 'GPU+FPGA')

    success_count = sum(1 for r in results if r.get('status') == 'success' or r.get('status') == 'verified')
    error_count = sum(1 for r in results if r.get('status') == 'error')

    print("\n=== Summary ===")
    print(f"Total files processed: {len(results)}")
    print(f"Goedel-Prover-V2: {goedel_count}")
    print(f"bf4prover: {bf4_count}")
    print(f"GPU+FPGA: {gpu_fpga_count}")
    print(f"bfs_prover audit: {bfs_result.get('status', 'error')}")
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"Files per second: {len(results)/elapsed:.2f}")

    # Save report
    report = {
        "total_files": len(results),
        "prover_distribution": {
            "Goedel-Prover-V2": goedel_count,
            "bf4prover": bf4_count,
            "GPU+FPGA": gpu_fpga_count,
            "bfs_prover": bfs_result.get('status')
        },
        "success_count": success_count,
        "error_count": error_count,
        "elapsed_time": elapsed,
        "files_per_second": len(results)/elapsed,
        "gpu_available": pipeline.gpu_available,
        "results": results,
        "bfs_audit": bfs_result
    }

    report_file = base_path / "4-Infrastructure" / "hardware" / "integrated_prover_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {report_file}")

if __name__ == "__main__":
    main()
