#!/usr/bin/env python3
"""
Research Stack Reorganization Script
Moves existing directories into goal-based numbered sub-folders.

Target structure:
  0-Core-Formalism/     - Lean formalism, core source, bind primitive
  1-Distributed-Systems/  - ENE mesh, gossip, consensus, nodes
  2-Search-Space/       - PIST, SVQF, FAMM, quaternion/braid primitives
  3-Mathematical-Models/ - Math database, equation registry, proofs
  4-Infrastructure/     - Python shims, GPU, cloud, web, hardware, drivers
  5-Applications/       - Scripts, tests, pipelines, output, audit
  6-Documentation/      - Docs, papers, semantics, wiki, archive, invention_record
  shared-data/          - Databases, artifacts, data, benchmarks
  workspace-config/     - .env, config, IDE settings
"""

import shutil
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/allaun/Documents/Research Stack")

# All remaining root scripts -> 5-Applications/scripts/
import glob
remaining_scripts = glob.glob("scripts/*.py") + glob.glob("scripts/*.sh") + glob.glob("scripts/*.js") + glob.glob("scripts/*.asm") + glob.glob("scripts/*.wgsl") + glob.glob("scripts/*.bin")

# All remaining root tools/ -> categorized by goal
tools_mapping = {
    "tools/build": "5-Applications/build",
    "tools/ComfyUI": "4-Infrastructure/ComfyUI",
    "tools/gpu": "4-Infrastructure/gpu",
    "tools/manifold": "2-Search-Space/manifold",
    "tools/mcp-researcher": "4-Infrastructure/mcp-researcher",
    "tools/ObsidianConnector": "6-Documentation/wiki/ObsidianConnector",
    "tools/rust": "0-Core-Formalism/rust",
    "tools/scripts": "5-Applications/tools-scripts",
    "tools/search": "2-Search-Space/search",
    "tools/servo-fetch": "4-Infrastructure/servo-fetch",
    "tools/surface": "4-Infrastructure/surface",
    "tools/text-to-cad": "5-Applications/text-to-cad",
    "tools/waveprobe": "1-Distributed-Systems/waveprobe",
    "tools/lean_unified_shim.py": "4-Infrastructure/infra/lean_unified_shim.py",
    "tools/requirements_swarm_api.txt": "5-Applications/requirements_swarm_api.txt",
}

# Mapping: source relative path -> destination relative path
MOVE_MAP = {
    # 0-Core-Formalism: Lean formalization, core source
    "tools/lean/Semantics": "0-Core-Formalism/lean/Semantics",
    "core": "0-Core-Formalism/core",
    "core/attest_wasm": "0-Core-Formalism/core/attest_wasm",
    "core/src": "0-Core-Formalism/core/src",

    # 1-Distributed-Systems: ENE, mesh, gossip
    "infra/ene_distributed_node": "1-Distributed-Systems/ene/src/",
    "data/ene_nodes": "1-Distributed-Systems/ene/nodes",
    "data/ene_provenance": "1-Distributed-Systems/ene/provenance",
    "data/ene_complete_archive": "1-Distributed-Systems/ene/archive",

    # 2-Search-Space: PIST, SVQF, FAMM, braid
    # (currently scattered in scratch/ and 0-Core-Formalism/core/; will be consolidated later)

    # 3-Mathematical-Models: equation registry, math database
    "data/mathlib_database": "3-Mathematical-Models/database",
    "data/equation_extraction_100": "3-Mathematical-Models/equations_100",
    "data/equation_extraction_10000": "3-Mathematical-Models/equations_10000",
    "data/equation_extraction_parallel_10000": "3-Mathematical-Models/equations_parallel_10000",
    "data/equation_extraction_test": "3-Mathematical-Models/equations_test",
    "data/equation_extraction_parallel_test": "3-Mathematical-Models/equations_parallel_test",

    # 4-Infrastructure: shims, GPU, cloud, hardware, drivers
    "infra": "4-Infrastructure/infra",
    "infra/lean_shim.py": "4-Infrastructure/shims/lean_shim.py",
    "infra/manifold_geometry.py": "4-Infrastructure/shims/manifold_geometry.py",
    "infra/manifold_perception.py": "4-Infrastructure/shims/manifold_perception.py",
    "hardware": "4-Infrastructure/hardware",
    "drivers": "4-Infrastructure/drivers",
    "config": "4-Infrastructure/config",

    # 5-Applications: ALL scripts, tests, pipelines, output, audit
    "scripts": "5-Applications/scripts",
    "tests": "5-Applications/tests",
    "out": "5-Applications/out",
    "audit": "5-Applications/audit",

    # 6-Documentation: docs, papers, semantics, wiki
    "docs": "6-Documentation/docs",
    "invention_record": "6-Documentation/invention_record",
    "Obdisidan connector": "6-Documentation/wiki/Obsidian-connector",

    # shared-data: databases, artifacts, data, benchmarks
    "artifacts": "shared-data/artifacts",
    "data": "shared-data/data",
}

# Files at root that stay at root
ROOT_KEEP = [
    ".git",
    ".gitignore",
    ".gitattributes",
    ".env",
    ".env.example",
    "CONCEPTS.md",
    "PROJECT_MAP.md",
    "TODO_MAP.md",
    "README.md",
    "substrate_index.db",
    "package.json",
    "package-lock.json",
    ".github",
    ".claude",
    "scratch",
    "Stack",
    "logs",
    "API KEYS",
    "venv_proxy",
    "venv_wgpu",
    "hutter_venv",
    "node_modules",
    ".windsurf",
]

# Files to move to workspace-config/
CONFIG_MOVE = {
    ".env": "workspace-config/.env",
    ".env.example": "workspace-config/.env.example",
    "config": "workspace-config/config",
}


def move_item(src_rel: str, dst_rel: str, project_root: Path):
    """Move a file or directory from src to dst, using git mv if in git repo."""
    src = project_root / src_rel
    dst = project_root / dst_rel
    
    if not src.exists():
        print(f"  SKIP (not found): {src_rel}")
        return
    
    # Ensure parent directory exists
    dst.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if destination already exists
    if dst.exists():
        print(f"  CONFLICT: {dst_rel} already exists")
        return
    
    # Check if we're in a git repo
    git_dir = project_root / ".git"
    use_git_mv = git_dir.exists()
    
    if use_git_mv:
        import subprocess
        result = subprocess.run(
            ["git", "mv", str(src_rel), str(dst_rel)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  GIT MV: {src_rel} -> {dst_rel}")
        else:
            # Fall back to shutil
            shutil.move(str(src), str(dst))
            print(f"  MV: {src_rel} -> {dst_rel}")
    else:
        shutil.move(str(src), str(dst))
        print(f"  MV: {src_rel} -> {dst_rel}")


def main():
    print("=" * 60)
    print("Research Stack Reorganization to Goal-Based Structure")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print()
    
    # Create numbered directories
    for num in range(7):
        dir_name = f"{num}-{'Core-Formalism' if num == 0 else 'Distributed-Systems' if num == 1 else 'Search-Space' if num == 2 else 'Mathematical-Models' if num == 3 else 'Infrastructure' if num == 4 else 'Applications' if num == 5 else 'Documentation'}"
        (PROJECT_ROOT / dir_name).mkdir(exist_ok=True)
    
    # Create shared-data and workspace-config
    (PROJECT_ROOT / "shared-data").mkdir(exist_ok=True)
    (PROJECT_ROOT / "workspace-config").mkdir(exist_ok=True)
    
    print("Created goal-based directories.")
    print()
    
    # Execute moves
    print("Moving items...")
    for src, dst in MOVE_MAP.items():
        move_item(src, dst, PROJECT_ROOT)
    
    print()
    print("Moving config files...")
    for src, dst in CONFIG_MOVE.items():
        move_item(src, dst, PROJECT_ROOT)
    
    print()
    print("=" * 60)
    print("Reorganization complete.")
    print("=" * 60)
    print()
    print("Remaining at root (intentionally):")
    for item in ROOT_KEEP:
        if (PROJECT_ROOT / item).exists():
            print(f"  - {item}")
    
    print()
    print("Next steps:")
    print("  1. Update PROJECT_MAP.md with new structure")
    print("  2. Update lakefile.toml srcDir paths")
    print("  3. Update Python import paths in infra/")
    print("  4. Run 'git status' to verify tracked files")


if __name__ == "__main__":
    main()
