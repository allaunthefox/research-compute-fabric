"""Tests for rollback manager module."""

from unittest.mock import MagicMock, patch

import pytest


class TestRollbackManager:
    """Test RollbackManager class."""

    def test_execute_with_protection_success(self, temp_dir):
        """Test successful execution with rollback protection."""
        from nodupe.tools.maintenance.manager import RollbackManager
        from nodupe.tools.maintenance.snapshot import SnapshotManager
        from nodupe.tools.maintenance.transaction import TransactionLog

        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("original content")

        # Create managers
        snapshot_mgr = SnapshotManager(str(temp_dir / ".nodupe/backups"))
        tx_log = TransactionLog(str(temp_dir / ".nodupe/backups"))
        rollback_mgr = RollbackManager(snapshot_mgr, tx_log)

        # Define operation that modifies file
        def modify_operation():
            """Modify the test file content."""
            test_file.write_text("modified content")
            return "success"

        # Execute with protection
        result = rollback_mgr.execute_with_protection([str(test_file)], modify_operation)

        assert result == "success"
        assert test_file.read_text() == "modified content"

    def test_execute_with_protection_rollback_on_failure(self, temp_dir):
        """Test rollback on operation failure."""
        from nodupe.tools.maintenance.manager import RollbackManager
        from nodupe.tools.maintenance.snapshot import SnapshotManager
        from nodupe.tools.maintenance.transaction import TransactionLog

        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("original content")

        # Create managers
        snapshot_mgr = SnapshotManager(str(temp_dir / ".nodupe/backups"))
        tx_log = TransactionLog(str(temp_dir / ".nodupe/backups"))
        rollback_mgr = RollbackManager(snapshot_mgr, tx_log)

        # Define failing operation
        def failing_operation():
            """Failing operation that raises an error."""
            test_file.write_text("modified content")
            raise ValueError("Operation failed")

        # Execute with protection - should raise
        with pytest.raises(ValueError):
            rollback_mgr.execute_with_protection([str(test_file)], failing_operation)

        # File should be rolled back to original content
        assert test_file.read_text() == "original content"

    def test_restore_to_snapshot(self, temp_dir):
        """Test restore to snapshot."""
        from nodupe.tools.maintenance.manager import RollbackManager
        from nodupe.tools.maintenance.snapshot import SnapshotManager
        from nodupe.tools.maintenance.transaction import TransactionLog

        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("original content")

        # Create managers
        snapshot_mgr = SnapshotManager(str(temp_dir / ".nodupe/backups"))
        tx_log = TransactionLog(str(temp_dir / ".nodupe/backups"))
        rollback_mgr = RollbackManager(snapshot_mgr, tx_log)

        # Create snapshot
        snapshot = snapshot_mgr.create_snapshot([str(test_file)])

        # Modify file
        test_file.write_text("modified content")

        # Restore to snapshot
        result = rollback_mgr.restore_to_snapshot(snapshot.snapshot_id)

        assert result is True
        assert test_file.read_text() == "original content"

    def test_undo_last_operation_no_transactions(self):
        """Test undo when no transactions exist."""
        from nodupe.tools.maintenance.manager import RollbackManager
        from nodupe.tools.maintenance.snapshot import SnapshotManager
        from nodupe.tools.maintenance.transaction import TransactionLog

        # Create managers with empty directories
        snapshot_mgr = MagicMock()
        tx_log = TransactionLog()
        rollback_mgr = RollbackManager(snapshot_mgr, tx_log)

        result = rollback_mgr.undo_last_operation()

        assert result is False

    def test_undo_last_operation_with_completed(self, temp_dir):
        """Test undo with completed transaction."""
        from nodupe.tools.maintenance.manager import RollbackManager
        from nodupe.tools.maintenance.snapshot import SnapshotManager
        from nodupe.tools.maintenance.transaction import Operation, OperationType, TransactionLog

        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("original content")

        # Create managers
        snapshot_mgr = SnapshotManager(str(temp_dir / ".nodupe/backups"))
        tx_log = TransactionLog(str(temp_dir / ".nodupe/backups"))
        rollback_mgr = RollbackManager(snapshot_mgr, tx_log)

        # Manually create a transaction
        tx_id = tx_log.begin_transaction()

        # Add operation
        operation = Operation(
            operation_type=OperationType.MODIFY.value,
            path=str(test_file),
            original_hash="abc123",
            backup_path=str(temp_dir / "backup.txt")
        )
        tx_log.log_operation(operation)

        # Commit transaction
        tx_log.commit_transaction()

        # Modify file
        test_file.write_text("modified content")

        # Undo last operation
        result = rollback_mgr.undo_last_operation()

        assert result is True

    def test_list_snapshots(self, temp_dir):
        """Test listing snapshots."""
        from nodupe.tools.maintenance.manager import RollbackManager
        from nodupe.tools.maintenance.snapshot import SnapshotManager
        from nodupe.tools.maintenance.transaction import TransactionLog

        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        # Create managers
        snapshot_mgr = SnapshotManager(str(temp_dir / ".nodupe/backups"))
        tx_log = TransactionLog(str(temp_dir / ".nodupe/backups"))
        rollback_mgr = RollbackManager(snapshot_mgr, tx_log)

        # Create a snapshot
        snapshot_mgr.create_snapshot([str(test_file)])

        # List snapshots
        snapshots = rollback_mgr.list_snapshots()

        assert len(snapshots) >= 1
        assert 'snapshot_id' in snapshots[0]

    def test_list_transactions(self, temp_dir):
        """Test listing transactions."""
        from nodupe.tools.maintenance.manager import RollbackManager
        from nodupe.tools.maintenance.snapshot import SnapshotManager
        from nodupe.tools.maintenance.transaction import TransactionLog

        # Create managers
        snapshot_mgr = SnapshotManager(str(temp_dir / ".nodupe/backups"))
        tx_log = TransactionLog(str(temp_dir / ".nodupe/backups"))
        rollback_mgr = RollbackManager(snapshot_mgr, tx_log)

        # Begin and commit a transaction
        tx_id = tx_log.begin_transaction()
        tx_log.commit_transaction()

        # List transactions
        transactions = rollback_mgr.list_transactions()

        assert len(transactions) >= 1
        assert 'transaction_id' in transactions[0]


    def test_undo_last_operation_no_completed_transactions(self):
        """Test undo when transactions exist but none are completed."""
        from nodupe.tools.maintenance.manager import RollbackManager
        from nodupe.tools.maintenance.snapshot import SnapshotManager
        from nodupe.tools.maintenance.transaction import TransactionLog

        # Create mock managers
        snapshot_mgr = MagicMock()
        tx_log = MagicMock()

        # Mock transactions with no completed transactions
        tx_log.list_transactions.return_value = [
            {"transaction_id": "tx1", "status": "pending", "operation_count": 1},
            {"transaction_id": "tx2", "status": "rolled_back", "operation_count": 2},
        ]

        rollback_mgr = RollbackManager(snapshot_mgr, tx_log)
        result = rollback_mgr.undo_last_operation()

        # Should return False since no completed transaction found
        assert result is False
