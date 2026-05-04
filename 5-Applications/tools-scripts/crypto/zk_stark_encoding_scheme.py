#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Minimal encoding scheme for ZK-STARK proofs.
Triplet: metadata + reconstruction_manifest + sha256
"""

import json
import hashlib
import zlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def encode_proofs_triplet(
    proofs_jsonl_path: str,
    output_dir: str = "out",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Encode proofs into three-part scheme: metadata, manifest, sha256.
    
    Args:
        proofs_jsonl_path: Path to .jsonl file containing proofs
        output_dir: Directory for output files
        metadata: Optional metadata dict to include (default: auto-generated)
    
    Returns:
        Dict with keys: metadata_path, manifest_path, sha256_hash
    """
    proofs_path = Path(proofs_jsonl_path)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Read proofs
    proofs = []
    with open(proofs_path, "r") as f:
        for line in f:
            if line.strip():
                proofs.append(json.loads(line))
    
    if not proofs:
        raise ValueError(f"No proofs found in {proofs_jsonl_path}")
    
    # 1. METADATA: proof set summary
    timestamp = datetime.utcnow().isoformat() + "Z"
    proof_count = len(proofs)
    total_amount = sum(p.get("amount_usd", 0.0) for p in proofs)
    proof_ids = [p.get("payout_intent_id") for p in proofs]
    constraint_hash = proofs[0].get("constraint_hash") if proofs else None
    
    metadata_dict = metadata or {
        "encoding_version": "1.0",
        "scheme": "triplet_metadata_manifest_sha256",
        "timestamp_utc": timestamp,
        "proof_count": proof_count,
        "total_amount_usd": total_amount,
        "constraint_hash": constraint_hash,
        "source_file": str(proofs_path.name),
    }
    
    # 2. RECONSTRUCTION MANIFEST: how to reassemble proofs
    proof_refs = []
    offset = 0
    for i, proof in enumerate(proofs):
        proof_line = json.dumps(proof)
        proof_line_bytes = (proof_line + "\n").encode("utf-8")
        proof_refs.append({
            "index": i,
            "payout_intent_id": proof.get("payout_intent_id"),
            "byte_offset": offset,
            "byte_length": len(proof_line_bytes),
            "constraint_hash": proof.get("constraint_hash"),
        })
        offset += len(proof_line_bytes)
    
    manifest_dict = {
        "reconstruction_version": "1.0",
        "total_proofs": proof_count,
        "total_bytes": offset,
        "proof_references": proof_refs,
        "encoding_metadata": metadata_dict,
    }
    
    # Write METADATA file
    metadata_filename = f"metadata_{timestamp.replace(':', '-').replace('.', '-')}.json"
    metadata_file = output_path / metadata_filename
    with open(metadata_file, "w") as f:
        json.dump(metadata_dict, f, indent=2)
    
    # Write MANIFEST file
    manifest_filename = f"manifest_{timestamp.replace(':', '-').replace('.', '-')}.json"
    manifest_file = output_path / manifest_filename
    with open(manifest_file, "w") as f:
        json.dump(manifest_dict, f, indent=2)
    
    # 3. SHA256: integrity hash over original proofs + metadata + manifest
    combined_preimage = json.dumps(metadata_dict) + json.dumps(manifest_dict)
    for proof in proofs:
        combined_preimage += json.dumps(proof, sort_keys=True)
    
    sha256_hash = hashlib.sha256(combined_preimage.encode("utf-8")).hexdigest()
    
    return {
        "metadata_file": str(metadata_file),
        "manifest_file": str(manifest_file),
        "sha256": sha256_hash,
        "proof_count": proof_count,
        "total_amount_usd": total_amount,
    }


def verify_triplet(
    metadata_path: str,
    manifest_path: str,
    sha256_reference: str,
    proofs_jsonl_path: str,
) -> bool:
    """
    Verify encoded triplet integrity.
    
    Args:
        metadata_path: Path to metadata JSON
        manifest_path: Path to manifest JSON
        sha256_reference: Expected SHA256 hash
        proofs_jsonl_path: Path to original proofs JSONL
    
    Returns:
        True if triplet verifies, False otherwise
    """
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    proofs = []
    with open(proofs_jsonl_path) as f:
        for line in f:
            if line.strip():
                proofs.append(json.loads(line))
    
    # Recompute hash
    combined = json.dumps(metadata) + json.dumps(manifest)
    for proof in proofs:
        combined += json.dumps(proof, sort_keys=True)
    
    computed_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    
    return computed_hash == sha256_reference


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python zk_stark_encoding_scheme.py <proofs.jsonl> [output_dir]")
        print("\nExample:")
        print("  python zk_stark_encoding_scheme.py 5-Applications/out/zk_stark_compliant_proofs.jsonl")
        sys.exit(1)
    
    proofs_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "out"
    
    result = encode_proofs_triplet(proofs_file, output_dir)
    print(json.dumps(result, indent=2))
    print("\n✓ Encoding complete:")
    print(f"  Metadata: {result['metadata_file']}")
    print(f"  Manifest: {result['manifest_file']}")
    print(f"  SHA256:   {result['sha256']}")
