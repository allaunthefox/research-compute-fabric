#!/usr/bin/env python3
"""Canary batch: run 20-50 Lean theorems through proof worker → PIST → classify.

Generates:
  shared-data/pist_canary_receipts.jsonl    — structural receipts v2
  shared-data/pist_canary_results.jsonl     — PIST classification results
  shared-data/pist_canary_report.json       — cluster/analysis report
"""

import json
import math
import os
import random
import subprocess
import sys
import tempfile
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from validate_rrc_predictions import parse_equation, build_proof_metrics

PIST_DECOMPOSE = os.environ.get(
    "PIST_DECOMPOSE_BIN",
    "/home/allaun/.local/share/opencode/worktree/"
    "0b42981cf7f7d5e172b1e93f8d4bb64a3dd63962/Turn-and-Burn/infra/rust/"
    "ene-rds/target/release/pist-decompose",
)

PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")
if not PROOF_SERVER_TOKEN:
    tf = os.environ.get("PROOF_SERVER_TOKEN_FILE",
                        os.path.expanduser("~/.config/ene/language-proof-server.token"))
    try:
        PROOF_SERVER_TOKEN = Path(tf).read_text().strip()
    except (FileNotFoundError, OSError):
        PROOF_SERVER_TOKEN = ""

CANARY_THEOREMS = [
    # ── rfl / trivial ──
    ("rfl_one", "theorem t (n : Nat) : n = n := by rfl"),
    ("rfl_add", "theorem t (n : Nat) : n + 0 = n := by rfl"),
    ("rfl_succ", "theorem t (n : Nat) : n.succ = n.succ := by rfl"),

    # ── simp ──
    ("simp_add_zero", "theorem t (n : Nat) : n + 0 = n := by simp"),
    ("simp_mul_one", "theorem t (n : Nat) : n * 1 = n := by simp"),
    ("simp_add_comm", "theorem t (a b : Nat) : a + b = b + a := by simp [add_comm]"),
    ("simp_add_assoc", "theorem t (a b c : Nat) : (a + b) + c = a + (b + c) := by simp [add_assoc]"),
    ("simp_mul_comm", "theorem t (a b : Nat) : a * b = b * a := by simp [mul_comm]"),

    # ── omega / arithmetic ──
    ("omega_add", "theorem t (a b c : Nat) : a + b + c = a + c + b := by omega"),
    ("omega_mul", "theorem t (a b : Nat) : (a + b) * 2 = a*2 + b*2 := by omega"),
    ("omega_ineq", "theorem t (a b : Nat) (h : a ≤ b) : a + 1 ≤ b + 1 := by omega"),
    ("omega_mod", "theorem t (a : Nat) : a % 2 < 2 := by omega"),
    ("omega_double", "theorem t (n : Nat) : n + n = 2 * n := by omega"),

    # ── ring ──
    ("ring_sq", "theorem t (x y : Nat) : (x + y)^2 = x^2 + 2*x*y + y^2 := by nlinarith"),
    ("ring_cube", "theorem t (x : Nat) : (x+1)^3 = x^3 + 3*x^2 + 3*x + 1 := by nlinarith"),
    ("ring_expand", "theorem t (a b : Nat) : (a + b) * (a - b) = a^2 - b^2 := by omega"),

    # ── induction ──
    ("induct_add_zero", "theorem t (n : Nat) : n + 0 = n := by induction n with k IH; rfl; simp [add_succ, IH]"),
    ("induct_add_succ", "theorem t (n m : Nat) : n + m.succ = (n + m).succ := by induction n with k IH; rfl; simp [add_succ, IH]"),
    ("induct_mul", "theorem t (n m : Nat) : n * m = m * n := by induction n with k IH; simp; simp [mul_add, IH, add_comm, add_left_comm, add_assoc]"),

    # ── rewrite-heavy ──
    ("rw_add_comm", "theorem t (a b : Nat) : a + b = b + a := by rw [add_comm a b]"),
    ("rw_mul_comm", "theorem t (a b : Nat) : a * b = b * a := by rw [mul_comm]"),
    ("rw_add_assoc", "theorem t (a b c : Nat) : a + b + c = c + b + a := by rw [add_comm a b, add_comm (a+b) c, add_comm b a]; rfl"),

    # ── with imports ──
    ("with_import_list", "import Mathlib.Data.List.Basic\ntheorem t (l : List Nat) : l.reverse.reverse = l := by simp"),
    ("with_import_nat", "import Mathlib.Data.Nat.Basic\ntheorem t (a b : Nat) : a.gcd b = b.gcd a := Nat.gcd_comm a b"),
    ("with_import_int", "import Mathlib.Data.Int.Basic\ntheorem t (a b : ℤ) : a + b = b + a := by omega"),
    ("with_import_set", "import Mathlib.Data.Set.Basic\ntheorem t (s : Set Nat) : s ∪ s = s := Set.union_self s"),

    # ── algebra / ring ──
    ("algebra_id", "theorem t (x : Nat) : x * 1 = x := by simp"),
    ("algebra_distrib", "theorem t (a b c : Nat) : a * (b + c) = a * b + a * c := by omega"),
    ("algebra_sq_diff", "theorem t (x y : Nat) : x^2 - y^2 = (x - y) * (x + y) := by omega"),

    # ── logic / boolean ──
    ("logic_and", "theorem t (A B : Prop) : A ∧ B → A := by intro h; exact h.1"),
    ("logic_or", "theorem t (A B : Prop) : A ∨ B → B ∨ A := by intro h; cases h; right; exact h; left; exact h"),
    ("logic_not_not", "theorem t (P : Prop) : P → ¬¬P := by intro hp hnp; exact hnp hp"),
    ("logic_impl_trans", "theorem t (A B C : Prop) : (A → B) → (B → C) → (A → C) := by intro h1 h2 ha; exact h2 (h1 ha)"),

    # ── lattice / order ──
    ("order_refl", "theorem t (a : Nat) : a ≤ a := Nat.le_refl a"),
    ("order_trans", "theorem t (a b c : Nat) (h1 : a ≤ b) (h2 : b ≤ c) : a ≤ c := Nat.le_trans h1 h2"),
    ("order_antisymm", "theorem t (a b : Nat) (h1 : a ≤ b) (h2 : b ≤ a) : a = b := Nat.le_antisymm h1 h2"),

    # ── failure cases ──
    ("expect_fail_type_mismatch", "theorem t : Nat → String := λ n => n"),
    ("expect_fail_unsat", "theorem t (x : Nat) : x < x := by omega"),
    ("expect_fail_axiom", "theorem t : 1 = 0 := by native_decide"),
    ("expect_fail_timeout_like", "theorem t (a b : Nat) : a^10 + b^10 = (a+b)^10 := by nlinarith"),

    # ── deliberately complex ──
    ("complex_fib", "def fib : Nat → Nat | 0 => 0 | 1 => 1 | n+2 => fib (n+1) + fib n\ntheorem t (n : Nat) : fib (n+2) = fib (n+1) + fib n := by rfl"),
    ("complex_sum", "theorem t (n : Nat) : ∑ k in Finset.range n, k = n*(n-1)/2 := by sorry"),
]


def prove(code: str, name: str, url: str, timeout_s: int = 60) -> dict:
    """Send a Lean proof to a worker and return the response."""
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", "-X", "POST", f"{url}/lean/check",
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {PROOF_SERVER_TOKEN}",
         "-d", json.dumps({"code": code, "name": name})],
        capture_output=True, text=True, timeout=timeout_s,
    )
    if result.returncode != 0:
        return {"error": f"curl exit {result.returncode}: {result.stderr[:200]}", "ok": False}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"error": f"json: {e}", "raw": result.stdout[:300], "ok": False}


def build_receipt(response: dict, name: str, code: str, status: str) -> dict:
    """Build structural receipt v2 from proof worker response."""
    receipt = response.get("receipt", response)
    ok = response.get("ok", False)
    elapsed = receipt.get("elapsed_ms", 0)
    returncode = receipt.get("returncode", -1)

    struct = parse_equation(name)
    struct["equation_text"] = name.replace("_", " ")

    lines = code.strip().split("\n")
    imports = [l.split("import")[1].strip() for l in lines if l.strip().startswith("import")]
    proof_lines = [l for l in lines if not l.strip().startswith("import") and not l.strip().startswith("def ")]
    proof_script = proof_lines[0] if proof_lines else code

    shape_map = {
        "verified": "CognitiveLoadField",
        "failed": "HoldForUnlawfulOrUnderspecifiedShape",
        "timeout": "HoldForUnlawfulOrUnderspecifiedShape",
    }
    shape = shape_map.get(status, "HoldForUnlawfulOrUnderspecifiedShape")
    proof = build_proof_metrics(shape)
    domain = shape.replace("CognitiveLoadField", "analysis") \
                  .replace("HoldForUnlawfulOrUnderspecifiedShape", "unknown")

    return {
        "receipt_version": "rrc-proof-receipt-v2",
        "theorem_name": name,
        **struct,
        "domain": domain,
        "theorem_statement": code,
        "proof_script": proof_script,
        "imports": imports,
        "dependencies": imports,
        "source_hash": receipt.get("input_sha256", str(uuid.uuid4())),
        "environment_hash": receipt.get("generated_at_utc", datetime.now(timezone.utc).isoformat()),
        "status": status,
        "kernel_checked": ok,
        "returncode": returncode,
        "elapsed_ms": elapsed,
        "proof_metrics": proof,
        "metrics": {
            "statement_chars": len(code),
            "proof_chars": len(proof_script),
            "dependency_count": proof["dependency_count"],
            "import_count": len(imports),
            "tactic_count": proof["tactic_count"],
            "ast_depth_estimate": struct["ast_metrics"]["depth"],
        },
    }


def pist_classify(receipt: dict) -> dict:
    """Run pist-decompose on a structural receipt."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(receipt, f)
        fpath = f.name
    try:
        result = subprocess.run(
            [PIST_DECOMPOSE, fpath, "--num-leaves", "8"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return {"error": result.stderr[:200], "ok": False}
        return json.loads(result.stdout)
    finally:
        os.unlink(fpath)


def main():
    worker_url = os.environ.get("CANARY_WORKER_URL",
                                "http://100.110.163.82:8787")
    theorems = [(n, c) for n, c in CANARY_THEOREMS]
    print(f"Canary batch: {len(theorems)} theorems, worker={worker_url}", flush=True)

    receipts_path = os.path.join(os.path.dirname(__file__), "../..",
                                 "shared-data/pist_canary_receipts.jsonl")
    results_path = os.path.join(os.path.dirname(__file__), "../..",
                                "shared-data/pist_canary_results.jsonl")
    report_path = os.path.join(os.path.dirname(__file__), "../..",
                               "shared-data/pist_canary_report.json")

    rfile = open(receipts_path, "w")
    rslts = []

    for i, (name, code) in enumerate(theorems):
        print(f"\n[{i+1}/{len(theorems)}] {name:30s} ... ", end="", flush=True)
        t0 = time.time()

        try:
            resp = prove(code, name, worker_url)
            dt = time.time() - t0
        except subprocess.TimeoutExpired:
            resp = {"ok": False, "error": "timeout", "receipt": {"elapsed_ms": 60_000, "returncode": -1}}
            dt = 60.0

        ok = resp.get("ok", False)
        receipt = resp.get("receipt", resp)
        std = receipt.get("stdout", "")
        err = receipt.get("stderr", "")
        rc = receipt.get("returncode", -1)
        elapsed = receipt.get("elapsed_ms", int(dt * 1000))

        if "error" in resp and "timeout" in str(resp.get("error")):
            status = "timeout"
        elif ok and rc == 0:
            status = "verified"
        elif "error" in resp:
            status = "worker_error"
        elif not ok and "Lean" in str(std) or "error" in str(std):
            status = "elaboration_error"
        else:
            status = "failed"

        # Verify the proof result actually makes sense
        if status == "verified" and not std.strip() and not err.strip():
            status = "verified_empty_output"

        print(f"{status:25s} {dt:5.1f}s rc={rc}", flush=True)

        structural = build_receipt(resp, name, code, status)

        # Run PIST
        pist_result = pist_classify(structural)
        proxy = pist_result.get("rrc_shape", {}).get("proxy", {}).get("label", "?")
        exact = pist_result.get("rrc_shape", {}).get("exact", {}).get("label", "?")
        zmp = pist_result.get("spectral", {}).get("zero_mode_proxy_count", "?")
        mhash = pist_result.get("braid", {}).get("matrix_hash", "?")[:16]
        chash = pist_result.get("canonical_hash", "?")[:16]
        gap = pist_result.get("spectral", {}).get("symmetric_spectral_gap", 0)
        rank = pist_result.get("spectral", {}).get("rank_estimate", 0)
        lap0 = pist_result.get("spectral", {}).get("laplacian_zero_count", 0)

        print(f"         PIST→ proxy={proxy:30s} exact={exact:30s} ZMP={zmp} gap={gap:.3f}", flush=True)

        row = {
            "name": name, "status": status, "ok": ok, "returncode": rc,
            "elapsed_ms": elapsed, "wall_s": round(dt, 2),
            "proxy_shape": proxy, "exact_shape": exact,
            "zmp": zmp, "spectral_gap": gap, "rank_estimate": rank,
            "laplacian_zero_count": lap0,
            "matrix_hash": mhash, "canonical_hash": chash,
        }
        rslts.append(row)

        # Write receipt JSONL
        rfile.write(json.dumps(structural) + "\n")

    rfile.close()

    # ── Analysis ──
    print("\n" + "=" * 60, flush=True)
    print("CANARY REPORT", flush=True)
    print("=" * 60, flush=True)

    n = len(rslts)
    verified = sum(1 for r in rslts if r["status"] == "verified")
    failed = sum(1 for r in rslts if r["status"] != "verified")

    print(f"\nTotal: {n}", flush=True)
    print(f"Verified: {verified} ({verified/n*100:.0f}%)", flush=True)
    print(f"Failed/error: {failed} ({failed/n*100:.0f}%)", flush=True)
    print()

    # Status distribution
    statuses = Counter(r["status"] for r in rslts)
    print("Status distribution:", flush=True)
    for s, c in sorted(statuses.items()):
        print(f"  {s:30s}: {c:3d}", flush=True)
    print()

    # Shape distribution
    shape_counts = Counter(r["exact_shape"] for r in rslts)
    print("RRCShape distribution (exact):", flush=True)
    for s, c in sorted(shape_counts.items(), key=lambda x: -x[1]):
        print(f"  {s:35s}: {c:3d} ({c/n*100:.0f}%)", flush=True)
    print()

    # Unique hashes
    u_matrices = len(set(r["matrix_hash"] for r in rslts))
    u_canon = len(set(r["canonical_hash"] for r in rslts))
    u_spectra = len(set(json.dumps(r["spectral_gap"]) for r in rslts))
    print(f"Unique matrix hashes: {u_matrices}/{n} ({u_matrices/n*100:.0f}%)", flush=True)
    print(f"Unique canonical hashes: {u_canon}/{n} ({u_canon/n*100:.0f}%)", flush=True)
    print(f"Unique spectral gaps: {u_spectra}/{n}", flush=True)
    print()

    # Feature diversity
    gaps = [r["spectral_gap"] for r in rslts if isinstance(r["spectral_gap"], (int, float))]
    ranks = [r["rank_estimate"] for r in rslts if isinstance(r["rank_estimate"], int)]
    lap0s = [r["laplacian_zero_count"] for r in rslts if isinstance(r["laplacian_zero_count"], int)]
    print(f"Spectral gap: mean={sum(gaps)/len(gaps):.3f} range=[{min(gaps):.3f},{max(gaps):.3f}] uniq={len(set(gaps))}", flush=True)
    print(f"Rank estimate: mean={sum(ranks)/len(ranks):.1f} range=[{min(ranks)},{max(ranks)}] uniq={len(set(ranks))}", flush=True)
    print(f"Laplacian zero count: range=[{min(lap0s)},{max(lap0s)}] uniq={len(set(lap0s))}", flush=True)
    print()

    # Verified vs failed spectral comparison
    for label, fn in [("verified", lambda r: r["status"] == "verified"),
                       ("failed", lambda r: r["status"] != "verified")]:
        subset = [r for r in rslts if fn(r)]
        if len(subset) < 2:
            continue
        avg_gap = sum(r["spectral_gap"] for r in subset) / len(subset)
        print(f"{label} (n={len(subset)}): avg_gap={avg_gap:.3f}", flush=True)

    # Write results JSONL
    with open(results_path, "w") as f:
        for row in rslts:
            f.write(json.dumps(row) + "\n")

    # Write report
    report = {
        "n": n,
        "verified": verified,
        "failed": failed,
        "statuses": dict(statuses),
        "shape_distribution": dict(shape_counts),
        "unique_matrix_hashes": u_matrices,
        "unique_canonical_hashes": u_canon,
        "unique_spectral_gaps": u_spectra,
        "spectral_gap_stats": {
            "mean": round(sum(gaps)/len(gaps), 4),
            "min": round(min(gaps), 4),
            "max": round(max(gaps), 4),
            "unique": len(set(round(g, 6) for g in gaps)),
        },
        "rank_stats": {
            "mean": round(sum(ranks)/len(ranks), 2),
            "min": min(ranks),
            "max": max(ranks),
            "unique": len(set(ranks)),
        },
        "results": rslts,
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Receipts:  {receipts_path}", flush=True)
    print(f"Results:   {results_path}", flush=True)
    print(f"Report:    {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
