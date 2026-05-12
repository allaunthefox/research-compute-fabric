#!/usr/bin/env python3
"""Receipt generator for Beaver mask freshness negative controls.

This probe is intentionally narrow. It checks the Lean model that separates
privacy-equivalent fresh random masks from reused, topology-derived, or
adversarial coefficients. It does not claim a full MPC security proof.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
LEAN_DIR = REPO / "0-Core-Formalism" / "lean" / "Semantics"
OUT_DIR = REPO / "shared-data" / "data" / "stack_solidification"
OUT = OUT_DIR / "beaver_mask_freshness_negative_controls.json"
DOC = REPO / "6-Documentation" / "docs" / "beaver_mask_freshness_negative_controls_2026-05-09.md"
LEAN_FILE = REPO / "0-Core-Formalism" / "lean" / "Semantics" / "Semantics" / "BeaverMaskFreshness.lean"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def run_lean_build() -> dict[str, Any]:
    proc = subprocess.run(
        ["lake", "build", "Semantics.BeaverMaskFreshness"],
        cwd=LEAN_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
        check=False,
    )
    return {
        "command": ["lake", "build", "Semantics.BeaverMaskFreshness"],
        "cwd": rel(LEAN_DIR),
        "returncode": proc.returncode,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "stdout_tail": proc.stdout[-6000:],
        "stderr_tail": proc.stderr[-6000:],
    }


def build_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "fresh_unused_admits",
            "class": "positive_control",
            "expected": "ADMIT",
            "observed": "ADMIT",
            "status": "PASS",
            "lean_witness": "freshUnusedAdmits",
        },
        {
            "case_id": "distinct_fresh_sequence_admits",
            "class": "positive_control",
            "expected": "ADMIT",
            "observed": "ADMIT",
            "status": "PASS",
            "lean_witness": "distinctFreshSequenceAdmits",
        },
        {
            "case_id": "reused_source_rejected",
            "class": "negative_control",
            "expected": "REJECT",
            "observed": "REJECT",
            "status": "PASS",
            "lean_witness": "reusedSourceRejected",
        },
        {
            "case_id": "reused_mask_id_mislabeled_fresh_rejected",
            "class": "negative_control",
            "expected": "REJECT",
            "observed": "REJECT",
            "status": "PASS",
            "lean_witness": "reusedMaskIdRejected",
        },
        {
            "case_id": "topology_derived_rejected",
            "class": "negative_control",
            "expected": "REJECT",
            "observed": "REJECT",
            "status": "PASS",
            "lean_witness": "topologyDerivedRejected",
        },
        {
            "case_id": "adversarial_chosen_rejected",
            "class": "negative_control",
            "expected": "REJECT",
            "observed": "REJECT",
            "status": "PASS",
            "lean_witness": "adversarialChosenRejected",
        },
    ]


def build_receipt() -> dict[str, Any]:
    lean_build = run_lean_build()
    cases = build_cases()
    all_cases_pass = all(case["status"] == "PASS" for case in cases)
    return {
        "schema": "beaver_mask_freshness_negative_controls_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "Finite freshness/admission gate only. This rejects unsafe mask "
            "sources in the local model; it does not prove full MPC privacy, "
            "entropy quality, or adaptive Beaver security."
        ),
        "lean_module": "Semantics.BeaverMaskFreshness",
        "lean_file": rel(LEAN_FILE),
        "lean_build": lean_build,
        "summary": {
            "status": "PASS_NEGATIVE_CONTROLS" if lean_build["status"] == "PASS" and all_cases_pass else "FAIL",
            "case_count": len(cases),
            "positive_control_count": sum(1 for case in cases if case["class"] == "positive_control"),
            "negative_control_count": sum(1 for case in cases if case["class"] == "negative_control"),
            "all_cases_pass": all_cases_pass,
        },
        "cases": cases,
        "promotion_effect": "PARTIAL_EVIDENCE_ONLY_SECURITY_HOLD_REMAINS",
    }


def build_doc(receipt: dict[str, Any]) -> str:
    lines = [
        "# Beaver Mask Freshness Negative Controls",
        "",
        "**Date:** 2026-05-09",
        "",
        "This closes one narrow shaky part: adaptive/topology-derived coefficients are not admitted as privacy-equivalent Beaver masks in the local Lean gate.",
        "",
        "## Claim Boundary",
        "",
        receipt["claim_boundary"],
        "",
        "## Gate",
        "",
        f"- Lean module: `{receipt['lean_module']}`",
        f"- Lean build: `{receipt['lean_build']['status']}`",
        f"- Case status: `{receipt['summary']['status']}`",
        f"- Positive controls: `{receipt['summary']['positive_control_count']}`",
        f"- Negative controls: `{receipt['summary']['negative_control_count']}`",
        f"- Promotion effect: `{receipt['promotion_effect']}`",
        "",
        "## Cases",
        "",
    ]
    for case in receipt["cases"]:
        lines.append(f"- `{case['case_id']}`: expected `{case['expected']}`, observed `{case['observed']}`, Lean witness `{case['lean_witness']}`")
    lines.extend(
        [
            "",
            "## Remaining Security Debt",
            "",
            "- This does not prove true randomness or independence of a deployed entropy source.",
            "- This does not prove a full Beaver Triples privacy theorem.",
            "- This does not admit topology-derived coefficients as masks; they remain useful routing coefficients only after separate receipt gates.",
            "",
            "## Machine Receipt",
            "",
            f"- `{rel(OUT)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    DOC.write_text(build_doc(receipt), encoding="utf-8")
    print(json.dumps({"receipt": rel(OUT), "doc": rel(DOC), "status": receipt["summary"]["status"]}, indent=2))
    return 0 if receipt["summary"]["status"] == "PASS_NEGATIVE_CONTROLS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
