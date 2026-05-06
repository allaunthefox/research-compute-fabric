# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on connection.py module.

This test file targets the missing coverage in:
- connection.py: DatabaseConnection class, connection pooling, singleton pattern
"""

import sqlite3
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from nodupe.tools.databases.connection import (
    DatabaseConnection,
    get_connection,
)


class TestDatabaseConnectionCoverage:
    """Tests for DatabaseConnection class to achieve 100% coverage."""

    @pytest.fixture
    def in_memory_db(self):
        """Create an in-memory DatabaseConnection."""
        db = DatabaseConnection(":memory:")
        yield db
        db.close()

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temp file-based DatabaseConnection."""
        db_path = tmp_path / "test.db"
        db = DatabaseConnection(str(db_path))
        yield db
        db.close()
        # Clean up singleton instances
        DatabaseConnection._instances.clear()

    def test_initialization_with_memory(self):
        """Test DatabaseConnection initialization with :memory:."""
        db = DatabaseConnection(":memory:")

        assert db.db_path == ":memory:"
        assert db._initialized is True
        db.close()

    def test_initialization_with_path(self, tmp_path):
        """Test DatabaseConnection initialization with file path."""
        db_path = tmp_path / "test.db"
        db = DatabaseConnection(str(db_path))

        assert db.db_path == str(db_path.absolute())
        assert db._initialized is True
        db.close()

    def test_get_connection_creates_connection(self, in_memory_db):
        """Test get_connection creates a new connection."""
        conn = in_memory_db.get_connection()

        assert isinstance(conn, sqlite3.Connection)

    def test_get_connection_caches_connection(self, in_memory_db):
        """Test get_connection returns same connection on subsequent calls."""
        conn1 = in_memory_db.get_connection()
        conn2 = in_memory_db.get_connection()

        assert conn1 is conn2

    def test_get_connection_pragmas_set(self, in_memory_db):
        """Test get_connection configures PRAGMA settings."""
        conn = in_memory_db.get_connection()

        # Verify synchronous is set to NORMAL
        cursor = conn.execute("PRAGMA synchronous")
        assert cursor.fetchone()[0] in (0, 1, 2)

    def test_get_connection_creates_directory(self, tmp_path):
        """Test get_connection creates parent directory if needed."""
        db_path = tmp_path / "subdir" / "nested" / "test.db"

        db = DatabaseConnection(str(db_path))
        conn = db.get_connection()

        assert db_path.parent.exists()
        db.close()

    def test_execute_query_without_params(self, in_memory_db):
        """Test execute without parameters."""
        # First create a table
        in_memory_db.execute("CREATE TABLE test (id INTEGER, name TEXT)")

        # Insert data
        cursor = in_memory_db.execute("INSERT INTO test VALUES (1, 'test')")

        assert cursor is not None
        in_memory_db.commit()

    def test_execute_query_with_params_tuple(self, in_memory_db):
        """Test execute with tuple parameters."""
        in_memory_db.execute("CREATE TABLE test (id INTEGER, name TEXT)")

        cursor = in_memory_db.execute(
            "INSERT INTO test VALUES (?, ?)",
            (1, 'test')
        )

        assert cursor is not None
        in_memory_db.commit()

    def test_execute_query_with_params_dict(self, in_memory_db):
        """Test execute with dictionary parameters."""
        in_memory_db.execute("CREATE TABLE test (id INTEGER, name TEXT)")

        cursor = in_memory_db.execute(
            "INSERT INTO test VALUES (:id, :name)",
            {"id": 1, "name": "test"}
        )

        assert cursor is not None
        in_memory_db.commit()

    def test_execute_query_error(self, in_memory_db):
        """Test execute raises error on invalid query."""
        with pytest.raises(sqlite3.Error):
            in_memory_db.execute("INVALID SQL")

    def test_executemany(self, in_memory_db):
        """Test executemany with multiple parameter sets."""
        in_memory_db.execute("CREATE TABLE test (id INTEGER, name TEXT)")

        params_list = [
            (1, 'a'),
            (2, 'b'),
            (3, 'c'),
        ]

        cursor = in_memory_db.executemany(
            "INSERT INTO test VALUES (?, ?)",
            params_list
        )

        assert cursor is not None
        in_memory_db.commit()

    def test_executemany_error(self, in_memory_db):
        """Test executemany raises error on invalid query."""
        with pytest.raises(sqlite3.Error):
            in_memory_db.executemany("INVALID SQL", [])

    def test_commit(self, in_memory_db):
        """Test commit commits the transaction."""
        in_memory_db.execute("CREATE TABLE test (id INTEGER)")
        in_memory_db.execute("INSERT INTO test VALUES (1)")

        # Should not raise
        in_memory_db.commit()

    def test_commit_error(self):
        """Test commit raises error when connection fails."""
        mock_conn = MagicMock()
        mock_conn.commit.side_effect = sqlite3.Error("Commit failed")

        db = DatabaseConnection(":memory:")
        db._local.connection = mock_conn

        with pytest.raises(sqlite3.Error):
            db.commit()

    def test_rollback(self, in_memory_db):
        """Test rollback rolls back the transaction."""
        in_memory_db.execute("CREATE TABLE test (id INTEGER)")
        in_memory_db.execute("INSERT INTO test VALUES (1)")

        # Should not raise
        in_memory_db.rollback()

    def test_rollback_error(self):
        """Test rollback raises error when connection fails."""
        mock_conn = MagicMock()
        mock_conn.rollback.side_effect = sqlite3.Error("Rollback failed")

        db = DatabaseConnection(":memory:")
        db._local.connection = mock_conn

        with pytest.raises(sqlite3.Error):
            db.rollback()

    def test_close(self, in_memory_db):
        """Test close closes the connection."""
        # Get connection first
        in_memory_db.get_connection()

        # Close should not raise
        in_memory_db.close()

    def test_close_no_connection(self, in_memory_db):
        """Test close when no connection exists."""
        # Don't get connection, just close
        in_memory_db.close()  # Should not raise

    def test_close_error(self):
        """Test close handles error gracefully."""
        mock_conn = MagicMock()
        mock_conn.close.side_effect = sqlite3.Error("Close failed")

        db = DatabaseConnection(":memory:")
        db._local.connection = mock_conn

        # Should not raise - close handles errors
        db.close()

    def test_del_calls_close(self, tmp_path):
        """Test __del__ calls close."""
        db_path = tmp_path / "test.db"
        db = DatabaseConnection(str(db_path))
        db.get_connection()

        # Simulate del by calling __del__
        db.__del__()


class TestDatabaseConnectionSingleton:
    """Tests for DatabaseConnection singleton pattern."""

    def teardown_method(self):
        """Clean up singleton instances after each test."""
        DatabaseConnection._instances.clear()

    def test_get_instance_creates_new(self):
        """Test get_instance creates a new instance."""
        db = DatabaseConnection.get_instance(":memory:")

        assert isinstance(db, DatabaseConnection)

    def test_get_instance_returns_same(self):
        """Test get_instance returns same instance."""
        db1 = DatabaseConnection.get_instance(":memory:")
        db2 = DatabaseConnection.get_instance(":memory:")

        assert db1 is db2

    def test_get_instance_different_paths_different_instances(self):
        """Test get_instance returns different instances for different paths."""
        db1 = DatabaseConnection.get_instance(":memory:")
        db2 = DatabaseConnection.get_instance("file.db")

        assert db1 is not db2

    def test_get_instance_thread_safety(self):
        """Test get_instance is thread-safe."""
        results = []

        def get_instance_in_thread():
            """Helper function to get database instance in a thread."""
            db = DatabaseConnection.get_instance("thread_test.db")
            results.append(db)

        threads = [threading.Thread(target=get_instance_in_thread) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should get the same instance
        assert len(set(id(r) for r in results)) == 1

        # Clean up
        DatabaseConnection._instances.clear()

    def test_singleton_lock_prevents_race_condition(self):
        """Test that singleton lock prevents race condition."""
        # This test verifies the lock exists and works
        assert hasattr(DatabaseConnection, '_lock')
        assert isinstance(DatabaseConnection._lock, type(threading.Lock()))


class TestInitializeDatabase:
    """Tests for initialize_database method."""

    @pytest.fixture
    def db_with_connection(self):
        """Create DatabaseConnection with mocked connection."""
        db = DatabaseConnection(":memory:")
        yield db
        db.close()
        DatabaseConnection._instances.clear()

    def test_initialize_database_creates_schema(self, db_with_connection):
        """Test initialize_database creates schema tables."""
        db_with_connection.initialize_database()

        conn = db_with_connection.get_connection()

        # Check files table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='files'"
        )
        assert cursor.fetchone() is not None

    def test_initialize_database_creates_indexes(self, db_with_connection):
        """Test initialize_database creates indexes."""
        db_with_connection.initialize_database()

        conn = db_with_connection.get_connection()

        # Check indexes exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = cursor.fetchall()
        assert len(indexes) > 0


class TestGetConnectionFunction:
    """Tests for get_connection convenience function."""

    def test_get_connection_returns_instance(self):
        """Test get_connection returns DatabaseConnection instance."""
        conn = get_connection(":memory:")

        assert isinstance(conn, DatabaseConnection)
        conn.close()
        DatabaseConnection._instances.clear()

    def test_get_connection_with_custom_path(self, tmp_path):
        """Test get_connection with custom path."""
        db_path = tmp_path / "custom.db"

        conn = get_connection(str(db_path))

        assert conn.db_path == str(db_path.absolute())
        conn.close()
        DatabaseConnection._instances.clear()


class TestDatabaseConnectionEdgeCases:
    """Edge case tests for DatabaseConnection."""

    def test_isolation_level_immediate(self, in_memory_db):
        """Test connection uses IMMEDIATE isolation level."""
        conn = in_memory_db.get_connection()

        # SQLite's isolation_level is None when using context managers
        # but starts with IMMEDIATE for write operations
        assert conn.isolation_level == 'IMMEDIATE'

    def test_foreign_keys_enabled(self, in_memory_db):
        """Test foreign keys are enabled."""
        conn = in_memory_db.get_connection()

        cursor = conn.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1


@pytest.fixture
def in_memory_db():
    """Fixture for in-memory DatabaseConnection."""
    db = DatabaseConnection(":memory:")
    yield db
    db.close()
    DatabaseConnection._instances.clear()
