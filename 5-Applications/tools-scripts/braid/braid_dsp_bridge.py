#!/usr/bin/env python3
"""
Braid-DSP Bridge

Reads the standing-wave color-braid simulation CSVs and feeds them through a
Python replica of the BraidNeuromorphicTranslator logic.  This demonstrates
how the older DSP-neuromorphic translation layer can be repurposed for the
BT20 Genetic Ladder / braid-spike model.

Inputs (expected in the ingest directory):
    tip_qualified_braid_1_200_timeline.csv
    tip_qualified_braid_1_200_codons.csv

Output:
    Prints per-epoch neuromorphic state summaries and braid-processing guidance.
"""

import csv
import math
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Translator replica (Python version of 0-Core-Formalism/core/src/braid_neuromorphic_translation.rs)
# ---------------------------------------------------------------------------

class BraidFeatureRecord:
    def __init__(self, epoch_id, n, shell_geometry, color_field, codon_context):
        self.epoch_id = epoch_id
        self.n = n
        self.shell_geometry = shell_geometry      # [a, b, ab, a-b, shell]
        self.color_field = color_field            # [mass, polarity, A, T, G, C]
        self.codon_context = codon_context        # [interaction_sum, reinforced, opposed, neutral]

class NeuromorphicState:
    def __init__(self, mp, weights, thresholds, firing):
        self.membrane_potential = mp
        self.neuron_weights = weights
        self.neuron_thresholds = thresholds
        self.firing_rate = firing

class BraidGuidance:
    def __init__(self, boundary, center, resonance, neutral):
        self.mode_bias = {
            "boundary_sensitive": boundary,
            "center_sensitive": center,
            "resonance_sensitive": resonance,
            "neutral_traversal": neutral,
        }
        self.boundary_sensitive = boundary
        self.center_sensitive = center
        self.resonance_sensitive = resonance
        self.neutral_traversal = neutral

class BraidNeuromorphicTranslator:
    def __init__(self, neuron_count: int = 8, feature_dim: int = 15):
        self.neuron_count = neuron_count
        self.feature_dim = feature_dim
        self.translation_matrix = [
            [((i * 0.1 + j * 0.1) % 1.0) * 0.2 for j in range(feature_dim)]
            for i in range(neuron_count)
        ]
        self.batch_sync_counter = 0

    def braid_to_neuromorphic(self, features: BraidFeatureRecord) -> NeuromorphicState:
        combined = features.shell_geometry + features.color_field + features.codon_context
        effective_dim = min(self.feature_dim, len(combined))
        feature_mean = sum(combined[:effective_dim]) / max(1, effective_dim)

        mp = [0.0] * self.neuron_count
        weights = [0.1] * self.neuron_count
        thresholds = [0.5] * self.neuron_count
        firing = [0.0] * self.neuron_count

        for i in range(self.neuron_count):
            bias = sum(self.translation_matrix[i][:effective_dim])
            mp[i] = feature_mean * bias * 0.5
            weights[i] = 0.1 + min(0.9, abs(mp[i]) * 0.5)
            firing[i] = max(0.0, min(1.0, mp[i] / 0.5))

        return NeuromorphicState(mp, weights, thresholds, firing)

    def state_to_prior(self, state: NeuromorphicState, epoch_id: int):
        return {
            "epoch_id": epoch_id,
            "neuromorphic_prior_vector": state.membrane_potential[:],
            "candidate_mask": state.firing_rate[:],
            "proposal_weight_vector": state.neuron_weights[:],
            "lag_bias_vector": [p * 0.1 for p in state.membrane_potential],
        }

    def neuromorphic_to_braid_guidance(self, prior) -> BraidGuidance:
        pv = prior["neuromorphic_prior_vector"]
        boundary = pv[0] if len(pv) > 0 else 0.5
        center = pv[1] if len(pv) > 1 else 0.5
        resonance = pv[2] if len(pv) > 2 else 0.5
        neutral = pv[3] if len(pv) > 3 else 0.5

        total = boundary + center + resonance + neutral
        if total <= 0:
            total = 1.0

        return BraidGuidance(
            boundary / total,
            center / total,
            resonance / total,
            neutral / total,
        )

    def batch_sync(self, batch_id: int, epoch_id: int):
        self.batch_sync_counter = batch_id
        for i in range(self.neuron_count):
            for j in range(self.feature_dim):
                self.translation_matrix[i][j] *= 0.995
                self.translation_matrix[i][j] += 0.005 * (i / self.neuron_count)


# ---------------------------------------------------------------------------
# CSV ingestion
# ---------------------------------------------------------------------------

def load_timeline(path: Path):
    rows = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "n": int(r["n"]),
                "shell": int(r["shell"]),
                "a": int(r["a"]),
                "b": int(r["b"]),
                "primary_count": int(r["primary_count"]),
                "echo_count": int(r["echo_count"]),
                "eq_resonance_count": int(r["eq_resonance_count"]),
                "mirror_resonance_count": int(r["mirror_resonance_count"]),
                "total_activity": int(r["total_activity"]),
                "resonance_total": int(r["resonance_total"]),
                "event_labels": r["event_labels"],
                "resonance_types": r["resonance_types"],
                "field_class": r.get("field_class", ""),
                "interaction_sum": float(r.get("interaction_sum", 0)),
                "field_mass": float(r.get("field_mass", 0)),
                "field_polarity": float(r.get("field_polarity", 0)),
                "field_A": float(r.get("field_A", 0)),
                "field_T": float(r.get("field_T", 0)),
                "field_G": float(r.get("field_G", 0)),
                "field_C": float(r.get("field_C", 0)),
            })
    return rows


def build_features_per_shell(rows):
    """Aggregate braid features per shell (epoch)."""
    shells = defaultdict(list)
    for r in rows:
        shells[r["shell"]].append(r)

    features = []
    for shell_id in sorted(shells.keys()):
        grp = shells[shell_id]
        n_mid = grp[len(grp) // 2]["n"]

        shell_geometry = [
            sum(r["a"] for r in grp) / len(grp),
            sum(r["b"] for r in grp) / len(grp),
            sum(r["a"] * r["b"] for r in grp) / len(grp),
            sum(r["a"] - r["b"] for r in grp) / len(grp),
            float(shell_id),
        ]

        color_field = [
            sum(r["field_mass"] for r in grp) / len(grp),
            sum(r["field_polarity"] for r in grp) / len(grp),
            sum(r["field_A"] for r in grp) / len(grp),
            sum(r["field_T"] for r in grp) / len(grp),
            sum(r["field_G"] for r in grp) / len(grp),
            sum(r["field_C"] for r in grp) / len(grp),
        ]

        reinforced = sum(1 for r in grp if r.get("field_class") == "reinforced")
        opposed = sum(1 for r in grp if r.get("field_class") == "opposed")
        neutral = sum(1 for r in grp if r.get("field_class") == "neutral")

        codon_context = [
            sum(r["interaction_sum"] for r in grp) / max(1, len(grp)),
            float(reinforced),
            float(opposed),
            float(neutral),
        ]

        features.append(BraidFeatureRecord(
            epoch_id=shell_id,
            n=n_mid,
            shell_geometry=shell_geometry,
            color_field=color_field,
            codon_context=codon_context,
        ))

    return features


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ingest_dir = Path("/home/allaun/Documents/ingest")
    timeline_path = ingest_dir / "tip_qualified_braid_1_200_timeline.csv"

    if not timeline_path.exists():
        print(f"Error: {timeline_path} not found.")
        return

    rows = load_timeline(timeline_path)
    features = build_features_per_shell(rows)

    translator = BraidNeuromorphicTranslator(neuron_count=8, feature_dim=15)

    print("Braid → Neuromorphic Translation (per-shell epochs)\n")
    print(f"{'Shell':>5} | {'Boundary':>9} | {'Center':>7} | {'Resonance':>9} | {'Neutral':>7}")
    print("-" * 55)

    for feat in features:
        state = translator.braid_to_neuromorphic(feat)
        prior = translator.state_to_prior(state, feat.epoch_id)
        guidance = translator.neuromorphic_to_braid_guidance(prior)

        print(
            f"{feat.epoch_id:>5} | "
            f"{guidance.boundary_sensitive:>8.3f} | "
            f"{guidance.center_sensitive:>6.3f} | "
            f"{guidance.resonance_sensitive:>8.3f} | "
            f"{guidance.neutral_traversal:>6.3f}"
        )

        # Batch sync every 5 shells to show learning drift
        if feat.epoch_id % 5 == 0:
            translator.batch_sync(feat.epoch_id, feat.epoch_id)


if __name__ == "__main__":
    main()
