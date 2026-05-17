#!/usr/bin/env python3
"""Smoke test the local Gemma physics/math router model via Ollama."""

from __future__ import annotations

import argparse
import json
import urllib.request


def generate(model: str, prompt: str, host: str, timeout: int) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_ctx": 4096, "num_predict": 512},
    }
    req = urllib.request.Request(
        f"{host}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    return data.get("response", "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gemma-physics-math")
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    prompt = json.dumps(
        {
            "task": "rank_candidate_template",
            "candidate": {
                "model_name": "PBACS_1bit_Transport",
                "equation": "b_t = 1[v_t + e_{t-1} > theta_t]; e_t = v_t + e_{t-1} - b_t",
                "evidence_tier": "spec_admissible",
                "domain_type": "LAYER_K_SIGNAL",
                "bind_class": "control_bind",
            },
            "instruction": (
                "Return compact JSON with keys selected, model_role, evidence_tier, "
                "claim_boundary, use_as, surface_payload_hint, reason. Do not claim "
                "proof; decide whether it is useful as a local routing prior."
            ),
        },
        ensure_ascii=False,
    )
    raw = generate(args.model, prompt, args.host, args.timeout)
    receipt = {
        "schema": "ollama_physics_math_smoke_v1",
        "model": args.model,
        "raw_response": raw,
    }
    try:
        receipt["parsed_response"] = json.loads(raw)
        receipt["json_parse_ok"] = True
    except Exception as exc:
        receipt["parsed_response"] = None
        receipt["json_parse_ok"] = False
        receipt["parse_error"] = str(exc)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
