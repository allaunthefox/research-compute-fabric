#!/usr/bin/env python3
"""Torsion-indexed network witness topology bridge.

This probe records the unification between the network topology equation and
the invariant load-witness model. It treats routes, load paths, proof paths, and
material-failure paths as constrained manifold trajectories. It does not promote
the network topology theory to a validated law; it preserves the bridge as a
receipt-bearing model chart with HOLD gates.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "torsion_indexed_network_witness_topology"
RECEIPT = OUT_DIR / "torsion_indexed_network_witness_topology_receipt.json"
SUMMARY = OUT_DIR / "torsion_indexed_network_witness_topology.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Torsion Indexed Network Witness Topology.tid"

SOURCES = [
    REPO / "shared-data" / "network_topology_database.json",
    REPO / "3-Mathematical-Models" / "fiber_optic_vibrational_tensor" / "Fundamental_Network_Topology_Equation.md",
    REPO / "6-Documentation" / "wiki" / "Network-Topology-Theory.md",
    REPO / "shared-data" / "data" / "network_topology_model_reweighting" / "network_topology_model_reweighting_receipt.json",
    REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation" / "hutter_torsion_clock_adaptation_receipt.json",
    REPO / "shared-data" / "data" / "torsion_interval_gaussian_splat_witness" / "torsion_interval_gaussian_splat_witness_receipt.json",
    REPO / "shared-data" / "data" / "collatz_ladder_shadow_filter" / "collatz_ladder_shadow_filter_receipt.json",
    REPO / "shared-data" / "data" / "underverse_variant_accounting" / "underverse_variant_accounting_receipt.json",
]

TERM_MAP = [
    {
        "network_term": "E(N)",
        "witness_analogue": "base admissibility of topology, object, proof route, or load graph",
        "guard": "HOLD_TOPOLOGY_EQUATION_VALIDATION",
    },
    {
        "network_term": "P(N)",
        "witness_analogue": "physics constraint: latency/distance/power or load/stress/torsion",
        "guard": "HOLD_COEFFICIENT_RECEIPT_DEBT",
    },
    {
        "network_term": "I(N)",
        "witness_analogue": "infrastructure density or material/support density",
        "guard": "HOLD_PROVENANCE",
    },
    {
        "network_term": "S(N)",
        "witness_analogue": "strategic importance or load-bearing criticality",
        "guard": "HOLD_TOPOLOGY_PREDICTION_VALIDATION",
    },
    {
        "network_term": "C(N)",
        "witness_analogue": "complexity penalty and anti-good-enough hidden route cost",
        "guard": "HOLD_RESIDUAL_MISSING",
    },
    {
        "network_term": "W(N)",
        "witness_analogue": "eigenmode separation: low/mid/high route, traffic, load, or failure channels",
        "guard": "HOLD_AXIS_UNDECLARED",
    },
    {
        "network_term": "M(N)",
        "witness_analogue": "compression quality and witness compactness",
        "guard": "HOLD_GLOBAL",
    },
    {
        "network_term": "H(N)",
        "witness_analogue": "boundary/bulk closure and exact replay gate",
        "guard": "REJECT_ROOT_MISMATCH",
    },
    {
        "network_term": "F(N)",
        "witness_analogue": "fractional memory and history-sensitive dynamics",
        "guard": "HOLD_TORSION_CLOCK_BOUNDARY",
    },
]

TRANSITIONS = [
    {
        "case": "compress_down",
        "condition": "closure holds and counted cost decreases",
        "operator": "pi_k_minus_1(X)",
        "decision": "ADMIT_AS_COMPRESSED_CHART_FIXTURE",
    },
    {
        "case": "expand_up",
        "condition": "hidden residual, holographic error, or undeclared axis remains",
        "operator": "Phi_k_plus_1(X)",
        "decision": "HOLD_EXPAND_WITH_WITNESS",
    },
    {
        "case": "terminate",
        "condition": "NaN0, missing residual, hidden payload, rollback failure, or root mismatch",
        "operator": "bottom",
        "decision": "REJECT_OR_NAN0_BOUNDARY",
    },
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def source_ref(path: Path) -> dict[str, Any]:
    return {"path": rel(path), "exists": path.exists(), "sha256": file_hash(path)}


def build_payload() -> dict[str, Any]:
    payload = {
        "schema": "torsion_indexed_network_witness_topology_v1",
        "name": "Torsion-Indexed Network Witness Topology",
        "source_refs": [source_ref(path) for path in SOURCES],
        "core_statement": (
            "Network routes, load paths, proof paths, and material-failure paths "
            "are constrained manifold trajectories. The network topology equation "
            "is the macro-routing layer; invariant load witnessing is the local "
            "admissibility layer."
        ),
        "torsion_substitution": "N_t -> N_T; clock time is metadata, accumulated torsion/state-advance indexes causal frames",
        "network_equation": "E_ext(N_T)=E(N_T)*W(N_T)*M(N_T)*H(N_T)*F(N_T)",
        "admissibility_equation": (
            "A(Omega_T)=1[mechanics_close]*E_ext(N_T)*"
            "1[merkle_shadow_root_recomputes]*1[residual_risk_bounded]"
        ),
        "ladder_rule": "L(X)=pi_k_minus_1(X) if closure and cost improve; Phi_k_plus_1(X) if residual requires expansion; bottom if NaN0/root/rollback/residual failure",
        "term_map": TERM_MAP,
        "transitions": TRANSITIONS,
        "claim_boundary": (
            "Bridge receipt only. This does not validate network predictions, "
            "mechanical safety, the Collatz conjecture, or operational topology "
            "inference. It records the shared routing skeleton and the gates "
            "required before any promotion."
        ),
        "decision": "ADMIT_BRIDGE_AS_HOLD_MODEL_CHART",
    }
    payload["bridge_hash"] = hash_obj({k: v for k, v in payload.items() if k != "bridge_hash"})
    return payload


def build_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "torsion_indexed_network_witness_topology_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "bridge_hash": payload["bridge_hash"],
        "source_count": len(payload["source_refs"]),
        "missing_source_count": sum(1 for item in payload["source_refs"] if not item["exists"]),
        "term_count": len(payload["term_map"]),
        "transition_count": len(payload["transitions"]),
        "decision": payload["decision"],
        "claim_boundary": payload["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Torsion-Indexed Network Witness Topology",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`  ",
        f"Bridge hash: `{payload['bridge_hash']}`",
        "",
        payload["claim_boundary"],
        "",
        "## Core Statement",
        "",
        payload["core_statement"],
        "",
        "## Equations",
        "",
        f"- Torsion substitution: `{payload['torsion_substitution']}`",
        f"- Network equation: `{payload['network_equation']}`",
        f"- Admissibility equation: `{payload['admissibility_equation']}`",
        f"- Ladder rule: `{payload['ladder_rule']}`",
        "",
        "## Term Map",
        "",
        "| Network term | Witness analogue | Guard |",
        "|---|---|---|",
    ]
    for item in payload["term_map"]:
        lines.append(f"| {item['network_term']} | {item['witness_analogue']} | {item['guard']} |")
    lines.extend(["", "## Ladder Transitions", "", "| Case | Condition | Operator | Decision |", "|---|---|---|---|"])
    for item in payload["transitions"]:
        lines.append(f"| {item['case']} | {item['condition']} | `{item['operator']}` | {item['decision']} |")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    text = [
        "title: Torsion Indexed Network Witness Topology",
        "tags: NetworkTopology TorsionClock Underverse Receipt HOLD",
        "type: text/vnd.tiddlywiki",
        "",
        "! Torsion-Indexed Network Witness Topology",
        "",
        f"Decision: `{receipt['decision']}`",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        f"Bridge hash: `{payload['bridge_hash']}`",
        "",
        "!! Core Statement",
        "",
        payload["core_statement"],
        "",
        "!! Equations",
        "",
        f"* Torsion substitution: `{payload['torsion_substitution']}`",
        f"* Network equation: `{payload['network_equation']}`",
        f"* Admissibility equation: `{payload['admissibility_equation']}`",
        f"* Ladder rule: `{payload['ladder_rule']}`",
        "",
        "!! Term Map",
        "",
        "| Network term | Witness analogue | Guard |h",
    ]
    for item in payload["term_map"]:
        text.append(f"| {item['network_term']} | {item['witness_analogue']} | {item['guard']} |")
    text.extend(
        [
            "",
            "!! Links",
            "",
            "* [[Network Topology Model Reweighting]]",
            "* [[Hutter Torsion Clock Adaptation]]",
            "* [[Torsion Interval Gaussian Splat Witness]]",
            "* [[Collatz Ladder Shadow Filter]]",
            "* [[Underverse Variant Accounting]]",
            f"* Receipt: `{rel(RECEIPT)}`",
            f"* Summary: `{rel(SUMMARY)}`",
        ]
    )
    TIDDLER.write_text("\n".join(text) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    receipt = build_receipt(payload)
    (OUT_DIR / "torsion_indexed_network_witness_topology.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(payload, receipt)
    write_tiddler(payload, receipt)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "receipt_hash": receipt["receipt_hash"],
                "bridge_hash": payload["bridge_hash"],
                "summary": rel(SUMMARY),
                "tiddler": rel(TIDDLER),
                "missing_source_count": receipt["missing_source_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
