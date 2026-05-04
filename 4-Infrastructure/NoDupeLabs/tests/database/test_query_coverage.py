# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on query.py module.

This test file targets the missing coverage in:
- query.py: Query optimization paths, batch operations, performance monitoring
"""

from unittest.mock import MagicMock

import pytest

from nodupe.tools.databases.query import (
    DatabaseBackup,
    DatabaseBatch,
    DatabaseIntegrity,
    DatabaseMigration,
    DatabaseOptimization,
    DatabasePerformance,
    DatabaseQuery,
    DatabaseRecovery,
)


class TestDatabaseQueryCoverage:
    """Tests for DatabaseQuery class to achieve 100% coverage."""

    def test_execute_with_get_connection(self):
        """Test execute when db has get_connection method."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_db.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('row1_col1', 'row1_col2'), ('row2_col1', 'row2_col2')]
        mock_cursor.description = [('col1',), ('col2',)]

        query = DatabaseQuery(mock_db)
        results = query.execute("SELECT * FROM test")

        assert len(results) == 2
        assert results[0] == {'col1': 'row1_col1', 'col2': 'row1_col2'}
        assert results[1] == {'col1': 'row2_col1', 'col2': 'row2_col2'}
        mock_db.get_connection.assert_called_once()

    def test_execute_with_connect(self):
        """Test execute when db has connect method (no get_connection)."""
        mock_db = MagicMock()
        del mock_db.get_connection  # Remove get_connection attribute

        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_db.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_cursor.description = [('col1',)]

        query = DatabaseQuery(mock_db)
        results = query.execute("SELECT * FROM test")

        assert results == []
        mock_db.connect.assert_called_once()

    def test_execute_with_params(self):
        """Test execute with parameters."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_db.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_cursor.description = [('col1',)]

        query = DatabaseQuery(mock_db)
        query.execute("SELECT * FROM test WHERE id = ?", (123,))

        mock_cursor.execute.assert_called_once_with("SELECT * FROM test WHERE id = ?", (123,))

    def test_execute_no_params(self):
        """Test execute without parameters (uses empty tuple)."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_db.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_cursor.description = [('col1',)]

        query = DatabaseQuery(mock_db)
        query.execute("SELECT * FROM test")

        mock_cursor.execute.assert_called_once_with("SELECT * FROM test", ())


class TestDatabaseBatchCoverage:
    """Tests for DatabaseBatch class to achieve 100% coverage."""

    def test_execute_batch_with_get_connection(self):
        """Test execute_batch when db has get_connection method."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_db.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        batch = DatabaseBatch(mock_db)
        operations = [
            ("INSERT INTO test VALUES (?, ?)", (1, 'a')),
            ("UPDATE test SET col = ?", ('b',)),
        ]
        batch.execute_batch(operations)

        assert mock_cursor.execute.call_count == 2
        mock_conn.commit.assert_called_once()

    def test_execute_batch_with_connect(self):
        """Test execute_batch when db has connect method."""
        mock_db = MagicMock()
        del mock_db.get_connection

        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_db.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        batch = DatabaseBatch(mock_db)
        batch.execute_batch([("INSERT INTO test VALUES (1)", ())])

        mock_db.connect.assert_called_once()

    def test_execute_transaction_batch_success(self):
        """Test execute_transaction_batch successful commit."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_db.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        batch = DatabaseBatch(mock_db)
        operations = [("INSERT INTO test VALUES (?)", (1,))]
        batch.execute_transaction_batch(operations)

        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()

    def test_execute_transaction_batch_rollback(self):
        """Test execute_transaction_batch rollback on exception."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_db.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Query failed")

        batch = DatabaseBatch(mock_db)
        operations = [("INSERT INTO test VALUES (?)", (1,))]

        with pytest.raises(Exception, match="Query failed"):
            batch.execute_transaction_batch(operations)

        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()


class TestDatabasePerformanceCoverage:
    """Tests for DatabasePerformance class to achieve 100% coverage."""

    def test_get_metrics(self):
        """Test get_metrics returns metrics dict."""
        mock_db = MagicMock()
        perf = DatabasePerformance(mock_db)

        metrics = perf.get_metrics()

        assert 'metrics' in metrics
        assert metrics['metrics']['queries'] == 0
        assert metrics['metrics']['total_time'] == 0.0
        assert metrics['metrics']['avg_time'] == 0.0

    def test_record_query_first(self):
        """Test record_query for first query."""
        mock_db = MagicMock()
        perf = DatabasePerformance(mock_db)

        perf.record_query(0.5)

        assert perf._metrics['queries'] == 1
        assert perf._metrics['total_time'] == 0.5
        assert perf._metrics['avg_time'] == 0.5

    def test_record_query_multiple(self):
        """Test record_query for multiple queries."""
        mock_db = MagicMock()
        perf = DatabasePerformance(mock_db)

        perf.record_query(0.3)
        perf.record_query(0.5)
        perf.record_query(0.4)

        assert perf._metrics['queries'] == 3
        assert perf._metrics['total_time'] == pytest.approx(1.2)
        assert perf._metrics['avg_time'] == pytest.approx(0.4)

    def test_monitor_performance(self):
        """Test monitor_performance returns db.monitoring."""
        mock_db = MagicMock()
        mock_monitoring = MagicMock()
        mock_db.monitoring = mock_monitoring

        perf = DatabasePerformance(mock_db)
        result = perf.monitor_performance()

        assert result is mock_monitoring

    def test_get_results(self):
        """Test get_results returns db.monitoring.get_metrics()."""
        mock_db = MagicMock()
        mock_monitoring = MagicMock()
        mock_monitoring.get_metrics.return_value = {'test': 'metrics'}
        mock_db.monitoring = mock_monitoring

        perf = DatabasePerformance(mock_db)
        result = perf.get_results()

        assert result == {'test': 'metrics'}
        mock_monitoring.get_metrics.assert_called_once()


class TestDatabaseIntegrityCoverage:
    """Tests for DatabaseIntegrity class to achieve 100% coverage."""

    def test_validate(self):
        """Test validate returns expected format."""
        mock_db = MagicMock()
        integrity = DatabaseIntegrity(mock_db)

        result = integrity.validate()

        assert 'valid' in result
        assert 'errors' in result
        assert 'tables' in result
        assert result['valid'] is True
        assert result['errors'] == []
        assert result['tables'] == []

    def test_check_integrity(self):
        """Test check_integrity returns expected format with indexes."""
        mock_db = MagicMock()
        integrity = DatabaseIntegrity(mock_db)

        result = integrity.check_integrity()

        assert 'valid' in result
        assert 'errors' in result
        assert 'tables' in result
        assert 'indexes' in result
        assert result['valid'] is True
        assert result['errors'] == []
        assert result['tables'] == []
        assert result['indexes'] == []


class TestDatabaseBackupCoverage:
    """Tests for DatabaseBackup class to achieve 100% coverage."""

    def test_create_backup(self, tmp_path):
        """Test create_backup copies database file."""
        mock_db = MagicMock()
        source_db = tmp_path / "source.db"
        source_db.write_bytes(b"database content")
        mock_db.path = str(source_db)

        backup_path = tmp_path / "backup.db"

        backup = DatabaseBackup(mock_db)
        backup.create_backup(str(backup_path))

        assert backup_path.exists()
        assert backup_path.read_bytes() == b"database content"

    def test_restore_backup(self, tmp_path):
        """Test restore_backup copies backup to restore path."""
        mock_db = MagicMock()
        backup_file = tmp_path / "backup.db"
        backup_file.write_bytes(b"backup content")
        restore_path = tmp_path / "restored.db"

        backup = DatabaseBackup(mock_db)
        backup.restore_backup(str(backup_file), str(restore_path))

        assert restore_path.exists()
        assert restore_path.read_bytes() == b"backup content"


class TestDatabaseMigrationCoverage:
    """Tests for DatabaseMigration class to achieve 100% coverage."""

    def test_migrate_schema(self):
        """Test migrate_schema (pass-through implementation)."""
        mock_db = MagicMock()
        migration = DatabaseMigration(mock_db)

        migrations = {
            'table1': {'add': ['col1'], 'remove': []},
        }

        # Should not raise (pass-through implementation)
        migration.migrate_schema(migrations)

    def test_migrate_data(self):
        """Test migrate_data (pass-through implementation)."""
        mock_db = MagicMock()
        migration = DatabaseMigration(mock_db)

        transformations = {'col1': 'UPPER(col1)'}
        new_columns = ['col2']

        # Should not raise (pass-through implementation)
        migration.migrate_data('table1', transformations, new_columns)

    def test_migrate_data_no_new_columns(self):
        """Test migrate_data without new_columns parameter."""
        mock_db = MagicMock()
        migration = DatabaseMigration(mock_db)

        transformations = {'col1': 'UPPER(col1)'}

        # Should not raise (pass-through implementation)
        migration.migrate_data('table1', transformations)


class TestDatabaseRecoveryCoverage:
    """Tests for DatabaseRecovery class to achieve 100% coverage."""

    def test_handle_errors_success(self):
        """Test handle_errors when integrity check passes."""
        mock_db = MagicMock()
        mock_integrity = MagicMock()
        mock_integrity.check_integrity.return_value = {'valid': True, 'errors': []}
        mock_db.integrity = mock_integrity

        recovery = DatabaseRecovery(mock_db)
        result = recovery.handle_errors(raise_on_error=False)

        assert result is True

    def test_handle_errors_invalid_not_raise(self):
        """Test handle_errors when integrity check fails (not raising)."""
        mock_db = MagicMock()
        mock_integrity = MagicMock()
        mock_integrity.check_integrity.return_value = {'valid': False, 'errors': ['error1']}
        mock_db.integrity = mock_integrity

        recovery = DatabaseRecovery(mock_db)
        result = recovery.handle_errors(raise_on_error=False)

        assert result is False

    def test_handle_errors_invalid_raise(self):
        """Test handle_errors when integrity check fails (raising)."""
        mock_db = MagicMock()
        mock_integrity = MagicMock()
        mock_integrity.check_integrity.return_value = {'valid': False, 'errors': ['error1']}
        mock_db.integrity = mock_integrity

        recovery = DatabaseRecovery(mock_db)

        with pytest.raises(Exception, match="Database integrity check failed"):
            recovery.handle_errors(raise_on_error=True)

    def test_handle_errors_exception_not_raise(self):
        """Test handle_errors when exception occurs (not raising)."""
        mock_db = MagicMock()
        mock_db.integrity.check_integrity.side_effect = Exception("DB error")

        recovery = DatabaseRecovery(mock_db)
        result = recovery.handle_errors(raise_on_error=False)

        assert result is False

    def test_handle_errors_exception_raise(self):
        """Test handle_errors when exception occurs (raising)."""
        mock_db = MagicMock()
        mock_db.integrity.check_integrity.side_effect = Exception("DB error")

        recovery = DatabaseRecovery(mock_db)

        with pytest.raises(Exception, match="DB error"):
            recovery.handle_errors(raise_on_error=True)


class TestDatabaseOptimizationCoverage:
    """Tests for DatabaseOptimization class to achieve 100% coverage."""

    def test_optimize_query_basic(self):
        """Test optimize_query strips and removes trailing semicolon."""
        mock_db = MagicMock()
        optimization = DatabaseOptimization(mock_db)

        result = optimization.optimize_query("SELECT * FROM test;  ")

        assert result == "SELECT * FROM test"

    def test_optimize_query_no_semicolon(self):
        """Test optimize_query when no trailing semicolon."""
        mock_db = MagicMock()
        optimization = DatabaseOptimization(mock_db)

        result = optimization.optimize_query("SELECT * FROM test")

        assert result == "SELECT * FROM test"

    def test_optimize_query_whitespace_only(self):
        """Test optimize_query with whitespace-only query."""
        mock_db = MagicMock()
        optimization = DatabaseOptimization(mock_db)

        result = optimization.optimize_query("  ;  ")

        assert result == ""

    def test_optimize_query_empty(self):
        """Test optimize_query with empty query."""
        mock_db = MagicMock()
        optimization = DatabaseOptimization(mock_db)

        result = optimization.optimize_query("")

        assert result == ""
