# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/ml/embedding_cache.py - EmbeddingCache."""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.ml.embedding_cache import (
    EmbeddingCache,
    EmbeddingCacheError,
    create_embedding_cache,
)


class TestEmbeddingCacheInitialization:
    """Test EmbeddingCache initialization."""

    def test_default_initialization(self):
        """Test EmbeddingCache with default parameters."""
        cache = EmbeddingCache()
        
        assert cache.max_size == 1000
        assert cache.ttl_seconds == 3600
        assert cache.max_dimensions == 1024
        assert cache.get_cache_size() == 0

    def test_custom_initialization(self):
        """Test EmbeddingCache with custom parameters."""
        cache = EmbeddingCache(
            max_size=500,
            ttl_seconds=1800,
            max_dimensions=512
        )
        
        assert cache.max_size == 500
        assert cache.ttl_seconds == 1800
        assert cache.max_dimensions == 512

    def test_zero_max_size(self):
        """Test EmbeddingCache with zero max_size."""
        cache = EmbeddingCache(max_size=0)
        
        assert cache.max_size == 0

    def test_zero_ttl(self):
        """Test EmbeddingCache with zero TTL."""
        cache = EmbeddingCache(ttl_seconds=0)
        
        assert cache.ttl_seconds == 0


class TestEmbeddingCacheBasicOperations:
    """Test basic cache operations."""

    def test_set_and_get_embedding(self):
        """Test setting and getting embeddings."""
        cache = EmbeddingCache()
        embedding = [0.1, 0.2, 0.3, 0.4]
        
        cache.set_embedding("key1", embedding)
        result = cache.get_embedding("key1")
        
        assert result == embedding

    def test_get_nonexistent_key(self):
        """Test getting a non-existent key returns None."""
        cache = EmbeddingCache()
        
        result = cache.get_embedding("nonexistent")
        
        assert result is None

    def test_set_multiple_embeddings(self):
        """Test setting multiple embeddings."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 2.0])
        cache.set_embedding("key2", [3.0, 4.0])
        cache.set_embedding("key3", [5.0, 6.0])
        
        assert cache.get_cache_size() == 3
        assert cache.get_embedding("key1") == [1.0, 2.0]
        assert cache.get_embedding("key2") == [3.0, 4.0]
        assert cache.get_embedding("key3") == [5.0, 6.0]

    def test_update_existing_key(self):
        """Test updating an existing key."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 2.0])
        cache.set_embedding("key1", [3.0, 4.0])
        
        assert cache.get_embedding("key1") == [3.0, 4.0]
        assert cache.get_cache_size() == 1


class TestEmbeddingCacheEviction:
    """Test cache eviction policies."""

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = EmbeddingCache(max_size=2)
        
        cache.set_embedding("key1", [1.0])
        cache.set_embedding("key2", [2.0])
        cache.set_embedding("key3", [3.0])  # Should evict key1
        
        assert cache.get_embedding("key1") is None
        assert cache.get_embedding("key2") == [2.0]
        assert cache.get_embedding("key3") == [3.0]

    def test_max_size_zero_skipped(self):
        """Test cache with max_size=0 cannot store anything."""
        cache = EmbeddingCache(max_size=0)
        
        cache.set_embedding("key1", [1.0])
        
        assert cache.get_embedding("key1") is None
        assert cache.get_cache_size() == 0


class TestEmbeddingCacheTTL:
    """Test TTL functionality."""

    def test_expired_entry_returns_none(self):
        """Test that expired entries return None."""
        cache = EmbeddingCache(ttl_seconds=0)  # Immediate expiry
        
        cache.set_embedding("key1", [1.0, 2.0])
        time.sleep(0.01)  # Small delay to ensure expiration
        
        result = cache.get_embedding("key1")
        
        assert result is None

    def test_valid_entry_returns_value(self):
        """Test that valid entries return the correct value."""
        cache = EmbeddingCache(ttl_seconds=3600)
        
        cache.set_embedding("key1", [1.0, 2.0])
        
        result = cache.get_embedding("key1")
        
        assert result == [1.0, 2.0]


class TestEmbeddingCacheInvalidation:
    """Test cache invalidation."""

    def test_invalidate_existing_key(self):
        """Test invalidating an existing key."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 2.0])
        result = cache.invalidate("key1")
        
        assert result is True
        assert cache.get_embedding("key1") is None

    def test_invalidate_nonexistent_key(self):
        """Test invalidating a non-existent key returns False."""
        cache = EmbeddingCache()
        
        result = cache.invalidate("nonexistent")
        
        assert result is False

    def test_invalidate_all(self):
        """Test invalidating all entries."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0])
        cache.set_embedding("key2", [2.0])
        cache.set_embedding("key3", [3.0])
        
        cache.invalidate_all()
        
        assert cache.get_cache_size() == 0
        assert cache.get_embedding("key1") is None
        assert cache.get_embedding("key2") is None
        assert cache.get_embedding("key3") is None


class TestEmbeddingCacheValidation:
    """Test cache validation."""

    def test_validate_cache_removes_expired(self):
        """Test validate_cache removes expired entries."""
        cache = EmbeddingCache(ttl_seconds=0)
        
        cache.set_embedding("key1", [1.0])
        cache.set_embedding("key2", [2.0])
        
        time.sleep(0.01)
        
        removed = cache.validate_cache()
        
        assert removed == 2
        assert cache.get_cache_size() == 0

    def test_validate_cache_keeps_valid(self):
        """Test validate_cache keeps valid entries."""
        cache = EmbeddingCache(ttl_seconds=3600)
        
        cache.set_embedding("key1", [1.0])
        cache.set_embedding("key2", [2.0])
        
        removed = cache.validate_cache()
        
        assert removed == 0
        assert cache.get_cache_size() == 2


class TestEmbeddingCacheStats:
    """Test cache statistics."""

    def test_initial_stats(self):
        """Test initial statistics are zero."""
        cache = EmbeddingCache()
        stats = cache.get_stats()
        
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['evictions'] == 0
        assert stats['insertions'] == 0

    def test_stats_after_hit(self):
        """Test stats after a cache hit."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0])
        cache.get_embedding("key1")  # Hit
        
        stats = cache.get_stats()
        
        assert stats['hits'] == 1
        assert stats['misses'] == 0

    def test_stats_after_miss(self):
        """Test stats after a cache miss."""
        cache = EmbeddingCache()
        
        cache.get_embedding("nonexistent")  # Miss
        
        stats = cache.get_stats()
        
        assert stats['hits'] == 0
        assert stats['misses'] == 1

    def test_stats_after_insertion(self):
        """Test stats after insertions."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0])
        
        stats = cache.get_stats()
        
        assert stats['insertions'] == 1

    def test_stats_after_eviction(self):
        """Test stats after eviction."""
        cache = EmbeddingCache(max_size=1)
        
        cache.set_embedding("key1", [1.0])
        cache.set_embedding("key2", [2.0])  # Evicts key1
        
        stats = cache.get_stats()
        
        assert stats['evictions'] == 1

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0])
        cache.get_embedding("key1")  # Hit
        cache.get_embedding("key2")  # Miss
        
        stats = cache.get_stats()
        
        assert stats['hit_rate'] == 0.5

    def test_hit_rate_zero_when_no_requests(self):
        """Test hit rate is 0 when no requests made."""
        cache = EmbeddingCache()
        
        stats = cache.get_stats()
        
        assert stats['hit_rate'] == 0.0


class TestEmbeddingCacheResize:
    """Test cache resizing."""

    def test_resize_smaller(self):
        """Test resizing to a smaller size."""
        cache = EmbeddingCache(max_size=5)
        
        cache.set_embedding("key1", [1.0])
        cache.set_embedding("key2", [2.0])
        cache.set_embedding("key3", [3.0])
        
        cache.resize(2)
        
        assert cache.max_size == 2
        assert cache.get_cache_size() == 2

    def test_resize_larger(self):
        """Test resizing to a larger size."""
        cache = EmbeddingCache(max_size=2)
        
        cache.set_embedding("key1", [1.0])
        
        cache.resize(5)
        
        assert cache.max_size == 5
        assert cache.get_cache_size() == 1


class TestEmbeddingCacheMemoryUsage:
    """Test memory usage estimation."""

    def test_empty_cache_memory_usage(self):
        """Test memory usage of empty cache."""
        cache = EmbeddingCache()
        
        usage = cache.get_memory_usage()
        
        assert usage == 0

    def test_memory_usage_includes_key_and_embedding(self):
        """Test memory usage includes key and embedding data."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 2.0, 3.0])
        
        usage = cache.get_memory_usage()
        
        assert usage > 0


class TestEmbeddingCacheSimilarity:
    """Test similarity calculations."""

    def test_cosine_similarity_identical_vectors(self):
        """Test cosine similarity of identical vectors."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 0.0])
        
        similarity = cache.calculate_similarity("key1", "key1")
        
        assert similarity == 1.0

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 0.0])
        cache.set_embedding("key2", [0.0, 1.0])
        
        similarity = cache.calculate_similarity("key1", "key2")
        
        assert similarity == 0.0

    def test_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity of opposite vectors."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 0.0])
        cache.set_embedding("key2", [-1.0, 0.0])
        
        similarity = cache.calculate_similarity("key1", "key2")
        
        assert similarity == 0.0

    def test_cosine_similarity_with_missing_keys(self):
        """Test similarity calculation with missing keys."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 0.0])
        
        similarity = cache.calculate_similarity("key1", "nonexistent")
        
        assert similarity is None

    def test_find_similar(self):
        """Test finding similar embeddings."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 0.0])
        cache.set_embedding("key2", [0.9, 0.1])
        cache.set_embedding("key3", [0.1, 0.9])
        
        similar = cache.find_similar("key1", threshold=0.5, max_results=2)
        
        assert len(similar) <= 2
        # key2 should be similar to key1
        keys = [k for k, _ in similar]
        assert "key2" in keys

    def test_find_similar_no_match(self):
        """Test find similar with no matches."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 0.0])
        cache.set_embedding("key2", [-1.0, 0.0])
        
        similar = cache.find_similar("key1", threshold=0.9)
        
        assert len(similar) == 0


class TestEmbeddingCacheAverage:
    """Test average embedding calculation."""

    def test_get_average_embedding(self):
        """Test getting average of multiple embeddings."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 2.0])
        cache.set_embedding("key2", [3.0, 4.0])
        
        avg = cache.get_average_embedding(["key1", "key2"])
        
        assert avg == [2.0, 3.0]

    def test_get_average_embedding_with_missing(self):
        """Test average calculation with some missing keys."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0, 2.0])
        
        avg = cache.get_average_embedding(["key1", "nonexistent"])
        
        assert avg == [1.0, 2.0]

    def test_get_average_embedding_empty_keys(self):
        """Test average with empty key list."""
        cache = EmbeddingCache()
        
        avg = cache.get_average_embedding([])
        
        assert avg is None


class TestEmbeddingCachePatternMatching:
    """Test cache clearing by pattern."""

    def test_clear_by_pattern(self):
        """Test clearing entries by pattern."""
        cache = EmbeddingCache()
        
        cache.set_embedding("file_abc", [1.0])
        cache.set_embedding("file_def", [2.0])
        cache.set_embedding("image_xyz", [3.0])
        
        cleared = cache.clear_by_pattern("file_")
        
        assert cleared == 2
        assert cache.get_embedding("file_abc") is None
        assert cache.get_embedding("file_def") is None
        assert cache.get_embedding("image_xyz") == [3.0]

    def test_clear_by_pattern_case_insensitive(self):
        """Test clearing entries is case insensitive."""
        cache = EmbeddingCache()
        
        cache.set_embedding("FILE_abc", [1.0])
        
        cleared = cache.clear_by_pattern("file_")
        
        assert cleared == 1


class TestEmbeddingCacheIsCached:
    """Test is_cached method."""

    def test_is_cached_returns_true(self):
        """Test is_cached returns True for cached entry."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0])
        
        assert cache.is_cached("key1") is True

    def test_is_cached_returns_false(self):
        """Test is_cached returns False for non-cached entry."""
        cache = EmbeddingCache()
        
        assert cache.is_cached("nonexistent") is False


class TestEmbeddingCacheCleanupExpired:
    """Test cleanup_expired method."""

    def test_cleanup_expired(self):
        """Test cleanup_expired removes expired entries."""
        cache = EmbeddingCache(ttl_seconds=0)
        
        cache.set_embedding("key1", [1.0])
        cache.set_embedding("key2", [2.0])
        
        time.sleep(0.01)
        
        cleaned = cache.cleanup_expired()
        
        assert cleaned == 2


class TestEmbeddingCacheGetCachedKeys:
    """Test get_cached_keys method."""

    def test_get_cached_keys(self):
        """Test getting all cached keys."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0])
        cache.set_embedding("key2", [2.0])
        cache.set_embedding("key3", [3.0])
        
        keys = cache.get_cached_keys()
        
        assert set(keys) == {"key1", "key2", "key3"}


class TestEmbeddingCacheError:
    """Test EmbeddingCacheError exception."""

    def test_embedding_cache_error_raised(self):
        """Test EmbeddingCacheError is raised correctly."""
        cache = EmbeddingCache(max_dimensions=2)
        
        with pytest.raises(EmbeddingCacheError):
            cache.set_embedding("key1", [1.0, 2.0, 3.0])  # Exceeds max_dimensions


class TestEmbeddingCacheDimensionValidation:
    """Test dimension validation."""

    def test_validate_dimensions_exceed_max(self):
        """Test that exceeding max dimensions raises error."""
        cache = EmbeddingCache(max_dimensions=5)
        
        with pytest.raises(EmbeddingCacheError):
            cache.set_embedding("key1", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

    def test_validate_dimensions_at_max(self):
        """Test that dimensions at max are allowed."""
        cache = EmbeddingCache(max_dimensions=3)
        
        # Should not raise
        cache.set_embedding("key1", [1.0, 2.0, 3.0])
        
        assert cache.get_embedding("key1") == [1.0, 2.0, 3.0]


class TestCreateEmbeddingCache:
    """Test create_embedding_cache factory function."""

    def test_create_with_defaults(self):
        """Test create_embedding_cache with defaults."""
        cache = create_embedding_cache()
        
        assert cache.max_size == 1000
        assert cache.ttl_seconds == 3600
        assert cache.max_dimensions == 1024

    def test_create_with_custom_values(self):
        """Test create_embedding_cache with custom values."""
        cache = create_embedding_cache(
            max_size=2000,
            ttl_seconds=7200,
            max_dims=2048
        )
        
        assert cache.max_size == 2000
        assert cache.ttl_seconds == 7200
        assert cache.max_dimensions == 2048


class TestEmbeddingCacheThreadSafety:
    """Test thread safety of cache operations."""

    def test_concurrent_access(self):
        """Test concurrent access to cache."""
        cache = EmbeddingCache()
        
        def write_entries(start, count):
            """Write entries to cache for thread test."""
            for i in range(count):
                cache.set_embedding(f"key{start + i}", [float(i)])
        
        def read_entries(count):
            """Read entries from cache for thread test."""
            for i in range(count):
                cache.get_embedding(f"key{i}")
        
        threads = [
            threading.Thread(target=write_entries, args=(0, 50)),
            threading.Thread(target=write_entries, args=(50, 50)),
            threading.Thread(target=read_entries, args=(100,))
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # No errors should occur


class TestEmbeddingCacheEdgeCases:
    """Test edge cases."""

    def test_empty_embedding(self):
        """Test storing empty embedding."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [])
        
        assert cache.get_embedding("key1") == []

    def test_single_element_embedding(self):
        """Test storing single element embedding."""
        cache = EmbeddingCache()
        
        cache.set_embedding("key1", [1.0])
        
        assert cache.get_embedding("key1") == [1.0]

    def test_large_embedding(self):
        """Test storing large embedding."""
        cache = EmbeddingCache(max_dimensions=10000)
        large_embedding = list(range(1000))
        
        cache.set_embedding("key1", large_embedding)
        
        assert cache.get_embedding("key1") == large_embedding

    def test_very_long_key(self):
        """Test with very long key."""
        cache = EmbeddingCache()
        long_key = "key_" + "x" * 1000

        cache.set_embedding(long_key, [1.0])

        assert cache.get_embedding(long_key) == [1.0]

    def test_cosine_similarity_dimension_mismatch(self):
        """Test cosine similarity raises error for mismatched dimensions."""
        cache = EmbeddingCache()

        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]  # Different dimension

        with pytest.raises(EmbeddingCacheError):
            cache._cosine_similarity(vec1, vec2)

    def test_cosine_similarity_zero_magnitude(self):
        """Test cosine similarity returns 0 for zero magnitude vectors."""
        cache = EmbeddingCache()

        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]

        similarity = cache._cosine_similarity(vec1, vec2)

        assert similarity == 0.0

    def test_find_similar_no_reference(self):
        """Test find_similar returns empty list when reference not found."""
        cache = EmbeddingCache()

        cache.set_embedding("key1", [1.0, 2.0, 3.0])

        # Search for non-existent key
        results = cache.find_similar("nonexistent")

        assert results == []

    def test_average_embedding_empty_list(self):
        """Test get_average_embedding returns None for empty list."""
        cache = EmbeddingCache()

        result = cache.get_average_embedding([])

        assert result is None
