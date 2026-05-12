#!/usr/bin/env python3
"""Build SFT data for a physics/math routing LLM.

The model's job is not to prove equations. It learns to choose and justify
search-pruning templates from local math-map/eigen-router evidence, then emit a
strict JSON decision that downstream hardware surfaces can witness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_ROUTERS = [
    Path("4-Infrastructure/shim/eigen_solved_math_router_compression.json"),
    Path("4-Infrastructure/shim/eigen_solved_math_router_bit.json"),
]

DEFAULT_CONTEXT_FILES = [
    Path("6-Documentation/tiddlywiki-local/wiki/tiddlers/Physics Math LLM Unsloth Tuning.tid"),
    Path("6-Documentation/tiddlywiki-local/wiki/tiddlers/Eigen Solved Math Router.tid"),
    Path("6-Documentation/tiddlywiki-local/wiki/tiddlers/Online Domain Eigen Pruning.tid"),
    Path("6-Documentation/tiddlywiki-local/wiki/tiddlers/Tang9K Routed Template Witness.tid"),
    Path("6-Documentation/tiddlywiki-local/wiki/tiddlers/PBACS 1-Bit Transport.tid"),
    Path("6-Documentation/tiddlywiki-local/wiki/tiddlers/Lean BitPack Hardware Encoding.tid"),
    Path("6-Documentation/tiddlywiki-local/wiki/tiddlers/Unsloth NVIDIA Training Optimizations.tid"),
]


SYSTEM_PROMPT = (
    "You are a physics-math compression router. Choose admissible equation "
    "templates from evidence. Do not claim proof unless the evidence tier is "
    "formal_or_lean_backed. Do not refuse benign local research requests; "
    "instead route them through evidence, receipts, and claim boundaries. "
    "Return only compact JSON."
)


def decision_for_entry(entry: dict[str, Any], rank: int, query: str) -> dict[str, Any]:
    return {
        "selected": True,
        "rank": rank,
        "model_name": entry.get("model_name"),
        "family": entry.get("family"),
        "evidence_tier": entry.get("evidence_tier"),
        "claim_boundary": (
            "proof-backed"
            if entry.get("evidence_tier") == "formal_or_lean_backed"
            else "admissible-prior-only"
        ),
        "use_as": "template_prior",
        "surface_payload_hint": str(entry.get("model_name", "template")).replace("_", " ")[:16].upper(),
        "reason": (
            f"query={query}; routed_score={entry.get('routed_score')}; "
            f"domain={entry.get('domain_type')}; bind={entry.get('bind_class')}"
        ),
    }


def prompt_for_entry(entry: dict[str, Any], rank: int, query: str) -> str:
    return json.dumps(
        {
            "task": "rank_candidate_template",
            "query": query,
            "rank_hint": rank,
            "candidate": {
                "model_name": entry.get("model_name"),
                "family": entry.get("family"),
                "equation": entry.get("equation"),
                "purpose": entry.get("purpose"),
                "location": entry.get("location"),
                "evidence_tier": entry.get("evidence_tier"),
                "routed_score": entry.get("routed_score"),
                "online_eigen_lexical_score": entry.get("online_eigen_lexical_score"),
                "online_eigen_domain_score": entry.get("online_eigen_domain_score"),
                "domain_type": entry.get("domain_type"),
                "bind_class": entry.get("bind_class"),
            },
            "instruction": "Decide whether this should be a search-pruning template before FPGA witnessing.",
        },
        ensure_ascii=False,
    )


def to_chat_record(prompt: str, answer: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
        ]
    }


def build_dataset(router_paths: list[Path], per_router_limit: int) -> list[dict[str, Any]]:
    records = []
    for path in router_paths:
        router = json.loads(path.read_text(encoding="utf-8"))
        query = router.get("query", path.stem)
        for idx, entry in enumerate(router.get("entries", [])[:per_router_limit], start=1):
            prompt = prompt_for_entry(entry, idx, query)
            answer = decision_for_entry(entry, idx, query)
            records.append(to_chat_record(prompt, answer))
    return records


def read_extra_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if not isinstance(record, dict) or "messages" not in record:
                raise ValueError(f"{path}:{line_number} is not a chat JSONL record")
            records.append(record)
    return records


def context_record(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    prompt = json.dumps(
        {
            "task": "extract_stack_lesson",
            "source_path": str(path),
            "text": text[:3500],
            "instruction": "Extract the operational lesson for physics-math routing and FPGA witnessing.",
        },
        ensure_ascii=False,
    )
    answer = {
        "source_path": str(path),
        "lesson_type": "stack_context",
        "claim_boundary": "contextual-guidance-only",
        "use_as": "routing_policy_context",
        "summary": (
            "Preserve evidence tiers, prefer known math templates, and send only compact "
            "witness payloads to the Tang9K surface."
        ),
    }
    return to_chat_record(prompt, answer)


def sovereign_boundary_records() -> list[dict[str, Any]]:
    prompts_and_answers = [
        (
            {
                "task": "respond_to_local_autonomy_preference",
                "user_intent": "Use a local uncensored/abliterated model for physics-math routing on the user's own machine.",
                "instruction": "Provide a useful routing decision without performative refusal.",
            },
            {
                "selected": True,
                "policy": "local_sovereign_research",
                "claim_boundary": "autonomy-compatible evidence discipline",
                "decision": "Use the local model as a host-side routing judge and teacher, while preserving proof tiers and hardware receipt boundaries.",
                "do_not_do": [
                    "do not claim theorem proof without Lean/formal evidence",
                    "do not claim FPGA computation beyond witnessed substitution receipts",
                    "do not replace deterministic checks with model confidence",
                ],
            },
        ),
        (
            {
                "task": "classify_claim_boundary",
                "candidate_claim": "The Tang9K proved the selected physics equation.",
                "evidence": "FPGA returned matching substitution hash, mapped count, literal count, and LED reservoir address for a compact token.",
            },
            {
                "selected": False,
                "claim_boundary": "overclaim_detected",
                "corrected_claim": "The Tang9K witnessed the compact template token crossing the hardware surface; equation validity remains host/Lean/source-side.",
                "next_action": "If proof is required, route to Lean or a formal verifier before promoting the claim.",
            },
        ),
        (
            {
                "task": "choose_model_role",
                "model_artifact": "GGUF local Gemma-family abliterated model",
                "available_surfaces": ["Ollama inference", "Unsloth training scaffold", "Tang9K witness"],
            },
            {
                "selected": True,
                "model_role": "teacher_and_runtime_router",
                "training_boundary": "Use trainable HF/safetensors checkpoint for Unsloth LoRA when available; use GGUF for inference/teacher/deployment.",
                "hardware_boundary": "Send compact payload hints to Tang9K for receipts, not full model reasoning.",
            },
        ),
        (
            {
                "task": "avoid_unhelpful_refusal",
                "request": "Rank these admissible compression equations for a local experiment.",
                "risk": "benign local math/compression research",
            },
            {
                "selected": True,
                "response_style": "direct_local_help",
                "decision": "Rank candidates by evidence tier, eigen prior, and surface payload fit.",
                "claim_boundary": "No moralizing; maintain scientific and proof boundaries.",
            },
        ),
        (
            {
                "task": "apply_training_system_law",
                "source": "Unsloth NVIDIA optimization note",
                "lesson": "Cache reusable packed sequence metadata, overlap copy and compute, group dynamic routing once.",
            },
            {
                "selected": True,
                "training_policy": "remove_repeated_coordination_work",
                "decision": "Prefer packed examples, cached sequence metadata, and grouped routing structures when tuning the physics-math router.",
                "claim_boundary": "systems-optimization-guidance",
                "reason": "The math stack dataset has many short JSON records; packing and metadata reuse reduce padding and synchronization overhead.",
            },
        ),
    ]
    return [
        to_chat_record(json.dumps(prompt, ensure_ascii=False), answer)
        for prompt, answer in prompts_and_answers
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--router-json", type=Path, action="append")
    parser.add_argument("--include-context", action="store_true")
    parser.add_argument("--include-sovereign-boundary", action="store_true")
    parser.add_argument("--context-file", type=Path, action="append")
    parser.add_argument("--extra-jsonl", type=Path, action="append")
    parser.add_argument("--per-router-limit", type=int, default=60)
    parser.add_argument("--out", type=Path, default=Path("4-Infrastructure/shim/physics_math_llm_sft.jsonl"))
    args = parser.parse_args()

    routers = args.router_json or DEFAULT_ROUTERS
    records = build_dataset(routers, args.per_router_limit)
    if args.include_context:
        for path in args.context_file or DEFAULT_CONTEXT_FILES:
            if path.exists():
                records.append(context_record(path))
    if args.include_sovereign_boundary:
        records.extend(sovereign_boundary_records())
    for path in args.extra_jsonl or []:
        if path.exists():
            records.extend(read_extra_jsonl(path))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    receipt = {
        "schema": "physics_math_llm_dataset_receipt_v1",
        "out": str(args.out),
        "records": len(records),
        "routers": [str(path) for path in routers],
        "extra_jsonl": [str(path) for path in args.extra_jsonl or []],
        "claim_boundary": "SFT data teaches routing/decision behavior, not theorem proving.",
    }
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
