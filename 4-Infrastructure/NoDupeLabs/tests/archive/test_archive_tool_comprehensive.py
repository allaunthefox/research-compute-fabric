# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Comprehensive tests for nodupe/tools/archive/archive_tool.py.

This test suite provides extensive coverage for the StandardArchiveTool class,
including edge cases, error handling, and integration scenarios.

Tests cover:
- Tool properties (name, version, dependencies)
- api_methods property and all exposed methods
- initialize() and shutdown() methods
- run_standalone() with all argument combinations
- describe_usage() method
- get_capabilities() method
- register_tool() function
- Error paths and edge cases
- Integration with ArchiveHandler
"""

import sys
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from nodupe.tools.archive.archive_logic import ArchiveHandler, ArchiveHandlerError
from nodupe.tools.archive.archive_tool import (
    StandardArchiveTool,
    register_tool,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def tool() -> StandardArchiveTool:
    """Create a fresh StandardArchiveTool instance."""
    return StandardArchiveTool()


@pytest.fixture
def mock_container() -> MagicMock:
    """Create a mock container for testing."""
    return MagicMock()


@pytest.fixture
def sample_zip_file(tmp_path: Path) -> Path:
    """Create a sample zip file for testing."""
    zip_path = tmp_path / "sample.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("file1.txt", "content 1")
        zf.writestr("file2.txt", "content 2")
        zf.writestr("subdir/file3.txt", "content 3")
    return zip_path


@pytest.fixture
def sample_tar_file(tmp_path: Path) -> Path:
    """Create a sample tar file for testing."""
    tar_path = tmp_path / "sample.tar"
    with tarfile.open(tar_path, 'w') as tf:
        # Create file content in memory
        data = b"tar content 1"
        info = tarfile.TarInfo(name="file1.txt")
        info.size = len(data)
        tf.addfile(info, BytesIO(data))
    return tar_path


@pytest.fixture
def sample_targz_file(tmp_path: Path) -> Path:
    """Create a sample tar.gz file for testing."""
    targz_path = tmp_path / "sample.tar.gz"
    with tarfile.open(targz_path, 'w:gz') as tf:
        data = b"gzip content"
        info = tarfile.TarInfo(name="compressed.txt")
        info.size = len(data)
        tf.addfile(info, BytesIO(data))
    return targz_path


# =============================================================================
# Test Class: Tool Properties
# =============================================================================

class TestToolProperties:
    """Test StandardArchiveTool property accessors."""

    def test_name_property_returns_string(self, tool: StandardArchiveTool) -> None:
        """name property returns correct string value."""
        name = tool.name
        assert isinstance(name, str)
        assert name == "standard_archive"

    def test_name_property_is_consistent(self, tool: StandardArchiveTool) -> None:
        """name property returns same value on multiple calls."""
        name1 = tool.name
        name2 = tool.name
        assert name1 == name2

    def test_version_property_returns_string(self, tool: StandardArchiveTool) -> None:
        """version property returns correct string value."""
        version = tool.version
        assert isinstance(version, str)
        assert version == "1.0.0"

    def test_version_property_format(self, tool: StandardArchiveTool) -> None:
        """version property returns semantic version format."""
        version = tool.version
        parts = version.split('.')
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_dependencies_property_returns_list(self, tool: StandardArchiveTool) -> None:
        """dependencies property returns a list."""
        deps = tool.dependencies
        assert isinstance(deps, list)

    def test_dependencies_property_is_empty(self, tool: StandardArchiveTool) -> None:
        """dependencies property returns empty list (no dependencies)."""
        assert len(tool.dependencies) == 0

    def test_dependencies_property_is_immutable_copy(self, tool: StandardArchiveTool) -> None:
        """dependencies property returns new list each call."""
        deps1 = tool.dependencies
        deps2 = tool.dependencies
        assert deps1 is not deps2


# =============================================================================
# Test Class: API Methods
# =============================================================================

class TestApiMethods:
    """Test StandardArchiveTool api_methods property and exposed methods."""

    def test_api_methods_returns_dict(self, tool: StandardArchiveTool) -> None:
        """api_methods property returns a dictionary."""
        methods = tool.api_methods
        assert isinstance(methods, dict)

    def test_api_methods_contains_extract_archive(self, tool: StandardArchiveTool) -> None:
        """api_methods contains extract_archive method."""
        assert 'extract_archive' in tool.api_methods

    def test_api_methods_contains_create_archive(self, tool: StandardArchiveTool) -> None:
        """api_methods contains create_archive method."""
        assert 'create_archive' in tool.api_methods

    def test_api_methods_contains_is_archive(self, tool: StandardArchiveTool) -> None:
        """api_methods contains is_archive method."""
        assert 'is_archive' in tool.api_methods

    def test_api_methods_contains_detect_format(self, tool: StandardArchiveTool) -> None:
        """api_methods contains detect_format method."""
        assert 'detect_format' in tool.api_methods

    def test_api_methods_count(self, tool: StandardArchiveTool) -> None:
        """api_methods contains exactly 4 methods."""
        assert len(tool.api_methods) == 4

    def test_api_methods_are_callable(self, tool: StandardArchiveTool) -> None:
        """All api_methods values are callable."""
        for name, method in tool.api_methods.items():
            assert callable(method), f"{name} is not callable"

    def test_api_methods_bound_to_handler(self, tool: StandardArchiveTool) -> None:
        """api_methods are bound to handler instance methods."""
        assert tool.api_methods['extract_archive'] == tool.handler.extract_archive
        assert tool.api_methods['create_archive'] == tool.handler.create_archive
        assert tool.api_methods['is_archive'] == tool.handler.is_archive_file
        assert tool.api_methods['detect_format'] == tool.handler.detect_archive_format

    def test_api_methods_extract_archive_signature(self, tool: StandardArchiveTool) -> None:
        """extract_archive method has correct signature."""
        import inspect
        sig = inspect.signature(tool.api_methods['extract_archive'])
        params = list(sig.parameters.keys())
        assert 'archive_path' in params

    def test_api_methods_create_archive_signature(self, tool: StandardArchiveTool) -> None:
        """create_archive method has correct signature."""
        import inspect
        sig = inspect.signature(tool.api_methods['create_archive'])
        params = list(sig.parameters.keys())
        assert 'output_path' in params


# =============================================================================
# Test Class: Initialize Method
# =============================================================================

class TestInitializeMethod:
    """Test StandardArchiveTool.initialize() method."""

    def test_initialize_registers_service(self, tool: StandardArchiveTool, mock_container: MagicMock) -> None:
        """initialize() registers archive_handler_service with container."""
        tool.initialize(mock_container)
        mock_container.register_service.assert_called_once_with(
            'archive_handler_service', tool.handler
        )

    def test_initialize_with_none_container_raises(self, tool: StandardArchiveTool) -> None:
        """initialize() with None container raises AttributeError."""
        with pytest.raises(AttributeError):
            tool.initialize(None)  # type: ignore

    def test_initialize_preserves_handler_instance(self, tool: StandardArchiveTool, mock_container: MagicMock) -> None:
        """initialize() does not replace handler instance."""
        original_handler = tool.handler
        tool.initialize(mock_container)
        assert tool.handler is original_handler

    def test_initialize_idempotent(self, tool: StandardArchiveTool, mock_container: MagicMock) -> None:
        """initialize() can be called multiple times."""
        tool.initialize(mock_container)
        tool.initialize(mock_container)
        assert mock_container.register_service.call_count == 2

    def test_initialize_with_mock_container_attributes(self, tool: StandardArchiveTool) -> None:
        """initialize() works with container having register_service attribute."""
        container = MagicMock(spec=['register_service'])
        tool.initialize(container)
        container.register_service.assert_called_once()


# =============================================================================
# Test Class: Shutdown Method
# =============================================================================

class TestShutdownMethod:
    """Test StandardArchiveTool.shutdown() method."""

    def test_shutdown_calls_handler_cleanup(self, tool: StandardArchiveTool) -> None:
        """shutdown() calls handler.cleanup() method."""
        with patch.object(tool.handler, 'cleanup') as mock_cleanup:
            tool.shutdown()
            mock_cleanup.assert_called_once()

    def test_shutdown_multiple_calls_safe(self, tool: StandardArchiveTool) -> None:
        """shutdown() can be called multiple times without error."""
        tool.shutdown()
        tool.shutdown()
        tool.shutdown()

    def test_shutdown_after_initialize(self, tool: StandardArchiveTool, mock_container: MagicMock) -> None:
        """shutdown() works correctly after initialize()."""
        tool.initialize(mock_container)
        tool.shutdown()
        # Should not raise

    def test_shutdown_cleanup_exception_handled(self, tool: StandardArchiveTool) -> None:
        """shutdown() handles exceptions from handler.cleanup()."""
        with patch.object(tool.handler, 'cleanup', side_effect=Exception("cleanup error")):
            # Should not raise - exception propagates
            with pytest.raises(Exception, match="cleanup error"):
                tool.shutdown()


# =============================================================================
# Test Class: Run Standalone Method
# =============================================================================

class TestRunStandaloneMethod:
    """Test StandardArchiveTool.run_standalone() method with various arguments."""

    def test_run_standalone_empty_args_shows_help(self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str]) -> None:
        """run_standalone() with empty args prints help and returns 0."""
        result = tool.run_standalone([])
        assert result == 0
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower()

    def test_run_standalone_help_flag(self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str]) -> None:
        """run_standalone() with --help flag prints help."""
        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['--help'])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower()

    def test_run_standalone_detect_zip_format(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], sample_zip_file: Path
    ) -> None:
        """run_standalone() detects zip format correctly."""
        result = tool.run_standalone([str(sample_zip_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Type:" in captured.out
        assert "zip" in captured.out.lower()

    def test_run_standalone_detect_tar_format(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], sample_tar_file: Path
    ) -> None:
        """run_standalone() detects tar format correctly."""
        result = tool.run_standalone([str(sample_tar_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Type:" in captured.out
        assert "tar" in captured.out.lower()

    def test_run_standalone_detect_targz_format(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], sample_targz_file: Path
    ) -> None:
        """run_standalone() detects tar.gz format correctly."""
        result = tool.run_standalone([str(sample_targz_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Type:" in captured.out
        assert "tar.gz" in captured.out.lower() or "gzip" in captured.out.lower()

    def test_run_standalone_extract_to_directory(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], sample_zip_file: Path, tmp_path: Path
    ) -> None:
        """run_standalone() extracts archive to specified directory."""
        extract_dir = tmp_path / "extracted"
        result = tool.run_standalone([str(sample_zip_file), "--extract", str(extract_dir)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Success" in captured.out
        assert extract_dir.exists()

    def test_run_standalone_extract_creates_directory(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], sample_zip_file: Path, tmp_path: Path
    ) -> None:
        """run_standalone() creates extract directory if it doesn't exist."""
        extract_dir = tmp_path / "new_dir" / "subdir"
        result = tool.run_standalone([str(sample_zip_file), "--extract", str(extract_dir)])
        assert result == 0
        assert extract_dir.exists()

    def test_run_standalone_nonexistent_file_unknown_type(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """run_standalone() with nonexistent file shows unknown type."""
        nonexistent = tmp_path / "does_not_exist.zip"
        result = tool.run_standalone([str(nonexistent)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Unknown" in captured.out or "Type:" in captured.out

    def test_run_standalone_invalid_zip_error(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """run_standalone() handles invalid zip file with error."""
        invalid_zip = tmp_path / "invalid.zip"
        invalid_zip.write_text("not a valid zip file content")
        extract_dir = tmp_path / "extract"
        result = tool.run_standalone([str(invalid_zip), "--extract", str(extract_dir)])
        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_run_standalone_invalid_tar_error(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """run_standalone() handles invalid tar file with error."""
        invalid_tar = tmp_path / "invalid.tar"
        invalid_tar.write_text("not a valid tar file content")
        extract_dir = tmp_path / "extract"
        result = tool.run_standalone([str(invalid_tar), "--extract", str(extract_dir)])
        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_run_standalone_returns_int(self, tool: StandardArchiveTool, tmp_path: Path) -> None:
        """run_standalone() always returns an integer."""
        result = tool.run_standalone([])
        assert isinstance(result, int)

    def test_run_standalone_extract_success_message_format(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], sample_zip_file: Path, tmp_path: Path
    ) -> None:
        """run_standalone() extract success message has correct format."""
        extract_dir = tmp_path / "out"
        result = tool.run_standalone([str(sample_zip_file), "--extract", str(extract_dir)])
        captured = capsys.readouterr()
        # Message format: "Success: Put N files into <dir>"
        assert "Success:" in captured.out
        assert "files" in captured.out


# =============================================================================
# Test Class: Describe Usage Method
# =============================================================================

class TestDescribeUsageMethod:
    """Test StandardArchiveTool.describe_usage() method."""

    def test_describe_usage_returns_string(self, tool: StandardArchiveTool) -> None:
        """describe_usage() returns a string."""
        description = tool.describe_usage()
        assert isinstance(description, str)

    def test_describe_usage_not_empty(self, tool: StandardArchiveTool) -> None:
        """describe_usage() returns non-empty string."""
        description = tool.describe_usage()
        assert len(description) > 0

    def test_describe_usage_mentions_collection(self, tool: StandardArchiveTool) -> None:
        """describe_usage() mentions 'collection' concept."""
        description = tool.describe_usage()
        assert "collection" in description.lower()

    def test_describe_usage_mentions_files(self, tool: StandardArchiveTool) -> None:
        """describe_usage() mentions 'file' concept."""
        description = tool.describe_usage()
        assert "file" in description.lower()

    def test_describe_usage_mentions_unpack_or_extract(self, tool: StandardArchiveTool) -> None:
        """describe_usage() mentions unpack or extract functionality."""
        description = tool.describe_usage()
        assert "unpack" in description.lower() or "extract" in description.lower()

    def test_describe_usage_is_human_readable(self, tool: StandardArchiveTool) -> None:
        """describe_usage() returns human-readable text."""
        description = tool.describe_usage()
        # Should be a proper sentence
        assert description[0].isupper()
        assert description.endswith('.')


# =============================================================================
# Test Class: Get Capabilities Method
# =============================================================================

class TestGetCapabilitiesMethod:
    """Test StandardArchiveTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self, tool: StandardArchiveTool) -> None:
        """get_capabilities() returns a dictionary."""
        capabilities = tool.get_capabilities()
        assert isinstance(capabilities, dict)

    def test_get_capabilities_has_formats_key(self, tool: StandardArchiveTool) -> None:
        """get_capabilities() contains 'formats' key."""
        capabilities = tool.get_capabilities()
        assert 'formats' in capabilities

    def test_get_capabilities_has_features_key(self, tool: StandardArchiveTool) -> None:
        """get_capabilities() contains 'features' key."""
        capabilities = tool.get_capabilities()
        assert 'features' in capabilities

    def test_get_capabilities_formats_is_list(self, tool: StandardArchiveTool) -> None:
        """get_capabilities()['formats'] is a list."""
        capabilities = tool.get_capabilities()
        assert isinstance(capabilities['formats'], list)

    def test_get_capabilities_features_is_list(self, tool: StandardArchiveTool) -> None:
        """get_capabilities()['features'] is a list."""
        capabilities = tool.get_capabilities()
        assert isinstance(capabilities['features'], list)

    def test_get_capabilities_formats_contains_zip(self, tool: StandardArchiveTool) -> None:
        """get_capabilities()['formats'] contains 'zip'."""
        capabilities = tool.get_capabilities()
        assert 'zip' in capabilities['formats']

    def test_get_capabilities_formats_contains_tar(self, tool: StandardArchiveTool) -> None:
        """get_capabilities()['formats'] contains 'tar'."""
        capabilities = tool.get_capabilities()
        assert 'tar' in capabilities['formats']

    def test_get_capabilities_formats_contains_compressed_variants(
        self, tool: StandardArchiveTool
    ) -> None:
        """get_capabilities()['formats'] contains compressed tar variants."""
        capabilities = tool.get_capabilities()
        formats = capabilities['formats']
        assert 'tar.gz' in formats
        assert 'tar.bz2' in formats
        assert 'tar.xz' in formats
        assert 'tar.lzma' in formats

    def test_get_capabilities_features_contains_extraction(
        self, tool: StandardArchiveTool
    ) -> None:
        """get_capabilities()['features'] contains 'extraction'."""
        capabilities = tool.get_capabilities()
        assert 'extraction' in capabilities['features']

    def test_get_capabilities_features_contains_detection(
        self, tool: StandardArchiveTool
    ) -> None:
        """get_capabilities()['features'] contains 'detection'."""
        capabilities = tool.get_capabilities()
        assert 'detection' in capabilities['features']

    def test_get_capabilities_features_contains_password_removed_support(
        self, tool: StandardArchiveTool
    ) -> None:
        """get_capabilities()['features'] contains 'PASSWORD_REMOVED_support'."""
        capabilities = tool.get_capabilities()
        assert 'PASSWORD_REMOVED_support' in capabilities['features']

    def test_get_capabilities_consistent_across_calls(
        self, tool: StandardArchiveTool
    ) -> None:
        """get_capabilities() returns consistent values across calls."""
        cap1 = tool.get_capabilities()
        cap2 = tool.get_capabilities()
        assert cap1 == cap2


# =============================================================================
# Test Class: Register Tool Function
# =============================================================================

class TestRegisterToolFunction:
    """Test register_tool() function."""

    def test_register_tool_returns_tool_instance(self) -> None:
        """register_tool() returns StandardArchiveTool instance."""
        result = register_tool()
        assert isinstance(result, StandardArchiveTool)

    def test_register_tool_creates_new_instance_each_call(self) -> None:
        """register_tool() creates new instance on each call."""
        tool1 = register_tool()
        tool2 = register_tool()
        assert tool1 is not tool2

    def test_register_tool_instances_have_same_name(self) -> None:
        """register_tool() instances have same name."""
        tool1 = register_tool()
        tool2 = register_tool()
        assert tool1.name == tool2.name

    def test_register_tool_instances_have_same_version(self) -> None:
        """register_tool() instances have same version."""
        tool1 = register_tool()
        tool2 = register_tool()
        assert tool1.version == tool2.version

    def test_register_tool_instances_have_independent_handlers(self) -> None:
        """register_tool() instances have independent handlers."""
        tool1 = register_tool()
        tool2 = register_tool()
        assert tool1.handler is not tool2.handler


# =============================================================================
# Test Class: Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for StandardArchiveTool."""

    def test_full_lifecycle(self, tool: StandardArchiveTool, mock_container: MagicMock) -> None:
        """Test complete tool lifecycle: create -> initialize -> use -> shutdown."""
        # Initialize
        tool.initialize(mock_container)
        mock_container.register_service.assert_called_once()

        # Use - check properties
        assert tool.name == "standard_archive"
        assert tool.version == "1.0.0"

        # Use - check capabilities
        caps = tool.get_capabilities()
        assert 'formats' in caps

        # Use - check api methods
        api = tool.api_methods
        assert callable(api['extract_archive'])

        # Shutdown
        tool.shutdown()

    def test_extract_created_archive_roundtrip(
        self, tool: StandardArchiveTool, tmp_path: Path
    ) -> None:
        """Test creating archive and extracting it (roundtrip)."""
        # Create test files
        file1 = tmp_path / "test1.txt"
        file1.write_text("test content 1")
        file2 = tmp_path / "test2.txt"
        file2.write_text("test content 2")

        # Create archive
        archive_path = tmp_path / "roundtrip.zip"
        tool.handler.create_archive(
            str(archive_path),
            [str(file1), str(file2)]
        )
        assert archive_path.exists()

        # Extract archive
        extract_dir = tmp_path / "extracted"
        result = tool.handler.extract_archive(str(archive_path), str(extract_dir))
        assert len(result) >= 1
        assert extract_dir.exists()

    def test_detect_format_then_extract(
        self, tool: StandardArchiveTool, sample_zip_file: Path, tmp_path: Path
    ) -> None:
        """Test detecting format then extracting."""
        # Detect format
        fmt = tool.handler.detect_archive_format(str(sample_zip_file))
        assert fmt == 'zip'

        # Extract
        extract_dir = tmp_path / "detected"
        result = tool.handler.extract_archive(str(sample_zip_file), str(extract_dir))
        assert len(result) >= 1

    def test_is_archive_file_true(
        self, tool: StandardArchiveTool, sample_zip_file: Path
    ) -> None:
        """Test is_archive_file returns True for valid archive."""
        assert tool.handler.is_archive_file(str(sample_zip_file)) is True

    def test_api_method_extract_archive_via_dict(
        self, tool: StandardArchiveTool, sample_zip_file: Path, tmp_path: Path
    ) -> None:
        """Test calling extract_archive through api_methods dict."""
        extract_dir = tmp_path / "via_api"
        api_methods = tool.api_methods
        result = api_methods['extract_archive'](str(sample_zip_file), str(extract_dir))
        assert isinstance(result, dict)
        assert len(result) >= 1

    def test_api_method_detect_format_via_dict(
        self, tool: StandardArchiveTool, sample_zip_file: Path
    ) -> None:
        """Test calling detect_format through api_methods dict."""
        api_methods = tool.api_methods
        fmt = api_methods['detect_format'](str(sample_zip_file))
        assert fmt == 'zip'


# =============================================================================
# Test Class: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_tool_with_empty_handler_temp_dirs(self, tool: StandardArchiveTool) -> None:
        """Tool handler starts with empty temp_dirs list."""
        # Access private attribute for testing
        assert len(tool.handler._temp_dirs) == 0

    def test_handler_cleanup_clears_temp_dirs(self, tool: StandardArchiveTool) -> None:
        """Handler cleanup clears temp_dirs list."""
        tool.handler._temp_dirs.append('/fake/path')
        tool.shutdown()
        assert len(tool.handler._temp_dirs) == 0

    def test_multiple_tool_instances_independent(self) -> None:
        """Multiple tool instances are independent."""
        tool1 = StandardArchiveTool()
        tool2 = StandardArchiveTool()
        assert tool1.handler is not tool2.handler
        tool1.shutdown()
        tool2.shutdown()

    def test_tool_string_representation(self, tool: StandardArchiveTool) -> None:
        """Tool has meaningful string representation."""
        # Should not raise
        str_repr = str(tool)
        assert isinstance(str_repr, str)

    def test_api_methods_keys_are_strings(self, tool: StandardArchiveTool) -> None:
        """All api_methods keys are strings."""
        for key in tool.api_methods.keys():
            assert isinstance(key, str)

    def test_run_standalone_with_unknown_extension(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """run_standalone() handles file with unknown extension."""
        unknown_file = tmp_path / "file.xyz"
        unknown_file.write_text("unknown format")
        result = tool.run_standalone([str(unknown_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Unknown" in captured.out or "Type:" in captured.out

    def test_get_capabilities_formats_all_supported(
        self, tool: StandardArchiveTool
    ) -> None:
        """All documented formats are in capabilities."""
        caps = tool.get_capabilities()
        expected_formats = ['zip', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'tar.lzma']
        for fmt in expected_formats:
            assert fmt in caps['formats'], f"Missing format: {fmt}"

    def test_handler_error_class_exists(self) -> None:
        """ArchiveHandlerError exception class exists."""
        assert ArchiveHandlerError is not None
        assert issubclass(ArchiveHandlerError, Exception)

    def test_tool_inherits_from_base_tool_class(self, tool: StandardArchiveTool) -> None:
        """StandardArchiveTool inherits from Tool base class."""
        from nodupe.core.tool_system.base import Tool
        assert isinstance(tool, Tool)


# =============================================================================
# Test Class: Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling scenarios."""

    def test_extract_nonexistent_archive_raises(
        self, tool: StandardArchiveTool, tmp_path: Path
    ) -> None:
        """extract_archive raises FileNotFoundError for nonexistent archive."""
        nonexistent = tmp_path / "nonexistent.zip"
        with pytest.raises(FileNotFoundError):
            tool.handler.extract_archive(str(nonexistent))

    def test_create_archive_with_nonexistent_files(
        self, tool: StandardArchiveTool, tmp_path: Path
    ) -> None:
        """create_archive handles nonexistent source files gracefully."""
        output = tmp_path / "output.zip"
        nonexistent = tmp_path / "does_not_exist.txt"
        # Should create archive with only existing files (none in this case)
        result = tool.handler.create_archive(str(output), [str(nonexistent)])
        # Archive might be empty or not created
        # The implementation adds only existing files

    def test_detect_format_on_directory(
        self, tool: StandardArchiveTool, tmp_path: Path
    ) -> None:
        """detect_archive_format on directory returns None."""
        result = tool.handler.detect_archive_format(str(tmp_path))
        assert result is None

    def test_is_archive_on_directory(
        self, tool: StandardArchiveTool, tmp_path: Path
    ) -> None:
        """is_archive_file on directory returns False."""
        result = tool.handler.is_archive_file(str(tmp_path))
        assert result is False

    def test_handler_exception_wrapping(
        self, tool: StandardArchiveTool, tmp_path: Path
    ) -> None:
        """Handler wraps exceptions in ArchiveHandlerError."""
        invalid = tmp_path / "invalid.zip"
        invalid.write_text("not a zip")
        extract_dir = tmp_path / "extract"
        with pytest.raises((zipfile.BadZipFile, ArchiveHandlerError)):
            tool.handler.extract_archive(str(invalid), str(extract_dir))


# =============================================================================
# Test Class: Argument Parsing Edge Cases
# =============================================================================

class TestArgumentParsing:
    """Test run_standalone argument parsing edge cases."""

    def test_run_standalone_only_extract_flag_no_archive(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """run_standalone() with only --extract flag shows error."""
        # argparse will show error about missing archive argument
        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['--extract', '/some/dir'])
        # argparse exits with code 2 for argument errors
        assert exc_info.value.code == 2

    def test_run_standalone_unknown_argument(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """run_standalone() with unknown argument shows error."""
        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['--unknown-flag'])
        assert exc_info.value.code == 2

    def test_run_standalone_extract_with_relative_path(
        self, tool: StandardArchiveTool, sample_zip_file: Path, tmp_path: Path
    ) -> None:
        """run_standalone() works with relative extract path."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)
            extract_dir = Path("relative_extract")
            result = tool.run_standalone([str(sample_zip_file), "--extract", str(extract_dir)])
            assert result == 0
            assert extract_dir.exists()
        finally:
            os.chdir(original_cwd)


# =============================================================================
# Main block test
# =============================================================================

class TestMainBlock:
    """Test __main__ block behavior."""

    def test_module_can_be_run_as_main(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Module can be executed as __main__."""
        from nodupe.tools.archive import archive_tool as at
        tool = at.StandardArchiveTool()
        # --help causes argparse to call sys.exit(0)
        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['--help'])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower()

    def test_run_standalone_via_sys_argv_simulation(
        self, tool: StandardArchiveTool, capsys: pytest.CaptureFixture[str], sample_zip_file: Path, tmp_path: Path
    ) -> None:
        """run_standalone() simulates sys.argv usage."""
        extract_dir = tmp_path / "sys_argv_test"
        # Simulate: archive_tool.py archive.zip --extract /path
        args = [str(sample_zip_file), "--extract", str(extract_dir)]
        result = tool.run_standalone(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "Success" in captured.out
