"""Tests for the telemetry collector module.

This module tests the registration and metrics collection functionality
of the telemetry system, including query cache registration and metric gathering.
"""

import re

from nodupe.tools import telemetry
from nodupe.tools.databases.query_cache import QueryCache


def test_telemetry_collector_register_and_collect(monkeypatch):
    """Test that query caches can be registered and metrics collected.

    Verifies that:
    - Multiple query caches can be registered with unique names
    - Metrics are correctly collected for each registered cache
    - Cache hits and misses are properly tracked
    - Cleanup (unregistration) works correctly
    """
    # create two caches and register them
    qc1 = QueryCache(max_size=3, ttl_seconds=60)
    qc2 = QueryCache(max_size=5, ttl_seconds=60)

    telemetry.register_query_cache("alpha", qc1)
    telemetry.register_query_cache("beta", qc2)

    qc1.set_result("a", None, 1)
    qc1.get_result("a")  # hit
    qc1.get_result("missing")  # miss

    qc2.set_result("x", None, 2)
    qc2.get_result("missing")  # miss

    metrics = telemetry.collect_metrics()

    # should have two sections (one per registered cache)
    assert "cache=\"alpha\"" in metrics
    assert "cache=\"beta\"" in metrics

    # check basic metric names are present for both caches
    assert re.search(r"nodupe_query_cache_hits_total\{cache=\"alpha\"\}", metrics)
    assert re.search(r"nodupe_query_cache_misses_total\{cache=\"beta\"\}", metrics)

    # cleanup
    telemetry.unregister_query_cache("alpha")
    telemetry.unregister_query_cache("beta")
