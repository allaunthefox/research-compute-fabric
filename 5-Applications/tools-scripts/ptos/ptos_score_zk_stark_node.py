#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Graph OS node scorer for ZK-STARK triplet encoding governance.
Integrates spending proof verification into Graph OS risk assessment.
"""

import json
import hashlib
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import argparse


def generate_node_id(module_name: str) -> str:
    """Generate stable node ID from module name."""
    return hashlib.sha256(module_name.encode()).hexdigest()


def score_zk_stark_node(
    metadata_path: str,
    manifest_path: str,
    sha256_reference: str,
    proofs_jsonl_path: Optional[str] = None,
    tier: str = "CRYSTALLINE",
) -> Dict[str, Any]:
    """
    Score ZK-STARK triplet encoding as a Graph OS governance node.
    
    Args:
        metadata_path: Path to metadata JSON
        manifest_path: Path to manifest JSON
        sha256_reference: SHA256 hash to verify
        proofs_jsonl_path: Optional path to proofs for verification
        tier: Graph OS tier (SINGULARITY/PLASMA/CRYSTALLINE/FOAM)
    
    Returns:
        Graph OS node score dict with risk/guard assessment
    """
    
    # Load triplet components
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    risk_total = 0
    guard_total = 0
    tags = []
    risk_hits = {
        "proof_generation_failure": 0,
        "hash_mismatch_on_verification": 0,
        "manifest_inconsistency": 0,
        "constraint_hash_mismatch": 0,
        "byte_offset_corruption": 0,
    }
    guard_hits = {
        "governance_gate": 0,
        "integrity_binding": 0,
        "byte_reconstruction": 0,
        "timestamp_provenance": 0,
    }
    
    # Validate manifest consistency
    if metadata.get("proof_count") != manifest.get("total_proofs"):
        risk_total += 2
        risk_hits["manifest_inconsistency"] += 1
        tags.append("manifest_inconsistency")
    else:
        guard_total += 1
        guard_hits["governance_gate"] += 1
        tags.append("metadata_manifest_aligned")
    
    # Verify SHA256 if proofs provided
    if proofs_jsonl_path:
        proofs = []
        with open(proofs_jsonl_path) as f:
            for line in f:
                if line.strip():
                    proofs.append(json.loads(line))
        
        combined = json.dumps(metadata) + json.dumps(manifest)
        for proof in proofs:
            combined += json.dumps(proof, sort_keys=True)
        
        computed_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        if computed_hash == sha256_reference:
            guard_total += 3
            guard_hits["integrity_binding"] += 1
            tags.append("sha256_integrity_verified")
        else:
            risk_total += 3
            risk_hits["hash_mismatch_on_verification"] += 1
            tags.append("hash_mismatch_detected")
    else:
        guard_total += 2  # Assume valid if not verified
        guard_hits["integrity_binding"] += 1
        tags.append("sha256_integrity_assumed")
    
    # Check constraint hash consistency
    constraint_hash = metadata.get("constraint_hash")
    all_match = all(
        ref.get("constraint_hash") == constraint_hash
        for ref in manifest.get("proof_references", [])
    )
    
    if all_match:
        guard_total += 2
        guard_hits["byte_reconstruction"] += 1
        tags.append("constraint_hash_consistent")
    else:
        risk_total += 2
        risk_hits["constraint_hash_mismatch"] += 1
        tags.append("constraint_hash_mismatch")
    
    # Check timestamp freshness
    timestamp_str = metadata.get("timestamp_utc", "")
    if timestamp_str:
        guard_total += 1
        guard_hits["timestamp_provenance"] += 1
        tags.append(f"timestamp_{timestamp_str[:10]}")
    
    # Add metadata tags
    proof_count = metadata.get("proof_count", 0)
    total_amount = metadata.get("total_amount_usd", 0.0)
    tags.append(f"{proof_count}_proofs")
    tags.append(f"{total_amount:0.0f}_usd_aggregate")
    
    # Calculate net score
    net_score = guard_total - risk_total
    
    # Determine status
    if net_score > 5:
        status = "ALLOW"
        action = "Spending proof governance working as designed"
    elif net_score >= 0:
        status = "MONITOR"
        action = "Minor issues detected; verify constraint boundaries"
    else:
        status = "ESCALATE"
        action = "Critical failure; stop spending execution"
    
    # Generate node ID
    node_id = generate_node_id("Graph OS_ZK_STARK_SPENDING_PROOFS")
    
    return {
        "node_id": node_id,
        "module": "Graph OS_ZK_STARK_SPENDING_PROOFS",
        "tier": tier,
        "tags": tags,
        "risk_total": risk_total,
        "guard_total": guard_total,
        "net_score": net_score,
        "status": status,
        "action": action,
        "risk_breakdown": risk_hits,
        "guard_breakdown": guard_hits,
        "metadata_file": str(metadata_path),
        "manifest_file": str(manifest_path),
        "sha256_reference": sha256_reference,
        "timestamp_scored": datetime.utcnow().isoformat() + "Z",
    }


def add_node_to_csv(
    csv_path: str,
    node_score: Dict[str, Any],
    output_path: Optional[str] = None,
) -> str:
    """
    Add ZK-STARK node to Graph OS risk node scores CSV.
    
    Args:
        csv_path: Path to existing CSV
        node_score: Node score dict from score_zk_stark_node()
        output_path: Optional output path (default: append to existing)
    
    Returns:
        Path to updated CSV
    """
    node_id = node_score["node_id"]
    
    # Read existing CSV
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    
    # Check if node already exists
    existing_idx = next((i for i, r in enumerate(rows) if r.get("node_id") == node_id), None)
    
    # Prepare new row
    new_row = {
        "node_id": node_id,
        "tier": node_score["tier"],
        "module": node_score["module"],
        "tags": ",".join(node_score["tags"]),
        "risk_total": node_score["risk_total"],
        "guard_total": node_score["guard_total"],
        "net_score": node_score["net_score"],
        "risk_human_cognitive_overdrive_hits": node_score["risk_breakdown"].get("proof_generation_failure", 0),
        "risk_autonomy_and_override_hits": node_score["risk_breakdown"].get("hash_mismatch_on_verification", 0),
        "risk_ultra_fast_systemic_coupling_hits": node_score["risk_breakdown"].get("manifest_inconsistency", 0),
        "risk_containment_and_access_boundary_hits": node_score["risk_breakdown"].get("constraint_hash_mismatch", 0),
        "guard_governance_gate_hits": node_score["guard_breakdown"].get("governance_gate", 0),
        "guard_containment_boundary_hits": node_score["guard_breakdown"].get("byte_reconstruction", 0),
        "guard_verification_redundancy_hits": node_score["guard_breakdown"].get("timestamp_provenance", 0),
    }
    
    # Update or append
    if existing_idx is not None:
        rows[existing_idx] = new_row
    else:
        rows.append(new_row)
    
    # Write updated CSV
    out_path = output_path or csv_path
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Score ZK-STARK triplet governance for Graph OS"
    )
    parser.add_argument("--metadata", required=True, help="Metadata JSON path")
    parser.add_argument("--manifest", required=True, help="Manifest JSON path")
    parser.add_argument("--sha256", required=True, help="SHA256 reference hash")
    parser.add_argument("--proofs", help="Proofs JSONL path (optional)")
    parser.add_argument(
        "--tier", default="CRYSTALLINE", choices=["SINGULARITY", "PLASMA", "CRYSTALLINE", "FOAM"]
    )
    parser.add_argument(
        "--update-csv",
        help="Graph OS CSV to update (will append node if not exists)",
    )
    parser.add_argument("--output", help="Output JSON path")
    
    args = parser.parse_args()
    
    # Score the node
    node_score = score_zk_stark_node(
        args.metadata,
        args.manifest,
        args.sha256,
        args.proofs,
        tier=args.tier,
    )
    
    # Output JSON
    if args.output:
        with open(args.output, "w") as f:
            json.dump(node_score, f, indent=2)
        print(f"✓ Node score written to {args.output}")
    else:
        print(json.dumps(node_score, indent=2))
    
    # Update CSV if requested
    if args.update_csv:
        csv_path = add_node_to_csv(args.update_csv, node_score)
        print(f"✓ CSV updated: {csv_path}")
    
    # Summary
    print(f"\nZK-STARK Governance Node:")
    print(f"  Status: {node_score['status']}")
    print(f"  Net Score: {node_score['net_score']} (guard={node_score['guard_total']}, risk={node_score['risk_total']})")
    print(f"  Action: {node_score['action']}")
