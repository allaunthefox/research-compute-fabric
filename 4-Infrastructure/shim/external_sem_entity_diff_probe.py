#!/usr/bin/env python3
"""Probe Ataraxy-Labs/sem as an optional entity-level diff aid.

No code is imported into the stack. This records whether a caller-provided sem
binary can extract entity surfaces for the current solidification tools and
where it helps close failure tickets.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "shared-data" / "data" / "stack_solidification" / "external_sem_entity_diff_probe_receipt.json"
DOC = REPO / "6-Documentation" / "docs" / "external_sem_entity_diff_probe_2026-05-09.md"

TARGETS = [
    "4-Infrastructure/shim/stack_fail_closure_register.py",
    "4-Infrastructure/shim/tang9k_uart_beacon_probe.py",
    "4-Infrastructure/shim/stack_solidification_audit.py",
    "4-Infrastructure/shim/rrc_tri_cycle_audit.py",
]


def run(command: list[str], timeout: int = 120) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def parse_entities(stdout: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return data
    return []


def build_doc(receipt: dict[str, Any]) -> str:
    lines = [
        "# External sem Entity-Diff Probe",
        "",
        "**Date:** 2026-05-09",
        "",
        "## Decision",
        "",
        f"- Status: `{receipt['decision']}`",
        "- No implementation code was imported.",
        "- No repository dependency was added.",
        "- Use only as an optional external audit aid unless explicitly vendored later.",
        "",
        "## Why It Helps",
        "",
        "- Primary fit: `FAIL-WORKTREE-SCOPE-007`, because entity-level diffs reduce broad dirty-tree risk.",
        "- Secondary fit: `FAIL-RECEIPT-GATE-006`, because entity IDs can be attached to receipt and rollback checklists.",
        "- It does not close security, coefficient, topology prediction, or FPGA transport gates by itself.",
        "",
        "## Tool Boundary",
        "",
        f"- Source: `{receipt['source_url']}`",
        f"- License: `{receipt['license']}`",
        f"- Requested binary: `{receipt['sem_binary']}`",
        f"- Version result: `{receipt['version']['stdout_tail'].strip()}`",
        f"- `/usr/bin/sem` collision: `{receipt['gnu_parallel_collision']['detected']}`",
        "",
        "## Entity Probe",
        "",
    ]
    for row in receipt["entity_targets"]:
        lines.append(f"### `{row['path']}`")
        lines.append("")
        lines.append(f"- Status: `{row['status']}`")
        for entity in row.get("entities", []):
            lines.append(
                f"- `{entity.get('type')}` `{entity.get('name')}` lines {entity.get('start_line')}-{entity.get('end_line')}"
            )
        lines.append("")
    lines.append("## Machine Receipt")
    lines.append("")
    lines.append(f"- `{OUT.relative_to(REPO)}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sem-bin", default="/tmp/sem_probe/sem/crates/target/release/sem")
    args = parser.parse_args()

    sem_bin = Path(args.sem_bin)
    version = run([str(sem_bin), "--version"]) if sem_bin.exists() else {
        "command": [str(sem_bin), "--version"],
        "returncode": 127,
        "stdout_tail": "",
        "stderr_tail": "sem binary not found",
    }
    gnu = run(["/usr/bin/sem", "--version"]) if Path("/usr/bin/sem").exists() else {
        "command": ["/usr/bin/sem", "--version"],
        "returncode": 127,
        "stdout_tail": "",
        "stderr_tail": "not found",
    }
    entity_targets = []
    for target in TARGETS:
        if not sem_bin.exists():
            result = {"returncode": 127, "stdout_tail": "", "stderr_tail": "sem binary not found"}
        else:
            result = run([str(sem_bin), "entities", target, "--json"])
        entities = parse_entities(result.get("stdout_tail", ""))
        entity_targets.append(
            {
                "path": target,
                "status": "PASS" if result["returncode"] == 0 and entities else "FAIL",
                "entity_count": len(entities),
                "entities": entities,
                "stderr_tail": result.get("stderr_tail", ""),
            }
        )

    receipt = {
        "schema": "external_sem_entity_diff_probe_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": "https://github.com/Ataraxy-Labs/sem",
        "license": "MIT OR Apache-2.0",
        "sem_binary": str(sem_bin),
        "version": version,
        "gnu_parallel_collision": {
            "detected": "GNU parallel" in gnu.get("stdout_tail", "") or "GNU parallel" in gnu.get("stderr_tail", ""),
            "version_probe": gnu,
        },
        "entity_targets": entity_targets,
        "mapped_fail_tickets": [
            "FAIL-WORKTREE-SCOPE-007",
            "FAIL-RECEIPT-GATE-006",
        ],
        "decision": (
            "OPTIONAL_AUDIT_AID_READY"
            if version["returncode"] == 0 and all(row["status"] == "PASS" for row in entity_targets)
            else "OPTIONAL_AUDIT_AID_NOT_READY"
        ),
        "claim_boundary": "External tool orientation only. This does not import sem code, add sem as a dependency, or close any HOLD gate by itself.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    DOC.write_text(build_doc(receipt), encoding="utf-8")
    print(json.dumps({"receipt": str(OUT.relative_to(REPO)), "doc": str(DOC.relative_to(REPO)), "decision": receipt["decision"]}, indent=2))
    return 0 if receipt["decision"] == "OPTIONAL_AUDIT_AID_READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
