# Telemetry — QueryCache metrics

This document explains how to collect Prometheus-format metrics emitted by the
in-process `QueryCache` and the lightweight telemetry helper included in
NoDupeLabs.

Key points
- `QueryCache.export_metrics_prometheus()` emits counters and gauges in
  Prometheus text format.
- `nodupe.tools.telemetry` provides a tiny registry + `collect_metrics()` that
  aggregates metrics from registered `QueryCache` instances and adds a
  `cache="<name>"` label.

Usage

- Register a cache in your application:

```py
from nodupe.tools.databases.query_cache import QueryCache
from nodupe.tools.telemetry import register_query_cache

qc = QueryCache(max_size=100, ttl_seconds=3600)
register_query_cache("main-cache", qc)
```

- Collect metrics (programmatic):

```py
from nodupe.tools.telemetry import collect_metrics
print(collect_metrics())
```

- CLI (manual scrape):

```sh
python -m nodupe.tools.telemetry
```

Metric names

- `nodupe_query_cache_hits_total` (counter)
- `nodupe_query_cache_misses_total` (counter)
- `nodupe_query_cache_insertions_total` (counter)
- `nodupe_query_cache_evictions_total` (counter)
- `nodupe_query_cache_ttl_expiries_total` (counter)
- `nodupe_query_cache_size` (gauge)
- `nodupe_query_cache_capacity` (gauge)
- `nodupe_query_cache_hit_rate` (gauge)

All metrics emitted via `collect_metrics()` include a `cache` label so you
can run a single Prometheus scrape to capture multiple cache instances.

Example Prometheus line

nodupe_query_cache_hits_total{cache="main-cache"} 42

Testing

- Unit tests validate the Prometheus-format output and numeric values.
- Integration tests simulate cache hits/misses/TTL expiries and assert
  correctness of exported metrics.
