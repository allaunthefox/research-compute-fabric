#!/usr/bin/env python3
"""Generate closure checklists for Rainbow Raccoon Compiler HOLD objects."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
COMPILER_RECEIPT = REPO / "4-Infrastructure" / "shim" / "rainbow_raccoon_compiler_receipt.json"
OUT_DIR = REPO / "shared-data" / "data" / "stack_solidification"
OUT = OUT_DIR / "rrc_hold_closure_checklist.json"
DOC = REPO / "6-Documentation" / "docs" / "rrc_hold_closure_checklist_2026-05-09.md"


AXIS_CLOSURE = {
    "lean_or_independent_replay_gate": {
        "gate": "Lean theorem, native_decide witness, or independent replay receipt exists",
        "action": "add a replay harness or Lean theorem for the object-specific invariant",
    },
    "scale_band_declared": {
        "gate": "scale/range band is explicit and checked",
        "action": "declare numeric scale band, unit domain, and overflow behavior",
    },
    "projection_declared": {
        "gate": "projection map from source object to manifold axes exists",
        "action": "define projection axes and hash the projection payload",
    },
    "witness_declared": {
        "gate": "witness payload and verifier are named",
        "action": "attach witness schema, verifier command, and receipt path",
    },
    "decoder_declared": {
        "gate": "decoder/replay route is named",
        "action": "attach decoder route and exact replay hash",
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def checklist_item(obj: dict[str, Any]) -> dict[str, Any]:
    source = obj["object"]
    witness = obj["type_witness"]
    missing = witness.get("missing_or_weak_axes", [])
    closures = []
    for axis in missing:
        spec = AXIS_CLOSURE.get(
            axis,
            {
                "gate": f"{axis} closed with explicit receipt",
                "action": f"add closure evidence for {axis}",
            },
        )
        closures.append({"axis": axis, **spec, "status": "OPEN"})
    return {
        "object_id": source["object_id"],
        "label": source["label"],
        "kind": source["kind"],
        "source_path": source["source_path"],
        "payload_sha256": source["payload_sha256"],
        "nearest_shape": obj["nearest_lawful_shape"]["shape"],
        "status": witness["status"],
        "lean_boundary": witness.get("lean_boundary"),
        "closures": closures,
        "promotion_rule": "Remain HOLD until every closure status is CLOSED and the compiler rerun emits CANDIDATE.",
    }


def build_doc(receipt: dict[str, Any]) -> str:
    lines = [
        "# RRC HOLD Closure Checklist",
        "",
        "**Date:** 2026-05-09",
        "",
        "This document gives each Rainbow Raccoon Compiler HOLD object a concrete closure checklist.",
        "",
        "## Summary",
        "",
        f"- Compiler receipt hash: `{receipt['compiler_receipt_hash']}`",
        f"- HOLD objects: `{receipt['summary']['hold_count']}`",
        f"- Candidate objects: `{receipt['summary']['candidate_count']}`",
        f"- Open closure items: `{receipt['summary']['open_closure_count']}`",
        "",
        "## HOLD Objects",
        "",
    ]
    for item in receipt["hold_objects"]:
        lines.append(f"### `{item['object_id']}` {item['label']}")
        lines.append("")
        lines.append(f"- Shape: `{item['nearest_shape']}`")
        lines.append(f"- Source: `{item['source_path']}`")
        lines.append(f"- Payload SHA-256: `{item['payload_sha256']}`")
        lines.append(f"- Lean boundary: `{item['lean_boundary']}`")
        for closure in item["closures"]:
            lines.append(f"- OPEN `{closure['axis']}`: {closure['gate']}")
            lines.append(f"- Action: {closure['action']}")
        lines.append(f"- Promotion rule: {item['promotion_rule']}")
        lines.append("")
    lines.append("## Candidate Objects")
    lines.append("")
    for item in receipt["candidate_objects"]:
        lines.append(f"- `{item['object_id']}` {item['label']} -> `{item['nearest_shape']}`")
    lines.append("")
    lines.append("## Machine Receipt")
    lines.append("")
    lines.append(f"- `{OUT.relative_to(REPO)}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    compiler = load_json(COMPILER_RECEIPT)
    hold_objects = []
    candidate_objects = []
    for obj in compiler.get("compiled_objects", []):
        status = obj.get("type_witness", {}).get("status")
        if status == "HOLD":
            hold_objects.append(checklist_item(obj))
        elif status == "CANDIDATE":
            candidate_objects.append(checklist_item(obj))
    receipt = {
        "schema": "rrc_hold_closure_checklist_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "compiler_receipt": str(COMPILER_RECEIPT.relative_to(REPO)),
        "compiler_receipt_hash": compiler.get("receipt_hash"),
        "claim_boundary": "Checklist only. This does not close HOLD objects or promote compiler candidates.",
        "summary": {
            "hold_count": len(hold_objects),
            "candidate_count": len(candidate_objects),
            "open_closure_count": sum(len(item["closures"]) for item in hold_objects),
        },
        "hold_objects": hold_objects,
        "candidate_objects": candidate_objects,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    DOC.write_text(build_doc(receipt), encoding="utf-8")
    print(json.dumps({"receipt": str(OUT.relative_to(REPO)), "doc": str(DOC.relative_to(REPO)), "open_closures": receipt["summary"]["open_closure_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
