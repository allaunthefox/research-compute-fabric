#!/usr/bin/env python3
"""
populate-open-webui-knowledge-expanded.py

Comprehensive knowledge population + Cascade persona setup for Open WebUI.

Usage:
    1. Go to http://127.0.0.1:3000 and create your admin account
    2. Get API key: Settings → Account → API Key
    3. Run: python3 scripts/populate-open-webui-knowledge-expanded.py <API_KEY>

This creates 12 knowledge collections covering the entire project.
"""

import sys
import os
import requests

BASE_URL = "http://127.0.0.1:3000"
HEADERS = {"Content-Type": "application/json"}
REPO_ROOT = "/home/allaun/CascadeProjects/Research-Stack"


def set_api_key(key):
    HEADERS["Authorization"] = f"Bearer {key}"


def create_knowledge(name, description):
    url = f"{BASE_URL}/api/v1/knowledge/"
    payload = {"name": name, "description": description}
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data.get("id") or data.get("data", {}).get("id")


def upload_file(filepath):
    url = f"{BASE_URL}/api/v1/files/"
    filename = os.path.basename(filepath)
    mime = "text/markdown" if filepath.endswith(".md") else "text/plain"
    with open(filepath, "rb") as f:
        files = {"file": (filename, f, mime)}
        resp = requests.post(url, headers={"Authorization": HEADERS["Authorization"]}, files=files)
    resp.raise_for_status()
    data = resp.json()
    return data.get("id") or data.get("data", {}).get("id")


def add_file_to_knowledge(knowledge_id, file_id):
    url = f"{BASE_URL}/api/v1/knowledge/{knowledge_id}/files/"
    payload = {"file_id": file_id}
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()


def process_collection(name, description, file_paths):
    print(f"\n  Creating: {name}")
    kid = create_knowledge(name, description)
    print(f"    -> ID: {kid}")

    for fp in file_paths:
        abs_fp = os.path.join(REPO_ROOT, fp)
        if not os.path.isfile(abs_fp):
            print(f"    [SKIP] Not found: {fp}")
            continue
        print(f"    Uploading: {os.path.basename(fp)}")
        try:
            fid = upload_file(abs_fp)
            add_file_to_knowledge(kid, fid)
        except Exception as e:
            print(f"    [ERROR] {e}")
    print(f"  Done: {name}")


def collect_files(pattern, max_files=50):
    import glob
    files = glob.glob(os.path.join(REPO_ROOT, pattern), recursive=True)
    files = [os.path.relpath(f, REPO_ROOT) for f in files if os.path.isfile(f)]
    return sorted(files)[:max_files]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print(f"\nUsage: python3 {sys.argv[0]} <API_KEY>")
        sys.exit(1)

    api_key = sys.argv[1]
    set_api_key(api_key)

    try:
        r = requests.get(f"{BASE_URL}/api/v1/users/", headers=HEADERS, timeout=5)
        r.raise_for_status()
        print(f"Connected to Open WebUI at {BASE_URL}")
    except Exception as e:
        print(f"ERROR: Cannot connect: {e}")
        sys.exit(1)

    os.chdir(REPO_ROOT)

    # 1. Core
    process_collection(
        "Research Stack Core",
        "Central project documents.",
        ["README.md", "PROJECT_MAP.md", "CONCEPTS.md", "TODO_MAP.md"],
    )

    # 2. GCCL
    process_collection(
        "GCCL Theory",
        "Genetic-Code Compression Language.",
        collect_files("docs/research/GCCL_*.md"),
    )

    # 3. KOTC
    process_collection(
        "KOTC & Daemon Systems",
        "Knowledge-Of-Task-Completion architecture.",
        collect_files("docs/research/KOTC_*.md"),
    )

    # 4. VLB
    process_collection(
        "VLB & Witness Substrate",
        "Very-Large-Block witness and substrate.",
        collect_files("docs/research/VLB_*.md"),
    )

    # 5. FAMM
    process_collection(
        "FAMM & Route Memory",
        "Fluid-Automata Memory Model.",
        collect_files("docs/famm/*.md"),
    )

    # 6. Roadmaps
    process_collection(
        "Roadmaps & Strategy",
        "Project roadmaps and planning.",
        collect_files("docs/roadmaps/*.md"),
    )

    # 7. Speculative
    process_collection(
        "Speculative Materials",
        "Exploratory research notes.",
        collect_files("docs/speculative-materials/*.md"),
    )

    # 8. Lean READMEs
    process_collection(
        "Lean Formalism READMEs",
        "Per-domain READMEs.",
        collect_files("*/README.md", max_files=20),
    )

    # 9. Documentation
    process_collection(
        "Documentation Guides",
        "Human-readable explanations.",
        collect_files("6-Documentation/*.md", max_files=20),
    )

    # 10. Workflows
    process_collection(
        "Windsurf Workflows",
        "Agent workflow definitions.",
        collect_files(".windsurf/workflows/*.md"),
    )

    # 11. Assignments & Audit
    process_collection(
        "Agent Assignments & Audit",
        "Task assignments and sorry audit.",
        [".windsurf/ASSIGNMENTS.md", ".windsurf/SORRY_AUDIT.md"],
    )

    # 12. Lean Core Files
    lean_core = collect_files("0-Core-Formalism/lean/Semantics/Semantics/*.lean", max_files=30)
    process_collection(
        "Lean Core Source",
        "Key Lean formalism source files.",
        lean_core,
    )

    # 13. Data
    process_collection(
        "Project Data Files",
        "Data tables and indices.",
        collect_files("data/*.tsv", max_files=10) + collect_files("data/*.json", max_files=10),
    )

    print("\n========================================")
    print("All collections populated.")
    print("Next: Create a custom model with the Cascade prompt.")
    print("========================================\n")


if __name__ == "__main__":
    main()
