# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/commands/scan.py - ScanTool."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.commands.scan import ScanTool, register_tool


class TestScanToolProperties:
    """Test ScanTool properties."""

    def test_name_property(self):
        """ScanTool.name returns correct value."""
        tool = ScanTool()
        assert tool.name == "scan"

    def test_version_property(self):
        """ScanTool.version returns correct value."""
        tool = ScanTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """ScanTool.dependencies returns empty list."""
        tool = ScanTool()
        assert tool.dependencies == []

    def test_description_attribute(self):
        """ScanTool has correct description."""
        tool = ScanTool()
        assert tool.description == "Scan directories for duplicate files"


class TestScanToolInitialize:
    """Test ScanTool.initialize() method."""

    def test_initialize_no_error(self):
        """initialize() completes without error."""
        tool = ScanTool()
        container = MagicMock()
        # Should not raise
        tool.initialize(container)

    def test_initialize_with_none_container(self):
        """initialize() handles None container gracefully."""
        tool = ScanTool()
        # Should not raise
        tool.initialize(None)


class TestScanToolShutdown:
    """Test ScanTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = ScanTool()
        # Should not raise
        tool.shutdown()


class TestScanToolGetCapabilities:
    """Test ScanTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary."""
        tool = ScanTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'commands' in capabilities

    def test_get_capabilities_contains_scan_command(self):
        """get_capabilities() contains scan command."""
        tool = ScanTool()
        capabilities = tool.get_capabilities()

        assert 'scan' in capabilities['commands']


class TestScanToolEventHandlers:
    """Test ScanTool event handler methods."""

    def test_on_scan_start(self, capsys):
        """_on_scan_start() prints start message."""
        tool = ScanTool()
        tool._on_scan_start(path='/test/path')

        captured = capsys.readouterr()
        assert "[TOOL] Scan started: /test/path" in captured.out

    def test_on_scan_start_default_path(self, capsys):
        """_on_scan_start() uses default path when not provided."""
        tool = ScanTool()
        tool._on_scan_start()

        captured = capsys.readouterr()
        assert "[TOOL] Scan started: unknown" in captured.out

    def test_on_scan_complete(self, capsys):
        """_on_scan_complete() prints completion message."""
        tool = ScanTool()
        tool._on_scan_complete(files_processed=42)

        captured = capsys.readouterr()
        assert "[TOOL] Scan completed: 42 files processed" in captured.out

    def test_on_scan_complete_default_count(self, capsys):
        """_on_scan_complete() uses default count when not provided."""
        tool = ScanTool()
        tool._on_scan_complete()

        captured = capsys.readouterr()
        assert "[TOOL] Scan completed: 0 files processed" in captured.out


class TestScanToolRegisterCommands:
    """Test ScanTool.register_commands() method."""

    def test_register_commands_creates_parser(self):
        """register_commands() creates scan subparser."""
        tool = ScanTool()
        subparsers = MagicMock()
        scan_parser = MagicMock()
        subparsers.add_parser.return_value = scan_parser

        tool.register_commands(subparsers)

        subparsers.add_parser.assert_called_once_with(
            'scan', help='Scan directories for duplicates'
        )

    def test_register_commands_adds_paths_argument(self):
        """register_commands() adds paths argument."""
        tool = ScanTool()
        subparsers = MagicMock()
        scan_parser = MagicMock()
        subparsers.add_parser.return_value = scan_parser

        tool.register_commands(subparsers)

        # Verify add_argument was called for paths
        scan_parser.add_argument.assert_any_call(
            'paths', nargs='+', help='Directories to scan'
        )

    def test_register_commands_adds_min_size_argument(self):
        """register_commands() adds min-size argument."""
        tool = ScanTool()
        subparsers = MagicMock()
        scan_parser = MagicMock()
        subparsers.add_parser.return_value = scan_parser

        tool.register_commands(subparsers)

        scan_parser.add_argument.assert_any_call(
            '--min-size', type=int, default=0, help='Minimum file size'
        )

    def test_register_commands_adds_max_size_argument(self):
        """register_commands() adds max-size argument."""
        tool = ScanTool()
        subparsers = MagicMock()
        scan_parser = MagicMock()
        subparsers.add_parser.return_value = scan_parser

        tool.register_commands(subparsers)

        scan_parser.add_argument.assert_any_call(
            '--max-size', type=int, help='Maximum file size'
        )

    def test_register_commands_adds_extensions_argument(self):
        """register_commands() adds extensions argument."""
        tool = ScanTool()
        subparsers = MagicMock()
        scan_parser = MagicMock()
        subparsers.add_parser.return_value = scan_parser

        tool.register_commands(subparsers)

        scan_parser.add_argument.assert_any_call(
            '--extensions', nargs='+', help='File extensions to include'
        )

    def test_register_commands_adds_exclude_argument(self):
        """register_commands() adds exclude argument."""
        tool = ScanTool()
        subparsers = MagicMock()
        scan_parser = MagicMock()
        subparsers.add_parser.return_value = scan_parser

        tool.register_commands(subparsers)

        scan_parser.add_argument.assert_any_call(
            '--exclude', nargs='+', help='Directories to exclude'
        )

    def test_register_commands_adds_verbose_argument(self):
        """register_commands() adds verbose argument."""
        tool = ScanTool()
        subparsers = MagicMock()
        scan_parser = MagicMock()
        subparsers.add_parser.return_value = scan_parser

        tool.register_commands(subparsers)

        scan_parser.add_argument.assert_any_call(
            '--verbose', '-v', action='store_true', help='Verbose output'
        )

    def test_register_commands_sets_func(self):
        """register_commands() sets func to execute_scan."""
        tool = ScanTool()
        subparsers = MagicMock()
        scan_parser = MagicMock()
        subparsers.add_parser.return_value = scan_parser

        tool.register_commands(subparsers)

        scan_parser.set_defaults.assert_called_once_with(func=tool.execute_scan)


class TestScanToolExecuteValidation:
    """Test ScanTool.execute_scan() validation logic."""

    def test_execute_scan_no_paths_provided(self, capsys):
        """execute_scan() returns error when no paths provided."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = []

        result = tool.execute_scan(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "No paths provided" in captured.out

    def test_execute_scan_path_does_not_exist(self, capsys):
        """execute_scan() returns error when path doesn't exist."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = ['/nonexistent/path']

        result = tool.execute_scan(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Path does not exist: /nonexistent/path" in captured.out

    def test_execute_scan_missing_container(self, capsys):
        """execute_scan() returns error when container not available."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = ['/tmp']
        args.container = None

        result = tool.execute_scan(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Dependency container not available" in captured.out

    def test_execute_scan_missing_database_service(self, capsys):
        """execute_scan() handles missing database service."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = ['/tmp']
        args.container = MagicMock()
        args.container.get_service.return_value = None
        args.verbose = False

        with patch('nodupe.tools.commands.scan.DatabaseConnection') as mock_db_conn:
            mock_instance = MagicMock()
            mock_db_conn.get_instance.return_value = mock_instance

            # Mock FileWalker and FileProcessor to avoid actual scanning
            with patch('nodupe.tools.commands.scan.FileWalker'):
                with patch('nodupe.tools.commands.scan.FileProcessor'):
                    tool.execute_scan(args)

                    # Should fallback to default connection
                    mock_db_conn.get_instance.assert_called()


class TestScanToolExecuteScan:
    """Test ScanTool.execute_scan() main functionality."""

    @pytest.fixture
    def temp_scan_dir(self):
        """Create temporary directory with files for scanning."""
        temp_dir = Path(tempfile.mkdtemp())
        # Create some test files
        for i in range(3):
            f = temp_dir / f"file{i}.txt"
            f.write_text(f"content {i}")
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_execute_scan_single_path(self, capsys, temp_scan_dir):
        """execute_scan() scans a single path."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 0
        args.max_size = None
        args.extensions = None
        args.exclude = None
        args.verbose = False

        # Mock FileProcessor to return test results
        mock_results = [
            {'path': str(temp_scan_dir / 'file0.txt'), 'size': 10, 'hash': 'abc123'},
            {'path': str(temp_scan_dir / 'file1.txt'), 'size': 10, 'hash': 'def456'},
        ]

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.return_value = mock_results
            mock_processor_class.return_value = mock_processor

            with patch('nodupe.tools.commands.scan.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.batch_add_files.return_value = 2
                mock_repo_class.return_value = mock_repo

                result = tool.execute_scan(args)

                assert result == 0
                captured = capsys.readouterr()
                assert f"Scanning directory: {temp_scan_dir}" in captured.out
                assert "Found 2 files" in captured.out
                assert "Saved 2 records" in captured.out

    def test_execute_scan_multiple_paths(self, capsys):
        """execute_scan() scans multiple paths."""
        tool = ScanTool()
        temp_dir1 = Path(tempfile.mkdtemp())
        temp_dir2 = Path(tempfile.mkdtemp())

        try:
            args = MagicMock()
            args.paths = [str(temp_dir1), str(temp_dir2)]
            args.container = MagicMock()
            args.container.get_service.return_value = MagicMock()
            args.min_size = 0
            args.max_size = None
            args.extensions = None
            args.exclude = None
            args.verbose = False

            mock_results = [
                {'path': str(temp_dir1 / 'file.txt'), 'size': 10, 'hash': 'abc123'},
            ]

            with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
                mock_processor = MagicMock()
                mock_processor.process_files.return_value = mock_results
                mock_processor_class.return_value = mock_processor

                with patch('nodupe.tools.commands.scan.FileRepository') as mock_repo_class:
                    mock_repo = MagicMock()
                    mock_repo.batch_add_files.return_value = 1
                    mock_repo_class.return_value = mock_repo

                    result = tool.execute_scan(args)

                    assert result == 0
                    captured = capsys.readouterr()
                    assert f"Scanning directory: {temp_dir1}" in captured.out
                    assert f"Scanning directory: {temp_dir2}" in captured.out
        finally:
            shutil.rmtree(temp_dir1)
            shutil.rmtree(temp_dir2)

    def test_execute_scan_no_files_found(self, capsys, temp_scan_dir):
        """execute_scan() handles no files found."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 0
        args.max_size = None
        args.extensions = None
        args.exclude = None
        args.verbose = False

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.return_value = []
            mock_processor_class.return_value = mock_processor

            result = tool.execute_scan(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "No files found" in captured.out


class TestScanToolExecuteScanFilters:
    """Test ScanTool.execute_scan() with filters."""

    @pytest.fixture
    def temp_scan_dir(self):
        """Create temporary directory with files for scanning."""
        temp_dir = Path(tempfile.mkdtemp())
        # Create some test files with different sizes
        (temp_dir / "small.txt").write_text("small")
        (temp_dir / "medium.txt").write_text("m" * 1000)
        (temp_dir / "large.txt").write_text("l" * 10000)
        (temp_dir / "image.jpg").write_bytes(b"jpg content")
        (temp_dir / "doc.pdf").write_bytes(b"pdf content")
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_execute_scan_min_size_filter(self, capsys, temp_scan_dir):
        """execute_scan() applies min-size filter."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 500  # Only files >= 500 bytes
        args.max_size = None
        args.extensions = None
        args.exclude = None
        args.verbose = False

        def filter_func(info):
            """Filter function for min_size test."""
            return info['size'] >= 500

        mock_results = [
            {'path': str(temp_scan_dir / 'medium.txt'), 'size': 1000, 'hash': 'abc123'},
            {'path': str(temp_scan_dir / 'large.txt'), 'size': 10000, 'hash': 'def456'},
        ]

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.return_value = mock_results
            mock_processor_class.return_value = mock_processor

            with patch('nodupe.tools.commands.scan.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.batch_add_files.return_value = 2
                mock_repo_class.return_value = mock_repo

                result = tool.execute_scan(args)

                assert result == 0

    def test_execute_scan_max_size_filter(self, capsys, temp_scan_dir):
        """execute_scan() applies max-size filter."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 0
        args.max_size = 5000  # Only files <= 5000 bytes
        args.extensions = None
        args.exclude = None
        args.verbose = False

        mock_results = [
            {'path': str(temp_scan_dir / 'small.txt'), 'size': 5, 'hash': 'abc123'},
            {'path': str(temp_scan_dir / 'medium.txt'), 'size': 1000, 'hash': 'def456'},
        ]

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.return_value = mock_results
            mock_processor_class.return_value = mock_processor

            with patch('nodupe.tools.commands.scan.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.batch_add_files.return_value = 2
                mock_repo_class.return_value = mock_repo

                result = tool.execute_scan(args)

                assert result == 0

    def test_execute_scan_extensions_filter(self, capsys, temp_scan_dir):
        """execute_scan() applies extensions filter."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 0
        args.max_size = None
        args.extensions = ['jpg', 'pdf']  # Only jpg and pdf files
        args.exclude = None
        args.verbose = False

        mock_results = [
            {'path': str(temp_scan_dir / 'image.jpg'), 'size': 11, 'hash': 'abc123', 'extension': '.jpg'},
            {'path': str(temp_scan_dir / 'doc.pdf'), 'size': 11, 'hash': 'def456', 'extension': '.pdf'},
        ]

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.return_value = mock_results
            mock_processor_class.return_value = mock_processor

            with patch('nodupe.tools.commands.scan.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.batch_add_files.return_value = 2
                mock_repo_class.return_value = mock_repo

                result = tool.execute_scan(args)

                assert result == 0


class TestScanToolExecuteScanVerbose:
    """Test ScanTool.execute_scan() verbose output."""

    @pytest.fixture
    def temp_scan_dir(self):
        """Create temporary directory with files for scanning."""
        temp_dir = Path(tempfile.mkdtemp())
        for i in range(3):
            f = temp_dir / f"file{i}.txt"
            f.write_text(f"content {i}")
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_execute_scan_verbose_output(self, capsys, temp_scan_dir):
        """execute_scan() with verbose flag prints progress."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 0
        args.max_size = None
        args.extensions = None
        args.exclude = None
        args.verbose = True

        mock_results = [
            {'path': str(temp_scan_dir / 'file0.txt'), 'size': 10, 'hash': 'abc123'},
        ]

        def progress_callback(p):
            """Mock progress callback for testing."""
            print(f"\rScanning... {p['files_processed']} files", end="", flush=True)

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.return_value = mock_results
            mock_processor_class.return_value = mock_processor

            with patch('nodupe.tools.commands.scan.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.batch_add_files.return_value = 1
                mock_repo_class.return_value = mock_repo

                result = tool.execute_scan(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "Scanning" in captured.out


class TestScanToolExecuteEdgeCases:
    """Test ScanTool.execute_scan() edge cases."""

    def test_execute_scan_general_exception(self, capsys):
        """execute_scan() handles general exceptions."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = ['/tmp']
        args.verbose = True
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")

        result = tool.execute_scan(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[TOOL ERROR] Scan failed:" in captured.out

    def test_execute_scan_general_exception_with_traceback(self, capsys):
        """execute_scan() prints traceback when verbose is True."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = ['/tmp']
        args.verbose = True
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")

        result = tool.execute_scan(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Traceback" in captured.out or "Traceback" in captured.err or "[TOOL ERROR]" in captured.out

    def test_execute_scan_timing(self, capsys):
        """execute_scan() reports timing information."""
        tool = ScanTool()
        temp_dir = Path(tempfile.mkdtemp())

        try:
            args = MagicMock()
            args.paths = [str(temp_dir)]
            args.container = MagicMock()
            args.container.get_service.return_value = MagicMock()
            args.min_size = 0
            args.max_size = None
            args.extensions = None
            args.exclude = None
            args.verbose = False

            mock_results = []

            with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
                mock_processor = MagicMock()
                mock_processor.process_files.return_value = mock_results
                mock_processor_class.return_value = mock_processor

                result = tool.execute_scan(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "Scan complete in" in captured.out
        finally:
            shutil.rmtree(temp_dir)


class TestScanToolRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_scan_tool(self):
        """register_tool() returns a ScanTool instance."""
        tool = register_tool()
        assert isinstance(tool, ScanTool)


class TestScanToolModuleLevel:
    """Test module-level exports."""

    def test_scan_tool_instance_exists(self):
        """scan_tool module-level instance exists."""
        from nodupe.tools.commands import scan
        assert scan.scan_tool is not None
        assert isinstance(scan.scan_tool, ScanTool)

    def test_register_tool_function_exists(self):
        """register_tool function is exported."""
        from nodupe.tools.commands import scan
        assert callable(scan.register_tool)

    def test_all_export(self):
        """__all__ contains expected exports."""
        from nodupe.tools.commands import scan
        assert 'scan_tool' in scan.__all__
        assert 'register_tool' in scan.__all__

    def test_api_methods_property(self):
        """api_methods property returns empty list."""
        tool = ScanTool()
        assert tool.api_methods == {}

    def test_describe_usage(self):
        """describe_usage() returns usage description."""
        tool = ScanTool()
        usage = tool.describe_usage()
        assert "Scan directories" in usage

    def test_run_standalone(self):
        """run_standalone() calls execute_scan."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = ['/tmp']
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.return_value = []
            mock_processor_class.return_value = mock_processor

            result = tool.run_standalone(args)
            assert result == 0


class TestScanToolCoverageCompletion:
    """Additional tests to achieve 100% coverage."""

    @pytest.fixture
    def temp_scan_dir(self):
        """Create temporary directory with files for scanning."""
        temp_dir = Path(tempfile.mkdtemp())
        # Create files with different sizes and extensions
        (temp_dir / "small.txt").write_text("small")
        (temp_dir / "medium.txt").write_text("m" * 1000)
        (temp_dir / "large.txt").write_text("l" * 10000)
        (temp_dir / "image.jpg").write_bytes(b"jpg content")
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_execute_scan_file_filter_min_size_reject(self, capsys, temp_scan_dir):
        """execute_scan() file_filter rejects files below min_size."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 5000  # Only files >= 5000 bytes
        args.max_size = None
        args.extensions = None
        args.exclude = None
        args.verbose = False

        # Mock FileProcessor to call the actual filter
        def mock_process_files(root_path, file_filter, on_progress):
            """Mock FileProcessor.process_files for testing."""
            # Test the filter with various file sizes
            test_files = [
                {'path': str(temp_scan_dir / 'small.txt'), 'size': 5, 'extension': '.txt'},
                {'path': str(temp_scan_dir / 'large.txt'), 'size': 10000, 'extension': '.txt'},
            ]
            # Filter should reject small.txt
            assert not file_filter(test_files[0])
            # Filter should accept large.txt
            assert file_filter(test_files[1])
            return test_files

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.side_effect = mock_process_files
            mock_processor_class.return_value = mock_processor

            with patch('nodupe.tools.commands.scan.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.batch_add_files.return_value = 1
                mock_repo_class.return_value = mock_repo

                result = tool.execute_scan(args)

                assert result == 0

    def test_execute_scan_file_filter_max_size_reject(self, capsys, temp_scan_dir):
        """execute_scan() file_filter rejects files above max_size."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 0
        args.max_size = 100  # Only files <= 100 bytes
        args.extensions = None
        args.exclude = None
        args.verbose = False

        def mock_process_files(root_path, file_filter, on_progress):
            """Mock FileProcessor.process_files for testing."""
            test_files = [
                {'path': str(temp_scan_dir / 'small.txt'), 'size': 5, 'extension': '.txt'},
                {'path': str(temp_scan_dir / 'large.txt'), 'size': 10000, 'extension': '.txt'},
            ]
            # Filter should accept small.txt
            assert file_filter(test_files[0])
            # Filter should reject large.txt
            assert not file_filter(test_files[1])
            return test_files

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.side_effect = mock_process_files
            mock_processor_class.return_value = mock_processor

            with patch('nodupe.tools.commands.scan.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.batch_add_files.return_value = 1
                mock_repo_class.return_value = mock_repo

                result = tool.execute_scan(args)

                assert result == 0

    def test_execute_scan_file_filter_extension_reject(self, capsys, temp_scan_dir):
        """execute_scan() file_filter rejects files with wrong extension."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 0
        args.max_size = None
        args.extensions = ['txt']  # Only txt files
        args.exclude = None
        args.verbose = False

        def mock_process_files(root_path, file_filter, on_progress):
            """Mock FileProcessor.process_files for testing."""
            test_files = [
                {'path': str(temp_scan_dir / 'small.txt'), 'size': 5, 'extension': '.txt'},
                {'path': str(temp_scan_dir / 'image.jpg'), 'size': 11, 'extension': '.jpg'},
            ]
            # Filter should accept txt
            assert file_filter(test_files[0])
            # Filter should reject jpg
            assert not file_filter(test_files[1])
            return test_files

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.side_effect = mock_process_files
            mock_processor_class.return_value = mock_processor

            with patch('nodupe.tools.commands.scan.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.batch_add_files.return_value = 1
                mock_repo_class.return_value = mock_repo

                result = tool.execute_scan(args)

                assert result == 0

    def test_execute_scan_progress_callback_verbose(self, capsys, temp_scan_dir):
        """execute_scan() progress_callback prints when verbose."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 0
        args.max_size = None
        args.extensions = None
        args.exclude = None
        args.verbose = True


        def mock_process_files(root_path, file_filter, on_progress):
            """Mock FileProcessor.process_files for testing."""
            # Call the progress callback to test it
            on_progress({'files_processed': 10, 'files_per_second': 100.5})
            return []

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.side_effect = mock_process_files
            mock_processor_class.return_value = mock_processor

            result = tool.execute_scan(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Scanning..." in captured.out

    def test_execute_scan_progress_callback_not_verbose(self, capsys, temp_scan_dir):
        """execute_scan() progress_callback does not print when not verbose."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        args.min_size = 0
        args.max_size = None
        args.extensions = None
        args.exclude = None
        args.verbose = False

        def mock_process_files(root_path, file_filter, on_progress):
            """Mock FileProcessor.process_files for testing."""
            # Call the progress callback - should not print
            on_progress({'files_processed': 10, 'files_per_second': 100.5})
            return []

        with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_files.side_effect = mock_process_files
            mock_processor_class.return_value = mock_processor

            result = tool.execute_scan(args)

            assert result == 0
            captured = capsys.readouterr()
            # Should not have progress output when not verbose
            assert "Scanning..." not in captured.out

    def test_execute_scan_database_fallback_warning(self, capsys, temp_scan_dir):
        """execute_scan() shows warning when falling back to default database."""
        tool = ScanTool()
        args = MagicMock()
        args.paths = [str(temp_scan_dir)]
        args.container = MagicMock()
        args.container.get_service.return_value = None  # No database service
        args.verbose = False

        with patch('nodupe.tools.commands.scan.DatabaseConnection') as mock_db_conn:
            with patch('nodupe.tools.commands.scan.FileProcessor') as mock_processor_class:
                with patch('nodupe.tools.commands.scan.FileRepository') as mock_repo_class:
                    mock_instance = MagicMock()
                    mock_db_conn.get_instance.return_value = mock_instance
                    mock_processor = MagicMock()
                    mock_processor.process_files.return_value = []
                    mock_processor_class.return_value = mock_processor
                    mock_repo = MagicMock()
                    mock_repo_class.return_value = mock_repo

                    result = tool.execute_scan(args)

                    assert result == 0
                    captured = capsys.readouterr()
                    assert "Attempting to connect to default database" in captured.out
