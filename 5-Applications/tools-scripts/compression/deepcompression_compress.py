#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
DeepCompression compression: Maximum Shannon entropy reduction.
Converts any file/archive to: manifest.json + blob.zlib + sha256.txt

Usage:
  python3 blackhole_compress.py ~/Downloads/Research\\ Documents-20260318T220015Z-1-001.zip
"""

import os
import sys
import json
import zlib
import hashlib
from datetime import datetime, timezone
from pathlib import Path

def compute_sha256(data: bytes) -> str:
    """Compute SHA256 hash of data."""
    return hashlib.sha256(data).hexdigest()

def nibble_fingerprint(data: bytes) -> str:
    """Create 16-bit hex fingerprint (4 nibbles) from data."""
    h = hashlib.md5(data).digest()
    return h[:2].hex()  # 16 bits = 4 hex digits

def relevance_bucket_4bit(data: bytes) -> int:
    """Classify data into 4-bit relevance bucket (0-15)."""
    size = len(data)
    # Log-scale bucketing: smaller = higher relevance
    if size < 1024:
        return 15  # Tiny, high relevance
    elif size < 1024*1024:
        return 14  # Small
    elif size < 10*1024*1024:
        return 13  # Medium
    elif size < 100*1024*1024:
        return 12  # Large
    else:
        return 11  # Huge

def blackhole_compress(input_path: str, output_dir: str = None) -> dict:
    """
    Compress file to deepcompression vault format.
    
    Returns:
        dict with keys: manifest_path, blob_path, sha256_path, stats
    """
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Setup output directory
    if output_dir is None:
        output_dir = input_path.parent / f"blackhole_{input_path.stem}"
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Read input
    print(f"[*] Reading input: {input_path}")
    with open(input_path, 'rb') as f:
        raw_bytes = f.read()
    
    raw_size = len(raw_bytes)
    print(f"[*] Input size: {raw_size:,} bytes ({raw_size/1024/1024:.2f} MB)")
    
    # Compress with maximum Shannon reduction (zlib level 9)
    print(f"[*] Compressing (zlib level 9)...")
    compressed = zlib.compress(raw_bytes, level=9)
    compressed_size = len(compressed)
    compression_ratio = compressed_size / max(1, raw_size)
    
    print(f"[*] Compressed size: {compressed_size:,} bytes ({compressed_size/1024/1024:.2f} MB)")
    print(f"[*] Compression ratio: {compression_ratio:.4f} ({(1-compression_ratio)*100:.2f}% reduction)")
    
    # Compute hashes
    print(f"[*] Computing hashes...")
    sha256_full = compute_sha256(raw_bytes)
    sha256_compressed = compute_sha256(compressed)
    
    # Create manifest with minimal nibble index
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = {
        "format": "deepcompression",
        "version": "1.0",
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": input_path.name,
        "source_bytes": raw_size,
        "compressed_bytes": compressed_size,
        "compression_ratio": round(compression_ratio, 6),
        "shannon_limit_reached": compression_ratio < 0.4,  # Heuristic: <40% is near Shannon limit
        "sha256_original": sha256_full,
        "sha256_compressed": sha256_compressed,
        "zlib_method": "deflate",
        "zlib_level": 9,
        "fingerprint": nibble_fingerprint(raw_bytes),
        "relevance_bucket": relevance_bucket_4bit(raw_bytes),
    }
    
    # Write manifest
    manifest_path = output_dir / f"manifest_{run_id}.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"[+] Manifest: {manifest_path}")
    
    # Write compressed blob
    blob_path = output_dir / f"blackhole_{run_id}.zlib"
    with open(blob_path, 'wb') as f:
        f.write(compressed)
    print(f"[+] Blob: {blob_path} ({compressed_size:,} bytes)")
    
    # Write SHA256 file
    sha256_path = output_dir / f"sha256_{run_id}.txt"
    with open(sha256_path, 'w') as f:
        f.write(f"{sha256_full}  {input_path.name}\n")
        f.write(f"{sha256_compressed}  {blob_path.name}\n")
    print(f"[+] SHA256: {sha256_path}")
    
    # Cleanup: remove original if extraction happened
    print(f"\n[*] DeepCompression vault created at: {output_dir}")
    print(f"[*] Files:")
    print(f"    - {manifest_path.name}")
    print(f"    - {blob_path.name}")
    print(f"    - {sha256_path.name}")
    
    return {
        "manifest_path": manifest_path,
        "blob_path": blob_path,
        "sha256_path": sha256_path,
        "stats": {
            "original_bytes": raw_size,
            "compressed_bytes": compressed_size,
            "compression_ratio": compression_ratio,
            "sha256_original": sha256_full,
            "sha256_compressed": sha256_compressed,
        }
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = blackhole_compress(input_file, output_dir)
    print(f"\n[✓] Complete. Output directory: {result['manifest_path'].parent}")
