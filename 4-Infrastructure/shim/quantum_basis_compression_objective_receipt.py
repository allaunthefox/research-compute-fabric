#!/usr/bin/env python3
"""Receipt generator for the quantum-basis compression objective.

This converts the quantum cognitive-load implication into an executable
HOLD-first codec objective: a candidate basis is useful only when kernel,
parameters, protocol, and residual replay byte-exactly and cost less than raw.
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
OUT_DIR = REPO / "shared-data" / "data" / "quantum_basis_compression_objective"
RECEIPT = OUT_DIR / "quantum_basis_compression_objective_receipt.json"
TABLE = OUT_DIR / "quantum_basis_compression_objective_table.jsonl"
SUMMARY = OUT_DIR / "quantum_basis_compression_objective_receipt.md"


OBJECTIVE_PACKET = {
    "name": "Quantum Basis Compression Objective",
    "core_map": "S -> (K_Q,Theta_Q,R,Pi) -> S_hat",
    "lossless_gate": "Decode(K_Q,Theta_Q,R,Pi) == S",
    "byte_error": "epsilon_byte = ||S - S_hat||_0 = 0",
    "score": (
        "J_compress = |D| + |K_Q| + |Theta_Q| + |R| + |Pi| + "
        "lambda_T D_replay + lambda_L L_decode"
    ),
    "gain": "G_Q = |S| - (|D| + |K_Q| + |Theta_Q| + |R_Q| + |Pi_Q|)",
    "admission": "G_Q > 0 and exact replay",
    "residual": "R_Q = S - Replay(K_Q,Theta_Q,Pi_Q)",
    "native_phrase": (
        "Compression is finding the projection where most of the object becomes "
        "lawful reconstruction and only the law-breaking part remains residual."
    ),
}


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    source: str
    kernel: str
    theta: dict[str, Any]
    protocol: dict[str, Any]
    negative_control: bool


FIXTURES = [
    Fixture(
        fixture_id="periodic_ab_kernel_admit",
        source="AB" * 128,
        kernel="repeat_literal",
        theta={"literal": "AB", "count": 128},
        protocol={"decoder": "repeat_literal_v1"},
        negative_control=False,
    ),
    Fixture(
        fixture_id="periodic_ab_wrong_count_negative",
        source="AB" * 128,
        kernel="repeat_literal",
        theta={"literal": "AB", "count": 127},
        protocol={"decoder": "repeat_literal_v1"},
        negative_control=True,
    ),
    Fixture(
        fixture_id="nearly_random_literal_hold",
        source="A7fQ9zLm02PqXRtB",
        kernel="raw_literal",
        theta={"literal": "A7fQ9zLm02PqXRtB"},
        protocol={"decoder": "raw_literal_v1"},
        negative_control=False,
    ),
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def replay(kernel: str, theta: dict[str, Any], protocol: dict[str, Any]) -> str:
    decoder = protocol.get("decoder")
    if kernel == "repeat_literal" and decoder == "repeat_literal_v1":
        return str(theta["literal"]) * int(theta["count"])
    if kernel == "raw_literal" and decoder == "raw_literal_v1":
        return str(theta["literal"])
    raise ValueError(f"unsupported kernel/protocol pair {kernel}/{decoder}")


def residual_patch(source: str, candidate: str) -> list[dict[str, Any]]:
    patch: list[dict[str, Any]] = []
    max_len = max(len(source), len(candidate))
    for index in range(max_len):
        actual = source[index] if index < len(source) else ""
        proposed = candidate[index] if index < len(candidate) else ""
        if actual != proposed:
            patch.append({"i": index, "actual": actual, "candidate": proposed})
    return patch


def shannon_entropy_bytes(data: bytes) -> float:
    if not data:
        return 0.0
    counts: dict[int, int] = {}
    for value in data:
        counts[value] = counts.get(value, 0) + 1
    total = len(data)
    return -sum((count / total) * math.log(count / total, 2) for count in counts.values())


def run_fixture(fixture: Fixture) -> dict[str, Any]:
    source_bytes = fixture.source.encode("utf-8")
    try:
        reconstruction = replay(fixture.kernel, fixture.theta, fixture.protocol)
        replay_error = None
    except Exception as exc:  # noqa: BLE001 - receipt should preserve failure text.
        reconstruction = ""
        replay_error = str(exc)

    patch = residual_patch(fixture.source, reconstruction)
    exact_replay_without_residual = fixture.source == reconstruction
    residual_declared = True
    reconstructed_with_patch = list(reconstruction)
    for item in patch:
        index = int(item["i"])
        while index >= len(reconstructed_with_patch):
            reconstructed_with_patch.append("")
        reconstructed_with_patch[index] = str(item["actual"])
    repaired = "".join(reconstructed_with_patch[: len(fixture.source)])
    exact_replay_with_residual = repaired == fixture.source

    dictionary_payload = {"objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET))}
    kernel_payload = {"kernel": fixture.kernel}
    theta_payload = fixture.theta
    protocol_payload = fixture.protocol
    residual_payload = {"patch": patch}
    counted_payload = {
        "D": dictionary_payload,
        "K_Q": kernel_payload,
        "Theta_Q": theta_payload,
        "R": residual_payload,
        "Pi": protocol_payload,
    }
    raw_bytes = len(source_bytes)
    dictionary_bytes = len(stable_json(dictionary_payload).encode("utf-8"))
    kernel_bytes = len(stable_json(kernel_payload).encode("utf-8"))
    theta_bytes = len(stable_json(theta_payload).encode("utf-8"))
    protocol_bytes = len(stable_json(protocol_payload).encode("utf-8"))
    residual_bytes = 0 if exact_replay_without_residual else len(stable_json(residual_payload).encode("utf-8"))
    counted_bytes = dictionary_bytes + kernel_bytes + theta_bytes + protocol_bytes + residual_bytes
    byte_gain = raw_bytes - counted_bytes
    residual_entropy = shannon_entropy_bytes(stable_json(residual_payload).encode("utf-8")) if residual_bytes else 0.0
    source_entropy = shannon_entropy_bytes(source_bytes)

    if fixture.negative_control and exact_replay_with_residual and not exact_replay_without_residual:
        status = "HOLD_DIAGNOSTIC"
    elif fixture.negative_control and exact_replay_without_residual:
        status = "FAIL_NEGATIVE_CONTROL"
    elif exact_replay_with_residual and byte_gain > 0 and not fixture.negative_control:
        status = "ADMIT_FIXTURE"
    else:
        status = "HOLD_DIAGNOSTIC"

    result = {
        "fixture_id": fixture.fixture_id,
        "negative_control": fixture.negative_control,
        "source_hash": sha256_text(fixture.source),
        "reconstruction_hash": sha256_text(reconstruction),
        "objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET)),
        "replay_error": replay_error,
        "exact_replay_without_residual": exact_replay_without_residual,
        "exact_replay_with_residual": exact_replay_with_residual,
        "residual_declared": residual_declared,
        "raw_bytes": raw_bytes,
        "dictionary_bytes": dictionary_bytes,
        "kernel_bytes": kernel_bytes,
        "theta_bytes": theta_bytes,
        "protocol_bytes": protocol_bytes,
        "residual_bytes": residual_bytes,
        "counted_bytes": counted_bytes,
        "byte_gain": byte_gain,
        "source_entropy_bits_per_byte": source_entropy,
        "residual_entropy_bits_per_byte": residual_entropy,
        "patch_count": len(patch),
        "counted_payload_hash": sha256_text(stable_json(counted_payload)),
        "status": status,
    }
    result["result_hash"] = sha256_text(stable_json({k: v for k, v in result.items() if k != "result_hash"}))
    return result


def write_summary(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "# Quantum Basis Compression Objective Receipt",
        "",
        f"Schema: `{receipt['schema']}`  ",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Objective",
        "",
        f"`{OBJECTIVE_PACKET['core_map']}`",
        "",
        f"`{OBJECTIVE_PACKET['score']}`",
        "",
        f"`{OBJECTIVE_PACKET['admission']}`",
        "",
        "## Fixtures",
        "",
        "| Fixture | Status | Exact replay | Byte gain | Residual bytes |",
        "|---|---|---:|---:|---:|",
    ]
    for result in receipt["results"]:
        lines.append(
            f"| {result['fixture_id']} | {result['status']} | "
            f"{result['exact_replay_with_residual']} | {result['byte_gain']} | "
            f"{result['residual_bytes']} |"
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
        "schema": "quantum_basis_compression_objective_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_packet": OBJECTIVE_PACKET,
        "objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET)),
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
            "Quantum-basis compression objective prior only. It checks a tiny "
            "lossless generator plus residual accounting surface; it does not "
            "claim Hutter performance, does not validate quantum compression, "
            "and does not promote any aesthetic transform without positive "
            "byte law and exact replay."
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
