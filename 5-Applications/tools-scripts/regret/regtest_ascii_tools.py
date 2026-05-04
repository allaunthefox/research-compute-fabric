# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Small utilities reused by the regtest ASCII stager PoC."""
from typing import Iterable


def chunk_bytes(b: bytes, size: int) -> Iterable[bytes]:
    for i in range(0, len(b), size):
        yield b[i:i+size]


def join_chunks(hex_chunks: Iterable[str]) -> bytes:
    return bytes.fromhex("".join(hex_chunks))
