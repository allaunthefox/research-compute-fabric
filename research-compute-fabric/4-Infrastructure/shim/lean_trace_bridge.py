#!/usr/bin/env python3
"""Lean Trace Bridge — captures tactic-level goal state transitions.

Tier 2 MVP: splits a Lean proof into tactic steps, replays each prefix
through the proof worker, and builds a structured trace with goal-state
snapshots captured from Lean's error output.

Usage:
    python3 lean_trace_bridge.py <canary_receipt.jsonl [index]> [--out trace.json]
    python3 lean_trace_bridge.py --code 'theorem t : 1+1=2 := by omega' --name t [--out trace.json]
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")
if not PROOF_SERVER_TOKEN:
    tf = os.environ.get("PROOF_SERVER_TOKEN_FILE",
                        os.path.expanduser("~/.config/ene/language-proof-server.token"))
    try:
        PROOF_SERVER_TOKEN = Path(tf).read_text().strip()
    except (FileNotFoundError, OSError):
        PROOF_SERVER_TOKEN = ""

WORKER_URL = os.environ.get("CANARY_WORKER_URL", "http://100.110.163.82:8787")


def split_tactic_lines(code: str) -> list[str]:
    """Split a Lean proof into individual tactic steps.
    
    Handles single-line proofs (by simp), semicolon-separated (by simp; omega),
    and indented multi-line blocks (induction with case branches).
    """
    lines = code.strip().split("\n")
    
    # Find the `by` block
    by_content_lines = []
    found_by = False
    
    for line in lines:
        stripped = line.strip()
        
        # Detect `:= by` on the same line
        if not found_by and ":= by " in stripped:
            parts = stripped.split(":= by ", 1)
            by_content_lines.append(parts[1].strip())
            found_by = True
            continue
        if not found_by and ":= by" in stripped:
            found_by = True
            continue
        
        if not found_by:
            # Check for standalone `by` on this line
            if stripped == "by":
                found_by = True
                continue
            continue  # still in header
        
        # We're in the by-block
        if stripped and not stripped.startswith("--") and not stripped.startswith("/-"):
            by_content_lines.append(stripped)
    
    by_content = "\n".join(by_content_lines).strip()
    if not by_content:
        return [code]
    
    # Merge continuation lines into their parent tactic:
    # - Lines starting with | are induction case branches
    # - Lines at deeper indent continue the previous tactic
    # - Then split on semicolons for finer granularity
    merged = []
    current = ""
    for line in by_content_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if current and not stripped.startswith("|"):
            # Check if this is a continuation (indented) or new tactic
            if line[0].isspace():
                current += " " + stripped
            else:
                merged.append(current.strip())
                current = stripped
        else:
            current += (" " if current else "") + stripped
    if current.strip():
        merged.append(current.strip())
    
    # Split on semicolons for truly independent steps
    tactics = []
    for m in merged:
        parts = re.split(r';', m)
        tactics.extend(p.strip() for p in parts if p.strip())
    
    return tactics if tactics else [code]
    
    # Fallback: split on semicolons if we got nothing
    if not tactics:
        for part in re.split(r'[;\n]', by_content):
            t = part.strip()
            if t:
                tactics.append(t)
    
    return tactics if tactics else [code]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prove_step(code: str, timeout_s: int = 120) -> dict:
    """Send Lean code to the proof worker."""
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", "-X", "POST",
         f"{WORKER_URL}/lean/check",
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {PROOF_SERVER_TOKEN}",
         "-d", json.dumps({"code": code, "name": "trace_step"})],
        capture_output=True, text=True, timeout=timeout_s,
    )
    if result.returncode != 0:
        return {"ok": False, "error": f"curl: {result.stderr[:200]}", "stdout": "", "stderr": ""}
    try:
        resp = json.loads(result.stdout)
        receipt = resp.get("receipt", resp)
        return {
            "ok": resp.get("ok", False),
            "stdout": receipt.get("stdout", ""),
            "stderr": receipt.get("stderr", ""),
            "returncode": receipt.get("returncode", -1),
            "elapsed_ms": receipt.get("elapsed_ms", 0),
            "error": receipt.get("error", ""),
        }
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"json: {e}", "stdout": result.stdout[:500], "stderr": ""}


def extract_goal_text(output: str, is_error: bool = False) -> str:
    """Extract the goal state from Lean's output.
    
    Lean prints the goal state when a tactic block is incomplete.
    The goal appears after 'unsolved goals' or as the error context.
    """
    # Try to find the goal statement
    patterns = [
        r"(?<=unsolved goals\n).*?(?=\n\n)",
        r"(?<=⊢\n).*?(?=\n|$)",
        r"(?<=⊢ ).*$",
        r"(?<=expected\n).*?(?=\n|$)",
    ]
    for p in patterns:
        m = re.search(p, output, re.DOTALL)
        if m and m.group().strip():
            return m.group().strip()[:500]
    
    # Fallback: last significant line
    lines = [l.strip() for l in output.split("\n") if l.strip() and "error" not in l.lower()]
    return lines[-1][:500] if lines else output[:500]


def extract_hypotheses(output: str) -> list[str]:
    """Extract hypothesis names from the goal context."""
    hyps = []
    for m in re.finditer(r"(?:^|\n)(\w+)\s*:", output):
        hyps.append(m.group(1))
    return hyps[:20]


def count_symbols(text: str) -> dict:
    """Count operator symbols in a goal text."""
    ops = {
        "+": 0, "*": 0, "-": 0, "/": 0, "^": 0,
        "≤": 0, "≥": 0, "<": 0, ">": 0, "=": 0,
        "∧": 0, "∨": 0, "→": 0, "¬": 0, "∀": 0, "∃": 0,
        "∑": 0, "∫": 0, "∪": 0, "∩": 0, "⊆": 0,
    }
    for char in text:
        if char in ops:
            ops[char] += 1
    return {k: v for k, v in ops.items() if v > 0}


def build_trace(code: str, name: str = "unnamed") -> dict:
    """Build a ProofTraceReceipt by replaying tactic steps."""
    tactics = split_tactic_lines(code)
    
    if not tactics or tactics == [code]:
        result = prove_step(code)
        ok = result.get("ok", False)
        return {
            "trace_version": "proof-trace-v1",
            "receipt_hash": sha256(code),
            "theorem_name": name,
            "status": "verified" if ok else "failed",
            "tactic_count": 1,
            "total_elapsed_ms": result.get("elapsed_ms", 0),
            "steps": [{"step": 0, "tactic": code, "result": "success" if ok else "failure"}],
            "goal_transition_matrix": [[1] if ok else [0]],
            "flexure_joints": [],
            "warning": "full_code_fallback"
        }
    
    # Reconstruct the theorem header (everything before `:= by` or `by`)
    by_pos = code.rfind(":= by")
    if by_pos < 0:
        by_pos = code.rfind("\nby")
        if by_pos < 0:
            by_pos = code.find("by ")
    header = code[:by_pos] + ":= by" if by_pos > 0 else code.split("by")[0]
    
    steps = []
    prev_stdout = ""
    prev_stderr = ""
    
    for i, tactic in enumerate(tactics):
        # Build incremental proof
        prefix = header + "\n"
        for j in range(i + 1):
            prefix += "  " + tactics[j] + "\n"
        
        t0 = time.time()
        result = prove_step(prefix)
        dt = time.time() - t0
        
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        ok = result.get("ok", False)
        
        goal_before = extract_goal_text(prev_stdout + "\n" + prev_stderr)
        goal_after = extract_goal_text(stdout + "\n" + stderr)
        hyps_before = extract_hypotheses(prev_stdout + "\n" + prev_stderr)
        hyps_after = extract_hypotheses(stdout + "\n" + stderr)
        
        delta = {
            "symbol_delta": len(count_symbols(goal_after)) - len(count_symbols(goal_before)),
            "hypothesis_delta": len(hyps_after) - len(hyps_before),
            "goal_count_delta": (len(hyps_after) + 1 if goal_after else 0) - (len(hyps_before) + 1 if goal_before else 0),
        }
        
        steps.append({
            "step": i,
            "tactic": tactic,
            "before_goal_hash": sha256(goal_before) if goal_before else "",
            "after_goal_hash": sha256(goal_after) if goal_after else "",
            "before_goal_text": goal_before[:300],
            "after_goal_text": goal_after[:300],
            "goal_count_before": len(hyps_before) + 1 if goal_before else 0,
            "goal_count_after": len(hyps_after) + 1 if goal_after else 0,
            "hypothesis_count_before": len(hyps_before),
            "hypothesis_count_after": len(hyps_after),
            "operator_count_before": len(count_symbols(goal_before)),
            "operator_count_after": len(count_symbols(goal_after)),
            "delta": delta,
            "elapsed_ms": result.get("elapsed_ms", int(dt * 1000)),
            "result": "success" if ok else "failure",
            "stdout_preview": stdout[:200],
            "stderr_preview": stderr[:200],
        })
        
        prev_stdout = stdout
        prev_stderr = stderr
    
    # Final verification
    final_result = prove_step(code)
    
    # Build transition matrix
    hashes = []
    for s in steps:
        if s.get("before_goal_hash"):
            hashes.append(s["before_goal_hash"])
    if steps:
        hashes.append(steps[-1].get("after_goal_hash", ""))
    unique = list(dict.fromkeys(hashes))
    h2i = {h: i for i, h in enumerate(unique)}
    n = len(unique)
    matrix = [[0] * n for _ in range(n)]
    for s in steps:
        bh = s.get("before_goal_hash", "")
        ah = s.get("after_goal_hash", "")
        if bh in h2i and ah in h2i:
            matrix[h2i[bh]][h2i[ah]] += 1
    
    # Extract flexure joints
    joints = []
    for s in steps:
        d = s.get("delta", {})
        score = abs(d.get("goal_count_delta", 0)) * 3 + abs(d.get("hypothesis_delta", 0)) + abs(d.get("symbol_delta", 0)) * 2
        joints.append({
            "step": s["step"],
            "tactic": s["tactic"],
            "tactic_family": classify_tactic(s["tactic"]),
            "delta_score": score,
            "delta": d,
            "result": s.get("result", "unknown"),
        })
    
    return {
        "trace_version": "proof-trace-v1",
        "receipt_hash": sha256(code),
        "theorem_name": name,
        "status": "verified" if final_result.get("ok") else "failed",
        "tactic_count": len(steps),
        "total_elapsed_ms": sum(s.get("elapsed_ms", 0) for s in steps),
        "steps": steps,
        "goal_transition_matrix": matrix,
        "flexure_joints": joints,
    }


def build_transition_matrix(steps: list[dict]) -> list[list[int]]:
    """Build an adjacency matrix from goal-state hash transitions."""
    n = len(steps) + 1  # +1 for the final state
    matrix = [[0] * n for _ in range(n)]
    
    # Collect unique goal hashes
    hashes = []
    for s in steps:
        if s.get("before_goal_hash"):
            hashes.append(s["before_goal_hash"])
    if steps:
        hashes.append(steps[-1].get("after_goal_hash", ""))
    
    # Assign indices
    unique = list(dict.fromkeys(hashes))
    hash_to_idx = {h: i for i, h in enumerate(unique)}
    
    for s in steps:
        bh = s.get("before_goal_hash", "")
        ah = s.get("after_goal_hash", "")
        if bh in hash_to_idx and ah in hash_to_idx:
            i = hash_to_idx[bh]
            j = hash_to_idx[ah]
            matrix[i][j] += 1
    
    return matrix


def extract_flexure_joints(steps: list[dict]) -> list[dict]:
    """Extract flexure joints from tactic transitions.
    
    A flexure is a transition that significantly changes the goal state.
    """
    joints = []
    for s in steps:
        d = s.get("delta", {})
        score = (
            abs(d.get("goal_count_delta", 0)) * 3
            + abs(d.get("hypothesis_delta", 0))
            + abs(d.get("symbol_delta", 0)) * 2
        )
        joint = {
            "step": s["step"],
            "tactic": s["tactic"],
            "tactic_family": classify_tactic(s["tactic"]),
            "delta_score": score,
            "delta": d,
            "result": s.get("result", "unknown"),
        }
        joints.append(joint)
    return joints


def classify_tactic(tactic: str) -> str:
    """Classify a tactic into a family."""
    tactic_lower = tactic.lower()
    if "simp" in tactic_lower:
        return "normalization"
    if "omega" in tactic_lower:
        return "arithmetic"
    if "ring" in tactic_lower or "nlinarith" in tactic_lower:
        return "algebraic"
    if "induction" in tactic_lower:
        return "induction"
    if "cases" in tactic_lower:
        return "case_analysis"
    if "rw" in tactic_lower or "rewrite" in tactic_lower:
        return "rewrite"
    if "apply" in tactic_lower or "exact" in tactic_lower:
        return "discharge"
    if "intro" in tactic_lower or "refine" in tactic_lower:
        return "introduction"
    if "calc" in tactic_lower:
        return "calculation"
    if "rfl" in tactic_lower:
        return "reflexivity"
    if "constructor" in tactic_lower:
        return "constructor"
    if "have" in tactic_lower or "let" in tactic_lower:
        return "lemma_introduction"
    return "unknown"


def main():
    if len(sys.argv) < 2:
        print("Usage:", file=sys.stderr)
        print("  python3 lean_trace_bridge.py --code 'theorem t ... := by ...' --name t", file=sys.stderr)
        print("  python3 lean_trace_bridge.py shared-data/pist_canary_receipts.jsonl [index]", file=sys.stderr)
        return 1

    out_path = None
    code = None
    name = "unnamed"

    # Parse arguments
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--code" and i + 1 < len(args):
            code = args[i + 1]
        elif arg == "--name" and i + 1 < len(args):
            name = args[i + 1]
        elif arg == "--out" and i + 1 < len(args):
            out_path = args[i + 1]

    # If no --code, check for receipts file
    if code is None:
        for arg in args:
            if arg.endswith(".jsonl") and not arg.startswith("--"):
                idx = 0
                for j, a2 in enumerate(args):
                    if a2 == arg and j + 1 < len(args) and args[j + 1].isdigit():
                        idx = int(args[j + 1])
                with open(arg) as f:
                    for line_idx, line in enumerate(f):
                        if line_idx == idx:
                            receipt = json.loads(line)
                            code = receipt.get("theorem_statement", "")
                            name = receipt.get("theorem_name", f"receipt_{idx}")
                            break
                break
    
    if code is None:
        print("ERROR: No code provided", file=sys.stderr)
        return 1

    print(f"Building trace for: {name}", flush=True)
    print(f"Code length: {len(code)} chars", flush=True)

    trace = build_trace(code, name)
    
    steps = trace.get("steps", [])
    print(f"\nTrace complete:")
    print(f"  Steps: {len(steps)}")
    print(f"  Status: {trace.get('status')}")
    print(f"  Total time: {trace.get('total_elapsed_ms')}ms")
    
    families = {}
    for s in steps:
        j = s.get("flexure_joints", []) if isinstance(s, dict) else []
    for j in trace.get("flexure_joints", []):
        fam = j.get("tactic_family", "?")
        families[fam] = families.get(fam, 0) + 1
    
    print(f"\nTactic families:")
    for fam, count in sorted(families.items(), key=lambda x: -x[1]):
        print(f"  {fam:20s}: {count:3d}")
    
    print(f"\nTransition matrix: {len(trace.get('goal_transition_matrix', []))}x"
          f"{len(trace.get('goal_transition_matrix', [[]]))}")
    
    # Save
    if out_path:
        with open(out_path, "w") as f:
            json.dump(trace, f, indent=2)
        print(f"\nTrace saved: {out_path}", flush=True)
    else:
        # Print summary
        print(f"\nStep details:")
        for s in steps[:5]:
            jd = s.get("delta", {})
            print(f"  [{s['step']}] {s['tactic']:30s} → {s['result']:8s} "
                  f"|{s.get('goal_count_before',0)}→{s.get('goal_count_after',0)}| "
                  f"d(g)={jd.get('goal_count_delta',0):+d} "
                  f"d(h)={jd.get('hypothesis_delta',0):+d}")
        if len(steps) > 5:
            print(f"  ... ({len(steps) - 5} more steps)")
    
    return 0


if __name__ == "__main__":
    main()
