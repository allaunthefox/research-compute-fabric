#!/usr/bin/env python3
"""Prove a Lean theorem and classify its spectral shape.

Usage:
    python3 pist_prove_and_classify.py --code 'theorem t: 1+1=2 := by omega' --name my_theorem
"""
# PARTIAL BOUNDARY: contains domain logic; not a provable surface. Port to Lean/RRC before treating as authoritative.

import argparse
import json
import os
from rds_connect import connect_rds
import subprocess
import sys
import tempfile
import uuid
from collections import Counter
from pathlib import Path

# Import receipt builder from validation script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from validate_rrc_predictions import parse_equation, build_proof_metrics

PROOF_SERVER_URLS = os.environ.get(
    "PROOF_SERVER_URLS",
    "http://54.236.176.28:8787,http://100.110.163.82:8787,http://100.102.173.61:8787,http://100.85.244.73:8787",
)
PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")
if not PROOF_SERVER_TOKEN:
    token_file = os.environ.get("PROOF_SERVER_TOKEN_FILE",
                                os.path.expanduser("~/.config/ene/language-proof-server.token"))
    try:
        PROOF_SERVER_TOKEN = Path(token_file).read_text().strip()
    except (FileNotFoundError, OSError):
        PROOF_SERVER_TOKEN = ""

PIST_DECOMPOSE = os.environ.get(
    "PIST_DECOMPOSE_BIN",
    "/home/allaun/.local/share/opencode/worktree/"
    "0b42981cf7f7d5e172b1e93f8d4bb64a3dd63962/Turn-and-Burn/infra/rust/"
    "ene-rds/target/release/pist-decompose",
)


def prove(code: str, name: str = "unnamed", url: str | None = None) -> dict:
    """Send a Lean proof to a worker and return the response."""
    if not PROOF_SERVER_TOKEN:
        print("ERROR: No proof server token set.", file=sys.stderr)
        sys.exit(1)

    if url is None:
        url = PROOF_SERVER_URLS.split(",")[0].strip()

    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", "-X", "POST", f"{url}/lean/check",
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {PROOF_SERVER_TOKEN}",
         "-d", json.dumps({"code": code, "name": name})],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        return {"error": result.stderr, "ok": False}
    try:
        data = json.loads(result.stdout)
        return data if isinstance(data, dict) else {"error": "not json", "raw": result.stdout[:500], "ok": False}
    except json.JSONDecodeError as e:
        return {"error": f"json decode: {e}", "ok": False}


def build_structural_receipt(proof_response: dict, name: str, code: str) -> dict:
    """Convert a proof worker response into a structural receipt v2."""
    receipt = proof_response.get("receipt", proof_response)
    stdout = receipt.get("stdout", "")
    stderr = receipt.get("stderr", "")
    ok = proof_response.get("ok", False)
    elapsed = receipt.get("elapsed_ms", 0)

    # Parse the Lean code for structural features
    struct = parse_equation(name)
    lines = code.strip().split("\n")
    imports = [l.split("import")[1].strip() for l in lines if l.strip().startswith("import")]

    # The name doubles as equation_text for canonicalization
    eq_name = name.replace("_", " ").replace("theorem ", "").strip()
    struct["equation_text"] = eq_name

    # Determine shape from proof style
    if "omega" in code or "arith" in code or "simp" in code:
        shape = "CognitiveLoadField"
    elif "calc" in code or "rw" in code:
        shape = "SignalShapedRouteCompiler"
    elif "induction" in code or "cases" in code:
        shape = "ProjectableGeometryTopology"
    elif "ring" in code or "field_simp" in code:
        shape = "CadForceProbeReceipt"
    elif "apply" in code or "exact" in code:
        shape = "LogogramProjection"
    else:
        shape = "HoldForUnlawfulOrUnderspecifiedShape"

    proof = build_proof_metrics(shape)
    domain = shape.replace("CognitiveLoadField", "analysis") \
                  .replace("SignalShapedRouteCompiler", "topology") \
                  .replace("ProjectableGeometryTopology", "geometry") \
                  .replace("CadForceProbeReceipt", "physics") \
                  .replace("LogogramProjection", "symbolic") \
                  .replace("HoldForUnlawfulOrUnderspecifiedShape", "unknown")

    proof_lines = [l for l in lines if not l.strip().startswith("import") and l.strip()]
    proof_script = proof_lines[0] if proof_lines else code

    return {
        "receipt_version": "rrc-proof-receipt-v2",
        "theorem_name": name,
        **struct,
        "domain": domain,
        "theorem_statement": code,
        "proof_script": proof_script,
        "imports": imports,
        "dependencies": imports,
        "source_hash": f"{name}_{ok}_{elapsed}",
        "environment_hash": f"lean4-v4.30.0-{ok}",
        "status": "verified" if ok else "failed",
        "kernel_checked": ok,
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


def pist_classify(receipt: dict, dry_run: bool = False) -> dict:
    """Run pist-decompose on a structural receipt."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(receipt, f)
        fpath = f.name
    try:
        if dry_run:
            with open(fpath) as f:
                return {"receipt": json.load(f), "dry_run": True}
        result = subprocess.run(
            [PIST_DECOMPOSE, fpath, "--num-leaves", "8"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return {"error": result.stderr, "ok": False}
        return json.loads(result.stdout)
    finally:
        os.unlink(fpath)


def insert_classification(conn, receipt, pist_result):
    """Insert the classified result into ene.artifacts."""
    import psycopg2
    cur = conn.cursor()
    hash_val = pist_result.get("canonical_hash", pist_result.get("receipt_hash", "?"))[:16]
    label = pist_result.get("rrc_shape", {}).get("exact", {}).get("label", "unknown")
    content = json.dumps({
        "receipt_hash": pist_result.get("receipt_hash", ""),
        "theorem": receipt["theorem_name"],
        "rrc_shape": label,
        "spectral": pist_result.get("spectral", {}),
    })
    import hashlib
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    metadata = json.dumps({"pist_ready": True, "rrc_shape": label,
                           "classification_basis": "exact_spectral_v1",
                           "source": "live_lean_proof"})
    cur.execute(
        "INSERT INTO ene.artifacts (path, kind, language, title, content, content_hash, metadata) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb) ON CONFLICT (path) DO UPDATE SET metadata = %s::jsonb",
        (f"receipts/live/{hash_val}.json", "pist_receipt", "lean",
         f"PIST: {label} — {receipt['theorem_name']}", content, content_hash, metadata, metadata),
    )
    conn.commit()
    cur.close()
    return hash_val


def main():
    parser = argparse.ArgumentParser(description="Prove + classify a Lean theorem")
    parser.add_argument("--code", default="theorem t: 1+1=2 := by native_decide")
    parser.add_argument("--name", default="t")
    parser.add_argument("--url", default="http://100.110.163.82:8787")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--insert", action="store_true")
    args = parser.parse_args()

    print("1. Sending to proof worker...", flush=True)
    response = prove(args.code, args.name, args.url)
    if not response.get("ok"):
        print(f"   Proof failed: {response.get('error', 'unknown')}", flush=True)
        print(f"   stdout: {response.get('receipt', {}).get('stdout', '')[:200]}", flush=True)

    print("2. Building structural receipt...", flush=True)
    receipt = build_structural_receipt(response, args.name, args.code)
    print(f"   Theorem: {args.name}", flush=True)
    print(f"   RRCShape (inferred): {receipt.get('domain', '?')}", flush=True)

    print("3. Running PIST decomposition...", flush=True)
    pist_result = pist_classify(receipt, args.dry_run)
    if "error" in pist_result:
        print(f"   ERROR: {pist_result['error']}", flush=True)
        return 1

    if args.dry_run:
        print(json.dumps(pist_result, indent=2))
        return 0

    proxy_label = pist_result.get("rrc_shape", {}).get("proxy", {}).get("label", "?")
    exact_label = pist_result.get("rrc_shape", {}).get("exact", {}).get("label", "?")
    zmp = pist_result.get("spectral", {}).get("zero_mode_proxy_count", "?")
    print(f"   Proxy shape: {proxy_label} (ZMP={zmp})", flush=True)
    print(f"   Exact shape: {exact_label}", flush=True)

    if args.insert:
        print("4. Inserting into RDS...", flush=True)
        conn = connect_rds()
        hash_val = insert_classification(conn, receipt, pist_result)
        print(f"   Inserted as: receipts/live/{hash_val}.json", flush=True)
        conn.close()

    print("Done.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
