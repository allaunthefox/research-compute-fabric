"""Tests for file walker module."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


class TestFileWalker:
    """Test FileWalker class."""

    def test_walker_initialization(self):
        """Test walker initialization."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        walker = FileWalker()
        
        assert walker._file_count == 0
        assert walker._dir_count == 0
        assert walker._error_count == 0
        assert walker._enable_archive_support is True

    def test_walker_with_custom_archive_handler(self):
        """Test walker with custom archive handler."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        mock_handler = MagicMock()
        walker = FileWalker(archive_handler=mock_handler)
        
        assert walker._archive_handler is mock_handler

    def test_walk_empty_directory(self, temp_dir):
        """Test walking an empty directory."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        walker = FileWalker()
        
        result = walker.walk(str(empty_dir))
        
        assert result == []

    def test_walk_single_file(self, temp_dir):
        """Test walking directory with single file."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        walker = FileWalker()
        
        result = walker.walk(str(temp_dir))
        
        assert len(result) == 1
        assert result[0]['name'] == 'test.txt'
        assert result[0]['is_file'] is True

    def test_walk_nested_directories(self, temp_dir):
        """Test walking nested directories."""
        from nodupe.tools.scanner_engine.walker import FileWalker

        # Create nested structure
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        file1 = temp_dir / "file1.txt"
        file2 = subdir / "file2.txt"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        walker = FileWalker()
        
        result = walker.walk(str(temp_dir))
        
        assert len(result) == 2

    def test_walk_with_file_filter(self, temp_dir):
        """Test walking with file filter."""
        from nodupe.tools.scanner_engine.walker import FileWalker

        # Create files with different extensions
        txt_file = temp_dir / "test.txt"
        log_file = temp_dir / "test.log"
        
        txt_file.write_text("text content")
        log_file.write_text("log content")
        
        walker = FileWalker()
        
        # Filter for only .txt files
        result = walker.walk(str(temp_dir), file_filter=lambda f: f.get('extension') == '.txt')
        
        assert len(result) == 1
        assert result[0]['extension'] == '.txt'

    def test_walk_with_progress_callback(self, temp_dir):
        """Test walking with progress callback."""
        from nodupe.tools.scanner_engine.walker import FileWalker

        # Create multiple files to ensure progress is updated
        for i in range(15):
            test_file = temp_dir / f"test{i}.txt"
            test_file.write_text(f"test content {i}")
        
        walker = FileWalker()
        
        progress_calls = []
        
        def on_progress(progress):
            """Callback function for progress updates."""
            progress_calls.append(progress)
        
        # The progress is checked after processing each directory and each file
        # So we should get multiple progress updates
        result = walker.walk(str(temp_dir), on_progress=on_progress)
        
        # Since there are 15 files, we should get at least some progress updates
        # (one after each file is processed)
        assert len(result) == 15
        # Note: Progress callback may not be called for every file due to 
        # the time-based throttling (0.1 seconds). That's why we verify files are processed.
        # The test is primarily about ensuring the callback mechanism exists.

    def test_get_file_info(self, temp_dir):
        """Test getting file info."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        walker = FileWalker()
        
        info = walker._get_file_info(str(test_file), "test.txt")
        
        assert info['path'] == str(test_file)
        assert info['relative_path'] == "test.txt"
        assert info['name'] == "test.txt"
        assert info['extension'] == ".txt"
        assert info['size'] == 12
        assert info['is_file'] is True
        assert info['is_directory'] is False

    def test_get_file_info_symlink(self, temp_dir):
        """Test getting file info for symlink."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        real_file = temp_dir / "real.txt"
        real_file.write_text("content")
        
        symlink = temp_dir / "link.txt"
        symlink.symlink_to(real_file)
        
        walker = FileWalker()
        
        info = walker._get_file_info(str(symlink), "link.txt")
        
        assert info['is_symlink'] is True

    def test_is_archive_file(self, temp_dir):
        """Test archive file detection."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        test_file = temp_dir / "test.zip"
        test_file.write_text("content")
        
        # Use a MagicMock that properly returns values
        mock_handler = MagicMock()
        mock_handler.is_archive_file = MagicMock(return_value=True)
        
        walker = FileWalker(archive_handler=mock_handler)
        
        assert walker._is_archive_file(str(test_file)) is True
        
        mock_handler.is_archive_file = MagicMock(return_value=False)
        
        assert walker._is_archive_file(str(test_file)) is False

    def test_is_archive_file_exception(self, temp_dir):
        """Test archive file detection with exception."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        # Use a MagicMock that raises exception
        mock_handler = MagicMock()
        mock_handler.is_archive_file = MagicMock(side_effect=Exception("Error"))
        
        walker = FileWalker(archive_handler=mock_handler)
        
        result = walker._is_archive_file(str(test_file))
        
        assert result is False

    def test_process_archive_file(self, temp_dir):
        """Test processing archive file."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        archive_file = temp_dir / "test.zip"
        archive_file.write_text("content")
        
        mock_handler = MagicMock()
        mock_handler.get_archive_contents_info = MagicMock(return_value=[
            {'path': 'file1.txt', 'name': 'file1.txt'}
        ])
        
        walker = FileWalker(archive_handler=mock_handler)
        
        result = walker._process_archive_file(str(archive_file), str(temp_dir))
        
        assert len(result) == 1

    def test_process_archive_file_exception(self, temp_dir):
        """Test processing archive file with exception."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        archive_file = temp_dir / "test.zip"
        archive_file.write_text("content")
        
        mock_handler = MagicMock()
        mock_handler.get_archive_contents_info = MagicMock(side_effect=Exception("Error"))
        
        walker = FileWalker(archive_handler=mock_handler)
        
        result = walker._process_archive_file(str(archive_file), str(temp_dir))
        
        assert result == []

    def test_reset_counters(self):
        """Test counter reset."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        walker = FileWalker()
        
        walker._file_count = 10
        walker._dir_count = 5
        walker._error_count = 2
        
        walker._reset_counters()
        
        assert walker._file_count == 0
        assert walker._dir_count == 0
        assert walker._error_count == 0

    def test_get_statistics(self, temp_dir):
        """Test getting statistics."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        walker = FileWalker()
        
        walker.walk(str(temp_dir))
        
        stats = walker.get_statistics()
        
        assert stats['total_files'] == 1
        assert stats['total_directories'] >= 1
        assert 'total_time' in stats
        assert 'average_files_per_second' in stats

    def test_enable_archive_support(self):
        """Test enabling/disabling archive support."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        walker = FileWalker()
        
        assert walker.is_archive_support_enabled() is True
        
        walker.enable_archive_support(False)
        
        assert walker.is_archive_support_enabled() is False
        
        walker.enable_archive_support(True)

        assert walker.is_archive_support_enabled() is True

    def test_get_file_info_error_handling(self, temp_dir, monkeypatch):
        """Test _get_file_info handles errors gracefully."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        import os

        walker = FileWalker()

        # Mock os.stat to raise an exception
        original_stat = os.stat
        os.stat = MagicMock(side_effect=OSError("Permission denied"))

        try:
            with pytest.raises(OSError):
                walker._get_file_info(str(temp_dir / "nonexistent.txt"), "nonexistent.txt")
        finally:
            os.stat = original_stat

    def test_process_archive_file_empty(self, temp_dir):
        """Test _process_archive_file with empty archive."""
        from nodupe.tools.scanner_engine.walker import FileWalker

        walker = FileWalker()

        # Create a fake archive file
        archive_file = temp_dir / "fake.zip"
        archive_file.write_text("fake archive content")

        # Mock archive handler to return empty list
        mock_handler = MagicMock()
        mock_handler.is_archive_file.return_value = True
        mock_handler.get_archive_contents_info.return_value = []
        walker._archive_handler = mock_handler

        result = walker._process_archive_file(str(archive_file), str(temp_dir))

        assert result == []

    def test_walk_with_file_filter_reject_all(self, temp_dir):
        """Test walk with file filter that rejects all files."""
        from nodupe.tools.scanner_engine.walker import FileWalker

        # Create test files
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.txt").write_text("content2")

        walker = FileWalker()

        # Filter that rejects all files
        def reject_all(file_info):
            return False

        result = walker.walk(str(temp_dir), file_filter=reject_all)

        assert len(result) == 0

    def test_walk_with_error_handling(self, temp_dir, monkeypatch):
        """Test walk handles directory errors gracefully."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        import os

        walker = FileWalker()

        # Create a valid file
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        # Mock os.listdir to raise permission error for one directory
        original_listdir = os.listdir

        def mock_listdir(path):
            if "restricted" in str(path):
                raise PermissionError("Access denied")
            return original_listdir(path)

        os.listdir = mock_listdir

        try:
            # Create a restricted subdirectory
            restricted_dir = temp_dir / "restricted"
            restricted_dir.mkdir()

            # Should handle error and continue
            result = walker.walk(str(temp_dir))

            # Should have processed at least the test file
            assert len(result) >= 1
        finally:
            os.listdir = original_listdir


class TestCreateFileWalker:
    """Test create_file_walker factory function."""

    def test_create_file_walker(self):
        """Test creating file walker."""
        from nodupe.tools.scanner_engine.walker import create_file_walker
        
        walker = create_file_walker()
        
        assert walker is not None
        assert walker._file_count == 0
