#!/usr/bin/env python3
"""Receipt-backed Gaussian splat manifold projection probe.

Gaussian splatting is useful for this stack as a visible-chart representation:
each splat is a local projected patch with anisotropic uncertainty, opacity,
payload, residual, and receipt pointer. The splat field is not the whole
manifold; it is an observer-bound shadow atlas over a richer object.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "gaussian_splat_manifold_projection"
REGISTRY = OUT_DIR / "gaussian_splat_manifold_projection_registry.json"
RECEIPT = OUT_DIR / "gaussian_splat_manifold_projection_receipt.json"
SUMMARY = OUT_DIR / "gaussian_splat_manifold_projection.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Gaussian Splat Manifold Projection.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "observer_chart_projection_guardrail" / "observer_chart_projection_guardrail_receipt.json",
    REPO / "shared-data" / "data" / "kerr_like_load_witness_geometry" / "kerr_like_load_witness_geometry_receipt.json",
    REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation" / "hutter_torsion_clock_adaptation_receipt.json",
    REPO / "shared-data" / "data" / "mmff_rigid_body_geometry" / "mmff_rigid_body_geometry_receipt.json",
    REPO / "6-Documentation" / "docs" / "specs" / "PROJECTABLE_GEOMETRY_COMPRESSOR_SPEC.md",
    REPO / "6-Documentation" / "docs" / "specs" / "OMINDIRECTION_LOGOGRAM_DESIGN_AND_COMPILER.md",
]

CITATIONS = [
    {
        "id": "kerbl_3d_gaussian_splatting",
        "title": "3D Gaussian Splatting for Real-Time Radiance Field Rendering",
        "url": "https://arxiv.org/abs/2308.04079",
        "role": "external_rendering_anchor",
        "status": "external_reference",
    },
    {
        "id": "huang_2d_gaussian_splatting",
        "title": "2D Gaussian Splatting for Geometrically Accurate Radiance Fields",
        "url": "https://arxiv.org/abs/2403.17888",
        "role": "external_surface_geometry_anchor",
        "status": "external_reference",
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


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def source_ref(path: Path) -> dict[str, Any]:
    return {"path": rel(path), "exists": path.exists(), "sha256": file_hash(path)}


def splat_route(
    *,
    route_id: str,
    observer_chart: str,
    source_manifold: str,
    splat_kind: str,
    payload: str,
    residual_declared: bool,
    receipt_pointer: bool,
    observer_scope_declared: bool,
    global_truth_claim: bool,
    unsafe_expansion: bool = False,
) -> dict[str, Any]:
    admissible = (
        residual_declared
        and receipt_pointer
        and observer_scope_declared
        and not global_truth_claim
        and not unsafe_expansion
    )
    if unsafe_expansion:
        decision = "QUARANTINE_UNSAFE_SPLAT_EXPANSION"
    elif global_truth_claim:
        decision = "HOLD_SPLAT_GLOBALIZED"
    elif not residual_declared or not receipt_pointer:
        decision = "HOLD_SPLAT_RESIDUAL_OR_RECEIPT_MISSING"
    elif admissible:
        decision = "ADMIT_SPLAT_OBSERVER_CHART"
    else:
        decision = "HOLD_SPLAT_SCOPE_MISSING"
    item = {
        "route_id": route_id,
        "observer_chart": observer_chart,
        "source_manifold": source_manifold,
        "splat_kind": splat_kind,
        "payload": payload,
        "local_atom": {
            "mu": "projected_center",
            "sigma": "anisotropic_covariance_or_surface_disk",
            "alpha": "opacity_or_witness_confidence",
            "c": "color_material_semantic_payload",
            "R": "residual_or_receipt_pointer",
        },
        "residual_declared": residual_declared,
        "receipt_pointer": receipt_pointer,
        "observer_scope_declared": observer_scope_declared,
        "global_truth_claim": global_truth_claim,
        "unsafe_expansion": unsafe_expansion,
        "admissible": admissible,
        "decision": decision,
    }
    item["route_hash"] = hash_obj({k: v for k, v in item.items() if k != "route_hash"})
    return item


def build_registry() -> dict[str, Any]:
    routes = [
        splat_route(
            route_id="organic_periodic_table_relevance_splats",
            observer_chart="organic chemist chart",
            source_manifold="periodic table chemical manifold",
            splat_kind="semantic_2d_splat",
            payload="carbon-centered relevance field plus declared residual for non-organic chemistry",
            residual_declared=True,
            receipt_pointer=True,
            observer_scope_declared=True,
            global_truth_claim=False,
        ),
        splat_route(
            route_id="kerr_like_load_state_splats",
            observer_chart="mechanical witness chart",
            source_manifold="torsion-coupled load admissibility manifold",
            splat_kind="state_atlas_splat",
            payload="safe chart, ergoregion, horizon, and failure-core patches",
            residual_declared=True,
            receipt_pointer=True,
            observer_scope_declared=True,
            global_truth_claim=False,
        ),
        splat_route(
            route_id="hutter_codec_torsion_splats",
            observer_chart="compression accounting chart",
            source_manifold="corpus/code/protocol receipt-state manifold",
            splat_kind="byte_debt_splat",
            payload="replay, provenance, packet, dictionary, baseline, receipt, and route-coupling fields",
            residual_declared=True,
            receipt_pointer=True,
            observer_scope_declared=True,
            global_truth_claim=False,
        ),
        splat_route(
            route_id="mmff_material_shadow_splats",
            observer_chart="molecular/material geometry chart",
            source_manifold="16D chemistry/body state projected to 3D coordinate shadow",
            splat_kind="geometry_shadow_splat",
            payload="local coordinate/material/strain patch with MMFF adapter surfaces in HOLD",
            residual_declared=True,
            receipt_pointer=True,
            observer_scope_declared=True,
            global_truth_claim=False,
        ),
        splat_route(
            route_id="photoreal_splat_claimed_as_truth",
            observer_chart="visual rendering chart",
            source_manifold="unobserved physical scene and material state",
            splat_kind="radiance_splat",
            payload="photoreal projection without residual or observer boundary",
            residual_declared=False,
            receipt_pointer=False,
            observer_scope_declared=False,
            global_truth_claim=True,
        ),
    ]
    return {
        "schema": "gaussian_splat_manifold_projection_registry_v1",
        "citations": CITATIONS,
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Gaussian splat manifold projection only. Splats are local visible-chart "
            "atoms over a richer manifold. They may render or summarize an observer "
            "projection, but they do not prove global truth without residuals, receipts, "
            "and observer scope."
        ),
        "canonical_statement": (
            "A splat field is a shadow atlas: useful, compact, and renderable, but "
            "admissible only when each patch declares its observer scope, residual, "
            "and receipt pointer."
        ),
        "projection_equation": "pi_observer(Omega) ~= sum_i G_i(mu_i,Sigma_i,alpha_i,c_i,R_i) + residual",
        "admissibility_equation": (
            "A_splat=1[observer_scope_declared] * 1[residual_declared] * "
            "1[receipt_pointer] * 1[not global_truth_claim] * 1[not unsafe_expansion]"
        ),
        "encoding_rule": {
            "splat_atom": "mu + Sigma + alpha + payload + residual/receipt pointer",
            "projection_role": "visible chart patch, not invariant manifold",
            "hutter_role": "render byte-debt/provenance regions as diagnostic splats; canonical byte gates still decide",
            "safety_role": "splat can summarize risk regions but cannot certify safety alone",
        },
        "routes": routes,
        "aggregates": {
            "route_count": len(routes),
            "admit_splat_chart_count": sum(1 for item in routes if item["decision"] == "ADMIT_SPLAT_OBSERVER_CHART"),
            "hold_count": sum(1 for item in routes if item["decision"].startswith("HOLD")),
            "quarantine_count": sum(1 for item in routes if item["decision"].startswith("QUARANTINE")),
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "gaussian_splat_manifold_projection_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "citations": registry["citations"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_GAUSSIAN_SPLAT_OBSERVER_CHART_PRIMITIVE",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Gaussian Splat Manifold Projection",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Equations",
        "",
        f"- Projection: `{registry['projection_equation']}`",
        f"- Admit: `{registry['admissibility_equation']}`",
        "",
        "## Encoding Rules",
        "",
    ]
    for key, value in registry["encoding_rule"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Routes",
            "",
            "| Route | Splat kind | Observer chart | Decision |",
            "|---|---|---|---|",
        ]
    )
    for item in registry["routes"]:
        lines.append(f"| `{item['route_id']}` | `{item['splat_kind']}` | {item['observer_chart']} | `{item['decision']}` |")
    lines.extend(["", "## Citations", ""])
    for citation in registry["citations"]:
        lines.append(f"- `{citation['id']}`: {citation['title']} ({citation['url']}); role: `{citation['role']}`")
    lines.extend(["", "## Source Refs", ""])
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Encoding GaussianSplat Projection Receipt
title: Gaussian Splat Manifold Projection
type: text/vnd.tiddlywiki

! Gaussian Splat Manifold Projection

Durable runner:

```
4-Infrastructure/shim/gaussian_splat_manifold_projection_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

!! Doctrine

A splat field is a shadow atlas. It is useful, compact, and renderable, but it is not the whole manifold.

```
G_i = (mu_i, Sigma_i, alpha_i, c_i, R_i)
pi_observer(Omega) ~= sum_i G_i + residual
```

Each splat must carry observer scope, residual declaration, and receipt pointer before it can be used as an admissible chart atom.

!! Links

* [[Observer Chart Projection Guardrail]]
* [[Kerr-Like Load Witness Geometry]]
* [[Hutter Torsion Clock Adaptation]]
* [[MMFF Rigid Body Geometry]]
"""
    TIDDLER.write_text(text, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    write_tiddler(receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "tiddler": rel(TIDDLER),
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
