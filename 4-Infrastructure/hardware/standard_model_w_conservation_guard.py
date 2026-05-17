#!/usr/bin/env python3
"""W-conservation guard for Standard Model projection retunes.

This uses existing electroweak research as a constraint vocabulary for the
local symbolic projection work.  "W conservation" is interpreted as a guarded
bundle of electroweak structure, not conservation of W-boson particle number:

* SU(2) x U(1) gauge context
* charged-current pairing and CKM mixing
* Higgs/Goldstone mass-generation link
* Ward/Slavnov-Taylor identity discipline
* ghost/gauge-fixing accounting at the receipt boundary

The output is a route/design guard for geometric compression experiments, not a
physical Standard Model calculation.
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
ACCOUNTING_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_residual_accounting_probe_receipt.json"
)
SENSITIVITY_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_projection_sensitivity_probe_receipt.json"
)
OUT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_w_conservation_guard_receipt.json"
)

W_AXIS = "electroweak_charged_w"
W_REQUIRED_SUPPORT = ("field", "shear", "spectral")
W_LINKED_AXES = (
    "charged_current_ckm",
    "electroweak_neutral_za",
    "higgs_goldstone_scalar",
    "fermion_quark_sector",
    "fermion_lepton_sector",
    "ghost_gaugefix_sector",
    "derivative_kinetic_flow",
)


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


def row_support(row: dict[str, dict[str, Any]]) -> tuple[str, ...]:
    return tuple(sorted(row))


def candidate_has_all_w_support(candidate: dict[str, Any]) -> bool:
    return tuple(sorted(W_REQUIRED_SUPPORT)) == row_support(candidate["candidate_row"])


def classify_candidate(candidate: dict[str, Any] | None) -> dict[str, Any]:
    if candidate is None:
        return {
            "status": "missing",
            "passes_guard": False,
            "reasons": ["no candidate supplied"],
        }

    reasons: list[str] = []
    passes = True

    if candidate["axis"] != W_AXIS:
        passes = False
        reasons.append("candidate does not retune the charged W axis")
    if candidate["support_changed"]:
        passes = False
        reasons.append("candidate changes primitive support")
    if not candidate_has_all_w_support(candidate):
        passes = False
        reasons.append("candidate does not preserve field/shear/spectral W support")
    if parse_fraction_json(candidate["residual_l1_improvement"]) <= 0:
        passes = False
        reasons.append("candidate does not improve residual_l1")

    if passes:
        reasons.append("candidate preserves W support and improves residual_l1")
        status = "admissible_w_guarded_retune"
    else:
        status = "diagnostic_only"

    return {
        "axis": candidate["axis"],
        "status": status,
        "passes_guard": passes,
        "reasons": reasons,
        "candidate_row": candidate["candidate_row"],
        "baseline_row": candidate["baseline_row"],
        "candidate_residual_l1": candidate["candidate_residual_l1"],
        "residual_l1_improvement": candidate["residual_l1_improvement"],
        "improvement_ratio_of_baseline": candidate["improvement_ratio_of_baseline"],
        "support_changed": candidate["support_changed"],
        "candidate_top_residual_axis": candidate["candidate_top_residual_axis"],
    }


def build_receipt() -> dict[str, Any]:
    accounting = load_json(ACCOUNTING_RECEIPT)
    sensitivity = load_json(SENSITIVITY_RECEIPT)
    best_raw = sensitivity["diagnostic_summary"]["best_candidate"]
    best_support_preserving = sensitivity["diagnostic_summary"]["best_support_preserving_candidate"]
    w_axis_accounting = accounting["axis_accounting"][W_AXIS]

    research_guard = {
        "not_particle_number_conservation": (
            "The W boson is massive/unstable after electroweak symmetry breaking; "
            "the useful conservation language is gauge/current/identity structure, "
            "not conserved W particle count."
        ),
        "electroweak_gauge_context": (
            "Treat W as part of the SU(2) x U(1) electroweak gauge structure, "
            "not as an isolated axis."
        ),
        "charged_current_pairing": (
            "W-retunes must keep links to charged-current fermion grammar and CKM "
            "mixing instead of hiding the charge-changing role in a packet-only row."
        ),
        "higgs_goldstone_mass_link": (
            "W-retunes must remember the Higgs/Goldstone link that supplies the "
            "mass/longitudinal-mode bookkeeping after symmetry breaking."
        ),
        "ward_slavnov_taylor_guard": (
            "Gauge-fixing, ghost, and Green-function identities are treated as "
            "receipt obligations: a retune may be diagnostic unless the identity "
            "boundary is explicitly preserved or residualized."
        ),
    }

    receipt = {
        "schema": "standard_model_w_conservation_guard_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_w_conservation_guard",
        "source": {
            "accounting_receipt": str(ACCOUNTING_RECEIPT.relative_to(REPO)),
            "accounting_stable_hash_sha256": accounting.get("stable_residual_accounting_hash_sha256"),
            "sensitivity_receipt": str(SENSITIVITY_RECEIPT.relative_to(REPO)),
            "sensitivity_stable_hash_sha256": sensitivity.get("stable_projection_sensitivity_hash_sha256"),
            "research_sources": [
                {
                    "label": "PDG 2025 Electroweak Model review",
                    "url": "https://pdg.lbl.gov/2025/reviews/rpp2025-rev-standard-model.pdf",
                    "used_for": "SU(2)xU(1) gauge context, CKM charged-current placement, Higgs/W mass link, W precision context",
                },
                {
                    "label": "Slavnov-Taylor and Ward Identities in the Electroweak Theory",
                    "url": "https://arxiv.org/abs/1407.3960",
                    "used_for": "Ward/Slavnov-Taylor identity discipline and gauge-fixing independence",
                },
                {
                    "label": "The Renormalization of the Electroweak Standard Model to All Orders",
                    "url": "https://arxiv.org/abs/hep-th/9709154",
                    "used_for": "all-order identity structure: Slavnov-Taylor, rigid Ward, and abelian local Ward identities",
                },
            ],
        },
        "research_guard": research_guard,
        "local_w_axis_signal": {
            "axis": W_AXIS,
            "residual": w_axis_accounting["residual"],
            "scale_class": w_axis_accounting["scale_class"],
            "correction_direction": w_axis_accounting["correction_direction"],
            "handle": w_axis_accounting["handle"],
            "sector": w_axis_accounting["sector"],
            "dominant_primitive_before_guard": w_axis_accounting["dominant_primitive"],
            "linked_axes_to_preserve": W_LINKED_AXES,
        },
        "candidate_classification": {
            "best_raw_candidate": classify_candidate(best_raw),
            "best_support_preserving_candidate": classify_candidate(best_support_preserving),
        },
        "recommended_local_geometry": {
            "axis": W_AXIS,
            "retune_row": best_support_preserving["candidate_row"],
            "status": "recommended_next_diagnostic_route",
            "reason": (
                "It is the best support-preserving improvement: it keeps W on "
                "field/shear/spectral support while shifting the local geometry "
                "toward field-dominant W accounting."
            ),
            "required_next_checks": [
                "recompute 12D->4D reduction with the guarded W row",
                "recompute residual accounting and genus-3 handle pressure",
                "verify exact rehydration remains closed",
                "charge any projection-row metadata cost before compression promotion",
                "keep Ward/Slavnov-Taylor language as a guard, not a physical proof",
            ],
        },
        "claim_boundary": (
            "This applies electroweak conservation/identity research as a guard "
            "over symbolic projection retunes. It is not a W-boson conservation "
            "law, Standard Model correction, QFT calculation, or empirical claim."
        ),
        "lawful": True,
    }

    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "research_guard": receipt["research_guard"],
        "local_w_axis_signal": receipt["local_w_axis_signal"],
        "candidate_classification": receipt["candidate_classification"],
        "recommended_local_geometry": receipt["recommended_local_geometry"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_w_conservation_guard_hash_sha256"] = sha256_bytes(stable_preimage)
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
        "stable_w_conservation_guard_hash_sha256": receipt["stable_w_conservation_guard_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "w_axis_signal": receipt["local_w_axis_signal"],
        "candidate_classification": receipt["candidate_classification"],
        "recommended_local_geometry": receipt["recommended_local_geometry"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
