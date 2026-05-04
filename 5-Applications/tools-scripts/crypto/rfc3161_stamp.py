# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
"""RFC 3161 timestamp utility for the attestation pipeline.

Requests a notarized timestamp from FreeTSA for any file and saves
the response as <file>.tsr alongside it.  Both attestation scripts
call stamp() after writing their output JSON.

Verify later with:
    openssl ts -verify -in <file>.tsr -data <file> \
        -CAfile 5-Applications/scripts/freetsa_chain.pem
"""
# import subprocess (REMOVED BY WARDEN)
import urllib.request
from pathlib import Path
from typing import Dict

_CHAIN = Path(__file__).parent / "freetsa_chain.pem"
_TSA_URL = "https://freetsa.org/tsr"


def stamp(out_path: Path, tsa_url: str = _TSA_URL) -> Dict[str, str]:
    """Request an RFC 3161 timestamp for *out_path*.

    Writes <out_path>.tsr next to the target file.
    Returns a dict with timestamp_utc, serial, tsr_path, and verify_cmd.
    Raises RuntimeError if openssl or the TSA request fails.
    """
    out_path = Path(out_path)
    tsq_path = out_path.with_suffix(".tsq")
    tsr_path = out_path.with_suffix(".tsr")

    # Generate timestamp request
    result = subprocess.run(
        ["openssl", "ts", "-query", "-data", str(out_path),
         "-no_nonce", "-sha256", "-cert", "-out", str(tsq_path)],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"openssl ts -query failed: {result.stderr.decode()}")

    # POST to TSA
    try:
        req = urllib.request.Request(
            tsa_url,
            data=tsq_path.read_bytes(),
            headers={"Content-Type": "application/timestamp-query"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            tsr_path.write_bytes(resp.read())
    finally:
        tsq_path.unlink(missing_ok=True)

    # Extract human-readable metadata
    meta = subprocess.run(
        ["openssl", "ts", "-reply", "-in", str(tsr_path), "-text"],
        capture_output=True, text=True,
    )
    info: Dict[str, str] = {"tsr_path": str(tsr_path), "tsa_url": tsa_url}
    for line in meta.stdout.splitlines():
        if "Time stamp:" in line:
            info["timestamp_utc"] = line.split("Time stamp:")[-1].strip()
        elif "Serial number:" in line:
            info["serial"] = line.split("Serial number:")[-1].strip()
        elif "Policy OID:" in line:
            info["policy_oid"] = line.split("Policy OID:")[-1].strip()

    info["verify_cmd"] = (
        f"openssl ts -verify -in {tsr_path} -data {out_path} "
        f"-CAfile {_CHAIN}"
    )
    return info


def verify(out_path: Path) -> bool:
    """Quick verify — returns True if the .tsr next to *out_path* is valid."""
    tsr_path = Path(out_path).with_suffix(".tsr")
    if not tsr_path.exists():
        return False
    result = subprocess.run(
        ["openssl", "ts", "-verify", "-in", str(tsr_path),
         "-data", str(out_path), "-CAfile", str(_CHAIN)],
        capture_output=True,
    )
    return result.returncode == 0
