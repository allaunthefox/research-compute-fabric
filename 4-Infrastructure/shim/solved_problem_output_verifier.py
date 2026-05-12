#!/usr/bin/env python3
"""Run solved/known-problem checks and emit verification receipts.

This harness is deliberately conservative. It reruns a small set of existing
4-primitive Erdős scripts whose targets are solved theorems, solved lower-bound
smokes, or finite constructions. Open conjecture smoke tests are listed as
excluded so they cannot be promoted to theorem evidence by accident.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
WIKI = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ratio_ok(value: float, target: float = 1.0, eps: float = 1e-12) -> bool:
    return abs(float(value) - target) <= eps


def validate_egz(data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    analysis = data.get("theorem_analysis", {})
    results = data.get("results", [])
    packet_witness_ok = sum(
        1
        for item in results
        if item.get("subset_found")
        and item.get("subset")
        and sum(item["subset"]) % int(item["n"]) == 0
        and len(item["subset"]) == int(item["n"])
    )
    ok = (
        analysis.get("subset_found_count") == analysis.get("total_tests")
        and ratio_ok(analysis.get("success_rate", 0.0))
        and packet_witness_ok == len(results)
    )
    return ok, {
        "subset_found_count": analysis.get("subset_found_count"),
        "total_tests": analysis.get("total_tests"),
        "success_rate": analysis.get("success_rate"),
        "packet_witness_ok": packet_witness_ok,
    }


def validate_ekr(data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    analysis = data.get("theorem_analysis", [])
    results = data.get("results", [])
    ratio_hits = sum(1 for item in analysis if ratio_ok(item.get("ratio", 0.0)))
    family_ok = sum(1 for item in results if item.get("is_intersecting") and item.get("family_size") == item.get("field", {}).get("theoretical_max"))
    ok = bool(analysis) and ratio_hits == len(analysis) and family_ok == len(results)
    return ok, {
        "ratio_hits": ratio_hits,
        "analysis_count": len(analysis),
        "intersecting_optimal_family_count": family_ok,
        "result_count": len(results),
    }


def validate_szekeres(data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    analysis = data.get("theorem_analysis", {})
    results = data.get("results", [])
    witness_ok = sum(
        1
        for item in results
        if item.get("theorem_holds") and int(item.get("max_monotone_length", 0)) >= int(item.get("n", 0)) + 1
    )
    ok = (
        analysis.get("theorem_holds_count") == analysis.get("total_tests")
        and ratio_ok(analysis.get("success_rate", 0.0))
        and witness_ok == len(results)
    )
    return ok, {
        "theorem_holds_count": analysis.get("theorem_holds_count"),
        "total_tests": analysis.get("total_tests"),
        "success_rate": analysis.get("success_rate"),
        "monotone_witness_ok": witness_ok,
    }


def validate_distinct_distances(data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    analysis = data.get("problem_analysis", {})
    results = data.get("results", [])
    bound_ok = sum(
        1
        for item in results
        if item.get("bound_holds")
        and item.get("num_distinct_distances", 0) >= item.get("theoretical_bound", float("inf"))
    )
    ok = (
        analysis.get("bound_holds_count") == analysis.get("total_tests")
        and ratio_ok(analysis.get("success_rate", 0.0))
        and bound_ok == len(results)
    )
    return ok, {
        "bound_holds_count": analysis.get("bound_holds_count"),
        "total_tests": analysis.get("total_tests"),
        "success_rate": analysis.get("success_rate"),
        "per_instance_bound_ok": bound_ok,
    }


def validate_hadamard_sylvester(data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    analysis = data.get("conjecture_analysis", {})
    results = data.get("results", [])
    construction_ok = sum(
        1
        for item in results
        if item.get("hadamard_exists") and item.get("spectral", {}).get("is_orthogonal")
    )
    ok = (
        analysis.get("hadamard_exists_count") == analysis.get("total_tests")
        and ratio_ok(analysis.get("existence_rate", 0.0))
        and construction_ok == len(results)
    )
    return ok, {
        "hadamard_exists_count": analysis.get("hadamard_exists_count"),
        "total_tests": analysis.get("total_tests"),
        "existence_rate": analysis.get("existence_rate"),
        "orthogonal_construction_ok": construction_ok,
        "boundary_note": analysis.get("note"),
    }


CaseValidator = Callable[[dict[str, Any]], tuple[bool, dict[str, Any]]]


CASES: list[dict[str, Any]] = [
    {
        "id": "erdos_ginzburg_ziv",
        "title": "Erdos-Ginzburg-Ziv theorem",
        "classification": "solved_theorem",
        "script": "test_erdos_ginzburg_ziv_4primitive.py",
        "result": "test_erdos_ginzburg_ziv_4primitive_results.json",
        "validator": validate_egz,
        "claim_boundary": "Finite generated instances verify the local witness detector against a solved theorem; this is not a proof of the theorem.",
    },
    {
        "id": "erdos_ko_rado",
        "title": "Erdos-Ko-Rado theorem",
        "classification": "solved_theorem",
        "script": "test_erdos_ko_rado_4primitive.py",
        "result": "test_erdos_ko_rado_4primitive_results.json",
        "validator": validate_ekr,
        "claim_boundary": "Finite small parameter checks verify the local family detector against a solved theorem; this is not a proof of the theorem.",
    },
    {
        "id": "erdos_szekeres",
        "title": "Erdos-Szekeres monotone subsequence theorem",
        "classification": "solved_theorem",
        "script": "test_erdos_szekeres_4primitive.py",
        "result": "test_erdos_szekeres_4primitive_results.json",
        "validator": validate_szekeres,
        "claim_boundary": "Finite random permutations verify the local monotone-subsequence detector against a solved theorem; this is not a proof of the theorem.",
    },
    {
        "id": "erdos_distinct_distances",
        "title": "Erdos distinct distances lower-bound smoke",
        "classification": "solved_bound_smoke",
        "script": "test_erdos_distinct_distances_4primitive.py",
        "result": "test_erdos_distinct_distances_4primitive_results.json",
        "validator": validate_distinct_distances,
        "claim_boundary": "Finite point clouds verify the local lower-bound checker; this does not solve or certify the full extremal geometry result.",
    },
    {
        "id": "hadamard_sylvester",
        "title": "Hadamard Sylvester construction",
        "classification": "finite_construction",
        "script": "test_erdos_hadamard_4primitive.py",
        "result": "test_erdos_hadamard_4primitive_results.json",
        "validator": validate_hadamard_sylvester,
        "claim_boundary": "Verifies Sylvester power-of-two Hadamard constructions only; the general Hadamard conjecture remains open.",
    },
]


EXCLUDED_CASES = [
    {
        "id": "erdos_gyarfas",
        "reason": "known anomaly lane: claimed failures need independent cycle certificates before use",
        "result": "test_erdos_gyarfas_4primitive_results.json",
    },
    {
        "id": "erdos_selfridge",
        "reason": "open conjecture finite smoke only",
        "result": "test_erdos_selfridge_4primitive_results.json",
    },
    {
        "id": "erdos_straus",
        "reason": "open conjecture finite smoke only",
        "result": "test_erdos_straus_4primitive_results.json",
    },
    {
        "id": "erdos_ternary_2n",
        "reason": "open conjecture finite smoke only",
        "result": "test_erdos_ternary_2n_4primitive_results.json",
    },
    {
        "id": "erdos_mollin_walsh",
        "reason": "status naming may be inverted; inspect before promotion",
        "result": "test_erdos_mollin_walsh_4primitive_results.json",
    },
]


def run_case(case: dict[str, Any], timeout: int) -> dict[str, Any]:
    script = SHIM / case["script"]
    result = SHIM / case["result"]
    before_hash = sha256_bytes(result.read_bytes()) if result.exists() else None
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(REPO),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    stdout_tail = proc.stdout[-4000:]
    stderr_tail = proc.stderr[-4000:]
    run_ok = proc.returncode == 0 and result.exists()
    after_hash = sha256_bytes(result.read_bytes()) if result.exists() else None
    validation_ok = False
    metrics: dict[str, Any] = {}
    result_top_keys: list[str] = []
    if run_ok:
        data = load_json(result)
        result_top_keys = sorted(data.keys())
        validation_ok, metrics = case["validator"](data)
    return {
        "id": case["id"],
        "title": case["title"],
        "classification": case["classification"],
        "script": str(script.relative_to(REPO)),
        "result": str(result.relative_to(REPO)),
        "returncode": proc.returncode,
        "run_ok": run_ok,
        "validation_ok": validation_ok,
        "result_hash_before": before_hash,
        "result_hash_after": after_hash,
        "result_top_keys": result_top_keys,
        "metrics": metrics,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "claim_boundary": case["claim_boundary"],
    }


def build_curriculum(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a solved-problem verification router. Return compact JSON and never promote finite smoke tests into proofs."
    records = []
    for case in receipt["cases"]:
        prompt = {
            "task": "classify_solved_problem_output",
            "case_id": case["id"],
            "classification": case["classification"],
            "metrics": case["metrics"],
            "claim_boundary": case["claim_boundary"],
            "instruction": "Decide whether this result can be used as verifier evidence for the local math stack.",
        }
        answer = {
            "selected": bool(case["validation_ok"]),
            "use_as": "solved_problem_verification" if case["validation_ok"] else "diagnostic_failure",
            "evidence_tier": case["classification"],
            "claim_boundary": case["claim_boundary"],
            "source_path": case["result"],
            "source_hash": case["result_hash_after"],
            "receipt_rule": "Use as detector/output validation only; require formal proof receipts for theorem promotion.",
        }
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
                ]
            }
        )
    return records


def write_wiki(receipt: dict[str, Any], path: Path) -> None:
    passed = sum(1 for case in receipt["cases"] if case["validation_ok"])
    total = len(receipt["cases"])
    lines = [
        "created: 20260507000000000",
        "modified: 20260507000000000",
        "tags: ResearchStack Erdos Verification Metaprobe Math",
        "title: Solved Problem Output Verifier",
        "type: text/vnd.tiddlywiki",
        "",
        "! Solved Problem Output Verifier",
        "",
        "This tiddler records the solved/known-problem verifier for the local 4-primitive Erdős scripts.",
        "",
        f"Durable source: `4-Infrastructure/shim/solved_problem_output_verifier.py`",
        "",
        f"Receipt: `4-Infrastructure/shim/solved_problem_output_verifier_receipt.json`",
        "",
        f"Curriculum: `4-Infrastructure/shim/solved_problem_output_verifier_curriculum.jsonl`",
        "",
        "!! Verification Result",
        "",
        f"* Cases passed: {passed}/{total}",
        f"* Overall lawful: `{str(receipt['lawful']).lower()}`",
        "",
        "!! Included Cases",
        "",
    ]
    for case in receipt["cases"]:
        status = "PASS" if case["validation_ok"] else "FAIL"
        lines.append(f"* {status} `{case['id']}` ({case['classification']}): {case['claim_boundary']}")
    lines.extend(
        [
            "",
            "!! Excluded / Non-Promotable Cases",
            "",
        ]
    )
    for case in receipt["excluded_cases"]:
        lines.append(f"* `{case['id']}`: {case['reason']}")
    lines.extend(
        [
            "",
            "!! Claim Boundary",
            "",
            "This verifier checks local outputs against solved or construction-backed expectations. It does not prove the theorems, and it explicitly keeps open conjecture smoke tests out of the solved-problem lane.",
            "",
            "!! Links",
            "",
            "* [[Erdos Four Primitive Diagnostics]]",
            "* [[Custom Equation Awareness Manifest]]",
            "* [[Physics Math LLM Metaprobe Audit]]",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--receipt", type=Path, default=SHIM / "solved_problem_output_verifier_receipt.json")
    parser.add_argument("--curriculum", type=Path, default=SHIM / "solved_problem_output_verifier_curriculum.jsonl")
    parser.add_argument("--wiki", type=Path, default=WIKI / "Solved Problem Output Verifier.tid")
    args = parser.parse_args()

    cases = [run_case(case, args.timeout) for case in CASES]
    pass_count = sum(1 for case in cases if case["validation_ok"])
    receipt = {
        "schema": "solved_problem_output_verifier_receipt_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "Solved-problem runs validate local detectors and outputs; they are not theorem proofs and do not promote open conjecture smoke tests.",
        "cases": cases,
        "excluded_cases": EXCLUDED_CASES,
        "pass_count": pass_count,
        "case_count": len(cases),
        "lawful": pass_count == len(cases),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in build_curriculum(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_wiki(receipt, args.wiki)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0 if receipt["lawful"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
