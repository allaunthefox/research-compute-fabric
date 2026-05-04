# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on query_cache.py module.

This test file targets the missing coverage in:
- query_cache.py: QueryCache class methods
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.databases.query_cache import (
    QueryCache,
    QueryCacheError,
    create_query_cache,
)


class TestQueryCacheInit:
    """Tests for QueryCache initialization."""

    def test_init_default_values(self):
        """Test QueryCache with default values."""
        cache = QueryCache()
        assert cache.max_size == 1000
        assert cache.ttl_seconds == 3600

    def test_init_custom_values(self):
        """Test QueryCache with custom values."""
        cache = QueryCache(max_size=500, ttl_seconds=1800)
        assert cache.max_size == 500
        assert cache.ttl_seconds == 1800

    def test_init_stats_initialized(self):
        """Test stats are initialized correctly."""
        cache = QueryCache()
        stats = cache._stats

        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['evictions'] == 0
        assert stats['insertions'] == 0


class TestGetResult:
    """Tests for get_result method."""

    def test_get_result_miss(self):
        """Test get_result when not cached."""
        cache = QueryCache()
        result = cache.get_result("SELECT * FROM test")
        assert result is None

    def test_get_result_hit(self):
        """Test get_result when cached."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", result={"data": "value"})

        result = cache.get_result("SELECT * FROM test")
        assert result == {"data": "value"}

    def test_get_result_with_params(self):
        """Test get_result with parameters."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test WHERE id = ?", params={"id": 1}, result=[1])

        result = cache.get_result("SELECT * FROM test WHERE id = ?", params={"id": 1})
        assert result == [1]

    def test_get_result_params_mismatch(self):
        """Test get_result with different parameters."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", params={"id": 1}, result=[1])

        result = cache.get_result("SELECT * FROM test", params={"id": 2})
        assert result is None

    def test_get_result_expired(self):
        """Test get_result when entry is expired."""
        cache = QueryCache(ttl_seconds=1)

        # Manually add with old timestamp
        cache._cache["select * from test:none"] = ({"data": "value"}, time.monotonic() - 10)

        result = cache.get_result("SELECT * FROM test")
        assert result is None


class TestSetResult:
    """Tests for set_result method."""

    def test_set_result_basic(self):
        """Test basic set_result."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", result={"data": "value"})

        assert "select * from test:none" in cache._cache

    def test_set_result_with_params(self):
        """Test set_result with parameters."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", params={"id": 1}, result=[1])

        # Check that key is generated with params hash
        keys = list(cache._cache.keys())
        assert any("select * from test:" in k for k in keys)

    def test_set_result_updates_stats(self):
        """Test set_result updates insertion stats."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", result={"data": "value"})

        assert cache._stats['insertions'] == 1

    def test_set_result_eviction_when_full(self):
        """Test set_result evicts oldest when cache is full."""
        cache = QueryCache(max_size=2)

        cache.set_result("SELECT 1", result=1)
        cache.set_result("SELECT 2", result=2)
        cache.set_result("SELECT 3", result=3)

        assert len(cache._cache) == 2
        assert cache._stats['evictions'] == 1


class TestInvalidate:
    """Tests for invalidate method."""

    def test_invalidate_existing(self):
        """Test invalidating existing entry."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", result={"data": "value"})

        result = cache.invalidate("SELECT * FROM test")

        assert result is True
        assert "select * from test:none" not in cache._cache

    def test_invalidate_nonexisting(self):
        """Test invalidating non-existing entry."""
        cache = QueryCache()
        result = cache.invalidate("SELECT * FROM nonexistent")

        assert result is False


class TestInvalidateAll:
    """Tests for invalidate_all method."""

    def test_invalidate_all(self):
        """Test invalidating all entries."""
        cache = QueryCache()
        cache.set_result("SELECT 1", result=1)
        cache.set_result("SELECT 2", result=2)

        cache.invalidate_all()

        assert len(cache._cache) == 0
        assert cache._stats['evictions'] == 2


class TestInvalidateByPrefix:
    """Tests for invalidate_by_prefix method."""

    def test_invalidate_by_prefix(self):
        """Test invalidating by prefix."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM users", result=[1])
        cache.set_result("SELECT * FROM posts", result=[2])
        cache.set_result("SELECT * FROM comments", result=[3])

        count = cache.invalidate_by_prefix("select * from users")

        assert count == 1

    def test_invalidate_by_prefix_no_match(self):
        """Test invalidating by prefix with no match."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM users", result=[1])

        count = cache.invalidate_by_prefix("nonexistent")

        assert count == 0


class TestValidateCache:
    """Tests for validate_cache method."""

    def test_validate_cache_removes_expired(self):
        """Test validate_cache removes expired entries."""
        cache = QueryCache(ttl_seconds=1)

        # Manually add with old timestamp
        cache._cache["test:none"] = ({"data": "value"}, time.monotonic() - 10)

        removed = cache.validate_cache()

        assert removed == 1
        assert "test:none" not in cache._cache

    def test_validate_cache_none_expired(self):
        """Test validate_cache when no entries expired."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", result={"data": "value"})

        removed = cache.validate_cache()

        assert removed == 0


class TestGetStats:
    """Tests for get_stats method."""

    def test_get_stats_basic(self):
        """Test basic get_stats."""
        cache = QueryCache()
        stats = cache.get_stats()

        assert 'hits' in stats
        assert 'misses' in stats
        assert 'evictions' in stats
        assert 'insertions' in stats
        assert 'size' in stats
        assert 'capacity' in stats
        assert 'hit_rate' in stats

    def test_get_stats_with_hits(self):
        """Test get_stats with cache hits."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", result={"data": "value"})
        cache.get_result("SELECT * FROM test")  # Hit
        cache.get_result("SELECT * FROM test")  # Hit

        stats = cache.get_stats()
        assert stats['hits'] == 2
        assert stats['hit_rate'] == 1.0

    def test_get_stats_hit_rate_no_activity(self):
        """Test hit rate calculation with no activity."""
        cache = QueryCache()
        stats = cache.get_stats()

        assert stats['hit_rate'] == 0.0


class TestGetCacheSize:
    """Tests for get_cache_size method."""

    def test_get_cache_size_empty(self):
        """Test get_cache_size when empty."""
        cache = QueryCache()
        assert cache.get_cache_size() == 0

    def test_get_cache_size_with_entries(self):
        """Test get_cache_size with entries."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", result={"data": "value"})

        assert cache.get_cache_size() == 1


class TestIsCached:
    """Tests for is_cached method."""

    def test_is_cached_true(self):
        """Test is_cached when cached."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", result={"data": "value"})

        assert cache.is_cached("SELECT * FROM test") is True

    def test_is_cached_false(self):
        """Test is_cached when not cached."""
        cache = QueryCache()
        assert cache.is_cached("SELECT * FROM nonexistent") is False


class TestCleanupExpired:
    """Tests for cleanup_expired method."""

    def test_cleanup_expired(self):
        """Test cleanup_expired."""
        cache = QueryCache(ttl_seconds=1)

        # Manually add with old timestamp
        cache._cache["test:none"] = ({"data": "value"}, time.monotonic() - 10)

        removed = cache.cleanup_expired()

        assert removed == 1


class TestResize:
    """Tests for resize method."""

    def test_resize_smaller(self):
        """Test resizing to smaller size."""
        cache = QueryCache(max_size=10)
        cache.set_result("SELECT 1", result=1)
        cache.set_result("SELECT 2", result=2)

        cache.resize(1)

        assert cache.max_size == 1
        assert len(cache._cache) == 1

    def test_resize_larger(self):
        """Test resizing to larger size."""
        cache = QueryCache(max_size=2)
        cache.resize(10)
        assert cache.max_size == 10


class TestGetMemoryUsage:
    """Tests for get_memory_usage method."""

    def test_get_memory_usage_empty(self):
        """Test get_memory_usage when empty."""
        cache = QueryCache()
        usage = cache.get_memory_usage()
        assert usage == 0

    def test_get_memory_usage_with_entries(self):
        """Test get_memory_usage with entries."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM test", result={"data": "value"})

        usage = cache.get_memory_usage()
        assert usage > 0


class TestGenerateKey:
    """Tests for _generate_key method."""

    def test_generate_key_no_params(self):
        """Test _generate_key without params."""
        cache = QueryCache()
        key = cache._generate_key("SELECT * FROM test")

        assert "select * from test" in key
        assert "none" in key

    def test_generate_key_with_params(self):
        """Test _generate_key with params."""
        cache = QueryCache()
        key = cache._generate_key("SELECT * FROM test", params={"id": 1})

        assert "select * from test" in key

    def test_generate_key_normalizes_query(self):
        """Test _generate_key normalizes query."""
        cache = QueryCache()
        key1 = cache._generate_key("SELECT * FROM test")
        key2 = cache._generate_key("select * from test")

        assert key1 == key2

    def test_generate_key_with_different_params(self):
        """Test _generate_key with different params produces different keys."""
        cache = QueryCache()
        key1 = cache._generate_key("SELECT * FROM test", params={"id": 1})
        key2 = cache._generate_key("SELECT * FROM test", params={"id": 2})

        assert key1 != key2


class TestClearByQueryPattern:
    """Tests for clear_by_query_pattern method."""

    def test_clear_by_query_pattern(self):
        """Test clearing by query pattern."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM users", result=[1])
        cache.set_result("SELECT * FROM posts", result=[2])

        count = cache.clear_by_query_pattern("users")

        assert count == 1

    def test_clear_by_query_pattern_case_insensitive(self):
        """Test clearing by query pattern is case insensitive."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM users", result=[1])

        count = cache.clear_by_query_pattern("USERS")

        assert count == 1


class TestGetCachedQueries:
    """Tests for get_cached_queries method."""

    def test_get_cached_queries(self):
        """Test getting cached queries."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM users", result=[1])
        cache.set_result("SELECT * FROM posts", result=[2])

        queries = cache.get_cached_queries()

        assert len(queries) == 2

    def test_get_cached_queries_deduplicates(self):
        """Test get_cached_queries deduplicates."""
        cache = QueryCache()
        cache.set_result("SELECT * FROM users", params={"id": 1}, result=[1])
        cache.set_result("SELECT * FROM users", params={"id": 2}, result=[2])

        queries = cache.get_cached_queries()

        assert len(queries) == 1


class TestCreateQueryCache:
    """Tests for create_query_cache factory function."""

    def test_create_query_cache_default(self):
        """Test create_query_cache with defaults."""
        cache = create_query_cache()
        assert isinstance(cache, QueryCache)
        assert cache.max_size == 1000
        assert cache.ttl_seconds == 3600

    def test_create_query_cache_custom(self):
        """Test create_query_cache with custom values."""
        cache = create_query_cache(max_size=500, ttl_seconds=1800)
        assert cache.max_size == 500
        assert cache.ttl_seconds == 1800


class TestQueryCacheError:
    """Tests for QueryCacheError exception."""

    def test_query_cache_error_creation(self):
        """Test QueryCacheError can be created."""
        error = QueryCacheError("Test error")
        assert str(error) == "Test error"

    def test_query_cache_error_inheritance(self):
        """Test QueryCacheError inherits from Exception."""
        error = QueryCacheError("Test")
        assert isinstance(error, Exception)
