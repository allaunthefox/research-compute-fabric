#!/usr/bin/env python3
"""Logogram Chirality Route Gate.

Computes a small compatibility receipt for a logogram chirality witness.

This does not interpret glyphs semantically. It only checks whether direction,
handedness, phase, placement, and mode should become active route coordinates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def phase_distance(a: float, b: float) -> float:
    diff = abs((a - b) % 1.0)
    return min(diff, 1.0 - diff)


def compat_score(config: dict[str, Any]) -> dict[str, Any]:
    chi = config["chirality_witness"]
    target = config.get("target_chirality", {})

    weights = config.get("weights", {})
    w_hand = float(weights.get("handedness", 0.35))
    w_dir = float(weights.get("direction", 0.20))
    w_phase = float(weights.get("phase", 0.20))
    w_place = float(weights.get("placement", 0.10))
    w_mode = float(weights.get("mode", 0.15))

    handedness_match = chi.get("handedness") == target.get("handedness", chi.get("handedness"))
    direction_match = chi.get("direction") == target.get("direction", chi.get("direction"))
    placement_match = chi.get("placement") == target.get("placement", chi.get("placement"))
    mode_match = chi.get("mode") == target.get("mode", chi.get("mode"))

    phase_target = float(target.get("phase", chi.get("phase", 0.0)))
    phase = float(chi.get("phase", 0.0))
    phase_score = max(0.0, 1.0 - 2.0 * phase_distance(phase, phase_target))

    score = (
        w_hand * float(handedness_match)
        + w_dir * float(direction_match)
        + w_phase * phase_score
        + w_place * float(placement_match)
        + w_mode * float(mode_match)
    )

    threshold = float(config.get("active_route_threshold", 0.75))
    return {
        "score": score,
        "threshold": threshold,
        "decision": "route_active" if score >= threshold else "metadata_only",
        "matches": {
            "handedness": handedness_match,
            "direction": direction_match,
            "phase_score": phase_score,
            "placement": placement_match,
            "mode": mode_match,
        },
    }


def run(config: dict[str, Any]) -> dict[str, Any]:
    compatibility = compat_score(config)

    benefit = config.get("benefit_gate", {})
    beneficial = any(bool(benefit.get(k, False)) for k in [
        "disambiguates_same_payload",
        "prevents_wrong_handed_pist_transition",
        "reduces_nuvmap_false_merge",
        "improves_replay_determinism",
        "measured_route_gain_observed",
    ])

    receipt = {
        "receipt_type": "famm_logogram_chirality_witness",
        "schema_version": "0.1.0",
        "symbol_id": config["symbol_id"],
        "payload_hash": config["payload_hash"],
        "chirality_witness": config["chirality_witness"],
        "compatibility": compatibility,
        "residual_policy": config.get("residual_policy", "carry_orientation_delta_and_verify_on_replay"),
        "benefit_gate": {
            **benefit,
            "beneficial": beneficial,
            "promotion": "active_route_coordinate" if beneficial and compatibility["decision"] == "route_active" else "receipt_metadata_only",
        },
        "no_drift_boundary": (
            "Glyph/logogram orientation is not payload authority. It becomes active only "
            "when it changes admissibility, replay, NUVMAP merge safety, or measured route gain."
        ),
    }
    receipt["receipt_hash"] = sha256_json(receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    receipt = run(config)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Decision: {receipt['compatibility']['decision']}")
    print(f"Promotion: {receipt['benefit_gate']['promotion']}")
    print(f"Receipt hash: {receipt['receipt_hash']}")


if __name__ == "__main__":
    main()
