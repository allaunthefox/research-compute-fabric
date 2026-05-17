#!/usr/bin/env python3
"""Build receipted priors from the local AIMO neuro-symbolic deck.

The local AIMO presentation is image-only, so this registry consumes the OCR
text generated from the PDF pages and records the design surface conservatively:
parser-first, stochastic-proposer, deterministic verifier, bounded fallback.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "aimo_sources"
PACKETS = OUT_DIR / "aimo_neuro_symbolic_prior_packets.jsonl"
RECEIPT = OUT_DIR / "aimo_neuro_symbolic_prior_receipt.json"

SOURCES = {
    "aimo_deck_pdf": Path("/home/allaun/Documents/ingest/AIMO_Presentation.pdf"),
    "aimo_deck_ocr": OUT_DIR / "AIMO_Presentation_ocr.txt",
    "cafa2_pdf": Path("/home/allaun/Documents/ingest/s13059-016-1037-6.pdf"),
    "cafa2_text": OUT_DIR / "s13059-016-1037-6.txt",
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def source_receipts() -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for key, path in SOURCES.items():
        if not path.exists():
            receipts[key] = {"path": str(path), "exists": False}
            continue
        data = path.read_bytes()
        receipts[key] = {
            "path": str(path),
            "exists": True,
            "bytes": len(data),
            "sha256": sha256_bytes(data),
        }
    return receipts


def count_terms(text: str, terms: list[str]) -> dict[str, int]:
    lowered = text.lower()
    return {term: lowered.count(term.lower()) for term in terms}


def packet(packet_id: str, name: str, role: str, density_markers: list[str], route: str, claim_boundary: str) -> dict[str, Any]:
    obj = {
        "schema": "aimo_neuro_symbolic_prior_packet_v1",
        "packet_id": packet_id,
        "name": name,
        "rrc_shape_hint": "NeuroSymbolicVerifierPipeline",
        "role": role,
        "density_markers": density_markers,
        "route": route,
        "claim_boundary": claim_boundary,
        "decision": "HOLD",
    }
    obj["packet_hash"] = sha256_text(stable_json(obj))
    return obj


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    aimo_text = SOURCES["aimo_deck_ocr"].read_text(encoding="utf-8", errors="replace")
    cafa_text = SOURCES["cafa2_text"].read_text(encoding="utf-8", errors="replace")

    packets = [
        packet(
            packet_id="AIMO.PRIOR.PARSER_MANIFOLD.0001",
            name="AIMO parser-first manifold alignment",
            role="Parser fixes syntax, tags semantics, and assigns strategy before any model answer is trusted.",
            density_markers=[
                "syntax_fix_layer",
                "semantic_tagging_layer",
                "strategy_assignment",
                "latex_input_cleaning",
                "garbage_in_hallucination_out_boundary",
            ],
            route="raw_problem -> parser/filter -> typed equation strategy -> proposer",
            claim_boundary="OCR-derived design prior only; not a validated implementation.",
        ),
        packet(
            packet_id="AIMO.PRIOR.STOCHASTIC_PROPOSER.0001",
            name="AIMO low-temperature proposer",
            role="LLM generates algebraic systems, not trusted final reasoning.",
            density_markers=[
                "temperature_low_sampling",
                "equation_only_prompt",
                "heuristic_proposer",
                "generation_length_penalty",
                "multi_temperature_fallback",
            ],
            route="typed problem -> equation-only LLM proposal -> symbolic verifier",
            claim_boundary="Proposer output is untrusted until deterministic replay/checks pass.",
        ),
        packet(
            packet_id="AIMO.PRIOR.SYMPY_VERIFIER.0001",
            name="AIMO deterministic symbolic verifier",
            role="SymPy execution, substitution, and back-substitution reject unbalanced generated states.",
            density_markers=[
                "sympy_execution",
                "back_substitution_check",
                "variable_sparsity_guard",
                "equation_density_guard",
                "fast_fail_operator_detection",
            ],
            route="candidate equations -> bounded SymPy solve -> substitute solution -> accept/reject",
            claim_boundary="Symbolic checks are only as good as parser coverage and modeled constraints.",
        ),
        packet(
            packet_id="AIMO.PRIOR.DUAL_VALIDATION_MATRIX.0001",
            name="AIMO dual validation core matrix",
            role="Cross-checks rule/math validation against neural answer consistency and fallback consensus.",
            density_markers=[
                "rule_math_check_axis",
                "neural_answer_axis",
                "impossible_state_rejection",
                "low_confidence_fallback",
                "confidence_self_diagnosis",
            ],
            route="symbolic result + neural result -> confidence matrix -> strict integer extraction",
            claim_boundary="A confidence matrix is a routing gate, not proof of mathematical correctness.",
        ),
        packet(
            packet_id="AIMO.PRIOR.FAILSAFE_SUBMISSION.0001",
            name="AIMO crash-safe integer fallback",
            role="Maintains valid submission shape under fatal failures using deterministic fallback integer.",
            density_markers=[
                "exception_guard",
                "hash_fallback_integer",
                "valid_output_range",
                "vram_reclamation",
                "symbolic_cache",
            ],
            route="exception -> deterministic hash fallback -> valid integer output",
            claim_boundary="Submission safety prevents invalid output; it does not prevent wrong output.",
        ),
        packet(
            packet_id="CAFA.PRIOR.PROTEIN_ONTOLOGY_EVAL.0001",
            name="CAFA protein-function ontology evaluation",
            role="Protein function prediction is graph-structured: protein-centric and term-centric evaluation over GO/HPO.",
            density_markers=[
                "gene_ontology_graph",
                "human_phenotype_ontology_graph",
                "protein_centric_multilabel_output",
                "term_centric_binary_ranking",
                "ontology_specific_metrics",
            ],
            route="protein -> ontology term graph/ranking -> benchmark evaluation",
            claim_boundary="Evaluation prior only; not a function-prediction proof or ProtBoost validation.",
        ),
        packet(
            packet_id="SPX.PRIOR.LOSSLESS_SHARDING_RANS.0001",
            name="SPX lossless sharding and rANS compression prior",
            role="Image codec prior for deterministic, single-pass residual sharding and entropy coding.",
            density_markers=[
                "reversible_color_transform",
                "median_edge_prediction",
                "stateless_sharding",
                "bias_cancellation_residual_centering",
                "interleaved_rans_entropy_coding",
            ],
            route="input field -> predictor residual -> shard context -> rANS stream -> bit-perfect replay",
            claim_boundary="External README-derived prior; benchmark claims require local reproduction before promotion.",
        ),
    ]

    PACKETS.write_text("\n".join(stable_json(p) for p in packets) + "\n", encoding="utf-8")
    aimo_terms = [
        "parser",
        "sympy",
        "verification",
        "fallback",
        "deterministic",
        "temperature",
        "equation",
        "guardrail",
        "hash",
    ]
    cafa_terms = [
        "ontology",
        "protein-centric",
        "term-centric",
        "gene ontology",
        "human phenotype ontology",
        "benchmark",
        "prediction",
    ]
    receipt = {
        "schema": "aimo_neuro_symbolic_prior_receipt_v1",
        "packet_count": len(packets),
        "packets": str(PACKETS.relative_to(REPO)),
        "source_receipts": source_receipts(),
        "aimo_ocr_term_counts": count_terms(aimo_text, aimo_terms),
        "cafa_term_counts": count_terms(cafa_text, cafa_terms),
        "ocr_page_count": len(re.findall(r"===== page-", aimo_text)),
        "density_marker_total": sum(len(p["density_markers"]) for p in packets),
        "claim_boundary": (
            "AIMO deck is OCR-derived from local image slides; SPX is an external README prior; "
            "CAFA text is extracted from local open-access PDF. All packets remain HOLD until "
            "implementation, benchmark, or proof receipts close."
        ),
        "decision": "HOLD",
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
