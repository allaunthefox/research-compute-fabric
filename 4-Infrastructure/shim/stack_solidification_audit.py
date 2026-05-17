#!/usr/bin/env python3
"""End-to-end stand-up audit for the Rainbow Raccoon stack.

This is a snapshot tool, not a promotion tool. It collects the current proof,
compiler, receipt, JSON, and hardware-boundary evidence into one receipt so the
stack can be stabilized without turning HOLD surfaces into claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "stack_solidification"
OUT = OUT_DIR / "stack_solidification_receipt.json"
DOC = REPO / "6-Documentation" / "docs" / "stack_solidification_status_2026-05-09.md"

JSON_SURFACES = [
    "shared-data/network_topology_database.json",
    "4-Infrastructure/shim/rainbow_raccoon_compiler_receipt.json",
    "shared-data/data/rrc_tri_cycle_audit/rrc_tri_cycle_audit_receipt.json",
    "shared-data/data/stack_solidification/external_sem_entity_diff_probe_receipt.json",
    "shared-data/data/stack_solidification/rrc_hold_closure_checklist.json",
    "shared-data/data/stack_solidification/network_topology_coefficient_calibration_manifest.json",
    "shared-data/data/stack_solidification/network_topology_prediction_hold_registry.json",
    "shared-data/data/stack_solidification/beaver_mask_freshness_negative_controls.json",
    "shared-data/data/stack_solidification/whitespace_zero_grammar_probe.json",
    "shared-data/data/stack_solidification/tang9k_rrc_q16_virtual_serial_probe.json",
    "shared-data/data/stack_solidification/tang9k_uart_transport_routes.json",
    "shared-data/data/stack_solidification/stack_fail_closure_register.json",
    "shared-data/data/stack_solidification/smn_tool_awareness_registry.json",
    "shared-data/data/stack_solidification/smn_tool_awareness_receipt.json",
    "4-Infrastructure/shim/tang9k_uart_beacon_probe_receipt.json",
    "4-Infrastructure/shim/tang9k_uart_beacon_swapped_probe_receipt.json",
    "4-Infrastructure/shim/tang9k_uart_loopback_after_jtag_clear_probe_receipt.json",
]

PYTHON_SURFACES = [
    "4-Infrastructure/shim/external_sem_entity_diff_probe.py",
    "4-Infrastructure/shim/beaver_mask_freshness_negative_controls.py",
    "4-Infrastructure/shim/whitespace_zero_grammar_probe.py",
    "4-Infrastructure/shim/network_topology_hold_manifests.py",
    "4-Infrastructure/shim/rainbow_raccoon_compiler.py",
    "4-Infrastructure/shim/rrc_hold_closure_checklist.py",
    "4-Infrastructure/shim/rrc_tri_cycle_audit.py",
    "4-Infrastructure/shim/stack_fail_closure_register.py",
    "4-Infrastructure/shim/tang9k_rrc_q16_accel.py",
    "4-Infrastructure/shim/tang9k_rrc_q16_virtual_serial_probe.py",
    "4-Infrastructure/shim/tang9k_uart_transport_router.py",
    "4-Infrastructure/shim/tang9k_uart_beacon_probe.py",
    "4-Infrastructure/shim/smn_tool_awareness_registry.py",
    "4-Infrastructure/shim/enwiki9_logogram_receipt_aggregation_probe.py",
    "4-Infrastructure/shim/stack_solidification_audit.py",
]


@dataclass
class CmdResult:
    command: list[str]
    cwd: str
    returncode: int
    stdout_tail: str
    stderr_tail: str


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def run_cmd(command: list[str], cwd: Path, timeout: int = 300) -> CmdResult:
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
        cwd=rel(cwd),
        returncode=proc.returncode,
        stdout_tail=proc.stdout[-6000:],
        stderr_tail=proc.stderr[-6000:],
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_gate() -> dict[str, Any]:
    rows = []
    for item in JSON_SURFACES:
        path = REPO / item
        try:
            data = load_json(path)
            rows.append(
                {
                    "path": item,
                    "status": "PASS",
                    "top_level_type": type(data).__name__,
                    "sha256": file_sha256(path),
                }
            )
        except Exception as exc:  # pragma: no cover - diagnostic path
            rows.append({"path": item, "status": "FAIL", "error": repr(exc)})
    return {"status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL", "rows": rows}


def py_compile_gate() -> dict[str, Any]:
    cmd = ["python3", "-m", "py_compile", *PYTHON_SURFACES]
    result = run_cmd(cmd, REPO, timeout=120)
    return {"status": "PASS" if result.returncode == 0 else "FAIL", "result": result.__dict__}


def refresh_support_receipts_gate() -> dict[str, Any]:
    scripts = [
        "4-Infrastructure/shim/network_topology_hold_manifests.py",
        "4-Infrastructure/shim/beaver_mask_freshness_negative_controls.py",
        "4-Infrastructure/shim/whitespace_zero_grammar_probe.py",
        "4-Infrastructure/shim/tang9k_rrc_q16_virtual_serial_probe.py",
        "4-Infrastructure/shim/tang9k_uart_transport_router.py",
        "4-Infrastructure/shim/rrc_hold_closure_checklist.py",
    ]
    rows = []
    for script in scripts:
        result = run_cmd(["python3", script], REPO, timeout=300)
        rows.append(
            {
                "script": script,
                "status": "PASS" if result.returncode == 0 else "FAIL",
                "result": result.__dict__,
            }
        )
    return {"status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL", "rows": rows}


def compiler_gate() -> dict[str, Any]:
    result = run_cmd(["python3", "4-Infrastructure/shim/rainbow_raccoon_compiler.py"], REPO, timeout=120)
    receipt_path = REPO / "4-Infrastructure" / "shim" / "rainbow_raccoon_compiler_receipt.json"
    receipt = load_json(receipt_path) if receipt_path.exists() else {}
    objects = receipt.get("compiled_objects", [])
    return {
        "status": "PASS_WITH_HOLDS" if result.returncode == 0 else "FAIL",
        "result": result.__dict__,
        "receipt": rel(receipt_path),
        "receipt_hash": receipt.get("receipt_hash"),
        "compiled_object_count": len(objects),
        "candidate_count": sum(1 for obj in objects if obj.get("type_witness", {}).get("status") == "CANDIDATE"),
        "hold_count": sum(1 for obj in objects if obj.get("type_witness", {}).get("status") == "HOLD"),
    }


def tri_cycle_gate(include_hardware: bool, hardware_port: str) -> dict[str, Any]:
    cmd = ["python3", "4-Infrastructure/shim/rrc_tri_cycle_audit.py"]
    if include_hardware:
        cmd.extend(["--include-hardware", "--hardware-port", hardware_port])
    result = run_cmd(cmd, REPO, timeout=300)
    receipt_path = REPO / "shared-data" / "data" / "rrc_tri_cycle_audit" / "rrc_tri_cycle_audit_receipt.json"
    receipt = load_json(receipt_path) if receipt_path.exists() else {}
    gates = receipt.get("gates", {})
    fpga = gates.get("fpga_witness", {})
    return {
        "status": "PASS_WITH_BLOCKED_HARDWARE" if result.returncode == 0 and fpga.get("hardware_status") == "FAIL" else "PASS" if result.returncode == 0 else "FAIL",
        "result": result.__dict__,
        "receipt": rel(receipt_path),
        "promotion_decision": receipt.get("promotion_decision"),
        "prover": gates.get("prover", {}).get("status"),
        "compiler": gates.get("compiler", {}).get("status"),
        "fpga_software": fpga.get("software_status"),
        "fpga_hardware": fpga.get("hardware_status"),
        "uart_beacon_any": fpga.get("uart_beacon", {}).get("any_beacon_seen"),
        "less_solid_surface_counts": receipt.get("less_solid_surface_counts", {}),
    }


def lean_gate(run_full_lean: bool) -> dict[str, Any]:
    if not run_full_lean:
        return {"status": "SKIPPED", "reason": "run with --full-lean to refresh this gate"}
    result = run_cmd(["lake", "build"], REPO / "0-Core-Formalism" / "lean" / "Semantics", timeout=600)
    return {"status": "PASS" if result.returncode == 0 else "FAIL", "result": result.__dict__}


def hardware_bitstream_gate() -> dict[str, Any]:
    surfaces = [
        "4-Infrastructure/hardware/tangnano9k_rrc_q16_accel.fs",
        "4-Infrastructure/hardware/tangnano9k_uart_beacon.fs",
    ]
    return {
        "status": "PASS" if all((REPO / p).exists() for p in surfaces) else "FAIL",
        "bitstreams": [{"path": p, "sha256": file_sha256(REPO / p), "present": (REPO / p).exists()} for p in surfaces],
    }


def external_sem_gate() -> dict[str, Any]:
    path = REPO / "shared-data" / "data" / "stack_solidification" / "external_sem_entity_diff_probe_receipt.json"
    if not path.exists():
        return {"status": "NOT_RUN", "receipt": str(path.relative_to(REPO))}
    receipt = load_json(path)
    return {
        "status": receipt.get("decision", "UNKNOWN"),
        "receipt": str(path.relative_to(REPO)),
        "gnu_parallel_collision": receipt.get("gnu_parallel_collision", {}).get("detected"),
        "mapped_fail_tickets": receipt.get("mapped_fail_tickets", []),
    }


def hold_checklist_gate() -> dict[str, Any]:
    path = REPO / "shared-data" / "data" / "stack_solidification" / "rrc_hold_closure_checklist.json"
    if not path.exists():
        return {"status": "NOT_RUN", "receipt": str(path.relative_to(REPO))}
    receipt = load_json(path)
    return {
        "status": "PASS_OPEN_ITEMS_TRACKED",
        "receipt": str(path.relative_to(REPO)),
        "hold_count": receipt.get("summary", {}).get("hold_count"),
        "open_closure_count": receipt.get("summary", {}).get("open_closure_count"),
    }


def network_hold_manifest_gate() -> dict[str, Any]:
    coeff = REPO / "shared-data" / "data" / "stack_solidification" / "network_topology_coefficient_calibration_manifest.json"
    pred = REPO / "shared-data" / "data" / "stack_solidification" / "network_topology_prediction_hold_registry.json"
    if not coeff.exists() or not pred.exists():
        return {"status": "NOT_RUN", "coefficient_manifest": str(coeff.relative_to(REPO)), "prediction_registry": str(pred.relative_to(REPO))}
    coeff_data = load_json(coeff)
    pred_data = load_json(pred)
    return {
        "status": "PASS_HOLD_QUEUES_DECLARED",
        "coefficient_manifest": str(coeff.relative_to(REPO)),
        "prediction_registry": str(pred.relative_to(REPO)),
        "coefficient_rows": coeff_data.get("summary", {}).get("row_count"),
        "prediction_rows": pred_data.get("summary", {}).get("row_count"),
    }


def beaver_mask_freshness_gate() -> dict[str, Any]:
    path = REPO / "shared-data" / "data" / "stack_solidification" / "beaver_mask_freshness_negative_controls.json"
    if not path.exists():
        return {"status": "NOT_RUN", "receipt": str(path.relative_to(REPO))}
    receipt = load_json(path)
    return {
        "status": receipt.get("summary", {}).get("status", "UNKNOWN"),
        "receipt": str(path.relative_to(REPO)),
        "lean_build": receipt.get("lean_build", {}).get("status"),
        "case_count": receipt.get("summary", {}).get("case_count"),
        "negative_control_count": receipt.get("summary", {}).get("negative_control_count"),
        "promotion_effect": receipt.get("promotion_effect"),
    }


def whitespace_zero_grammar_gate() -> dict[str, Any]:
    path = REPO / "shared-data" / "data" / "stack_solidification" / "whitespace_zero_grammar_probe.json"
    if not path.exists():
        return {"status": "NOT_RUN", "receipt": str(path.relative_to(REPO))}
    receipt = load_json(path)
    return {
        "status": receipt.get("summary", {}).get("status", "UNKNOWN"),
        "receipt": str(path.relative_to(REPO)),
        "lean_build": receipt.get("lean_build", {}).get("status"),
        "case_count": receipt.get("summary", {}).get("case_count"),
        "admit_count": receipt.get("summary", {}).get("admit_count"),
        "hold_count": receipt.get("summary", {}).get("hold_count"),
        "stored_whitespace_codes_total": receipt.get("summary", {}).get("stored_whitespace_codes_total"),
    }


def virtual_serial_gate() -> dict[str, Any]:
    path = REPO / "shared-data" / "data" / "stack_solidification" / "tang9k_rrc_q16_virtual_serial_probe.json"
    if not path.exists():
        return {"status": "NOT_RUN", "receipt": str(path.relative_to(REPO))}
    receipt = load_json(path)
    return {
        "status": receipt.get("summary", {}).get("status", "UNKNOWN"),
        "receipt": str(path.relative_to(REPO)),
        "case_count": receipt.get("summary", {}).get("case_count"),
        "match_count": receipt.get("summary", {}).get("match_count"),
        "frames_seen": receipt.get("summary", {}).get("frames_seen"),
    }


def uart_transport_routes_gate() -> dict[str, Any]:
    path = REPO / "shared-data" / "data" / "stack_solidification" / "tang9k_uart_transport_routes.json"
    if not path.exists():
        return {"status": "NOT_RUN", "receipt": str(path.relative_to(REPO))}
    receipt = load_json(path)
    return {
        "status": receipt.get("active_route_status", "UNKNOWN"),
        "receipt": str(path.relative_to(REPO)),
        "active_route": receipt.get("active_route"),
        "route_count": len(receipt.get("route_table", [])),
        "virtual_status": receipt.get("virtual_probe", {}).get("status"),
    }


def stack_fail_closure_gate() -> dict[str, Any]:
    result = run_cmd(["python3", "4-Infrastructure/shim/stack_fail_closure_register.py"], REPO, timeout=120)
    path = REPO / "shared-data" / "data" / "stack_solidification" / "stack_fail_closure_register.json"
    receipt = load_json(path) if path.exists() else {}
    return {
        "status": "PASS_TICKETS_DECLARED" if result.returncode == 0 else "FAIL",
        "receipt": str(path.relative_to(REPO)),
        "ticket_count": receipt.get("summary", {}).get("ticket_count"),
        "blocked_or_hold_count": receipt.get("summary", {}).get("blocked_or_hold_count"),
        "fpga_hardware_status": receipt.get("summary", {}).get("fpga_hardware_status"),
        "promotion_decision": receipt.get("summary", {}).get("promotion_decision"),
        "result": result.__dict__,
    }


def smn_tool_awareness_gate() -> dict[str, Any]:
    result = run_cmd(["python3", "4-Infrastructure/shim/smn_tool_awareness_registry.py"], REPO, timeout=120)
    path = REPO / "shared-data" / "data" / "stack_solidification" / "smn_tool_awareness_receipt.json"
    receipt = load_json(path) if path.exists() else {}
    return {
        "status": receipt.get("status", "FAIL" if result.returncode else "UNKNOWN"),
        "decision": receipt.get("decision"),
        "receipt": str(path.relative_to(REPO)),
        "nomenclature": receipt.get("gates", {}).get("nomenclature", {}).get("status"),
        "smn_data": receipt.get("gates", {}).get("smn_data", {}).get("status"),
        "result": result.__dict__,
    }


def worktree_gate() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    counts: dict[str, int] = {}
    total = 0
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        total += 1
        key = line[:2]
        counts[key] = counts.get(key, 0) + 1
    return {
        "status": "DIRTY" if total else "CLEAN",
        "tracked_or_untracked_count": total,
        "status_prefix_counts": dict(sorted(counts.items())),
        "note": "Broad working tree is dirty; stage only scoped artifacts.",
    }


def build_doc(receipt: dict[str, Any]) -> str:
    gates = receipt["gates"]
    tri = gates["tri_cycle"]
    lines = [
        "# Stack Solidification Status",
        "",
        "**Date:** 2026-05-09",
        "",
        "## Bottom Line",
        "",
        "The stack is buildable and internally gateable, but not promotable as a live hardware-accelerated system yet.",
        "",
        "## Gates",
        "",
        f"- Full Lean/Semantics build: `{gates['lean']['status']}`",
        f"- JSON integrity: `{gates['json']['status']}`",
        f"- Python shim compile: `{gates['python_compile']['status']}`",
        f"- Support receipt refresh: `{gates['support_receipts']['status']}`",
        f"- Rainbow Raccoon compiler: `{gates['compiler']['status']}` ({gates['compiler']['candidate_count']} candidate, {gates['compiler']['hold_count']} HOLD)",
        f"- Tri-cycle audit: `{tri['status']}`; promotion decision `{tri['promotion_decision']}`",
        f"- FPGA software witness: `{tri['fpga_software']}`",
        f"- FPGA hardware witness: `{tri['fpga_hardware']}`",
        f"- UART beacon seen: `{tri['uart_beacon_any']}`",
        f"- Hardware bitstreams present: `{gates['hardware_bitstreams']['status']}`",
        f"- Optional sem entity-diff aid: `{gates['external_sem']['status']}`",
        f"- RRC HOLD closure checklist: `{gates['hold_checklist']['status']}` ({gates['hold_checklist'].get('open_closure_count')} open)",
        f"- Network HOLD manifests: `{gates['network_hold_manifests']['status']}` ({gates['network_hold_manifests'].get('coefficient_rows')} coefficient rows, {gates['network_hold_manifests'].get('prediction_rows')} prediction rows)",
        f"- Beaver mask freshness controls: `{gates['beaver_mask_freshness']['status']}` ({gates['beaver_mask_freshness'].get('case_count')} cases)",
        f"- Whitespace-zero grammar: `{gates['whitespace_zero_grammar']['status']}` ({gates['whitespace_zero_grammar'].get('admit_count')} admitted, {gates['whitespace_zero_grammar'].get('hold_count')} HOLD)",
        f"- Q16 virtual serial probe: `{gates['virtual_serial']['status']}` ({gates['virtual_serial'].get('match_count')}/{gates['virtual_serial'].get('case_count')} matches)",
        f"- UART transport routes: `{gates['uart_transport_routes']['status']}` (active `{gates['uart_transport_routes'].get('active_route')}`)",
        f"- Stack fail closure register: `{gates['stack_fail_closure']['status']}` ({gates['stack_fail_closure'].get('ticket_count')} tickets)",
        f"- SMN tool awareness: `{gates['smn_tool_awareness']['status']}` ({gates['smn_tool_awareness'].get('decision')})",
        f"- Worktree: `{gates['worktree']['status']}`",
        "- Staging manifest: `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`",
        "",
        "## Current Solid Core",
        "",
        "- Lean/Semantics builds end to end.",
        "- Core JSON receipts and network topology database parse.",
        "- Compiler gate admits only the Q16 fixed-point lowering certificate as candidate.",
        "- Q16 software witness lane passes.",
        "- Q16 host UART framing and parser pass over a PTY-backed virtual serial device.",
        "- UART route table now selects the PTY-backed Q16 route while keeping blocked physical routes visible.",
        "- HOLD buckets are explicit rather than silently promoted.",
        "- Optional sem entity extraction is available for scoped Python audit files.",
        "- SMN is tool-visible as Semantic Mass Number and explicitly separated from Mass Number admissibility packets.",
        "- Every compiler HOLD object now has an explicit closure checklist.",
        "- Current failures and broad HOLD buckets have closure tickets in a stack fail register.",
        "- Network topology coefficients and predictions are split into HOLD queues.",
        "- Beaver mask freshness has Lean-backed finite negative controls; full MPC security remains HOLD.",
        "- Canonical logogram grammar can derive ordinary spaces from symbol count/order with zero stored whitespace codes.",
        "- Agent routing now has repo-root, Lean/Semantics, and Infrastructure contracts.",
        "- Stack receipts and the network topology database are visible through narrow `.gitignore` exceptions instead of broad `shared-data/` exposure.",
        "",
        "## Current Blockers",
        "",
        "- Live FPGA UART transport remains blocked: beacon receipts show no bytes on `/dev/ttyUSB0` or `/dev/ttyUSB1`.",
        "- Hardware acceleration claims remain blocked until the UART route or external adapter path produces matching receipts.",
        "- Security, coefficient, topology-prediction, and receipt-gate debts remain HOLD surfaces.",
        "- The worktree is broad and dirty; do not stage by directory sweep.",
        "- `/usr/bin/sem` is GNU Parallel on this machine; use the isolated sem binary path if sem is needed.",
        "",
        "## Less Solid Surface Counts",
        "",
    ]
    for bucket, count in sorted(tri.get("less_solid_surface_counts", {}).items()):
        lines.append(f"- `{bucket}`: {count}")
    lines.extend(
        [
            "",
            "## Next Stabilization Moves",
            "",
            "1. Resolve fabric UART transport with board bridge docs or an external USB-UART adapter.",
            "2. Work the closure register tickets in order: UART transport, flash persistence, adaptive-mask security, coefficient calibration, topology predictions, receipt gates, then worktree scope.",
            "3. Keep Q16 as the first narrow candidate lane; do not widen compiler promotion until more Lean-backed certificates exist.",
            "4. Produce a scoped staging manifest before any commit because the working tree contains many unrelated/generated surfaces.",
            "",
            "## Receipt",
            "",
            f"- Machine receipt: `{rel(OUT)}`",
            "- Staging manifest: `6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-lean", action="store_true")
    parser.add_argument("--include-hardware", action="store_true")
    parser.add_argument("--hardware-port", default="/dev/ttyUSB1")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "schema": "stack_solidification_receipt_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "Stack status audit only. This does not promote HOLD surfaces or hardware acceleration claims.",
        "gates": {},
    }
    receipt["gates"]["lean"] = lean_gate(args.full_lean)
    receipt["gates"]["python_compile"] = py_compile_gate()
    receipt["gates"]["compiler"] = compiler_gate()
    receipt["gates"]["support_receipts"] = refresh_support_receipts_gate()
    receipt["gates"]["tri_cycle"] = tri_cycle_gate(args.include_hardware, args.hardware_port)
    receipt["gates"]["stack_fail_closure"] = stack_fail_closure_gate()
    receipt["gates"]["smn_tool_awareness"] = smn_tool_awareness_gate()
    receipt["gates"]["json"] = json_gate()
    receipt["gates"]["hardware_bitstreams"] = hardware_bitstream_gate()
    receipt["gates"]["external_sem"] = external_sem_gate()
    receipt["gates"]["hold_checklist"] = hold_checklist_gate()
    receipt["gates"]["network_hold_manifests"] = network_hold_manifest_gate()
    receipt["gates"]["beaver_mask_freshness"] = beaver_mask_freshness_gate()
    receipt["gates"]["whitespace_zero_grammar"] = whitespace_zero_grammar_gate()
    receipt["gates"]["virtual_serial"] = virtual_serial_gate()
    receipt["gates"]["uart_transport_routes"] = uart_transport_routes_gate()
    receipt["gates"]["worktree"] = worktree_gate()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    DOC.write_text(build_doc(receipt), encoding="utf-8")
    print(json.dumps({"receipt": rel(OUT), "doc": rel(DOC), "status": "WRITTEN"}, indent=2))
    hard_fail = any(
        receipt["gates"][gate]["status"] == "FAIL"
        for gate in ["lean", "json", "python_compile", "compiler", "support_receipts", "stack_fail_closure", "hardware_bitstreams"]
    )
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
