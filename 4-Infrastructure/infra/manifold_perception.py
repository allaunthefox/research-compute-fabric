#!/usr/bin/env python3
"""
Manifold Perception Engine — Topological Analysis of the Research Stack

This script implements the extraction engine for ManifoldTopology.lean.
It scans the entire Research Stack, classifies artifacts, maps them onto
manifold dimensions, identifies boundaries and holes, and generates a
structured topological report.

Per AGENTS.md §0: Lean is the source of truth. This script is an extraction
engine only — all invariants are formally defined in ManifoldTopology.lean.

Usage:
    cd /home/allaun/Research\ Stack && python3 infra/manifold_perception.py

Output:
    data/manifold_topology_report.json — structured topological analysis
    data/manifold_holes.json — detected gaps requiring attention
    data/manifold_boundaries.json — boundary analysis per dimension
"""

import os
import re
import json
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime


RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")
DATA_DIR = RESEARCH_STACK / "data"
LEAN_DIR = RESEARCH_STACK / "tools" / "lean" / "Semantics" / "Semantics"
DOCS_DIR = RESEARCH_STACK / "docs"
INFRA_DIR = RESEARCH_STACK / "4-Infrastructure" / "infra"


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of file contents."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def count_lines(path: Path) -> int:
    """Count lines in a file."""
    try:
        return len(path.read_text().splitlines())
    except Exception:
        return 0


def classify_artifact(path: Path) -> str:
    """Classify an artifact into a PointKind-equivalent category."""
    suffix = path.suffix.lower()
    rel = str(path.relative_to(RESEARCH_STACK))

    if suffix == ".lean":
        if "ReceiptCore" in rel or "ManifoldTopology" in rel or "GeometricCompression" in rel:
            return "core_lean"
        return "lean_module"
    elif suffix == ".md":
        if "MATH_MODEL_MAP" in rel:
            return "math_model_registry"
        return "markdown_doc"
    elif suffix == ".py":
        if "manifold_perception" in rel:
            return "extraction_engine"
        return "python_script"
    elif suffix == ".toml":
        return "toml_config"
    elif suffix in (".json", ".jsonl"):
        return "json_data"
    elif suffix == ".tsv":
        return "tsv_data"
    elif suffix == ".parquet":
        return "parquet_data"
    elif suffix == ".db":
        return "sqlite_database"
    elif suffix in (".rs", ".rsx"):
        return "rust_source"
    elif suffix in (".c", ".cpp", ".h", ".hpp"):
        return "c_source"
    elif suffix in (".v", ".sv", ".vhd", ".vhdl"):
        return "hardware_source"
    else:
        return "other"


def parse_lean_file(path: Path) -> dict:
    """Extract metadata from a Lean file."""
    text = path.read_text()
    return {
        "theorem_count": len(re.findall(r'^\s*theorem\s+\w+', text, re.MULTILINE)),
        "def_count": len(re.findall(r'^\s*def\s+\w+', text, re.MULTILINE)),
        "inductive_count": len(re.findall(r'^\s*inductive\s+\w+', text, re.MULTILINE)),
        "structure_count": len(re.findall(r'^\s*structure\s+\w+', text, re.MULTILINE)),
        "eval_count": len(re.findall(r'^\s*#eval', text, re.MULTILINE)),
        "sorry_count": len(re.findall(r'\bsorry\b', text)),
        "namespace_count": len(re.findall(r'^\s*namespace\s+', text, re.MULTILINE)),
        "imports": re.findall(r'^\s*import\s+(.+)', text, re.MULTILINE),
    }


def parse_markdown_file(path: Path) -> dict:
    """Extract metadata from a Markdown file."""
    text = path.read_text()
    return {
        "heading_count": len(re.findall(r'^#{1,6}\s+', text, re.MULTILINE)),
        "equation_count": len(re.findall(r'\$\$.+?\$\$', text, re.DOTALL)),
        "inline_equation_count": len(re.findall(r'\$(?!\$).+?\$', text)),
        "table_count": len(re.findall(r'^\|.*\|.*\|', text, re.MULTILINE)),
        "code_block_count": len(re.findall(r'^```', text, re.MULTILINE)),
        "reference_count": len(re.findall(r'\[.*?\]\(.*?\)', text)),
    }


def parse_math_model_map(path: Path) -> dict:
    """Extract MATH_MODEL_MAP entries."""
    text = path.read_text()
    entries = []
    for line in text.splitlines():
        if line.startswith("|") and not line.startswith("| #") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[1].isdigit():
                entries.append({
                    "id": int(parts[1]),
                    "name": parts[2],
                    "equation": parts[3],
                    "description": parts[4] if len(parts) > 4 else "",
                })
    return {"entries": entries, "count": len(entries)}


def scan_directory(directory: Path, ignore_patterns=None) -> list:
    """Recursively scan a directory and return all file paths."""
    if ignore_patterns is None:
        ignore_patterns = ['.git', '.lake', 'build', '__pycache__', '.mypy_cache', '.pytest_cache', 'node_modules', '.rclone']

    files = []
    for root, dirs, filenames in os.walk(directory):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_patterns and not d.startswith('.')]
        for fname in filenames:
            files.append(Path(root) / fname)
    return files


def build_manifold():
    """Build the complete topological manifold of the Research Stack."""
    print("[ManifoldPerception] Scanning Research Stack...")

    # --- Scan all directories ---
    lean_files = list(LEAN_DIR.rglob("*.lean")) if LEAN_DIR.exists() else []
    docs_files = list(DOCS_DIR.rglob("*.md")) if DOCS_DIR.exists() else []
    infra_files = list(INFRA_DIR.rglob("*.py")) if INFRA_DIR.exists() else []
    data_files = list(DATA_DIR.rglob("*")) if DATA_DIR.exists() else []

    # Remove hidden/lake/build artifacts
    lean_files = [f for f in lean_files if '.lake' not in str(f) and 'build' not in str(f)]

    print(f"  Found {len(lean_files)} Lean files")
    print(f"  Found {len(docs_files)} Markdown docs")
    print(f"  Found {len(infra_files)} Python infra files")
    print(f"  Found {len(data_files)} data artifacts")

    # --- Classify Lean files ---
    lean_metadata = []
    for f in lean_files:
        meta = parse_lean_file(f)
        meta.update({
            "path": str(f.relative_to(RESEARCH_STACK)),
            "lines": count_lines(f),
            "hash": sha256_file(f),
            "kind": classify_artifact(f),
        })
        lean_metadata.append(meta)

    # --- Classify docs ---
    docs_metadata = []
    for f in docs_files:
        meta = parse_markdown_file(f)
        meta.update({
            "path": str(f.relative_to(RESEARCH_STACK)),
            "lines": count_lines(f),
            "hash": sha256_file(f),
            "kind": classify_artifact(f),
        })
        docs_metadata.append(meta)

    # --- MATH_MODEL_MAP analysis ---
    math_map_path = DOCS_DIR / "MATH_MODEL_MAP.md"
    math_map = parse_math_model_map(math_map_path) if math_map_path.exists() else {"entries": [], "count": 0}

    # --- Compute aggregate statistics ---
    total_lean_lines = sum(m["lines"] for m in lean_metadata)
    total_doc_lines = sum(m["lines"] for m in docs_metadata)
    total_theorems = sum(m["theorem_count"] for m in lean_metadata)
    total_defs = sum(m["def_count"] for m in lean_metadata)
    total_sorry = sum(m["sorry_count"] for m in lean_metadata)
    total_evals = sum(m["eval_count"] for m in lean_metadata)
    total_structures = sum(m["structure_count"] for m in lean_metadata)
    total_inductives = sum(m["inductive_count"] for m in lean_metadata)

    # --- Identify holes (gaps) ---
    holes = []

    # Hole 1: Lean files with sorry but no proven theorems
    for m in lean_metadata:
        if m["sorry_count"] > 0 and m["theorem_count"] == 0:
            holes.append({
                "center": m["path"],
                "expected_kind": "theorem_or_def",
                "severity": "critical",
                "description": f"File has {m['sorry_count']} sorry() but 0 theorems — blocked formalization",
                "missing_count": m["sorry_count"],
            })

    # Hole 2: Lean files with no #eval witnesses
    for m in lean_metadata:
        if m["eval_count"] == 0 and m["def_count"] > 0:
            holes.append({
                "center": m["path"],
                "expected_kind": "eval_witness",
                "severity": "structural",
                "description": f"File has {m['def_count']} definitions but 0 #eval witnesses",
                "missing_count": m["def_count"],
            })

    # Hole 3: MATH_MODEL_MAP entries without Lean implementations
    lean_modules = {m["path"].replace("0-Core-Formalism/lean/Semantics/Semantics/", "").replace(".lean", "")
                    for m in lean_metadata}
    for entry in math_map["entries"]:
        name = entry["name"].replace(" ", "").replace("-", "")
        # Heuristic: does any Lean module name match?
        if not any(name.lower() in mod.lower() for mod in lean_modules):
            holes.append({
                "center": f"MATH_MODEL_MAP#{entry['id']}",
                "expected_kind": "lean_module",
                "severity": "structural",
                "description": f"Model '{entry['name']}' has no corresponding Lean module",
                "missing_count": 1,
            })

    # Hole 4: Missing receipt infrastructure for new domains
    receipt_kinds = ["leanBuild", "benchmark", "sourceAudit", "reverseCollapse",
                     "deltaPhiAudit", "adversarialTrial", "humanReview",
                     "wardenEmission", "externalProof"]
    # Already all present in ReceiptCore — this is a boundary, not a hole

    # --- Identify boundaries ---
    boundaries = []

    # Boundary 1: Total Lean code size
    boundaries.append({
        "dimension": "lineCount",
        "position": total_lean_lines,
        "is_terminal": total_lean_lines > 120000,
        "description": f"Lean corpus at {total_lean_lines} lines (capacity ~130K)",
    })

    # Boundary 2: TTM Layer M concentration
    layer_m_files = [m for m in lean_metadata if "ReceiptCore" in m["path"] or
                     "ManifoldTopology" in m["path"] or
                     "GeometricCompression" in m["path"] or
                     "FixedPoint" in m["path"]]
    boundaries.append({
        "dimension": "ttmLayer",
        "position": len(layer_m_files),
        "is_terminal": len(layer_m_files) > 10,
        "description": f"Layer M (Lean Semantics): {len(layer_m_files)} core modules",
    })

    # Boundary 3: Proof completeness
    proof_ratio = (total_theorems / (total_theorems + total_sorry)) if (total_theorems + total_sorry) > 0 else 1.0
    boundaries.append({
        "dimension": "proofCompleteness",
        "position": int(proof_ratio * 100),
        "is_terminal": proof_ratio >= 0.95,
        "description": f"Proof completeness: {proof_ratio:.1%} ({total_theorems} theorems, {total_sorry} sorry)",
    })

    # Boundary 4: Documentation coverage
    doc_coverage = len(docs_metadata) / max(len(lean_metadata), 1)
    boundaries.append({
        "dimension": "documentationCoverage",
        "position": int(doc_coverage * 100),
        "is_terminal": doc_coverage >= 1.0,
        "description": f"Doc coverage: {doc_coverage:.1%} ({len(docs_metadata)} docs / {len(lean_metadata)} Lean files)",
    })

    # --- Compute cross-reference density ---
    all_imports = set()
    for m in lean_metadata:
        for imp in m.get("imports", []):
            all_imports.add(imp.strip())
    boundaries.append({
        "dimension": "crossReferenceDensity",
        "position": len(all_imports),
        "is_terminal": len(all_imports) > 50,
        "description": f"Cross-reference density: {len(all_imports)} unique imports",
    })

    # --- Build the manifold report ---
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "observer": "aiFull",
        "dimensions": {
            "ttmLayer": 13,
            "formalizationDepth": 5,
            "fileCount": len(lean_files) + len(docs_files),
            "lineCount": total_lean_lines + total_doc_lines,
            "crossReferenceDensity": len(all_imports),
            "documentationCoverage": int(doc_coverage * 100),
            "proofCompleteness": int(proof_ratio * 100),
        },
        "points": {
            "lean_files": len(lean_metadata),
            "doc_files": len(docs_metadata),
            "infra_files": len(infra_files),
            "data_files": len(data_files),
            "math_models": math_map["count"],
            "total_lines": total_lean_lines + total_doc_lines,
        },
        "structures": {
            "theorems": total_theorems,
            "definitions": total_defs,
            "inductives": total_inductives,
            "structures": total_structures,
            "eval_witnesses": total_evals,
            "sorry_markers": total_sorry,
        },
        "boundaries": boundaries,
        "holes": holes,
        "top_files_by_theorems": sorted(lean_metadata, key=lambda x: x["theorem_count"], reverse=True)[:10],
        "top_files_by_sorry": sorted(lean_metadata, key=lambda x: x["sorry_count"], reverse=True)[:10],
    }

    # --- Write outputs ---
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    report_path = DATA_DIR / "manifold_topology_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[ManifoldPerception] Wrote: {report_path}")

    holes_path = DATA_DIR / "manifold_holes.json"
    with open(holes_path, 'w') as f:
        json.dump({"holes": holes, "count": len(holes), "severity_counts": {
            "cosmetic": len([h for h in holes if h["severity"] == "cosmetic"]),
            "structural": len([h for h in holes if h["severity"] == "structural"]),
            "critical": len([h for h in holes if h["severity"] == "critical"]),
            "existential": len([h for h in holes if h["severity"] == "existential"]),
        }}, f, indent=2, default=str)
    print(f"[ManifoldPerception] Wrote: {holes_path}")

    boundaries_path = DATA_DIR / "manifold_boundaries.json"
    with open(boundaries_path, 'w') as f:
        json.dump({"boundaries": boundaries, "count": len(boundaries)}, f, indent=2, default=str)
    print(f"[ManifoldPerception] Wrote: {boundaries_path}")

    # --- Print summary to console ---
    print("\n" + "=" * 70)
    print("MANIFOLD TOPOLOGY REPORT")
    print("=" * 70)
    print(f"\nDimensions:")
    for k, v in report["dimensions"].items():
        print(f"  {k:25s}: {v}")
    print(f"\nArtifacts:")
    for k, v in report["points"].items():
        print(f"  {k:25s}: {v}")
    print(f"\nFormal Structures:")
    for k, v in report["structures"].items():
        print(f"  {k:25s}: {v}")
    print(f"\nBoundaries: {len(boundaries)}")
    for b in boundaries:
        term = "TERMINAL" if b["is_terminal"] else "soft"
        print(f"  [{term}] {b['dimension']:25s} @ {b['position']:6d} — {b['description']}")
    print(f"\nHoles: {len(holes)}")
    for h in holes[:10]:  # Show top 10
        print(f"  [{h['severity']:10s}] {h['center']:40s} — {h['description']}")
    if len(holes) > 10:
        print(f"  ... and {len(holes) - 10} more holes")
    print("\n" + "=" * 70)

    return report


if __name__ == "__main__":
    build_manifold()
