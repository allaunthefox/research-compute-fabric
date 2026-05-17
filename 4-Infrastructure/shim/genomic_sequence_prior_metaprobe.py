#!/usr/bin/env python3
"""Genomic/DNA sequence prior metaprobe.

This is a computational sequence surface for the local router: DNA strings,
k-mers, tokenizers, long-context genome models, and provenance receipts. It is
not a protocol-design, synthesis, or wet-lab instruction surface.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SEQUENCE_AXES = [
    {
        "axis": "nucleotide_sequence",
        "payload": ["A", "C", "G", "T", "N", "sequence_length", "strand", "organism"],
        "router_use": "symbolic_sequence_compression_and_kmer_surface",
        "receipt_rule": "preserve source assembly, coordinates, strand, and tokenizer",
    },
    {
        "axis": "kmer_tokenization",
        "payload": ["k", "stride", "vocabulary", "ambiguous_base_policy", "reverse_complement_policy"],
        "router_use": "bitpacking_logogram_and_metaprobe_token_axis",
        "receipt_rule": "record k, stride, vocabulary hash, and sequence preprocessing",
    },
    {
        "axis": "long_context_genomic_model",
        "payload": ["context_length", "objective", "species_scope", "embedding", "downstream_task"],
        "router_use": "external_model_prior_for_sequence_routing",
        "receipt_rule": "generated labels remain predictions until evaluated against benchmark/source labels",
    },
    {
        "axis": "genomic_provenance",
        "payload": ["dataset", "license", "organism", "assembly", "annotation_version", "contamination_check"],
        "router_use": "admissibility_gate_for_sequence_corpora",
        "receipt_rule": "do not train/ingest without provenance, license, and task boundary",
    },
    {
        "axis": "rna_conditioned_destructive_gate",
        "payload": ["guide_match_condition", "activation_threshold", "target_marker", "destructive_action", "off_target_boundary"],
        "router_use": "selective gate motif for semantic/control-plane pruning: activate only under exact marker match, otherwise spare the carrier",
        "receipt_rule": "computational motif only; record source, match predicate, non-activation condition, and no wet-lab parameters",
    },
]


HF_DNA_DATASET_PRIORS = [
    {
        "id": "huggingface/datasets?search=dna",
        "role": "dna_dataset_discovery_registry_prior",
        "boundary": "registry-prior-only",
        "use_as": "dna_corpus_search_axis",
        "notes": [
            "HF DNA dataset search listed 390 results when checked.",
            "Top examples included antibiotic-resistance DNA, Human/Mouse/Zebrafish/Fruitfly/Worm/Arabidopsis DNA corpora, DNABERT6 tokenized variants, k-mer tokenized variants, and BPE/SentencePiece tokenized variants.",
        ],
    },
    {
        "id": "macwiatrak/bacbench-antibiotic-resistance-dna",
        "role": "antibiotic_resistance_sequence_benchmark_prior",
        "boundary": "benchmark-prior-only",
        "use_as": "sequence_classification_eval_axis",
    },
    {
        "id": "simecek/Human_DNA_v0",
        "role": "human_reference_dna_corpus_prior",
        "boundary": "dataset-prior-only",
        "use_as": "human_sequence_tokenization_axis",
    },
    {
        "id": "simecek/Human_DNA_v0_DNABert6tokenized",
        "role": "dnabert6_tokenized_human_sequence_prior",
        "boundary": "dataset-prior-only",
        "use_as": "kmer_tokenization_comparison_axis",
    },
]


HF_DNA_MODEL_PRIORS = [
    {
        "id": "AIRI-Institute/GENA-LM family",
        "role": "genomic_language_model_prior",
        "boundary": "model-search-prior-only",
        "use_as": "bert/bigbird_style_sequence_encoder_axis",
    },
    {
        "id": "InstaDeepAI/Nucleotide Transformer family",
        "role": "multi_species_nucleotide_transformer_prior",
        "boundary": "model-search-prior-only",
        "use_as": "multi_species_embedding_and_6mer_tokenizer_axis",
    },
    {
        "id": "LongSafari/HyenaDNA family",
        "role": "long_context_single_nucleotide_model_prior",
        "boundary": "model-search-prior-only",
        "use_as": "long_sequence_compression_and_context_axis",
    },
    {
        "id": "multimolecule/DNABERT k-mer family",
        "role": "kmer_masked_language_model_prior",
        "boundary": "model-search-prior-only",
        "use_as": "3mer_to_6mer_tokenization_axis",
    },
    {
        "id": "arcinstitute/evo2_20b",
        "role": "large_genome_model_prior",
        "boundary": "model-search-prior-only",
        "use_as": "large_scale_genomic_reasoning_comparator",
    },
]


BIOLOGICAL_CONTROL_PRIORS = [
    {
        "id": "USU_Cas12a2_selective_cell_destruction_2026",
        "role": "rna_conditioned_selective_destruction_gate_prior",
        "boundary": "news-and-paper-pointer-prior-only",
        "use_as": "conditional_activation_and_destructive_pruning_motif",
        "source": "USU Biochemists Show CRISPR Can Selectively Destroy Cells, a Cancer-Treatment Goal",
        "url": "https://www.usu.edu/today/story/usu-biochemists-show-crispr-can-selectively-destroy-cells-a-cancer-treatment-goal",
        "notes": [
            "USU report says CRISPR-Cas12a2 binds complementary RNA rather than DNA and, once activated, destroys DNA encountered by the enzyme.",
            "Article claims imperfect guide/target complement prevents activation and describes selective killing of cells containing a single-point cancer-associated mutant in reported experiments.",
            "Local use is only a compression/control motif: exact-match gate, destructive prune action, spare-on-mismatch boundary.",
        ],
    },
]


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a genomic sequence router. Return compact JSON with evidence boundaries."
    records = []
    for axis in receipt["sequence_axes"]:
        prompt = {
            "task": "route_genomic_sequence_axis",
            "axis": axis["axis"],
            "payload": axis["payload"],
            "instruction": "Choose how this DNA axis should enter the compression/metaprobe router.",
        }
        answer = {
            "selected": True,
            "use_as": axis["router_use"],
            "claim_boundary": "computational-sequence-prior-only",
            "surface_payload_hint": axis["axis"][:16].upper(),
            "receipt_rule": axis["receipt_rule"],
        }
        records.append(chat_record(system, prompt, answer))
    for prior in receipt["dataset_priors"]:
        prompt = {
            "task": "use_dna_dataset_prior",
            "dataset": prior["id"],
            "role": prior["role"],
            "instruction": "Explain how to sample this DNA dataset family without overclaiming.",
        }
        answer = {
            "selected": True,
            "use_as": prior["use_as"],
            "claim_boundary": prior["boundary"],
            "sampling_rule": "sample small; preserve organism, assembly, coordinates, tokenizer, license, and task label provenance",
        }
        records.append(chat_record(system, prompt, answer))
    for prior in receipt["model_priors"]:
        prompt = {
            "task": "use_dna_model_prior",
            "model_family": prior["id"],
            "role": prior["role"],
            "instruction": "Explain how this genome model family should influence routing without becoming proof.",
        }
        answer = {
            "selected": True,
            "use_as": prior["use_as"],
            "claim_boundary": prior["boundary"],
            "metaprobe_rule": "Use embeddings/predictions as sequence priors only; benchmark and source-label receipts decide promotion.",
        }
        records.append(chat_record(system, prompt, answer))
    for prior in receipt["biological_control_priors"]:
        prompt = {
            "task": "use_biological_control_prior_as_compression_motif",
            "prior": prior["id"],
            "role": prior["role"],
            "instruction": "Map this biological control idea into a safe compression/metaprobe gate.",
        }
        answer = {
            "selected": True,
            "use_as": prior["use_as"],
            "claim_boundary": prior["boundary"],
            "metaprobe_rule": "Use only as a conditional activation/destructive-pruning motif; do not emit wet-lab design, guide design, dosing, delivery, or therapeutic instructions.",
            "surface_payload_hint": "RNA-GATE-PRUNE",
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
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/genomic_sequence_prior_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/genomic_sequence_prior_curriculum.jsonl"))
    args = parser.parse_args()

    receipt = {
        "schema": "genomic_sequence_prior_receipt_v1",
        "claim_boundary": "DNA priors support computational sequence routing, not wet-lab design or biological validation.",
        "sequence_axes": SEQUENCE_AXES,
        "dataset_priors": HF_DNA_DATASET_PRIORS,
        "model_priors": HF_DNA_MODEL_PRIORS,
        "biological_control_priors": BIOLOGICAL_CONTROL_PRIORS,
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
