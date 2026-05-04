# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for Database wrapper to achieve higher coverage."""

import sqlite3
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from nodupe.tools.databases.wrapper import Database, DatabaseError


class TestDatabaseWrapperCoverage:
    """Test cases to achieve higher coverage of Database wrapper."""

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_database_init(self, mock_conn_class):
        """Test Database initialization."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        db = Database("/test.db", timeout=30.0)
        
        assert db.path == "/test.db"
        assert db.timeout == 30.0
        assert hasattr(db, 'connection')
        assert hasattr(db, 'schema')
        assert hasattr(db, 'query')
        assert hasattr(db, 'transaction_manager')
        assert hasattr(db, 'cache')
        assert hasattr(db, 'locking')
        assert hasattr(db, 'logging')
        assert hasattr(db, 'session')
        assert hasattr(db, 'compression')
        assert hasattr(db, 'serialization')
        assert hasattr(db, 'cleanup')

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_database_aliases(self, mock_conn_class):
        """Test backward compatibility aliases."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        db = Database("/test.db")
        
        # Test that aliases work
        assert db.monitoring is db.performance
        assert db.validation is db.integrity
        assert db.schema_migration is db.migration
        assert db.optimization is db.performance

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_close(self, mock_conn_class):
        """Test close method."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        db = Database("/test.db")
        db.close()
        
        mock_conn.close.assert_called_once()

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_create_table_success(self, mock_conn_class):
        """Test create_table successful execution."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.get_connection.return_value = mock_connection
        
        db = Database("/test.db")
        db.create_table("test_table", "id INTEGER PRIMARY KEY, name TEXT")
        
        mock_connection.execute.assert_called()

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_create_table_sql_error(self, mock_conn_class):
        """Test create_table raises DatabaseError on SQL error."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        import sqlite3
        mock_connection = MagicMock()
        mock_connection.execute.side_effect = sqlite3.Error("SQL error")
        mock_conn.get_connection.return_value = mock_connection
        
        db = Database("/test.db")
        
        with pytest.raises(DatabaseError):
            db.create_table("test_table", "invalid schema")

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_create(self, mock_conn_class):
        """Test create method."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.lastrowid = 1
        mock_conn.get_connection.return_value = mock_connection
        
        db = Database("/test.db")
        result = db.create("files", {"path": "/test.txt", "size": 100})
        
        assert result == 1
        mock_connection.commit.assert_called()

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_update(self, mock_conn_class):
        """Test update method."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.rowcount = 1
        mock_conn.get_connection.return_value = mock_connection
        
        db = Database("/test.db")
        result = db.update("UPDATE files SET size = ? WHERE id = ?", (200, 1))
        
        assert result == 1
        mock_connection.commit.assert_called()

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_delete(self, mock_conn_class):
        """Test delete method."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.rowcount = 1
        mock_conn.get_connection.return_value = mock_connection
        
        db = Database("/test.db")
        result = db.delete("DELETE FROM files WHERE id = ?", (1,))
        
        assert result == 1
        mock_connection.commit.assert_called()

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_execute_batch(self, mock_conn_class):
        """Test execute_batch method."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        db = Database("/test.db")
        
        with patch.object(db.batch, 'execute_batch') as mock_batch:
            db.execute_batch([("INSERT INTO files VALUES (?, ?)", ("/a", 100))])
            mock_batch.assert_called_once()

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_execute_transaction_batch(self, mock_conn_class):
        """Test execute_transaction_batch method."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        db = Database("/test.db")
        
        with patch.object(db.batch, 'execute_transaction_batch') as mock_batch:
            db.execute_transaction_batch([("INSERT INTO files VALUES (?, ?)", ("/a", 100))])
            mock_batch.assert_called_once()

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_transaction_context_manager(self, mock_conn_class):
        """Test transaction context manager."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        db = Database("/test.db")
        
        with patch.object(db.transaction_manager, 'transaction') as mock_tx:
            mock_tx.return_value.__enter__ = MagicMock(return_value=None)
            mock_tx.return_value.__exit__ = MagicMock(return_value=None)
            
            with db.transaction():
                pass
            
            mock_tx.assert_called_once()

    @patch('nodupe.tools.databases.wrapper.DatabaseConnection')
    def test_context_manager_protocol(self, mock_conn_class):
        """Test context manager protocol."""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        db = Database("/test.db")
        
        with db as database:
            assert database is db
        
        mock_conn.close.assert_called()
