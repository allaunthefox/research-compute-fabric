#!/usr/bin/env python3
"""King Context retrieval prior for custom equation awareness.

King Context is recorded as a retrieval-shape prior: metadata-first search,
preview-before-full-read, learned shortcuts, and ADR memory. Locally, we apply
that shape to custom equation manifests so the LLM sees the right equations
without dumping the entire forest into context.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


KING_CONTEXT_PRIOR = {
    "id": "deandevz/king-context",
    "url": "https://github.com/deandevz/king-context",
    "role": "metadata_first_progressive_disclosure_retrieval_prior",
    "boundary": "repo-readme-prior-only",
    "local_use": "equation_manifest_search_preview_and_learned_shortcut_axis",
    "notes": [
        "README describes a local-first retrieval layer for AI agents.",
        "Core shape: search metadata before reading full content, preview roughly 400 tokens before full read, and avoid file dumps.",
        "Metadata fields include keywords, use_cases, tags, and priority.",
        "Includes ADR-style decision memory and learned shortcuts for repeated lookups.",
        "Benchmarks claim token-efficiency improvements versus Context7; local use requires our own receipts.",
    ],
}


RETRIEVAL_AXES = [
    {
        "axis": "metadata_first_equation_search",
        "payload": ["keywords", "primitive_hint", "claim_boundary", "source_path", "priority"],
        "router_use": "search equation manifest by metadata before loading equation text",
        "receipt_rule": "record query, matched metadata, source hash, preview hash, and full-read decision",
    },
    {
        "axis": "preview_before_full_equation",
        "payload": ["equation_preview", "context_budget", "full_read_gate", "source_hash"],
        "router_use": "show compact equation preview before pulling long docs or full source files",
        "receipt_rule": "record preview bytes/tokens and whether full source was read",
    },
    {
        "axis": "learned_equation_shortcuts",
        "payload": ["query_pattern", "equation_id", "source_path", "section_hint", "reuse_count"],
        "router_use": "cache repeated equation lookups for future model/scout passes",
        "receipt_rule": "shortcut must include source hash and invalidate on source hash change",
    },
    {
        "axis": "adr_equation_decision_memory",
        "payload": ["decision", "equation_ids", "claim_boundary", "promotion_gate", "timestamp"],
        "router_use": "preserve equation-routing decisions as durable ADR-like memory",
        "receipt_rule": "decision entries must list equations, gates, and blocked claims",
    },
]


def chat_record(system: str, prompt: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
        ]
    }


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are an equation retrieval router. Return compact JSON with source/hash boundaries."
    records = []
    for axis in receipt["retrieval_axes"]:
        records.append(
            chat_record(
                system,
                {
                    "task": "route_equation_retrieval_axis",
                    "axis": axis["axis"],
                    "payload": axis["payload"],
                    "instruction": "Use this retrieval shape before loading custom equations.",
                },
                {
                    "selected": True,
                    "use_as": axis["router_use"],
                    "claim_boundary": "retrieval-shape-prior-only",
                    "surface_payload_hint": axis["axis"][:16].upper(),
                    "receipt_rule": axis["receipt_rule"],
                },
            )
        )
    prior = receipt["king_context_prior"]
    records.append(
        chat_record(
            system,
            {
                "task": "use_king_context_prior",
                "repo": prior["id"],
                "role": prior["role"],
                "url": prior["url"],
                "instruction": "Map King Context's retrieval shape into local custom equation awareness.",
            },
            {
                "selected": True,
                "use_as": prior["local_use"],
                "claim_boundary": prior["boundary"],
                "metaprobe_rule": "Use metadata-first preview retrieval for equations; local token savings require our own measured receipts.",
            },
        )
    )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/king_context_equation_retrieval_prior_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/king_context_equation_retrieval_prior_curriculum.jsonl"))
    args = parser.parse_args()
    receipt = {
        "schema": "king_context_equation_retrieval_prior_v1",
        "claim_boundary": "King Context is a retrieval-shape prior for equation awareness; local performance must be measured.",
        "king_context_prior": KING_CONTEXT_PRIOR,
        "retrieval_axes": RETRIEVAL_AXES,
        "lawful": True,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
