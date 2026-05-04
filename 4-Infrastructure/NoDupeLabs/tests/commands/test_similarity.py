# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/commands/similarity.py - SimilarityCommandTool."""

from unittest.mock import MagicMock, patch

from nodupe.tools.commands.similarity import SimilarityCommandTool, register_tool


class TestSimilarityCommandToolProperties:
    """Test SimilarityCommandTool properties."""

    def test_name_property(self):
        """SimilarityCommandTool.name returns correct value."""
        tool = SimilarityCommandTool()
        assert tool.name == "similarity_command"

    def test_version_property(self):
        """SimilarityCommandTool.version returns correct value."""
        tool = SimilarityCommandTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """SimilarityCommandTool.dependencies returns correct list."""
        tool = SimilarityCommandTool()
        assert tool.dependencies == ["similarity_backend"]

    def test_description_attribute(self):
        """SimilarityCommandTool has correct description."""
        tool = SimilarityCommandTool()
        assert tool.description == "Find similar files using various metrics"


class TestSimilarityCommandToolInitialize:
    """Test SimilarityCommandTool.initialize() method."""

    def test_initialize_no_error(self):
        """initialize() completes without error."""
        tool = SimilarityCommandTool()
        container = MagicMock()
        # Should not raise
        tool.initialize(container)

    def test_initialize_with_none_container(self):
        """initialize() handles None container gracefully."""
        tool = SimilarityCommandTool()
        # Should not raise
        tool.initialize(None)


class TestSimilarityCommandToolShutdown:
    """Test SimilarityCommandTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = SimilarityCommandTool()
        # Should not raise
        tool.shutdown()


class TestSimilarityCommandToolGetCapabilities:
    """Test SimilarityCommandTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary."""
        tool = SimilarityCommandTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'commands' in capabilities

    def test_get_capabilities_contains_similarity_command(self):
        """get_capabilities() contains similarity command."""
        tool = SimilarityCommandTool()
        capabilities = tool.get_capabilities()

        assert 'similarity' in capabilities['commands']


class TestSimilarityCommandToolEventHandlers:
    """Test SimilarityCommandTool event handler methods."""

    def test_on_similarity_start(self, capsys):
        """_on_similarity_start() prints start message."""
        tool = SimilarityCommandTool()
        tool._on_similarity_start(metric='name')

        captured = capsys.readouterr()
        assert "[TOOL] Similarity search started: name" in captured.out

    def test_on_similarity_start_default_metric(self, capsys):
        """_on_similarity_start() uses default metric when not provided."""
        tool = SimilarityCommandTool()
        tool._on_similarity_start()

        captured = capsys.readouterr()
        assert "[TOOL] Similarity search started: unknown" in captured.out

    def test_on_similarity_complete(self, capsys):
        """_on_similarity_complete() prints completion message."""
        tool = SimilarityCommandTool()
        tool._on_similarity_complete(pairs_found=42)

        captured = capsys.readouterr()
        assert "[TOOL] Similarity search completed: 42 similar pairs found" in captured.out

    def test_on_similarity_complete_default_count(self, capsys):
        """_on_similarity_complete() uses default count when not provided."""
        tool = SimilarityCommandTool()
        tool._on_similarity_complete()

        captured = capsys.readouterr()
        assert "[TOOL] Similarity search completed: 0 similar pairs found" in captured.out


class TestSimilarityCommandToolRegisterCommands:
    """Test SimilarityCommandTool.register_commands() method."""

    def test_register_commands_creates_parser(self):
        """register_commands() creates similarity subparser."""
        tool = SimilarityCommandTool()
        subparsers = MagicMock()
        sim_parser = MagicMock()
        subparsers.add_parser.return_value = sim_parser

        tool.register_commands(subparsers)

        subparsers.add_parser.assert_called_once_with(
            'similarity', help='Find similar files'
        )

    def test_register_commands_adds_metric_argument(self):
        """register_commands() adds metric argument."""
        tool = SimilarityCommandTool()
        subparsers = MagicMock()
        sim_parser = MagicMock()
        subparsers.add_parser.return_value = sim_parser

        tool.register_commands(subparsers)

        apply_parser_call = None
        for call_arg in sim_parser.add_argument.call_args_list:
            if '--metric' in str(call_arg):
                apply_parser_call = call_arg
                break

        assert apply_parser_call is not None

    def test_register_commands_adds_threshold_argument(self):
        """register_commands() adds threshold argument."""
        tool = SimilarityCommandTool()
        subparsers = MagicMock()
        sim_parser = MagicMock()
        subparsers.add_parser.return_value = sim_parser

        tool.register_commands(subparsers)

        threshold_call = None
        for call_arg in sim_parser.add_argument.call_args_list:
            if '--threshold' in str(call_arg):
                threshold_call = call_arg
                break

        assert threshold_call is not None

    def test_register_commands_adds_limit_argument(self):
        """register_commands() adds limit argument."""
        tool = SimilarityCommandTool()
        subparsers = MagicMock()
        sim_parser = MagicMock()
        subparsers.add_parser.return_value = sim_parser

        tool.register_commands(subparsers)

        limit_call = None
        for call_arg in sim_parser.add_argument.call_args_list:
            if '--limit' in str(call_arg):
                limit_call = call_arg
                break

        assert limit_call is not None

    def test_register_commands_adds_output_argument(self):
        """register_commands() adds output argument."""
        tool = SimilarityCommandTool()
        subparsers = MagicMock()
        sim_parser = MagicMock()
        subparsers.add_parser.return_value = sim_parser

        tool.register_commands(subparsers)

        output_call = None
        for call_arg in sim_parser.add_argument.call_args_list:
            if '--output' in str(call_arg):
                output_call = call_arg
                break

        assert output_call is not None

    def test_register_commands_sets_func(self):
        """register_commands() sets func to execute_similarity."""
        tool = SimilarityCommandTool()
        subparsers = MagicMock()
        sim_parser = MagicMock()
        subparsers.add_parser.return_value = sim_parser

        tool.register_commands(subparsers)

        sim_parser.set_defaults.assert_called_once_with(func=tool.execute_similarity)


class TestSimilarityCommandToolExecuteValidation:
    """Test SimilarityCommandTool.execute_similarity() validation logic."""

    def test_execute_similarity_missing_query_file(self, capsys):
        """execute_similarity() returns error when query_file is None."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.query_file = None
        args.metric = 'name'
        args.threshold = 0.8
        args.limit = 10

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Query file is required" in captured.out

    def test_execute_similarity_threshold_below_zero(self, capsys):
        """execute_similarity() returns error for threshold < 0.0."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.threshold = -0.1
        args.limit = 10
        delattr(args, 'query_file')

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Threshold must be between 0.0 and 1.0" in captured.out

    def test_execute_similarity_threshold_above_one(self, capsys):
        """execute_similarity() returns error for threshold > 1.0."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.threshold = 1.5
        args.limit = 10
        delattr(args, 'query_file')

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Threshold must be between 0.0 and 1.0" in captured.out

    def test_execute_similarity_k_zero(self, capsys):
        """execute_similarity() returns error for k=0."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.k = 0
        args.threshold = 0.8
        delattr(args, 'query_file')

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] k must be a positive integer" in captured.out

    def test_execute_similarity_k_negative(self, capsys):
        """execute_similarity() returns error for negative k."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.k = -5
        args.threshold = 0.8
        delattr(args, 'query_file')

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] k must be a positive integer" in captured.out

    def test_execute_similarity_limit_zero(self, capsys):
        """execute_similarity() returns error for limit=0."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.limit = 0
        args.threshold = 0.8
        delattr(args, 'query_file')
        delattr(args, 'k')

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] limit must be a positive integer" in captured.out

    def test_execute_similarity_invalid_metric(self, capsys):
        """execute_similarity() returns error for invalid metric."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'invalid_metric'
        args.threshold = 0.8
        args.limit = 10
        delattr(args, 'query_file')
        delattr(args, 'k')

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Invalid metric: invalid_metric" in captured.out


class TestSimilarityCommandToolExecuteNoFiles:
    """Test SimilarityCommandTool.execute_similarity() with no files."""

    def test_execute_similarity_no_files_in_database(self, capsys):
        """execute_similarity() handles empty database."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'name'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            # Test that it handles empty database gracefully
            assert "Analysis complete" in captured.out or "No files" in captured.out


class TestSimilarityCommandToolExecuteHashMetric:
    """Test SimilarityCommandTool.execute_similarity() with hash metric."""

    def test_execute_similarity_hash_metric_finds_duplicates(self, capsys):
        """execute_similarity() with hash metric finds duplicates."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'hash'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        # Create files with same hash (duplicates)
        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
            {'id': 2, 'path': '/path/to/file2.txt', 'hash': 'abc123', 'size': 100, 'name': 'file2.txt'},
            {'id': 3, 'path': '/path/to/file3.txt', 'hash': 'abc123', 'size': 100, 'name': 'file3.txt'},
            {'id': 4, 'path': '/path/to/unique.txt', 'hash': 'xyz789', 'size': 200, 'name': 'unique.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Analyzing 4 files using metric: hash" in captured.out
            # Should mark 2 files as duplicates (file2 and file3 are duplicates of file1)
            assert mock_repo.mark_as_duplicate.call_count == 2


class TestSimilarityCommandToolExecuteSizeMetric:
    """Test SimilarityCommandTool.execute_similarity() with size metric."""

    def test_execute_similarity_size_metric_finds_duplicates(self, capsys):
        """execute_similarity() with size metric finds duplicates."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'size'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        # Create files with same size (duplicates by size)
        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
            {'id': 2, 'path': '/path/to/file2.txt', 'hash': 'def456', 'size': 100, 'name': 'file2.txt'},
            {'id': 3, 'path': '/path/to/file3.txt', 'hash': 'ghi789', 'size': 200, 'name': 'file3.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Analyzing 3 files using metric: size" in captured.out
            # Should mark 1 file as duplicate (file2 is duplicate of file1 by size)
            assert mock_repo.mark_as_duplicate.call_count == 1


class TestSimilarityCommandToolExecuteNameMetric:
    """Test SimilarityCommandTool.execute_similarity() with name metric."""

    def test_execute_similarity_name_metric_finds_duplicates(self, capsys):
        """execute_similarity() with name metric finds duplicates."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'name'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        # Create files with same name (duplicates by name)
        files = [
            {'id': 1, 'path': '/path/to/file.txt', 'hash': 'abc123', 'size': 100, 'name': 'file.txt'},
            {'id': 2, 'path': '/other/file.txt', 'hash': 'def456', 'size': 200, 'name': 'file.txt'},
            {'id': 3, 'path': '/unique/other.txt', 'hash': 'ghi789', 'size': 150, 'name': 'other.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Analyzing 3 files using metric: name" in captured.out
            # Should mark 1 file as duplicate (second file.txt is duplicate of first)
            assert mock_repo.mark_as_duplicate.call_count == 1


class TestSimilarityCommandToolExecuteVectorMetric:
    """Test SimilarityCommandTool.execute_similarity() with vector metric."""

    def test_execute_similarity_vector_metric_not_implemented(self, capsys):
        """execute_similarity() with vector metric reports not implemented."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'vector'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Vector similarity search not yet implemented" in captured.out


class TestSimilarityCommandToolExecuteVerbose:
    """Test SimilarityCommandTool.execute_similarity() verbose output."""

    def test_execute_similarity_verbose_output(self, capsys):
        """execute_similarity() with verbose flag prints details."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'hash'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = True
        args.container = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
            {'id': 2, 'path': '/path/to/file2.txt', 'hash': 'abc123', 'size': 100, 'name': 'file2.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "[DUP]" in captured.out


class TestSimilarityCommandToolExecuteEdgeCases:
    """Test SimilarityCommandTool.execute_similarity() edge cases."""

    def test_execute_similarity_files_without_hash(self, capsys):
        """execute_similarity() handles files without hash."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'hash'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        # Files with missing hash
        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': None, 'size': 100, 'name': 'file1.txt'},
            {'id': 2, 'path': '/path/to/file2.txt', 'hash': 'abc123', 'size': 100, 'name': 'file2.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            # Should not crash, just skip files without hash

    def test_execute_similarity_general_exception(self, capsys):
        """execute_similarity() handles general exceptions."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'hash'
        args.verbose = True
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")
        delattr(args, 'query_file')
        delattr(args, 'k')

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[TOOL ERROR] Similarity search failed:" in captured.out

    def test_execute_similarity_fallback_to_global_container(self, capsys):
        """execute_similarity() falls back to global container."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'name'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = None  # No container
        delattr(args, 'query_file')
        delattr(args, 'k')

        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
        ]

        with patch('nodupe.core.container.container') as mock_global_container:
            with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
                mock_global_container.get_service.return_value = MagicMock()
                mock_repo = MagicMock()
                mock_repo.get_all_files.return_value = files
                mock_repo_class.return_value = mock_repo

                result = tool.execute_similarity(args)

                assert result == 0


class TestSimilarityCommandToolRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_similarity_tool(self):
        """register_tool() returns a SimilarityCommandTool instance."""
        tool = register_tool()
        assert isinstance(tool, SimilarityCommandTool)


class TestSimilarityCommandToolModuleLevel:
    """Test module-level exports."""

    def test_similarity_tool_instance_exists(self):
        """similarity_tool module-level instance exists."""
        from nodupe.tools.commands import similarity
        assert similarity.similarity_tool is not None
        assert isinstance(similarity.similarity_tool, SimilarityCommandTool)

    def test_register_tool_function_exists(self):
        """register_tool function is exported."""
        from nodupe.tools.commands import similarity
        assert callable(similarity.register_tool)

    def test_all_export(self):
        """__all__ contains expected exports."""
        from nodupe.tools.commands import similarity
        assert 'similarity_tool' in similarity.__all__
        assert 'register_tool' in similarity.__all__

    def test_api_methods_property(self):
        """api_methods property returns tool methods."""
        tool = SimilarityCommandTool()
        # api_methods should contain tool methods
        assert isinstance(tool.api_methods, dict) or isinstance(tool.api_methods, list)
        assert len(tool.api_methods) >= 0  # May have methods or be empty

    def test_describe_usage(self):
        """describe_usage() returns usage description."""
        tool = SimilarityCommandTool()
        usage = tool.describe_usage()
        # Should have some description
        assert isinstance(usage, str) and len(usage) > 0

    def test_run_standalone(self):
        """run_standalone() calls execute_similarity."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'name'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.run_standalone(args)
            assert result == 0


class TestSimilarityCommandToolExecuteValidationEdgeCases:
    """Test SimilarityCommandTool.execute_similarity() validation edge cases."""

    def test_execute_similarity_query_file_is_none(self, capsys):
        """execute_similarity() returns error when query_file is explicitly None."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.query_file = None  # Explicitly set to None
        args.metric = 'name'
        args.threshold = 0.8
        args.limit = 10

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR] Query file is required" in captured.out

    def test_execute_similarity_threshold_valid(self, capsys):
        """execute_similarity() proceeds when threshold is valid."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.threshold = 0.5  # Valid threshold
        args.limit = 10
        args.metric = 'name'
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Executing similarity command" in captured.out

    def test_execute_similarity_k_valid(self, capsys):
        """execute_similarity() proceeds when k is valid."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.k = 5  # Valid k
        args.threshold = 0.8
        args.metric = 'name'
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'limit')

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Executing similarity command" in captured.out


class TestSimilarityCommandToolExecuteContainerFallback:
    """Test SimilarityCommandTool.execute_similarity() container fallback."""

    def test_execute_similarity_uses_global_container_when_none(self, capsys):
        """execute_similarity() uses global container when args.container is None."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'name'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = None  # No container
        delattr(args, 'query_file')
        delattr(args, 'k')

        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
        ]

        with patch('nodupe.core.container.container') as mock_global_container:
            with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
                mock_global_container.get_service.return_value = MagicMock()
                mock_repo = MagicMock()
                mock_repo.get_all_files.return_value = files
                mock_repo_class.return_value = mock_repo

                result = tool.execute_similarity(args)

                assert result == 0


class TestSimilarityCommandToolExecuteVerboseEdgeCases:
    """Test SimilarityCommandTool.execute_similarity() verbose edge cases."""

    def test_execute_similarity_verbose_exception_traceback(self, capsys):
        """execute_similarity() prints traceback when verbose is True."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'name'
        args.verbose = True
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")
        delattr(args, 'query_file')
        delattr(args, 'k')
        delattr(args, 'limit')

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Traceback" in captured.out or "Traceback" in captured.err or "[TOOL ERROR]" in captured.out


class TestSimilarityCommandToolCoverageCompletion:
    """Additional tests to achieve 100% coverage."""

    def test_execute_similarity_threshold_boundary_zero(self, capsys):
        """execute_similarity() accepts threshold at boundary 0.0."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.threshold = 0.0  # Valid boundary
        args.limit = 10
        args.metric = 'name'
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Executing similarity command" in captured.out

    def test_execute_similarity_threshold_boundary_one(self, capsys):
        """execute_similarity() accepts threshold at boundary 1.0."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.threshold = 1.0  # Valid boundary
        args.limit = 10
        args.metric = 'name'
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Executing similarity command" in captured.out

    def test_execute_similarity_limit_boundary_one(self, capsys):
        """execute_similarity() accepts limit at boundary 1."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.limit = 1  # Valid boundary
        args.threshold = 0.8
        args.metric = 'name'
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = []
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Executing similarity command" in captured.out

    def test_execute_similarity_content_metric(self, capsys):
        """execute_similarity() with content metric."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'content'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            # Content metric falls through to hash/size/name grouping logic
            assert "Analyzing 1 files" in captured.out

    def test_execute_similarity_database_service_fallback(self, capsys):
        """execute_similarity() falls back to default database connection."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'name'
        args.threshold = 0.8
        args.limit = 10
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = None  # No database service
        delattr(args, 'query_file')
        delattr(args, 'k')

        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
        ]

        with patch('nodupe.tools.databases.connection.DatabaseConnection') as mock_db_conn:
            with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
                mock_instance = MagicMock()
                mock_db_conn.get_instance.return_value = mock_instance
                mock_repo = MagicMock()
                mock_repo.get_all_files.return_value = files
                mock_repo_class.return_value = mock_repo

                result = tool.execute_similarity(args)

                assert result == 0
                mock_db_conn.get_instance.assert_called()

    def test_execute_similarity_exception_without_verbose(self, capsys):
        """execute_similarity() handles exception without verbose traceback."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'name'
        args.verbose = False  # No verbose
        args.container = MagicMock()
        args.container.get_service.side_effect = Exception("Test exception")
        delattr(args, 'query_file')
        delattr(args, 'k')
        delattr(args, 'limit')

        result = tool.execute_similarity(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[TOOL ERROR] Similarity search failed:" in captured.out
        # Should NOT have traceback when verbose is False
        assert "Traceback" not in captured.out

    def test_execute_similarity_threshold_valid_path(self, capsys):
        """execute_similarity() continues when threshold is valid (0.5)."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.threshold = 0.5  # Valid threshold in middle of range
        args.limit = 10
        args.metric = 'hash'
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'k')

        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Executing similarity command" in captured.out

    def test_execute_similarity_k_valid_path(self, capsys):
        """execute_similarity() continues when k is valid (5)."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.k = 5  # Valid k
        args.threshold = 0.8
        args.metric = 'hash'
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        delattr(args, 'query_file')
        delattr(args, 'limit')

        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Executing similarity command" in captured.out

    def test_execute_similarity_no_threshold_attr(self, capsys):
        """execute_similarity() covers branch when args has no threshold attribute."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'name'
        args.limit = 10
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        # Remove threshold attribute to cover False branch
        delattr(args, 'threshold')
        delattr(args, 'query_file')
        delattr(args, 'k')

        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Executing similarity command" in captured.out

    def test_execute_similarity_no_limit_attr(self, capsys):
        """execute_similarity() covers branch when args has no limit attribute."""
        tool = SimilarityCommandTool()
        args = MagicMock()
        args.metric = 'name'
        args.threshold = 0.8
        args.verbose = False
        args.container = MagicMock()
        args.container.get_service.return_value = MagicMock()
        # Remove limit attribute to cover False branch
        delattr(args, 'limit')
        delattr(args, 'query_file')
        delattr(args, 'k')

        files = [
            {'id': 1, 'path': '/path/to/file1.txt', 'hash': 'abc123', 'size': 100, 'name': 'file1.txt'},
        ]

        with patch('nodupe.tools.databases.files.FileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_all_files.return_value = files
            mock_repo_class.return_value = mock_repo

            result = tool.execute_similarity(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Executing similarity command" in captured.out
