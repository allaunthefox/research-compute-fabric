#!/usr/bin/env python3
"""Combined-approach equation surface probe.

This probe asks whether the recently combined HOLD priors expose reusable
equation surfaces. It does not admit any equation as proven, predictive, or
safety-valid. It records candidate operators that can become experiments only
after replay, resource, provenance, and negative-control receipts close.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "combined_approach_equation_surface"
RECEIPT = OUT_DIR / "combined_approach_equation_surface_receipt.json"
SUMMARY = OUT_DIR / "combined_approach_equation_surface.md"
PAYLOAD_JSON = OUT_DIR / "combined_approach_equation_surface.json"
TIDDLER = (
    REPO
    / "6-Documentation"
    / "tiddlywiki-local"
    / "wiki"
    / "tiddlers"
    / "Combined Approach Equation Surface.tid"
)

SOURCES = [
    REPO / "shared-data" / "data" / "external_ai_model_prior_ingest" / "external_ai_model_prior_ingest_receipt.json",
    REPO / "shared-data" / "data" / "torsion_indexed_network_witness_topology" / "torsion_indexed_network_witness_topology_receipt.json",
    REPO / "shared-data" / "data" / "network_topology_model_reweighting" / "network_topology_model_reweighting_receipt.json",
    REPO / "shared-data" / "data" / "underverse_variant_accounting" / "underverse_variant_accounting_receipt.json",
    REPO / "shared-data" / "data" / "hutter_frame_invariant_root" / "hutter_frame_invariant_root_receipt.json",
    REPO / "shared-data" / "data" / "hutter_differential_frame_chain" / "hutter_differential_frame_chain_receipt.json",
    REPO / "shared-data" / "data" / "hutter_multidimensional_causal_chain" / "hutter_multidimensional_causal_chain_receipt.json",
    REPO / "shared-data" / "data" / "phonon_music_logogram_layer" / "phonon_music_logogram_layer_receipt.json",
    REPO / "shared-data" / "network_topology_database.json",
    REPO / "3-Mathematical-Models" / "fiber_optic_vibrational_tensor" / "Fundamental_Network_Topology_Equation.md",
    REPO / "6-Documentation" / "wiki" / "Network-Topology-Theory.md",
    REPO / "shared-data" / "data" / "x86_emulator_eigen_baseline" / "x86_emulator_eigen_baseline_receipt.json",
    REPO / "shared-data" / "data" / "modly_text_to_cad_bridge" / "modly_text_to_cad_bridge_receipt.json",
    REPO / "shared-data" / "data" / "transcriptformer_evolutionary_prior" / "transcriptformer_evolutionary_prior_receipt.json",
    REPO / "shared-data" / "data" / "parquet_logogram_efficiency" / "parquet_logogram_efficiency_receipt.json",
    REPO / "shared-data" / "data" / "parquet_logogram_eigenprobe" / "parquet_logogram_eigenprobe_receipt.json",
]

CANDIDATES = [
    {
        "equation_id": "receipt_weighted_torsion_route_field",
        "equation": "E_R(N_T)=sum_i w_i^R * alpha_i * f_i(N_T), where w_i^R=normalize(w_i * m_i)",
        "reads_as": (
            "A topology or witness graph is scored through receipt-reweighted methodology "
            "weights at torsion/state-advance frame T."
        ),
        "combined_sources": [
            "network_topology_model_reweighting",
            "torsion_indexed_network_witness_topology",
        ],
        "use_as": "conservative routing score before any external prior is allowed to steer search",
        "decision": "HOLD_COEFFICIENT_RECEIPT_DEBT",
        "promotion_gate": "requires dataset receipts, coefficient derivation, negative controls, and prediction/outcome replay",
    },
    {
        "equation_id": "soft_parallel_route_revision",
        "equation": "X_{k+1}=R_theta(X_k, softmax(E_R(X_k)/tau), residual_k, receipt_root_k)",
        "reads_as": (
            "A DMax-like soft parallel revision step can propose route/frame repairs, "
            "but each revision must carry residual and receipt roots."
        ),
        "combined_sources": [
            "external_ai_model_prior_ingest:DMax.parallel_self_revision",
            "receipt_weighted_torsion_route_field",
        ],
        "use_as": "parallel decoder/search scheduler for Hutter frame candidates",
        "decision": "HOLD_EXTERNAL_DECODING_PRIOR",
        "promotion_gate": "requires exact replay, byte accounting, baseline comparison, and resource envelope under prize rules",
    },
    {
        "equation_id": "torsion_indexed_admissibility_gate",
        "equation": "A(Omega_T)=1[M(Omega_T)<=eps_mech] * E_ext(N_T) * 1[root(Omega_T)] * 1[rho(Omega_T)<=eps_risk]",
        "reads_as": (
            "The route/load/proof state is admissible only when mechanics close, "
            "extended topology remains bounded, witness roots recompute, and residual risk is below horizon."
        ),
        "combined_sources": [
            "torsion_clock",
            "network_topology_equation",
            "merkle_witness",
            "underverse_guardrails",
        ],
        "use_as": "shared admissibility gate for network, load, and proof routes",
        "decision": "HOLD_TORSION_CLOCK_BOUNDARY",
        "promotion_gate": "requires local invariant mechanics or decode-closure fixture and explicit residual horizon",
    },
    {
        "equation_id": "long_range_sequence_function_memory_gate",
        "equation": "F_seq(S)=H_boundary(S) * F_memory(S) * G_adapter(S, C_history, K_alpha)",
        "reads_as": (
            "An NTv3-like long-range sequence/function prior can only enter as an adapter "
            "multiplying boundary closure and bounded memory."
        ),
        "combined_sources": [
            "external_ai_model_prior_ingest:NTv3.long_range_sequence_function",
            "holographic_boundary_bulk",
            "fractional_memory",
        ],
        "use_as": "biological or text-sequence dependency prior for long-range Hutter structure",
        "decision": "HOLD_BIORXIV_PREPRINT_PRIOR",
        "promotion_gate": "requires source/model-card receipts, license check, local benchmark, and declared biological/text adapter",
    },
    {
        "equation_id": "landau_gauntlet_admission_operator",
        "equation": "G(E)=1[derive_F0(E)] * 1[replay(E)] * 1[baseline(E)] * 1[resource(E)] * 1[residual(E)]",
        "reads_as": (
            "A PhysMaster/LANDAU-style generated equation is admitted only if the gauntlet "
            "can derive its primitive form, replay it, beat baselines, obey resource limits, and bound residuals."
        ),
        "combined_sources": [
            "external_ai_model_prior_ingest:PhysMaster.LANDAU_agent_trace",
            "godel_gauntlet",
            "foundation_forward_equation_compiler",
        ],
        "use_as": "equation candidate promotion gate",
        "decision": "HOLD_EXTERNAL_AGENT_PRIOR",
        "promotion_gate": "requires task trace, code artifact, numeric replay, critic failure log, and independent verifier",
    },
    {
        "equation_id": "expand_or_compress_ladder_operator",
        "equation": "L(X)=pi_{k-1}(X) if closure and cost improve; Phi_{k+1}(X) if residual remains; bottom if root/NaN0/rollback fails",
        "reads_as": (
            "The Collatz-style ladder is not number theory here; it is the search-control "
            "law that decides whether a state compresses, expands, or terminates."
        ),
        "combined_sources": [
            "collatz_ladder_shadow_filter",
            "torsion_indexed_network_witness_topology",
            "underverse_variant_accounting",
        ],
        "use_as": "state-transition law for frame-invariant roots and M-JPEG-like independent frame decode",
        "decision": "ADMIT_AS_HOLD_MODEL_CHART",
        "promotion_gate": "requires executable fixture proving branch decisions are deterministic and receipt-bound",
    },
    {
        "equation_id": "adversarial_phase_safety_filter",
        "equation": "P_safe(Y)=1[delay(Y)<=d_max] * 1[phase_energy(Y)<=p_max] * 1[no_disorientation_feedback(Y)]",
        "reads_as": (
            "Audio, response-time, and phonon/logogram layers need an anti-music guard that "
            "rejects delayed or phase-shaped feedback intended to impair the observer."
        ),
        "combined_sources": [
            "phonon_music_logogram_layer",
            "underverse_variant_accounting",
            "observer_chart_projection_guardrail",
        ],
        "use_as": "safety gate for phased audio, anti-BPM, and observer-feedback channels",
        "decision": "HOLD_SAFETY_CONDITION",
        "promotion_gate": "requires benign/negative controls, accessibility policy, and no-harm playback constraints",
    },
    {
        "equation_id": "cross_domain_prior_pressure",
        "equation": "P_cross(X)=sum_j beta_j * gate_j(X) * adapter_j(X) - residual_cost(X)",
        "reads_as": (
            "External priors may create search pressure only through declared gates and adapters, "
            "with residual cost subtracted before any route is promoted."
        ),
        "combined_sources": [
            "external_ai_model_prior_ingest",
            "underverse_variant_accounting",
            "network_topology_model_reweighting",
        ],
        "use_as": "single accounting surface for outside model, biology, physics, and media priors",
        "decision": "HOLD_EXTERNAL_MODEL_PRIOR",
        "promotion_gate": "requires every beta, gate, adapter, and residual cost to be receipt-backed",
    },
    {
        "equation_id": "torsional_beaver_beta_step",
        "equation": "Omega_secure=Psi_Beaver[B_theta tensor C_shared] xor Delta_privacy",
        "reads_as": (
            "A Beaver-triple multiplication can be reinterpreted as a torsion-bearing "
            "basis/context coupling step, as long as the original MPC privacy boundary "
            "and exact closure equation remain explicit."
        ),
        "combined_sources": [
            "beaver_triples_cognitive_load_integrated_data",
            "torsion_indexed_network_witness_topology",
            "underverse_variant_accounting",
        ],
        "use_as": "privacy-preserving multiplication primitive for route-efficiency and eigenmode factors",
        "decision": "HOLD_RAINBOW_RACCOON_DERIVATION",
        "promotion_gate": "requires explicit lineage separation, independent MPC derivation, exact arithmetic fixture, and no copied implementation surface",
    },
    {
        "equation_id": "secure_cognitive_load_efficiency",
        "equation": "E_secure(N)=E_ext(N)*exp(-zeta*L_inv_enhanced(N))",
        "reads_as": (
            "The extended topology score is discounted by invariant-aware cognitive, "
            "routing, memory, trajectory, and convergence-inhibition load."
        ),
        "combined_sources": [
            "network_topology_equation",
            "beaver_triples_cognitive_load_integrated_data",
            "decoder_reconstruction_core",
        ],
        "use_as": "secure distributed route score with explicit cognitive/load penalty",
        "decision": "HOLD_COEFFICIENT_RECEIPT_DEBT",
        "promotion_gate": "requires coefficient receipts, fixture workloads, baseline routes, and invariant failure negative controls",
    },
    {
        "equation_id": "inflight_delayline_famm_efficiency",
        "equation": "E_inflight(N,eps,dl,FAMM)=E_secure(N)*Omega_AngrySphinx*Gamma_DelayLine*Phi_FAMM",
        "reads_as": (
            "A route can be scored as secure inflight computation only after applying "
            "defensive cost amplification, delay-line jitter/lag/salt loss, and FAMM route-memory pressure."
        ),
        "combined_sources": [
            "angrysphinx_delayline_famm_integrated_data",
            "secure_cognitive_load_efficiency",
            "hutter_torsion_clock_adaptation",
        ],
        "use_as": "HOLD equation for defensive inflight route accounting",
        "decision": "HOLD_RAINBOW_RACCOON_DERIVATION",
        "promotion_gate": "requires benign defensive threat model, resource envelope, timing fixture, and proof that no abusive traffic or resource harvesting is enabled",
    },
    {
        "equation_id": "minimal_node_resource_accounting_guard",
        "equation": "R_account=R_inflight*(1-Omega_AngrySphinx)*(1-Gamma_DelayLine)*(1-Phi_FAMM)",
        "reads_as": (
            "The resource term must be treated as an accounting guard, not permission "
            "to consume third-party nodes. Any real use must be local, consented, and bounded."
        ),
        "combined_sources": [
            "angrysphinx_delayline_famm_integrated_data",
            "hutter_prize_next_roadmap",
            "godel_gauntlet_safety_condition",
        ],
        "use_as": "local resource-budget guard for prize-rule and safety accounting",
        "decision": "HOLD_RESOURCE_AND_CONSENT_BOUNDARY",
        "promotion_gate": "requires local-only fixture, explicit consent boundary, hard resource limits, and prize-rule byte/runtime receipts",
    },
    {
        "equation_id": "isomorphic_congestion_chunking",
        "equation": "V_16=direct_sum_i C_i, n=ceil(16/chunk_size(congestion_level))",
        "reads_as": (
            "During congestion, the 16D Rainbow Raccoon state can be decomposed into "
            "adaptive chunks while preserving the structural relationships needed for reconstruction."
        ),
        "combined_sources": [
            "isomorphic_chunking_congestion",
            "rainbow_raccoon_derivation",
            "hutter_multidimensional_causal_chain",
        ],
        "use_as": "congestion-adaptive chunking law for frame/state transport",
        "decision": "HOLD_ISOMORPHIC_CHUNKING",
        "promotion_gate": "requires deterministic chunk boundaries, congestion fixture, reconstruction receipt, and exact source/root replay",
    },
    {
        "equation_id": "chunk_isomorphism_preservation_gate",
        "equation": "G_iso(C_i,C_j)=1[norm_F(phi(C_i)-C_j)<=eps_isomorphic]",
        "reads_as": (
            "A chunked state remains admissible only when the declared structure-preserving "
            "map between chunks stays within the isomorphism tolerance."
        ),
        "combined_sources": [
            "isomorphic_chunking_congestion",
            "torsion_indexed_admissibility_gate",
            "underverse_variant_accounting",
        ],
        "use_as": "chunk reconstruction guard and negative-control target",
        "decision": "HOLD_ISOMORPHISM_GATE",
        "promotion_gate": "requires explicit phi definition, norm implementation, tolerance derivation, and failing negative controls",
    },
    {
        "equation_id": "chunked_energy_loss_objective",
        "equation": "E_loss_min_chunked=min_strategy(E_loss_16D+E_loss_chunking+E_loss_reconstruction)",
        "reads_as": (
            "The chunking strategy is selected by minimizing total loss from the base "
            "16D projection, chunk boundaries, and reconstruction error."
        ),
        "combined_sources": [
            "rainbow_raccoon_energy_conservation",
            "isomorphic_chunking_congestion",
            "receipt_weighted_torsion_route_field",
        ],
        "use_as": "optimization objective for choosing no chunking, 2/4/8 chunks, redundancy, or alternate projection",
        "decision": "HOLD_OPTIMIZATION_OBJECTIVE",
        "promotion_gate": "requires measured loss terms, strategy enumeration, baseline comparison, and receipt-bound minimizer",
    },
    {
        "equation_id": "degraded_chunk_reconstruction_gate",
        "equation": "G_degraded=1[chunk_loss_rate<=theta_chunk_loss]*1[residual_error<=eps_error]*G_iso",
        "reads_as": (
            "Partial chunk loss can only degrade gracefully when loss rate, residual error, "
            "and isomorphism preservation all remain inside declared gates."
        ),
        "combined_sources": [
            "isomorphic_chunking_congestion",
            "godel_gauntlet_safety_condition",
            "minimal_node_resource_accounting_guard",
        ],
        "use_as": "safety gate for partial reconstruction under congestion",
        "decision": "HOLD_DEGRADED_RECONSTRUCTION_GATE",
        "promotion_gate": "requires lost-chunk fixtures, retransmission path, degraded receipt, and explicit refusal cases",
    },
    {
        "equation_id": "famm_chunk_route_bias",
        "equation": "L_famm_chunk=sum_i(chunk_i_success^2+chunk_i_failure+delta_phi_i)",
        "reads_as": (
            "FAMM route memory can bias future chunk routes away from repeated failures "
            "while preserving near-miss and phase-delta signals."
        ),
        "combined_sources": [
            "isomorphic_chunking_congestion",
            "famm_route_integration",
            "hutter_differential_frame_chain",
        ],
        "use_as": "route-memory penalty for chunk scheduling and retransmission choice",
        "decision": "HOLD_FAMM_CHUNK_BIAS",
        "promotion_gate": "requires route-history fixture, bounded update rule, no starvation proof, and replayable chunk schedule",
    },
    {
        "equation_id": "stenographic_hop_sequence_gate",
        "equation": "H_t=(f_1,...,f_n), hop(t+1)=adapt_hop(hop(t), network_state(t))",
        "reads_as": (
            "The carrier path can hop across declared 16D frequency bins only when the "
            "hop sequence is receipt-bound, collision-separated, and gate-approved."
        ),
        "combined_sources": [
            "stenographic_hopping_mimo_analogs",
            "isomorphic_chunking_congestion",
            "adversarial_phase_safety_filter",
        ],
        "use_as": "frequency/path diversity scheduler for chunked Rainbow Raccoon transport",
        "decision": "HOLD_STENOGRAPHIC_HOPPING",
        "promotion_gate": "requires deterministic hop seed receipt, anti-collision spacing, benign fixture, and refusal cases for adversarial hop patterns",
    },
    {
        "equation_id": "mimo_16d_channel_model",
        "equation": "Y_f=H_f X_f+N_f",
        "reads_as": (
            "A 16D Rainbow Raccoon state can be viewed through a MIMO-style channel "
            "where the transmitted Beaver-triple superposition is transformed by a frequency-indexed channel matrix."
        ),
        "combined_sources": [
            "stenographic_hopping_mimo_analogs",
            "rainbow_raccoon_derivation",
            "waveprobe_eigenmode_separation",
        ],
        "use_as": "channel model for parallel chunk or Beaver-triple transport",
        "decision": "HOLD_MIMO_CHANNEL_ANALOG",
        "promotion_gate": "requires declared dimensions, channel fixture, noise model, and decode/reconstruction receipt",
    },
    {
        "equation_id": "mimo_capacity_diagnostic",
        "equation": "C=mean_f log2(det(I+(rho/N_t)*H_f*H_f_H))",
        "reads_as": (
            "MIMO capacity is used as a diagnostic for how much parallel Beaver-triple "
            "or chunk traffic a declared channel can carry, not as a validation claim."
        ),
        "combined_sources": [
            "stenographic_hopping_mimo_analogs",
            "receipt_weighted_torsion_route_field",
            "minimal_node_resource_accounting_guard",
        ],
        "use_as": "capacity-side diagnostic for strategy selection under congestion",
        "decision": "HOLD_CAPACITY_DIAGNOSTIC",
        "promotion_gate": "requires measured or synthetic H_f fixture, SNR declaration, baseline capacity check, and resource-bound replay",
    },
    {
        "equation_id": "adaptive_mimo_channel_estimator",
        "equation": "H_estimated(t+1)=adapt(H_estimated(t), pilot_symbols(t))",
        "reads_as": (
            "The projection/channel matrix may adapt only through declared pilot symbols "
            "and a receipt-bound estimator such as RLS or a Kalman-style update."
        ),
        "combined_sources": [
            "stenographic_hopping_mimo_analogs",
            "network_adaptation_protocol_tuning",
            "godel_gauntlet_safety_condition",
        ],
        "use_as": "bounded matrix update rule for dynamic 16D-to-4D projection tuning",
        "decision": "HOLD_ADAPTIVE_CHANNEL_ESTIMATION",
        "promotion_gate": "requires pilot-symbol fixture, bounded update norm, rollback hash, and negative-transfer gate",
    },
    {
        "equation_id": "mimo_beamforming_beaver_route",
        "equation": "w_f=dominant_eigenvector(H_f*H_f_H), X_f=w_f*(a,b,c)",
        "reads_as": (
            "Beamforming selects a dominant spatial/channel direction for Beaver-triple "
            "or chunk transport while keeping the route decision receipt-bound."
        ),
        "combined_sources": [
            "stenographic_hopping_mimo_analogs",
            "secure_cognitive_load_efficiency",
            "famm_chunk_route_bias",
        ],
        "use_as": "directional route selector for MIMO-style chunk transport",
        "decision": "HOLD_BEAMFORMING_ROUTE_SELECTOR",
        "promotion_gate": "requires eigenvector fixture, deterministic tie-breaks, no-starvation check, and exact reconstruction receipt",
    },
    {
        "equation_id": "hopping_mimo_total_loss",
        "equation": "E_loss_total=E_loss_16D+E_loss_hopping+E_loss_MIMO+E_loss_polariton",
        "reads_as": (
            "The hopping/MIMO/polariton layer is admissible only when the added route "
            "diversity costs are counted alongside the base 16D projection loss."
        ),
        "combined_sources": [
            "stenographic_hopping_mimo_analogs",
            "chunked_energy_loss_objective",
            "landau_gauntlet_admission_operator",
        ],
        "use_as": "total-loss objective for deciding whether hopping/MIMO is worth using",
        "decision": "HOLD_TOTAL_LOSS_OBJECTIVE",
        "promotion_gate": "requires separate measured loss terms, no-hop baseline, MIMO baseline, and receipt-bound minimizer",
    },
    {
        "equation_id": "pathfinding_line_utility_selector",
        "equation": "route_line(l)=argmax_s U_s(l), s in {prediction_cache, ram_trace}",
        "reads_as": (
            "The pathfinding algorithm chooses the most useful reconstruction lines by "
            "routing each line either into prediction cache or RAM trace evidence."
        ),
        "combined_sources": [
            "civic_design_path_finding",
            "decoder_reconstruction_core",
            "famm_route_integration",
        ],
        "use_as": "line-level selector for cache-vs-trace placement",
        "decision": "HOLD_LINE_UTILITY_SELECTOR",
        "promotion_gate": "requires line identity receipts, deterministic selector fixture, cache/trace baselines, and exact replay of chosen lines",
    },
    {
        "equation_id": "prediction_cache_line_value",
        "equation": "U_cache(l)=p_hit(l)*bytes_saved(l)-stale_penalty(l)-receipt_cost(l)",
        "reads_as": (
            "A line belongs in prediction cache when it is likely to recur, saves bytes, "
            "and does not carry too much staleness or receipt overhead."
        ),
        "combined_sources": [
            "enwiki9_logogram_receipt_aggregation_probe",
            "receipt_weighted_torsion_route_field",
            "soft_parallel_route_revision",
        ],
        "use_as": "cache utility score for repeated decoder-facing lines",
        "decision": "HOLD_CACHE_VALUE_MODEL",
        "promotion_gate": "requires cache-hit fixture, stale-cache negative controls, counted byte savings, and cache invalidation receipt",
    },
    {
        "equation_id": "ram_trace_line_value",
        "equation": "U_trace(l)=replay_gain(l)+causal_gain(l)+anomaly_gain(l)-trace_bytes(l)-privacy_risk(l)",
        "reads_as": (
            "A line belongs in RAM traces when it improves replay, causal ordering, or "
            "anomaly detection enough to justify trace bytes and privacy risk."
        ),
        "combined_sources": [
            "delay_line_ram_inflight_computation",
            "hutter_differential_frame_chain",
            "godel_gauntlet_race_condition",
        ],
        "use_as": "trace utility score for causal and replay-sensitive lines",
        "decision": "HOLD_TRACE_VALUE_MODEL",
        "promotion_gate": "requires RAM-trace fixture, privacy boundary, replay improvement metric, and trace-pruning negative controls",
    },
    {
        "equation_id": "cache_trace_arbitration_gate",
        "equation": "G_cache_trace(l)=1[root_ok(l)]*1[choice_cost(l)<incumbent_cost(l)]*1[residual_bounded(l)]",
        "reads_as": (
            "A line routing decision is admissible only if the selected cache/trace path "
            "keeps roots valid, improves counted cost, and bounds residual ambiguity."
        ),
        "combined_sources": [
            "pathfinding_line_utility_selector",
            "torsion_indexed_admissibility_gate",
            "combined_approach_equation_surface",
        ],
        "use_as": "promotion gate for cache-vs-trace line placement",
        "decision": "HOLD_CACHE_TRACE_ARBITRATION",
        "promotion_gate": "requires root recomputation, incumbent comparison, residual receipt, and rollback for wrong line placement",
    },
    {
        "equation_id": "compiler_pipeline_line_lowering_prior",
        "equation": "line -> token -> AST -> IR -> SSA -> optimized_value -> object_artifact",
        "reads_as": (
            "The Go compiler pipeline is a concrete prior for treating lines as staged "
            "representations, where later stages preserve only the forms useful for execution, replay, or downstream consumers."
        ),
        "combined_sources": [
            "https://blog.gaborkoos.com/posts/2026-05-08-The-Go-Compiler-a-Deep-Dive-Into-How-Your-Code-Becomes-a-Binary/",
            "pathfinding_line_utility_selector",
            "decoder_reconstruction_core",
        ],
        "use_as": "compiler-pipeline prior for line lowering and staged cache/trace placement",
        "decision": "HOLD_EXTERNAL_COMPILER_PIPELINE_PRIOR",
        "promotion_gate": "requires local compiler fixture, line-to-stage receipts, and no claim that Go internals validate Hutter compression",
    },
    {
        "equation_id": "ssa_dependency_line_trace",
        "equation": "G_ssa=(Blocks,Values,Edges), def_count(v)=1, uses(v)->def(v)",
        "reads_as": (
            "SSA makes data dependencies explicit, so a useful line can be valued by "
            "the graph of definitions, uses, phi joins, and optimization opportunities it creates."
        ),
        "combined_sources": [
            "go_compiler_ssa_prior",
            "ram_trace_line_value",
            "hutter_differential_frame_chain",
        ],
        "use_as": "RAM-trace prior for line causality and local graph rewrite value",
        "decision": "HOLD_SSA_TRACE_PRIOR",
        "promotion_gate": "requires SSA-like fixture, explicit dependency graph, phi-node receipt, and replay improvement metric",
    },
    {
        "equation_id": "ir_normalization_cache_prior",
        "equation": "U_ir_cache(l)=normalization_reuse(l)*surface_forms_collapsed(l)-lowering_cost(l)",
        "reads_as": (
            "IR lowering is a cache prior: source-surface variety can collapse into "
            "a smaller semantic core that is cheaper to reuse than to reparse repeatedly."
        ),
        "combined_sources": [
            "go_compiler_ir_prior",
            "prediction_cache_line_value",
            "enwiki9_logogram_receipt_aggregation_probe",
        ],
        "use_as": "prediction-cache score for normalized line forms",
        "decision": "HOLD_IR_NORMALIZATION_PRIOR",
        "promotion_gate": "requires equivalence-class fixture, lowering receipt, byte savings measurement, and wrong-normalization negative controls",
    },
    {
        "equation_id": "phi_cache_trace_merge_gate",
        "equation": "Phi_line=select(pred_block, cache_line, trace_line)",
        "reads_as": (
            "A phi-like merge lets the decoder choose between cached prediction and RAM "
            "trace evidence based on the path that reached the merge point."
        ),
        "combined_sources": [
            "go_compiler_ssa_phi_prior",
            "cache_trace_arbitration_gate",
            "expand_or_compress_ladder_operator",
        ],
        "use_as": "merge gate for branch-dependent cache/trace line recovery",
        "decision": "HOLD_PHI_MERGE_PRIOR",
        "promotion_gate": "requires branch fixture, deterministic predecessor selection, root recomputation, and rollback on wrong merge",
    },
    {
        "equation_id": "x86_emulator_shape_baseline_vector",
        "equation": "B_e=[fetch_decode,state_flags,memory_address,control_flow,ir_lowering,cache_trace,host_codegen,vcpu_virtualization,exit_intercept,nested_paging]",
        "reads_as": (
            "Each x86 emulator or hypervisor source gets a baseline structural vector "
            "before any shape optimization is allowed."
        ),
        "combined_sources": [
            "x86_emulator_eigen_baseline",
            "pathfinding_line_utility_selector",
            "compiler_pipeline_line_lowering_prior",
        ],
        "use_as": "measured baseline for deciding whether cache, trace, IR, host lowering, VM-exit, or vCPU virtualization should be emphasized",
        "decision": "HOLD_X86_EMULATOR_BASELINE",
        "promotion_gate": "requires fetched source hashes, stable basis definitions, and rerun after upstream source drift",
    },
    {
        "equation_id": "x86_emulator_shape_distance_objective",
        "equation": "D(e,target)=||B_e-B_target||_2 + lambda*missing_source(e)",
        "reads_as": (
            "Optimization should be shape-aware: compare a candidate target shape "
            "against the measured emulator baseline instead of optimizing blind."
        ),
        "combined_sources": [
            "x86_emulator_shape_baseline_vector",
            "chunked_energy_loss_objective",
            "cache_trace_arbitration_gate",
        ],
        "use_as": "distance objective for selecting interpreter, trace-cache, IR, or dynarec-like shape",
        "decision": "HOLD_SHAPE_DISTANCE_OBJECTIVE",
        "promotion_gate": "requires target vector declaration, deterministic norm calculation, baseline comparison, and negative controls",
    },
    {
        "equation_id": "baseline_shape_axis_gate",
        "equation": "G_shape(e)=argmax(cache_trace(e),ir_lowering(e),host_codegen(e),fetch_decode(e),control_flow(e),vcpu_virtualization(e),exit_intercept(e),nested_paging(e))",
        "reads_as": (
            "The pathfinding/cache/trace selector should first ask which emulator "
            "axis dominates the baseline source, then choose a compatible storage or lowering strategy."
        ),
        "combined_sources": [
            "x86_emulator_eigen_baseline",
            "prediction_cache_line_value",
            "ram_trace_line_value",
        ],
        "use_as": "baseline-gated choice between prediction cache, RAM trace, IR lowering, and interpreter control flow",
        "decision": "HOLD_BASELINE_AXIS_GATE",
        "promotion_gate": "requires axis tie-break rules, source refresh receipt, cache/trace workload fixture, and exact replay",
    },
    {
        "equation_id": "modly_text_to_cad_guess_residual_loop",
        "equation": "R_guess=features(Modly_mesh)-features(render(TextToCAD_source))",
        "reads_as": (
            "A local image-to-mesh model guess can be made legible by comparing its "
            "mesh features against the rendered output of regenerated parametric CAD source."
        ),
        "combined_sources": [
            "modly_text_to_cad_bridge",
            "rainbow_raccoon_derivation",
            "mesh_prior_to_parametric_cad",
        ],
        "use_as": "show what the model guessed at and convert the mismatch into bounded compiler residuals",
        "decision": "HOLD_GUESS_RESIDUAL_LOOP",
        "promotion_gate": "requires local mesh artifact, source regeneration, render comparison, residual metric, and rollback receipt",
    },
    {
        "equation_id": "rainbow_raccoon_cad_refinement_step",
        "equation": "CAD_{t+1}=compile(CAD_t,R_guess_t,constraints,closure_receipt_t)",
        "reads_as": (
            "Rainbow Raccoon acts as the compiler loop that turns observed model guesses "
            "and residuals into the next parametric CAD source revision."
        ),
        "combined_sources": [
            "modly_text_to_cad_bridge",
            "self_refining_cad_compiler_step",
            "cad_source_promotion_gate",
        ],
        "use_as": "bounded self-refinement step for mesh-to-parametric CAD conversion",
        "decision": "HOLD_SELF_REFINING_CAD_COMPILER",
        "promotion_gate": "requires deterministic source diff, explicit constraints, regenerated CAD outputs, and closure receipt",
    },
    {
        "equation_id": "mesh_guess_closure_gate",
        "equation": "G_guess=1[source_regenerates]*1[render_hash_recomputes]*1[residual_bounded]*1[rollback_exists]",
        "reads_as": (
            "An opaque model-generated mesh is never promoted directly; it must pass "
            "through source regeneration, render replay, residual bounds, and rollback."
        ),
        "combined_sources": [
            "modly_text_to_cad_bridge",
            "holographic_boundary_bulk",
            "folded_promotion_gate",
        ],
        "use_as": "promotion gate for model-guess-to-CAD refinement loops",
        "decision": "HOLD_GUESS_CLOSURE_GATE",
        "promotion_gate": "requires source regeneration, render hash replay, bounded residual, rollback hash, and negative controls",
    },
    {
        "equation_id": "transcriptformer_evolutionary_representation_prior",
        "equation": "Z_cell=f_theta(gene_identity,expression_count,species_embedding,evolutionary_context)",
        "reads_as": (
            "TranscriptFormer is an external prior for learning conserved representations "
            "from evolutionary breadth across species and cell states."
        ),
        "combined_sources": [
            "transcriptformer_evolutionary_prior",
            "engineering_fitness_topology_trait",
            "cross_domain_prior_pressure",
        ],
        "use_as": "biology-side prior that conserved organization can emerge from broad evolutionary training surfaces",
        "decision": "HOLD_EVOLUTIONARY_REPRESENTATION_PRIOR",
        "promotion_gate": "requires local benchmark, full-method receipt, data provenance, leakage controls, and no biological prediction promotion",
    },
    {
        "equation_id": "conserved_structure_emergence_gate",
        "equation": "G_conserved=1[hierarchy_emerges]*1[zero_shot_transfer]*1[negative_controls_pass]",
        "reads_as": (
            "Emergent hierarchy claims can affect topology theory only after transfer "
            "and negative-control evidence distinguish conserved structure from benchmark artifacts."
        ),
        "combined_sources": [
            "transcriptformer_evolutionary_prior",
            "landau_gauntlet_admission_operator",
            "receipt_weighted_torsion_route_field",
        ],
        "use_as": "gate for using emergent biological hierarchy as conserved-organization evidence",
        "decision": "HOLD_CONSERVED_STRUCTURE_GATE",
        "promotion_gate": "requires species-heldout tests, hierarchy metrics, baseline comparison, and independent negative controls",
    },
    {
        "equation_id": "homology_leakage_caveat",
        "equation": "Risk_leak=homology_overlap+species_signal_dominance+annotation_reuse+benchmark_pseudoreplication",
        "reads_as": (
            "Cross-species generalization claims must carry a leakage/confound lane for "
            "homology overlap, species clustering, annotation reuse, and pseudoreplication."
        ),
        "combined_sources": [
            "transcriptformer_evolutionary_prior",
            "underverse_variant_accounting",
            "godel_gauntlet_safety_condition",
        ],
        "use_as": "anti-overclaim caveat for evolutionary foundation-model priors",
        "decision": "HOLD_LEAKAGE_CAVEAT",
        "promotion_gate": "requires leakage audit, species-vs-cell-type decomposition, benchmark split receipt, and ablation fixtures",
    },
    {
        "equation_id": "logogram_species_code_adapter",
        "equation": "L_species=encode(conserved_tokens,lineage_markers,mutation_residuals,phenotype_closure)",
        "reads_as": (
            "The logogram can be treated as a species-code-like symbolic compression "
            "layer only when conserved tokens, lineage markers, mutation residuals, "
            "and phenotype/readout closure are explicit."
        ),
        "combined_sources": [
            "transcriptformer_evolutionary_prior",
            "phonon_music_logogram_layer",
            "decoder_facing_reconstruction_core",
        ],
        "use_as": "adapter from logogram tokens to genetic/species-code style accounting",
        "decision": "HOLD_LOGOGRAM_SPECIES_CODE_ADAPTER",
        "promotion_gate": "requires token lineage fixture, mutation/residual accounting, decode readout, and negative controls",
    },
    {
        "equation_id": "logogram_genotype_phenotype_closure",
        "equation": "G_logogram=1[decode(L)->phenotype_readout]*1[lineage_consistent]*1[residual_bounded]",
        "reads_as": (
            "A logogram code is not admitted as conserved structure unless it decodes "
            "to an observable readout, preserves lineage consistency, and bounds residuals."
        ),
        "combined_sources": [
            "logogram_species_code_adapter",
            "holographic_boundary_bulk",
            "mesh_guess_closure_gate",
        ],
        "use_as": "closure gate for logogram-as-species-code hypotheses",
        "decision": "HOLD_LOGOGRAM_PHENOTYPE_CLOSURE",
        "promotion_gate": "requires exact decode fixture, observable readout definition, lineage audit, residual bound, and rollback hash",
    },
    {
        "equation_id": "parquet_logogram_transcode_efficiency",
        "equation": "E_pq_log=(bytes_sample_parquet-bytes_logogram_species_global)/bytes_sample_parquet",
        "reads_as": (
            "When Parquet rows are transcoded into logogram species-code packets, "
            "the measured byte gain is the counted difference from an equivalent "
            "sample Parquet artifact, after packet and dictionary costs."
        ),
        "combined_sources": [
            "parquet_logogram_efficiency",
            "logogram_species_code_adapter",
            "decoder_facing_reconstruction_core",
        ],
        "use_as": "honest byte-accounting objective for Parquet-to-logogram transcode experiments",
        "decision": "HOLD_PARQUET_LOGOGRAM_EFFICIENCY",
        "promotion_gate": "requires exact replay, equivalent sample construction, schema hash replay, dictionary accounting, and Parquet baseline comparison",
    },
    {
        "equation_id": "columnar_lineage_logogram_gain",
        "equation": "G_lineage=(bytes_object_canonical-bytes_species_payload)/bytes_object_canonical",
        "reads_as": (
            "The species-code/logogram lane can save bytes by carrying schema and "
            "lineage markers once instead of repeating object keys in every row."
        ),
        "combined_sources": [
            "parquet_logogram_efficiency",
            "transcriptformer_evolutionary_prior",
            "logogram_species_code_adapter",
        ],
        "use_as": "separate schema/lineage reuse gain from total packet-vs-Parquet performance",
        "decision": "HOLD_COLUMNAR_LINEAGE_GAIN",
        "promotion_gate": "requires row-count fixture, canonical object baseline, species payload replay, and negative controls for wrong schema order",
    },
    {
        "equation_id": "parquet_logogram_exact_replay_gate",
        "equation": "G_pq_log=1[canonical_rows_decode]*1[schema_hash_recomputes]*1[row_count_matches]*1[residual_bounded]",
        "reads_as": (
            "A Parquet-to-logogram transcode is admissible only when the canonical "
            "rows decode, schema hash recomputes, row count matches, and residual "
            "lane is bounded."
        ),
        "combined_sources": [
            "parquet_logogram_efficiency",
            "holographic_boundary_bulk",
            "landau_gauntlet_admission_operator",
        ],
        "use_as": "promotion gate for treating logogram packets as a valid Parquet-derived representation",
        "decision": "HOLD_PARQUET_LOGOGRAM_REPLAY_GATE",
        "promotion_gate": "requires exact decoder fixture, schema-hash negative control, row-count mismatch refusal, and bounded residual receipt",
    },
    {
        "equation_id": "hybrid_parquet_logogram_sidecar_cost",
        "equation": "C_hybrid=(bytes_sidecar_packet+bytes_dictionary)/bytes_sample_parquet",
        "reads_as": (
            "Hybrid mode keeps Parquet as the storage substrate and counts the "
            "logogram control sidecar as overhead, rather than pretending the "
            "sidecar is free."
        ),
        "combined_sources": [
            "parquet_logogram_efficiency",
            "pathfinding_line_utility_selector",
            "cache_trace_arbitration_gate",
        ],
        "use_as": "sidecar overhead term for Parquet plus logogram routing/receipt metadata",
        "decision": "HOLD_HYBRID_SIDECAR_COST",
        "promotion_gate": "requires equivalent Parquet sample, sidecar decode replay, dictionary accounting, and overhead threshold receipts",
    },
    {
        "equation_id": "hybrid_materialization_avoidance_gain",
        "equation": "G_hybrid=(bytes_object_canonical-(bytes_sample_parquet+bytes_sidecar_packet+bytes_dictionary))/bytes_object_canonical",
        "reads_as": (
            "The useful hybrid gain is not raw replacement compression; it is the "
            "avoided expansion into object-row canonical materialization while "
            "retaining cache/trace/lineage routing metadata."
        ),
        "combined_sources": [
            "parquet_logogram_efficiency",
            "parquet_logogram_eigenprobe",
            "decoder_facing_reconstruction_core",
        ],
        "use_as": "materialization-avoidance objective for Parquet substrate plus logogram sidecar",
        "decision": "HOLD_HYBRID_MATERIALIZATION_GAIN",
        "promotion_gate": "requires workload fixture showing avoided materialization, exact row/schema receipts, and query/replay baseline comparison",
    },
    {
        "equation_id": "parquet_logogram_loss_eigen_axis",
        "equation": "PC_loss=eig(cov(z(features))), target=E_pq_log",
        "reads_as": (
            "The eigenprobe explains why replacement loses by decomposing source "
            "features into axes correlated with packet-vs-Parquet gain or loss."
        ),
        "combined_sources": [
            "parquet_logogram_eigenprobe",
            "x86_emulator_shape_baseline_vector",
            "baseline_shape_axis_gate",
        ],
        "use_as": "diagnostic axis for deciding whether to use replacement, sidecar, prediction cache, RAM trace, or native Parquet",
        "decision": "HOLD_PARQUET_LOGOGRAM_EIGEN_DIAGNOSTIC",
        "promotion_gate": "requires larger fixture matrix, feature stability check, negative controls, and rerun after encoder changes",
    },
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def source_ref(path: Path) -> dict[str, Any]:
    return {"path": rel(path), "exists": path.exists(), "sha256": file_hash(path)}


def candidate_entry(raw: dict[str, Any]) -> dict[str, Any]:
    entry = {
        **raw,
        "claim_boundary": "candidate equation surface only; not admitted as theorem, safety proof, or compression result",
    }
    entry["candidate_hash"] = hash_obj({k: v for k, v in entry.items() if k != "candidate_hash"})
    return entry


def build_payload() -> dict[str, Any]:
    candidates = [candidate_entry(item) for item in CANDIDATES]
    payload = {
        "schema": "combined_approach_equation_surface_v1",
        "name": "Combined Approach Equation Surface",
        "source_refs": [source_ref(path) for path in SOURCES],
        "claim_boundary": (
            "Equation-surface discovery only. New equations are HOLD candidates "
            "until local fixtures prove deterministic replay, counted resources, "
            "negative controls, provenance, and exact decode or safety closure."
        ),
        "candidate_equations": candidates,
        "candidate_root": hash_obj([item["candidate_hash"] for item in candidates]),
        "aggregates": {
            "candidate_count": len(candidates),
            "source_count": len(SOURCES),
            "missing_source_count": 0,
            "admitted_equation_count": 0,
            "hold_candidate_count": len(candidates),
        },
        "finding": (
            "The combined approaches expose equation surfaces for receipt-weighted "
            "routing, soft parallel revision, torsion-indexed admissibility, long-range "
            "sequence memory, gauntlet admission, ladder transition control, phase-safety, "
            "cross-domain prior pressure, Rainbow Raccoon secure inflight accounting, "
            "isomorphic congestion chunking, stenographic MIMO hopping, and cache/trace "
            "line-utility arbitration. The Go compiler pipeline adds an external HOLD "
            "prior for staged line lowering, IR normalization, SSA trace value, and "
            "phi-like cache/trace merging. The x86 emulator baseline probe adds measured "
            "source-shape vectors so cache/trace/IR/hypervisor optimization has baseline "
            "values, including Xen, KVM, VirtualBox, and bhyve VM-exit/vCPU surfaces. "
            "The Modly/text-to-CAD bridge adds a Rainbow Raccoon compiler loop for "
            "observing model mesh guesses, compiling them into parametric CAD, and "
            "feeding bounded residuals into self-refinement. TranscriptFormer adds a "
            "biology-side evolutionary foundation-model prior for conserved organization "
            "across 1.53B years of species distance, gated by homology/leakage caveats. "
            "The logogram species-code adapter treats logograms as genetic-style symbolic "
            "coding only under explicit lineage, mutation residual, and phenotype/readout closure gates. "
            "The Parquet-to-logogram efficiency probe adds a measured accounting lane: "
            "schema/key reuse can be separated from actual packet-vs-Parquet byte performance, "
            "so efficiency gains are counted rather than assumed. The Parquet/logogram eigenprobe "
            "explains why replacement loses on current fixtures and why hybrid sidecars are the "
            "better next shape: Parquet keeps physical storage while logograms carry schema lineage, "
            "cache/trace routing, and replay metadata. "
            "None are promoted beyond HOLD."
        ),
        "decision": "ADMIT_EQUATION_SURFACE_AS_HOLD_CANDIDATES",
    }
    payload["aggregates"]["missing_source_count"] = sum(1 for item in payload["source_refs"] if not item["exists"])
    payload["payload_hash"] = hash_obj({k: v for k, v in payload.items() if k != "payload_hash"})
    return payload


def build_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "combined_approach_equation_surface_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "payload_hash": payload["payload_hash"],
        "candidate_root": payload["candidate_root"],
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
        "# Combined Approach Equation Surface",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`  ",
        f"Candidate root: `{payload['candidate_root']}`",
        "",
        payload["claim_boundary"],
        "",
        "## Finding",
        "",
        payload["finding"],
        "",
        "## Candidate Equations",
        "",
        "| Candidate | Equation | Decision | Use as |",
        "|---|---|---|---|",
    ]
    for item in payload["candidate_equations"]:
        lines.append(f"| {item['equation_id']} | `{item['equation']}` | {item['decision']} | {item['use_as']} |")
    lines.extend(["", "## Promotion Gates", ""])
    for item in payload["candidate_equations"]:
        lines.append(f"- `{item['equation_id']}`: {item['promotion_gate']}")
    lines.extend(["", "## Source Receipts", ""])
    for item in payload["source_refs"]:
        status = "ok" if item["exists"] else "missing"
        lines.append(f"- `{item['path']}`: {status}")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "title: Combined Approach Equation Surface",
        "tags: EquationSurface Hutter NetworkTopology ExternalPrior HOLD Receipt",
        "type: text/vnd.tiddlywiki",
        "",
        "! Combined Approach Equation Surface",
        "",
        f"Decision: `{receipt['decision']}`",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        f"Candidate root: `{payload['candidate_root']}`",
        "",
        "!! Finding",
        "",
        payload["finding"],
        "",
        "!! Candidate Equations",
        "",
        "| Candidate | Decision |h",
    ]
    for item in payload["candidate_equations"]:
        lines.append(f"| {item['equation_id']} | {item['decision']} |")
    lines.extend(
        [
            "",
            "!! Boundary",
            "",
            payload["claim_boundary"],
            "",
            f"Receipt: `{rel(RECEIPT)}`",
        ]
    )
    TIDDLER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    receipt = build_receipt(payload)
    PAYLOAD_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    write_summary(payload, receipt)
    write_tiddler(payload, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
