#!/usr/bin/env python3
"""
Braid Feature Mapper

Maps the standing-wave color-braid simulation CSVs into the BraidFeatureRecord
schema defined in 6-Documentation/docs/design/BT20_BRAID_FEATURE_SCHEMA_V1.md.

Inputs (expected in /home/allaun/Documents/ingest/):
    tip_qualified_braid_1_200_timeline.csv
    tip_qualified_braid_1_200_codons.csv

Output:
    braid_feature_records_1_200.csv
    One row per active event, fully populated with timing lattice fields
    and the three feature vectors.
"""

import csv
import math
from collections import defaultdict
from pathlib import Path

TIMING_SLOTS_PER_CYCLE = 8
MAX_ECHO_DEPTH = 3

CHANNEL_IDX = {"A": 0, "T": 1, "G": 2, "C": 3}
SLOT_MAP = {"A": 0, "G": 2, "C": 4, "T": 6}


def compute_codeword(event_type: str, tip_polarity: int, interaction_sum: float) -> int:
    group = {"A": 0b00, "G": 0b01, "C": 0b10, "T": 0b11}.get(event_type, 0b00)
    polarity = 1 if tip_polarity >= 0 else 0
    field_sign = 1 if interaction_sum >= 0.0 else 0
    raw = ((group & 0b11) << 2) | ((polarity & 1) << 1) | (field_sign & 1)
    parity_bit = ((raw >> 2) & 1) ^ ((raw >> 1) & 1) ^ (raw & 1)
    return (raw & 0b1110) | (parity_bit & 1)


def one_hot_color(event_type: str) -> list:
    v = [0, 0, 0, 0]
    idx = CHANNEL_IDX.get(event_type)
    if idx is not None:
        v[idx] = 1
    return v


def load_timeline(path: Path) -> list:
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


def parse_event_labels(label_str: str) -> list:
    """Parse 'A[0,-3] | G*[0,-5]' into list of tokens."""
    if not label_str.strip():
        return []
    tokens = []
    for part in label_str.split("|"):
        part = part.strip()
        if not part:
            continue
        # format: STATE[ab,a-b]  or  STATE*[ab,a-b]
        is_echo = "*" in part
        state = part[0]
        rest = part[1:].replace("*", "")
        # rest now starts with [ and ends with ]
        inner = rest.strip()[1:-1]
        ab_str, d_str = inner.split(",")
        tokens.append({
            "state": state,
            "echo": is_echo,
            "ab": int(ab_str),
            "a_minus_b": int(d_str),
        })
    return tokens


def load_codons(path: Path) -> dict:
    """Map start_n -> codon info."""
    codons = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            start_n = int(r["start_n"])
            codons[start_n] = {
                "codon": r["codon"],
                "resonance_hits": int(r["resonance_hits_in_window"]),
                "resonance_types": r["resonance_types_in_window"],
            }
    return codons


def build_feature_records(timeline_rows: list, codon_map: dict) -> list:
    records = []
    # Pre-index codons by n for quick lookup
    codon_by_n = {}
    for start_n, info in codon_map.items():
        # approximate: attach codon to the three events in that window
        codon_by_n[start_n] = info

    for row in timeline_rows:
        if row["total_activity"] == 0:
            continue

        tokens = parse_event_labels(row["event_labels"])
        for tok in tokens:
            state = tok["state"]
            ab = tok["ab"]
            a_minus_b = tok["a_minus_b"]
            interaction = row["interaction_sum"]
            kind = "echo" if tok["echo"] else "primary"

            slot = SLOT_MAP.get(state, 0)
            # Echoes get the adjacent odd slot behind the primary
            if kind == "echo":
                slot = min(TIMING_SLOTS_PER_CYCLE - 1, slot + 1)

            codeword = compute_codeword(state, a_minus_b, interaction)
            parity_bit = codeword & 1

            color = one_hot_color(state)
            if kind == "echo":
                # Standing-wave echo inverts the color contribution
                color = [-c for c in color]

            # Resonance flags
            eq_flag = row["eq_resonance_count"] > 0
            mir_flag = row["mirror_resonance_count"] > 0
            rein_flag = row["field_class"] == "reinforced"
            cross_flag = kind == "echo"

            # Codon context: try to find the codon window starting near this n
            ctx = codon_by_n.get(row["n"], {})
            codon_tokens = ctx.get("codon", "").split()
            codon_ctx = [0, 0, 0]
            for i, ct in enumerate(codon_tokens[:3]):
                # simple hash: use ascii sum mod 64
                codon_ctx[i] = sum(ord(c) for c in ct) % 64

            geometry = [
                float(row["a"]),
                float(row["b"]),
                float(ab),
                float(a_minus_b),
                interaction,
                float(row["shell"]) / 20.0,
                0.0,  # timing_phase normalized later
            ]

            field = [
                row["field_A"],
                row["field_T"],
                row["field_G"],
                row["field_C"],
                row["field_mass"],
                row["field_polarity"],
                float(parity_bit),
                1.0 / TIMING_SLOTS_PER_CYCLE,
            ]

            rarity = 1.0 / max(1, ctx.get("resonance_hits", 0) + 1)
            code_vec = [
                float(row["resonance_total"]),
                rarity,
                0.0,  # slot_entropy placeholder
                1.0,  # timing_confidence
                float(codeword) / 31.0,
            ]

            records.append({
                "chunk_id": row["shell"],
                "shell_id": row["shell"],
                "event_n": row["n"],
                "event_type": state,
                "event_kind": kind,
                "timing_slot": slot,
                "timing_phase": 0,
                "timing_jitter_budget": 1,
                "timing_parity_bit": parity_bit,
                "timing_codeword": codeword,
                "tip_mass": ab,
                "tip_polarity": a_minus_b,
                "color_A": color[0],
                "color_T": color[1],
                "color_G": color[2],
                "color_C": color[3],
                "field_mass": row["field_mass"],
                "field_polarity": row["field_polarity"],
                "field_A": row["field_A"],
                "field_T": row["field_T"],
                "field_G": row["field_G"],
                "field_C": row["field_C"],
                "interaction_sum": interaction,
                "codon_ctx_0": codon_ctx[0],
                "codon_ctx_1": codon_ctx[1],
                "codon_ctx_2": codon_ctx[2],
                "res_eq": int(eq_flag),
                "res_mirror": int(mir_flag),
                "res_reinforced": int(rein_flag),
                "res_cross_shell": int(cross_flag),
                "geometry_vector": ";".join(f"{x:.4f}" for x in geometry),
                "field_vector": ";".join(f"{x:.4f}" for x in field),
                "code_vector": ";".join(f"{x:.4f}" for x in code_vec),
            })

    return records


def main():
    ingest_dir = Path("/home/allaun/Documents/ingest")
    timeline_path = ingest_dir / "tip_qualified_braid_1_200_timeline.csv"
    codon_path = ingest_dir / "tip_qualified_braid_1_200_codons.csv"
    output_path = Path("/home/allaun/Documents/Research Stack/data/benchmarks/braid_feature_records_1_200.csv")

    if not timeline_path.exists():
        print(f"Error: {timeline_path} not found.")
        return
    if not codon_path.exists():
        print(f"Warning: {codon_path} not found; codon context will be empty.")

    timeline = load_timeline(timeline_path)
    codons = load_codons(codon_path) if codon_path.exists() else {}

    records = build_feature_records(timeline, codons)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "chunk_id", "shell_id", "event_n", "event_type", "event_kind",
        "timing_slot", "timing_phase", "timing_jitter_budget", "timing_parity_bit", "timing_codeword",
        "tip_mass", "tip_polarity",
        "color_A", "color_T", "color_G", "color_C",
        "field_mass", "field_polarity", "field_A", "field_T", "field_G", "field_C",
        "interaction_sum",
        "codon_ctx_0", "codon_ctx_1", "codon_ctx_2",
        "res_eq", "res_mirror", "res_reinforced", "res_cross_shell",
        "geometry_vector", "field_vector", "code_vector",
    ]

    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records)} BraidFeatureRecords to {output_path}")

    # Quick stats
    primary = sum(1 for r in records if r["event_kind"] == "primary")
    echoes = sum(1 for r in records if r["event_kind"] == "echo")
    print(f"  Primary events: {primary}")
    print(f"  Echo events: {echoes}")

    codewords = defaultdict(int)
    for r in records:
        codewords[r["timing_codeword"]] += 1
    print(f"  Unique codewords: {len(codewords)}")
    for cw, cnt in sorted(codewords.items()):
        print(f"    codeword {cw:02b}/{cw}: {cnt}")


if __name__ == "__main__":
    main()
