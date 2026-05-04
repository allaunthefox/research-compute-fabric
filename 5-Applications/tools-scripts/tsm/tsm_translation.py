#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Bidirectional TSM translator for surface-safe domain exchange.

Design intent:
- Runtime can stay pure TSM internally.
- Surface artifacts never expose raw TSM internals.
- Translation is deterministic in both directions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Tuple, cast


TSM_VERSION = "v3.2-USAL"
ISA_VERSION = "ISA-v1"
SURFACE_TRANSLATION_VERSION = "surface-archive-translation/2"
FORBIDDEN_SURFACE_KEYS = {
    "absorbed_state",
    "manifold_id",
    "logic_signal_substrate_version",
}
FORBIDDEN_KEY_SUBSTRINGS = (
    "blob",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        raw = cast(Dict[Any, Any], value)
        out: Dict[str, Any] = {}
        for key, item in raw.items():
            out[str(key)] = item
        return out
    return {}


def _has_forbidden_key(key: str) -> bool:
    k = key.strip().lower()
    if k in FORBIDDEN_SURFACE_KEYS:
        return True
    return any(part in k for part in FORBIDDEN_KEY_SUBSTRINGS)


def _validate_surface_node(node: Any, path: Tuple[str, ...]) -> None:
    if isinstance(node, dict):
        raw = cast(Dict[Any, Any], node)
        for key, value in raw.items():
            key_str = str(key)
            if _has_forbidden_key(key_str):
                dotted = ".".join(path + (key_str,)) if path else key_str
                raise ValueError(f"fail_closed_surface_gate: forbidden key '{key_str}' at '{dotted}'")
            _validate_surface_node(value, path + (key_str,))
        return
    if isinstance(node, list):
        items = cast(list[Any], node)
        for i, item in enumerate(items):
            _validate_surface_node(item, path + (f"[{i}]",))


def assert_surface_write_safe(payload: Dict[str, Any], scope: str = "surface") -> None:
    """Fail-closed guard for outbound surface/profile payloads.

    Rejects any leaked TSM internals or absorbed blobs before writes.
    """
    _validate_surface_node(payload, (scope,))


def logic_signal_substrate_from_archive_domain(archive_domain: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize archive domain into internal USAL-TSM form.

    This structure is intended for internal USAL-bound compute only.
    """
    mode = str(archive_domain.get("selected_mode") or archive_domain.get("auto_winner_mode") or "unknown")
    
    # In v3.2+, we return a USAL-aligned skeleton
    return {
        "logic_signal_substrate_version": TSM_VERSION,
        "isa_version": ISA_VERSION,
        "kind": "archive_compression",
        "state": {
            "policy": str(archive_domain.get("selection_policy") or "auto_smallest_compressed_bytes"),
            "mode": mode,
            "payload_format": str(archive_domain.get("payload_format") or "unknown"),
            "compressed_bytes": int(archive_domain.get("compressed_bytes") or 0),
            "raw_bytes": int(archive_domain.get("raw_bytes") or 0),
        },
        "lineage": {
            "manifest_path": str(archive_domain.get("manifest_path") or ""),
            "updated_utc": str(archive_domain.get("updated_utc") or _utc_now()),
        },
        "substrate_transparency": "ENABLED"
    }


def surface_from_logic_signal_substrate(logic_signal_substrate_state: Dict[str, Any]) -> Dict[str, Any]:
    """Emit sanitized surface-safe representation from TSM state.

    Drops internal TSM fields by design to avoid leaking TSM.
    """
    state = _as_dict(logic_signal_substrate_state.get("state"))
    lineage = _as_dict(logic_signal_substrate_state.get("lineage"))

    return {
        "domain": "archive_compression",
        "selection_policy": str(state.get("policy") or "auto_smallest_compressed_bytes"),
        "selected_mode": str(state.get("mode") or "unknown"),
        "payload_format": str(state.get("payload_format") or "unknown"),
        "compressed_bytes": int(state.get("compressed_bytes") or 0),
        "raw_bytes": int(state.get("raw_bytes") or 0),
        "manifest_path": str(lineage.get("manifest_path") or ""),
        "updated_utc": str(lineage.get("updated_utc") or _utc_now()),
        "translation": {
            "version": SURFACE_TRANSLATION_VERSION,
            "logic_signal_substrate_exposed": False,
        },
    }


def logic_signal_substrate_from_surface(surface_domain: Dict[str, Any]) -> Dict[str, Any]:
    """Rehydrate internal TSM from sanitized surface representation."""
    return {
        "logic_signal_substrate_version": TSM_VERSION,
        "kind": "archive_compression",
        "state": {
            "policy": str(surface_domain.get("selection_policy") or "auto_smallest_compressed_bytes"),
            "mode": str(surface_domain.get("selected_mode") or "unknown"),
            "payload_format": str(surface_domain.get("payload_format") or "unknown"),
            "compressed_bytes": int(surface_domain.get("compressed_bytes") or 0),
            "raw_bytes": int(surface_domain.get("raw_bytes") or 0),
        },
        "lineage": {
            "manifest_path": str(surface_domain.get("manifest_path") or ""),
            "updated_utc": str(surface_domain.get("updated_utc") or _utc_now()),
        },
        "internals": {},
    }
