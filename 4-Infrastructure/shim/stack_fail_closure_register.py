#!/usr/bin/env python3
"""Create closure tickets for current stack failures and HOLD buckets."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
TRI = REPO / "shared-data" / "data" / "rrc_tri_cycle_audit" / "rrc_tri_cycle_audit_receipt.json"
STACK = REPO / "shared-data" / "data" / "stack_solidification" / "stack_solidification_receipt.json"
OUT_DIR = REPO / "shared-data" / "data" / "stack_solidification"
OUT = OUT_DIR / "stack_fail_closure_register.json"
DOC = REPO / "6-Documentation" / "docs" / "stack_fail_closure_register_2026-05-09.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_dirty_count() -> int | None:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return len([line for line in proc.stdout.splitlines() if line.strip()])


def ticket(
    ticket_id: str,
    title: str,
    failure_class: str,
    status: str,
    evidence: list[str],
    closure_gate: list[str],
    next_action: list[str],
    owner_surface: str,
) -> dict[str, Any]:
    return {
        "ticket_id": ticket_id,
        "title": title,
        "failure_class": failure_class,
        "status": status,
        "evidence": evidence,
        "closure_gate": closure_gate,
        "next_action": next_action,
        "owner_surface": owner_surface,
    }


def build_register() -> dict[str, Any]:
    tri = load_json(TRI)
    stack = load_json(STACK) if STACK.exists() else {}
    sem_receipt_path = OUT_DIR / "external_sem_entity_diff_probe_receipt.json"
    sem_receipt = load_json(sem_receipt_path) if sem_receipt_path.exists() else {}
    hold_checklist_path = OUT_DIR / "rrc_hold_closure_checklist.json"
    hold_checklist = load_json(hold_checklist_path) if hold_checklist_path.exists() else {}
    coeff_manifest_path = OUT_DIR / "network_topology_coefficient_calibration_manifest.json"
    coeff_manifest = load_json(coeff_manifest_path) if coeff_manifest_path.exists() else {}
    pred_registry_path = OUT_DIR / "network_topology_prediction_hold_registry.json"
    pred_registry = load_json(pred_registry_path) if pred_registry_path.exists() else {}
    beaver_controls_path = OUT_DIR / "beaver_mask_freshness_negative_controls.json"
    beaver_controls = load_json(beaver_controls_path) if beaver_controls_path.exists() else {}
    virtual_serial_path = OUT_DIR / "tang9k_rrc_q16_virtual_serial_probe.json"
    virtual_serial = load_json(virtual_serial_path) if virtual_serial_path.exists() else {}
    transport_routes_path = OUT_DIR / "tang9k_uart_transport_routes.json"
    transport_routes = load_json(transport_routes_path) if transport_routes_path.exists() else {}
    less_solid = tri.get("less_solid_surface_counts", {})
    gates = tri.get("gates", {})
    fpga = gates.get("fpga_witness", {})
    compiler_receipt_path = REPO / "4-Infrastructure" / "shim" / "rainbow_raccoon_compiler_receipt.json"
    compiler_receipt = load_json(compiler_receipt_path) if compiler_receipt_path.exists() else {}
    compiler = stack.get("gates", {}).get("compiler", {})
    if not compiler:
        objects = compiler_receipt.get("compiled_objects", [])
        compiler = {
            "receipt_hash": compiler_receipt.get("receipt_hash"),
            "candidate_count": sum(
                1 for obj in objects if obj.get("type_witness", {}).get("status") == "CANDIDATE"
            ),
            "hold_count": sum(
                1 for obj in objects if obj.get("type_witness", {}).get("status") == "HOLD"
            ),
        }
    worktree = stack.get("gates", {}).get("worktree", {})
    if not worktree:
        dirty_count = git_dirty_count()
        worktree = {
            "status": "DIRTY" if dirty_count else "CLEAN",
            "tracked_or_untracked_count": dirty_count,
        }

    tickets = [
        ticket(
            "FAIL-FPGA-UART-001",
            "Live fabric UART transport has no observable bytes",
            "fpga_transport_or_witness_debt",
            "BLOCKED",
            [
                "Q16 software witness passes",
                "Q16 hardware witness returns short receipt frames",
                "TX-only beacon standard pins produced zero bytes on ttyUSB0 and ttyUSB1",
                "TX-only beacon swapped pins produced zero bytes on ttyUSB0 and ttyUSB1",
                "Old faXX/ffXX direct-probe interpretation is superseded as bridge/MPSSE behavior, not fabric proof",
                "FPGA UART route analysis identifies the onboard BL702 bridge route as blocked and recommends external USB-UART",
                "Forced JTAG reset plus SRAM reload succeeds, but beacon/Q16 UART receipts remain empty",
                "Loopback-after-JTAG-clear diagnostic produced faXX-style bytes on ttyUSB0, consistent with bridge/MPSSE behavior rather than a valid fabric receipt",
                (
                    "PTY-backed virtual serial Q16 probe: "
                    f"{virtual_serial.get('summary', {}).get('status', 'not_run')} "
                    f"({virtual_serial.get('summary', {}).get('match_count', 'not_run')}/"
                    f"{virtual_serial.get('summary', {}).get('case_count', 'not_run')} matches)"
                ),
                (
                    "UART transport router active route: "
                    f"{transport_routes.get('active_route', 'not_run')} "
                    f"({transport_routes.get('active_route_status', 'not_run')})"
                ),
            ],
            [
                "external USB-UART or verified onboard bridge captures beacon payload a6425131360a",
                "loopback or beacon receipt passes before Q16 accelerator retry",
                "Q16 hardware receipts match software receipts for shift, weighted, and monotone cases",
            ],
            [
                "Attach external USB-UART: adapter TX to fabric RX pin 18, adapter RX to fabric TX pin 17, and GND to GND",
                "Probe the new adapter path, usually /dev/ttyUSB2 or /dev/ttyACM0, with the TX-only beacon before Q16",
                "If external UART works, patch host default port or call scripts with --port and rerun Q16 hardware receipts",
                "If external UART fails, inspect PNR pin placement and add LED-observed heartbeat fallback",
            ],
            "6-Documentation/docs/fpga_uart_route_analysis_2026-05-09.md",
        ),
        ticket(
            "FAIL-FPGA-FLASH-002",
            "Durable flash programming readback fails",
            "fpga_transport_or_witness_debt",
            "HELD_SRAM_ONLY",
            [
                "SRAM load passes CRC",
                "Flash programming attempt had readback CRC failure",
            ],
            [
                "flash write and readback CRC pass for the exact Q16 bitstream",
                "or documentation keeps SRAM-only boundary explicit",
            ],
            [
                "Keep SRAM-only claim boundary until flash command and board target are verified",
                "Do not mark hardware install persistent",
            ],
            "6-Documentation/docs/fpga_rrc_q16_accel_setup_2026-05-09.md",
        ),
        ticket(
            "FAIL-SECURITY-BEAVER-003",
            "Adaptive Beaver coefficients are not privacy-equivalent masks yet",
            "security_proof_debt",
            "HOLD",
            [
                f"{less_solid.get('security_proof_debt', 0)} security proof debt surfaces found",
                "tri-cycle audit blocks promotion for adaptive mask claims",
                f"mask freshness negative controls: {beaver_controls.get('summary', {}).get('status', 'not_run')}",
                f"mask freshness case count: {beaver_controls.get('summary', {}).get('case_count', 'not_run')}",
            ],
            [
                "formal independence/freshness theorem exists",
                "secret-sharing non-reuse receipt exists",
                "negative control shows adapted coefficients do not leak party inputs",
            ],
            [
                "Add a Lean-facing finite-state mask freshness model",
                "Generate negative-control fixtures for repeated coefficients and topology-derived coefficients",
            ],
            "Network-Topology-Theory.md + Fundamental_Network_Topology_Equation.md",
        ),
        ticket(
            "FAIL-COEFFICIENT-CALIBRATION-004",
            "Numeric weights remain receipt-weighted priors, not calibrated coefficients",
            "coefficient_or_calibration_debt",
            "HOLD",
            [
                f"{less_solid.get('coefficient_or_calibration_debt', 0)} coefficient/calibration debt surfaces found",
                "receipt reweighting exists, but coefficient calibration and negative controls remain open",
                f"coefficient HOLD manifest rows: {coeff_manifest.get('summary', {}).get('row_count', 'not_run')}",
            ],
            [
                "dataset provenance receipt linked",
                "coefficient calibration receipt linked",
                "sensitivity sweep and negative controls pass",
            ],
            [
                "Create coefficient calibration fixture manifest",
                "Separate hypothesis weights from calibrated weights in docs and JSON surfaces",
            ],
            "shared-data/network_topology_database.json",
        ),
        ticket(
            "FAIL-TOPOLOGY-PREDICTION-005",
            "Topology predictions are not validation claims",
            "topology_prediction_debt",
            "HOLD",
            [
                f"{less_solid.get('topology_prediction_debt', 0)} topology prediction debt surfaces found",
                "tri-cycle audit requires pre-registered target and independent comparison",
                f"prediction HOLD registry rows: {pred_registry.get('summary', {}).get('row_count', 'not_run')}",
            ],
            [
                "pre-registered prediction target exists",
                "outcome receipt exists",
                "independent public map or measurement comparison exists",
            ],
            [
                "Create prediction-target registry with timestamps and immutable receipt hashes",
                "Move existing predicted nodes into HOLD prediction queue, not validation table",
            ],
            "shared-data/network_topology_database.json",
        ),
        ticket(
            "FAIL-RECEIPT-GATE-006",
            "Route promotion lacks complete receipt and rollback closure",
            "receipt_gate_debt",
            "HOLD",
            [
                f"{less_solid.get('receipt_gate_debt', 0)} receipt-gate debt surfaces found",
                "compiler keeps 6 objects HOLD and only 1 candidate",
                f"compiler receipt hash: {compiler.get('receipt_hash')}",
                f"optional sem entity probe: {sem_receipt.get('decision', 'not_run')}",
                (
                    "HOLD closure checklist: "
                    f"{hold_checklist.get('summary', {}).get('open_closure_count', 'not_run')} open items"
                ),
            ],
            [
                "validation receipt exists",
                "rollback hash exists",
                "exact replay or decode closure hash matches",
            ],
            [
                "Close every item in rrc_hold_closure_checklist.json before rerunning compiler promotion",
                "Do not widen candidate admission beyond Q16 until Lean or independent replay closes",
            ],
            "4-Infrastructure/shim/rainbow_raccoon_compiler.py",
        ),
        ticket(
            "FAIL-WORKTREE-SCOPE-007",
            "Broad worktree is too dirty for safe sweep commit",
            "release_hygiene_debt",
            "BLOCKED_FOR_BROAD_STAGE",
            [
                f"worktree status: {worktree.get('status')}",
                f"changed/untracked count: {worktree.get('tracked_or_untracked_count')}",
                "staging manifest created for the solidification slice",
                f"optional sem entity probe: {sem_receipt.get('decision', 'not_run')}",
            ],
            [
                "commit scope is explicit file list",
                "generated artifacts are intentionally included or excluded",
                "no unrelated modified Lean/doc/probe files are swept in",
                "entity-level change list exists for staged or scoped files when sem is available",
            ],
            [
                "Use stack_solidification_staging_manifest_2026-05-09.md before any commit",
                "Create separate manifests for CPU/logogram/wiki maturation slices if needed",
                "Use /tmp/sem_probe/sem/crates/target/release/sem, not /usr/bin/sem, unless a durable sem binary is installed",
            ],
            "6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md",
        ),
    ]
    return {
        "schema": "stack_fail_closure_register_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "Closure register only. Tickets describe gates required to close failures; they do not claim closure.",
        "source_receipts": [str(TRI.relative_to(REPO)), str(STACK.relative_to(REPO))],
        "optional_tool_receipts": [str(sem_receipt_path.relative_to(REPO))] if sem_receipt_path.exists() else [],
        "closure_receipts": [
            str(path.relative_to(REPO))
            for path in [hold_checklist_path, coeff_manifest_path, pred_registry_path, beaver_controls_path, virtual_serial_path, transport_routes_path]
            if path.exists()
        ],
        "summary": {
            "ticket_count": len(tickets),
            "blocked_or_hold_count": sum(1 for item in tickets if item["status"] in {"BLOCKED", "HOLD", "BLOCKED_FOR_BROAD_STAGE", "HELD_SRAM_ONLY"}),
            "fpga_hardware_status": fpga.get("hardware_status"),
            "fpga_software_status": fpga.get("software_status"),
            "promotion_decision": tri.get("promotion_decision"),
        },
        "tickets": tickets,
    }


def build_doc(register: dict[str, Any]) -> str:
    lines = [
        "# Stack Fail Closure Register",
        "",
        "**Date:** 2026-05-09",
        "",
        "This register turns current failures into closure gates. It does not mark them solved.",
        "",
        "## Summary",
        "",
        f"- Tickets: `{register['summary']['ticket_count']}`",
        f"- Promotion decision: `{register['summary']['promotion_decision']}`",
        f"- FPGA software status: `{register['summary']['fpga_software_status']}`",
        f"- FPGA hardware status: `{register['summary']['fpga_hardware_status']}`",
        "",
        "## Tickets",
        "",
    ]
    for item in register["tickets"]:
        lines.append(f"### `{item['ticket_id']}` {item['title']}")
        lines.append("")
        lines.append(f"- Class: `{item['failure_class']}`")
        lines.append(f"- Status: `{item['status']}`")
        lines.append(f"- Owner surface: `{item['owner_surface']}`")
        for evidence in item["evidence"]:
            lines.append(f"- Evidence: {evidence}")
        for gate in item["closure_gate"]:
            lines.append(f"- Closure gate: {gate}")
        for action in item["next_action"]:
            lines.append(f"- Next action: {action}")
        lines.append("")
    lines.append("## Machine Receipt")
    lines.append("")
    lines.append(f"- `{OUT.relative_to(REPO)}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    register = build_register()
    OUT.write_text(json.dumps(register, indent=2, sort_keys=True), encoding="utf-8")
    DOC.write_text(build_doc(register), encoding="utf-8")
    print(json.dumps({"receipt": str(OUT.relative_to(REPO)), "doc": str(DOC.relative_to(REPO)), "tickets": len(register["tickets"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
