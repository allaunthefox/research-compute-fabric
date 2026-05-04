#!/usr/bin/env python3
"""
Markdown to JSON-L Converter

Converts all unconverted .md files in the workspace to JSON-L format
compatible with UNIFIED_JSONL_SCHEMA.md using src="ene".

Usage:
  python md_to_jsonl_converter.py
  python md_to_jsonl_converter.py --output-file <path>
"""

import json
import os
import sys
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

# Configuration
WORKSPACE_ROOT = Path("/home/allaun/Documents/Research Stack")
MANIFEST_PATH = WORKSPACE_ROOT / "data" / "manifest.jsonl"
SEARCH_DIRS = [
    WORKSPACE_ROOT,  # Root .md files
    WORKSPACE_ROOT / "docs",
    WORKSPACE_ROOT / "docs" / "semantics",
    WORKSPACE_ROOT / "data" / "germane" / "research",
    WORKSPACE_ROOT / "data" / "germane" / "architecture",
]

# Domain classification by filename pattern
DOMAIN_PATTERNS = {
    "LEAn|lean|semantics": "formalization",
    "MATH|math|equation": "mathematics",
    "ene|ENE": "ene",
    "hutter|compression|kolmogorov": "compression",
    "physics|field|quantum": "physics",
    "genome|rgflow|swarm": "orchestration",
    "notion|linear|issue|task": "project_management",
    "brain|manifold|topology": "topology",
    "spec|specification|schema": "specification",
}

TIER_MAPPING = {
    "docs": "CORE",
    "semantics": "CORE",
    "ene": "CORE",
    "research": "AUX",
    "architecture": "AUX",
}


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def infer_domain(filepath: Path, content: str) -> str:
    """Infer domain from filename and content."""
    name = filepath.stem.upper()
    for patterns, domain in DOMAIN_PATTERNS.items():
        if any(p in name for p in patterns.split("|")):
            return domain
    
    # Default: use parent directory as hint
    parent = filepath.parent.name.lower()
    if "semantics" in parent or "lean" in parent:
        return "formalization"
    elif "research" in parent:
        return "compression"  # Most research files are about compression/hutter
    elif "architecture" in parent:
        return "topology"
    return "unknown"


def infer_tier(filepath: Path) -> str:
    """Infer tier from path."""
    path_str = str(filepath).lower()
    for pattern, tier in TIER_MAPPING.items():
        if pattern in path_str:
            return tier
    return "AUX"


def extract_summary(filepath: Path, max_lines: int = 5) -> str:
    """Extract first few non-empty lines as summary."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = []
        for i, line in enumerate(f):
            if i >= max_lines * 3:  # Read more to find content
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(stripped)
                if len(lines) >= max_lines:
                    break
        return " ".join(lines)[:200]


def compute_genome(filepath: Path) -> Dict[str, int]:
    """Compute genome (6D quantized signature) for file."""
    try:
        size = filepath.stat().st_size
        lines = len(filepath.read_text(encoding="utf-8", errors="replace").split("\n"))
        
        # Quantize to 3 bits (0-7) per dimension
        mu = (lines % 256) // 32  # compression ratio bin based on lines
        rho = min(7, (size // 1024) % 8)  # information density (KB bins)
        c = 4  # fixed cost for documentation
        m = 4  # manifold: document is stable
        ne = 7 if len(filepath.stem) > 15 else 3  # negentropy: longer names = higher semantic content
        sig = 0  # documentation has no signal category
        
        return {
            "mu": mu, "rho": rho, "c": c, "m": m, "ne": ne, "sig": sig
        }
    except Exception as e:
        print(f"Warning: Could not compute genome for {filepath}: {e}")
        return {"mu": 0, "rho": 0, "c": 4, "m": 4, "ne": 0, "sig": 0}


def compute_bind(filepath: Path) -> Dict[str, Any]:
    """Compute bind struct (cost, lawful check, invariant)."""
    return {
        "lawful": True,
        "cost": 0x00010000,  # 1.0 in Q16_16 — documentation is reference cost
        "invariant": "documentConsistency",
        "class": "informational_bind"
    }


def compute_address_from_genome(genome: Dict[str, int]) -> int:
    """Convert 6D genome to 18-bit linear address."""
    mu = genome.get("mu", 0)
    rho = genome.get("rho", 0)
    c = genome.get("c", 0)
    m = genome.get("m", 0)
    ne = genome.get("ne", 0)
    sig = genome.get("sig", 0)
    
    address = (((((mu * 8 + rho) * 8 + c) * 8 + m) * 8 + ne) * 8 + sig)
    return address


def md_to_jsonl_entry(filepath: Path, node_id: str = "qfox") -> Dict[str, Any]:
    """Convert a single markdown file to JSON-L entry."""
    
    # Compute file metadata
    file_hash = compute_sha256(filepath)
    file_stat = filepath.stat()
    mtime_unix = file_stat.st_mtime
    file_size = file_stat.st_size
    
    # Compute derived fields
    domain = infer_domain(filepath, "")
    tier = infer_tier(filepath)
    genome = compute_genome(filepath)
    address = compute_address_from_genome(genome)
    bind = compute_bind(filepath)
    
    # Create pkg identifier
    rel_path = filepath.relative_to(WORKSPACE_ROOT)
    pkg = f"ene/markdown/{rel_path.stem}".replace("\\", "/")
    version = datetime.fromtimestamp(mtime_unix, tz=timezone.utc).isoformat()
    
    # Concept anchor
    concept_anchor = {
        "domain": domain,
        "concept": filepath.stem.lower().replace(" ", "_").replace("-", "_"),
        "resolution": "STABLE"  # documents are stable, immutable records
    }
    
    # Data payload
    data = {
        "pkg": pkg,
        "version": version,
        "tier": tier,
        "domain": domain,
        "archetype": "markdown_document",
        "concept_anchor": concept_anchor,
        "file_path": str(rel_path).replace("\\", "/"),
        "file_hash": file_hash,
        "byte_count": file_size,
        "summary": extract_summary(filepath)
    }
    
    # Provenance
    provenance = {
        "node": node_id,
        "lake_seed": "md_converter_seed",
        "tailscale_ip": "127.0.0.1",
        "attestation_hash": file_hash,
        "prev_id": None
    }
    
    # Full JSON-L entry
    entry = {
        "t": mtime_unix,
        "src": "ene",
        "id": f"ene:{pkg}:{version}",
        "op": "upsert",
        "data": data,
        "genome": genome,
        "bind": bind,
        "provenance": provenance
    }
    
    return entry


def find_all_md_files() -> List[Path]:
    """Find all .md files in search directories."""
    md_files = []
    for search_dir in SEARCH_DIRS:
        if not search_dir.exists():
            continue
        for md_file in search_dir.glob("*.md"):
            md_files.append(md_file)
        # Recursively search subdirectories for germane/
        if "germane" in str(search_dir):
            for md_file in search_dir.glob("**/*.md"):
                md_files.append(md_file)
    
    return sorted(list(set(md_files)))  # Remove duplicates and sort


def load_existing_manifest() -> set:
    """Load IDs from existing manifest to avoid duplicates."""
    existing_ids = set()
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            existing_ids.add(entry.get("id", ""))
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"Warning: Could not read existing manifest: {e}")
    return existing_ids


def convert_all_md_files(output_file: Optional[str] = None) -> Tuple[int, int, int]:
    """
    Convert all markdown files to JSON-L.
    
    Returns: (total_files, converted, skipped)
    """
    output_path = Path(output_file) if output_file else MANIFEST_PATH
    
    print(f"🔍 Scanning for .md files in {len(SEARCH_DIRS)} directories...")
    md_files = find_all_md_files()
    print(f"✅ Found {len(md_files)} markdown files")
    
    existing_ids = load_existing_manifest()
    print(f"📋 Manifest already has {len(existing_ids)} entries")
    
    converted = 0
    skipped = 0
    
    # Append new entries to manifest
    with open(output_path, "a") as manifest_f:
        for i, md_file in enumerate(md_files, 1):
            try:
                entry = md_to_jsonl_entry(md_file)
                entry_id = entry.get("id", "")
                
                if entry_id in existing_ids:
                    skipped += 1
                    status = "⏭️  SKIP"
                else:
                    manifest_f.write(json.dumps(entry) + "\n")
                    manifest_f.flush()
                    converted += 1
                    status = "✅ CONV"
                
                rel_path = md_file.relative_to(WORKSPACE_ROOT)
                print(f"[{i:3d}/{len(md_files)}] {status} {rel_path}")
                
            except Exception as e:
                print(f"[{i:3d}/{len(md_files)}] ❌ ERR  {md_file.relative_to(WORKSPACE_ROOT)}: {e}")
                skipped += 1
    
    return len(md_files), converted, skipped


def main():
    """Main entry point."""
    output_file = None
    if len(sys.argv) > 2 and sys.argv[1] == "--output-file":
        output_file = sys.argv[2]
    
    print("=" * 70)
    print("Markdown to JSON-L Converter")
    print(f"Workspace: {WORKSPACE_ROOT}")
    print(f"Output: {output_file or MANIFEST_PATH}")
    print("=" * 70)
    
    total, converted, skipped = convert_all_md_files(output_file)
    
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"  Total files found: {total}")
    print(f"  Newly converted:   {converted}")
    print(f"  Already exists:    {skipped}")
    print(f"  Output file: {output_file or MANIFEST_PATH}")
    print("=" * 70)
    
    return 0 if converted > 0 or skipped > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
