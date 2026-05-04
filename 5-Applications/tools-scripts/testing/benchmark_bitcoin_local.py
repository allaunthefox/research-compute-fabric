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
"""Local-only Bitcoin benchmark helper.

Computes the hashrate required to hit a USD target over a duration (default 48h)
given BTC price and network hashrate (e.g., 5-day average). Optionally drives a
local regtest node (if `bitcoind`/`bitcoin-cli` are installed) to generate the
expected number of blocks and report rewards for a temporary wallet.

This is intended for simulation / apples-to-oranges comparison on regtest.
"""

import argparse
import json
import shutil
# import subprocess (REMOVED BY WARDEN)
import sys
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parent.parent


def compute_required_hash(target_usd: float, duration_hours: float, btc_price: float, net_hash_eh: float,
                          block_reward_btc: float = 3.125, block_time_s: float = 600.0) -> Dict[str, Any]:
    duration_s = duration_hours * 3600.0
    n_blocks = duration_s / block_time_s
    network_usd = n_blocks * block_reward_btc * btc_price
    share = target_usd / network_usd if network_usd > 0 else 0.0
    required_hash_eh = share * net_hash_eh
    return {
        "duration_hours": duration_hours,
        "n_blocks": int(round(n_blocks)),
        "network_usd": network_usd,
        "required_share": share,
        "required_hash_eh": required_hash_eh,
    }


def estimate_hash_from_gpgpu_logic_signal_substrate(logic_signal_substrate_path: str, ops_per_hash: float = 1000.0) -> Dict[str, Any]:
    """Estimate H/s from a TSM manifest that contains `internals.benchmark.flops_allocated`.

    - `flops_allocated` is expected to be a numeric TFLOPS value (e.g. 10000 means 10,000 TFLOPS).
    - `ops_per_hash` is a heuristic mapping from floating ops to SHA-256 double-hash work.
    """
    import json
    from pathlib import Path

    p = Path(logic_signal_substrate_path)
    if not p.exists():
        return {"error": "logic_signal_substrate not found"}
    try:
        manifest = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"failed to parse logic_signal_substrate: {e}"}

    flops = None
    try:
        flops = manifest.get("internals", {}).get("benchmark", {}).get("flops_allocated")
    except Exception:
        flops = None

    if flops is None:
        return {"error": "flops_allocated not present in manifest"}

    # Accept numeric or numeric-like strings
    try:
        flops_val = float(str(flops).replace(",", ""))
    except Exception:
        return {"error": "flops_allocated not numeric"}

    # Interpret as TFLOPS
    flops_per_sec = flops_val * 1e12
    hash_per_sec = flops_per_sec / float(ops_per_hash)
    hash_eh = hash_per_sec / 1e18
    return {
        "flops_allocated_tflops": flops_val,
        "flops_per_sec": flops_per_sec,
        "ops_per_hash": ops_per_hash,
        "hash_per_sec": hash_per_sec,
        "hash_eh_s": hash_eh,
    }


def classify_band(required_hash_eh: float) -> str:
    if required_hash_eh < 2.0:
        return "Invisible (<2 EH/s)"
    if 2.0 <= required_hash_eh <= 10.0:
        return "Noteworthy (2-10 EH/s)"
    if required_hash_eh > 20.0:
        return "RED FLAG (>20 EH/s)"
    return "Elevated (10-20 EH/s)"


def which_bin(name: str) -> str:
    p = shutil.which(name)
    return p or ""


def run_regtest_simulation(datadir: Path, n_blocks: int) -> Dict[str, Any]:
    bd = which_bin("bitcoind")
    cli = which_bin("bitcoin-cli")
    if not bd or not cli:
        return {"error": "bitcoind/bitcoin-cli not found on PATH"}

    script = ROOT / "scripts" / "logic_signal_substrate_bitcoind_regtest.py"
    # start bitcoind
    subprocess.run([sys.executable, str(script), "--datadir", str(datadir), "--start"], check=False)
    # generate blocks
    cp = subprocess.run([sys.executable, str(script), "--datadir", str(datadir), "--generate-blocks", str(n_blocks)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # stop bitcoind
    subprocess.run([sys.executable, str(script), "--datadir", str(datadir), "--stop"], check=False)
    return {"stdout": cp.stdout, "stderr": cp.stderr, "returncode": cp.returncode}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--btc-price", type=float, required=True, help="BTC price in USD")
    ap.add_argument("--net-hash-eh", type=float, required=True, help="Network hashrate (EH/s) — e.g., 400")
    ap.add_argument("--duration-hours", type=float, default=48.0, help="Duration to target (hours)")
    ap.add_argument("--target-usd", type=float, default=500000.0, help="USD target to reach")
    ap.add_argument("--block-reward", type=float, default=3.125, help="Block reward in BTC (default post-halving)")
    ap.add_argument("--simulate-regtest", action="store_true", help="If present, run a regtest node and generate blocks")
    ap.add_argument("--datadir", default=str(Path("out") / "bitcoind_regtest"), help="Regtest datadir for simulation")
    ap.add_argument("--use-gpgpu", action="store_true", help="Estimate hash from a TSM GPGPU manifest")
    ap.add_argument("--logic_signal_substrate", default="", help="Path to TSM manifest to read flops_allocated from")
    ap.add_argument("--ops-per-hash", type=float, default=1000.0, help="Heuristic ops-per-hash for FLOPS->hash conversion")
    ap.add_argument("--tflops", type=float, default=0.0, help="Provide TFLOPS directly instead of reading a TSM manifest")
    args = ap.parse_args()
    res = compute_required_hash(args.target_usd, args.duration_hours, args.btc_price, args.net_hash_eh, args.block_reward)
    res["band"] = classify_band(res["required_hash_eh"])

    print(json.dumps(res, indent=2))

    # Optional: estimate achievable hash from local GPGPU TSM manifest
    if args.use_gpgpu:
        if not args.logic_signal_substrate:
            print(json.dumps({"error": "--use-gpgpu requires --logic_signal_substrate <path>"}, indent=2))
        else:
            g = estimate_hash_from_gpgpu_logic_signal_substrate(args.logic_signal_substrate, ops_per_hash=args.ops_per_hash)
            print(json.dumps({"gpgpu_estimate": g}, indent=2))
            if "hash_eh_s" in g:
                # compute share and expected USD over duration using this hash
                our_hash_eh = g["hash_eh_s"]
                our_share = our_hash_eh / args.net_hash_eh if args.net_hash_eh > 0 else 0.0
                expected_usd = our_share * res["network_usd"]
                print(json.dumps({"our_hash_eh": our_hash_eh, "our_share": our_share, "expected_usd": expected_usd}, indent=2))
        # allow supplying TFLOPS directly
        if args.tflops and args.tflops > 0.0:
            flops_direct = {
                "flops_allocated_tflops": args.tflops,
                "ops_per_hash": args.ops_per_hash,
            }
            flops_per_sec = args.tflops * 1e12
            hash_per_sec = flops_per_sec / float(args.ops_per_hash)
            hash_eh = hash_per_sec / 1e18
            flops_direct.update({"hash_per_sec": hash_per_sec, "hash_eh_s": hash_eh})
            print(json.dumps({"gpgpu_direct_estimate": flops_direct}, indent=2))
            our_share = hash_eh / args.net_hash_eh if args.net_hash_eh > 0 else 0.0
            print(json.dumps({"our_hash_eh": hash_eh, "our_share": our_share, "expected_usd": our_share * res["network_usd"]}, indent=2))

    if args.simulate_regtest:
        print("Attempting regtest simulation (requires bitcoind/bitcoin-cli)...")
        sim = run_regtest_simulation(Path(args.datadir), res["n_blocks"])  # type: ignore[arg-type]
        print(json.dumps(sim, indent=2))



if __name__ == "__main__":
    main()
