#!/usr/bin/env python3
"""
Batch Lean Hardware Checker

Runs the Lean hardware checker on all relevant Lean files in the project
and generates a summary report.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict

def get_all_lean_files():
    """Find all Lean files in the project."""
    base_path = "/home/allaun/Documents/Research Stack"
    result = subprocess.run(
        ["find", base_path, "-name", "*.lean", "-type f"],
        capture_output=True,
        text=True
    )
    files = result.stdout.strip().split('\n')
    print(f"DEBUG: Raw find returned {len(files)} files")
    print(f"DEBUG: First few files: {files[:5] if files else 'none'}")
    # Filter out archive, consolidated, and .changes files
    filtered = [f.replace(base_path + '/', '') for f in files
                if 'archive' not in f and 'consolidated' not in f and '.changes' not in f and f]
    print(f"Found {len(filtered)} Lean files to process")
    return filtered

LEAN_FILES = get_all_lean_files()

def run_checker(lean_file: str) -> Dict:
    """Run the Lean hardware checker on a single file."""
    try:
        result = subprocess.run(
            ["python", "4-Infrastructure/hardware/lean_hardware_checker.py", lean_file],
            capture_output=True,
            text=True,
            timeout=10
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

def main():
    print("=== Batch Lean Hardware Checker ===\n")

    os.chdir("/home/allaun/Documents/Research Stack")

    results = []
    for i, lean_file in enumerate(LEAN_FILES):
        if Path(lean_file).exists():
            print(f"[{i+1}/{len(LEAN_FILES)}] Processing: {lean_file}")
            result = run_checker(lean_file)
            results.append(result)
            print(f"  Status: {result['status']}")
        else:
            print(f"[{i+1}/{len(LEAN_FILES)}] Skipping (not found): {lean_file}")
            results.append({
                "file": lean_file,
                "status": "skipped",
                "error": "File not found"
            })

    # Generate summary report
    print("\n=== Summary ===")
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")
    skipped = sum(1 for r in results if r["status"] == "skipped")

    print(f"Total files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")

    # Save summary
    summary = {
        "total_files": len(results),
        "successful": successful,
        "failed": failed,
        "skipped": skipped,
        "results": results
    }

    with open("lean_hardware_checker_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\nSummary saved to: lean_hardware_checker_summary.json")

if __name__ == "__main__":
    main()
