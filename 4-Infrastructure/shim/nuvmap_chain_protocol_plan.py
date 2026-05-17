#!/usr/bin/env python3
"""Create a protocol receipt for a dedicated NUVMAP chain.

NUVMAP is treated here as a receipt chain for metaprobe/waveprobe outputs. This
is not a token, investment, mainnet, or compression-result claim. It specifies
what a block would carry so scanner state can be stored and replayed without
using third-party chains as an accidental storage layer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "shared-data/data/blockchain_corpus/nuvmap_chain_protocol_plan_receipt.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def build_receipt() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "nuvmap_chain_protocol_plan_v0",
        "created_utc": now_iso(),
        "claim_boundary": (
            "Protocol design receipt only. This does not create a blockchain, token, market, "
            "consensus network, compression result, or Hutter Prize claim. It defines a local/devnet "
            "receipt substrate for metaprobe and waveprobe state."
        ),
        "purpose": {
            "name": "NUVMAP",
            "expanded_role": "Numerical Universe Vector Map receipt chain",
            "core_use": "Store replayable probe-state commitments so scanning can route itself over time.",
            "anti_goal": "Do not use public commodity ledgers as arbitrary bulk storage when a purpose-built receipt chain is enough.",
        },
        "chain_model": {
            "deployment_stage": "LOCAL_DEVNET_ONLY",
            "economic_model": "NO_TOKEN_NO_MARKET",
            "consensus_candidate": "single-writer_receipt_log_then_multisig_validator_set",
            "finality_model": "append-only_merkle_root_with_periodic_external_anchor_optional",
            "data_availability": "on-chain summaries plus content-addressed off-chain sidecars",
        },
        "block_shape": {
            "header": {
                "parent_hash": "sha256(previous_block)",
                "height": "u64",
                "created_utc": "iso8601",
                "scanner_policy_hash": "sha256(l3_policy)",
                "state_root": "merkle_root(receipt_state)",
                "sidecar_manifest_root": "merkle_root(sidecar_hashes)",
            },
            "body": {
                "waveprobe_receipts": "bounded list of wave/eigen/density diagnostic summaries",
                "metaprobe_receipts": "bounded list of route/context/curriculum summaries",
                "storage_channel_receipts": "detected on-chain storage surfaces from source chains",
                "scan_actions": "next bounded scan plan emitted by L3 scheduler",
                "negative_controls": "required controls before promotion of any route",
            },
            "forbidden_body_fields": [
                "private keys",
                "wallet credentials",
                "bulk copyrighted payloads",
                "payloads intended to hide from moderation or provenance",
                "financial promotion metadata",
            ],
        },
        "probe_mapping": {
            "metadata_blitter": {
                "input": "fixed-size metadata words from chain/block/window records",
                "output": "sortable route keys and packed metric words",
                "storage": "blitter shader hash, parameter receipt, key/metric buffer hashes",
            },
            "waveprobe": {
                "input": "byte windows, block fields, density neighborhoods, eigenvalue spectra",
                "output": "local signal vector plus residual/curvature summary",
                "storage": "hash, vector summary, source window receipt, not raw bulk by default",
            },
            "metaprobe": {
                "input": "domain priors, route families, previous scan receipts",
                "output": "policy/context update and HOLD/ADMIT/QUARANTINE decision hints",
                "storage": "decision receipt, route vector, source receipt backlinks",
            },
            "l3_scheduler": {
                "input": "current receipt frontier",
                "output": "next scan frontier",
                "storage": "scanner policy hash and action list",
            },
        },
        "radix_bin_model": {
            "metaphor": "hyper_soliton_search",
            "claim_boundary": "Radix bins are route basins, not semantic labels.",
            "fields": {
                "hash8": "phase seed / local identity packet",
                "density7": "amplitude / byte pressure",
                "delta7": "shock or torsion gradient",
                "zero6": "void / low-information throat",
                "flags4": "boundary condition",
            },
            "stability_rule": "Promote only bins that persist across salts, windows, and negative controls.",
        },
        "minimal_transaction_types": [
            {
                "type": "BLITTER_BIN_RECEIPT",
                "required_fields": ["shader_hash", "params_hash", "source_hash", "key_buffer_hash", "metric_buffer_hash", "decision"],
            },
            {
                "type": "WAVE_RECEIPT",
                "required_fields": ["source_hash", "window_descriptor", "feature_vector_hash", "decision"],
            },
            {
                "type": "META_RECEIPT",
                "required_fields": ["prior_id", "route_family", "evidence_hash", "decision"],
            },
            {
                "type": "STORAGE_SURFACE_RECEIPT",
                "required_fields": ["source_chain", "channel", "carrier_descriptor", "payload_hash_or_null", "decision"],
            },
            {
                "type": "SCAN_POLICY_UPDATE",
                "required_fields": ["previous_policy_hash", "new_policy_hash", "action_merkle_root", "decision"],
            },
            {
                "type": "NEGATIVE_CONTROL",
                "required_fields": ["control_kind", "source_hash", "result_hash", "decision"],
            },
        ],
        "decision_law": {
            "ADMIT": "All required hashes replay, source windows exist, and negative controls do not collapse the signal.",
            "HOLD": "Evidence is incomplete, cost is unknown, payload surface is unverified, or object-level provenance is missing.",
            "QUARANTINE": "Hash mismatch, unsafe payload class, missing provenance, or claim boundary violation.",
        },
        "next_implementation_steps": [
            "Create a JSON fixture block with one WAVE_RECEIPT, one META_RECEIPT, and one SCAN_POLICY_UPDATE.",
            "Add a verifier that recomputes the block hash and merkle roots.",
            "Feed the current blockchain_l3_self_scan_scheduler receipt into the first fixture block.",
            "Run negative controls before any compression-route promotion.",
            "Only after local fixture replay works, consider a small append-only local devnet.",
        ],
        "decision": "ADMIT_NUVMAP_PROTOCOL_PLAN_HOLD_CHAIN_IMPLEMENTATION",
    }
    payload["receipt_hash"] = sha256_text(stable_json({k: v for k, v in payload.items() if k != "receipt_hash"}))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    receipt = build_receipt()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": receipt["decision"], "out": rel(args.out), "receipt_hash": receipt["receipt_hash"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
