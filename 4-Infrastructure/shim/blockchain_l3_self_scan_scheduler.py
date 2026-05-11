#!/usr/bin/env python3
"""Emit a Layer-3 self-scanning plan for blockchain corpus receipts.

The scheduler treats existing inventory and transfer receipts as the control
surface. It does not decode chain semantics or fetch more data. Its job is to
turn scan evidence into the next bounded scan actions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DEFAULT_ACCOUNT = REPO / "shared-data/data/blockchain_corpus/blockchain_full_account_live_receipt.json"
DEFAULT_OUT = REPO / "shared-data/data/blockchain_corpus/blockchain_l3_self_scan_scheduler_receipt.json"


STORAGE_CHANNELS = {
    "bitcoin": [
        {
            "channel": "op_return",
            "scan_surface": "transaction outputs / scriptPubKey",
            "use_boundary": "Detect and receipt embedded payload surfaces; do not publish or optimize arbitrary payload insertion.",
        },
        {
            "channel": "witness_inscription_like_payload",
            "scan_surface": "segwit witness data",
            "use_boundary": "Treat as public immutable payload evidence only.",
        },
        {
            "channel": "coinbase_tag",
            "scan_surface": "coinbase transaction script/witness fields",
            "use_boundary": "Pool tags and receipt markers only; no attribution claim without external witness.",
        },
    ],
    "evm": [
        {
            "channel": "calldata",
            "scan_surface": "transaction input bytes",
            "use_boundary": "Route by byte density and selector shape only; no private-key, exploit, or evasion workflow.",
        },
        {
            "channel": "event_logs",
            "scan_surface": "topics and data fields",
            "use_boundary": "Receipt emitted public events as storage-like data lanes.",
        },
        {
            "channel": "contract_bytecode",
            "scan_surface": "creation/runtime bytecode",
            "use_boundary": "Static payload/code-carrier diagnostic only.",
        },
        {
            "channel": "blob_or_da_payload",
            "scan_surface": "data availability/blob lanes when present in source tables",
            "use_boundary": "Cost-bounded metadata scan first; bulk payload fetch remains HOLD.",
        },
    ],
    "memo": [
        {
            "channel": "memo_or_message",
            "scan_surface": "transaction memo/message/payload fields",
            "use_boundary": "Public memo payload diagnostics only.",
        }
    ],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rel(path: str | Path) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


def density_band(total_bytes: int, object_count: int) -> str:
    if object_count <= 0:
        return "empty"
    bytes_per_object = total_bytes / object_count
    if bytes_per_object >= 64 * 1024 * 1024:
        return "heavy"
    if bytes_per_object >= 8 * 1024 * 1024:
        return "medium"
    return "light"


def completion_state(item: dict[str, Any]) -> dict[str, Any]:
    object_count = int(item.get("object_count") or 0)
    remote_payload = int(item.get("remote_payload_count") or 0)
    remote_parquet = int(item.get("remote_parquet_count") or 0)
    completed = min(remote_payload, remote_parquet)
    missing = max(object_count - completed, 0)
    ratio = completed / object_count if object_count else 0.0
    return {
        "completed_objects": completed,
        "missing_objects": missing,
        "remote_parquet_count": remote_parquet,
        "remote_payload_count": remote_payload,
        "completion_ratio": round(ratio, 9),
    }


def scan_actions(item: dict[str, Any], state: dict[str, Any], band: str) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    chain = item.get("chain")
    table = item.get("table")
    inventory = item.get("inventory")

    if state["missing_objects"]:
        actions.append(
            {
                "action": "RETRY_MISSING_OBJECTS",
                "reason": "Remote payload/parquet count is below inventory object count.",
                "script": "4-Infrastructure/shim/blockchain_public_dataset_transfer.py",
                "inputs": {"inventory": inventory, "chain": chain, "table": table},
                "decision": "HOLD_UNTIL_RETRY_RECEIPT",
            }
        )

    actions.append(
        {
            "action": "RUN_HEADER_OR_BLOCK_PATTERN_PROBE",
            "reason": "Use deterministic numeric residuals as route priors before byte-heavy scans.",
            "script": "4-Infrastructure/shim/blockchain_header_pattern_probe.py",
            "inputs": {"chain": chain, "table": table, "inventory": inventory},
            "decision": "ADMIT_BOUNDED_ROUTE_PRIOR_SCAN",
        }
    )

    if band in {"medium", "heavy"}:
        actions.append(
            {
                "action": "RUN_PARQUET_LOGOGRAM_EIGENPROBE_SAMPLE",
                "reason": "Large average objects should be sampled through feature/density probes before broader transfer.",
                "script": "4-Infrastructure/shim/parquet_logogram_eigenprobe.py",
                "inputs": {"chain": chain, "table": table, "sample_policy": "first_middle_last_partition"},
                "decision": "ADMIT_SAMPLE_ONLY_HOLD_BULK",
            }
        )

    actions.append(
        {
            "action": "REFRESH_SELF_SCAN_SCHEDULER",
            "reason": "The scan output becomes the next L3 control input.",
            "script": "4-Infrastructure/shim/blockchain_l3_self_scan_scheduler.py",
            "inputs": {"account_receipt": rel(DEFAULT_ACCOUNT)},
            "decision": "ADMIT_RECEIPT_FEEDBACK_LOOP",
        }
    )
    return actions


def chain_storage_family(chain: str | None) -> str:
    if chain in {"ethereum", "ethereum-classic", "arbitrum", "base", "cronos"}:
        return "evm"
    if chain in {"bitcoin", "bitcoin-cash", "dash", "dogecoin", "litecoin", "zcash"}:
        return "bitcoin"
    if chain in {"xrp", "stellar", "ton", "aptos", "provenance"}:
        return "memo"
    return "unknown"


def storage_channel_actions(item: dict[str, Any], band: str) -> dict[str, Any]:
    chain = item.get("chain")
    family = chain_storage_family(chain)
    channels = STORAGE_CHANNELS.get(family, [])
    actions = []
    if channels:
        actions.append(
            {
                "action": "RUN_ONCHAIN_STORAGE_CHANNEL_PROBE",
                "reason": "Blockchain records can contain intentional public data carriers; scan them as storage surfaces before treating bytes as neutral noise.",
                "inputs": {
                    "chain": chain,
                    "family": family,
                    "table": item.get("table"),
                    "inventory": item.get("inventory"),
                    "density_band": band,
                },
                "decision": "ADMIT_STORAGE_SURFACE_SCAN_HOLD_PAYLOAD_USE",
            }
        )
    return {
        "family": family,
        "channels": channels,
        "actions": actions,
        "claim_boundary": (
            "Storage-channel model is for detection, accounting, and receipt routing. "
            "It does not recommend publishing payloads on-chain, bypassing moderation, "
            "hiding data, or using public ledgers as private storage."
        ),
    }


def build_receipt(account_path: Path) -> dict[str, Any]:
    account = json.loads(account_path.read_text(encoding="utf-8"))
    entries = []
    for item in account.get("source_inventories", []):
        total_bytes = int(item.get("total_listed_bytes") or 0)
        object_count = int(item.get("object_count") or 0)
        state = completion_state(item)
        band = density_band(total_bytes, object_count)
        entries.append(
            {
                "chain": item.get("chain"),
                "table": item.get("table"),
                "dataset": item.get("dataset"),
                "inventory": item.get("inventory"),
                "inventory_hash": item.get("inventory_hash"),
                "object_count": object_count,
                "total_listed_bytes": total_bytes,
                "bytes_per_object": round(total_bytes / object_count, 3) if object_count else 0.0,
                "density_band": band,
                "storage_channel_model": storage_channel_actions(item, band),
                "completion": state,
                "scan_actions": scan_actions(item, state, band),
            }
        )

    entries.sort(key=lambda row: (row["completion"]["missing_objects"] > 0, row["total_listed_bytes"]), reverse=True)
    payload = {
        "schema": "blockchain_l3_self_scan_scheduler_v0",
        "created_utc": now_iso(),
        "claim_boundary": (
            "Layer-3 scan scheduling receipt only. It uses existing inventory and transfer receipts "
            "to choose next bounded probes. It does not decode chain semantics, claim compression gain, "
            "claim market prediction, or fetch additional corpus bytes."
        ),
        "layer3_interpretation": {
            "old_label": "L3 Bitstream",
            "scanner_label": "L3 executable scan policy",
            "core_rule": "scan_receipts_t -> route_policy_t_plus_1",
            "feedback_equation": "P_{t+1}=L3(R_t,A_t,C_t); R_{t+1}=scan(P_{t+1})",
            "storage_rule": "onchain_payload_surfaces_t -> storage_channel_receipts_t_plus_1",
        },
        "global_storage_boundary": (
            "Public blockchains can store data, but this scheduler only models storage-bearing "
            "surfaces for detection, provenance, and compression-route diagnostics. Bulk payload "
            "reconstruction and payload publication remain outside this receipt."
        ),
        "account_receipt": rel(account_path),
        "account_receipt_hash": account.get("receipt_hash"),
        "source_count": len(entries),
        "frontier": entries,
        "decision": "ADMIT_L3_SELF_SCAN_POLICY",
    }
    payload["receipt_hash"] = sha256_text(stable_json({k: v for k, v in payload.items() if k != "receipt_hash"}))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", type=Path, default=DEFAULT_ACCOUNT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    receipt = build_receipt(args.account)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": receipt["decision"], "out": rel(args.out), "receipt_hash": receipt["receipt_hash"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
