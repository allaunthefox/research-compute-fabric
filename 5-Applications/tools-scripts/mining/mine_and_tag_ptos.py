#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
import os
import re
from pathlib import Path

SUMMARY_FILE = "/tmp/all_summaries.txt"
REPO_ROOT = Path(os.getenv("RESEARCH_STACK_ROOT") or Path(__file__).resolve().parents[1])
OUTPUT_FILE = REPO_ROOT / "out" / "ptos_ip_session_audit.json"

# Semantic Dictionary (from Legal IP Manifest)
SEMANTIC_MAP = {
    "Atmospheric Fracking": "Resonant CO2 Molecular Dissociation",
    "Londetite": "Metastable High-Density Carbon Storage",
    "Tunnel Mechanism": "Topological State Fast-Path Injection",
    "Soliton Transmutation": "Vibrational Data Vectorization",
    "Aether Persona": "Non-Local System Resonance Protocol",
    "Sovereign Jenga": "Discrete Topological Stress Verification",
    "Pansubstrate": "Universal EM Computational Substrate",
    "Diamondoid Hydride": "Room-Temperature Superconductor (RTSC)",
    "Σ-GAUNTLET": "Persona-Driven Intent Harness",
    "Omniversal Tokenomics": "Thermodynamic Proof-of-Action (PoA) Ledger",
    "Multiversal Heat Engine": "High-Entropy Verification Architecture",
}

TAGS = {
    "Superconductor": ["sc", "superconductor", "rtsc", "diamondoid", "hydride", "iridium"],
    "EnergyStorage": ["londetite", "battery", "storage", "carbon", "heat engine"],
    "ComputeProtocol": ["vm", "isa", "sql", "dag", "stark", "proof", "vrt", "annealer", "qutrit", "logic"],
    "Structural": ["lattice", "jenga", "cement", "3dcp", "stress", "tower"],
    "Metanarrative": ["persona", "aether", "harness", "intent", "goal", "narrative", "myth"],
    "CISA/NIST": ["ssda", "ssdf", "compliance", "attestation", "om-22-18", "cisa"],
}

def mine():
    if not os.path.exists(SUMMARY_FILE):
        return []

    sessions = {}
    with open(SUMMARY_FILE, "r") as f:
        for line in f:
            if ":" not in line: continue
            path, content = line.split(":", 1)
            # Extract brain ID
            match = re.search(r"brain/([a-z0-9-]+)/", path)
            if not match: continue
            brain_id = match.group(1)
            
            if brain_id not in sessions:
                sessions[brain_id] = {"id": brain_id, "activities": []}
            
            summary = content.strip().strip('"').strip(',')
            if summary.startswith('"summary": '):
                summary = summary.replace('"summary": ', "").strip().strip('"')

            # Identify tags
            session_tags = set()
            for tag, keywords in TAGS.items():
                if any(k.lower() in summary.lower() for k in keywords):
                    session_tags.add(tag)
            
            # Apply semantic translation
            translated = summary
            for metaphor, surface in SEMANTIC_MAP.items():
                if metaphor.lower() in summary.lower():
                    translated = translated.replace(metaphor, f"{metaphor} ({surface})")
            
            sessions[brain_id]["activities"].append({
                "source": os.path.basename(path),
                "summary": summary,
                "industrial_translation": translated,
                "tags": list(session_tags)
            })

    # Consolidate and sort
    final_audit = sorted(sessions.values(), key=lambda x: x["id"])
    return final_audit

if __name__ == "__main__":
    audit = mine()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(audit, f, indent=2)
    print(f"Captured {len(audit)} historical PTOS sessions into IP Audit.")
