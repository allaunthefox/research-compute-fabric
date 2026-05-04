"""Tests for the main module - CLI entry point."""

import argparse
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from nodupe.core.main import CLIHandler, main


class TestCLIHandlerInitialization:
    """Test CLIHandler initialization and setup."""

    def test_cli_handler_creation(self):
        """Test CLIHandler instance creation."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        assert cli is not None
        assert cli.loader is mock_loader
        assert cli.parser is not None

    def test_cli_handler_with_tool_registry(self):
        """Test CLIHandler with tool registry."""
        mock_loader = Mock()
        mock_registry = Mock()
        mock_registry.get_tools.return_value = []
        mock_loader.tool_registry = mock_registry
        cli = CLIHandler(mock_loader)

        assert cli.loader.tool_registry is mock_registry

    def test_create_parser_structure(self):
        """Test parser has expected structure."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        parser = cli._create_parser()
        assert parser is not None
        assert parser.description is not None

    def test_parser_has_verbose_flag(self):
        """Test parser has verbose flag."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        args = cli.parser.parse_args(['--verbose'])
        assert args.verbose is True

    def test_parser_has_debug_flag(self):
        """Test parser has debug flag."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        args = cli.parser.parse_args(['--debug'])
        assert args.debug is True

    def test_parser_has_speed_option(self):
        """Test parser has speed option."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        args = cli.parser.parse_args(['--speed', 'fast'])
        assert args.speed == 'fast'

    def test_parser_has_cores_option(self):
        """Test parser has cores option."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        args = cli.parser.parse_args(['--cores', '8'])
        assert args.cores == 8

    def test_parser_has_max_workers_option(self):
        """Test parser has max_workers option."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        args = cli.parser.parse_args(['--max-workers', '16'])
        assert args.max_workers == 16

    def test_parser_has_batch_size_option(self):
        """Test parser has batch_size option."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        args = cli.parser.parse_args(['--batch-size', '500'])
        assert args.batch_size == 500


class TestCLIHandlerCommandRegistration:
    """Test command registration functionality."""

    def test_register_builtin_commands(self):
        """Test built-in commands are registered."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        # Parse known commands to verify they exist
        args = cli.parser.parse_args(['version'])
        assert args.command == 'version'

        args = cli.parser.parse_args(['tools'])
        assert args.command == 'tools'

        args = cli.parser.parse_args(['tool'])
        assert args.command == 'tool'

        args = cli.parser.parse_args(['scan', '/path'])
        assert args.command == 'scan'

        args = cli.parser.parse_args(['similarity'])
        assert args.command == 'similarity'

        args = cli.parser.parse_args(['plan'])
        assert args.command == 'plan'

    def test_register_tool_commands_from_registry(self):
        """Test registering tool commands from registry."""
        mock_loader = Mock()
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.register_commands = Mock()
        mock_registry = Mock()
        mock_registry.get_tools.return_value = [mock_tool]
        mock_loader.tool_registry = mock_registry

        cli = CLIHandler.__new__(CLIHandler)
        cli.loader = mock_loader
        cli.parser = argparse.ArgumentParser()

        cli._register_commands()

        mock_tool.register_commands.assert_called_once()

    def test_register_tool_commands_handles_exception(self, caplog):
        """Test tool command registration handles exceptions."""
        mock_loader = Mock()
        mock_tool = Mock()
        mock_tool.name = "FailingTool"
        mock_tool.register_commands = Mock(side_effect=Exception("Registration failed"))
        mock_registry = Mock()
        mock_registry.get_tools.return_value = [mock_tool]
        mock_loader.tool_registry = mock_registry

        cli = CLIHandler.__new__(CLIHandler)
        cli.loader = mock_loader
        cli.parser = argparse.ArgumentParser()

        with caplog.at_level(logging.WARNING):
            cli._register_commands()

        # Should not raise, just log warning
        mock_tool.register_commands.assert_called_once()

    def test_register_tool_commands_tool_without_register_commands(self):
        """Test tool without register_commands method."""
        mock_loader = Mock()
        mock_tool = Mock()
        mock_tool.name = "NoRegisterTool"
        # Remove register_commands attribute
        del mock_tool.register_commands
        mock_registry = Mock()
        mock_registry.get_tools.return_value = [mock_tool]
        mock_loader.tool_registry = mock_registry

        cli = CLIHandler.__new__(CLIHandler)
        cli.loader = mock_loader
        cli.parser = argparse.ArgumentParser()

        # Should not raise
        cli._register_commands()


class TestCLIHandlerRun:
    """Test CLIHandler run method."""

    def test_run_with_no_args_shows_help(self):
        """Test run with no arguments shows help."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_loader.config = Mock()
        mock_loader.config.config = {}
        cli = CLIHandler(mock_loader)

        with patch.object(cli.parser, 'parse_args') as mock_parse:
            mock_parsed = Mock()
            mock_parsed.debug = False
            del mock_parsed.func
            mock_parse.return_value = mock_parsed

            with patch.object(cli.parser, 'print_help') as mock_help:
                result = cli.run([])

                mock_help.assert_called_once()
                assert result == 0

    def test_run_with_version_command(self, capsys):
        """Test run with version command."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        result = cli.run(['version'])

        captured = capsys.readouterr()
        assert "NoDupeLabs CLI v1.0.0" in captured.out
        assert result == 0

    def test_run_with_tools_list_command(self, capsys):
        """Test run with tools --list command."""
        mock_loader = Mock()
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.version = "1.0.0"
        mock_registry = Mock()
        mock_registry.get_tools.return_value = [mock_tool]
        mock_loader.tool_registry = mock_registry
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        result = cli.run(['tools', '--list'])

        captured = capsys.readouterr()
        assert "TestTool" in captured.out
        assert result == 0

    def test_run_with_scan_command(self, capsys, tmp_path):
        """Test run with scan command."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        # Create a test directory
        test_dir = tmp_path / "test_scan"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")

        result = cli.run(['scan', str(test_dir)])

        captured = capsys.readouterr()
        assert "Scanning:" in captured.out
        assert result == 0

    def test_run_with_scan_nonexistent_path(self, capsys):
        """Test run with scan command on nonexistent path."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        result = cli.run(['scan', '/nonexistent/path'])

        # Just check that it returns error code 1
        assert result == 1

    def test_run_with_scan_file_not_directory(self, capsys, tmp_path):
        """Test run with scan command on file instead of directory."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = cli.run(['scan', str(test_file)])

        # Just check that it returns error code 1
        assert result == 1

    def test_run_with_similarity_command(self, capsys):
        """Test run with similarity command."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        result = cli.run(['similarity', '/path'])

        captured = capsys.readouterr()
        assert "Similarity analysis" in captured.out
        assert result == 0

    def test_run_with_plan_command(self, capsys):
        """Test run with plan command."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        result = cli.run(['plan', '/path'])

        captured = capsys.readouterr()
        assert "Creating deduplication plan" in captured.out
        assert result == 0

    def test_run_with_debug_flag(self, capsys):
        """Test run with debug flag."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        with patch.object(cli, '_setup_debug_logging') as mock_setup:
            result = cli.run(['--debug', 'version'])

            mock_setup.assert_called_once()
            assert result == 0

    def test_run_with_exception(self, capsys):
        """Test run handles exceptions in commands."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        # Create args that will raise exception
        mock_parsed = Mock()
        mock_parsed.func = Mock(side_effect=Exception("Command failed"))
        mock_parsed.debug = False

        with patch.object(cli.parser, 'parse_args', return_value=mock_parsed):
            result = cli.run([])

            assert result == 1

    def test_run_with_debug_and_exception(self, capsys):
        """Test run with debug flag and exception shows traceback."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        mock_parsed = Mock()
        mock_parsed.func = Mock(side_effect=Exception("Command failed"))
        mock_parsed.debug = True

        with patch.object(cli.parser, 'parse_args', return_value=mock_parsed):
            with patch('traceback.print_exc') as mock_traceback:
                result = cli.run([])

                mock_traceback.assert_called_once()
                assert result == 1


class TestCLIHandlerCommands:
    """Test individual CLI handler commands."""

    def test_cmd_version_basic(self, capsys):
        """Test version command basic output."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        result = cli._cmd_version(Mock())

        captured = capsys.readouterr()
        assert "NoDupeLabs CLI v1.0.0" in captured.out
        assert result == 0

    def test_cmd_version_with_config(self, capsys):
        """Test version command with config."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {
            'drive_type': 'SSD',
            'cpu_cores': 8,
            'ram_gb': 16
        }
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        result = cli._cmd_version(Mock())

        captured = capsys.readouterr()
        assert "SSD" in captured.out
        assert "8" in captured.out
        assert "16" in captured.out
        assert result == 0

    def test_cmd_version_no_config_attribute(self, capsys):
        """Test version command when config has no config attribute."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock(spec=[])
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        result = cli._cmd_version(Mock())

        captured = capsys.readouterr()
        assert "NoDupeLabs CLI v1.0.0" in captured.out
        assert result == 0

    def test_cmd_tools_no_registry(self, capsys):
        """Test tools command when registry is not active."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        result = cli._cmd_tool(Mock())

        # Just check that it returns error code 1
        assert result == 1

    def test_cmd_tools_list(self, capsys):
        """Test tools list command."""
        mock_loader = Mock()
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.version = "1.0.0"
        mock_registry = Mock()
        mock_registry.get_tools.return_value = [mock_tool]
        mock_loader.tool_registry = mock_registry
        cli = CLIHandler(mock_loader)

        mock_args = Mock()
        mock_args.list = True

        result = cli._cmd_tool(mock_args)

        captured = capsys.readouterr()
        assert "TestTool" in captured.out
        assert result == 0

    def test_cmd_tools_list_accessible_tool(self, capsys):
        """Test tools list with accessible tool."""
        from nodupe.core.tool_system.base import AccessibleTool

        mock_loader = Mock()

        class MockAccessibleTool(AccessibleTool):
            """Mock accessible tool for testing."""
            name = "AccessibleTool"
            version = "1.0.0"
            dependencies = []

            def initialize(self, container):
                """Initialize the mock tool."""
                pass

            def shutdown(self):
                """Shutdown the mock tool."""
                pass

            def get_capabilities(self):
                """Get tool capabilities."""
                return {}

            @property
            def api_methods(self):
                """Return API methods."""
                return {}

            def run_standalone(self, args):
                """Run tool as standalone."""
                return 0

            def describe_usage(self):
                """Describe tool usage."""
                return "Usage"

        mock_registry = Mock()
        mock_registry.get_tools.return_value = [MockAccessibleTool()]
        mock_loader.tool_registry = mock_registry
        cli = CLIHandler(mock_loader)

        mock_args = Mock()
        mock_args.list = True

        result = cli._cmd_tool(mock_args)

        captured = capsys.readouterr()
        assert "AccessibleTool" in captured.out
        assert result == 0

    def test_cmd_tools_list_non_accessible_tool(self, capsys):
        """Test tools list with non-accessible tool."""
        from nodupe.core.tool_system.base import Tool

        mock_loader = Mock()

        class MockNonAccessibleTool(Tool):
            """Mock non-accessible tool for testing."""
            name = "NonAccessibleTool"
            version = "1.0.0"
            dependencies = []

            def initialize(self, container):
                """Initialize the mock tool."""
                pass

            def shutdown(self):
                """Shutdown the mock tool."""
                pass

            def get_capabilities(self):
                """Get tool capabilities."""
                return {}

            @property
            def api_methods(self):
                """Return API methods."""
                return {}

            def run_standalone(self, args):
                """Run tool as standalone."""
                return 0

            def describe_usage(self):
                """Describe tool usage."""
                return "Usage"

        mock_registry = Mock()
        mock_registry.get_tools.return_value = [MockNonAccessibleTool()]
        mock_loader.tool_registry = mock_registry
        cli = CLIHandler(mock_loader)

        mock_args = Mock()
        mock_args.list = True

        result = cli._cmd_tool(mock_args)

        captured = capsys.readouterr()
        assert "NonAccessibleTool" in captured.out
        assert result == 0

    def test_cmd_tools_no_list_flag(self, capsys):
        """Test tools command without list flag."""
        mock_loader = Mock()
        mock_registry = Mock()
        mock_registry.get_tools.return_value = []
        mock_loader.tool_registry = mock_registry
        cli = CLIHandler(mock_loader)

        mock_args = Mock()
        mock_args.list = False

        result = cli._cmd_tool(mock_args)

        assert result == 0

    def test_cmd_scan_basic(self, capsys, tmp_path):
        """Test scan command basic functionality."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        test_dir = tmp_path / "scan_test"
        test_dir.mkdir()

        mock_args = Mock()
        mock_args.path = str(test_dir)

        result = cli._cmd_scan(mock_args)

        captured = capsys.readouterr()
        assert "Scanning:" in captured.out
        assert result == 0

    def test_cmd_similarity_basic(self, capsys):
        """Test similarity command basic functionality."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        mock_args = Mock()
        mock_args.path = "/test/path"

        result = cli._cmd_similarity(mock_args)

        captured = capsys.readouterr()
        assert "Similarity analysis" in captured.out
        assert result == 0

    def test_cmd_plan_basic(self, capsys):
        """Test plan command basic functionality."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        mock_args = Mock()
        mock_args.path = "/test/path"

        result = cli._cmd_plan(mock_args)

        captured = capsys.readouterr()
        assert "Creating deduplication plan" in captured.out
        assert result == 0


class TestCLIHandlerUtilities:
    """Test CLIHandler utility methods."""

    def test_setup_debug_logging(self):
        """Test debug logging setup."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        cli = CLIHandler(mock_loader)

        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            cli._setup_debug_logging()

            mock_logger.setLevel.assert_called_once()

    def test_apply_overrides_all(self):
        """Test applying all performance overrides."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config_obj = Mock()
        mock_config_obj.config = {}
        mock_loader.config = mock_config_obj
        cli = CLIHandler(mock_loader)

        mock_args = Mock()
        mock_args.cores = 8
        mock_args.max_workers = 16
        mock_args.batch_size = 500

        cli._apply_overrides(mock_args)

        assert mock_config_obj.config['cpu_cores'] == 8
        assert mock_config_obj.config['max_workers'] == 16
        assert mock_config_obj.config['batch_size'] == 500

    def test_apply_overrides_partial(self):
        """Test applying partial performance overrides."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config_obj = Mock()
        mock_config_obj.config = {}
        mock_loader.config = mock_config_obj
        cli = CLIHandler(mock_loader)

        mock_args = Mock()
        mock_args.cores = 4
        mock_args.max_workers = None
        mock_args.batch_size = None

        cli._apply_overrides(mock_args)

        assert mock_config_obj.config['cpu_cores'] == 4
        assert 'max_workers' not in mock_config_obj.config
        assert 'batch_size' not in mock_config_obj.config

    def test_apply_overrides_no_config(self):
        """Test apply overrides with no config."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_loader.config = None
        cli = CLIHandler(mock_loader)

        mock_args = Mock()
        mock_args.cores = 8

        # Should not raise
        cli._apply_overrides(mock_args)

    def test_apply_overrides_config_no_config_attr(self):
        """Test apply overrides when config has no config attribute."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock(spec=[])
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        mock_args = Mock()
        mock_args.cores = 8

        # Should not raise
        cli._apply_overrides(mock_args)


class TestMainFunction:
    """Test main entry point function."""

    def test_main_success(self):
        """Test main function success case."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_cli_class:

            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader

            mock_cli = Mock()
            mock_cli.run.return_value = 0
            mock_cli_class.return_value = mock_cli

            result = main(['version'])

            mock_bootstrap.assert_called_once()
            mock_cli_class.assert_called_once_with(mock_loader)
            mock_cli.run.assert_called_once_with(['version'])
            mock_loader.shutdown.assert_called_once()
            assert result == 0

    def test_main_keyboard_interrupt(self, capsys):
        """Test main function with keyboard interrupt."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_cli_class:

            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader

            mock_cli = Mock()
            mock_cli.run.side_effect = KeyboardInterrupt()
            mock_cli_class.return_value = mock_cli

            result = main([])

            assert result == 130
            mock_loader.shutdown.assert_called_once()

    def test_main_exception_during_run(self, capsys):
        """Test main function with exception during run."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_cli_class:

            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader

            mock_cli = Mock()
            mock_cli.run.side_effect = Exception("Run failed")
            mock_cli_class.return_value = mock_cli

            result = main([])

            assert result == 1
            mock_loader.shutdown.assert_called_once()

    def test_main_bootstrap_exception(self, capsys):
        """Test main function with bootstrap exception."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap:
            mock_bootstrap.side_effect = Exception("Bootstrap failed")

            result = main([])

            assert result == 1

    def test_main_shutdown_exception(self, capsys):
        """Test main function with shutdown exception."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_cli_class:

            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader
            mock_loader.shutdown.side_effect = Exception("Shutdown failed")

            mock_cli = Mock()
            mock_cli.run.return_value = 0
            mock_cli_class.return_value = mock_cli

            result = main([])

            assert result == 0
            mock_loader.shutdown.assert_called_once()

    def test_main_with_none_args(self):
        """Test main function with None args."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_cli_class:

            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader

            mock_cli = Mock()
            mock_cli.run.return_value = 0
            mock_cli_class.return_value = mock_cli

            result = main(None)

            assert result == 0


class TestCLIHandlerEdgeCases:
    """Test edge cases for CLIHandler."""

    def test_tool_alias_command(self, capsys):
        """Test tool alias command (alias for tools)."""
        mock_loader = Mock()
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.version = "1.0.0"
        mock_registry = Mock()
        mock_registry.get_tools.return_value = [mock_tool]
        mock_loader.tool_registry = mock_registry
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        result = cli.run(['tool', '--list'])

        captured = capsys.readouterr()
        assert "TestTool" in captured.out
        assert result == 0

    def test_run_injects_container_into_args(self):
        """Test that run injects container into args."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        mock_parsed = Mock()
        mock_parsed.func = Mock(return_value=0)
        mock_parsed.debug = False

        with patch.object(cli.parser, 'parse_args', return_value=mock_parsed):
            cli.run([])

            assert mock_parsed.container == mock_loader.container

    def test_cmd_version_accessibility_compliance(self, capsys):
        """Test version command reports accessibility compliance."""
        mock_loader = Mock()
        mock_loader.tool_registry = None
        mock_config = Mock()
        mock_config.config = {}
        mock_loader.config = mock_config
        cli = CLIHandler(mock_loader)

        result = cli._cmd_version(Mock())

        captured = capsys.readouterr()
        assert "ISO Accessibility Compliant" in captured.out
        assert result == 0
