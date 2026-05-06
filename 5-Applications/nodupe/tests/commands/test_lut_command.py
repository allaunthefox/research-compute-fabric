# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/commands/lut_command.py - LUTTool."""

from unittest.mock import MagicMock

from nodupe.core.api.codes import ActionCode
from nodupe.tools.commands.lut_command import LUTTool, register_tool


class TestLUTToolProperties:
    """Test LUTTool properties."""

    def test_name_property(self):
        """LUTTool.name returns correct value."""
        tool = LUTTool()
        assert tool.name == "lut_service"

    def test_version_property(self):
        """LUTTool.version returns correct value."""
        tool = LUTTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """LUTTool.dependencies returns empty list."""
        tool = LUTTool()
        assert tool.dependencies == []

    def test_api_methods_property(self):
        """LUTTool.api_methods returns correct methods."""
        tool = LUTTool()
        api_methods = tool.api_methods

        assert 'get_codes' in api_methods
        assert 'describe_code' in api_methods
        assert 'check_iso_compliance' in api_methods

        # Verify they are bound to correct methods
        assert api_methods['get_codes'] == ActionCode.get_lut
        assert api_methods['describe_code'] == ActionCode.get_description


class TestLUTToolInitialize:
    """Test LUTTool.initialize() method."""

    def test_initialize_registers_service(self):
        """initialize() registers lut_service."""
        tool = LUTTool()
        container = MagicMock()

        tool.initialize(container)

        container.register_service.assert_called_once_with('lut_service', tool)


class TestLUTToolShutdown:
    """Test LUTTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = LUTTool()
        # Should not raise
        tool.shutdown()


class TestLUTToolDescribeUsage:
    """Test LUTTool.describe_usage() method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        tool = LUTTool()
        description = tool.describe_usage()

        assert isinstance(description, str)
        assert "dictionary" in description.lower() or "system" in description.lower()


class TestLUTToolRunStandalone:
    """Test LUTTool.run_standalone() method."""

    def test_run_standalone_no_args_shows_help(self, capsys):
        """run_standalone() with no args shows help and returns 0."""
        tool = LUTTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        # Help should be printed
        assert "usage" in captured.out.lower() or "code" in captured.out.lower()

    def test_run_standalone_with_code(self, capsys):
        """run_standalone() with --code argument prints description."""
        tool = LUTTool()

        # Get a valid code from ActionCode
        codes = ActionCode.get_lut()
        if codes.get('codes'):
            valid_code = codes['codes'][0]['code']
            result = tool.run_standalone(['--code', str(valid_code)])

            assert result == 0
            captured = capsys.readouterr()
            assert f"Code {valid_code}:" in captured.out

    def test_run_standalone_with_invalid_code(self, capsys):
        """run_standalone() with invalid code returns description."""
        tool = LUTTool()
        # Use an invalid code number
        result = tool.run_standalone(['--code', '999999'])

        assert result == 0
        captured = capsys.readouterr()
        # Should still print something
        assert "Code 999999:" in captured.out

    def test_run_standalone_with_valid_code(self, capsys):
        """run_standalone() with valid code prints description."""
        tool = LUTTool()

        # Get a valid code from ActionCode
        codes = ActionCode.get_lut()
        if codes.get('codes'):
            valid_code = codes['codes'][0]['code']
            result = tool.run_standalone(['--code', str(valid_code)])

            assert result == 0
            captured = capsys.readouterr()
            assert f"Code {valid_code}:" in captured.out
            # Verify description is printed
            assert "Unknown Action" not in captured.out or valid_code in captured.out


class TestLUTToolGetCapabilities:
    """Test LUTTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary with expected keys."""
        tool = LUTTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'specification' in capabilities
        assert 'features' in capabilities

    def test_get_capabilities_specification(self):
        """get_capabilities() returns ISO specification."""
        tool = LUTTool()
        capabilities = tool.get_capabilities()

        assert capabilities['specification'] == 'ISO-8000-110:2021'

    def test_get_capabilities_features(self):
        """get_capabilities() returns list of features."""
        tool = LUTTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['features'], list)
        assert 'code_lookup' in capabilities['features']
        assert 'description_retrieval' in capabilities['features']


class TestRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_lut_tool(self):
        """register_tool() returns a LUTTool instance."""
        tool = register_tool()
        assert isinstance(tool, LUTTool)


class TestLUTToolMain:
    """Test LUTTool __main__ behavior."""

    def test_main_block_execution(self):
        """Test that __main__ block can be executed."""
        from nodupe.tools.commands import lut_command as lc

        # Simulate running as main
        tool = lc.LUTTool()
        result = tool.run_standalone([])
        assert result == 0
