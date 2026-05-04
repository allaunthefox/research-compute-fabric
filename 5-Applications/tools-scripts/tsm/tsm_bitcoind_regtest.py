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
"""Small helper to run a local `bitcoind` regtest instance and inject it into
the omnitoken/TSM surface so the network can "see" a bitcoind node.

Usage examples:
  python 5-Applications/scripts/logic_signal_substrate_bitcoind_regtest.py --status
  python 5-Applications/scripts/logic_signal_substrate_bitcoind_regtest.py --start --datadir 5-Applications/out/bitcoind_regtest
  python 5-Applications/scripts/logic_signal_substrate_bitcoind_regtest.py --generate-blocks 101 --datadir 5-Applications/out/bitcoind_regtest
  python 5-Applications/scripts/logic_signal_substrate_bitcoind_regtest.py --inject-surface --datadir 5-Applications/out/bitcoind_regtest

This script does NOT install Bitcoin Core; it checks for `bitcoind` and
`bitcoin-cli` on PATH and prints instructions if they're missing.
"""

import argparse
import json
import shutil
# import subprocess (REMOVED BY WARDEN)
import time
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parent.parent

try:
    from scripts.weld_omnitoken_surface import utc_now, assert_surface_write_safe, OMNI_SURFACE_PATH
except Exception:
    from weld_omnitoken_surface import utc_now, assert_surface_write_safe, OMNI_SURFACE_PATH  # type: ignore


def which_binary(name: str) -> Optional[str]:
    return shutil.which(name)


def run_cmd(cmd: list, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)


def is_bitcoind_running(datadir: Path) -> bool:
    cli = which_binary("bitcoin-cli")
    if not cli:
        return False
    try:
        cp = run_cmd([cli, "-regtest", f"-datadir={str(datadir)}", "getblockchaininfo"], timeout=5)
        return cp.returncode == 0
    except Exception:
        return False


def start_bitcoind(datadir: Path) -> bool:
    bd = which_binary("bitcoind")
    if not bd:
        print("bitcoind not found on PATH")
        return False
    datadir.mkdir(parents=True, exist_ok=True)
    cmd = [bd, "-regtest", f"-datadir={str(datadir)}", "-daemon"]
    try:
        cp = run_cmd(cmd, timeout=10)
        if cp.returncode != 0:
            print("bitcoind start failed:", cp.stderr)
            return False
    except Exception as e:
        print("Error starting bitcoind:", e)
        return False
    # wait for RPC ready
    for _ in range(20):
        if is_bitcoind_running(datadir):
            return True
        time.sleep(0.5)
    return is_bitcoind_running(datadir)


def stop_bitcoind(datadir: Path) -> bool:
    cli = which_binary("bitcoin-cli")
    if not cli:
        print("bitcoin-cli not found on PATH")
        return False
    cp = run_cmd([cli, f"-datadir={str(datadir)}", "stop"], timeout=10)
    return cp.returncode == 0


def generate_blocks(datadir: Path, blocks: int, address: Optional[str] = None) -> Dict[str, Any]:
    cli = which_binary("bitcoin-cli")
    if not cli:
        raise RuntimeError("bitcoin-cli not found")
    if not address:
        # ensure a wallet exists and getnewaddress
        run_cmd([cli, "-regtest", f"-datadir={str(datadir)}", "createwallet", "logic_signal_substrate_temp_wallet"])  # ignore errors
        cp_addr = run_cmd([cli, "-regtest", f"-datadir={str(datadir)}", "-rpcwallet=logic_signal_substrate_temp_wallet", "getnewaddress"], timeout=10)
        address = cp_addr.stdout.strip() or ""
    cp = run_cmd([cli, "-regtest", f"-datadir={str(datadir)}", "-rpcwallet=logic_signal_substrate_temp_wallet", "generatetoaddress", str(blocks), address], timeout=60)
    return {"returncode": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr}


def inject_surface(datadir: Path, rpc_endpoint: str) -> None:
    if not OMNI_SURFACE_PATH.exists():
        print("OMNI surface not found; cannot inject bitcoind domain")
        return
    try:
        surface = json.loads(OMNI_SURFACE_PATH.read_text(encoding="utf-8"))
    except Exception:
        print("Failed to read/parse OMNI surface; aborting injection")
        return

    surface_bus: Dict[str, Any] = dict(surface.get("surface_bus") or {})
    domains: Dict[str, Any] = dict(surface_bus.get("domains") or {})

    domains["bitcoind_regtest"] = {
        "domain": "bitcoind_regtest",
        "direction": "bidirectional",
        "transport": "bitcoin-rpc",
        "rpc_endpoint": rpc_endpoint,
        "datadir": str(datadir),
        "updated_utc": utc_now(),
    }

    surface_bus["schema"] = str(surface_bus.get("schema") or "omnitoken-surface-bus/v1")
    surface_bus["agnostic"] = True
    surface_bus["domains"] = domains
    surface["surface_bus"] = surface_bus
    surface["updated_utc"] = utc_now()

    assert_surface_write_safe(surface, scope="bitcoind_regtest_injection")
    OMNI_SURFACE_PATH.write_text(json.dumps(surface, indent=2) + "\n", encoding="utf-8")
    print("Injected bitcoind_regtest into surface:", OMNI_SURFACE_PATH)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datadir", default=str(Path("out") / "bitcoind_regtest"), help="regtest datadir")
    ap.add_argument("--start", action="store_true", help="Start bitcoind (regtest)")
    ap.add_argument("--stop", action="store_true", help="Stop bitcoind")
    ap.add_argument("--status", action="store_true", help="Check bitcoind status")
    ap.add_argument("--generate-blocks", type=int, default=0, help="Generate N blocks (regtest) using generatetoaddress")
    ap.add_argument("--inject-surface", action="store_true", help="Inject bitcoind_regtest domain into OMNI surface")
    ap.add_argument("--rpc-endpoint", default="http://127.0.0.1:18443", help="RPC endpoint (for surface injection)")
    args = ap.parse_args()

    datadir = Path(args.datadir)

    bd = which_binary("bitcoind")
    bc = which_binary("bitcoin-cli")
    if not bd or not bc:
        print("Missing Bitcoin Core binaries on PATH.")
        print("Install on Debian/Ubuntu: sudo apt install bitcoind bitcoin-qt (or download binaries from bitcoin.org)")
        print("Or use your OS package manager / download prebuilt binaries.")

    if args.status:
        print("bitcoind:", bd)
        print("bitcoin-cli:", bc)
        print("running (datadir):", is_bitcoind_running(datadir))
        return

    if args.start:
        ok = start_bitcoind(datadir)
        print("Started bitcoind:" if ok else "Failed to start bitcoind")

    if args.generate_blocks > 0:
        print(f"Generating {args.generate_blocks} block(s) ...")
        res = generate_blocks(datadir, args.generate_blocks)
        print(res.get("stdout", ""))
        if res.get("stderr"):
            print(res.get("stderr"))

    if args.stop:
        ok = stop_bitcoind(datadir)
        print("Stopped bitcoind:" if ok else "Failed to stop bitcoind (or not running)")

    if args.inject_surface:
        inject_surface(datadir, args.rpc_endpoint)



if __name__ == "__main__":
    main()
