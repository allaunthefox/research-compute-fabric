#!/usr/bin/env python3
"""
ArXiv API Miner — Safe, legitimate bulk paper ingestion.

Uses the official arXiv API (export.arxiv.org) with polite delays.
Maps abstracts to the unified equation: Ω = Ψ [ B ⊗ C ] ⊕ Δ

Usage:
    python arxiv_miner.py --max 500 --output arxiv_findings.md
"""

import argparse
import sys
import time
import random
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote
import xml.etree.ElementTree as ET

import requests


ARXIV_API = "http://export.arxiv.org/api/query"
SEARCH_TERMS = [
    "quantum+mechanics", "general+relativity", "cosmology", "dark+matter",
    "black+hole", "particle+physics", "standard+model", "string+theory",
    "condensed+matter", "graphene", "superconductor", "topological",
    "genetics", "evolution", "genome", "neuroscience", "brain",
    "machine+learning", "artificial+intelligence", "neural+network",
    "thermodynamics", "statistical+mechanics", "information+theory",
    "fusion+energy", "battery", "solar+cell", "materials+science",
    "ancient+DNA", "archaeology", "paleontology", "anthropology",
    "climate+change", "carbon+cycle", "ecosystem", "microbiology",
    "cell+biology", "molecular+biology", "biochemistry", "protein",
    "fluid+dynamics", "plasma+physics", "optics", "photonics",
    "mathematics", "number+theory", "topology", "algebra",
    "chemistry", "organic+chemistry", "catalysis", "nanotechnology",
]

NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def fetch_arxiv(search_query: str, start: int = 0, max_results: int = 100) -> Optional[str]:
    url = (
        f"{ARXIV_API}?search_query=all:{quote(search_query)}"
        f"&start={start}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    )
    headers = {"User-Agent": "ResearchBot/1.0 (research@example.edu)"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        time.sleep(3.0 + random.uniform(0, 2))  # ArXiv polite delay
        return resp.text
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return None


def parse_entries(xml_text: str) -> List[dict]:
    root = ET.fromstring(xml_text.encode("utf-8"))
    entries = []
    for entry in root.findall("atom:entry", NAMESPACES):
        title = entry.find("atom:title", NAMESPACES)
        summary = entry.find("atom:summary", NAMESPACES)
        link = entry.find("atom:id", NAMESPACES)
        published = entry.find("atom:published", NAMESPACES)
        entries.append({
            "title": (title.text or "").strip().replace("\n", " ") if title is not None else "",
            "summary": (summary.text or "").strip().replace("\n", " ")[:800] if summary is not None else "",
            "url": (link.text or "").strip() if link is not None else "",
            "date": (published.text or "").strip()[:4] if published is not None else "",
        })
    return entries


def heuristic_map(title: str, summary: str) -> dict:
    text = (title + " " + summary).lower()
    mapping = {
        "Ω": "observed phenomenon / measured quantity",
        "Ψ": "theoretical mechanism / operator",
        "B": "conserved basis / fundamental component",
        "C": "dynamic context / variable parameter",
        "Δ": "residual error / noise / uncertainty",
    }

    if any(w in text for w in ["gene", "dna", "rna", "protein", "genome", "amino acid"]):
        mapping = {"Ω": "phenotype / trait", "Ψ": "gene expression / evolution", "B": "DNA sequence / protein", "C": "regulatory context / environment", "Δ": "mutation / drift"}
    elif any(w in text for w in ["black hole", "gravity", "dark matter", "spacetime", "cosmic"]):
        mapping = {"Ω": "gravitational signal", "Ψ": "GR / cosmological model", "B": "spacetime metric", "C": "mass distribution", "Δ": "quantum foam / noise"}
    elif any(w in text for w in ["quantum", "wavefunction", "electron", "photon", "entanglement"]):
        mapping = {"Ω": "measured eigenvalue", "Ψ": "quantum evolution / collapse", "B": "quantum state basis", "C": "measurement apparatus", "Δ": "uncertainty / decoherence"}
    elif any(w in text for w in ["brain", "neuron", "cognitive", "memory", "consciousness", "intelligence"]):
        mapping = {"Ω": "behavior / cognition", "Ψ": "network coordination", "B": "neural circuits", "C": "task / stimulus", "Δ": "neural noise"}
    elif any(w in text for w in ["ai", "machine learning", "neural network", "llm", "reinforcement"]):
        mapping = {"Ω": "model output / decision", "Ψ": "optimization / inference", "B": "weights / data", "C": "prompt / input", "Δ": "generalization gap"}
    elif any(w in text for w in ["fusion", "plasma", "tokamak", "stellarator", "magnetic"]):
        mapping = {"Ω": "confinement / energy", "Ψ": "guiding center / symmetry", "B": "coil geometry", "C": "plasma pressure", "Δ": "perturbation / ripple"}
    elif any(w in text for w in ["battery", "solar", "supercapacitor", "energy storage"]):
        mapping = {"Ω": "capacity / efficiency", "Ψ": "ion transport / charge transfer", "B": "material lattice", "C": "temperature / voltage", "Δ": "degradation / resistance"}
    elif any(w in text for w in ["ancient", "archaeology", "paleontology", "denisovan", "neanderthal"]):
        mapping = {"Ω": "evolutionary inference", "Ψ": "phylogenetic / cultural model", "B": "genome / artifact", "C": "climate / society", "Δ": "contamination / decay"}
    elif any(w in text for w in ["climate", "carbon", "warming", "soil", "ecosystem", "biodiversity"]):
        mapping = {"Ω": "CO₂ / species count", "Ψ": "biogeochemical cycle", "B": "microbial community", "C": "temperature / human activity", "Δ": "stochastic variation"}
    elif any(w in text for w in ["material", "graphene", "superconductor", "nanotechnology", "moiré", "topological"]):
        mapping = {"Ω": "conductivity / phase transition", "Ψ": "band structure / phonon", "B": "crystal lattice", "C": "doping / twist / strain", "Δ": "disorder / defects"}
    elif any(w in text for w in ["thermodynamics", "entropy", "statistical mechanics", "information theory"]):
        mapping = {"Ω": "entropy / free energy", "Ψ": "ensemble average / MaxEnt", "B": "microstate basis", "C": "macroscopic constraint", "Δ": "thermal fluctuation"}
    elif any(w in text for w in ["mathematics", "topology", "algebra", "number theory", "geometry"]):
        mapping = {"Ω": "theorem / invariant", "Ψ": "proof / operator", "B": "axiom / basis", "C": "parameter / space", "Δ": "approximation / error"}

    return mapping


def format_entry(number: int, entry: dict, mapping: dict) -> str:
    return (
        f"## {number}. {entry['title']}\n\n"
        f"**Source:** [{entry['url']}]({entry['url']})  ({entry['date']})\n\n"
        f"**Summary:** {entry['summary'][:500]}\n\n"
        f"| Symbol | Mapping |\n"
        f"|--------|---------|\n"
        f"| Ω | {mapping['Ω']} |\n"
        f"| Ψ | {mapping['Ψ']} |\n"
        f"| B | {mapping['B']} |\n"
        f"| C | {mapping['C']} |\n"
        f"| Δ | {mapping['Δ']} |\n\n"
        f"---\n\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=500, help="Target number of papers")
    parser.add_argument("--output", type=str, default="/home/allaun/Documents/Research Stack/3-Mathematical-Models/arxiv_findings.md")
    parser.add_argument("--per-query", type=int, default=50, help="Papers per search query")
    args = parser.parse_args()

    target = args.max
    all_entries: List[dict] = []
    seen_urls = set()

    print(f"Mining arXiv: target={target}, per-query={args.per_query}")
    print("=" * 60)

    for query in SEARCH_TERMS:
        if len(all_entries) >= target:
            break
        print(f"\nQuery: {query}  ({len(all_entries)}/{target})")
        xml = fetch_arxiv(query, start=0, max_results=args.per_query)
        if not xml:
            continue
        entries = parse_entries(xml)
        new = 0
        for e in entries:
            if e["url"] not in seen_urls:
                seen_urls.add(e["url"])
                all_entries.append(e)
                new += 1
                if len(all_entries) >= target:
                    break
        print(f"  +{new} new (total {len(all_entries)})")

    all_entries = all_entries[:target]
    print(f"\nTotal mined: {len(all_entries)}")

    lines = [
        "# ArXiv Findings — Auto-Mapped to Unified Equation",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Papers:** {len(all_entries)}",
        f"**Equation:** Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)",
        "",
        "---",
        "",
    ]

    for i, e in enumerate(all_entries, start=1):
        mapping = heuristic_map(e["title"], e["summary"])
        lines.append(format_entry(i, e, mapping))

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {args.output}")
    print("Done.")


if __name__ == "__main__":
    main()
