#!/usr/bin/env python3
"""Comprehensive Text Container → JSON-L Converter (legacy shim).

Hardcoded node/provenance assumptions were removed:
- node id is configurable via --node-id or ENE_NODE_ID
- tailscale ip via ENE_TAILSCALE_IP
- workspace root via ENE_WORKSPACE_ROOT

This script is an ingest shim. Treat outputs as non-authoritative.
"""

import argparse
import json
import csv
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from shim.utils.hashing import file_sha256


def env_default(name: str, default: str) -> str:
    try:
        import os

        v = os.environ.get(name)
    except Exception:
        v = None
    return v if v is not None and v != "" else default


WORKSPACE_ROOT = Path(env_default("ENE_WORKSPACE_ROOT", "/home/allaun/Documents/Research Stack"))
MANIFEST_PATH = WORKSPACE_ROOT / "data" / "manifest.jsonl"

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

PROCESS_EXTENSIONS = {".md", ".json", ".jsonl", ".csv", ".tsv", ".txt"}

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
    filepath: Path
    ext: str
    size: int
    mtime: float
    hash: str


def should_skip(filepath: Path) -> Tuple[bool, str]:
    path_str = str(filepath)

    config_files = {
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "devcontainer.json",
        "settings.json",
        "launch.json",
        "tasks.json",
        ".stylelintrc.json",
        "biome.json",
        "lake-manifest.json",
        "pyrightconfig.json",
        "manifest.json",
        "requirements.txt",
        "app.json",
        "acme.json",
        ".vscode",
        ".devcontainer",
    }

    if filepath.name in config_files:
        return True, "config"

    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return True, f"excluded:{pattern}"

    if filepath.stat().st_size > 100_000_000:
        return True, "too_large"

    return False, ""





def infer_domain(filepath: Path, content: str = "") -> str:
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

    if filepath.suffix in {".csv", ".tsv"}:
        return "data_science"
    if filepath.suffix == ".json":
        return "specification"
    return "unknown"


def infer_tier(filepath: Path) -> str:
    path = str(filepath).lower()
    if "6-Documentation/docs/semantics" in path or "docs" in path:
        return "CORE"
    if "shared-data/data/germane" in path:
        return "AUX"
    if "out" in path:
        return "DERIVED"
    return "AUX"


def read_text_safely(filepath: Path, max_size: int = 1_000_000) -> str:
    encodings = ["utf-8", "utf-8-sig", "latin-1", "ascii", "cp1252"]

    size = filepath.stat().st_size
    if size > max_size:
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


def compute_genome(filepath: Path, content: str = "") -> Dict[str, int]:
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


def text_to_jsonl_entry(filepath: Path, node_id: str) -> Optional[Dict[str, Any]]:
    should_skip_file, _reason = should_skip(filepath)
    if should_skip_file:
        return None

    content = read_text_safely(filepath)
    file_hash = file_sha256(filepath)
    file_stat = filepath.stat()
    mtime_unix = file_stat.st_mtime
    file_size = file_stat.st_size

    domain = infer_domain(filepath, content)
    tier = infer_tier(filepath)
    genome = compute_genome(filepath, content)

    rel_path = filepath.relative_to(WORKSPACE_ROOT)
    pkg = f"ene/text/{filepath.suffix[1:]}/{rel_path.stem}".replace("\\", "/")
    version = datetime.fromtimestamp(mtime_unix, tz=timezone.utc).isoformat()

    concept_anchor = {
        "domain": domain,
        "concept": filepath.stem.lower().replace(" ", "_").replace("-", "_").replace(".", "_"),
        "resolution": "STABLE",
    }

    summary = extract_summary(content)

    data_payload: Dict[str, Any] = {
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

    if filepath.suffix == ".json":
        try:
            obj = json.loads(content)
            data_payload["json_keys"] = list(obj.keys() if isinstance(obj, dict) else [])
        except Exception:
            data_payload["json_keys"] = []

    if filepath.suffix in {".csv", ".tsv"}:
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                first_row = next(reader, None)
                if first_row:
                    data_payload["columns"] = list(first_row.keys())
        except Exception:
            pass

    provenance = {
        "node": node_id,
        "lake_seed": env_default("ENE_LAKE_SEED", "text_converter"),
        "tailscale_ip": env_default("ENE_TAILSCALE_IP", "127.0.0.1"),
        "attestation_hash": file_hash,
        "prev_id": None,
    }

    bind = {
        "lawful": True,
        "cost": 0x00010000,
        "invariant": "documentConsistency",
        "class": "informational_bind",
    }

    return {
        "t": mtime_unix,
        "src": "ene",
        "id": f"ene:{pkg}:{version}",
        "op": "upsert",
        "data": data_payload,
        "genome": genome,
        "bind": bind,
        "provenance": provenance,
    }


def find_all_text_containers() -> List[Path]:
    containers = []
    for ext in PROCESS_EXTENSIONS:
        for file_path in WORKSPACE_ROOT.rglob(f"*{ext}"):
            if file_path.is_file():
                containers.append(file_path)
    return sorted(list(set(containers)))


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


def convert_all_text_containers(node_id: str, output_file: Optional[str] = None) -> Tuple[int, int, int, int]:
    output_path = Path(output_file) if output_file else MANIFEST_PATH

    containers = find_all_text_containers()
    existing_ids = load_existing_manifest()

    converted = 0
    skipped = 0
    already_exists = 0

    with open(output_path, "a") as manifest_f:
        for container in containers:
            entry = text_to_jsonl_entry(container, node_id=node_id)
            if entry is None:
                skipped += 1
                continue

            entry_id = entry.get("id", "")
            if entry_id in existing_ids:
                already_exists += 1
            else:
                manifest_f.write(json.dumps(entry) + "\n")
                manifest_f.flush()
                converted += 1

    return len(containers), converted, already_exists, skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", default=None)
    parser.add_argument("--node-id", default=env_default("ENE_NODE_ID", "qfox"))
    args = parser.parse_args()

    total, converted, already_exists, skipped = convert_all_text_containers(
        node_id=args.node_id, output_file=args.output_file
    )
    print(
        json.dumps(
            {
                "total": total,
                "converted": converted,
                "already_exists": already_exists,
                "skipped": skipped,
                "node_id": args.node_id,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
