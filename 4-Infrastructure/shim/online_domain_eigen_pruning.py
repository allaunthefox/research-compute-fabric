#!/usr/bin/env python3
"""Spectral pruning over adjacent online compression/math domains.

The input is a small, source-backed set of peer-reviewed/standards-adjacent
domain priors. The script builds a term-domain matrix, computes the leading
eigenvector of the domain similarity matrix, and emits weighted terms/domains
that can shrink later compression/logogram/FPGA searches.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]{2,}")


DEFAULT_DOMAINS: list[dict[str, str]] = [
    {
        "domain": "minimum_description_length",
        "equation": "argmin_M L(M) + L(D | M)",
        "role": "model selection prior; choose the shortest lawful template before encoding",
        "source": "Grunwald, Model Selection Based on Minimum Description Length, Journal of Mathematical Psychology, 2000",
        "url": "https://www.sciencedirect.com/science/article/abs/pii/S0022249699912804",
    },
    {
        "domain": "arithmetic_entropy_coding",
        "equation": "message -> interval with subinterval widths proportional to symbol probabilities",
        "role": "baseline entropy coder and probability weighting model",
        "source": "Youssef, Parallel Algorithms for Entropy-Coding Techniques, NIST, 1998",
        "url": "https://www.nist.gov/publications/parallel-algorithms-entropy-coding-techniques",
    },
    {
        "domain": "asymmetric_numeral_systems",
        "equation": "state-machine entropy coding with symbol-state allocation f_s ~= p_s R",
        "role": "finite-state entropy coding, table/LUT-adjacent for hardware",
        "source": "Pieprzyk et al., The Compression Optimality of Asymmetric Numeral Systems, Entropy, 2023",
        "url": "https://www.mdpi.com/1099-4300/25/4/672",
    },
    {
        "domain": "simd_bp128_bitpacking",
        "equation": "block_width = ceil(log2(max(block)+1)); pack N integers at block_width bits",
        "role": "lane-width prior for GPU/FPGA integer surfaces",
        "source": "Lemire and Boytsov, Decoding billions of integers per second through vectorization, Software: Practice and Experience, 2015",
        "url": "https://arxiv.org/abs/1209.2137",
    },
    {
        "domain": "bounce_lightweight_integer_compression",
        "equation": "compress k separate blocks of size N across SIMD lanes to preserve scalar ratio",
        "role": "partitioned lane layout prior for avoiding wide-register ratio loss",
        "source": "Bittner et al., BOUNCE: memory-efficient SIMD approach for lightweight integer compression, Distributed and Parallel Databases, 2023",
        "url": "https://link.springer.com/article/10.1007/s10619-023-07426-0",
    },
    {
        "domain": "delta_sigma_one_bit",
        "equation": "b_t = Q(v_t + e_{t-1}); e_t = v_t + e_{t-1} - b_t",
        "role": "1-bit residual-feedback transport prior, adjacent to PBACS",
        "source": "Zierhofer, Adaptive Delta-Sigma Modulation for Enhanced Input Dynamic Range, EURASIP JASP, 2008",
        "url": "https://link.springer.com/article/10.1155/2008/439203",
    },
    {
        "domain": "normalized_compression_distance",
        "equation": "NCD_Z(x,y) = (Z(xy) - min(Z(x), Z(y))) / max(Z(x), Z(y))",
        "role": "compressor-backed similarity gate for choosing nearby templates",
        "source": "Cilibrasi and Vitanyi, Clustering by Compression, IEEE Transactions on Information Theory, 2005",
        "url": "https://ir.cwi.nl/pub/16389",
    },
]


STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "into",
    "that",
    "this",
    "through",
    "using",
    "based",
    "source",
    "journal",
    "transactions",
    "systems",
    "compression",
    "coding",
}


def tokenize(text: str) -> list[str]:
    tokens = []
    for match in TOKEN_RE.finditer(text.lower()):
        token = match.group(0).strip("_+-")
        if token and token not in STOPWORDS:
            tokens.append(token)
    return tokens


def leading_eigenvector(matrix: list[list[float]], iterations: int = 80) -> list[float]:
    n = len(matrix)
    vec = [1.0 / math.sqrt(n)] * n
    for _ in range(iterations):
        nxt = [sum(matrix[i][j] * vec[j] for j in range(n)) for i in range(n)]
        norm = math.sqrt(sum(x * x for x in nxt)) or 1.0
        vec = [x / norm for x in nxt]
    total = sum(abs(x) for x in vec) or 1.0
    return [abs(x) / total for x in vec]


def build_surface(domains: list[dict[str, str]]) -> dict[str, Any]:
    docs = []
    df: Counter[str] = Counter()
    for item in domains:
        text = " ".join([item["domain"], item["equation"], item["role"], item["source"]])
        counts = Counter(tokenize(text))
        docs.append(counts)
        df.update(counts.keys())

    vocab = sorted(df)
    n_docs = len(docs)
    vectors = []
    for counts in docs:
        total = sum(counts.values()) or 1
        vector = []
        for token in vocab:
            tf = counts[token] / total
            idf = math.log((1 + n_docs) / (1 + df[token])) + 1
            vector.append(tf * idf)
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        vectors.append([x / norm for x in vector])

    sim = []
    for left in vectors:
        row = []
        for right in vectors:
            row.append(sum(a * b for a, b in zip(left, right)))
        sim.append(row)

    domain_weights = leading_eigenvector(sim)
    term_scores: Counter[str] = Counter()
    for weight, vector in zip(domain_weights, vectors):
        for token, value in zip(vocab, vector):
            term_scores[token] += weight * value

    weighted_domains = []
    for item, weight in sorted(zip(domains, domain_weights), key=lambda pair: -pair[1]):
        weighted_domains.append({**item, "eigen_weight": weight})

    return {
        "schema": "online_domain_eigen_pruning_v1",
        "claim_boundary": "Leading eigenvector is a ranking prior over adjacent source-backed domains, not proof of correctness.",
        "domain_count": len(domains),
        "weighted_domains": weighted_domains,
        "top_terms": [
            {"term": term, "weight": weight}
            for term, weight in term_scores.most_common(40)
        ],
        "domain_similarity_matrix": sim,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--limit-terms", type=int, default=40)
    args = parser.parse_args()

    surface = build_surface(DEFAULT_DOMAINS)
    surface["top_terms"] = surface["top_terms"][: args.limit_terms]
    text = json.dumps(surface, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
