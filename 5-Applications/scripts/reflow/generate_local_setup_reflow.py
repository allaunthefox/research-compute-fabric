#!/usr/bin/env python3
"""Generate the Phi-centered local setup reflow index.

The index is intentionally an overlay. It classifies existing Research Stack
files into the cockpit categories extracted from the chat export, with Phi as
the center of gravity, without moving files or changing canonical source
locations.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "reflow"
PHINARY_MAP = ROOT / "MATH_MODEL_MAP_phinary.tsv"


@dataclass(frozen=True)
class Category:
    name: str
    role: str
    patterns: tuple[str, ...]
    keywords: tuple[str, ...]


CATEGORIES: tuple[Category, ...] = (
    Category(
        "phi_center",
        "Root field, golden-ratio/phinary indexing, and Phi scheduling.",
        (
            "6-Documentation/docs/PHI_CENTER_REVAMP.md",
            "6-Documentation/docs/specs/PHI_S3C_PIST_BRIDGE_SPEC.md",
            "6-Documentation/docs/papers/EQUATION_00_PHI_UNIVERSAL.md",
            "6-Documentation/docs/papers/VERIFICATION_SELF_CONSISTENCY.md",
            "6-Documentation/docs/papers/UNIFICATION_STATUS_2026-04-22.md",
            "0-Core-Formalism/lean/Semantics/Semantics/UniversalField.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/PhiUniversalMetaprobe.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/PhiShellEncoding.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/PhinaryNumberSystem.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/GoldenAngleEncoding.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/GoldenSpiralManifold.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/GoldenSpiralNavigation.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/TopologyGoldenSpiral.lean",
            "0-Core-Formalism/lean/Semantics/Semantics/TopologyPhinary.lean",
            "MATH_MODEL_MAP_phinary.tsv",
            "5-Applications/scripts/convert_equations_to_phinary.py",
        ),
        (
            "Phi",
            "PHI",
            "Φ",
            "φ",
            "PhiUniversal",
            "UniversalField",
            "Phinary",
            "phinary",
            "Golden",
            "golden",
        ),
    ),
    Category(
        "foundation_trunk",
        "Base-load, compression, routing, and efficiency primitives under Phi.",
        (
            "MATH_MODEL_MAP.tsv",
            "MATH_MODELS_UNIVERSAL.json",
            "EQUATION_FOREST_INDEX.md",
            "6-Documentation/docs/semantics/UNIFIED_LOAD_EQUATION_SPEC.md",
        ),
        ("Load", "CognitiveLoad", "Compression", "Efficiency", "EtaMoE"),
    ),
    Category(
        "shell_codec_chassis",
        "S3C/DIAT/PIST shell arithmetic and manifold bridge under Phi.",
        (
            "6-Documentation/docs/S3C_MANIFOLD_GEOMETRY.md",
            "6-Documentation/docs/specs/PHI_S3C_PIST_BRIDGE_SPEC.md",
            "6-Documentation/docs/specs/MS3C_NESTED_REDUCTION_GEAR_SPEC.md",
        ),
        ("S3C", "PIST", "Pist", "DIAT", "Shell", "Bracket"),
    ),
    Category(
        "phylogenetic_graph",
        "GraphML/equation descent, lineage, and tree-of-life interpretation under Phi.",
        (
            "research_graph.graphml",
            "PROJECT_MAP.md",
            "6-Documentation/docs/papers/EQUATION_PHYLOGENETIC_TREE.md",
        ),
        ("Phylogenetic", "Graph", "Lineage", "Descent", "Tree"),
    ),
    Category(
        "manifold_field",
        "n-space/manifold view of the graph organism under Phi weighting.",
        (
            "6-Documentation/docs/specs/GCL_FIELD_EQUATIONS_SPEC.md",
            "6-Documentation/docs/specs/GCL_TOPOLOGY_REVISION_SPEC.md",
        ),
        ("Manifold", "GCL", "Topology", "Geometry", "Field", "Torus"),
    ),
    Category(
        "ingest_support_shell",
        "Text streams, databases, indexes, and search-friendly exports.",
        (
            "6-Documentation/docs/semantics/notation_ingest_bundle.md",
        ),
        ("Ingest", "Ingestion", "JsonL", "Surface", "Database", "Archive"),
    ),
)


SEARCH_ROOTS = (
    ROOT,
    ROOT / "docs",
    ROOT / "docs" / "papers",
    ROOT / "docs" / "semantics",
    ROOT / "docs" / "specs",
    ROOT / "tools" / "lean" / "Semantics" / "Semantics",
    ROOT / "scripts",
    ROOT / "data",
)

SKIP_PARTS = {
    ".git",
    ".lake",
    "node_modules",
    "ComfyUI",
    "locally-uncensored_temp",
    "searxng",
    "venv",
    "venv_proxy",
    "venv_wgpu",
    "venv_unsloth",
    "hutter_venv",
    "__pycache__",
}

SKIP_REL_PREFIXES = (
    "shared-data/data/archive_org_test/",
    "shared-data/data/archives/",
    "shared-data/data/connectomes/",
    "shared-data/data/crypto_rfc_docs/",
    "shared-data/data/crypto_rgflow/",
    "shared-data/data/cross_domain_papers/",
    "shared-data/data/datasets/",
    "shared-data/data/hutter_archive/",
    "shared-data/data/hutter_test/",
    "shared-data/data/mathlib_database/",
    "6-Documentation/docs/nlab/",
    "shared-data/data/training_data/",
)

EXTS = {".md", ".lean", ".json", ".jsonl", ".tsv", ".graphml", ".tex"}

BRIDGE_TARGETS = (
    {
        "id": "EQUATION_00_PHI_UNIVERSAL",
        "name": "Phi universal corrected field",
        "source_path": "6-Documentation/docs/papers/EQUATION_00_PHI_UNIVERSAL.md",
        "phi_role": "field",
        "phi_form": "absolute_cost|relative_efficiency",
        "s3c_role": "not_applicable",
        "pist_role": "not_applicable",
        "lineage_role": "root",
        "status": "documented_corrected_boundary",
    },
    {
        "id": "UniversalField.lean",
        "name": "UniversalField corrected Lean root",
        "source_path": "0-Core-Formalism/lean/Semantics/Semantics/UniversalField.lean",
        "phi_role": "field",
        "phi_form": "absolute_cost|relative_efficiency",
        "s3c_role": "not_applicable",
        "pist_role": "not_applicable",
        "lineage_role": "root",
        "status": "lean_anchor",
    },
    {
        "id": "Intrinsic_Load_LI",
        "name": "Intrinsic load substrate",
        "source_path": "MATH_MODEL_MAP.tsv",
        "phi_role": "field",
        "phi_form": "absolute_cost",
        "s3c_role": "not_applicable",
        "pist_role": "not_applicable",
        "lineage_role": "root_child",
        "status": "active_bridge_target",
    },
    {
        "id": "Total_Cognitive_Load",
        "name": "Total cognitive load aggregate",
        "source_path": "MATH_MODEL_MAP.tsv",
        "phi_role": "field",
        "phi_form": "control_pressure",
        "s3c_role": "not_applicable",
        "pist_role": "not_applicable",
        "lineage_role": "trunk",
        "status": "active_bridge_target",
    },
    {
        "id": "S3C.shellDecomposition",
        "name": "S3C exact shell coordinates",
        "source_path": "0-Core-Formalism/lean/Semantics/Semantics/S3C.lean",
        "phi_role": "ratio",
        "phi_form": "spacing",
        "s3c_role": "shell_coordinate",
        "pist_role": "not_applicable",
        "lineage_role": "trunk",
        "status": "lean_anchor",
    },
    {
        "id": "S3C.massZero",
        "name": "S3C closed-shell throat activation",
        "source_path": "0-Core-Formalism/lean/Semantics/Semantics/S3C.lean",
        "phi_role": "field",
        "phi_form": "relative_efficiency",
        "s3c_role": "closed_mass|throat",
        "pist_role": "not_applicable",
        "lineage_role": "branch",
        "status": "lean_anchor",
    },
    {
        "id": "S3C.massPlus",
        "name": "S3C open-shell next-shell tension",
        "source_path": "0-Core-Formalism/lean/Semantics/Semantics/S3C.lean",
        "phi_role": "field",
        "phi_form": "relative_efficiency",
        "s3c_role": "open_mass",
        "pist_role": "not_applicable",
        "lineage_role": "branch",
        "status": "lean_anchor",
    },
    {
        "id": "PistBridge.shellStateToPistCoords",
        "name": "S3C/PIST witness transport",
        "source_path": "0-Core-Formalism/lean/Semantics/Semantics/PistBridge.lean",
        "phi_role": "field",
        "phi_form": "not_applicable",
        "s3c_role": "shell_coordinate",
        "pist_role": "witness_state|transport",
        "lineage_role": "branch",
        "status": "lean_anchor",
    },
    {
        "id": "research_graph.graphml",
        "name": "Exterior phylogenetic graph",
        "source_path": "research_graph.graphml",
        "phi_role": "field|ratio",
        "phi_form": "lineage_weighting",
        "s3c_role": "not_applicable",
        "pist_role": "not_applicable",
        "lineage_role": "support",
        "status": "graph_anchor",
    },
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def is_candidate(path: Path) -> bool:
    if not path.is_file() or path.suffix not in EXTS:
        return False
    relative = rel(path)
    if any(relative.startswith(prefix) for prefix in SKIP_REL_PREFIXES):
        return False
    parts = set(path.relative_to(ROOT).parts)
    return not parts.intersection(SKIP_PARTS)


def iter_candidates() -> list[Path]:
    found: dict[str, Path] = {}
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        if root == ROOT:
            candidates = root.glob("*")
        else:
            candidates = root.rglob("*")
        for path in candidates:
            if is_candidate(path):
                found[rel(path)] = path
    return [found[k] for k in sorted(found)]


def classify(path: Path) -> list[str]:
    r = rel(path)
    haystack = f"{r} {path.stem}"
    hits: list[str] = []
    for category in CATEGORIES:
        direct = r in category.patterns
        keyword = any(keyword_matches(k, haystack) for k in category.keywords)
        if direct or keyword:
            hits.append(category.name)
    return hits


def keyword_matches(keyword: str, haystack: str) -> bool:
    if keyword in {"Phi", "PHI"}:
        return re.search(rf"(?<![A-Za-z]){re.escape(keyword)}(?![A-Za-z])", haystack) is not None
    if keyword in {"Φ", "φ"}:
        return keyword in haystack
    return keyword.lower() in haystack.lower()


def load_phinary_ids() -> dict[str, str]:
    if not PHINARY_MAP.exists():
        return {}
    with PHINARY_MAP.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return {
            row.get("Model_Name", ""): row.get("Phinary_ID", "")
            for row in reader
            if row.get("Model_Name")
        }


def write_bridge_targets() -> tuple[Path, Path]:
    phinary_ids = load_phinary_ids()
    rows = []
    for target in BRIDGE_TARGETS:
        row = dict(target)
        row["phinary_id"] = phinary_ids.get(target["id"], "")
        if target["id"] == "EQUATION_00_PHI_UNIVERSAL":
            row["phinary_id"] = "0"
        rows.append(row)

    tsv_path = OUT_DIR / "phi_s3c_pist_bridge_targets.tsv"
    json_path = OUT_DIR / "phi_s3c_pist_bridge_targets.json"
    fieldnames = (
        "id",
        "name",
        "source_path",
        "phi_role",
        "phi_form",
        "s3c_role",
        "pist_role",
        "phinary_id",
        "lineage_role",
        "status",
    )
    with tsv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return tsv_path, json_path


def main() -> None:
    rows = []
    category_rank = {category.name: idx for idx, category in enumerate(CATEGORIES)}
    for path in iter_candidates():
        categories = classify(path)
        if not categories:
            continue
        rows.append(
            {
                "path": rel(path),
                "categories": ",".join(categories),
                "primary_category": categories[0],
                "extension": path.suffix.lstrip("."),
            }
        )
    rows.sort(key=lambda row: (category_rank[row["primary_category"]], row["path"]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tsv_path = OUT_DIR / "local_setup_reflow.tsv"
    json_path = OUT_DIR / "local_setup_reflow.json"
    manifest_path = OUT_DIR / "phi_center_manifest.json"
    bridge_tsv_path, bridge_json_path = write_bridge_targets()

    with tsv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=("path", "primary_category", "categories", "extension"),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["primary_category"]] = counts.get(row["primary_category"], 0) + 1

    payload = {
        "source_context": "/home/allaun/Documents/DeleteMe/ChatGPT-Filling_in_Help.json",
        "revamp_center": "phi_center",
        "revamp_order": [c.name for c in CATEGORIES],
        "generated_from": str(ROOT),
        "categories": [
            {
                "name": c.name,
                "role": c.role,
                "patterns": list(c.patterns),
                "keywords": list(c.keywords),
            }
            for c in CATEGORIES
        ],
        "files": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    phi_manifest = {
        "center": "phi_center",
        "statement": "Phi is the local setup root: field equation, phinary index, shell weighting, graph descent, and scheduling all descend from it.",
        "control_order": [
            "phi_center",
            "foundation_trunk",
            "shell_codec_chassis",
            "phylogenetic_graph",
            "manifold_field",
            "ingest_support_shell",
        ],
        "anchor_files": [
            row for row in rows
            if row["primary_category"] == "phi_center"
            or "phi_center" in row["categories"].split(",")
        ],
        "category_counts": counts,
        "bridge_targets": str(bridge_tsv_path.relative_to(ROOT)),
    }
    manifest_path.write_text(json.dumps(phi_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"wrote {tsv_path.relative_to(ROOT)} ({len(rows)} rows)")
    print(f"wrote {json_path.relative_to(ROOT)}")
    print(f"wrote {manifest_path.relative_to(ROOT)}")
    print(f"wrote {bridge_tsv_path.relative_to(ROOT)}")
    print(f"wrote {bridge_json_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
