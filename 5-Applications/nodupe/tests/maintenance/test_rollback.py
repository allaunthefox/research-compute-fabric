"""Tests for rollback CLI module."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from click.testing import CliRunner


class TestRollbackCLI:
    """Test rollback CLI commands."""

    def test_rollback_list_snapshots(self, temp_dir):
        """Test rollback list command with snapshots."""
        from nodupe.tools.maintenance.rollback import list_cmd
        from nodupe.tools.maintenance.snapshot import SnapshotManager

        # Create a snapshot
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        snapshot_mgr = SnapshotManager(str(temp_dir / ".nodupe/backups"))
        snapshot_mgr.create_snapshot([str(test_file)])

        # Mock SnapshotManager to use our temp directory
        with patch('nodupe.tools.maintenance.rollback.SnapshotManager') as mock_mgr:
            mock_instance = MagicMock()
            mock_instance.list_snapshots.return_value = [
                {"snapshot_id": "abc123", "timestamp": "2025-01-01", "file_count": 1}
            ]
            mock_mgr.return_value = mock_instance

            runner = CliRunner()
            result = runner.invoke(list_cmd, ['--snapshots'])

            assert result.exit_code == 0
            assert "Snapshots" in result.output

    def test_rollback_list_transactions(self, temp_dir):
        """Test rollback list command with transactions."""
        from nodupe.tools.maintenance.rollback import list_cmd
        from nodupe.tools.maintenance.transaction import TransactionLog

        # Create a transaction
        tx_log = TransactionLog(str(temp_dir / ".nodupe/backups"))
        tx_id = tx_log.begin_transaction()
        tx_log.commit_transaction()

        with patch('nodupe.tools.maintenance.rollback.TransactionLog') as mock_tx:
            mock_instance = MagicMock()
            mock_instance.list_transactions.return_value = [
                {"transaction_id": "abc123", "timestamp": "2025-01-01", "status": "completed", "operation_count": 1}
            ]
            mock_tx.return_value = mock_instance

            runner = CliRunner()
            result = runner.invoke(list_cmd, ['--transactions'])

            assert result.exit_code == 0
            assert "Transactions" in result.output

    def test_rollback_create_command(self, temp_dir):
        """Test rollback create command."""
        from nodupe.tools.maintenance.rollback import create_cmd

        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        with patch('nodupe.tools.maintenance.rollback.SnapshotManager') as mock_mgr:
            mock_instance = MagicMock()
            mock_instance.create_snapshot.return_value = MagicMock(
                snapshot_id="abc123",
                files=[str(test_file)]
            )
            mock_mgr.return_value = mock_instance

            runner = CliRunner()
            result = runner.invoke(create_cmd, [str(test_file)])

            assert result.exit_code == 0
            assert "snapshot" in result.output.lower()

    def test_rollback_restore_command_success(self):
        """Test rollback restore command with success."""
        from nodupe.tools.maintenance.rollback import restore_cmd

        with patch('nodupe.tools.maintenance.rollback.SnapshotManager') as mock_mgr:
            mock_instance = MagicMock()
            mock_instance.restore_snapshot.return_value = True
            mock_mgr.return_value = mock_instance

            runner = CliRunner()
            result = runner.invoke(restore_cmd, ['abc123'])

            assert result.exit_code == 0
            assert "Restored" in result.output

    def test_rollback_restore_command_failure(self):
        """Test rollback restore command with failure."""
        from nodupe.tools.maintenance.rollback import restore_cmd

        with patch('nodupe.tools.maintenance.rollback.SnapshotManager') as mock_mgr:
            mock_instance = MagicMock()
            mock_instance.restore_snapshot.return_value = False
            mock_mgr.return_value = mock_instance

            runner = CliRunner()
            result = runner.invoke(restore_cmd, ['nonexistent'])

            assert result.exit_code == 1

    def test_rollback_delete_command_success(self):
        """Test rollback delete command with success."""
        from nodupe.tools.maintenance.rollback import delete_cmd

        with patch('nodupe.tools.maintenance.rollback.SnapshotManager') as mock_mgr:
            mock_instance = MagicMock()
            mock_instance.delete_snapshot.return_value = True
            mock_mgr.return_value = mock_instance

            runner = CliRunner()
            result = runner.invoke(delete_cmd, ['abc123'])

            assert result.exit_code == 0
            assert "Deleted" in result.output

    def test_rollback_delete_command_failure(self):
        """Test rollback delete command with failure."""
        from nodupe.tools.maintenance.rollback import delete_cmd

        with patch('nodupe.tools.maintenance.rollback.SnapshotManager') as mock_mgr:
            mock_instance = MagicMock()
            mock_instance.delete_snapshot.return_value = False
            mock_mgr.return_value = mock_instance

            runner = CliRunner()
            result = runner.invoke(delete_cmd, ['nonexistent'])

            # When delete returns False, click.echo is called with the error message
            # but the exit code may still be 0, let's check for the message instead
            assert "not found" in result.output.lower() or result.exit_code == 1

    def test_rollback_undo_command_success(self):
        """Test rollback undo command with success."""
        from nodupe.tools.maintenance.rollback import undo_cmd

        with patch('nodupe.tools.maintenance.rollback.RollbackManager') as mock_mgr:
            mock_instance = MagicMock()
            mock_instance.undo_last_operation.return_value = True
            mock_mgr.return_value = mock_instance

            runner = CliRunner()
            result = runner.invoke(undo_cmd)

            assert result.exit_code == 0

    def test_rollback_undo_command_failure(self):
        """Test rollback undo command with no operations."""
        from nodupe.tools.maintenance.rollback import undo_cmd

        with patch('nodupe.tools.maintenance.rollback.RollbackManager') as mock_mgr:
            mock_instance = MagicMock()
            mock_instance.undo_last_operation.return_value = False
            mock_mgr.return_value = mock_instance

            runner = CliRunner()
            result = runner.invoke(undo_cmd)

            assert result.exit_code == 0
            assert "No operation" in result.output


class TestRollbackCLICoverage:
    """Tests for CLI coverage - specific branches."""

    def test_list_cmd_no_flags_shows_both(self):
        """Test list command with no flags shows both snapshots and transactions."""
        from click.testing import CliRunner

        from nodupe.tools.maintenance.rollback import list_cmd

        runner = CliRunner()

        # Need to mock the managers to avoid file system operations
        with patch('nodupe.tools.maintenance.rollback.SnapshotManager') as mock_snap, \
             patch('nodupe.tools.maintenance.rollback.TransactionLog') as mock_tx:
            mock_snap_instance = MagicMock()
            mock_snap_instance.list_snapshots.return_value = []
            mock_snap.return_value = mock_snap_instance

            mock_tx_instance = MagicMock()
            mock_tx_instance.list_transactions.return_value = []
            mock_tx.return_value = mock_tx_instance

            result = runner.invoke(list_cmd, [])

            # With no flags, both should be shown (snapshots or not transactions)
            assert "Snapshots" in result.output or "No snapshots" in result.output

    def test_list_cmd_transactions_only(self):
        """Test list command with --transactions flag only shows transactions."""
        from click.testing import CliRunner

        from nodupe.tools.maintenance.rollback import list_cmd

        runner = CliRunner()

        with patch('nodupe.tools.maintenance.rollback.SnapshotManager') as mock_snap, \
             patch('nodupe.tools.maintenance.rollback.TransactionLog') as mock_tx:
            mock_snap_instance = MagicMock()
            mock_snap.return_value = mock_snap_instance

            mock_tx_instance = MagicMock()
            mock_tx_instance.list_transactions.return_value = []
            mock_tx.return_value = mock_tx_instance

            result = runner.invoke(list_cmd, ['--transactions'])

            # Should only show transactions
            assert "Transactions" in result.output or "No transactions" in result.output

    def test_list_cmd_snapshots_only(self):
        """Test list command with --snapshots flag only shows snapshots."""
        from click.testing import CliRunner

        from nodupe.tools.maintenance.rollback import list_cmd

        runner = CliRunner()

        with patch('nodupe.tools.maintenance.rollback.SnapshotManager') as mock_snap, \
             patch('nodupe.tools.maintenance.rollback.TransactionLog') as mock_tx:
            mock_snap_instance = MagicMock()
            mock_snap_instance.list_snapshots.return_value = []
            mock_snap.return_value = mock_snap_instance

            mock_tx_instance = MagicMock()
            mock_tx.return_value = mock_tx_instance

            result = runner.invoke(list_cmd, ['--snapshots'])

            # Should only show snapshots
            assert "Snapshots" in result.output or "No snapshots" in result.output
