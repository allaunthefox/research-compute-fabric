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
"""Watch regtest wallet balance and notify when USD threshold reached.

Usage:
  5-Applications/scripts/balance_watcher.py --datadir PATH --threshold-usd N [--btc-price P] [--once]

If `--btc-price` is omitted the script fetches the current BTC/USD price from
CoinGecko. On threshold reached it writes a notification JSON to
`5-Applications/out/bitcoind_regtest/notification_threshold.json` and updates
`5-Applications/out/omnitoken_bridge/egress_surface.json` under `surface_bus.domains.bitcoind_regtest`.
"""


import argparse
import json
# import subprocess (REMOVED BY WARDEN)
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


def run_cli(datadir: Path, *args):
    cmd = ["bitcoin-cli", "-regtest", f"-datadir={datadir}"] + list(args)
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"CLI failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()


def get_balance(datadir: Path) -> float:
    return float(run_cli(datadir, "getbalance"))


def fetch_btc_price_usd() -> float:
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    with urlopen(url, timeout=10) as r:
        data = json.load(r)
    return float(data["bitcoin"]["usd"])


def load_surface(surface_path: Path):
    try:
        return json.loads(surface_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_surface(surface_path: Path, surface: dict):
    surface_path.write_text(json.dumps(surface, indent=2) + "\n", encoding="utf-8")


def notify(datadir: Path, usd_value: float, threshold: float, surface_path: Path):
    out_dir = datadir.parent
    note = {
        "threshold_usd": threshold,
        "current_usd": usd_value,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    notif_path = out_dir / "notification_threshold.json"
    notif_path.write_text(json.dumps(note, indent=2) + "\n", encoding="utf-8")

    # patch surface if present
    surface = load_surface(surface_path)
    surface_bus = surface.get("surface_bus") or {}
    domains = surface_bus.get("domains") or {}
    dom = domains.get("bitcoind_regtest") or {}
    dom["last_notified_threshold_usd"] = threshold
    dom["last_notified_usd"] = usd_value
    dom["last_notified_utc"] = note["timestamp_utc"]
    domains["bitcoind_regtest"] = dom
    surface_bus["domains"] = domains
    surface["surface_bus"] = surface_bus
    surface["updated_utc"] = note["timestamp_utc"]
    try:
        save_surface(surface_path, surface)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datadir", required=True)
    ap.add_argument("--threshold-usd", type=float, required=True)
    ap.add_argument("--btc-price", type=float)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    datadir = Path(args.datadir)
    surface_path = Path("5-Applications/out/omnitoken_bridge/egress_surface.json")

    if args.btc_price is None:
        try:
            btc_price = fetch_btc_price_usd()
        except Exception as e:
            print(f"Failed to fetch BTC price: {e}", file=sys.stderr)
            return 2
    else:
        btc_price = float(args.btc_price)

    balance = get_balance(datadir)
    usd_value = balance * btc_price
    now = datetime.now(timezone.utc).isoformat()
    print(f"{now} Balance: {balance:.8f} BTC  Price: ${btc_price:.2f}  USD value: ${usd_value:,.2f}")

    if usd_value >= args.threshold_usd:
        print(f"Threshold {args.threshold_usd} USD reached (current ${usd_value:,.2f}) — notifying")
        try:
            notify(datadir, usd_value, args.threshold_usd, surface_path)
        except Exception as e:
            print(f"Notification failed: {e}", file=sys.stderr)
        return 0
    else:
        print(f"Threshold not reached: ${usd_value:,.2f} < ${args.threshold_usd:,.2f}")
        return 1



if __name__ == "__main__":
    sys.exit(main())
