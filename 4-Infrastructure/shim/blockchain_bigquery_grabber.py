#!/usr/bin/env python3
"""BigQuery grabber command surface for public cryptocurrency datasets.

The script intentionally defaults to dry-run command emission. Actual BigQuery
exports require Google Cloud authentication and a GCS staging bucket. This keeps
the corpus lane receipt-bearing without embedding credentials or pretending
that a public dataset can be exported anonymously.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


DATASETS = {
    "bitcoin-cash": "bigquery-public-data.crypto_bitcoin_cash",
    "dash": "bigquery-public-data.crypto_dash",
    "dogecoin": "bigquery-public-data.crypto_dogecoin",
    "ethereum-classic": "bigquery-public-data.crypto_ethereum_classic",
    "litecoin": "bigquery-public-data.crypto_litecoin",
    "zcash": "bigquery-public-data.crypto_zcash",
}

DEFAULT_TABLES = ["blocks", "transactions", "inputs", "outputs"]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)


def build_plan(chains: list[str], tables: list[str], gcs_bucket: str, drive_destination: str) -> dict[str, Any]:
    entries = []
    for chain in chains:
        dataset = DATASETS[chain]
        chain_slug = chain
        local_root = f"shared-data/data/blockchain_corpus/bigquery_exports/{chain_slug}"
        remote_root = f"{drive_destination.rstrip('/')}/public-datasets/google-bigquery/{chain_slug}"
        commands = [f"bq ls {dataset}"]
        for table in tables:
            commands.append(
                "bq extract --destination_format=PARQUET "
                f"'{dataset}.{table}' "
                f"'gs://{gcs_bucket}/research-stack/blockchain-corpus/{chain_slug}/{table}/*.parquet'"
            )
        commands.extend(
            [
                (
                    "gcloud storage cp --recursive "
                    f"'gs://{gcs_bucket}/research-stack/blockchain-corpus/{chain_slug}/' "
                    f"'{local_root}/'"
                ),
                f"rclone copy '{local_root}/' '{remote_root}/'",
            ]
        )
        entries.append(
            {
                "chain": chain,
                "dataset": dataset,
                "tables": tables,
                "gcs_prefix": f"gs://{gcs_bucket}/research-stack/blockchain-corpus/{chain_slug}/",
                "local_root": local_root,
                "drive_destination": remote_root,
                "commands": commands,
            }
        )
    return {
        "schema": "blockchain_bigquery_grabber_plan_v0",
        "claim_boundary": "Dry-run command plan only unless --execute is used with authenticated Google Cloud tooling.",
        "tool_status": {
            "bq": shutil.which("bq"),
            "gcloud": shutil.which("gcloud"),
            "gsutil": shutil.which("gsutil"),
            "rclone": shutil.which("rclone"),
            "python": sys.executable,
            "python_bigquery_client": python_module_available("google.cloud.bigquery"),
            "python_google_auth": python_module_available("google.auth"),
        },
        "entries": entries,
    }


def python_module_available(module: str) -> bool:
    try:
        __import__(module)
        return True
    except Exception:
        return False


def list_with_python_client(entries: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    try:
        from google.api_core.exceptions import GoogleAPIError  # type: ignore
        from google.auth.exceptions import DefaultCredentialsError  # type: ignore
        from google.cloud import bigquery  # type: ignore
    except Exception as exc:  # noqa: BLE001 - receipt exact missing module.
        return "HOLD_BIGQUERY_PYTHON_CLIENT_MISSING", [
            {"error": type(exc).__name__, "message": str(exc), "python": sys.executable}
        ]

    try:
        client = bigquery.Client()
    except DefaultCredentialsError as exc:
        return "HOLD_GOOGLE_ADC_MISSING", [
            {
                "error": type(exc).__name__,
                "message": str(exc).splitlines()[0],
                "python": sys.executable,
                "next_step": "Run gcloud auth application-default login or provide GOOGLE_APPLICATION_CREDENTIALS.",
            }
        ]
    except Exception as exc:  # noqa: BLE001 - receipt unexpected auth/client failures.
        return "HOLD_BIGQUERY_CLIENT_INIT_FAILED", [
            {"error": type(exc).__name__, "message": str(exc), "python": sys.executable}
        ]

    results = []
    ok = True
    for entry in entries:
        try:
            tables = list(client.list_tables(entry["dataset"]))
            results.append(
                {
                    "chain": entry["chain"],
                    "dataset": entry["dataset"],
                    "tables": [{"table_id": table.table_id, "full_table_id": table.full_table_id} for table in tables],
                }
            )
        except GoogleAPIError as exc:
            ok = False
            results.append({"chain": entry["chain"], "dataset": entry["dataset"], "error": type(exc).__name__, "message": str(exc)})
        except Exception as exc:  # noqa: BLE001 - receipt per-dataset failure.
            ok = False
            results.append({"chain": entry["chain"], "dataset": entry["dataset"], "error": type(exc).__name__, "message": str(exc)})
    return ("ADMIT_BIGQUERY_PYTHON_LIST_CHECK" if ok else "HOLD_BIGQUERY_PYTHON_LIST_CHECK_FAILED"), results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chains", nargs="+", default=list(DATASETS), choices=sorted(DATASETS))
    parser.add_argument("--tables", nargs="+", default=DEFAULT_TABLES)
    parser.add_argument("--gcs-bucket", default="<YOUR_GCS_BUCKET>")
    parser.add_argument(
        "--drive-destination",
        default="Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10",
    )
    parser.add_argument("--out", default="shared-data/data/blockchain_corpus/blockchain_bigquery_grabber_plan.json")
    parser.add_argument("--execute-list-only", action="store_true", help="Run only bq ls commands to verify table access.")
    parser.add_argument("--execute-python-list-only", action="store_true", help="Run table listing through google-cloud-bigquery.")
    args = parser.parse_args()

    plan = build_plan(args.chains, args.tables, args.gcs_bucket, args.drive_destination)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.execute_list_only:
        if not shutil.which("bq"):
            print(json.dumps({"decision": "HOLD_BQ_CLI_MISSING", "out": str(out)}))
            return 2
        results = []
        for entry in plan["entries"]:
            proc = run(["bq", "ls", entry["dataset"]])
            results.append(
                {
                    "chain": entry["chain"],
                    "dataset": entry["dataset"],
                    "returncode": proc.returncode,
                    "stdout": proc.stdout[-4000:],
                    "stderr": proc.stderr[-4000:],
                }
            )
        result_path = out.with_name(out.stem + "_list_results.json")
        result_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        ok = all(item["returncode"] == 0 for item in results)
        print(json.dumps({"decision": "ADMIT_BQ_LIST_CHECK" if ok else "HOLD_BQ_LIST_CHECK_FAILED", "out": str(out), "results": str(result_path)}))
        return 0 if ok else 2

    if args.execute_python_list_only:
        decision, results = list_with_python_client(plan["entries"])
        result_path = out.with_name(out.stem + "_python_list_results.json")
        result_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"decision": decision, "out": str(out), "results": str(result_path)}))
        return 0 if decision.startswith("ADMIT") else 2

    print(json.dumps({"decision": "ADMIT_BIGQUERY_GRABBER_DRY_RUN_PLAN", "out": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
