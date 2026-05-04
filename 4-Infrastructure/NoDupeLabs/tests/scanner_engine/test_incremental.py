"""Tests for incremental scanning module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestIncremental:
    """Test Incremental class."""

    def test_save_checkpoint(self, temp_dir):
        """Test saving checkpoint."""
        from nodupe.tools.scanner_engine.incremental import Incremental
        
        scan_path = str(temp_dir)
        processed_files = {
            "file1.txt": {"hash": "abc123", "size": 100},
            "file2.txt": {"hash": "def456", "size": 200}
        }
        metadata = {"version": "1.0"}
        
        Incremental.save_checkpoint(scan_path, processed_files, metadata)
        
        checkpoint_file = temp_dir / ".nodupe_checkpoint.json"
        
        assert checkpoint_file.exists()
        
        with open(checkpoint_file) as f:
            data = json.load(f)
        
        assert data["scan_path"] == scan_path
        assert "file1.txt" in data["processed_files"]
        assert "file2.txt" in data["processed_files"]
        assert data["metadata"]["version"] == "1.0"
        assert "timestamp" in data

    def test_save_checkpoint_no_metadata(self, temp_dir):
        """Test saving checkpoint without metadata."""
        from nodupe.tools.scanner_engine.incremental import Incremental
        
        scan_path = str(temp_dir)
        processed_files = {"file1.txt": {"hash": "abc123"}}
        
        Incremental.save_checkpoint(scan_path, processed_files)
        
        checkpoint_file = temp_dir / ".nodupe_checkpoint.json"
        
        assert checkpoint_file.exists()
        
        with open(checkpoint_file) as f:
            data = json.load(f)
        
        assert data["metadata"] == {}

    def test_load_checkpoint(self, temp_dir):
        """Test loading checkpoint."""
        from nodupe.tools.scanner_engine.incremental import Incremental

        # Create checkpoint file manually
        checkpoint_data = {
            "scan_path": str(temp_dir),
            "processed_files": {"file1.txt": {"hash": "abc123"}},
            "timestamp": "2025-01-01T00:00:00",
            "metadata": {}
        }
        
        checkpoint_file = temp_dir / ".nodupe_checkpoint.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f)
        
        result = Incremental.load_checkpoint(str(temp_dir))
        
        assert result is not None
        assert result["scan_path"] == str(temp_dir)
        assert "file1.txt" in result["processed_files"]

    def test_load_checkpoint_no_file(self, temp_dir):
        """Test loading checkpoint when no file exists."""
        from nodupe.tools.scanner_engine.incremental import Incremental
        
        result = Incremental.load_checkpoint(str(temp_dir))
        
        assert result is None

    def test_load_checkpoint_invalid_json(self, temp_dir):
        """Test loading checkpoint with invalid JSON."""
        from nodupe.tools.scanner_engine.incremental import Incremental
        
        checkpoint_file = temp_dir / ".nodupe_checkpoint.json"
        checkpoint_file.write_text("not valid json")
        
        result = Incremental.load_checkpoint(str(temp_dir))
        
        assert result is None

    def test_load_checkpoint_corrupted(self, temp_dir):
        """Test loading corrupted checkpoint."""
        from nodupe.tools.scanner_engine.incremental import Incremental
        
        checkpoint_file = temp_dir / ".nodupe_checkpoint.json"
        checkpoint_file.write_text("")
        
        result = Incremental.load_checkpoint(str(temp_dir))
        
        assert result is None

    def test_get_remaining_files_no_checkpoint(self, temp_dir):
        """Test getting remaining files when no checkpoint exists."""
        from nodupe.tools.scanner_engine.incremental import Incremental
        
        all_files = ["file1.txt", "file2.txt", "file3.txt"]
        
        result = Incremental.get_remaining_files(str(temp_dir), all_files)
        
        assert result == all_files

    def test_get_remaining_files_with_checkpoint(self, temp_dir):
        """Test getting remaining files with existing checkpoint."""
        from nodupe.tools.scanner_engine.incremental import Incremental

        # Create checkpoint with some processed files
        checkpoint_data = {
            "scan_path": str(temp_dir),
            "processed_files": {
                "file1.txt": {"hash": "abc123"},
                "file2.txt": {"hash": "def456"}
            },
            "timestamp": "2025-01-01T00:00:00",
            "metadata": {}
        }
        
        checkpoint_file = temp_dir / ".nodupe_checkpoint.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f)
        
        all_files = ["file1.txt", "file2.txt", "file3.txt", "file4.txt"]
        
        result = Incremental.get_remaining_files(str(temp_dir), all_files)
        
        assert "file1.txt" not in result
        assert "file2.txt" not in result
        assert "file3.txt" in result
        assert "file4.txt" in result

    def test_update_checkpoint(self, temp_dir):
        """Test updating checkpoint."""
        from nodupe.tools.scanner_engine.incremental import Incremental

        # First save a checkpoint
        initial_files = {"file1.txt": {"hash": "abc123"}}
        Incremental.save_checkpoint(str(temp_dir), initial_files)
        
        # Update with new files
        new_files = {"file2.txt": {"hash": "def456"}}
        Incremental.update_checkpoint(str(temp_dir), new_files)
        
        # Check that both are present
        checkpoint = Incremental.load_checkpoint(str(temp_dir))
        
        assert "file1.txt" in checkpoint["processed_files"]
        assert "file2.txt" in checkpoint["processed_files"]

    def test_update_checkpoint_no_existing(self, temp_dir):
        """Test updating checkpoint when none exists."""
        from nodupe.tools.scanner_engine.incremental import Incremental
        
        new_files = {"file1.txt": {"hash": "abc123"}}
        Incremental.update_checkpoint(str(temp_dir), new_files)
        
        checkpoint = Incremental.load_checkpoint(str(temp_dir))
        
        assert checkpoint is not None
        assert "file1.txt" in checkpoint["processed_files"]

    def test_cleanup_checkpoint(self, temp_dir):
        """Test cleaning up checkpoint."""
        from nodupe.tools.scanner_engine.incremental import Incremental

        # Create checkpoint file
        checkpoint_file = temp_dir / ".nodupe_checkpoint.json"
        checkpoint_file.write_text("{}")
        
        result = Incremental.cleanup_checkpoint(str(temp_dir))
        
        assert result is True
        assert not checkpoint_file.exists()

    def test_cleanup_checkpoint_no_file(self, temp_dir):
        """Test cleaning up checkpoint when no file exists."""
        from nodupe.tools.scanner_engine.incremental import Incremental
        
        result = Incremental.cleanup_checkpoint(str(temp_dir))
        
        assert result is False

    def test_checkpoint_file_name(self):
        """Test checkpoint file name constant."""
        from nodupe.tools.scanner_engine.incremental import Incremental
        
        assert Incremental.CHECKPOINT_FILE == ".nodupe_checkpoint.json"
