#!/usr/bin/env python3
"""Emit decoder-facing reconstruction-core prior packets.

This is a documentation/architecture receipt generator. It does not implement a
compressor. It preserves the 2026-05-08 synthesis as finite HOLD packets that
can be diffed, linked from the wiki, and later promoted only by benchmarked
byte-exact replay.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "shared-data" / "data" / "decoder_reconstruction_core"


@dataclass(frozen=True)
class PriorPacket:
    packet_id: str
    name: str
    decision: str
    source_url: str
    canonical_phrase: str
    density_markers: list[str]
    claim_boundary: str


def stable_hash(obj: object) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_packets() -> list[PriorPacket]:
    source_url = "https://chatgpt.com/c/69fe87f6-9838-83ea-b95b-54b0579122c3"
    return [
        PriorPacket(
            packet_id="DRC.PRIOR.NOT_ASSEMBLY.0001",
            name="Decoder-facing reconstruction core boundary",
            decision="HOLD",
            source_url=source_url,
            canonical_phrase="This is not assembly. It is a lawful reconstruction core.",
            density_markers=[
                "not_human_readable_ir",
                "deterministic_replay_boundary",
                "residual_repair_interface",
                "byte_exact_output_gate",
                "inspection_moved_to_receipts",
            ],
            claim_boundary=(
                "Defines an interface boundary only; validity still requires "
                "byte-exact replay, residual repair, and counted bytes."
            ),
        ),
        PriorPacket(
            packet_id="DRC.PRIOR.OMCF_PIST.0001",
            name="OMCF plus PIST field carrier synthesis",
            decision="HOLD",
            source_url=source_url,
            canonical_phrase="OMCF carries the object; PIST moves the surface.",
            density_markers=[
                "mass_gaussian_continuant",
                "semantic_mass_imaginary_lane",
                "pist_surface_transform",
                "oamvr_oavmr_receipt",
                "deterministic_expansion_packet",
            ],
            claim_boundary=(
                "Design carrier only; no OMCF/PIST packet promotes without "
                "deterministic replay and positive byte law."
            ),
        ),
        PriorPacket(
            packet_id="DRC.PRIOR.HEX_SEED_TRIAD.0001",
            name="Hex seed ladder logogram boundary triad",
            decision="HOLD",
            source_url=source_url,
            canonical_phrase="The seed stores the law, not the expanded table.",
            density_markers=[
                "ladder_lut",
                "hex_logogram_atlas",
                "manifold_boundary_atlas",
                "seed_generated_grouping",
                "residual_exception_stream",
            ],
            claim_boundary=(
                "Seeded generation is an admissible shortcut only when seed, "
                "law, receipt, and residual are cheaper than explicit storage."
            ),
        ),
        PriorPacket(
            packet_id="DRC.PRIOR.CONTROL_FILTERS.0001",
            name="Meme-named control filter stack",
            decision="HOLD",
            source_url=source_url,
            canonical_phrase="Absurd name -> rigorous gate -> receipt -> replay.",
            density_markers=[
                "loc_nes_monster_false_pattern_filter",
                "fyc_manifold_traversal_gate",
                "couch_hysteresis_filter",
                "tree_fiddy_recursion_bound",
                "bhocs_commit_gate",
                "famm_delay_memory_pressure",
            ],
            claim_boundary=(
                "Mnemonic labels do not substitute for proof; each filter must "
                "map to a deterministic predicate or measured gate."
            ),
        ),
        PriorPacket(
            packet_id="DRC.PRIOR.PROPOSER_VERIFIER.0001",
            name="AIMO/SPX proposal-verifier and residual-sharding prior",
            decision="HOLD",
            source_url=source_url,
            canonical_phrase="The model may wander. The verifier does not.",
            density_markers=[
                "minimal_stochastic_proposal",
                "deterministic_verifier",
                "coverage_first_traversal",
                "stateless_residual_sharding",
                "ans_rans_entropy_backend",
            ],
            claim_boundary=(
                "External notebooks and repositories are idea priors only; "
                "clean-room implementation and local replay receipts are required."
            ),
        ),
    ]


def write_jsonl(path: Path, packets: Iterable[PriorPacket]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for packet in packets:
            fh.write(json.dumps(asdict(packet), sort_keys=True) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packets = build_packets()
    packet_dicts = [asdict(packet) for packet in packets]

    packets_path = OUT_DIR / "decoder_reconstruction_core_prior_packets.jsonl"
    receipt_path = OUT_DIR / "decoder_reconstruction_core_prior_receipt.json"

    write_jsonl(packets_path, packets)

    receipt = {
        "schema": "decoder_reconstruction_core_prior_receipt_v1",
        "packet_count": len(packets),
        "packet_ids": [packet.packet_id for packet in packets],
        "density_marker_total": sum(len(packet.density_markers) for packet in packets),
        "decision": "HOLD",
        "packets_sha256": stable_hash(packet_dicts),
        "claim_boundary": (
            "Architecture prior only; no compression win is claimed without "
            "byte-exact replay, residual repair, and measured byte-law gain."
        ),
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
