"""Comprehensive tests for the Transaction module.

Tests cover:
- OperationType enum
- Operation dataclass
- TransactionLog initialization
- Transaction lifecycle (begin, log, commit, rollback)
- Error conditions and edge cases
- File persistence
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from nodupe.tools.maintenance.transaction import (
    Operation,
    OperationType,
    TransactionLog,
)


class TestOperationType:
    """Tests for OperationType enum."""

    def test_operation_type_values(self):
        """Test that OperationType has expected values."""
        assert OperationType.DELETE.value == "delete"
        assert OperationType.MODIFY.value == "modify"
        assert OperationType.MOVE.value == "move"
        assert OperationType.COPY.value == "copy"
        assert OperationType.RESTORE.value == "restore"

    def test_operation_type_count(self):
        """Test number of operation types."""
        assert len(list(OperationType)) == 5

    def test_operation_type_from_string(self):
        """Test accessing OperationType by value."""
        assert OperationType("delete") == OperationType.DELETE
        assert OperationType("modify") == OperationType.MODIFY
        assert OperationType("move") == OperationType.MOVE
        assert OperationType("copy") == OperationType.COPY
        assert OperationType("restore") == OperationType.RESTORE

    def test_operation_type_invalid_string(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError):
            OperationType("invalid")


class TestOperation:
    """Tests for Operation dataclass."""

    def test_operation_creation_minimal(self):
        """Test creating Operation with minimal fields."""
        op = Operation(
            operation_type="delete",
            path="/test/file.txt"
        )
        assert op.operation_type == "delete"
        assert op.path == "/test/file.txt"
        assert op.original_hash is None
        assert op.backup_path is None
        assert op.new_path is None

    def test_operation_creation_full(self):
        """Test creating Operation with all fields."""
        op = Operation(
            operation_type="modify",
            path="/test/file.txt",
            original_hash="abc123",
            backup_path="/backup/abc123",
            new_path="/test/file_renamed.txt"
        )
        assert op.operation_type == "modify"
        assert op.path == "/test/file.txt"
        assert op.original_hash == "abc123"
        assert op.backup_path == "/backup/abc123"
        assert op.new_path == "/test/file_renamed.txt"

    def test_operation_to_dict(self):
        """Test converting Operation to dictionary."""
        op = Operation(
            operation_type="move",
            path="/src/file.txt",
            new_path="/dst/file.txt"
        )
        data = op.to_dict()
        assert data["operation_type"] == "move"
        assert data["path"] == "/src/file.txt"
        assert data["new_path"] == "/dst/file.txt"
        assert data["original_hash"] is None
        assert data["backup_path"] is None

    def test_operation_to_dict_all_fields(self):
        """Test to_dict with all fields populated."""
        op = Operation(
            operation_type="modify",
            path="/test/file.txt",
            original_hash="abc123",
            backup_path="/backup/abc123",
            new_path=None
        )
        data = op.to_dict()
        assert data["operation_type"] == "modify"
        assert data["path"] == "/test/file.txt"
        assert data["original_hash"] == "abc123"
        assert data["backup_path"] == "/backup/abc123"
        assert data["new_path"] is None

    def test_operation_from_dict(self):
        """Test creating Operation from dictionary."""
        data = {
            "operation_type": "copy",
            "path": "/src/file.txt",
            "original_hash": "def456",
            "backup_path": "/backup/def456",
            "new_path": "/dst/file.txt"
        }
        op = Operation.from_dict(data)
        assert op.operation_type == "copy"
        assert op.path == "/src/file.txt"
        assert op.original_hash == "def456"
        assert op.backup_path == "/backup/def456"
        assert op.new_path == "/dst/file.txt"

    def test_operation_from_dict_minimal(self):
        """Test creating Operation from minimal dictionary."""
        data = {
            "operation_type": "delete",
            "path": "/test/file.txt"
        }
        op = Operation.from_dict(data)
        assert op.operation_type == "delete"
        assert op.path == "/test/file.txt"
        assert op.original_hash is None
        assert op.backup_path is None
        assert op.new_path is None

    def test_operation_roundtrip(self):
        """Test Operation to_dict and from_dict roundtrip."""
        original = Operation(
            operation_type="modify",
            path="/test/file.txt",
            original_hash="abc123",
            backup_path="/backup/abc123",
            new_path="/test/file_new.txt"
        )
        data = original.to_dict()
        restored = Operation.from_dict(data)
        assert restored.operation_type == original.operation_type
        assert restored.path == original.path
        assert restored.original_hash == original.original_hash
        assert restored.backup_path == original.backup_path
        assert restored.new_path == original.new_path


class TestTransactionLog:
    """Tests for TransactionLog class."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary log directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def transaction_log(self, temp_log_dir):
        """Create a TransactionLog instance with temp directory."""
        return TransactionLog(log_dir=str(temp_log_dir))

    # Initialization Tests
    def test_transaction_log_initialization(self, temp_log_dir):
        """Test TransactionLog initialization creates directories."""
        log = TransactionLog(log_dir=str(temp_log_dir))
        assert log.log_dir == temp_log_dir
        assert log.transaction_dir.exists()
        assert log.transaction_dir == temp_log_dir / "transactions"
        assert log.current_transaction is None
        assert log.current_operations == []

    def test_transaction_log_default_dir(self):
        """Test TransactionLog with default directory."""
        log = TransactionLog()
        assert log.log_dir == Path(".nodupe/backups")
        assert log.transaction_dir.exists()

    def test_transaction_log_creates_transaction_dir(self, temp_log_dir):
        """Test that transaction directory is created if it doesn't exist."""
        # Remove the transactions subdirectory
        tx_dir = temp_log_dir / "transactions"
        if tx_dir.exists():
            tx_dir.rmdir()

        log = TransactionLog(log_dir=str(temp_log_dir))
        assert log.transaction_dir.exists()

    # Begin Transaction Tests
    def test_begin_transaction(self, transaction_log):
        """Test beginning a transaction."""
        tx_id = transaction_log.begin_transaction()
        assert tx_id is not None
        assert len(tx_id) == 8  # UUID truncated to 8 chars
        assert transaction_log.current_transaction == tx_id
        assert transaction_log.current_operations == []

    def test_begin_transaction_multiple(self, transaction_log):
        """Test beginning multiple transactions."""
        tx_id1 = transaction_log.begin_transaction()
        transaction_log.commit_transaction()

        tx_id2 = transaction_log.begin_transaction()
        assert tx_id1 != tx_id2
        assert transaction_log.current_transaction == tx_id2

    def test_begin_transaction_generates_unique_ids(self, transaction_log):
        """Test that each transaction gets a unique ID."""
        ids = set()
        for _ in range(100):
            tx_id = transaction_log.begin_transaction()
            transaction_log.commit_transaction()
            ids.add(tx_id)
        # All IDs should be unique
        assert len(ids) == 100

    # Log Operation Tests
    def test_log_operation(self, transaction_log):
        """Test logging an operation."""
        transaction_log.begin_transaction()
        op = Operation(operation_type="delete", path="/test/file.txt")
        transaction_log.log_operation(op)

        assert len(transaction_log.current_operations) == 1
        assert transaction_log.current_operations[0] == op

    def test_log_operation_multiple(self, transaction_log):
        """Test logging multiple operations."""
        transaction_log.begin_transaction()

        ops = [
            Operation(operation_type="delete", path="/test/file1.txt"),
            Operation(operation_type="modify", path="/test/file2.txt"),
            Operation(operation_type="move", path="/test/file3.txt", new_path="/test/file3_new.txt"),
        ]

        for op in ops:
            transaction_log.log_operation(op)

        assert len(transaction_log.current_operations) == 3
        assert transaction_log.current_operations == ops

    def test_log_operation_no_active_transaction(self, transaction_log):
        """Test that logging operation without transaction raises error."""
        op = Operation(operation_type="delete", path="/test/file.txt")
        with pytest.raises(RuntimeError) as exc_info:
            transaction_log.log_operation(op)
        assert "No active transaction" in str(exc_info.value)
        assert "begin_transaction()" in str(exc_info.value)

    def test_log_operation_after_commit(self, transaction_log):
        """Test that logging operation after commit raises error."""
        transaction_log.begin_transaction()
        transaction_log.commit_transaction()

        op = Operation(operation_type="delete", path="/test/file.txt")
        with pytest.raises(RuntimeError):
            transaction_log.log_operation(op)

    # Commit Transaction Tests
    def test_commit_transaction(self, transaction_log):
        """Test committing a transaction."""
        tx_id = transaction_log.begin_transaction()
        transaction_log.log_operation(
            Operation(operation_type="delete", path="/test/file.txt")
        )

        committed_id = transaction_log.commit_transaction()
        assert committed_id == tx_id
        assert transaction_log.current_transaction is None
        assert transaction_log.current_operations == []

    def test_commit_transaction_creates_file(self, transaction_log, temp_log_dir):
        """Test that commit creates a JSON file."""
        tx_id = transaction_log.begin_transaction()
        transaction_log.log_operation(
            Operation(operation_type="delete", path="/test/file.txt")
        )

        transaction_log.commit_transaction()

        tx_path = temp_log_dir / "transactions" / f"{tx_id}.json"
        assert tx_path.exists()

    def test_commit_transaction_file_content(self, transaction_log, temp_log_dir):
        """Test committed transaction file content."""
        tx_id = transaction_log.begin_transaction()
        op = Operation(
            operation_type="modify",
            path="/test/file.txt",
            original_hash="abc123"
        )
        transaction_log.log_operation(op)
        transaction_log.commit_transaction()

        tx_path = temp_log_dir / "transactions" / f"{tx_id}.json"
        with open(tx_path) as f:
            data = json.load(f)

        assert data["transaction_id"] == tx_id
        assert "timestamp" in data
        assert len(data["operations"]) == 1
        assert data["operations"][0]["operation_type"] == "modify"
        assert data["status"] == "completed"

    def test_commit_transaction_timestamp(self, transaction_log, temp_log_dir):
        """Test that commit includes timestamp."""
        from datetime import datetime

        tx_id = transaction_log.begin_transaction()
        transaction_log.commit_transaction()

        tx_path = temp_log_dir / "transactions" / f"{tx_id}.json"
        with open(tx_path) as f:
            data = json.load(f)

        # Verify timestamp is valid ISO format
        datetime.fromisoformat(data["timestamp"])

    def test_commit_transaction_no_active_transaction(self, transaction_log):
        """Test that commit without transaction raises error."""
        with pytest.raises(RuntimeError) as exc_info:
            transaction_log.commit_transaction()
        assert "No active transaction" in str(exc_info.value)

    def test_commit_transaction_empty_operations(self, transaction_log, temp_log_dir):
        """Test committing transaction with no operations."""
        tx_id = transaction_log.begin_transaction()
        committed_id = transaction_log.commit_transaction()

        assert committed_id == tx_id

        tx_path = temp_log_dir / "transactions" / f"{tx_id}.json"
        with open(tx_path) as f:
            data = json.load(f)

        assert data["operations"] == []
        assert data["status"] == "completed"

    # Rollback Transaction Tests
    def test_rollback_transaction(self, transaction_log, temp_log_dir):
        """Test rolling back a transaction."""
        # Create a test file
        test_file = temp_log_dir / "test_file.txt"
        test_file.write_text("original content")

        # Create and commit transaction with backup
        tx_id = transaction_log.begin_transaction()
        backup_path = temp_log_dir / "backup" / "test_backup.txt"
        backup_path.parent.mkdir()
        backup_path.write_text("original content")

        op = Operation(
            operation_type="modify",
            path=str(test_file),
            backup_path=str(backup_path)
        )
        transaction_log.log_operation(op)
        transaction_log.commit_transaction()

        # Modify the file
        test_file.write_text("modified content")

        # Rollback
        success = transaction_log.rollback_transaction(tx_id)
        assert success is True

        # Verify file was restored
        assert test_file.read_text() == "original content"

    def test_rollback_transaction_updates_status(self, transaction_log, temp_log_dir):
        """Test that rollback updates transaction status."""
        tx_id = transaction_log.begin_transaction()
        transaction_log.commit_transaction()

        success = transaction_log.rollback_transaction(tx_id)
        assert success is True

        tx_path = temp_log_dir / "transactions" / f"{tx_id}.json"
        with open(tx_path) as f:
            data = json.load(f)

        assert data["status"] == "rolled_back"

    def test_rollback_transaction_nonexistent(self, transaction_log):
        """Test rolling back nonexistent transaction returns False."""
        success = transaction_log.rollback_transaction("nonexistent_id")
        assert success is False

    def test_rollback_transaction_no_backup(self, transaction_log, temp_log_dir):
        """Test rollback when operation has no backup path."""
        test_file = temp_log_dir / "test_file.txt"
        test_file.write_text("original content")

        tx_id = transaction_log.begin_transaction()
        op = Operation(
            operation_type="delete",
            path=str(test_file),
            backup_path=None  # No backup
        )
        transaction_log.log_operation(op)
        transaction_log.commit_transaction()

        # Delete the file
        test_file.unlink()

        # Rollback should succeed but not restore (no backup)
        success = transaction_log.rollback_transaction(tx_id)
        assert success is True
        # File should not be restored
        assert not test_file.exists()

    def test_rollback_transaction_backup_missing(self, transaction_log, temp_log_dir):
        """Test rollback when backup file is missing."""
        test_file = temp_log_dir / "test_file.txt"
        test_file.write_text("original content")

        tx_id = transaction_log.begin_transaction()
        backup_path = temp_log_dir / "missing_backup.txt"
        # Don't create the backup file

        op = Operation(
            operation_type="modify",
            path=str(test_file),
            backup_path=str(backup_path)
        )
        transaction_log.log_operation(op)
        transaction_log.commit_transaction()

        # Modify the file
        test_file.write_text("modified content")

        # Rollback should succeed but not restore (backup missing)
        success = transaction_log.rollback_transaction(tx_id)
        assert success is True
        # File should remain modified
        assert test_file.read_text() == "modified content"

    def test_rollback_transaction_reverses_order(self, transaction_log, temp_log_dir):
        """Test that rollback reverses operation order."""
        file1 = temp_log_dir / "file1.txt"
        file2 = temp_log_dir / "file2.txt"
        file1.write_text("original 1")
        file2.write_text("original 2")

        backup1 = temp_log_dir / "backup1.txt"
        backup2 = temp_log_dir / "backup2.txt"
        backup1.write_text("original 1")
        backup2.write_text("original 2")

        tx_id = transaction_log.begin_transaction()

        # Log operations in order
        transaction_log.log_operation(Operation(
            operation_type="modify",
            path=str(file1),
            backup_path=str(backup1)
        ))
        transaction_log.log_operation(Operation(
            operation_type="modify",
            path=str(file2),
            backup_path=str(backup2)
        ))
        transaction_log.commit_transaction()

        # Modify files
        file1.write_text("modified 1")
        file2.write_text("modified 2")

        # Rollback
        transaction_log.rollback_transaction(tx_id)

        # Both files should be restored
        assert file1.read_text() == "original 1"
        assert file2.read_text() == "original 2"

    def test_rollback_transaction_multiple_operations(self, transaction_log, temp_log_dir):
        """Test rollback with multiple operations."""
        files = []
        backups = []
        for i in range(5):
            f = temp_log_dir / f"file{i}.txt"
            f.write_text(f"original {i}")
            files.append(f)

            b = temp_log_dir / f"backup{i}.txt"
            b.write_text(f"original {i}")
            backups.append(b)

        tx_id = transaction_log.begin_transaction()
        for i in range(5):
            transaction_log.log_operation(Operation(
                operation_type="modify",
                path=str(files[i]),
                backup_path=str(backups[i])
            ))
        transaction_log.commit_transaction()

        # Modify all files
        for i, f in enumerate(files):
            f.write_text(f"modified {i}")

        # Rollback
        success = transaction_log.rollback_transaction(tx_id)
        assert success is True

        # Verify all files restored
        for i, f in enumerate(files):
            assert f.read_text() == f"original {i}"

    # Get Transaction Tests
    def test_get_transaction(self, transaction_log, temp_log_dir):
        """Test getting transaction details."""
        tx_id = transaction_log.begin_transaction()
        op = Operation(operation_type="delete", path="/test/file.txt")
        transaction_log.log_operation(op)
        transaction_log.commit_transaction()

        data = transaction_log.get_transaction(tx_id)
        assert data is not None
        assert data["transaction_id"] == tx_id
        assert data["status"] == "completed"
        assert len(data["operations"]) == 1

    def test_get_transaction_nonexistent(self, transaction_log):
        """Test getting nonexistent transaction returns None."""
        data = transaction_log.get_transaction("nonexistent_id")
        assert data is None

    def test_get_transaction_after_rollback(self, transaction_log, temp_log_dir):
        """Test getting transaction after rollback."""
        tx_id = transaction_log.begin_transaction()
        transaction_log.commit_transaction()
        transaction_log.rollback_transaction(tx_id)

        data = transaction_log.get_transaction(tx_id)
        assert data is not None
        assert data["status"] == "rolled_back"

    # List Transactions Tests
    def test_list_transactions_empty(self, transaction_log):
        """Test listing transactions when none exist."""
        transactions = transaction_log.list_transactions()
        assert transactions == []

    def test_list_transactions_single(self, transaction_log, temp_log_dir):
        """Test listing single transaction."""
        tx_id = transaction_log.begin_transaction()
        transaction_log.commit_transaction()

        transactions = transaction_log.list_transactions()
        assert len(transactions) == 1
        assert transactions[0]["transaction_id"] == tx_id
        assert transactions[0]["status"] == "completed"
        assert transactions[0]["operation_count"] == 0

    def test_list_transactions_multiple(self, transaction_log):
        """Test listing multiple transactions."""
        tx_ids = []
        for _ in range(5):
            tx_id = transaction_log.begin_transaction()
            transaction_log.log_operation(
                Operation(operation_type="delete", path="/test/file.txt")
            )
            transaction_log.commit_transaction()
            tx_ids.append(tx_id)

        transactions = transaction_log.list_transactions()
        assert len(transactions) == 5

        # Verify all transaction IDs are present
        transaction_ids = {t["transaction_id"] for t in transactions}
        for tx_id in tx_ids:
            assert tx_id in transaction_ids

    def test_list_transactions_sorted_by_timestamp(self, transaction_log):
        """Test that transactions are sorted by timestamp (newest first)."""
        import time

        tx_id1 = transaction_log.begin_transaction()
        transaction_log.commit_transaction()
        time.sleep(0.01)  # Ensure different timestamps
        tx_id2 = transaction_log.begin_transaction()
        transaction_log.commit_transaction()

        transactions = transaction_log.list_transactions()
        assert len(transactions) == 2
        # Newest first
        assert transactions[0]["transaction_id"] == tx_id2
        assert transactions[1]["transaction_id"] == tx_id1

    def test_list_transactions_includes_operation_count(self, transaction_log):
        """Test that list_transactions includes correct operation count."""
        transaction_log.begin_transaction()
        for i in range(5):
            transaction_log.log_operation(
                Operation(operation_type="delete", path=f"/test/file{i}.txt")
            )
        transaction_log.commit_transaction()

        transactions = transaction_log.list_transactions()
        assert transactions[0]["operation_count"] == 5

    def test_list_transactions_includes_status(self, transaction_log, temp_log_dir):
        """Test that list_transactions includes status."""
        tx_id = transaction_log.begin_transaction()
        transaction_log.commit_transaction()

        transactions = transaction_log.list_transactions()
        assert transactions[0]["status"] == "completed"

        # Rollback and check status
        transaction_log.rollback_transaction(tx_id)
        transactions = transaction_log.list_transactions()
        assert transactions[0]["status"] == "rolled_back"

    # Integration Tests
    def test_transaction_full_lifecycle(self, transaction_log, temp_log_dir):
        """Test complete transaction lifecycle."""
        # Create test file
        test_file = temp_log_dir / "test.txt"
        test_file.write_text("original")
        backup = temp_log_dir / "backup.txt"
        backup.write_text("original")

        # Begin transaction
        tx_id = transaction_log.begin_transaction()
        assert transaction_log.current_transaction == tx_id

        # Log operation
        op = Operation(
            operation_type="modify",
            path=str(test_file),
            original_hash="abc123",
            backup_path=str(backup)
        )
        transaction_log.log_operation(op)
        assert len(transaction_log.current_operations) == 1

        # Commit
        committed_id = transaction_log.commit_transaction()
        assert committed_id == tx_id
        assert transaction_log.current_transaction is None

        # Verify transaction file exists
        tx_path = temp_log_dir / "transactions" / f"{tx_id}.json"
        assert tx_path.exists()

        # Modify file
        test_file.write_text("modified")

        # Rollback
        success = transaction_log.rollback_transaction(tx_id)
        assert success is True
        assert test_file.read_text() == "original"

        # Verify status updated
        data = transaction_log.get_transaction(tx_id)
        assert data["status"] == "rolled_back"

    def test_transaction_persistence(self, temp_log_dir):
        """Test that transactions persist across TransactionLog instances."""
        # Create first log and transaction
        log1 = TransactionLog(log_dir=str(temp_log_dir))
        tx_id = log1.begin_transaction()
        log1.log_operation(Operation(operation_type="delete", path="/test/file.txt"))
        log1.commit_transaction()

        # Create second log instance
        log2 = TransactionLog(log_dir=str(temp_log_dir))

        # Should be able to list the transaction
        transactions = log2.list_transactions()
        assert len(transactions) == 1
        assert transactions[0]["transaction_id"] == tx_id

        # Should be able to get transaction details
        data = log2.get_transaction(tx_id)
        assert data is not None

        # Should be able to rollback
        success = log2.rollback_transaction(tx_id)
        assert success is True

    def test_transaction_with_different_operation_types(self, transaction_log, temp_log_dir):
        """Test transaction with all operation types."""
        tx_id = transaction_log.begin_transaction()

        ops = [
            Operation(operation_type="delete", path="/test/delete.txt"),
            Operation(operation_type="modify", path="/test/modify.txt", original_hash="abc"),
            Operation(operation_type="move", path="/src/move.txt", new_path="/dst/move.txt"),
            Operation(operation_type="copy", path="/src/copy.txt", new_path="/dst/copy.txt"),
            Operation(operation_type="restore", path="/test/restore.txt", backup_path="/backup/restore.txt"),
        ]

        for op in ops:
            transaction_log.log_operation(op)

        transaction_log.commit_transaction()

        # Verify all operations are logged
        data = transaction_log.get_transaction(tx_id)
        assert len(data["operations"]) == 5
        operation_types = [op["operation_type"] for op in data["operations"]]
        assert "delete" in operation_types
        assert "modify" in operation_types
        assert "move" in operation_types
        assert "copy" in operation_types
        assert "restore" in operation_types

    # Edge Cases
    def test_transaction_with_unicode_paths(self, transaction_log, temp_log_dir):
        """Test transaction with unicode paths."""
        tx_id = transaction_log.begin_transaction()
        op = Operation(
            operation_type="delete",
            path="/test/файл_文件.txt"
        )
        transaction_log.log_operation(op)
        transaction_log.commit_transaction()

        data = transaction_log.get_transaction(tx_id)
        assert data is not None
        assert "файл" in data["operations"][0]["path"] or "文件" in data["operations"][0]["path"]

    def test_transaction_with_special_characters(self, transaction_log, temp_log_dir):
        """Test transaction with special characters in paths."""
        tx_id = transaction_log.begin_transaction()
        op = Operation(
            operation_type="delete",
            path="/test/file with spaces & special.txt"
        )
        transaction_log.log_operation(op)
        transaction_log.commit_transaction()

        data = transaction_log.get_transaction(tx_id)
        assert data is not None
        assert "spaces" in data["operations"][0]["path"]

    def test_transaction_very_long_path(self, transaction_log, temp_log_dir):
        """Test transaction with very long path."""
        long_path = "/test/" + "a" * 1000 + "/file.txt"
        tx_id = transaction_log.begin_transaction()
        op = Operation(operation_type="delete", path=long_path)
        transaction_log.log_operation(op)
        transaction_log.commit_transaction()

        data = transaction_log.get_transaction(tx_id)
        assert data is not None
        assert len(data["operations"][0]["path"]) > 1000

    def test_transaction_concurrent_simulation(self, temp_log_dir):
        """Test simulating concurrent transactions (should be serialized)."""
        log1 = TransactionLog(log_dir=str(temp_log_dir))
        log2 = TransactionLog(log_dir=str(temp_log_dir))

        # Both start transactions
        log1.begin_transaction()
        log2.begin_transaction()

        # Both log operations
        log1.log_operation(Operation(operation_type="delete", path="/test/file1.txt"))
        log2.log_operation(Operation(operation_type="delete", path="/test/file2.txt"))

        # Both commit
        log1.commit_transaction()
        log2.commit_transaction()

        # Both transactions should exist
        transactions = log1.list_transactions()
        assert len(transactions) == 2

    def test_transaction_empty_operation_fields(self, transaction_log, temp_log_dir):
        """Test transaction with empty string fields."""
        tx_id = transaction_log.begin_transaction()
        op = Operation(
            operation_type="delete",
            path="",  # Empty path
            original_hash="",
            backup_path="",
            new_path=""
        )
        transaction_log.log_operation(op)
        transaction_log.commit_transaction()

        data = transaction_log.get_transaction(tx_id)
        assert data is not None
        assert data["operations"][0]["path"] == ""

    def test_transaction_none_values(self, transaction_log, temp_log_dir):
        """Test transaction with None values."""
        tx_id = transaction_log.begin_transaction()
        op = Operation(
            operation_type="delete",
            path="/test/file.txt",
            original_hash=None,
            backup_path=None,
            new_path=None
        )
        transaction_log.log_operation(op)
        transaction_log.commit_transaction()

        data = transaction_log.get_transaction(tx_id)
        assert data is not None
        assert data["operations"][0]["original_hash"] is None

    def test_transaction_large_number_of_operations(self, transaction_log):
        """Test transaction with many operations."""
        tx_id = transaction_log.begin_transaction()
        for i in range(1000):
            transaction_log.log_operation(
                Operation(operation_type="delete", path=f"/test/file{i}.txt")
            )
        committed_id = transaction_log.commit_transaction()
        assert committed_id == tx_id

        data = transaction_log.get_transaction(tx_id)
        assert len(data["operations"]) == 1000

    def test_transaction_rollback_idempotence(self, transaction_log, temp_log_dir):
        """Test that rolling back multiple times is safe."""
        tx_id = transaction_log.begin_transaction()
        transaction_log.commit_transaction()

        # Rollback multiple times
        success1 = transaction_log.rollback_transaction(tx_id)
        success2 = transaction_log.rollback_transaction(tx_id)
        success3 = transaction_log.rollback_transaction(tx_id)

        assert success1 is True
        assert success2 is True  # Should be idempotent
        assert success3 is True

    def test_transaction_directory_operations(self, transaction_log, temp_log_dir):
        """Test transaction logging for directory operations."""
        tx_id = transaction_log.begin_transaction()

        # Log directory operations
        transaction_log.log_operation(Operation(
            operation_type="delete",
            path=str(temp_log_dir / "test_dir")
        ))
        transaction_log.log_operation(Operation(
            operation_type="move",
            path=str(temp_log_dir / "src_dir"),
            new_path=str(temp_log_dir / "dst_dir")
        ))

        transaction_log.commit_transaction()

        data = transaction_log.get_transaction(tx_id)
        assert len(data["operations"]) == 2
