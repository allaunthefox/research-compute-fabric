#!/usr/bin/env python3
"""Synthesize local compression and signal-shaping priors into testable routes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "compression_signal_shaping_synthesis_receipt.json"
CURRICULUM = SHIM / "compression_signal_shaping_synthesis_curriculum.jsonl"


SOURCE_ARTIFACTS = [
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/PAQ Style Compression Review.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Hutter Equation Metastate Transfold.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/T16 Candidate Pipeline Equation Prior.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Phi Scaling Response Model Selection.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Classical Signal Roots Quantum Translation Program.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Semantic Topology Compression Regimes.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/LLM Compression Architecture Priors.tid",
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/docmd Size Strategy Prior.tid",
    "4-Infrastructure/shim/nonlinear_compressed_sensing_structural_prior_receipt.json",
    "4-Infrastructure/shim/generative_compressed_sensing_prior_receipt.json",
    "4-Infrastructure/shim/invertible_generative_inverse_prior_receipt.json",
    "4-Infrastructure/shim/holographic_fractional_recursive_equation_fold_receipt.json",
    "4-Infrastructure/shim/signal_equation_invariant_roots_receipt.json",
    "4-Infrastructure/shim/semantic_topology_compression_regimes_receipt.json",
    "4-Infrastructure/shim/llm_compression_architecture_prior_receipt.json",
    "4-Infrastructure/shim/connectome_protective_cognitive_load_reweighting_receipt.json",
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_digest(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(REPO)),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def build_receipt() -> dict[str, Any]:
    sources = [file_digest(REPO / rel) for rel in SOURCE_ARTIFACTS if (REPO / rel).exists()]
    receipt: dict[str, Any] = {
        "schema": "compression_signal_shaping_synthesis_v1",
        "source_artifacts": sources,
        "primary_read": (
            "Across the local compression, compressed-sensing, signal-root, semantic-topology, "
            "and docmd payload notes, the new pattern is not another universal compressor. "
            "It is a signal-shaped route compiler: shape the route space before coding, then "
            "pay exact residual, witness, decoder, and container bytes after coding."
        ),
        "approach_taxonomy": [
            {
                "approach": "PAQ_style_context_mixing",
                "shapes": "probability context",
                "use": "long-range sparse contexts, context mixing, arithmetic-coding style evidence",
                "promotion_gate": "only byte measurement and exact decode count",
                "risk": "context/model bytes can silently exceed gain",
            },
            {
                "approach": "decision_diagram_route_search",
                "shapes": "candidate route space",
                "use": "enumerate transform routes with lower bounds and prune dominated branches",
                "promotion_gate": "route cost < incumbent with decoder/residual/witness counted",
                "risk": "route explosion without admissible lower bounds",
            },
            {
                "approach": "T16_candidate_pipeline",
                "shapes": "weak event detection",
                "use": "detect residual-collapse events in noisy candidate forests",
                "promotion_gate": "event must become an executable route with exact rehydration",
                "risk": "signal analogy mistaken for compression evidence",
            },
            {
                "approach": "phi_response_family_selection",
                "shapes": "response curve",
                "use": "choose log/saturating/Hill/low-exponent response by measured error",
                "promotion_gate": "held-out fit beats simple baselines",
                "risk": "Phi gain treated as universal law",
            },
            {
                "approach": "nonlinear_compressed_sensing",
                "shapes": "regular nonlinear measurement map",
                "use": "guide structured recovery when RIP-like or separability conditions exist",
                "promotion_gate": "structure and regularity conditions explicit",
                "risk": "nonlinear manifold route without bounds",
            },
            {
                "approach": "generative_compressed_sensing",
                "shapes": "latent proposal manifold",
                "use": "replace plain sparsity with learned low-dimensional priors",
                "promotion_gate": "latent + residual + uncertainty bytes beat baseline",
                "risk": "generator becomes hidden payload or biased source substitute",
            },
            {
                "approach": "invertible_generative_inverse",
                "shapes": "invertible/flow chart",
                "use": "reduce representation error and expose uncertainty in inverse route charts",
                "promotion_gate": "invertibility guard, support check, residual closure",
                "risk": "approximate invertibility treated as lossless",
            },
            {
                "approach": "holographic_fractional_recursive_fold",
                "shapes": "boundary descriptor and bounded memory",
                "use": "short descriptor plus exact residual, graph harmonics, bounded history",
                "promotion_gate": "decoded hash closes and memory/kernel bytes counted",
                "risk": "boundary/bulk split hides payload",
            },
            {
                "approach": "signal_invariant_roots",
                "shapes": "signal morphology feature space",
                "use": "route chunks by spectral, transient, autocorrelation, DCT, phase, and similarity roots",
                "promotion_gate": "features only choose routes; bytes decide",
                "risk": "feature score promoted without codec trial",
            },
            {
                "approach": "semantic_topology_regimes",
                "shapes": "fold/prune/tear decision",
                "use": "avoid false merges; classify beautiful/ugly/horrible compression regimes",
                "promotion_gate": "round-trip loss and contradiction/torsion receipts",
                "risk": "smooth story over torn semantics",
            },
            {
                "approach": "llm_control_plane_compression",
                "shapes": "prompt/logogram/control representation",
                "use": "prune prompts, use symbolic cells, use compressed proxy views",
                "promotion_gate": "source bytes, retained bytes, quality delta, provenance",
                "risk": "lossy summary sold as exact compression",
            },
            {
                "approach": "docmd_static_payload_strategy",
                "shapes": "runtime payload",
                "use": "pre-render static HTML, omit heavy framework runtime, gate plugins, externalize search index",
                "promotion_gate": "built-site payload measurement with exact plugin config",
                "risk": "architecture reduction confused with content compression",
            },
        ],
        "new_candidate_patterns": [
            {
                "id": "N1_signal_shaped_route_compiler",
                "novelty": "combine signal invariant roots with DD route search",
                "shape": "chunk -> feature vector -> route family -> codec trial -> exact residual",
                "why_it_popped": "signal roots supply cheap morphology; DD supplies admissible route discipline",
                "candidate_equation": "route = argmin_r LB(r | phi_signal(chunk), topology_regime, history_state)",
                "first_test": "wiki8 chunk sweep with features: entropy, XML tag density, DCT energy, transient edges, autocorrelation, cosine reuse",
                "promotion_gate": "chosen route beats bz2/zstd baseline after feature/witness bytes",
                "testability": "high",
            },
            {
                "id": "N2_runtime_staticization_as_compression_prepass",
                "novelty": "treat docmd-style no-runtime output as a compression prepass for wiki/tiddler publishing",
                "shape": "tiddlers/articles -> static route pages + external search index + manifest",
                "why_it_popped": "payload shrinks by not shipping dynamic state; maps to gated leaves in DD",
                "candidate_equation": "payload_total = html_static + js_core + css_core + selected_plugin_assets + index_external",
                "first_test": "build a small TiddlyWiki/article slice both live and static; compare initial gzip payload and search index cost",
                "promotion_gate": "same navigation/search affordance with lower initial payload",
                "testability": "high",
            },
            {
                "id": "N3_witness_budgeted_latent_route",
                "novelty": "use generative/flow priors only as proposals with explicit latent/residual byte accounting",
                "shape": "latent z proposes transform; exact residual repairs; uncertainty decides hold",
                "why_it_popped": "generative and invertible priors are useful only when they stop hiding model state",
                "candidate_equation": "C = bytes(z) + bytes(model_id) + bytes(residual) + bytes(witness) + bytes(decoder)",
                "first_test": "small structured corpus slice with tokenbook latent IDs and exact residual lane",
                "promotion_gate": "C < incumbent and decoded hash equals source hash",
                "testability": "medium",
            },
            {
                "id": "N4_fractional_history_route_scheduler",
                "novelty": "bounded-memory scheduler for nonstationary corpus regions",
                "shape": "route choice depends on recent route residuals through a finite fractional kernel",
                "why_it_popped": "fractional dynamics and cognitive overload both say history changes threshold response",
                "candidate_equation": "h_t = sum_{tau<t, window W} K_alpha(t-tau) * residual_tau; route_t = R(chunk_t, h_t)",
                "first_test": "stream wiki8 chunks; compare memoryless route choice vs bounded-history route choice",
                "promotion_gate": "history bytes are counted and improve total compressed size",
                "testability": "medium",
            },
            {
                "id": "N5_topology_regime_guard",
                "novelty": "use beautiful/ugly/horrible semantics as a pre-code safety gate",
                "shape": "fold when invariants align, prune when quality loss bounded, isolate when torsion high",
                "why_it_popped": "semantic compression needs a tear detector before it creates false tokenbooks",
                "candidate_equation": "regime = classify(invariant_overlap, torsion, round_trip_loss, contradiction)",
                "first_test": "compare tokenbook merges with and without contradiction/torsion holds on docs/tiddlers",
                "promotion_gate": "fewer bad merges without losing byte wins",
                "testability": "medium",
            },
            {
                "id": "N6_physical_signal_probe_feedback",
                "novelty": "borrow CAD/DNA force-probe discipline for compression experiments",
                "shape": "route hypothesis -> measurable perturbation -> negative control -> receipt",
                "why_it_popped": "the CAD frame made measurement and negative controls explicit; compression routes need the same habit",
                "candidate_equation": "promote iff positive route beats baseline and matched negative control fails or underperforms",
                "first_test": "for each new transform, include a deliberately bad route with same sidecar budget",
                "promotion_gate": "positive gain survives against negative control",
                "testability": "high",
            },
        ],
        "unifying_equations": {
            "signal_feature_vector": "phi_signal(c) = [H(c), tag_density(c), DCT_energy(c), transient(c), autocorr(c), cosine_reuse(c)]",
            "route_selection": "r* = argmin_r LB(r | phi_signal(c), semantic_regime(c), history_state)",
            "exact_cost": "C_total = bytes(payload) + bytes(sidecar) + bytes(residual) + bytes(decoder) + bytes(witness) + bytes(container)",
            "promotion": "promote iff H(decode(r*)) == H(source) and C_total < incumbent and failure_rules == none",
            "negative_control": "valid_gain iff C(candidate) < C(baseline) and C(candidate) < C(matched_bad_route)",
        },
        "immediate_experiment_ladder": [
            {
                "step": "E1",
                "name": "wiki8_signal_feature_baseline",
                "action": "extract per-chunk signal features and compare feature clusters to bz2/zstd outcomes",
                "success": "feature clusters predict which chunks benefit from which existing codec route",
            },
            {
                "step": "E2",
                "name": "route_classifier_without_new_codec",
                "action": "choose among existing routes only: raw, bz2, zstd, xml_token+bz2, tokenbook+bz2 if available",
                "success": "classifier beats always-bz2 after classifier sidecar bytes",
            },
            {
                "step": "E3",
                "name": "topology_guard_tokenbook",
                "action": "apply semantic/topology guards before tokenbook merge",
                "success": "bad merges fall while byte gain remains non-negative",
            },
            {
                "step": "E4",
                "name": "docmd_static_wiki_slice",
                "action": "export a small tiddler/article slice to static pages plus external index",
                "success": "lower initial payload than live surface with same navigability",
            },
            {
                "step": "E5",
                "name": "bounded_history_scheduler",
                "action": "route stream chunks with finite fractional residual memory",
                "success": "history-aware route choice beats memoryless route after history bytes",
            },
        ],
        "what_is_actually_new": [
            "The strongest new move is route-space signal shaping, not a new compressor.",
            "docmd reframes compression as runtime-state omission: do not ship branches you can rebuild.",
            "Signal invariant roots give a concrete feature surface for choosing routes before spending codec time.",
            "Semantic topology supplies a guard against destructive tokenbook merges.",
            "Generative/invertible models should be restricted to proposal charts with explicit residual byte accounting.",
            "Every interesting analogy becomes useful only after it is paired with a negative control and exact decode receipt.",
        ],
        "failure_rules": [
            "feature score treated as byte gain -> invalid",
            "sidecar, witness, residual, decoder, or container bytes omitted -> invalid receipt",
            "latent/generative prior used as hidden source payload -> invalid",
            "semantic merge without round-trip or contradiction check -> hold",
            "history kernel unbounded or uncounted -> fail closed",
            "docmd-style staticization reported as Hutter compression -> overclaim",
            "negative controls omitted from new route claim -> weak claim",
        ],
        "claim_boundary": (
            "This synthesis proposes testable route-shaping experiments. It is not a Hutter Prize result, "
            "not proof of a new compressor, and not a guarantee that signal features will improve wiki8."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "classify_compression_approach",
            "input": "PAQ, DD, signal roots, generative prior, docmd, semantic topology",
            "target": "what it shapes: probability, route space, morphology, latent chart, runtime payload, or fold/prune/tear gate",
        },
        {
            "task": "reject_unpaid_sidecar",
            "input": "candidate route with model, latent, index, or witness bytes",
            "target": "count every non-source byte in C_total before promotion",
        },
        {
            "task": "choose_new_experiment",
            "input": "new pattern N1-N6",
            "target": "run the highest-testability ladder first: signal-shaped route compiler or docmd static wiki slice",
        },
        {
            "task": "separate_signal_from_compression",
            "input": "feature score, invariant root, or route priority",
            "target": "diagnostic until exact decode and byte measurement close",
        },
    ]
    CURRICULUM.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> None:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_curriculum(receipt)
    print(json.dumps({
        "receipt": str(OUT.relative_to(REPO)),
        "curriculum": str(CURRICULUM.relative_to(REPO)),
        "receipt_hash": receipt["receipt_hash"],
        "source_count": len(receipt["source_artifacts"]),
        "approach_count": len(receipt["approach_taxonomy"]),
        "new_candidate_count": len(receipt["new_candidate_patterns"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
