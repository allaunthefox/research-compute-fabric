"""Test Filesystem Module - Coverage Completion.

Tests to achieve 100% coverage for filesystem.py
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from nodupe.tools.os_filesystem.filesystem import (
    Filesystem,
    FilesystemError,
)


class TestFilesystemSafeRead:
    """Test safe_read method."""

    def test_safe_read_string_path(self):
        """Test reading file with string path."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            f.flush()
            result = Filesystem.safe_read(f.name)
            assert result == b'test content'

    def test_safe_read_path_object(self):
        """Test reading file with Path object."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            f.flush()
            result = Filesystem.safe_read(Path(f.name))
            assert result == b'test content'

    def test_safe_read_not_exists(self):
        """Test reading nonexistent file."""
        with pytest.raises(FilesystemError) as exc_info:
            Filesystem.safe_read("/nonexistent/file.txt")
        assert "does not exist" in str(exc_info.value)

    def test_safe_read_is_directory(self):
        """Test reading a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.safe_read(tmpdir)
            assert "not a file" in str(exc_info.value)

    def test_safe_read_exceeds_max_size(self):
        """Test reading file that exceeds max size."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            f.flush()
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.safe_read(f.name, max_size=5)
            assert "exceeds limit" in str(exc_info.value)

    def test_safe_read_within_max_size(self):
        """Test reading file within max size."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test')
            f.flush()
            result = Filesystem.safe_read(f.name, max_size=10)
            assert result == b'test'

    def test_safe_read_os_error(self):
        """Test reading file with OS error."""
        with patch('pathlib.Path.exists', side_effect=OSError("Permission denied")):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.safe_read("/test")
            assert "Failed to read" in str(exc_info.value)


class TestFilesystemSafeWrite:
    """Test safe_write method."""

    def test_safe_write_string_path(self):
        """Test writing file with string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")
            Filesystem.safe_write(filepath, b'test content')
            assert Path(filepath).read_bytes() == b'test content'

    def test_safe_write_path_object(self):
        """Test writing file with Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            Filesystem.safe_write(filepath, b'test content')
            assert filepath.read_bytes() == b'test content'

    def test_safe_write_creates_parent_dir(self):
        """Test that safe_write creates parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "test.txt"
            Filesystem.safe_write(filepath, b'test content')
            assert filepath.read_bytes() == b'test content'

    def test_safe_write_non_atomic(self):
        """Test non-atomic write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            Filesystem.safe_write(filepath, b'test content', atomic=False)
            assert filepath.read_bytes() == b'test content'

    def test_safe_write_atomic_failure_cleanup(self):
        """Test that atomic write cleans up temp file on failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            with patch('os.write', side_effect=OSError("Write failed")):
                with pytest.raises(FilesystemError):
                    Filesystem.safe_write(filepath, b'test content', atomic=True)
            # Temp file should be cleaned up
            temp_files = list(Path(tmpdir).glob(".test.txt.tmp*"))
            assert len(temp_files) == 0

    def test_safe_write_os_error(self):
        """Test writing file with OS error."""
        with patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.safe_write("/test/file.txt", b'content')
            assert "Failed to write" in str(exc_info.value)


class TestFilesystemValidatePath:
    """Test validate_path method."""

    def test_validate_path_string(self):
        """Test validating string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Filesystem.validate_path(tmpdir)
            assert result is True

    def test_validate_path_object(self):
        """Test validating Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Filesystem.validate_path(Path(tmpdir))
            assert result is True

    def test_validate_path_must_exist_exists(self):
        """Test validating path that must exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = Filesystem.validate_path(tmpdir, must_exist=True)
            assert result is True

    def test_validate_path_must_exist_not_exists(self):
        """Test validating path that must exist but doesn't."""
        with pytest.raises(FilesystemError) as exc_info:
            Filesystem.validate_path("/nonexistent/path", must_exist=True)
        assert "does not exist" in str(exc_info.value)

    def test_validate_path_os_error(self):
        """Test validating path with OS error."""
        with patch('pathlib.Path.resolve', side_effect=OSError("Cannot resolve")):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.validate_path("/test")
            assert "Invalid path" in str(exc_info.value)

    def test_validate_path_runtime_error(self):
        """Test validating path with RuntimeError."""
        with patch('pathlib.Path.resolve', side_effect=RuntimeError("Error")):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.validate_path("/test")
            assert "Invalid path" in str(exc_info.value)


class TestFilesystemGetSize:
    """Test get_size method."""

    def test_get_size_string_path(self):
        """Test getting size with string path."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            f.flush()
            size = Filesystem.get_size(f.name)
            assert size == len(b'test content')

    def test_get_size_path_object(self):
        """Test getting size with Path object."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content')
            f.flush()
            size = Filesystem.get_size(Path(f.name))
            assert size == len(b'test content')

    def test_get_size_os_error(self):
        """Test getting size with OS error."""
        with patch('pathlib.Path.stat', side_effect=OSError("Cannot stat")):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.get_size("/test")
            assert "Failed to get file size" in str(exc_info.value)


class TestFilesystemListDirectory:
    """Test list_directory method."""

    def test_list_directory_string_path(self):
        """Test listing directory with string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir).joinpath("file1.txt").touch()
            Path(tmpdir).joinpath("file2.txt").touch()
            result = Filesystem.list_directory(tmpdir)
            assert len(result) == 2

    def test_list_directory_path_object(self):
        """Test listing directory with Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir).joinpath("file1.txt").touch()
            result = Filesystem.list_directory(Path(tmpdir))
            assert len(result) == 1

    def test_list_directory_with_pattern(self):
        """Test listing directory with pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir).joinpath("file1.txt").touch()
            Path(tmpdir).joinpath("file2.py").touch()
            result = Filesystem.list_directory(tmpdir, pattern="*.py")
            assert len(result) == 1
            assert result[0].name == "file2.py"

    def test_list_directory_not_dir(self):
        """Test listing a file as directory."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.list_directory(f.name)
            assert "not a directory" in str(exc_info.value)

    def test_list_directory_os_error(self):
        """Test listing directory with OS error."""
        with patch('pathlib.Path.is_dir', side_effect=OSError("Permission denied")):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.list_directory("/test")
            assert "Failed to list directory" in str(exc_info.value)


class TestFilesystemEnsureDirectory:
    """Test ensure_directory method."""

    def test_ensure_directory_string_path(self):
        """Test ensuring directory with string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new", "nested", "dir")
            Filesystem.ensure_directory(new_dir)
            assert Path(new_dir).is_dir()

    def test_ensure_directory_path_object(self):
        """Test ensuring directory with Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "dir"
            Filesystem.ensure_directory(new_dir)
            assert new_dir.is_dir()

    def test_ensure_directory_exists(self):
        """Test ensuring directory that already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Filesystem.ensure_directory(tmpdir)
            assert Path(tmpdir).is_dir()

    def test_ensure_directory_os_error(self):
        """Test ensuring directory with OS error."""
        with patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.ensure_directory("/test/dir")
            assert "Failed to create directory" in str(exc_info.value)


class TestFilesystemRemoveFile:
    """Test remove_file method."""

    def test_remove_file_string_path(self):
        """Test removing file with string path."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            filepath = f.name
        Filesystem.remove_file(filepath)
        assert not Path(filepath).exists()

    def test_remove_file_path_object(self):
        """Test removing file with Path object."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            filepath = Path(f.name)
        Filesystem.remove_file(filepath)
        assert not filepath.exists()

    def test_remove_file_missing_ok_true(self):
        """Test removing nonexistent file with missing_ok=True."""
        # Should not raise
        Filesystem.remove_file("/nonexistent/file.txt", missing_ok=True)

    def test_remove_file_missing_ok_false(self):
        """Test removing nonexistent file with missing_ok=False."""
        with pytest.raises(FilesystemError):
            Filesystem.remove_file("/nonexistent/file.txt", missing_ok=False)

    def test_remove_file_os_error(self):
        """Test removing file with OS error."""
        with patch('pathlib.Path.unlink', side_effect=OSError("Permission denied")):
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.remove_file("/test")
            assert "Failed to remove" in str(exc_info.value)


class TestFilesystemCopyFile:
    """Test copy_file method."""

    def test_copy_file_string_paths(self):
        """Test copying file with string paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "src.txt")
            dst = os.path.join(tmpdir, "dst.txt")
            Path(src).write_text("content")
            Filesystem.copy_file(src, dst)
            assert Path(dst).read_text() == "content"

    def test_copy_file_path_objects(self):
        """Test copying file with Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.txt"
            dst = Path(tmpdir) / "dst.txt"
            src.write_text("content")
            Filesystem.copy_file(src, dst)
            assert dst.read_text() == "content"

    def test_copy_file_src_not_exists(self):
        """Test copying nonexistent source file."""
        with pytest.raises(FilesystemError) as exc_info:
            Filesystem.copy_file("/nonexistent/src.txt", "/dst.txt")
        assert "Source file does not exist" in str(exc_info.value)

    def test_copy_file_dst_exists_no_overwrite(self):
        """Test copying when destination exists without overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.txt"
            dst = Path(tmpdir) / "dst.txt"
            src.touch()
            dst.touch()
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.copy_file(src, dst, overwrite=False)
            assert "Destination file exists" in str(exc_info.value)

    def test_copy_file_dst_exists_with_overwrite(self):
        """Test copying when destination exists with overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.txt"
            dst = Path(tmpdir) / "dst.txt"
            src.write_text("new content")
            dst.write_text("old content")
            Filesystem.copy_file(src, dst, overwrite=True)
            assert dst.read_text() == "new content"

    def test_copy_file_creates_parent_dir(self):
        """Test that copy_file creates parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.txt"
            dst = Path(tmpdir) / "subdir" / "dst.txt"
            src.write_text("content")
            Filesystem.copy_file(src, dst)
            assert dst.read_text() == "content"

    def test_copy_file_os_error(self):
        """Test copying file with OS error."""
        with patch('shutil.copy2', side_effect=OSError("Copy failed")):
            with tempfile.TemporaryDirectory() as tmpdir:
                src = Path(tmpdir) / "src.txt"
                dst = Path(tmpdir) / "dst.txt"
                src.touch()
                with pytest.raises(FilesystemError) as exc_info:
                    Filesystem.copy_file(src, dst)
                assert "Failed to copy" in str(exc_info.value)


class TestFilesystemMoveFile:
    """Test move_file method."""

    def test_move_file_string_paths(self):
        """Test moving file with string paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "src.txt")
            dst = os.path.join(tmpdir, "dst.txt")
            Path(src).write_text("content")
            Filesystem.move_file(src, dst)
            assert not Path(src).exists()
            assert Path(dst).read_text() == "content"

    def test_move_file_path_objects(self):
        """Test moving file with Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.txt"
            dst = Path(tmpdir) / "dst.txt"
            src.write_text("content")
            Filesystem.move_file(src, dst)
            assert not src.exists()
            assert dst.read_text() == "content"

    def test_move_file_src_not_exists(self):
        """Test moving nonexistent source file."""
        with pytest.raises(FilesystemError) as exc_info:
            Filesystem.move_file("/nonexistent/src.txt", "/dst.txt")
        assert "Source file does not exist" in str(exc_info.value)

    def test_move_file_dst_exists_no_overwrite(self):
        """Test moving when destination exists without overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.txt"
            dst = Path(tmpdir) / "dst.txt"
            src.touch()
            dst.touch()
            with pytest.raises(FilesystemError) as exc_info:
                Filesystem.move_file(src, dst, overwrite=False)
            assert "Destination file exists" in str(exc_info.value)

    def test_move_file_dst_exists_with_overwrite(self):
        """Test moving when destination exists with overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.txt"
            dst = Path(tmpdir) / "dst.txt"
            src.write_text("new content")
            dst.write_text("old content")
            Filesystem.move_file(src, dst, overwrite=True)
            assert not src.exists()
            assert dst.read_text() == "new content"

    def test_move_file_creates_parent_dir(self):
        """Test that move_file creates parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.txt"
            dst = Path(tmpdir) / "subdir" / "dst.txt"
            src.write_text("content")
            Filesystem.move_file(src, dst)
            assert dst.read_text() == "content"

    def test_move_file_os_error(self):
        """Test moving file with OS error."""
        with patch('shutil.move', side_effect=OSError("Move failed")):
            with tempfile.TemporaryDirectory() as tmpdir:
                src = Path(tmpdir) / "src.txt"
                dst = Path(tmpdir) / "dst.txt"
                src.touch()
                with pytest.raises(FilesystemError) as exc_info:
                    Filesystem.move_file(src, dst)
                assert "Failed to move" in str(exc_info.value)


class TestFilesystemError:
    """Test FilesystemError exception."""

    def test_filesystem_error_creation(self):
        """Test creating FilesystemError."""
        error = FilesystemError("Test error")
        assert str(error) == "Test error"

    def test_filesystem_error_with_cause(self):
        """Test creating FilesystemError with cause."""
        original_error = ValueError("Original error")
        error = FilesystemError("Filesystem error")
        error.__cause__ = original_error
        assert error.__cause__ is not None
