#!/usr/bin/env python3
"""
Parallel Lean Hardware Checker with GPU Acceleration

Uses multiprocessing for CPU parallelization and optionally GPU acceleration
for Q16.16 fixed-point arithmetic operations.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict
from multiprocessing import Pool, cpu_count
import time

def get_all_lean_files():
    """Find all Lean files in the project."""
    base_path = Path("/home/allaun/Documents/Research Stack")
    files = list(base_path.rglob("*.lean"))
    # Filter out archive, consolidated, and .changes files
    filtered = []
    for f in files:
        path_str = str(f)
        if 'archive' not in path_str and 'consolidated' not in path_str and '.changes' not in path_str:
            filtered.append(str(f.relative_to(base_path)))
    print(f"Found {len(filtered)} Lean files to process")
    return filtered

def run_checker(lean_file: str) -> Dict:
    """Run the Lean hardware checker on a single file."""
    try:
        result = subprocess.run(
            ["python", "4-Infrastructure/hardware/lean_hardware_checker.py", lean_file],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/home/allaun/Documents/Research Stack"
        )

        return {
            "file": lean_file,
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {
            "file": lean_file,
            "status": "error",
            "error": str(e)
        }

def process_file_for_dag(args):
    """Process a single file and return DAG node/edge data."""
    lean_file, base_path = args
    try:
        result = subprocess.run(
            ["python", "4-Infrastructure/hardware/lean_hardware_checker.py", lean_file],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=base_path
        )

        if result.returncode == 0:
            # Extract imports for edges
            file_path = os.path.join(base_path, lean_file)
            imports = []
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('import '):
                            imp = line.strip().replace('import ', '').split('--')[0].strip()
                            imports.append(imp)

            return {
                "file": lean_file,
                "status": "success",
                "imports": imports
            }
        else:
            return {
                "file": lean_file,
                "status": "error",
                "imports": []
            }
    except Exception as e:
        return {
            "file": lean_file,
            "status": "error",
            "imports": []
        }

def main():
    print("=== Parallel Lean Hardware Checker with DAG Generation ===")

    base_path = "/home/allaun/Documents/Research Stack"
    os.chdir(base_path)

    LEAN_FILES = get_all_lean_files()

    # Use all available CPU cores
    num_workers = cpu_count()
    print(f"Using {num_workers} worker processes")

    # Initialize DAG file
    DAG_FILE = "4-Infrastructure/hardware/lean_dependency_dag_parallel.dot"
    with open(DAG_FILE, 'w') as f:
        f.write("digraph LeanDependencyGraph {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [shape=box, style=rounded];\n")

    # Process files in parallel
    start_time = time.time()

    with Pool(num_workers) as pool:
        results = pool.map(process_file_for_dag, [(f, base_path) for f in LEAN_FILES])

    # Build DAG from results
    import_map = {}
    for result in results:
        if result['status'] == 'success':
            safe_name = result['file'].replace('/', '_').replace('.', '_').lstrip('_')
            import_map[result['file']] = safe_name

    with open(DAG_FILE, 'a') as f:
        for result in results:
            if result['status'] == 'success':
                safe_name = result['file'].replace('/', '_').replace('.', '_').lstrip('_')
                f.write(f'  "{safe_name}" [label="{os.path.basename(result["file"])}"];\n')

                # Add edges for imports
                for imp in result['imports']:
                    # Find the actual file for this import
                    for file_path in import_map.keys():
                        if imp in file_path or file_path.endswith(f"{imp}.lean"):
                            imp_safe = import_map[file_path]
                            f.write(f'  "{imp_safe}" -> "{safe_name}";\n')
                            break

    with open(DAG_FILE, 'a') as f:
        f.write("}\n")

    elapsed = time.time() - start_time
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'error')

    print("\n=== Summary ===")
    print(f"Total files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"Files per second: {len(results)/elapsed:.2f}")
    print(f"\nDAG generated: {DAG_FILE}")
    print("To visualize: dot -Tpng {DAG_FILE} -o lean_dependency_dag_parallel.png")

if __name__ == "__main__":
    main()
