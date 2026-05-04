"""Test Security Logic Module - Coverage Completion.

Tests to achieve 100% coverage for security_logic.py
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from nodupe.tools.security_audit.security_logic import (
    Security,
    SecurityError,
)


class TestSecuritySanitizePathEdgeCases:
    """Test sanitize_path edge cases for full coverage."""

    def test_sanitize_path_with_path_object(self):
        """Test sanitizing a Path object."""
        path_obj = Path("test/file.txt")
        result = Security.sanitize_path(path_obj)
        assert "test" in result
        assert "file.txt" in result

    def test_sanitize_path_null_byte(self):
        """Test sanitizing path with null byte."""
        with pytest.raises(SecurityError) as exc_info:
            Security.sanitize_path("test\x00file.txt")
        assert "null bytes" in str(exc_info.value)

    def test_sanitize_path_parent_not_allowed(self):
        """Test sanitizing path with .. when not allowed."""
        with pytest.raises(SecurityError) as exc_info:
            Security.sanitize_path("../test/file.txt", allow_parent=False)
        assert "parent directory" in str(exc_info.value)

    def test_sanitize_path_parent_allowed(self):
        """Test sanitizing path with .. when allowed."""
        result = Security.sanitize_path("../test/file.txt", allow_parent=True)
        assert result is not None

    def test_sanitize_path_backslash_conversion(self):
        """Test sanitizing path with backslashes."""
        result = Security.sanitize_path("test\\file.txt")
        assert "\\" not in result
        assert "/" in result or "test" in result

    def test_sanitize_path_multiple_slashes(self):
        """Test sanitizing path with multiple slashes."""
        result = Security.sanitize_path("test//file.txt")
        assert "//" not in result

    def test_sanitize_path_absolute_not_allowed(self):
        """Test sanitizing absolute path when not allowed."""
        with pytest.raises(SecurityError) as exc_info:
            Security.sanitize_path("/etc/passwd", allow_absolute=False)
        assert "Absolute paths" in str(exc_info.value)

    def test_sanitize_path_resolve_fallback(self):
        """Test sanitizing path when resolve fails."""
        with patch('pathlib.Path.resolve', side_effect=OSError("Cannot resolve")):
            result = Security.sanitize_path("test/file.txt")
            assert result is not None

    def test_sanitize_path_general_exception(self):
        """Test sanitizing path with general exception."""
        with patch('pathlib.Path.resolve', side_effect=RuntimeError("Unexpected error")):
            result = Security.sanitize_path("test/file.txt")
            assert result is not None


class TestSecurityValidatePathEdgeCases:
    """Test validate_path edge cases for full coverage."""

    def test_validate_path_string_input(self):
        """Test validating string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            Path(test_file).touch()
            result = Security.validate_path(test_file, must_exist=True)
            assert result is True

    def test_validate_path_path_object_input(self):
        """Test validating Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            result = Security.validate_path(test_file, must_exist=True)
            assert result is True

    def test_validate_path_cannot_resolve(self):
        """Test validating path that cannot be resolved."""
        with patch('pathlib.Path.resolve', side_effect=OSError("Cannot resolve")):
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_path("test/file.txt", must_exist=True)
            assert "Cannot resolve" in str(exc_info.value)

    def test_validate_path_allowed_parent_string(self):
        """Test validating path with allowed parent as string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            result = Security.validate_path(
                str(test_file),
                must_exist=True,
                allowed_parent=tmpdir
            )
            assert result is True

    def test_validate_path_outside_allowed_parent(self):
        """Test validating path outside allowed parent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            other_dir = tempfile.mkdtemp()
            test_file = Path(other_dir) / "test.txt"
            test_file.touch()
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_path(
                    str(test_file),
                    must_exist=True,
                    allowed_parent=tmpdir
                )
            assert "outside allowed directory" in str(exc_info.value)

    def test_validate_path_allowed_parent_cannot_resolve(self):
        """Test validating path when allowed parent cannot be resolved."""
        with patch('pathlib.Path.resolve', side_effect=OSError("Cannot resolve")):
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_path(
                    "test/file.txt",
                    must_exist=True,
                    allowed_parent="/nonexistent"
                )
            assert "Cannot resolve" in str(exc_info.value)

    def test_validate_path_must_exist_not_exists(self):
        """Test validating path that must exist but doesn't."""
        with pytest.raises(SecurityError) as exc_info:
            Security.validate_path("/nonexistent/file.txt", must_exist=True)
        assert "does not exist" in str(exc_info.value)

    def test_validate_path_must_be_file_not_file(self):
        """Test validating path that must be file but is directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_path(tmpdir, must_be_file=True)
            assert "not a file" in str(exc_info.value)

    def test_validate_path_must_be_dir_not_dir(self):
        """Test validating path that must be directory but is file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_path(test_file, must_be_dir=True)
            assert "not a directory" in str(exc_info.value)

    def test_validate_path_general_exception(self):
        """Test validating path with general exception."""
        with patch('pathlib.Path.resolve', side_effect=Exception("Unexpected")):
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_path("test/file.txt")
            assert "validation failed" in str(exc_info.value)


class TestSecuritySanitizeFilenameEdgeCases:
    """Test sanitize_filename edge cases for full coverage."""

    def test_sanitize_filename_empty(self):
        """Test sanitizing empty filename."""
        with pytest.raises(SecurityError) as exc_info:
            Security.sanitize_filename("")
        assert "Invalid filename" in str(exc_info.value)

    def test_sanitize_filename_dot(self):
        """Test sanitizing dot filename."""
        with pytest.raises(SecurityError) as exc_info:
            Security.sanitize_filename(".")
        assert "Invalid filename" in str(exc_info.value)

    def test_sanitize_filename_double_dot(self):
        """Test sanitizing double dot filename."""
        with pytest.raises(SecurityError) as exc_info:
            Security.sanitize_filename("..")
        assert "Invalid filename" in str(exc_info.value)

    def test_sanitize_filename_invalid_chars(self):
        """Test sanitizing filename with invalid characters."""
        result = Security.sanitize_filename("test<file>.txt")
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_filename_reserved_name(self):
        """Test sanitizing reserved Windows name."""
        result = Security.sanitize_filename("CON.txt")
        assert result.startswith("_")

    def test_sanitize_filename_truncate_with_extension(self):
        """Test sanitizing filename that needs truncation with extension."""
        long_name = "a" * 300 + ".txt"
        result = Security.sanitize_filename(long_name, max_length=50)
        assert len(result) <= 50
        assert result.endswith(".txt")

    def test_sanitize_filename_truncate_without_extension(self):
        """Test sanitizing filename that needs truncation without extension."""
        long_name = "a" * 300
        result = Security.sanitize_filename(long_name, max_length=50)
        assert len(result) <= 50

    def test_sanitize_filename_becomes_empty(self):
        """Test sanitizing filename that becomes empty."""
        with patch('re.sub', return_value="   "):
            with pytest.raises(SecurityError) as exc_info:
                Security.sanitize_filename("test.txt")
            assert "empty" in str(exc_info.value)

    def test_sanitize_filename_general_exception(self):
        """Test sanitizing filename with general exception."""
        with patch('os.path.basename', side_effect=Exception("Unexpected")):
            with pytest.raises(SecurityError) as exc_info:
                Security.sanitize_filename("test.txt")
            assert "sanitization failed" in str(exc_info.value)


class TestSecurityIsSafePath:
    """Test is_safe_path method."""

    def test_is_safe_path_true(self):
        """Test safe path within base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            result = Security.is_safe_path(str(test_file), tmpdir)
            assert result is True

    def test_is_safe_path_false(self):
        """Test unsafe path outside base."""
        result = Security.is_safe_path("/etc/passwd", "/home")
        assert result is False

    def test_is_safe_path_exception(self):
        """Test is_safe_path with exception."""
        with patch('pathlib.Path.resolve', side_effect=OSError("Cannot resolve")):
            result = Security.is_safe_path("/test", "/base")
            assert result is False


class TestSecurityCheckPermissionsEdgeCases:
    """Test check_permissions edge cases."""

    def test_check_permissions_path_object(self):
        """Test checking permissions with Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            result = Security.check_permissions(test_file, readable=True)
            assert result is True

    def test_check_permissions_not_exists(self):
        """Test checking permissions on nonexistent path."""
        with pytest.raises(SecurityError) as exc_info:
            Security.check_permissions("/nonexistent/file.txt", readable=True)
        assert "does not exist" in str(exc_info.value)

    def test_check_permissions_not_readable(self):
        """Test checking permissions when not readable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            # Make file unreadable
            os.chmod(test_file, 0o000)
            try:
                with pytest.raises(SecurityError) as exc_info:
                    Security.check_permissions(str(test_file), readable=True)
                assert "not readable" in str(exc_info.value)
            finally:
                os.chmod(test_file, 0o644)

    def test_check_permissions_not_writable(self):
        """Test checking permissions when not writable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            # Make file read-only
            os.chmod(test_file, 0o444)
            try:
                with pytest.raises(SecurityError) as exc_info:
                    Security.check_permissions(str(test_file), writable=True)
                assert "not writable" in str(exc_info.value)
            finally:
                os.chmod(test_file, 0o644)

    def test_check_permissions_not_executable(self):
        """Test checking permissions when not executable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            with pytest.raises(SecurityError) as exc_info:
                Security.check_permissions(str(test_file), executable=True)
            assert "not executable" in str(exc_info.value)

    def test_check_permissions_general_exception(self):
        """Test checking permissions with general exception."""
        with patch('pathlib.Path.exists', side_effect=Exception("Unexpected")):
            with pytest.raises(SecurityError) as exc_info:
                Security.check_permissions("/test", readable=True)
            assert "Permission check failed" in str(exc_info.value)


class TestSecurityIsSymlink:
    """Test is_symlink method."""

    def test_is_symlink_true(self):
        """Test detecting symlink."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            link = Path(tmpdir) / "link.txt"
            link.symlink_to(test_file)
            result = Security.is_symlink(str(link))
            assert result is True

    def test_is_symlink_false(self):
        """Test non-symlink."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            result = Security.is_symlink(str(test_file))
            assert result is False

    def test_is_symlink_exception(self):
        """Test is_symlink with exception."""
        with patch('pathlib.Path.is_symlink', side_effect=OSError("Error")):
            result = Security.is_symlink("/test")
            assert result is False


class TestSecurityResolveSymlink:
    """Test resolve_symlink method."""

    def test_resolve_symlink_follow(self):
        """Test resolving symlink with follow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            link = Path(tmpdir) / "link.txt"
            link.symlink_to(test_file)
            result = Security.resolve_symlink(str(link), follow_symlinks=True)
            assert str(test_file) in result

    def test_resolve_symlink_no_follow(self):
        """Test resolving symlink without follow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            link = Path(tmpdir) / "link.txt"
            link.symlink_to(test_file)
            result = Security.resolve_symlink(str(link), follow_symlinks=False)
            assert str(link) in result

    def test_resolve_symlink_path_object(self):
        """Test resolving symlink with Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.touch()
            link = Path(tmpdir) / "link.txt"
            link.symlink_to(test_file)
            result = Security.resolve_symlink(link)
            assert str(test_file) in result

    def test_resolve_symlink_exception(self):
        """Test resolving symlink with exception."""
        with patch('pathlib.Path.resolve', side_effect=OSError("Cannot resolve")):
            with pytest.raises(SecurityError) as exc_info:
                Security.resolve_symlink("/test")
            assert "Cannot resolve" in str(exc_info.value)


class TestSecurityValidateExtension:
    """Test validate_extension method."""

    def test_validate_extension_allowed_with_dot(self):
        """Test validating allowed extension with dot."""
        result = Security.validate_extension("test.txt", [".txt", ".pdf"])
        assert result is True

    def test_validate_extension_allowed_without_dot(self):
        """Test validating allowed extension without dot."""
        result = Security.validate_extension("test.txt", ["txt", "pdf"])
        assert result is True

    def test_validate_extension_not_allowed(self):
        """Test validating disallowed extension."""
        with pytest.raises(SecurityError) as exc_info:
            Security.validate_extension("test.exe", [".txt", ".pdf"])
        assert "not in allowed list" in str(exc_info.value)

    def test_validate_extension_case_insensitive(self):
        """Test validating extension is case insensitive."""
        result = Security.validate_extension("test.TXT", [".txt"])
        assert result is True

    def test_validate_extension_general_exception(self):
        """Test validating extension with general exception."""
        with patch('pathlib.Path.suffix', side_effect=Exception("Error")):
            with pytest.raises(SecurityError) as exc_info:
                Security.validate_extension("test.txt", [".txt"])
            assert "validation failed" in str(exc_info.value)


class TestSecurityGenerateSafeFilename:
    """Test generate_safe_filename method."""

    def test_generate_safe_filename_basic(self):
        """Test generating safe filename basic."""
        result = Security.generate_safe_filename("test", ".txt")
        assert "test" in result
        assert result.endswith(".txt")

    def test_generate_safe_filename_extension_with_dot(self):
        """Test generating safe filename with extension already having dot."""
        result = Security.generate_safe_filename("test", ".txt")
        assert result.endswith(".txt")

    def test_generate_safe_filename_extension_without_dot(self):
        """Test generating safe filename with extension without dot."""
        result = Security.generate_safe_filename("test", "txt")
        assert result.endswith(".txt")

    def test_generate_safe_filename_with_timestamp(self, monkeypatch):
        """Test generating safe filename with timestamp."""
        # Mock datetime to return fixed timestamp
        class MockDatetime:
            """Mock datetime class for testing."""
            @staticmethod
            def now():
                """Return mock current time."""
                class MockNow:
                    """Mock datetime.now() result class."""
                    @staticmethod
                    def strftime(fmt):
                        """Format timestamp as string."""
                        return "20240101_120000"
                return MockNow()

        with patch('nodupe.tools.security_audit.security_logic.datetime', MockDatetime):
            result = Security.generate_safe_filename("test", ".txt", add_timestamp=True)
            assert "test" in result
            assert "20240101_120000" in result

    def test_generate_safe_filename_general_exception(self):
        """Test generating safe filename with general exception."""
        with patch('nodupe.tools.security_audit.security_logic.Security.sanitize_filename',
                   side_effect=Exception("Error")):
            with pytest.raises(SecurityError) as exc_info:
                Security.generate_safe_filename("test", ".txt")
            assert "generation failed" in str(exc_info.value)


class TestSecurityError:
    """Test SecurityError exception."""

    def test_security_error_creation(self):
        """Test creating SecurityError."""
        error = SecurityError("Test error")
        assert str(error) == "Test error"

    def test_security_error_with_cause(self):
        """Test creating SecurityError with cause."""
        original_error = ValueError("Original error")
        error = SecurityError("Security error")
        error.__cause__ = original_error
        assert error.__cause__ is not None
