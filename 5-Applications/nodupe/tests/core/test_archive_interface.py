"""Tests for the archive_interface module."""

from unittest.mock import MagicMock, Mock

import pytest

from nodupe.core.archive_interface import ArchiveHandlerInterface


class ConcreteArchiveHandler(ArchiveHandlerInterface):
    """Concrete implementation of ArchiveHandlerInterface for testing."""

    def __init__(self):
        """Initialize ConcreteArchiveHandler with default mock values."""
        self._is_archive_result = False
        self._format_result = None
        self._extract_result = {}
        self._create_result = ""
        self._contents_result = []
        self._cleanup_called = False

    def is_archive_file(self, file_path: str) -> bool:
        """Check if file is an archive (mock implementation)."""
        return self._is_archive_result

    def detect_archive_format(self, file_path: str) -> str | None:
        """Detect archive format (mock implementation)."""
        return self._format_result

    def extract_archive(
        self,
        archive_path: str,
        extract_to: str | None = None,
        PASSWORD_REMOVED: bytes | None = None
    ) -> dict[str, str]:
        """Extract archive contents (mock implementation)."""
        return self._extract_result

    def create_archive(
        self,
        output_path: str,
        files: list[str],
        format: str | None = None
    ) -> str:
        """Create archive (mock implementation)."""
        return self._create_result

    def get_archive_contents_info(
        self,
        archive_path: str,
        base_path: str
    ) -> list[dict[str, any]]:
        """Get archive contents info (mock implementation)."""
        return self._contents_result

    def cleanup(self) -> None:
        """Clean up resources (mock implementation)."""
        self._cleanup_called = True


class TestArchiveHandlerInterface:
    """Test ArchiveHandlerInterface abstract base class."""

    def test_interface_cannot_be_instantiated(self):
        """Test that ArchiveHandlerInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ArchiveHandlerInterface()

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that a concrete implementation can be instantiated."""
        handler = ConcreteArchiveHandler()
        assert handler is not None

    def test_is_archive_file_abstract_method(self):
        """Test is_archive_file method signature."""
        handler = ConcreteArchiveHandler()
        result = handler.is_archive_file("/path/to/file.zip")
        assert isinstance(result, bool)

    def test_detect_archive_format_abstract_method(self):
        """Test detect_archive_format method signature."""
        handler = ConcreteArchiveHandler()
        result = handler.detect_archive_format("/path/to/file.zip")
        # Can return string or None
        assert result is None or isinstance(result, str)

    def test_extract_archive_abstract_method(self):
        """Test extract_archive method signature."""
        handler = ConcreteArchiveHandler()
        result = handler.extract_archive("/path/to/archive.zip")
        assert isinstance(result, dict)

    def test_extract_archive_with_extract_to(self):
        """Test extract_archive with extract_to parameter."""
        handler = ConcreteArchiveHandler()
        result = handler.extract_archive(
            "/path/to/archive.zip",
            extract_to="/path/to/extract"
        )
        assert isinstance(result, dict)

    def test_extract_archive_with_password_removed(self):
        """Test extract_archive with PASSWORD_REMOVED parameter."""
        handler = ConcreteArchiveHandler()
        result = handler.extract_archive(
            "/path/to/archive.zip",
            PASSWORD_REMOVED=b"test_password"
        )
        assert isinstance(result, dict)

    def test_extract_archive_with_all_parameters(self):
        """Test extract_archive with all parameters."""
        handler = ConcreteArchiveHandler()
        result = handler.extract_archive(
            "/path/to/archive.zip",
            extract_to="/path/to/extract",
            PASSWORD_REMOVED=b"test_password"
        )
        assert isinstance(result, dict)

    def test_create_archive_abstract_method(self):
        """Test create_archive method signature."""
        handler = ConcreteArchiveHandler()
        result = handler.create_archive("/path/to/output.zip", ["/file1.txt", "/file2.txt"])
        assert isinstance(result, str)

    def test_create_archive_with_format(self):
        """Test create_archive with format parameter."""
        handler = ConcreteArchiveHandler()
        result = handler.create_archive(
            "/path/to/output.zip",
            ["/file1.txt"],
            format="zip"
        )
        assert isinstance(result, str)

    def test_get_archive_contents_info_abstract_method(self):
        """Test get_archive_contents_info method signature."""
        handler = ConcreteArchiveHandler()
        result = handler.get_archive_contents_info("/path/to/archive.zip", "/base")
        assert isinstance(result, list)

    def test_cleanup_abstract_method(self):
        """Test cleanup method."""
        handler = ConcreteArchiveHandler()
        handler.cleanup()
        assert handler._cleanup_called is True


class TestArchiveHandlerInterfaceImplementation:
    """Test ArchiveHandlerInterface with mock implementations."""

    def test_mock_implementation(self):
        """Test with mock implementation."""
        mock_handler = Mock(spec=ArchiveHandlerInterface)
        mock_handler.is_archive_file.return_value = True
        mock_handler.detect_archive_format.return_value = "zip"
        mock_handler.extract_archive.return_value = {"file.txt": "/extracted/file.txt"}
        mock_handler.create_archive.return_value = "/created.zip"
        mock_handler.get_archive_contents_info.return_value = [{"name": "file.txt"}]
        mock_handler.cleanup.return_value = None

        assert mock_handler.is_archive_file("/test.zip") is True
        assert mock_handler.detect_archive_format("/test.zip") == "zip"
        assert mock_handler.extract_archive("/test.zip") == {"file.txt": "/extracted/file.txt"}
        assert mock_handler.create_archive("/out.zip", ["/file.txt"]) == "/created.zip"
        assert mock_handler.get_archive_contents_info("/test.zip", "/base") == [{"name": "file.txt"}]
        mock_handler.cleanup()
        mock_handler.cleanup.assert_called_once()

    def test_is_archive_file_various_paths(self):
        """Test is_archive_file with various file paths."""
        handler = ConcreteArchiveHandler()
        handler._is_archive_result = True

        assert handler.is_archive_file("/path/to/file.zip") is True
        assert handler.is_archive_file("relative/path/file.tar") is True
        assert handler.is_archive_file("file.gz") is True
        assert handler.is_archive_file("") is True

    def test_detect_archive_format_various_formats(self):
        """Test detect_archive_format with various formats."""
        handler = ConcreteArchiveHandler()

        handler._format_result = "zip"
        assert handler.detect_archive_format("/test.zip") == "zip"

        handler._format_result = "tar"
        assert handler.detect_archive_format("/test.tar") == "tar"

        handler._format_result = "gz"
        assert handler.detect_archive_format("/test.gz") == "gz"

        handler._format_result = None
        assert handler.detect_archive_format("/test.txt") is None

    def test_extract_archive_empty_result(self):
        """Test extract_archive with empty result."""
        handler = ConcreteArchiveHandler()
        handler._extract_result = {}

        result = handler.extract_archive("/empty.zip")
        assert result == {}

    def test_extract_archive_multiple_files(self):
        """Test extract_archive with multiple files."""
        handler = ConcreteArchiveHandler()
        handler._extract_result = {
            "file1.txt": "/extracted/file1.txt",
            "file2.txt": "/extracted/file2.txt",
            "subdir/file3.txt": "/extracted/subdir/file3.txt"
        }

        result = handler.extract_archive("/archive.zip")
        assert len(result) == 3
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "subdir/file3.txt" in result

    def test_create_archive_empty_files_list(self):
        """Test create_archive with empty files list."""
        handler = ConcreteArchiveHandler()
        handler._create_result = "/empty.zip"

        result = handler.create_archive("/empty.zip", [])
        assert result == "/empty.zip"

    def test_create_archive_single_file(self):
        """Test create_archive with single file."""
        handler = ConcreteArchiveHandler()
        handler._create_result = "/single.zip"

        result = handler.create_archive("/single.zip", ["/file.txt"])
        assert result == "/single.zip"

    def test_create_archive_multiple_files(self):
        """Test create_archive with multiple files."""
        handler = ConcreteArchiveHandler()
        handler._create_result = "/multi.zip"

        files = ["/file1.txt", "/file2.txt", "/file3.txt"]
        result = handler.create_archive("/multi.zip", files)
        assert result == "/multi.zip"

    def test_get_archive_contents_info_empty(self):
        """Test get_archive_contents_info with empty archive."""
        handler = ConcreteArchiveHandler()
        handler._contents_result = []

        result = handler.get_archive_contents_info("/empty.zip", "/base")
        assert result == []

    def test_get_archive_contents_info_with_metadata(self):
        """Test get_archive_contents_info with file metadata."""
        handler = ConcreteArchiveHandler()
        handler._contents_result = [
            {
                "name": "file1.txt",
                "size": 1024,
                "modified": "2024-01-01T00:00:00Z",
                "is_dir": False
            },
            {
                "name": "subdir",
                "size": 0,
                "modified": "2024-01-01T00:00:00Z",
                "is_dir": True
            }
        ]

        result = handler.get_archive_contents_info("/archive.zip", "/base")
        assert len(result) == 2
        assert result[0]["name"] == "file1.txt"
        assert result[0]["size"] == 1024
        assert result[1]["is_dir"] is True


class TestArchiveHandlerInterfaceEdgeCases:
    """Test edge cases for ArchiveHandlerInterface."""

    def test_is_archive_file_none_path(self):
        """Test is_archive_file with None path."""
        handler = ConcreteArchiveHandler()
        handler._is_archive_result = False

        # Should handle None gracefully
        result = handler.is_archive_file(None)  # type: ignore
        assert result is False

    def test_detect_archive_format_empty_string(self):
        """Test detect_archive_format with empty string."""
        handler = ConcreteArchiveHandler()
        handler._format_result = None

        result = handler.detect_archive_format("")
        assert result is None

    def test_extract_archive_none_archive_path(self):
        """Test extract_archive with None archive path."""
        handler = ConcreteArchiveHandler()
        handler._extract_result = {}

        result = handler.extract_archive(None)  # type: ignore
        assert result == {}

    def test_create_archive_none_output_path(self):
        """Test create_archive with None output path."""
        handler = ConcreteArchiveHandler()
        handler._create_result = ""

        result = handler.create_archive(None, [])  # type: ignore
        assert result == ""

    def test_get_archive_contents_info_none_paths(self):
        """Test get_archive_contents_info with None paths."""
        handler = ConcreteArchiveHandler()
        handler._contents_result = []

        result = handler.get_archive_contents_info(None, None)  # type: ignore
        assert result == []

    def test_cleanup_called_multiple_times(self):
        """Test cleanup can be called multiple times."""
        handler = ConcreteArchiveHandler()

        handler.cleanup()
        handler.cleanup()
        handler.cleanup()

        assert handler._cleanup_called is True

    def test_interface_subclass_check(self):
        """Test that concrete implementation is recognized as subclass."""
        assert issubclass(ConcreteArchiveHandler, ArchiveHandlerInterface)

    def test_instance_check(self):
        """Test that concrete instance is recognized as instance."""
        handler = ConcreteArchiveHandler()
        assert isinstance(handler, ArchiveHandlerInterface)
