#!/usr/bin/env python3
"""Route table for Tang Nano 9K UART-like transports.

The onboard FTDI/BL702 route is currently blocked for fabric UART. This router
subsumes those physical UART entries under one manifest and selects a
PTY-backed virtual Q16 route as the active non-hardware transport.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "shared-data" / "data" / "stack_solidification" / "tang9k_uart_transport_routes.json"
DOC = REPO / "6-Documentation" / "docs" / "tang9k_uart_transport_routes_2026-05-09.md"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_virtual_probe() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", "4-Infrastructure/shim/tang9k_rrc_q16_virtual_serial_probe.py"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    receipt_path = REPO / "shared-data" / "data" / "stack_solidification" / "tang9k_rrc_q16_virtual_serial_probe.json"
    receipt = load_json(receipt_path)
    return {
        "command": ["python3", "4-Infrastructure/shim/tang9k_rrc_q16_virtual_serial_probe.py"],
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "receipt": rel(receipt_path),
        "status": receipt.get("summary", {}).get("status", "UNKNOWN"),
        "match_count": receipt.get("summary", {}).get("match_count"),
        "case_count": receipt.get("summary", {}).get("case_count"),
    }


def serial_receipt_summary(path: str) -> dict[str, Any]:
    receipt = load_json(REPO / path)
    results = receipt.get("results", [])
    return {
        "receipt": path,
        "present": bool(receipt),
        "conclusion": receipt.get("conclusion"),
        "ports": [
            {
                "port": row.get("port"),
                "byte_count": row.get("byte_count"),
                "contains_expected": row.get("contains_expected"),
                "hex_prefix": row.get("hex_prefix"),
            }
            for row in results
        ],
    }


def build_manifest() -> dict[str, Any]:
    virtual = run_virtual_probe()
    onboard_beacon = serial_receipt_summary("4-Infrastructure/shim/tang9k_uart_beacon_probe_receipt.json")
    swapped_beacon = serial_receipt_summary("4-Infrastructure/shim/tang9k_uart_beacon_swapped_probe_receipt.json")
    loopback_after_clear = serial_receipt_summary("4-Infrastructure/shim/tang9k_uart_loopback_after_jtag_clear_probe_receipt.json")
    active_status = (
        "PASS_ACTIVE_VIRTUAL_ROUTE"
        if virtual["status"] == "PASS_VIRTUAL_SERIAL"
        and virtual.get("match_count") == virtual.get("case_count") == 3
        else "FAIL"
    )
    return {
        "schema": "tang9k_uart_transport_routes_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "Transport route table only. The active virtual route validates host Q16 serial "
            "framing and parser behavior. It does not validate live FPGA fabric or the "
            "Tang Nano onboard UART bridge."
        ),
        "active_route": "virtual://q16-pty",
        "active_route_status": active_status,
        "route_table": [
            {
                "route_id": "onboard-ftdi-a",
                "device": "/dev/ttyUSB0",
                "kind": "physical_ftdi_mpsse_or_bridge",
                "status": "BLOCKED_FOR_FABRIC_UART",
                "evidence": "faXX/MPSSE-style bytes or zero beacon bytes; no valid fabric receipt",
                "receipts": [onboard_beacon["receipt"], swapped_beacon["receipt"], loopback_after_clear["receipt"]],
            },
            {
                "route_id": "onboard-ftdi-b",
                "device": "/dev/ttyUSB1",
                "kind": "physical_ftdi_secondary_endpoint",
                "status": "BLOCKED_FOR_FABRIC_UART",
                "evidence": "zero beacon bytes and empty Q16 hardware receipts",
                "receipts": [onboard_beacon["receipt"], swapped_beacon["receipt"], loopback_after_clear["receipt"]],
            },
            {
                "route_id": "external-usb-uart",
                "device": "/dev/ttyUSB2_or_/dev/ttyACM0",
                "kind": "physical_external_adapter",
                "status": "PENDING_HARDWARE",
                "evidence": "recommended live-hardware closure route; adapter not present in this probe",
                "receipts": [],
            },
            {
                "route_id": "virtual-q16-pty",
                "device": "virtual://q16-pty",
                "kind": "pty_backed_virtual_serial",
                "status": virtual["status"],
                "evidence": "shift, weighted, and monotone Q16 receipt frames match through PTY-backed serial route",
                "receipts": [virtual["receipt"]],
            },
        ],
        "physical_receipt_summaries": {
            "onboard_beacon": onboard_beacon,
            "swapped_beacon": swapped_beacon,
            "loopback_after_jtag_clear": loopback_after_clear,
        },
        "virtual_probe": virtual,
        "routing_policy": {
            "default_non_hardware_route": "virtual://q16-pty",
            "live_hardware_promotion_requires": [
                "external or verified onboard route captures beacon payload a6425131360a",
                "Q16 shift, weighted, and monotone hardware receipts match software expectations",
                "stack audit reports FPGA hardware witness PASS",
            ],
            "blocked_routes_remain_visible": True,
        },
    }


def build_doc(manifest: dict[str, Any]) -> str:
    lines = [
        "# Tang Nano 9K UART Transport Routes",
        "",
        "**Date:** 2026-05-09",
        "",
        manifest["claim_boundary"],
        "",
        "## Active Route",
        "",
        f"- Active route: `{manifest['active_route']}`",
        f"- Status: `{manifest['active_route_status']}`",
        "",
        "## Route Table",
        "",
        "| Route | Device | Kind | Status |",
        "| --- | --- | --- | --- |",
    ]
    for route in manifest["route_table"]:
        lines.append(
            f"| `{route['route_id']}` | `{route['device']}` | `{route['kind']}` | `{route['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Routing Policy",
            "",
            f"- Default non-hardware route: `{manifest['routing_policy']['default_non_hardware_route']}`",
            "- Live hardware promotion requires:",
        ]
    )
    for gate in manifest["routing_policy"]["live_hardware_promotion_requires"]:
        lines.append(f"  - {gate}")
    lines.extend(["", "## Machine Receipt", "", f"- `{OUT.relative_to(REPO)}`"])
    return "\n".join(lines) + "\n"


def main() -> int:
    manifest = build_manifest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DOC.write_text(build_doc(manifest), encoding="utf-8")
    print(json.dumps({"receipt": rel(OUT), "doc": rel(DOC), "status": manifest["active_route_status"]}, indent=2))
    return 0 if manifest["active_route_status"] == "PASS_ACTIVE_VIRTUAL_ROUTE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
