#!/usr/bin/env python3
"""Receipt generator for the logogram-DNA codec objective.

This folds the DNA-style codec filter through Omindirection and GCCL: glyphs
are not payloads, adapters are not authorities, and every compressed codon-like
atom must pass payload, direction, chirality, placement, residual, receipt, and
adapter gates before it can participate in replay.
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
OUT_DIR = REPO / "shared-data" / "data" / "logogram_dna_codec"
RECEIPT = OUT_DIR / "logogram_dna_codec_receipt.json"
TABLE = OUT_DIR / "logogram_dna_codec_table.jsonl"
SUMMARY = OUT_DIR / "logogram_dna_codec_receipt.md"


OBJECTIVE_PACKET = {
    "name": "Logogram-DNA Codec Objective",
    "core_map": "S = Repair_R(Regulate_B_DeltaG(Replay_Pi(Gamma)))",
    "atom_shape": "a_i = (p_i,h_i,d_i,chi_i,phi_i,x_i,tau_i,r_i,g_i,rho_i,delta_i)",
    "payload_separation": "payload != glyph != rendered layout",
    "lossless_gate": "Decode(Gamma,Pi,R) == S",
    "substitution_gate": "SubOK(t_i -> g_i) iff Recover(g_i,r_i,rho_i) == t_i",
    "binding_gate": "B_logo = 1/(1 + exp((DeltaG_bind - mu_logo)/(k_B T_decode)))",
    "admission_gate": (
        "Adm(a_i) = F_payload F_direction F_chirality F_phase F_placement "
        "F_residual F_receipt F_adapter"
    ),
    "score": (
        "J_logo_DNA = |D|+|Gamma|+|Pi|+|R|+|H_receipts| - lambda_1 G_sub "
        "+ lambda_2 H(R)+lambda_3 DeltaG_bind/(k_B T_decode)+lambda_4 U_route "
        "+ lambda_5 L_human+lambda_6 C_collision+lambda_7 C_HOLD+lambda_8 C_QUARANTINE"
    ),
    "native_phrase": (
        "A lawful logogram is a compressed symbolic codon whose meaning is not "
        "the glyph, but the receipted replay path back to its canonical payload."
    ),
}


@dataclass(frozen=True)
class AtomFixture:
    symbol_id: str
    semantic_key: str
    canonical_payload_kernel: str
    kernel_args: dict[str, Any]
    glyph: str
    direction: str
    chirality: str
    phase: int
    placement: dict[str, Any]
    residual_sidecar: dict[str, Any] | None
    receipt_present: bool
    adapter_canonical: bool
    decision: str


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    atoms: list[AtomFixture]
    protocol: dict[str, Any]
    negative_control: bool
    notes: str


FIXTURES = [
    Fixture(
        fixture_id="lawful_logogram_codons_admit",
        protocol={"decoder": "logogram_codons_v1", "repair": "sidecar_v1"},
        negative_control=False,
        notes="Three receipted atoms replay long canonical payloads through compact glyph codons.",
        atoms=[
            AtomFixture(
                symbol_id="lg-trig-identity",
                semantic_key="math.trig.pythagorean",
                canonical_payload_kernel="repeat_literal",
                kernel_args={"literal": "sin(x)^2+cos(x)^2=1;", "count": 96},
                glyph="LG1",
                direction="forward",
                chirality="none",
                phase=0,
                placement={"kind": "row", "coord": [0, 0], "liberties": 2, "captured_by": None, "territory": "math"},
                residual_sidecar=None,
                receipt_present=True,
                adapter_canonical=True,
                decision="ACCEPT",
            ),
            AtomFixture(
                symbol_id="lg-euler",
                semantic_key="math.euler.identity",
                canonical_payload_kernel="repeat_literal",
                kernel_args={"literal": "exp(i*pi)+1=0;", "count": 96},
                glyph="LG2",
                direction="forward",
                chirality="none",
                phase=0,
                placement={"kind": "row", "coord": [1, 0], "liberties": 2, "captured_by": None, "territory": "math"},
                residual_sidecar=None,
                receipt_present=True,
                adapter_canonical=True,
                decision="ACCEPT",
            ),
            AtomFixture(
                symbol_id="lg-newton",
                semantic_key="physics.force",
                canonical_payload_kernel="repeat_literal",
                kernel_args={"literal": "F=m*a;", "count": 192},
                glyph="LG3",
                direction="forward",
                chirality="none",
                phase=0,
                placement={"kind": "row", "coord": [2, 0], "liberties": 2, "captured_by": None, "territory": "physics"},
                residual_sidecar=None,
                receipt_present=True,
                adapter_canonical=True,
                decision="ACCEPT",
            ),
        ],
    ),
    Fixture(
        fixture_id="auto_direction_hold",
        protocol={"decoder": "logogram_codons_v1", "repair": "sidecar_v1"},
        negative_control=True,
        notes="Recoverable atom is held because promoted direction cannot remain auto.",
        atoms=[
            AtomFixture(
                symbol_id="lg-auto",
                semantic_key="math.auto.direction",
                canonical_payload_kernel="repeat_literal",
                kernel_args={"literal": "a+b=b+a;", "count": 16},
                glyph="LGA",
                direction="auto",
                chirality="none",
                phase=0,
                placement={"kind": "row", "coord": [0, 0], "liberties": 1, "captured_by": None, "territory": "math"},
                residual_sidecar=None,
                receipt_present=True,
                adapter_canonical=True,
                decision="HOLD",
            )
        ],
    ),
    Fixture(
        fixture_id="semantic_tear_quarantine",
        protocol={"decoder": "logogram_codons_v1", "repair": "sidecar_v1"},
        negative_control=True,
        notes="Adapter mutation and missing receipt route the atom to quarantine.",
        atoms=[
            AtomFixture(
                symbol_id="lg-tear",
                semantic_key="math.semantic.tear",
                canonical_payload_kernel="repeat_literal",
                kernel_args={"literal": "x=x;", "count": 8},
                glyph="LGT",
                direction="forward",
                chirality="right",
                phase=90,
                placement={"kind": "quarantine", "coord": [0, 0], "liberties": 0, "captured_by": None, "territory": "tear"},
                residual_sidecar=None,
                receipt_present=False,
                adapter_canonical=False,
                decision="QUARANTINE",
            )
        ],
    ),
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def counted_size(obj: Any) -> int:
    return len(stable_json(obj).encode("utf-8"))


def entropy_bytes(data: bytes) -> float:
    if not data:
        return 0.0
    counts: dict[int, int] = {}
    for value in data:
        counts[value] = counts.get(value, 0) + 1
    total = len(data)
    return -sum((count / total) * math.log(count / total, 2) for count in counts.values())


def payload(atom: AtomFixture) -> str:
    if atom.canonical_payload_kernel == "repeat_literal":
        return str(atom.kernel_args["literal"]) * int(atom.kernel_args["count"])
    raise ValueError(f"unsupported payload kernel {atom.canonical_payload_kernel}")


def chiral_ok(chirality: str, phase: int) -> bool:
    if not (0 <= phase < 360):
        return False
    if chirality == "none":
        return phase == 0
    if chirality == "left":
        return 0 <= phase < 180
    if chirality == "right":
        return 180 <= phase < 360
    if chirality == "ambidextrous":
        return True
    return False


def placement_ok(atom: AtomFixture) -> bool:
    placement = atom.placement
    if placement.get("kind") == "quarantine":
        return atom.decision == "QUARANTINE"
    if placement.get("kind") == "board" and int(placement.get("liberties", 0)) == 0 and placement.get("captured_by") is None:
        return False
    return "coord" in placement and "territory" in placement


def atom_receipt(atom: AtomFixture, atom_payload: str) -> dict[str, Any]:
    payload_hash = sha256_text(atom_payload)
    source_hash = sha256_text(stable_json({"symbol_id": atom.symbol_id, "semantic_key": atom.semantic_key}))
    atom_hash = sha256_text(
        stable_json(
            {
                "symbol_id": atom.symbol_id,
                "glyph": atom.glyph,
                "payload_hash": payload_hash,
                "direction": atom.direction,
                "chirality": atom.chirality,
                "phase": atom.phase,
                "placement": atom.placement,
            }
        )
    )
    receipt_hash = sha256_text(stable_json({"payload_hash": payload_hash, "source_hash": source_hash, "atom_hash": atom_hash}))
    return {
        "payload_hash": payload_hash,
        "source_hash": source_hash,
        "atom_hash": atom_hash,
        "receipt_hash": receipt_hash,
    }


def recover_atom(atom: AtomFixture) -> str:
    return payload(atom)


def binding_delta(atoms: list[AtomFixture]) -> float:
    if len(atoms) < 2:
        return 0.0
    total = 0.0
    for left, right in zip(atoms, atoms[1:]):
        if left.placement.get("territory") == right.placement.get("territory"):
            total -= 1.0
        else:
            total += 0.5
        if left.direction == right.direction and left.direction != "auto":
            total -= 0.5
        else:
            total += 1.0
        if chiral_ok(left.chirality, left.phase) and chiral_ok(right.chirality, right.phase):
            total -= 0.25
        else:
            total += 2.0
    return total


def route_curvature(atoms: list[AtomFixture]) -> float:
    if len(atoms) < 3:
        return 0.0
    coords = [atom.placement.get("coord", [0, 0]) for atom in atoms]
    vectors = []
    for left, right in zip(coords, coords[1:]):
        vectors.append((right[0] - left[0], right[1] - left[1]))
    return float(sum(abs(bx - ax) + abs(by - ay) for (ax, ay), (bx, by) in zip(vectors, vectors[1:])))


def validate_atom(atom: AtomFixture, atom_payload: str) -> dict[str, Any]:
    receipt = atom_receipt(atom, atom_payload) if atom.receipt_present else {}
    residual_ok = atom.residual_sidecar is not None or recover_atom(atom) == atom_payload
    gates = {
        "payload": bool(atom_payload),
        "direction": atom.direction in {"forward", "reverse", "neutral"},
        "chirality_phase": chiral_ok(atom.chirality, atom.phase),
        "placement": placement_ok(atom),
        "residual": residual_ok,
        "receipt": atom.receipt_present and bool(receipt.get("payload_hash")),
        "adapter": atom.adapter_canonical,
    }
    if atom.decision == "QUARANTINE":
        admitted_decision = "QUARANTINE"
    elif all(gates.values()):
        admitted_decision = "ACCEPT"
    else:
        admitted_decision = "HOLD"
    return {
        "symbol_id": atom.symbol_id,
        "semantic_key": atom.semantic_key,
        "glyph": atom.glyph,
        "payload_hash": sha256_text(atom_payload),
        "receipt": receipt,
        "gates": gates,
        "declared_decision": atom.decision,
        "computed_decision": admitted_decision,
        "gate_pass": all(gates.values()) and admitted_decision == atom.decision,
    }


def run_fixture(fixture: Fixture) -> dict[str, Any]:
    atom_payloads = [payload(atom) for atom in fixture.atoms]
    source = "".join(atom_payloads)
    recovered = "".join(recover_atom(atom) for atom in fixture.atoms if atom.decision != "QUARANTINE")
    exact_replay = recovered == source
    atom_results = [validate_atom(atom, atom_payload) for atom, atom_payload in zip(fixture.atoms, atom_payloads)]
    has_quarantine = any(result["computed_decision"] == "QUARANTINE" for result in atom_results)
    hold_count = sum(1 for result in atom_results if result["computed_decision"] == "HOLD")
    accepted_count = sum(1 for result in atom_results if result["computed_decision"] == "ACCEPT")

    dictionary_payload = {"objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET))}
    gamma_payload = [
        {
            "symbol_id": atom.symbol_id,
            "glyph": atom.glyph,
            "direction": atom.direction,
            "chirality": atom.chirality,
            "phase": atom.phase,
            "placement": atom.placement,
            "payload_kernel": atom.canonical_payload_kernel,
            "kernel_args": atom.kernel_args,
        }
        for atom in fixture.atoms
    ]
    residual_payload = {
        "sidecars": [
            {"symbol_id": atom.symbol_id, "sidecar": atom.residual_sidecar}
            for atom in fixture.atoms
            if atom.residual_sidecar is not None
        ]
    }
    receipt_payload = {
        "receipts": [
            result["receipt"].get("receipt_hash")
            for result in atom_results
            if result["receipt"].get("receipt_hash")
        ]
    }
    protocol_payload = fixture.protocol

    raw_bytes = len(source.encode("utf-8"))
    dictionary_bytes = counted_size(dictionary_payload)
    gamma_bytes = counted_size(gamma_payload)
    protocol_bytes = counted_size(protocol_payload)
    residual_bytes = counted_size(residual_payload) if residual_payload["sidecars"] else 0
    receipt_bytes = counted_size(receipt_payload)
    counted_bytes = dictionary_bytes + gamma_bytes + protocol_bytes + residual_bytes + receipt_bytes
    substitution_gain = raw_bytes - (gamma_bytes + residual_bytes + receipt_bytes)
    byte_gain = raw_bytes - counted_bytes
    delta_g = binding_delta(fixture.atoms)
    curvature = route_curvature(fixture.atoms)
    residual_entropy = entropy_bytes(stable_json(residual_payload).encode("utf-8")) if residual_bytes else 0.0

    if fixture.negative_control:
        status = "HOLD_DIAGNOSTIC" if not has_quarantine else "QUARANTINE_DIAGNOSTIC"
    elif exact_replay and byte_gain > 0 and hold_count == 0 and not has_quarantine:
        status = "ADMIT_FIXTURE"
    else:
        status = "HOLD_DIAGNOSTIC"

    result = {
        "fixture_id": fixture.fixture_id,
        "notes": fixture.notes,
        "negative_control": fixture.negative_control,
        "source_hash": sha256_text(source),
        "recovered_hash": sha256_text(recovered),
        "objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET)),
        "exact_replay": exact_replay,
        "raw_bytes": raw_bytes,
        "dictionary_bytes": dictionary_bytes,
        "gamma_bytes": gamma_bytes,
        "protocol_bytes": protocol_bytes,
        "residual_bytes": residual_bytes,
        "receipt_bytes": receipt_bytes,
        "counted_bytes": counted_bytes,
        "substitution_gain": substitution_gain,
        "byte_gain": byte_gain,
        "delta_g_bind_analog": delta_g,
        "route_curvature": curvature,
        "residual_entropy_bits_per_byte": residual_entropy,
        "accepted_count": accepted_count,
        "hold_count": hold_count,
        "quarantine_count": sum(1 for result in atom_results if result["computed_decision"] == "QUARANTINE"),
        "atom_results": atom_results,
        "status": status,
    }
    result["result_hash"] = sha256_text(stable_json({k: v for k, v in result.items() if k != "result_hash"}))
    return result


def write_summary(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "# Logogram-DNA Codec Receipt",
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
        f"`{OBJECTIVE_PACKET['admission_gate']}`",
        "",
        f"`{OBJECTIVE_PACKET['substitution_gate']}`",
        "",
        "## Fixtures",
        "",
        "| Fixture | Status | Exact replay | Byte gain | Accepted | HOLD | Quarantine |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for result in receipt["results"]:
        lines.append(
            f"| {result['fixture_id']} | {result['status']} | {result['exact_replay']} | "
            f"{result['byte_gain']} | {result['accepted_count']} | {result['hold_count']} | "
            f"{result['quarantine_count']} |"
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
        "schema": "logogram_dna_codec_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "objective_packet": OBJECTIVE_PACKET,
        "objective_hash": sha256_text(stable_json(OBJECTIVE_PACKET)),
        "source_specs": [
            "6-Documentation/docs/specs/OMINDIRECTION_LOGOGRAM_DESIGN_AND_COMPILER.md",
            "6-Documentation/docs/specs/GCCL_ENCODING_CONTRACT.md",
            "6-Documentation/docs/provenance/DNA_CODEC_FILTER_SOURCES.cff",
        ],
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
            "Logogram-DNA codec objective prior only. It combines local Omindirection "
            "and GCCL law gates with the DNA-filtered repair/binding analogy. It "
            "does not claim biological modeling, renderer correctness, global "
            "logogram compression, Hutter performance, or external proof status."
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
