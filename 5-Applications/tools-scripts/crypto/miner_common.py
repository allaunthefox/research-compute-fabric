# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# Common utilities for neuromorphic miner benchmark/proof scripts.
# Extracted to avoid duplication between benchmark_uplift.py and
# final_proof_uplift.py.
from __future__ import annotations

import hashlib
import os
import struct
import sys
import time

# Ensure sibling modules in 5-Applications/scripts/ are importable.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Block header template (Bitcoin-style, 80 bytes, all-zero for benchmarking).
HEADER_BASE = bytes.fromhex(
    "00000020" + "00" * 64 + "00" * 32 + "00000000" + "ffff001d" + "00000000"
)
