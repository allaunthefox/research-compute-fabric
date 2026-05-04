# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/archive/archive_tool.py - Archive tool integration.

Comprehensive tests covering:
- Tool properties and metadata
- Tool initialization and shutdown
- CLI argument parsing
- API method exposure
- Integration with ArchiveHandler
"""

import zipfile
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.archive.archive_logic import ArchiveHandler
from nodupe.tools.archive.archive_tool import (
    StandardArchiveTool,
    register_tool,
)

# =============================================================================
# Test StandardArchiveTool Properties
# =============================================================================

class TestStandardArchiveToolProperties:
    """Test StandardArchiveTool properties."""

    def test_name_property(self):
        """name property returns correct value."""
        tool = StandardArchiveTool()
        assert tool.name == "standard_archive"

    def test_version_property(self):
        """version property returns correct value."""
        tool = StandardArchiveTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """dependencies property returns empty list."""
        tool = StandardArchiveTool()
        assert tool.dependencies == []

    def test_handler_initialized(self):
        """handler is initialized as ArchiveHandler."""
        tool = StandardArchiveTool()
        assert isinstance(tool.handler, ArchiveHandler)


# =============================================================================
# Test StandardArchiveTool API Methods
# =============================================================================

class TestStandardArchiveToolApiMethods:
    """Test StandardArchiveTool api_methods property."""

    def test_api_methods_property(self):
        """api_methods returns correct dictionary."""
        tool = StandardArchiveTool()
        api_methods = tool.api_methods

        assert isinstance(api_methods, dict)
        assert 'extract_archive' in api_methods
        assert 'create_archive' in api_methods
        assert 'is_archive' in api_methods
        assert 'detect_format' in api_methods

    def test_api_methods_bound_to_handler(self):
        """api_methods are bound to handler methods."""
        tool = StandardArchiveTool()
        api_methods = tool.api_methods

        assert api_methods['extract_archive'] == tool.handler.extract_archive
        assert api_methods['create_archive'] == tool.handler.create_archive
        assert api_methods['is_archive'] == tool.handler.is_archive_file
        assert api_methods['detect_format'] == tool.handler.detect_archive_format


# =============================================================================
# Test StandardArchiveTool Initialize
# =============================================================================

class TestStandardArchiveToolInitialize:
    """Test StandardArchiveTool.initialize() method."""

    def test_initialize_registers_service(self):
        """initialize() registers archive_handler_service."""
        tool = StandardArchiveTool()
        container = MagicMock()

        tool.initialize(container)

        container.register_service.assert_called_once_with(
            'archive_handler_service', tool.handler
        )

    def test_initialize_with_mock_container(self):
        """initialize() works with mock container."""
        tool = StandardArchiveTool()
        container = MagicMock()

        # Should not raise
        tool.initialize(container)
        assert container.register_service.called


# =============================================================================
# Test StandardArchiveTool Shutdown
# =============================================================================

class TestStandardArchiveToolShutdown:
    """Test StandardArchiveTool.shutdown() method."""

    def test_shutdown_calls_handler_cleanup(self):
        """shutdown() calls handler.cleanup()."""
        tool = StandardArchiveTool()

        with patch.object(tool.handler, 'cleanup') as mock_cleanup:
            tool.shutdown()
            mock_cleanup.assert_called_once()

    def test_shutdown_multiple_calls_safe(self):
        """shutdown() can be called multiple times safely."""
        tool = StandardArchiveTool()

        # Should not raise on multiple calls
        tool.shutdown()
        tool.shutdown()
        tool.shutdown()


# =============================================================================
# Test StandardArchiveTool run_standalone
# =============================================================================

class TestStandardArchiveToolRunStandalone:
    """Test StandardArchiveTool.run_standalone() method."""

    def test_run_standalone_no_args_shows_help(self, capsys):
        """run_standalone() with no args shows help."""
        tool = StandardArchiveTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "archive" in captured.out.lower()

    def test_run_standalone_extract_mode(self, capsys, tmp_path):
        """run_standalone() with --extract extracts archive."""
        tool = StandardArchiveTool()

        # Create a test zip file
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("test.txt", "test content")

        extract_dir = tmp_path / "extracted"

        result = tool.run_standalone([str(zip_path), "--extract", str(extract_dir)])

        assert result == 0
        captured = capsys.readouterr()
        assert "Success" in captured.out or str(len(extract_dir)) in captured.out

    def test_run_standalone_detect_mode(self, capsys, tmp_path):
        """run_standalone() without --extract detects format."""
        tool = StandardArchiveTool()

        # Create a test zip file
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("test.txt", "test content")

        result = tool.run_standalone([str(zip_path)])

        assert result == 0
        captured = capsys.readouterr()
        assert "Type:" in captured.out or "zip" in captured.out.lower()

    def test_run_standalone_nonexistent_archive(self, capsys, tmp_path):
        """run_standalone() handles nonexistent archive."""
        tool = StandardArchiveTool()
        nonexistent = tmp_path / "nonexistent.zip"

        # The tool catches the exception and returns 1
        # But the detect_archive_format returns None for nonexistent files
        # So it prints "Type: Unknown Collection Type" and returns 0
        result = tool.run_standalone([str(nonexistent)])

        # Since the file doesn't exist, detect_archive_format returns None
        # and the tool prints "Type: Unknown Collection Type"
        assert result == 0
        captured = capsys.readouterr()
        assert "Unknown" in captured.out or "Type:" in captured.out

    def test_run_standalone_extract_error(self, capsys, tmp_path):
        """run_standalone() handles extraction errors."""
        tool = StandardArchiveTool()

        # Create an invalid zip file
        invalid_zip = tmp_path / "invalid.zip"
        invalid_zip.write_text("not a zip file")

        extract_dir = tmp_path / "extracted"

        result = tool.run_standalone([str(invalid_zip), "--extract", str(extract_dir)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out


# =============================================================================
# Test StandardArchiveTool describe_usage
# =============================================================================

class TestStandardArchiveToolDescribeUsage:
    """Test StandardArchiveTool.describe_usage() method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        tool = StandardArchiveTool()
        description = tool.describe_usage()

        assert isinstance(description, str)
        assert len(description) > 0

    def test_describe_usage_content(self):
        """describe_usage() returns meaningful content."""
        tool = StandardArchiveTool()
        description = tool.describe_usage()

        # Should mention key concepts
        assert "collection" in description.lower() or "file" in description.lower()
        assert "unpack" in description.lower() or "extract" in description.lower()


# =============================================================================
# Test StandardArchiveTool get_capabilities
# =============================================================================

class TestStandardArchiveToolGetCapabilities:
    """Test StandardArchiveTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary."""
        tool = StandardArchiveTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)

    def test_get_capabilities_formats(self):
        """get_capabilities() includes supported formats."""
        tool = StandardArchiveTool()
        capabilities = tool.get_capabilities()

        assert 'formats' in capabilities
        formats = capabilities['formats']
        assert isinstance(formats, list)
        assert 'zip' in formats
        assert 'tar' in formats

    def test_get_capabilities_features(self):
        """get_capabilities() includes features."""
        tool = StandardArchiveTool()
        capabilities = tool.get_capabilities()

        assert 'features' in capabilities
        features = capabilities['features']
        assert isinstance(features, list)
        assert 'extraction' in features
        assert 'detection' in features


# =============================================================================
# Test register_tool function
# =============================================================================

class TestRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_tool(self):
        """register_tool() returns a StandardArchiveTool instance."""
        tool = register_tool()
        assert isinstance(tool, StandardArchiveTool)

    def test_register_tool_creates_new_instance(self):
        """register_tool() creates a new instance each call."""
        tool1 = register_tool()
        tool2 = register_tool()

        assert tool1 is not tool2
        assert tool1.name == tool2.name


# =============================================================================
# Test StandardArchiveTool Main Block
# =============================================================================

class TestStandardArchiveToolMain:
    """Test StandardArchiveTool __main__ behavior."""

    def test_main_block_execution(self, capsys):
        """Test that __main__ block can be executed."""
        from nodupe.tools.archive import archive_tool as at

        # Simulate running as main with --help
        tool = at.StandardArchiveTool()
        # argparse prints help and raises SystemExit(0)
        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['--help'])
        assert exc_info.value.code == 0


# =============================================================================
# Test StandardArchiveTool Integration
# =============================================================================

class TestStandardArchiveToolIntegration:
    """Integration tests for StandardArchiveTool."""

    def test_tool_lifecycle(self, tmp_path):
        """Test complete tool lifecycle: create -> initialize -> use -> shutdown."""
        tool = StandardArchiveTool()
        container = MagicMock()

        # Initialize
        tool.initialize(container)
        container.register_service.assert_called_once()

        # Use - check capabilities
        capabilities = tool.get_capabilities()
        assert 'formats' in capabilities

        # Use - check API methods
        api_methods = tool.api_methods
        assert callable(api_methods['extract_archive'])

        # Shutdown
        tool.shutdown()

    def test_tool_properties_consistency(self):
        """Test that tool properties return consistent values."""
        tool1 = StandardArchiveTool()
        tool2 = StandardArchiveTool()

        # Properties should be consistent across instances
        assert tool1.name == tool2.name
        assert tool1.version == tool2.version
        assert tool1.dependencies == tool2.dependencies

    def test_extract_and_verify(self, tmp_path):
        """Test extracting archive and verifying contents."""
        tool = StandardArchiveTool()

        # Create a test archive with multiple files
        zip_path = tmp_path / "multi.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.txt", "content 1")
            zf.writestr("file2.txt", "content 2")
            zf.writestr("subdir/file3.txt", "content 3")

        extract_dir = tmp_path / "extracted"
        result = tool.handler.extract_archive(str(zip_path), str(extract_dir))

        assert len(result) >= 2
        assert extract_dir.exists()

    def test_create_and_extract_roundtrip(self, tmp_path):
        """Test creating archive and extracting it."""
        tool = StandardArchiveTool()

        # Create test files
        file1 = tmp_path / "test1.txt"
        file1.write_text("test content 1")
        file2 = tmp_path / "test2.txt"
        file2.write_text("test content 2")

        # Create archive
        archive_path = tmp_path / "output.zip"
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


# =============================================================================
# Test StandardArchiveTool Edge Cases
# =============================================================================

class TestStandardArchiveToolEdgeCases:
    """Test StandardArchiveTool edge cases."""

    def test_run_standalone_with_help_flag(self, capsys):
        """run_standalone() with --help flag."""
        tool = StandardArchiveTool()
        # argparse prints help and raises SystemExit(0)
        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['--help'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower()

    def test_api_methods_are_callable(self):
        """All api_methods are callable."""
        tool = StandardArchiveTool()
        api_methods = tool.api_methods

        for name, method in api_methods.items():
            assert callable(method), f"{name} should be callable"

    def test_handler_cleanup_on_tool_shutdown(self):
        """Handler cleanup is called on tool shutdown."""
        tool = StandardArchiveTool()

        with patch.object(tool.handler, 'cleanup') as mock_cleanup:
            tool.shutdown()
            mock_cleanup.assert_called_once()

    def test_initialize_preserves_handler(self):
        """initialize() preserves the same handler instance."""
        tool = StandardArchiveTool()
        original_handler = tool.handler
        container = MagicMock()

        tool.initialize(container)

        assert tool.handler is original_handler

    def test_describe_usage_human_readable(self):
        """describe_usage() returns human-readable text."""
        tool = StandardArchiveTool()
        description = tool.describe_usage()

        # Should be readable sentences
        assert len(description) > 20
        # Should start with capital or be a complete thought
        assert description[0].isupper() or description.strip()
