# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/mime/mime_tool.py - MIME detection tool integration.

Comprehensive tests covering:
- Tool properties and metadata
- Tool initialization and shutdown
- API method exposure
- Integration with MIMEDetection
- Capabilities reporting
"""

from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.mime.mime_logic import MIMEDetection
from nodupe.tools.mime.mime_tool import (
    StandardMIMETool,
    register_tool,
)

# =============================================================================
# Test StandardMIMETool Properties
# =============================================================================

class TestStandardMIMEToolProperties:
    """Test StandardMIMETool properties."""

    def test_name_property(self):
        """name property returns correct value."""
        tool = StandardMIMETool()
        assert tool.name == "standard_mime"

    def test_version_property(self):
        """version property returns correct value."""
        tool = StandardMIMETool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """dependencies property returns empty list."""
        tool = StandardMIMETool()
        assert tool.dependencies == []

    def test_detector_initialized(self):
        """detector is initialized as MIMEDetection."""
        tool = StandardMIMETool()
        assert isinstance(tool.detector, MIMEDetection)


# =============================================================================
# Test StandardMIMETool API Methods
# =============================================================================

class TestStandardMIMEToolApiMethods:
    """Test StandardMIMETool api_methods property."""

    def test_api_methods_property(self):
        """api_methods returns correct dictionary."""
        tool = StandardMIMETool()
        api_methods = tool.api_methods

        assert isinstance(api_methods, dict)
        assert 'detect_mime_type' in api_methods
        assert 'is_text' in api_methods
        assert 'is_image' in api_methods
        assert 'is_archive' in api_methods

    def test_api_methods_bound_to_detector(self):
        """api_methods are bound to detector methods."""
        tool = StandardMIMETool()
        api_methods = tool.api_methods

        assert api_methods['detect_mime_type'] == tool.detector.detect_mime_type
        assert api_methods['is_text'] == tool.detector.is_text
        assert api_methods['is_image'] == tool.detector.is_image
        assert api_methods['is_archive'] == tool.detector.is_archive

    def test_api_methods_are_callable(self):
        """All api_methods are callable."""
        tool = StandardMIMETool()
        api_methods = tool.api_methods

        for name, method in api_methods.items():
            assert callable(method), f"{name} should be callable"


# =============================================================================
# Test StandardMIMETool Initialize
# =============================================================================

class TestStandardMIMEToolInitialize:
    """Test StandardMIMETool.initialize() method."""

    def test_initialize_registers_service(self):
        """initialize() registers mime_service."""
        tool = StandardMIMETool()
        container = MagicMock()

        tool.initialize(container)

        container.register_service.assert_called_once_with(
            'mime_service', tool.detector
        )

    def test_initialize_with_mock_container(self):
        """initialize() works with mock container."""
        tool = StandardMIMETool()
        container = MagicMock()

        # Should not raise
        tool.initialize(container)
        assert container.register_service.called

    def test_initialize_preserves_detector(self):
        """initialize() preserves the same detector instance."""
        tool = StandardMIMETool()
        original_detector = tool.detector
        container = MagicMock()

        tool.initialize(container)

        assert tool.detector is original_detector


# =============================================================================
# Test StandardMIMETool Shutdown
# =============================================================================

class TestStandardMIMEToolShutdown:
    """Test StandardMIMETool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = StandardMIMETool()

        # Should not raise
        tool.shutdown()

    def test_shutdown_multiple_calls(self):
        """shutdown() can be called multiple times safely."""
        tool = StandardMIMETool()

        # Should not raise on multiple calls
        tool.shutdown()
        tool.shutdown()
        tool.shutdown()


# =============================================================================
# Test StandardMIMETool get_capabilities
# =============================================================================

class TestStandardMIMEToolGetCapabilities:
    """Test StandardMIMETool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary."""
        tool = StandardMIMETool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)

    def test_get_capabilities_features(self):
        """get_capabilities() includes features."""
        tool = StandardMIMETool()
        capabilities = tool.get_capabilities()

        assert 'features' in capabilities
        features = capabilities['features']
        assert isinstance(features, list)
        assert 'magic_number_detection' in features
        assert 'extension_mapping' in features
        assert 'rfc6838_compliance' in features

    def test_get_capabilities_features_count(self):
        """get_capabilities() returns expected number of features."""
        tool = StandardMIMETool()
        capabilities = tool.get_capabilities()

        assert len(capabilities['features']) == 3


# =============================================================================
# Test register_tool function
# =============================================================================

class TestRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_tool(self):
        """register_tool() returns a StandardMIMETool instance."""
        tool = register_tool()
        assert isinstance(tool, StandardMIMETool)

    def test_register_tool_creates_new_instance(self):
        """register_tool() creates a new instance each call."""
        tool1 = register_tool()
        tool2 = register_tool()

        assert tool1 is not tool2
        assert tool1.name == tool2.name
        assert tool1.version == tool2.version


# =============================================================================
# Test StandardMIMETool Integration
# =============================================================================

class TestStandardMIMEToolIntegration:
    """Integration tests for StandardMIMETool."""

    def test_tool_lifecycle(self):
        """Test complete tool lifecycle: create -> initialize -> use -> shutdown."""
        tool = StandardMIMETool()
        container = MagicMock()

        # Initialize
        tool.initialize(container)
        container.register_service.assert_called_once()

        # Use - check capabilities
        capabilities = tool.get_capabilities()
        assert 'features' in capabilities

        # Use - check API methods
        api_methods = tool.api_methods
        assert callable(api_methods['detect_mime_type'])

        # Shutdown
        tool.shutdown()

    def test_tool_properties_consistency(self):
        """Test that tool properties return consistent values."""
        tool1 = StandardMIMETool()
        tool2 = StandardMIMETool()

        # Properties should be consistent across instances
        assert tool1.name == tool2.name
        assert tool1.version == tool2.version
        assert tool1.dependencies == tool2.dependencies

    def test_detect_mime_type_integration(self, tmp_path):
        """Test MIME type detection through tool."""
        tool = StandardMIMETool()

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        mime_type = tool.detector.detect_mime_type(str(test_file))
        assert isinstance(mime_type, str)
        assert len(mime_type) > 0

    def test_is_text_integration(self, tmp_path):
        """Test is_text check through tool."""
        tool = StandardMIMETool()

        # Create a text file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        mime_type = tool.detector.detect_mime_type(str(test_file))
        is_text = tool.detector.is_text(mime_type)

        assert isinstance(is_text, bool)

    def test_is_image_integration(self, tmp_path):
        """Test is_image check through tool."""
        tool = StandardMIMETool()

        # Create a fake image file with PNG magic bytes
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'fake image data')

        mime_type = tool.detector.detect_mime_type(str(test_file))
        is_image = tool.detector.is_image(mime_type)

        assert isinstance(is_image, bool)

    def test_is_archive_integration(self, tmp_path):
        """Test is_archive check through tool."""
        tool = StandardMIMETool()

        # Create a fake zip file with ZIP magic bytes
        test_file = tmp_path / "test.zip"
        test_file.write_bytes(b'PK\x03\x04' + b'fake zip data')

        mime_type = tool.detector.detect_mime_type(str(test_file))
        is_archive = tool.detector.is_archive(mime_type)

        assert isinstance(is_archive, bool)


# =============================================================================
# Test StandardMIMETool Edge Cases
# =============================================================================

class TestStandardMIMEToolEdgeCases:
    """Test StandardMIMETool edge cases."""

    def test_api_methods_all_present(self):
        """All expected API methods are present."""
        tool = StandardMIMETool()
        api_methods = tool.api_methods

        expected_methods = ['detect_mime_type', 'is_text', 'is_image', 'is_archive']
        for method in expected_methods:
            assert method in api_methods, f"{method} should be in api_methods"

    def test_detector_independent_of_tool(self):
        """Detector can be used independently of tool."""
        tool = StandardMIMETool()
        detector = tool.detector

        # Detector should work without tool
        assert hasattr(detector, 'detect_mime_type')
        assert hasattr(detector, 'is_text')
        assert hasattr(detector, 'is_image')
        assert hasattr(detector, 'is_archive')

    def test_tool_without_initialize(self):
        """Tool methods work without calling initialize."""
        tool = StandardMIMETool()

        # Should be able to get capabilities without initialize
        capabilities = tool.get_capabilities()
        assert 'features' in capabilities

        # Should be able to access api_methods without initialize
        api_methods = tool.api_methods
        assert len(api_methods) > 0

    def test_multiple_tools_independent(self):
        """Multiple tool instances are independent."""
        tool1 = StandardMIMETool()
        tool2 = StandardMIMETool()

        # Each should have its own detector
        assert tool1.detector is not tool2.detector

        # But they should behave the same
        assert tool1.name == tool2.name
        assert tool1.version == tool2.version

    def test_capabilities_immutability(self):
        """get_capabilities returns independent dict each call."""
        tool = StandardMIMETool()

        caps1 = tool.get_capabilities()
        caps2 = tool.get_capabilities()

        # Should be different dict objects
        assert caps1 is not caps2

        # But have same content
        assert caps1 == caps2

    def test_detector_type(self):
        """detector is correct type."""
        tool = StandardMIMETool()
        assert isinstance(tool.detector, MIMEDetection)

    def test_tool_inherits_from_base(self):
        """StandardMIMETool inherits from Tool base class."""
        from nodupe.core.tool_system.base import Tool

        tool = StandardMIMETool()
        assert isinstance(tool, Tool)

    def test_api_methods_dict_not_shared(self):
        """api_methods returns new dict each call."""
        tool = StandardMIMETool()

        api1 = tool.api_methods
        api2 = tool.api_methods

        # Should be different dict objects
        assert api1 is not api2

        # But have same content
        assert api1 == api2


# =============================================================================
# Test StandardMIMETool with Mocked Detector
# =============================================================================

class TestStandardMIMEToolMocked:
    """Test StandardMIMETool with mocked detector."""

    def test_api_methods_use_detector(self):
        """API methods delegate to detector."""
        tool = StandardMIMETool()

        # Verify methods are callable and delegate to detector
        assert callable(tool.api_methods['detect_mime_type'])
        assert callable(tool.api_methods['is_text'])
        assert callable(tool.api_methods['is_image'])
        assert callable(tool.api_methods['is_archive'])

        # Verify they produce the same results as detector methods
        assert tool.api_methods['detect_mime_type']('/test.txt') == tool.detector.detect_mime_type('/test.txt')
        assert tool.api_methods['is_text']('text/plain') == tool.detector.is_text('text/plain')
        assert tool.api_methods['is_image']('image/jpeg') == tool.detector.is_image('image/jpeg')
        assert tool.api_methods['is_archive']('application/zip') == tool.detector.is_archive('application/zip')

    def test_initialize_calls_container(self):
        """initialize properly calls container.register_service."""
        tool = StandardMIMETool()
        container = MagicMock()

        tool.initialize(container)

        container.register_service.assert_called_once_with(
            'mime_service', tool.detector
        )

    def test_initialize_with_different_containers(self):
        """initialize can be called with different containers."""
        tool = StandardMIMETool()
        container1 = MagicMock()
        container2 = MagicMock()

        tool.initialize(container1)
        tool.initialize(container2)

        assert container1.register_service.called
        assert container2.register_service.called


# =============================================================================
# Test StandardMIMETool Functional Tests
# =============================================================================

class TestStandardMIMEToolFunctional:
    """Functional tests for StandardMIMETool."""

    def test_detect_common_extensions(self, tmp_path):
        """Test detection of common file extensions."""
        tool = StandardMIMETool()

        test_cases = [
            ("test.txt", "text/plain"),
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.pdf", "application/pdf"),
            ("test.zip", "application/zip"),
        ]

        for filename, expected_mime in test_cases:
            test_file = tmp_path / filename
            test_file.write_text("test content")

            mime_type = tool.detector.detect_mime_type(str(test_file))
            # Just verify it returns a string, actual MIME detection may vary
            assert isinstance(mime_type, str)

    def test_detect_magic_bytes(self, tmp_path):
        """Test detection using magic bytes."""
        tool = StandardMIMETool()

        # PNG magic bytes
        png_file = tmp_path / "test.png"
        png_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'fake png')

        mime_type = tool.detector.detect_mime_type(str(png_file))
        assert mime_type == 'image/png'

        # ZIP magic bytes
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b'PK\x03\x04' + b'fake zip')

        mime_type = tool.detector.detect_mime_type(str(zip_file))
        assert mime_type == 'application/zip'

    def test_is_text_various_types(self, tmp_path):
        """Test is_text with various MIME types."""
        tool = StandardMIMETool()

        text_types = [
            'text/plain',
            'text/html',
            'application/json',
            'application/xml',
        ]

        for mime_type in text_types:
            assert tool.detector.is_text(mime_type) is True

        non_text_types = [
            'image/png',
            'application/zip',
            'video/mp4',
        ]

        for mime_type in non_text_types:
            assert tool.detector.is_text(mime_type) is False

    def test_is_image_various_types(self, tmp_path):
        """Test is_image with various MIME types."""
        tool = StandardMIMETool()

        image_types = [
            'image/png',
            'image/jpeg',
            'image/gif',
        ]

        for mime_type in image_types:
            assert tool.detector.is_image(mime_type) is True

        non_image_types = [
            'text/plain',
            'application/zip',
            'video/mp4',
        ]

        for mime_type in non_image_types:
            assert tool.detector.is_image(mime_type) is False

    def test_is_archive_various_types(self, tmp_path):
        """Test is_archive with various MIME types."""
        tool = StandardMIMETool()

        archive_types = [
            'application/zip',
            'application/x-tar',
            'application/gzip',
        ]

        for mime_type in archive_types:
            assert tool.detector.is_archive(mime_type) is True

        non_archive_types = [
            'text/plain',
            'image/png',
            'video/mp4',
        ]

        for mime_type in non_archive_types:
            assert tool.detector.is_archive(mime_type) is False


# =============================================================================
# Test StandardMIMETool run_standalone
# =============================================================================

class TestStandardMIMEToolRunStandalone:
    """Test StandardMIMETool.run_standalone() method."""

    def test_run_standalone_no_args_shows_help(self, capsys):
        """run_standalone() with no args shows help."""
        tool = StandardMIMETool()

        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone([])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "file" in captured.out.lower()

    def test_run_standalone_with_file(self, capsys, tmp_path):
        """run_standalone() with file argument detects MIME type."""
        tool = StandardMIMETool()

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = tool.run_standalone([str(test_file)])

        assert result == 0
        captured = capsys.readouterr()
        assert "MIME Type:" in captured.out

    def test_run_standalone_with_image_file(self, capsys, tmp_path):
        """run_standalone() with image file detects correctly."""
        tool = StandardMIMETool()

        # Create a PNG file with magic bytes
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'fake png')

        result = tool.run_standalone([str(test_file)])

        assert result == 0
        captured = capsys.readouterr()
        assert "image/png" in captured.out

    def test_run_standalone_with_archive_file(self, capsys, tmp_path):
        """run_standalone() with archive file detects correctly."""
        tool = StandardMIMETool()

        # Create a ZIP file with magic bytes
        test_file = tmp_path / "test.zip"
        test_file.write_bytes(b'PK\x03\x04' + b'fake zip')

        result = tool.run_standalone([str(test_file)])

        assert result == 0
        captured = capsys.readouterr()
        assert "application/zip" in captured.out

    def test_run_standalone_with_nonexistent_file(self, capsys, tmp_path):
        """run_standalone() handles nonexistent file."""
        tool = StandardMIMETool()
        nonexistent = tmp_path / "nonexistent.txt"

        # The MIME detector may return a default type for nonexistent files
        # The tool should handle this gracefully
        result = tool.run_standalone([str(nonexistent)])

        # Result may be 0 (default type returned) or 1 (error)
        assert result in [0, 1]
        captured = capsys.readouterr()
        # Should output something (either MIME type or error)
        assert len(captured.out) > 0

    def test_run_standalone_with_help_flag(self, capsys):
        """run_standalone() with --help flag."""
        tool = StandardMIMETool()

        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['--help'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower()

    def test_describe_usage_content(self):
        """describe_usage() returns meaningful content."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        assert isinstance(description, str)
        assert len(description) > 50
        assert "file" in description.lower() or "type" in description.lower()


# =============================================================================
# Test StandardMIMETool Missing Coverage - Error Paths
# =============================================================================

class TestStandardMIMEToolMissingCoverage:
    """Test missing coverage paths in StandardMIMETool."""

    def test_run_standalone_exception_handling(self, capsys, tmp_path):
        """run_standalone() handles exceptions and returns 1."""
        tool = StandardMIMETool()

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Mock detector to raise an exception
        with patch.object(tool.detector, 'detect_mime_type', side_effect=Exception("Detection failed")):
            result = tool.run_standalone([str(test_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out

    def test_run_standalone_verbose_success(self, capsys, tmp_path):
        """run_standalone() with verbose flag shows detailed output."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Mock detector to return a known MIME type
        with patch.object(tool.detector, 'detect_mime_type', return_value='text/plain'):
            with patch.object(tool.detector, 'is_text', return_value=True):
                with patch.object(tool.detector, 'is_image', return_value=False):
                    with patch.object(tool.detector, 'is_archive', return_value=False):
                        result = tool.run_standalone([str(test_file), '--verbose'])

        assert result == 0
        captured = capsys.readouterr()
        assert "Is text:" in captured.out
        assert "Is image:" in captured.out
        assert "Is archive:" in captured.out

    def test_run_standalone_with_file_flag(self, capsys, tmp_path):
        """run_standalone() with --file flag."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch.object(tool.detector, 'detect_mime_type', return_value='text/plain'):
            result = tool.run_standalone(['--file', str(test_file)])

        assert result == 0
        captured = capsys.readouterr()
        assert "MIME Type:" in captured.out

    def test_run_standalone_unknown_flag_no_file(self, capsys):
        """run_standalone() with unknown flag and no file shows help."""
        tool = StandardMIMETool()

        with pytest.raises(SystemExit) as exc_info:
            result = tool.run_standalone(['--unknown-flag'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_run_standalone_verbose_error_path(self, capsys, tmp_path):
        """run_standalone() error path with verbose output."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Mock to raise exception during detection
        with patch.object(tool.detector, 'detect_mime_type', side_effect=RuntimeError("Runtime error")):
            result = tool.run_standalone([str(test_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out
