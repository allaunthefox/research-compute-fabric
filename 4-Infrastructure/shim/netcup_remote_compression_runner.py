#!/usr/bin/env python3
"""Controlled Netcup remote baseline runner for finance LUT bundles.

Default mode is dry-run: it builds the local portable bundle and writes the
exact remote commands that would be used. Passing --execute performs rsync/ssh.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

import finance_claim_lut_harness as harness


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"


def run(cmd: list[str], cwd: Path = REPO) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {"cmd": cmd, "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    bundle = harness.write_corpus_bundle(harness.load_samples(args.samples), args.bundle_dir)
    remote_dir = args.remote_dir.rstrip("/")
    planned = {
        "copy_bundle": f"rsync -a {args.bundle_dir}/ {args.host}:{remote_dir}/",
        "copy_harness": f"rsync -a {SHIM / 'finance_claim_lut_harness.py'} {args.host}:{remote_dir}/",
        "verify": f"ssh {args.host} 'cd {remote_dir} && python3 finance_claim_lut_harness.py verify --receipt finance_claim_lut_harness_receipt.json'",
        "bench": f"ssh {args.host} 'cd {remote_dir} && python3 finance_claim_lut_harness.py bench --samples canonical_samples.json --fixture-dir remote_fixtures'",
    }
    receipt: dict[str, Any] = {
        "schema": "netcup_remote_compression_receipt_v1",
        "mode": "execute" if args.execute else "dry_run",
        "host": args.host,
        "remote_dir": remote_dir,
        "local_bundle_receipt": bundle,
        "local_environment": {"python": platform.python_version(), "platform": platform.platform()},
        "planned_commands": planned,
        "remote_results": [],
        "lawful": bool(bundle.get("lawful")),
        "claim_boundary": "Netcup baseline proves controlled remote reproducibility only; it is not noisy recovery or provider endorsement",
    }
    if not args.execute:
        receipt["remote_status"] = "not_run_dry_run"
        return receipt

    if not args.host:
        receipt["remote_status"] = "blocked_missing_host"
        receipt["lawful"] = False
        return receipt
    if not shutil.which("rsync") or not shutil.which("ssh"):
        receipt["remote_status"] = "blocked_missing_rsync_or_ssh"
        receipt["lawful"] = False
        return receipt

    commands = [
        ["ssh", args.host, f"mkdir -p {remote_dir}"],
        ["rsync", "-a", f"{args.bundle_dir}/", f"{args.host}:{remote_dir}/"],
        ["rsync", "-a", str(SHIM / "finance_claim_lut_harness.py"), f"{args.host}:{remote_dir}/"],
        ["ssh", args.host, f"cd {remote_dir} && python3 finance_claim_lut_harness.py verify --receipt finance_claim_lut_harness_receipt.json"],
        ["ssh", args.host, f"cd {remote_dir} && python3 finance_claim_lut_harness.py bench --samples canonical_samples.json --fixture-dir remote_fixtures"],
    ]
    results = [run(cmd) for cmd in commands]
    receipt["remote_results"] = results
    receipt["remote_status"] = "ok" if all(item["returncode"] == 0 for item in results) else "failed"
    receipt["lawful"] = receipt["lawful"] and receipt["remote_status"] == "ok"
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=Path)
    parser.add_argument("--bundle-dir", type=Path, default=SHIM / "finance_claim_remote_bundle")
    parser.add_argument("--host", default="netcup")
    parser.add_argument("--remote-dir", default="~/finance_claim_remote_bundle")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out", type=Path, default=SHIM / "netcup_remote_compression_receipt.json")
    args = parser.parse_args()
    receipt = build_receipt(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0 if receipt.get("lawful") or not args.execute else 1


if __name__ == "__main__":
    raise SystemExit(main())
