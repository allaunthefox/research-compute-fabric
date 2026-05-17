#!/usr/bin/env python3
"""Receipt probe for zero-whitespace-code logogram grammar.

The grammar does not store ordinary spaces as payload atoms. For canonical
single-space token streams, spacing is reconstructed from symbol count/order.
Non-canonical whitespace remains HOLD unless a residual policy is declared.
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
OUT = OUT_DIR / "whitespace_zero_grammar_probe.json"
DOC = REPO / "6-Documentation" / "docs" / "whitespace_zero_grammar_2026-05-09.md"


CANONICAL_CASES = [
    "structure transformation receipt replay repair",
    "braid rope ammr leaf peak",
    "token order symbol identity transform rule",
]

HOLD_CASES = [
    "two  spaces need residual",
    " leading space needs residual",
    "tabs\tneed\tresidual",
]


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def run_lean_build() -> dict[str, Any]:
    proc = subprocess.run(
        ["lake", "build", "Semantics.WhitespaceFreeGrammar"],
        cwd=LEAN_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
        check=False,
    )
    return {
        "command": ["lake", "build", "Semantics.WhitespaceFreeGrammar"],
        "cwd": rel(LEAN_DIR),
        "returncode": proc.returncode,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "stdout_tail": proc.stdout[-6000:],
        "stderr_tail": proc.stderr[-6000:],
    }


def is_canonical_single_space(text: str) -> bool:
    return bool(text) and text == " ".join(text.split(" ")) and "\t" not in text and "\n" not in text and not text.startswith(" ") and not text.endswith(" ")


def encode_symbols(text: str) -> list[str]:
    return text.split()


def run_case(case_id: str, text: str, expect_exact: bool) -> dict[str, Any]:
    symbols = encode_symbols(text)
    reconstructed = " ".join(symbols)
    raw_bytes = len(text.encode("utf-8"))
    payload_bytes = sum(len(symbol.encode("utf-8")) for symbol in symbols)
    derived_boundaries = max(0, len(symbols) - 1)
    stored_whitespace_codes = 0
    exact_replay = reconstructed == text
    canonical = is_canonical_single_space(text)
    status = "ADMIT_FIXTURE" if exact_replay and canonical and expect_exact else "HOLD_NEEDS_WHITESPACE_RESIDUAL"
    return {
        "case_id": case_id,
        "raw": text,
        "symbols": symbols,
        "symbol_count": len(symbols),
        "raw_bytes": raw_bytes,
        "payload_bytes": payload_bytes,
        "stored_whitespace_codes": stored_whitespace_codes,
        "stored_whitespace_bytes": 0,
        "derived_boundary_count": derived_boundaries,
        "reconstructed": reconstructed,
        "exact_replay": exact_replay,
        "canonical_single_space": canonical,
        "delta_vs_raw_without_receipt": raw_bytes - payload_bytes,
        "status": status,
    }


def build_receipt() -> dict[str, Any]:
    lean_build = run_lean_build()
    cases = [
        run_case(f"canonical_{idx}", text, True)
        for idx, text in enumerate(CANONICAL_CASES, start=1)
    ] + [
        run_case(f"hold_{idx}", text, False)
        for idx, text in enumerate(HOLD_CASES, start=1)
    ]
    admitted = [case for case in cases if case["status"] == "ADMIT_FIXTURE"]
    holds = [case for case in cases if case["status"].startswith("HOLD")]
    return {
        "schema": "whitespace_zero_grammar_probe_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "Zero whitespace-code grammar for canonical single-space token streams. "
            "Whitespace is reconstructed from symbol count/order. Non-canonical "
            "spacing requires an explicit residual and is not admitted by this gate."
        ),
        "lean_module": "Semantics.WhitespaceFreeGrammar",
        "lean_build": lean_build,
        "grammar_rule": {
            "stored_whitespace_codes": 0,
            "boundary_rule": "insert one display space between adjacent symbols during canonical replay",
            "payload_rule": "store symbol payloads only",
            "residual_rule": "non-canonical whitespace requires residual",
        },
        "summary": {
            "status": "PASS_ZERO_WHITESPACE_CANONICAL" if lean_build["status"] == "PASS" and len(admitted) == len(CANONICAL_CASES) and len(holds) == len(HOLD_CASES) else "FAIL",
            "case_count": len(cases),
            "admit_count": len(admitted),
            "hold_count": len(holds),
            "stored_whitespace_codes_total": sum(case["stored_whitespace_codes"] for case in cases),
            "canonical_delta_bytes_total": sum(case["delta_vs_raw_without_receipt"] for case in admitted),
        },
        "cases": cases,
    }


def build_doc(receipt: dict[str, Any]) -> str:
    lines = [
        "# Whitespace-Zero Grammar Probe",
        "",
        "**Date:** 2026-05-09",
        "",
        receipt["claim_boundary"],
        "",
        "## Rule",
        "",
        "- Store symbol payloads.",
        "- Store zero ordinary whitespace codes.",
        "- Reconstruct one canonical display space between adjacent symbols.",
        "- HOLD any non-canonical whitespace unless a residual is declared.",
        "",
        "## Status",
        "",
        f"- Lean module: `{receipt['lean_module']}`",
        f"- Lean build: `{receipt['lean_build']['status']}`",
        f"- Probe status: `{receipt['summary']['status']}`",
        f"- Admitted canonical fixtures: `{receipt['summary']['admit_count']}`",
        f"- HOLD fixtures needing residual: `{receipt['summary']['hold_count']}`",
        f"- Stored whitespace codes total: `{receipt['summary']['stored_whitespace_codes_total']}`",
        "",
        "## Cases",
        "",
    ]
    for case in receipt["cases"]:
        lines.append(
            f"- `{case['case_id']}`: `{case['status']}`, symbols `{case['symbol_count']}`, "
            f"payload `{case['payload_bytes']}` bytes, raw `{case['raw_bytes']}` bytes, "
            f"derived boundaries `{case['derived_boundary_count']}`, exact replay `{case['exact_replay']}`"
        )
    lines.extend(
        [
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
    return 0 if receipt["summary"]["status"] == "PASS_ZERO_WHITESPACE_CANONICAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
