"""Lightweight telemetry collector for nodupe components.

This module provides a tiny registry to collect Prometheus-format metrics
exported by components that implement `export_metrics_prometheus(prefix, labels)`
(e.g. `QueryCache`).

Usage:
- Register QueryCache instances via `register_query_cache(name, qc)`
- Call `collect_metrics()` to return aggregated Prometheus text
- CLI: `python -m nodupe.tools.telemetry` prints metrics to stdout
"""
from __future__ import annotations

from threading import RLock
from typing import Dict

from nodupe.tools.databases.query_cache import QueryCache

_registry: Dict[str, QueryCache] = {}
_lock = RLock()


def register_query_cache(name: str, qc: QueryCache) -> None:
    """Register a QueryCache instance under a stable name."""
    with _lock:
        _registry[name] = qc


def unregister_query_cache(name: str) -> None:
    """Unregister a previously-registered QueryCache."""
    with _lock:
        _registry.pop(name, None)


def list_registered() -> Dict[str, QueryCache]:
    """Return a copy of the registry."""
    with _lock:
        return dict(_registry)


def collect_metrics(prefix: str = "nodupe_query_cache_") -> str:
    """Collect Prometheus metrics from all registered QueryCache instances.

    Each cache's metrics will be emitted with an additional label `cache="<name>"`.
    """
    parts = []
    with _lock:
        for name, qc in _registry.items():
            try:
                parts.append(qc.export_metrics_prometheus(prefix=prefix, labels={"cache": name}))
            except Exception:  # nosec B110
                # Do not allow one failing component to break metric collection
                parts.append(f"# error collecting metrics from {name}")

    return "\n\n".join(parts)


def main() -> int:
    """CLI entrypoint for manual metric collection."""
    print(collect_metrics())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
