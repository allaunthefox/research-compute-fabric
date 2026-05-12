#!/usr/bin/env python3
"""Receipt for Nash 2026 Sigilith symbolic-resilience prior.

This is an analysis/citation prior only. The source record carries a non-commercial
research/no-derivative implementation boundary, so this artifact extracts high-level
equation shapes and claim boundaries without implementing the Sigilith framework.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
SOURCE_DIR = REPO / "shared-data" / "sources" / "hcommons" / "gjgw2-j1f46"
SOURCE_PDF = SOURCE_DIR / "Nash2026Sigilith_SymbolicResilience.pdf"
SOURCE_TEXT = SOURCE_DIR / "Nash2026Sigilith_SymbolicResilience.txt"
RECORD_JSON = SOURCE_DIR / "record_api.json"
RECEIPT = SHIM / "sigilith_symbolic_resilience_prior_receipt.json"
CURRICULUM = SHIM / "sigilith_symbolic_resilience_prior_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    record = json.loads(RECORD_JSON.read_text(encoding="utf-8"))
    pdf_sha256 = sha256_bytes(SOURCE_PDF)
    text_sha256 = sha256_bytes(SOURCE_TEXT)
    pdf_md5 = hashlib.md5(SOURCE_PDF.read_bytes(), usedforsecurity=False).hexdigest()
    metadata = record.get("metadata", {})
    receipt: dict[str, Any] = {
        "schema": "sigilith_symbolic_resilience_prior_v1",
        "source": {
            "record_id": record.get("id"),
            "title": metadata.get("title"),
            "creator": "Nash, Ky",
            "publication_date": metadata.get("publication_date"),
            "doi": record.get("pids", {}).get("doi", {}).get("identifier"),
            "record_url": record.get("links", {}).get("self_html"),
            "api_url": record.get("links", {}).get("self"),
            "pdf_filename": SOURCE_PDF.name,
            "pdf_md5": pdf_md5,
            "pdf_sha256": pdf_sha256,
            "text_sha256": text_sha256,
        },
        "license_boundary": [
            "use as citation and high-level analysis prior only",
            "do not implement Sigilith/CDMQ methods from this source without permission",
            "do not create derivative framework artifacts from protected method details",
            "preserve author claim boundary: no biological, cognitive, or autonomous interpretation implied",
        ],
        "primary_read": (
            "The paper offers a synthetic symbolic-system analogue for resilience under "
            "drift: constraint density, modifier regeneration, and paradox buffering "
            "can delay collapse. This maps cleanly to the stack's overload model as a "
            "symbolic collapse-topology prior, not as evidence of biological autonomy."
        ),
        "source_claim_boundary": (
            "Survival-like behavior is defined as delayed terminal collapse through "
            "internal stabilization dynamics without biological, cognitive, or autonomous claims."
        ),
        "system_comparison": {
            "R1": {
                "description": "baseline CDMQ system with no resilience mechanisms",
                "observed_pattern": "rapid drift escalation and single-stage collapse",
                "T_collapse": 100,
            },
            "R2": {
                "description": "enhanced system with increased constraint density, modifier regeneration, and paradox buffering",
                "observed_pattern": "drift suppression, plateau formation, modifier regeneration, paradox buffering, delayed collapse",
                "T_collapse": 140,
            },
            "CDC": 40,
        },
        "equation_shapes": [
            {
                "id": "drift_magnitude",
                "shape": "D_t = Q_t / (C_t + M_t)",
                "semantics": "paradox/quality activation over stabilizing constraint and modifier mass",
                "folded_use": "symbolic analogue of overload pressure",
            },
            {
                "id": "collapse_delay_coefficient",
                "shape": "CDC = T_collapse(R2) - T_collapse(R1)",
                "semantics": "delay gained by resilience mechanisms",
                "folded_use": "collapse-resistance delta for route/system variants",
            },
            {
                "id": "constraint_density",
                "shape": "C_rho = C / N",
                "semantics": "constraint density per symbolic sequence length",
                "folded_use": "stabilization mass per route/window",
            },
            {
                "id": "modifier_recovery_rate",
                "shape": "MRR = (M_(t+1) - M_t) / Delta_t",
                "semantics": "rate of modifier regeneration",
                "folded_use": "recovery capacity after overload or drift",
            },
            {
                "id": "paradox_suppression_ratio",
                "shape": "PSR = 1 - (Q_active / Q_total)",
                "semantics": "suppression of paradox activation",
                "folded_use": "buffering gate for contradiction/overflow",
            },
        ],
        "collapse_topology": [
            "drift rise",
            "drift reversal",
            "drift plateau",
            "drift rebound",
            "partial collapse",
            "stabilisation",
            "final collapse",
        ],
        "overload_model_mapping": {
            "Q_t": "active contradiction/paradox/salience pressure",
            "C_t": "constraints or assimilation structures",
            "M_t": "modifiers, repair operators, or buffering mechanisms",
            "D_t": "symbolic overload pressure",
            "C_rho": "institutional/cognitive constraint density",
            "MRR": "repair/offload regeneration rate",
            "PSR": "paradox or contradiction buffering effectiveness",
            "CDC": "delay before terminal collapse or forced reconfiguration",
        },
        "historical_bandwidth_mapping": {
            "accelerated_transfer": "raises Q_t and drift pressure",
            "assimilation_infrastructure": "raises C_t and C_rho",
            "adaptive_interpretive_tools": "raise M_t and MRR",
            "paradox_buffering": "raises PSR and delays collapse",
            "residual_stress": "unbuffered Q_t that drives rebound or collapse",
        },
        "promotion_rule": [
            "use only as structural analogy and equation-shape prior",
            "map CDMQ variables to local variables explicitly before use",
            "validate any overload/collapse claim against local data",
            "keep source license and no-autonomy claim boundary attached",
        ],
        "failure_rules": [
            "treating synthetic symbolic behavior as biological evidence -> overclaim",
            "implementing protected Sigilith/CDMQ methods from source -> permission boundary violation",
            "using survival-like language without boundary -> invalid framing",
            "mapping Q/C/M variables without local definitions -> hold",
            "claiming collapse prediction without empirical timeline data -> overclaim",
        ],
        "linked_local_models": [
            "Connectome Protective Cognitive Load Reweighting",
            "Holographic Fractional Recursive Equation Fold",
            "Decision Diagram Compression Tuning Prior",
        ],
        "claim_boundary": (
            "This receipt records a symbolic-resilience citation and high-level equation "
            "fold. It is not an implementation, not a derivative Sigilith method, not "
            "biological evidence, and not proof of the historical overload theory."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "map_symbolic_resilience_equation",
            "input": "D_t, CDC, C_rho, MRR, or PSR equation",
            "target": "overload pressure, collapse delay, constraint density, recovery rate, or paradox buffering",
        },
        {
            "task": "preserve_source_claim_boundary",
            "input": "survival-like symbolic behavior claim",
            "target": "delayed terminal collapse only; no biological/cognitive/autonomous implication",
        },
        {
            "task": "reject_unlicensed_implementation",
            "input": "proposal to implement Sigilith/CDMQ methods from source",
            "target": "hold unless permission or independent derivation is documented",
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
        "equation_count": len(receipt["equation_shapes"]),
        "collapse_topology_stages": len(receipt["collapse_topology"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
