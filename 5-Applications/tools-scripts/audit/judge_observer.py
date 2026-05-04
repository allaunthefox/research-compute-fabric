#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Judge Observer — passive witness to organism trials across the tailnet.

Polls each node via omnitoken transport (self-assembling, transport-agnostic).
Appends observations to a JSONL log. No intervention. Pure observation.

Nodes watched:
  - racknerd-atl:8446  homeostasis dashboard (compression organism)
  - racknerd-atl:8443  attestation witness
  - racknerd-atl:8449  warden metrics
  - architect:8447     warden metrics
"""

import json
import time
import hashlib
import os
import sys
from datetime import datetime, timezone

# Add parent dir to path for omni_resolver import
sys.path.insert(0, os.path.expanduser("~/omni_stack"))

try:
    import omni_resolver
except ImportError:
    omni_resolver = None

LOG_PATH = os.path.expanduser("~/omni_stack/organism_trials.jsonl")
INTERVAL  = 60  # seconds between observation rounds

# Omnitoken URIs — transport-agnostic, self-assembling across any network
ENDPOINTS = [
    {"node": "racknerd-atl", "role": "homeostasis",   "omni": "omni://racknerd:8446/stats"},
    {"node": "racknerd-atl", "role": "attestation",   "omni": "omni://racknerd:8443/status"},
    {"node": "racknerd-atl", "role": "warden",        "omni": "omni://racknerd:8449/metrics"},
    {"node": "architect",    "role": "warden",        "omni": "omni://warden:8447/metrics"},
]

_last_hash = ""
_tick = 0


def _fetch_omni(omni_uri: str, timeout: float = 5.0):
    """Fetch via omnitoken transport — self-assembles across UDP/TCP/Tailscale."""
    if omni_resolver is None:
        return None, "omni_resolver not available"
    try:
        result = omni_resolver.omni_request(omni_uri)
        if result is None:
            return None, "null response"
        return result, None
    except Exception as e:
        return None, str(e)


def observe():
    global _last_hash, _tick
    _tick += 1
    ts = datetime.now(timezone.utc).isoformat()

    snapshot = {"tick": _tick, "timestamp": ts, "observations": []}

    for ep in ENDPOINTS:
        data, err = _fetch_omni(ep["omni"])
        obs = {
            "node": ep["node"],
            "role": ep["role"],
            "omni": ep["omni"],
            "status": "ok" if data is not None else "unreachable",
        }
        if data is not None:
            obs["data"] = data
        if err:
            obs["error"] = err
        snapshot["observations"].append(obs)

    # Hash chain
    entry_str = json.dumps({k: v for k, v in snapshot.items() if k != "hash"}, sort_keys=True)
    snapshot["parent"] = _last_hash
    snapshot["hash"] = hashlib.sha256((_last_hash + entry_str).encode()).hexdigest()
    _last_hash = snapshot["hash"]

    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

    reachable = sum(1 for o in snapshot["observations"] if o["status"] == "ok")
    print(f"[judge] tick={_tick} ts={ts} reachable={reachable}/{len(ENDPOINTS)} hash={snapshot['hash'][:12]}...")


def main():
    print(f"[judge] observer starting — log={LOG_PATH} interval={INTERVAL}s")
    print(f"[judge] watching {len(ENDPOINTS)} omni endpoints across {len(set(e['node'] for e in ENDPOINTS))} nodes")
    print(f"[judge] transport: omnitoken (self-assembling across UDP/TCP/Tailscale)")

    # Load last hash from existing log if present
    global _last_hash, _tick
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            for line in f:
                try:
                    e = json.loads(line)
                    _last_hash = e.get("hash", _last_hash)
                    _tick = e.get("tick", _tick)
                except Exception:
                    pass
        print(f"[judge] resumed from tick={_tick} hash={_last_hash[:12]}...")

    while True:
        try:
            observe()
        except Exception as e:
            print(f"[judge] observe error: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
