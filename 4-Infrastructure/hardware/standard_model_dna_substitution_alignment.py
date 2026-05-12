#!/usr/bin/env python3
"""DNA substitution alignment for the force-regime compression model.

This substitutes the four local primitives with the A/T/G/C genetic event
alphabet used elsewhere in the hardware probes:

* A -> field
* T -> shear
* G -> packet
* C -> spectral

The goal is modest: check whether the existing 4D primitive keel and genus-3
residual boat can be represented as a DNA-like alphabet without losing closure.
This is a symbolic compression substitution, not a biological or physics claim.
"""

from __future__ import annotations

import argparse
import hashlib
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
    / "standard_model_dna_substitution_alignment_receipt.json"
)

BASE_TO_PRIMITIVE = {
    "A": "field",
    "T": "shear",
    "G": "packet",
    "C": "spectral",
}
PRIMITIVE_TO_BASE = {primitive: base for base, primitive in BASE_TO_PRIMITIVE.items()}
BASE_PHASE_DEGREES = {
    "A": 0,
    "T": 90,
    "G": 180,
    "C": 270,
}
HANDLE_TO_BASE = {
    "packet_local": "G",
    "shear_torsion": "T",
    "spectral_field": "C",
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


def base_vector_from_primitive(primitive_vector: dict[str, Fraction]) -> dict[str, Fraction]:
    return {
        base: primitive_vector[primitive]
        for base, primitive in BASE_TO_PRIMITIVE.items()
    }


def primitive_vector_from_base(base_vector: dict[str, Fraction]) -> dict[str, Fraction]:
    return {
        primitive: base_vector[base]
        for base, primitive in BASE_TO_PRIMITIVE.items()
    }


def phase_centroid(base_vector: dict[str, Fraction]) -> dict[str, Any]:
    real = 0.0
    imag = 0.0
    for base, value in base_vector.items():
        radians = math.radians(BASE_PHASE_DEGREES[base])
        real += float(value) * math.cos(radians)
        imag += float(value) * math.sin(radians)
    magnitude = math.hypot(real, imag)
    angle = math.degrees(math.atan2(imag, real)) % 360.0 if magnitude else 0.0
    return {
        "real": real,
        "imag": imag,
        "magnitude": magnitude,
        "angle_degrees": angle,
    }


def dominant_base(base_vector: dict[str, Fraction]) -> dict[str, Any]:
    base, value = max(base_vector.items(), key=lambda item: abs(item[1]))
    return {
        "base": base,
        "primitive": BASE_TO_PRIMITIVE[base],
        "value": fraction_json(value),
        "phase_degrees": BASE_PHASE_DEGREES[base],
    }


def sector_dna_signatures(force: dict[str, Any]) -> dict[str, Any]:
    sectors = {}
    for sector, data in force["force_like_sectors"].items():
        primitive_vector = vector_from_json(data["primitive_vector"])
        base_vector = base_vector_from_primitive(primitive_vector)
        handle_vector = vector_from_json(data["residual_handle_vector"])
        residual_bases = {base: Fraction(0) for base in BASE_TO_PRIMITIVE}
        for handle, value in handle_vector.items():
            residual_bases[HANDLE_TO_BASE[handle]] += value
        sectors[sector] = {
            "base_vector": vector_json(base_vector),
            "dominant_base": dominant_base(base_vector),
            "phase_centroid": phase_centroid(base_vector),
            "residual_base_vector": vector_json(residual_bases),
            "dominant_residual_base": dominant_base(residual_bases),
            "codon_hint": "".join(
                sorted(
                    BASE_TO_PRIMITIVE,
                    key=lambda base: abs(base_vector[base]),
                    reverse=True,
                )[:3]
            ),
            "source_dominant_primitive": data["dominant_primitive"],
            "source_dominant_residual_handle": data["dominant_residual_handle"],
        }
    return sectors


def build_receipt() -> dict[str, Any]:
    force = load_json(FORCE_RECEIPT)
    primitive_keel = vector_from_json(force["closure"]["primitive_target"])
    dna_keel = base_vector_from_primitive(primitive_keel)
    roundtrip_primitive = primitive_vector_from_base(dna_keel)
    primitive_delta = {
        primitive: roundtrip_primitive[primitive] - primitive_keel[primitive]
        for primitive in primitive_keel
    }

    handle_signed_sum = vector_from_json(force["closure"]["handle_signed_sum_target"])
    residual_base_signed = {base: Fraction(0) for base in BASE_TO_PRIMITIVE}
    for handle, value in handle_signed_sum.items():
        residual_base_signed[HANDLE_TO_BASE[handle]] += value

    sectors = sector_dna_signatures(force)

    receipt = {
        "schema": "standard_model_dna_substitution_alignment_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_dna_substitution_alignment",
        "source": {
            "force_regime_receipt": str(FORCE_RECEIPT.relative_to(REPO)),
            "force_regime_stable_hash_sha256": force.get("stable_force_regime_hash_sha256"),
        },
        "substitution": {
            "base_to_primitive": BASE_TO_PRIMITIVE,
            "primitive_to_base": PRIMITIVE_TO_BASE,
            "base_phase_degrees": BASE_PHASE_DEGREES,
            "handle_to_base": HANDLE_TO_BASE,
            "meaning": (
                "DNA bases are used as a four-symbol control alphabet over the "
                "existing primitive coordinates."
            ),
        },
        "dna_keel": {
            "base_vector": vector_json(dna_keel),
            "base_total": fraction_json(sum(dna_keel.values(), Fraction(0))),
            "dominant_base": dominant_base(dna_keel),
            "phase_centroid": phase_centroid(dna_keel),
            "roundtrip_primitive_delta": vector_json(primitive_delta),
            "roundtrip_l1_error": fraction_json(signed_l1(primitive_delta)),
        },
        "dna_residual_boat": {
            "residual_base_signed_vector": vector_json(residual_base_signed),
            "residual_base_signed_total": fraction_json(sum(residual_base_signed.values(), Fraction(0))),
            "zero_drift": sum(residual_base_signed.values(), Fraction(0)) == 0,
            "dominant_residual_base": dominant_base(residual_base_signed),
        },
        "force_sector_dna_signatures": sectors,
        "alignment": {
            "primitive_roundtrip_exact": all(value == 0 for value in primitive_delta.values()),
            "keel_total_is_one": sum(dna_keel.values(), Fraction(0)) == 1,
            "residual_zero_drift": sum(residual_base_signed.values(), Fraction(0)) == 0,
            "force_regime_closed": force["closure"]["closed"],
            "aligned": (
                all(value == 0 for value in primitive_delta.values())
                and sum(dna_keel.values(), Fraction(0)) == 1
                and sum(residual_base_signed.values(), Fraction(0)) == 0
                and force["closure"]["closed"]
            ),
        },
        "claim_boundary": (
            "This substitutes DNA bases as a symbolic four-letter control "
            "alphabet. It does not imply biological DNA implements the Standard "
            "Model, validate genomic physics, or make a synthetic-biology claim."
        ),
        "lawful": True,
    }

    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "substitution": receipt["substitution"],
        "dna_keel": receipt["dna_keel"],
        "dna_residual_boat": receipt["dna_residual_boat"],
        "force_sector_dna_signatures": receipt["force_sector_dna_signatures"],
        "alignment": receipt["alignment"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_dna_alignment_hash_sha256"] = sha256_bytes(stable_preimage)
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
        "aligned": receipt["alignment"]["aligned"],
        "stable_dna_alignment_hash_sha256": receipt["stable_dna_alignment_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "dna_keel": receipt["dna_keel"],
        "dna_residual_boat": receipt["dna_residual_boat"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
