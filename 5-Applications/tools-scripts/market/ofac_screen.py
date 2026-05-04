#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""OFAC Sanctioned Address Screening Module.

Fail-closed address screening against a local SDN snapshot.
Designed to be called from the legal_omnitoken_action_bot front layer
or any execution surface before committing on-chain actions.

Usage:
    from scripts.ofac_screen import OFACScreen

    screen = OFACScreen()              # loads default 4-Infrastructure/config/ofac_sdn_snapshot.json
    result = screen.check("0xabc...")  # returns ScreenResult
    if result.blocked:
        # DO NOT EXECUTE — sanctioned address hit

Fail-Closed Behavior:
    - If the SDN snapshot is missing → ALL addresses are blocked
    - If the SDN snapshot is stale (>48h) → ALL addresses are blocked
    - If the address format is invalid → blocked (ambiguous = deny)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, cast

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SDN_PATH = ROOT / "config" / "ofac_sdn_snapshot.json"

# Maximum age of the SDN snapshot before fail-closed kicks in
MAX_STALENESS_HOURS = 48

# EVM address pattern (0x + 40 hex chars)
EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Solana base58 address pattern (32-44 chars, no 0/O/I/l)
SOLANA_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


@dataclass
class ScreenResult:
    """Result of an OFAC address screening check."""
    address: str
    blocked: bool
    reason: str
    matched_label: Optional[str] = None
    matched_program: Optional[str] = None
    snapshot_age_hours: Optional[float] = None
    fail_closed: bool = False


@dataclass
class OFACScreen:
    """Fail-closed OFAC sanctioned address screener.

    Loads a local SDN snapshot and checks addresses against it.
    If the snapshot is missing or stale, ALL addresses are blocked.
    """

    sdn_path: Path = DEFAULT_SDN_PATH
    _sanctioned_set: Set[str] = field(default_factory=set, repr=False)
    _address_labels: Dict[str, str] = field(default_factory=dict, repr=False)
    _snapshot_utc: Optional[datetime] = None
    _loaded: bool = False
    _load_error: Optional[str] = None

    def __post_init__(self) -> None:
        self._load_snapshot()

    def _load_snapshot(self) -> None:
        """Load and index the SDN snapshot. Fail-closed on error."""
        if not self.sdn_path.exists():
            self._load_error = f"SDN snapshot missing: {self.sdn_path}"
            return

        try:
            raw = json.loads(self.sdn_path.read_text(encoding="utf-8"))
            payload: Mapping[str, Any] = cast(Mapping[str, Any], raw) if isinstance(raw, dict) else {}

            # Parse generation timestamp
            gen_utc = payload.get("generated_utc", "")
            if gen_utc:
                self._snapshot_utc = datetime.fromisoformat(str(gen_utc).replace("Z", "+00:00"))

            # Index sanctioned addresses (normalized to lowercase)
            addresses_raw = payload.get("sanctioned_addresses", [])
            addresses = cast(List[Any], addresses_raw) if isinstance(addresses_raw, list) else []
            for entry in addresses:
                if not isinstance(entry, dict):
                    continue
                entry_map: Mapping[str, Any] = cast(Mapping[str, Any], entry)
                addr = str(entry_map.get("address", "")).strip().lower()
                label = str(entry_map.get("label", ""))
                if addr:
                    self._sanctioned_set.add(addr)
                    self._address_labels[addr] = label

            self._loaded = True

        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            self._load_error = f"SDN snapshot parse error: {exc}"

    def _snapshot_age_hours(self) -> Optional[float]:
        """How old the SDN snapshot is, in hours."""
        if not self._snapshot_utc:
            return None
        now = datetime.now(timezone.utc)
        delta = now - self._snapshot_utc
        return delta.total_seconds() / 3600.0

    def _is_stale(self) -> bool:
        """True if the snapshot is older than MAX_STALENESS_HOURS."""
        age = self._snapshot_age_hours()
        if age is None:
            return True  # no timestamp = stale
        return age > MAX_STALENESS_HOURS

    def _validate_address_format(self, address: str) -> bool:
        """Basic format validation for EVM or Solana addresses."""
        if EVM_ADDRESS_RE.match(address):
            return True
        if SOLANA_ADDRESS_RE.match(address):
            return True
        return False

    def check(self, address: str) -> ScreenResult:
        """Screen a single address against the SDN snapshot.

        Fail-closed: returns blocked=True if snapshot is missing, stale,
        or the address format is ambiguous.
        """
        normalized = address.strip().lower()
        age = self._snapshot_age_hours()

        # Fail-closed: snapshot not loaded
        if not self._loaded:
            return ScreenResult(
                address=address,
                blocked=True,
                reason=f"FAIL_CLOSED: {self._load_error}",
                snapshot_age_hours=age,
                fail_closed=True,
            )

        # Fail-closed: snapshot is stale
        if self._is_stale():
            return ScreenResult(
                address=address,
                blocked=True,
                reason=f"FAIL_CLOSED: SDN snapshot stale ({age:.1f}h > {MAX_STALENESS_HOURS}h)",
                snapshot_age_hours=age,
                fail_closed=True,
            )

        # Fail-closed: invalid address format
        if not self._validate_address_format(address):
            return ScreenResult(
                address=address,
                blocked=True,
                reason="FAIL_CLOSED: address format unrecognized (ambiguous = deny)",
                snapshot_age_hours=age,
                fail_closed=True,
            )

        # Direct match check
        if normalized in self._sanctioned_set:
            label = self._address_labels.get(normalized, "unknown")
            return ScreenResult(
                address=address,
                blocked=True,
                reason="SANCTIONED_ADDRESS_HIT",
                matched_label=label,
                snapshot_age_hours=age,
                fail_closed=False,
            )

        # Clear
        return ScreenResult(
            address=address,
            blocked=False,
            reason="CLEAR",
            snapshot_age_hours=age,
            fail_closed=False,
        )

    def check_batch(self, addresses: List[str]) -> List[ScreenResult]:
        """Screen multiple addresses. Stops early on first hit (fail-fast)."""
        results: List[ScreenResult] = []
        for addr in addresses:
            result = self.check(addr)
            results.append(result)
            if result.blocked:
                break  # fail-fast on first sanctioned hit
        return results

    def summary(self) -> Dict[str, Any]:
        """Return a summary of the screener state for logging."""
        return {
            "sdn_path": str(self.sdn_path),
            "loaded": self._loaded,
            "load_error": self._load_error,
            "snapshot_utc": self._snapshot_utc.isoformat() if self._snapshot_utc else None,
            "snapshot_age_hours": round(self._snapshot_age_hours() or 0, 2),
            "is_stale": self._is_stale(),
            "sanctioned_address_count": len(self._sanctioned_set),
            "fail_closed_active": not self._loaded or self._is_stale(),
        }


# ── CLI: standalone screening utility ────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="OFAC sanctioned address screener (fail-closed)")
    parser.add_argument("addresses", nargs="*", help="Addresses to screen")
    parser.add_argument("--sdn-path", default=str(DEFAULT_SDN_PATH), help="Path to SDN snapshot JSON")
    parser.add_argument("--status", action="store_true", help="Print screener status and exit")

    args = parser.parse_args()
    screen = OFACScreen(sdn_path=Path(args.sdn_path))

    if args.status:
        print(json.dumps(screen.summary(), indent=2))
        sys.exit(0)

    if not args.addresses:
        print("Usage: ofac_screen.py <address1> [address2] ...")
        print("       ofac_screen.py --status")
        sys.exit(1)

    any_blocked = False
    for addr in args.addresses:
        result = screen.check(addr)
        status_icon = "🚫 BLOCKED" if result.blocked else "✅ CLEAR"
        print(f"  {status_icon}  {result.address}  —  {result.reason}")
        if result.matched_label:
            print(f"           label: {result.matched_label}")
        if result.blocked:
            any_blocked = True

    sys.exit(1 if any_blocked else 0)
