#!/usr/bin/env python3
"""Receipt-backed torsion-interval Gaussian splat witness probe.

This extends Gaussian splat manifold projections by indexing splat fields by
accumulated torsion instead of wall-clock time. Each interval is a local witness
frame, and each frame has its own Merkle root. The global root commits the
torsion-state history without claiming full material omniscience.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "torsion_interval_gaussian_splat_witness"
REGISTRY = OUT_DIR / "torsion_interval_gaussian_splat_witness_registry.json"
RECEIPT = OUT_DIR / "torsion_interval_gaussian_splat_witness_receipt.json"
SUMMARY = OUT_DIR / "torsion_interval_gaussian_splat_witness.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Torsion Interval Gaussian Splat Witness.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "gaussian_splat_manifold_projection" / "gaussian_splat_manifold_projection_receipt.json",
    REPO / "shared-data" / "data" / "kerr_like_load_witness_geometry" / "kerr_like_load_witness_geometry_receipt.json",
    REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation" / "hutter_torsion_clock_adaptation_receipt.json",
    REPO / "shared-data" / "data" / "mmff_rigid_body_geometry" / "mmff_rigid_body_geometry_receipt.json",
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

DELTA_TORSION = 10
DRIFT_ERGOREGION_THRESHOLD = 35
DRIFT_HORIZON_THRESHOLD = 70


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def merkle_root(leaves: list[str]) -> str:
    if not leaves:
        return sha256_bytes(b"")
    level = leaves[:]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [sha256_bytes((level[index] + level[index + 1]).encode("ascii")) for index in range(0, len(level), 2)]
    return level[0]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def source_ref(path: Path) -> dict[str, Any]:
    return {"path": rel(path), "exists": path.exists(), "sha256": file_hash(path)}


def splat(
    *,
    splat_id: str,
    position: tuple[int, int, int],
    covariance_diag: tuple[int, int, int],
    orientation_deg: int,
    confidence_milli: int,
    residual_risk_milli: int,
    load_vector: tuple[int, int, int],
) -> dict[str, Any]:
    item = {
        "splat_id": splat_id,
        "mu_pm": position,
        "sigma_diag_pm2": covariance_diag,
        "orientation_deg": orientation_deg,
        "confidence_milli": confidence_milli,
        "residual_risk_milli": residual_risk_milli,
        "load_vector_milli": load_vector,
    }
    item["splat_hash"] = hash_obj(item)
    return item


def frame(*, interval_index: int, torsion_start: int, torsion_end: int, splats: list[dict[str, Any]]) -> dict[str, Any]:
    leaf_hashes = [item["splat_hash"] for item in splats]
    risk = sum(item["residual_risk_milli"] for item in splats)
    covariance_bloom = sum(max(item["sigma_diag_pm2"]) - min(item["sigma_diag_pm2"]) for item in splats)
    confidence_loss = sum(1000 - item["confidence_milli"] for item in splats)
    drift_score = risk // 100 + covariance_bloom // 500 + confidence_loss // 100
    if drift_score >= DRIFT_HORIZON_THRESHOLD:
        decision = "HOLD_TORSION_SPLAT_HORIZON"
    elif drift_score >= DRIFT_ERGOREGION_THRESHOLD:
        decision = "HOLD_TORSION_SPLAT_ERGOREGION"
    else:
        decision = "ADMIT_TORSION_SPLAT_FRAME"
    item = {
        "interval_index": interval_index,
        "torsion_start": torsion_start,
        "torsion_end": torsion_end,
        "delta_torsion": torsion_end - torsion_start,
        "splat_count": len(splats),
        "splats": splats,
        "frame_merkle_root": merkle_root(leaf_hashes),
        "risk_sum_milli": risk,
        "covariance_bloom": covariance_bloom,
        "confidence_loss_milli": confidence_loss,
        "drift_score": drift_score,
        "decision": decision,
    }
    item["frame_hash"] = hash_obj({k: v for k, v in item.items() if k != "frame_hash"})
    return item


def build_registry() -> dict[str, Any]:
    frames = [
        frame(
            interval_index=0,
            torsion_start=0,
            torsion_end=10,
            splats=[
                splat(splat_id="thread_core", position=(0, 0, 0), covariance_diag=(100, 100, 120), orientation_deg=0, confidence_milli=980, residual_risk_milli=40, load_vector=(0, 0, -900)),
                splat(splat_id="footing_edge", position=(0, -400, -900), covariance_diag=(120, 140, 120), orientation_deg=3, confidence_milli=960, residual_risk_milli=60, load_vector=(20, 0, -700)),
            ],
        ),
        frame(
            interval_index=1,
            torsion_start=10,
            torsion_end=20,
            splats=[
                splat(splat_id="thread_core", position=(0, 0, 0), covariance_diag=(120, 150, 260), orientation_deg=12, confidence_milli=910, residual_risk_milli=220, load_vector=(80, 0, -890)),
                splat(splat_id="footing_edge", position=(0, -400, -900), covariance_diag=(150, 230, 300), orientation_deg=17, confidence_milli=880, residual_risk_milli=260, load_vector=(120, 0, -690)),
            ],
        ),
        frame(
            interval_index=2,
            torsion_start=20,
            torsion_end=30,
            splats=[
                splat(splat_id="thread_core", position=(0, 0, 0), covariance_diag=(260, 480, 820), orientation_deg=32, confidence_milli=720, residual_risk_milli=700, load_vector=(250, 0, -860)),
                splat(splat_id="footing_edge", position=(0, -400, -900), covariance_diag=(300, 620, 950), orientation_deg=38, confidence_milli=690, residual_risk_milli=760, load_vector=(310, 0, -640)),
                splat(splat_id="side_shear_bloom", position=(220, -160, -420), covariance_diag=(180, 560, 1050), orientation_deg=44, confidence_milli=640, residual_risk_milli=840, load_vector=(420, 20, -510)),
            ],
        ),
    ]
    return {
        "schema": "torsion_interval_gaussian_splat_witness_registry_v1",
        "citations": CITATIONS,
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Torsion-interval Gaussian splat witness only. Frames are sampled by "
            "accumulated torsion, not wall-clock time. Splat fields are visible "
            "witness shadows and do not certify material truth without external "
            "mechanical validation."
        ),
        "canonical_statement": (
            "Gaussian splats are local witness particles; torsion intervals are causal "
            "frames; Merkle roots make each frame accountable."
        ),
        "torsion_interval_rule": {
            "delta_torsion": DELTA_TORSION,
            "effective_torsion": "T_eff = integral(a||tau|| + b||load cross normal|| + c||delta_q|| + d*risk) ds",
            "frame": "G_k = {G_i(T_k)}",
            "frame_root": "R_k = MerkleRoot(H(G_1(T_k)), ..., H(G_n(T_k)))",
            "global_root": "R_global = MerkleRoot(R_0, ..., R_K)",
            "wall_clock_role": "metadata_shadow_only",
        },
        "admissibility_equation": (
            "A_frame=1[drift_score < ergoregion_threshold] * 1[frame_merkle_root] * "
            "1[residual_declared] * 1[observer_scope_declared]"
        ),
        "frames": frames,
        "global_merkle_root": merkle_root([item["frame_merkle_root"] for item in frames]),
        "aggregates": {
            "frame_count": len(frames),
            "splat_count": sum(item["splat_count"] for item in frames),
            "admit_frame_count": sum(1 for item in frames if item["decision"] == "ADMIT_TORSION_SPLAT_FRAME"),
            "ergoregion_frame_count": sum(1 for item in frames if item["decision"] == "HOLD_TORSION_SPLAT_ERGOREGION"),
            "horizon_frame_count": sum(1 for item in frames if item["decision"] == "HOLD_TORSION_SPLAT_HORIZON"),
            "drift_ergoregion_threshold": DRIFT_ERGOREGION_THRESHOLD,
            "drift_horizon_threshold": DRIFT_HORIZON_THRESHOLD,
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "torsion_interval_gaussian_splat_witness_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "global_merkle_root": registry["global_merkle_root"],
        "citations": registry["citations"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_TORSION_INTERVAL_SPLAT_WITNESS_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Torsion-Interval Gaussian Splat Witness",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Global Merkle root: `{registry['global_merkle_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Torsion Rule",
        "",
    ]
    for key, value in registry["torsion_interval_rule"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Frames",
            "",
            "| Interval | Torsion | Splats | Drift | Decision | Frame root |",
            "|---:|---|---:|---:|---|---|",
        ]
    )
    for item in registry["frames"]:
        lines.append(
            f"| {item['interval_index']} | `{item['torsion_start']}..{item['torsion_end']}` | "
            f"{item['splat_count']} | {item['drift_score']} | `{item['decision']}` | `{item['frame_merkle_root']}` |"
        )
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
tags: ResearchStack Encoding GaussianSplat TorsionClock Receipt
title: Torsion Interval Gaussian Splat Witness
type: text/vnd.tiddlywiki

! Torsion Interval Gaussian Splat Witness

Durable runner:

```
4-Infrastructure/shim/torsion_interval_gaussian_splat_witness_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

Global Merkle root:

```
{receipt['global_merkle_root']}
```

!! Doctrine

Use Gaussian splats as local witness particles sampled at torsion intervals instead of clock intervals.

```
G_k = {{G_i(T_k)}}
R_k = MerkleRoot(H(G_1(T_k)), ..., H(G_n(T_k)))
R_global = MerkleRoot(R_0, ..., R_K)
```

The result is a renderable audit surface over load, twist, residual risk, and material-shadow drift.

!! Links

* [[Gaussian Splat Manifold Projection]]
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
                "global_merkle_root": registry["global_merkle_root"],
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
