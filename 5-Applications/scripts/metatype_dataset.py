import os
import requests
import json
import subprocess
from datetime import datetime

# Configuration
DATA_DIR = "data"
INGEST_URL = "http://localhost:3000/ingest"

METATYPES = {
    "shared-data/data/atomic_weights.csv": {
        "observe": "A CSV dataset containing atomic numbers, chemical symbols, element names, and standard atomic weights for 118 elements, featuring precision notations and interval ranges.",
        "classify": "empirical_result",
        "act": "Utilize as a foundational lookup table for physical simulations and material science calculations within the field solver emulators.",
        "prove": "Establishes a ground-truth mapping for atomic masses, providing the necessary witnesses for physical consistency in stoichiometry-based computations.",
        "remember": "High archival value as a standardized reference for fundamental physical constants essential for long-term scientific reproducibility.",
        "tags": ["csv", "chemistry", "atomic-weights", "physical-constants", "empirical-data"],
        "sigma_codon": "0x1f4a8b2c"
    },
    "shared-data/data/ingestion_manifest_self_type_2026-04-14.md": {
        "observe": "A markdown ingestion manifest documenting the extraction and classification of 87 files from a self-typing research archive, including SHA256 hashes and verification status.",
        "classify": "ingestion_manifest",
        "act": "Govern the distribution of research components into specific destinations (Lean, Python, Docs) and track the 'DID NOT CONVERGE' status of the verification swarm.",
        "prove": "Provides an immutable audit trail of file integrity and documents the structural failure modes identified during the self-typing bootstrap process.",
        "remember": "Critical archival record for project provenance, documenting the specific milestone where fundamental issues in constraint geometry were identified.",
        "tags": ["markdown", "manifest", "ingestion", "self-typing", "provenance", "audit"],
        "sigma_codon": "0xa7d9e1f4"
    },
    "6-Documentation/docs/specs/quantization.md": {
        "observe": "A formal technical specification for ternary weight quantization and MatMul-free MLGRU recurrence, including LaTeX formulas, Lean definitions, and WGSL shader implementations.",
        "classify": "formal_spec",
        "act": "Serve as the primary architectural blueprint for implementing 10x memory-reduced neural inference on WebGPU using Q16_16 fixed-point arithmetic.",
        "prove": "Demonstrates formal error bounds for quantization and mathematically proves the transition from O(d^2) to O(d) computational complexity for element-wise updates.",
        "remember": "Foundational architectural document defining the platform's core strategy for sustainable, high-efficiency inference on restricted hardware.",
        "tags": ["markdown", "specification", "quantization", "mlgru", "webgpu", "lean"],
        "sigma_codon": "0x5e2c6f0d"
    },
    "6-Documentation/docs/MATH_MODEL_MAP.md": {
        "observe": "Comprehensive catalog of 251 mathematical models across 13 TTM layers, defining the project's formal logic and cross-model dependencies.",
        "classify": "formal_taxonomy",
        "act": "Index new developments into the TTM hierarchy and validate against Layer M semantics to maintain the Collapse Principle.",
        "prove": "131 models verified in Tier 1-3 proofs; Layer M semantics show a 54% auto-proof rate within the Lean framework.",
        "remember": "The system is an evolving CanonicalState object where layers A–L are projections rather than separate systems.",
        "tags": ["math", "TTM", "catalog", "formalism", "semantics"],
        "sigma_codon": "0xa4f92b7c"
    },
    "6-Documentation/docs/VISION_NORTH_STAR.md": {
        "observe": "Strategic shift from patchwork specialization toward a unified circulatory system based on 'bind' primitives and n-space vectorization.",
        "classify": "strategic_vision",
        "act": "Ground semantic atoms in Standard Model particles to achieve inter-manifold lawful translation and interspecies communication.",
        "prove": "Truth Seal [SSS-ENE-TRUTH-2026-04-14] verified via implementation of Bind.lean and Semantics/Physics modules.",
        "remember": "Files are not locations but n-space vectors; the Standard Model serves as the universal invariant boundary for cognition.",
        "tags": ["vision", "n-space", "philosophy", "evolution", "standard-model"],
        "sigma_codon": "0x1e5d9c3b"
    },
    "shared-data/data/germane/architecture/CANONICAL_CORE_V1.md": {
        "observe": "Modular 10-layer specification for adaptive systems, formalizing SSS stability, torsion fields, and the Alcubierre information metric.",
        "classify": "system_architecture",
        "act": "Physically instantiate the 'trinary tic' (Add, Subtract, Pause) and SSS constraints within the hardware-accelerated field solver.",
        "prove": "Layers 1-10 marked as [VERIFIED]; SSS formalization prevents 'fuzz invasion' by maintaining counter-torque against manifold torsion.",
        "remember": "The map is the territory; Sisyphus is the moving crystallization front advancing structure into chaos.",
        "tags": ["core", "spec", "SSS", "alcubierre", "geometry"],
        "sigma_codon": "0xf7a3d2e1"
    }
}

def process_file(file_path):
    if os.path.isdir(file_path):
        return
    
    filename = os.path.basename(file_path)
    if filename.endswith(".db") or filename.endswith(".zip") or filename.startswith("."):
        return

    print(f"[*] Metatyping: {file_path}")
    
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()
        
        sigma = METATYPES.get(file_path, {})
        
        payload = {
            "title": f"SIGMA: {filename}",
            "body": content,
            "kind": sigma.get("classify", "metatyped_archive"),
            "tags": list(set(["metatyping", "sigma-classification", os.path.splitext(filename)[1][1:]] + sigma.get("tags", []))),
            "target": "ene",
            "sigma": sigma
        }
        
        # Ingest to local server
        resp = requests.post(INGEST_URL, json=payload)
        if resp.status_code == 200:
            print(f"    ✅ INGESTED: {filename} (Codon: {sigma.get('sigma_codon', 'N/A')})")
        else:
            print(f"    ❌ FAILED: {resp.text}")
            
    except Exception as e:
        print(f"    ⚠️ ERROR: {str(e)}")

def scan_recursive(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith(".md") or f.endswith(".csv"):
                files.append(os.path.join(root, f))
    return files

def main():
    # 1. Start with pre-defined critical files
    target_files = list(METATYPES.keys())
    
    # 2. Add architecture documents
    arch_files = scan_recursive("shared-data/data/germane/architecture")
    for f in arch_files:
        if f not in target_files:
            target_files.append(f)
            
    # 3. Process
    for f in target_files:
        if os.path.exists(f):
            process_file(f)

if __name__ == "__main__":
    main()
