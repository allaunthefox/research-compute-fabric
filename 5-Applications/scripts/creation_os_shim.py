#!/usr/bin/env python3
"""Creation OS Benchmark Shim — JSON → Lean #eval Verification

This script reads Creation OS benchmark outputs (JSON) and generates Lean
#eval test cases for verification against SigmaGate fixed-point implementations.

Usage:
    python3 5-Applications/scripts/creation_os_shim.py \
        --input benchmarks/suite/full_results.json \
        --output 0-Core-Formalism/lean/Semantics/Semantics/SigmaGateBenchmark.lean

Per AGENTS.md §1.4: Float conversion is allowed at I/O boundaries only.
This is the JSON marshalling layer, not core logic.
"""

import json
import argparse
import sys
from pathlib import Path


def q0_16_from_float(f: float) -> str:
    """Convert float to Q0_16 hex literal.

    Q0_16 range: [-1, 0.999985], resolution ~0.0000305.
    Clamp to valid range.
    """
    clamped = max(-1.0, min(0.999985, f))
    if clamped < 0:
        val = int((1.0 + clamped) * 32767)  # Two's complement approximation
        val |= 0x8000  # Sign bit
    else:
        val = int(clamped * 32767)
    return f"⟨0x{val:04X}⟩"


def accuracy_to_label(accuracy: float) -> str:
    """Convert accuracy to Lean Label. >0.5 = correct."""
    return "Label.correct" if accuracy > 0.5 else "Label.incorrect"


def generate_lean_benchmark(rows: list[dict]) -> str:
    """Generate Lean benchmark module from Creation OS data."""

    lines = [
        "/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.",
        "Released under Apache 2.0 license as described in the file LICENSE.",
        "Authors: Research Stack Team",
        "",
        "SigmaGateBenchmark.lean — Creation OS Benchmark Verification",
        "",
        "Auto-generated from Creation OS benchmarks/suite/full_results.json",
        "via 5-Applications/scripts/creation_os_shim.py (JSON → Lean #eval shim).",
        "",
        "Per AGENTS.md §1.4: Float conversion at I/O boundary only.",
        "-/",
        "import Semantics.SigmaGate",
        "",
        "namespace Semantics.SigmaGate.Benchmark",
        "",
        "open Semantics.SigmaGate",
        "open Semantics.SigmaGate.Conformal",
        "",
        "-- ════════════════════════════════════════════════════════════",
        "-- §1  Creation OS Benchmark Data (Auto-Imported)",
        "-- ════════════════════════════════════════════════════════════",
        "",
        "/-- Benchmark rows from Creation OS multi-dataset σ-gate suite (SCI-6).",
        "    Schema: cos.suite_sci.v1",
        "    Source: https://github.com/spektre-labs/creation-os",
        "    BitNet-b1.58-2B, cos chat, pipeline mode filter.",
        "    -/",
    ]

    for i, row in enumerate(rows):
        name = row["name"]
        n_rows = row["n_rows"]
        n_scored = row["n_scored"]
        accuracy_all = row["accuracy_all"]
        sigma_mean = row["sigma_mean"]
        alpha = row["alpha"]
        delta = row["delta"]
        tau = row["tau"]
        tau_valid = row["tau_valid"]
        risk_ucb = row["risk_ucb"]

        sigma_hex = q0_16_from_float(sigma_mean)
        tau_hex = q0_16_from_float(tau)
        alpha_hex = q0_16_from_float(alpha)

        lines.append(f"/-- Dataset: {name}, N={n_rows}, accuracy={accuracy_all:.4f} -/")
        lines.append(f"def dataset_{name} : ShimScoredItem := ⟨")
        lines.append(f"  {sigma_mean:.6f},  -- sigma_mean")
        lines.append(f"  {accuracy_all:.6f},  -- accuracy")
        lines.append(f'  "{name}"')
        lines.append("⟩")
        lines.append("")

        # Threshold for this dataset
        lines.append(f"/-- Threshold for {name}: α={alpha}, τ={tau:.4f} -/")
        lines.append(f"def threshold_{name} : ConformalThreshold := {{")
        lines.append(f"  tau := {tau_hex},")
        lines.append(f"  alpha := {alpha_hex},")
        lines.append("  delta := ⟨0x0001⟩,")
        lines.append(f"  calibratedOn := {n_rows}")
        lines.append("}")
        lines.append("")

    lines.extend([
        "-- ════════════════════════════════════════════════════════════",
        "-- §2  Verification #eval Witnesses",
        "-- ════════════════════════════════════════════════════════════",
        "",
        "/-- Verify all Creation OS datasets against conservative threshold.",
        "    Each dataset is checked for valid threshold structure.",
        "    -/",
    ])

    for i, row in enumerate(rows):
        name = row["name"]
        lines.append(f'#eval! isValidConformalThreshold threshold_{name}  -- {name}')

    lines.extend([
        "",
        "/-- Verify empirical coverage: does threshold structure match dataset?",
        "    This is a structural check, not a full statistical test.",
        "    -/",
    ])

    for i, row in enumerate(rows):
        name = row["name"]
        lines.append(f'#eval! verifyShimCoverage threshold_{name} #[dataset_{name}]  -- {name}')

    lines.extend([
        "",
        "/-- Assemble all datasets for combined threshold verification.",
        "    Tests if the conservative threshold generalizes across tasks.",
        "    -/",
        "def allDatasets : Array ShimScoredItem := #[",
    ])
    for i, row in enumerate(rows):
        name = row["name"]
        comma = "," if i < len(rows) - 1 else ""
        lines.append(f"  dataset_{name}{comma}")
    lines.append("]")
    lines.append("")
    lines.append("/-- Combined verification across all tasks. -/")
    lines.append("#eval! verifyShimCoverage ConformalThreshold.conservative allDatasets")
    lines.append("")

    lines.extend([
        "-- ════════════════════════════════════════════════════════════",
        "-- §3  Sigma Score Reconstruction from Entropy Measures",
        "-- ════════════════════════════════════════════════════════════",
        "",
        "/-- Convert Creation OS sigma_mean to Lean SigmaScore.",
        "    Float bridge at I/O boundary (AGENTS.md §1.4 compliant).",
        "    -/",
    ])

    for i, row in enumerate(rows):
        name = row["name"]
        sigma_mean = row["sigma_mean"]
        sigma_hex = q0_16_from_float(sigma_mean)
        lines.append(f"def score_{name} : SigmaScore := ⟨{sigma_hex}, \"creation_os_{name}\", 1⟩")
        lines.append(f"#eval! score_{name}.value")
        lines.append("")

    lines.extend([
        "-- ════════════════════════════════════════════════════════════",
        "-- §4  Threshold Calibration Cross-Check",
        "-- ════════════════════════════════════════════════════════════",
        "",
        "/-- Conservative threshold (α=0.80, δ=0.10) cross-check.",
        "    Verifies structural validity against 5.5σ target.",
        "    -/",
        "#eval! isValidConformalThreshold ConformalThreshold.conservative",
        "",
        "/-- High-confidence threshold (targeting 6.5σ) cross-check.",
        "    Structural validity only — full 6.5σ requires 1M+ samples.",
        "    -/",
        "#eval! isValidConformalThreshold ConformalThreshold.sixSigma",
        "",
        "end Semantics.SigmaGate.Benchmark",
        "",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Creation OS → Lean shim")
    parser.add_argument("--input", required=True, help="Path to Creation OS JSON")
    parser.add_argument("--output", required=True, help="Path to write Lean file")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        data = json.load(f)

    if "rows" not in data:
        print("Error: JSON missing 'rows' field", file=sys.stderr)
        sys.exit(1)

    rows = data["rows"]
    lean_code = generate_lean_benchmark(rows)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(lean_code)

    print(f"Wrote {len(rows)} benchmark rows to {args.output}")
    print(f"Lines of Lean code: {len(lean_code.splitlines())}")


if __name__ == "__main__":
    main()
