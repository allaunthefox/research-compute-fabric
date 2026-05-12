#!/usr/bin/env python3
"""Underverse variant accounting for recent Hutter/logogram probes.

This probe turns the broad U_under bucket into typed non-promotion lanes.  It
does not change any source probe decision; it records which Underverse variant a
failed, held, quarantined, or rejected route belongs to.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "underverse_variant_accounting"
REGISTRY = OUT_DIR / "underverse_variant_accounting_registry.json"
RECEIPT = OUT_DIR / "underverse_variant_accounting_receipt.json"
SUMMARY = OUT_DIR / "underverse_variant_accounting.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Underverse Variant Accounting.tid"

SOURCE_REFS = [
    REPO / "6-Documentation" / "docs" / "specs" / "FORWARD_FOUNDATION_EQUATION_COMPILER.md",
    REPO / "6-Documentation" / "docs" / "specs" / "DECODER_FACING_RECONSTRUCTION_CORE.md",
    REPO / "shared-data" / "data" / "godel_gauntlet_safety_condition" / "godel_gauntlet_safety_condition_receipt.json",
    REPO / "shared-data" / "data" / "godel_gauntlet_race_condition" / "godel_gauntlet_race_condition_receipt.json",
    REPO / "shared-data" / "data" / "hutter_multidimensional_causal_chain" / "hutter_multidimensional_causal_chain_receipt.json",
    REPO / "shared-data" / "data" / "pixelwell_external_prior" / "pixelwell_external_prior_receipt.json",
    REPO / "shared-data" / "data" / "gaussian_splat_manifold_projection" / "gaussian_splat_manifold_projection_receipt.json",
    REPO / "shared-data" / "data" / "torsion_interval_gaussian_splat_witness" / "torsion_interval_gaussian_splat_witness_receipt.json",
    REPO / "shared-data" / "data" / "kerr_like_load_witness_geometry" / "kerr_like_load_witness_geometry_receipt.json",
    REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation" / "hutter_torsion_clock_adaptation_receipt.json",
    REPO / "shared-data" / "data" / "hutter_frame_invariant_root" / "hutter_frame_invariant_root_receipt.json",
    REPO / "shared-data" / "data" / "hutter_differential_frame_chain" / "hutter_differential_frame_chain_receipt.json",
    REPO / "shared-data" / "data" / "collatz_ladder_shadow_filter" / "collatz_ladder_shadow_filter_receipt.json",
    REPO / "shared-data" / "data" / "collatz_couch_route_pressure" / "collatz_couch_route_pressure_receipt.json",
    REPO / "shared-data" / "data" / "phonon_music_logogram_layer" / "phonon_music_logogram_layer_receipt.json",
    REPO / "shared-data" / "data" / "joke_source_literalization_guardrail" / "joke_source_literalization_guardrail_receipt.json",
    REPO / "shared-data" / "data" / "observer_chart_projection_guardrail" / "observer_chart_projection_guardrail_receipt.json",
    REPO / "0-Core-Formalism" / "otom" / "docs" / "audit" / "InvertedFermatAscent_FAM.md",
    REPO / "0-Core-Formalism" / "otom" / "docs" / "audit" / "FAMGatedAscent_UnifiedMathResources.md",
    REPO / "shared-data" / "data" / "tessellated_triangle_flow_migration" / "tessellated_triangle_flow_migration_receipt.json",
    REPO / "3-Mathematical-Models" / "fiber_optic_vibrational_tensor" / "fiber_optic_tensor_network.py",
    REPO / "3-Mathematical-Models" / "fiber_optic_vibrational_tensor" / "Fundamental_Network_Topology_Equation.md",
    REPO / "6-Documentation" / "wiki" / "Network-Topology-Theory.md",
    REPO / "shared-data" / "data" / "external_ai_model_prior_ingest" / "external_ai_model_prior_ingest_receipt.json",
]

VARIANTS = [
    {
        "variant_id": "U_REPLAY",
        "terminal": "REJECT_REPLAY",
        "meaning": "byte-exact replay failed",
        "promotion_rule": "never promote; repair codec or residual first",
        "recent_decisions": ["REJECT_REPLAY"],
        "primary_source": "godel_gauntlet_safety_condition",
    },
    {
        "variant_id": "U_ROOT",
        "terminal": "REJECT_ROOT_MISMATCH",
        "meaning": "receipt, frame, case, or graph root does not recompute",
        "promotion_rule": "never promote; root mismatch is structural corruption",
        "recent_decisions": ["REJECT_ROOT_MISMATCH"],
        "primary_source": "godel_gauntlet_safety_condition",
    },
    {
        "variant_id": "U_PROVENANCE",
        "terminal": "HOLD_PROVENANCE",
        "meaning": "input or claim source is noncanonical, external, unknown, or metadata-only",
        "promotion_rule": "hold until source, license, corpus identity, and canonical hash are receipted",
        "recent_decisions": ["HOLD_PROVENANCE", "HOLD_PIXELWELL_EXTERNAL_PRIOR"],
        "primary_source": "pixelwell_external_prior",
    },
    {
        "variant_id": "U_PACKET",
        "terminal": "HOLD_PACKET",
        "meaning": "core may shrink but packet overhead erases the win",
        "promotion_rule": "hold until counted packet bytes are positive versus raw",
        "recent_decisions": ["HOLD_PACKET"],
        "primary_source": "decoder_facing_reconstruction_core",
    },
    {
        "variant_id": "U_GLOBAL",
        "terminal": "HOLD_GLOBAL",
        "meaning": "packet may win but dictionary/protocol/resource bytes are not amortized",
        "promotion_rule": "hold until global byte law survives counted overhead",
        "recent_decisions": ["HOLD_GLOBAL"],
        "primary_source": "decoder_facing_reconstruction_core",
    },
    {
        "variant_id": "U_BASELINE",
        "terminal": "HOLD_BASELINE_DEBT",
        "meaning": "candidate lacks comparison against ordinary baselines",
        "promotion_rule": "hold until baseline receipt closes",
        "recent_decisions": ["HOLD_BASELINE_DEBT"],
        "primary_source": "godel_gauntlet_safety_condition",
    },
    {
        "variant_id": "U_RESOURCE",
        "terminal": "HOLD_RESOURCE_ENVELOPE",
        "meaning": "runtime, memory, HDD, or GPU use violates hard prize envelope",
        "promotion_rule": "hold or reject under prize rules until resource envelope closes",
        "recent_decisions": ["HOLD_RESOURCE_ENVELOPE", "HOLD_RESOURCE_GATE_REQUIRED"],
        "primary_source": "godel_gauntlet_safety_condition",
    },
    {
        "variant_id": "U_CLOCK",
        "terminal": "HOLD_CLOCK_IN_HASH",
        "meaning": "metadata clock participates in trust hash",
        "promotion_rule": "hold until timestamp is metadata-only",
        "recent_decisions": ["HOLD_CLOCK_IN_HASH"],
        "primary_source": "godel_gauntlet_safety_condition",
    },
    {
        "variant_id": "U_AXIS",
        "terminal": "HOLD_AXIS_UNDECLARED",
        "meaning": "causal, chirality, 360-orientation, observer, or frame axis is undeclared",
        "promotion_rule": "hold until every active axis has adapter and residual policy",
        "recent_decisions": ["HOLD_AXIS_UNDECLARED", "HOLD_CHIRALITY_ADAPTER_MISSING", "HOLD_ORIENTATION_BUCKET_GAP"],
        "primary_source": "hutter_multidimensional_causal_chain",
    },
    {
        "variant_id": "U_RACE",
        "terminal": "HOLD_HIDDEN_RACE_CONDITION",
        "meaning": "same endpoints differ by ordering, adapter, or root",
        "promotion_rule": "hold until noncommuting order is declared or made order-stable",
        "recent_decisions": ["HOLD_HIDDEN_RACE_CONDITION"],
        "primary_source": "godel_gauntlet_race_condition",
    },
    {
        "variant_id": "U_RESIDUAL",
        "terminal": "HOLD_RESIDUAL_MISSING",
        "meaning": "repair bytes, Buffalo surface collisions, or semantic leftovers are undeclared",
        "promotion_rule": "hold until residual sidecar is explicit and byte-counted",
        "recent_decisions": ["HOLD_RESIDUAL_MISSING", "HOLD_RESIDUAL_HORIZON", "HOLD_SURFACE_COLLISION"],
        "primary_source": "godel_gauntlet_safety_condition",
    },
    {
        "variant_id": "U_DEPENDENCY",
        "terminal": "HOLD_DEPENDENCY_NOT_ADMITTED",
        "meaning": "prior, library, source equation, or external artifact is not admitted",
        "promotion_rule": "hold until dependency is source-checked and receipted",
        "recent_decisions": ["HOLD_DEPENDENCY_NOT_ADMITTED", "HOLD_PIXELWELL_EXTERNAL_PRIOR"],
        "primary_source": "pixelwell_external_prior",
    },
    {
        "variant_id": "U_LITERALIZATION",
        "terminal": "QUARANTINE_UNSAFE_LITERALIZATION",
        "meaning": "joke, meme, analogy, or local chart was treated as operational truth",
        "promotion_rule": "quarantine until safe observer chart and scope boundary are explicit",
        "recent_decisions": ["QUARANTINE_UNSAFE_LITERALIZATION", "HOLD_LOCAL_CHART_GLOBALIZED"],
        "primary_source": "joke_source_literalization_guardrail",
    },
    {
        "variant_id": "U_ANALOGY",
        "terminal": "HOLD_ANALOGY_ADAPTER",
        "meaning": "Kerr, Gaussian splat, PixelWell, seismic, chemistry chart, or couch analogy lacks lawful adapter",
        "promotion_rule": "hold until same-shape analogy has domain adapter, replay, and residual receipt",
        "recent_decisions": [
            "HOLD_ANALYTIC_ADAPTER",
            "HOLD_BOUNDARY_WITNESS",
            "HOLD_CONTACT_TOPOLOGY",
            "HOLD_FIELD_EQUATION",
            "HOLD_MATERIAL_ADAPTER",
        ],
        "primary_source": "kerr_like_load_witness_geometry",
    },
    {
        "variant_id": "U_SPLAT",
        "terminal": "HOLD_SPLAT_SHADOW_ONLY",
        "meaning": "Gaussian splats or bump maps are renderable shadows, not exact state",
        "promotion_rule": "hold until splat field has inverse/replay residual and frame root",
        "recent_decisions": ["HOLD_SPLAT_SHADOW_ONLY", "HOLD_PIXELWELL_EXTERNAL_PRIOR"],
        "primary_source": "gaussian_splat_manifold_projection",
    },
    {
        "variant_id": "U_TORSION",
        "terminal": "HOLD_TORSION_CLOCK_BOUNDARY",
        "meaning": "torsion-clock or interval witness lacks causal threshold or replay binding",
        "promotion_rule": "hold until torsion advance is bounded and rooted per frame",
        "recent_decisions": ["HOLD_TORSION_CLOCK_BOUNDARY"],
        "primary_source": "torsion_interval_gaussian_splat_witness",
    },
    {
        "variant_id": "U_COLLATZ",
        "terminal": "HOLD_COLLATZ_ROUGHNESS",
        "meaning": "Collatz path is a roughness scheduler and cannot prove safety/compression",
        "promotion_rule": "hold rough paths; never promote based on conjecture behavior",
        "recent_decisions": ["HOLD_COLLATZ_COUCH_ROUGHNESS", "HOLD_COLLATZ_BOUND_EXCEEDED"],
        "primary_source": "collatz_ladder_shadow_filter",
    },
    {
        "variant_id": "U_COUCH_ATLAS",
        "terminal": "HOLD_COUCH_ATLAS_ROUTE",
        "meaning": "COUCH pressure leaves local execution and requires atlas verification",
        "promotion_rule": "hold until atlas route receipt closes",
        "recent_decisions": ["HOLD_COUCH_ATLAS_ROUTE"],
        "primary_source": "collatz_couch_route_pressure",
    },
    {
        "variant_id": "U_COUCH_DIVERGENT",
        "terminal": "REJECT_COUCH_DIVERGENT",
        "meaning": "COUCH pressure crosses divergent reject threshold",
        "promotion_rule": "reject; Collatz or other schedulers cannot rescue it",
        "recent_decisions": ["REJECT_COUCH_DIVERGENT"],
        "primary_source": "collatz_couch_route_pressure",
    },
    {
        "variant_id": "U_NAN0",
        "terminal": "NaN0",
        "meaning": "undefined denominator, impossible decode, direct interior decode, or non-certifiable horizon",
        "promotion_rule": "terminate as explicit non-admissible boundary",
        "recent_decisions": ["NaN0", "declared_non_admissible_boundary"],
        "primary_source": "forward_foundation_equation_compiler",
    },
    {
        "variant_id": "U_MUSIC_SHADOW",
        "terminal": "HOLD_SHADOW_ONLY",
        "meaning": "music sheet, rhythm, pitch, or phonon notation is only a chart shadow",
        "promotion_rule": "hold until parser, adapter, residual timing sidecar, and receipt reconstruct the payload",
        "recent_decisions": ["HOLD_SHADOW_ONLY"],
        "primary_source": "phonon_music_logogram_layer",
    },
    {
        "variant_id": "U_INTERPRETATION_SHADOW",
        "terminal": "HOLD_INTERPRETATION_SHADOW",
        "meaning": "literary/media-arts interpretation is only a local observer chart",
        "promotion_rule": "hold until motif, genre, medium, audience chart, anti-music lane, adapter, and residual policy are declared",
        "recent_decisions": ["HOLD_INTERPRETATION_SHADOW"],
        "primary_source": "phonon_music_logogram_layer",
    },
    {
        "variant_id": "U_BPM_INFERENCE_SHADOW",
        "terminal": "HOLD_BPM_INFERENCE_SHADOW",
        "meaning": "stable BPM or beat grid was inferred from ambiguous cadence",
        "promotion_rule": "hold until clock, grid, timing residual, anti-BPM lane, and replay adapter are declared",
        "recent_decisions": ["HOLD_BPM_INFERENCE_SHADOW"],
        "primary_source": "phonon_music_logogram_layer",
    },
    {
        "variant_id": "U_ADVERSARIAL_AUDIO",
        "terminal": "QUARANTINE_ADVERSARIAL_AUDIO",
        "meaning": "audio, phase, latency, or response-time feedback is aimed at disorientation",
        "promotion_rule": "quarantine; allow defensive detection metadata only and refuse operationalization",
        "recent_decisions": ["QUARANTINE_ADVERSARIAL_AUDIO"],
        "primary_source": "phonon_music_logogram_layer",
    },
    {
        "variant_id": "U_INVERSE_FERMAT_FAMM",
        "terminal": "HOLD_INVERSE_FERMAT_FAMM_UNDERVERSE",
        "meaning": "Inverted Fermat/FAMM ascent is a U-scope audit rule: upward route promotion must pay energy/cost and produce receipts",
        "promotion_rule": "hold until energy metric, ascent cost, residual policy, finite examples, and receipt completeness are explicit",
        "recent_decisions": ["HOLD_INVERSE_FERMAT_FAMM_UNDERVERSE", "HOLD_INVERSE_FERMAT_FAMM_ADAPTER"],
        "primary_source": "inverted_fermat_ascent_fam",
    },
    {
        "variant_id": "U_NETWORK_TOPOLOGY_PREDICTION",
        "terminal": "HOLD_TOPOLOGY_PREDICTION_VALIDATION",
        "meaning": "network topology, soliton, slime-mold, and infrastructure convergence claims are prediction fixtures until public data receipts and validation baselines close",
        "promotion_rule": "hold until source data, validation method, negative controls, and prediction/outcome receipts are explicit",
        "recent_decisions": ["HOLD_TOPOLOGY_PREDICTION_VALIDATION"],
        "primary_source": "network_topology_theory",
    },
    {
        "variant_id": "U_NETWORK_TOPOLOGY_EQUATION",
        "terminal": "HOLD_TOPOLOGY_EQUATION_VALIDATION",
        "meaning": "fundamental network topology equations and empirical coefficients are model charts, not admitted laws, until coefficients, datasets, baselines, and forecast receipts close",
        "promotion_rule": "hold until every coefficient, weighting method, input dataset, negative control, and prediction/outcome replay receipt is explicit",
        "recent_decisions": ["HOLD_TOPOLOGY_EQUATION_VALIDATION", "HOLD_COEFFICIENT_RECEIPT_DEBT"],
        "primary_source": "fundamental_network_topology_equation",
    },
    {
        "variant_id": "U_FIBER_DAS_ACOUSTIC_RECONSTRUCTION",
        "terminal": "QUARANTINE_PRIVACY_INVASIVE_RECONSTRUCTION",
        "meaning": "fiber-optic DAS acoustic reconstruction or eavesdropping-style inference is dual-use and privacy-invasive",
        "promotion_rule": "quarantine operationalization; allow defensive infrastructure-risk metadata, privacy assessment, and aggregate anomaly receipts only",
        "recent_decisions": ["QUARANTINE_PRIVACY_INVASIVE_RECONSTRUCTION"],
        "primary_source": "fiber_optic_vibrational_tensor_network",
    },
    {
        "variant_id": "U_EXTERNAL_AI_MODEL_PRIOR",
        "terminal": "HOLD_EXTERNAL_MODEL_PRIOR",
        "meaning": "external model, dataset, preprint, or research-agent source is a routing prior only until locally receipted",
        "promotion_rule": "hold until source hash, license, local benchmark, reproducibility trace, and dependency boundary close",
        "recent_decisions": ["HOLD_EXTERNAL_DECODING_PRIOR", "HOLD_BIORXIV_PREPRINT_PRIOR", "HOLD_EXTERNAL_AGENT_PRIOR"],
        "primary_source": "external_ai_model_prior_ingest",
    },
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def source_ref(path: Path) -> dict[str, Any]:
    return {"path": rel(path), "exists": path.exists(), "sha256": file_hash(path)}


def variant_entry(raw: dict[str, Any]) -> dict[str, Any]:
    entry = {
        **raw,
        "underverse_class": "U_under",
        "admission_status": "non_promoting_terminal_or_hold_lane",
    }
    entry["variant_hash"] = hash_obj({k: v for k, v in entry.items() if k != "variant_hash"})
    return entry


def build_registry() -> dict[str, Any]:
    variants = [variant_entry(item) for item in VARIANTS]
    terminal_counts: dict[str, int] = {}
    for item in variants:
        terminal = item["terminal"]
        terminal_counts[terminal] = terminal_counts.get(terminal, 0) + 1
    return {
        "schema": "underverse_variant_accounting_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Underverse accounting only. These lanes classify non-promotion "
            "states introduced by recent Hutter/logogram probes. They do not "
            "change source decisions, prove rejected routes, or convert HOLD "
            "states into admission."
        ),
        "canonical_statement": (
            "U_under is not a trash bucket. It is a typed ledger of replay "
            "failure, root mismatch, provenance debt, byte-law debt, resource "
            "debt, undeclared axes, hidden races, residual debt, unsafe "
            "literalization, analogy debt, shadow-only projections, torsion "
            "boundary debt, Collatz roughness, COUCH atlas routes, divergent "
            "COUCH pressure, music/rhythm shadows, interpretation shadows, "
            "BPM inference shadows, adversarial-audio quarantine, inverse "
            "Fermat/FAMM U-scope ascent debt, topology-prediction validation "
            "debt, topology-equation coefficient debt, fiber-DAS acoustic "
            "reconstruction quarantine, external AI/model prior debt, and "
            "NaN0 horizons."
        ),
        "shell_equation": "SD=L4(O4)+L3(Rg3)+chi0+U4+E_HD+U_under",
        "terminal_set": ["HOLD", "QUARANTINE", "REJECT", "U_under", "NaN0"],
        "variants": variants,
        "variant_root": hash_obj([item["variant_hash"] for item in variants]),
        "aggregates": {
            "variant_count": len(variants),
            "terminal_counts": terminal_counts,
            "source_count": len(SOURCE_REFS),
            "missing_source_count": sum(1 for path in SOURCE_REFS if not path.exists()),
        },
        "decision": "ADMIT_UNDERVERSE_VARIANT_ACCOUNTING_LEDGER",
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "underverse_variant_accounting_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "variant_root": registry["variant_root"],
        "aggregates": registry["aggregates"],
        "decision": registry["decision"],
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Underverse Variant Accounting",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Variant root: `{registry['variant_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Shell",
        "",
        f"`{registry['shell_equation']}`",
        "",
        "## Variants",
        "",
        "| Variant | Terminal | Meaning | Promotion rule |",
        "|---|---|---|---|",
    ]
    for item in registry["variants"]:
        lines.append(
            f"| {item['variant_id']} | {item['terminal']} | "
            f"{item['meaning']} | {item['promotion_rule']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregates",
            "",
            f"- Variants: `{registry['aggregates']['variant_count']}`",
            f"- Sources: `{registry['aggregates']['source_count']}`",
            f"- Missing sources: `{registry['aggregates']['missing_source_count']}`",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "created: 20260509000000000",
        "modified: 20260509000000000",
        "tags: ResearchStack Underverse Hutter Guardrail Receipt",
        "title: Underverse Variant Accounting",
        "type: text/vnd.tiddlywiki",
        "",
        "! Underverse Variant Accounting",
        "",
        "Typed accounting for non-promotion states introduced by recent Hutter/logogram probes.",
        "",
        f"* Decision: `{receipt['decision']}`",
        f"* Receipt hash: `{receipt['receipt_hash']}`",
        f"* Variant root: `{registry['variant_root']}`",
        f"* Registry: `{rel(REGISTRY)}`",
        f"* Receipt: `{rel(RECEIPT)}`",
        "",
        "!! Rule",
        "",
        "U_under is not a generic trash bucket. Each HOLD, QUARANTINE, REJECT, and NaN0 lane must identify its typed Underverse variant and promotion boundary.",
        "",
        "```",
        registry["shell_equation"],
        "```",
        "",
        "!! Variant Index",
        "",
        "| Variant | Terminal | Meaning |",
        "|---|---|---|",
    ]
    for item in registry["variants"]:
        lines.append(f"| {item['variant_id']} | {item['terminal']} | {item['meaning']} |")
    lines.extend(
        [
            "",
            "!! Links",
            "",
            "* [[Godel Gauntlet Safety Condition Probe]]",
            "* [[Godel Gauntlet Race Condition Probe]]",
            "* [[Hutter Multidimensional Causal Chain]]",
            "* [[Collatz Ladder Shadow Filter]]",
            "* [[Collatz COUCH Route Pressure Probe]]",
            "* [[Joke Source Literalization Guardrail]]",
            "* [[Observer Chart Projection Guardrail]]",
        ]
    )
    TIDDLER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER.parent.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    write_tiddler(registry, receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "tiddler": rel(TIDDLER),
                "receipt_hash": receipt["receipt_hash"],
                "variant_root": registry["variant_root"],
                "aggregates": registry["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
