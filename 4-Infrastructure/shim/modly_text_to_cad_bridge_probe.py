#!/usr/bin/env python3
"""Modly to text-to-CAD bridge probe.

This probe records a conservative bridge between Modly's local image-to-mesh
pipeline, the repo-local text-to-CAD harness, and the Rainbow Raccoon compiler
idea. It does not vendor Modly, install model weights, or treat generated meshes
as parametric CAD source. The bridge keeps mesh output as a model-guess prior,
then routes durable source of truth through text-to-CAD generator files while
Rainbow Raccoon carries residuals, closure gates, and refinement receipts.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "modly_text_to_cad_bridge"
PAYLOAD_JSON = OUT_DIR / "modly_text_to_cad_bridge.json"
SUMMARY = OUT_DIR / "modly_text_to_cad_bridge.md"
RECEIPT = OUT_DIR / "modly_text_to_cad_bridge_receipt.json"
TIDDLER = (
    REPO
    / "6-Documentation"
    / "tiddlywiki-local"
    / "wiki"
    / "tiddlers"
    / "Modly Text To CAD Bridge.tid"
)

REMOTE_SOURCES = [
    {
        "name": "modly_readme",
        "url": "https://raw.githubusercontent.com/lightningpixel/modly/main/README.md",
    },
    {
        "name": "modly_package",
        "url": "https://raw.githubusercontent.com/lightningpixel/modly/main/package.json",
    },
    {
        "name": "modly_generation_router",
        "url": "https://raw.githubusercontent.com/lightningpixel/modly/main/api/routers/generation.py",
    },
    {
        "name": "modly_export_router",
        "url": "https://raw.githubusercontent.com/lightningpixel/modly/main/api/routers/export.py",
    },
    {
        "name": "modly_generator_contract",
        "url": "https://raw.githubusercontent.com/lightningpixel/modly/main/api/services/generators/base.py",
    },
]

LOCAL_SOURCES = [
    REPO / "5-Applications" / "text-to-cad" / "README.md",
    REPO / "5-Applications" / "text-to-cad" / "AGENTS.md",
    REPO / "5-Applications" / "text-to-cad" / "skills" / "cad" / "SKILL.md",
    REPO / "5-Applications" / "text-to-cad" / "skills" / "cad" / "references" / "generator-contract.md",
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


def fetch_remote(source: dict[str, str]) -> dict[str, Any]:
    try:
        request = urllib.request.Request(
            source["url"],
            headers={"User-Agent": "ResearchStack-modly-text-to-cad-bridge/1.0"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
        return {
            **source,
            "fetched": True,
            "fetch_error": None,
            "bytes": len(data),
            "sha256": sha256_bytes(data),
        }
    except Exception as exc:  # pragma: no cover - receipt captures network failures.
        return {
            **source,
            "fetched": False,
            "fetch_error": f"{type(exc).__name__}: {exc}",
            "bytes": 0,
            "sha256": None,
        }


def local_ref(path: Path) -> dict[str, Any]:
    exists = path.exists()
    data = path.read_bytes() if exists else b""
    return {
        "path": rel(path),
        "exists": exists,
        "bytes": len(data),
        "sha256": sha256_bytes(data) if exists else None,
    }


def build_payload() -> dict[str, Any]:
    remote_refs = [fetch_remote(source) for source in REMOTE_SOURCES]
    local_refs = [local_ref(path) for path in LOCAL_SOURCES]
    payload = {
        "schema": "modly_text_to_cad_bridge_v1",
        "claim_boundary": (
            "Bridge hypothesis only. Modly mesh output is treated as a local prior "
            "or evidence artifact, not as editable CAD source. Text-to-CAD generator "
            "files remain the durable source of truth."
        ),
        "remote_refs": remote_refs,
        "local_refs": local_refs,
        "bridge_pipeline": [
            "image_or_photo_input",
            "modly_local_image_to_mesh_generation",
            "rainbow_raccoon_guess_capture",
            "modly_export_glb_stl_obj_or_ply",
            "mesh_cleanup_and_feature_measurement",
            "text_to_cad_parametric_generator_synthesis",
            "rainbow_raccoon_residual_compile",
            "explicit_step_stl_dxf_glb_urdf_regeneration",
            "render_compare_and_residual_update",
            "cad_explorer_review_with_cad_refs",
        ],
        "candidate_equations": [
            {
                "equation_id": "mesh_prior_to_parametric_cad",
                "equation": "CAD_source = synthesize(generator_contract, mesh_features, design_intent, constraints)",
                "decision": "HOLD_MESH_TO_PARAMETRIC_CAD",
                "use_as": "turn Modly mesh evidence into editable text-to-CAD source",
            },
            {
                "equation_id": "modly_mesh_prior_weight",
                "equation": "W_mesh = q_mesh * q_silhouette * q_scale * q_topology - cleanup_cost",
                "decision": "HOLD_MESH_PRIOR_WEIGHT",
                "use_as": "decide how strongly a generated mesh should influence CAD synthesis",
            },
            {
                "equation_id": "cad_source_promotion_gate",
                "equation": "promote iff source_regenerates && mesh_alignment_ok && step_valid && receipt_exists",
                "decision": "HOLD_CAD_PROMOTION_GATE",
                "use_as": "keep source-controlled CAD as the promotion boundary",
            },
            {
                "equation_id": "rainbow_raccoon_guess_residual_loop",
                "equation": "R_guess = features(Modly_mesh) - features(render(TextToCAD_source))",
                "decision": "HOLD_GUESS_RESIDUAL_LOOP",
                "use_as": "show what the model guessed at and feed bounded residuals back into refinement",
            },
            {
                "equation_id": "self_refining_cad_compiler_step",
                "equation": "CAD_{t+1}=compile(CAD_t, R_guess_t, constraints, closure_receipt_t)",
                "decision": "HOLD_SELF_REFINING_CAD_COMPILER",
                "use_as": "Rainbow Raccoon compiler loop from mesh guess to improved parametric CAD",
            },
            {
                "equation_id": "mesh_guess_closure_gate",
                "equation": "G_guess=1[source_regenerates]*1[render_hash_recomputes]*1[residual_bounded]*1[rollback_exists]",
                "decision": "HOLD_GUESS_CLOSURE_GATE",
                "use_as": "prevent the refinement loop from treating an opaque mesh guess as validated geometry",
            },
        ],
        "adapter_shape": {
            "modly_role": "local image-to-mesh prior generator and mesh export surface",
            "text_to_cad_role": "parametric source-of-truth generator, validator, exporter, and viewer/ref surface",
            "rainbow_raccoon_role": "compiler/refinement layer that records model guesses, residuals, closure gates, and rollback receipts",
            "safe_default": "do not vendor Modly or download model weights automatically; import only user-provided mesh artifacts or explicit local Modly outputs",
            "artifact_boundary": "generated mesh can guide silhouette and proportions; generated Python CAD source owns editable geometry",
            "refinement_boundary": "self-refinement is allowed only over local fixtures, explicit constraints, render comparisons, and rollback hashes",
        },
        "decision": "ADMIT_MODLY_TEXT_TO_CAD_BRIDGE_AS_HOLD_PRIOR",
    }
    payload["aggregates"] = {
        "remote_source_count": len(remote_refs),
        "remote_fetched_count": sum(1 for item in remote_refs if item["fetched"]),
        "local_source_count": len(local_refs),
        "local_existing_count": sum(1 for item in local_refs if item["exists"]),
        "candidate_count": len(payload["candidate_equations"]),
    }
    payload["payload_hash"] = hash_obj({k: v for k, v in payload.items() if k != "payload_hash"})
    return payload


def build_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "modly_text_to_cad_bridge_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "payload_hash": payload["payload_hash"],
        "aggregates": payload["aggregates"],
        "remote_hashes": {item["name"]: item["sha256"] for item in payload["remote_refs"]},
        "local_hashes": {item["path"]: item["sha256"] for item in payload["local_refs"]},
        "decision": payload["decision"],
        "claim_boundary": payload["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Modly Text-to-CAD Bridge",
        "",
        f"Decision: `{payload['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        payload["claim_boundary"],
        "",
        "## Bridge Pipeline",
        "",
    ]
    for index, step in enumerate(payload["bridge_pipeline"], start=1):
        lines.append(f"{index}. `{step}`")
    lines.extend(
        [
            "",
            "## Adapter Shape",
            "",
        ]
    )
    for key, value in payload["adapter_shape"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Candidate Equations",
            "",
            "| Candidate | Equation | Decision | Use as |",
            "|---|---|---|---|",
        ]
    )
    for item in payload["candidate_equations"]:
        lines.append(f"| {item['equation_id']} | `{item['equation']}` | {item['decision']} | {item['use_as']} |")
    lines.extend(["", "## Sources", ""])
    for item in payload["remote_refs"]:
        status = "ok" if item["fetched"] else "missing"
        lines.append(f"- `{item['name']}`: {status} - {item['url']}")
    for item in payload["local_refs"]:
        status = "ok" if item["exists"] else "missing"
        lines.append(f"- `{item['path']}`: {status}")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "title: Modly Text To CAD Bridge",
        "tags: TextToCAD Modly CAD MeshPrior HOLD Receipt",
        "type: text/vnd.tiddlywiki",
        "",
        "! Modly Text To CAD Bridge",
        "",
        f"Decision: `{payload['decision']}`",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        "!! Bridge",
        "",
        "Modly is treated as a local image-to-mesh prior generator. Text-to-CAD remains the parametric source-of-truth generator and validation/export surface. Rainbow Raccoon acts as the compiler loop that records what the model guessed, compares it to regenerated CAD, and carries bounded residuals into the next refinement step.",
        "",
        "!! Pipeline",
        "",
    ]
    for step in payload["bridge_pipeline"]:
        lines.append(f"* `{step}`")
    lines.extend(
        [
            "",
            "!! Boundary",
            "",
            payload["claim_boundary"],
            "",
            f"Receipt: `shared-data/data/modly_text_to_cad_bridge/modly_text_to_cad_bridge_receipt.json`",
        ]
    )
    TIDDLER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    receipt = build_receipt(payload)
    PAYLOAD_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    write_summary(payload, receipt)
    write_tiddler(payload, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
