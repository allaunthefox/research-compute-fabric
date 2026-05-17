#!/usr/bin/env python3
"""Stress the DNA substitution layer with intentionally absurd genetics.

This checks whether the primitive accounting survives carrier weirdness:

* all 24 A/T/G/C -> primitive permutations
* reverse-complement remapping
* phase rotations by 0/90/180/270 degrees
* hachimoji-like inert extension bases
* one deliberate non-bijective broken mapping that must fail closed

The pass condition is not biological plausibility.  The pass condition is that
bijective carrier substitutions round-trip exactly and non-bijective carrier
substitutions are detected as invalid.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
FORCE_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_force_regime_model_receipt.json"
)
OUT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_absurd_genetics_stress_receipt.json"
)

PRIMITIVES = ("field", "shear", "packet", "spectral")
BASES = ("A", "T", "G", "C")
EXTRA_HACHIMOJI_BASES = ("B", "S", "P", "Z")
BASE_PHASES = {"A": 0, "T": 90, "G": 180, "C": 270}
COMPLEMENT = {"A": "T", "T": "A", "G": "C", "C": "G"}
HANDLE_TO_PRIMITIVE = {
    "packet_local": "packet",
    "shear_torsion": "shear",
    "spectral_field": "spectral",
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fraction_str(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def fraction_json(value: Fraction) -> dict[str, Any]:
    return {
        "fraction": fraction_str(value),
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def parse_fraction_json(item: dict[str, Any]) -> Fraction:
    return Fraction(int(item["numerator"]), int(item["denominator"]))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def vector_from_json(items: dict[str, dict[str, Any]]) -> dict[str, Fraction]:
    return {key: parse_fraction_json(value) for key, value in items.items()}


def vector_json(vector: dict[str, Fraction]) -> dict[str, dict[str, Any]]:
    return {key: fraction_json(value) for key, value in sorted(vector.items())}


def signed_l1(vector: dict[str, Fraction]) -> Fraction:
    return sum((abs(value) for value in vector.values()), Fraction(0))


def is_bijective(mapping: dict[str, str]) -> bool:
    return set(mapping) == set(BASES) and set(mapping.values()) == set(PRIMITIVES)


def encode_primitive_to_bases(
    primitive_vector: dict[str, Fraction],
    base_to_primitive: dict[str, str],
) -> dict[str, Fraction]:
    return {
        base: primitive_vector[primitive]
        for base, primitive in base_to_primitive.items()
    }


def decode_bases_to_primitive(
    base_vector: dict[str, Fraction],
    base_to_primitive: dict[str, str],
) -> dict[str, Fraction] | None:
    if not is_bijective(base_to_primitive):
        return None
    decoded = {primitive: Fraction(0) for primitive in PRIMITIVES}
    for base, primitive in base_to_primitive.items():
        decoded[primitive] += base_vector[base]
    return decoded


def phase_centroid(base_vector: dict[str, Fraction], phase_offset: int) -> dict[str, Any]:
    real = 0.0
    imag = 0.0
    for base, value in base_vector.items():
        phase = (BASE_PHASES.get(base, 0) + phase_offset) % 360
        radians = math.radians(phase)
        real += float(value) * math.cos(radians)
        imag += float(value) * math.sin(radians)
    magnitude = math.hypot(real, imag)
    angle = math.degrees(math.atan2(imag, real)) % 360.0 if magnitude else 0.0
    return {"real": real, "imag": imag, "magnitude": magnitude, "angle_degrees": angle}


def primitive_delta(
    decoded: dict[str, Fraction] | None,
    target: dict[str, Fraction],
) -> dict[str, Fraction] | None:
    if decoded is None:
        return None
    return {
        primitive: decoded[primitive] - target[primitive]
        for primitive in PRIMITIVES
    }


def residual_base_vector(
    handle_signed_sum: dict[str, Fraction],
    base_to_primitive: dict[str, str],
) -> dict[str, Fraction] | None:
    if not is_bijective(base_to_primitive):
        return None
    primitive_to_base = {primitive: base for base, primitive in base_to_primitive.items()}
    vector = {base: Fraction(0) for base in BASES}
    for handle, primitive in HANDLE_TO_PRIMITIVE.items():
        vector[primitive_to_base[primitive]] += handle_signed_sum[handle]
    return vector


def evaluate_mapping(
    name: str,
    base_to_primitive: dict[str, str],
    primitive_keel: dict[str, Fraction],
    handle_signed_sum: dict[str, Fraction],
    phase_offset: int = 0,
    hachimoji_inert: bool = False,
) -> dict[str, Any]:
    bijective = is_bijective(base_to_primitive)
    base_vector = encode_primitive_to_bases(primitive_keel, base_to_primitive)
    decoded = decode_bases_to_primitive(base_vector, base_to_primitive)
    delta = primitive_delta(decoded, primitive_keel)
    residual_bases = residual_base_vector(handle_signed_sum, base_to_primitive)
    residual_total = sum(residual_bases.values(), Fraction(0)) if residual_bases is not None else None
    extra_bases = {base: Fraction(0) for base in EXTRA_HACHIMOJI_BASES} if hachimoji_inert else {}
    extended_vector = dict(base_vector)
    extended_vector.update(extra_bases)
    roundtrip_l1 = signed_l1(delta) if delta is not None else None
    aligned = (
        bijective
        and delta is not None
        and all(value == 0 for value in delta.values())
        and sum(base_vector.values(), Fraction(0)) == 1
        and residual_total == 0
        and all(value == 0 for value in extra_bases.values())
    )
    return {
        "name": name,
        "base_to_primitive": base_to_primitive,
        "bijective": bijective,
        "phase_offset_degrees": phase_offset,
        "hachimoji_inert_extension": hachimoji_inert,
        "base_vector": vector_json(base_vector),
        "extended_base_vector": vector_json(extended_vector),
        "base_total": fraction_json(sum(base_vector.values(), Fraction(0))),
        "phase_centroid": phase_centroid(base_vector, phase_offset),
        "roundtrip_delta": vector_json(delta) if delta is not None else None,
        "roundtrip_l1_error": fraction_json(roundtrip_l1) if roundtrip_l1 is not None else None,
        "residual_base_vector": vector_json(residual_bases) if residual_bases is not None else None,
        "residual_signed_total": fraction_json(residual_total) if residual_total is not None else None,
        "aligned": aligned,
        "expected_failure": not bijective,
        "failed_closed": not bijective and decoded is None and residual_bases is None,
    }


def reverse_complement_mapping(base_to_primitive: dict[str, str]) -> dict[str, str]:
    return {
        COMPLEMENT[base]: primitive
        for base, primitive in base_to_primitive.items()
    }


def build_receipt() -> dict[str, Any]:
    force = load_json(FORCE_RECEIPT)
    primitive_keel = vector_from_json(force["closure"]["primitive_target"])
    handle_signed_sum = vector_from_json(force["closure"]["handle_signed_sum_target"])

    evaluations = []
    for idx, primitive_perm in enumerate(itertools.permutations(PRIMITIVES)):
        mapping = {base: primitive for base, primitive in zip(BASES, primitive_perm)}
        evaluations.append(evaluate_mapping(
            name=f"perm_{idx:02d}",
            base_to_primitive=mapping,
            primitive_keel=primitive_keel,
            handle_signed_sum=handle_signed_sum,
            phase_offset=(idx % 4) * 90,
        ))
    canonical = {"A": "field", "T": "shear", "G": "packet", "C": "spectral"}
    evaluations.append(evaluate_mapping(
        name="reverse_complement_canonical",
        base_to_primitive=reverse_complement_mapping(canonical),
        primitive_keel=primitive_keel,
        handle_signed_sum=handle_signed_sum,
        phase_offset=180,
    ))
    evaluations.append(evaluate_mapping(
        name="hachimoji_inert_extension",
        base_to_primitive=canonical,
        primitive_keel=primitive_keel,
        handle_signed_sum=handle_signed_sum,
        phase_offset=0,
        hachimoji_inert=True,
    ))
    evaluations.append(evaluate_mapping(
        name="broken_non_bijective_collision",
        base_to_primitive={"A": "field", "T": "field", "G": "packet", "C": "spectral"},
        primitive_keel=primitive_keel,
        handle_signed_sum=handle_signed_sum,
        phase_offset=0,
    ))

    lawful_cases = [case for case in evaluations if not case["expected_failure"]]
    failure_cases = [case for case in evaluations if case["expected_failure"]]
    aligned_count = sum(1 for case in lawful_cases if case["aligned"])
    failed_closed_count = sum(1 for case in failure_cases if case["failed_closed"])

    receipt = {
        "schema": "standard_model_absurd_genetics_stress_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_absurd_genetics_stress",
        "source": {
            "force_regime_receipt": str(FORCE_RECEIPT.relative_to(REPO)),
            "force_regime_stable_hash_sha256": force.get("stable_force_regime_hash_sha256"),
        },
        "stress_design": {
            "permutation_count": 24,
            "reverse_complement_cases": 1,
            "hachimoji_inert_cases": 1,
            "deliberate_broken_cases": 1,
            "pass_rule": (
                "All bijective carrier mappings must round-trip with zero "
                "primitive error and zero residual drift; non-bijective mappings "
                "must fail closed."
            ),
        },
        "summary": {
            "total_cases": len(evaluations),
            "lawful_case_count": len(lawful_cases),
            "aligned_lawful_count": aligned_count,
            "expected_failure_count": len(failure_cases),
            "failed_closed_count": failed_closed_count,
            "all_lawful_aligned": aligned_count == len(lawful_cases),
            "all_expected_failures_closed": failed_closed_count == len(failure_cases),
            "does_not_self_implode": (
                aligned_count == len(lawful_cases)
                and failed_closed_count == len(failure_cases)
                and force["closure"]["closed"]
            ),
        },
        "evaluations": evaluations,
        "claim_boundary": (
            "This is an absurd symbolic carrier stress test. It does not make "
            "biological, genetic-engineering, QFT, or cosmological claims."
        ),
        "lawful": True,
    }
    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "stress_design": receipt["stress_design"],
        "summary": receipt["summary"],
        "evaluations": receipt["evaluations"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_absurd_genetics_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    receipt = build_receipt()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "lawful": receipt["lawful"],
        "stable_absurd_genetics_hash_sha256": receipt["stable_absurd_genetics_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "summary": receipt["summary"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
