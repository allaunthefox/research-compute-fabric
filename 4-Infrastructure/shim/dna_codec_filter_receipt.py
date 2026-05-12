#!/usr/bin/env python3
"""Receipt generator for the DNA-filtered codec objective.

This treats DNA equations as an engineering filter for the reconstruction
core: conserved motif information, local binding compatibility, repair
layers, mutation-budget pressure, and replay curvature are measured as
route-prior fields. The hard gate remains byte-exact repair plus positive
byte law.
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
OUT_DIR = REPO / "shared-data" / "data" / "dna_codec_filter"
RECEIPT = OUT_DIR / "dna_codec_filter_receipt.json"
TABLE = OUT_DIR / "dna_codec_filter_table.jsonl"
SUMMARY = OUT_DIR / "dna_codec_filter_receipt.md"
SOURCE_MANIFEST = REPO / "6-Documentation" / "docs" / "provenance" / "DNA_CODEC_FILTER_SOURCES.cff"


OBJECTIVE_PACKET = {
    "name": "DNA-Filtered Codec Objective",
    "core_map": "S = Repair_R(Regulate_B_DeltaG(Replay(K,Theta,Pi)))",
    "lossless_gate": "Repair(Replay(K,Theta,Pi),R) == S",
    "byte_error": "epsilon_byte = 0",
    "score": (
        "J_DNA_codec = |D|+|K|+|Theta|+|Pi|+|R| + lambda_1 H_seq(R) "
        "- lambda_2 R_motif(K,Theta) + lambda_3 DeltaG_codec "
        "+ lambda_4 U_route + lambda_5 E_replication + lambda_6 E_mutation "
        "+ lambda_7 C_regulatory"
    ),
    "motif_information": "R_motif = sum_l(log2(|A_d|) - H_d(l))",
    "binding_energy": "DeltaG_codec = sum_i DeltaG_local(k_i,k_{i+1}) + DeltaG_context + DeltaG_mismatch",
    "repair_stack": "S0 = Replay(K,Theta,Pi); S = Repair(S0,R)",
    "mutation_budget": "epsilon_token <= epsilon_archive / N_tokens",
    "route_curvature": "U_route = 1/2 kappa_decode integral ||d t_state / ds||^2 ds",
    "native_phrase": (
        "Compression as genomic reconstruction: what to grow, where to bind, "
        "when to unfold, how to repair, and what residual remains."
    ),
}


SOURCE_SURFACES = [
    {
        "name": "Sequence logos / positional information content",
        "url": "https://bioconductor.org/packages/release/bioc/html/seqLogo.html",
        "role": "conserved motif information prior",
    },
    {
        "name": "SantaLucia nearest-neighbor DNA thermodynamics",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC19045/",
        "role": "local binding-compatibility analogy",
    },
    {
        "name": "DNA replication proofreading and mismatch repair",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6153641/",
        "role": "layered repair/fidelity analogy",
    },
    {
        "name": "Drake rule and genome-size mutation pressure",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4563715/",
        "role": "per-token error budget analogy",
    },
    {
        "name": "Worm-like chain model",
        "url": "https://chem.libretexts.org/Bookshelves/Biological_Chemistry/Concepts_in_Biophysical_Chemistry_%28Tokmakoff%29/02%3A_Macromolecules/09%3A_Macromolecular_Mechanics/9.02%3A_Worm-like_Chain",
        "role": "replay curvature analogy",
    },
]


LOCAL_BINDING_SCORE = {
    "AA": 1.4,
    "AC": -1.2,
    "AG": -0.4,
    "AT": -1.0,
    "CA": -1.1,
    "CC": 1.3,
    "CG": -2.1,
    "CT": -0.4,
    "GA": -0.4,
    "GC": -2.0,
    "GG": 1.3,
    "GT": -1.1,
    "TA": -0.9,
    "TC": -0.4,
    "TG": -1.0,
    "TT": 1.4,
}


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    source: str
    kernel: str
    theta: dict[str, Any]
    protocol: dict[str, Any]
    negative_control: bool
    notes: str


FIXTURES = [
    Fixture(
        fixture_id="motif_binding_repair_admit",
        source="ACGT" * 256,
        kernel="repeat_motif",
        theta={"motif": "ACGT", "count": 256, "regulator": "stable_nn"},
        protocol={"decoder": "repeat_motif_v1", "repair": "patch_v1"},
        negative_control=False,
        notes="Conserved local motif with exact replay and positive byte law.",
    ),
    Fixture(
        fixture_id="wrong_count_repair_hold",
        source="ACGT" * 256,
        kernel="repeat_motif",
        theta={"motif": "ACGT", "count": 255, "regulator": "stable_nn"},
        protocol={"decoder": "repeat_motif_v1", "repair": "patch_v1"},
        negative_control=True,
        notes="Residual can repair the missing motif, but the route is a negative control.",
    ),
    Fixture(
        fixture_id="unstable_binding_literal_hold",
        source="AAAACCCCGGGGTTTT",
        kernel="raw_literal",
        theta={"literal": "AAAACCCCGGGGTTTT", "regulator": "homopolymer_run"},
        protocol={"decoder": "raw_literal_v1", "repair": "patch_v1"},
        negative_control=False,
        notes="Exact replay, but no positive byte law and high local self-run penalty.",
    ),
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def entropy(values: list[str]) -> float:
    if not values:
        return 0.0
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    total = len(values)
    return -sum((count / total) * math.log(count / total, 2) for count in counts.values())


def shannon_entropy_bytes(data: bytes) -> float:
    if not data:
        return 0.0
    counts: dict[int, int] = {}
    for value in data:
        counts[value] = counts.get(value, 0) + 1
    total = len(data)
    return -sum((count / total) * math.log(count / total, 2) for count in counts.values())


def replay(kernel: str, theta: dict[str, Any], protocol: dict[str, Any]) -> str:
    decoder = protocol.get("decoder")
    if kernel == "repeat_motif" and decoder == "repeat_motif_v1":
        return str(theta["motif"]) * int(theta["count"])
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


def apply_patch(source: str, candidate: str, patch: list[dict[str, Any]]) -> str:
    repaired = list(candidate)
    for item in patch:
        index = int(item["i"])
        while index >= len(repaired):
            repaired.append("")
        repaired[index] = str(item["actual"])
    return "".join(repaired[: len(source)])


def motif_information(source: str, motif: str | None) -> float:
    alphabet_size = 4
    if not motif:
        return 0.0
    width = len(motif)
    if width == 0 or len(source) < width:
        return 0.0
    windows = [source[index : index + width] for index in range(0, len(source), width) if len(source[index : index + width]) == width]
    if not windows:
        return 0.0
    gain = 0.0
    for position in range(width):
        column = [window[position] for window in windows]
        gain += max(0.0, math.log(alphabet_size, 2) - entropy(column))
    return gain * len(windows)


def binding_energy(sequence: str) -> float:
    if len(sequence) < 2:
        return 0.0
    return sum(LOCAL_BINDING_SCORE.get(sequence[index : index + 2], 0.0) for index in range(len(sequence) - 1))


def route_curvature(sequence: str) -> float:
    if len(sequence) < 3:
        return 0.0
    directions = []
    order = {"A": 0, "C": 1, "G": 2, "T": 3}
    for left, right in zip(sequence, sequence[1:]):
        directions.append(order.get(right, 0) - order.get(left, 0))
    return sum(abs(right - left) for left, right in zip(directions, directions[1:]))


def repair_error_budget(patch_count: int, token_count: int) -> dict[str, float]:
    # Engineering analogy only: every layer is a bounded receipt, not a biology claim.
    p_kernel = 1e-6
    p_basis = 1e-6
    p_replay = 1e-9
    p_repair = max(1e-12, (patch_count + 1) / max(token_count, 1) * 1e-9)
    # A layered verifier fails if any required layer fails. For independent
    # small risks the union bound is the conservative engineering proxy.
    p_fail_union_bound = min(1.0, p_kernel + p_basis + p_replay + p_repair)
    return {
        "p_kernel": p_kernel,
        "p_basis": p_basis,
        "p_replay": p_replay,
        "p_repair": p_repair,
        "p_decode_fail_union_bound": p_fail_union_bound,
        "negative_log10_fail_union_bound": -math.log10(p_fail_union_bound),
    }


def counted_size(obj: Any) -> int:
    return len(stable_json(obj).encode("utf-8"))


def run_fixture(fixture: Fixture) -> dict[str, Any]:
    try:
        reconstruction = replay(fixture.kernel, fixture.theta, fixture.protocol)
        replay_error = None
    except Exception as exc:  # noqa: BLE001 - receipt should preserve failure text.
        reconstruction = ""
        replay_error = str(exc)

    patch = residual_patch(fixture.source, reconstruction)
    repaired = apply_patch(fixture.source, reconstruction, patch)
    exact_replay_without_residual = fixture.source == reconstruction
    exact_replay_with_residual = repaired == fixture.source
    motif = fixture.theta.get("motif") if isinstance(fixture.theta.get("motif"), str) else None
    motif_gain = motif_information(fixture.source, motif)
    delta_g = binding_energy(motif or fixture.source)
    curvature = route_curvature(reconstruction or fixture.source)
    source_entropy = shannon_entropy_bytes(fixture.source.encode("utf-8"))
    residual_payload = {"patch": patch}
    residual_bytes = 0 if exact_replay_without_residual else counted_size(residual_payload)
    residual_entropy = shannon_entropy_bytes(stable_json(residual_payload).encode("utf-8")) if residual_bytes else 0.0

    dictionary_payload = {
        "objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET)),
        "source_manifest": rel(SOURCE_MANIFEST),
    }
    kernel_payload = {"kernel": fixture.kernel}
    theta_payload = fixture.theta
    protocol_payload = fixture.protocol
    counted_payload = {
        "D": dictionary_payload,
        "K": kernel_payload,
        "Theta": theta_payload,
        "Pi": protocol_payload,
        "R": residual_payload,
    }
    raw_bytes = len(fixture.source.encode("utf-8"))
    dictionary_bytes = counted_size(dictionary_payload)
    kernel_bytes = counted_size(kernel_payload)
    theta_bytes = counted_size(theta_payload)
    protocol_bytes = counted_size(protocol_payload)
    counted_bytes = dictionary_bytes + kernel_bytes + theta_bytes + protocol_bytes + residual_bytes
    byte_gain = raw_bytes - counted_bytes
    error_budget = repair_error_budget(len(patch), len(fixture.source))
    mutation_budget_per_token = 0.0
    if len(fixture.source) > 0:
        mutation_budget_per_token = 0.0 / len(fixture.source)

    locally_stable = delta_g < 0.0
    positive_byte_law = byte_gain > 0
    residual_declared = True

    if fixture.negative_control and exact_replay_without_residual:
        status = "FAIL_NEGATIVE_CONTROL"
    elif fixture.negative_control:
        status = "HOLD_DIAGNOSTIC"
    elif exact_replay_with_residual and positive_byte_law and locally_stable:
        status = "ADMIT_FIXTURE"
    else:
        status = "HOLD_DIAGNOSTIC"

    result = {
        "fixture_id": fixture.fixture_id,
        "notes": fixture.notes,
        "negative_control": fixture.negative_control,
        "source_hash": sha256_text(fixture.source),
        "reconstruction_hash": sha256_text(reconstruction),
        "repaired_hash": sha256_text(repaired),
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
        "positive_byte_law": positive_byte_law,
        "source_entropy_bits_per_byte": source_entropy,
        "residual_entropy_bits_per_byte": residual_entropy,
        "motif_information_bits": motif_gain,
        "delta_g_codec_analog": delta_g,
        "locally_stable": locally_stable,
        "route_curvature": curvature,
        "mutation_budget_per_token_for_lossless_archive": mutation_budget_per_token,
        "repair_error_budget": error_budget,
        "patch_count": len(patch),
        "counted_payload_hash": sha256_text(stable_json(counted_payload)),
        "status": status,
    }
    result["result_hash"] = sha256_text(stable_json({k: v for k, v in result.items() if k != "result_hash"}))
    return result


def write_summary(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "# DNA Codec Filter Receipt",
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
        f"`{OBJECTIVE_PACKET['lossless_gate']}`",
        "",
        "## Fixtures",
        "",
        "| Fixture | Status | Exact repair | Byte gain | Motif bits | DeltaG analog | Route curvature |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for result in receipt["results"]:
        lines.append(
            f"| {result['fixture_id']} | {result['status']} | "
            f"{result['exact_replay_with_residual']} | {result['byte_gain']} | "
            f"{result['motif_information_bits']:.2f} | {result['delta_g_codec_analog']:.2f} | "
            f"{result['route_curvature']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Source Surfaces",
            "",
        ]
    )
    for source in SOURCE_SURFACES:
        lines.append(f"- {source['name']}: {source['url']}")
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
        "schema": "dna_codec_filter_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_packet": OBJECTIVE_PACKET,
        "objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET)),
        "source_manifest": rel(SOURCE_MANIFEST),
        "source_surfaces": SOURCE_SURFACES,
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
            "DNA-filtered codec objective prior only. It maps biological equations "
            "to codec filters for motif conservation, local binding compatibility, "
            "repair layering, mutation-budget pressure, and replay curvature. It "
            "does not model DNA, does not ingest biological data, does not validate "
            "biology, and does not claim compression benchmark performance."
        ),
    }
    receipt["receipt_hash"] = sha256_text(
        stable_json(
            {
                k: v
                for k, v in receipt.items()
                if k not in {"receipt_hash", "generated_at_utc"}
            }
        )
    )
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
