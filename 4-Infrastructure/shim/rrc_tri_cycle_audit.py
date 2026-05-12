#!/usr/bin/env python3
"""Tri-cycle audit for prover, Rainbow Raccoon Compiler, and FPGA witness lanes.

The audit is intentionally conservative. It does not promote claims. It finds
HOLD/weak surfaces, reruns the available proof/compiler/witness gates, and emits
a receipt describing which parts are still blocked.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT_DIR = REPO / "shared-data" / "data" / "rrc_tri_cycle_audit"
OUT = OUT_DIR / "rrc_tri_cycle_audit_receipt.json"
DOC = REPO / "6-Documentation" / "docs" / "rrc_tri_cycle_audit_2026-05-09.md"

TARGET_FILES = [
    "6-Documentation/wiki/Network-Topology-Theory.md",
    "3-Mathematical-Models/fiber_optic_vibrational_tensor/Fundamental_Network_Topology_Equation.md",
    "shared-data/network_topology_database.json",
    "6-Documentation/docs/fpga_rrc_q16_accel_setup_2026-05-09.md",
]

MARKERS = [
    "HOLD",
    "HOLD_SECURITY_PROOF_DEBT",
    "HOLD_COEFFICIENT_RECEIPT_DEBT",
    "HOLD_ANALOGY_ADAPTER",
    "HOLD_TOPOLOGY_PREDICTION_VALIDATION",
    "not ready",
    "unverified",
    "USB-UART",
    "CRC check : FAIL",
    "does not validate",
    "not a validation claim",
    "receipt_path_exists",
]

GATE_REGISTER: dict[str, dict[str, Any]] = {
    "security_proof_debt": {
        "status": "BLOCK_PROMOTION",
        "closure_required": [
            "formal independence/freshness theorem for adaptive masks",
            "secret-sharing non-reuse receipt",
            "negative control showing adapted coefficients do not leak party inputs",
        ],
        "allowed_use": "design hypothesis and simulation only",
    },
    "coefficient_or_calibration_debt": {
        "status": "BLOCK_NUMERIC_CLAIMS",
        "closure_required": [
            "dataset provenance receipt",
            "coefficient calibration receipt",
            "negative controls and sensitivity sweep",
        ],
        "allowed_use": "receipt-weighted prior accounting only",
    },
    "topology_prediction_debt": {
        "status": "BLOCK_VALIDATION_CLAIMS",
        "closure_required": [
            "pre-registered prediction target",
            "outcome receipt",
            "independent public-map or measurement comparison",
        ],
        "allowed_use": "HOLD topology hypothesis only",
    },
    "receipt_gate_debt": {
        "status": "BLOCK_ROUTE_PROMOTION",
        "closure_required": [
            "validation receipt exists",
            "rollback hash exists",
            "exact replay or decode closure hash matches",
        ],
        "allowed_use": "audit queue only",
    },
    "fpga_transport_or_witness_debt": {
        "status": "BLOCK_HARDWARE_ACCELERATION_CLAIMS",
        "closure_required": [
            "simple UART loopback passes on fabric pins",
            "Q16 accelerator hardware receipts match software receipts",
            "durable flash readback passes or SRAM-only boundary remains explicit",
        ],
        "allowed_use": "software witness and SRAM-loaded bitstream development",
    },
    "general_hold_surface": {
        "status": "BLOCK_PUBLIC_PROMOTION",
        "closure_required": [
            "bucket-specific gate assigned",
            "source receipt linked",
            "negative-control or replay evidence attached",
        ],
        "allowed_use": "internal research map",
    },
}


@dataclass
class CmdResult:
    command: list[str]
    cwd: str
    returncode: int
    stdout_tail: str
    stderr_tail: str


def run_cmd(command: list[str], cwd: Path, timeout: int = 120) -> CmdResult:
    proc = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return CmdResult(
        command=command,
        cwd=str(cwd.relative_to(REPO)),
        returncode=proc.returncode,
        stdout_tail=proc.stdout[-4000:],
        stderr_tail=proc.stderr[-4000:],
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_uart_beacon_diagnostics() -> dict[str, Any]:
    receipts = [
        SHIM / "tang9k_uart_beacon_probe_receipt.json",
        SHIM / "tang9k_uart_beacon_swapped_probe_receipt.json",
    ]
    diagnostics: list[dict[str, Any]] = []
    for path in receipts:
        if not path.exists():
            diagnostics.append({"receipt": str(path.relative_to(REPO)), "present": False})
            continue
        data = load_json(path)
        if isinstance(data.get("ports"), dict):
            port_rows = [
                {
                    "port": port,
                    "byte_count": item.get("byte_count"),
                    "contains_expected": item.get("contains_expected"),
                    "contains_q16_ascii": "513136" in item.get("raw_hex", ""),
                }
                for port, item in data["ports"].items()
            ]
        else:
            port_rows = [
                {
                    "port": item.get("port"),
                    "byte_count": item.get("byte_count"),
                    "contains_expected": item.get("contains_expected"),
                    "contains_q16_ascii": item.get("contains_q16_ascii"),
                }
                for item in data.get("results", [])
            ]
        conclusion = data.get("conclusion")
        if conclusion is None and port_rows:
            conclusion = (
                "PASS"
                if any(port.get("contains_expected") for port in port_rows)
                else "FAIL_NO_BEACON_ON_FTDI_INTERFACES"
            )
        diagnostics.append(
            {
                "receipt": str(path.relative_to(REPO)),
                "present": True,
                "schema": data.get("schema"),
                "constraints": data.get("constraints"),
                "bitstream_sha256": data.get("bitstream_sha256"),
                "conclusion": conclusion,
                "ports": port_rows,
            }
        )
    return {
        "receipts": diagnostics,
        "any_beacon_seen": any(
            any(port.get("contains_expected") for port in item.get("ports", []))
            for item in diagnostics
            if item.get("present")
        ),
    }


def scan_less_solid_surfaces() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for rel in TARGET_FILES:
        path = REPO / rel
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            marker_hits = [marker for marker in MARKERS if marker.lower() in line.lower()]
            if not marker_hits:
                continue
            findings.append(
                {
                    "path": rel,
                    "line": lineno,
                    "markers": marker_hits,
                    "text": line.strip()[:280],
                    "bucket": bucket_for_line(line),
                }
            )
    return findings


def bucket_for_line(line: str) -> str:
    lower = line.lower()
    if "security" in lower or "privacy" in lower or "beaver" in lower:
        return "security_proof_debt"
    if "coefficient" in lower or "calibration" in lower or "weight" in lower:
        return "coefficient_or_calibration_debt"
    if "prediction" in lower or "validation" in lower or "outcome" in lower:
        return "topology_prediction_debt"
    if "fpga" in lower or "usb-uart" in lower or "crc" in lower or "q16" in lower:
        return "fpga_transport_or_witness_debt"
    if "receipt" in lower:
        return "receipt_gate_debt"
    return "general_hold_surface"


def run_q16_witnesses(include_hardware: bool, hardware_port: str | None) -> dict[str, Any]:
    cases = [
        (
            "shift",
            [
                "python3",
                "4-Infrastructure/shim/tang9k_rrc_q16_accel.py",
                "--op",
                "shift",
                "--x",
                "0x00038000",
            ],
        ),
        (
            "weighted",
            [
                "python3",
                "4-Infrastructure/shim/tang9k_rrc_q16_accel.py",
                "--op",
                "weighted",
                "--energy",
                "0x000a0000",
                "--alpha",
                "0x00008000",
            ],
        ),
        (
            "monotone",
            [
                "python3",
                "4-Infrastructure/shim/tang9k_rrc_q16_accel.py",
                "--op",
                "monotone",
                "--a",
                "0x00010000",
                "--b",
                "0x00030000",
            ],
        ),
    ]
    results: dict[str, Any] = {"software": {}, "hardware": {}, "hardware_requested": include_hardware}
    for name, cmd in cases:
        software_out = SHIM / f"rrc_tri_cycle_{name}_software_receipt.json"
        software_cmd = cmd + ["--out", str(software_out.relative_to(REPO))]
        software = run_cmd(software_cmd, REPO)
        results["software"][name] = {
            "command": software.command,
            "returncode": software.returncode,
            "receipt": str(software_out.relative_to(REPO)),
            "match": software.returncode == 0 and load_json(software_out).get("match") is True,
        }
        if include_hardware and hardware_port:
            hardware_out = SHIM / f"rrc_tri_cycle_{name}_hardware_receipt.json"
            hardware_cmd = cmd + [
                "--port",
                hardware_port,
                "--retries",
                "1",
                "--out",
                str(hardware_out.relative_to(REPO)),
            ]
            hardware = run_cmd(hardware_cmd, REPO, timeout=20)
            receipt = load_json(hardware_out) if hardware_out.exists() else {}
            results["hardware"][name] = {
                "command": hardware.command,
                "returncode": hardware.returncode,
                "receipt": str(hardware_out.relative_to(REPO)),
                "match": hardware.returncode == 0 and receipt.get("match") is True,
                "hardware_error": receipt.get("hardware_error"),
            }
    results["software_pass"] = all(v["match"] for v in results["software"].values())
    results["hardware_pass"] = (
        all(v["match"] for v in results["hardware"].values()) if results["hardware"] else None
    )
    return results


def summarize_rrc(receipt: dict[str, Any]) -> dict[str, Any]:
    compiled = receipt.get("compiled_objects", [])
    rows = []
    for obj in compiled:
        rows.append(
            {
                "object_id": obj["object"]["object_id"],
                "label": obj["object"]["label"],
                "shape": obj["nearest_lawful_shape"]["shape"],
                "status": obj["type_witness"]["status"],
                "missing_or_weak_axes": obj["type_witness"].get("missing_or_weak_axes", []),
                "lean_boundary": obj["type_witness"].get("lean_boundary"),
            }
        )
    return {
        "receipt_hash": receipt.get("receipt_hash"),
        "compiled_object_count": len(compiled),
        "candidate_count": sum(1 for row in rows if row["status"] == "CANDIDATE"),
        "hold_count": sum(1 for row in rows if row["status"] == "HOLD"),
        "objects": rows,
    }


def bucket_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in findings:
        counts[item["bucket"]] = counts.get(item["bucket"], 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def active_gate_register(findings: list[dict[str, Any]]) -> dict[str, Any]:
    counts = bucket_counts(findings)
    return {
        bucket: GATE_REGISTER[bucket] | {"finding_count": count}
        for bucket, count in counts.items()
        if bucket in GATE_REGISTER
    }


def build_doc(receipt: dict[str, Any]) -> str:
    gates = receipt["gates"]
    buckets = receipt["less_solid_surface_counts"]
    lines = [
        "# RRC Tri-Cycle Audit",
        "",
        "**Date:** 2026-05-09",
        "",
        "## Gates",
        "",
        f"- Prover gate: `{gates['prover']['status']}`",
        f"- Compiler gate: `{gates['compiler']['status']}`",
        f"- FPGA software witness gate: `{gates['fpga_witness']['software_status']}`",
        f"- FPGA hardware witness gate: `{gates['fpga_witness']['hardware_status']}`",
        f"- UART beacon diagnostic: `{'PASS' if gates['fpga_witness']['uart_beacon']['any_beacon_seen'] else 'FAIL_NO_BEACON'}`",
        "",
        "## Less Solid Buckets",
        "",
    ]
    for bucket, count in buckets.items():
        gate = receipt["gate_register"].get(bucket, {})
        lines.append(f"- `{bucket}`: {count} ({gate.get('status', 'NO_GATE')})")
    lines.extend(
        [
            "",
            "## Closure Gates",
            "",
        ]
    )
    for bucket, gate in receipt["gate_register"].items():
        lines.append(f"### `{bucket}`")
        lines.append("")
        lines.append(f"- Status: `{gate['status']}`")
        lines.append(f"- Allowed use: {gate['allowed_use']}")
        for req in gate["closure_required"]:
            lines.append(f"- Requires: {req}")
        lines.append("")
    lines.extend(
        [
            "",
            "## UART Beacon Diagnostics",
            "",
        ]
    )
    for beacon in gates["fpga_witness"]["uart_beacon"]["receipts"]:
        lines.append(f"- `{beacon['receipt']}`: `{beacon.get('conclusion', 'MISSING')}`")
        for port in beacon.get("ports", []):
            lines.append(
                f"- Port `{port['port']}` byte_count={port['byte_count']} contains_expected={port['contains_expected']}"
            )
    lines.extend(
        [
            "",
            "## Highest Priority Holds",
            "",
        ]
    )
    for item in receipt["less_solid_surfaces"][:20]:
        lines.append(
            f"- `{item['bucket']}` [{item['path']}:{item['line']}](../../{item['path']}#L{item['line']}): {item['text']}"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This audit does not promote any HOLD claim. It only checks which weak surfaces are currently covered by prover, compiler, and FPGA-witness receipts.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-hardware", action="store_true")
    parser.add_argument("--hardware-port", default="/dev/ttyUSB1")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    less_solid = scan_less_solid_surfaces()
    prover = run_cmd(
        ["lake", "build", "Semantics.MetaManifoldProver"],
        REPO / "0-Core-Formalism" / "lean" / "Semantics",
        timeout=180,
    )
    compiler = run_cmd(["python3", "4-Infrastructure/shim/rainbow_raccoon_compiler.py"], REPO)
    compiler_receipt = load_json(SHIM / "rainbow_raccoon_compiler_receipt.json")
    q16 = run_q16_witnesses(args.include_hardware, args.hardware_port)
    uart_beacon = load_uart_beacon_diagnostics()

    receipt = {
        "schema": "rrc_tri_cycle_audit_receipt_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "Tri-cycle audit only. Prover gate checks Lean build, compiler gate checks RRC HOLD/CANDIDATE "
            "receipts, and FPGA gate checks Q16 witness harnesses. Hardware UART failures remain blockers."
        ),
        "less_solid_surface_counts": bucket_counts(less_solid),
        "gate_register": active_gate_register(less_solid),
        "less_solid_surfaces": less_solid,
        "gates": {
            "prover": {
                "status": "PASS" if prover.returncode == 0 else "FAIL",
                "command": prover.command,
                "returncode": prover.returncode,
                "stdout_tail": prover.stdout_tail,
                "stderr_tail": prover.stderr_tail,
            },
            "compiler": {
                "status": "PASS_WITH_HOLDS" if compiler.returncode == 0 else "FAIL",
                "command": compiler.command,
                "returncode": compiler.returncode,
                "stdout_tail": compiler.stdout_tail,
                "stderr_tail": compiler.stderr_tail,
                "summary": summarize_rrc(compiler_receipt),
            },
            "fpga_witness": {
                "software_status": "PASS" if q16["software_pass"] else "FAIL",
                "hardware_status": (
                    "PASS"
                    if q16["hardware_pass"] is True
                    else "FAIL"
                    if q16["hardware_pass"] is False
                    else "NOT_REQUESTED"
                ),
                "q16": q16,
                "uart_beacon": uart_beacon,
            },
        },
        "promotion_decision": "NO_PROMOTION",
        "next_actions": [
            "Close or explicitly retain HOLD_SECURITY_PROOF_DEBT before treating adaptive Beaver coefficients as privacy-equivalent masks.",
            "Treat coefficient and topology prediction rows as calibration debt until outcome receipts and negative controls close.",
            "Fix Tang Nano 9K USB-UART fabric route before claiming live FPGA acceleration receipts; TX-only beacon receipts currently show no bytes on ttyUSB0 or ttyUSB1.",
            "Use the Q16 lane as the first proof-backed compiler-to-FPGA witness once hardware transport responds.",
        ],
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    DOC.write_text(build_doc(receipt), encoding="utf-8")
    print(json.dumps({"receipt": str(OUT.relative_to(REPO)), "doc": str(DOC.relative_to(REPO)), "promotion_decision": "NO_PROMOTION"}, indent=2))
    return 0 if prover.returncode == 0 and compiler.returncode == 0 and q16["software_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
