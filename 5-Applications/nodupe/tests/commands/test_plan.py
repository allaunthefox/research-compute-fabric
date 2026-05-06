# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/commands/plan.py - PlanTool."""

import json
import os
import sys
import types
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from nodupe.tools.commands.plan import PlanTool, register_tool


# Set up mock modules for the non-existent imports BEFORE importing the plan module
# This is needed because plan.py tries to import from nodupe.core.database.* which doesn't exist

# Create mock modules
_mock_db_conn = MagicMock()
_mock_db_files = MagicMock()
_mock_container = MagicMock()

# Set up sys.modules with the fake modules
_original_modules = {}
_fake_modules = {
    'nodupe.core.database': types.ModuleType('nodupe.core.database'),
    'nodupe.core.database.connection': types.ModuleType('nodupe.core.database.connection'),
    'nodupe.core.database.files': types.ModuleType('nodupe.core.database.files'),
    'nodupe.core.container': types.ModuleType('nodupe.core.container'),
}

# Set the mock classes
_fake_modules['nodupe.core.database.connection'].DatabaseConnection = _mock_db_conn
_fake_modules['nodupe.core.database.files'].FileRepository = _mock_db_files
_fake_modules['nodupe.core.container'].container = _mock_container
_fake_modules['nodupe.core.container'].container.get_service = MagicMock()

# Store original modules and apply mocks
for mod_name in _fake_modules:
    _original_modules[mod_name] = sys.modules.get(mod_name)
    sys.modules[mod_name] = _fake_modules[mod_name]


class TestPlanToolProperties:
    """Test PlanTool properties."""

    def test_name_property(self):
        """PlanTool.name returns correct value."""
        tool = PlanTool()
        assert tool.name == "plan"

    def test_version_property(self):
        """PlanTool.version returns correct value."""
        tool = PlanTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """PlanTool.dependencies returns correct list."""
        tool = PlanTool()
        assert tool.dependencies == ["scan", "database"]

    def test_description_attribute(self):
        """PlanTool has correct description."""
        tool = PlanTool()
        assert tool.description == "Create execution plan from scan results"


class TestPlanToolInitialize:
    """Test PlanTool.initialize() method."""

    def test_initialize_no_error(self):
        """initialize() completes without error."""
        tool = PlanTool()
        container = MagicMock()
        tool.initialize(container)

    def test_initialize_with_none_container(self):
        """initialize() handles None container gracefully."""
        tool = PlanTool()
        tool.initialize(None)


class TestPlanToolShutdown:
    """Test PlanTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = PlanTool()
        tool.shutdown()


class TestPlanToolGetCapabilities:
    """Test PlanTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary."""
        tool = PlanTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'commands' in capabilities
        assert 'strategies' in capabilities

    def test_get_capabilities_contains_plan_command(self):
        """get_capabilities() contains plan command."""
        tool = PlanTool()
        capabilities = tool.get_capabilities()

        assert 'plan' in capabilities['commands']

    def test_get_capabilities_contains_strategies(self):
        """get_capabilities() contains strategies."""
        tool = PlanTool()
        capabilities = tool.get_capabilities()

        assert 'newest' in capabilities['strategies']
        assert 'oldest' in capabilities['strategies']
        assert 'interactive' in capabilities['strategies']


class TestPlanToolEventHandlers:
    """Test PlanTool event handler methods."""

    def test_on_plan_start(self, capsys):
        """_on_plan_start() prints start message."""
        tool = PlanTool()
        tool._on_plan_start(strategy='newest')

        captured = capsys.readouterr()
        assert "[TOOL] Planning started with strategy: newest" in captured.out

    def test_on_plan_start_default_strategy(self, capsys):
        """_on_plan_start() uses default strategy when not provided."""
        tool = PlanTool()
        tool._on_plan_start()

        captured = capsys.readouterr()
        assert "[TOOL] Planning started with strategy: unknown" in captured.out

    def test_on_plan_complete(self, capsys):
        """_on_plan_complete() prints completion message."""
        tool = PlanTool()
        tool._on_plan_complete(action_count=42)

        captured = capsys.readouterr()
        assert "[TOOL] Planning completed. Actions generated: 42" in captured.out

    def test_on_plan_complete_default_count(self, capsys):
        """_on_plan_complete() uses default count when not provided."""
        tool = PlanTool()
        tool._on_plan_complete()

        captured = capsys.readouterr()
        assert "[TOOL] Planning completed. Actions generated: 0" in captured.out


class TestPlanToolRegisterCommands:
    """Test PlanTool.register_commands() method."""

    def test_register_commands_creates_parser(self):
        """register_commands() creates plan subparser."""
        tool = PlanTool()
        subparsers = MagicMock()
        plan_parser = MagicMock()
        subparsers.add_parser.return_value = plan_parser

        tool.register_commands(subparsers)

        subparsers.add_parser.assert_called_once_with(
            'plan', help='Create execution plan from scan results'
        )

    def test_register_commands_adds_strategy_argument(self):
        """register_commands() adds strategy argument."""
        tool = PlanTool()
        subparsers = MagicMock()
        plan_parser = MagicMock()
        subparsers.add_parser.return_value = plan_parser

        tool.register_commands(subparsers)

        plan_parser.add_argument.assert_any_call(
            '--strategy',
            choices=['newest', 'oldest', 'interactive'],
            default='newest',
            help='Strategy to select keeper file'
        )

    def test_register_commands_adds_output_argument(self):
        """register_commands() adds output argument."""
        tool = PlanTool()
        subparsers = MagicMock()
        plan_parser = MagicMock()
        subparsers.add_parser.return_value = plan_parser

        tool.register_commands(subparsers)

        plan_parser.add_argument.assert_any_call(
            '--output', '-o', default='plan.json', help='Output plan file path'
        )

    def test_register_commands_sets_func(self):
        """register_commands() sets func to execute_plan."""
        tool = PlanTool()
        subparsers = MagicMock()
        plan_parser = MagicMock()
        subparsers.add_parser.return_value = plan_parser

        tool.register_commands(subparsers)

        plan_parser.set_defaults.assert_called_once_with(func=tool.execute_plan)


class TestPlanToolExecuteNoFiles:
    """Test PlanTool.execute_plan() with no files."""

    def test_execute_plan_no_files_in_database(self, capsys):
        """execute_plan() handles empty database."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'newest'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = []
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        result = tool.execute_plan(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No files in database to plan" in captured.out


class TestPlanToolExecuteNewestStrategy:
    """Test PlanTool.execute_plan() with newest strategy."""

    def test_execute_plan_newest_strategy(self, capsys):
        """execute_plan() with newest strategy keeps newest file."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'newest'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Create files with different modified times
        files = [
            {'id': 1, 'path': '/path/to/old.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
            {'id': 2, 'path': '/path/to/new.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 2000, 'is_duplicate': False},
        ]

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            args.output = output_file

            result = tool.execute_plan(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Applying strategy 'newest'" in captured.out
            assert "Plan saved to" in captured.out

            # Verify the plan file was created
            assert os.path.exists(output_file)
            with open(output_file) as f:
                plan_data = json.load(f)
            assert 'metadata' in plan_data
            assert 'actions' in plan_data
            assert plan_data['metadata']['strategy'] == 'newest'


class TestPlanToolExecuteOldestStrategy:
    """Test PlanTool.execute_plan() with oldest strategy."""

    def test_execute_plan_oldest_strategy(self, capsys):
        """execute_plan() with oldest strategy keeps oldest file."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'oldest'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Create files with different modified times
        files = [
            {'id': 1, 'path': '/path/to/old.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
            {'id': 2, 'path': '/path/to/new.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 2000, 'is_duplicate': False},
        ]

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            args.output = output_file

            result = tool.execute_plan(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Applying strategy 'oldest'" in captured.out


class TestPlanToolExecuteInteractiveStrategy:
    """Test PlanTool.execute_plan() with interactive strategy."""

    def test_execute_plan_interactive_strategy(self, capsys):
        """execute_plan() with interactive strategy keeps shortest path."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'interactive'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Create files with different path lengths
        files = [
            {'id': 1, 'path': '/a/b/c/d/e/long/path/file.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
            {'id': 2, 'path': '/short.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 2000, 'is_duplicate': False},
        ]

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            args.output = output_file

            result = tool.execute_plan(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Applying strategy 'interactive'" in captured.out


class TestPlanToolExecuteWithKeeperReassignment:
    """Test PlanTool.execute_plan() with keeper reassignment."""

    def test_execute_plan_reassigns_keeper_if_marked_duplicate(self, capsys):
        """execute_plan() reassigns keeper if it was marked as duplicate."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'newest'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Create files where the keeper (newest) is marked as duplicate
        files = [
            {'id': 1, 'path': '/path/to/old.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
            {'id': 2, 'path': '/path/to/new.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 2000, 'is_duplicate': True, 'duplicate_of': 999},
        ]

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            args.output = output_file

            result = tool.execute_plan(args)

            assert result == 0


class TestPlanToolExecuteNoDuplicates:
    """Test PlanTool.execute_plan() with no duplicates."""

    def test_execute_plan_no_duplicates(self, capsys):
        """execute_plan() handles case with no duplicates."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'newest'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Create files with unique hashes
        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
            {'id': 2, 'path': '/path/to/file2.txt', 'hash': 'def456', 'size': 100,
             'modified_time': 2000, 'is_duplicate': False},
        ]

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            args.output = output_file

            result = tool.execute_plan(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "0 duplicates identified" in captured.out


class TestPlanToolExecuteAllDuplicates:
    """Test PlanTool.execute_plan() where all files are duplicates."""

    def test_execute_plan_all_duplicates(self, capsys):
        """execute_plan() handles case where all files are duplicates."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'newest'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Create files all with same hash
        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
            {'id': 2, 'path': '/path/to/file2.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 2000, 'is_duplicate': False},
            {'id': 3, 'path': '/path/to/file3.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 3000, 'is_duplicate': False},
        ]

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            args.output = output_file

            result = tool.execute_plan(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "2 duplicates identified in 1 groups" in captured.out


class TestPlanToolExecuteFilesWithoutHash:
    """Test PlanTool.execute_plan() with files without hash."""

    def test_execute_plan_files_without_hash(self, capsys):
        """execute_plan() skips files without hash."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'newest'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Create files with missing hash
        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': None, 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
            {'id': 2, 'path': '/path/to/file2.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 2000, 'is_duplicate': False},
        ]

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            args.output = output_file

            result = tool.execute_plan(args)

            assert result == 0


class TestPlanToolExecuteEdgeCases:
    """Test PlanTool.execute_plan() edge cases."""

    def test_execute_plan_general_exception(self, capsys):
        """execute_plan() handles general exceptions."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'newest'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")

        result = tool.execute_plan(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[TOOL ERROR] Plan failed:" in captured.out

    def test_execute_plan_multiple_duplicate_groups(self, capsys):
        """execute_plan() handles multiple duplicate groups."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'newest'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Create two groups of duplicates
        files = [
            # Group 1: hash abc123
            {'id': 1, 'path': '/path/to/group1_file1.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
            {'id': 2, 'path': '/path/to/group1_file2.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 2000, 'is_duplicate': False},
            # Group 2: hash def456
            {'id': 3, 'path': '/path/to/group2_file1.txt', 'hash': 'def456', 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
            {'id': 4, 'path': '/path/to/group2_file2.txt', 'hash': 'def456', 'size': 100,
             'modified_time': 2000, 'is_duplicate': False},
            {'id': 5, 'path': '/path/to/group2_file3.txt', 'hash': 'def456', 'size': 100,
             'modified_time': 3000, 'is_duplicate': False},
        ]

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            args.output = output_file

            result = tool.execute_plan(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "3 duplicates identified in 2 groups" in captured.out

    def test_execute_plan_reassigned_stats(self, capsys):
        """execute_plan() reports reassigned count in stats."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'newest'
        args.output = 'plan.json'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Files where keeper is marked as duplicate
        files = [
            {'id': 1, 'path': '/path/to/old.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
            {'id': 2, 'path': '/path/to/new.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 2000, 'is_duplicate': True, 'duplicate_of': 999},
        ]

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            args.output = output_file

            result = tool.execute_plan(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Reassigned" in captured.out


class TestPlanToolRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_plan_tool(self):
        """register_tool() returns a PlanTool instance."""
        tool = register_tool()
        assert isinstance(tool, PlanTool)


class TestPlanToolModuleLevel:
    """Test module-level exports."""

    def test_plan_tool_instance_exists(self):
        """plan_tool module-level instance exists."""
        from nodupe.tools.commands import plan
        assert plan.plan_tool is not None
        assert isinstance(plan.plan_tool, PlanTool)

    def test_register_tool_function_exists(self):
        """register_tool function is exported."""
        from nodupe.tools.commands import plan
        assert callable(plan.register_tool)

    def test_all_export(self):
        """__all__ contains expected exports."""
        from nodupe.tools.commands import plan
        assert 'plan_tool' in plan.__all__
        assert 'register_tool' in plan.__all__


class TestPlanToolApiMethods:
    """Test PlanTool.api_methods property."""

    def test_api_methods_returns_dict(self):
        """api_methods property returns dictionary."""
        tool = PlanTool()
        api = tool.api_methods
        assert isinstance(api, dict)
        assert 'create_plan' in api
        assert 'get_strategies' in api

    def test_api_methods_get_strategies_callable(self):
        """api_methods get_strategies is callable and returns strategies."""
        tool = PlanTool()
        strategies = tool.api_methods['get_strategies']()
        assert 'newest' in strategies
        assert 'oldest' in strategies
        assert 'interactive' in strategies


class TestPlanToolDescribeUsage:
    """Test PlanTool.describe_usage() method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        tool = PlanTool()
        usage = tool.describe_usage()
        assert isinstance(usage, str)

    def test_describe_usage_contains_plan(self):
        """describe_usage() contains 'Plan tool'."""
        tool = PlanTool()
        usage = tool.describe_usage()
        assert "Plan tool" in usage


class TestPlanToolRunStandalone:
    """Test PlanTool.run_standalone() method."""

    def test_run_standalone_with_args(self):
        """run_standalone() parses arguments and calls execute_plan."""
        tool = PlanTool()

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = []
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            result = tool.run_standalone(['--strategy', 'newest', '-o', output_file])

            assert result == 0

    def test_run_standalone_default_strategy(self):
        """run_standalone() uses default strategy when not specified."""
        tool = PlanTool()

        # Set up mock repo
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = []
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            result = tool.run_standalone(['-o', output_file])

            assert result == 0

    def test_run_standalone_invalid_strategy(self):
        """run_standalone() exits with error for invalid strategy."""
        tool = PlanTool()

        with pytest.raises(SystemExit):
            tool.run_standalone(['--strategy', 'invalid_strategy'])

    def test_run_standalone_with_help(self):
        """run_standalone() shows help with --help."""
        tool = PlanTool()

        with pytest.raises(SystemExit):
            tool.run_standalone(['--help'])


class TestPlanToolExecuteMissingDatabaseService:
    """Test PlanTool.execute_plan() when database service is not available."""

    def test_execute_plan_fallback_to_connection(self, capsys):
        """execute_plan() falls back to DatabaseConnection when service unavailable."""
        tool = PlanTool()
        args = MagicMock()
        args.strategy = 'newest'
        args.output = 'plan.json'
        args.container = MagicMock()
        # Return None for database service to trigger fallback
        args.container.get_service.return_value = None

        # Create files
        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100,
             'modified_time': 1000, 'is_duplicate': False},
        ]

        # Set up mock for both FileRepository and DatabaseConnection
        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        _fake_modules['nodupe.core.database.files'].FileRepository.return_value = mock_repo

        # Make get_instance return a mock db
        mock_db = MagicMock()
        _fake_modules['nodupe.core.database.connection'].DatabaseConnection.get_instance.return_value = mock_db

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'plan.json')
            args.output = output_file

            result = tool.execute_plan(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "[ERROR] Database service not available" in captured.out
            # Verify it tried to use the fallback
            _fake_modules['nodupe.core.database.connection'].DatabaseConnection.get_instance.assert_called()
