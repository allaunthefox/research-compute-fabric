#!/usr/bin/env python3
"""
seismic_search.py — ENE Pattern-Based Search Engine

Adapts public domain search patterns (BM25, Inverted Indexing) to the 
Sovereign Informatic Manifold using Phi-modulated relevance scoring.

Citations:
- Robertson & Jones (1976), Probabilistic Relevance Framework.
- rank_bm25 (MIT), Dorian Brown et al.
- Rosetta Code (GFDL), Trie-based indexing patterns.
"""

import os
import json
import math
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"

class SeismicSearchEngine:
    def __init__(self, phi: float = 0.0):
        """
        phi: Real-time informatic stress [0.0, 1.0].
        High phi increases 'Self-Relevance' of foundational axioms.
        """
        self.phi = phi
        self.k1 = 1.2 + (phi * 0.8) # Saturation increases with stress
        self.b = 0.75 - (phi * 0.25) # Length normalization relaxes under stress
        
        self.index: Dict[str, List[Tuple[str, int]]] = {} # term -> [(doc_id, freq)]
        self.doc_lengths: Dict[str, int] = {} # doc_id -> length
        self.total_tokens = 0
        self.avg_doc_len = 0.0
        self.doc_count = 0
        self.corpus: Dict[str, str] = {} # doc_id -> path

    def _tokenize(self, text: str) -> List[str]:
        """Simple cleaning and tokenization (Pattern: rank_bm25)."""
        text = text.lower()
        # Remove non-alphanumeric
        tokens = re.findall(r'\b\w\w+\b', text)
        return tokens

    def build_index(self, root_dir: Path):
        """Builds an inverted index from the documentation directory."""
        total_len = 0
        docs_found = []

        # Find all .md, .v, .lean, and .py files
        extensions = {".md", ".v", ".lean", ".py"}
        for root, _, files in os.walk(root_dir):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    docs_found.append(Path(root) / file)

        if not docs_found:
            return

        self.doc_count += len(docs_found)

        for doc_path in docs_found:
            doc_id = str(doc_path.relative_to(root_dir))
            self.corpus[doc_id] = str(doc_path)
            
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                tokens = self._tokenize(content)
                self.doc_lengths[doc_id] = len(tokens)
                self.total_tokens += len(tokens)
                
                # Term counts for this doc
                counts = {}
                for t in tokens:
                    counts[t] = counts.get(t, 0) + 1
                
                for term, freq in counts.items():
                    if term not in self.index:
                        self.index[term] = []
                    self.index[term].append((doc_id, freq))

        if self.doc_count > 0:
            self.avg_doc_len = self.total_tokens / self.doc_count

    def get_idf(self, term: str) -> float:
        """Calculates Inverse Document Frequency (Pattern: Robertson & Jones)."""
        if term not in self.index:
            return 0.0
        
        num_with_term = len(self.index[term])
        # Smooth IDF
        return math.log((self.doc_count - num_with_term + 0.5) / (num_with_term + 0.5) + 1.0)

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Performs BM25 search modulated by Seismic Phi.
        Adapted from pattern: Okapi BM25 Ranking.
        """
        q_tokens = self._tokenize(query)
        scores: Dict[str, float] = {} # doc_id -> score

        for term in q_tokens:
            idf = self.get_idf(term)
            if idf <= 0:
                continue
                
            for doc_id, tf in self.index.get(term, []):
                d_len = self.doc_lengths[doc_id]
                
                # Standard BM25 Numerator
                num = tf * (self.k1 + 1)
                # Standard BM25 Denominator
                den = tf + self.k1 * (1 - self.b + self.b * (d_len / self.avg_doc_len))
                
                score = idf * (num / den)
                
                # --- Seismic Adaptation: Axiom Boost ---
                # Foundational design rationale gets a resonance multiplier
                if "rationale" in doc_id.lower() or "manifest" in doc_id.lower():
                    score *= (1.5 + self.phi) # Resonance boost based on stress
                
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        # Sort and format
        results = []
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for doc_id, score in sorted_docs[:limit]:
            results.append({
                "doc": doc_id,
                "score": round(score, 3),
                "path": self.corpus[doc_id]
            })
            
        return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seismic Search Engine (ENE Adaptation)")
    parser.add_argument("query", help="Vague natural language query")
    parser.add_argument("--phi", type=float, default=0.0, help="Informatic stress [0-1]")
    parser.add_argument("--docs", default=str(DOCS_DIR), help="Docs directory to index")
    args = parser.parse_args()

    engine = SeismicSearchEngine(phi=args.phi)
    print(f"[*] Indexing Sovereing Manifold (Target: {args.docs})...")
    engine.build_index(Path(args.docs))
    
    print(f"[*] Resonance Check (Query: '{args.query}', Phi: {args.phi})...")
    results = engine.search(args.query)
    
    if not results:
        print("[!] No conceptual resonance detected.")
    else:
        print("-" * 50)
        print(f"{'RESONANCE':<10} | {'FOUNDATIONAL AXIOM / DOCUMENT'}")
        print("-" * 50)
        for r in results:
            print(f"{r['score']:<10} | {r['doc']}")
        print("-" * 50)
