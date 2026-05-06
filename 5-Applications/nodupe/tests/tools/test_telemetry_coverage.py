"""Test Telemetry Module - Coverage Completion.

Tests to achieve 100% coverage for nodupe/tools/telemetry.py
"""

import importlib
from unittest.mock import MagicMock, patch

import pytest


class TestTelemetryFunctions:
    """Test telemetry module functions."""

    def setup_method(self):
        """Reset the registry before each test."""
        # Force reload the module to ensure clean state
        import nodupe.tools.telemetry as telemetry
        importlib.reload(telemetry)

    def teardown_method(self):
        """Clean up after each test."""
        import nodupe.tools.telemetry as telemetry
        telemetry._registry.clear()

    def test_register_query_cache(self):
        """Test registering a QueryCache instance."""
        from nodupe.tools import telemetry

        mock_cache = MagicMock()
        mock_cache.export_metrics_prometheus = MagicMock(return_value="# metrics")

        telemetry.register_query_cache("test_cache", mock_cache)

        registered = telemetry.list_registered()
        assert "test_cache" in registered
        assert registered["test_cache"] == mock_cache

    def test_register_query_cache_overwrites(self):
        """Test that registering with same name overwrites."""
        from nodupe.tools import telemetry

        mock_cache1 = MagicMock()
        mock_cache2 = MagicMock()

        telemetry.register_query_cache("test_cache", mock_cache1)
        telemetry.register_query_cache("test_cache", mock_cache2)

        registered = telemetry.list_registered()
        assert registered["test_cache"] == mock_cache2

    def test_unregister_query_cache(self):
        """Test unregistering a QueryCache."""
        from nodupe.tools import telemetry

        mock_cache = MagicMock()
        telemetry.register_query_cache("test_cache", mock_cache)
        telemetry.unregister_query_cache("test_cache")

        registered = telemetry.list_registered()
        assert "test_cache" not in registered

    def test_unregister_query_cache_nonexistent(self):
        """Test unregistering non-existent cache doesn't error."""
        from nodupe.tools import telemetry

        # Should not raise
        telemetry.unregister_query_cache("nonexistent")

    def test_list_registered_empty(self):
        """Test listing when nothing is registered."""
        from nodupe.tools import telemetry

        registered = telemetry.list_registered()
        assert registered == {}

    def test_list_registered_returns_copy(self):
        """Test that list_registered returns a copy, not the original."""
        from nodupe.tools import telemetry

        mock_cache = MagicMock()
        telemetry.register_query_cache("test_cache", mock_cache)

        registered = telemetry.list_registered()
        registered["test_cache"] = None  # Modify the copy

        # Original should be unchanged
        assert telemetry.list_registered()["test_cache"] == mock_cache

    def test_collect_metrics_empty(self):
        """Test collecting metrics when nothing is registered."""
        from nodupe.tools import telemetry

        result = telemetry.collect_metrics()
        assert result == ""

    def test_collect_metrics_single_cache(self):
        """Test collecting metrics from single cache."""
        from nodupe.tools import telemetry

        mock_cache = MagicMock()
        mock_cache.export_metrics_prometheus.return_value = "cache_hits_total 100"

        telemetry.register_query_cache("test_cache", mock_cache)

        result = telemetry.collect_metrics()
        assert "cache_hits_total" in result
        mock_cache.export_metrics_prometheus.assert_called_once()

    def test_collect_metrics_multiple_caches(self):
        """Test collecting metrics from multiple caches."""
        from nodupe.tools import telemetry

        mock_cache1 = MagicMock()
        mock_cache1.export_metrics_prometheus.return_value = "cache_hits 50"

        mock_cache2 = MagicMock()
        mock_cache2.export_metrics_prometheus.return_value = "cache_misses 25"

        telemetry.register_query_cache("cache1", mock_cache1)
        telemetry.register_query_cache("cache2", mock_cache2)

        result = telemetry.collect_metrics()
        assert "cache_hits" in result
        assert "cache_misses" in result

    def test_collect_metrics_default_prefix(self):
        """Test collecting metrics with default prefix."""
        from nodupe.tools import telemetry

        mock_cache = MagicMock()
        mock_cache.export_metrics_prometheus.return_value = "nodupe_query_cache_hits 100"

        telemetry.register_query_cache("test_cache", mock_cache)

        # Verify it was called with default prefix
        telemetry.collect_metrics()
        mock_cache.export_metrics_prometheus.assert_called_once()
        call_kwargs = mock_cache.export_metrics_prometheus.call_args
        assert call_kwargs.kwargs.get("prefix") == "nodupe_query_cache_"

    def test_collect_metrics_cache_error(self):
        """Test that cache error doesn't break metric collection."""
        from nodupe.tools import telemetry

        mock_cache1 = MagicMock()
        mock_cache1.export_metrics_prometheus.return_value = "metrics1 100"

        mock_cache2 = MagicMock()
        mock_cache2.export_metrics_prometheus.side_effect = RuntimeError("Cache error")

        telemetry.register_query_cache("working_cache", mock_cache1)
        telemetry.register_query_cache("failing_cache", mock_cache2)

        result = telemetry.collect_metrics()
        assert "metrics1" in result
        assert "error collecting metrics from failing_cache" in result

    def test_collect_metrics_includes_cache_label(self):
        """Test that cache name is included as label."""
        from nodupe.tools import telemetry

        mock_cache = MagicMock()
        mock_cache.export_metrics_prometheus.return_value = "metrics 100"

        telemetry.register_query_cache("my_cache", mock_cache)

        # Call collect to trigger the method
        telemetry.collect_metrics()

        mock_cache.export_metrics_prometheus.assert_called_once()
        call_kwargs = mock_cache.export_metrics_prometheus.call_args
        assert call_kwargs.kwargs.get("labels", {}).get("cache") == "my_cache"

    def test_main_function(self):
        """Test the main CLI function."""
        from nodupe.tools import telemetry

        mock_cache = MagicMock()
        mock_cache.export_metrics_prometheus.return_value = "# metrics"

        telemetry.register_query_cache("test", mock_cache)

        with patch('nodupe.tools.telemetry.print') as mock_print:
            result = telemetry.main()
            assert result == 0
            mock_print.assert_called_once()


class TestTelemetryModule:
    """Test telemetry module as a whole."""

    def setup_method(self):
        """Reset the registry before each test."""
        import nodupe.tools.telemetry as telemetry
        importlib.reload(telemetry)

    def teardown_method(self):
        """Clean up after each test."""
        import nodupe.tools.telemetry as telemetry
        telemetry._registry.clear()

    def test_telemetry_module_exports(self):
        """Test that module has expected exports."""
        from nodupe.tools import telemetry

        assert hasattr(telemetry, 'register_query_cache')
        assert hasattr(telemetry, 'unregister_query_cache')
        assert hasattr(telemetry, 'list_registered')
        assert hasattr(telemetry, 'collect_metrics')
        assert hasattr(telemetry, 'main')

    def test_main_returns_zero_on_success(self):
        """Test that main returns 0 on success."""
        from nodupe.tools import telemetry

        mock_cache = MagicMock()
        mock_cache.export_metrics_prometheus.return_value = ""

        telemetry.register_query_cache("test", mock_cache)

        with patch('nodupe.tools.telemetry.print'):
            result = telemetry.main()
            assert result == 0
