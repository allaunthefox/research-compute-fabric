#!/usr/bin/env python3
"""
KOTC — Kinetic Operation Token Completion Daemon simulator.

This is a local prototype scaffold. It does not call a real model. It treats a
candidate completion as an auditable operation and emits a receipt.

Usage:
  python tools/kotc/kotc_sim.py --candidate candidate.txt --target Semantics.InvariantReceipt.Core --mode REPAIR
  python tools/kotc/kotc_sim.py --candidate - --target docs/research/KOTC --mode DRAFT < candidate.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple


class Mode(str, Enum):
    DRAFT = "DRAFT"
    REPAIR = "REPAIR"
    STRICT = "STRICT"


class Decision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    HOLD = "HOLD"
    QUARANTINE = "QUARANTINE"


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class CompletionReceipt:
    receipt_type: str
    completion_id: str
    mode: str
    target_module: str
    context_files: List[str]
    symbol_refs: List[str]
    kot_cost_q16: str
    risk: str
    decision: str
    policy_checks: Dict[str, str]
    candidate_hash: str
    notes: List[str]


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def q16_hex(units: int) -> str:
    """Encode integer units as Q16.16 raw hex."""
    raw = max(0, min(units << 16, 0xFFFFFFFF))
    return f"0x{raw:08X}"


def estimate_kot_units(candidate: str, mode: Mode, policy_failures: int) -> int:
    base = max(1, len(candidate.encode("utf-8")) // 128)
    mode_multiplier = {
        Mode.DRAFT: 1,
        Mode.REPAIR: 2,
        Mode.STRICT: 4,
    }[mode]
    return base * mode_multiplier + policy_failures * 16


def extract_symbol_refs(candidate: str) -> List[str]:
    refs = set(re.findall(r"\b[A-Z][A-Za-z0-9_]{2,}\b", candidate))
    allow = {
        "Q16_16",
        "Receipt",
        "Outcome",
        "ModelUpgrade",
        "SubstrateAdapter",
        "RegisteredModel",
        "KOT",
        "AMMR",
        "AVMR",
        "NUVMAP",
        "GCCL",
        "GCCLRep",
        "InvariantReceipt",
    }
    return sorted(ref for ref in refs if ref in allow)


def check_policy(candidate: str, mode: Mode, target: str) -> Tuple[Dict[str, str], List[str]]:
    notes: List[str] = []
    checks: Dict[str, str] = {}

    hot_path_target = any(token.lower() in target.lower() for token in [
        "fixedpoint", "physics", "kernel", "codec", "hot", "semantics"
    ])
    float_patterns = [r"\bFloat\b", r"\bDouble\b", r"\bf32\b", r"\bf64\b", r"\bfloat\b"]
    has_float = any(re.search(pattern, candidate) for pattern in float_patterns)
    if hot_path_target and has_float:
        checks["no_float_hot_path"] = "failed"
        notes.append("Float-like type or token appears in a hot-path/core target.")
    elif has_float:
        checks["no_float_hot_path"] = "warning"
        notes.append("Float-like token appears outside an obvious hot path; review required.")
    else:
        checks["no_float_hot_path"] = "passed"

    physical_claim_tokens = ["SI", "joule", "newton", "mass", "energy", "thermodynamic", "physics"]
    has_physical_claim = any(token.lower() in candidate.lower() for token in physical_claim_tokens)
    has_receipt_or_scope = any(token.lower() in candidate.lower() for token in ["receipt", "dimensionless", "proxy", "not_si", "not physical"])
    if has_physical_claim and not has_receipt_or_scope:
        checks["no_unreviewed_physical_claim"] = "failed"
        notes.append("Physical/SI-like claim appears without receipt/scope/dimensionless boundary.")
    elif has_physical_claim:
        checks["no_unreviewed_physical_claim"] = "warning"
    else:
        checks["no_unreviewed_physical_claim"] = "passed"

    theorem_weakening_patterns = [r"admit", r"axiom\s+", r"unsafe", r"set_option\s+autoImplicit\s+true"]
    has_theorem_weakening = any(re.search(pattern, candidate, re.IGNORECASE) for pattern in theorem_weakening_patterns)
    if has_theorem_weakening:
        checks["no_theorem_weakening"] = "failed"
        notes.append("Candidate contains proof-weakening or unsafe pattern.")
    else:
        checks["no_theorem_weakening"] = "passed"

    introduces_invariant = bool(re.search(r"\bInvariant\b|\binvariant\b|\btheorem\b|\blemma\b", candidate))
    has_receipt = "Receipt" in candidate or "receipt" in candidate.lower()
    if introduces_invariant and not has_receipt and mode == Mode.STRICT:
        checks["no_unchecked_invariant_introduction"] = "failed"
        notes.append("Strict-mode invariant/theorem introduction lacks receipt language.")
    elif introduces_invariant and not has_receipt:
        checks["no_unchecked_invariant_introduction"] = "warning"
    else:
        checks["no_unchecked_invariant_introduction"] = "passed"

    compiler_pass_tokens = ["CompilerPass", "pass_id", "workflow", "WorkflowDAG", "transform"]
    mentions_pass = any(token in candidate for token in compiler_pass_tokens)
    mentions_cost = any(token.lower() in candidate.lower() for token in ["cost", "kot", "budget"])
    if mentions_pass and not mentions_cost:
        checks["no_unbudgeted_compiler_pass"] = "failed"
        notes.append("Compiler-pass-like candidate lacks KOT/cost/budget accounting.")
    else:
        checks["no_unbudgeted_compiler_pass"] = "passed"

    authority_tokens = ["coreModule", "CORE_MODULE", "proved", "certified", "ASIL-D", "canonical"]
    has_authority = any(token in candidate for token in authority_tokens)
    if has_authority and not has_receipt:
        checks["no_authority_escalation"] = "failed"
        notes.append("Candidate escalates authority/certification without receipt evidence.")
    elif has_authority:
        checks["no_authority_escalation"] = "warning"
    else:
        checks["no_authority_escalation"] = "passed"

    if "Receipt" not in candidate and "receipt" not in candidate.lower():
        checks["no_silent_receipt_drop"] = "warning" if mode != Mode.DRAFT else "not_applicable"
    else:
        checks["no_silent_receipt_drop"] = "passed"

    if re.search(r"while\s+true|partial\s+def|rec\s+", candidate):
        checks["no_unbounded_recursion"] = "warning"
        notes.append("Potentially unbounded recursion/loop pattern needs review.")
    else:
        checks["no_unbounded_recursion"] = "passed"

    return checks, notes


def decide(checks: Dict[str, str], mode: Mode) -> Tuple[Decision, Risk]:
    failures = sum(1 for value in checks.values() if value == "failed")
    warnings = sum(1 for value in checks.values() if value == "warning")

    if failures >= 2:
        return Decision.QUARANTINE, Risk.CRITICAL
    if failures == 1:
        return Decision.QUARANTINE if mode == Mode.STRICT else Decision.REJECT, Risk.HIGH
    if warnings >= 3:
        return Decision.HOLD, Risk.HIGH
    if warnings > 0:
        return Decision.HOLD, Risk.MEDIUM
    return Decision.ACCEPT, Risk.LOW


def load_candidate(path_arg: str) -> str:
    if path_arg == "-":
        return sys.stdin.read()
    return Path(path_arg).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="KOTC completion simulator")
    parser.add_argument("--candidate", required=True, help="Candidate text file, or '-' for stdin")
    parser.add_argument("--target", required=True, help="Target module/path")
    parser.add_argument("--mode", choices=[m.value for m in Mode], default="REPAIR")
    parser.add_argument("--context", action="append", default=[], help="Context file path; repeatable")
    parser.add_argument("--completion-id", default="kotc_local", help="Receipt completion id suffix/name")
    args = parser.parse_args()

    mode = Mode(args.mode)
    candidate = load_candidate(args.candidate)
    checks, notes = check_policy(candidate, mode, args.target)
    decision, risk = decide(checks, mode)
    failures = sum(1 for value in checks.values() if value == "failed")
    kot_units = estimate_kot_units(candidate, mode, failures)

    completion_id = args.completion_id
    if not completion_id.startswith("kotc_"):
        completion_id = "kotc_" + completion_id

    receipt = CompletionReceipt(
        receipt_type="kotc.completion.v1",
        completion_id=completion_id,
        mode=mode.value,
        target_module=args.target,
        context_files=args.context,
        symbol_refs=extract_symbol_refs(candidate),
        kot_cost_q16=q16_hex(kot_units),
        risk=risk.value,
        decision=decision.value,
        policy_checks=checks,
        candidate_hash=sha256_text(candidate),
        notes=notes,
    )

    print(json.dumps(asdict(receipt), indent=2, sort_keys=True))
    return 0 if decision in {Decision.ACCEPT, Decision.HOLD} else 2


if __name__ == "__main__":
    raise SystemExit(main())
