#!/usr/bin/env python3
"""Cross-domain registry eigenvectors for compression priors.

This script strips the domain romance off math/chemistry/DNA/benchmark registry
receipts and keeps the useful compression object: a term-domain matrix and its
leading eigenvector. The output is a search/routing prior only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import online_domain_eigen_pruning as eigen


DEFAULT_RECEIPTS = [
    Path("4-Infrastructure/shim/epoch_eci_metaprobe_receipt.json"),
    Path("4-Infrastructure/shim/math_prover_prior_metaprobe_receipt.json"),
    Path("4-Infrastructure/shim/molecular_domain_prior_receipt.json"),
    Path("4-Infrastructure/shim/genomic_sequence_prior_receipt.json"),
    Path("4-Infrastructure/shim/pde_model_prior_receipt.json"),
    Path("4-Infrastructure/shim/llm_compression_architecture_prior_receipt.json"),
    Path("4-Infrastructure/shim/semantic_topology_compression_regimes_receipt.json"),
    Path("4-Infrastructure/shim/math_logogram_surface_receipt.json"),
    Path("4-Infrastructure/shim/intense_math_modeling_router_receipt.json"),
    Path("4-Infrastructure/shim/moving_sofa_nspace_prior_receipt.json"),
    Path("4-Infrastructure/shim/moving_sofa_scout_harness_receipt.json"),
    Path("4-Infrastructure/shim/moving_sofa_scout_response_validation_receipt.json"),
    Path("4-Infrastructure/shim/custom_equation_awareness_manifest_receipt.json"),
    Path("4-Infrastructure/shim/king_context_equation_retrieval_prior_receipt.json"),
]


def safe_name(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")[:96] or "unnamed"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def receipt_to_domains(path: Path, receipt: dict[str, Any]) -> list[dict[str, str]]:
    schema = receipt.get("schema", path.stem)
    domains: list[dict[str, str]] = []

    if schema == "epoch_eci_metaprobe_receipt_v1":
        summary = receipt.get("summary", {})
        benchmark_names = ", ".join(name for name, _count in summary.get("top_benchmark_names", [])[:16])
        domains.append(
            {
                "domain": "epoch_eci_benchmark_family",
                "equation": "performance(model, benchmark) in [0,1]; composite capability prior",
                "role": (
                    f"external benchmark family with {summary.get('benchmark_unique')} benchmarks; "
                    f"math_rows={summary.get('is_math_true_rows')}; coding_rows={summary.get('is_coding_true_rows')}; "
                    f"top_benchmarks={benchmark_names}; not local correctness"
                ),
                "source": "Epoch ECI benchmark table",
                "url": receipt.get("source_url", ""),
            }
        )

    if schema == "math_prover_prior_metaprobe_receipt_v1":
        for item in receipt.get("model_priors", []):
            domains.append(prior_to_domain("math_model", item))
        for item in receipt.get("dataset_priors", []):
            domains.append(prior_to_domain("dataset_registry", item))
        for query, result in receipt.get("theoremsearch", {}).items():
            theorems = result.get("theorems", [])[:3]
            slogans = " ".join(str(theorem.get("slogan") or theorem.get("name") or "") for theorem in theorems)
            papers = ", ".join(str(theorem.get("paper_title") or theorem.get("source") or "") for theorem in theorems)
            domains.append(
                {
                    "domain": f"theoremsearch_query_{safe_name(query)}",
                    "equation": slogans,
                    "role": f"retrieval prior for query={query}; adjacent_papers={papers}",
                    "source": "TheoremSearch",
                    "url": "https://www.theoremsearch.com/search",
                }
            )

    if schema == "molecular_domain_prior_receipt_v1":
        for item in receipt.get("molecular_axes", []):
            domains.append(axis_to_domain("molecular_axis", item))
        for item in receipt.get("hf_chemistry_priors", []):
            domains.append(prior_to_domain("chemistry_dataset", item))
        for section in receipt.get("registry_sections", [])[:10]:
            domains.append(
                {
                    "domain": f"bond_registry_{safe_name(section.get('name', 'section'))}",
                    "equation": "bond matrix = geometry + force constants + provenance",
                    "role": " ".join(
                        str(section.get(key, ""))
                        for key in ("integration_value", "entries", "license")
                    ),
                    "source": str(section.get("source") or "local chemical bond matrix registry"),
                    "url": "",
                }
            )

    if schema == "genomic_sequence_prior_receipt_v1":
        for item in receipt.get("sequence_axes", []):
            domains.append(axis_to_domain("genomic_axis", item))
        for item in receipt.get("dataset_priors", []):
            domains.append(prior_to_domain("dna_dataset", item))
        for item in receipt.get("model_priors", []):
            domains.append(prior_to_domain("dna_model", item))
        for item in receipt.get("biological_control_priors", []):
            domains.append(prior_to_domain("bio_control_prior", item))

    if schema == "pde_model_prior_receipt_v1":
        for item in receipt.get("pde_axes", []):
            domains.append(axis_to_domain("pde_axis", item))
        for item in receipt.get("verified_pde_priors", []):
            domains.append(prior_to_domain("pde_model", item))
        for item in receipt.get("soft_pde_candidates", []):
            domains.append(
                {
                    "domain": f"pde_soft_candidate_{safe_name(str(item.get('id', 'candidate')))}",
                    "equation": str(item.get("user_claim") or ""),
                    "role": f"{item.get('status', '')} {item.get('use_as', '')}",
                    "source": str(item.get("id") or "pde_soft_candidate"),
                    "url": "",
                }
            )

    if schema == "llm_compression_architecture_prior_receipt_v1":
        for item in receipt.get("compression_axes", []):
            domains.append(axis_to_domain("llm_compression_axis", item))
        for item in receipt.get("verified_compression_priors", []):
            domains.append(prior_to_domain("llm_compression_prior", item))

    if schema == "semantic_topology_compression_regimes_v1":
        for item in receipt.get("regimes", []):
            domains.append(
                {
                    "domain": f"semantic_topology_regime_{safe_name(str(item.get('label', 'regime')))}",
                    "equation": " ".join(str(part) for part in item.get("payload", [])),
                    "role": " ".join(
                        str(item.get(key, ""))
                        for key in ("condition", "operation", "failure_mode", "lean_predicate_hint")
                    ),
                    "source": str(item.get("id") or "semantic_topology_regime"),
                    "url": "",
                }
            )

    if schema == "math_logogram_surface_receipt_v1":
        for item in receipt.get("samples", []):
            metrics = item.get("compression_metrics", {})
            domains.append(
                {
                    "domain": f"math_logogram_surface_{safe_name(str(item.get('id', 'sample')))}",
                    "equation": str(item.get("canonical") or item.get("source") or ""),
                    "role": (
                        f"kind={item.get('kind')}; regime={item.get('semantic_regime')}; "
                        f"payload_len={item.get('surface_payload_len')}; "
                        f"payload_over_raw={metrics.get('payload_over_raw')}; "
                        f"canonical_hash={item.get('canonical_hash')}; "
                        f"cell_hash={item.get('cell_hash')}"
                    ),
                    "source": "math_logogram_surface_builder",
                    "url": "",
                }
            )

    if schema == "intense_math_modeling_router_v1":
        for item in receipt.get("routes", []):
            domains.append(
                {
                    "domain": f"intense_math_route_{safe_name(str(item.get('route', 'route')))}",
                    "equation": str(item.get("condition") or ""),
                    "role": f"{item.get('model_role', '')}; {item.get('use_for', '')}; judges={','.join(item.get('judge', []))}",
                    "source": "intense_math_modeling_router",
                    "url": "",
                }
            )

    if schema == "moving_sofa_nspace_prior_v1":
        for item in receipt.get("sofa_axes", []):
            domains.append(axis_to_domain("moving_sofa_axis", item))
        for item in receipt.get("sofa_priors", []):
            domains.append(prior_to_domain("moving_sofa_prior", item))

    if schema == "moving_sofa_scout_harness_receipt_v1":
        for item in receipt.get("packets", []):
            domains.append(
                {
                    "domain": f"moving_sofa_scout_{safe_name(str(item.get('task_id', 'task')))}",
                    "equation": str(item.get("ask") or ""),
                    "role": (
                        f"axis={item.get('axis', {}).get('axis')}; "
                        f"required={','.join(item.get('required_response_fields', []))}; "
                        f"gate={item.get('promotion_gate')}; "
                        f"hash={item.get('packet_hash')}"
                    ),
                    "source": "moving_sofa_scout_harness",
                    "url": "",
                }
            )

    if schema == "moving_sofa_scout_response_validation_v1":
        for item in receipt.get("validations", []):
            domains.append(
                {
                    "domain": f"moving_sofa_validation_{safe_name(str(item.get('task_id', 'task')))}",
                    "equation": str(item.get("promotion") or ""),
                    "role": (
                        f"required_ok={item.get('required_ok')}; "
                        f"contract_ok={item.get('contract_ok')}; "
                        f"packet_hash_ok={item.get('packet_hash_ok')}; "
                        f"boundary_ok={item.get('boundary_ok')}; "
                        f"receipts_ok={item.get('receipts_ok')}; "
                        f"forbidden_claim={item.get('forbidden_claim')}"
                    ),
                    "source": "moving_sofa_scout_response_validator",
                    "url": "",
                }
            )

    if schema == "custom_equation_awareness_manifest_v1":
        for item in receipt.get("equations", [])[:240]:
            domains.append(
                {
                    "domain": f"custom_equation_{safe_name(str(item.get('name', 'equation')))}",
                    "equation": str(item.get("equation") or ""),
                    "role": (
                        f"primitive={item.get('primitive_hint')}; "
                        f"boundary={item.get('claim_boundary')}; "
                        f"source={item.get('source_path')}; "
                        f"hash={item.get('equation_hash')}"
                    ),
                    "source": str(item.get("source_path") or "custom_equation_manifest"),
                    "url": "",
                }
            )

    if schema == "king_context_equation_retrieval_prior_v1":
        prior = receipt.get("king_context_prior", {})
        if prior:
            domains.append(prior_to_domain("retrieval_prior", prior))
        for item in receipt.get("retrieval_axes", []):
            domains.append(axis_to_domain("equation_retrieval_axis", item))

    return domains


def prior_to_domain(prefix: str, item: dict[str, Any]) -> dict[str, str]:
    raw_notes = item.get("notes", [])
    if isinstance(raw_notes, list):
        notes = " ".join(str(note) for note in raw_notes)
    elif raw_notes:
        notes = str(raw_notes)
    else:
        notes = ""
    name = str(item.get("id") or item.get("role") or prefix)
    return {
        "domain": f"{prefix}_{safe_name(name)}",
        "equation": str(item.get("role") or item.get("boundary") or ""),
        "role": " ".join(str(item.get(key, "")) for key in ("use_as", "boundary", "local_use")) + " " + notes,
        "source": name,
        "url": str(item.get("url") or ""),
    }


def axis_to_domain(prefix: str, item: dict[str, Any]) -> dict[str, str]:
    axis = str(item.get("axis", prefix))
    payload = " ".join(str(part) for part in item.get("payload", []))
    return {
        "domain": f"{prefix}_{safe_name(axis)}",
        "equation": payload,
        "role": f"{item.get('router_use', '')} {item.get('receipt_rule', '')}",
        "source": prefix,
        "url": "",
    }


def curriculum_records(surface: dict[str, Any]) -> list[dict[str, Any]]:
    top_domains = [
        {"domain": item["domain"], "weight": item["eigen_weight"]}
        for item in surface.get("weighted_domains", [])[:12]
    ]
    top_terms = surface.get("top_terms", [])[:20]
    prompt = {
        "task": "use_cross_domain_eigenvectors_for_compression",
        "top_domains": top_domains,
        "top_terms": top_terms,
        "instruction": "Explain how these eigenvectors should bias compression/search routing without doing domain work.",
    }
    answer = {
        "selected": True,
        "use_as": "cross_domain_compression_basis",
        "claim_boundary": "eigenvector-ranking-prior-only",
        "decision": "Use high-weight terms/domains as shared coordinates for token packing, metaprobe routing, and dataset sampling; do not treat them as chemistry, genomics, finance, or theorem truth.",
        "surface_payload_hint": "EIGEN-COMPRESS",
    }
    return [
        {
            "messages": [
                {"role": "system", "content": "You are a compression router. Return compact JSON with evidence boundaries."},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
            ]
        }
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt-json", type=Path, action="append")
    parser.add_argument("--out", type=Path, default=Path("4-Infrastructure/shim/cross_domain_registry_eigenvectors.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/cross_domain_registry_eigenvectors_curriculum.jsonl"))
    parser.add_argument("--limit-terms", type=int, default=64)
    args = parser.parse_args()

    receipt_paths = args.receipt_json or DEFAULT_RECEIPTS
    all_domains: list[dict[str, str]] = []
    used_receipts = []
    for path in receipt_paths:
        if not path.exists():
            continue
        receipt = load_json(path)
        used_receipts.append(str(path))
        all_domains.extend(receipt_to_domains(path, receipt))

    surface = eigen.build_surface(all_domains)
    surface["schema"] = "cross_domain_registry_eigenvectors_v1"
    surface["claim_boundary"] = "Leading eigenvectors compress registry topology; they are not domain truth or proof."
    surface["source_receipts"] = used_receipts
    surface["domain_count"] = len(all_domains)
    surface["top_terms"] = surface["top_terms"][: args.limit_terms]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(surface, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(surface):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(surface, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
