#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Compatibility shim for TSM harness access.

Import order:
1. real logic_signal_substrate_mcp_harness if present
2. CATEGORY/TSM harness if it imports cleanly
3. bounded local stub so scripts can still run in simulation mode
"""

from __future__ import annotations

import hashlib
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


HARNESS_SOURCE = "unknown"
HARNESS_IMPORT_ERROR: Optional[str] = None

try:
    from logic_signal_substrate_mcp_harness import TSMKernel, TermType  # type: ignore

    HARNESS_SOURCE = "logic_signal_substrate_mcp_harness"
except Exception as primary_error:  # pragma: no cover - import boundary
    try:
        from CATEGORY.TSM.tsm_mcp_harness import TSMKernel, TermType  # type: ignore

        HARNESS_SOURCE = "CATEGORY.TSM.tsm_mcp_harness"
    except Exception as secondary_error:  # pragma: no cover - import boundary
        HARNESS_IMPORT_ERROR = (
            f"primary={primary_error.__class__.__name__}: {primary_error}; "
            f"secondary={secondary_error.__class__.__name__}: {secondary_error}"
        )
        HARNESS_SOURCE = "compat_stub"

        class TermType(Enum):
            PERMANENT = "permanent"
            LEASE = "lease"
            TICKS = "ticks"
            LOCKED = "locked"

        class TSMKernel:
            """Bounded simulation surface used when no importable harness exists."""

            def __init__(self):
                self._sync_counter = 0

            def execute(self, opcodes: List[Tuple[str, List[Any]]]) -> List[Any]:
                results: List[Any] = []
                for opcode, args in opcodes:
                    if opcode == "0x03":
                        results.append(self.sync_precision())
                    elif opcode == "0x30":
                        pool_id = args[0] if args else "zpool"
                        results.append(f"Z-Pool {pool_id} initialized")
                    elif opcode == "0x31":
                        amount = float(args[0]) if args else 0.0
                        address = str(args[1]) if len(args) > 1 else "unknown"
                        results.append(
                            f"Shielded {amount:.6f} ZEC to {address[:16]}..."
                        )
                    elif opcode == "0x33":
                        state_id = str(args[1]) if len(args) > 1 else "unknown"
                        results.append(f"Viewing key bonded to {state_id[:16]}...")
                    elif opcode == "0x50":
                        receiver = str(args[0]) if args else "Orchard"
                        results.append(self._generate_unified_address(receiver))
                    elif opcode == "0xA2":
                        path = str(args[0]) if args else ""
                        if path == "/orders":
                            results.append(
                                {
                                    "success": False,
                                    "error_response": (
                                        "compat_stub does not place live orders"
                                    ),
                                }
                            )
                        else:
                            results.append(
                                {
                                    "success": True,
                                    "status": "simulated",
                                    "path": path,
                                }
                            )
                    elif opcode == "0xA3":
                        results.append(
                            {
                                "success": True,
                                "market": 25.0,
                                "source": "compat_stub",
                            }
                        )
                    else:
                        results.append(f"compat_stub unsupported opcode: {opcode}")
                return results

            async def execute_async(self, opcodes: List[Tuple[str, List[Any]]]) -> List[Any]:
                return self.execute(opcodes)

            def absorb_bh(self, data: str, metadata: Dict[str, Any] | None = None) -> str:
                payload = f"{data}|{metadata or {}}|{time.time()}".encode("utf-8")
                return hashlib.sha256(payload).hexdigest()

            def sync_precision(self) -> str:
                self._sync_counter += 1
                return f"precision_sync_stub_{self._sync_counter}"

            def omni_bal(self, mode: str | None = None) -> str:
                return f"omni_bal_stub:{mode or 'default'}"

            def stark_prove(self, payload: str, manifest: Dict[str, Any] | None = None) -> str:
                digest = hashlib.sha256(
                    f"{payload}|{manifest or {}}|{time.time()}".encode("utf-8")
                ).hexdigest()
                return digest

            def ledger_commit(self, state_id: str, term: TermType = TermType.LEASE) -> str:
                return f"ledger_commit_stub:{state_id[:16]}:{term.value}"

            def _generate_unified_address(self, receiver_type: str) -> str:
                digest = hashlib.sha256(
                    f"{receiver_type}|{time.time()}".encode("utf-8")
                ).hexdigest()
                prefix = "u1" if receiver_type == "Orchard" else "zs1"
                return f"{prefix}compat{digest[:24]}"
