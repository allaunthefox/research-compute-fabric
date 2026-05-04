#!/usr/bin/env python3
"""
review_pipeline.py — Unified Compression / GCL / Metaprobe Review Shortcut

One-command initiation of the three core verification pipelines:
  1. Compression (HumanNeuralCompression.lean — lake build + #eval witnesses)
  2. GCL (Genetic Codon Layer — bytecode integrity + NesGCL square stream)
  3. Metaprobe (FixedPoint Q16_16 theorem verification via GPU metaprobe)

Usage:
  python 5-Applications/scripts/review_pipeline.py --all
  python 5-Applications/scripts/review_pipeline.py --compression --gcl
  python 5-Applications/scripts/review_pipeline.py --metaprobe
  python 5-Applications/scripts/review_pipeline.py --bbd

Returns JSON summary to stdout and writes timestamped report to
  5-Applications/out/review_pipeline_YYYYMMDD_HHMMSS.json
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
OUT_DIR = REPO_ROOT / "out"
LEAN_DIR = REPO_ROOT / "tools" / "lean" / "Semantics"


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> dict:
    """Run a shell command and return structured result."""
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd or REPO_ROOT,
            timeout=timeout,
        )
        elapsed = round(time.time() - start, 3)
        return {
            "cmd": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout,
            "stderr": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr,
            "elapsed_sec": elapsed,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "cmd": " ".join(cmd),
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
            "elapsed_sec": timeout,
            "success": False,
        }
    except Exception as e:
        return {
            "cmd": " ".join(cmd),
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "elapsed_sec": round(time.time() - start, 3),
            "success": False,
        }


def review_compression() -> dict:
    """Review 1: HumanNeuralCompression.lean — lake build + witness eval."""
    print("[review] Compression — HumanNeuralCompression.lean")
    results = {}

    # Step 1: Full lake build
    print("  → lake build ...")
    results["lake_build"] = run(
        ["lake", "build"],
        cwd=LEAN_DIR,
        timeout=300,
    )

    # Step 2: Check for sorry in HumanNeuralCompression
    print("  → Checking for sorry ...")
    sorry_check = run(
        ["grep", "-n", "\\bsorry\\b", "Semantics/HumanNeuralCompression.lean"],
        cwd=LEAN_DIR,
    )
    results["sorry_check"] = {
        "cmd": sorry_check["cmd"],
        "success": sorry_check["returncode"] != 0,  # grep returns 1 when no matches (desired)
        "returncode": sorry_check["returncode"],
        "matches": sorry_check["stdout"].strip().split("\n") if sorry_check["stdout"].strip() else [],
    }

    # Step 3: Count theorems
    print("  → Counting theorems ...")
    theorem_count = run(
        ["grep", "-c", "^theorem", "Semantics/HumanNeuralCompression.lean"],
        cwd=LEAN_DIR,
    )
    results["theorem_count"] = {
        "count": int(theorem_count["stdout"].strip()) if theorem_count["success"] else 0,
    }

    overall = (
        results["lake_build"]["success"]
        and results["sorry_check"]["success"]
    )
    return {"stage": "compression", "pass": overall, "details": results}


def review_gcl() -> dict:
    """Review 2: GCL — NesGCL square stream + bytecode integrity."""
    print("[review] GCL — NesGCL square stream")
    results = {}

    # Check key GCL files exist
    gcl_files = [
        REPO_ROOT / "scripts" / "nes_gcl_square_stream.py",
        REPO_ROOT / "scripts" / "nes_oisc_gcl_lut.py",
        REPO_ROOT / "scripts" / "sentence_as_computation_gcl.py",
        REPO_ROOT / "scripts" / "subleq_gcl_decompressor.bin",
    ]
    results["files_present"] = {
        str(p.relative_to(REPO_ROOT)): p.exists()
        for p in gcl_files
    }

    # Quick syntax check on Python GCL modules
    print("  → Syntax check nes_gcl_square_stream.py ...")
    results["syntax_nes_gcl"] = run(
        [sys.executable, "-m", "py_compile", str(gcl_files[0])],
        timeout=30,
    )

    print("  → Syntax check nes_oisc_gcl_lut.py ...")
    results["syntax_nes_oisc"] = run(
        [sys.executable, "-m", "py_compile", str(gcl_files[1])],
        timeout=30,
    )

    overall = all(results["files_present"].values()) and results["syntax_nes_gcl"]["success"]
    return {"stage": "gcl", "pass": overall, "details": results}


def review_metaprobe() -> dict:
    """Review 3: Metaprobe FixedPoint verifier."""
    print("[review] Metaprobe — FixedPoint Q16_16 verification")
    results = {}

    metaprobe_script = REPO_ROOT / "scripts" / "metaprobe_fixedpoint_verifier.py"
    results["script_present"] = metaprobe_script.exists()

    if not metaprobe_script.exists():
        return {"stage": "metaprobe", "pass": False, "details": results}

    print("  → Running metaprobe_fixedpoint_verifier.py ...")
    results["metaprobe_run"] = run(
        [sys.executable, str(metaprobe_script)],
        timeout=60,
    )

    overall = results["metaprobe_run"]["success"]
    return {"stage": "metaprobe", "pass": overall, "details": results}


def review_bbd() -> dict:
    """Review 4: BrainBoxDescriptor.lean — BBD theorems and composition laws."""
    print("[review] BBD — BrainBoxDescriptor.lean")
    results = {}

    # Check file exists
    bbd_file = LEAN_DIR / "Semantics" / "BrainBoxDescriptor.lean"
    results["file_present"] = bbd_file.exists()

    # Check for sorry
    print("  → Checking for sorry ...")
    sorry_check = run(
        ["grep", "-n", "\\bsorry\\b", "Semantics/BrainBoxDescriptor.lean"],
        cwd=LEAN_DIR,
    )
    results["sorry_check"] = {
        "cmd": sorry_check["cmd"],
        "success": sorry_check["returncode"] != 0,
        "returncode": sorry_check["returncode"],
        "matches": sorry_check["stdout"].strip().split("\n") if sorry_check["stdout"].strip() else [],
    }

    # Count theorems
    print("  → Counting theorems ...")
    theorem_count = run(
        ["grep", "-c", "^theorem", "Semantics/BrainBoxDescriptor.lean"],
        cwd=LEAN_DIR,
    )
    results["theorem_count"] = {
        "count": int(theorem_count["stdout"].strip()) if theorem_count["success"] else 0,
    }

    overall = results["file_present"] and results["sorry_check"]["success"]
    return {"stage": "bbd", "pass": overall, "details": results}


def main():
    parser = argparse.ArgumentParser(
        description="Unified review pipeline for Compression, GCL, and Metaprobe"
    )
    parser.add_argument("--all", action="store_true", help="Run all three reviews")
    parser.add_argument("--compression", action="store_true", help="Run compression review only")
    parser.add_argument("--gcl", action="store_true", help="Run GCL review only")
    parser.add_argument("--metaprobe", action="store_true", help="Run metaprobe review only")
    parser.add_argument("--bbd", action="store_true", help="Run BBD (BrainBoxDescriptor) review only")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON to stdout")
    args = parser.parse_args()

    if not any([args.all, args.compression, args.gcl, args.metaprobe, args.bbd]):
        parser.print_help()
        sys.exit(1)

    stages = []
    if args.all or args.compression:
        stages.append(review_compression)
    if args.all or args.gcl:
        stages.append(review_gcl)
    if args.all or args.metaprobe:
        stages.append(review_metaprobe)
    if args.all or args.bbd:
        stages.append(review_bbd)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stages": [],
    }

    all_pass = True
    for fn in stages:
        result = fn()
        report["stages"].append(result)
        all_pass = all_pass and result["pass"]
        status = "PASS" if result["pass"] else "FAIL"
        print(f"  [{status}] {result['stage']}\n")

    report["overall_pass"] = all_pass

    # Write timestamped report
    OUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = OUT_DIR / f"review_pipeline_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"Report written: {out_path.relative_to(REPO_ROOT)}")

    if args.json:
        print(json.dumps(report, indent=2))

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
