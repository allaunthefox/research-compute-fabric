#!/usr/bin/env python3
"""
populate-open-webui-knowledge.py

Prefill Open WebUI knowledge collections with your Research Stack documents.

Usage:
    1. Go to http://127.0.0.1:3000 and create your admin account
    2. Get API key: Settings → Account → API Key
    3. Run: python3 scripts/populate-open-webui-knowledge.py <API_KEY>

Collections created:
    - Research Stack Core       (README, PROJECT_MAP, CONCEPTS, TODO_MAP)
    - GCCL Theory               (docs/research/GCCL_*.md)
    - KOTC & Daemon Systems     (docs/research/KOTC_*.md)
    - VLB & Witness Substrate   (docs/research/VLB_*.md)
    - FAMM & Route Memory       (docs/famm/*.md)
    - Roadmaps & Strategy       (docs/roadmaps/*.md)
    - Speculative Materials     (docs/speculative-materials/*.md)
    - Lean Formalism READMEs    (*/README.md)
    - Documentation Guides      (6-Documentation/*.md)
"""

import sys
import json
import os
import requests

BASE_URL = "http://127.0.0.1:3000"
HEADERS = {"Content-Type": "application/json"}

REPO_ROOT = "/home/allaun/CascadeProjects/Research-Stack"


def set_api_key(key):
    HEADERS["Authorization"] = f"Bearer {key}"


def create_knowledge(name, description):
    """Create a knowledge collection."""
    url = f"{BASE_URL}/api/v1/knowledge/"
    payload = {"name": name, "description": description}
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    data = resp.json()
    # Open WebUI returns {id, ...}
    return data.get("id") or data.get("data", {}).get("id")


def upload_file(filepath):
    """Upload a single file, return file_id."""
    url = f"{BASE_URL}/api/v1/files/"
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        files = {"file": (filename, f, "text/markdown")}
        resp = requests.post(url, headers={"Authorization": HEADERS["Authorization"]}, files=files)
    resp.raise_for_status()
    data = resp.json()
    return data.get("id") or data.get("data", {}).get("id")


def add_file_to_knowledge(knowledge_id, file_id):
    """Attach an uploaded file to a knowledge collection."""
    url = f"{BASE_URL}/api/v1/knowledge/{knowledge_id}/files/"
    payload = {"file_id": file_id}
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()


def process_collection(name, description, file_paths):
    """Create a collection and upload+attach all files."""
    print(f"\n  Creating collection: {name}")
    kid = create_knowledge(name, description)
    print(f"    -> ID: {kid}")

    for fp in file_paths:
        if not os.path.isfile(fp):
            print(f"    [SKIP] Not found: {fp}")
            continue
        print(f"    Uploading: {os.path.basename(fp)}")
        try:
            fid = upload_file(fp)
            add_file_to_knowledge(kid, fid)
        except Exception as e:
            print(f"    [ERROR] {e}")
    print(f"  Done: {name}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print(f"\nUsage: python3 {sys.argv[0]} <API_KEY>")
        sys.exit(1)

    api_key = sys.argv[1]
    set_api_key(api_key)

    # Verify connectivity
    try:
        r = requests.get(f"{BASE_URL}/api/v1/users/", headers=HEADERS, timeout=5)
        r.raise_for_status()
        print(f"Connected to Open WebUI at {BASE_URL}")
    except Exception as e:
        print(f"ERROR: Cannot connect to Open WebUI: {e}")
        sys.exit(1)

    os.chdir(REPO_ROOT)

    # ---------------------------------------------------------------
    # Collection 1: Research Stack Core
    # ---------------------------------------------------------------
    process_collection(
        "Research Stack Core",
        "Central project documents: overview, map, concepts, and roadmap.",
        [
            "README.md",
            "PROJECT_MAP.md",
            "CONCEPTS.md",
            "TODO_MAP.md",
        ],
    )

    # ---------------------------------------------------------------
    # Collection 2: GCCL Theory
    # ---------------------------------------------------------------
    process_collection(
        "GCCL Theory",
        "Genetic-Code Compression Language theoretical foundations.",
        [
            "docs/research/GCCL_GENETIC_INFORMATION_MIXTURE_PRIMITIVES.md",
            "docs/research/GCCL_THEORY_INTRO.md",
        ],
    )

    # ---------------------------------------------------------------
    # Collection 3: KOTC & Daemon Systems
    # ---------------------------------------------------------------
    process_collection(
        "KOTC & Daemon Systems",
        "Knowledge-Of-Task-Completion daemon architecture.",
        [
            "docs/research/KOTC_COMPLETION_DAEMON.md",
        ],
    )

    # ---------------------------------------------------------------
    # Collection 4: VLB & Witness Substrate
    # ---------------------------------------------------------------
    process_collection(
        "VLB & Witness Substrate",
        "Very-Large-Block witness and substrate estimation.",
        [
            "docs/research/VLB_NIBBLE_DELTA_WITNESS_SUBSTRATE_ESTIMATE.md",
        ],
    )

    # ---------------------------------------------------------------
    # Collection 5: FAMM & Route Memory
    # ---------------------------------------------------------------
    process_collection(
        "FAMM & Route Memory",
        "Fluid-Automata Memory Model and stigmergic routing.",
        [
            "docs/famm/FAMM_Stigmergic_Route_Memory.md",
        ],
    )

    # ---------------------------------------------------------------
    # Collection 6: Roadmaps & Strategy
    # ---------------------------------------------------------------
    process_collection(
        "Roadmaps & Strategy",
        "Project roadmaps and strategic planning documents.",
        [
            "docs/roadmaps/RESEARCH_STACK_FOREST_MAP_WATERFALL.md",
        ],
    )

    # ---------------------------------------------------------------
    # Collection 7: Speculative Materials
    # ---------------------------------------------------------------
    process_collection(
        "Speculative Materials",
        "Exploratory and speculative research notes.",
        [
            "docs/speculative-materials/PhotonChasedFerriteTraceFormation.md",
        ],
    )

    # ---------------------------------------------------------------
    # Collection 8: Lean Formalism READMEs
    # ---------------------------------------------------------------
    process_collection(
        "Lean Formalism READMEs",
        "Per-domain READMEs for the Lean formalism sub-projects.",
        [
            "0-Core-Formalism/README.md",
            "1-Distributed-Systems/README.md",
            "2-Search-Space/README.md",
            "3-Mathematical-Models/README.md",
            "4-Infrastructure/README.md",
            "5-Applications/README.md",
            "6-Documentation/README.md",
        ],
    )

    # ---------------------------------------------------------------
    # Collection 9: Documentation Guides
    # ---------------------------------------------------------------
    process_collection(
        "Documentation Guides",
        "Human-readable explanations, pitches, and guides.",
        [
            "6-Documentation/EXPLANATION_FOR_HUMANS.md",
            "6-Documentation/ELEVATOR_PITCH.md",
            "6-Documentation/calculator_plain_math.md",
        ],
    )

    print("\n========================================")
    print("All knowledge collections populated.")
    print("Go to http://127.0.0.1:3000 and check")
    print("Workspace → Knowledge to browse them.")
    print("========================================\n")


if __name__ == "__main__":
    main()
