#!/usr/bin/env python3
# SHIM ONLY — NO INVARIANT CHECKS, NO COST COMPUTATION, NO BRANCHING DECISIONS
"""Rainbow Raccoon Compiler integration shim.

This is a data-passing shim only. Manifold projection, Euclidean distance
computation, nearest-lawful-shape classification, and type-witness decisions
have all been moved behind the Lean receipt boundary. This file performs only:
- JSON serialization / deserialization
- File I/O (read, write, digest)
- Orchestration (spawn/collect receipts)

Manifold projection    → Lean: Semantics/RRCManifold.lean
Nearest lawful shape   → Lean: Semantics/RRCClassification.lean
Type witness (HOLD/CANDIDATE) → Lean: Semantics/RRCTypeWitness.lean

# TODO: Replace with Lean receipt when Q16_16 build is stable
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "rainbow_raccoon_compiler_receipt.json"
CURRICULUM = SHIM / "rainbow_raccoon_compiler_curriculum.jsonl"


SOURCE_ARTIFACTS = [
    "docs/compression_signal_shaping_synthesis.md",
    "4-Infrastructure/shim/compression_signal_shaping_synthesis_receipt.json",
    "4-Infrastructure/shim/projectable_geometry_topology_model_receipt.json",
    "4-Infrastructure/shim/holographic_fractional_recursive_equation_fold_receipt.json",
    "4-Infrastructure/shim/connectome_protective_cognitive_load_reweighting_receipt.json",
    "4-Infrastructure/shim/cad_force_probe_experiment_matrix_receipt.json",
    "docs/research/GCCL_THEORY_INTRO.md",
    "0-Core-Formalism/lean/Semantics/Semantics/GeometricCompressionWorkspace.lean",
]


@dataclass(frozen=True)
class RRCObject:
    object_id: str
    label: str
    kind: str
    payload: str
    source_path: str | None = None


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


def text_payload(path: str) -> str:
    p = REPO / path
    if not p.exists():
        return ""
    data = p.read_text(encoding="utf-8", errors="replace")
    return data[:12000]


def build_objects() -> list[RRCObject]:
    return [
        RRCObject(
            object_id="rrc_obj_signal_route_compiler",
            label="Compression Signal Shaping Synthesis",
            kind="compression_route_prior",
            source_path="docs/compression_signal_shaping_synthesis.md",
            payload=text_payload("docs/compression_signal_shaping_synthesis.md"),
        ),
        RRCObject(
            object_id="rrc_obj_projectable_geometry",
            label="Projectable Geometry Topology Receipt",
            kind="geometry_topology_receipt",
            source_path="4-Infrastructure/shim/projectable_geometry_topology_model_receipt.json",
            payload=text_payload("4-Infrastructure/shim/projectable_geometry_topology_model_receipt.json"),
        ),
        RRCObject(
            object_id="rrc_obj_cognitive_load",
            label="Connectome Protective Cognitive Load Receipt",
            kind="cognitive_field_receipt",
            source_path="4-Infrastructure/shim/connectome_protective_cognitive_load_reweighting_receipt.json",
            payload=text_payload("4-Infrastructure/shim/connectome_protective_cognitive_load_reweighting_receipt.json"),
        ),
        RRCObject(
            object_id="rrc_obj_cad_force_probe",
            label="CAD Force Probe Experiment Matrix Receipt",
            kind="cad_force_receipt",
            source_path="4-Infrastructure/shim/cad_force_probe_experiment_matrix_receipt.json",
            payload=text_payload("4-Infrastructure/shim/cad_force_probe_experiment_matrix_receipt.json"),
        ),
        RRCObject(
            object_id="rrc_obj_underspecified",
            label="Underspecified raw object negative control",
            kind="negative_control",
            payload="raw object with no declared projection, witness, decoder, residual, or scale band",
        ),
    ]


# TODO: Replace with Lean receipt when Q16_16 build is stable
# Lean modules:
#   Semantics/RRCManifold.lean      → project_to_manifold
#   Semantics/RRCClassification.lean → nearest_lawful_shape
#   Semantics/RRCTypeWitness.lean    → type_witness (HOLD vs CANDIDATE)


def compile_object(obj: RRCObject) -> dict[str, Any]:
    """
    Data-passing shim. Manifold projection, lawful-shape classification,
    and type-witness determination are deferred to Lean.
    """
    return {
        "object": {
            "object_id": obj.object_id,
            "label": obj.label,
            "kind": obj.kind,
            "source_path": obj.source_path,
            "payload_sha256": sha256_text(obj.payload),
            "payload_bytes_sampled": len(obj.payload.encode("utf-8")),
        },
        "_status": "SHIM_PASSTHROUGH",
        "_note": (
            "TODO: Replace with Lean receipt when Q16_16 build is stable. "
            "Manifold projection → Semantics/RRCManifold.lean, "
            "lawful shape → Semantics/RRCClassification.lean, "
            "type witness → Semantics/RRCTypeWitness.lean"
        ),
    }


def build_receipt() -> dict[str, Any]:
    sources = [file_digest(REPO / rel) for rel in SOURCE_ARTIFACTS if (REPO / rel).exists()]
    objects = build_objects()
    compiled_objects = [compile_object(obj) for obj in objects]
    receipt: dict[str, Any] = {
        "schema": "rainbow_raccoon_compiler_integration_v1",
        "claim_state": "shim_passthrough_not_proof",
        "source_artifacts": sources,
        "compiler_name": "Rainbow Raccoon Compiler",
        "compiler_abbrev": "RRC",
        "primary_read": (
            "RRC type-checking is deferred to Lean. This shim emits "
            "hash-stable receipts with TODO markers for each Lean module."
        ),
        "pipeline": [
            {"step": "object", "meaning": "raw object read from source files"},
            {"step": "manifold_projection", "meaning": "TODO: Lean RRCManifold.lean"},
            {"step": "nearest_lawful_shape", "meaning": "TODO: Lean RRCClassification.lean"},
            {"step": "type_witness", "meaning": "TODO: Lean RRCTypeWitness.lean"},
            {"step": "field_equation", "meaning": "TODO: Lean field-equation module"},
            {"step": "invariant_receipt", "meaning": "hash-stable receipt for replay"},
        ],
        "compiled_objects": compiled_objects,
        "promotion_rules": [
            "No CANDIDATE or HOLD determination is made by this shim.",
            "All classification and witness decisions deferred to Lean.",
        ],
        "next_integration_steps": [
            "Write Semantics/RRCManifold.lean with 16-axis coordinate computation.",
            "Write Semantics/RRCClassification.lean with lawful-shape prototypes.",
            "Write Semantics/RRCTypeWitness.lean with HOLD/CANDIDATE gate.",
        ],
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = []
    for compiled in receipt["compiled_objects"]:
        rows.append(
            {
                "prompt": (
                    "Classify this object with the Rainbow Raccoon Compiler pipeline: "
                    f"{compiled['object']['label']}"
                ),
                "completion": {
                    "_status": "SHIM_PASSTHROUGH",
                    "_note": "TODO: Lean receipt (RRCManifold + RRCClassification + RRCTypeWitness)",
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
                "compiled_object_count": len(receipt["compiled_objects"]),
                "_status": "SHIM_PASSTHROUGH",
                "_note": "TODO: Replace with Lean receipt when Q16_16 build is stable",
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
