#!/usr/bin/env python3
"""N-space tuning manifest for the local physics/math/compression LLM.

The advantage of this stack is not just more examples. It is explicit
coordinate tooling: manifold deltas, oriented-volume adapters, fixed-width
hardware cells, n-dimensional behavioral vectors, and eigen-basis priors.
This script turns those into compact SFT curriculum records.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


NSPACE_AXES = [
    {
        "axis": "ns_md_hardware_delta",
        "dimension": "addressed manifold cell",
        "source": "0-Core-Formalism/otom/hardware/verilog/core/ns_md_decoder.v",
        "primitive": "[32-bit Addr][8-bit Control][optional Count][64-bit Witness]",
        "compression_use": "delta-coded manifold updates with nibble switch payloads",
        "receipt_rule": "addr/control/count/witness must survive transport",
    },
    {
        "axis": "oriented_volume_adapter",
        "dimension": "n-dimensional basis cell",
        "source": "0-Core-Formalism/otom/specs/Cramers-Rule-Oriented-Volume-Adapter.md",
        "primitive": "x_k = det(A_k) / det(A)",
        "compression_use": "coordinate extraction by shared reference-face cancellation",
        "receipt_rule": "det(A) nonzero and replacement-column index recorded",
    },
    {
        "axis": "behavioral_manifold_31",
        "dimension": "31 coordinates",
        "source": "0-Core-Formalism/otom/tools/lean/Semantics/Semantics/MarketFilter.lean",
        "primitive": "identity/conservation/transformation/scaling/dynamics coordinate blocks",
        "compression_use": "compare behavior by weighted fixed-point distance, not labels",
        "receipt_rule": "Q16.16 coordinates, weights, and claim state retained",
    },
    {
        "axis": "cross_domain_eigen_basis",
        "dimension": "term-domain similarity space",
        "source": "4-Infrastructure/shim/cross_domain_registry_eigenvectors.json",
        "primitive": "leading eigenvector over registry-derived term/domain matrix",
        "compression_use": "shared coordinates such as bond/matrix/geometry/provenance or kmer/long_context",
        "receipt_rule": "eigenvector is ranking prior only, never domain truth",
    },
    {
        "axis": "bitpack_hardware_cell",
        "dimension": "fixed bit width",
        "source": "6-Documentation/tiddlywiki-local/wiki/tiddlers/Lean BitPack Hardware Encoding.tid",
        "primitive": "value -> BitVec n -> UART/PBACS/Tang receipt",
        "compression_use": "turn symbolic/logogram tokens into witnessable fixed-width cells",
        "receipt_rule": "bit width and roundtrip representation must be explicit",
    },
]


PIPELINE_STAGES = [
    {
        "stage": "retrieve",
        "action": "load local registry/wiki/eigen/prover receipts",
        "failure_mode": "unverified memory or stale web claims",
    },
    {
        "stage": "embed_nspace",
        "action": "map candidate into an explicit coordinate axis",
        "failure_mode": "free prose without coordinates",
    },
    {
        "stage": "compress",
        "action": "choose shortest lawful payload: delta, kmer, bond matrix, bitpack cell, or template token",
        "failure_mode": "large chatty prompt instead of compact surface cell",
    },
    {
        "stage": "route",
        "action": "select Lean/source/Tang/Ollama/metaprobe channel by claim boundary",
        "failure_mode": "model confidence replacing receipts",
    },
    {
        "stage": "witness",
        "action": "emit JSON receipt and optional hardware receipt",
        "failure_mode": "summary without durable artifact",
    },
]


def existing_receipt_summary() -> dict[str, Any]:
    paths = [
        Path("4-Infrastructure/shim/metaprobe_physics_math_llm_direct_receipt.json"),
        Path("4-Infrastructure/shim/cross_domain_registry_eigenvectors.json"),
        Path("4-Infrastructure/shim/molecular_registry_eigenvectors.json"),
        Path("4-Infrastructure/shim/genomic_registry_eigenvectors.json"),
    ]
    out = {}
    for path in paths:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        out[str(path)] = {
            "schema": data.get("schema"),
            "lawful": data.get("lawful", data.get("overall_lawful")),
            "domain_count": data.get("domain_count"),
            "top_terms": [item.get("term") for item in data.get("top_terms", [])[:8]],
            "top_domains": [item.get("domain") for item in data.get("weighted_domains", [])[:5]],
        }
    return out


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are an n-space compression router. Return compact JSON with evidence boundaries."
    records = []
    for axis in receipt["nspace_axes"]:
        prompt = {
            "task": "route_with_nspace_axis",
            "axis": axis["axis"],
            "dimension": axis["dimension"],
            "primitive": axis["primitive"],
            "instruction": "Use this axis to compress and route a local research claim.",
        }
        answer = {
            "selected": True,
            "use_as": axis["compression_use"],
            "claim_boundary": "coordinate-routing-prior",
            "surface_payload_hint": axis["axis"][:16].upper(),
            "receipt_rule": axis["receipt_rule"],
        }
        records.append(chat_record(system, prompt, answer))

    prompt = {
        "task": "apply_nspace_pipeline",
        "pipeline": receipt["pipeline_stages"],
        "instruction": "Choose the pipeline behavior for tuning the local LLM.",
    }
    answer = {
        "selected": True,
        "use_as": "nspace_llm_pipeline_policy",
        "claim_boundary": "pipeline-guidance-only",
        "decision": "Prefer coordinate-bearing examples over prose-only examples; every answer should choose an axis, payload, route, and receipt.",
        "surface_payload_hint": "NSPACE-ROUTE",
    }
    records.append(chat_record(system, prompt, answer))
    return records


def chat_record(system: str, prompt: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/nspace_llm_pipeline_tuning_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/nspace_llm_pipeline_tuning_curriculum.jsonl"))
    args = parser.parse_args()

    receipt = {
        "schema": "nspace_llm_pipeline_tuning_receipt_v1",
        "claim_boundary": "N-space axes tune routing/compression behavior; they do not prove domain claims.",
        "nspace_axes": NSPACE_AXES,
        "pipeline_stages": PIPELINE_STAGES,
        "existing_receipts": existing_receipt_summary(),
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
