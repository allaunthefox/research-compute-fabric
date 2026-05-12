#!/usr/bin/env python3
"""Emit Prethinker computational-epistemics prior packets.

This preserves dr3d/prethinker as an external architecture prior for governed
semantic intake. It does not vendor code and does not claim local reproduction.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "shared-data" / "data" / "prethinker_epistemics"


@dataclass(frozen=True)
class EpistemicPriorPacket:
    packet_id: str
    name: str
    facet: str
    source_url: str
    external_term: str
    local_mapping: str
    rrc_use: str
    density_markers: list[str]
    claim_boundary: str
    decision: str = "HOLD"


def stable_hash(obj: object) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_packets() -> list[EpistemicPriorPacket]:
    repo = "https://github.com/dr3d/prethinker"
    semantic_instrument = (
        "https://raw.githubusercontent.com/dr3d/prethinker/main/docs/SEMANTIC_INSTRUMENT.md"
    )
    compiler = (
        "https://raw.githubusercontent.com/dr3d/prethinker/main/docs/"
        "MULTI_PASS_SEMANTIC_COMPILER.md"
    )
    mapper = (
        "https://raw.githubusercontent.com/dr3d/prethinker/main/docs/"
        "SEMANTIC_IR_MAPPER_SPEC.md"
    )
    harness = (
        "https://raw.githubusercontent.com/dr3d/prethinker/main/docs/"
        "CURRENT_HARNESS_INSTRUMENT.md"
    )

    return [
        EpistemicPriorPacket(
            packet_id="PRETHINKER.PRIOR.AUTHORITY_BOUNDARY.0001",
            name="Model proposes, deterministic mapper admits",
            facet="authority_boundary",
            source_url=repo,
            external_term="governed semantic intake / deterministic admission gates",
            local_mapping="LLM proposal != accepted state",
            rrc_use="use as proposal/admission boundary for RRC semantic candidates",
            density_markers=[
                "semantic_workspace",
                "deterministic_mapper",
                "prolog_truth_layer",
                "candidate_operation_gate",
                "unsafe_write_block",
            ],
            claim_boundary="Architecture prior only; local mapper/replay implementation required.",
        ),
        EpistemicPriorPacket(
            packet_id="PRETHINKER.PRIOR.SOURCE_ENVELOPE.0001",
            name="Source envelope and epistemic status split",
            facet="source_envelope",
            source_url=mapper,
            external_term="source policy and candidate operation admission",
            local_mapping="claim carrier must preserve who said what before promoting content",
            rrc_use="separate speech/source atoms from payload truth atoms",
            density_markers=[
                "said_vs_known",
                "claim_content_container",
                "direct_context_inferred_source_policy",
                "unsafe_implication_diagnostic",
                "claim_fact_noncollapse",
            ],
            claim_boundary="Does not determine truth; preserves source-scoped candidates for admission.",
        ),
        EpistemicPriorPacket(
            packet_id="PRETHINKER.PRIOR.TEMPORAL_BINDING.0001",
            name="Temporal binding and interval-state surface",
            facet="temporal_state",
            source_url=semantic_instrument,
            external_term="temporal status lens / temporal unavailable uncertainty",
            local_mapping="temporal is corpus-time, interval, correction dependency, or pass index",
            rrc_use="route time anchors into explicit temporal state, not flattened event facts",
            density_markers=[
                "temporal_anchor",
                "status_interval",
                "deadline_family",
                "effective_expired_boundary",
                "correction_dependent_interval",
            ],
            claim_boundary="Temporal graph or lens output is proposal-only until candidate operations pass gates.",
        ),
        EpistemicPriorPacket(
            packet_id="PRETHINKER.PRIOR.STRUCTURED_ABSENCE.0001",
            name="Structured absence and uncertainty vocabulary",
            facet="structured_absence",
            source_url=semantic_instrument,
            external_term="unknown / unstated / pending / disputed / unsupported states",
            local_mapping="absence can be a positive epistemic state, not missing data",
            rrc_use="encode HOLD/unknown/unstated/resolved-negative without filling the gap",
            density_markers=[
                "unknown_not_unstated",
                "pending_not_false",
                "disputed_claims",
                "unsupported_claim",
                "resolved_negative",
            ],
            claim_boundary="Uncertainty labels are admission states, not replacement facts.",
        ),
        EpistemicPriorPacket(
            packet_id="PRETHINKER.PRIOR.CORRECTION_CASCADE.0001",
            name="Correction provenance and cascade guard",
            facet="correction_cascade",
            source_url=mapper,
            external_term="safe retract / correction projection / temporal correction guard",
            local_mapping="correction changes dependent carriers while preserving original speech act receipt",
            rrc_use="route corrections through residual/retraction sidecars and dependency repair",
            density_markers=[
                "correction_target",
                "retract_plan",
                "replacement_anchor",
                "dependent_interval_recalc",
                "original_claim_preserved",
            ],
            claim_boundary="Correction candidates require explicit retract/correction plan before durable mutation.",
        ),
        EpistemicPriorPacket(
            packet_id="PRETHINKER.PRIOR.COUNTERFACTUAL_CONTAINMENT.0001",
            name="Counterfactual containment",
            facet="counterfactual",
            source_url=mapper,
            external_term="pure hypothetical query projection",
            local_mapping="hypothetical premises may answer a query but must not write durable facts",
            rrc_use="keep what-if expansion in scoped diagnostic world or query lane",
            density_markers=[
                "hypothetical_query",
                "no_premise_write",
                "inferred_query_allowed",
                "durable_truth_blocked",
                "counterfactual_scope",
            ],
            claim_boundary="Counterfactual answers do not promote premise or conclusion into global state.",
        ),
        EpistemicPriorPacket(
            packet_id="PRETHINKER.PRIOR.RATIONALE_MECHANISM.0001",
            name="Rationale versus mechanism",
            facet="rationale_mechanism",
            source_url=semantic_instrument,
            external_term="rationale/contrast lens",
            local_mapping="event mechanism and stated reason are separate atom families",
            rrc_use="preserve why-surface separately from action surface for selector routing",
            density_markers=[
                "mechanism_fact",
                "rationale_fact",
                "contrast_note",
                "why_question_surface",
                "answer_shape_guard",
            ],
            claim_boundary="Rationale is source-scoped support, not automatic causal proof.",
        ),
        EpistemicPriorPacket(
            packet_id="PRETHINKER.PRIOR.SELECTOR_SURFACE.0001",
            name="Selector surface and row-level activation",
            facet="selector_problem",
            source_url=harness,
            external_term="selector guards / row-level activation / exact-row protection",
            local_mapping="different questions need different admitted surfaces over the same artifact",
            rrc_use="choose evidence surface by question type without mutating the core record",
            density_markers=[
                "question_act_routing",
                "surface_specificity",
                "baseline_readiness",
                "row_level_gate",
                "exact_row_protection",
            ],
            claim_boundary="Selector policy is diagnostic until transfer support prevents regressions.",
        ),
        EpistemicPriorPacket(
            packet_id="PRETHINKER.PRIOR.MULTI_PASS_LENSES.0001",
            name="Multi-pass semantic lens accumulation",
            facet="semantic_lenses",
            source_url=compiler,
            external_term="semantic parallax / safe-surface accumulation",
            local_mapping="compile multiple constrained views; union only admitted rows",
            rrc_use="use separate lens passes for source, temporal, rule, rationale, and selector surfaces",
            density_markers=[
                "semantic_parallax",
                "backbone_lens",
                "support_lens",
                "rule_lens",
                "safe_surface_union",
            ],
            claim_boundary="Union is deterministic over admitted clauses only; it does not reread prose.",
        ),
        EpistemicPriorPacket(
            packet_id="PRETHINKER.PRIOR.STRUGGLE_DETECTION.0001",
            name="Semantic struggle and zombie retry detector",
            facet="struggle_detection",
            source_url=harness,
            external_term="semantic_progress_assessment_v1",
            local_mapping="Tree Fiddy-style stop condition for nonproductive semantic passes",
            rrc_use="stop candidate generation when unique contribution stalls or duplicate ratio rises",
            density_markers=[
                "zombie_risk",
                "duplicate_ratio",
                "recent_unique_contribution",
                "stop_and_report",
                "named_expected_contribution",
            ],
            claim_boundary="Stop recommendation is telemetry-derived, not a semantic truth result.",
        ),
    ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packets = build_packets()
    packet_dicts = [asdict(packet) for packet in packets]

    packets_path = OUT_DIR / "prethinker_computational_epistemics_packets.jsonl"
    receipt_path = OUT_DIR / "prethinker_computational_epistemics_receipt.json"

    with packets_path.open("w", encoding="utf-8") as fh:
        for packet in packet_dicts:
            fh.write(json.dumps(packet, sort_keys=True) + "\n")

    receipt = {
        "schema": "prethinker_computational_epistemics_receipt_v1",
        "packet_count": len(packets),
        "facets": sorted({packet.facet for packet in packets}),
        "density_marker_total": sum(len(packet.density_markers) for packet in packets),
        "decision": "HOLD",
        "packets_sha256": stable_hash(packet_dicts),
        "claim_boundary": (
            "External architecture prior only. No Prethinker code is vendored; "
            "local adoption requires clean-room mapping, replay receipts, and byte-law gates."
        ),
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
