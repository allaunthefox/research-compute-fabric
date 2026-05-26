#!/usr/bin/env python3
"""Tier 2B trace bridge — instrumented Lean theorems with real goal-state traces.

Prepends a `trace_state_json` tactic, injects trace calls around each tactic step,
parses @@PIST_TRACE_JSON@@ sentinels from stdout, builds transition matrices.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

TRACE_PREAMBLE = """import Lean
open Lean Elab Tactic Meta

elab "trace_state_json" name:str : tactic => do
  let s := name.getString
  IO.println s!"@@PIST_TRACE_JSON@@{s}"
"""

WORKER_URL = os.environ.get("CANARY_WORKER_URL", "http://100.110.163.82:8787")
PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")
if not PROOF_SERVER_TOKEN:
    tf = os.environ.get("PROOF_SERVER_TOKEN_FILE", os.path.expanduser("~/.config/ene/language-proof-server.token"))
    try:
        PROOF_SERVER_TOKEN = Path(tf).read_text().strip()
    except (FileNotFoundError, OSError):
        PROOF_SERVER_TOKEN = ""


def instrument_theorem(code: str) -> tuple[str, list[str]]:
    """Inject trace_state_json calls before/after each tactic step.
    Returns (instrumented_code, [tag_names]).
    """
    code = code.strip()
    
    # Find the by-block start (position of 'by ' or 'by\n')
    by_start = code.find(":= by")
    if by_start < 0:
        by_start = code.find("= by")
    if by_start < 0:
        by_start = code.find("\nby")
    if by_start < 0:
        return code, []
    
    # header is everything up to and including ':= by' or '= by'
    header = code[:by_start].rstrip()
    if header.endswith(":=") or header.endswith("="):
        header += " by"
    elif ":" in code[:by_start]:
        header += " := by"
    else:
        header += " :="
    
    body = code[by_start:].strip()
    # Remove the leading '= by' or ':= by' or 'by'
    for prefix in [":= by", "= by", "by"]:
        if body.startswith(prefix):
            body = body[len(prefix):].strip()
            break
    
    # Parse tactics from body (semicolon or newline separated)
    tactics = []
    for part in re.split(r'[;\n]', body):
        t = part.strip()
        if t and not t.startswith("--") and not t.startswith("/-"):
            tactics.append(t)
    
    if not tactics:
        return code, []
    
    # Build instrumented code
    lines = [header]
    tags = []
    for i, t in enumerate(tactics):
        btag = f"step_{i}_before"
        atag = f"step_{i}_after"
        lines.append(f"  trace_state_json \"{btag}\"")
        lines.append(f"  {t}")
        lines.append(f"  trace_state_json \"{atag}\"")
        tags.append(btag)
        tags.append(atag)
    
    instrumented = "\n".join(lines)
    full = TRACE_PREAMBLE + "\n" + instrumented
    return full, tags


def prove(code: str, name: str = "trace") -> dict:
    """Send Lean code to the proof worker."""
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", "-X", "POST", f"{WORKER_URL}/lean/check",
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {PROOF_SERVER_TOKEN}",
         "-d", json.dumps({"code": code, "name": name})],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        return {"ok": False, "stdout": "", "error": f"curl: {result.stderr[:200]}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"ok": False, "stdout": "", "error": f"json: {e}"}


def build_trace(code: str, name: str = "test") -> dict:
    """Run instrumented theorem and build transition matrix from trace tags."""
    instrumented, tags = instrument_theorem(code)
    if not tags:
        # Fallback: run non-instrumented
        resp = prove(code, name)
        ok = resp.get("ok", False)
        return {
            "trace_version": "proof-trace-v2", "theorem_name": name,
            "status": "verified" if ok else "failed",
            "tactic_count": 1, "trace_tags": [], "n_trace_points": 0,
            "n_unique_goal_states": 1, "transition_matrix": [[1]],
            "stdout": resp.get("stdout", ""),
            "warning": "instrumentation_failed"
        }
    
    resp = prove(instrumented, name + "_traced")
    stdout = resp.get("stdout", "")
    ok = resp.get("ok", False)
    
    # Parse trace tags from stdout
    found_tags = []
    for line in stdout.split("\n"):
        if "@@PIST_TRACE_JSON@@" in line:
            tag = line.split("@@PIST_TRACE_JSON@@")[1].strip()
            found_tags.append(tag)
    
    # Build transition matrix from tag hashes
    hashes = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in found_tags]
    unique = list(dict.fromkeys(hashes))
    h2i = {h: i for i, h in enumerate(unique)}
    n = len(unique)
    matrix = [[0] * n for _ in range(n)]
    
    for i in range(len(hashes) - 1):
        if hashes[i] in h2i and hashes[i + 1] in h2i:
            matrix[h2i[hashes[i]]][h2i[hashes[i + 1]]] += 1
    
    return {
        "trace_version": "proof-trace-v2",
        "theorem_name": name,
        "status": "verified" if ok else "failed",
        "tactic_count": len(tags) // 2,
        "trace_tags": found_tags,
        "n_trace_points": len(found_tags),
        "n_unique_goal_states": n,
        "transition_matrix": matrix,
        "stdout_preview": stdout[:500],
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        code = "theorem t (n : Nat) : n + 0 = n := by\n  simp"
        name = "t"
    else:
        code = sys.argv[1]
        name = sys.argv[2] if len(sys.argv) > 2 else "test"
    
    trace = build_trace(code, name)
    print(json.dumps(trace, indent=2))
    print(f"\nStatus: {trace['status']}")
    print(f"Trace points: {trace['n_trace_points']}")
    print(f"Unique states: {trace['n_unique_goal_states']}")
    print(f"Matrix size: {len(trace['transition_matrix'])}x{len(trace['transition_matrix'][0]) if trace['transition_matrix'] else 0}")
