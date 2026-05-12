#!/usr/bin/env python3
"""Receipt for reweighted cognitive-load equations with connectome-protective overflow."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
RECEIPT = SHIM / "connectome_protective_cognitive_load_reweighting_receipt.json"
CURRICULUM = SHIM / "connectome_protective_cognitive_load_reweighting_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "connectome_protective_cognitive_load_reweighting_v1",
        "source_type": "user_supplied_reweighting_equations_plus_local_multi_domain_cognitive_load_spec",
        "primary_read": (
            "Reweight cognitive load as a domain-specific response-family model with "
            "a protective overflow gate. Overflow shifts excess load into an emotional "
            "offload channel as a hypothesis about preserving working graph stability. "
            "The main intended use is historical and civilizational modeling of overload "
            "under accelerated information transfer; it does not erase load and does "
            "not prove biological connectome protection."
        ),
        "core_equations": {
            "raw_cognitive_load": (
                "L_cog_raw(d,x) = C_d * response_family_d(x; theta_d) * "
                "lambda_phi^D_f * B_gate(d,constraints)"
            ),
            "trauma_adjusted_threshold": (
                "L_threshold_eff = L_threshold * exp(-rho_T * T_trauma)"
            ),
            "bandwidth_adjusted_threshold": (
                "L_threshold_hist = L_threshold_eff * exp(-rho_B * B_overflow)"
            ),
            "bandwidth_overflow": (
                "B_overflow = max(0, transfer_bandwidth - assimilation_bandwidth) / assimilation_bandwidth"
            ),
            "trauma_adjusted_emotional_barrier": (
                "DeltaE_emotional_eff = DeltaE_emotional + chi_T * T_trauma"
            ),
            "historical_emotional_barrier": (
                "DeltaE_emotional_hist = DeltaE_emotional_eff + chi_B * B_overflow"
            ),
            "trauma_adjusted_emotional_temperature": (
                "kT_emotional_eff = kT_emotional / (1 + psi_T * T_trauma)"
            ),
            "historical_emotional_temperature": (
                "kT_emotional_hist = kT_emotional_eff / (1 + psi_B * B_overflow)"
            ),
            "overflow_gate": (
                "G_over(d) = 1 if L_cog_raw <= L_threshold_hist; "
                "else exp(-gamma_d * (L_cog_raw - L_threshold_hist) / kT_emotional_hist)"
            ),
            "effective_cognitive_load": "L_cog_eff = L_cog_raw * G_over",
            "emotional_offload": (
                "L_emotional_offload = max(0, L_cog_raw - L_threshold_hist) * eta_offload_hist"
            ),
            "trauma_adjusted_offload_efficiency": (
                "eta_offload_eff = eta_offload * exp(-omega_T * T_trauma)"
            ),
            "historical_offload_efficiency": (
                "eta_offload_hist = eta_offload_eff * exp(-omega_B * B_overflow)"
            ),
            "emotional_load": (
                "L_emotional = C_emotional,d * emotional_response_d(L_emotional_offload; "
                "theta_emotional,d) * lambda_phi^D_f * B_gate_emotional,d"
            ),
            "emotional_gate": (
                "B_gate_emotional = exp(-gamma_emotional * DeltaE_emotional_hist / kT_emotional_hist)"
            ),
            "residual_stress": (
                "L_residual_stress = max(0, L_cog_raw - L_threshold_hist) * (1 - eta_offload_hist)"
            ),
            "total_protective_load": (
                "L_total = L_cog_eff + L_emotional + L_residual_stress"
            ),
            "threshold": "L_threshold = C_threshold * lambda_phi^D_f * B_gate_threshold",
        },
        "domain_response_families": {
            "text": {
                "cognitive": "log(1 + beta_text * complexity)",
                "emotional": "log(1 + beta_emotional_text * L_emotional_offload)",
                "reason": "text and language often compress broad semantic scale into thresholded/log-like response",
            },
            "code": {
                "cognitive": "(complexity / (K_code + complexity))^hill_code",
                "emotional": "(L_emotional_offload / (K_emotional + L_emotional_offload))^hill_emotional",
                "reason": "working-memory and frustration effects are better modeled as saturating channels",
            },
            "visual": {
                "cognitive": "(V_max * visual_complexity) / (K_M + visual_complexity)",
                "emotional": "(V_max_emotional * L_emotional_offload) / (K_M_emotional + L_emotional_offload)",
                "reason": "feature extraction and visual overload are saturation-limited",
            },
            "audio": {
                "cognitive": "audio_complexity^alpha_audio",
                "emotional": "L_emotional_offload^alpha_emotional",
                "reason": "auditory load is modeled as low-exponent accumulation",
            },
            "multimodal": {
                "cognitive": "sum_d w_d * response_family_d(complexity_d; theta_d)",
                "emotional": "sum_d w_d * L_emotional,d",
                "reason": "cross-modal load is an adaptive mixture with interference weights",
            },
        },
        "component_reweighting": {
            "base_components": ["L_I", "L_E", "L_G", "L_R", "L_M"],
            "raw_sum": "L_cog_raw = w_I L_I + w_E L_E - w_G L_G + w_R L_R + w_M L_M",
            "constraints": [
                "sum positive weights before signed germane term is normalized",
                "w_G is bounded so germane load cannot create impossible negative load",
                "all component families are selected by measured error and held-out validation",
                "overflow is computed from raw load before suppression",
                "effective load and emotional load are reported separately",
            ],
        },
        "phi_prior": {
            "D_f": "log(2)/log(phi) ~= 1.44042009041",
            "phi_gain": "phi^D_f = 2",
            "phi_squared_gain": "(phi^2)^D_f = 4",
            "claim": "Phi remains a topology prior, not a universal load law.",
        },
        "connectome_protection_interpretation": {
            "defensible_form": (
                "overflow offload is a stability hypothesis for preserving working "
                "cognitive graph coherence under load"
            ),
            "trauma_reweighting": (
                "trauma is modeled as an energy-landscape modifier: it can lower the "
                "effective cognitive threshold, raise the emotional regulation barrier, "
                "reduce offload efficiency, and increase residual stress after overflow"
            ),
            "historical_bandwidth_reweighting": (
                "accelerated information transfer is modeled as bandwidth overflow: when "
                "transfer bandwidth exceeds assimilation bandwidth, the historical threshold "
                "drops, regulation barriers rise, offload efficiency falls, and residual "
                "social/emotional stress accumulates"
            ),
            "psychohistory_analogy": (
                "Harry Seldon-style psychohistory is a useful fictional analogy for the "
                "population-scale version: not prediction of individuals, but modeling "
                "aggregate phase pressure from bandwidth, assimilation lag, institutional "
                "response, and overflow dynamics"
            ),
            "avoid_overclaim": [
                "do not claim measured biological damage prevention",
                "do not claim emotional offload is cost-free",
                "do not claim emotional load is pathology",
                "do not treat trauma as a scalar clinical diagnosis",
                "do not treat historical bandwidth overflow as proof of causality without archival or quantitative anchors",
                "do not cite psychohistory as evidence; use it only as a structural metaphor",
                "do not promote without local/empirical threshold calibration",
            ],
        },
        "required_measurements": [
            "domain complexity metric",
            "component load vector",
            "response-family fit error",
            "held-out validation error",
            "threshold calibration",
            "overflow amount",
            "emotional offload estimate",
            "residual stress or unresolved load",
            "trauma exposure/stress proxy if used, with explicit consent and privacy boundary",
            "historical transfer bandwidth proxy",
            "historical assimilation bandwidth proxy",
            "archive, media, literacy, institution, or infrastructure anchor for bandwidth assumptions",
            "population-scale outcome proxy if using psychohistory-style aggregate modeling",
        ],
        "promotion_rule": [
            "domain response family selected by measured error and validation",
            "overflow threshold calibrated or explicitly marked hypothetical",
            "trauma modifiers calibrated or explicitly marked hypothetical",
            "bandwidth overflow modifiers calibrated or explicitly marked historical hypothesis",
            "emotional offload reported as separate channel",
            "phi gain used only as topology prior",
            "claim boundary distinguishes model hypothesis from biological proof",
        ],
        "failure_rules": [
            "protective offload described as proven brain mechanism -> overclaim",
            "emotional offload treated as zero-cost load deletion -> invalid model",
            "threshold missing -> hold",
            "trauma proxy used without consent/privacy boundary -> invalid measurement",
            "trauma modeled as simple blame/defect variable -> invalid framing",
            "historical bandwidth overflow asserted without source anchors -> hold",
            "accelerated information transfer treated as single-cause history -> overclaim",
            "fictional psychohistory analogy treated as evidence -> invalid citation",
            "response family chosen by preference instead of validation -> hold",
            "germane negative term drives total load below zero -> clamp or reject",
            "phi gain used as universal law -> overclaim",
        ],
        "linked_artifacts": [
            "4-Infrastructure/shim/multi_domain_adaptive_cognitive_load.md",
            "6-Documentation/tiddlywiki-local/wiki/tiddlers/Phi Scaling Response Model Selection.tid",
            "6-Documentation/tiddlywiki-local/wiki/tiddlers/Connectome Manipulation Self Update Prior.tid",
            "6-Documentation/tiddlywiki-local/wiki/tiddlers/Holographic Fractional Recursive Connectome Prior.tid",
        ],
        "claim_boundary": (
            "This is a reweighting receipt for a cognitive-load model hypothesis. "
            "It is not medical advice, not a validated neuroscience result, and not "
            "proof that emotional processing protects biological connectomes."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "compute_protective_load_channels",
            "input": "raw cognitive load, threshold, emotional energy scale, offload efficiency",
            "target": "effective cognitive load, emotional offload, emotional load, residual stress",
        },
        {
            "task": "select_domain_response_family",
            "input": "domain complexity and observed load data",
            "target": "log, Hill, Michaelis-Menten, low-exponent, or mixture selected by validation",
        },
        {
            "task": "reject_overclaiming_connectome_protection",
            "input": "protective overflow claim",
            "target": "hypothesis unless biological/behavioral measurements calibrate threshold and offload",
        },
    ]
    CURRICULUM.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> None:
    receipt = build_receipt()
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_curriculum(receipt)
    print(json.dumps({
        "receipt": str(RECEIPT.relative_to(REPO)),
        "curriculum": str(CURRICULUM.relative_to(REPO)),
        "receipt_hash": receipt["receipt_hash"],
        "domain_count": len(receipt["domain_response_families"]),
        "failure_rule_count": len(receipt["failure_rules"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
