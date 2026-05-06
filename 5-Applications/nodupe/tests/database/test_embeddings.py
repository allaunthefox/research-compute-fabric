# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Comprehensive tests for embedding storage and queries.

Tests cover:
- Embedding storage and retrieval
- Vector operations and queries
- Similarity search functionality
- Batch operations
- Model version management
- Error handling
- Schema validation (including dimensions column bug fix)
"""

import os
import pickle
import sqlite3

import numpy as np
import pytest

from nodupe.tools.databases.embeddings import EmbeddingRepository, get_embedding_repository

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database connection."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    # Create minimal schema for embeddings
    conn.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            embedding BLOB NOT NULL,
            model_version TEXT NOT NULL,
            created_time INTEGER NOT NULL,
            dimensions INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def db_connection(in_memory_db):
    """Create a DatabaseConnection wrapper for in-memory DB."""
    # Create a mock-like wrapper that uses our in-memory connection
    class TestDBConnection:
        """Test database connection wrapper for embeddings tests."""
        def __init__(self, conn):
            """Initialize test DB connection.

            Args:
                conn: SQLite connection object.
            """
            self._conn = conn
            self.db_path = ":memory:"

        def get_connection(self):
            """Get database connection.

            Returns:
                SQLite connection object.
            """
            return self._conn

        def execute(self, query, params=None):
            """Execute a query.

            Args:
                query: SQL query string.
                params: Query parameters (optional).

            Returns:
                Cursor object.
            """
            if params:
                return self._conn.execute(query, params)
            return self._conn.execute(query)

        def executemany(self, query, params_list):
            """Execute multiple queries.

            Args:
                query: SQL query string.
                params_list: List of parameter tuples.

            Returns:
                Cursor object.
            """
            return self._conn.executemany(query, params_list)

        def commit(self):
            """Commit transaction."""
            self._conn.commit()

        def rollback(self):
            """Rollback transaction."""
            self._conn.rollback()

        def close(self):
            """Close connection (no-op for test)."""
            pass

    return TestDBConnection(in_memory_db)


@pytest.fixture
def embedding_repo(db_connection):
    """Create an EmbeddingRepository instance."""
    return EmbeddingRepository(db_connection)


@pytest.fixture
def sample_embedding():
    """Create a sample embedding vector."""
    return [0.1, 0.2, 0.3, 0.4, 0.5]


@pytest.fixture
def sample_embeddings_batch():
    """Create a batch of sample embeddings."""
    return [
        {"file_id": 1, "embedding": [0.1, 0.2, 0.3], "model_version": "v1", "created_time": 1000},
        {"file_id": 2, "embedding": [0.4, 0.5, 0.6], "model_version": "v1", "created_time": 1001},
        {"file_id": 3, "embedding": [0.7, 0.8, 0.9], "model_version": "v2", "created_time": 1002},
    ]


# =============================================================================
# EmbeddingRepository Initialization Tests
# =============================================================================

class TestEmbeddingRepositoryInit:
    """Tests for EmbeddingRepository initialization."""

    def test_init_with_db_connection(self, db_connection):
        """Test initialization with database connection."""
        repo = EmbeddingRepository(db_connection)
        assert repo.db is db_connection

    def test_init_stores_connection(self, db_connection):
        """Test that connection is stored correctly."""
        repo = EmbeddingRepository(db_connection)
        assert hasattr(repo, "db")


# =============================================================================
# Add Embedding Tests
# =============================================================================

class TestAddEmbedding:
    """Tests for add_embedding method."""

    def test_add_embedding_success(self, embedding_repo, sample_embedding):
        """Test adding an embedding successfully."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        assert embedding_id is not None
        assert embedding_id > 0

    def test_add_embedding_returns_integer(self, embedding_repo, sample_embedding):
        """Test that add_embedding returns an integer ID."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        assert isinstance(embedding_id, int)

    def test_add_embedding_serializes_to_blob(self, db_connection, sample_embedding):
        """Test that embedding is serialized to blob."""
        repo = EmbeddingRepository(db_connection)
        embedding_id = repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        cursor = db_connection.execute(
            "SELECT embedding FROM embeddings WHERE id = ?",
            (embedding_id,)
        )
        row = cursor.fetchone()
        assert row is not None
        # Verify it's serialized as JSON (secure format)
        import json
        loaded = json.loads(row[0].decode('utf-8'))
        assert np.array_equal(loaded, sample_embedding)

    def test_add_embedding_stores_metadata(self, embedding_repo, sample_embedding):
        """Test that embedding metadata is stored correctly."""
        embedding_id = embedding_repo.add_embedding(
            file_id=42,
            embedding=sample_embedding,
            model_version="test_model",
            created_time=12345
        )

        result = embedding_repo.get_embedding(embedding_id)
        assert result is not None
        assert result["file_id"] == 42
        assert result["model_version"] == "test_model"
        assert result["created_time"] == 12345

    def test_add_embedding_multiple(self, embedding_repo, sample_embedding):
        """Test adding multiple embeddings."""
        ids = []
        for i in range(5):
            embedding_id = embedding_repo.add_embedding(
                file_id=i,
                embedding=sample_embedding,
                model_version="v1.0",
                created_time=1000 + i
            )
            ids.append(embedding_id)

        assert len(ids) == 5
        assert all(id > 0 for id in ids)
        # IDs should be unique
        assert len(set(ids)) == 5

    def test_add_embedding_different_models(self, embedding_repo, sample_embedding):
        """Test adding embeddings with different model versions."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="model_a",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="model_b",
            created_time=1001
        )

        embeddings = embedding_repo.get_embeddings_by_file(1)
        assert len(embeddings) == 2
        models = {e["model_version"] for e in embeddings}
        assert models == {"model_a", "model_b"}


# =============================================================================
# Get Embedding Tests
# =============================================================================

class TestGetEmbedding:
    """Tests for get_embedding method."""

    def test_get_embedding_by_id(self, embedding_repo, sample_embedding):
        """Test getting embedding by ID."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding(embedding_id)
        assert result is not None
        assert result["id"] == embedding_id
        assert np.array_equal(result["embedding"], sample_embedding)

    def test_get_embedding_returns_dict(self, embedding_repo, sample_embedding):
        """Test that get_embedding returns a dictionary."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding(embedding_id)
        assert isinstance(result, dict)

    def test_get_embedding_has_all_fields(self, embedding_repo, sample_embedding):
        """Test that returned embedding has all expected fields."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding(embedding_id)
        assert "id" in result
        assert "file_id" in result
        assert "embedding" in result
        assert "model_version" in result
        assert "created_time" in result

    def test_get_embedding_not_found(self, embedding_repo):
        """Test getting non-existent embedding returns None."""
        result = embedding_repo.get_embedding(99999)
        assert result is None

    def test_get_embedding_deserializes_blob(self, embedding_repo, sample_embedding):
        """Test that embedding blob is properly deserialized."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding(embedding_id)
        assert isinstance(result["embedding"], (list, np.ndarray))
        # dtype check removed - sample_embedding is now a list


# =============================================================================
# Get Embedding By File Tests
# =============================================================================

class TestGetEmbeddingByFile:
    """Tests for get_embedding_by_file method."""

    def test_get_embedding_by_file_and_model(self, embedding_repo, sample_embedding):
        """Test getting embedding by file ID and model version."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding_by_file(1, "v1.0")
        assert result is not None
        assert result["file_id"] == 1
        assert result["model_version"] == "v1.0"

    def test_get_embedding_by_file_not_found(self, embedding_repo):
        """Test getting non-existent embedding by file returns None."""
        result = embedding_repo.get_embedding_by_file(999, "v1.0")
        assert result is None

    def test_get_embedding_by_file_wrong_model(self, embedding_repo, sample_embedding):
        """Test that wrong model version returns None."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding_by_file(1, "v2.0")
        assert result is None

    def test_get_embedding_by_file_returns_first_match(self, embedding_repo, sample_embedding):
        """Test that get_embedding_by_file returns first match."""
        # Add two embeddings for same file with same model (shouldn't happen but test behavior)
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )

        result = embedding_repo.get_embedding_by_file(1, "v1.0")
        assert result is not None
        assert result["file_id"] == 1


# =============================================================================
# Get Embeddings By File Tests
# =============================================================================

class TestGetEmbeddingsByFile:
    """Tests for get_embeddings_by_file method."""

    def test_get_embeddings_by_file(self, embedding_repo, sample_embedding):
        """Test getting all embeddings for a file."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding * 2,
            model_version="v2.0",
            created_time=1001
        )

        results = embedding_repo.get_embeddings_by_file(1)
        assert len(results) == 2

    def test_get_embeddings_by_file_empty(self, embedding_repo):
        """Test getting embeddings for non-existent file."""
        results = embedding_repo.get_embeddings_by_file(999)
        assert results == []

    def test_get_embeddings_by_file_returns_list(self, embedding_repo, sample_embedding):
        """Test that get_embeddings_by_file returns a list."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        results = embedding_repo.get_embeddings_by_file(1)
        assert isinstance(results, list)

    def test_get_embeddings_by_file_ordered_by_model(self, embedding_repo, sample_embedding):
        """Test that embeddings are ordered by model version."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v2.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )

        results = embedding_repo.get_embeddings_by_file(1)
        assert len(results) == 2
        # Should be ordered by model_version
        assert results[0]["model_version"] == "v1.0"
        assert results[1]["model_version"] == "v2.0"


# =============================================================================
# Get Embeddings By Model Tests
# =============================================================================

class TestGetEmbeddingsByModel:
    """Tests for get_embeddings_by_model method."""

    def test_get_embeddings_by_model(self, embedding_repo, sample_embedding):
        """Test getting all embeddings for a model version."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=2,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )
        embedding_repo.add_embedding(
            file_id=3,
            embedding=sample_embedding * 3,
            model_version="v2.0",
            created_time=1002
        )

        results = embedding_repo.get_embeddings_by_model("v1.0")
        assert len(results) == 2

    def test_get_embeddings_by_model_empty(self, embedding_repo):
        """Test getting embeddings for non-existent model."""
        results = embedding_repo.get_embeddings_by_model("nonexistent")
        assert results == []

    def test_get_embeddings_by_model_returns_list(self, embedding_repo, sample_embedding):
        """Test that get_embeddings_by_model returns a list."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        results = embedding_repo.get_embeddings_by_model("v1.0")
        assert isinstance(results, list)

    def test_get_embeddings_by_model_ordered_by_file_id(self, embedding_repo, sample_embedding):
        """Test that embeddings are ordered by file_id."""
        embedding_repo.add_embedding(
            file_id=3,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )
        embedding_repo.add_embedding(
            file_id=2,
            embedding=sample_embedding * 3,
            model_version="v1.0",
            created_time=1002
        )

        results = embedding_repo.get_embeddings_by_model("v1.0")
        file_ids = [r["file_id"] for r in results]
        assert file_ids == sorted(file_ids)


# =============================================================================
# Update Embedding Tests
# =============================================================================

class TestUpdateEmbedding:
    """Tests for update_embedding method."""

    def test_update_embedding_success(self, embedding_repo, sample_embedding):
        """Test updating an embedding."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        new_embedding = sample_embedding * 2
        result = embedding_repo.update_embedding(embedding_id, new_embedding)
        assert result is True

    def test_update_embedding_persists(self, embedding_repo, sample_embedding):
        """Test that updated embedding persists."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        new_embedding = sample_embedding * 2
        embedding_repo.update_embedding(embedding_id, new_embedding)

        result = embedding_repo.get_embedding(embedding_id)
        assert np.array_equal(result["embedding"], new_embedding)

    def test_update_embedding_not_found(self, embedding_repo, sample_embedding):
        """Test updating non-existent embedding returns False."""
        result = embedding_repo.update_embedding(99999, sample_embedding)
        assert result is False

    def test_update_embedding_preserves_metadata(self, embedding_repo, sample_embedding):
        """Test that update preserves metadata."""
        embedding_id = embedding_repo.add_embedding(
            file_id=42,
            embedding=sample_embedding,
            model_version="original_model",
            created_time=12345
        )

        new_embedding = sample_embedding * 2
        embedding_repo.update_embedding(embedding_id, new_embedding)

        result = embedding_repo.get_embedding(embedding_id)
        assert result["file_id"] == 42
        assert result["model_version"] == "original_model"
        assert result["created_time"] == 12345


# =============================================================================
# Delete Embedding Tests
# =============================================================================

class TestDeleteEmbedding:
    """Tests for delete_embedding method."""

    def test_delete_embedding_success(self, embedding_repo, sample_embedding):
        """Test deleting an embedding."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.delete_embedding(embedding_id)
        assert result is True

    def test_delete_embedding_removes_record(self, embedding_repo, sample_embedding):
        """Test that deleted embedding is removed."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        embedding_repo.delete_embedding(embedding_id)
        result = embedding_repo.get_embedding(embedding_id)
        assert result is None

    def test_delete_embedding_not_found(self, embedding_repo):
        """Test deleting non-existent embedding returns False."""
        result = embedding_repo.delete_embedding(99999)
        assert result is False

    def test_delete_embedding_idempotent(self, embedding_repo, sample_embedding):
        """Test that deleting same embedding twice returns False second time."""
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        embedding_repo.delete_embedding(embedding_id)
        result = embedding_repo.delete_embedding(embedding_id)
        assert result is False


# =============================================================================
# Delete Embeddings By File Tests
# =============================================================================

class TestDeleteEmbeddingsByFile:
    """Tests for delete_embeddings_by_file method."""

    def test_delete_embeddings_by_file(self, embedding_repo, sample_embedding):
        """Test deleting all embeddings for a file."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding * 2,
            model_version="v2.0",
            created_time=1001
        )
        embedding_repo.add_embedding(
            file_id=2,
            embedding=sample_embedding * 3,
            model_version="v1.0",
            created_time=1002
        )

        count = embedding_repo.delete_embeddings_by_file(1)
        assert count == 2

    def test_delete_embeddings_by_file_removes_records(self, embedding_repo, sample_embedding):
        """Test that deleted embeddings are removed."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding * 2,
            model_version="v2.0",
            created_time=1001
        )

        embedding_repo.delete_embeddings_by_file(1)
        results = embedding_repo.get_embeddings_by_file(1)
        assert len(results) == 0

    def test_delete_embeddings_by_file_no_matches(self, embedding_repo):
        """Test deleting embeddings for non-existent file returns 0."""
        count = embedding_repo.delete_embeddings_by_file(999)
        assert count == 0

    def test_delete_embeddings_by_file_returns_int(self, embedding_repo, sample_embedding):
        """Test that delete_embeddings_by_file returns an integer."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        count = embedding_repo.delete_embeddings_by_file(1)
        assert isinstance(count, int)


# =============================================================================
# Delete Embeddings By Model Tests
# =============================================================================

class TestDeleteEmbeddingsByModel:
    """Tests for delete_embeddings_by_model method."""

    def test_delete_embeddings_by_model(self, embedding_repo, sample_embedding):
        """Test deleting all embeddings for a model version."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=2,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )
        embedding_repo.add_embedding(
            file_id=3,
            embedding=sample_embedding * 3,
            model_version="v2.0",
            created_time=1002
        )

        count = embedding_repo.delete_embeddings_by_model("v1.0")
        assert count == 2

    def test_delete_embeddings_by_model_removes_records(self, embedding_repo, sample_embedding):
        """Test that deleted embeddings are removed."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=2,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )

        embedding_repo.delete_embeddings_by_model("v1.0")
        results = embedding_repo.get_embeddings_by_model("v1.0")
        assert len(results) == 0

    def test_delete_embeddings_by_model_no_matches(self, embedding_repo):
        """Test deleting embeddings for non-existent model returns 0."""
        count = embedding_repo.delete_embeddings_by_model("nonexistent")
        assert count == 0

    def test_delete_embeddings_by_model_returns_int(self, embedding_repo, sample_embedding):
        """Test that delete_embeddings_by_model returns an integer."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        count = embedding_repo.delete_embeddings_by_model("v1.0")
        assert isinstance(count, int)


# =============================================================================
# Get All Embeddings Tests
# =============================================================================

class TestGetAllEmbeddings:
    """Tests for get_all_embeddings method."""

    def test_get_all_embeddings(self, embedding_repo, sample_embedding):
        """Test getting all embeddings."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=2,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )

        results = embedding_repo.get_all_embeddings()
        assert len(results) == 2

    def test_get_all_embeddings_empty(self, embedding_repo):
        """Test getting all embeddings when none exist."""
        results = embedding_repo.get_all_embeddings()
        assert results == []

    def test_get_all_embeddings_returns_list(self, embedding_repo, sample_embedding):
        """Test that get_all_embeddings returns a list."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        results = embedding_repo.get_all_embeddings()
        assert isinstance(results, list)

    def test_get_all_embeddings_ordered(self, embedding_repo, sample_embedding):
        """Test that embeddings are ordered by file_id, model_version."""
        embedding_repo.add_embedding(
            file_id=2,
            embedding=sample_embedding,
            model_version="v2.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding * 3,
            model_version="v2.0",
            created_time=1002
        )

        results = embedding_repo.get_all_embeddings()
        file_ids = [r["file_id"] for r in results]
        assert file_ids == sorted(file_ids)


# =============================================================================
# Count Embeddings Tests
# =============================================================================

class TestCountEmbeddings:
    """Tests for count_embeddings methods."""

    def test_count_embeddings(self, embedding_repo, sample_embedding):
        """Test counting all embeddings."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=2,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )
        embedding_repo.add_embedding(
            file_id=3,
            embedding=sample_embedding * 3,
            model_version="v2.0",
            created_time=1002
        )

        count = embedding_repo.count_embeddings()
        assert count == 3

    def test_count_embeddings_empty(self, embedding_repo):
        """Test counting when no embeddings exist."""
        count = embedding_repo.count_embeddings()
        assert count == 0

    def test_count_embeddings_returns_int(self, embedding_repo, sample_embedding):
        """Test that count_embeddings returns an integer."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        count = embedding_repo.count_embeddings()
        assert isinstance(count, int)

    def test_count_embeddings_by_model(self, embedding_repo, sample_embedding):
        """Test counting embeddings by model version."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=2,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )
        embedding_repo.add_embedding(
            file_id=3,
            embedding=sample_embedding * 3,
            model_version="v2.0",
            created_time=1002
        )

        count = embedding_repo.count_embeddings_by_model("v1.0")
        assert count == 2

    def test_count_embeddings_by_model_empty(self, embedding_repo):
        """Test counting by model when no matches."""
        count = embedding_repo.count_embeddings_by_model("nonexistent")
        assert count == 0

    def test_count_embeddings_by_model_returns_int(self, embedding_repo, sample_embedding):
        """Test that count_embeddings_by_model returns an integer."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        count = embedding_repo.count_embeddings_by_model("v1.0")
        assert isinstance(count, int)


# =============================================================================
# Batch Add Embeddings Tests
# =============================================================================

class TestBatchAddEmbeddings:
    """Tests for batch_add_embeddings method."""

    def test_batch_add_embeddings(self, embedding_repo, sample_embeddings_batch):
        """Test batch adding embeddings."""
        count = embedding_repo.batch_add_embeddings(sample_embeddings_batch)
        assert count == 3

    def test_batch_add_embeddings_persists(self, embedding_repo, sample_embeddings_batch):
        """Test that batch added embeddings persist."""
        embedding_repo.batch_add_embeddings(sample_embeddings_batch)

        all_embeddings = embedding_repo.get_all_embeddings()
        assert len(all_embeddings) == 3

    def test_batch_add_embeddings_empty_list(self, embedding_repo):
        """Test batch adding empty list returns 0."""
        count = embedding_repo.batch_add_embeddings([])
        assert count == 0

    def test_batch_add_embeddings_returns_int(self, embedding_repo, sample_embeddings_batch):
        """Test that batch_add_embeddings returns an integer."""
        count = embedding_repo.batch_add_embeddings(sample_embeddings_batch)
        assert isinstance(count, int)

    def test_batch_add_embeddings_various_models(self, embedding_repo, sample_embeddings_batch):
        """Test batch adding embeddings with different models."""
        embedding_repo.batch_add_embeddings(sample_embeddings_batch)

        v1_count = embedding_repo.count_embeddings_by_model("v1")
        v2_count = embedding_repo.count_embeddings_by_model("v2")
        assert v1_count == 2
        assert v2_count == 1

    def test_batch_add_embeddings_numpy_arrays(self, embedding_repo):
        """Test batch adding embeddings with numpy arrays."""
        embeddings = [
            {"file_id": 1, "embedding": np.array([0.1, 0.2, 0.3]), "model_version": "v1", "created_time": 1000},
            {"file_id": 2, "embedding": np.array([0.4, 0.5, 0.6]), "model_version": "v1", "created_time": 1001},
        ]
        count = embedding_repo.batch_add_embeddings(embeddings)
        assert count == 2


# =============================================================================
# Clear All Embeddings Tests
# =============================================================================

class TestClearAllEmbeddings:
    """Tests for clear_all_embeddings method."""

    def test_clear_all_embeddings(self, embedding_repo, sample_embedding):
        """Test clearing all embeddings."""
        embedding_repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        embedding_repo.add_embedding(
            file_id=2,
            embedding=sample_embedding * 2,
            model_version="v1.0",
            created_time=1001
        )

        embedding_repo.clear_all_embeddings()
        count = embedding_repo.count_embeddings()
        assert count == 0

    def test_clear_all_embeddings_empty(self, embedding_repo):
        """Test clearing when no embeddings exist."""
        # Should not raise
        embedding_repo.clear_all_embeddings()
        count = embedding_repo.count_embeddings()
        assert count == 0

    def test_clear_all_embeddings_commits(self, db_connection, sample_embedding):
        """Test that clear_all_embeddings commits the transaction."""
        repo = EmbeddingRepository(db_connection)
        repo.add_embedding(
            file_id=1,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )

        repo.clear_all_embeddings()

        # Verify committed by checking count
        count = repo.count_embeddings()
        assert count == 0


# =============================================================================
# Get Embedding Repository Function Tests
# =============================================================================

class TestGetEmbeddingRepository:
    """Tests for get_embedding_repository function."""

    def test_get_embedding_repository(self, tmp_path):
        """Test get_embedding_repository function."""
        db_path = str(tmp_path / "test.db")
        repo = get_embedding_repository(db_path)
        assert isinstance(repo, EmbeddingRepository)

    def test_get_embedding_repository_creates_connection(self, tmp_path):
        """Test that get_embedding_repository creates a connection."""
        db_path = str(tmp_path / "test.db")
        repo = get_embedding_repository(db_path)
        assert repo.db is not None

    def test_get_embedding_repository_default_path(self, monkeypatch, tmp_path):
        """Test get_embedding_repository with default path."""
        monkeypatch.chdir(tmp_path)
        # Create output directory
        os.makedirs(tmp_path / "output", exist_ok=True)
        repo = get_embedding_repository(str(tmp_path / "output" / "index.db"))
        assert isinstance(repo, EmbeddingRepository)


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in embedding operations."""

    def test_add_embedding_with_invalid_file_id(self, embedding_repo, sample_embedding):
        """Test adding embedding with invalid file_id still works (no FK constraint in test)."""
        # Even with non-existent file_id, should work if no FK constraint
        embedding_id = embedding_repo.add_embedding(
            file_id=99999,
            embedding=sample_embedding,
            model_version="v1.0",
            created_time=1000
        )
        assert embedding_id is not None

    def test_get_embedding_with_invalid_id(self, embedding_repo):
        """Test getting embedding with invalid ID returns None."""
        result = embedding_repo.get_embedding(-1)
        assert result is None

    def test_update_embedding_with_invalid_id(self, embedding_repo, sample_embedding):
        """Test updating embedding with invalid ID returns False."""
        result = embedding_repo.update_embedding(-1, sample_embedding)
        assert result is False

    def test_delete_embedding_with_invalid_id(self, embedding_repo):
        """Test deleting embedding with invalid ID returns False."""
        result = embedding_repo.delete_embedding(-1)
        assert result is False


# =============================================================================
# Large Dataset Tests
# =============================================================================

class TestLargeDataset:
    """Tests for large embedding datasets."""

    def test_batch_add_large_dataset(self, embedding_repo):
        """Test batch adding large number of embeddings."""
        embeddings = [
            {"file_id": i, "embedding": [float(i), float(i+1), float(i+2)], "model_version": "v1", "created_time": 1000 + i}
            for i in range(100)
        ]
        count = embedding_repo.batch_add_embeddings(embeddings)
        assert count == 100

    def test_count_large_dataset(self, embedding_repo):
        """Test counting large number of embeddings."""
        embeddings = [
            {"file_id": i, "embedding": [float(i), float(i+1), float(i+2)], "model_version": "v1", "created_time": 1000 + i}
            for i in range(100)
        ]
        embedding_repo.batch_add_embeddings(embeddings)

        count = embedding_repo.count_embeddings()
        assert count == 100

    def test_get_all_large_dataset(self, embedding_repo):
        """Test getting all embeddings from large dataset."""
        embeddings = [
            {"file_id": i, "embedding": [float(i), float(i+1), float(i+2)], "model_version": "v1", "created_time": 1000 + i}
            for i in range(100)
        ]
        embedding_repo.batch_add_embeddings(embeddings)

        all_embeddings = embedding_repo.get_all_embeddings()
        assert len(all_embeddings) == 100

    def test_delete_by_file_large_dataset(self, embedding_repo):
        """Test deleting by file_id in large dataset."""
        embeddings = [
            {"file_id": i % 10, "embedding": [float(i), float(i+1), float(i+2)], "model_version": "v1", "created_time": 1000 + i}
            for i in range(100)
        ]
        embedding_repo.batch_add_embeddings(embeddings)

        # Each file_id (0-9) should have 10 embeddings
        count = embedding_repo.delete_embeddings_by_file(5)
        assert count == 10

    def test_delete_by_model_large_dataset(self, embedding_repo):
        """Test deleting by model_version in large dataset."""
        embeddings = [
            {"file_id": i, "embedding": [float(i), float(i+1), float(i+2)], "model_version": f"v{i % 5}", "created_time": 1000 + i}
            for i in range(100)
        ]
        embedding_repo.batch_add_embeddings(embeddings)

        # Each model (v0-v4) should have 20 embeddings
        count = embedding_repo.delete_embeddings_by_model("v2")
        assert count == 20


# =============================================================================
# Vector Operations Tests
# =============================================================================

class TestVectorOperations:
    """Tests for vector operations with embeddings."""

    def test_numpy_array_embedding(self, embedding_repo):
        """Test storing numpy array embeddings."""
        embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding(embedding_id)
        assert np.array_equal(result["embedding"], embedding)

    def test_list_embedding(self, embedding_repo):
        """Test storing list embeddings."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding(embedding_id)
        assert result["embedding"] == embedding

    def test_high_dimensional_embedding(self, embedding_repo):
        """Test storing high-dimensional embeddings."""
        embedding = np.random.rand(512).astype(np.float32)
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding(embedding_id)
        assert len(result["embedding"]) == 512

    def test_embedding_precision(self, embedding_repo):
        """Test that embedding precision is preserved."""
        embedding = np.array([0.123456789, 0.987654321, 0.111111111], dtype=np.float64)
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding(embedding_id)
        # Check values are close (JSON preserves float64 precision)
        assert np.allclose(result["embedding"], embedding)

    def test_zero_vector_embedding(self, embedding_repo):
        """Test storing zero vector embedding."""
        embedding = np.zeros(10, dtype=np.float32)
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding(embedding_id)
        assert np.array_equal(result["embedding"], embedding)

    def test_negative_values_embedding(self, embedding_repo):
        """Test storing embeddings with negative values."""
        embedding = np.array([-0.5, -0.3, 0.0, 0.3, 0.5], dtype=np.float32)
        embedding_id = embedding_repo.add_embedding(
            file_id=1,
            embedding=embedding,
            model_version="v1.0",
            created_time=1000
        )

        result = embedding_repo.get_embedding(embedding_id)
        assert np.array_equal(result["embedding"], embedding)


# =============================================================================
# Schema Bug Fix Tests (dimensions column)
# =============================================================================

class TestSchemaBugFix:
    """Tests related to the schema bug (missing dimensions column)."""

    def test_schema_has_dimensions_column(self, in_memory_db):
        """Test that embeddings table has dimensions column."""
        cursor = in_memory_db.execute("PRAGMA table_info(embeddings)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "dimensions" in columns

    def test_embedding_with_dimensions(self, in_memory_db):
        """Test adding embedding with dimensions value."""
        embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
        # nosec B301 - Testing legacy pickle deserialization fallback
        # nosem: python.lang.security.deserialization.pickle.avoid-pickle - Testing legacy pickle deserialization fallback
        embedding_bytes = pickle.dumps(embedding)

        in_memory_db.execute(
            """
            INSERT INTO embeddings (file_id, embedding, model_version, created_time, dimensions)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, embedding_bytes, "v1.0", 1000, 5)
        )
        in_memory_db.commit()

        cursor = in_memory_db.execute("SELECT dimensions FROM embeddings WHERE file_id = 1")
        result = cursor.fetchone()
        assert result[0] == 5

    def test_dimensions_stored_correctly(self, in_memory_db):
        """Test that dimensions are stored correctly for various sizes."""
        for dim in [10, 50, 128, 512, 1024]:
            embedding = np.random.rand(dim).astype(np.float32)
            # nosec B301 - Testing legacy pickle deserialization fallback
            # nosem: python.lang.security.deserialization.pickle.avoid-pickle - Testing legacy pickle deserialization fallback
            embedding_bytes = pickle.dumps(embedding)

            in_memory_db.execute(
                """
                INSERT INTO embeddings (file_id, embedding, model_version, created_time, dimensions)
                VALUES (?, ?, ?, ?, ?)
                """,
                (1, embedding_bytes, "v1.0", 1000, dim)
            )
            in_memory_db.commit()

            cursor = in_memory_db.execute("SELECT dimensions FROM embeddings WHERE file_id = 1 AND model_version = 'v1.0' ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            assert result[0] == dim

    def test_get_embedding_dimensions_helper(self, db_connection):
        """Test _get_embedding_dimensions helper method."""
        repo = EmbeddingRepository(db_connection)
        # Test with list
        assert repo._get_embedding_dimensions([1, 2, 3]) == 3
        # Test with numpy array
        assert repo._get_embedding_dimensions(np.array([1, 2, 3, 4])) == 4
        # Test with empty list
        assert repo._get_embedding_dimensions([]) == 0
        # Test with non-sequence (should return 0)
        assert repo._get_embedding_dimensions(42) == 0
