#!/usr/bin/env python3
"""External AI model prior ingest for Hutter/topology routing.

This probe records outside model/paper links as priors only. It does not import
weights, run external code, or promote an external result into the stack. The
goal is to keep DMax, NTv3, and PhysMaster as typed HOLD surfaces with explicit
promotion gates.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "external_ai_model_prior_ingest"
RECEIPT = OUT_DIR / "external_ai_model_prior_ingest_receipt.json"
SUMMARY = OUT_DIR / "external_ai_model_prior_ingest.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "External AI Model Prior Ingest.tid"

PRIORS = [
    {
        "prior_id": "DMax.parallel_self_revision",
        "title": "DMax: Aggressive Parallel Decoding for dLLMs",
        "sources": [
            "https://arxiv.org/pdf/2604.08302",
            "https://github.com/czg1225/DMax",
            "https://huggingface.co/collections/Zigeng/dmax-training-data",
            "https://huggingface.co/collections/Zigeng/dmax-models",
        ],
        "observed_claim": (
            "DMax reframes dLLM decoding as self-revising embedding-space refinement "
            "with on-policy uniform training and soft parallel decoding."
        ),
        "stack_mapping": [
            "hutter_differential_frame_chain",
            "hutter_frame_invariant_root",
            "parallel_route_repair",
            "self_revision_without_truth_promotion",
        ],
        "use_as": "decoding_parallelism_prior",
        "decision": "HOLD_EXTERNAL_DECODING_PRIOR",
        "promotion_gate": (
            "local benchmark required: exact replay, counted bytes, baseline comparison, "
            "resource envelope, and deterministic receipt over any adapted decoding path"
        ),
    },
    {
        "prior_id": "NTv3.long_range_sequence_function",
        "title": "A foundational model for joint sequence-function multi-species modeling at scale for long-range genomic prediction",
        "sources": [
            "https://www.biorxiv.org/content/10.64898/2025.12.22.695963v1",
            "https://huggingface.co/spaces/InstaDeepAI/ntv3",
            "https://huggingface.co/collections/InstaDeepAI/nucleotide-transformer-v3",
            "https://github.com/instadeepai/nucleotide-transformer",
        ],
        "observed_claim": (
            "NTv3 is presented as a foundation-model surface for long-range genomics "
            "and joint sequence-function modeling."
        ),
        "stack_mapping": [
            "genomic_sequence_prior_surface",
            "cross_domain_sequence_function_prior",
            "long_range_dependency_probe",
            "biological_adapter_hold_lane",
        ],
        "use_as": "long_range_sequence_function_prior",
        "decision": "HOLD_BIORXIV_PREPRINT_PRIOR",
        "promotion_gate": (
            "hold until preprint/source/model cards are locally receipted, benchmarked, "
            "license-checked, and mapped through a declared biological adapter"
        ),
    },
    {
        "prior_id": "PhysMaster.LANDAU_agent_trace",
        "title": "PhysMaster: Building an Autonomous AI Physicist for Theoretical and Computational Physics Research",
        "sources": [
            "https://arxiv.org/pdf/2512.19799",
        ],
        "observed_claim": (
            "PhysMaster presents an LLM-based physics research agent with a LANDAU "
            "library/priors/methodology substrate and code-based numerical loops."
        ),
        "stack_mapping": [
            "forward_foundation_equation_compiler",
            "godel_gauntlet",
            "equation_atom_receipts",
            "research_agent_trace_prior",
        ],
        "use_as": "research_agent_methodology_prior",
        "decision": "HOLD_EXTERNAL_AGENT_PRIOR",
        "promotion_gate": (
            "hold until task traces, retrieved-paper roots, numerical artifacts, "
            "critic failures, and reproduction receipts are local and inspectable"
        ),
    },
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def prior_entry(raw: dict[str, Any]) -> dict[str, Any]:
    entry = {
        **raw,
        "admission_status": "external_prior_hold",
        "claim_boundary": "metadata and routing prior only; no imported model/output is admitted",
    }
    entry["prior_hash"] = hash_obj({k: v for k, v in entry.items() if k != "prior_hash"})
    return entry


def build_payload() -> dict[str, Any]:
    priors = [prior_entry(item) for item in PRIORS]
    payload = {
        "schema": "external_ai_model_prior_ingest_v1",
        "claim_boundary": (
            "External model/paper prior ingest only. These sources can suggest "
            "routing, benchmark, or architecture experiments, but they do not "
            "become trusted dependencies until local receipts close."
        ),
        "priors": priors,
        "prior_root": hash_obj([item["prior_hash"] for item in priors]),
        "aggregates": {
            "prior_count": len(priors),
            "source_url_count": sum(len(item["sources"]) for item in priors),
            "hold_count": sum(1 for item in priors if item["decision"].startswith("HOLD")),
        },
        "decision": "ADMIT_EXTERNAL_AI_MODEL_PRIORS_AS_HOLD",
    }
    payload["payload_hash"] = hash_obj({k: v for k, v in payload.items() if k != "payload_hash"})
    return payload


def build_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "external_ai_model_prior_ingest_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "payload_hash": payload["payload_hash"],
        "prior_root": payload["prior_root"],
        "aggregates": payload["aggregates"],
        "decision": payload["decision"],
        "claim_boundary": payload["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# External AI Model Prior Ingest",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`  ",
        f"Prior root: `{payload['prior_root']}`",
        "",
        payload["claim_boundary"],
        "",
        "## Priors",
        "",
        "| Prior | Use as | Decision | Promotion gate |",
        "|---|---|---|---|",
    ]
    for item in payload["priors"]:
        lines.append(f"| {item['prior_id']} | {item['use_as']} | {item['decision']} | {item['promotion_gate']} |")
    lines.extend(["", "## Source URLs", ""])
    for item in payload["priors"]:
        lines.append(f"### {item['prior_id']}")
        for url in item["sources"]:
            lines.append(f"- {url}")
        lines.append("")
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


def write_tiddler(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    text = [
        "title: External AI Model Prior Ingest",
        "tags: ExternalPrior Hutter DMax PhysMaster Genomics HOLD Receipt",
        "type: text/vnd.tiddlywiki",
        "",
        "! External AI Model Prior Ingest",
        "",
        f"Decision: `{receipt['decision']}`",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        f"Prior root: `{payload['prior_root']}`",
        "",
        "!! Priors",
        "",
        "| Prior | Use as | Decision |h",
    ]
    for item in payload["priors"]:
        text.append(f"| {item['prior_id']} | {item['use_as']} | {item['decision']} |")
    text.extend(
        [
            "",
            "!! Links",
            "",
            "* [[Hutter Differential Frame Chain]]",
            "* [[Hutter Frame Invariant Root]]",
            "* [[Network Topology Model Reweighting]]",
            "* [[Underverse Variant Accounting]]",
            f"* Receipt: `{rel(RECEIPT)}`",
            f"* Summary: `{rel(SUMMARY)}`",
        ]
    )
    TIDDLER.write_text("\n".join(text) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    receipt = build_receipt(payload)
    (OUT_DIR / "external_ai_model_prior_ingest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(payload, receipt)
    write_tiddler(payload, receipt)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "receipt_hash": receipt["receipt_hash"],
                "prior_root": payload["prior_root"],
                "summary": rel(SUMMARY),
                "tiddler": rel(TIDDLER),
                "aggregates": payload["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
