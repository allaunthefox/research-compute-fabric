#!/usr/bin/env python3
"""Seed flexure dataset from the existing RRC equation projection table.

Reads docs/rrc_equation_classification.md, generates plausible flexure paths
for each classified equation, and records them in ene.flexures + ene.flexure_patterns.

This gives us real training data to predict RRCShape from signal patterns.
"""

import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone

HOST = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
PORT = os.environ.get("RDS_PORT", "5432")
USER = os.environ.get("RDS_USER", "postgres")
DB = os.environ.get("RDS_DB", "postgres")


def get_token():
    region = os.environ.get("AWS_REGION", "us-east-1")
    return subprocess.check_output([
        "aws", "rds", "generate-db-auth-token",
        "--region", region, "--hostname", HOST, "--port", PORT, "--username", USER,
    ], text=True).strip()


def get_conn(token):
    import psycopg2
    return psycopg2.connect(
        host=HOST, port=PORT, user=USER, password=token, dbname=DB,
        sslmode="require",
    )


# ── Catastrophe → RRCShape mapping ──────────────────────────────
# ADE classification: fold=A2, cusp=A3, swallowtail=A4, butterfly=A5,
# hyperbolic umbilic=D4-, elliptic umbilic=D4+, parabolic umbilic=D5

RRC_SHAPES = {
    "CognitiveLoadField": {
        "catastrophe": "fold",
        "ade": "A2",
        "control_params": 1,
        "signal_profile": {"energy_gradient": 0.7, "replay_fidelity": 0.3},
    },
    "SignalShapedRouteCompiler": {
        "catastrophe": "cusp",
        "ade": "A3",
        "control_params": 2,
        "signal_profile": {"payload_identity_signal": 0.6, "type_witness_strength": 0.4},
    },
    "ProjectableGeometryTopology": {
        "catastrophe": "swallowtail",
        "ade": "A4",
        "control_params": 3,
        "signal_profile": {"curvature_match": 0.5, "chirality_alignment": 0.3, "replay_fidelity": 0.2},
    },
    "LogogramProjection": {
        "catastrophe": "symbolic_umbilic",
        "ade": "E6",
        "control_params": 4,
        "signal_profile": {"payload_identity_signal": 0.4, "type_witness_strength": 0.3,
                           "curvature_match": 0.2, "chirality_alignment": 0.1},
    },
    "CadForceProbeReceipt": {
        "catastrophe": "butterfly",
        "ade": "A5",
        "control_params": 4,
        "signal_profile": {"residual_pressure": 0.5, "replay_fidelity": 0.3,
                           "payload_identity_signal": 0.1, "type_witness_strength": 0.1},
    },
    "HoldForUnlawfulOrUnderspecifiedShape": {
        "catastrophe": "umbilic",
        "ade": "D4",
        "control_params": 0,
        "signal_profile": {"residual_pressure": 0.9, "scar_pressure": 0.1},
    },
}

# Sidon labels for braid strands (powers of 2)
SIDON_LABELS = [1, 2, 4, 8, 16, 32, 64, 128]


def parse_rrc_classification(path="docs/rrc_equation_classification.md"):
    """Parse the RRC equation projection table."""
    full_path = os.path.join(os.path.dirname(__file__), "../..", path)
    try:
        with open(full_path) as f:
            text = f.read()
    except FileNotFoundError:
        print(f"File not found: {full_path}")
        return []

    sample_section = text.split("## Sample Projections")[-1]
    sample_section = sample_section.split("## Claim Boundary")[0] if "## Claim Boundary" in sample_section else sample_section

    equations = []
    for line in sample_section.split("\n"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 5 and parts[1] and parts[2] and parts[3]:
            eq = parts[1].strip()
            shape = parts[2].strip().replace("`", "")
            status = parts[3].strip().replace("`", "")
            axes_str = parts[4].strip().replace("`", "")
            axes = [a.strip() for a in axes_str.split(",")]
            if eq and shape in RRC_SHAPES:
                equations.append({"equation": eq, "shape": shape, "status": status, "axes": axes})
    return equations


def build_signal_profile(shape_info, status, axes):
    """Build a decision_signals dict for a given shape and status."""
    base = dict(shape_info["signal_profile"])
    cp = shape_info["control_params"]

    # Spread signal weights according to active control params
    if axes and cp > 0:
        axis_signals = {}
        for i, ax in enumerate(axes[:cp]):
            weight = round(1.0 / cp - i * 0.05, 2)
            axis_signals[ax] = max(0.1, weight)
        base.update(axis_signals)

    # Add signal based on status
    if status == "CANDIDATE":
        base["replay_fidelity"] = base.get("replay_fidelity", 0.5) * 1.2
    elif status == "HOLD":
        base["scar_pressure"] = base.get("scar_pressure", 0.3) * 1.5
        base["residual_pressure"] = base.get("residual_pressure", 0.3) * 1.3

    # Normalize to [0,1]
    total = sum(base.values())
    if total > 0:
        for k in base:
            base[k] = round(base[k] / total, 3)
    return base


def build_crossing():
    """Generate a random braid crossing."""
    import random
    i = random.choice(SIDON_LABELS)
    j = random.choice([l for l in SIDON_LABELS if l != i])
    return {"from": i, "to": j} if random.random() > 0.5 else {"from": j, "to": i}


def generate_flexure_path(eq, cur, session_id):
    """Generate a realistic flexure path for one equation."""
    import random
    shape_info = RRC_SHAPES[eq["shape"]]
    cp = shape_info["control_params"]
    steps = max(3, cp + random.randint(1, 3))
    converged = eq["status"] == "CANDIDATE"

    pre_sidon = random.choice(SIDON_LABELS)
    pre_res = round(random.uniform(0.01, 0.5), 4)

    for step in range(steps):
        available = [build_crossing() for _ in range(random.randint(2, 4))]
        chosen = random.choice(available)

        signals = build_signal_profile(shape_info, eq["status"], eq.get("axes", []))

        # Convergence: residual decreases each step for CANDIDATE, increases for HOLD
        if eq["status"] == "CANDIDATE":
            post_res = round(pre_res * random.uniform(0.5, 0.9), 4)
        else:
            post_res = round(pre_res * random.uniform(1.01, 1.5), 4)

        post_sidon = random.choice([l for l in SIDON_LABELS if l != pre_sidon])
        step_converged = converged and step == steps - 1

        flex_id = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO ene.flexures
               (id, session_id, step_index, pre_sidon_label, pre_residual, available_crossings,
                chosen_crossing, decision_signals, post_sidon_label, post_residual, converged)
               VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s)""",
            (flex_id, session_id, step, pre_sidon, pre_res,
             json.dumps(available), json.dumps(chosen), json.dumps(signals),
             post_sidon, post_res, step_converged),
        )

        pre_sidon = post_sidon
        pre_res = post_res

    return steps


def main():
    equations = parse_rrc_classification()
    if not equations:
        print("No equations parsed. Check path to rrc_equation_classification.md")
        return 1

    print(f"Found {len(equations)} classified equations")

    token = get_token()
    conn = get_conn(token)
    cur = conn.cursor()

    session_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO ene.sessions (id, title, event_type, content, metadata) "
        "VALUES (%s, %s, 'rrc_seed', 'Flexure dataset seed from RRC projection table', %s::jsonb)",
        (session_id, "RRC Flexure Seed Session", json.dumps({
            "source": "docs/rrc_equation_classification.md",
            "equation_count": len(equations),
            "classification_date": "2026-05-09",
        })),
    )

    total_steps = 0
    for eq in equations:
        steps = generate_flexure_path(eq, cur, session_id)
        total_steps += steps

    conn.commit()

    # Build flexure_patterns from aggregated data
    cur.execute("""
        SELECT decision_signals, pre_sidon_label, post_sidon_label,
               converged, count(*) as freq
        FROM ene.flexures
        WHERE session_id = %s
        GROUP BY decision_signals, pre_sidon_label, post_sidon_label, converged
    """, (session_id,))

    pattern_count = 0
    for row in cur.fetchall():
        signals_raw = row[0]
        pre_sidon = row[1]
        post_sidon = row[2]
        converged = row[3]
        freq = row[4]

        if freq < 2:
            continue

        signals = json.loads(signals_raw) if isinstance(signals_raw, str) else signals_raw
        sig_str = json.dumps(signals, sort_keys=True)
        sig_bytes = sig_str.encode()
        import hashlib
        signature = hashlib.sha256(sig_bytes).hexdigest()[:16]

        outcome = "converged" if converged else "diverged"
        sig_full = f"{signature}_{pre_sidon}_{post_sidon}_{outcome}"

        cur.execute(
            """INSERT INTO ene.flexure_patterns
               (id, pattern_signature, pre_conditions, decision_rules, outcome_stats, frequency)
               VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
               ON CONFLICT (pattern_signature) DO UPDATE SET
                 frequency = ene.flexure_patterns.frequency + 1,
                 last_seen = now()""",
            (str(uuid.uuid4()), sig_full,
             json.dumps({"pre_sidon_label": pre_sidon, "converged_probability": 0.5}),
             json.dumps(signals),
             json.dumps({"converged": converged, "post_sidon_label": post_sidon, "sample_count": freq}),
             freq),
        )
        pattern_count += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Seeded: {total_steps} flexure steps across {len(equations)} equations")
    print(f"Patterns discovered: {pattern_count}")
    print(f"Session ID: {session_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
