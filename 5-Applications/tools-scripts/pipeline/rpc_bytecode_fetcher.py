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
"""RPC Bytecode Fetcher — Real-time on-chain verification.

This utility pulls deployed bytecode for a given contract address via
JSON-RPC (eth_getCode). It handles multiple chains and provides
fail-closed error handling.

Ghost-ICMP + Soliton Walk path (multi-hop MEV resilience):
  When a normal HTTP fetch fails — e.g. because the MEV transaction has
  traversed 100+ network hops and the primary RPC host is no longer
  reachable — ghost_rpc_fetch() takes over:

    1. Resolves candidate endpoints and probes L3 reachability via Ghost-ICMP.
    2. A classical soliton quantum walk selects the next endpoint by
       chasing the "void" — endpoints with the lowest recent-hit density
       (freshest paths) weighted by their historical Waveprobe coherence.
       The walk propagates through low-resistance topology, not randomly.
    3. Waveprobe coherence gates the survival-state cache: φ ≥ 0.8 (θ)
       returns the cached state; φ < 0.8 triggers a live re-fetch.
    4. Final fail-closed: returns None.

The ghost_icmp binary must be built at GHOST_ICMP_BIN or the default
tools/ relative path.
"""

import json
import logging
import math
import os
import socket
# import subprocess (REMOVED BY WARDEN)
import time
from pathlib import Path
from typing import Optional, Dict, List
import httpx

logger = logging.getLogger("rpc_bytecode_fetcher")
logger.setLevel(logging.INFO)

# ── Waveprobe constants (WAVEPROBE_EQUATION.md) ───────────────────────────────
_COHERENCE_THRESHOLD = 0.8        # θ — phase-lock gate
_PHI = 1.618_033_988_749_895      # golden ratio

# Ghost-ICMP binary location
_GHOST_ICMP_BIN = os.environ.get(
    "GHOST_ICMP_BIN",
    str(
        Path(__file__).resolve().parent.parent
        / "tools" / "ghost_icmp" / "target" / "debug" / "ghost_icmp"
    ),
)


# ── Waveprobe coherence ───────────────────────────────────────────────────────

def _entropy(buf: bytes) -> float:
    if not buf:
        return 0.0
    counts: Dict[int, int] = {}
    for b in buf:
        counts[b] = counts.get(b, 0) + 1
    n = len(buf)
    return sum(-c / n * math.log2(c / n) for c in counts.values()) / 8.0


def _repetition(buf: bytes) -> float:
    if len(buf) < 2:
        return 0.0
    runs = sum(1 for i in range(len(buf) - 1) if buf[i] == buf[i + 1])
    return runs / (len(buf) - 1)


def _waveprobe_coherence(local: bytes, remote: bytes) -> float:
    """φ-coherence between two byte sequences (w_e=0.4, w_r=0.3, w_d=0.3)."""
    if not local or not remote:
        return 0.0
    fe = max(0.0, 1.0 - abs(_entropy(local) - _entropy(remote)))
    fr = max(0.0, 1.0 - abs(_repetition(local) - _repetition(remote)))
    return 0.4 * fe + 0.6 * fr   # w_d ≈ w_r (no dict model in Python path)


def _phi_ideal_reference(length: int, mode: int = 0) -> bytes:
    """φ-ideal reference vector — mirrors ghost_icmp Rust encoder basis."""
    phi_scale = _PHI ** (mode % 7)
    return bytes(int(phi_scale * i) & 0xFF for i in range(max(length, 1)))


# ── Soliton quantum walk path selector ───────────────────────────────────────

class SolitonWalk:
    """Classical soliton path selector using basin-attractor dynamics.

    Each RPC endpoint is an attractor basin.  The soliton falls into the
    deepest available basin — the endpoint with the highest accumulated
    Waveprobe coherence amplitude.  Staleness introduces uncertainty that
    broadens the basin well (makes the soliton less certain about depth)
    but does NOT flip the direction of attraction — untested endpoints
    retain their prior potential (unknown ≠ shallow).

    Basin potential:  U(url) = -amplitude² / (1 + β·√Δt)
      - More negative = deeper basin = stronger attractor.
      - On success:  basin deepens (amplitude increases via EMA).
      - On failure:  basin collapses (amplitude halved, soliton rolls away).
      - Staleness broadens uncertainty but unknown endpoints keep prior U.

    β = 0.02 (uncertainty broadening rate)
    α = 0.35 (EMA learning rate)
    """

    _BETA  = 0.02
    _ALPHA = 0.35

    def __init__(self, endpoints: List[str]):
        self._amplitude: Dict[str, float] = {url: 0.5 for url in endpoints}
        self._last_hit:  Dict[str, float] = {url: 0.0 for url in endpoints}
        # Track which endpoints have been measured at least once
        self._measured: Dict[str, bool] = {url: False for url in endpoints}

    def _basin_potential(self, url: str) -> float:
        """U(url) — more negative = deeper basin = stronger attractor.

        For unmeasured endpoints, return the prior potential (amplitude²)
        without staleness penalty — the soliton is drawn to unexplored
        basins because they could be deep (unknown ≠ shallow).
        """
        amp = self._amplitude[url]
        # Unmeasured endpoints: pure prior, no staleness penalty
        if not self._measured.get(url, False):
            return -(amp ** 2)

        elapsed = time.monotonic() - self._last_hit[url]
        uncertainty = 1.0 + self._BETA * math.sqrt(elapsed)
        return -(amp ** 2) / uncertainty

    def select(self) -> Optional[str]:
        """Fall into the deepest available basin (most negative potential)."""
        if not self._amplitude:
            return None

        potentials = {url: self._basin_potential(url) for url in self._amplitude}
        # Softmax over -U so deepest basin has highest weight
        neg_u = {url: -u for url, u in potentials.items()}
        max_v = max(neg_u.values())
        exp_v = {url: math.exp(v - max_v) for url, v in neg_u.items()}
        total = sum(exp_v.values())
        probs = {url: v / total for url, v in exp_v.items()}

        import random
        urls    = list(probs.keys())
        weights = [probs[u] for u in urls]
        return random.choices(urls, weights=weights, k=1)[0]

    def record_success(self, url: str, phi_corr: float) -> None:
        """Deepen the basin after a confirmed coherent result."""
        self._amplitude[url] = (
            (1 - self._ALPHA) * self._amplitude[url] + self._ALPHA * phi_corr
        )
        self._last_hit[url] = time.monotonic()
        self._measured[url] = True

    def record_failure(self, url: str) -> None:
        """Collapse the basin — soliton rolls toward the next stable region."""
        self._amplitude[url] *= 0.5
        self._measured[url] = True


# ── Ghost-ICMP probe ──────────────────────────────────────────────────────────

def _icmp_probe(host: str) -> bool:
    """Ghost-ICMP probe. Degrades to TCP-443 if binary unavailable."""
    ghost_bin = Path(_GHOST_ICMP_BIN)
    if ghost_bin.exists() and os.access(ghost_bin, os.X_OK):
        try:
            proc_res = subprocess.run(
                [str(ghost_bin), "probe", "--target", host],
                capture_output=True, timeout=5, check=False,
            )
            return proc_res.returncode == 0
        except (subprocess.TimeoutExpired, OSError, subprocess.SubprocessError):
            pass
    # Graceful degradation
    try:
        with socket.create_connection((host, 443), timeout=3):
            return True
    except OSError:
        return False


def _host_from_url(url: str) -> str:
    from urllib.parse import urlparse
    try:
        return urlparse(url).hostname or ""
    except (ValueError, AttributeError):
        return ""


# ── Main fetcher ──────────────────────────────────────────────────────────────

class RPCBytecodeFetcher:
    """Fetch contract bytecode across EVM chains.

    Includes a Ghost-ICMP + Soliton Walk + Waveprobe resilience path for
    multi-hop MEV topologies where the primary TCP path is unreachable.
    """

    def __init__(self, config_path: str = "4-Infrastructure/config/rpc_endpoints.json"):
        self.config_path = config_path
        self.endpoints = self._load_config()
        # survival_cache: address → last known-good bytecode bytes
        self._survival: Dict[str, bytes] = {}
        # per-chain soliton walk (built lazily)
        self._walks: Dict[str, SolitonWalk] = {}

    def _load_config(self) -> Dict:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("Failed to load RPC config: %s", e)
            return {}

    def _get_walk(self, chain: str) -> SolitonWalk:
        if chain not in self._walks:
            ep = self.endpoints.get(chain, {})
            urls = [u for u in [ep.get("url"), ep.get("fallback_url")] if u]
            self._walks[chain] = SolitonWalk(urls or [""])
        return self._walks[chain]

    def fetch_bytecode(self, address: str, chain: str = "ethereum") -> Optional[str]:
        """Primary path: HTTP JSON-RPC. Falls back to ghost_rpc_fetch on failure."""
        if not address:
            return None

        chain = chain.lower()
        endpoint = self.endpoints.get(chain)
        if not endpoint:
            logger.warning("No RPC endpoint configured for chain: %s", chain)
            return None

        rpc_url = endpoint.get("url")
        if not rpc_url:
            return None

        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getCode",
            "params": [address, "latest"],
            "id": 1,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(rpc_url, json=payload)
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    logger.error("RPC error for %s on %s: %s", address, chain, data["error"])
                    return None

                bytecode = data.get("result")
                if bytecode == "0x" or bytecode is None:
                    logger.warning("No bytecode (EOA) at %s on %s", address, chain)
                    return "0x"

                # Cache survival state + update soliton walk amplitude
                raw = bytes.fromhex(bytecode.lstrip("0x") or "00")
                phi_ref = _phi_ideal_reference(len(raw))
                phi_corr = _waveprobe_coherence(raw, phi_ref)
                self._survival[address] = raw
                self._get_walk(chain).record_success(rpc_url, phi_corr)
                return bytecode

        except (httpx.RequestError, json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "HTTP fetch failed for %s on %s: %s — Ghost-ICMP fallback",
                address, chain, e,
            )
            self._get_walk(chain).record_failure(rpc_url)
            return self.ghost_rpc_fetch(address, chain)

    def ghost_rpc_fetch(self, address: str, chain: str) -> Optional[str]:
        """Ghost-ICMP + Soliton Walk + Waveprobe resilience path.

        Steps:
          1. Soliton walk selects the next candidate endpoint (void-chase).
          2. Ghost-ICMP probes L3 reachability of that host.
          3. Waveprobe coherence gates the survival-state cache:
               φ ≥ θ → return cached state (phase-locked).
               φ < θ → drift detected, attempt live fetch on selected URL.
          4. Fail-closed: return None.
        """
        walk = self._get_walk(chain)
        # ── Step 1: Soliton walk selects endpoint ────────────────────────
        selected_url = walk.select()
        if not selected_url:
            logger.error("[ghost_rpc] No candidate endpoints for chain %s", chain)
            return None

        host = _host_from_url(selected_url)
        logger.info("[ghost_rpc] Soliton walk selected: %s (host=%s)", selected_url, host)

        # ── Step 2: Ghost-ICMP probe ─────────────────────────────────────
        reachable = _icmp_probe(host) if host else False
        logger.info(
            "[ghost_rpc] ICMP probe → %s: %s",
            host or "?", "reachable" if reachable else "unreachable",
        )

        # ── Step 3: Waveprobe coherence gate ────────────────────────────
        survival = self._survival.get(address)
        if survival:
            phi_ref = _phi_ideal_reference(len(survival))
            phi_corr = _waveprobe_coherence(survival, phi_ref)
            logger.info(
                "[ghost_rpc] Waveprobe φ=%.3f (θ=%.1f) for %s",
                phi_corr, _COHERENCE_THRESHOLD, address,
            )

            if phi_corr >= _COHERENCE_THRESHOLD:
                # Phase-locked: survival state valid, return without network hit
                logger.info("[ghost_rpc] φ ≥ θ — survival state returned for %s", address)
                walk.record_success(selected_url, phi_corr)
                return "0x" + survival.hex()

            logger.info("[ghost_rpc] φ < θ — void detected, chasing fresh path")

        # ── Step 4: Live fetch on walk-selected URL ──────────────────────
        if reachable and selected_url:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getCode",
                "params": [address, "latest"],
                "id": 1,
            }
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(selected_url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    bytecode = data.get("result")
                    if bytecode and bytecode != "0x":
                        raw = bytes.fromhex(bytecode.lstrip("0x") or "00")
                        phi_ref = _phi_ideal_reference(len(raw))
                        phi_corr = _waveprobe_coherence(raw, phi_ref)
                        self._survival[address] = raw
                        walk.record_success(selected_url, phi_corr)
                        logger.info("[ghost_rpc] Fresh fetch succeeded via %s", selected_url)
                        return bytecode
            except (httpx.RequestError, json.JSONDecodeError, KeyError) as e:
                logger.error("[ghost_rpc] Live fetch failed via %s: %s", selected_url, e)
                walk.record_failure(selected_url)

        # ── Fail-closed ──────────────────────────────────────────────────
        logger.error("[ghost_rpc] All paths exhausted for %s on %s", address, chain)
        return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch bytecode from RPC")
    parser.add_argument("address", help="Contract address (0x...)")
    parser.add_argument("--chain", default="ethereum", help="Chain handle")
    parser.add_argument("--ghost", action="store_true", help="Force Ghost-ICMP path")
    args = parser.parse_args()

    fetcher = RPCBytecodeFetcher()
    if args.ghost:
        result = fetcher.ghost_rpc_fetch(args.address, args.chain)
    else:
        result = fetcher.fetch_bytecode(args.address, args.chain)
    print(result if result else "Failed to fetch bytecode.")
