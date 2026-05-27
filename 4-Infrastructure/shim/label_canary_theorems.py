#!/usr/bin/env python3
"""Generate ground-truth multi-labels for the 42 canary theorems.

Reads canary receipts + results, infers labels from Lean code and proof output.
Outputs shared-data/pist_canary_ground_truth_labels.jsonl
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "../..",
                            "shared-data/pist_canary_results.jsonl")
RECEIPTS_PATH = os.path.join(os.path.dirname(__file__), "../..",
                             "shared-data/pist_canary_receipts.jsonl")
LABELS_PATH = os.path.join(os.path.dirname(__file__), "../..",
                           "shared-data/pist_canary_ground_truth_labels.jsonl")


def parse_domain(code: str) -> str:
    """Infer theorem domain from Lean code."""
    code_lower = code.lower()
    if "list" in code_lower and ("map" in code_lower or "reverse" in code_lower or "length" in code_lower):
        return "list"
    if "set" in code_lower and ("union" in code_lower or "inter" in code_lower):
        return "set"
    if "prop" in code_lower and ("∧" in code or "∨" in code or "→" in code or "¬" in code):
        return "logic"
    if "≤" in code or "≥" in code or "order" in code_lower or "le_refl" in code or "le_trans" in code:
        return "order"
    if "ring" in code_lower or "mul_comm" in code or "*" in code:
        return "algebra"
    if "gcd" in code_lower or "nat." in code_lower or "+" in code or "omega" in code_lower:
        return "arithmetic"
    if "def " in code:
        return "fixed_point"
    if "induction" in code_lower:
        return "induction"
    return "other"


def parse_proof_method(code: str) -> str:
    """Infer primary proof method from proof script.
    
    Handles both full theorem statements and bare by-blocks.
    """
    # Extract the by-block if present
    m = re.search(r'by\s+(.+?)$', code)
    if m:
        proof = m.group(1).strip()
    else:
        proof = code.strip()

    if not proof:
        return "unknown"

    if "omega" in proof:
        return "omega"
    if "nlinarith" in proof:
        return "nlinarith"
    if "ring" in proof:
        return "ring"
    if "simp" in proof and "induction" not in proof:
        return "simp"
    if "induction" in proof:
        return "induction"
    if "rw " in proof or "rewrite" in proof:
        return "rewrite"
    if "rfl" in proof:
        return "rfl"
    if "cases" in proof:
        return "cases"
    if "apply" in proof or "exact" in proof:
        return "apply"
    if "intro" in proof:
        return "intro"
    if "calc" in proof:
        return "calc"
    if "native_decide" in proof:
        return "native_decide"
    if "sorry" in proof:
        return "incomplete"
    return "unknown"


def parse_obstruction(stdout: str, stderr: str, status: str, code: str) -> str | None:
    """Infer obstruction type from proof output."""
    if status == "verified" or "verified" in status:
        return None
    combined = (stdout + " " + stderr).lower()
    if "timeout" in status or "timeout" in combined:
        return "timeout"
    if "type mismatch" in combined or "typeMismatch" in combined:
        return "type_mismatch"
    if "failed to synthesize" in combined or "synthInstance" in combined:
        return "missing_instance"
    if "unknown identifier" in combined or "unknownConstant" in combined:
        return "missing_lemma"
    if "unsat" in combined or "contradiction" in combined:
        return "unsatisfiable_goal"
    if "omega" in combined and "could not prove" in combined:
        return "nonlinear_arithmetic"
    if "coercion" in combined:
        return "coercion_gap"
    if "simp" in combined and "did not simplify" in combined:
        return "simplifier_gap"
    if "stack overflow" in combined or "recursion" in combined:
        return "recursion_limit"
    if "no applicable" in combined:
        return "no_applicable_tactic"
    return "other"


def infer_joint_label(domain: str, proof_method: str, obstruction: str | None, code: str) -> str:
    """Infer the type of proof joint from domain + method."""
    if obstruction:
        return f"{domain}_{obstruction}"
    if proof_method == "rfl":
        return "definitional_equality"
    if proof_method == "simp":
        return "rewrite_normalization"
    if proof_method == "omega":
        return "linear_constraint_closure"
    if proof_method == "nlinarith":
        return "nonlinear_constraint_closure"
    if proof_method == "induction":
        return "inductive_step"
    if proof_method == "rewrite":
        return "equality_chaining"
    if proof_method == "apply":
        return "rule_application"
    if proof_method == "cases":
        return "case_analysis"
    if proof_method == "intro":
        return "implication_introduction"
    if proof_method == "calc":
        return "calculational_proof"
    if proof_method == "incomplete":
        return "incomplete_proof"
    return f"{domain}_{proof_method}"


def infer_rrc_shape(domain: str, proof_method: str, obstruction: str | None, code: str) -> str:
    """Map domain + proof method to RRCShape."""
    if obstruction:
        return "HoldForUnlawfulOrUnderspecifiedShape"
    if proof_method in ("rfl", "simp"):
        return "CognitiveLoadField"
    if proof_method in ("omega", "nlinarith", "ring"):
        return "SignalShapedRouteCompiler"
    if proof_method == "induction":
        return "ProjectableGeometryTopology"
    if proof_method in ("rewrite", "calc"):
        return "CadForceProbeReceipt"
    if proof_method in ("apply", "cases", "intro"):
        return "LogogramProjection"
    if domain in ("logic", "order"):
        return "LogogramProjection"
    return "HoldForUnlawfulOrUnderspecifiedShape"


def find_in_receipt(receipts: list[dict], name: str) -> dict | None:
    for r in receipts:
        if r.get("theorem_name") == name:
            return r
    return None


def main():
    # Load results
    results = []
    with open(RESULTS_PATH) as f:
        for line in f:
            results.append(json.loads(line))

    # Load receipts
    receipts = []
    with open(RECEIPTS_PATH) as f:
        for line in f:
            receipts.append(json.loads(line))

    print(f"Loaded {len(results)} results, {len(receipts)} receipts", flush=True)

    labels = []
    for r in results:
        name = r["name"]
        receipt = find_in_receipt(receipts, name)
        code = receipt.get("theorem_statement", "") if receipt else ""
        stdout = receipt.get("theorem_statement", "") if receipt else ""

        status = r["status"]
        proof_method = parse_proof_method(code)
        domain = parse_domain(code)
        obstruction = parse_obstruction(
            r.get("stdout", ""),
            r.get("stderr", ""),
            status,
            code,
        )
        joint = infer_joint_label(domain, proof_method, obstruction, code)
        rrc = infer_rrc_shape(domain, proof_method, obstruction, code)

        labels.append({
            "theorem_name": name,
            "canonical_hash": r.get("canonical_hash", ""),
            "proof_status": "verified" if "verified" in status else status,
            "domain_label": domain,
            "proof_method_label": proof_method,
            "obstruction_label": obstruction,
            "joint_label": joint,
            "manual_rrc_shape": rrc,
            "label_confidence": "auto",
            "notes": code[:80] if code else "",
        })

    # Print distribution
    print(f"\nGround-truth labels generated: {len(labels)}", flush=True)

    print("\nDomain distribution:")
    for label, count in sorted(Counter(l["domain_label"] for l in labels).items()):
        print(f"  {label:20s}: {count:3d}")

    print("\nProof method distribution:")
    for label, count in sorted(Counter(l["proof_method_label"] for l in labels).items()):
        print(f"  {label:20s}: {count:3d}")
    print("\nObstruction distribution:")
    for label, count in sorted(Counter(l["obstruction_label"] or "none" for l in labels).items()):
        print(f"  {label:30s}: {count:3d}")

    print("\nManual RRCShape distribution:")
    for label, count in sorted(Counter(l["manual_rrc_shape"] for l in labels).items()):
        print(f"  {label:35s}: {count:3d}")

    # Write labels
    with open(LABELS_PATH, "w") as f:
        for lbl in labels:
            f.write(json.dumps(lbl) + "\n")
    print(f"\nLabels: {LABELS_PATH}", flush=True)

    # Cross-tab: domain × proof method
    print("\nCross-tab: domain × proof method")
    domains = sorted(set(l["domain_label"] for l in labels))
    methods = sorted(set(l["proof_method_label"] for l in labels))
    header = "  " + "".join(f"{m:18s}" for m in methods)
    print(header)
    for dom in domains:
        row = f"  {dom:12s}"
        for meth in methods:
            c = sum(1 for l in labels if l["domain_label"] == dom and l["proof_method_label"] == meth)
            row += f"{c:>18d}"
        print(row)

    return 0


if __name__ == "__main__":
    main()
