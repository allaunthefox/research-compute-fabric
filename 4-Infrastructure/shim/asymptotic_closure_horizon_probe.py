#!/usr/bin/env python3
"""Receipt-backed asymptotic closure horizon probe.

An asymptote is a useful metaphor with a sharp operational rule: approaching a
gate is not passing it. A route that improves forever but has no finite
intersection with replay, byte law, residual closure, or source receipts remains
HOLD_ASYMPTOTIC.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "asymptotic_closure_horizon"
REGISTRY = OUT_DIR / "asymptotic_closure_horizon_registry.json"
RECEIPT = OUT_DIR / "asymptotic_closure_horizon_receipt.json"
SUMMARY = OUT_DIR / "asymptotic_closure_horizon.md"

TREE_FIDDY_CAGE_BOUNDARY_BYTES = 350

CITATIONS = [
    {
        "id": "user_supplied_asymptote_meme",
        "title": "Asymptote meme: a line that meets the curve at infinity",
        "role": "source_prompt",
        "status": "user_supplied_image_prompt",
    },
    {
        "id": "bibliographic_event_horizon_receipt",
        "title": "Bibliographic event horizon receipt",
        "path": "shared-data/data/bibliographic_event_horizon/bibliographic_event_horizon_receipt.json",
        "role": "local_route_input",
        "status": "receipt_bound_diagnostic",
    },
    {
        "id": "mmff_rigid_body_geometry_receipt",
        "title": "MMFF rigid-body geometry receipt",
        "path": "shared-data/data/mmff_rigid_body_geometry/mmff_rigid_body_geometry_receipt.json",
        "role": "finite_pass_example",
        "status": "coordinate_replay_fixture",
    },
    {
        "id": "forward_foundation_equation_compiler",
        "title": "Forward foundation equation compiler",
        "path": "6-Documentation/docs/specs/FORWARD_FOUNDATION_EQUATION_COMPILER.md",
        "role": "local_trust_boundary",
        "status": "finite_forward_receipt_required",
    },
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def route(
    *,
    route_id: str,
    surface: str,
    finite_gate: str,
    approach_milli: int,
    finite_intersection: bool,
    receipt_complete: bool,
    residual_declared: bool,
    byte_law_checked: bool,
) -> dict[str, Any]:
    passes = finite_intersection and receipt_complete and residual_declared and byte_law_checked
    asymptotic_hold = approach_milli >= 950 and not passes
    item = {
        "route_id": route_id,
        "surface": surface,
        "finite_gate": finite_gate,
        "approach_milli": approach_milli,
        "finite_intersection": finite_intersection,
        "receipt_complete": receipt_complete,
        "residual_declared": residual_declared,
        "byte_law_checked": byte_law_checked,
        "passes": passes,
        "asymptotic_hold": asymptotic_hold,
        "decision": "ADMIT_FINITE_INTERSECTION" if passes else ("HOLD_ASYMPTOTIC" if asymptotic_hold else "HOLD_INCOMPLETE"),
        "repair": "find a finite witness, not a prettier limit argument" if asymptotic_hold else "complete finite gate receipts",
    }
    item["route_hash"] = hash_obj({k: v for k, v in item.items() if k != "route_hash"})
    return item


def build_registry() -> dict[str, Any]:
    routes = [
        route(
            route_id="citation_gravity_near_authority",
            surface="bibliographic event horizon",
            finite_gate="forward derivation receipt",
            approach_milli=990,
            finite_intersection=False,
            receipt_complete=False,
            residual_declared=True,
            byte_law_checked=False,
        ),
        route(
            route_id="compression_global_near_zero",
            surface="enwiki/logogram compression ladder",
            finite_gate="delta_global > 0 under counted dictionary/protocol/receipt bytes",
            approach_milli=975,
            finite_intersection=False,
            receipt_complete=True,
            residual_declared=True,
            byte_law_checked=True,
        ),
        route(
            route_id="mmff_geometry_coordinate_replay",
            surface="MMFF rigid-body coordinate shadow",
            finite_gate="exact coordinate replay with bounded O-AMMR archive",
            approach_milli=1000,
            finite_intersection=True,
            receipt_complete=True,
            residual_declared=True,
            byte_law_checked=True,
        ),
        route(
            route_id="proof_label_dependency_chain",
            surface="theorem/citation label chain",
            finite_gate="compiled forward from foundation kernel with closure witness",
            approach_milli=995,
            finite_intersection=False,
            receipt_complete=False,
            residual_declared=False,
            byte_law_checked=False,
        ),
    ]
    archive_bytes = 32 + len(routes) * 44
    return {
        "schema": "asymptotic_closure_horizon_registry_v1",
        "source_prompt": {
            "meme": "Asymptote: A line that meets the curve at infinity",
            "operational_rewrite": "A route that meets the gate only at infinity has not passed a finite receipt gate.",
        },
        "citations": CITATIONS,
        "claim_boundary": (
            "Asymptotic closure is an admission diagnostic only. It does not reject "
            "limits or asymptotic analysis as mathematics; it rejects infinite-approach "
            "language as a substitute for finite replay, residual, receipt, and byte-law evidence."
        ),
        "equation": {
            "finite_pass": "finite_intersection and receipt_complete and residual_declared and byte_law_checked",
            "asymptotic_hold": "approach_milli >= 950 and not finite_pass",
        },
        "tree_fiddy_guard": {
            "cage_boundary_bytes": TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "archive_bytes": archive_bytes,
            "archive_admissible": archive_bytes <= TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "active_pull_rule": "Q_active(i)=0 only after finite pass or bounded diagnostic archive",
        },
        "routes": routes,
        "aggregates": {
            "route_count": len(routes),
            "finite_pass_count": sum(1 for item in routes if item["passes"]),
            "asymptotic_hold_count": sum(1 for item in routes if item["asymptotic_hold"]),
            "incomplete_hold_count": sum(1 for item in routes if item["decision"] == "HOLD_INCOMPLETE"),
            "tree_fiddy_archive_bytes": archive_bytes,
            "tree_fiddy_cage_boundary_bytes": TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "tree_fiddy_archive_admissible": archive_bytes <= TREE_FIDDY_CAGE_BOUNDARY_BYTES,
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "asymptotic_closure_horizon_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "citations": registry["citations"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_ASYMPTOTIC_HOLD_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Asymptotic Closure Horizon Probe",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Rule",
        "",
        f"- Finite pass: `{registry['equation']['finite_pass']}`",
        f"- Asymptotic hold: `{registry['equation']['asymptotic_hold']}`",
        "",
        "## Routes",
        "",
        "| Route | Surface | Approach | Finite intersection | Decision |",
        "|---|---|---:|---|---|",
    ]
    for item in registry["routes"]:
        lines.append(
            f"| `{item['route_id']}` | {item['surface']} | {item['approach_milli']} | "
            f"`{item['finite_intersection']}` | `{item['decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Tree Fiddy Guard",
            "",
            f"- Archive bytes: `{registry['aggregates']['tree_fiddy_archive_bytes']}` / `{registry['aggregates']['tree_fiddy_cage_boundary_bytes']}`",
            f"- Archive admissible: `{registry['aggregates']['tree_fiddy_archive_admissible']}`",
            "",
            "## Citations",
            "",
        ]
    )
    for citation in registry["citations"]:
        target = citation.get("url") or citation.get("path") or citation["status"]
        lines.append(f"- `{citation['id']}`: {citation['title']} ({target}); role: `{citation['role']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "aggregates": registry["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
