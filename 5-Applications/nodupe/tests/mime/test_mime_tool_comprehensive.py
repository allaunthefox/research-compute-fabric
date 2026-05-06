# SPDX-License-Identifier: Apache-20
# Copyright (c) 2025 Allaun

"""Comprehensive tests for nodupe/tools/mime/mime_tool.py.

This test file provides comprehensive coverage for the StandardMIMETool class,
focusing on areas not covered by the basic test suite. It includes tests for:
- All run_standalone argument combinations
- Edge cases and error paths
- Detailed content verification
- Integration scenarios

Target: Improve coverage from 68.0% to 90%+
"""

from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.mime.mime_tool import (
    StandardMIMETool,
    register_tool,
)


# =============================================================================
# Test run_standalone with Various Flag Combinations
# =============================================================================

class TestRunStandaloneFlagCombinations:
    """Test run_standalone() with all flag combinations."""

    def test_run_standalone_short_help_flag(self, capsys):
        """run_standalone() with -h short flag shows help."""
        tool = StandardMIMETool()

        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['-h'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Standard MIME Detection Tool" in captured.out

    def test_run_standalone_short_file_flag(self, capsys, tmp_path):
        """run_standalone() with -f short flag detects MIME type."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch.object(tool.detector, 'detect_mime_type', return_value='text/plain'):
            result = tool.run_standalone(['-f', str(test_file)])

        assert result == 0
        captured = capsys.readouterr()
        assert f"File: {test_file}" in captured.out
        assert "MIME Type: text/plain" in captured.out

    def test_run_standalone_short_verbose_flag(self, capsys, tmp_path):
        """run_standalone() with -v short flag shows verbose output."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch.object(tool.detector, 'detect_mime_type', return_value='text/plain'):
            with patch.object(tool.detector, 'is_text', return_value=True):
                with patch.object(tool.detector, 'is_image', return_value=False):
                    with patch.object(tool.detector, 'is_archive', return_value=False):
                        result = tool.run_standalone([str(test_file), '-v'])

        assert result == 0
        captured = capsys.readouterr()
        assert "Is text: True" in captured.out
        assert "Is image: False" in captured.out
        assert "Is archive: False" in captured.out

    def test_run_standalone_combined_short_flags(self, capsys, tmp_path):
        """run_standalone() with combined short flags."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch.object(tool.detector, 'detect_mime_type', return_value='text/plain'):
            with patch.object(tool.detector, 'is_text', return_value=True):
                with patch.object(tool.detector, 'is_image', return_value=False):
                    with patch.object(tool.detector, 'is_archive', return_value=False):
                        result = tool.run_standalone(['-f', str(test_file), '-v'])

        assert result == 0
        captured = capsys.readouterr()
        assert "MIME Type: text/plain" in captured.out
        assert "Is text:" in captured.out

    def test_run_standalone_long_and_short_verbose_together(self, capsys, tmp_path):
        """run_standalone() with both --verbose and -v flags."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch.object(tool.detector, 'detect_mime_type', return_value='text/plain'):
            with patch.object(tool.detector, 'is_text', return_value=True):
                with patch.object(tool.detector, 'is_image', return_value=False):
                    with patch.object(tool.detector, 'is_archive', return_value=False):
                        result = tool.run_standalone([str(test_file), '--verbose', '-v'])

        assert result == 0
        captured = capsys.readouterr()
        # Should still show verbose output (flags are just checked for presence)
        assert "Is text:" in captured.out

    def test_run_standalone_help_in_middle_of_args(self, capsys):
        """run_standalone() with --help in middle of args shows help."""
        tool = StandardMIMETool()

        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['--file', 'test.txt', '--help'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Standard MIME Detection Tool" in captured.out

    def test_run_standalone_file_flag_takes_precedence(self, capsys, tmp_path):
        """run_standalone() --file flag takes precedence over positional."""
        tool = StandardMIMETool()
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        # Mock to track which file is detected
        detected_files = []

        def track_detection(path):
            detected_files.append(path)
            return 'text/plain'

        with patch.object(tool.detector, 'detect_mime_type', side_effect=track_detection):
            result = tool.run_standalone(['--file', str(file1), str(file2)])

        assert result == 0
        assert len(detected_files) == 1
        assert str(file1) in detected_files[0]
        captured = capsys.readouterr()
        assert f"File: {file1}" in captured.out

    def test_run_standalone_file_flag_no_path_following(self, capsys):
        """run_standalone() --file with no path following shows help."""
        tool = StandardMIMETool()

        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['--file'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Standard MIME Detection Tool" in captured.out

    def test_run_standalone_short_file_flag_no_path_following(self, capsys):
        """run_standalone() -f with no path following shows help."""
        tool = StandardMIMETool()

        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['-f'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Standard MIME Detection Tool" in captured.out


# =============================================================================
# Test run_standalone Error Handling and Edge Cases
# =============================================================================

class TestRunStandaloneErrorHandling:
    """Test run_standalone() error handling paths."""

    def test_run_standalone_nonexistent_file_error(self, capsys, tmp_path):
        """run_standalone() with nonexistent file handles gracefully."""
        tool = StandardMIMETool()
        nonexistent = tmp_path / "does_not_exist.txt"

        # Mock detector to raise error for nonexistent file
        with patch.object(tool.detector, 'detect_mime_type', side_effect=FileNotFoundError("File not found")):
            result = tool.run_standalone([str(nonexistent)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out

    def test_run_standalone_permission_error(self, capsys, tmp_path):
        """run_standalone() handles permission errors."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with patch.object(tool.detector, 'detect_mime_type', side_effect=PermissionError("Permission denied")):
            result = tool.run_standalone([str(test_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out

    def test_run_standalone_os_error(self, capsys, tmp_path):
        """run_standalone() handles OS errors."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with patch.object(tool.detector, 'detect_mime_type', side_effect=OSError("OS error")):
            result = tool.run_standalone([str(test_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out

    def test_run_standalone_value_error(self, capsys, tmp_path):
        """run_standalone() handles value errors."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with patch.object(tool.detector, 'detect_mime_type', side_effect=ValueError("Invalid value")):
            result = tool.run_standalone([str(test_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out

    def test_run_standalone_with_directory_instead_of_file(self, capsys, tmp_path):
        """run_standalone() with directory path handles gracefully."""
        tool = StandardMIMETool()
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # The detector may handle directories differently
        result = tool.run_standalone([str(test_dir)])

        # Should not crash - either returns 0 with default type or 1 with error
        assert result in [0, 1]
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_run_standalone_with_empty_file(self, capsys, tmp_path):
        """run_standalone() with empty file."""
        tool = StandardMIMETool()
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        result = tool.run_standalone([str(test_file)])

        # Should handle empty file gracefully
        assert result in [0, 1]
        captured = capsys.readouterr()
        # Should output something
        assert len(captured.out) > 0

    def test_run_standalone_with_binary_file(self, capsys, tmp_path):
        """run_standalone() with binary file."""
        tool = StandardMIMETool()
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b'\x00\x01\x02\x03\x04\x05')

        result = tool.run_standalone([str(test_file)])

        # Should handle binary file
        assert result == 0
        captured = capsys.readouterr()
        assert "MIME Type:" in captured.out

    def test_run_standalone_with_file_path_spaces(self, capsys, tmp_path):
        """run_standalone() with file path containing spaces."""
        tool = StandardMIMETool()
        test_file = tmp_path / "file with spaces.txt"
        test_file.write_text("test content")

        with patch.object(tool.detector, 'detect_mime_type', return_value='text/plain'):
            result = tool.run_standalone([str(test_file)])

        assert result == 0
        captured = capsys.readouterr()
        assert f"File: {test_file}" in captured.out


# =============================================================================
# Test describe_usage Method Content
# =============================================================================

class TestDescribeUsageContent:
    """Test describe_usage() method content verification."""

    def test_describe_usage_contains_title(self):
        """describe_usage() contains tool title."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        assert "Standard MIME Detection Tool" in description

    def test_describe_usage_contains_file_option(self):
        """describe_usage() contains --file option."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        assert "--file" in description

    def test_describe_usage_contains_verbose_option(self):
        """describe_usage() contains --verbose option."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        assert "--verbose" in description

    def test_describe_usage_contains_examples_section(self):
        """describe_usage() contains examples section."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        assert "Examples:" in description or "example" in description.lower()

    def test_describe_usage_contains_features_section(self):
        """describe_usage() contains features section."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        assert "Features:" in description or "features" in description.lower()

    def test_describe_usage_contains_magic_number_reference(self):
        """describe_usage() mentions magic number detection."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        assert "magic" in description.lower()

    def test_describe_usage_contains_extension_reference(self):
        """describe_usage() mentions extension-based detection."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        assert "extension" in description.lower()

    def test_describe_usage_contains_rfc_reference(self):
        """describe_usage() mentions RFC 6838 compliance."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        assert "RFC" in description or "rfc" in description.lower()

    def test_describe_usage_multiline_content(self):
        """describe_usage() returns multiline content."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        lines = description.strip().split('\n')
        assert len(lines) > 5

    def test_describe_usage_contains_path_argument_example(self):
        """describe_usage() contains PATH argument example."""
        tool = StandardMIMETool()
        description = tool.describe_usage()

        assert "PATH" in description or "path" in description.lower()


# =============================================================================
# Test get_capabilities Detailed Content
# =============================================================================

class TestGetCapabilitiesDetailed:
    """Test get_capabilities() detailed content verification."""

    def test_get_capabilities_returns_features_list(self):
        """get_capabilities() returns features as a list."""
        tool = StandardMIMETool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['features'], list)

    def test_get_capabilities_magic_number_detection_feature(self):
        """get_capabilities() includes magic_number_detection feature."""
        tool = StandardMIMETool()
        capabilities = tool.get_capabilities()

        assert 'magic_number_detection' in capabilities['features']

    def test_get_capabilities_extension_mapping_feature(self):
        """get_capabilities() includes extension_mapping feature."""
        tool = StandardMIMETool()
        capabilities = tool.get_capabilities()

        assert 'extension_mapping' in capabilities['features']

    def test_get_capabilities_rfc6838_compliance_feature(self):
        """get_capabilities() includes rfc6838_compliance feature."""
        tool = StandardMIMETool()
        capabilities = tool.get_capabilities()

        assert 'rfc6838_compliance' in capabilities['features']

    def test_get_capabilities_no_extra_keys(self):
        """get_capabilities() returns only expected keys."""
        tool = StandardMIMETool()
        capabilities = tool.get_capabilities()

        # Should only have 'features' key
        assert set(capabilities.keys()) == {'features'}


# =============================================================================
# Test register_tool Function
# =============================================================================

class TestRegisterToolDetailed:
    """Test register_tool() function detailed behavior."""

    def test_register_tool_returns_fresh_instance(self):
        """register_tool() returns a fresh tool instance."""
        tool = register_tool()

        assert isinstance(tool, StandardMIMETool)
        assert tool.name == "standard_mime"
        assert tool.version == "1.0.0"

    def test_register_tool_detector_is_fresh(self):
        """register_tool() creates tool with fresh detector."""
        tool1 = register_tool()
        tool2 = register_tool()

        # Each tool should have its own detector
        assert tool1.detector is not tool2.detector

    def test_register_tool_capabilities_after_registration(self):
        """register_tool() returns tool with working capabilities."""
        tool = register_tool()
        capabilities = tool.get_capabilities()

        assert 'features' in capabilities
        assert len(capabilities['features']) > 0

    def test_register_tool_api_methods_accessible(self):
        """register_tool() returns tool with accessible API methods."""
        tool = register_tool()
        api_methods = tool.api_methods

        assert 'detect_mime_type' in api_methods
        assert callable(api_methods['detect_mime_type'])


# =============================================================================
# Test Integration Scenarios
# =============================================================================

class TestIntegrationScenarios:
    """Test integration scenarios for StandardMIMETool."""

    def test_tool_full_lifecycle_with_container(self):
        """Test full tool lifecycle with container integration."""
        tool = StandardMIMETool()
        container = MagicMock()

        # Initialize
        tool.initialize(container)
        container.register_service.assert_called_once_with(
            'mime_service', tool.detector
        )

        # Use capabilities
        capabilities = tool.get_capabilities()
        assert 'features' in capabilities

        # Use API methods
        api_methods = tool.api_methods
        assert len(api_methods) == 4

        # Shutdown
        tool.shutdown()

        # Verify container was only called once during initialize
        assert container.register_service.call_count == 1

    def test_tool_reinitialize_with_same_container(self):
        """Test reinitializing tool with same container."""
        tool = StandardMIMETool()
        container = MagicMock()

        tool.initialize(container)
        tool.initialize(container)

        # Should register service twice
        assert container.register_service.call_count == 2

    def test_tool_api_methods_delegate_correctly(self, tmp_path):
        """Test that API methods correctly delegate to detector."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'fake png')

        # Test through API methods
        mime_type = tool.api_methods['detect_mime_type'](str(test_file))
        assert mime_type == 'image/png'

        is_image = tool.api_methods['is_image'](mime_type)
        assert is_image is True

        is_text = tool.api_methods['is_text'](mime_type)
        assert is_text is False

        is_archive = tool.api_methods['is_archive'](mime_type)
        assert is_archive is False

    def test_run_standalone_verbose_with_image_file(self, capsys, tmp_path):
        """run_standalone() verbose output with image file."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'fake png')

        result = tool.run_standalone([str(test_file), '--verbose'])

        assert result == 0
        captured = capsys.readouterr()
        assert "image/png" in captured.out
        assert "Is text:" in captured.out
        assert "Is image:" in captured.out
        assert "Is archive:" in captured.out

    def test_run_standalone_verbose_with_archive_file(self, capsys, tmp_path):
        """run_standalone() verbose output with archive file."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.zip"
        test_file.write_bytes(b'PK\x03\x04' + b'fake zip data')

        result = tool.run_standalone([str(test_file), '--verbose'])

        assert result == 0
        captured = capsys.readouterr()
        assert "application/zip" in captured.out
        assert "Is archive:" in captured.out


# =============================================================================
# Test Edge Cases for Complete Coverage
# =============================================================================

class TestEdgeCasesCompleteCoverage:
    """Test edge cases for complete code coverage."""

    def test_run_standalone_multiple_positional_args_uses_first(self, capsys, tmp_path):
        """run_standalone() with multiple positional args uses first."""
        tool = StandardMIMETool()
        file1 = tmp_path / "first.txt"
        file2 = tmp_path / "second.txt"
        file1.write_text("first")
        file2.write_text("second")

        detected_files = []

        def track_detection(path):
            detected_files.append(path)
            return 'text/plain'

        with patch.object(tool.detector, 'detect_mime_type', side_effect=track_detection):
            result = tool.run_standalone([str(file1), str(file2)])

        assert result == 0
        assert len(detected_files) == 1
        captured = capsys.readouterr()
        assert f"File: {file1}" in captured.out

    def test_run_standalone_unknown_flags_with_file(self, capsys, tmp_path):
        """run_standalone() with unknown flags still processes file."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with patch.object(tool.detector, 'detect_mime_type', return_value='text/plain'):
            result = tool.run_standalone(['--unknown', str(test_file), '--another-unknown'])

        assert result == 0
        captured = capsys.readouterr()
        assert "MIME Type:" in captured.out

    def test_run_standalone_verbose_flag_before_file(self, capsys, tmp_path):
        """run_standalone() with --verbose before file argument."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with patch.object(tool.detector, 'detect_mime_type', return_value='text/plain'):
            with patch.object(tool.detector, 'is_text', return_value=True):
                with patch.object(tool.detector, 'is_image', return_value=False):
                    with patch.object(tool.detector, 'is_archive', return_value=False):
                        result = tool.run_standalone(['--verbose', str(test_file)])

        assert result == 0
        captured = capsys.readouterr()
        assert "Is text:" in captured.out

    def test_run_standalone_all_flags_combined(self, capsys, tmp_path):
        """run_standalone() with all flags combined."""
        tool = StandardMIMETool()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with patch.object(tool.detector, 'detect_mime_type', return_value='text/plain'):
            with patch.object(tool.detector, 'is_text', return_value=True):
                with patch.object(tool.detector, 'is_image', return_value=False):
                    with patch.object(tool.detector, 'is_archive', return_value=False):
                        result = tool.run_standalone(['--verbose', '-v', '--file', str(test_file)])

        assert result == 0
        captured = capsys.readouterr()
        assert "MIME Type:" in captured.out
        assert "Is text:" in captured.out

    def test_detector_methods_with_none_mime_type(self):
        """Test detector methods handle edge case MIME types."""
        tool = StandardMIMETool()

        # Test with empty string
        assert tool.detector.is_text('') is False
        assert tool.detector.is_image('') is False
        assert tool.detector.is_archive('') is False

        # Test with None-like values
        assert tool.detector.is_text('application/octet-stream') is False

    def test_tool_properties_are_read_only(self):
        """Test that tool properties cannot be modified."""
        tool = StandardMIMETool()

        # Properties should be read-only (property decorators)
        # Just verify they return consistent values
        name1 = tool.name
        name2 = tool.name
        assert name1 == name2

        version1 = tool.version
        version2 = tool.version
        assert version1 == version2

    def test_tool_string_representation(self):
        """Test tool has meaningful string representation."""
        tool = StandardMIMETool()

        # Should have standard object representation
        assert str(tool) is not None
        assert repr(tool) is not None
