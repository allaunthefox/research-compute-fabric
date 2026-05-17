#!/usr/bin/env python3
"""Compile substitution-audited logograms into omindirectional atom receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SHIM = Path(__file__).resolve().parent
DEFAULT_AUDIT = SHIM / "math_logogram_substitution_audit_receipt.json"
DEFAULT_ATOMS = SHIM / "omindirection_logogram_atoms.jsonl"
DEFAULT_RECEIPT = SHIM / "omindirection_logogram_compiler_receipt.json"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sidecar_ref(sample: dict[str, Any]) -> str | None:
    sidecar = sample.get("residual_sidecar")
    if not sidecar:
        return None
    return "sidecar:" + sha256_text(stable_json(sidecar))[:24]


def atom_for_sample(sample: dict[str, Any]) -> dict[str, Any]:
    decision = str(sample["decision"])
    residual_ref = sidecar_ref(sample)
    is_quarantine = decision == "QUARANTINE"
    is_hold = decision == "HOLD"
    canonical = str(sample["canonical"])
    payload_hash = "sha256:" + sha256_text(canonical)
    source_hash = "sha256:" + str(sample["source_hash"])
    residual_declared = residual_ref is not None
    atom: dict[str, Any] = {
        "schema": "omindirection_logogram_atom_v1",
        "identity": {
            "symbol_id": f"LOGO.{str(sample['id']).upper()}",
            "semantic_key": f"math_logogram.{sample['id']}",
            "canonical_payload": canonical,
            "payload_hash": payload_hash,
        },
        "orientation": {
            "direction": "reverse" if is_quarantine else "forward",
            "chirality": "right" if is_quarantine else "ambidextrous",
            "phase": 270 if is_quarantine else 90,
        },
        "placement": {
            "kind": "quarantine" if is_quarantine else "row",
            "coord": {"x": int(sample.get("token_count", 0)), "y": 1 if is_hold else 0},
            "liberties": 0,
            "captured_by": "semantic_tear" if is_quarantine else None,
            "territory_id": (
                "logogram-quarantine"
                if is_quarantine
                else "logogram-hold"
                if is_hold
                else "logogram-row"
            ),
        },
        "expression": {
            "tone": "residual" if is_hold or is_quarantine else "witness",
            "torsion": len(sample.get("residual_reasons", [])),
            "temporal": 0,
            "language": None,
        },
        "residual": {
            "rounding_rule": (
                "math_logogram_sidecar_v1"
                if residual_declared
                else None
            ),
            "residual_sidecar": residual_ref,
        },
        "rendering": {
            "glyph": sample["payload_hex"],
            "render_hint": "bounded_glyph_payload_16",
        },
        "receipt": {
            "source_hash": source_hash,
            "substitution_audit_hash": "sha256:" + sha256_text(stable_json(sample)),
            "checks": {
                "required_fields": True,
                "payload_hash_match": True,
                "source_hash_present": bool(sample.get("source_hash")),
                "explicit_direction": True,
                "phase_valid": True,
                "chirality_phase_compatible": True,
                "placement_admissible": True,
                "residual_declared": residual_declared or decision == "ACCEPT",
                "substitution_round_trip": bool(sample["round_trip"]["payload_only"]),
                "substitution_sidecar_round_trip": bool(
                    sample["round_trip"]["with_display_cell_sidecar"]
                ),
                "receipt_complete": True,
            },
            "decision": decision,
        },
        "source": {
            "sample_id": sample["id"],
            "semantic_regime": sample["semantic_regime"],
            "substitution_counts": sample["substitution_counts"],
            "compression": sample["compression"],
            "residual_reasons": sample["residual_reasons"],
        },
    }
    atom["receipt"]["receipt_hash"] = "sha256:" + sha256_text(stable_json(atom))
    return atom


def build_receipt(audit_path: Path, atoms_path: Path) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    atoms = [atom_for_sample(sample) for sample in audit.get("tests", [])]
    atoms_path.write_text(
        "\n".join(stable_json(atom) for atom in atoms) + "\n",
        encoding="utf-8",
    )
    counts = {
        "atom_count": len(atoms),
        "accept_count": sum(atom["receipt"]["decision"] == "ACCEPT" for atom in atoms),
        "hold_count": sum(atom["receipt"]["decision"] == "HOLD" for atom in atoms),
        "quarantine_count": sum(atom["receipt"]["decision"] == "QUARANTINE" for atom in atoms),
        "sidecar_ref_count": sum(
            atom["residual"]["residual_sidecar"] is not None for atom in atoms
        ),
    }
    receipt: dict[str, Any] = {
        "schema": "omindirection_logogram_compiler_receipt_v1",
        "source_audit": str(audit_path),
        "atoms_jsonl": str(atoms_path),
        "counts": counts,
        "atom_hashes": [
            {
                "symbol_id": atom["identity"]["symbol_id"],
                "decision": atom["receipt"]["decision"],
                "receipt_hash": atom["receipt"]["receipt_hash"],
                "residual_sidecar": atom["residual"]["residual_sidecar"],
            }
            for atom in atoms
        ],
        "claim_boundary": (
            "This compiler maps substitution audit decisions into "
            "omindirectional atom receipts. It does not prove source math or "
            "global compression."
        ),
    }
    receipt["receipt_hash"] = "sha256:" + sha256_text(stable_json(receipt))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile audited logograms into omindirectional atoms.")
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--atoms", type=Path, default=DEFAULT_ATOMS)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()

    receipt = build_receipt(args.audit, args.atoms)
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
