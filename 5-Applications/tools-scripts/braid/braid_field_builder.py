#!/usr/bin/env python3
"""
Braid Field Builder v3

Reads the tip-qualified braid simulation CSV and computes:
1. Real standing-wave rear residues from future events
2. Populated FieldCoord (mass, polarity, color channels)
3. Nonzero interaction scores with shell-dependent normalization
4. Homeostatic bias via sliding-window mean subtraction
5. Active timing code (slot, dynamic phase, parity, jitter, continuous priority)
6. Codon window grouping that respects shell boundaries
7. Plain-language explanations

Outputs:
    braid_explained_events_1_200.csv
    braid_glossary.csv
    braid_field_interaction.png
"""

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

TIMING_SLOTS = 8
ECHO_DEPTH = 3
ECHO_WEIGHTS = {1: -1.0, 2: -0.5, 3: -0.25}
SLOT_MAP = {"A": 0, "G": 2, "C": 4, "T": 6}
CHANNEL_IDX = {"A": 0, "T": 1, "G": 2, "C": 3}
PHASE_CLIP = 3  # max |phase| in ticks
INTERACTION_SCALE = 64.0  # tanh scaling denominator
HOMEOSTATIC_WINDOW = 7  # sliding window size for mean subtraction


def parse_event_labels(label_str: str) -> list:
    if not label_str.strip():
        return []
    tokens = []
    for part in label_str.split("|"):
        part = part.strip()
        if not part:
            continue
        is_echo = "*" in part
        state = part[0]
        rest = part[1:].replace("*", "")
        inner = rest.strip()[1:-1]
        ab_str, d_str = inner.split(",")
        tokens.append({
            "state": state,
            "echo": is_echo,
            "ab": int(ab_str),
            "a_minus_b": int(d_str),
        })
    return tokens


def load_active_events(path: Path) -> list:
    rows = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if int(r["total_activity"]) == 0:
                continue
            rows.append({
                "n": int(r["n"]),
                "shell": int(r["shell"]),
                "a": int(r["a"]),
                "b": int(r["b"]),
                "event_labels": r["event_labels"],
                "field_class": r.get("field_class", ""),
                "interaction_sum": float(r.get("interaction_sum", 0)),
            })
    return rows


def build_standalone_active_events(timeline_rows: list) -> list:
    events = []
    for row in timeline_rows:
        tokens = parse_event_labels(row["event_labels"])
        for tok in tokens:
            events.append({
                "n": row["n"],
                "shell": row["shell"],
                "a": row["a"],
                "b": row["b"],
                "state": tok["state"],
                "echo": tok["echo"],
                "ab": tok["ab"],
                "a_minus_b": tok["a_minus_b"],
            })
    return events


def compute_field(events: list) -> dict:
    field = defaultdict(lambda: {
        "mass": 0.0,
        "polarity": 0.0,
        "A": 0.0,
        "T": 0.0,
        "G": 0.0,
        "C": 0.0,
        "sources": [],
    })

    for ev in events:
        n0 = ev["n"]
        tip_mass = float(ev["ab"])
        tip_polarity = float(ev["a_minus_b"])
        color = [0.0, 0.0, 0.0, 0.0]
        idx = CHANNEL_IDX[ev["state"]]
        weight = 1.0 if not ev["echo"] else -1.0
        color[idx] = weight

        for d, alpha in ECHO_WEIGHTS.items():
            target = n0 - d
            if target < 1:
                continue
            field[target]["mass"] += alpha * tip_mass
            field[target]["polarity"] += alpha * tip_polarity
            field[target]["A"] += alpha * color[0]
            field[target]["T"] += alpha * color[1]
            field[target]["G"] += alpha * color[2]
            field[target]["C"] += alpha * color[3]
            field[target]["sources"].append(f"{ev['state']}{'*' if ev['echo'] else ''}@{n0}×{alpha}")

    return field


def compute_codeword(state: str, a_minus_b: int, interaction: float) -> int:
    group = {"A": 0b00, "G": 0b01, "C": 0b10, "T": 0b11}.get(state, 0b00)
    polarity = 1 if a_minus_b >= 0 else 0
    field_sign = 1 if interaction >= 0.0 else 0
    raw = ((group & 0b11) << 2) | ((polarity & 1) << 1) | (field_sign & 1)
    # Fixed parity: XOR of data bits (bits 3,2,1) so the 4-bit codeword has even popcount.
    parity = ((raw >> 3) & 1) ^ ((raw >> 2) & 1) ^ ((raw >> 1) & 1)
    return (raw & 0b1110) | (parity & 1)


def compute_phase(polarity: int, shell_width: int, interaction: float) -> int:
    """
    Active timing phase derived from normalized tip polarity and
    scaled interaction magnitude.
    """
    pol_term = 3.0 * polarity / max(1, shell_width)
    int_term = 2.0 * math.tanh(interaction / INTERACTION_SCALE)
    phase = round(pol_term + int_term)
    return max(-PHASE_CLIP, min(PHASE_CLIP, int(phase)))


def compute_priority(interaction: float) -> float:
    """Continuous priority in [-1, 1] using tanh."""
    return math.tanh(interaction / INTERACTION_SCALE)


def compute_index_bit(priority: float) -> int:
    """Binary index bit derived from continuous priority."""
    return 1 if priority > 0.0 else 0


def explain_event(row: dict) -> str:
    state = row["state"]
    n = row["n"]
    shell = row["shell"]
    ab = row["ab"]
    d = row["a_minus_b"]
    kind = "echo" if row["echo"] else "primary"
    timing = row["timing_slot"]
    phase = row["timing_phase"]
    interaction = row["interaction"]
    classification = row["field_class"]
    codon_win = row["codon_window_id"]
    pos = row["codon_position"]
    priority = row["priority"]

    meaning = {
        "A": "boundary-in (square entry)",
        "G": "center-left (shell axis left)",
        "C": "center-right (shell axis right)",
        "T": "boundary-out (square exit)",
    }.get(state, "unknown")

    if classification == "reinforced":
        class_desc = "amplified by the local standing-wave field"
    elif classification == "opposed":
        class_desc = "suppressed by the local standing-wave field"
    else:
        class_desc = "unaffected by the local standing-wave field"

    priority_label = "high-priority" if priority > 0 else "low-priority"

    return (
        f"At integer {n} (shell {shell}), a {kind} {meaning} event occurs "
        f"in timing slot {timing} phase {phase:+d} with tip mass {ab} and polarity {d}. "
        f"It belongs to codon window {codon_win} at position {pos}. "
        f"The event is {class_desc} (interaction={interaction:.2f}) and carries {priority_label} "
        f"(priority={priority:.3f})."
    )


def build_explained_csv(events: list, field: dict) -> list:
    # First pass: compute raw interactions for sliding-window mean
    raw_interactions = []
    for ev in events:
        n = ev["n"]
        f = field.get(n, {
            "mass": 0.0, "polarity": 0.0,
            "A": 0.0, "T": 0.0, "G": 0.0, "C": 0.0, "sources": []
        })
        tip_mass = ev["ab"]
        tip_polarity = ev["a_minus_b"]
        color = [0, 0, 0, 0]
        color[CHANNEL_IDX[ev["state"]]] = 1 if not ev["echo"] else -1

        interaction = (
            tip_mass * f["mass"] +
            tip_polarity * f["polarity"] +
            sum(color[i] * [f["A"], f["T"], f["G"], f["C"]][i] for i in range(4))
        )
        raw_interactions.append(interaction)

    # Compute sliding-window means for homeostatic bias
    homeostatic_means = []
    for i in range(len(raw_interactions)):
        window = raw_interactions[max(0, i - HOMEOSTATIC_WINDOW // 2)
                                  :min(len(raw_interactions), i + HOMEOSTATIC_WINDOW // 2 + 1)]
        homeostatic_means.append(sum(window) / len(window))

    # Second pass: build rows with shell-respecting codon windows
    rows = []
    shell_counters = defaultdict(int)  # tracks event index per shell

    for idx, ev in enumerate(events):
        n = ev["n"]
        f = field.get(n, {
            "mass": 0.0, "polarity": 0.0,
            "A": 0.0, "T": 0.0, "G": 0.0, "C": 0.0, "sources": []
        })

        tip_mass = ev["ab"]
        tip_polarity = ev["a_minus_b"]
        color = [0, 0, 0, 0]
        color[CHANNEL_IDX[ev["state"]]] = 1 if not ev["echo"] else -1

        raw_interaction = raw_interactions[idx]
        # Homeostatic bias: subtract local mean so the distribution centers around 0
        interaction = raw_interaction - homeostatic_means[idx]

        if interaction > 0:
            field_class = "reinforced"
        elif interaction < 0:
            field_class = "opposed"
        else:
            field_class = "neutral"

        shell_width = 2 * ev["shell"] + 1
        phase = compute_phase(tip_polarity, shell_width, interaction)
        priority = compute_priority(interaction)
        idx_bit = compute_index_bit(priority)

        # Shell-respecting codon window: reset counter at every shell boundary
        shell = ev["shell"]
        shell_local_idx = shell_counters[shell]
        codon_win = shell_local_idx // 3
        codon_pos = shell_local_idx % 3
        shell_counters[shell] += 1

        slot = SLOT_MAP[ev["state"]]
        if ev["echo"]:
            slot = min(TIMING_SLOTS - 1, slot + 1)

        codeword = compute_codeword(ev["state"], tip_polarity, interaction)
        parity = codeword & 1

        rows.append({
            "active_index": idx,
            "n": n,
            "shell": ev["shell"],
            "state": ev["state"],
            "kind": "echo" if ev["echo"] else "primary",
            "a": ev["a"],
            "b": ev["b"],
            "ab": tip_mass,
            "a_minus_b": tip_polarity,
            "timing_slot": slot,
            "timing_phase": phase,
            "timing_jitter_budget": 1,
            "parity_bit": parity,
            "codeword": codeword,
            "priority": round(priority, 6),
            "index_bit": idx_bit,
            "codon_window_id": codon_win,
            "codon_position": codon_pos,
            "field_mass": round(f["mass"], 4),
            "field_polarity": round(f["polarity"], 4),
            "field_A": round(f["A"], 4),
            "field_T": round(f["T"], 4),
            "field_G": round(f["G"], 4),
            "field_C": round(f["C"], 4),
            "raw_interaction": round(raw_interaction, 4),
            "interaction": round(interaction, 4),
            "field_class": field_class,
            "field_sources": " | ".join(f["sources"]),
            "explanation": explain_event({
                "state": ev["state"], "n": n, "shell": ev["shell"],
                "ab": tip_mass, "a_minus_b": tip_polarity,
                "echo": ev["echo"], "timing_slot": slot, "timing_phase": phase,
                "field_class": field_class, "interaction": interaction,
                "codon_window_id": codon_win, "codon_position": codon_pos,
                "priority": priority,
            }),
        })

    return rows


def build_glossary() -> list:
    return [
        {"term_id": "G01", "term": "shell", "definition": "The integer floor of sqrt(n), denoted k(n). Defines the square bracket surrounding n."},
        {"term_id": "G02", "term": "timing_slot", "definition": "The micro-lane within an 8-slot cycle assigned to an event type (A=0, G=2, C=4, T=6)."},
        {"term_id": "G03", "term": "timing_phase", "definition": "Active fine offset inside the timing slot, derived from normalized tip polarity and interaction magnitude."},
        {"term_id": "G04", "term": "parity_bit", "definition": "Single-bit error-detecting code computed as XOR of event group, polarity, and field sign."},
        {"term_id": "G05", "term": "jitter_budget", "definition": "Maximum allowable slot displacement before the event is considered out-of-bound or erroneous."},
        {"term_id": "G06", "term": "codon_window_id", "definition": "Index of the 3-event triplet grouping within a single shell (resets at shell boundaries)."},
        {"term_id": "G07", "term": "tip_mass", "definition": "The product a·b, measuring shell-internal interaction magnitude."},
        {"term_id": "G08", "term": "tip_polarity", "definition": "The difference a−b, measuring axial asymmetry or directional bias."},
        {"term_id": "G09", "term": "standing-wave field", "definition": "Accumulated backward echoes from future events, decaying as −1, −½, −¼."},
        {"term_id": "G10", "term": "interaction", "definition": "Dot product of the event's tip/color state against the local standing-wave field, after homeostatic mean subtraction."},
        {"term_id": "G11", "term": "field_class", "definition": "Classification of the event based on interaction sign: reinforced (>0), opposed (<0), or neutral (=0)."},
        {"term_id": "G12", "term": "codeword", "definition": "Compact 5-bit temporal symbol encoding event group, polarity, field sign, and parity."},
        {"term_id": "G13", "term": "priority", "definition": "Continuous priority score tanh(interaction/τ) in [-1, 1]. Maps to binary index_bit for hardware."},
        {"term_id": "G14", "term": "homeostatic_bias", "definition": "Sliding-window mean subtraction that recenters the interaction distribution to ~50% reinforced/opposed."},
        {"term_id": "G15", "term": "RSCU/CAI", "definition": "Recommended codon usage normalization (Relative Synonymous Codon Usage / Codon Adaptation Index) for organism-specific tables."},
    ]


def main():
    ingest_dir = Path("/home/allaun/Documents/ingest")
    timeline_path = ingest_dir / "tip_qualified_braid_1_200_timeline.csv"
    out_dir = Path("/home/allaun/Documents/Research Stack/data/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)

    explained_path = out_dir / "braid_explained_events_1_200.csv"
    glossary_path = out_dir / "braid_glossary.csv"
    plot_path = out_dir / "braid_field_interaction.png"

    if not timeline_path.exists():
        print(f"Error: {timeline_path} not found.")
        return

    timeline = load_active_events(timeline_path)
    events = build_standalone_active_events(timeline)
    field = compute_field(events)
    explained = build_explained_csv(events, field)
    glossary = build_glossary()

    fieldnames = [
        "active_index", "n", "shell", "state", "kind",
        "a", "b", "ab", "a_minus_b",
        "timing_slot", "timing_phase", "timing_jitter_budget", "parity_bit", "codeword",
        "priority", "index_bit",
        "codon_window_id", "codon_position",
        "field_mass", "field_polarity", "field_A", "field_T", "field_G", "field_C",
        "raw_interaction", "interaction", "field_class", "field_sources", "explanation"
    ]
    with explained_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(explained)

    with glossary_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["term_id", "term", "definition"])
        writer.writeheader()
        writer.writerows(glossary)

    # Plot
    ns = [r["n"] for r in explained]
    interactions = [r["interaction"] for r in explained]
    classes = [r["field_class"] for r in explained]
    colors = {"reinforced": "green", "opposed": "red", "neutral": "gray"}
    point_colors = [colors.get(c, "black") for c in classes]

    plt.figure(figsize=(12, 5))
    plt.scatter(ns, interactions, c=point_colors, s=30, alpha=0.8)
    plt.axhline(0, color="black", linewidth=0.5)
    plt.xlabel("Integer n")
    plt.ylabel("Homeostatic interaction score")
    plt.title("Standing-wave field interaction for active braid events (1–200)")
    plt.tight_layout()
    plt.savefig(plot_path, dpi=180, bbox_inches="tight")

    print(f"Wrote {len(explained)} explained events to {explained_path}")
    print(f"Wrote {len(glossary)} glossary terms to {glossary_path}")
    print(f"Wrote interaction plot to {plot_path}")

    reinforced = sum(1 for r in explained if r["field_class"] == "reinforced")
    opposed = sum(1 for r in explained if r["field_class"] == "opposed")
    neutral = sum(1 for r in explained if r["field_class"] == "neutral")
    high_priority = sum(1 for r in explained if r["index_bit"] == 1)
    print(f"\nClass breakdown: reinforced={reinforced}, opposed={opposed}, neutral={neutral}")
    print(f"Priority breakdown: high={high_priority}, low={len(explained)-high_priority}")

    print("\n--- Sample explanations ---")
    for r in explained[:5]:
        print(f"[{r['state']} n={r['n']}] {r['explanation']}")


if __name__ == "__main__":
    main()
