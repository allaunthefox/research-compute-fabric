#!/usr/bin/env python3
"""16D Chaos Game Field Shrinker.

A FAMM-weighted lifted chaos game over 16D shortcut anchors.

This runner does not prove coverage or optimality. It shrinks a route/search
field toward attractor basins and emits a computational receipt for handoff to
exact gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def as_vec16(value: list[float], name: str) -> np.ndarray:
    arr = np.array(value, dtype=float)
    if arr.shape != (16,):
        raise ValueError(f"{name} must be a length-16 vector")
    return arr


def softmax_sample(logits: np.ndarray, rng: np.random.Generator) -> int:
    z = logits - np.max(logits)
    probs = np.exp(z)
    probs = probs / np.sum(probs)
    return int(rng.choice(len(logits), p=probs))


def contraction_matrix(anchor: dict[str, Any]) -> np.ndarray:
    c = anchor.get("contraction", 0.5)
    if isinstance(c, (int, float)):
        return np.eye(16) * float(c)

    arr = np.array(c, dtype=float)
    if arr.shape == (16,):
        return np.diag(arr)
    if arr.shape == (16, 16):
        return arr
    raise ValueError("contraction must be scalar, length-16 diagonal, or 16x16 matrix")


def anchor_logits(
    state: np.ndarray,
    anchors: list[dict[str, Any]],
    weights: dict[str, float],
    prev_anchor: str | None,
    transition_scars: dict[str, float],
) -> np.ndarray:
    out = []
    for a in anchors:
        vec = as_vec16(a["vector"], f"anchor {a.get('id', '<unknown>')}")
        dist = float(np.linalg.norm(state - vec))
        scar = float(a.get("scar", 0.0))
        invariant = float(a.get("invariant_overlap", 0.0))
        cost = float(a.get("cost", 0.0))
        mass = float(a.get("semantic_mass", 0.0))
        receipt = float(a.get("receipt_strength", 0.0))

        transition_penalty = 0.0
        if prev_anchor is not None:
            key = f"{prev_anchor}->{a.get('id')}"
            transition_penalty = float(transition_scars.get(key, 0.0))

        logit = (
            -float(weights.get("alpha_distance", 1.0)) * dist
            -float(weights.get("beta_scar", 1.0)) * scar
            + float(weights.get("gamma_invariant", 1.0)) * invariant
            - float(weights.get("eta_cost", 1.0)) * cost
            + float(weights.get("lambda_mass", 1.0)) * mass
            + float(weights.get("rho_receipt", 1.0)) * receipt
            - float(weights.get("tau_transition_scar", 1.0)) * transition_penalty
        )
        out.append(logit)
    return np.array(out, dtype=float)


def run(config: dict[str, Any]) -> dict[str, Any]:
    rng = np.random.default_rng(int(config.get("seed", 0)))
    state = as_vec16(config["initial_state"], "initial_state")
    anchors = config["anchors"]
    weights = config.get("weights", {})
    transition_scars = config.get("transition_scars", {})
    steps = int(config.get("steps", 2048))
    burn_in = int(config.get("burn_in", 128))
    noise_scale = float(config.get("noise_scale", 0.0))
    projection_axes = config.get("projection_axes", [0, 1])

    if len(projection_axes) != 2:
        raise ValueError("projection_axes must have length 2")

    orbit_hash_samples = []
    projection_hash_samples = []
    selected_counts: dict[str, int] = {}
    transition_counts: dict[str, int] = {}
    prev_id: str | None = None

    for t in range(steps):
        logits = anchor_logits(state, anchors, weights, prev_id, transition_scars)
        idx = softmax_sample(logits, rng)
        anchor = anchors[idx]
        anchor_id = str(anchor["id"])
        avec = as_vec16(anchor["vector"], f"anchor {anchor_id}")
        contraction = contraction_matrix(anchor)

        eps = rng.normal(0.0, noise_scale, size=16) if noise_scale > 0 else np.zeros(16)
        state = avec + contraction @ (state - avec) + eps

        selected_counts[anchor_id] = selected_counts.get(anchor_id, 0) + 1
        if prev_id is not None:
            key = f"{prev_id}->{anchor_id}"
            transition_counts[key] = transition_counts.get(key, 0) + 1
        prev_id = anchor_id

        if t >= burn_in:
            orbit_hash_samples.append([round(float(x), 8) for x in state.tolist()])
            projection_hash_samples.append([
                round(float(state[int(projection_axes[0])]), 8),
                round(float(state[int(projection_axes[1])]), 8),
            ])

    final_logits = anchor_logits(state, anchors, weights, prev_id, transition_scars)
    z = final_logits - np.max(final_logits)
    final_probs = np.exp(z) / np.sum(np.exp(z))

    route_recommendations = []
    for anchor, prob, logit in sorted(zip(anchors, final_probs, final_logits), key=lambda x: float(x[1]), reverse=True):
        route_recommendations.append({
            "anchor_id": anchor["id"],
            "probability": float(prob),
            "logit": float(logit),
            "handoff_gate": anchor.get("handoff_gate", "manual_review"),
        })

    receipt = {
        "receipt_type": "famm_16d_chaos_game_field_shrinker_receipt",
        "schema_version": "0.1.0",
        "basis_layer": "16D_CHAOS_GAME_FIELD_SHRINKER",
        "seed": int(config.get("seed", 0)),
        "steps": steps,
        "burn_in": burn_in,
        "projection_axes": projection_axes,
        "anchor_count": len(anchors),
        "selected_counts": selected_counts,
        "transition_counts": transition_counts,
        "orbit_sha256": sha256_json(orbit_hash_samples),
        "projection_sha256": sha256_json(projection_hash_samples),
        "final_state": [float(x) for x in state.tolist()],
        "final_projection": [
            float(state[int(projection_axes[0])]),
            float(state[int(projection_axes[1])]),
        ],
        "route_recommendations": route_recommendations,
        "no_drift_boundary": (
            "This is a computational field-shrinking receipt. It proposes attractor basins "
            "and route candidates; it is not proof and must hand off to exact gates."
        ),
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    receipt = run(cfg)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    top = receipt["route_recommendations"][0] if receipt["route_recommendations"] else None
    print(f"Wrote {out_path}")
    if top:
        print(f"Top anchor: {top['anchor_id']} p={top['probability']:.4f} handoff={top['handoff_gate']}")
    print(f"Projection SHA-256: {receipt['projection_sha256']}")
    print(f"Receipt SHA-256: {receipt['receipt_sha256']}")


if __name__ == "__main__":
    main()
