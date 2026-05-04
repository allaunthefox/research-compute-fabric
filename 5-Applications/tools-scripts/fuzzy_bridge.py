#!/usr/bin/env python3
import sqlite3
import json
import requests
import sys
from datetime import datetime

# Path logic
DB_PATH = 'shared-data/data/substrate_index.db'
INGEST_URL = "http://localhost:3000/ingest"

def get_similarity(v1, v2):
    if not v1 or not v2 or len(v1) != 14 or len(v2) != 14:
        return 0
    return sum(a * b for a, b in zip(v1, v2))

def find_fuzzy_bridges(source_pkg, source_vector):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"[FUZZY] Scanning manifold for bridges to {source_pkg}...")
    
    # Find all records with a vector that isn't the source
    cursor.execute("SELECT pkg, concept_vector, description FROM packages WHERE pkg != ? AND concept_vector IS NOT NULL AND concept_vector != '[]'", (source_pkg,))
    rows = cursor.fetchall()
    
    bridges = []
    for row in rows:
        target_vector = json.loads(row['concept_vector'])
        sim = get_similarity(source_vector, target_vector)
        
        # Discovery Threshold: 0.4 (from Lean FuzzyAssociation module)
        if sim >= 0.4:
            bridges.append({
                "target": row['pkg'],
                "confidence": sim,
                "description": row['description'][:200]
            })
    
    conn.close()
    return sorted(bridges, key=lambda x: x['confidence'], reverse=True)[:3]

def ingest_with_fuzzy_logic(paper_data):
    # 1. Map paper to 14D Vector
    # This paper is about hardware-native compression and efficient routing
    vector = [0.0] * 14
    vector[1] = 0.8  # Compression
    vector[8] = 0.9  # Hardware/FPGA
    vector[9] = 0.6  # Signal/DSP
    
    # Normalize
    mag = sum(x*x for x in vector)**0.5
    normalized_vector = [x/mag for x in vector]

    pkg_name = f"academia/{paper_data['title'].lower().replace(' ', '_').replace('-', '_')[:50]}"
    
    # 2. Find Bridges
    bridges = find_fuzzy_bridges(pkg_name, normalized_vector)
    
    bridge_note = ""
    if bridges:
        bridge_note = "\n\n### 🧠 EMERGENT FUZZY BRIDGES\n"
        for b in bridges:
            bridge_note += f"- **Linked to {b['target']}** (Confidence: {b['confidence']:.2f})\n"

    # 3. Ingest
    payload = {
        "title": paper_data['title'],
        "body": f"{paper_data['abstract']}\n\n---\n**Source:** {paper_data['url']}{bridge_note}",
        "kind": "research",
        "tags": ["matmul-free", "ternary", "bitlinear", "neuromorphic"],
        "target": "ene", # Index into substrate first
        "quality_status": "REQUIRES_PROOF" if bridges else "VERIFIED"
    }
    
    resp = requests.post(INGEST_URL, json=payload)
    if resp.status_code == 200:
        result = resp.json()
        print(f"✅ INGESTED: {pkg_name}")
        
        # 4. If bridges found, push to Notion/Linear as high-priority discovery
        if bridges:
            print(f"🔥 DISCOVERY: {len(bridges)} fuzzy connections found. Surfacing to Notion...")
            payload["target"] = "notion"
            payload["title"] = f"[DISCOVERY] {payload['title']}"
            payload["tags"].append("fuzzy-bridge")
            requests.post(INGEST_URL, json=payload)
    else:
        print(f"❌ FAILED: {resp.text}")

if __name__ == "__main__":
    # Sample data from the fetch result
    paper = {
        "title": "Scalable MatMul-free Language Modeling",
        "abstract": "Matrix multiplication (MatMul) typically dominates the computational cost of Large Language Models (LLMs). This work demonstrates that LLMs can be constructed entirely without MatMul operations while maintaining strong performance at scale by utilizing ternary weights and a MatMul-free token mixer.",
        "url": "https://arxiv.org/abs/2405.14633"
    }
    ingest_with_fuzzy_logic(paper)
