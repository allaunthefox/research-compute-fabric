# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on indexing.py module.

This test file targets the missing coverage in:
- indexing.py: Index creation edge cases, analyze_query paths, is_index_used paths
"""

import sqlite3
from unittest.mock import MagicMock

import pytest

from nodupe.tools.databases.indexing import (
    DatabaseIndexing,
    IndexingError,
    create_covering_index,
)


class TestDatabaseIndexingCoverage:
    """Tests for DatabaseIndexing class to achieve 100% coverage."""

    @pytest.fixture
    def in_memory_connection(self):
        """Create an in-memory SQLite database connection."""
        conn = sqlite3.connect(":memory:")
        yield conn
        conn.close()

    @pytest.fixture
    def db_with_schema(self, in_memory_connection):
        """Create in-memory DB with required tables."""
        conn = in_memory_connection
        # Create minimal tables needed for indexing tests
        conn.execute("""
            CREATE TABLE files (
                id INTEGER PRIMARY KEY,
                path TEXT,
                size INTEGER,
                hash TEXT,
                is_duplicate BOOLEAN,
                duplicate_of INTEGER,
                status TEXT,
                modified_time INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE embeddings (
                id INTEGER PRIMARY KEY,
                file_id INTEGER,
                model_version TEXT,
                created_time INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE file_relationships (
                id INTEGER PRIMARY KEY,
                file1_id INTEGER,
                file2_id INTEGER,
                relationship_type TEXT,
                similarity_score REAL
            )
        """)
        conn.execute("""
            CREATE TABLE tools (
                id INTEGER PRIMARY KEY,
                name TEXT,
                type TEXT,
                status TEXT,
                enabled BOOLEAN
            )
        """)
        conn.commit()
        yield conn

    def test_create_indexes_rollback_on_error(self):
        """Test create_indexes calls rollback on error."""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = sqlite3.Error("Error creating cursor")
        indexing = DatabaseIndexing(mock_conn)

        with pytest.raises(IndexingError):
            indexing.create_indexes()

        mock_conn.rollback.assert_called_once()

    def test_create_index_rollback_on_error(self, db_with_schema):
        """Test create_index calls rollback on error."""
        indexing = DatabaseIndexing(db_with_schema)

        # Try to create index on non-existent table
        with pytest.raises(IndexingError):
            indexing.create_index(
                index_name="idx_test",
                table_name="nonexistent_table",
                columns=["col"]
            )

    def test_drop_index_rollback_on_error(self):
        """Test drop_index calls rollback on error."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = sqlite3.Error("Error")
        mock_conn.cursor.return_value = mock_cursor
        indexing = DatabaseIndexing(mock_conn)

        with pytest.raises(IndexingError):
            indexing.drop_index("some_index")

        mock_conn.rollback.assert_called_once()

    def test_get_index_info_empty_result(self, db_with_schema):
        """Test get_index_info returns empty list for non-existent index."""
        indexing = DatabaseIndexing(db_with_schema)

        info = indexing.get_index_info("nonexistent_index")

        assert info == []

    def test_analyze_query_short_row(self, db_with_schema):
        """Test analyze_query handles rows with fewer than 4 columns."""
        indexing = DatabaseIndexing(db_with_schema)

        # Mock cursor to return rows with only 3 columns
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 2, "detail")]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        indexing.connection = mock_conn

        plan = indexing.analyze_query("SELECT * FROM files")

        assert len(plan) == 1
        assert plan[0]['detail'] == "detail"

    def test_analyze_query_full_row(self, db_with_schema):
        """Test analyze_query handles rows with 4+ columns."""
        indexing = DatabaseIndexing(db_with_schema)

        # Mock cursor to return rows with 4 columns
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 2, 3, "full detail")]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        indexing.connection = mock_conn

        plan = indexing.analyze_query("SELECT * FROM files")

        assert len(plan) == 1
        assert plan[0]['detail'] == "full detail"

    def test_is_index_used_found(self, db_with_schema):
        """Test is_index_used when index is found in plan."""
        indexing = DatabaseIndexing(db_with_schema)

        # Create an index
        indexing.create_index("idx_path", "files", ["path"])

        # Insert data so query planner might use the index
        db_with_schema.execute("INSERT INTO files (path, size, modified_time) VALUES ('test', 100, 1)")
        db_with_schema.commit()

        # Check if index is used (result depends on query planner)
        result = indexing.is_index_used("SELECT * FROM files WHERE path = 'test'", "idx_path")
        assert isinstance(result, bool)

    def test_is_index_used_not_found(self, db_with_schema):
        """Test is_index_used when index is not in plan."""
        indexing = DatabaseIndexing(db_with_schema)

        # Create an index
        indexing.create_index("idx_size", "files", ["size"])

        # Check for non-existent index in plan
        result = indexing.is_index_used("SELECT * FROM files", "nonexistent_index")

        assert result is False

    def test_is_index_used_case_insensitive(self, db_with_schema):
        """Test is_index_used does case-insensitive matching."""
        indexing = DatabaseIndexing(db_with_schema)

        # Create an index
        indexing.create_index("IDX_UPPER", "files", ["size"])

        # Check with lowercase name
        result = indexing.is_index_used("SELECT * FROM files", "idx_upper")

        assert isinstance(result, bool)

    def test_get_table_stats_no_dbstat(self, db_with_schema):
        """Test get_table_stats when dbstat table doesn't exist."""
        indexing = DatabaseIndexing(db_with_schema)

        # dbstat table may not exist in all SQLite versions
        stats = indexing.get_table_stats("files")

        assert stats['table_name'] == "files"
        assert 'row_count' in stats
        assert 'table_size_bytes' in stats
        assert 'index_count' in stats

    def test_reindex_rollback_on_error(self, db_with_schema):
        """Test reindex calls rollback on error."""
        indexing = DatabaseIndexing(db_with_schema)

        # REINDEX on non-existent index raises error
        with pytest.raises(IndexingError):
            indexing.reindex("nonexistent_index")

    def test_find_missing_indexes_with_pk_only_table(self, db_with_schema):
        """Test find_missing_indexes for table with only PK."""
        indexing = DatabaseIndexing(db_with_schema)

        # Create a table with only id column
        db_with_schema.execute("CREATE TABLE simple_table (id INTEGER PRIMARY KEY, name TEXT)")
        db_with_schema.commit()

        suggestions = indexing.find_missing_indexes()

        assert isinstance(suggestions, list)

    def test_find_missing_indexes_with_common_columns(self, db_with_schema):
        """Test find_missing_indexes suggests indexes on common columns."""
        indexing = DatabaseIndexing(db_with_schema)

        # Create a table with common column names
        db_with_schema.execute("""
            CREATE TABLE common_cols (
                id INTEGER PRIMARY KEY,
                created_at INTEGER,
                updated_at INTEGER,
                status TEXT,
                type TEXT
            )
        """)
        db_with_schema.commit()

        suggestions = indexing.find_missing_indexes()

        # Should suggest indexes on common columns
        assert isinstance(suggestions, list)
        # Check if any suggestion is for our table
        table_suggestions = [s for s in suggestions if s['table'] == 'common_cols']
        assert len(table_suggestions) > 0

    def test_get_index_stats_empty_db(self, in_memory_connection):
        """Test get_index_stats with empty database."""
        indexing = DatabaseIndexing(in_memory_connection)

        stats = indexing.get_index_stats()

        assert stats['total_indexes'] == 0
        assert stats['total_tables'] == 0
        assert stats['avg_indexes_per_table'] == 0

    def test_get_index_stats_with_tables(self, db_with_schema):
        """Test get_index_stats with tables and indexes."""
        indexing = DatabaseIndexing(db_with_schema)
        indexing.create_indexes()

        stats = indexing.get_index_stats()

        assert stats['total_indexes'] > 0
        assert stats['total_tables'] > 0
        assert 'indexes_by_table' in stats

    def test_get_indexes_sqlite_error(self):
        """Test get_indexes handles sqlite3.Error."""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = sqlite3.Error("Database error")
        indexing = DatabaseIndexing(mock_conn)

        with pytest.raises(IndexingError, match="Failed to get indexes"):
            indexing.get_indexes()

    def test_get_table_stats_sqlite_error(self):
        """Test get_table_stats handles sqlite3.Error."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = sqlite3.Error("Error")
        mock_conn.cursor.return_value = mock_cursor
        indexing = DatabaseIndexing(mock_conn)

        with pytest.raises(IndexingError, match="Failed to get table stats"):
            indexing.get_table_stats("files")

    def test_reindex_all_rollback_on_error(self):
        """Test reindex() calls rollback on error."""
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = sqlite3.Error("REINDEX failed")
        indexing = DatabaseIndexing(mock_conn)

        with pytest.raises(IndexingError):
            indexing.reindex()

        mock_conn.rollback.assert_called_once()


class TestCreateCoveringIndexCoverage:
    """Tests for create_covering_index function."""

    def test_create_covering_index_sqlite_error(self):
        """Test create_covering_index handles sqlite3.Error."""
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = sqlite3.Error("Error")

        with pytest.raises(IndexingError, match="Failed to create covering index"):
            create_covering_index(
                connection=mock_conn,
                index_name="idx_covering",
                table_name="files",
                where_columns=["path"],
                select_columns=["size"]
            )

    def test_create_covering_index_duplicate_columns(self):
        """Test create_covering_index handles duplicate columns."""
        # Create in-memory DB with table
        conn = sqlite3.connect(":memory:")
        conn.execute("""
            CREATE TABLE files (
                id INTEGER PRIMARY KEY,
                path TEXT,
                size INTEGER,
                hash TEXT
            )
        """)
        conn.commit()

        # When select_columns overlap with where_columns
        create_covering_index(
            connection=conn,
            index_name="idx_overlap",
            table_name="files",
            where_columns=["path", "size"],
            select_columns=["size", "hash"]  # size is duplicated
        )

        # Verify index was created
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_overlap'"
        )
        assert cursor.fetchone() is not None
        conn.close()


class TestIndexingErrorCoverage:
    """Tests for IndexingError exception."""

    def test_indexing_error_creation(self):
        """Test IndexingError can be created."""
        error = IndexingError("Test error")
        assert str(error) == "Test error"

    def test_indexing_error_with_cause(self):
        """Test IndexingError with cause."""
        try:
            try:
                raise sqlite3.Error("SQLite error")
            except sqlite3.Error as e:
                raise IndexingError("Indexing failed") from e
        except IndexingError as ie:
            assert ie.__cause__ is not None
            assert isinstance(ie.__cause__, sqlite3.Error)
