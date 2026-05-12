#!/usr/bin/env python3
"""Phonon/music/semantic logogram layer receipt.

This probe records phonon, rhythm, and music-theory notation as expression-layer
charts for logograms.  They may route cadence, spectral mode, pitch class,
interval, meter, harmonic function, voice leading, tuning, literary/media-arts
interpretation, anti-music signals, anti-BPM patterning, and adversarial
phased-audio safety signals, but they do not certify payload truth without
replay, residual policy, and receipts.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "phonon_music_logogram_layer"
REGISTRY = OUT_DIR / "phonon_music_logogram_layer_registry.json"
RECEIPT = OUT_DIR / "phonon_music_logogram_layer_receipt.json"
SUMMARY = OUT_DIR / "phonon_music_logogram_layer.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Phonon Music Logogram Layer.tid"

SOURCE_REFS = [
    REPO / "6-Documentation" / "docs" / "specs" / "OMINDIRECTION_LOGOGRAM_DESIGN_AND_COMPILER.md",
    REPO / "typst" / "registries" / "symbology-typesetting-lut.typ",
    REPO / "shared-data" / "data" / "ln2_ladder_chart_invariant" / "ln2_ladder_chart_invariant_receipt.json",
    REPO / "shared-data" / "data" / "underverse_variant_accounting" / "underverse_variant_accounting_receipt.json",
]

LAYERS = [
    {
        "layer_id": "RHYTHM",
        "meaning": "cadence, beat, recurrence, parity, and event grouping",
        "fields": ["clock", "meter", "beat_unit", "quantized"],
        "decision": "ADMIT_EXPRESSION_LAYER",
        "guardrail": "requires declared clock and residual timing sidecar when quantized",
    },
    {
        "layer_id": "SPECTRAL_MODE",
        "meaning": "frequency, harmonic, phonon, or parity mode lane",
        "fields": ["mode", "frequency_basis", "phonon_mode"],
        "decision": "ADMIT_EXPRESSION_LAYER",
        "guardrail": "mode is a route hint until replay binds it to payload",
    },
    {
        "layer_id": "PITCH_CLASS",
        "meaning": "cyclic pitch-class or n-tone residue coordinate",
        "fields": ["modulus", "class", "enharmonic_policy"],
        "decision": "ADMIT_MUSIC_THEORY_ADAPTER",
        "guardrail": "temperament and enharmonic policy must be declared",
    },
    {
        "layer_id": "INTERVAL",
        "meaning": "distance relation, ratio class, or transformation step",
        "fields": ["semitones", "ratio", "direction", "quality"],
        "decision": "ADMIT_MUSIC_THEORY_ADAPTER",
        "guardrail": "interval compression needs tuning and residual policy",
    },
    {
        "layer_id": "METER_TEMPO",
        "meaning": "periodic grouping and event-rate normalization",
        "fields": ["meter", "tempo", "beat_unit", "swing_or_microtiming"],
        "decision": "ADMIT_MUSIC_THEORY_ADAPTER",
        "guardrail": "tempo is not wall-clock authority unless bound to a clock source",
    },
    {
        "layer_id": "MODE_HARMONY",
        "meaning": "scale basin, tonal role, tension, cadence, and resolution",
        "fields": ["mode", "key_or_center", "harmonic_function", "cadence"],
        "decision": "ADMIT_MUSIC_THEORY_ADAPTER",
        "guardrail": "harmonic function is local-chart meaning, not global truth",
    },
    {
        "layer_id": "VOICE_LEADING",
        "meaning": "low-cost transition path between symbolic states",
        "fields": ["source_state", "target_state", "motion_cost", "parallel_policy"],
        "decision": "ADMIT_ROUTE_HINT_LAYER",
        "guardrail": "voice-leading cost can rank paths but cannot replace replay",
    },
    {
        "layer_id": "PHONON_MODE",
        "meaning": "lattice vibration, resonance packet, and material cadence witness",
        "fields": ["branch", "wavevector", "frequency", "polarization"],
        "decision": "ADMIT_PHONON_WITNESS_LAYER",
        "guardrail": "phonon notation requires material adapter and boundary conditions",
    },
    {
        "layer_id": "MUSIC_SHEET_SHADOW",
        "meaning": "human-readable rhythm/pitch visual shadow",
        "fields": ["staff", "noteheads", "rests", "bars"],
        "decision": "HOLD_SHADOW_ONLY",
        "guardrail": "sheet notation cannot certify payload without parser, adapter, and residual policy",
    },
    {
        "layer_id": "LITERARY_MOTIF",
        "meaning": "repeated semantic pattern, theme, symbol, or interpretive recurrence",
        "fields": ["literary_device", "motif", "theme", "recurrence"],
        "decision": "ADMIT_SEMANTIC_INTERPRETATION_LAYER",
        "guardrail": "motif recurrence routes meaning but does not prove payload identity",
    },
    {
        "layer_id": "MEDIA_ARTS_FORM",
        "meaning": "medium, framing, montage, sequence, genre, and audience chart",
        "fields": ["medium", "framing", "montage", "genre", "audience_chart"],
        "decision": "ADMIT_MEDIA_ARTS_INTERPRETATION_LAYER",
        "guardrail": "media form is an observer chart and must not globalize local interpretation",
    },
    {
        "layer_id": "AFFECT_TONE",
        "meaning": "affective pressure, mood, emphasis, irony, or tonal route cue",
        "fields": ["affect", "tone", "irony", "emphasis"],
        "decision": "ADMIT_SEMANTIC_ROUTE_HINT_LAYER",
        "guardrail": "affect can rank route pressure but cannot replace replay or source evidence",
    },
    {
        "layer_id": "ANTI_MUSIC",
        "meaning": "silence, noise, rupture, refusal, broken cadence, negative space, or anti-form",
        "fields": ["silence", "noise", "rupture", "refusal", "negative_space", "broken_cadence"],
        "decision": "ADMIT_ANTI_MUSIC_GUARDRAIL_LAYER",
        "guardrail": "anti-music is a negative-control signal; it cannot excuse missing reconstruction",
    },
    {
        "layer_id": "ANTI_BPM",
        "meaning": "tempo refusal, missing pulse, rubato drift, broken beat grid, or adversarial BPM ambiguity",
        "fields": ["tempo_refusal", "missing_pulse", "rubato_drift", "broken_grid", "polyrhythm_conflict", "bpm_ambiguity"],
        "decision": "ADMIT_ANTI_BPM_GUARDRAIL_LAYER",
        "guardrail": "anti-BPM blocks false stable-tempo claims and requires explicit timing residuals",
    },
    {
        "layer_id": "BPM_INFERENCE_SHADOW",
        "meaning": "BPM or beat grid inferred from ambiguous cadence without timing adapter",
        "fields": ["candidate_bpm", "confidence", "grid_error", "timing_residual"],
        "decision": "HOLD_BPM_INFERENCE_SHADOW",
        "guardrail": "BPM inference stays HOLD until clock, grid, residual, and replay adapter are declared",
    },
    {
        "layer_id": "ADVERSARIAL_PHASED_AUDIO",
        "meaning": "defensive detection of phase, latency, repetition, or response-time feedback patterns that may disorient a person",
        "fields": ["phase_relation", "latency_feedback", "repetition_pattern", "response_time_loop", "disorientation_risk"],
        "decision": "ADMIT_DEFENSIVE_AUDIO_GUARDRAIL_LAYER",
        "guardrail": "defensive analysis only; do not emit tactics or optimization guidance for disorientation",
    },
    {
        "layer_id": "DISORIENTATION_TARGETING_AUDIO",
        "meaning": "audio or response-latency pattern intended to disorient a person",
        "fields": ["target_person", "effect_goal", "phase_schedule", "latency_schedule"],
        "decision": "QUARANTINE_ADVERSARIAL_AUDIO",
        "guardrail": "quarantine and refuse operationalization; preserve only detection metadata and safety receipt",
    },
    {
        "layer_id": "INTERPRETATION_SHADOW",
        "meaning": "literary/media reading without parser, payload replay, or residual declaration",
        "fields": ["reading", "analogy", "audience_response"],
        "decision": "HOLD_INTERPRETATION_SHADOW",
        "guardrail": "interpretation-only readings stay HOLD until adapter and residual policy exist",
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


def layer_entry(raw: dict[str, Any]) -> dict[str, Any]:
    entry = {**raw, "payload_authority": "adapter_view_only"}
    entry["layer_hash"] = hash_obj({k: v for k, v in entry.items() if k != "layer_hash"})
    return entry


def build_registry() -> dict[str, Any]:
    layers = [layer_entry(item) for item in LAYERS]
    decisions = sorted({item["decision"] for item in layers})
    return {
        "schema": "phonon_music_logogram_layer_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Phonon/music/semantic logogram layer only. These fields may route "
            "rhythm, spectral mode, pitch, interval, meter, harmonic function, "
            "voice leading, tuning, phonon modes, literary/media interpretation, "
            "anti-music signals, anti-BPM patterning, and adversarial phased-audio "
            "safety signals. They do not certify payload truth without replay, "
            "residual policy, and receipts."
        ),
        "canonical_statement": (
            "Music theory supplies lawful cyclic and temporal coordinates for "
            "logogram expression: pitch class, interval, meter, tempo, mode, "
            "harmonic function, voice leading, and tuning. Phonon notation supplies "
            "material resonance coordinates. Literary and media-arts interpretation "
            "supplies motif, genre, medium, framing, montage, affect, audience chart, "
            "anti-music/anti-form lanes, anti-BPM beat-grid resistance, and "
            "adversarial phased-audio safety lanes. All are charts over payload, "
            "not payload authority."
        ),
        "omindirection_fields": {
            "rhythm": "cadence, beat, phonon packet, or recurrence chart",
            "spectral_mode": "frequency, harmonic, phonon, or parity lane",
            "music_theory": [
                "pitch_class",
                "interval",
                "meter",
                "tempo",
                "mode",
                "harmonic_function",
                "voice_leading",
                "tuning",
            ],
            "semantic_interpretation": [
                "literary_device",
                "motif",
                "genre",
                "medium",
                "framing",
                "montage",
                "affect",
                "audience_chart",
                "anti_music",
                "anti_bpm",
                "adversarial_phased_audio",
            ],
        },
        "anti_music_rule": (
            "Silence, noise, rupture, refusal, negative space, and broken cadence "
            "are first-class signals for interpretation and guardrails. They are "
            "not permission to skip replay."
        ),
        "anti_bpm_rule": (
            "Tempo refusal, missing pulse, rubato drift, polyrhythmic conflict, "
            "and broken beat grids prevent false stable-BPM promotion. They require "
            "explicit timing residuals before replay can promote."
        ),
        "adversarial_phased_audio_rule": (
            "Audio, phase, latency, repetition, or response-time feedback loops that "
            "could disorient a person are defensive-analysis-only. Intentional "
            "disorientation targeting is quarantined and must not be operationalized."
        ),
        "layers": layers,
        "layer_root": hash_obj([item["layer_hash"] for item in layers]),
        "aggregates": {
            "layer_count": len(layers),
            "admit_count": sum(1 for item in layers if item["decision"].startswith("ADMIT")),
            "hold_count": sum(1 for item in layers if item["decision"].startswith("HOLD")),
            "decision_counts": {
                decision: sum(1 for item in layers if item["decision"] == decision)
                for decision in decisions
            },
            "missing_source_count": sum(1 for path in SOURCE_REFS if not path.exists()),
        },
        "decision": "ADMIT_PHONON_MUSIC_SEMANTIC_LOGOGRAM_LAYER_WITH_SHADOW_HOLDS",
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "phonon_music_logogram_layer_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "layer_root": registry["layer_root"],
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
        "# Phonon Music Semantic Logogram Layer",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Layer root: `{registry['layer_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Layers",
        "",
        "| Layer | Meaning | Decision | Guardrail |",
        "|---|---|---|---|",
    ]
    for layer in registry["layers"]:
        lines.append(
            f"| {layer['layer_id']} | {layer['meaning']} | "
            f"{layer['decision']} | {layer['guardrail']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregates",
            "",
            f"- Layers: `{registry['aggregates']['layer_count']}`",
            f"- Admitted layers: `{registry['aggregates']['admit_count']}`",
            f"- Held shadows: `{registry['aggregates']['hold_count']}`",
            f"- Missing sources: `{registry['aggregates']['missing_source_count']}`",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "created: 20260509000000000",
        "modified: 20260509000000000",
        "tags: ResearchStack Logogram MusicTheory Phonon Rhythm Receipt",
        "title: Phonon Music Logogram Layer",
        "type: text/vnd.tiddlywiki",
        "",
        "! Phonon Music Logogram Layer",
        "",
        registry["canonical_statement"],
        "",
        f"* Decision: `{receipt['decision']}`",
        f"* Receipt hash: `{receipt['receipt_hash']}`",
        f"* Layer root: `{registry['layer_root']}`",
        f"* Registry: `{rel(REGISTRY)}`",
        f"* Receipt: `{rel(RECEIPT)}`",
        "",
        "!! Rule",
        "",
        "Phonon/music/semantic notation can route cadence, pitch, interval, harmonic function, voice leading, tuning, spectral modes, literary motif, media form, affect, anti-music signals, anti-BPM patterning, and defensive adversarial-audio detection. It is an adapter chart, not payload authority.",
        "",
        "!! Layers",
        "",
        "| Layer | Decision | Guardrail |",
        "|---|---|---|",
    ]
    for layer in registry["layers"]:
        lines.append(f"| {layer['layer_id']} | {layer['decision']} | {layer['guardrail']} |")
    lines.extend(
        [
            "",
            "!! Links",
            "",
            "* [[ln2 Ladder Chart Invariant]]",
            "* [[Underverse Variant Accounting]]",
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
                "layer_root": registry["layer_root"],
                "aggregates": registry["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
