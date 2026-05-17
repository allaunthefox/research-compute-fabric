#!/usr/bin/env python3
"""Receipt generator for the LeanDojo/mathlib proof-boundary lane.

LeanDojo/mathlib are route priors only. This receipt promotes only local Lean
replay evidence: targeted `lake build` plus witness `#eval` output from a tiny
extension theorem fixture.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
LEAN_ROOT = REPO / "0-Core-Formalism" / "lean" / "Semantics"
LEAN_FILE = LEAN_ROOT / "ExtensionScaffold" / "Compression" / "ProofReplay.lean"
OUT_DIR = REPO / "shared-data" / "data" / "lean_proof_replay"
RECEIPT = OUT_DIR / "lean_proof_replay_receipt.json"
SUMMARY = OUT_DIR / "lean_proof_replay_receipt.md"


EXPECTED_WITNESSES = ["94", "true", "true", "false", "false"]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def run_command(argv: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "argv": argv,
        "cwd": rel(cwd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "stdout_hash": sha256_text(proc.stdout),
        "stderr_hash": sha256_text(proc.stderr),
    }


def parse_witnesses(stdout: str) -> list[str]:
    witnesses: list[str] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped in {"true", "false"} or stripped.isdigit():
            witnesses.append(stripped)
            continue
        if ": " in stripped:
            tail = stripped.rsplit(": ", 1)[-1].strip()
            if tail in {"true", "false"} or tail.isdigit():
                witnesses.append(tail)
    return witnesses


def write_summary(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "# Lean Proof Replay Receipt",
        "",
        f"Schema: `{receipt['schema']}`  ",
        f"Decision: `{receipt['decision']}`  ",
        f"Status: `{receipt['status']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Witnesses",
        "",
        f"Expected: `{receipt['expected_witnesses']}`",
        "",
        f"Observed: `{receipt['observed_witnesses']}`",
        "",
        "## Commands",
        "",
    ]
    for command in receipt["commands"]:
        lines.extend(
            [
                f"- `{' '.join(command['argv'])}`",
                f"  - returncode: `{command['returncode']}`",
                f"  - stdout hash: `{command['stdout_hash']}`",
                f"  - stderr hash: `{command['stderr_hash']}`",
            ]
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build = run_command(["lake", "build", "ExtensionScaffold.Compression.ProofReplay"], LEAN_ROOT)
    eval_run = run_command(["lake", "env", "lean", "ExtensionScaffold/Compression/ProofReplay.lean"], LEAN_ROOT)
    observed = parse_witnesses(eval_run["stdout"])
    build_pass = build["returncode"] == 0
    witness_pass = observed == EXPECTED_WITNESSES
    status = "ADMIT_FIXTURE" if build_pass and witness_pass else "HOLD_DIAGNOSTIC"
    receipt = {
        "schema": "lean_proof_replay_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lean_file": rel(LEAN_FILE),
        "lean_file_hash": sha256_file(LEAN_FILE),
        "module": "ExtensionScaffold.Compression.ProofReplay",
        "commands": [build, eval_run],
        "expected_witnesses": EXPECTED_WITNESSES,
        "observed_witnesses": observed,
        "build_pass": build_pass,
        "witness_pass": witness_pass,
        "status": status,
        "decision": "HOLD",
        "claim_boundary": (
            "LeanDojo/mathlib proof-boundary fixture only. External proof corpora "
            "may propose obligations, but promotion requires local Lean replay. "
            "This receipt proves only a tiny local admission predicate fixture, "
            "not any external theorem, compression benchmark, or mathlib coverage claim."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json({k: v for k, v in receipt.items() if k != "receipt_hash"}))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt, SUMMARY)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "status": receipt["status"],
                "observed_witnesses": observed,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if build_pass and witness_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
