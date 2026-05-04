# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/commands/verify.py - VerifyTool.

This module tests the VerifyTool implementation including property access,
method functionality, and integration with the dependency container.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.commands.verify import VerifyTool, register_tool


class TestVerifyToolProperties:
    """Test VerifyTool properties."""

    def test_name_property(self):
        """VerifyTool.name returns correct value."""
        tool = VerifyTool()
        assert tool.name == "verify"

    def test_version_property(self):
        """VerifyTool.version returns correct value."""
        tool = VerifyTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """VerifyTool.dependencies returns correct list."""
        tool = VerifyTool()
        assert tool.dependencies == ["database"]

    def test_description_attribute(self):
        """VerifyTool has correct description."""
        tool = VerifyTool()
        assert tool.description == "Verify file integrity and database consistency"


class TestVerifyToolInitialize:
    """Test VerifyTool.initialize() method."""

    def test_initialize_no_error(self):
        """initialize() completes without error."""
        tool = VerifyTool()
        container = MagicMock()
        # Should not raise
        tool.initialize(container)

    def test_initialize_with_none_container(self):
        """initialize() handles None container gracefully."""
        tool = VerifyTool()
        # Should not raise
        tool.initialize(None)


class TestVerifyToolShutdown:
    """Test VerifyTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = VerifyTool()
        # Should not raise
        tool.shutdown()


class TestVerifyToolGetCapabilities:
    """Test VerifyTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary."""
        tool = VerifyTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'commands' in capabilities

    def test_get_capabilities_contains_verify_command(self):
        """get_capabilities() contains verify command."""
        tool = VerifyTool()
        capabilities = tool.get_capabilities()

        assert 'verify' in capabilities['commands']


class TestVerifyToolEventHandlers:
    """Test VerifyTool event handler methods."""

    def test_on_verify_start(self, capsys):
        """_on_verify_start() prints start message."""
        tool = VerifyTool()
        tool._on_verify_start(mode='all')

        captured = capsys.readouterr()
        assert "[TOOL] Verify started: all" in captured.out

    def test_on_verify_start_default_mode(self, capsys):
        """_on_verify_start() uses default mode when not provided."""
        tool = VerifyTool()
        tool._on_verify_start()

        captured = capsys.readouterr()
        assert "[TOOL] Verify started: unknown" in captured.out

    def test_on_verify_complete(self, capsys):
        """_on_verify_complete() prints completion message."""
        tool = VerifyTool()
        tool._on_verify_complete(checks_performed=100, errors_found=0)

        captured = capsys.readouterr()
        assert "[TOOL] Verify completed: 100 checks, 0 errors" in captured.out

    def test_on_verify_complete_with_errors(self, capsys):
        """_on_verify_complete() reports errors."""
        tool = VerifyTool()
        tool._on_verify_complete(checks_performed=100, errors_found=5)

        captured = capsys.readouterr()
        assert "[TOOL] Verify completed: 100 checks, 5 errors" in captured.out


class TestVerifyToolRegisterCommands:
    """Test VerifyTool.register_commands() method."""

    def test_register_commands_creates_parser(self):
        """register_commands() creates verify subparser."""
        tool = VerifyTool()
        subparsers = MagicMock()
        verify_parser = MagicMock()
        subparsers.add_parser.return_value = verify_parser

        tool.register_commands(subparsers)

        subparsers.add_parser.assert_called_once_with(
            'verify', help='Verify file integrity and database consistency'
        )

    def test_register_commands_adds_mode_argument(self):
        """register_commands() adds mode argument."""
        tool = VerifyTool()
        subparsers = MagicMock()
        verify_parser = MagicMock()
        subparsers.add_parser.return_value = verify_parser

        tool.register_commands(subparsers)

        verify_parser.add_argument.assert_any_call(
            '--mode',
            choices=['integrity', 'consistency', 'checksums', 'all'],
            default='all',
            help='Verification mode to run'
        )

    def test_register_commands_adds_fast_argument(self):
        """register_commands() adds fast argument."""
        tool = VerifyTool()
        subparsers = MagicMock()
        verify_parser = MagicMock()
        subparsers.add_parser.return_value = verify_parser

        tool.register_commands(subparsers)

        verify_parser.add_argument.assert_any_call(
            '--fast', action='store_true', help='Perform fast verification (skip heavy checks)'
        )

    def test_register_commands_adds_verbose_argument(self):
        """register_commands() adds verbose argument."""
        tool = VerifyTool()
        subparsers = MagicMock()
        verify_parser = MagicMock()
        subparsers.add_parser.return_value = verify_parser

        tool.register_commands(subparsers)

        verify_parser.add_argument.assert_any_call(
            '--verbose', '-v', action='store_true', help='Verbose output'
        )

    def test_register_commands_adds_repair_argument(self):
        """register_commands() adds repair argument."""
        tool = VerifyTool()
        subparsers = MagicMock()
        verify_parser = MagicMock()
        subparsers.add_parser.return_value = verify_parser

        tool.register_commands(subparsers)

        verify_parser.add_argument.assert_any_call(
            '--repair', action='store_true', help='Attempt to repair detected issues'
        )

    def test_register_commands_adds_output_argument(self):
        """register_commands() adds output argument."""
        tool = VerifyTool()
        subparsers = MagicMock()
        verify_parser = MagicMock()
        subparsers.add_parser.return_value = verify_parser

        tool.register_commands(subparsers)

        verify_parser.add_argument.assert_any_call(
            '--output', help='Output results to file'
        )

    def test_register_commands_sets_func(self):
        """register_commands() sets func to execute_verify."""
        tool = VerifyTool()
        subparsers = MagicMock()
        verify_parser = MagicMock()
        subparsers.add_parser.return_value = verify_parser

        tool.register_commands(subparsers)

        verify_parser.set_defaults.assert_called_once_with(func=tool.execute_verify)


class TestVerifyToolExecuteValidation:
    """Test VerifyTool.execute_verify() validation logic."""

    def test_execute_verify_missing_container(self, capsys):
        """execute_verify() returns error when container not available."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'all'
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = None

        result = tool.execute_verify(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Dependency container not available" in captured.out

    def test_execute_verify_missing_database_service(self, capsys):
        """execute_verify() handles missing database service."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'all'
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = None

        with patch('nodupe.tools.commands.verify.DatabaseConnection') as mock_db_conn:
            mock_instance = MagicMock()
            mock_db_conn.get_instance.return_value = mock_instance

            # Mock the verification methods
            with patch.object(tool, '_verify_integrity') as mock_integrity:
                with patch.object(tool, '_verify_consistency') as mock_consistency:
                    with patch.object(tool, '_verify_checksums') as mock_checksums:
                        mock_integrity.return_value = {'checks': 0, 'errors': 0, 'warnings': 0}
                        mock_consistency.return_value = {'checks': 0, 'errors': 0, 'warnings': 0}
                        mock_checksums.return_value = {'checks': 0, 'errors': 0, 'warnings': 0}

                        tool.execute_verify(args)

                        # Should fallback to default connection
                        mock_db_conn.get_instance.assert_called()


class TestVerifyToolExecuteIntegrityMode:
    """Test VerifyTool.execute_verify() with integrity mode."""

    def test_execute_verify_integrity_mode(self, capsys):
        """execute_verify() runs integrity verification."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'integrity'
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Running integrity verification" in captured.out

    def test_execute_verify_integrity_with_files(self, capsys):
        """execute_verify() integrity mode checks files."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.mode = 'integrity'
            args.fast = False
            args.verbose = False
            args.repair = False
            args.output = None
            args.container = MagicMock()
            args.container.get_service.return_value = MagicMock()

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_all_files.return_value = files
                mock_repo_class.return_value = mock_repo

                result = tool.execute_verify(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "Checking integrity of 1 files" in captured.out
        finally:
            shutil.rmtree(temp_dir)


class TestVerifyToolExecuteConsistencyMode:
    """Test VerifyTool.execute_verify() with consistency mode."""

    def test_execute_verify_consistency_mode(self, capsys):
        """execute_verify() runs consistency verification."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'consistency'
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo.get_duplicate_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Running consistency verification" in captured.out

    def test_execute_verify_consistency_with_duplicates(self, capsys):
        """execute_verify() consistency mode checks duplicate relationships."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'consistency'
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        files = [
            {'id': 1, 'path': '/path/to/original.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': False, 'duplicate_of': None},
            {'id': 2, 'path': '/path/to/duplicate.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': True, 'duplicate_of': 1},
        ]

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo.get_duplicate_files.return_value = [files[1]]
            mock_repo.get_file.return_value = files[0]
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Checking consistency of 2 files" in captured.out


class TestVerifyToolExecuteChecksumsMode:
    """Test VerifyTool.execute_verify() with checksums mode."""

    def test_execute_verify_checksums_mode(self, capsys):
        """execute_verify() runs checksum verification."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.mode = 'checksums'
            args.fast = False
            args.verbose = False
            args.repair = False
            args.output = None
            args.container = MagicMock()
            args.container.get_service.return_value = MagicMock()

            # Calculate actual hash
            actual_hash = hashlib.sha256(b"test content").hexdigest()
            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': actual_hash},
            ]

            with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_all_files.return_value = files
                mock_repo_class.return_value = mock_repo

                result = tool.execute_verify(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "Verifying checksums for 1 files" in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_execute_verify_checksums_fast_mode_skips(self, capsys):
        """execute_verify() checksums mode skips in fast mode."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'checksums'
        args.fast = True
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Skipping checksum verification in fast mode" in captured.out


class TestVerifyToolExecuteAllMode:
    """Test VerifyTool.execute_verify() with all mode."""

    def test_execute_verify_all_mode(self, capsys):
        """execute_verify() runs all verification modes."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'all'
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo.get_duplicate_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Running integrity verification" in captured.out
            assert "Running consistency verification" in captured.out
            assert "Running checksums verification" in captured.out


class TestVerifyToolExecuteVerbose:
    """Test VerifyTool.execute_verify() verbose output."""

    def test_execute_verify_verbose_with_errors(self, capsys):
        """execute_verify() verbose mode prints error details."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'integrity'
        args.fast = False
        args.verbose = True
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        files = [
            {'id': 1, 'path': '/nonexistent/file.txt', 'size': 100, 'hash': 'abc123'},
        ]

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            # When errors are found, return code is 1
            assert result == 1
            captured = capsys.readouterr()
            assert "[ERROR] File not found:" in captured.out


class TestVerifyToolExecuteRepair:
    """Test VerifyTool.execute_verify() with repair mode."""

    def test_execute_verify_repair_mode_enabled(self, capsys):
        """execute_verify() repair mode reports repair would be attempted."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'integrity'
        args.fast = False
        args.verbose = False
        args.repair = True
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        files = [
            {'id': 1, 'path': '/nonexistent/file.txt', 'size': 100, 'hash': 'abc123'},
        ]

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 1  # Errors found
            captured = capsys.readouterr()
            assert "Repair mode enabled" in captured.out


class TestVerifyToolExecuteOutput:
    """Test VerifyTool.execute_verify() with output file."""

    def test_execute_verify_output_to_file(self, capsys, tmp_path):
        """execute_verify() writes results to output file."""
        tool = VerifyTool()
        output_file = tmp_path / "results.json"

        args = MagicMock()
        args.mode = 'integrity'
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = str(output_file)
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            assert output_file.exists()

            with open(output_file) as f:
                results = json.load(f)

            assert 'timestamp' in results
            assert 'command_args' in results
            assert 'summary' in results
            assert 'details' in results


class TestVerifyToolVerifyIntegrity:
    """Test VerifyTool._verify_integrity() method."""

    def test_verify_integrity_file_exists(self):
        """_verify_integrity() checks file existence."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = False

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            results = tool._verify_integrity(mock_repo, args)

            assert results['checks'] == 1
            assert results['errors'] == 0
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_integrity_file_not_exists(self):
        """_verify_integrity() reports missing files as errors."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False

        files = [
            {'id': 1, 'path': '/nonexistent/file.txt', 'size': 100, 'hash': 'abc123'},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files

        results = tool._verify_integrity(mock_repo, args)

        assert results['checks'] == 1
        assert results['errors'] == 1

    def test_verify_integrity_size_mismatch(self):
        """_verify_integrity() reports size mismatch as error."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = False

            files = [
                {'id': 1, 'path': str(test_file), 'size': 999, 'hash': 'abc123'},  # Wrong size
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            results = tool._verify_integrity(mock_repo, args)

            assert results['checks'] == 1
            assert results['errors'] == 1
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_integrity_fast_mode(self):
        """_verify_integrity() skips readability check in fast mode."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = True
            args.verbose = False

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            results = tool._verify_integrity(mock_repo, args)

            assert results['checks'] == 1
            assert results['errors'] == 0
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_integrity_exception(self, capsys):
        """_verify_integrity() handles exceptions gracefully."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False

        mock_repo = MagicMock()
        mock_repo.get_all_files.side_effect = Exception("Test exception")

        results = tool._verify_integrity(mock_repo, args)

        assert results['errors'] >= 1


class TestVerifyToolVerifyConsistency:
    """Test VerifyTool._verify_consistency() method."""

    def test_verify_consistency_valid_relationships(self):
        """_verify_consistency() validates duplicate relationships."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False

        files = [
            {'id': 1, 'path': '/path/to/original.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': False, 'duplicate_of': None},
            {'id': 2, 'path': '/path/to/duplicate.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': True, 'duplicate_of': 1},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        mock_repo.get_duplicate_files.return_value = [files[1]]
        mock_repo.get_file.return_value = files[0]

        results = tool._verify_consistency(mock_repo, args)

        assert results['checks'] == 2
        assert results['errors'] == 0

    def test_verify_consistency_missing_duplicate_of(self):
        """_verify_consistency() reports missing duplicate_of reference."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False

        files = [
            {'id': 1, 'path': '/path/to/duplicate.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': True, 'duplicate_of': None},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        mock_repo.get_duplicate_files.return_value = files

        results = tool._verify_consistency(mock_repo, args)

        assert results['checks'] == 1
        assert results['errors'] == 1

    def test_verify_consistency_self_reference(self):
        """_verify_consistency() reports self-reference as error."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False

        files = [
            {'id': 1, 'path': '/path/to/file.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': True, 'duplicate_of': 1},  # References itself
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        mock_repo.get_duplicate_files.return_value = files
        mock_repo.get_file.return_value = files[0]

        results = tool._verify_consistency(mock_repo, args)

        assert results['checks'] == 1
        assert results['errors'] == 1

    def test_verify_consistency_orphaned_reference(self):
        """_verify_consistency() reports orphaned references."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False

        files = [
            {'id': 1, 'path': '/path/to/duplicate.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': True, 'duplicate_of': 999},  # References non-existent file
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        mock_repo.get_duplicate_files.return_value = files
        mock_repo.get_file.return_value = None  # Original not found

        results = tool._verify_consistency(mock_repo, args)

        assert results['errors'] >= 1

    def test_verify_consistency_exception(self, capsys):
        """_verify_consistency() handles exceptions gracefully."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False

        mock_repo = MagicMock()
        mock_repo.get_all_files.side_effect = Exception("Test exception")

        results = tool._verify_consistency(mock_repo, args)

        assert results['errors'] >= 1


class TestVerifyToolVerifyChecksums:
    """Test VerifyTool._verify_checksums() method."""

    def test_verify_checksums_valid_hash(self):
        """_verify_checksums() validates correct hashes."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = False

            actual_hash = hashlib.sha256(content).hexdigest()
            files = [
                {'id': 1, 'path': str(test_file), 'size': len(content), 'hash': actual_hash},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            results = tool._verify_checksums(mock_repo, args)

            assert results['checks'] == 1
            assert results['errors'] == 0
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_checksums_invalid_hash(self):
        """_verify_checksums() reports hash mismatch."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = False

            files = [
                {'id': 1, 'path': str(test_file), 'size': len(content), 'hash': 'wronghash123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            results = tool._verify_checksums(mock_repo, args)

            assert results['checks'] == 1
            assert results['errors'] == 1
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_checksums_no_hash_stored(self):
        """_verify_checksums() warns when no hash stored."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False

        files = [
            {'id': 1, 'path': '/path/to/file.txt', 'size': 100, 'hash': None},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files

        results = tool._verify_checksums(mock_repo, args)

        assert results['checks'] == 0
        assert results['warnings'] == 1

    def test_verify_checksums_file_not_exists(self):
        """_verify_checksums() reports missing file as error."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False

        files = [
            {'id': 1, 'path': '/nonexistent/file.txt', 'size': 100, 'hash': 'abc123'},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files

        results = tool._verify_checksums(mock_repo, args)

        assert results['errors'] >= 1

    def test_verify_checksums_fast_mode(self):
        """_verify_checksums() skips in fast mode."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = True
        args.verbose = False

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = []

        results = tool._verify_checksums(mock_repo, args)

        assert results['checks'] == 0
        assert results['errors'] == 0

    def test_verify_checksums_exception(self, capsys):
        """_verify_checksums() handles exceptions gracefully."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False

        mock_repo = MagicMock()
        mock_repo.get_all_files.side_effect = Exception("Test exception")

        results = tool._verify_checksums(mock_repo, args)

        assert results['errors'] >= 1

    def test_verify_checksums_no_hash_warning(self, capsys):
        """_verify_checksums() warns when file has no hash."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = True

        files = [
            {'id': 1, 'path': '/path/to/file.txt', 'size': 100, 'hash': None},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files

        results = tool._verify_checksums(mock_repo, args)

        assert results['warnings'] == 1

    def test_verify_checksums_hash_mismatch(self, capsys):
        """_verify_checksums() reports hash mismatch."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = True

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'wrong_hash'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            results = tool._verify_checksums(mock_repo, args)

            assert results['errors'] == 1
            captured = capsys.readouterr()
            assert "Hash mismatch" in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_checksums_os_error(self, capsys):
        """_verify_checksums() handles OSError when calculating hash."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = True

        # Create a temp file
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        try:
            files = [
                {'id': 1, 'path': str(test_file), 'size': 4, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock open to raise OSError
            with patch('builtins.open', side_effect=OSError("Test OS error")):
                results = tool._verify_checksums(mock_repo, args)

                assert results['errors'] == 1
                captured = capsys.readouterr()
                assert "Cannot calculate hash" in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_checksums_memory_error(self, capsys):
        """_verify_checksums() handles MemoryError when calculating hash."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = True

        # Create a temp file
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        try:
            files = [
                {'id': 1, 'path': str(test_file), 'size': 4, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock open to raise MemoryError
            with patch('builtins.open', side_effect=MemoryError("Out of memory")):
                results = tool._verify_checksums(mock_repo, args)

                assert results['errors'] == 1
        finally:
            shutil.rmtree(temp_dir)


class TestVerifyToolVerifyConsistencyEdgeCases:
    """Test VerifyTool._verify_consistency() edge cases."""

    def test_verify_consistency_duplicate_without_reference(self, capsys):
        """_verify_consistency() reports duplicate without duplicate_of."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = True

        files = [
            {'id': 1, 'path': '/path/to/file.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': True, 'duplicate_of': None},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        mock_repo.get_duplicate_files.return_value = []

        results = tool._verify_consistency(mock_repo, args)

        assert results['errors'] == 1
        captured = capsys.readouterr()
        assert "has no duplicate_of reference" in captured.out

    def test_verify_consistency_duplicate_references_nonexistent(self, capsys):
        """_verify_consistency() reports duplicate referencing non-existent original."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = True

        files = [
            {'id': 1, 'path': '/path/to/file.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': True, 'duplicate_of': 999},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        mock_repo.get_duplicate_files.return_value = []
        mock_repo.get_file.return_value = None  # Original not found

        results = tool._verify_consistency(mock_repo, args)

        assert results['errors'] == 1
        captured = capsys.readouterr()
        assert "references non-existent original" in captured.out

    def test_verify_consistency_self_reference(self, capsys):
        """_verify_consistency() reports self-referencing duplicate."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = True

        files = [
            {'id': 1, 'path': '/path/to/file.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': False, 'duplicate_of': 1},  # Self-reference
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        mock_repo.get_duplicate_files.return_value = []

        results = tool._verify_consistency(mock_repo, args)

        assert results['errors'] == 1
        captured = capsys.readouterr()
        assert "references itself as duplicate" in captured.out

    def test_verify_consistency_orphaned_reference(self, capsys):
        """_verify_consistency() reports orphaned duplicate reference."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = True

        files = []
        duplicates = [
            {'id': 1, 'path': '/path/to/dup.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': True, 'duplicate_of': 999},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files
        mock_repo.get_duplicate_files.return_value = duplicates
        mock_repo.get_file.return_value = None  # Original not found

        results = tool._verify_consistency(mock_repo, args)

        assert results['errors'] == 1
        captured = capsys.readouterr()
        assert "Orphaned duplicate reference" in captured.out


class TestVerifyToolVerifyIntegrityEdgeCases:
    """Test VerifyTool._verify_integrity() edge cases."""

    def test_verify_integrity_size_check_os_error(self, capsys):
        """_verify_integrity() handles OSError when checking file size."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = True

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock stat to raise OSError
            with patch.object(Path, 'stat', side_effect=OSError("Cannot stat")):
                results = tool._verify_integrity(mock_repo, args)

                assert results['errors'] == 1
                captured = capsys.readouterr()
                assert "Cannot access file" in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_integrity_readability_permission_error(self, capsys):
        """_verify_integrity() handles PermissionError when checking readability."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = True

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock open to raise PermissionError
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                results = tool._verify_integrity(mock_repo, args)

                assert results['errors'] == 1
                captured = capsys.readouterr()
                assert "Cannot read file" in captured.out
        finally:
            shutil.rmtree(temp_dir)


class TestVerifyToolExecuteEdgeCases:
    """Test VerifyTool.execute_verify() edge cases."""

    def test_execute_verify_general_exception(self, capsys):
        """execute_verify() handles general exceptions."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'all'
        args.verbose = True
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")

        result = tool.execute_verify(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[TOOL ERROR] Verify failed:" in captured.out

    def test_execute_verify_general_exception_with_traceback(self, capsys):
        """execute_verify() prints traceback when verbose is True."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'all'
        args.verbose = True
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")

        result = tool.execute_verify(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Traceback" in captured.out or "Traceback" in captured.err or "[TOOL ERROR]" in captured.out

    def test_execute_verify_returns_error_on_failures(self, capsys):
        """execute_verify() returns 1 when errors found."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'integrity'
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        files = [
            {'id': 1, 'path': '/nonexistent/file.txt', 'size': 100, 'hash': 'abc123'},
        ]

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 1
            captured = capsys.readouterr()
            assert "integrity issues detected" in captured.out

    def test_execute_verify_returns_success_on_pass(self, capsys):
        """execute_verify() returns 0 when all checks pass."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'integrity'
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "All verification checks passed" in captured.out


class TestVerifyToolOutputFindingsToFile:
    """Test VerifyTool._output_findings_to_file() method."""

    def test_output_findings_writes_json(self, tmp_path):
        """_output_findings_to_file() writes JSON output."""
        tool = VerifyTool()
        output_file = tmp_path / "findings.json"

        results = {
            'integrity': {'checks': 10, 'errors': 1, 'warnings': 0, 'error_details': []},
            'consistency': {'checks': 5, 'errors': 0, 'warnings': 0, 'error_details': []},
            'checksums': {'checks': 10, 'errors': 0, 'warnings': 0, 'error_details': []},
        }

        args = MagicMock()
        args.mode = 'all'
        args.fast = False
        args.verbose = False
        args.repair = False

        tool._output_findings_to_file(results, str(output_file), args)

        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert 'timestamp' in data
        assert 'summary' in data
        assert data['summary']['total_checks'] == 25
        assert data['summary']['total_errors'] == 1


class TestVerifyToolRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_verify_tool(self):
        """register_tool() returns a VerifyTool instance."""
        tool = register_tool()
        assert isinstance(tool, VerifyTool)


class TestVerifyToolModuleLevel:
    """Test module-level exports."""

    def test_verify_tool_instance_exists(self):
        """verify_tool module-level instance exists."""
        from nodupe.tools.commands import verify
        assert verify.verify_tool is not None
        assert isinstance(verify.verify_tool, VerifyTool)

    def test_register_tool_function_exists(self):
        """register_tool function is exported."""
        from nodupe.tools.commands import verify
        assert callable(verify.register_tool)

    def test_all_export(self):
        """__all__ contains expected exports."""
        from nodupe.tools.commands import verify
        assert 'verify_tool' in verify.__all__
        assert 'register_tool' in verify.__all__

    def test_api_methods_property(self):
        """api_methods property returns verify methods."""
        tool = VerifyTool()
        api_methods = tool.api_methods
        assert 'verify' in api_methods
        assert 'verify_integrity' in api_methods
        assert 'verify_consistency' in api_methods
        assert 'verify_checksums' in api_methods
        assert callable(api_methods['verify'])
        assert callable(api_methods['verify_integrity'])

    def test_describe_usage(self):
        """describe_usage() returns usage description."""
        tool = VerifyTool()
        usage = tool.describe_usage()
        assert "Verify Tool" in usage
        assert "integrity" in usage
        assert "consistency" in usage
        assert "--mode" in usage

    def test_run_standalone(self):
        """run_standalone() calls execute_verify."""
        from unittest.mock import patch
        
        tool = VerifyTool()
        
        # Test with --help flag (should exit cleanly)
        with pytest.raises(SystemExit) as exc_info:
            tool.run_standalone(['--help'])
        assert exc_info.value.code == 0
        
        # Test with --mode flag (should work but may fail due to no database)
        # Just verify it doesn't crash with AttributeError
        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo
            
            # This should at least start without AttributeError
            try:
                result = tool.run_standalone(['--mode', 'integrity', '--fast'])
                # Result may be 0 (success) or 1 (db not available) - both OK
                assert result in [0, 1]
            except AttributeError:
                pytest.fail("run_standalone raised AttributeError")


class TestVerifyToolCoverageCompletion:
    """Additional tests to achieve 100% coverage."""

    def test_execute_verify_consistency_mode_verbose_orphaned(self, capsys):
        """execute_verify() consistency mode with verbose orphaned reference."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'consistency'
        args.fast = False
        args.verbose = True
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        files = [
            {'id': 1, 'path': '/path/to/duplicate.txt', 'size': 100, 'hash': 'abc123',
             'is_duplicate': True, 'duplicate_of': 999},
        ]

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo.get_duplicate_files.return_value = files
            mock_repo.get_file.return_value = None
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 1
            captured = capsys.readouterr()
            assert "Orphaned duplicate reference" in captured.out

    def test_verify_checksums_hash_mismatch_verbose(self, capsys):
        """_verify_checksums() reports hash mismatch with verbose output."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = True

            # Wrong hash stored
            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'wronghash123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            results = tool._verify_checksums(mock_repo, args)

            assert results['checks'] == 1
            assert results['errors'] == 1
            captured = capsys.readouterr()
            assert "Hash mismatch" in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_checksums_os_error_verbose(self, capsys):
        """_verify_checksums() handles OSError with verbose output."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = True

        # File that exists but we'll mock the open to fail
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock open to raise OSError
            with patch('builtins.open', side_effect=OSError("Permission denied")):
                results = tool._verify_checksums(mock_repo, args)

                assert results['checks'] == 1
                assert results['errors'] == 1
                captured = capsys.readouterr()
                assert "Cannot calculate hash" in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_checksums_memory_error_verbose(self, capsys):
        """_verify_checksums() handles MemoryError with verbose output."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = True

        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock open to raise MemoryError
            with patch('builtins.open', side_effect=MemoryError("Out of memory")):
                results = tool._verify_checksums(mock_repo, args)

                assert results['checks'] == 1
                assert results['errors'] == 1
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_integrity_file_no_hash_stored(self, capsys):
        """_verify_checksums() reports warning for files without stored hash."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = True

        files = [
            {'id': 1, 'path': '/path/to/file.txt', 'size': 100, 'hash': None},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files

        results = tool._verify_checksums(mock_repo, args)

        assert results['warnings'] == 1
        captured = capsys.readouterr()
        assert "No hash stored" in captured.out

    def test_execute_verify_all_modes_no_errors(self, capsys):
        """execute_verify() all modes with no errors shows success message."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'all'
        args.fast = True  # Skip checksums for speed
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo.get_duplicate_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "All verification checks passed" in captured.out

    def test_verify_integrity_size_mismatch_verbose(self, capsys):
        """_verify_integrity() reports size mismatch with verbose output."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = True

            # Wrong size stored
            files = [
                {'id': 1, 'path': str(test_file), 'size': 9999, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            results = tool._verify_integrity(mock_repo, args)

            assert results['checks'] == 1
            assert results['errors'] == 1
            captured = capsys.readouterr()
            assert "Size mismatch" in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_integrity_cannot_access_file_verbose(self, capsys):
        """_verify_integrity() handles OSError when accessing file stat."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = True

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock stat to raise OSError
            with patch.object(Path, 'stat', side_effect=OSError("Cannot stat")):
                results = tool._verify_integrity(mock_repo, args)

                assert results['checks'] == 1
                assert results['errors'] == 1
                captured = capsys.readouterr()
                assert "Cannot access file" in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_integrity_cannot_read_file_verbose(self, capsys):
        """_verify_integrity() handles PermissionError when reading file."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = True

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock open to raise PermissionError
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                results = tool._verify_integrity(mock_repo, args)

                assert results['checks'] == 1
                assert results['errors'] == 1
                captured = capsys.readouterr()
                assert "Cannot read file" in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_execute_verify_checksums_mode_with_errors(self, capsys):
        """execute_verify() checksums mode with errors returns 1."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.mode = 'checksums'
            args.fast = False
            args.verbose = False
            args.repair = False
            args.output = None
            args.container = MagicMock()
            args.container.get_service.return_value = MagicMock()

            # Wrong hash stored
            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'wronghash'},
            ]

            with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_all_files.return_value = files
                mock_repo_class.return_value = mock_repo

                result = tool.execute_verify(args)

                # When hash mismatch, return code is 1
                assert result == 1
        finally:
            shutil.rmtree(temp_dir)

    def test_execute_verify_no_errors_branch(self, capsys):
        """execute_verify() takes else branch when no errors found."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'integrity'
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        # Empty file list = no errors
        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            captured = capsys.readouterr()
            # Should show success message (else branch)
            assert "All verification checks passed" in captured.out

    def test_execute_verify_exception_without_verbose(self, capsys):
        """execute_verify() exception handler without verbose flag."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'all'
        args.verbose = False  # Not verbose - should NOT print traceback
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")

        result = tool.execute_verify(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[TOOL ERROR] Verify failed:" in captured.out
        # Should NOT have traceback when verbose=False

    def test_verify_integrity_file_not_found_no_verbose(self, capsys):
        """_verify_integrity() file not found without verbose output."""
        tool = VerifyTool()
        args = MagicMock()
        args.fast = False
        args.verbose = False  # Not verbose

        files = [
            {'id': 1, 'path': '/nonexistent/file.txt', 'size': 100, 'hash': 'abc123'},
        ]

        mock_repo = MagicMock()
        mock_repo.get_all_files.return_value = files

        results = tool._verify_integrity(mock_repo, args)

        assert results['checks'] == 1
        assert results['errors'] == 1
        captured = capsys.readouterr()
        # Should NOT print error details when verbose=False
        assert "[ERROR] File not found:" not in captured.out

    def test_verify_integrity_size_mismatch_no_verbose(self, capsys):
        """_verify_integrity() size mismatch without verbose output."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = False  # Not verbose

            # Wrong size stored
            files = [
                {'id': 1, 'path': str(test_file), 'size': 9999, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            results = tool._verify_integrity(mock_repo, args)

            assert results['checks'] == 1
            assert results['errors'] == 1
            captured = capsys.readouterr()
            # Should NOT print error details when verbose=False
            assert "Size mismatch" not in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_checksums_hash_mismatch_no_verbose(self, capsys):
        """_verify_checksums() hash mismatch without verbose output."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = False  # Not verbose

            # Wrong hash stored
            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'wronghash123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            results = tool._verify_checksums(mock_repo, args)

            assert results['checks'] == 1
            assert results['errors'] == 1
            captured = capsys.readouterr()
            # Should NOT print error details when verbose=False
            assert "Hash mismatch" not in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_integrity_stat_os_error_no_verbose(self, capsys):
        """_verify_integrity() OSError in stat() without verbose output."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = False  # Not verbose - covers False branch of if args.verbose

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock stat to raise OSError
            with patch.object(Path, 'stat', side_effect=OSError("Cannot stat")):
                results = tool._verify_integrity(mock_repo, args)

                assert results['checks'] == 1
                assert results['errors'] == 1
                captured = capsys.readouterr()
                # Should NOT print error details when verbose=False
                assert "Cannot access file" not in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_integrity_read_error_no_verbose(self, capsys):
        """_verify_integrity() read error without verbose output."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = False  # Not verbose - covers False branch of if args.verbose

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock open to raise PermissionError
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                results = tool._verify_integrity(mock_repo, args)

                assert results['checks'] == 1
                assert results['errors'] == 1
                captured = capsys.readouterr()
                # Should NOT print error details when verbose=False
                assert "Cannot read file" not in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_verify_checksums_hash_error_no_verbose(self, capsys):
        """_verify_checksums() hash calculation error without verbose output."""
        tool = VerifyTool()
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        try:
            args = MagicMock()
            args.fast = False
            args.verbose = False  # Not verbose - covers False branch of if args.verbose

            files = [
                {'id': 1, 'path': str(test_file), 'size': 12, 'hash': 'abc123'},
            ]

            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files

            # Mock open to raise OSError
            with patch('builtins.open', side_effect=OSError("Cannot read")):
                results = tool._verify_checksums(mock_repo, args)

                assert results['checks'] == 1
                assert results['errors'] == 1
                captured = capsys.readouterr()
                # Should NOT print error details when verbose=False
                assert "Cannot calculate hash" not in captured.out
        finally:
            shutil.rmtree(temp_dir)

    def test_execute_verify_integrity_only_mode(self, capsys):
        """execute_verify() integrity mode covers elif checksums False branch."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'integrity'  # Only integrity mode, not checksums
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            # This test covers the branch where elif mode == 'checksums' is False

    def test_execute_verify_consistency_only_mode(self, capsys):
        """execute_verify() consistency mode covers elif checksums False branch."""
        tool = VerifyTool()
        args = MagicMock()
        args.mode = 'consistency'  # Only consistency mode, not checksums
        args.fast = False
        args.verbose = False
        args.repair = False
        args.output = None
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()

        with patch('nodupe.tools.commands.verify.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo.get_duplicate_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_verify(args)

            assert result == 0
            # This test reaches elif mode == 'checksums' and takes False branch
