#!/usr/bin/env python3
"""Bridge math logograms into Rainbow Raccoon Compiler projections.

This consumes the existing math logogram surface receipt and runs each compiled
sample through the RRC manifold/type-witness boundary as a LogogramProjection.
The bridge is deliberately receipt-only: it does not prove the mathematics in a
logogram.  It verifies that the projection surface is declared, bounded, and
auditable enough to be a candidate object for later Lean/proof work.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
LOGOGRAM_RECEIPT = SHIM / "math_logogram_surface_receipt.json"
RRC_RECEIPT = SHIM / "rainbow_raccoon_compiler_receipt.json"
OUT = SHIM / "rrc_logogram_projection_bridge_receipt.json"
CURRICULUM = SHIM / "rrc_logogram_projection_bridge_curriculum.jsonl"


def load_rrc_module() -> Any:
    path = SHIM / "rainbow_raccoon_compiler.py"
    spec = importlib.util.spec_from_file_location("rainbow_raccoon_compiler", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load RRC module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(REPO)),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sample_projection_payload(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": sample["id"],
        "kind": sample["kind"],
        "source_hash": sample["source_hash"],
        "canonical_hash": sample["canonical_hash"],
        "cell_hash": sample["cell_hash"],
        "token_count": sample["token_count"],
        "token_kind_counts": sample["token_kind_counts"],
        "surface_payload_hex": sample["surface_payload_hex"],
        "surface_payload_len": sample["surface_payload_len"],
        "substitution_receipt": sample["substitution_receipt"],
        "compression_metrics": sample["compression_metrics"],
        "semantic_regime": sample["semantic_regime"],
        "projection": {
            "source_space": "latex_or_symbolic_logogram",
            "canonical_space": "deterministic_surface1_cells",
            "payload_space": "bounded_glyph_payload_16_bytes",
            "receipt_space": "substitution_receipt_plus_rrc_witness",
        },
        "decoder_declared": "canonical cells + glyph payload + source residual boundary",
        "scale_band_declared": "surface_payload_len <= 16 bytes; token_count finite; no math proof claim",
    }


def tear_repair_witness(sample: dict[str, Any]) -> dict[str, Any] | None:
    """Create a repair lane for semantic tearing without merging the torn mass."""
    if sample.get("semantic_regime") != "horrible_manifold_tearing":
        return None
    source = str(sample.get("source", ""))
    canonical = str(sample.get("canonical", ""))
    boundary = {
        "regime": sample["semantic_regime"],
        "source_hash": sample["source_hash"],
        "canonical_hash": sample["canonical_hash"],
        "cell_hash": sample["cell_hash"],
        "trigger_terms": [
            term
            for term in ["torsion", "contradiction", "tear", ">", "max"]
            if term in source or term in canonical
        ],
    }
    detached_mass_id = "detached_mass:" + sha256_text(stable_json(boundary))[:16]
    witness = {
        "schema": "rrc.logogram_tear_repair.v1",
        "repair_status": "isolated_not_merged",
        "repair_rule": "quarantine torn binding; preserve boundary and residual; refuse tokenbook merge",
        "contradiction_witness_hash": sha256_text(stable_json(boundary)),
        "tear_boundary_hash": sha256_text(sample["cell_hash"] + ":" + sample["semantic_regime"]),
        "detached_mass_id": detached_mass_id,
        "origin_block": {
            "sample_id": sample["id"],
            "source_hash": sample["source_hash"],
            "canonical_hash": sample["canonical_hash"],
        },
        "residual_lane": {
            "kind": "semantic_boundary_residual",
            "payload_hex": sample["surface_payload_hex"],
            "payload_len": sample["surface_payload_len"],
            "merge_admissible": False,
            "projection_lane": "quarantine_projection",
        },
    }
    witness["repair_receipt_hash"] = sha256_text(stable_json(witness))
    return witness


def compile_sample(rrc: Any, sample: dict[str, Any]) -> dict[str, Any]:
    payload = sample_projection_payload(sample)
    obj = rrc.RRCObject(
        object_id=f"rrc_logogram_{sample['id']}",
        label=f"Logogram projection: {sample['id']}",
        kind="logogram_projection",
        payload=json.dumps(payload, sort_keys=True, ensure_ascii=True),
        source_path="4-Infrastructure/shim/math_logogram_surface_receipt.json",
    )
    compiled = rrc.compile_object(obj)
    repair = tear_repair_witness(sample)
    payload_bound_ok = sample["surface_payload_len"] <= 16
    type_ok = compiled["type_witness"]["status"] == "CANDIDATE"
    merge_safe = sample["semantic_regime"] != "horrible_manifold_tearing"
    repaired_tear = repair is not None
    compiled["logogram_projection"] = {
        "sample_id": sample["id"],
        "semantic_regime": sample["semantic_regime"],
        "canonical_hash": sample["canonical_hash"],
        "cell_hash": sample["cell_hash"],
        "payload_hex": sample["surface_payload_hex"],
        "payload_len": sample["surface_payload_len"],
        "hash16": sample["substitution_receipt"]["hash16"],
        "projection_admissible": type_ok and payload_bound_ok and (merge_safe or repaired_tear),
        "merge_admissible": type_ok and payload_bound_ok and merge_safe,
        "projection_lane": "normal_projection" if merge_safe else "quarantine_projection",
        "tear_repair_witness": repair,
        "hold_reason": None,
    }
    if not compiled["logogram_projection"]["projection_admissible"]:
        reasons = []
        if compiled["type_witness"]["status"] != "CANDIDATE":
            reasons.extend(compiled["type_witness"]["missing_or_weak_axes"])
        if sample["surface_payload_len"] > 16:
            reasons.append("payload_exceeds_16_byte_surface")
        if sample["semantic_regime"] == "horrible_manifold_tearing" and repair is None:
            reasons.append("semantic_regime_horrible_manifold_tearing_without_repair_witness")
        compiled["logogram_projection"]["hold_reason"] = reasons
    compiled["invariant_receipt"]["receipt_hash"] = sha256_text(stable_json(compiled))
    return compiled


def build_receipt() -> dict[str, Any]:
    rrc = load_rrc_module()
    logogram = load_json(LOGOGRAM_RECEIPT)
    base_rrc = load_json(RRC_RECEIPT) if RRC_RECEIPT.exists() else {}
    compiled = [compile_sample(rrc, sample) for sample in logogram.get("samples", [])]
    receipt = {
        "schema": "rrc_logogram_projection_bridge_v1",
        "claim_state": "projection_bridge_not_math_proof",
        "source_artifacts": [
            file_digest(LOGOGRAM_RECEIPT),
            file_digest(SHIM / "math_logogram_surface_builder.py"),
            file_digest(SHIM / "rainbow_raccoon_compiler.py"),
        ]
        + ([file_digest(RRC_RECEIPT)] if RRC_RECEIPT.exists() else []),
        "upstream_rrc_receipt_hash": base_rrc.get("receipt_hash"),
        "primary_read": (
            "Logograms become RRC projection objects by binding canonical cell hashes, "
            "bounded glyph payloads, substitution receipts, and semantic regimes to a "
            "LogogramProjection type witness."
        ),
        "projection_equation": (
            "P_logogram(source) = (canonical_hash, cell_hash, glyph_payload_16, "
            "semantic_regime, substitution_receipt, rrc_type_witness)"
        ),
        "compiled_logograms": compiled,
        "counts": {
            "sample_count": len(compiled),
            "candidate_count": sum(1 for item in compiled if item["type_witness"]["status"] == "CANDIDATE"),
            "hold_count": sum(1 for item in compiled if item["type_witness"]["status"] == "HOLD"),
            "projection_admissible_count": sum(
                1 for item in compiled if item["logogram_projection"]["projection_admissible"]
            ),
            "merge_admissible_count": sum(
                1 for item in compiled if item["logogram_projection"]["merge_admissible"]
            ),
            "repaired_tear_count": sum(
                1
                for item in compiled
                if item["logogram_projection"].get("tear_repair_witness") is not None
            ),
        },
        "failure_rules": [
            "A logogram projection is not a proof of the source equation.",
            "A payload over 16 bytes is HOLD for this Surface-1 bridge.",
            "A horrible_manifold_tearing regime may enter quarantine projection only with a residual/contradiction witness.",
            "A repaired tear is never merge-admissible without a separate proof receipt.",
            "A missing RRC witness or weak projection axis is HOLD.",
        ],
        "next_steps": [
            "Add a declared residual lane for logograms that need more than 16 payload bytes.",
            "Map admissible logograms into the E1/E2 route classifier as symbolic-feature tokens.",
            "Create a Lean RRCShape.LogogramProjection witness gate.",
            "Use semantic regime HOLDs to prevent unsafe tokenbook merges.",
        ],
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = []
    for item in receipt["compiled_logograms"]:
        rows.append(
            {
                "prompt": {
                    "task": "rrc_logogram_projection",
                    "sample_id": item["logogram_projection"]["sample_id"],
                    "canonical_hash": item["logogram_projection"]["canonical_hash"],
                    "semantic_regime": item["logogram_projection"]["semantic_regime"],
                },
                "completion": {
                    "shape": item["nearest_lawful_shape"]["shape"],
                    "status": item["type_witness"]["status"],
                    "projection_admissible": item["logogram_projection"]["projection_admissible"],
                    "receipt_hash": item["invariant_receipt"]["receipt_hash"],
                },
            }
        )
    CURRICULUM.write_text(
        "\n".join(stable_json(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    write_curriculum(receipt)
    print(
        json.dumps(
            {
                "receipt": str(OUT.relative_to(REPO)),
                "curriculum": str(CURRICULUM.relative_to(REPO)),
                "receipt_hash": receipt["receipt_hash"],
                **receipt["counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
