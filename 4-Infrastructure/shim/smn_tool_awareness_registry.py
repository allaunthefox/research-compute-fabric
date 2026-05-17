#!/usr/bin/env python3
"""Emit the tool-facing SMN naming boundary registry.

This keeps downstream shims from conflating:

- Semantic Mass: raw semantic/routing pressure
- SMN: Semantic Mass Number, a counted semantic-load index
- Mass Number: admissibility packet with residual and boundary guard

The registry is a routing/validation aid only. It does not promote SMN scores to
truth claims or Mass Number receipts.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "stack_solidification"
REGISTRY = OUT_DIR / "smn_tool_awareness_registry.json"
RECEIPT = OUT_DIR / "smn_tool_awareness_receipt.json"

CANONICAL_FILES = [
    REPO / "6-Documentation/docs/specs/SMN_SEMANTIC_MASS_NUMBERS.md",
    REPO / "6-Documentation/tiddlywiki-local/wiki/tiddlers/Semantic Mass Numbers.tid",
    REPO / "6-Documentation/tiddlywiki-local/wiki/tiddlers/Mass Number Theory.tid",
    REPO / "6-Documentation/wiki/Concept-Archive.md",
    REPO / "0-Core-Formalism/otom/docs/wiki/NotationNomenclatureRegistry.md",
    REPO / "shared-data/data/stellar_gas_observation/sdss_manga_dr17_emission_line_channels.json",
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def file_entry(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_bytes(path.read_bytes()) if path.exists() else None,
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def smn_data_gate() -> dict[str, Any]:
    path = REPO / "shared-data/data/stellar_gas_observation/sdss_manga_dr17_emission_line_channels.json"
    if not path.exists():
        return {"status": "MISSING", "path": rel(path)}
    data = load_json(path)
    failures: list[dict[str, Any]] = []
    channel_count = 0
    ratio_count = 0
    for kind, items in (("channel", data.get("channels", [])), ("diagnostic_ratio", data.get("diagnostic_ratios", []))):
        for item in items:
            payload = item.get("semantic_mass_number")
            object_id = item.get("label") or item.get("id")
            if not payload:
                failures.append({"kind": kind, "object_id": object_id, "failure": "missing_semantic_mass_number"})
                continue
            components = payload.get("components", {})
            expected = sum(int(value) for value in components.values())
            if payload.get("smn") != expected:
                failures.append({"kind": kind, "object_id": object_id, "failure": "component_sum_mismatch"})
            if payload.get("not_atomic_mass_number") is not True:
                failures.append({"kind": kind, "object_id": object_id, "failure": "missing_not_atomic_mass_number_guard"})
            if payload.get("not_mass_number_receipt") is not True:
                failures.append({"kind": kind, "object_id": object_id, "failure": "missing_not_mass_number_receipt_guard"})
            if kind == "channel":
                channel_count += 1
            else:
                ratio_count += 1
    return {
        "status": "PASS" if not failures else "FAIL",
        "path": rel(path),
        "channels_checked": channel_count,
        "diagnostic_ratios_checked": ratio_count,
        "failures": failures,
    }


def nomenclature_gate() -> dict[str, Any]:
    path = REPO / "0-Core-Formalism/otom/docs/wiki/NotationNomenclatureRegistry.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    required = [
        "mass_number != SMN",
        "SMN != atomic_mass_number",
        "SMN != Mass_Number_receipt",
        "| `smn` | Semantic Mass Number |",
        "Do not use this as an alias for SMN",
    ]
    missing = [item for item in required if item not in text]
    forbidden = ["| `mass_number` | Mass Number | semantic mass number"]
    forbidden_hits = [item for item in forbidden if item in text]
    return {
        "status": "PASS" if not missing and not forbidden_hits else "FAIL",
        "path": rel(path),
        "missing": missing,
        "forbidden_hits": forbidden_hits,
    }


def build_registry() -> dict[str, Any]:
    registry = {
        "schema": "smn_tool_awareness_registry_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "Tool awareness only. SMN routes attention; it is not physical mass, proof, truth, or a Mass Number admissibility receipt.",
        "canonical_terms": [
            {
                "term": "Semantic Mass",
                "tool_key": "semantic_mass",
                "meaning": "raw semantic/routing pressure or burden",
                "not_equal_to": ["SMN", "Mass Number", "physical mass"],
            },
            {
                "term": "SMN",
                "expanded": "Semantic Mass Number",
                "tool_key": "smn",
                "meaning": "countable project-local semantic-load number for a symbol, channel, ratio, route, or gate",
                "formula": "SMN(x)=identity_load+relation_load+provenance_load+constraint_load+decision_load+repair_load",
                "not_equal_to": ["atomic mass number", "isotope mass", "SI mass", "Mass Number admissibility packet", "proof", "truth"],
            },
            {
                "term": "Mass Number",
                "tool_key": "mass_number",
                "meaning": "admissibility/accounting packet with residual and boundary guard",
                "not_equal_to": ["SMN", "atomic mass number", "physical mass"],
            },
        ],
        "normalization_rules": [
            {
                "match": "semantic mass number",
                "normalize_to": "SMN",
                "reason": "Avoid aliasing Mass Number admissibility packets.",
            },
            {
                "match": "mass_number",
                "normalize_to": "Mass Number",
                "reason": "Keep existing admissibility-gate code paths intact.",
            },
            {
                "match": "semantic_mass_number",
                "normalize_to": "SMN data payload",
                "reason": "Machine-readable score object, not physical mass and not proof.",
            },
        ],
        "tool_rules": {
            "search_index": "Index SMN as semantic-load terminology; do not merge with MassNumber gate entries.",
            "tiddlywiki": "Link SMN references to [[Semantic Mass Numbers]] and Mass Number gate references to [[Mass Number Theory]].",
            "equation_awareness": "Classify SMN formulas as semantic_load, not mass_number_transform.",
            "stellar_gas_tools": "Read semantic_mass_number payloads as routing/audit priority metadata only.",
            "promotion_gate": "High SMN may prioritize review but cannot admit without a receipt gate.",
        },
        "canonical_files": [file_entry(path) for path in CANONICAL_FILES],
        "gates": {
            "nomenclature": nomenclature_gate(),
            "smn_data": smn_data_gate(),
        },
    }
    registry["registry_hash"] = hash_obj({k: v for k, v in registry.items() if k != "registry_hash"})
    return registry


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    status = "PASS" if all(gate.get("status") == "PASS" for gate in registry["gates"].values()) else "FAIL"
    receipt = {
        "schema": "smn_tool_awareness_receipt_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "ADMIT_SMN_TOOL_AWARENESS" if status == "PASS" else "HOLD_SMN_TOOL_AWARENESS",
        "claim_boundary": registry["claim_boundary"],
        "registry": rel(REGISTRY),
        "registry_hash": registry["registry_hash"],
        "status": status,
        "gates": registry["gates"],
    }
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"registry": rel(REGISTRY), "receipt": rel(RECEIPT), "status": status}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
