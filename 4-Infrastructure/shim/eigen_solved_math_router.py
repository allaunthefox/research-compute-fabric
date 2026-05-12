#!/usr/bin/env python3
"""Route local math models through the online-domain eigen prior.

This combines:
  1. local admissible rows from MATH_MODEL_MAP.tsv, and
  2. the source-backed online domain eigenvector from online_domain_eigen_pruning.py.

The output is a ranked shortlist of local templates to try before widening a
compression/logogram/FPGA search.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import online_domain_eigen_pruning as eigen
import solved_math_pruning_surface as solved


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]{2,}")


def tokenize(text: str) -> set[str]:
    return {
        token.strip("_+-").lower()
        for token in TOKEN_RE.findall(text)
        if token.strip("_+-").lower() and token.strip("_+-").lower() not in eigen.STOPWORDS
    }


def load_eigen(path: Path | None) -> dict[str, Any]:
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return eigen.build_surface(eigen.DEFAULT_DOMAINS)


def entry_text(entry: dict[str, Any]) -> str:
    fields = [
        "model_name",
        "family",
        "equation",
        "variables",
        "purpose",
        "domain_type",
        "bind_class",
        "implemented",
    ]
    return " ".join(str(entry.get(field, "")) for field in fields)


def route_entries(local_index: dict[str, Any], eigen_index: dict[str, Any]) -> dict[str, Any]:
    term_weights = {item["term"]: float(item["weight"]) for item in eigen_index.get("top_terms", [])}
    domain_weights = {
        item["domain"]: float(item["eigen_weight"])
        for item in eigen_index.get("weighted_domains", [])
    }

    routed = []
    for entry in local_index.get("entries", []):
        tokens = tokenize(entry_text(entry))
        lexical = sum(weight for term, weight in term_weights.items() if term in tokens)

        domain_hit = 0.0
        joined = entry_text(entry).lower()
        for domain, weight in domain_weights.items():
            domain_tokens = set(domain.split("_"))
            if domain in joined or domain_tokens.intersection(tokens):
                domain_hit += weight

        evidence_component = float(entry.get("pruning_score", 0)) / 100.0
        score = evidence_component + lexical + 0.75 * domain_hit
        routed.append(
            {
                **entry,
                "online_eigen_lexical_score": lexical,
                "online_eigen_domain_score": domain_hit,
                "routed_score": score,
            }
        )

    routed.sort(key=lambda item: (-item["routed_score"], item["model_name"]))
    return {
        "schema": "eigen_solved_math_router_v1",
        "claim_boundary": "Ranking combines local evidence tiers and online eigen priors; it is a search-order hint, not a proof.",
        "local_source": local_index.get("source"),
        "online_source_schema": eigen_index.get("schema"),
        "query": local_index.get("query"),
        "entry_count": len(routed),
        "top_online_domains": eigen_index.get("weighted_domains", [])[:5],
        "entries": routed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-map", type=Path, default=solved.DEFAULT_MODEL_MAP)
    parser.add_argument("--eigen-json", type=Path, default=Path("4-Infrastructure/shim/online_domain_eigen_pruning.json"))
    parser.add_argument("--query", default="compression")
    parser.add_argument("--include-documented", action="store_true")
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    local = solved.build_index(
        solved.load_rows(args.model_map),
        query=args.query,
        include_documented=args.include_documented,
    )
    local["source"] = str(args.model_map)
    eig = load_eigen(args.eigen_json)
    routed = route_entries(local, eig)
    if args.limit >= 0:
        routed["entries"] = routed["entries"][: args.limit]
    text = json.dumps(routed, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
