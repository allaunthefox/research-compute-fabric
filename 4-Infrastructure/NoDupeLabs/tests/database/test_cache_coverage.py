# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for DatabaseCache to achieve 100% coverage."""

from unittest.mock import MagicMock

import pytest

from nodupe.tools.databases.cache import DatabaseCache


class TestDatabaseCacheCoverage:
    """Test cases to achieve full coverage of DatabaseCache."""

    def test_cache_get_key_not_found(self):
        """Test get returns None when key doesn't exist."""
        mock_conn = MagicMock()
        cache = DatabaseCache(mock_conn)
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_get_expired(self):
        """Test get returns None when entry is expired."""
        mock_conn = MagicMock()
        cache = DatabaseCache(mock_conn, ttl=0.0)  # Immediate expiration
        
        # Directly set an entry with an old timestamp
        import time
        old_timestamp = time.time() - 1.0
        cache._cache["key1"] = ("value1", old_timestamp)
        
        result = cache.get("key1")
        assert result is None

    def test_cache_set_eviction(self):
        """Test cache evicts oldest entry when at capacity."""
        mock_conn = MagicMock()
        cache = DatabaseCache(mock_conn, max_size=2)
        
        # Add two entries
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Add third entry - should evict key1 (oldest)
        cache.set("key3", "value3")
        
        # key1 should be evicted (oldest)
        assert cache.get("key1") is None
        # key2 and key3 should still exist
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_cache_delete_existing(self):
        """Test delete removes existing key."""
        mock_conn = MagicMock()
        cache = DatabaseCache(mock_conn)
        cache.set("key1", "value1")
        
        result = cache.delete("key1")
        assert result is True
        assert cache.get("key1") is None

    def test_cache_delete_nonexisting(self):
        """Test delete returns False for nonexistent key."""
        mock_conn = MagicMock()
        cache = DatabaseCache(mock_conn)
        
        result = cache.delete("nonexistent")
        assert result is False

    def test_cache_size(self):
        """Test size returns correct count."""
        mock_conn = MagicMock()
        cache = DatabaseCache(mock_conn)
        
        assert cache.size() == 0
        cache.set("key1", "value1")
        assert cache.size() == 1
        cache.set("key2", "value2")
        assert cache.size() == 2
        cache.delete("key1")
        assert cache.size() == 1
