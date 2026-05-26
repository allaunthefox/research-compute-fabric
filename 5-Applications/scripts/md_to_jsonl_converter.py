#!/usr/bin/env python3
"""Markdown to JSON-L Converter (legacy shim).

Converts .md files in a local workspace to JSON-L format compatible with
UNIFIED_JSONL_SCHEMA.md.

Hardcoded node/provenance assumptions were removed:
- node id is now configurable via --node-id or ENE_NODE_ID
- tailscale ip is now configurable via ENE_TAILSCALE_IP

NOTE: This is a legacy ingest surface and should be treated as non-authoritative.
"""

import argparse
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple


def env_default(name: str, default: str) -> str:
    try:
        v = __import__("os").environ.get(name)
    except Exception:
        v = None
    return v if v is not None and v != "" else default


# Configuration (still workspace-local; TODO: make this configurable via args)
WORKSPACE_ROOT = Path(env_default("ENE_WORKSPACE_ROOT", "/home/allaun/Documents/Research Stack"))
MANIFEST_PATH = WORKSPACE_ROOT / "data" / "manifest.jsonl"
SEARCH_DIRS = [
    WORKSPACE_ROOT,
    WORKSPACE_ROOT / "docs",
    WORKSPACE_ROOT / "docs" / "semantics",
    WORKSPACE_ROOT / "data" / "germane" / "research",
    WORKSPACE_ROOT / "data" / "germane" / "architecture",
]

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
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def infer_domain(filepath: Path, content: str) -> str:
    name = filepath.stem.upper()
    for patterns, domain in DOMAIN_PATTERNS.items():
        if any(p in name for p in patterns.split("|")):
            return domain

    parent = filepath.parent.name.lower()
    if "semantics" in parent or "lean" in parent:
        return "formalization"
    elif "research" in parent:
        return "compression"
    elif "architecture" in parent:
        return "topology"
    return "unknown"


def infer_tier(filepath: Path) -> str:
    path_str = str(filepath).lower()
    for pattern, tier in TIER_MAPPING.items():
        if pattern in path_str:
            return tier
    return "AUX"


def extract_summary(filepath: Path, max_lines: int = 5) -> str:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = []
        for i, line in enumerate(f):
            if i >= max_lines * 3:
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(stripped)
                if len(lines) >= max_lines:
                    break
        return " ".join(lines)[:200]


def compute_genome(filepath: Path) -> Dict[str, int]:
    try:
        size = filepath.stat().st_size
        lines = len(filepath.read_text(encoding="utf-8", errors="replace").split("\n"))

        mu = (lines % 256) // 32
        rho = min(7, (size // 1024) % 8)
        c = 4
        m = 4
        ne = 7 if len(filepath.stem) > 15 else 3
        sig = 0

        return {"mu": mu, "rho": rho, "c": c, "m": m, "ne": ne, "sig": sig}
    except Exception:
        return {"mu": 0, "rho": 0, "c": 4, "m": 4, "ne": 0, "sig": 0}


def compute_bind(filepath: Path) -> Dict[str, Any]:
    return {
        "lawful": True,
        "cost": 0x00010000,
        "invariant": "documentConsistency",
        "class": "informational_bind",
    }


def compute_address_from_genome(genome: Dict[str, int]) -> int:
    mu = genome.get("mu", 0)
    rho = genome.get("rho", 0)
    c = genome.get("c", 0)
    m = genome.get("m", 0)
    ne = genome.get("ne", 0)
    sig = genome.get("sig", 0)
    return (((((mu * 8 + rho) * 8 + c) * 8 + m) * 8 + ne) * 8 + sig)


def md_to_jsonl_entry(filepath: Path, node_id: str) -> Dict[str, Any]:
    file_hash = compute_sha256(filepath)
    file_stat = filepath.stat()
    mtime_unix = file_stat.st_mtime
    file_size = file_stat.st_size

    domain = infer_domain(filepath, "")
    tier = infer_tier(filepath)
    genome = compute_genome(filepath)
    _address = compute_address_from_genome(genome)
    bind = compute_bind(filepath)

    rel_path = filepath.relative_to(WORKSPACE_ROOT)
    pkg = f"ene/markdown/{rel_path.stem}".replace("\\", "/")
    version = datetime.fromtimestamp(mtime_unix, tz=timezone.utc).isoformat()

    concept_anchor = {
        "domain": domain,
        "concept": filepath.stem.lower().replace(" ", "_").replace("-", "_"),
        "resolution": "STABLE",
    }

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
        "summary": extract_summary(filepath),
    }

    provenance = {
        "node": node_id,
        "lake_seed": env_default("ENE_LAKE_SEED", "md_converter_seed"),
        "tailscale_ip": env_default("ENE_TAILSCALE_IP", "127.0.0.1"),
        "attestation_hash": file_hash,
        "prev_id": None,
    }

    return {
        "t": mtime_unix,
        "src": "ene",
        "id": f"ene:{pkg}:{version}",
        "op": "upsert",
        "data": data,
        "genome": genome,
        "bind": bind,
        "provenance": provenance,
    }


def find_all_md_files() -> List[Path]:
    md_files = []
    for search_dir in SEARCH_DIRS:
        if not search_dir.exists():
            continue
        for md_file in search_dir.glob("*.md"):
            md_files.append(md_file)
        if "germane" in str(search_dir):
            for md_file in search_dir.glob("**/*.md"):
                md_files.append(md_file)
    return sorted(list(set(md_files)))


def load_existing_manifest() -> set:
    existing_ids = set()
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    existing_ids.add(entry.get("id", ""))
                except json.JSONDecodeError:
                    continue
    return existing_ids


def convert_all_md_files(node_id: str, output_file: Optional[str] = None) -> Tuple[int, int, int]:
    output_path = Path(output_file) if output_file else MANIFEST_PATH

    md_files = find_all_md_files()
    existing_ids = load_existing_manifest()

    converted = 0
    skipped = 0

    with open(output_path, "a") as manifest_f:
        for md_file in md_files:
            entry = md_to_jsonl_entry(md_file, node_id=node_id)
            entry_id = entry.get("id", "")
            if entry_id in existing_ids:
                skipped += 1
            else:
                manifest_f.write(json.dumps(entry) + "\n")
                manifest_f.flush()
                converted += 1

    return len(md_files), converted, skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", default=None)
    parser.add_argument("--node-id", default=env_default("ENE_NODE_ID", "qfox"))
    args = parser.parse_args()

    total, converted, skipped = convert_all_md_files(node_id=args.node_id, output_file=args.output_file)
    print(json.dumps({"total": total, "converted": converted, "skipped": skipped, "node_id": args.node_id}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
