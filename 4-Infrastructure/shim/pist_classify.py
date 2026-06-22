#!/usr/bin/env python3
# INFRA:DEAD rds -- AWS RDS is gone. Any file referencing rds_connect.py or this hostname is stale and must be ported.
"""Classify a proof receipt via PIST and insert into RDS.

Usage:
    pist-classify receipt.json [--dry-run]
"""

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

from rds_connect import connect_rds

PIST_DECOMPOSE = os.environ.get(
    "PIST_DECOMPOSE_BIN",
    "/home/allaun/.local/share/opencode/worktree/"
    "0b42981cf7f7d5e172b1e93f8d4bb64a3dd63962/Turn-and-Burn/infra/rust/"
    "ene-rds/target/release/pist-decompose",
)


def classify(receipt_path: str, num_leaves: int = 8) -> dict:
    """Run pist-decompose on a receipt JSON."""
    result = subprocess.run(
        [PIST_DECOMPOSE, receipt_path, "--num-leaves", str(num_leaves)],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pist-decompose failed: {result.stderr}")
    return json.loads(result.stdout)


def insert_artifact(conn, receipt_path: str, classification: dict) -> str:
    """Insert classified artifact into ene.artifacts."""
    import psycopg2

    receipt_hash = classification["receipt_hash"]
    label = classification["rrc_shape"]["label"]
    zmp = classification["spectral"]["zero_mode_proxy_count"]
    gamma = classification["gamma_packet"]

    with open(receipt_path) as f:
        receipt_data = json.load(f)

    theorem = receipt_data.get("theorem_name", receipt_data.get("theorem_statement", "unknown"))
    proof = receipt_data.get("proof_script", "")
    content = json.dumps({
        "receipt_hash": receipt_hash,
        "theorem": theorem,
        "proof_length": len(proof),
        "classification": classification,
    })

    metadata = json.dumps({
        "pist_ready": True,
        "rrc_shape": label,
        "zmp": zmp,
        "gamma": gamma,
        "classification_basis": "convergence_proxy_v1",
        "source_receipt": receipt_path,
    })

    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM ene.artifacts WHERE path = %s",
        (f"receipts/{receipt_hash[:16]}.json",),
    )
    existing = cur.fetchone()
    if existing:
        artifact_id = existing[0]
        cur.execute(
            "UPDATE ene.artifacts SET metadata = %s::jsonb WHERE id = %s",
            (metadata, artifact_id),
        )
    else:
        import hashlib
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        cur.execute(
            "INSERT INTO ene.artifacts (path, kind, language, title, content, content_hash, metadata) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb) RETURNING id",
            (f"receipts/{receipt_hash[:16]}.json", "pist_receipt",
             "json", f"PIST: {label} — {theorem}", content, content_hash, metadata),
        )
        artifact_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    return str(artifact_id)


def record_flexure(conn, session_id: str, session_title: str, classification: dict):
    """Record a terminal flexure for the classified artifact."""
    import psycopg2

    zmp = classification["spectral"]["zero_mode_proxy_count"]
    braid = classification["braid"]
    gamma = classification["gamma_packet"]
    label = classification["rrc_shape"]["label"]

    cur = conn.cursor()
    flex_id = str(uuid.uuid4())
    chosen = {"classified_as": label, "zero_mode_proxy_count": zmp}
    signals = {
        "gamma": gamma["gamma"]["value"],
        "chi": gamma["chi"],
        "kappa": gamma["kappa"],
        "tau": gamma["tau"],
        "theta": gamma["theta"],
        "epsilon": gamma["epsilon"],
    }

    cur.execute(
        """INSERT INTO ene.flexures
           (id, session_id, step_index, pre_sidon_label, pre_residual,
            chosen_crossing, decision_signals, post_sidon_label,
            post_residual, converged)
           VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)""",
        (flex_id, session_id, 0, braid.get("strand_values", [0])[0],
         1.0 - gamma["epsilon"],
         json.dumps(chosen), json.dumps(signals),
         zmp, gamma["epsilon"], True),
    )
    conn.commit()
    cur.close()
    return flex_id


def main():
    if len(sys.argv) < 2:
        print("Usage: pist-classify receipt.json [--dry-run]", file=sys.stderr)
        return 1

    receipt_path = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    print(f"Classifying: {receipt_path}", flush=True)

    # Step 1: Run pist-decompose
    classification = classify(receipt_path)
    label = classification["rrc_shape"]["label"]
    zmp = classification["spectral"]["zero_mode_proxy_count"]
    print(f"  RRCShape: {label} (ZMP={zmp})", flush=True)
    print(f"  Receipt hash: {classification['receipt_hash'][:16]}...", flush=True)

    if dry_run:
        print(json.dumps(classification, indent=2))
        return 0

    # Step 2: Connect to RDS
    conn = connect_rds()

    # Step 3: Insert artifact
    artifact_id = insert_artifact(conn, receipt_path, classification)
    print(f"  Artifact ID: {artifact_id}", flush=True)

    # Step 4: Record terminal flexure
    session_id = os.environ.get("PIST_SESSION_ID", str(uuid.uuid4()))
    session_title = f"PIST: {label} — {os.path.basename(receipt_path)}"
    flex_id = record_flexure(conn, session_id, session_title, classification)
    print(f"  Flexure ID: {flex_id}", flush=True)
    print(f"  Session ID: {session_id}", flush=True)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
