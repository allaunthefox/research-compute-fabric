#!/usr/bin/env python3
"""Find where genetic carrier extensions fail.

The previous stress probe showed that A/T/G/C permutations survive when they
remain bijective, and hachimoji-like extra bases are harmless when inert.  This
probe makes the extra bases non-inert on purpose and records which accounting
law breaks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DNA_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_dna_substitution_alignment_receipt.json"
)
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
    / "standard_model_extension_failure_probe_receipt.json"
)

BASES = ("A", "T", "G", "C")
EXTRA_BASES = ("B", "S", "P", "Z")
PRIMITIVES = ("field", "shear", "packet", "spectral")
CANONICAL = {"A": "field", "T": "shear", "G": "packet", "C": "spectral"}
HANDLE_TO_BASE = {"packet_local": "G", "shear_torsion": "T", "spectral_field": "C"}


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


def decode_extended(
    base_vector: dict[str, Fraction],
    base_to_primitive: dict[str, str],
) -> tuple[dict[str, Fraction] | None, list[str]]:
    failures: list[str] = []
    if set(BASES) - set(base_to_primitive):
        failures.append("missing_core_base_decode")
    if set(base_to_primitive.values()) != set(PRIMITIVES):
        failures.append("primitive_coverage_failure")
    decoded = {primitive: Fraction(0) for primitive in PRIMITIVES}
    for base, value in base_vector.items():
        primitive = base_to_primitive.get(base)
        if primitive is None:
            if value != 0:
                failures.append("nonzero_unmapped_extension_mass")
            continue
        if primitive not in PRIMITIVES:
            failures.append("unknown_primitive_target")
            continue
        decoded[primitive] += value
    if failures:
        return None, sorted(set(failures))
    return decoded, []


def residual_total_with_extension(
    residual_bases: dict[str, Fraction],
    extra_residuals: dict[str, Fraction],
) -> Fraction:
    return sum(residual_bases.values(), Fraction(0)) + sum(extra_residuals.values(), Fraction(0))


def evaluate_case(
    name: str,
    base_vector: dict[str, Fraction],
    base_to_primitive: dict[str, str],
    primitive_target: dict[str, Fraction],
    residual_base_vector: dict[str, Fraction],
    extra_residuals: dict[str, Fraction] | None = None,
    expected_failure_laws: tuple[str, ...] = (),
) -> dict[str, Any]:
    extra_residuals = extra_residuals or {base: Fraction(0) for base in EXTRA_BASES}
    decoded, decode_failures = decode_extended(base_vector, base_to_primitive)
    if decoded is None:
        primitive_delta = None
        roundtrip_l1 = None
    else:
        primitive_delta = {
            primitive: decoded[primitive] - primitive_target[primitive]
            for primitive in PRIMITIVES
        }
        roundtrip_l1 = signed_l1(primitive_delta)

    base_total = sum(base_vector.values(), Fraction(0))
    residual_total = residual_total_with_extension(residual_base_vector, extra_residuals)

    law_failures: list[str] = list(decode_failures)
    if base_total != 1:
        law_failures.append("keel_total_not_one")
    if primitive_delta is not None and any(value != 0 for value in primitive_delta.values()):
        law_failures.append("primitive_roundtrip_error")
    if residual_total != 0:
        law_failures.append("residual_drift")
    if any(base in BASES and base_to_primitive.get(base) is None for base in BASES):
        law_failures.append("core_base_missing")
    if len(set(base_to_primitive.values()) & set(PRIMITIVES)) < len(PRIMITIVES):
        law_failures.append("primitive_loss")

    law_failures = sorted(set(law_failures))
    failed = bool(law_failures)
    expected = set(expected_failure_laws)
    observed = set(law_failures)
    return {
        "name": name,
        "base_vector": vector_json(base_vector),
        "base_to_primitive": base_to_primitive,
        "base_total": fraction_json(base_total),
        "decoded_primitive": vector_json(decoded) if decoded is not None else None,
        "primitive_delta": vector_json(primitive_delta) if primitive_delta is not None else None,
        "roundtrip_l1_error": fraction_json(roundtrip_l1) if roundtrip_l1 is not None else None,
        "residual_base_vector": vector_json(residual_base_vector),
        "extra_residuals": vector_json(extra_residuals),
        "residual_signed_total": fraction_json(residual_total),
        "law_failures": law_failures,
        "failed": failed,
        "expected_failure_laws": sorted(expected),
        "matches_expected_failure": expected <= observed,
    }


def build_receipt() -> dict[str, Any]:
    dna = load_json(DNA_RECEIPT)
    force = load_json(FORCE_RECEIPT)
    primitive_target = vector_from_json(force["closure"]["primitive_target"])
    canonical_base_vector = vector_from_json(dna["dna_keel"]["base_vector"])
    residual_base_vector = vector_from_json(dna["dna_residual_boat"]["residual_base_signed_vector"])

    cases = []

    harmless = dict(canonical_base_vector)
    harmless.update({base: Fraction(0) for base in EXTRA_BASES})
    cases.append(evaluate_case(
        "control_inert_extension",
        harmless,
        CANONICAL,
        primitive_target,
        residual_base_vector,
        expected_failure_laws=(),
    ))

    leaked_keel = dict(harmless)
    leaked_keel["B"] = Fraction(1, 100)
    cases.append(evaluate_case(
        "extension_keel_mass_leak",
        leaked_keel,
        CANONICAL,
        primitive_target,
        residual_base_vector,
        expected_failure_laws=("keel_total_not_one", "nonzero_unmapped_extension_mass"),
    ))

    aliased = dict(harmless)
    aliased["B"] = Fraction(1, 100)
    cases.append(evaluate_case(
        "extension_aliases_field",
        aliased,
        {**CANONICAL, "B": "field"},
        primitive_target,
        residual_base_vector,
        expected_failure_laws=("keel_total_not_one", "primitive_roundtrip_error"),
    ))

    split_shear = dict(harmless)
    split_shear["T"] -= Fraction(1, 100)
    split_shear["S"] = Fraction(1, 100)
    cases.append(evaluate_case(
        "extension_splits_shear_lawfully",
        split_shear,
        {**CANONICAL, "S": "shear"},
        primitive_target,
        residual_base_vector,
        expected_failure_laws=(),
    ))

    split_shear_unmapped = dict(split_shear)
    cases.append(evaluate_case(
        "extension_splits_shear_without_decode_rule",
        split_shear_unmapped,
        CANONICAL,
        primitive_target,
        residual_base_vector,
        expected_failure_laws=("nonzero_unmapped_extension_mass",),
    ))

    residual_leak = dict(harmless)
    cases.append(evaluate_case(
        "extension_residual_leak",
        residual_leak,
        CANONICAL,
        primitive_target,
        residual_base_vector,
        extra_residuals={"B": Fraction(1, 100), "S": Fraction(0), "P": Fraction(0), "Z": Fraction(0)},
        expected_failure_laws=("residual_drift",),
    ))

    residual_balanced = dict(harmless)
    cases.append(evaluate_case(
        "extension_balanced_residual_sideband",
        residual_balanced,
        CANONICAL,
        primitive_target,
        residual_base_vector,
        extra_residuals={"B": Fraction(1, 100), "S": Fraction(-1, 100), "P": Fraction(0), "Z": Fraction(0)},
        expected_failure_laws=(),
    ))

    primitive_collision = dict(harmless)
    cases.append(evaluate_case(
        "extension_collision_drops_spectral",
        primitive_collision,
        {"A": "field", "T": "shear", "G": "packet", "C": "packet"},
        primitive_target,
        residual_base_vector,
        expected_failure_laws=("primitive_coverage_failure", "primitive_loss"),
    ))

    expected_ok = [case for case in cases if not case["expected_failure_laws"]]
    expected_bad = [case for case in cases if case["expected_failure_laws"]]
    ok_passed = [case for case in expected_ok if not case["failed"]]
    bad_matched = [case for case in expected_bad if case["matches_expected_failure"]]

    receipt = {
        "schema": "standard_model_extension_failure_probe_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_extension_failure_probe",
        "source": {
            "dna_alignment_receipt": str(DNA_RECEIPT.relative_to(REPO)),
            "dna_alignment_stable_hash_sha256": dna.get("stable_dna_alignment_hash_sha256"),
            "force_regime_receipt": str(FORCE_RECEIPT.relative_to(REPO)),
            "force_regime_stable_hash_sha256": force.get("stable_force_regime_hash_sha256"),
        },
        "failure_laws": {
            "keel_total_not_one": "extension mass changed the normalized control vector total",
            "nonzero_unmapped_extension_mass": "an extra base carried mass without a decode rule",
            "primitive_roundtrip_error": "decoded primitive vector no longer equals the target vector",
            "residual_drift": "extension residuals no longer sum to zero",
            "primitive_coverage_failure": "decode map no longer covers all primitives",
            "primitive_loss": "at least one primitive cannot be represented",
        },
        "summary": {
            "case_count": len(cases),
            "expected_ok_count": len(expected_ok),
            "expected_ok_passed": len(ok_passed),
            "expected_failure_count": len(expected_bad),
            "expected_failures_matched": len(bad_matched),
            "extension_boundary_identified": (
                len(ok_passed) == len(expected_ok)
                and len(bad_matched) == len(expected_bad)
            ),
        },
        "cases": cases,
        "claim_boundary": (
            "This identifies symbolic carrier extension failure modes. It does "
            "not make biological, genetic-engineering, QFT, or cosmological claims."
        ),
        "lawful": True,
    }
    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "failure_laws": receipt["failure_laws"],
        "summary": receipt["summary"],
        "cases": receipt["cases"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_extension_failure_hash_sha256"] = sha256_bytes(stable_preimage)
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
        "stable_extension_failure_hash_sha256": receipt["stable_extension_failure_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "summary": receipt["summary"],
        "cases": [
            {
                "name": case["name"],
                "failed": case["failed"],
                "law_failures": case["law_failures"],
                "matches_expected_failure": case["matches_expected_failure"],
            }
            for case in receipt["cases"]
        ],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
