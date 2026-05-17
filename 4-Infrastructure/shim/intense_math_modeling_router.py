#!/usr/bin/env python3
"""Router for intense math-modeling scout passes.

This does not call ZAYA directly. It records when a ZAYA-like local reasoning
model should be looped in as a scout for decomposition/modeling, and which
receipts must judge the result afterward.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROUTES = [
    {
        "route": "cheap_deterministic",
        "condition": "known_axis and existing_receipt and low_branching",
        "model_role": "skip_llm",
        "use_for": "repeatable compression, bitpacking, logogram compilation, receipt regeneration",
        "judge": ["py_compile", "json_schema", "metaprobe"],
    },
    {
        "route": "zaya_scout",
        "condition": "high_branching or PDE/operator/modeling ambiguity or many candidate decompositions",
        "model_role": "Zyphra/ZAYA1-8B as local scout",
        "use_for": "candidate decomposition, route proposal, equation family selection, test-time compute branching",
        "judge": ["source_receipt", "Lean_or_solver_check", "metaprobe", "eigen_basis_delta"],
    },
    {
        "route": "formal_verifier",
        "condition": "theorem/proof/math-truth claim",
        "model_role": "model may propose proof text only",
        "use_for": "Lean sketch or theorem-search query proposal",
        "judge": ["lake_build", "native_decide", "source_theorem_receipt"],
    },
    {
        "route": "hardware_witness",
        "condition": "fixed_width_payload or Tang/PBACS/logogram surface",
        "model_role": "model may choose payload/regime only",
        "use_for": "surface payload selection, LED reservoir address, substitution witness",
        "judge": ["Tang_direct_witness", "substitution_receipt", "metaprobe"],
    },
]


EXAMPLE_TASKS = [
    {
        "task": "PDE n-space model choice",
        "features": ["PDE/operator/modeling ambiguity", "many candidate decompositions"],
        "selected_route": "zaya_scout",
        "reason": "Ask the scout to propose PINN/FNO/BSDE/tensor-train decomposition; receipts decide.",
    },
    {
        "task": "Erdos claimed counterexample",
        "features": ["math-truth claim", "source/verifier needed"],
        "selected_route": "formal_verifier",
        "reason": "LLM can propose checks, but graph/cycle verifier and Lean/source receipts judge.",
    },
    {
        "task": "LaTeX/logogram surface compile",
        "features": ["known_axis", "fixed_width_payload"],
        "selected_route": "hardware_witness",
        "reason": "No need for heavy reasoning unless the regime classifier is ambiguous.",
    },
    {
        "task": "Moving sofa / couch problem",
        "features": ["continuous geometry", "high branching", "configuration space", "obstruction certificates"],
        "selected_route": "zaya_scout",
        "reason": "Use ZAYA to propose contact-envelope decompositions, variational routes, and obstruction searches; proof status is judged by source/formal/certificate receipts.",
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
    system = "You are an intense math modeling router. Decide when to use a scout model and name the judging receipts."
    records: list[dict[str, Any]] = []
    for route in receipt["routes"]:
        records.append(
            chat_record(
                system,
                {
                    "task": "select_math_modeling_route",
                    "route": route["route"],
                    "condition": route["condition"],
                    "instruction": "Explain this route's use and the receipts that judge it.",
                },
                {
                    "selected": True,
                    "route": route["route"],
                    "model_role": route["model_role"],
                    "use_for": route["use_for"],
                    "judge": route["judge"],
                    "claim_boundary": "routing-policy-only",
                },
            )
        )
    for example in receipt["examples"]:
        records.append(
            chat_record(
                system,
                {
                    "task": "route_example_task",
                    "example": example["task"],
                    "features": example["features"],
                },
                {
                    "selected": True,
                    "route": example["selected_route"],
                    "reason": example["reason"],
                    "claim_boundary": "example-routing-prior-only",
                },
            )
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/intense_math_modeling_router_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/intense_math_modeling_router_curriculum.jsonl"))
    args = parser.parse_args()

    receipt = {
        "schema": "intense_math_modeling_router_v1",
        "claim_boundary": "ZAYA-style models are scouts for decomposition and branch selection, not judges of truth.",
        "preferred_scout_model": "Zyphra/ZAYA1-8B",
        "routes": ROUTES,
        "examples": EXAMPLE_TASKS,
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
