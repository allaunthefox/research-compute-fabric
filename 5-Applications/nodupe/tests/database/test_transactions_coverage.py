# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 NoDupeLabs

"""Tests to achieve 100% coverage on transactions.py module.

This test file targets the missing coverage in:
- transactions.py: Nested transaction edge cases, context manager paths
"""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.databases.transactions import (
    DatabaseTransaction,
    DatabaseTransactions,
    IsolationLevel,
    TransactionError,
    create_transaction_manager,
)


class TestDatabaseTransactionCoverage:
    """Tests for DatabaseTransaction class to achieve 100% coverage."""

    @pytest.fixture
    def in_memory_connection(self):
        """Create an in-memory SQLite database connection."""
        conn = sqlite3.connect(":memory:")
        yield conn
        conn.close()

    def test_execute_in_transaction_started_here(self):
        """Test execute_in_transaction when it starts the transaction."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        # Mock begin_transaction to not raise
        tx = DatabaseTransaction(mock_conn)

        operation = MagicMock(return_value="result")

        result = tx.execute_in_transaction(operation, "arg1", kwarg="value")

        assert result == "result"
        operation.assert_called_once_with("arg1", kwarg="value")
        # commit should have been called
        mock_conn.commit.assert_called_once()

    def test_execute_in_transaction_already_active(self):
        """Test execute_in_transaction when transaction is already active."""
        mock_conn = MagicMock()
        tx = DatabaseTransaction(mock_conn)
        tx._in_transaction = True  # Simulate active transaction

        operation = MagicMock(return_value="result")

        result = tx.execute_in_transaction(operation)

        assert result == "result"
        # Should not call begin_transaction again
        assert mock_conn.execute.call_count == 0
        # Should not commit since we didn't start it
        mock_conn.commit.assert_not_called()

    def test_execute_in_transaction_operation_raises(self):
        """Test execute_in_transaction when operation raises exception."""
        mock_conn = MagicMock()
        tx = DatabaseTransaction(mock_conn)

        operation = MagicMock(side_effect=Exception("Operation failed"))

        with pytest.raises(TransactionError, match="Transaction execution failed"):
            tx.execute_in_transaction(operation)

        mock_conn.rollback.assert_called_once()

    def test_execute_in_transaction_already_active_operation_raises(self):
        """Test execute_in_transaction when active tx and operation raises."""
        mock_conn = MagicMock()
        tx = DatabaseTransaction(mock_conn)
        tx._in_transaction = True

        operation = MagicMock(side_effect=Exception("Operation failed"))

        with pytest.raises(Exception, match="Operation failed"):
            tx.execute_in_transaction(operation)

        # Should not rollback since we didn't start the transaction
        mock_conn.rollback.assert_not_called()

    def test_execute_in_transaction_wraps_transaction_error(self):
        """Test execute_in_transaction re-raises TransactionError."""
        mock_conn = MagicMock()
        tx = DatabaseTransaction(mock_conn)

        # Make begin_transaction raise TransactionError
        with patch.object(tx, 'begin_transaction', side_effect=TransactionError("TX error")):
            with pytest.raises(TransactionError, match="TX error"):
                tx.execute_in_transaction(MagicMock())

    def test_transaction_context_manager_success(self, in_memory_connection):
        """Test transaction context manager on success."""
        tx = DatabaseTransaction(in_memory_connection)

        with tx.transaction():
            in_memory_connection.execute("CREATE TABLE test (id INTEGER)")

        # Should be committed
        assert not tx.is_active

    def test_transaction_context_manager_exception(self, in_memory_connection):
        """Test transaction context manager on exception."""
        tx = DatabaseTransaction(in_memory_connection)

        try:
            with tx.transaction():
                in_memory_connection.execute("CREATE TABLE test (id INTEGER)")
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should be rolled back
        assert not tx.is_active

    def test_savepoint_context_manager_success(self, in_memory_connection):
        """Test savepoint context manager on success."""
        tx = DatabaseTransaction(in_memory_connection)
        tx.begin_transaction()
        in_memory_connection.execute("CREATE TABLE test (id INTEGER)")

        with tx.savepoint("sp1"):
            in_memory_connection.execute("INSERT INTO test VALUES (1)")

        # Savepoint should be released
        assert "sp1" not in tx._savepoints

    def test_savepoint_context_manager_exception(self, in_memory_connection):
        """Test savepoint context manager on exception."""
        tx = DatabaseTransaction(in_memory_connection)
        tx.begin_transaction()
        in_memory_connection.execute("CREATE TABLE test (id INTEGER)")

        try:
            with tx.savepoint("sp1"):
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should have rolled back to savepoint
        # Savepoint should still exist after rollback

    def test_enter_context_manager(self, in_memory_connection):
        """Test __enter__ context manager method."""
        tx = DatabaseTransaction(in_memory_connection)

        result = tx.__enter__()

        assert result is tx
        assert tx.is_active

    def test_exit_context_manager_no_exception(self, in_memory_connection):
        """Test __exit__ without exception commits."""
        tx = DatabaseTransaction(in_memory_connection)
        tx.begin_transaction()

        result = tx.__exit__(None, None, None)

        assert result is False
        assert not tx.is_active

    def test_exit_context_manager_with_exception(self, in_memory_connection):
        """Test __exit__ with exception rolls back."""
        tx = DatabaseTransaction(in_memory_connection)
        tx.begin_transaction()

        result = tx.__exit__(ValueError, ValueError("test"), None)

        assert result is False
        assert not tx.is_active

    def test_is_active_property(self, in_memory_connection):
        """Test is_active property."""
        tx = DatabaseTransaction(in_memory_connection)

        assert tx.is_active is False

        tx.begin_transaction()
        assert tx.is_active is True

        tx.commit_transaction()
        assert tx.is_active is False


class TestDatabaseTransactionsCoverage:
    """Tests for DatabaseTransactions class to achieve 100% coverage."""

    @pytest.fixture
    def in_memory_connection(self):
        """Create an in-memory SQLite database connection."""
        conn = sqlite3.connect(":memory:")
        yield conn
        conn.close()

    def test_begin_transaction(self, in_memory_connection):
        """Test begin_transaction creates and begins transaction."""
        factory = DatabaseTransactions(in_memory_connection)

        tx = factory.begin_transaction()

        assert isinstance(tx, DatabaseTransaction)
        assert tx.is_active

    def test_begin_transaction_with_isolation_level(self, in_memory_connection):
        """Test begin_transaction with custom isolation level."""
        factory = DatabaseTransactions(in_memory_connection)

        tx = factory.begin_transaction(isolation_level=IsolationLevel.EXCLUSIVE)

        assert tx.isolation_level == IsolationLevel.EXCLUSIVE

    def test_commit_transaction_legacy(self, in_memory_connection):
        """Test commit_transaction legacy method."""
        factory = DatabaseTransactions(in_memory_connection)

        # Start a transaction
        in_memory_connection.execute("BEGIN")

        factory.commit_transaction()
        # Should not raise

    def test_commit_transaction_legacy_error(self):
        """Test commit_transaction legacy method error."""
        mock_conn = MagicMock()
        mock_conn.commit.side_effect = sqlite3.Error("Commit failed")
        factory = DatabaseTransactions(mock_conn)

        with pytest.raises(TransactionError, match="Commit failed"):
            factory.commit_transaction()

    def test_rollback_transaction_legacy(self, in_memory_connection):
        """Test rollback_transaction legacy method."""
        factory = DatabaseTransactions(in_memory_connection)

        # Start a transaction
        in_memory_connection.execute("BEGIN")

        factory.rollback_transaction()
        # Should not raise

    def test_rollback_transaction_legacy_error(self):
        """Test rollback_transaction legacy method error."""
        mock_conn = MagicMock()
        mock_conn.rollback.side_effect = sqlite3.Error("Rollback failed")
        factory = DatabaseTransactions(mock_conn)

        with pytest.raises(TransactionError, match="Rollback failed"):
            factory.rollback_transaction()

    def test_transaction_context_manager(self, in_memory_connection):
        """Test transaction context manager."""
        factory = DatabaseTransactions(in_memory_connection)

        with factory.transaction() as tx:
            assert isinstance(tx, DatabaseTransaction)
            in_memory_connection.execute("CREATE TABLE test (id INTEGER)")

        # Transaction should be committed
        assert not tx.is_active

    def test_transaction_context_manager_exception(self, in_memory_connection):
        """Test transaction context manager with exception."""
        factory = DatabaseTransactions(in_memory_connection)

        try:
            with factory.transaction() as tx:
                in_memory_connection.execute("CREATE TABLE test (id INTEGER)")
                raise ValueError("Test error")
        except ValueError:
            pass

        # Transaction should be rolled back
        assert not tx.is_active

    def test_savepoint_context_manager(self, in_memory_connection):
        """Test savepoint context manager."""
        factory = DatabaseTransactions(in_memory_connection)

        # Start a transaction first and create table
        in_memory_connection.execute("BEGIN")
        in_memory_connection.execute("CREATE TABLE test (id INTEGER)")

        with factory.savepoint("sp1") as sp_name:
            assert sp_name == "sp1"
            in_memory_connection.execute("INSERT INTO test VALUES (1)")

        # Savepoint should be released

    def test_savepoint_context_manager_exception(self, in_memory_connection):
        """Test savepoint context manager with exception."""
        factory = DatabaseTransactions(in_memory_connection)

        # Start a transaction first
        in_memory_connection.execute("BEGIN")
        in_memory_connection.execute("CREATE TABLE test (id INTEGER)")

        try:
            with factory.savepoint("sp1"):
                in_memory_connection.execute("INSERT INTO test VALUES (1)")
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should have rolled back to savepoint

    def test_execute_in_transaction(self, in_memory_connection):
        """Test execute_in_transaction method."""
        factory = DatabaseTransactions(in_memory_connection)

        operation = MagicMock(return_value="result")

        result = factory.execute_in_transaction(operation, "arg1", kwarg="value")

        assert result == "result"
        operation.assert_called_once_with("arg1", kwarg="value")

    def test_execute_in_transaction_with_isolation_level(self, in_memory_connection):
        """Test execute_in_transaction with custom isolation level."""
        factory = DatabaseTransactions(in_memory_connection)

        operation = MagicMock(return_value="result")

        result = factory.execute_in_transaction(
            operation,
            isolation_level=IsolationLevel.IMMEDIATE
        )

        assert result == "result"


class TestCreateTransactionManagerCoverage:
    """Tests for create_transaction_manager function."""

    def test_create_transaction_manager(self):
        """Test create_transaction_manager returns DatabaseTransactions."""
        conn = sqlite3.connect(":memory:")
        try:
            manager = create_transaction_manager(conn)

            assert isinstance(manager, DatabaseTransactions)
            assert manager.connection is conn
        finally:
            conn.close()


class TestIsolationLevelCoverage:
    """Tests for IsolationLevel enum."""

    def test_isolation_level_values(self):
        """Test IsolationLevel enum values."""
        assert IsolationLevel.DEFERRED.value == "DEFERRED"
        assert IsolationLevel.IMMEDIATE.value == "IMMEDIATE"
        assert IsolationLevel.EXCLUSIVE.value == "EXCLUSIVE"

    def test_isolation_level_names(self):
        """Test IsolationLevel enum names."""
        assert IsolationLevel.DEFERRED.name == "DEFERRED"
        assert IsolationLevel.IMMEDIATE.name == "IMMEDIATE"
        assert IsolationLevel.EXCLUSIVE.name == "EXCLUSIVE"


class TestTransactionErrorCoverage:
    """Tests for TransactionError exception."""

    def test_transaction_error_creation(self):
        """Test TransactionError can be created."""
        error = TransactionError("Test error")
        assert str(error) == "Test error"

    def test_transaction_error_with_cause(self):
        """Test TransactionError with cause."""
        try:
            try:
                raise sqlite3.Error("SQLite error")
            except sqlite3.Error as e:
                raise TransactionError("Transaction failed") from e
        except TransactionError as te:
            assert te.__cause__ is not None
            assert isinstance(te.__cause__, sqlite3.Error)
