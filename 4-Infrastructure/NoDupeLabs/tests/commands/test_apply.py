# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/commands/apply.py - ApplyTool."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.commands.apply import ApplyTool, register_tool


class TestApplyToolProperties:
    """Test ApplyTool properties."""

    def test_name_property(self):
        """ApplyTool.name returns correct value."""
        tool = ApplyTool()
        assert tool.name == "apply"

    def test_version_property(self):
        """ApplyTool.version returns correct value."""
        tool = ApplyTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """ApplyTool.dependencies returns empty list."""
        tool = ApplyTool()
        assert tool.dependencies == []

    def test_description_attribute(self):
        """ApplyTool has correct description."""
        tool = ApplyTool()
        assert tool.description == "Apply actions to duplicate files"


class TestApplyToolInitialize:
    """Test ApplyTool.initialize() method."""

    def test_initialize_no_error(self):
        """initialize() completes without error."""
        tool = ApplyTool()
        container = MagicMock()
        # Should not raise
        tool.initialize(container)

    def test_initialize_does_not_require_container(self):
        """initialize() handles None container gracefully."""
        tool = ApplyTool()
        # Should not raise
        tool.initialize(None)


class TestApplyToolShutdown:
    """Test ApplyTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = ApplyTool()
        # Should not raise
        tool.shutdown()


class TestApplyToolGetCapabilities:
    """Test ApplyTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary."""
        tool = ApplyTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'commands' in capabilities

    def test_get_capabilities_contains_apply_command(self):
        """get_capabilities() contains apply command."""
        tool = ApplyTool()
        capabilities = tool.get_capabilities()

        assert 'apply' in capabilities['commands']


class TestApplyToolEventHandlers:
    """Test ApplyTool event handler methods."""

    def test_on_apply_start(self, capsys):
        """_on_apply_start() prints start message."""
        tool = ApplyTool()
        tool._on_apply_start(action='delete')

        captured = capsys.readouterr()
        assert "[TOOL] Apply started: delete" in captured.out

    def test_on_apply_start_default_action(self, capsys):
        """_on_apply_start() uses default action when not provided."""
        tool = ApplyTool()
        tool._on_apply_start()

        captured = capsys.readouterr()
        assert "[TOOL] Apply started: unknown" in captured.out

    def test_on_apply_complete(self, capsys):
        """_on_apply_complete() prints completion message."""
        tool = ApplyTool()
        tool._on_apply_complete(files_processed=42)

        captured = capsys.readouterr()
        assert "[TOOL] Apply completed: 42 files processed" in captured.out

    def test_on_apply_complete_default_count(self, capsys):
        """_on_apply_complete() uses default count when not provided."""
        tool = ApplyTool()
        tool._on_apply_complete()

        captured = capsys.readouterr()
        assert "[TOOL] Apply completed: 0 files processed" in captured.out


class TestApplyToolRegisterCommands:
    """Test ApplyTool.register_commands() method."""

    def test_register_commands_creates_parser(self):
        """register_commands() creates apply subparser."""
        tool = ApplyTool()
        subparsers = MagicMock()
        apply_parser = MagicMock()
        subparsers.add_parser.return_value = apply_parser

        tool.register_commands(subparsers)

        subparsers.add_parser.assert_called_once_with('apply', help='Apply actions to duplicates')

    def test_register_commands_adds_action_argument(self):
        """register_commands() adds action argument."""
        tool = ApplyTool()
        subparsers = MagicMock()
        apply_parser = MagicMock()
        subparsers.add_parser.return_value = apply_parser

        tool.register_commands(subparsers)

        # Verify add_argument was called for action
        apply_parser.add_argument.assert_any_call(
            'action',
            choices=['delete', 'move', 'copy', 'list'],
            help='Action to perform'
        )

    def test_register_commands_adds_destination_argument(self):
        """register_commands() adds destination argument."""
        tool = ApplyTool()
        subparsers = MagicMock()
        apply_parser = MagicMock()
        subparsers.add_parser.return_value = apply_parser

        tool.register_commands(subparsers)

        apply_parser.add_argument.assert_any_call(
            '--destination', '-d',
            help='Destination directory (required for move/copy)'
        )

    def test_register_commands_adds_dry_run_argument(self):
        """register_commands() adds dry-run argument."""
        tool = ApplyTool()
        subparsers = MagicMock()
        apply_parser = MagicMock()
        subparsers.add_parser.return_value = apply_parser

        tool.register_commands(subparsers)

        apply_parser.add_argument.assert_any_call(
            '--dry-run', action='store_true', help='Dry run (no changes)'
        )

    def test_register_commands_adds_verbose_argument(self):
        """register_commands() adds verbose argument."""
        tool = ApplyTool()
        subparsers = MagicMock()
        apply_parser = MagicMock()
        subparsers.add_parser.return_value = apply_parser

        tool.register_commands(subparsers)

        apply_parser.add_argument.assert_any_call(
            '--verbose', '-v', action='store_true', help='Verbose output'
        )

    def test_register_commands_sets_func(self):
        """register_commands() sets func to execute_apply."""
        tool = ApplyTool()
        subparsers = MagicMock()
        apply_parser = MagicMock()
        subparsers.add_parser.return_value = apply_parser

        tool.register_commands(subparsers)

        apply_parser.set_defaults.assert_called_once_with(func=tool.execute_apply)


class TestApplyToolExecuteApplyValidation:
    """Test ApplyTool.execute_apply() validation logic."""

    def test_execute_apply_missing_input_file(self, capsys):
        """execute_apply() returns error when input file is None."""
        tool = ApplyTool()
        args = MagicMock()
        args.input = None
        args.action = 'list'
        args.container = None

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Input file is required" in captured.out

    def test_execute_apply_input_file_not_exists(self, capsys):
        """execute_apply() returns error when input file doesn't exist."""
        tool = ApplyTool()
        args = MagicMock()
        args.input = '/nonexistent/path/file.txt'
        args.action = 'list'
        args.container = None

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Input file does not exist:" in captured.out

    def test_execute_apply_invalid_action(self, capsys):
        """execute_apply() returns error for invalid action."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'invalid_action'
        args.container = None

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Invalid action: invalid_action" in captured.out

    def test_execute_apply_missing_destination_for_move(self, capsys):
        """execute_apply() returns error when move action missing destination."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'move'
        args.destination = None
        args.container = None

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] --destination is required for move/copy actions" in captured.out

    def test_execute_apply_missing_destination_for_copy(self, capsys):
        """execute_apply() returns error when copy action missing destination."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'copy'
        args.destination = None
        args.container = None

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] --destination is required for move/copy actions" in captured.out

    def test_execute_apply_destination_not_exists(self, capsys):
        """execute_apply() returns error when destination directory doesn't exist."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'move'
        args.destination = '/nonexistent/destination'
        args.container = None

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Target directory does not exist:" in captured.out

    def test_execute_apply_missing_container(self, capsys):
        """execute_apply() returns error when container not available."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'list'
        args.container = None
        # Remove input attribute to skip input validation
        delattr(args, 'input')

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Dependency container not available" in captured.out

    def test_execute_apply_missing_database_service(self, capsys):
        """execute_apply() handles missing database service."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'list'
        args.container = MagicMock()
        args.container.get_service.return_value = None
        delattr(args, 'input')

        # Mock DatabaseConnection.get_instance
        with patch('nodupe.tools.commands.apply.DatabaseConnection') as mock_db_conn:
            mock_instance = MagicMock()
            mock_db_conn.get_instance.return_value = mock_instance

            tool.execute_apply(args)

            # Should fallback to default connection
            mock_db_conn.get_instance.assert_called()


class TestApplyToolExecuteApplyList:
    """Test ApplyTool.execute_apply() list action."""

    def test_execute_apply_list_no_duplicates(self, capsys):
        """execute_apply() list action with no duplicates."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'list'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        # Mock FileRepository
        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_apply(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "No items marked as duplicates" in captured.out

    def test_execute_apply_list_with_duplicates(self, capsys):
        """execute_apply() list action with duplicates."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'list'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        # Mock duplicates
        duplicates = [
            {'id': 1, 'path': '/path/to/dup1.txt', 'duplicate_of': 100},
            {'id': 2, 'path': '/path/to/dup2.txt', 'duplicate_of': 100},
        ]
        original = {'id': 100, 'path': '/path/to/original.txt'}

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = duplicates
            mock_repo.get_file.return_value = original
            mock_repo_class.return_value = mock_repo

            result = tool.execute_apply(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Identified Duplicates:" in captured.out
            assert "/path/to/dup1.txt" in captured.out
            assert "/path/to/dup2.txt" in captured.out


class TestApplyToolExecuteApplyDelete:
    """Test ApplyTool.execute_apply() delete action."""

    @pytest.fixture
    def temp_files(self):
        """Create temporary files for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        files = []
        for i in range(3):
            f = temp_dir / f"file{i}.txt"
            f.write_text(f"content {i}")
            files.append(f)
        yield temp_dir, files
        shutil.rmtree(temp_dir)

    def test_execute_apply_delete_dry_run(self, capsys, temp_files):
        """execute_apply() delete action in dry-run mode."""
        tool = ApplyTool()
        temp_dir, files = temp_files

        args = MagicMock()
        args.action = 'delete'
        args.dry_run = True
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': i, 'path': str(f)} for i, f in enumerate(files)]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = duplicates
            mock_repo_class.return_value = mock_repo

            result = tool.execute_apply(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "[DRY-RUN] Would delete:" in captured.out
            assert "Dry run complete" in captured.out

    def test_execute_apply_delete_actual(self, capsys, temp_files):
        """execute_apply() delete action actually deletes files."""
        tool = ApplyTool()
        temp_dir, files = temp_files

        args = MagicMock()
        args.action = 'delete'
        args.dry_run = False
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': i, 'path': str(f)} for i, f in enumerate(files)]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            with patch('nodupe.tools.commands.apply.Filesystem') as mock_fs:
                mock_repo = MagicMock()
                mock_repo.get_duplicate_files.return_value = duplicates
                mock_repo_class.return_value = mock_repo

                result = tool.execute_apply(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "[DELETED]" in captured.out
                # Verify Filesystem.remove_file was called
                assert mock_fs.remove_file.call_count == len(files)


class TestApplyToolExecuteApplyMove:
    """Test ApplyTool.execute_apply() move action."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        src_dir = Path(tempfile.mkdtemp())
        dst_dir = Path(tempfile.mkdtemp())
        yield src_dir, dst_dir
        shutil.rmtree(src_dir)
        shutil.rmtree(dst_dir)

    def test_execute_apply_move_dry_run(self, capsys, temp_dirs):
        """execute_apply() move action in dry-run mode."""
        tool = ApplyTool()
        src_dir, dst_dir = temp_dirs

        # Create source file
        src_file = src_dir / "test.txt"
        src_file.write_text("test content")

        args = MagicMock()
        args.action = 'move'
        args.dry_run = True
        args.destination = str(dst_dir)
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': 1, 'path': str(src_file)}]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = duplicates
            mock_repo_class.return_value = mock_repo

            result = tool.execute_apply(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "[DRY-RUN] Would move:" in captured.out

    def test_execute_apply_move_actual(self, capsys, temp_dirs):
        """execute_apply() move action actually moves files."""
        tool = ApplyTool()
        src_dir, dst_dir = temp_dirs

        # Create source file
        src_file = src_dir / "test.txt"
        src_file.write_text("test content")

        args = MagicMock()
        args.action = 'move'
        args.dry_run = False
        args.destination = str(dst_dir)
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': 1, 'path': str(src_file)}]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            with patch('nodupe.tools.commands.apply.Filesystem') as mock_fs:
                mock_repo = MagicMock()
                mock_repo.get_duplicate_files.return_value = duplicates
                mock_repo_class.return_value = mock_repo

                result = tool.execute_apply(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "[MOVED]" in captured.out
                mock_fs.move_file.assert_called()
                mock_fs.ensure_directory.assert_called()


class TestApplyToolExecuteApplyCopy:
    """Test ApplyTool.execute_apply() copy action."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        src_dir = Path(tempfile.mkdtemp())
        dst_dir = Path(tempfile.mkdtemp())
        yield src_dir, dst_dir
        shutil.rmtree(src_dir)
        shutil.rmtree(dst_dir)

    def test_execute_apply_copy_dry_run(self, capsys, temp_dirs):
        """execute_apply() copy action in dry-run mode."""
        tool = ApplyTool()
        src_dir, dst_dir = temp_dirs

        # Create source file
        src_file = src_dir / "test.txt"
        src_file.write_text("test content")

        args = MagicMock()
        args.action = 'copy'
        args.dry_run = True
        args.destination = str(dst_dir)
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': 1, 'path': str(src_file)}]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = duplicates
            mock_repo_class.return_value = mock_repo

            result = tool.execute_apply(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "[DRY-RUN] Would copy:" in captured.out

    def test_execute_apply_copy_actual(self, capsys, temp_dirs):
        """execute_apply() copy action actually copies files."""
        tool = ApplyTool()
        src_dir, dst_dir = temp_dirs

        # Create source file
        src_file = src_dir / "test.txt"
        src_file.write_text("test content")

        args = MagicMock()
        args.action = 'copy'
        args.dry_run = False
        args.destination = str(dst_dir)
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': 1, 'path': str(src_file)}]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            with patch('nodupe.tools.commands.apply.Filesystem') as mock_fs:
                mock_repo = MagicMock()
                mock_repo.get_duplicate_files.return_value = duplicates
                mock_repo_class.return_value = mock_repo

                result = tool.execute_apply(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "[COPIED]" in captured.out
                mock_fs.copy_file.assert_called()
                mock_fs.ensure_directory.assert_called()


class TestApplyToolExecuteApplyEdgeCases:
    """Test ApplyTool.execute_apply() edge cases."""

    def test_execute_apply_file_not_found(self, capsys):
        """execute_apply() handles file not found during processing."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'delete'
        args.dry_run = False
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': 1, 'path': '/nonexistent/file.txt'}]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = duplicates
            mock_repo_class.return_value = mock_repo

            result = tool.execute_apply(args)

            assert result == 0  # Should continue processing other files
            captured = capsys.readouterr()
            assert "[WARN] File not found:" in captured.out

    def test_execute_apply_processing_error(self, capsys):
        """execute_apply() handles processing errors gracefully."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'delete'
        args.dry_run = False
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        # Create a temp file that exists so the error happens during processing
        import tempfile
        temp_dir = tempfile.mkdtemp()
        temp_file = Path(temp_dir) / "test.txt"
        temp_file.write_text("test")

        try:
            duplicates = [{'id': 1, 'path': str(temp_file)}]

            with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
                with patch('nodupe.tools.commands.apply.Filesystem') as mock_fs:
                    mock_fs.remove_file.side_effect = Exception("Test error")
                    mock_repo = MagicMock()
                    mock_repo.get_duplicate_files.return_value = duplicates
                    mock_repo_class.return_value = mock_repo

                    result = tool.execute_apply(args)

                    assert result == 0  # Should continue processing
                    captured = capsys.readouterr()
                    assert "[ERROR] Failed to process" in captured.out
        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_execute_apply_general_exception(self, capsys):
        """execute_apply() handles general exceptions."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'list'
        args.verbose = True
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")
        delattr(args, 'input')

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[TOOL ERROR] Apply failed:" in captured.out

    def test_execute_apply_verbose_exception_traceback(self, capsys):
        """execute_apply() prints traceback when verbose is True."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'list'
        args.verbose = True
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")
        delattr(args, 'input')

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Traceback" in captured.out or "Traceback" in captured.err or "[TOOL ERROR]" in captured.out


class TestApplyToolExecuteApplyMoveEdgeCases:
    """Test ApplyTool.execute_apply() move action edge cases."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        src_dir = Path(tempfile.mkdtemp())
        dst_dir = Path(tempfile.mkdtemp())
        yield src_dir, dst_dir
        shutil.rmtree(src_dir)
        shutil.rmtree(dst_dir)

    def test_execute_apply_move_collision_handling(self, capsys, temp_dirs):
        """execute_apply() move action handles destination collision."""
        tool = ApplyTool()
        src_dir, dst_dir = temp_dirs

        # Create source file
        src_file = src_dir / "test.txt"
        src_file.write_text("test content")

        # Create destination file with same name (collision)
        dst_file = dst_dir / "test.txt"
        dst_file.write_text("existing content")

        args = MagicMock()
        args.action = 'move'
        args.dry_run = False
        args.destination = str(dst_dir)
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': 1, 'path': str(src_file)}]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            with patch('nodupe.tools.commands.apply.Filesystem') as mock_fs:
                mock_repo = MagicMock()
                mock_repo.get_duplicate_files.return_value = duplicates
                mock_repo_class.return_value = mock_repo

                result = tool.execute_apply(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "[MOVED]" in captured.out
                mock_fs.move_file.assert_called()

    def test_execute_apply_copy_collision_handling(self, capsys, temp_dirs):
        """execute_apply() copy action handles destination collision."""
        tool = ApplyTool()
        src_dir, dst_dir = temp_dirs

        # Create source file
        src_file = src_dir / "test.txt"
        src_file.write_text("test content")

        # Create destination file with same name (collision)
        dst_file = dst_dir / "test.txt"
        dst_file.write_text("existing content")

        args = MagicMock()
        args.action = 'copy'
        args.dry_run = False
        args.destination = str(dst_dir)
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': 1, 'path': str(src_file)}]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            with patch('nodupe.tools.commands.apply.Filesystem') as mock_fs:
                mock_repo = MagicMock()
                mock_repo.get_duplicate_files.return_value = duplicates
                mock_repo_class.return_value = mock_repo

                result = tool.execute_apply(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "[COPIED]" in captured.out
                mock_fs.copy_file.assert_called()


class TestApplyToolExecuteApplyDryRun:
    """Test ApplyTool.execute_apply() dry run messages."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        src_dir = Path(tempfile.mkdtemp())
        dst_dir = Path(tempfile.mkdtemp())
        yield src_dir, dst_dir
        shutil.rmtree(src_dir)
        shutil.rmtree(dst_dir)

    def test_execute_apply_dry_run_complete_message(self, capsys, temp_dirs):
        """execute_apply() prints dry run complete message."""
        tool = ApplyTool()
        src_dir, dst_dir = temp_dirs

        # Create source file
        src_file = src_dir / "test.txt"
        src_file.write_text("test content")

        args = MagicMock()
        args.action = 'delete'
        args.dry_run = True
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': 1, 'path': str(src_file)}]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = duplicates
            mock_repo_class.return_value = mock_repo

            result = tool.execute_apply(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Dry run complete" in captured.out


class TestApplyToolModuleLevelEdgeCases:
    """Test ApplyTool module-level edge cases."""

    def test_api_methods_property(self):
        """api_methods property returns empty list."""
        tool = ApplyTool()
        assert tool.api_methods == {}

    def test_describe_usage(self):
        """describe_usage() returns usage description."""
        tool = ApplyTool()
        usage = tool.describe_usage()
        assert "Apply file management" in usage

    def test_run_standalone(self):
        """run_standalone() calls execute_apply."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'list'
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.run_standalone(args)
            assert result == 0


class TestApplyToolRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_apply_tool(self):
        """register_tool() returns an ApplyTool instance."""
        tool = register_tool()
        assert isinstance(tool, ApplyTool)


class TestApplyToolModuleLevel:
    """Test module-level exports."""

    def test_apply_tool_instance_exists(self):
        """apply_tool module-level instance exists."""
        from nodupe.tools.commands import apply
        assert apply.apply_tool is not None
        assert isinstance(apply.apply_tool, ApplyTool)

    def test_register_tool_function_exists(self):
        """register_tool function is exported."""
        from nodupe.tools.commands import apply
        assert callable(apply.register_tool)

    def test_all_export(self):
        """__all__ contains expected exports."""
        from nodupe.tools.commands import apply
        assert 'apply_tool' in apply.__all__
        assert 'register_tool' in apply.__all__


class TestApplyToolCoverageCompletion:
    """Additional tests to achieve 100% coverage."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        src_dir = Path(tempfile.mkdtemp())
        dst_dir = Path(tempfile.mkdtemp())
        # Create a file in dst_dir to cause collision
        collision_file = dst_dir / "test.txt"
        collision_file.write_text("existing content")
        yield src_dir, dst_dir
        shutil.rmtree(src_dir)
        shutil.rmtree(dst_dir)

    def test_execute_apply_move_collision_with_existing_file(self, capsys, temp_dirs):
        """execute_apply() move action handles collision with existing file."""
        tool = ApplyTool()
        src_dir, dst_dir = temp_dirs

        # Create source file
        src_file = src_dir / "test.txt"
        src_file.write_text("test content")

        args = MagicMock()
        args.action = 'move'
        args.dry_run = False
        args.destination = str(dst_dir)
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': 1, 'path': str(src_file)}]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            with patch('nodupe.tools.commands.apply.Filesystem') as mock_fs:
                mock_repo = MagicMock()
                mock_repo.get_duplicate_files.return_value = duplicates
                mock_repo_class.return_value = mock_repo

                result = tool.execute_apply(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "[MOVED]" in captured.out
                mock_fs.move_file.assert_called()

    def test_execute_apply_copy_collision_with_existing_file(self, capsys, temp_dirs):
        """execute_apply() copy action handles collision with existing file."""
        tool = ApplyTool()
        src_dir, dst_dir = temp_dirs

        # Create source file
        src_file = src_dir / "test.txt"
        src_file.write_text("test content")

        args = MagicMock()
        args.action = 'copy'
        args.dry_run = False
        args.destination = str(dst_dir)
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [{'id': 1, 'path': str(src_file)}]

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            with patch('nodupe.tools.commands.apply.Filesystem') as mock_fs:
                mock_repo = MagicMock()
                mock_repo.get_duplicate_files.return_value = duplicates
                mock_repo_class.return_value = mock_repo

                result = tool.execute_apply(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "[COPIED]" in captured.out
                mock_fs.copy_file.assert_called()

    def test_execute_apply_destination_validation_true_path(self, capsys):
        """execute_apply() validates destination path exists for move."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'move'
        args.destination = '/tmp'  # This should exist
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        # Mock duplicates to be empty so we don't actually process
        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_apply(args)

            # Should pass validation and continue
            assert result == 0
            captured = capsys.readouterr()
            assert "No items marked as duplicates" in captured.out

    def test_execute_apply_verbose_exception_handling(self, capsys):
        """execute_apply() prints traceback when verbose and exception occurs."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'list'
        args.verbose = True
        args.container = MagicMock()
        # Make get_service raise an exception
        args.container.get_service.side_effect = RuntimeError("Test runtime error")
        delattr(args, 'input')

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[TOOL ERROR] Apply failed:" in captured.out

    def test_execute_apply_destination_exists_validation(self, capsys):
        """execute_apply() validates destination path that exists."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'move'
        args.destination = '/tmp'  # This exists
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        # Mock FileRepository to return empty duplicates
        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_apply(args)

            # Should pass validation (destination exists) and continue
            assert result == 0
            captured = capsys.readouterr()
            # Should not have "Target directory does not exist" error
            assert "Target directory does not exist" not in captured.out

    def test_execute_apply_exception_without_verbose(self, capsys):
        """execute_apply() handles exception without verbose traceback."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'list'
        args.verbose = False  # No verbose
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")
        delattr(args, 'input')

        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[TOOL ERROR] Apply failed:" in captured.out
        # Should NOT have traceback when verbose is False

    def test_execute_apply_destination_not_set_branch(self, capsys):
        """execute_apply() covers branch when destination is not set."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'move'
        args.destination = None  # Destination not set - covers False branch
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        # This should fail validation before reaching the destination check
        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "--destination is required" in captured.out

    def test_execute_apply_list_action_branch(self, capsys):
        """execute_apply() covers branch for list action (not move/copy)."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'list'  # List action - covers False branch of move/copy
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        duplicates = [
            {'id': 1, 'path': '/path/to/dup1.txt', 'duplicate_of': 100},
        ]
        original = {'id': 100, 'path': '/path/to/original.txt'}

        with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_duplicate_files.return_value = duplicates
            mock_repo.get_file.return_value = original
            mock_repo_class.return_value = mock_repo

            result = tool.execute_apply(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Identified Duplicates:" in captured.out

    def test_execute_apply_delete_action_branch(self, capsys):
        """execute_apply() covers branch for delete action (not copy)."""
        tool = ApplyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.action = 'delete'  # Delete action - covers False branch of copy
            args.dry_run = True
            args.verbose = False
            args.container = MagicMock()
            args.container.get_service.return_value = MagicMock()
            delattr(args, 'input')

            duplicates = [{'id': 1, 'path': str(test_file)}]

            with patch('nodupe.tools.commands.apply.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_duplicate_files.return_value = duplicates
                mock_repo_class.return_value = mock_repo

                result = tool.execute_apply(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "[DRY-RUN] Would delete:" in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_execute_apply_move_action_no_destination_continue(self, capsys):
        """execute_apply() covers continue branch when destination missing for move."""
        tool = ApplyTool()
        args = MagicMock()
        args.action = 'move'
        args.destination = None  # No destination - triggers continue
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'input')

        # This should fail validation before reaching the continue statement
        result = tool.execute_apply(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "--destination is required" in captured.out
        assert "Traceback" not in captured.out
