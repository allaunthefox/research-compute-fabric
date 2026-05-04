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
"""
5-Applications/scripts/at_get.py — Academic Torrents automatic downloader

Downloads datasets and paper corpora by infohash via aria2c.
Uses the AT REST API for metadata, aria2c for actual transfer.

Requires:
    sudo pacman -S aria2          # or: apt install aria2

Usage:
    python3 5-Applications/scripts/at_get.py enwik9              # named corpus
    python3 5-Applications/scripts/at_get.py <40-char infohash>  # by hash
    python3 5-Applications/scripts/at_get.py --info <infohash>   # metadata only
    python3 5-Applications/scripts/at_get.py --list              # show known corpora

Known corpus hashes are in CORPUS_REGISTRY below.
Add new entries as you discover them; mark unverified ones with ? prefix in notes.

AT API:
    GET https://academictorrents.com/apiv2/entry/<INFOHASH>
    No search API exists — lookup is hash-only.
    Browse: https://academictorrents.com/browse.php?q=<query>  (manual)
"""

import argparse
import json
import os
import pathlib
import re
import shutil
# import subprocess (REMOVED BY WARDEN)
import sys
import urllib.request
from typing import Optional

# ── known corpus registry ─────────────────────────────────────────────────────
# Populate as hashes are manually confirmed via AT browse.
# Format: name → {"hash": "...", "desc": "...", "size_gb": float, "verified": bool}
CORPUS_REGISTRY: dict[str, dict] = {
    "enwik9": {
        "hash":      "e7d78d128db80266830e64c0142a67d0c5413ced",
        "desc":      "enwik9 — 10^9 bytes of Wikipedia XML (Hutter Prize benchmark)",
        "size_gb":   1.0,
        "verified":  True,
    },
    "enwik8": {
        "hash":      "8e8c34c9f27a54b2c2cca9a2f2d8f8c9a3e1b2c3",  # NEEDS VERIFICATION
        "desc":      "enwik8 — 10^8 bytes of Wikipedia XML",
        "size_gb":   0.1,
        "verified":  False,
    },
    "arxiv-fulltext-2024": {
        "hash":      "",  # populate after manual browse
        "desc":      "arXiv full-text bulk dump 2024 (via AT)",
        "size_gb":   None,
        "verified":  False,
    },
}

AT_API   = "https://academictorrents.com/apiv2/entry/{hash}?uid={uid}&pass={passkey}"
AT_UA    = "research-stack/1.0 (academic; at_get.py)"
OUT_DIR  = pathlib.Path("5-Applications/out/at_downloads")

# AT account: https://academictorrents.com/register.php
# Set env vars to enable metadata lookup:
#   export AT_UID=<your numeric uid>
#   export AT_PASS=<your passkey from profile page>
_AT_UID  = os.getenv("AT_UID", "")
_AT_PASS = os.getenv("AT_PASS", "")

# Trackers added to every magnet link — improves peer discovery
_TRACKERS = [
    "udp://tracker.academictorrents.com:6969",
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.tracker.cl:1337/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
]

# ── AT API ────────────────────────────────────────────────────────────────────

def at_info(infohash: str) -> dict:
    """Fetch metadata for infohash from AT REST API.

    Requires AT_UID + AT_PASS env vars (free account at academictorrents.com).
    Returns {"_error": "..."} when unauthenticated or hash not found.
    Download still works without this — metadata is optional.
    """
    if not _AT_UID:
        return {"_error": "AT_UID/AT_PASS not set — set env vars for metadata (optional)"}
    url = AT_API.format(hash=infohash.lower(), uid=_AT_UID, passkey=_AT_PASS)
    req = urllib.request.Request(url, headers={"User-Agent": AT_UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as exc:
        return {"_error": str(exc)}


def magnet(infohash: str, name: str = "") -> str:
    h = infohash.lower()
    m = f"magnet:?xt=urn:btih:{h}"
    if name:
        m += f"&dn={urllib.request.quote(name)}"
    for tr in _TRACKERS:
        m += f"&tr={urllib.request.quote(tr)}"
    return m


# ── download via aria2c ───────────────────────────────────────────────────────

def _check_aria2c() -> str:
    """Return path to aria2c or raise with install instructions."""
    path = shutil.which("aria2c")
    if path:
        return path
    print("[at_get] aria2c not found.")
    print("  Install: sudo pacman -S aria2    # CachyOS / Arch")
    print("           sudo apt install aria2  # Debian / Ubuntu")
    sys.exit(1)


def at_download(
    infohash: str,
    output_dir: pathlib.Path = OUT_DIR,
    seed_time: int = 0,
    connections: int = 4,
    name: str = "",
) -> pathlib.Path:
    """Download infohash via aria2c.  Returns output_dir when done."""
    aria2c = _check_aria2c()
    output_dir.mkdir(parents=True, exist_ok=True)

    mag = magnet(infohash, name)
    cmd = [
        aria2c,
        "--dir", str(output_dir),
        "--max-connection-per-server", str(connections),
        "--seed-time", str(seed_time),       # 0 = stop seeding after download
        "--console-log-level", "notice",
        "--summary-interval", "10",
        mag,
    ]

    print(f"[at_get] downloading {infohash[:12]}... → {output_dir}")
    print(f"[at_get] magnet: {mag[:80]}...")

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"[at_get] aria2c exited {result.returncode}")
        sys.exit(result.returncode)

    print(f"[at_get] done → {output_dir}")
    return output_dir


# ── entry point helpers ───────────────────────────────────────────────────────

def _resolve(name_or_hash: str) -> tuple[str, str]:
    """Return (infohash, name).  Accepts registry name or raw 40-char hash."""
    if re.fullmatch(r"[0-9a-fA-F]{40}", name_or_hash):
        return name_or_hash, name_or_hash[:12]
    entry = CORPUS_REGISTRY.get(name_or_hash.lower())
    if not entry:
        print(f"[at_get] unknown name '{name_or_hash}'. Use --list to see registry.")
        sys.exit(1)
    if not entry["hash"]:
        print(f"[at_get] '{name_or_hash}' has no hash yet — populate CORPUS_REGISTRY manually.")
        print(f"          Browse: https://academictorrents.com/browse.php?q={name_or_hash}")
        sys.exit(1)
    if not entry["verified"]:
        print(f"[at_get] WARNING: hash for '{name_or_hash}' is UNVERIFIED — confirm at AT before relying on it.")
    return entry["hash"], name_or_hash


def at_get(name_or_hash: str, output_dir: pathlib.Path = OUT_DIR) -> pathlib.Path:
    """Convenience: resolve name/hash → download → return output_dir."""
    infohash, name = _resolve(name_or_hash)
    info = at_info(infohash)
    if "_error" not in info:
        print(f"[at_get] AT metadata: {info.get('name', '?')} ({info.get('size', '?')} bytes)")
    else:
        print(f"[at_get] AT metadata unavailable ({info['_error']}), proceeding with magnet")
    return at_download(infohash, output_dir, name=name)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="Corpus name or 40-char infohash")
    ap.add_argument("--info",  metavar="HASH", help="Fetch AT metadata only (no download)")
    ap.add_argument("--list",  action="store_true", help="List known corpora")
    ap.add_argument("--out",   default=str(OUT_DIR), help=f"Output directory (default: {OUT_DIR})")
    args = ap.parse_args()

    if args.list:
        print("Known corpora in CORPUS_REGISTRY:")
        for name, entry in CORPUS_REGISTRY.items():
            v = "✓" if entry["verified"] else "?"
            h = entry["hash"][:12] + "..." if entry["hash"] else "(no hash)"
            print(f"  {v}  {name:<24} {h}  {entry['desc']}")
        return

    if args.info:
        info = at_info(args.info)
        print(json.dumps(info, indent=2))
        return

    if not args.target:
        ap.print_help()
        sys.exit(1)

    at_get(args.target, pathlib.Path(args.out))



if __name__ == "__main__":
    main()
