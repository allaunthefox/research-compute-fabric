# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on schema.py module.

This test file targets the missing coverage in:
- schema.py: Migration edge cases, version conflicts, schema validation paths
"""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.databases.schema import (
    DatabaseSchema,
    SchemaError,
    create_database,
)


class TestDatabaseSchemaCoverage:
    """Tests for DatabaseSchema class to achieve 100% coverage."""

    @pytest.fixture
    def in_memory_connection(self):
        """Create an in-memory SQLite database connection."""
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.close()

    @pytest.fixture
    def db_with_schema(self, in_memory_connection):
        """Create in-memory DB with full schema."""
        conn = in_memory_connection
        schema = DatabaseSchema(conn)
        schema.create_schema()
        yield conn

    def test_migrate_schema_target_is_current(self, db_with_schema):
        """Test migrate_schema when target version equals current version."""
        schema = DatabaseSchema(db_with_schema)

        # Should return early without error when already at target version
        schema.migrate_schema(target_version="1.0.0")
        # No exception should be raised

    def test_migrate_schema_no_schema_exists(self, in_memory_connection):
        """Test migrate_schema when no schema exists (creates fresh)."""
        schema = DatabaseSchema(in_memory_connection)

        # Should create schema fresh
        schema.migrate_schema(target_version="1.0.0")

        # Verify schema was created
        cursor = in_memory_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert 'files' in tables

    def test_migrate_from_version_not_implemented(self, db_with_schema):
        """Test _migrate_from_version raises SchemaError for unsupported versions."""
        schema = DatabaseSchema(db_with_schema)

        # Try to migrate to a different version (not implemented)
        with pytest.raises(SchemaError, match="Migration from 1.0.0 to 2.0.0 not implemented"):
            schema._migrate_from_version("1.0.0", "2.0.0")

    def test_migrate_from_version_same_version(self, db_with_schema):
        """Test _migrate_from_version when versions are the same."""
        schema = DatabaseSchema(db_with_schema)

        # Should return without error when versions match
        schema._migrate_from_version("1.0.0", "1.0.0")
        # No exception should be raised

    def test_migrate_schema_generic_exception(self, in_memory_connection):
        """Test migrate_schema catches generic exceptions."""
        schema = DatabaseSchema(in_memory_connection)

        # Mock get_schema_version to raise a generic exception
        with patch.object(schema, 'get_schema_version', side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(SchemaError, match="Schema migration failed"):
                schema.migrate_schema(target_version="1.0.0")

    def test_validate_schema_missing_table(self, in_memory_connection):
        """Test validate_schema detects missing tables."""
        # Don't create schema, just test validation
        schema = DatabaseSchema(in_memory_connection)

        is_valid, errors = schema.validate_schema()

        assert is_valid is False
        assert len(errors) > 0
        assert any("does not exist" in err for err in errors)

    def test_validate_schema_sqlite_error(self):
        """Test validate_schema handles sqlite3.Error."""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = sqlite3.Error("Database error")
        schema = DatabaseSchema(mock_conn)

        with pytest.raises(SchemaError, match="Schema validation failed"):
            schema.validate_schema()

    def test_get_schema_version_table_not_exists(self, in_memory_connection):
        """Test get_schema_version when schema_version table doesn't exist."""
        schema = DatabaseSchema(in_memory_connection)

        version = schema.get_schema_version()
        assert version is None

    def test_get_schema_version_empty_table(self, in_memory_connection):
        """Test get_schema_version when schema_version table exists but is empty."""
        # Create just the schema_version table
        in_memory_connection.execute("""
            CREATE TABLE schema_version (
                version TEXT PRIMARY KEY,
                applied_at INTEGER NOT NULL,
                description TEXT
            )
        """)
        in_memory_connection.commit()

        schema = DatabaseSchema(in_memory_connection)
        version = schema.get_schema_version()
        assert version is None

    def test_get_schema_version_sqlite_error(self):
        """Test get_schema_version handles sqlite3.Error."""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = sqlite3.Error("Database error")
        schema = DatabaseSchema(mock_conn)

        with pytest.raises(SchemaError, match="Failed to get schema version"):
            schema.get_schema_version()

    def test_drop_schema_sqlite_error(self):
        """Test drop_schema handles sqlite3.Error."""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = sqlite3.Error("Database error")
        schema = DatabaseSchema(mock_conn)

        with pytest.raises(SchemaError, match="Failed to drop schema"):
            schema.drop_schema()

    def test_get_table_info_sqlite_error(self):
        """Test get_table_info handles sqlite3.Error."""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = sqlite3.Error("Error")
        schema = DatabaseSchema(mock_conn)

        with pytest.raises(SchemaError, match="Failed to get table info"):
            schema.get_table_info("files")

    def test_get_indexes_sqlite_error(self):
        """Test get_indexes handles sqlite3.Error."""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = sqlite3.Error("Error")
        schema = DatabaseSchema(mock_conn)

        with pytest.raises(SchemaError, match="Failed to get indexes"):
            schema.get_indexes("files")

    def test_optimize_database_vacuum_error(self):
        """Test optimize_database handles VACUUM error."""
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = sqlite3.Error("VACUUM failed")
        schema = DatabaseSchema(mock_conn)

        with pytest.raises(SchemaError, match="Database optimization failed"):
            schema.optimize_database()

    def test_optimize_database_isolation_level_restore(self, db_with_schema):
        """Test optimize_database restores isolation level after VACUUM."""
        schema = DatabaseSchema(db_with_schema)

        # Store original isolation level
        original_level = db_with_schema.isolation_level

        # Run optimize (which changes isolation level temporarily)
        schema.optimize_database()

        # Isolation level should be restored
        assert db_with_schema.isolation_level == original_level

    def test_create_schema_sqlite_error(self):
        """Test create_schema handles sqlite3.Error."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = sqlite3.Error("Database error")
        mock_conn.cursor.return_value = mock_cursor
        schema = DatabaseSchema(mock_conn)

        with pytest.raises(SchemaError, match="Failed to create schema"):
            schema.create_schema()

    def test_create_schema_rollback_on_error(self):
        """Test create_schema calls rollback on error."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = sqlite3.Error("Database error")
        mock_conn.cursor.return_value = mock_cursor
        schema = DatabaseSchema(mock_conn)

        try:
            schema.create_schema()
        except SchemaError:
            pass

        # Verify rollback was called
        mock_conn.rollback.assert_called_once()

    def test_schemas_attribute_is_copy(self, in_memory_connection):
        """Test that self.schemas is a copy of TABLES."""
        schema = DatabaseSchema(in_memory_connection)

        # Modifying schemas should not affect TABLES
        schema.schemas['custom_table'] = 'CREATE TABLE custom (...)'

        assert 'custom_table' not in DatabaseSchema.TABLES


class TestCreateDatabaseCoverage:
    """Tests for create_database function."""

    def test_create_database_success(self, tmp_path):
        """Test create_database successfully creates database."""
        db_path = tmp_path / "test.db"

        conn = create_database(db_path)

        # Verify connection is valid
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert 'files' in tables
        conn.close()

    def test_create_database_creates_parent_directory(self, tmp_path):
        """Test create_database creates parent directories if needed."""
        db_path = tmp_path / "subdir" / "nested" / "test.db"

        conn = create_database(db_path)

        assert db_path.exists()
        conn.close()

    def test_create_database_schema_error(self):
        """Test create_database raises SchemaError on failure."""
        # Use a path that will cause an error
        with patch('nodupe.tools.databases.schema.sqlite3.connect', side_effect=sqlite3.Error("Connection failed")):
            with pytest.raises(SchemaError, match="Failed to create database"):
                create_database(Path("/nonexistent/path/test.db"))

    def test_create_database_mkdir_error(self):
        """Test create_database handles mkdir errors."""
        with patch('nodupe.tools.databases.schema.Path.mkdir', side_effect=OSError("Permission denied")):
            with pytest.raises(SchemaError, match="Failed to create database"):
                create_database(Path("/root/test.db"))
