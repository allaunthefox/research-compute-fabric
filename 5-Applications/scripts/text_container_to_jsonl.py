#!/usr/bin/env python3
"""
Comprehensive Text Container to JSON-L Converter

Converts all information-bearing text containers (MD, JSON, CSV, TSV, TXT) to
JSON-L format compatible with UNIFIED_JSONL_SCHEMA.md.

Handles:
  - .md files (Markdown documents)
  - .json files (JSON structures)
  - .jsonl files (already JSON-L, wrap as documents)
  - .csv files (tabular data)
  - .tsv files (tabular data)
  - .txt files (plain text documents)

Excludes:
  - Tool/library files (node_modules, .lake, tools/search, .git)
  - Config files (setup.json, package.json, etc.)
  - vendored dependencies

"""

import json
import csv
import os
import sys
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Configuration
WORKSPACE_ROOT = Path("/home/allaun/Documents/Research Stack")
MANIFEST_PATH = WORKSPACE_ROOT / "data" / "manifest.jsonl"

# Directories to skip
EXCLUDE_PATTERNS = [
    ".git",
    "node_modules",
    ".lake",
    "tools/search",
    ".vscode",
    ".devcontainer",
    "__pycache__",
    ".pytest_cache",
    "venv",
    "hutter_venv",
    "venv_",
]

# File types to process
PROCESS_EXTENSIONS = {".md", ".json", ".jsonl", ".csv", ".tsv", ".txt"}

# Archetype mapping
ARCHETYPE_MAP = {
    ".md": "markdown_document",
    ".json": "json_structure",
    ".jsonl": "jsonl_dataset",
    ".csv": "csv_table",
    ".tsv": "tsv_table",
    ".txt": "text_document",
}


@dataclass
class FileContainer:
    """Represents a text-based information container."""
    filepath: Path
    ext: str
    size: int
    mtime: float
    hash: str


def should_skip(filepath: Path) -> Tuple[bool, str]:
    """Check if file should be skipped."""
    path_str = str(filepath)
    
    # Skip 4-Infrastructure/config/metadata files
    config_files = {
        "package.json", "package-lock.json", "tsconfig.json", "devcontainer.json",
        "settings.json", "launch.json", "tasks.json", ".stylelintrc.json",
        "biome.json", "lake-manifest.json", "pyrightconfig.json",
        "manifest.json", "requirements.txt", "app.json", "acme.json",
        ".vscode", ".devcontainer"
    }
    
    if filepath.name in config_files:
        return True, "config"
    
    # Skip excluded paths
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return True, f"excluded:{pattern}"
    
    # Skip large binary-like files
    if filepath.stat().st_size > 100_000_000:  # > 100MB
        return True, "too_large"
    
    return False, ""


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of file."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"
    except Exception as e:
        return f"sha256:error:{str(e)}"


def infer_domain(filepath: Path, content: str = "") -> str:
    """Infer domain from filename and path."""
    name = filepath.stem.upper()
    path = str(filepath).upper()
    
    domain_hints = {
        "LEAN|SEMANTIC|FORMALIZATION": "formalization",
        "MATH|EQUATION|MODEL": "mathematics",
        "ENE|SUBSTRATE": "ene",
        "HUTTER|COMPRESS|KOLMOGOROV": "compression",
        "PHYSICS|FIELD|QUANTUM": "physics",
        "GENOME|RGFLOW|SWARM|TOPOLOGY": "orchestration",
        "NOTION|LINEAR|ISSUE|TASK": "project_management",
        "BRAIN|MANIFOLD": "topology",
        "SPEC|SPECIFICATION|SCHEMA": "specification",
        "DATA|DATASET|CSV|TSV": "data_science",
        "CONFIG|SETTING": "infrastructure",
    }
    
    for patterns, domain in domain_hints.items():
        if any(p in name or p in path for p in patterns.split("|")):
            return domain
    
    # Default based on extension
    if filepath.suffix == ".csv" or filepath.suffix == ".tsv":
        return "data_science"
    elif filepath.suffix == ".json":
        return "specification"
    return "unknown"


def infer_tier(filepath: Path) -> str:
    """Infer tier from path."""
    path = str(filepath).lower()
    if "6-Documentation/docs/semantics" in path or "docs" in path:
        return "CORE"
    elif "shared-data/data/germane" in path:
        return "AUX"
    elif "out" in path:
        return "DERIVED"
    return "AUX"


def read_text_safely(filepath: Path, max_size: int = 1_000_000) -> str:
    """Read text file safely with encoding fallback."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "ascii", "cp1252"]
    
    size = filepath.stat().st_size
    if size > max_size:
        # Read first and last chunks
        with open(filepath, "rb") as f:
            start = f.read(500)
            f.seek(max(0, size - 500))
            end = f.read(500)
        content_bytes = start + b"\n...\n" + end
    else:
        with open(filepath, "rb") as f:
            content_bytes = f.read()
    
    for encoding in encodings:
        try:
            return content_bytes.decode(encoding, errors="replace")
        except Exception:
            continue
    
    return "<unable to decode>"


def extract_summary(content: str, max_chars: int = 250) -> str:
    """Extract summary from content."""
    lines = content.split("\n")
    summary_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("{"):
            summary_lines.append(stripped)
            if len(" ".join(summary_lines)) >= max_chars:
                break
    
    summary = " ".join(summary_lines)[:max_chars]
    return summary or "<empty or binary file>"


def csv_to_dict_list(filepath: Path, limit_rows: int = 100) -> List[Dict]:
    """Read CSV file into list of dicts."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            return list(islice(reader, limit_rows))
    except Exception:
        return []


def compute_genome(filepath: Path, content: str = "") -> Dict[str, int]:
    """Compute 6D genome signature."""
    try:
        size = filepath.stat().st_size
        lines = len(content.split("\n")) if content else 10
        
        mu = (lines % 256) // 32
        rho = min(7, (size // 1024) % 8)
        c = 4
        m = 4
        ne = min(7, len(filepath.stem) // 10)
        sig = 0 if filepath.suffix != ".json" else 3
        
        return {"mu": mu, "rho": rho, "c": c, "m": m, "ne": ne, "sig": sig}
    except Exception:
        return {"mu": 0, "rho": 0, "c": 4, "m": 4, "ne": 0, "sig": 0}


def text_to_jsonl_entry(filepath: Path, node_id: str = "qfox") -> Optional[Dict[str, Any]]:
    """Convert a text container to JSON-L entry."""
    
    try:
        should_skip_file, reason = should_skip(filepath)
        if should_skip_file:
            return None
        
        # Read content
        content = read_text_safely(filepath)
        file_hash = compute_sha256(filepath)
        file_stat = filepath.stat()
        mtime_unix = file_stat.st_mtime
        file_size = file_stat.st_size
        
        # Compute metadata
        domain = infer_domain(filepath, content)
        tier = infer_tier(filepath)
        genome = compute_genome(filepath, content)
        
        # Create pkg identifier
        rel_path = filepath.relative_to(WORKSPACE_ROOT)
        pkg = f"ene/text/{filepath.suffix[1:]}/{rel_path.stem}".replace("\\", "/")
        version = datetime.fromtimestamp(mtime_unix, tz=timezone.utc).isoformat()
        
        concept_anchor = {
            "domain": domain,
            "concept": filepath.stem.lower().replace(" ", "_").replace("-", "_").replace(".", "_"),
            "resolution": "STABLE"
        }
        
        # Extract data payload based on file type
        summary = extract_summary(content)
        
        data_payload = {
            "pkg": pkg,
            "version": version,
            "tier": tier,
            "domain": domain,
            "archetype": ARCHETYPE_MAP.get(filepath.suffix, "text_document"),
            "concept_anchor": concept_anchor,
            "file_path": str(rel_path).replace("\\", "/"),
            "file_ext": filepath.suffix,
            "file_hash": file_hash,
            "byte_count": file_size,
            "line_count": len(content.split("\n")),
            "summary": summary,
        }
        
        # Add format-specific metadata
        if filepath.suffix == ".json":
            try:
                obj = json.loads(content)
                data_payload["json_keys"] = list(obj.keys() if isinstance(obj, dict) else [])
            except Exception:
                data_payload["json_keys"] = []
        
        elif filepath.suffix in {".csv", ".tsv"}:
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    first_row = next(reader, None)
                    if first_row:
                        data_payload["columns"] = list(first_row.keys())
            except Exception:
                pass
        
        # Provenance
        provenance = {
            "node": node_id,
            "lake_seed": "text_converter",
            "tailscale_ip": "127.0.0.1",
            "attestation_hash": file_hash,
            "prev_id": None
        }
        
        # Bind
        bind = {
            "lawful": True,
            "cost": 0x00010000,
            "invariant": "documentConsistency",
            "class": "informational_bind"
        }
        
        # Full JSON-L entry
        entry = {
            "t": mtime_unix,
            "src": "ene",
            "id": f"ene:{pkg}:{version}",
            "op": "upsert",
            "data": data_payload,
            "genome": genome,
            "bind": bind,
            "provenance": provenance
        }
        
        return entry
        
    except Exception as e:
        print(f"  ⚠️  Error processing {filepath}: {e}", file=sys.stderr)
        return None


def find_all_text_containers() -> List[Path]:
    """Find all text containers in workspace."""
    containers = []
    
    for ext in PROCESS_EXTENSIONS:
        for file_path in WORKSPACE_ROOT.rglob(f"*{ext}"):
            if file_path.is_file():
                containers.append(file_path)
    
    return sorted(list(set(containers)))


def load_existing_manifest() -> set:
    """Load IDs from existing manifest."""
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


def convert_all_text_containers(output_file: Optional[str] = None) -> Tuple[int, int, int, int]:
    """
    Convert all text containers to JSON-L.
    
    Returns: (total_files, newly_converted, already_exists, skipped)
    """
    from itertools import islice
    
    output_path = Path(output_file) if output_file else MANIFEST_PATH
    
    print(f"🔍 Scanning for text containers...")
    containers = find_all_text_containers()
    print(f"✅ Found {len(containers)} text containers")
    
    existing_ids = load_existing_manifest()
    print(f"📋 Manifest already has {len(existing_ids)} entries")
    print()
    
    converted = 0
    skipped = 0
    already_exists = 0
    
    ext_stats = {}
    
    with open(output_path, "a") as manifest_f:
        for i, container in enumerate(containers, 1):
            ext = container.suffix
            ext_stats[ext] = ext_stats.get(ext, 0) + 1
            
            entry = text_to_jsonl_entry(container)
            
            if entry is None:
                skipped += 1
                status = "⏭️  SKIP"
            else:
                entry_id = entry.get("id", "")
                if entry_id in existing_ids:
                    already_exists += 1
                    status = "⏪ DUP"
                else:
                    manifest_f.write(json.dumps(entry) + "\n")
                    manifest_f.flush()
                    converted += 1
                    status = "✅ CONV"
            
            rel_path = container.relative_to(WORKSPACE_ROOT)
            
            # Less verbose output
            if i % 10 == 0 or status == "✅ CONV":
                print(f"[{i:4d}/{len(containers)}] {status} {rel_path}")
    
    return len(containers), converted, already_exists, skipped


def main():
    """Main entry point."""
    output_file = None
    if len(sys.argv) > 2 and sys.argv[1] == "--output-file":
        output_file = sys.argv[2]
    
    print("=" * 75)
    print("🌐 Comprehensive Text Container to JSON-L Converter")
    print(f"Workspace: {WORKSPACE_ROOT}")
    print(f"Output: {output_file or MANIFEST_PATH}")
    print("=" * 75)
    print()
    
    total, converted, already_exists, skipped = convert_all_text_containers(output_file)
    
    print()
    print("=" * 75)
    print(f"📊 Summary:")
    print(f"  Total files scanned:  {total}")
    print(f"  Newly converted:      {converted}")
    print(f"  Already in manifest:  {already_exists}")
    print(f"  Skipped:              {skipped}")
    print(f"  Output file: {output_file or MANIFEST_PATH}")
    print("=" * 75)
    
    return 0 if converted > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
