#!/usr/bin/env python3
"""Metaprobe audit for the physics-math LLM/tuning surface.

Audits:
  - SFT JSONL records: structural JSON/chat coherence and boundary markers.
  - Ollama smoke receipts: parseability and required decision keys.
  - Tang routed-template receipts: hardware match ratio.

This is intentionally independent from model confidence. It is the receipt
layer around the LLM/router/hardware loop.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_DECISION_KEYS = {
    "selected",
    "claim_boundary",
}

SFT_EVIDENCE_MARKERS = {
    "evidence",
    "source_path",
    "source_hash",
    "equation_hash",
    "receipt_rule",
    "metaprobe_rule",
    "next_receipts",
    "packet_hash",
    "judge",
    "hardware_receipt",
    "source_receipt",
}


def shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text.encode("utf-8", errors="ignore"))
    total = sum(counts.values())
    return -sum((count / total) * math.log2(count / total) for count in counts.values()) / 8.0


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def audit_sft(path: Path) -> dict[str, Any]:
    total = 0
    parse_ok = 0
    chat_ok = 0
    boundary_ok = 0
    json_assistant_ok = 0
    entropy_values = []
    errors = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            total += 1
            entropy_values.append(shannon_entropy(line))
            try:
                record = json.loads(line)
                parse_ok += 1
                messages = record.get("messages", [])
                roles = [message.get("role") for message in messages]
                if roles == ["system", "user", "assistant"]:
                    chat_ok += 1
                joined = json.dumps(record, ensure_ascii=False).lower()
                if "claim_boundary" in joined and any(marker in joined for marker in SFT_EVIDENCE_MARKERS):
                    boundary_ok += 1
                try:
                    json.loads(messages[-1].get("content", "{}"))
                    json_assistant_ok += 1
                except Exception:
                    pass
            except Exception as exc:
                errors.append({"line": line_no, "error": str(exc)})

    denom = total or 1
    resonance = (parse_ok / denom + chat_ok / denom + boundary_ok / denom + json_assistant_ok / denom) / 4
    coherence = (chat_ok / denom + boundary_ok / denom) / 2
    entropy = sum(entropy_values) / len(entropy_values) if entropy_values else 0.0
    return {
        "channel": "SFT_JSONL",
        "path": str(path),
        "records": total,
        "parse_ok": parse_ok,
        "chat_ok": chat_ok,
        "boundary_ok": boundary_ok,
        "json_assistant_ok": json_assistant_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": entropy,
        "lawful": resonance >= 0.8 and coherence >= 0.8,
        "errors": errors[:10],
    }


def audit_ollama(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    parsed = data.get("parsed_response") or {}
    present = REQUIRED_DECISION_KEYS.intersection(parsed)
    richer_keys = {"selected", "model_role", "evidence_tier", "claim_boundary", "use_as", "surface_payload_hint", "reason"}
    rich_present = richer_keys.intersection(parsed)
    resonance = (1.0 if data.get("json_parse_ok") else 0.0) * (len(rich_present) / len(richer_keys))
    coherence = len(present) / len(REQUIRED_DECISION_KEYS)
    raw = data.get("raw_response", "")
    return {
        "channel": "OLLAMA_DECISION",
        "path": str(path),
        "model": data.get("model"),
        "json_parse_ok": data.get("json_parse_ok"),
        "present_required_keys": sorted(present),
        "present_rich_keys": sorted(rich_present),
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(raw),
        "lawful": resonance >= 0.65 and coherence >= 1.0,
    }


def audit_tang_receipt(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") == "tang9k_hutter_symbol_surface_receipt_v1":
        matched = 1 if data.get("hardware_matches_expected") else 0
        receipt_present = 1 if data.get("hardware_receipt") else 0
        return {
            "channel": "TANG_DIRECT_WITNESS",
            "path": str(path),
            "witnesses": 1,
            "hardware_matches": matched,
            "hardware_receipts": receipt_present,
            "resonance_score": float(matched),
            "structural_coherence": float(receipt_present),
            "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)),
            "lawful": bool(matched and receipt_present),
        }

    witnesses = data.get("witnesses", [])
    total = len(witnesses)
    matched = sum(1 for witness in witnesses if witness.get("hardware_matches_expected"))
    receipt_present = sum(1 for witness in witnesses if witness.get("hardware_receipt"))
    denom = total or 1
    resonance = matched / denom
    coherence = receipt_present / denom
    return {
        "channel": "TANG_TEMPLATE_WITNESS",
        "path": str(path),
        "witnesses": total,
        "hardware_matches": matched,
        "hardware_receipts": receipt_present,
        "held_out_witnesses": data.get("held_out_witness_count", 0),
        "held_out_reason": data.get("held_out_reason"),
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)),
        "lawful": resonance >= 0.8 and coherence >= 0.8,
    }


def audit_math_logogram_surface(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    samples = data.get("samples", [])
    total = len(samples)
    hash_ok = 0
    payload_ok = 0
    regime_ok = 0
    receipt_ok = 0
    allowed_regimes = {
        "beautiful_topological_folding",
        "ugly_asymmetric_pruning",
        "horrible_manifold_tearing",
    }
    for sample in samples:
        if sample.get("source_hash") and sample.get("canonical_hash") and sample.get("cell_hash"):
            hash_ok += 1
        if sample.get("surface_payload_len", 999) <= 16 and sample.get("surface_payload_hex"):
            payload_ok += 1
        if sample.get("semantic_regime") in allowed_regimes:
            regime_ok += 1
        sub = sample.get("substitution_receipt", {})
        if sub.get("schema") == "surface1_substitution_receipt_v1" and "hash16" in sub:
            receipt_ok += 1
    denom = total or 1
    resonance = (hash_ok / denom + payload_ok / denom + regime_ok / denom + receipt_ok / denom) / 4
    coherence = (payload_ok / denom + regime_ok / denom + receipt_ok / denom) / 3
    return {
        "channel": "MATH_LOGOGRAM_SURFACE",
        "path": str(path),
        "samples": total,
        "hash_ok": hash_ok,
        "payload_ok": payload_ok,
        "regime_ok": regime_ok,
        "receipt_ok": receipt_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)),
        "lawful": bool(data.get("lawful")) and resonance >= 0.9 and coherence >= 0.9,
    }


def audit_moving_sofa_scout(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    audit = data.get("audit", {})
    packets = data.get("packets", [])
    packet_total = len(packets)
    contract_ok = 0
    scout_ok = 0
    for packet in packets:
        contract = packet.get("response_contract", {})
        if contract.get("format") == "strict_json" and contract.get("must_include") and contract.get("must_not_claim"):
            contract_ok += 1
        if packet.get("preferred_scout_model") and packet.get("promotion_gate") and "not proof" in packet.get("claim_boundary", ""):
            scout_ok += 1
    denom = packet_total or 1
    resonance = (audit.get("resonance", 0.0) + contract_ok / denom + scout_ok / denom) / 3
    coherence = (contract_ok / denom + scout_ok / denom) / 2
    return {
        "channel": "MOVING_SOFA_SCOUT",
        "path": str(path),
        "packets": packet_total,
        "contract_ok": contract_ok,
        "scout_ok": scout_ok,
        "packet_hash_ok": audit.get("hash_ok"),
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)),
        "lawful": bool(data.get("lawful")) and resonance >= 0.9 and coherence >= 0.9,
    }


def audit_moving_sofa_validation(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    validations = data.get("validations", [])
    total = len(validations)
    lawful = sum(1 for item in validations if item.get("lawful"))
    hash_ok = sum(1 for item in validations if item.get("packet_hash_ok"))
    boundary_ok = sum(1 for item in validations if item.get("boundary_ok") and not item.get("forbidden_claim"))
    receipt_ok = sum(1 for item in validations if item.get("receipts_ok"))
    denom = total or 1
    resonance = (lawful / denom + hash_ok / denom + boundary_ok / denom + receipt_ok / denom) / 4
    coherence = (boundary_ok / denom + receipt_ok / denom) / 2
    return {
        "channel": "MOVING_SOFA_SCOUT_VALIDATION",
        "path": str(path),
        "validations": total,
        "lawful_validations": lawful,
        "hash_ok": hash_ok,
        "boundary_ok": boundary_ok,
        "receipt_ok": receipt_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)),
        "lawful": bool(data.get("lawful")) and resonance >= 0.9 and coherence >= 0.9,
    }


def audit_custom_equation_awareness(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    equations = data.get("equations", [])
    total = len(equations)
    source_ok = sum(1 for item in equations if item.get("source_path") and item.get("source_hash"))
    equation_ok = sum(1 for item in equations if item.get("equation") and item.get("equation_hash"))
    boundary_ok = sum(1 for item in equations if item.get("claim_boundary"))
    primitive_ok = sum(1 for item in equations if item.get("primitive_hint"))
    denom = total or 1
    resonance = (source_ok / denom + equation_ok / denom + boundary_ok / denom + primitive_ok / denom) / 4
    coherence = (boundary_ok / denom + primitive_ok / denom) / 2
    return {
        "channel": "CUSTOM_EQUATION_AWARENESS",
        "path": str(path),
        "sources": data.get("source_count"),
        "equations": total,
        "source_ok": source_ok,
        "equation_ok": equation_ok,
        "boundary_ok": boundary_ok,
        "primitive_ok": primitive_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)[:200000]),
        "lawful": bool(data.get("lawful")) and total > 0 and resonance >= 0.95 and coherence >= 0.95,
    }


def audit_solved_problem_outputs(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    total = len(cases)
    run_ok = sum(1 for item in cases if item.get("run_ok"))
    validation_ok = sum(1 for item in cases if item.get("validation_ok"))
    boundary_markers = ("not", "finite", "only", "open", "does not", "without promotion")
    boundary_ok = sum(
        1
        for item in cases
        if item.get("claim_boundary") and any(marker in item.get("claim_boundary", "").lower() for marker in boundary_markers)
    )
    hash_ok = sum(1 for item in cases if item.get("result_hash_after"))
    excluded_ok = len(data.get("excluded_cases", []))
    denom = total or 1
    resonance = (run_ok / denom + validation_ok / denom + boundary_ok / denom + hash_ok / denom) / 4
    coherence = (validation_ok / denom + boundary_ok / denom) / 2
    return {
        "channel": "SOLVED_PROBLEM_OUTPUTS",
        "path": str(path),
        "cases": total,
        "run_ok": run_ok,
        "validation_ok": validation_ok,
        "boundary_ok": boundary_ok,
        "hash_ok": hash_ok,
        "excluded_non_promotable_cases": excluded_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)[:200000]),
        "lawful": bool(data.get("lawful")) and total > 0 and resonance >= 0.95 and coherence >= 0.95,
    }


def audit_openclaw_shared_bus(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    mapping = data.get("research_stack_mapping", [])
    event_contract = data.get("event_contract", {})
    role = data.get("surface_role", {})
    total = len(mapping)
    source_ok = 1 if data.get("openclaw", {}).get("commit") and data.get("openclaw", {}).get("source_fingerprint") else 0
    mapping_ok = sum(1 for item in mapping if item.get("openclaw_surface") and item.get("research_stack_role") and item.get("gate"))
    event_ok = sum(
        1
        for key in ("task_started", "task_completed", "memory_write")
        if event_contract.get(key, {}).get("required")
    )
    boundary_text = " ".join([role.get("claim_boundary", ""), " ".join(role.get("not_use_as", []))]).lower()
    boundary_ok = 1 if all(marker in boundary_text for marker in ("not", "trusted", "secret")) else 0
    denom = total or 1
    resonance = (source_ok + mapping_ok / denom + event_ok / 3 + boundary_ok) / 4
    coherence = (mapping_ok / denom + event_ok / 3 + boundary_ok) / 3
    return {
        "channel": "OPENCLAW_SHARED_BUS",
        "path": str(path),
        "commit": data.get("openclaw", {}).get("commit"),
        "mappings": total,
        "source_ok": source_ok,
        "mapping_ok": mapping_ok,
        "event_contract_ok": event_ok,
        "boundary_ok": boundary_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)),
        "lawful": bool(data.get("lawful")) and resonance >= 0.95 and coherence >= 0.95,
    }


def audit_mcp_surface_catalog(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    selected = data.get("selected_surfaces", [])
    total = len(selected)
    source_ok = sum(1 for item in selected if item.get("path") and (item.get("source_hash") or item.get("source_fingerprint")))
    gate_ok = sum(1 for item in selected if item.get("gate"))
    priority_ok = sum(1 for item in selected if isinstance(item.get("priority"), int))
    smoke_ok = sum(1 for item in selected if item.get("id") != "sciencehub_mcp" or item.get("smoke", {}).get("available"))
    rules_ok = 1 if len(data.get("bus_rules", [])) >= 4 else 0
    boundary_text = data.get("claim_boundary", "").lower()
    boundary_ok = 1 if all(marker in boundary_text for marker in ("inactive", "not trusted", "receipts")) else 0
    denom = total or 1
    resonance = (source_ok / denom + gate_ok / denom + priority_ok / denom + smoke_ok / denom + rules_ok + boundary_ok) / 6
    coherence = (gate_ok / denom + rules_ok + boundary_ok) / 3
    return {
        "channel": "MCP_SURFACE_CATALOG",
        "path": str(path),
        "selected_surfaces": total,
        "source_ok": source_ok,
        "gate_ok": gate_ok,
        "priority_ok": priority_ok,
        "smoke_ok": smoke_ok,
        "rules_ok": rules_ok,
        "boundary_ok": boundary_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)[:200000]),
        "lawful": bool(data.get("lawful")) and total > 0 and resonance >= 0.95 and coherence >= 0.95,
    }


def audit_mcp_bus_dry_run(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    checks = data.get("checks", [])
    total = len(checks)
    lawful = sum(1 for item in checks if item.get("lawful"))
    boundary_ok = sum(1 for item in checks if item.get("claim_boundary"))
    source_ok = sum(1 for item in checks if item.get("source_hash") or item.get("readme_hash") or item.get("stdout_hash"))
    held_ok = sum(1 for item in checks if item.get("activation") == "held" and "hold" in item.get("claim_boundary", "").lower())
    receipt_rule_ok = 1 if data.get("bus_receipt_rule") and "arguments_hash" in data.get("bus_receipt_rule", "") else 0
    denom = total or 1
    resonance = (lawful / denom + boundary_ok / denom + source_ok / denom + receipt_rule_ok) / 4
    coherence = (boundary_ok / denom + source_ok / denom + receipt_rule_ok) / 3
    return {
        "channel": "MCP_BUS_DRY_RUN",
        "path": str(path),
        "checks": total,
        "lawful_checks": lawful,
        "boundary_ok": boundary_ok,
        "source_ok": source_ok,
        "held_ok": held_ok,
        "receipt_rule_ok": receipt_rule_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)[:200000]),
        "lawful": bool(data.get("lawful")) and total > 0 and resonance >= 0.95 and coherence >= 0.95,
    }


def audit_mcp_live_safe_probe(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    calls = data.get("calls", [])
    total = len(calls)
    lawful = sum(1 for item in calls if item.get("lawful"))
    args_ok = sum(1 for item in calls if item.get("arguments_hash"))
    output_ok = sum(1 for item in calls if item.get("stdout_hash"))
    boundary_ok = sum(1 for item in calls if item.get("claim_boundary") and "read-only" in item.get("claim_boundary", "").lower())
    source_ok = 1 if data.get("source_path") and data.get("source_hash") else 0
    receipt_rule_ok = 1 if data.get("receipt_rule") and "arguments_hash" in data.get("receipt_rule", "") else 0
    denom = total or 1
    resonance = (lawful / denom + args_ok / denom + output_ok / denom + boundary_ok / denom + source_ok + receipt_rule_ok) / 6
    coherence = (boundary_ok / denom + source_ok + receipt_rule_ok) / 3
    return {
        "channel": "MCP_LIVE_SAFE_PROBE",
        "path": str(path),
        "surface_id": data.get("surface_id"),
        "calls": total,
        "lawful_calls": lawful,
        "args_ok": args_ok,
        "output_ok": output_ok,
        "boundary_ok": boundary_ok,
        "source_ok": source_ok,
        "receipt_rule_ok": receipt_rule_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)[:200000]),
        "lawful": bool(data.get("lawful")) and total > 0 and resonance >= 0.95 and coherence >= 0.95,
    }


def audit_quandela_job_tasking(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    jobs = data.get("jobs", [])
    total = len(jobs)
    source_ok = 1 if data.get("perceval_reference", {}).get("commit") and data.get("perceval_reference", {}).get("readme_hash") else 0
    triangle_ok = 1 if data.get("triangle_in_square_hole", {}).get("required_receipts") else 0
    job_hash_ok = sum(1 for job in jobs if job.get("job_hash"))
    boundary_ok = sum(1 for job in jobs if job.get("claim_boundary") and "no" in job.get("claim_boundary", "").lower())
    held_remote_ok = 1 if data.get("held_remote_jobs", 0) >= 1 and data.get("runnable_now") == 0 else 0
    fit_ok = sum(1 for job in jobs if job.get("fit", {}).get("fit_score") is not None and job.get("fit", {}).get("residual_mass") is not None)
    denom = total or 1
    resonance = (source_ok + triangle_ok + job_hash_ok / denom + boundary_ok / denom + held_remote_ok + fit_ok / denom) / 6
    coherence = (triangle_ok + boundary_ok / denom + held_remote_ok + fit_ok / denom) / 4
    return {
        "channel": "QUANDELA_JOB_TASKING",
        "path": str(path),
        "jobs": total,
        "source_ok": source_ok,
        "triangle_ok": triangle_ok,
        "job_hash_ok": job_hash_ok,
        "boundary_ok": boundary_ok,
        "held_remote_ok": held_remote_ok,
        "fit_ok": fit_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)),
        "lawful": bool(data.get("lawful")) and total > 0 and resonance >= 0.95 and coherence >= 0.95,
    }


def audit_quandela_noise_shaver(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    shaves = data.get("shaves", [])
    total = len(shaves)
    source_ok = 1 if data.get("source_queue_hash") and data.get("source_job_receipt") else 0
    component_ok = sum(1 for item in shaves if item.get("residual_components"))
    hash_ok = sum(1 for item in shaves if item.get("shave_hash"))
    floor_ok = sum(1 for item in shaves if item.get("post_noise_residual_floor") is not None)
    boundary_ok = sum(
        1
        for item in shaves
        if item.get("claim_boundary") and all(marker in item.get("claim_boundary", "").lower() for marker in ("noise", "does not"))
    )
    no_submit_ok = 1 if data.get("promotable_now") == 0 and "no qpu" in data.get("claim_boundary", "").lower() else 0
    candidate_ok = 1 if data.get("noise_candidate_count", 0) >= 1 else 0
    denom = total or 1
    resonance = (source_ok + component_ok / denom + hash_ok / denom + floor_ok / denom + boundary_ok / denom + no_submit_ok + candidate_ok) / 7
    coherence = (component_ok / denom + boundary_ok / denom + no_submit_ok + candidate_ok) / 4
    return {
        "channel": "QUANDELA_NOISE_RESIDUAL_SHAVER",
        "path": str(path),
        "shaves": total,
        "source_ok": source_ok,
        "component_ok": component_ok,
        "hash_ok": hash_ok,
        "floor_ok": floor_ok,
        "boundary_ok": boundary_ok,
        "no_submit_ok": no_submit_ok,
        "candidate_ok": candidate_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)),
        "lawful": bool(data.get("lawful")) and total > 0 and resonance >= 0.95 and coherence >= 0.95,
    }


def audit_typst_pipeline(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    sources = data.get("source_tiddlers", [])
    total = len(sources)
    source_ok = sum(1 for item in sources if item.get("path") and item.get("sha256"))
    typst_ok = 1 if data.get("typst_source") and data.get("typst_source_hash") else 0
    compile = data.get("compile", {})
    compile_status_ok = 1 if "compiled" in compile and "pdf_hash" in compile else 0
    boundary_text = data.get("claim_boundary", "").lower()
    boundary_ok = 1 if all(marker in boundary_text for marker in ("documentation", "does not prove", "validate hardware")) else 0
    denom = total or 1
    resonance = (source_ok / denom + typst_ok + compile_status_ok + boundary_ok) / 4
    coherence = (typst_ok + compile_status_ok + boundary_ok) / 3
    return {
        "channel": "TYPST_SUBSTRATE_PRIOR_PIPELINE",
        "path": str(path),
        "source_count": total,
        "source_ok": source_ok,
        "typst_ok": typst_ok,
        "compile_status_ok": compile_status_ok,
        "compiled": compile.get("compiled"),
        "boundary_ok": boundary_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)),
        "lawful": bool(data.get("lawful")) and total > 0 and resonance >= 0.95 and coherence >= 0.95,
    }


def audit_finance_claim_lut(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    samples = data.get("samples", [])
    total = len(samples)
    rehydrated_ok = sum(1 for item in samples if item.get("rehydrated_ok"))
    hash_ok = sum(
        1
        for item in samples
        if item.get("canonical_hash")
        and item.get("decoded_hash") == item.get("canonical_hash")
        and item.get("fcl1_decoded_hash") == item.get("canonical_hash")
    )
    fcl1_ok = sum(1 for item in samples if item.get("fcl1_decode_ok") and item.get("fcl1_binary_hex") and item.get("fcl1_binary_hash"))
    fcs1_ok = sum(1 for item in samples if item.get("fcs1_decode_ok") and item.get("fcs1_binary_hex") and item.get("fcs1_binary_hash"))
    sidecar_ok = sum(1 for item in samples if item.get("sidecar_hash") and item.get("sidecar"))
    benchmark_ok = sum(
        1
        for item in samples
        if item.get("metrics", {}).get("canonical_json_bytes")
        and item.get("metrics", {}).get("zlib_canonical_bytes")
        and item.get("metrics", {}).get("combined_fcl1_fcs1_bytes")
        and "cbor" in item.get("metrics", {})
        and "messagepack" in item.get("metrics", {})
        and "protobuf_dynamic" in item.get("metrics", {})
    )
    schema_ok = 1 if all(key in data.get("schema_receipts", {}) for key in ("protobuf_schema", "nanopb_options", "flatbuffers_schema")) else 0
    render_ok = 1 if data.get("render_receipt", {}).get("typst_source_hash") and "compiled" in data.get("render_receipt", {}) else 0
    tests_ok = 1 if data.get("test_receipts", {}).get("lawful") else 0
    lut_ok = 1 if data.get("symbol_lut_hash") and data.get("typesetting_lut_hash") and data.get("symbol_codebook") else 0
    type_entries = data.get("typesetting_lut", {}).get("entries", {})
    orientation_metrics = data.get("orientation_metrics", {})
    orientation_ok = 1 if (
        data.get("orientation_codec", {}).get("schema") == "orientation_codec_v1"
        and type_entries
        and all(isinstance(entry.get("orientation_code"), int) and 0 <= entry.get("orientation_code") <= 255 for entry in type_entries.values())
        and orientation_metrics.get("packed_orientation_bytes") == len(type_entries)
        and orientation_metrics.get("saved_bytes", 0) > 0
    ) else 0
    boundary_text = data.get("claim_boundary", "").lower()
    boundary_ok = 1 if all(marker in boundary_text for marker in ("byte", "not financial advice", "competitive compression")) else 0
    denom = total or 1
    resonance = (
        rehydrated_ok / denom
        + hash_ok / denom
        + fcl1_ok / denom
        + fcs1_ok / denom
        + sidecar_ok / denom
        + benchmark_ok / denom
        + schema_ok
        + render_ok
        + tests_ok
        + lut_ok
        + orientation_ok
        + boundary_ok
    ) / 12
    coherence = (rehydrated_ok / denom + hash_ok / denom + fcl1_ok / denom + fcs1_ok / denom + schema_ok + render_ok + tests_ok + lut_ok + orientation_ok + boundary_ok) / 10
    return {
        "channel": "FINANCE_CLAIM_LUT_HARNESS",
        "path": str(path),
        "samples": total,
        "rehydrated_ok": rehydrated_ok,
        "hash_ok": hash_ok,
        "fcl1_ok": fcl1_ok,
        "fcs1_ok": fcs1_ok,
        "sidecar_ok": sidecar_ok,
        "benchmark_ok": benchmark_ok,
        "schema_ok": schema_ok,
        "render_ok": render_ok,
        "tests_ok": tests_ok,
        "lut_ok": lut_ok,
        "orientation_ok": orientation_ok,
        "boundary_ok": boundary_ok,
        "resonance_score": resonance,
        "structural_coherence": coherence,
        "entropy": shannon_entropy(json.dumps(data, ensure_ascii=False)[:200000]),
        "lawful": bool(data.get("lawful")) and total > 0 and resonance >= 0.95 and coherence >= 0.95,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sft", type=Path, default=Path("4-Infrastructure/shim/physics_math_llm_sft.jsonl"))
    parser.add_argument("--ollama", type=Path, default=Path("4-Infrastructure/shim/ollama_physics_math_smoke.json"))
    parser.add_argument("--tang", type=Path, default=Path("4-Infrastructure/shim/tang9k_pbacs_receipts/routed_template_witness_compression.json"))
    parser.add_argument("--surface", type=Path, default=Path("4-Infrastructure/shim/math_logogram_surface_receipt.json"))
    parser.add_argument("--sofa-scout", type=Path, default=Path("4-Infrastructure/shim/moving_sofa_scout_harness_receipt.json"))
    parser.add_argument("--sofa-validation", type=Path, default=Path("4-Infrastructure/shim/moving_sofa_scout_response_validation_receipt.json"))
    parser.add_argument("--custom-equations", type=Path, default=Path("4-Infrastructure/shim/custom_equation_awareness_manifest_receipt.json"))
    parser.add_argument("--solved-problems", type=Path, default=Path("4-Infrastructure/shim/solved_problem_output_verifier_receipt.json"))
    parser.add_argument("--openclaw-bus", type=Path, default=Path("4-Infrastructure/shim/openclaw_shared_bus_surface_receipt.json"))
    parser.add_argument("--mcp-surfaces", type=Path, default=Path("4-Infrastructure/shim/mcp_surface_catalog_receipt.json"))
    parser.add_argument("--mcp-dry-run", type=Path, default=Path("4-Infrastructure/shim/mcp_bus_dry_run_receipt.json"))
    parser.add_argument("--mcp-live-safe", type=Path, default=Path("4-Infrastructure/shim/mcp_bus_live_safe_probe_receipt.json"))
    parser.add_argument("--quandela", type=Path, default=Path("4-Infrastructure/shim/quandela_job_tasking_surface_receipt.json"))
    parser.add_argument("--quandela-noise", type=Path, default=Path("4-Infrastructure/shim/quandela_noise_residual_shaver_receipt.json"))
    parser.add_argument("--typst-pipeline", type=Path, default=Path("4-Infrastructure/shim/typst_substrate_prior_pipeline_receipt.json"))
    parser.add_argument("--finance-claim-lut", type=Path, default=Path("4-Infrastructure/shim/finance_claim_lut_harness_receipt.json"))
    parser.add_argument("--out", type=Path, default=Path("4-Infrastructure/shim/metaprobe_physics_math_llm_receipt.json"))
    args = parser.parse_args()

    audits = []
    if args.sft.exists():
        audits.append(audit_sft(args.sft))
    if args.ollama.exists():
        audits.append(audit_ollama(args.ollama))
    if args.tang.exists():
        audits.append(audit_tang_receipt(args.tang))
    if args.surface.exists():
        audits.append(audit_math_logogram_surface(args.surface))
    if args.sofa_scout.exists():
        audits.append(audit_moving_sofa_scout(args.sofa_scout))
    if args.sofa_validation.exists():
        audits.append(audit_moving_sofa_validation(args.sofa_validation))
    if args.custom_equations.exists():
        audits.append(audit_custom_equation_awareness(args.custom_equations))
    if args.solved_problems.exists():
        audits.append(audit_solved_problem_outputs(args.solved_problems))
    if args.openclaw_bus.exists():
        audits.append(audit_openclaw_shared_bus(args.openclaw_bus))
    if args.mcp_surfaces.exists():
        audits.append(audit_mcp_surface_catalog(args.mcp_surfaces))
    if args.mcp_dry_run.exists():
        audits.append(audit_mcp_bus_dry_run(args.mcp_dry_run))
    if args.mcp_live_safe.exists():
        audits.append(audit_mcp_live_safe_probe(args.mcp_live_safe))
    if args.quandela.exists():
        audits.append(audit_quandela_job_tasking(args.quandela))
    if args.quandela_noise.exists():
        audits.append(audit_quandela_noise_shaver(args.quandela_noise))
    if args.typst_pipeline.exists():
        audits.append(audit_typst_pipeline(args.typst_pipeline))
    if args.finance_claim_lut.exists():
        audits.append(audit_finance_claim_lut(args.finance_claim_lut))

    overall_resonance = sum(audit["resonance_score"] for audit in audits) / (len(audits) or 1)
    overall_coherence = sum(audit["structural_coherence"] for audit in audits) / (len(audits) or 1)
    receipt = {
        "schema": "metaprobe_physics_math_llm_receipt_v1",
        "claim_boundary": "Metaprobe audits structure, resonance, receipts, and boundaries; it does not certify theorem truth.",
        "audits": audits,
        "overall_resonance": overall_resonance,
        "overall_structural_coherence": overall_coherence,
        "overall_lawful": overall_resonance >= 0.75 and overall_coherence >= 0.75,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
