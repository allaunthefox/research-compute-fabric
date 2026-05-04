"""Comprehensive tests for the Snapshot module.

Tests cover:
- SnapshotFile and Snapshot dataclasses
- SnapshotManager initialization
- Hash computation with various algorithms
- Snapshot creation and restoration
- Idempotent backup behavior
- Edge cases and error conditions
"""

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from nodupe.tools.maintenance.snapshot import (
    HASH_ALGORITHMS,
    Snapshot,
    SnapshotFile,
    SnapshotManager,
    get_hasher,
)


class TestHashAlgorithms:
    """Tests for hash algorithm constants and get_hasher function."""

    def test_hash_algorithms_contains_all_supported(self):
        """Test that HASH_ALGORITHMS contains all expected algorithms."""
        expected_algorithms = {
            "sha256", "sha384", "sha512",
            "sha3_256", "sha3_384", "sha3_512",
            "blake2b", "blake2s"
        }
        assert set(HASH_ALGORITHMS.keys()) == expected_algorithms

    def test_get_hasher_returns_callable(self):
        """Test that get_hasher returns a callable for each algorithm."""
        for algorithm in HASH_ALGORITHMS:
            hasher_func = get_hasher(algorithm)
            assert callable(hasher_func)
            hasher = hasher_func()
            assert hasattr(hasher, 'update')
            assert hasattr(hasher, 'hexdigest')

    def test_get_hasher_sha256(self):
        """Test get_hasher with sha256."""
        hasher_func = get_hasher("sha256")
        hasher = hasher_func()
        hasher.update(b"test")
        assert hasher.hexdigest() == hashlib.sha256(b"test").hexdigest()

    def test_get_hasher_sha384(self):
        """Test get_hasher with sha384."""
        hasher_func = get_hasher("sha384")
        hasher = hasher_func()
        hasher.update(b"test")
        assert hasher.hexdigest() == hashlib.sha384(b"test").hexdigest()

    def test_get_hasher_sha512(self):
        """Test get_hasher with sha512."""
        hasher_func = get_hasher("sha512")
        hasher = hasher_func()
        hasher.update(b"test")
        assert hasher.hexdigest() == hashlib.sha512(b"test").hexdigest()

    def test_get_hasher_sha3_variants(self):
        """Test get_hasher with SHA-3 variants."""
        for algorithm in ["sha3_256", "sha3_384", "sha3_512"]:
            hasher_func = get_hasher(algorithm)
            hasher = hasher_func()
            hasher.update(b"test")
            expected = getattr(hashlib, algorithm)(b"test").hexdigest()
            assert hasher.hexdigest() == expected

    def test_get_hasher_blake2_variants(self):
        """Test get_hasher with BLAKE2 variants."""
        for algorithm in ["blake2b", "blake2s"]:
            hasher_func = get_hasher(algorithm)
            hasher = hasher_func()
            hasher.update(b"test")
            expected = getattr(hashlib, algorithm)(b"test").hexdigest()
            assert hasher.hexdigest() == expected

    def test_get_hasher_invalid_algorithm(self):
        """Test that get_hasher raises ValueError for invalid algorithm."""
        with pytest.raises(ValueError) as exc_info:
            get_hasher("invalid_algorithm")
        assert "Unsupported hash algorithm" in str(exc_info.value)
        assert "invalid_algorithm" in str(exc_info.value)

    def test_get_hasher_error_message_lists_supported(self):
        """Test that error message includes list of supported algorithms."""
        with pytest.raises(ValueError) as exc_info:
            get_hasher("md5")
        error_msg = str(exc_info.value)
        assert "sha256" in error_msg
        assert "blake2b" in error_msg


class TestSnapshotFile:
    """Tests for SnapshotFile dataclass."""

    def test_snapshot_file_creation(self):
        """Test creating a SnapshotFile instance."""
        sf = SnapshotFile(
            path="/test/file.txt",
            hash="abc123",
            size=1024,
            modified="2024-01-01T00:00:00"
        )
        assert sf.path == "/test/file.txt"
        assert sf.hash == "abc123"
        assert sf.size == 1024
        assert sf.modified == "2024-01-01T00:00:00"
        assert sf.backup_path is None
        assert sf.hash_algorithm is None

    def test_snapshot_file_with_optional_fields(self):
        """Test SnapshotFile with optional fields."""
        sf = SnapshotFile(
            path="/test/file.txt",
            hash="abc123",
            size=1024,
            modified="2024-01-01T00:00:00",
            backup_path="/backup/abc123",
            hash_algorithm="sha256"
        )
        assert sf.backup_path == "/backup/abc123"
        assert sf.hash_algorithm == "sha256"


class TestSnapshot:
    """Tests for Snapshot dataclass."""

    def test_snapshot_creation(self):
        """Test creating a Snapshot instance."""
        files = [
            SnapshotFile(
                path="/test/file1.txt",
                hash="hash1",
                size=100,
                modified="2024-01-01T00:00:00"
            )
        ]
        snapshot = Snapshot(
            snapshot_id="test123",
            timestamp="2024-01-01T00:00:00",
            files=files
        )
        assert snapshot.snapshot_id == "test123"
        assert snapshot.timestamp == "2024-01-01T00:00:00"
        assert len(snapshot.files) == 1
        assert snapshot.hash_algorithm is None

    def test_snapshot_with_hash_algorithm(self):
        """Test Snapshot with hash algorithm specified."""
        snapshot = Snapshot(
            snapshot_id="test123",
            timestamp="2024-01-01T00:00:00",
            files=[],
            hash_algorithm="sha384"
        )
        assert snapshot.hash_algorithm == "sha384"

    def test_snapshot_to_dict(self):
        """Test converting Snapshot to dictionary."""
        files = [
            SnapshotFile(
                path="/test/file.txt",
                hash="abc123",
                size=1024,
                modified="2024-01-01T00:00:00",
                backup_path="/backup/abc123"
            )
        ]
        snapshot = Snapshot(
            snapshot_id="test123",
            timestamp="2024-01-01T00:00:00",
            files=files,
            hash_algorithm="sha256"
        )
        data = snapshot.to_dict()
        assert data["snapshot_id"] == "test123"
        assert data["timestamp"] == "2024-01-01T00:00:00"
        assert data["hash_algorithm"] == "sha256"
        assert len(data["files"]) == 1
        assert data["files"][0]["path"] == "/test/file.txt"
        assert data["files"][0]["backup_path"] == "/backup/abc123"

    def test_snapshot_from_dict(self):
        """Test creating Snapshot from dictionary."""
        data = {
            "snapshot_id": "test456",
            "timestamp": "2024-02-01T00:00:00",
            "hash_algorithm": "sha512",
            "files": [
                {
                    "path": "/test/file.txt",
                    "hash": "def456",
                    "size": 2048,
                    "modified": "2024-02-01T00:00:00",
                    "backup_path": "/backup/def456",
                    "hash_algorithm": "sha512"
                }
            ]
        }
        snapshot = Snapshot.from_dict(data)
        assert snapshot.snapshot_id == "test456"
        assert snapshot.timestamp == "2024-02-01T00:00:00"
        assert snapshot.hash_algorithm == "sha512"
        assert len(snapshot.files) == 1
        assert snapshot.files[0].path == "/test/file.txt"
        assert snapshot.files[0].hash == "def456"

    def test_snapshot_from_dict_empty_files(self):
        """Test Snapshot.from_dict with empty files list."""
        data = {
            "snapshot_id": "empty123",
            "timestamp": "2024-01-01T00:00:00",
            "files": []
        }
        snapshot = Snapshot.from_dict(data)
        assert snapshot.snapshot_id == "empty123"
        assert len(snapshot.files) == 0

    def test_snapshot_from_dict_missing_hash_algorithm(self):
        """Test Snapshot.from_dict with missing hash_algorithm."""
        data = {
            "snapshot_id": "test789",
            "timestamp": "2024-01-01T00:00:00",
            "files": []
        }
        snapshot = Snapshot.from_dict(data)
        assert snapshot.hash_algorithm is None

    def test_snapshot_roundtrip(self):
        """Test Snapshot to_dict and from_dict roundtrip."""
        original = Snapshot(
            snapshot_id="roundtrip123",
            timestamp="2024-01-01T00:00:00",
            files=[
                SnapshotFile(
                    path="/test/file.txt",
                    hash="abc123",
                    size=1024,
                    modified="2024-01-01T00:00:00",
                    backup_path="/backup/abc123",
                    hash_algorithm="sha256"
                )
            ],
            hash_algorithm="sha256"
        )
        data = original.to_dict()
        restored = Snapshot.from_dict(data)
        assert restored.snapshot_id == original.snapshot_id
        assert restored.timestamp == original.timestamp
        assert restored.hash_algorithm == original.hash_algorithm
        assert len(restored.files) == len(original.files)
        assert restored.files[0].path == original.files[0].path
        assert restored.files[0].hash == original.files[0].hash


class TestSnapshotManager:
    """Tests for SnapshotManager class."""

    @pytest.fixture
    def temp_backup_dir(self):
        """Create a temporary backup directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def snapshot_manager(self, temp_backup_dir):
        """Create a SnapshotManager instance with temp directory."""
        return SnapshotManager(backup_dir=str(temp_backup_dir))

    @pytest.fixture
    def test_files(self, temp_backup_dir):
        """Create test files for snapshot testing."""
        files_dir = temp_backup_dir / "test_files"
        files_dir.mkdir()

        test_files = {}
        for i in range(3):
            file_path = files_dir / f"file{i}.txt"
            content = f"Content of file {i}" * (i + 1)
            file_path.write_text(content)
            test_files[f"file{i}"] = file_path

        # Create a binary file
        binary_file = files_dir / "binary.bin"
        binary_file.write_bytes(os.urandom(256))
        test_files["binary"] = binary_file

        return test_files

    # Initialization Tests
    def test_snapshot_manager_initialization(self, temp_backup_dir):
        """Test SnapshotManager initialization creates directories."""
        manager = SnapshotManager(backup_dir=str(temp_backup_dir))
        assert manager.backup_dir == temp_backup_dir
        assert manager.snapshot_dir.exists()
        assert manager.content_dir.exists()
        assert manager.snapshot_dir == temp_backup_dir / "snapshots"
        assert manager.content_dir == temp_backup_dir / "content"

    def test_snapshot_manager_default_hash_algorithm(self, temp_backup_dir):
        """Test SnapshotManager uses sha256 by default."""
        manager = SnapshotManager(backup_dir=str(temp_backup_dir))
        assert manager.hash_algorithm == "sha256"

    def test_snapshot_manager_custom_hash_algorithm(self, temp_backup_dir):
        """Test SnapshotManager with custom hash algorithm."""
        for algorithm in ["sha384", "sha512", "blake2b"]:
            manager = SnapshotManager(
                backup_dir=str(temp_backup_dir / algorithm),
                hash_algorithm=algorithm
            )
            assert manager.hash_algorithm == algorithm

    def test_snapshot_manager_creates_readme(self, temp_backup_dir):
        """Test that SnapshotManager creates README files."""
        SnapshotManager(backup_dir=str(temp_backup_dir))
        readme_path = temp_backup_dir / "README.md"
        recovery_path = temp_backup_dir / "RECOVERY.txt"
        assert readme_path.exists()
        assert recovery_path.exists()

    def test_snapshot_manager_readme_content(self, temp_backup_dir):
        """Test README content includes hash algorithm."""
        SnapshotManager(
            backup_dir=str(temp_backup_dir),
            hash_algorithm="sha384"
        )
        readme_content = (temp_backup_dir / "README.md").read_text()
        recovery_content = (temp_backup_dir / "RECOVERY.txt").read_text(encoding="latin-1")
        assert "sha384" in readme_content
        assert "sha384" in recovery_content

    def test_snapshot_manager_does_not_overwrite_readme(self, temp_backup_dir):
        """Test that existing README files are not overwritten."""
        readme_path = temp_backup_dir / "README.md"
        original_content = "# Custom README\nThis is custom content."
        readme_path.write_text(original_content)

        SnapshotManager(backup_dir=str(temp_backup_dir))
        assert readme_path.read_text() == original_content

    # Hash Computation Tests
    def test_compute_hash_sha256(self, snapshot_manager, test_files):
        """Test hash computation with sha256."""
        file_path = test_files["file0"]
        file_hash = snapshot_manager._compute_hash(file_path)
        assert file_hash is not None
        assert len(file_hash) == 64  # SHA-256 hex length

    def test_compute_hash_consistency(self, snapshot_manager, test_files):
        """Test that hash computation is consistent."""
        file_path = test_files["file0"]
        hash1 = snapshot_manager._compute_hash(file_path)
        hash2 = snapshot_manager._compute_hash(file_path)
        assert hash1 == hash2

    def test_compute_hash_different_files(self, snapshot_manager, test_files):
        """Test that different files have different hashes."""
        hash1 = snapshot_manager._compute_hash(test_files["file0"])
        hash2 = snapshot_manager._compute_hash(test_files["file1"])
        assert hash1 != hash2

    def test_compute_hash_nonexistent_file(self, snapshot_manager):
        """Test hash computation for nonexistent file returns None."""
        result = snapshot_manager._compute_hash(Path("/nonexistent/file.txt"))
        assert result is None

    def test_compute_hash_directory(self, snapshot_manager, temp_backup_dir):
        """Test hash computation for directory returns None."""
        result = snapshot_manager._compute_hash(temp_backup_dir)
        assert result is None

    def test_compute_hash_empty_file(self, snapshot_manager, temp_backup_dir):
        """Test hash computation for empty file."""
        empty_file = temp_backup_dir / "empty.txt"
        empty_file.write_text("")
        result = snapshot_manager._compute_hash(empty_file)
        assert result is not None
        # SHA-256 of empty string
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_compute_hash_large_file(self, snapshot_manager, temp_backup_dir):
        """Test hash computation for large file (tests chunked reading)."""
        large_file = temp_backup_dir / "large.bin"
        # Create a 1MB file
        with open(large_file, "wb") as f:
            for _ in range(100):
                f.write(os.urandom(10240))
        result = snapshot_manager._compute_hash(large_file)
        assert result is not None
        assert len(result) == 64

    # Backup Content Tests
    def test_backup_file_content_creates_backup(self, snapshot_manager, test_files):
        """Test that _backup_file_content creates backup."""
        file_path = test_files["file0"]
        file_hash = snapshot_manager._compute_hash(file_path)
        backup_path = snapshot_manager._backup_file_content(file_path, file_hash)
        assert Path(backup_path).exists()
        assert backup_path == str(snapshot_manager.content_dir / file_hash)

    def test_backup_file_content_idempotent(self, snapshot_manager, test_files):
        """Test that _backup_file_content is idempotent."""
        file_path = test_files["file0"]
        file_hash = snapshot_manager._compute_hash(file_path)

        # First backup
        backup_path1 = snapshot_manager._backup_file_content(file_path, file_hash)
        stat1 = Path(backup_path1).stat()

        # Second backup (should not copy again)
        backup_path2 = snapshot_manager._backup_file_content(file_path, file_hash)
        stat2 = Path(backup_path2).stat()

        assert backup_path1 == backup_path2
        # File stats should be identical (same inode on Unix)
        assert stat1.st_ino == stat2.st_ino

    def test_backup_file_content_preserves_content(self, snapshot_manager, test_files):
        """Test that backup preserves file content."""
        file_path = test_files["file0"]
        original_content = file_path.read_text()
        file_hash = snapshot_manager._compute_hash(file_path)
        backup_path = snapshot_manager._backup_file_content(file_path, file_hash)
        backup_content = Path(backup_path).read_text()
        assert backup_content == original_content

    # Snapshot Creation Tests
    def test_create_snapshot_single_file(self, snapshot_manager, test_files):
        """Test creating snapshot of single file."""
        file_path = test_files["file0"]
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        assert snapshot is not None
        assert snapshot.snapshot_id is not None
        assert len(snapshot.snapshot_id) == 16
        assert len(snapshot.files) == 1
        assert snapshot.files[0].path == str(file_path.absolute())
        assert snapshot.files[0].hash is not None
        assert snapshot.files[0].size == file_path.stat().st_size
        assert snapshot.files[0].backup_path is not None

    def test_create_snapshot_multiple_files(self, snapshot_manager, test_files):
        """Test creating snapshot of multiple files."""
        paths = [str(test_files[f"file{i}"]) for i in range(3)]
        snapshot = snapshot_manager.create_snapshot(paths)

        assert snapshot is not None
        assert len(snapshot.files) == 3
        file_paths = {f.path for f in snapshot.files}
        for path in paths:
            assert Path(path).absolute() in [Path(p) for p in file_paths]

    def test_create_snapshot_mixed_files(self, snapshot_manager, test_files):
        """Test creating snapshot with text and binary files."""
        paths = [str(test_files["file0"]), str(test_files["binary"])]
        snapshot = snapshot_manager.create_snapshot(paths)

        assert len(snapshot.files) == 2
        # Verify binary file hash is different from text file
        hashes = {f.hash for f in snapshot.files}
        assert len(hashes) == 2

    def test_create_snapshot_nonexistent_file(self, snapshot_manager):
        """Test creating snapshot with nonexistent file."""
        snapshot = snapshot_manager.create_snapshot(["/nonexistent/file.txt"])
        assert snapshot is not None
        assert len(snapshot.files) == 0

    def test_create_snapshot_directory(self, snapshot_manager, temp_backup_dir):
        """Test creating snapshot of directory (should be ignored)."""
        snapshot = snapshot_manager.create_snapshot([str(temp_backup_dir)])
        assert len(snapshot.files) == 0

    def test_create_snapshot_mixed_valid_invalid(self, snapshot_manager, test_files):
        """Test creating snapshot with mix of valid and invalid paths."""
        paths = [
            str(test_files["file0"]),
            "/nonexistent/file.txt",
            str(test_files["file1"])
        ]
        snapshot = snapshot_manager.create_snapshot(paths)
        assert len(snapshot.files) == 2

    def test_create_snapshot_saves_json(self, snapshot_manager, test_files):
        """Test that snapshot is saved as JSON."""
        file_path = test_files["file0"]
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        snapshot_path = snapshot_manager.snapshot_dir / f"{snapshot.snapshot_id}.json"
        assert snapshot_path.exists()

        with open(snapshot_path) as f:
            data = json.load(f)
        assert data["snapshot_id"] == snapshot.snapshot_id
        assert len(data["files"]) == 1

    def test_create_snapshot_idempotent_backup(self, snapshot_manager, test_files):
        """Test that snapshot creation uses idempotent backup."""
        file_path = test_files["file0"]

        # Create first snapshot
        snapshot1 = snapshot_manager.create_snapshot([str(file_path)])
        backup_path1 = snapshot1.files[0].backup_path

        # Modify the file
        file_path.write_text("Modified content")

        # Create second snapshot
        snapshot2 = snapshot_manager.create_snapshot([str(file_path)])
        backup_path2 = snapshot2.files[0].backup_path

        # Original backup should still exist
        assert Path(backup_path1).exists()
        # New backup should be created for modified content
        assert backup_path1 != backup_path2

    def test_create_snapshot_timestamp(self, snapshot_manager, test_files):
        """Test that snapshot has valid timestamp."""
        file_path = test_files["file0"]
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        assert snapshot.timestamp is not None
        # Verify timestamp format (ISO format)
        datetime.fromisoformat(snapshot.timestamp)

    def test_create_snapshot_file_modified_time(self, snapshot_manager, test_files):
        """Test that snapshot captures file modified time."""
        file_path = test_files["file0"]
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        file_data = snapshot.files[0]
        assert file_data.modified is not None
        # Verify modified time format
        datetime.fromisoformat(file_data.modified)

    # Snapshot Restoration Tests
    def test_restore_snapshot_success(self, snapshot_manager, test_files):
        """Test successful snapshot restoration."""
        file_path = test_files["file0"]
        original_content = file_path.read_text()

        # Create snapshot
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        # Modify the file
        modified_content = "Modified content"
        file_path.write_text(modified_content)
        assert file_path.read_text() == modified_content

        # Restore snapshot
        success = snapshot_manager.restore_snapshot(snapshot.snapshot_id)
        assert success is True
        assert file_path.read_text() == original_content

    def test_restore_snapshot_nonexistent(self, snapshot_manager):
        """Test restoring nonexistent snapshot returns False."""
        success = snapshot_manager.restore_snapshot("nonexistent_id")
        assert success is False

    def test_restore_snapshot_unchanged_file(self, snapshot_manager, test_files):
        """Test restoring snapshot when file is unchanged."""
        file_path = test_files["file0"]
        original_content = file_path.read_text()

        # Create snapshot
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        # Restore without modifying
        success = snapshot_manager.restore_snapshot(snapshot.snapshot_id)
        assert success is True
        assert file_path.read_text() == original_content

    def test_restore_snapshot_deleted_file(self, snapshot_manager, test_files):
        """Test restoring snapshot when file was deleted."""
        file_path = test_files["file0"]
        original_content = file_path.read_text()

        # Create snapshot
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        # Delete the file
        file_path.unlink()
        assert not file_path.exists()

        # Restore snapshot - should recreate deleted files from backup
        success = snapshot_manager.restore_snapshot(snapshot.snapshot_id)
        assert success is True
        # File should be restored from backup
        assert file_path.exists()
        assert file_path.read_text() == original_content

    def test_restore_snapshot_multiple_files(self, snapshot_manager, test_files):
        """Test restoring snapshot with multiple files."""
        file1 = test_files["file0"]
        file2 = test_files["file1"]
        original1 = file1.read_text()
        original2 = file2.read_text()

        # Create snapshot
        snapshot = snapshot_manager.create_snapshot([str(file1), str(file2)])

        # Modify both files
        file1.write_text("Modified 1")
        file2.write_text("Modified 2")

        # Restore
        success = snapshot_manager.restore_snapshot(snapshot.snapshot_id)
        assert success is True
        assert file1.read_text() == original1
        assert file2.read_text() == original2

    def test_restore_snapshot_partial_modification(self, snapshot_manager, test_files):
        """Test restoring snapshot when only some files changed."""
        file1 = test_files["file0"]
        file2 = test_files["file1"]
        original2 = file2.read_text()

        # Create snapshot
        snapshot = snapshot_manager.create_snapshot([str(file1), str(file2)])

        # Modify only file2
        file2.write_text("Modified 2")

        # Restore
        success = snapshot_manager.restore_snapshot(snapshot.snapshot_id)
        assert success is True
        # file1 should be unchanged (wasn't modified)
        # file2 should be restored
        assert file2.read_text() == original2

    def test_restore_snapshot_backup_path_missing(self, snapshot_manager, test_files):
        """Test restoring snapshot when backup path is missing."""
        file_path = test_files["file0"]
        file_path.read_text()

        # Create snapshot
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        # Delete the backup content
        backup_path = Path(snapshot.files[0].backup_path)
        backup_path.unlink()

        # Modify the file
        file_path.write_text("Modified content")

        # Restore should fail silently (backup missing)
        success = snapshot_manager.restore_snapshot(snapshot.snapshot_id)
        assert success is True  # Returns True but doesn't restore
        # File should remain modified
        assert file_path.read_text() == "Modified content"

    # List Snapshots Tests
    def test_list_snapshots_empty(self, snapshot_manager):
        """Test listing snapshots when none exist."""
        snapshots = snapshot_manager.list_snapshots()
        assert snapshots == []

    def test_list_snapshots_single(self, snapshot_manager, test_files):
        """Test listing single snapshot."""
        file_path = test_files["file0"]
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        snapshots = snapshot_manager.list_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0]["snapshot_id"] == snapshot.snapshot_id
        assert snapshots[0]["file_count"] == 1
        assert "timestamp" in snapshots[0]

    def test_list_snapshots_multiple(self, snapshot_manager, test_files):
        """Test listing multiple snapshots."""
        snapshots_created = []
        for i in range(3):
            file_path = test_files[f"file{i}"]
            snapshot = snapshot_manager.create_snapshot([str(file_path)])
            snapshots_created.append(snapshot)

        snapshots = snapshot_manager.list_snapshots()
        assert len(snapshots) == 3

        # Verify all snapshot IDs are present
        snapshot_ids = {s["snapshot_id"] for s in snapshots}
        for snapshot in snapshots_created:
            assert snapshot.snapshot_id in snapshot_ids

    def test_list_snapshots_sorted_by_timestamp(self, snapshot_manager, test_files):
        """Test that snapshots are sorted by timestamp (newest first)."""
        import time

        file_path = test_files["file0"]
        snapshot1 = snapshot_manager.create_snapshot([str(file_path)])
        time.sleep(0.01)  # Ensure different timestamps
        snapshot2 = snapshot_manager.create_snapshot([str(file_path)])

        snapshots = snapshot_manager.list_snapshots()
        assert len(snapshots) == 2
        # Newest first
        assert snapshots[0]["snapshot_id"] == snapshot2.snapshot_id
        assert snapshots[1]["snapshot_id"] == snapshot1.snapshot_id

    def test_list_snapshots_includes_file_count(self, snapshot_manager, test_files):
        """Test that list_snapshots includes correct file count."""
        paths = [str(test_files[f"file{i}"]) for i in range(3)]
        snapshot_manager.create_snapshot(paths)

        snapshots = snapshot_manager.list_snapshots()
        assert snapshots[0]["file_count"] == 3

    # Delete Snapshot Tests
    def test_delete_snapshot_success(self, snapshot_manager, test_files):
        """Test successful snapshot deletion."""
        file_path = test_files["file0"]
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        success = snapshot_manager.delete_snapshot(snapshot.snapshot_id)
        assert success is True

        # Verify snapshot file is deleted
        snapshot_path = snapshot_manager.snapshot_dir / f"{snapshot.snapshot_id}.json"
        assert not snapshot_path.exists()

    def test_delete_snapshot_nonexistent(self, snapshot_manager):
        """Test deleting nonexistent snapshot returns False."""
        success = snapshot_manager.delete_snapshot("nonexistent_id")
        assert success is False

    def test_delete_snapshot_content_preserved(self, snapshot_manager, test_files):
        """Test that deleting snapshot preserves content files."""
        file_path = test_files["file0"]
        snapshot = snapshot_manager.create_snapshot([str(file_path)])
        backup_path = snapshot.files[0].backup_path

        success = snapshot_manager.delete_snapshot(snapshot.snapshot_id)
        assert success is True

        # Content should still exist (content-addressable storage)
        assert Path(backup_path).exists()

    # Different Hash Algorithms Tests
    def test_snapshot_manager_sha384(self, temp_backup_dir, test_files):
        """Test SnapshotManager with sha384 algorithm."""
        manager = SnapshotManager(
            backup_dir=str(temp_backup_dir),
            hash_algorithm="sha384"
        )
        file_path = test_files["file0"]
        snapshot = manager.create_snapshot([str(file_path)])

        assert manager.hash_algorithm == "sha384"
        # SHA-384 produces 96-character hex hash
        assert len(snapshot.files[0].hash) == 96

    def test_snapshot_manager_sha512(self, temp_backup_dir, test_files):
        """Test SnapshotManager with sha512 algorithm."""
        manager = SnapshotManager(
            backup_dir=str(temp_backup_dir),
            hash_algorithm="sha512"
        )
        file_path = test_files["file0"]
        snapshot = manager.create_snapshot([str(file_path)])

        assert manager.hash_algorithm == "sha512"
        # SHA-512 produces 128-character hex hash
        assert len(snapshot.files[0].hash) == 128

    def test_snapshot_manager_blake2b(self, temp_backup_dir, test_files):
        """Test SnapshotManager with blake2b algorithm."""
        manager = SnapshotManager(
            backup_dir=str(temp_backup_dir),
            hash_algorithm="blake2b"
        )
        file_path = test_files["file0"]
        snapshot = manager.create_snapshot([str(file_path)])

        assert manager.hash_algorithm == "blake2b"
        # BLAKE2b produces 128-character hex hash (default)
        assert len(snapshot.files[0].hash) == 128

    # Edge Cases
    def test_create_snapshot_empty_paths_list(self, snapshot_manager):
        """Test creating snapshot with empty paths list."""
        snapshot = snapshot_manager.create_snapshot([])
        assert snapshot is not None
        assert len(snapshot.files) == 0

    def test_restore_snapshot_empty_files(self, snapshot_manager, temp_backup_dir):
        """Test restoring snapshot with no files."""
        snapshot = Snapshot(
            snapshot_id="empty",
            timestamp="2024-01-01T00:00:00",
            files=[]
        )
        # Save empty snapshot
        snapshot_path = snapshot_manager.snapshot_dir / "empty.json"
        with open(snapshot_path, "w") as f:
            json.dump(snapshot.to_dict(), f)

        success = snapshot_manager.restore_snapshot("empty")
        assert success is True

    def test_snapshot_manager_unicode_paths(self, snapshot_manager, temp_backup_dir):
        """Test snapshot with unicode file paths."""
        unicode_file = temp_backup_dir / "test_файл_文件.txt"
        unicode_file.write_text("Unicode content")

        snapshot = snapshot_manager.create_snapshot([str(unicode_file)])
        assert len(snapshot.files) == 1
        assert "файл" in snapshot.files[0].path or "文件" in snapshot.files[0].path

    def test_snapshot_manager_special_characters(self, snapshot_manager, temp_backup_dir):
        """Test snapshot with special characters in paths."""
        special_file = temp_backup_dir / "test file-with spaces.txt"
        special_file.write_text("Special content")

        snapshot = snapshot_manager.create_snapshot([str(special_file)])
        assert len(snapshot.files) == 1

    def test_snapshot_manager_very_long_path(self, snapshot_manager, temp_backup_dir):
        """Test snapshot with very long file path."""
        # Create nested directory structure
        deep_dir = temp_backup_dir / "a" / "b" / "c" / "d" / "e"
        deep_dir.mkdir(parents=True)
        deep_file = deep_dir / "file.txt"
        deep_file.write_text("Deep file content")

        snapshot = snapshot_manager.create_snapshot([str(deep_file)])
        assert len(snapshot.files) == 1

    def test_snapshot_manager_symlink(self, snapshot_manager, test_files):
        """Test snapshot with symlink."""
        symlink_path = test_files["file0"].parent / "symlink.txt"
        try:
            symlink_path.symlink_to(test_files["file0"])
            snapshot = snapshot_manager.create_snapshot([str(symlink_path)])
            # Symlinks should be followed
            assert len(snapshot.files) == 1
        except (OSError, NotImplementedError):
            # Skip if symlinks not supported on this platform
            pytest.skip("Symlinks not supported on this platform")

    def test_snapshot_manager_permission_denied(self, snapshot_manager, temp_backup_dir):
        """Test snapshot creation when file is not readable."""
        unreadable_file = temp_backup_dir / "unreadable.txt"
        unreadable_file.write_text("Content")
        try:
            os.chmod(unreadable_file, 0o000)
            snapshot = snapshot_manager.create_snapshot([str(unreadable_file)])
            # Should skip unreadable files
            assert len(snapshot.files) == 0
        finally:
            os.chmod(unreadable_file, 0o644)

    def test_snapshot_manager_backup_dir_permissions(self, temp_backup_dir):
        """Test SnapshotManager creates directories with correct permissions."""
        manager = SnapshotManager(backup_dir=str(temp_backup_dir))
        assert manager.snapshot_dir.exists()
        assert manager.content_dir.exists()
        assert manager.snapshot_dir.is_dir()
        assert manager.content_dir.is_dir()

    def test_snapshot_restore_to_new_location(self, snapshot_manager, test_files, temp_backup_dir):
        """Test that restore handles moved files correctly."""
        file_path = test_files["file0"]
        original_content = file_path.read_text()

        # Create snapshot
        snapshot = snapshot_manager.create_snapshot([str(file_path)])

        # Move file to new location
        new_path = temp_backup_dir / "moved.txt"
        file_path.rename(new_path)

        # Restore from snapshot - should restore to original location
        success = snapshot_manager.restore_snapshot(snapshot.snapshot_id)
        assert success is True
        # Original location should have file restored
        assert file_path.exists()
        assert file_path.read_text() == original_content
        # New location should still have file (wasn't touched)
        assert new_path.exists()
