#!/usr/bin/env python3
"""PDE model prior metaprobe for n-space LLM tuning.

PDE foundation/assistant models are useful here as compression coordinates:
operator tokens, boundary-condition conditioning, spatiotemporal grids,
shape-agnostic fields, control autoformalization, and code-generation routes.
This script records verified priors and softer user-supplied candidates without
turning any of them into numerical truth.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PDE_AXES = [
    {
        "axis": "operator_learning",
        "payload": ["PDE_operator", "initial_condition", "boundary_condition", "coefficients", "solution_field"],
        "router_use": "map symbolic PDE descriptions into operator-family compression cells",
        "receipt_rule": "record PDE class, boundary distribution, discretization, and residual/evaluation metric",
    },
    {
        "axis": "spatiotemporal_field",
        "payload": ["space_dim", "time_steps", "grid_or_mesh", "field_channels", "resolution"],
        "router_use": "n-space field packet for transformer/neural-operator priors",
        "receipt_rule": "record dimension, units, grid/mesh type, and downsample/patching rule",
    },
    {
        "axis": "shape_agnostic_geometry",
        "payload": ["1D", "2D", "3D", "heterogeneous_resolution", "scalar_vector_components"],
        "router_use": "geometry-invariant compression axis across domains",
        "receipt_rule": "record geometry map, coordinate frame, and transfer/fine-tune target",
    },
    {
        "axis": "pde_workflow_controller",
        "payload": ["informal_spec", "formal_spec", "subgoal", "solver_code", "utility_metric"],
        "router_use": "route language claims into formal/controller/code-generation surfaces",
        "receipt_rule": "formal spec and generated code must be checked by external solver or local verifier",
    },
    {
        "axis": "mesh_free_residual_probe",
        "payload": ["coordinate_sample", "pde_residual", "boundary_residual", "loss_weight", "collocation_seed"],
        "router_use": "PINN-style sparse coordinate probes for n-space manifolds without Cartesian grid expansion",
        "receipt_rule": "record sampled coordinates, PDE residual definition, boundary residual, seed, and held-out residual check",
    },
    {
        "axis": "latent_operator_compression",
        "payload": ["function_space_token", "spectral_modes", "latent_operator", "decode_rule", "resolution_transfer"],
        "router_use": "FNO/neural-operator style compression of function-space dynamics into reusable latent operators",
        "receipt_rule": "record train/eval resolution, retained modes, operator family, and extrapolation target",
    },
    {
        "axis": "stochastic_path_solver",
        "payload": ["brownian_path_seed", "terminal_condition", "gradient_estimate", "control_value", "path_batch"],
        "router_use": "Deep-BSDE style path sampling for very high-dimensional control/HJB-like PDE routing",
        "receipt_rule": "record path seeds, terminal condition, gradient network version, and variance/error estimate",
    },
    {
        "axis": "tensor_train_factorization",
        "payload": ["tt_rank", "core_index", "factor_core", "boundary_slice", "reconstruction_error"],
        "router_use": "tensor-train/decomposition compression for high-dimensional fields with sparse information volume",
        "receipt_rule": "record TT ranks, core shapes, reconstruction error, and boundary slices retained",
    },
]


VERIFIED_PDE_PRIORS = [
    {
        "id": "POSEIDON",
        "role": "multiscale_operator_transformer_pde_foundation_model",
        "boundary": "paper/project-prior-only",
        "use_as": "operator_foundation_model_axis",
        "source": "Poseidon: Efficient Foundation Models for PDEs",
        "url": "https://arxiv.org/abs/2405.19101",
        "notes": "Multiscale operator transformer / scOT style PDE foundation model; generalization prior, not local PDE truth.",
    },
    {
        "id": "MORPH",
        "role": "shape_agnostic_pde_foundation_model",
        "boundary": "paper/model-card-prior-only",
        "use_as": "shape_agnostic_field_axis",
        "source": "MORPH: Shape-agnostic PDE Foundation Models",
        "url": "https://arxiv.org/abs/2509.21670",
        "notes": "Handles heterogeneous 1D/2D/3D spatiotemporal PDE datasets with scalar/vector fields.",
    },
    {
        "id": "PDE-Controller",
        "role": "llm_autoformalization_and_pde_control_workflow",
        "boundary": "project/paper-prior-only",
        "use_as": "formal_spec_and_controller_axis",
        "source": "PDE-Controller: LLMs for Autoformalization and Reasoning of PDEs",
        "url": "https://pde-controller.github.io/",
        "notes": "Routes informal PDE control problems into formal specifications, subgoals, and solver/code workflows.",
    },
    {
        "id": "CodePDE",
        "role": "llm_generated_pde_solver_code",
        "boundary": "paper-prior-only",
        "use_as": "solver_code_generation_axis",
        "source": "CodePDE: An Inference Framework for LLM-driven PDE Solver Generation",
        "url": "https://arxiv.org/abs/2505.08783",
        "notes": "Frames PDE solving as numerical solver code generation.",
    },
    {
        "id": "Unisolver",
        "role": "pde_conditional_transformer_universal_solver",
        "boundary": "paper-prior-only",
        "use_as": "pde_conditioned_sequence_solver_axis",
        "source": "Unisolver: PDE-Conditional Transformers Are Universal PDE Solvers",
        "url": "https://arxiv.org/abs/2405.17527",
        "notes": "Useful correction for the user-supplied Universal Physics Solver label: source names Unisolver.",
    },
    {
        "id": "Aurora",
        "role": "earth_system_weather_foundation_model",
        "boundary": "paper/project-prior-only",
        "use_as": "atmospheric_spatiotemporal_field_axis",
        "source": "Aurora: A Foundation Model of the Atmosphere / Earth System",
        "url": "https://arxiv.org/abs/2405.13063",
        "notes": "Weather/atmospheric foundation model; PDE-adjacent via learned atmospheric dynamics, not a general PDE solver receipt.",
    },
    {
        "id": "Prithvi-WxC",
        "role": "weather_climate_foundation_model",
        "boundary": "paper/model-card-prior-only",
        "use_as": "weather_climate_field_axis",
        "source": "Prithvi WxC: Foundation Model for Weather and Climate",
        "url": "https://arxiv.org/abs/2409.13598",
        "notes": "2.3B weather/climate model released via Hugging Face; useful for large-token spatiotemporal topology.",
    },
    {
        "id": "CoDA-NO",
        "role": "codomain_attention_neural_operator",
        "boundary": "paper-prior-only",
        "use_as": "multiphysics_channel_tokenization_axis",
        "source": "Pretraining Codomain Attention Neural Operators for Solving Multiphysics PDEs",
        "url": "https://arxiv.org/abs/2403.12553",
        "notes": "Tokenizes functions along codomain/channel space; strong n-space compression analogy.",
    },
]


SOFT_PDE_CANDIDATES = [
    {
        "id": "LLM4PDE",
        "status": "needs_exact_primary_source",
        "user_claim": "language-conditioned neural solver integrating language-style PDE encodings with operator-learning backbones",
        "use_as": "candidate_language_conditioned_operator_axis",
    },
    {
        "id": "ICON-LM",
        "status": "needs_exact_primary_source",
        "user_claim": "in-context operator learning with text and data prompts",
        "use_as": "candidate_in_context_operator_axis",
    },
]


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are an n-space PDE compression router. Return compact JSON with evidence boundaries."
    records = []
    for axis in receipt["pde_axes"]:
        prompt = {
            "task": "route_pde_axis",
            "axis": axis["axis"],
            "payload": axis["payload"],
            "instruction": "Use this PDE axis as a compression/routing coordinate.",
        }
        answer = {
            "selected": True,
            "use_as": axis["router_use"],
            "claim_boundary": "pde-coordinate-prior-only",
            "surface_payload_hint": axis["axis"][:16].upper(),
            "receipt_rule": axis["receipt_rule"],
        }
        records.append(chat_record(system, prompt, answer))
    for prior in receipt["verified_pde_priors"]:
        prompt = {
            "task": "use_pde_model_prior",
            "model": prior["id"],
            "role": prior["role"],
            "source": prior["source"],
            "instruction": "Explain how this PDE model should tune routing without becoming numerical proof.",
        }
        answer = {
            "selected": True,
            "use_as": prior["use_as"],
            "claim_boundary": prior["boundary"],
            "metaprobe_rule": "Use as architecture/corpus coordinate; require residual/source/solver receipts for any PDE claim.",
        }
        records.append(chat_record(system, prompt, answer))
    for candidate in receipt["soft_pde_candidates"]:
        prompt = {
            "task": "handle_unverified_pde_candidate",
            "candidate": candidate["id"],
            "user_claim": candidate["user_claim"],
            "instruction": "Route this candidate conservatively.",
        }
        answer = {
            "selected": False,
            "use_as": candidate["use_as"],
            "claim_boundary": "needs-primary-source-before-training-weight",
            "next_action": "Keep as soft candidate until exact paper/model card is pinned.",
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
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/pde_model_prior_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/pde_model_prior_curriculum.jsonl"))
    args = parser.parse_args()

    receipt = {
        "schema": "pde_model_prior_receipt_v1",
        "claim_boundary": "PDE model priors tune n-space routing and compression; they do not solve or validate local PDEs.",
        "pde_axes": PDE_AXES,
        "verified_pde_priors": VERIFIED_PDE_PRIORS,
        "soft_pde_candidates": SOFT_PDE_CANDIDATES,
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
