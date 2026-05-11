#!/usr/bin/env python3
"""Create a receipt for alternative blockchain corpus sources.

This is an admission/planning receipt, not a data-transfer receipt. It records
which public/research sources can replace throttled Blockchair dump pulls and
emits concrete command templates for the tools that can fetch them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DESTINATION = "Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10"


BIGQUERY_CRYPTO_DATASETS = {
    "bitcoin_cash": {
        "chain": "bitcoin-cash",
        "dataset": "bigquery-public-data.crypto_bitcoin_cash",
        "blockchair_status": "PARTIAL_HTTP_402",
    },
    "dash": {
        "chain": "dash",
        "dataset": "bigquery-public-data.crypto_dash",
        "blockchair_status": "PARTIAL_HTTP_402",
    },
    "dogecoin": {
        "chain": "dogecoin",
        "dataset": "bigquery-public-data.crypto_dogecoin",
        "blockchair_status": "PARTIAL_HTTP_402",
    },
    "litecoin": {
        "chain": "litecoin",
        "dataset": "bigquery-public-data.crypto_litecoin",
        "blockchair_status": "PARTIAL_HTTP_402",
    },
    "zcash": {
        "chain": "zcash",
        "dataset": "bigquery-public-data.crypto_zcash",
        "blockchair_status": "PARTIAL_HTTP_402",
    },
    "ethereum_classic": {
        "chain": "ethereum-classic",
        "dataset": "bigquery-public-data.crypto_ethereum_classic",
        "blockchair_status": "NOT_ATTEMPTED",
    },
}


BITCOIN_ETL_CHAINS = [
    "bitcoin",
    "bitcoin_cash",
    "bitcoin_gold",
    "dogecoin",
    "litecoin",
    "dash",
    "zcash",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def command_status(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    version = None
    if path:
        try:
            version_command = [name, "version"] if name == "bq" else [name, "--version"]
            proc = subprocess.run(version_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=15)
            version = proc.stdout.splitlines()[0] if proc.stdout else None
        except Exception as exc:  # noqa: BLE001 - receipt diagnostic only.
            version = f"VERSION_CHECK_FAILED: {exc}"
    return {"available": bool(path), "path": path, "version": version}


def python_module_status(module: str) -> dict[str, Any]:
    try:
        __import__(module)
        return {"available": True, "module": module}
    except Exception as exc:  # noqa: BLE001 - receipt diagnostic only.
        return {"available": False, "module": module, "error": type(exc).__name__}


def bq_extract_commands(destination: str) -> list[dict[str, Any]]:
    commands = []
    for source_id, meta in BIGQUERY_CRYPTO_DATASETS.items():
        dataset = meta["dataset"]
        chain = meta["chain"]
        remote = f"{destination.rstrip('/')}/public-datasets/google-bigquery/{chain}"
        commands.append(
            {
                "source_id": source_id,
                "chain": chain,
                "dataset": dataset,
                "tables_to_try_first": ["blocks", "transactions", "inputs", "outputs"],
                "local_export_pattern": f"shared-data/data/blockchain_corpus/bigquery_exports/{chain}/{{table}}/*.parquet",
                "drive_destination": remote,
                "commands": [
                    f"bq ls {dataset}",
                    (
                        "bq extract --destination_format=PARQUET "
                        f"'{dataset}.{{table}}' "
                        f"'gs://<YOUR_GCS_BUCKET>/research-stack/blockchain-corpus/{chain}/{{table}}/*.parquet'"
                    ),
                    (
                        "gcloud storage cp --recursive "
                        f"'gs://<YOUR_GCS_BUCKET>/research-stack/blockchain-corpus/{chain}/' "
                        f"'shared-data/data/blockchain_corpus/bigquery_exports/{chain}/'"
                    ),
                    (
                        "rclone copy "
                        f"'shared-data/data/blockchain_corpus/bigquery_exports/{chain}/' "
                        f"'{remote}/'"
                    ),
                ],
            }
        )
    return commands


def bitcoin_etl_commands(destination: str) -> list[dict[str, Any]]:
    commands = []
    for chain in BITCOIN_ETL_CHAINS:
        remote = f"{destination.rstrip('/')}/node-etl/bitcoin-etl/{chain}"
        commands.append(
            {
                "chain": chain,
                "requires": ["running_full_node_or_rpc_snapshot", "bitcoin-etl"],
                "commands": [
                    "python3 -m pip install --user bitcoin-etl",
                    (
                        "bitcoinetl export_blocks_and_transactions "
                        "--start-block 0 --end-block <END_BLOCK> "
                        f"--provider-uri http://<rpc_user>:<rpc_pass>@127.0.0.1:<rpc_port> --chain {chain} "
                        f"--blocks-output shared-data/data/blockchain_corpus/node_etl/{chain}/blocks.jsonl "
                        f"--transactions-output shared-data/data/blockchain_corpus/node_etl/{chain}/transactions.jsonl"
                    ),
                    f"rclone copy 'shared-data/data/blockchain_corpus/node_etl/{chain}/' '{remote}/'",
                ],
            }
        )
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", default=DEFAULT_DESTINATION)
    parser.add_argument("--out", default="shared-data/data/blockchain_corpus/blockchain_alternative_source_plan_receipt.json")
    args = parser.parse_args()

    receipt = {
        "schema": "blockchain_alternative_source_plan_v0",
        "created_utc": utc_now(),
        "decision": "ADMIT_ALTERNATIVE_SOURCE_PLAN_HOLD_TRANSFER",
        "claim_boundary": (
            "This receipt identifies alternative public/research sources and tool readiness. "
            "It does not prove data was exported from BigQuery, does not bypass source terms, "
            "and does not claim decoded chain semantics."
        ),
        "destination": args.destination,
        "source_candidates": [
            {
                "name": "Google BigQuery Public Cryptocurrency Datasets",
                "decision": "PREFERRED_FOR_BLOCKCHAIR_GAPS",
                "chains": list(BIGQUERY_CRYPTO_DATASETS.values()),
                "why": "Covers Bitcoin-derived chains that Blockchair throttled: Bitcoin Cash, Dash, Dogecoin, Litecoin, and Zcash.",
            "claim_boundary": "Requires Google Cloud authentication and a GCS staging bucket before local/Drive export.",
                "python_client_ready": python_module_status("google.cloud.bigquery").get("available"),
                "source_urls": [
                    "https://cloud.google.com/blog/products/data-analytics/introducing-six-new-cryptocurrencies-in-bigquery-public-datasets-and-how-to-analyze-them",
                    "https://www.cloudskillsboost.google/focuses/8486?parent=catalog",
                ],
            },
            {
                "name": "Blockchain ETL / bitcoin-etl from full nodes or snapshots",
                "decision": "FALLBACK_IF_BIGQUERY_EXPORT_BLOCKED",
                "chains": BITCOIN_ETL_CHAINS,
                "why": "Can export Bitcoin-like chains from local RPC nodes or grabbed node snapshots without Blockchair dumps.",
                "claim_boundary": "Requires per-chain node data/RPC and enough local storage; slower but self-verifiable.",
                "source_urls": ["https://github.com/blockchain-etl/bitcoin-etl"],
            },
            {
                "name": "Bitquery Cloud Data Dumps",
                "decision": "EVALUATE_LICENSE_AND_COVERAGE",
                "chains": ["bitcoin"],
                "why": "Offers Parquet dump patterns and cloud data products; useful as a schema/tooling reference and possible paid/free lane.",
                "claim_boundary": "Coverage and licensing must be checked before mirroring.",
                "source_urls": ["https://docs.bitquery.io/docs/cloud/bitcoin/"],
            },
            {
                "name": "Kaggle/Hugging Face sampled datasets",
                "decision": "HOLD_SAMPLE_ONLY",
                "chains": ["bitcoin-cash", "dash", "dogecoin", "litecoin", "zcash"],
                "why": "Useful for smoke tests and model fixtures, not complete chain mirrors.",
                "claim_boundary": "Do not use for full-corpus claims.",
                "source_urls": [
                    "https://huggingface.co/datasets/Omarrran/CryptoXChain_500K_Multi_Network_Blockchain_Transaction_Dataset",
                    "https://www.kaggle.com/datasets/amritpal333/crypto-mining-data",
                ],
            },
        ],
        "local_tool_readiness": {
            "commands": {
                name: command_status(name)
                for name in ["rclone", "bq", "gcloud", "gsutil", "kaggle", "duckdb"]
            },
            "python_modules": {
                module: python_module_status(module)
                for module in ["requests", "boto3", "pyarrow", "pandas", "google.cloud.bigquery", "duckdb"]
            },
        },
        "bigquery_export_commands": bq_extract_commands(args.destination),
        "node_etl_commands": bitcoin_etl_commands(args.destination),
        "next_gate": {
            "decision": "HOLD_UNTIL_GOOGLE_ADC_AND_GCS_BUCKET",
            "required": [
                "Authenticate with a Google Cloud account allowed to query BigQuery public datasets.",
                "Use either gcloud application-default login or GOOGLE_APPLICATION_CREDENTIALS.",
                "Provide or create a GCS staging bucket for BigQuery extract jobs.",
                "Run the Python BigQuery list check against each candidate dataset and emit table inventory receipt.",
                "Export tables to Parquet, copy locally, then rclone to Drive with SHA receipts.",
            ],
        },
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": receipt["decision"], "out": str(out), "receipt_hash": receipt["receipt_hash"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
