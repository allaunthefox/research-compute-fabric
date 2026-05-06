# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on hash_cache.py module.

This test file targets the missing coverage in:
- hash_cache.py: HashCache class methods
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.hashing.hash_cache import (
    HashCache,
    HashCacheError,
    create_hash_cache,
)


class TestHashCacheInit:
    """Tests for HashCache initialization."""

    def test_init_default_values(self):
        """Test HashCache with default values."""
        cache = HashCache()
        assert cache.max_size == 1000
        assert cache.ttl_seconds == 3600
        assert cache.enable_persistence is False

    def test_init_custom_values(self):
        """Test HashCache with custom values."""
        cache = HashCache(max_size=500, ttl_seconds=1800, enable_persistence=True)
        assert cache.max_size == 500
        assert cache.ttl_seconds == 1800
        assert cache.enable_persistence is True

    def test_init_stats_initialized(self):
        """Test stats are initialized correctly."""
        cache = HashCache()
        stats = cache._stats

        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['evictions'] == 0
        assert stats['insertions'] == 0


class TestGetHash:
    """Tests for get_hash method."""

    def test_get_hash_miss(self):
        """Test get_hash when not cached."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        mock_path.__str__ = MagicMock(return_value="/test/path")

        result = cache.get_hash(mock_path)
        assert result is None

    def test_get_hash_hit(self):
        """Test get_hash when cached."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        # Manually add to cache
        cache._cache[path_str] = ("hash_value", 1000.0, time.monotonic())

        result = cache.get_hash(mock_path)
        assert result == "hash_value"

    def test_get_hash_expired(self):
        """Test get_hash when entry is expired."""
        cache = HashCache(ttl_seconds=1)
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        # Add to cache with old timestamp
        old_timestamp = time.monotonic() - 10  # 10 seconds ago
        cache._cache[path_str] = ("hash_value", 1000.0, old_timestamp)

        result = cache.get_hash(mock_path)
        assert result is None

    def test_get_hash_file_modified(self):
        """Test get_hash when file has been modified."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        # Current mtime differs from stored mtime
        mock_path.stat.return_value.st_mtime = 2000.0

        # Add to cache with old mtime
        cache._cache[path_str] = ("hash_value", 1000.0, time.monotonic())

        result = cache.get_hash(mock_path)
        assert result is None

    def test_get_hash_file_not_found(self):
        """Test get_hash when file no longer exists."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.side_effect = OSError("File not found")

        # Add to cache
        cache._cache[path_str] = ("hash_value", 1000.0, time.monotonic())

        result = cache.get_hash(mock_path)
        assert result is None


class TestSetHash:
    """Tests for set_hash method."""

    def test_set_hash_basic(self):
        """Test basic set_hash."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        cache.set_hash(mock_path, "hash_value")

        assert path_str in cache._cache
        assert cache._cache[path_str][0] == "hash_value"

    def test_set_hash_updates_stats(self):
        """Test set_hash updates insertion stats."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        cache.set_hash(mock_path, "hash_value")

        assert cache._stats['insertions'] == 1

    def test_set_hash_eviction_when_full(self):
        """Test set_hash evicts oldest when cache is full."""
        cache = HashCache(max_size=2)
        mock_path1 = MagicMock(spec=Path)
        mock_path1.__str__ = MagicMock(return_value="/path1")
        mock_path1.stat.return_value.st_mtime = 1000.0

        mock_path2 = MagicMock(spec=Path)
        mock_path2.__str__ = MagicMock(return_value="/path2")
        mock_path2.stat.return_value.st_mtime = 1000.0

        mock_path3 = MagicMock(spec=Path)
        mock_path3.__str__ = MagicMock(return_value="/path3")
        mock_path3.stat.return_value.st_mtime = 1000.0

        cache.set_hash(mock_path1, "hash1")
        cache.set_hash(mock_path2, "hash2")
        cache.set_hash(mock_path3, "hash3")

        assert len(cache._cache) == 2
        assert cache._stats['evictions'] == 1

    def test_set_hash_nonexistent_file(self):
        """Test set_hash with non-existent file."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        mock_path.stat.side_effect = OSError("File not found")

        cache.set_hash(mock_path, "hash_value")

        assert len(cache._cache) == 0


class TestInvalidate:
    """Tests for invalidate method."""

    def test_invalidate_existing(self):
        """Test invalidating existing entry."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        cache.set_hash(mock_path, "hash_value")
        result = cache.invalidate(mock_path)

        assert result is True
        assert path_str not in cache._cache

    def test_invalidate_nonexisting(self):
        """Test invalidating non-existing entry."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)

        result = cache.invalidate(mock_path)

        assert result is False


class TestInvalidateAll:
    """Tests for invalidate_all method."""

    def test_invalidate_all(self):
        """Test invalidating all entries."""
        cache = HashCache(max_size=10)
        mock_path1 = MagicMock(spec=Path)
        mock_path1.__str__ = MagicMock(return_value="/path1")
        mock_path1.stat.return_value.st_mtime = 1000.0

        mock_path2 = MagicMock(spec=Path)
        mock_path2.__str__ = MagicMock(return_value="/path2")
        mock_path2.stat.return_value.st_mtime = 1000.0

        cache.set_hash(mock_path1, "hash1")
        cache.set_hash(mock_path2, "hash2")

        cache.invalidate_all()

        assert len(cache._cache) == 0
        assert cache._stats['evictions'] == 2


class TestValidateCache:
    """Tests for validate_cache method."""

    def test_validate_cache_removes_expired(self):
        """Test validate_cache removes expired entries."""
        cache = HashCache(ttl_seconds=1)
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        # Add with old timestamp
        old_timestamp = time.monotonic() - 10
        cache._cache[path_str] = ("hash_value", 1000.0, old_timestamp)

        removed = cache.validate_cache()

        assert removed == 1
        assert path_str not in cache._cache

    def test_validate_cache_removes_modified(self):
        """Test validate_cache removes entries with modified files."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 2000.0  # Different from stored

        cache._cache[path_str] = ("hash_value", 1000.0, time.monotonic())

        removed = cache.validate_cache()

        assert removed == 1

    def test_validate_cache_removes_missing_files(self):
        """Test validate_cache removes entries for missing files."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.side_effect = OSError("File not found")

        cache._cache[path_str] = ("hash_value", 1000.0, time.monotonic())

        removed = cache.validate_cache()

        assert removed == 1


class TestGetStats:
    """Tests for get_stats method."""

    def test_get_stats_basic(self):
        """Test basic get_stats."""
        cache = HashCache()
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
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        cache.set_hash(mock_path, "hash_value")
        cache.get_hash(mock_path)  # Hit
        cache.get_hash(mock_path)  # Hit

        stats = cache.get_stats()
        assert stats['hits'] == 2
        assert stats['hit_rate'] == 1.0

    def test_get_stats_hit_rate_no_hits_or_misses(self):
        """Test hit rate calculation with no activity."""
        cache = HashCache()
        stats = cache.get_stats()

        assert stats['hit_rate'] == 0.0


class TestGetCacheSize:
    """Tests for get_cache_size method."""

    def test_get_cache_size_empty(self):
        """Test get_cache_size when empty."""
        cache = HashCache()
        assert cache.get_cache_size() == 0

    def test_get_cache_size_with_entries(self):
        """Test get_cache_size with entries."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        cache.set_hash(mock_path, "hash_value")
        assert cache.get_cache_size() == 1


class TestIsCached:
    """Tests for is_cached method."""

    def test_is_cached_true(self):
        """Test is_cached when cached."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        cache.set_hash(mock_path, "hash_value")
        assert cache.is_cached(mock_path) is True

    def test_is_cached_false(self):
        """Test is_cached when not cached."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)

        assert cache.is_cached(mock_path) is False


class TestCleanupExpired:
    """Tests for cleanup_expired method."""

    def test_cleanup_expired(self):
        """Test cleanup_expired."""
        cache = HashCache(ttl_seconds=1)
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        old_timestamp = time.monotonic() - 10
        cache._cache[path_str] = ("hash_value", 1000.0, old_timestamp)

        removed = cache.cleanup_expired()

        assert removed == 1


class TestResize:
    """Tests for resize method."""

    def test_resize_smaller(self):
        """Test resizing to smaller size."""
        cache = HashCache(max_size=10)
        mock_path1 = MagicMock(spec=Path)
        mock_path1.__str__ = MagicMock(return_value="/path1")
        mock_path1.stat.return_value.st_mtime = 1000.0

        mock_path2 = MagicMock(spec=Path)
        mock_path2.__str__ = MagicMock(return_value="/path2")
        mock_path2.stat.return_value.st_mtime = 1000.0

        cache.set_hash(mock_path1, "hash1")
        cache.set_hash(mock_path2, "hash2")

        cache.resize(1)

        assert cache.max_size == 1
        assert len(cache._cache) == 1

    def test_resize_larger(self):
        """Test resizing to larger size."""
        cache = HashCache(max_size=2)
        cache.resize(10)
        assert cache.max_size == 10


class TestGetMemoryUsage:
    """Tests for get_memory_usage method."""

    def test_get_memory_usage_empty(self):
        """Test get_memory_usage when empty."""
        cache = HashCache()
        usage = cache.get_memory_usage()
        assert usage == 0

    def test_get_memory_usage_with_entries(self):
        """Test get_memory_usage with entries."""
        cache = HashCache()
        mock_path = MagicMock(spec=Path)
        path_str = "/test/path"
        mock_path.__str__ = MagicMock(return_value=path_str)
        mock_path.stat.return_value.st_mtime = 1000.0

        cache.set_hash(mock_path, "hash_value")

        usage = cache.get_memory_usage()
        assert usage > 0


class TestCreateHashCache:
    """Tests for create_hash_cache factory function."""

    def test_create_hash_cache_default(self):
        """Test create_hash_cache with defaults."""
        cache = create_hash_cache()
        assert isinstance(cache, HashCache)
        assert cache.max_size == 1000
        assert cache.ttl_seconds == 3600

    def test_create_hash_cache_custom(self):
        """Test create_hash_cache with custom values."""
        cache = create_hash_cache(max_size=500, ttl_seconds=1800)
        assert cache.max_size == 500
        assert cache.ttl_seconds == 1800


class TestHashCacheError:
    """Tests for HashCacheError exception."""

    def test_hash_cache_error_creation(self):
        """Test HashCacheError can be created."""
        error = HashCacheError("Test error")
        assert str(error) == "Test error"

    def test_hash_cache_error_inheritance(self):
        """Test HashCacheError inherits from Exception."""
        error = HashCacheError("Test")
        assert isinstance(error, Exception)
