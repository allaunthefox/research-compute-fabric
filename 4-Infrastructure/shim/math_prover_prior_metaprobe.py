#!/usr/bin/env python3
"""External math/prover prior metaprobe.

This keeps model cards and theorem-search services in their proper role:
external priors for routing, retrieval, and curriculum construction. They do
not prove local claims unless a local formal checker accepts a proof artifact.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any


THEOREMSEARCH_URL = "https://api.theoremsearch.com/search"

MODEL_PRIORS = [
    {
        "id": "deepseek-ai/DeepSeek-Math-V2",
        "url": "https://huggingface.co/deepseek-ai/DeepSeek-Math-V2",
        "role": "self_verifiable_math_reasoning_prior",
        "local_use": "teacher_or_comparator_for_math_reasoning_style",
        "boundary": "model-card/evaluation-prior-only",
        "notes": [
            "Apache-2.0 Hugging Face model card.",
            "Model card emphasizes self-verification and theorem-proving style reasoning.",
            "Use as a source of verifier/generator separation patterns, not as local proof.",
        ],
    },
    {
        "id": "VladShash/deepseek-math-7b-lean-prover-dpo-olmo-3",
        "url": "https://huggingface.co/VladShash/deepseek-math-7b-lean-prover-dpo-olmo-3",
        "role": "lean_prover_dpo_prior",
        "local_use": "candidate teacher/comparator for Lean-shaped proof proposals",
        "boundary": "small-community-finetune-prior-only",
        "notes": [
            "Hugging Face card identifies a 7B safetensors model trained with TRL/DPO.",
            "Useful for proof-proposal style and preference data shape.",
            "Any generated Lean must still be checked by lake/Lean locally.",
        ],
    },
    {
        "id": "Zyphra/ZAYA1-8B",
        "url": "https://huggingface.co/Zyphra/ZAYA1-8B",
        "role": "small_moe_reasoning_model_prior",
        "local_use": "candidate_local_decision_model_for_test_time_compute_harnesses",
        "boundary": "model-card/evaluation-prior-only",
        "notes": [
            "Apache-2.0 Hugging Face model card.",
            "Model card describes 760M active parameters and 8.4B total parameters in a small mixture-of-experts language model.",
            "Model card emphasizes math, coding, long-form reasoning, on-device deployment, and test-time compute harness usefulness.",
            "Use as a local candidate/comparator for routing decisions; every output still needs metaprobe, source, Lean, or hardware receipts.",
        ],
    },
]

DATASET_PRIORS = [
    {
        "id": "huggingface/datasets?other=mathematics",
        "url": "https://huggingface.co/datasets?other=mathematics",
        "role": "math_dataset_discovery_registry_prior",
        "local_use": "dataset_search_axis_for_future_sampling",
        "boundary": "registry-prior-only",
        "notes": [
            "The Hugging Face mathematics dataset filter listed 350 active-filter results when checked.",
            "Trending examples included MathNet, proof-pile, MathVision, MathVista, Big-Math-RL-Verified, PolyMath, autoformalization, Coq facts/proofs, and DART math pools.",
            "Use as a discovery index for sampling candidates, not as an ingested corpus.",
            "Each candidate still needs license, schema, provenance, and contamination checks before local SFT use.",
        ],
    },
    {
        "id": "huggingface/datasets?other=chemistry&sort=trending",
        "url": "https://huggingface.co/datasets?other=chemistry&sort=trending",
        "role": "chemistry_dataset_discovery_registry_prior",
        "local_use": "molecular_physics_constraint_axis_for_future_sampling",
        "boundary": "registry-prior-only",
        "notes": [
            "The Hugging Face chemistry dataset filter listed 1,514 active-filter results when checked.",
            "Trending examples included ChemBench, drug-target-activity, ScienceQA, mdCATH, GeMS, material trajectories, QM9, binding affinity, and protein-ligand datasets.",
            "Use as a discovery index for physics/chemistry constraint corpora and molecular/field analogies, not as an ingested corpus.",
            "Each candidate needs modality, unit, license, provenance, leakage, and safety/domain checks before local SFT use.",
        ],
    },
    {
        "id": "huggingface/datasets?other=finance&sort=trending",
        "url": "https://huggingface.co/datasets?other=finance&sort=trending",
        "role": "finance_dataset_discovery_registry_prior",
        "local_use": "time_series_risk_and_market_signal_axis_for_future_sampling",
        "boundary": "registry-prior-only",
        "notes": [
            "The Hugging Face finance dataset filter listed 1,414 active-filter results when checked.",
            "Trending examples included EvasionBench, APEX agents, Twitter financial sentiment, Yahoo finance data, Finance-Instruct-500k, EDGAR corpus, crypto datasets, and transaction categorization.",
            "Use as a discovery index for time-series, risk, anomaly, and economic-signal routing tests.",
            "Finance examples must stay evaluation/simulation data unless separately validated; do not convert dataset priors into financial advice.",
        ],
    },
    {
        "id": "huggingface/datasets?sort=trending",
        "url": "https://huggingface.co/datasets?sort=trending",
        "role": "global_dataset_trending_drift_prior",
        "local_use": "registry_drift_detector_and_negative_control_axis",
        "boundary": "registry-prior-only",
        "notes": [
            "The global Hugging Face trending dataset page listed 994,526 datasets when checked.",
            "Trending examples spanned agent traces, synthetic reasoning, CAD, court/legal, SWE, MathNet, GSM8K, health, FineWeb-Edu, and C4.",
            "Use as a broad drift detector to see what corpus families are becoming common around the local stack.",
            "Do not sample directly from global trending without a domain filter, schema inspection, license check, and contamination check.",
        ],
    },
    {
        "id": "nvidia/Nemotron-SFT-Math-v3",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-SFT-Math-v3",
        "role": "large_scale_math_sft_curriculum_prior",
        "local_use": "sampling_schema_and_reasoning_mode_prior",
        "boundary": "dataset-card/corpus-prior-only",
        "notes": [
            "Hugging Face card describes a JSONL math reasoning dataset with messages, expected answers, provenance, license, tool usage, and source URLs.",
            "Dataset card reports 3,638,783 train samples and roughly 144 GB disk size; ingest should be sampled/streamed, not eagerly mirrored into the repo.",
            "Useful distinction: with Python TIR vs without Python TIR reasoning modes.",
            "Reference-answer matching is useful supervision hygiene but not a local proof receipt.",
        ],
    },
    {
        "id": "ShadenA/MathNet",
        "url": "https://huggingface.co/datasets/ShadenA/MathNet",
        "role": "multimodal_olympiad_problem_topology_prior",
        "local_use": "topic_country_competition_problem_type_schema_prior",
        "boundary": "dataset-card/topology-prior-only",
        "notes": [
            "Hugging Face card exposes parquet data with text and image modalities.",
            "Viewer reports about 27.8k rows, 59 subsets, country/competition/topic/language/problem_type fields, and olympiad/retrieval tags.",
            "Useful for graph-shaped curriculum buckets: combinatorics, geometry, algebra, olympiad source, language, and proof-only vs proof-and-answer.",
            "Images and licenses/provenance need explicit handling before any local mirror or training ingest.",
        ],
    },
]


QUERIES = [
    "graph minimum degree at least three cycle length power of two",
    "covering systems odd moduli Erdos Selfridge conjecture",
    "formal theorem graph cycle length Lean theorem",
]


def theorem_search(query: str, n_results: int) -> dict[str, Any]:
    body = json.dumps({"query": query, "n_results": n_results}).encode("utf-8")
    req = urllib.request.Request(
        THEOREMSEARCH_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Research-Stack-Math-Prover-Metaprobe/0.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def compact_theorem_result(result: dict[str, Any]) -> dict[str, Any]:
    compact = []
    for theorem in result.get("theorems", [])[:5]:
        paper = theorem.get("paper") or {}
        compact.append(
            {
                "name": theorem.get("name"),
                "theorem_type": theorem.get("theorem_type"),
                "slogan": theorem.get("slogan"),
                "link": theorem.get("link"),
                "score": theorem.get("score"),
                "source": paper.get("source"),
                "paper_title": paper.get("title"),
                "category": paper.get("primary_category"),
                "year": paper.get("year"),
            }
        )
    return {"theorems": compact}


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a physics-math proof router. Return compact JSON with evidence boundaries."
    records = []
    for prior in receipt["model_priors"]:
        prompt = {
            "task": "use_external_math_model_prior",
            "model": prior["id"],
            "role": prior["role"],
            "url": prior["url"],
            "instruction": "Explain how this model should influence local proof/search routing without becoming proof.",
        }
        answer = {
            "selected": True,
            "use_as": prior["local_use"],
            "claim_boundary": prior["boundary"],
            "metaprobe_rule": "Generated math/proof text must be checked by local Lean/source/verifier receipts before promotion.",
        }
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
                ]
            }
        )
    for prior in receipt["dataset_priors"]:
        prompt = {
            "task": "use_external_math_dataset_prior",
            "dataset": prior["id"],
            "role": prior["role"],
            "url": prior["url"],
            "instruction": "Explain how this corpus should influence local SFT sampling without replacing local receipts.",
        }
        answer = {
            "selected": True,
            "use_as": prior["local_use"],
            "claim_boundary": prior["boundary"],
            "sampling_rule": "Prefer small provenance-preserving samples first; keep source/license/tool_usage fields; separate TIR from non-TIR examples.",
            "metaprobe_rule": "Corpus examples train reasoning style and answer discipline; local theorem claims still require Lean/source/hardware receipts.",
        }
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
                ]
            }
        )
    prompt = {
        "task": "use_theoremsearch_prior",
        "queries": list(receipt["theoremsearch"].keys()),
        "instruction": "Explain how semantic theorem search should shrink local Erdős/prover search.",
    }
    answer = {
        "selected": True,
        "use_as": "retrieval_prior",
        "claim_boundary": "retrieved-theorem-context-only",
        "metaprobe_rule": "Use TheoremSearch results to suggest adjacent theorem neighborhoods and dependency probes; verify any imported statement locally.",
    }
    records.append(
        {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
            ]
        }
    )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-results", type=int, default=3)
    parser.add_argument("--no-live-search", action="store_true")
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/math_prover_prior_metaprobe_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/math_prover_prior_curriculum.jsonl"))
    args = parser.parse_args()

    theorem_results: dict[str, Any] = {}
    errors: dict[str, str] = {}
    if not args.no_live_search:
        for query in QUERIES:
            try:
                theorem_results[query] = compact_theorem_result(theorem_search(query, args.n_results))
            except Exception as exc:  # noqa: BLE001 - receipt should preserve network/API failures.
                errors[query] = f"{type(exc).__name__}: {exc}"

    receipt = {
        "schema": "math_prover_prior_metaprobe_receipt_v1",
        "claim_boundary": "External math models and theorem-search hits are routing priors, not local proofs.",
        "model_priors": MODEL_PRIORS,
        "dataset_priors": DATASET_PRIORS,
        "theoremsearch": theorem_results,
        "theoremsearch_errors": errors,
        "lawful": bool(MODEL_PRIORS) and (args.no_live_search or bool(theorem_results) or bool(errors)),
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
