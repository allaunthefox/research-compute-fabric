#!/usr/bin/env python3
"""Receipt generator for the quantum cognitive-load transfold equation.

This admits the pasted equation as a HOLD-first route prior, not as a proven
psychological, quantum-computing, or compression result. The executable part is
a tiny Pauli-string replay that checks feature extraction and component routing.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "quantum_cogload_transfold"
RECEIPT = OUT_DIR / "quantum_cogload_transfold_receipt.json"
TABLE = OUT_DIR / "quantum_cogload_transfold_table.jsonl"
SUMMARY = OUT_DIR / "quantum_cogload_transfold_receipt.md"


CANONICAL_PACKET = {
    "name": "Quantum Cognitive Load Transfold",
    "symbol": "L_QCog",
    "compact_equation": (
        "L_QCog(H_class,rho,Omega) = R_Sigma_Q({C_k_Q * R_k_Q("
        "x_k_Q(H_Q,U_Q,rho,Omega);theta_k_Q) * lambda_phi^D_f * "
        "B_k_Q(Omega)} for k in {I,E,G,R,M}; theta_Sigma_Q)"
    ),
    "transfold": {
        "H_Q": "(Pauli o C_n o Q_hbar)(H_class)",
        "pauli_expansion": "H_Q = sum_alpha c_alpha P_alpha",
        "pauli_string": "P_alpha = tensor_j sigma_j(alpha), sigma in {I,X,Y,Z}",
        "coefficient": "c_alpha = 2^-n Tr[P_alpha C_n(Q_hbar(H_class))]",
    },
    "feature_vector": [
        "H_P(c)",
        "S_P(c)",
        "chi_comm(H_Q)",
        "E_ent(rho)",
        "epsilon_C",
        "D_circ(U_Q)",
        "M_meas",
        "Delta_basis",
        "Delta_semantic",
    ],
    "components": {
        "I": ["H_P", "S_P", "chi_comm", "E_ent"],
        "E": ["epsilon_C", "D_circ", "M_meas", "Delta_basis"],
        "G": ["Delta_schema", "Delta_compression", "Delta_transfer"],
        "R": ["Delta_basis", "Delta_domain", "Delta_classical_quantum", "Delta_glyph_Pauli"],
        "M": ["n", "S_P", "D_context", "N_registers"],
    },
    "fractal_dimension": "D_f = log(2) / log(phi)",
    "native_stack_phrase": (
        "CogLoad_Q = ResponseFold(PauliMass + EntanglementBurden + "
        "NoncommutativeRouting + TruncationResidual + ReplayDepth + "
        "SemanticBasinPressure)"
    ),
}


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    pauli_coefficients: dict[str, float]
    tau: float
    rho_entanglement_bits: float
    epsilon_c: float
    circuit_depth: int
    measurement_count: int
    delta_basis: float
    delta_semantic: float
    negative_control: bool


FIXTURES = [
    Fixture(
        fixture_id="two_qubit_pauli_cloud_admit",
        pauli_coefficients={"ZI": 0.5, "IZ": 0.25, "XX": 0.125, "YY": 0.125},
        tau=0.1,
        rho_entanglement_bits=1.0,
        epsilon_c=0.01,
        circuit_depth=8,
        measurement_count=2,
        delta_basis=0.125,
        delta_semantic=0.2,
        negative_control=False,
    ),
    Fixture(
        fixture_id="single_term_toy_hold",
        pauli_coefficients={"ZI": 1.0},
        tau=0.1,
        rho_entanglement_bits=0.0,
        epsilon_c=0.0,
        circuit_depth=1,
        measurement_count=1,
        delta_basis=0.0,
        delta_semantic=0.0,
        negative_control=False,
    ),
    Fixture(
        fixture_id="missing_pauli_coefficients_negative",
        pauli_coefficients={},
        tau=0.1,
        rho_entanglement_bits=0.0,
        epsilon_c=1.0,
        circuit_depth=0,
        measurement_count=0,
        delta_basis=1.0,
        delta_semantic=1.0,
        negative_control=True,
    ),
]


ANTICOMMUTE = {
    ("X", "Y"),
    ("Y", "X"),
    ("X", "Z"),
    ("Z", "X"),
    ("Y", "Z"),
    ("Z", "Y"),
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def coefficient_probabilities(coefficients: dict[str, float]) -> dict[str, float]:
    norm = sum(value * value for value in coefficients.values())
    if norm <= 0:
        return {}
    return {key: (value * value) / norm for key, value in coefficients.items()}


def pauli_entropy(coefficients: dict[str, float]) -> float:
    probs = coefficient_probabilities(coefficients)
    return -sum(prob * math.log(prob, 2) for prob in probs.values() if prob > 0)


def support_size(coefficients: dict[str, float], tau: float) -> int:
    return sum(1 for value in coefficients.values() if abs(value) > tau)


def anticommutes(left: str, right: str) -> bool:
    if len(left) != len(right):
        raise ValueError("Pauli strings must have equal length")
    flips = 0
    for a, b in zip(left, right):
        if a == "I" or b == "I" or a == b:
            continue
        if (a, b) in ANTICOMMUTE:
            flips += 1
        else:
            raise ValueError(f"unsupported Pauli pair {a}{b}")
    return flips % 2 == 1


def commutation_burden(coefficients: dict[str, float]) -> float:
    probs = coefficient_probabilities(coefficients)
    keys = sorted(probs)
    burden = 0.0
    for i, left in enumerate(keys):
        for right in keys[i + 1 :]:
            if anticommutes(left, right):
                burden += probs[left] * probs[right]
    return burden


def component_scores(fixture: Fixture) -> dict[str, float]:
    h_p = pauli_entropy(fixture.pauli_coefficients)
    s_p = float(support_size(fixture.pauli_coefficients, fixture.tau))
    chi = commutation_burden(fixture.pauli_coefficients) if fixture.pauli_coefficients else 0.0
    e_ent = fixture.rho_entanglement_bits
    intrinsic = h_p + 0.25 * s_p + chi + e_ent
    extraneous = fixture.epsilon_c + 0.1 * fixture.circuit_depth + 0.25 * fixture.measurement_count + fixture.delta_basis
    germane = 0.5 * (fixture.delta_semantic + max(0.0, 1.0 - fixture.epsilon_c))
    routing = fixture.delta_basis + fixture.delta_semantic + chi
    memory = len(next(iter(fixture.pauli_coefficients), "")) + s_p + 0.25 * fixture.circuit_depth
    return {
        "H_P": h_p,
        "S_P": s_p,
        "chi_comm": chi,
        "E_ent": e_ent,
        "L_I_Q": intrinsic,
        "L_E_Q": extraneous,
        "L_G_Q": germane,
        "L_R_Q": routing,
        "L_M_Q": memory,
        "L_QCog_toy": intrinsic + extraneous + germane + routing + memory,
    }


def run_fixture(fixture: Fixture) -> dict[str, Any]:
    feature_errors: list[dict[str, Any]] = []
    if not fixture.pauli_coefficients:
        feature_errors.append({"path": "pauli_coefficients", "error": "missing_required_coefficients"})
    else:
        lengths = {len(item) for item in fixture.pauli_coefficients}
        if len(lengths) != 1:
            feature_errors.append({"path": "pauli_coefficients", "error": "mixed_pauli_string_lengths"})

    replay_valid = not feature_errors
    residual_declared = True
    scores = component_scores(fixture) if replay_valid else {}

    encoded_payload = {
        "canonical_packet_hash": sha256_text(stable_json(CANONICAL_PACKET)),
        "pauli_coefficients": fixture.pauli_coefficients,
        "tau": fixture.tau,
        "feature_extractors": ["H_P", "S_P", "chi_comm", "E_ent", "epsilon_C", "D_circ", "M_meas"],
    }
    explicit_payload = {
        "equation_packet": CANONICAL_PACKET,
        "toy_scores": scores,
    }
    residual_payload = {"feature_errors": feature_errors}
    encoded_bytes = len(stable_json(encoded_payload).encode("utf-8"))
    explicit_bytes = len(stable_json(explicit_payload).encode("utf-8"))
    residual_bytes = 0 if replay_valid else len(stable_json(residual_payload).encode("utf-8"))
    byte_gain = explicit_bytes - encoded_bytes - residual_bytes

    if fixture.negative_control and replay_valid:
        status = "FAIL_NEGATIVE_CONTROL"
    elif replay_valid and residual_declared and byte_gain > 0 and not fixture.negative_control and scores.get("S_P", 0) > 1:
        status = "ADMIT_FIXTURE"
    else:
        status = "HOLD_DIAGNOSTIC"

    result = {
        "fixture_id": fixture.fixture_id,
        "negative_control": fixture.negative_control,
        "pauli_coefficients_hash": sha256_text(stable_json(fixture.pauli_coefficients)),
        "canonical_packet_hash": sha256_text(stable_json(CANONICAL_PACKET)),
        "feature_error_count": len(feature_errors),
        "feature_errors": feature_errors,
        "scores": scores,
        "replay_valid": replay_valid,
        "residual_declared": residual_declared,
        "encoded_bytes": encoded_bytes,
        "explicit_bytes": explicit_bytes,
        "residual_bytes": residual_bytes,
        "byte_gain": byte_gain,
        "status": status,
    }
    result["result_hash"] = sha256_text(stable_json({k: v for k, v in result.items() if k != "result_hash"}))
    return result


def write_summary(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "# Quantum Cognitive Load Transfold Receipt",
        "",
        f"Schema: `{receipt['schema']}`  ",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Canonical Packet",
        "",
        f"`{CANONICAL_PACKET['compact_equation']}`",
        "",
        "## Fixture Status",
        "",
        "| Fixture | Status | Replay | Byte gain |",
        "|---|---|---:|---:|",
    ]
    for result in receipt["results"]:
        lines.append(
            f"| {result['fixture_id']} | {result['status']} | "
            f"{result['replay_valid']} | {result['byte_gain']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [run_fixture(fixture) for fixture in FIXTURES]
    with TABLE.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, sort_keys=True) + "\n")

    status_values = sorted({result["status"] for result in results})
    receipt = {
        "schema": "quantum_cogload_transfold_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_packet": CANONICAL_PACKET,
        "canonical_packet_hash": sha256_text(stable_json(CANONICAL_PACKET)),
        "fixture_count": len(results),
        "table": rel(TABLE),
        "summary": rel(SUMMARY),
        "status_counts": {
            status: sum(1 for result in results if result["status"] == status)
            for status in status_values
        },
        "results": results,
        "decision": "HOLD",
        "claim_boundary": (
            "Quantum cognitive-load transfold prior only. It records a canonical "
            "equation packet and a tiny Pauli-string feature replay; it does not "
            "prove cognitive load theory, does not validate a quantum algorithm, "
            "does not establish biological or psychological claims, and does not "
            "claim compression benchmark performance."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json({k: v for k, v in receipt.items() if k != "receipt_hash"}))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt, SUMMARY)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "table": rel(TABLE),
                "receipt_hash": receipt["receipt_hash"],
                "status_counts": receipt["status_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
