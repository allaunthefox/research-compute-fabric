# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Comprehensive tests for nodupe.core.main module.

This module provides thorough tests to increase coverage for the CLI
entry point module, testing all code paths including:
- CLIHandler initialization and parser creation
- Command registration
- Command execution (version, tool, scan, similarity, plan)
- Debug logging setup
- Performance override application
- Error handling
"""

import argparse
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nodupe.core.main import CLIHandler, main


class TestCLIHandlerInitialization:
    """Test CLIHandler initialization and parser creation."""

    def test_cli_handler_init_with_loader(self):
        """Test CLIHandler initializes with a loader."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)
        assert cli.loader == mock_loader
        assert cli.parser is not None

    def test_create_parser(self):
        """Test parser creation with all expected arguments."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)
        parser = cli.parser

        # Check global flags
        assert '--verbose' in [action.option_strings[0] for action in parser._actions if action.option_strings]
        assert '--debug' in [action.option_strings[0] for action in parser._actions if action.option_strings]

        # Check performance options
        assert '--speed' in [action.option_strings[0] for action in parser._actions if action.option_strings]
        assert '--cores' in [action.option_strings[0] for action in parser._actions if action.option_strings]
        assert '--max-workers' in [action.option_strings[0] for action in parser._actions if action.option_strings]
        assert '--batch-size' in [action.option_strings[0] for action in parser._actions if action.option_strings]

    def test_subparsers_created(self):
        """Test that subparsers are created for commands."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []
        cli = CLIHandler(mock_loader)

        # Get subparsers from _subparsers
        subparsers_action = cli.parser._subparsers._actions[-1]
        assert "version" in subparsers_action.choices
        assert "tool" in subparsers_action.choices
        assert "tools" in subparsers_action.choices
        assert "scan" in subparsers_action.choices
        assert "similarity" in subparsers_action.choices
        assert "plan" in subparsers_action.choices

    def _old_test_subparsers_created(self):
        """Test that subparsers are created for commands."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        # Find subparsers action
        subparsers_action = None
        for action in cli.parser._actions:
            if hasattr(action, 'choices'):
                subparsers_action = action
                break

        assert subparsers_action is not None
        assert 'version' in subparsers_action.choices
        assert 'tool' in subparsers_action.choices
        assert 'tools' in subparsers_action.choices
        assert 'scan' in subparsers_action.choices
        assert 'similarity' in subparsers_action.choices
        assert 'plan' in subparsers_action.choices


class TestCommandRegistration:
    """Test command registration functionality."""

    def test_register_commands_with_no_tools(self):
        """Test command registration with empty tool registry."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)
        # Should not raise any errors

    def test_register_commands_with_tools(self):
        """Test command registration with tools."""
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.register_commands = MagicMock()

        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = [mock_tool]

        cli = CLIHandler(mock_loader)

        # Check tool's register_commands was called
        mock_tool.register_commands.assert_called()

    def test_register_commands_with_accessible_tool(self):
        """Test command registration with accessible tool."""
        mock_tool = MagicMock()
        mock_tool.name = "accessible_tool"
        mock_tool.register_commands = MagicMock()

        # Make it look like an AccessibleTool
        mock_tool.get_ipc_socket_documentation = MagicMock()

        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = [mock_tool]

        cli = CLIHandler(mock_loader)

        mock_tool.register_commands.assert_called()

    def test_register_commands_exception_handling(self):
        """Test that exceptions during registration are handled."""
        mock_tool = MagicMock()
        mock_tool.name = "failing_tool"
        mock_tool.register_commands = MagicMock(side_effect=Exception("Registration failed"))

        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = [mock_tool]

        # Should not raise, just log warning
        cli = CLIHandler(mock_loader)
        assert cli.parser is not None


class TestCLIHandlerRun:
    """Test CLIHandler run method."""

    def test_run_with_version_command(self):
        """Test run method with version command."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        result = cli.run(['version'])
        assert result == 0

    def test_run_with_tool_command(self):
        """Test run method with tool command."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        result = cli.run(['tool'])
        assert result == 0

    def test_run_with_tool_list_command(self):
        """Test run method with tool --list command."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        result = cli.run(['tool', '--list'])
        assert result == 0

    def test_run_with_tools_command(self):
        """Test run method with tools command (alias)."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        result = cli.run(['tools', '--list'])
        assert result == 0

    def test_run_with_no_args(self):
        """Test run method with no arguments."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        with patch('sys.stdout', MagicMock()):
            result = cli.run([])
            # No command should show help and return 0
            assert result == 0

    def test_run_with_debug_flag(self):
        """Test run method with debug flag."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        result = cli.run(['--debug', 'version'])
        assert result == 0

    def test_run_with_verbose_flag(self):
        """Test run method with verbose flag."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        result = cli.run(['--verbose', 'version'])
        assert result == 0


class TestVersionCommand:
    """Test version command."""

    def test_version_command_with_config(self):
        """Test version command with loader config."""
        mock_loader = MagicMock()
        mock_loader.config = MagicMock()
        mock_loader.config.config = {
            'drive_type': 'ssd',
            'cpu_cores': 8,
            'ram_gb': 16
        }

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace()
        result = cli._cmd_version(args)
        assert result == 0

    def test_version_command_without_config(self):
        """Test version command without loader config."""
        mock_loader = MagicMock()
        mock_loader.config = None

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace()
        result = cli._cmd_version(args)
        assert result == 0


class TestToolCommand:
    """Test tool command."""

    def test_tool_command_with_registry(self):
        """Test tool command with tool registry."""
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.version = "1.0.0"

        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = [mock_tool]

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(list=True)
        result = cli._cmd_tool(args)
        assert result == 0

    def test_tool_command_without_registry(self):
        """Test tool command without tool registry."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = None

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(list=False)
        result = cli._cmd_tool(args)
        assert result == 1

    def test_tool_command_with_accessible_tool(self):
        """Test tool command with accessible tool."""
        mock_tool = MagicMock()
        mock_tool.name = "accessible_tool"
        mock_tool.version = "1.0.0"

        # Mock as AccessibleTool
        type(mock_tool).__name__ = 'AccessibleTool'

        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = [mock_tool]

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(list=True)
        result = cli._cmd_tool(args)
        assert result == 0


class TestScanCommand:
    """Test scan command."""

    def test_scan_command_with_valid_path(self, tmp_path):
        """Test scan command with valid directory."""
        # Create a temp directory with some files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")

        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(path=str(tmp_path))
        result = cli._cmd_scan(args)
        assert result == 0

    def test_scan_command_with_nonexistent_path(self):
        """Test scan command with nonexistent path."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(path='/nonexistent/path/12345')
        result = cli._cmd_scan(args)
        assert result == 1

    def test_scan_command_with_file_path(self, tmp_path):
        """Test scan command with a file instead of directory."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(path=str(test_file))
        result = cli._cmd_scan(args)
        assert result == 1


class TestSimilarityCommand:
    """Test similarity command."""

    def test_similarity_command_with_path(self):
        """Test similarity command with path argument."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(path='/some/path')
        result = cli._cmd_similarity(args)
        assert result == 0

    def test_similarity_command_without_path(self):
        """Test similarity command without path argument."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        args = argparse.Namespace()
        result = cli._cmd_similarity(args)
        assert result == 0


class TestPlanCommand:
    """Test plan command."""

    def test_plan_command_with_path(self):
        """Test plan command with path argument."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(path='/some/path')
        result = cli._cmd_plan(args)
        assert result == 0

    def test_plan_command_without_path(self):
        """Test plan command without path argument."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        args = argparse.Namespace()
        result = cli._cmd_plan(args)
        assert result == 0


class TestDebugLogging:
    """Test debug logging setup."""

    def test_setup_debug_logging(self):
        """Test debug logging setup."""
        mock_loader = MagicMock()
        cli = CLIHandler(mock_loader)

        # Should not raise
        cli._setup_debug_logging()


class TestPerformanceOverrides:
    """Test performance override application."""

    def test_apply_overrides_with_config(self):
        """Test applying performance overrides with config."""
        mock_loader = MagicMock()
        mock_loader.config = MagicMock()
        mock_loader.config.config = {
            'cpu_cores': 4,
            'max_workers': 8,
            'batch_size': 100
        }

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(cores=16, max_workers=32, batch_size=500)
        cli._apply_overrides(args)

        assert mock_loader.config.config['cpu_cores'] == 16
        assert mock_loader.config.config['max_workers'] == 32
        assert mock_loader.config.config['batch_size'] == 500

    def test_apply_overrides_partial(self):
        """Test applying partial performance overrides."""
        mock_loader = MagicMock()
        mock_loader.config = MagicMock()
        mock_loader.config.config = {
            'cpu_cores': 4,
            'max_workers': 8,
            'batch_size': 100
        }

        cli = CLIHandler(mock_loader)

        # Only override cores
        args = argparse.Namespace(cores=16, max_workers=None, batch_size=None)
        cli._apply_overrides(args)

        assert mock_loader.config.config['cpu_cores'] == 16
        assert mock_loader.config.config['max_workers'] == 8
        assert mock_loader.config.config['batch_size'] == 100

    def test_apply_overrides_without_config(self):
        """Test applying overrides without config."""
        mock_loader = MagicMock()
        mock_loader.config = None

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(cores=16, max_workers=32, batch_size=500)
        # Should not raise
        cli._apply_overrides(args)

    def test_apply_overrides_without_config_attr(self):
        """Test applying overrides with config lacking config attribute."""
        mock_loader = MagicMock()
        mock_loader.config = MagicMock()
        del mock_loader.config.config

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(cores=16, max_workers=32, batch_size=500)
        # Should not raise
        cli._apply_overrides(args)


class TestMainFunction:
    """Test main function."""

    def test_main_with_version_args(self):
        """Test main function with version args."""
        with patch('sys.argv', ['nodupe', 'version']):
            result = main()
            assert result == 0

    def test_main_keyboard_interrupt(self):
        """Test main function handles keyboard interrupt."""
        with patch('nodupe.core.main.bootstrap', side_effect=KeyboardInterrupt()):
            with patch('sys.argv', ['nodupe', 'version']):
                result = main()
                assert result == 130

    def test_main_startup_error(self):
        """Test main function handles startup errors."""
        with patch('nodupe.core.main.bootstrap', side_effect=Exception("Startup failed")):
            with patch('sys.argv', ['nodupe', 'version']):
                result = main()
                assert result == 1

    def test_main_shutdown_error(self):
        """Test main function handles shutdown errors."""
        mock_loader = MagicMock()
        mock_loader.shutdown = MagicMock(side_effect=Exception("Shutdown failed"))

        with patch('nodupe.core.main.bootstrap', return_value=mock_loader):
            with patch('sys.argv', ['nodupe', 'version']):
                result = main()
                assert result == 0  # Should still return 0 even if shutdown fails

    def test_main_with_speed_flag(self):
        """Test main function with speed flag."""
        with patch('sys.argv', ['nodupe', '--speed', 'fast', 'version']):
            result = main()
            assert result == 0


class TestCLIHandlerEdgeCases:
    """Test edge cases in CLIHandler."""

    def test_run_with_speed_normal(self):
        """Test run with speed=normal."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        result = cli.run(['--speed', 'normal', 'version'])
        assert result == 0

    def test_run_with_speed_safe(self):
        """Test run with speed=safe."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        result = cli.run(['--speed', 'safe', 'version'])
        assert result == 0

    def test_run_with_speed_fast(self):
        """Test run with speed=fast."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        result = cli.run(['--speed', 'fast', 'version'])
        assert result == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestToolCommandBranches:
    """Test tool command branch coverage."""

    def test_tool_command_with_non_accessible_tool(self):
        """Test tool command with a non-accessible tool."""
        mock_tool = MagicMock()
        mock_tool.name = "regular_tool"
        mock_tool.version = "1.0.0"
        # Ensure no get_ipc_socket_documentation method

        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = [mock_tool]

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(list=True)
        result = cli._cmd_tool(args)
        assert result == 0

    def test_tool_command_without_list_flag(self):
        """Test tool command without --list flag."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(list=False)
        result = cli._cmd_tool(args)
        assert result == 0


class TestExceptionHandling:
    """Test exception handling in CLI."""

    def test_run_command_exception_handling(self):
        """Test run method handles command exceptions."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        # Create a command that raises an exception
        def failing_command(args):
            """Helper function that raises an exception for testing."""
            raise Exception("Command failed")
            raise Exception("Command failed")
        # Use patch to inject a failing command
        with patch.object(cli.parser, 'parse_args') as mock_parse:
            mock_args = MagicMock()
            mock_args.debug = False
            mock_args.func = failing_command
            mock_args.cores = None
            mock_args.max_workers = None
            mock_args.batch_size = None
            mock_parse.return_value = mock_args

            result = cli.run([])
            assert result == 1

    def test_run_command_exception_with_debug(self):
        """Test run method handles command exceptions with debug enabled."""
        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = []

        cli = CLIHandler(mock_loader)

        # Create a command that raises an exception
        def failing_command(args):
            """Helper function that raises an exception for testing."""
            raise Exception("Command failed")

        with patch.object(cli.parser, 'parse_args') as mock_parse:
            mock_args = MagicMock()
            mock_args.debug = True  # Enable debug
            mock_args.func = failing_command
            mock_args.cores = None
            mock_args.max_workers = None
            mock_args.batch_size = None
            mock_parse.return_value = mock_args

            # Should not raise
            result = cli.run([])
            assert result == 1


class TestAccessibleToolBranch:
    """Test the AccessibleTool branch in tool command."""

    def test_tool_command_with_accessible_tool_instance_check(self):
        """Test that AccessibleTool isinstance check works correctly."""
        # Create a mock that pretends to be an AccessibleTool
        from nodupe.core.tool_system.base import AccessibleTool

        mock_tool = MagicMock(spec=AccessibleTool)
        mock_tool.name = "accessible_test"
        mock_tool.version = "2.0.0"

        # Verify it passes isinstance check
        assert isinstance(mock_tool, AccessibleTool)

        mock_loader = MagicMock()
        mock_loader.tool_registry = MagicMock()
        mock_loader.tool_registry.get_tools.return_value = [mock_tool]

        cli = CLIHandler(mock_loader)

        args = argparse.Namespace(list=True)
        result = cli._cmd_tool(args)
        assert result == 0
