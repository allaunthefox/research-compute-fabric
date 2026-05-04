# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

from __future__ import annotations

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
"""Regtest payout controller.

Usage:
  5-Applications/scripts/regtest_payout_controller.py --datadir PATH --initial-btc N --once
  5-Applications/scripts/regtest_payout_controller.py --datadir PATH --passive-btc-per-day N --run-passive

This script calculates blocks required to reach a BTC target (using current
subsidy derived from block height) and uses `bitcoin-cli -regtest -datadir=...`
to `generatetoaddress`. Passive mode will, once per day, send `passive_btc_per_day`
to a fresh address (ensuring matured funds by mining if needed).
"""


import argparse
import math
# import subprocess (REMOVED BY WARDEN)
import time
from pathlib import Path


def run_cli(datadir: Path, *args):
    cmd = ["bitcoin-cli", "-regtest", f"-datadir={datadir}"] + list(args)
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"CLI failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()


def get_blockcount(datadir: Path) -> int:
    return int(run_cli(datadir, "getblockcount"))


def get_subsidy_at_height(height: int) -> float:
    # Bitcoin subsidy halves every 210000 blocks starting at 50 BTC
    halvings = height // 210000
    base = 50.0
    return base / (2 ** halvings)


def get_new_address(datadir: Path) -> str:
    return run_cli(datadir, "getnewaddress")


def generate_to_address(datadir: Path, nblocks: int, address: str):
    print(f"Generating {nblocks} block(s) to {address}...")
    out = run_cli(datadir, "generatetoaddress", str(nblocks), address)
    print(out)


def get_balance(datadir: Path) -> float:
    return float(run_cli(datadir, "getbalance"))


def send_to_address(datadir: Path, address: str, amount: float) -> str:
    return run_cli(datadir, "sendtoaddress", address, str(amount))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datadir", required=True)
    ap.add_argument("--initial-btc", type=float, default=0.0,
                    help="One-off initial BTC target to generate (e.g. 10000)")
    ap.add_argument("--once", action="store_true",
                    help="Run the initial target once and exit")
    ap.add_argument("--passive-btc-per-day", type=float, default=0.0,
                    help="Send this amount once per 24h to a new address (regtest wallet must have matured funds)")
    ap.add_argument("--run-passive", action="store_true", help="Run passive loop (forever) )")

    args = ap.parse_args()
    datadir = Path(args.datadir)

    if args.initial_btc > 0:
        height = get_blockcount(datadir)
        subsidy = get_subsidy_at_height(height)
        blocks_needed = math.ceil(args.initial_btc / subsidy)
        addr = get_new_address(datadir)
        print(f"Height={height} Subsidy={subsidy} BTC/block → need {blocks_needed} blocks to reach {args.initial_btc} BTC")
        generate_to_address(datadir, blocks_needed, addr)
        if args.once:
            return

    if args.run_passive and args.passive_btc_per_day > 0:
        print("Entering passive payout loop (CTRL-C to stop)")
        while True:
            addr = get_new_address(datadir)
            # Ensure wallet has at least passive_btc_per_day matured
            balance = get_balance(datadir)
            if balance < args.passive_btc_per_day:
                print(f"Matured balance {balance} < {args.passive_btc_per_day}, mining 100 blocks to produce matured coins")
                tmp_addr = get_new_address(datadir)
                generate_to_address(datadir, 100, tmp_addr)
                # Wait a little for RPC/cookie state to settle
                time.sleep(1)
                balance = get_balance(datadir)
            print(f"Sending {args.passive_btc_per_day} BTC to {addr}")
            txid = send_to_address(datadir, addr, args.passive_btc_per_day)
            print(f"TX: {txid}")
            # Mine 1 block to confirm the transaction
            miner_addr = get_new_address(datadir)
            generate_to_address(datadir, 1, miner_addr)
            print("Sleeping 24h until next payout...")
            time.sleep(24 * 3600)



if __name__ == "__main__":
    main()
