#!/usr/bin/env python3
"""LLM compression architecture priors for n-space/metaprobe tuning.

These records keep the useful part of prompt, latent, and weight-compression
research: routing coordinates for a local compression-first LLM stack. They do
not claim any model is "intelligent" by itself, and they do not bypass receipts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


COMPRESSION_AXES = [
    {
        "axis": "symbolic_metalanguage",
        "payload": ["logic_symbol", "constraint", "operator", "scope", "semantic_receipt"],
        "router_use": "compress verbose instructions into logogram/symbolic control cells",
        "receipt_rule": "round-trip through expanded natural-language paraphrase and task-result check",
    },
    {
        "axis": "prompt_token_pruning",
        "payload": ["token_importance", "budget", "query_focus", "retained_span", "compression_ratio"],
        "router_use": "strip low-information prompt volume before routing into expensive models",
        "receipt_rule": "record source bytes, retained bytes, compression ratio, and downstream quality delta",
    },
    {
        "axis": "information_bottleneck",
        "payload": ["input_information", "target_information", "latent_state", "mutual_information_proxy", "distortion"],
        "router_use": "tune representations toward useful lossy compression instead of string memorization",
        "receipt_rule": "record proxy metric, retained-task score, and distortion/error budget",
    },
    {
        "axis": "system_class_compression",
        "payload": ["statistical_structure", "indexical_structure", "semantic_basin", "reconstruction_block", "policy_boundary"],
        "router_use": "preserve reusable statistical structure while refusing exact source reconstruction as a routing goal",
        "receipt_rule": "store source provenance, no-verbatim reconstruction rule, and similarity/audit check",
    },
    {
        "axis": "weight_palette_transcoding",
        "payload": ["weight_distribution", "exponent_palette", "codebook", "decode_path", "memory_bandwidth"],
        "router_use": "treat model weights as hardware-visible compressed palettes for inference surfaces",
        "receipt_rule": "record lossless/lossy status, decode cost, memory saved, and benchmark delta",
    },
    {
        "axis": "proxy_compressed_views",
        "payload": ["raw_bytes", "compressed_view", "alignment_loss", "decompress_hint", "view_id"],
        "router_use": "train the model to align raw text with compressed metaprobe/logogram views",
        "receipt_rule": "record compressor version, raw/compressed pairs, and equivalence-test prompts",
    },
    {
        "axis": "math_display_list_canonicalization",
        "payload": ["latex_source", "parse_node", "layout_box", "display_list", "render_receipt"],
        "router_use": "canonicalize math/logogram strings into renderer-independent symbolic display cells",
        "receipt_rule": "record parser version, source hash, display-list hash, and optional PNG/SVG/PDF render hash",
    },
]


VERIFIED_COMPRESSION_PRIORS = [
    {
        "id": "MetaGlyph",
        "role": "symbolic_metalanguage_prompt_compression",
        "boundary": "paper-prior-only",
        "use_as": "symbolic_logogram_prompt_axis",
        "source": "Semantic Compression of LLM Instructions via Symbolic Metalanguages",
        "url": "https://arxiv.org/abs/2601.07354",
        "notes": "Use mathematical/logical symbols as dense instruction primitives; candidate prior for custom logogram language.",
    },
    {
        "id": "LLMLingua",
        "role": "coarse_to_fine_prompt_compression",
        "boundary": "paper/project-prior-only",
        "use_as": "prompt_budget_and_token_importance_axis",
        "source": "LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models",
        "url": "https://arxiv.org/abs/2310.05736",
        "notes": "Budget controller and token-level prompt compression; useful baseline for metaprobe text compression.",
    },
    {
        "id": "LLMLingua-2",
        "role": "task_agnostic_prompt_compression",
        "boundary": "paper/project-prior-only",
        "use_as": "task_agnostic_token_classifier_axis",
        "source": "LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression",
        "url": "https://arxiv.org/abs/2403.12968",
        "notes": "Treats compression as token classification distilled for general prompt compression.",
    },
    {
        "id": "SelectiveContext",
        "role": "context_redundancy_pruning",
        "boundary": "paper-prior-only",
        "use_as": "context_redundancy_filter_axis",
        "source": "Compressing Context to Enhance Inference Efficiency of Large Language Models",
        "url": "https://arxiv.org/abs/2310.06201",
        "notes": "Prunes redundant context; good negative-control baseline against richer metaprobe compression.",
    },
    {
        "id": "LanguageModelingIsCompression",
        "role": "prediction_compression_equivalence",
        "boundary": "paper-prior-only",
        "use_as": "lm_as_compressor_objective_axis",
        "source": "Language Modeling Is Compression",
        "url": "https://arxiv.org/abs/2309.10668",
        "notes": "Useful objective lens: language modeling and compression are linked; not a direct model recipe.",
    },
    {
        "id": "InformationBottleneckLLM",
        "role": "representation_information_flow_lens",
        "boundary": "paper-prior-only",
        "use_as": "latent_information_bottleneck_axis",
        "source": "Exploring Information Processing in Large Language Models: Insights from Information Bottleneck Theory",
        "url": "https://arxiv.org/abs/2501.00999",
        "notes": "Use as measurement lens for retained information versus distortion in latent/control surfaces.",
    },
    {
        "id": "ProxyCompression",
        "role": "raw_and_compressed_view_training",
        "boundary": "paper-prior-only",
        "use_as": "raw_compressed_alignment_axis",
        "source": "Proxy Compression for Language Modeling",
        "url": "https://arxiv.org/abs/2602.04289",
        "notes": "Train against raw bytes and externally compressed views; close match to metaprobe/logogram pairs.",
    },
    {
        "id": "Unweight",
        "role": "lossless_mlp_weight_compression",
        "boundary": "paper-prior-only",
        "use_as": "weight_palette_transcoding_axis",
        "source": "Unweight: Lossless MLP Weight Compression for LLM Inference",
        "url": "https://research.cloudflare.com/papers/unweight-2026.pdf",
        "notes": "Hardware-level prior for compressed BF16/MLP weight movement; verify implementation before any speed claim.",
    },
    {
        "id": "RaTeX",
        "role": "rust_native_latex_math_display_list_renderer",
        "boundary": "repo-prior-only",
        "use_as": "math_logogram_canonicalization_axis",
        "source": "RaTeX: KaTeX-compatible math rendering engine in pure Rust",
        "url": "https://github.com/erweixin/RaTeX",
        "notes": "Useful as a Rust-native LaTeX/math/chemistry token canonicalizer into display lists; render artifacts can serve as visual receipts.",
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
    system = "You are a compression-first LLM router. Return compact JSON with receipt boundaries."
    records: list[dict[str, Any]] = []
    for axis in receipt["compression_axes"]:
        records.append(
            chat_record(
                system,
                {
                    "task": "route_compression_axis",
                    "axis": axis["axis"],
                    "payload": axis["payload"],
                    "instruction": "Use this as a metaprobe/logogram compression coordinate.",
                },
                {
                    "selected": True,
                    "use_as": axis["router_use"],
                    "claim_boundary": "compression-coordinate-prior-only",
                    "surface_payload_hint": axis["axis"][:16].upper(),
                    "receipt_rule": axis["receipt_rule"],
                },
            )
        )
    for prior in receipt["verified_compression_priors"]:
        records.append(
            chat_record(
                system,
                {
                    "task": "use_llm_compression_prior",
                    "model_or_lens": prior["id"],
                    "role": prior["role"],
                    "source": prior["source"],
                    "instruction": "Explain how this tunes the local LLM pipeline without replacing receipts.",
                },
                {
                    "selected": True,
                    "use_as": prior["use_as"],
                    "claim_boundary": prior["boundary"],
                    "metaprobe_rule": "Use as architecture/corpus coordinate; verify with compression ratio, quality delta, and source receipts.",
                },
            )
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/llm_compression_architecture_prior_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/llm_compression_architecture_prior_curriculum.jsonl"))
    args = parser.parse_args()

    receipt = {
        "schema": "llm_compression_architecture_prior_receipt_v1",
        "claim_boundary": "Compression architecture priors tune prompt/logogram/metaprobe routing; they are not local performance proof.",
        "compression_axes": COMPRESSION_AXES,
        "verified_compression_priors": VERIFIED_COMPRESSION_PRIORS,
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
