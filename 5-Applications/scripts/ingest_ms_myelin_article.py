#!/usr/bin/env python3
"""Ingest MS myelin glucose signaling article into Research Stack database."""

import json, time, hashlib
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

ARTICLE = {
    "id": "ms-myelin-glucose-2026-05-04",
    "source": "https://multiplesclerosisnewstoday.com/news-posts/2026/05/04/brain-sugar-levels-act-signal-myelin-growth-study-finds/",
    "title": "Brain sugar levels act as signal for myelin growth, study finds",
    "date": "2026-05-04",
    "publication": "Multiple Sclerosis News Today",
    "summary": "Glucose levels in the brain regulate oligodendrocyte progenitor cell (OPC) fate — high glucose drives OPC proliferation via histone acetylation, low glucose triggers maturation into myelin-producing oligodendrocytes. Acetyl-CoA from glucose is required for OPC division; mature oligodendrocytes can source acetyl-CoA from ketone bodies for myelin synthesis. ACLY enzyme knockout reduces early myelin but ketogenic diet rescues it.",
    "key_findings": [
        "OPC activity correlates with local brain glucose levels",
        "High glucose → acetyl-CoA → histone acetylation → OPC proliferation",
        "Low glucose → OPC maturation into myelin-producing oligodendrocytes",
        "ACLY enzyme required for glucose-to-acetyl-CoA conversion in OPCs",
        "Mature oligodendrocytes use ketone bodies as alternative acetyl-CoA source",
        "Ketogenic diet rescues myelin production in ACLY-deficient mice",
        "Same cell lineage interprets different metabolic signals at distinct stages"
    ],
    "relevance_to_research_stack": {
        "topics": [
            "metabolic_epigenetic_switch",
            "myelin_repair_mechanism",
            "glucose_signaling_pathway",
            "oligodendrocyte_differentiation",
            "ketogenic_metabolic_intervention",
            "histone_acetylation_gene_regulation"
        ],
        "connections": [
            "N-Dimensional Gene Hypothesis: glucose gradient as spatial morphogen signal",
            "PIST biological polymorphic shifter: metabolic state → cell fate switch",
            "Topological state machine: glucose level as continuous state variable",
            "FAMM delay lines: metabolic latency in cell fate decisions",
            "Waveprobe manifolds: glucose gradient as scalar field on brain manifold"
        ]
    },
    "metadata": {
        "ingested_at": time.time(),
        "content_hash": hashlib.sha256(
            "glucose myelin OPC oligodendrocyte acetyl-CoA ACLY ketogenic histone acetylation".encode()
        ).hexdigest()[:16],
        "tags": ["neuroscience", "metabolism", "myelin", "multiple-sclerosis", "epigenetics", "glucose-signaling"]
    }
}


def ingest():
    # Save to germane research data
    germane_dir = RESEARCH_STACK / "shared-data/data/germane/research"
    germane_dir.mkdir(parents=True, exist_ok=True)

    out_path = germane_dir / "ms_myelin_glucose_signaling_2026-05-04.json"
    with open(out_path, 'w') as f:
        json.dump(ARTICLE, f, indent=2)

    print(f"✓ Ingested: {out_path}")

    # Append to research index
    index_path = germane_dir / "research_ingestion_index.json"
    index = []
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)

    index.append({
        "id": ARTICLE["id"],
        "title": ARTICLE["title"],
        "date": ARTICLE["date"],
        "source": ARTICLE["source"],
        "ingested_at": ARTICLE["metadata"]["ingested_at"],
        "tags": ARTICLE["metadata"]["tags"],
    })

    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"✓ Index updated: {index_path} ({len(index)} entries)")

    # Print connections
    print(f"\nResearch Stack connections:")
    for conn in ARTICLE["relevance_to_research_stack"]["connections"]:
        print(f"  → {conn}")


if __name__ == "__main__":
    ingest()
