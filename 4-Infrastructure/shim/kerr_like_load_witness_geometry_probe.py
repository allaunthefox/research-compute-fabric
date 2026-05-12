#!/usr/bin/env python3
"""Receipt-backed Kerr-like load-witness geometry probe.

This probe captures the refined invariant-geometry load concept:

* mechanical equilibrium remains a real-valued physical gate;
* Merkle/O-AMMR commitments bind layer/process/material evidence;
* an Equihash-like witness is an admissibility predicate, not a force term;
* Kerr spacetime is used only as a typed state-atlas analogy for torsion-coupled
  load paths, warning regions, and irreversible failure horizons.

It is not a structural safety certificate and not a literal general-relativity
model of a mechanical part.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "kerr_like_load_witness_geometry"
REGISTRY = OUT_DIR / "kerr_like_load_witness_geometry_registry.json"
RECEIPT = OUT_DIR / "kerr_like_load_witness_geometry_receipt.json"
SUMMARY = OUT_DIR / "kerr_like_load_witness_geometry.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Kerr-Like Load Witness Geometry.tid"

PRACTICAL_TREE_FIDDY_DEPTH = 350
EPSILON_MECH = 1.0e-8
ERGOREGION_TORSION_RATIO = 0.18
FAILURE_HORIZON_TORSION_RATIO = 0.36
TORSION_CRITICAL = 36.0

CITATIONS = [
    {
        "id": "princeton_invariant_dual_mechanics",
        "title": "Invariant dual mechanics of tensegrity and origami",
        "url": "https://collaborate.princeton.edu/en/publications/invariant-dual-mechanics-of-tensegrity-and-origami/",
        "role": "external_mechanics_anchor",
        "status": "external_reference",
    },
    {
        "id": "pnas_invariant_dual_mechanics",
        "title": "Invariant dual mechanics of tensegrity and origami",
        "doi": "10.1073/pnas.2519138123",
        "role": "external_mechanics_anchor",
        "status": "external_reference",
    },
    {
        "id": "equihash_iacr",
        "title": "Equihash: Asymmetric Proof-of-Work Based on the Generalized Birthday Problem",
        "url": "https://eprint.iacr.org/2015/946",
        "role": "memory_hard_witness_anchor",
        "status": "external_reference",
    },
    {
        "id": "user_supplied_kerr_diagram",
        "title": "Extended Kerr spacetime null-geodesic diagram prompt",
        "role": "state_atlas_prompt",
        "status": "user_supplied_image_prompt",
    },
    {
        "id": "merkle_tensegrity_load_equation_harness",
        "title": "Merkle tensegrity load equation harness",
        "path": "4-Infrastructure/shim/merkle_tensegrity_load_equation_generator.py",
        "role": "local_predecessor",
        "status": "local_reference",
    },
    {
        "id": "tree_fiddy_semantics",
        "title": "Tree Fiddy semantics",
        "path": "6-Documentation/docs/semantics/TREE_FIDDY.md",
        "role": "recursion_bound",
        "status": "local_reference",
    },
    {
        "id": "geomtree_semijack_witness",
        "title": "GeomTREE Semi-Jack Physical Witness",
        "path": "6-Documentation/tiddlywiki-local/wiki/tiddlers/GeomTREE Semi-Jack Physical Witness.tid",
        "role": "local_application_surface",
        "status": "local_reference",
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


def state_case(
    *,
    case_id: str,
    description: str,
    load_norm: float,
    torsion_norm: float,
    mechanical_residual_l2: float,
    layer_commitment_root_present: bool,
    equihash_like_witness_present: bool,
    witness_depth: int,
    residual_declared: bool,
    torsion_clock: float,
    wall_clock_seconds: float,
    literal_kerr_claim: bool = False,
) -> dict[str, Any]:
    torsion_ratio = torsion_norm / max(load_norm, 1.0e-12)
    mechanical_close = mechanical_residual_l2 <= EPSILON_MECH
    commitment_close = layer_commitment_root_present and residual_declared
    witness_close = equihash_like_witness_present and witness_depth <= PRACTICAL_TREE_FIDDY_DEPTH
    torsion_clock_close = torsion_clock <= TORSION_CRITICAL
    typed_analogy_close = not literal_kerr_claim
    finite_pass = mechanical_close and commitment_close and witness_close and torsion_clock_close and typed_analogy_close
    ergoregion = ERGOREGION_TORSION_RATIO <= torsion_ratio < FAILURE_HORIZON_TORSION_RATIO
    horizon = torsion_ratio >= FAILURE_HORIZON_TORSION_RATIO
    if literal_kerr_claim:
        decision = "QUARANTINE_LITERAL_KERR_OVERCLAIM"
    elif horizon:
        decision = "HOLD_FAILURE_HORIZON"
    elif ergoregion:
        decision = "HOLD_ERGOREGION_WARNING"
    elif finite_pass:
        decision = "ADMIT_SAFE_CHART_FIXTURE"
    else:
        decision = "HOLD_INCOMPLETE_WITNESS"
    item = {
        "case_id": case_id,
        "description": description,
        "load_norm": load_norm,
        "torsion_norm": torsion_norm,
        "torsion_ratio": torsion_ratio,
        "mechanical_residual_l2": mechanical_residual_l2,
        "mechanical_close": mechanical_close,
        "layer_commitment_root_present": layer_commitment_root_present,
        "equihash_like_witness_present": equihash_like_witness_present,
        "witness_depth": witness_depth,
        "tree_fiddy_depth_bound": PRACTICAL_TREE_FIDDY_DEPTH,
        "residual_declared": residual_declared,
        "torsion_clock": torsion_clock,
        "torsion_critical": TORSION_CRITICAL,
        "torsion_clock_close": torsion_clock_close,
        "wall_clock_seconds": wall_clock_seconds,
        "wall_clock_role": "metadata_shadow_not_hash_or_causal_coordinate",
        "literal_kerr_claim": literal_kerr_claim,
        "typed_analogy_close": typed_analogy_close,
        "finite_pass": finite_pass,
        "ergoregion_warning": ergoregion,
        "failure_horizon": horizon,
        "decision": decision,
    }
    item["case_hash"] = hash_obj({k: v for k, v in item.items() if k != "case_hash"})
    return item


def build_registry() -> dict[str, Any]:
    cases = [
        state_case(
            case_id="axial_fixture_closed",
            description="Mostly axial load; mechanics, commitments, witness, residual, and depth gates close.",
            load_norm=100.0,
            torsion_norm=4.0,
            mechanical_residual_l2=1.0e-12,
            layer_commitment_root_present=True,
            equihash_like_witness_present=True,
            witness_depth=18,
            residual_declared=True,
            torsion_clock=5.0,
            wall_clock_seconds=3600.0,
        ),
        state_case(
            case_id="off_axis_ergoregion",
            description="Off-axis load has not failed, but static vertical-load assumptions are no longer admissible.",
            load_norm=100.0,
            torsion_norm=24.0,
            mechanical_residual_l2=2.0e-12,
            layer_commitment_root_present=True,
            equihash_like_witness_present=True,
            witness_depth=31,
            residual_declared=True,
            torsion_clock=25.0,
            wall_clock_seconds=120.0,
        ),
        state_case(
            case_id="semi_jack_failure_horizon",
            description="Torsion-coupled load crosses the non-recoverable admissibility horizon.",
            load_norm=100.0,
            torsion_norm=48.0,
            mechanical_residual_l2=4.0e-12,
            layer_commitment_root_present=True,
            equihash_like_witness_present=True,
            witness_depth=34,
            residual_declared=True,
            torsion_clock=44.0,
            wall_clock_seconds=20.0,
        ),
        state_case(
            case_id="missing_memory_hard_witness",
            description="Mechanics close, but the proposed load assignment has no costly-to-fake witness.",
            load_norm=100.0,
            torsion_norm=5.0,
            mechanical_residual_l2=1.0e-12,
            layer_commitment_root_present=True,
            equihash_like_witness_present=False,
            witness_depth=12,
            residual_declared=True,
            torsion_clock=8.0,
            wall_clock_seconds=12.0,
        ),
        state_case(
            case_id="literal_kerr_overclaim",
            description="The analogy is incorrectly promoted as literal Kerr spacetime.",
            load_norm=100.0,
            torsion_norm=8.0,
            mechanical_residual_l2=1.0e-12,
            layer_commitment_root_present=True,
            equihash_like_witness_present=True,
            witness_depth=10,
            residual_declared=True,
            torsion_clock=9.0,
            wall_clock_seconds=1.0,
            literal_kerr_claim=True,
        ),
    ]
    return {
        "schema": "kerr_like_load_witness_geometry_registry_v1",
        "citations": CITATIONS,
        "claim_boundary": (
            "Kerr-like load witness geometry is a typed admissibility atlas for "
            "torsion-coupled mechanical states. It is not literal Kerr spacetime, "
            "not a structural safety certificate, and not a claim that hashes or "
            "Equihash terms are mechanical forces."
        ),
        "type_separation": {
            "mechanical_plane": "real/vector/tensor equilibrium residuals with units",
            "commitment_plane": "Merkle/O-AMMR bitstring commitments to layer, process, material, and sensor packets",
            "witness_plane": "Equihash-like memory-hard predicate over committed state and quantized load vector",
            "state_atlas_plane": "Kerr-like analogy for safe chart, ergoregion warning, and failure horizon",
            "clock_plane": "wall-clock time is metadata; torsional state-advance is the causal coordinate",
        },
        "time_substitution": {
            "rule": "replace wall-clock t with torsional state coordinate T",
            "statement": "Clock time is what the observer sees; torsion is what the structure remembers.",
            "torsion_clock": "T(s)=integral(||tau|| + alpha*||load cross normal|| + beta*risk) ds",
            "observed_time": "t_obs = pi_t(T, load, residual_risk, material_shadow, commitment_root)",
            "hash_policy": "wall_clock_excluded_from_receipt_hash; torsion_clock_included_as state coordinate",
        },
        "avoid_equation": "T*A(q)*omega - T*B(q)*delta + lambda*hash_xor_term = 0",
        "admissibility_equation": (
            "A(Omega)=1[||T A(q) omega - T B(q) delta|| <= epsilon_mech] * "
            "1[torsion_clock(Omega) <= T_crit] * "
            "1[R_M = Commit(layer/process/material packets)] * "
            "1[Pi_NK(R_M, Q(load), seed)=1] * "
            "1[depth(T_witness) <= 350] * "
            "1[typed_analogy_not_literal]"
        ),
        "kerr_like_dictionary": {
            "mass_M": "load/informatic burden",
            "spin_a": "torsion, twist, off-axis moment, cyclic shear",
            "frame_dragging": "load-path coupling where torsion drags neighboring admissible states",
            "ergoregion": "warning chart where static load assumptions fail but failure is not yet asserted",
            "event_horizon": "irreversible admissibility boundary where residual risk cannot be certified away",
            "ring_singularity": "degenerate failure core: crack, buckling hinge, delamination, wrong-part interface",
            "geodesic": "candidate load/witness trajectory through state space",
        },
        "parameters": {
            "epsilon_mech": EPSILON_MECH,
            "ergoregion_torsion_ratio": ERGOREGION_TORSION_RATIO,
            "failure_horizon_torsion_ratio": FAILURE_HORIZON_TORSION_RATIO,
            "practical_tree_fiddy_depth": PRACTICAL_TREE_FIDDY_DEPTH,
            "torsion_critical": TORSION_CRITICAL,
        },
        "cases": cases,
        "aggregates": {
            "case_count": len(cases),
            "admit_safe_chart_count": sum(1 for item in cases if item["decision"] == "ADMIT_SAFE_CHART_FIXTURE"),
            "hold_ergoregion_count": sum(1 for item in cases if item["decision"] == "HOLD_ERGOREGION_WARNING"),
            "hold_failure_horizon_count": sum(1 for item in cases if item["decision"] == "HOLD_FAILURE_HORIZON"),
            "hold_incomplete_witness_count": sum(1 for item in cases if item["decision"] == "HOLD_INCOMPLETE_WITNESS"),
            "quarantine_literal_kerr_count": sum(1 for item in cases if item["decision"] == "QUARANTINE_LITERAL_KERR_OVERCLAIM"),
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "kerr_like_load_witness_geometry_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "citations": registry["citations"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_TYPED_KERR_LIKE_LOAD_WITNESS_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Kerr-Like Load Witness Geometry",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Type Separation",
        "",
    ]
    for key, value in registry["type_separation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Torsion-Clock",
            "",
            f"- Rule: `{registry['time_substitution']['rule']}`",
            f"- Statement: {registry['time_substitution']['statement']}",
            f"- Torsion clock: `{registry['time_substitution']['torsion_clock']}`",
            f"- Observed time: `{registry['time_substitution']['observed_time']}`",
            f"- Hash policy: `{registry['time_substitution']['hash_policy']}`",
            "",
            "## Equations",
            "",
            f"- Avoid: `{registry['avoid_equation']}`",
            f"- Admit: `{registry['admissibility_equation']}`",
            "",
            "## Kerr-Like Dictionary",
            "",
        ]
    )
    for key, value in registry["kerr_like_dictionary"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Torsion ratio | Torsion-clock | Wall-clock shadow | Mechanical close | Witness | Decision |",
            "|---|---:|---:|---:|---|---|---|",
        ]
    )
    for item in registry["cases"]:
        lines.append(
            f"| `{item['case_id']}` | {item['torsion_ratio']:.3f} | "
            f"{item['torsion_clock']:.3f} | {item['wall_clock_seconds']:.3f} | "
            f"`{item['mechanical_close']}` | `{item['equihash_like_witness_present']}` | `{item['decision']}` |"
        )
    lines.extend(["", "## Citations", ""])
    for citation in registry["citations"]:
        target = citation.get("url") or citation.get("doi") or citation.get("path") or citation["status"]
        lines.append(f"- `{citation['id']}`: {citation['title']} ({target}); role: `{citation['role']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Hardware Materials KerrLike LoadWitness Receipt
title: Kerr-Like Load Witness Geometry
type: text/vnd.tiddlywiki

! Kerr-Like Load Witness Geometry

Durable runner:

```
4-Infrastructure/shim/kerr_like_load_witness_geometry_probe.py
```

Receipt:

```
{receipt['registry']}
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

!! Claim Boundary

This is a typed admissibility atlas for torsion-coupled mechanical states. It is not literal Kerr spacetime and not a structural safety certificate.

!! Rule

Physical equilibrium remains in the mechanical plane. Merkle/O-AMMR commits fabrication and material evidence. Equihash-like work is a witness predicate. Kerr-like language names the state atlas: safe chart, ergoregion warning, and failure horizon.

!! Torsion Clock

Clock time is metadata. Torsional state-advance is the causal coordinate:

```
T(s)=integral(||tau|| + alpha*||load cross normal|| + beta*risk) ds
```

The structure does not remember seconds; it remembers twist, load history, holonomy, residual strain, and damage transport.

!! Links

* [[GeomTREE Semi-Jack Physical Witness]]
* [[Merkle Tensegrity Load Equation Harness]]
* [[Tree Fiddy]]
* [[Invariant Dual Mechanics Supporting Materials]]
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
