"""Tests for file_info module."""

from pathlib import Path

import pytest


class TestFileInfo:
    """Test FileInfo class."""

    def test_initialization(self, temp_dir):
        """Test FileInfo initialization."""
        from nodupe.tools.scanner_engine.file_info import FileInfo

        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        file_info = FileInfo(test_file)

        assert file_info.file_path == test_file

    def test_get_info(self, temp_dir):
        """Test getting file info."""
        from nodupe.tools.scanner_engine.file_info import FileInfo

        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        file_info = FileInfo(test_file)

        info = file_info.get_info()

        assert 'path' in info
        assert 'size' in info
        assert 'mtime' in info
        assert 'ctime' in info
        assert 'is_file' in info
        assert 'is_dir' in info
        assert 'is_symlink' in info

        assert info['path'] == str(test_file)
        assert info['size'] > 0
        assert info['is_file'] is True
        assert info['is_dir'] is False

    def test_get_info_nonexistent_file(self, temp_dir):
        """Test getting info for nonexistent file."""
        from nodupe.tools.scanner_engine.file_info import FileInfo

        nonexistent = temp_dir / "nonexistent.txt"

        file_info = FileInfo(nonexistent)

        with pytest.raises(FileNotFoundError):
            file_info.get_info()

    def test_get_info_directory(self, temp_dir):
        """Test getting info for directory."""
        from nodupe.tools.scanner_engine.file_info import FileInfo

        subdir = temp_dir / "subdir"
        subdir.mkdir()

        file_info = FileInfo(subdir)

        info = file_info.get_info()

        assert info['is_dir'] is True
        assert info['is_file'] is False

    def test_get_info_symlink(self, temp_dir):
        """Test getting info for symlink."""
        from nodupe.tools.scanner_engine.file_info import FileInfo

        real_file = temp_dir / "real.txt"
        real_file.write_text("content")

        symlink = temp_dir / "link.txt"
        symlink.symlink_to(real_file)

        file_info = FileInfo(symlink)

        info = file_info.get_info()

        assert info['is_symlink'] is True

    def test_get_info_with_path_object(self, temp_dir):
        """Test FileInfo with Path object."""
        from nodupe.tools.scanner_engine.file_info import FileInfo

        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        file_info = FileInfo(Path(test_file))

        info = file_info.get_info()

        assert info['is_file'] is True
