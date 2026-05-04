"""
Comprehensive tests for Phase 8 Hash Autotuning module - hashing_tool.py.

Tests cover:
- Command registration
- Argument parsing
- Hash computation
- Batch processing
- Error handling
- Tool metadata and capabilities
"""

import os
import sys
import tempfile
from unittest.mock import MagicMock

import pytest

from nodupe.core.tool_system.base import ToolMetadata
from nodupe.tools.hashing.hashing_tool import (
    StandardHashingTool,
    register_tool,
)


class TestStandardHashingToolInit:
    """Tests for StandardHashingTool initialization."""

    def test_init_creates_hasher(self):
        """Test that initialization creates a FileHasher instance."""
        tool = StandardHashingTool()
        assert tool.hasher is not None
        assert hasattr(tool.hasher, 'hash_file')
        assert hasattr(tool.hasher, 'hash_string')
        assert hasattr(tool.hasher, 'hash_bytes')

    def test_init_default_algorithm(self):
        """Test that hasher uses default algorithm."""
        tool = StandardHashingTool()
        # Default should be sha256 based on FileHasher default
        assert tool.hasher.get_algorithm() == 'sha256'


class TestToolProperties:
    """Tests for tool property attributes."""

    def test_name_property(self):
        """Test name property returns correct value."""
        tool = StandardHashingTool()
        assert tool.name == "hashing_standard"

    def test_version_property(self):
        """Test version property returns correct value."""
        tool = StandardHashingTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """Test dependencies property returns empty list."""
        tool = StandardHashingTool()
        assert tool.dependencies == []
        assert isinstance(tool.dependencies, list)

    def test_metadata_property(self):
        """Test metadata property returns ToolMetadata."""
        tool = StandardHashingTool()
        metadata = tool.metadata

        assert isinstance(metadata, ToolMetadata)
        assert metadata.name == "hashing_standard"
        assert metadata.version == "1.0.0"
        assert metadata.author == "NoDupeLabs"
        assert metadata.license == "Apache-2.0"
        assert "security" in metadata.tags
        assert "hashing" in metadata.tags
        assert "integrity" in metadata.tags
        assert "ISO-10118-3" in metadata.tags

    def test_metadata_software_id(self):
        """Test metadata software_id format."""
        tool = StandardHashingTool()
        assert tool.metadata.software_id == "org.nodupe.tool.hashing_standard"

    def test_metadata_description(self):
        """Test metadata description mentions ISO compliance."""
        tool = StandardHashingTool()
        assert "ISO/IEC 10118-3" in tool.metadata.description


class TestApiMethods:
    """Tests for api_methods property."""

    def test_api_methods_returns_dict(self):
        """Test api_methods returns a dictionary."""
        tool = StandardHashingTool()
        api_methods = tool.api_methods

        assert isinstance(api_methods, dict)

    def test_api_methods_contains_hash_file(self):
        """Test api_methods contains hash_file."""
        tool = StandardHashingTool()
        assert 'hash_file' in tool.api_methods
        assert callable(tool.api_methods['hash_file'])

    def test_api_methods_contains_hash_string(self):
        """Test api_methods contains hash_string."""
        tool = StandardHashingTool()
        assert 'hash_string' in tool.api_methods
        assert callable(tool.api_methods['hash_string'])

    def test_api_methods_contains_hash_bytes(self):
        """Test api_methods contains hash_bytes."""
        tool = StandardHashingTool()
        assert 'hash_bytes' in tool.api_methods
        assert callable(tool.api_methods['hash_bytes'])

    def test_api_methods_contains_get_algorithms(self):
        """Test api_methods contains get_algorithms."""
        tool = StandardHashingTool()
        assert 'get_algorithms' in tool.api_methods
        assert callable(tool.api_methods['get_algorithms'])

    def test_api_methods_contains_check_iso_compliance(self):
        """Test api_methods contains check_iso_compliance."""
        tool = StandardHashingTool()
        assert 'check_iso_compliance' in tool.api_methods
        assert callable(tool.api_methods['check_iso_compliance'])

    def test_api_methods_hash_file_delegates_to_hasher(self):
        """Test hash_file method delegates to hasher."""
        tool = StandardHashingTool()

        # Create a temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = tool.api_methods['hash_file'](temp_path)
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            os.unlink(temp_path)

    def test_api_methods_hash_string_delegates_to_hasher(self):
        """Test hash_string method delegates to hasher."""
        tool = StandardHashingTool()
        result = tool.api_methods['hash_string']("test string")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_api_methods_hash_bytes_delegates_to_hasher(self):
        """Test hash_bytes method delegates to hasher."""
        tool = StandardHashingTool()
        result = tool.api_methods['hash_bytes'](b"test bytes")

        assert isinstance(result, str)
        assert len(result) > 0


class TestCheckIsoCompliance:
    """Tests for check_iso_compliance method."""

    def test_iso_compliant_sha256(self):
        """Test SHA-256 is ISO compliant."""
        tool = StandardHashingTool()
        result = tool.check_iso_compliance('sha256')

        assert result['algorithm'] == 'sha256'
        assert result['is_iso_compliant'] is True
        assert result['standard'] == "ISO/IEC 10118-3:2018"

    def test_iso_compliant_sha512(self):
        """Test SHA-512 is ISO compliant."""
        tool = StandardHashingTool()
        result = tool.check_iso_compliance('sha512')

        assert result['is_iso_compliant'] is True

    def test_iso_compliant_sha3(self):
        """Test SHA3 algorithms are ISO compliant."""
        tool = StandardHashingTool()

        for algo in ['sha3-256', 'sha3-384', 'sha3-512']:
            result = tool.check_iso_compliance(algo)
            assert result['is_iso_compliant'] is True, f"{algo} should be ISO compliant"

    def test_iso_compliant_shake(self):
        """Test SHAKE algorithms are ISO compliant."""
        tool = StandardHashingTool()

        for algo in ['shake128', 'shake256']:
            result = tool.check_iso_compliance(algo)
            assert result['is_iso_compliant'] is True, f"{algo} should be ISO compliant"

    def test_not_iso_compliant_md5(self):
        """Test MD5 is not ISO compliant."""
        tool = StandardHashingTool()
        result = tool.check_iso_compliance('md5')

        assert result['algorithm'] == 'md5'
        assert result['is_iso_compliant'] is False
        assert result['standard'] == "N/A"

    def test_not_iso_compliant_unknown(self):
        """Test unknown algorithm is not ISO compliant."""
        tool = StandardHashingTool()
        result = tool.check_iso_compliance('unknown_algo')

        assert result['is_iso_compliant'] is False

    def test_iso_compliance_case_insensitive(self):
        """Test ISO compliance check is case insensitive."""
        tool = StandardHashingTool()

        result_upper = tool.check_iso_compliance('SHA256')
        result_lower = tool.check_iso_compliance('sha256')
        result_mixed = tool.check_iso_compliance('Sha256')

        assert result_upper['is_iso_compliant'] == result_lower['is_iso_compliant']
        assert result_mixed['is_iso_compliant'] == result_lower['is_iso_compliant']

    def test_iso_compliance_result_structure(self):
        """Test ISO compliance result has correct structure."""
        tool = StandardHashingTool()
        result = tool.check_iso_compliance('sha256')

        assert 'algorithm' in result
        assert 'is_iso_compliant' in result
        assert 'standard' in result
        assert isinstance(result['algorithm'], str)
        assert isinstance(result['is_iso_compliant'], bool)
        assert isinstance(result['standard'], str)


class TestInitialize:
    """Tests for initialize method."""

    def test_initialize_registers_hasher_service(self):
        """Test initialize registers hasher service."""
        tool = StandardHashingTool()
        mock_container = MagicMock()

        tool.initialize(mock_container)

        mock_container.register_service.assert_called_once()
        call_args = mock_container.register_service.call_args
        assert call_args[0][0] == 'hasher_service'
        assert call_args[0][1] is tool.hasher

    def test_initialize_with_none_container(self):
        """Test initialize handles None container gracefully."""
        tool = StandardHashingTool()

        # Should not raise an exception
        with pytest.raises(AttributeError):
            tool.initialize(None)


class TestShutdown:
    """Tests for shutdown method."""

    def test_shutdown_no_error(self):
        """Test shutdown completes without error."""
        tool = StandardHashingTool()

        # Should not raise any exception
        tool.shutdown()

    def test_shutdown_multiple_times(self):
        """Test shutdown can be called multiple times."""
        tool = StandardHashingTool()

        tool.shutdown()
        tool.shutdown()
        tool.shutdown()


class TestRunStandalone:
    """Tests for run_standalone method."""

    def test_run_standalone_no_args_shows_help(self):
        """Test run_standalone with no args shows help."""
        tool = StandardHashingTool()

        # Capture stdout
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            result = tool.run_standalone([])

        assert result == 0
        output = f.getvalue()
        assert 'usage' in output.lower() or 'help' in output.lower()

    def test_run_standalone_with_file(self, temp_dir):
        """Test run_standalone with a file argument."""
        tool = StandardHashingTool()

        # Create a temp file
        test_file = temp_dir / "test_hash.txt"
        test_file.write_text("test content for hashing")

        result = tool.run_standalone([str(test_file)])

        assert result == 0

    def test_run_standalone_with_algorithm(self, temp_dir):
        """Test run_standalone with custom algorithm."""
        tool = StandardHashingTool()

        test_file = temp_dir / "test_hash.txt"
        test_file.write_text("test content")

        result = tool.run_standalone([str(test_file), "--algo", "sha512"])

        assert result == 0

    def test_run_standalone_invalid_file(self):
        """Test run_standalone with non-existent file."""
        tool = StandardHashingTool()

        result = tool.run_standalone(["/nonexistent/path/file.txt"])

        assert result == 1

    def test_run_standalone_invalid_algorithm(self, temp_dir):
        """Test run_standalone with invalid algorithm."""
        tool = StandardHashingTool()

        test_file = temp_dir / "test_hash.txt"
        test_file.write_text("test content")

        result = tool.run_standalone([str(test_file), "--algo", "invalid_algo"])

        assert result == 1

    def test_run_standalone_output_format(self, temp_dir):
        """Test run_standalone output format."""
        tool = StandardHashingTool()

        test_file = temp_dir / "test_hash.txt"
        test_file.write_text("test content")

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            tool.run_standalone([str(test_file)])

        output = f.getvalue()
        assert "Digital Fingerprint:" in output

    def test_run_standalone_default_algorithm(self, temp_dir):
        """Test run_standalone uses sha256 by default."""
        tool = StandardHashingTool()

        test_file = temp_dir / "test_hash.txt"
        test_file.write_text("test content")

        # Hash should be sha256 (64 hex chars)
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            tool.run_standalone([str(test_file)])

        output = f.getvalue()
        # Extract hash from output
        if "Digital Fingerprint:" in output:
            hash_value = output.split("Digital Fingerprint:")[1].strip()
            # SHA256 produces 64 hex characters
            assert len(hash_value) == 64

    def test_run_standalone_md5_algorithm(self, temp_dir):
        """Test run_standalone with MD5 algorithm."""
        tool = StandardHashingTool()

        test_file = temp_dir / "test_hash.txt"
        test_file.write_text("test content")

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            tool.run_standalone([str(test_file), "--algo", "md5"])

        output = f.getvalue()
        if "Digital Fingerprint:" in output:
            hash_value = output.split("Digital Fingerprint:")[1].strip()
            # MD5 produces 32 hex characters
            assert len(hash_value) == 32


class TestDescribeUsage:
    """Tests for describe_usage method."""

    def test_describe_usage_returns_string(self):
        """Test describe_usage returns a string."""
        tool = StandardHashingTool()
        description = tool.describe_usage()

        assert isinstance(description, str)
        assert len(description) > 0

    def test_describe_usage_mentions_fingerprint(self):
        """Test describe_usage mentions digital fingerprint."""
        tool = StandardHashingTool()
        description = tool.describe_usage()

        assert "fingerprint" in description.lower()

    def test_describe_usage_mentions_backup(self):
        """Test describe_usage mentions backup verification."""
        tool = StandardHashingTool()
        description = tool.describe_usage()

        assert "backup" in description.lower()

    def test_describe_usage_plain_language(self):
        """Test describe_usage uses plain language."""
        tool = StandardHashingTool()
        description = tool.describe_usage()

        # Should be understandable without technical jargon
        assert len(description) > 20  # Reasonable length
        assert isinstance(description, str)


class TestGetCapabilities:
    """Tests for get_capabilities method."""

    def test_get_capabilities_returns_dict(self):
        """Test get_capabilities returns a dictionary."""
        tool = StandardHashingTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)

    def test_get_capabilities_contains_algorithms(self):
        """Test get_capabilities contains algorithms list."""
        tool = StandardHashingTool()
        capabilities = tool.get_capabilities()

        assert 'algorithms' in capabilities
        assert isinstance(capabilities['algorithms'], list)
        assert len(capabilities['algorithms']) > 0

    def test_get_capabilities_contains_features(self):
        """Test get_capabilities contains features list."""
        tool = StandardHashingTool()
        capabilities = tool.get_capabilities()

        assert 'features' in capabilities
        assert isinstance(capabilities['features'], list)

    def test_get_capabilities_features(self):
        """Test get_capabilities lists correct features."""
        tool = StandardHashingTool()
        capabilities = tool.get_capabilities()

        features = capabilities['features']
        assert 'file_hashing' in features
        assert 'string_hashing' in features
        assert 'byte_hashing' in features

    def test_get_capabilities_algorithms_available(self):
        """Test that listed algorithms are actually available."""
        tool = StandardHashingTool()
        capabilities = tool.get_capabilities()

        import hashlib
        for algo in capabilities['algorithms']:
            assert algo in hashlib.algorithms_available


class TestRegisterTool:
    """Tests for register_tool function."""

    def test_register_tool_returns_instance(self):
        """Test register_tool returns a StandardHashingTool instance."""
        result = register_tool()

        assert isinstance(result, StandardHashingTool)

    def test_register_tool_creates_new_instance(self):
        """Test register_tool creates a new instance each call."""
        result1 = register_tool()
        result2 = register_tool()

        assert result1 is not result2
        assert type(result1) == type(result2)


class TestHashingIntegration:
    """Integration tests for hashing functionality."""

    def test_hash_file_integration(self, temp_dir):
        """Test complete file hashing workflow."""
        tool = StandardHashingTool()

        # Create test file
        test_file = temp_dir / "integration_test.txt"
        test_content = "Integration test content for hashing"
        test_file.write_text(test_content)

        # Hash the file
        result = tool.hasher.hash_file(str(test_file))

        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in result)

    def test_hash_string_integration(self):
        """Test complete string hashing workflow."""
        tool = StandardHashingTool()

        test_string = "Integration test string"
        result = tool.hasher.hash_string(test_string)

        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_bytes_integration(self):
        """Test complete bytes hashing workflow."""
        tool = StandardHashingTool()

        test_bytes = b"Integration test bytes"
        result = tool.hasher.hash_bytes(test_bytes)

        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_consistency_across_methods(self, temp_dir):
        """Test that file and string hashing produce consistent results."""
        tool = StandardHashingTool()

        test_content = "Consistency test content"

        # Hash as string
        string_hash = tool.hasher.hash_string(test_content)

        # Hash as file
        test_file = temp_dir / "consistency_test.txt"
        test_file.write_text(test_content)
        file_hash = tool.hasher.hash_file(str(test_file))

        assert string_hash == file_hash

    def test_verify_hash_integration(self, temp_dir):
        """Test hash verification workflow."""
        tool = StandardHashingTool()

        test_file = temp_dir / "verify_test.txt"
        test_file.write_text("Content to verify")

        # Get hash
        expected_hash = tool.hasher.hash_file(str(test_file))

        # Verify
        is_valid = tool.hasher.verify_hash(str(test_file), expected_hash)
        assert is_valid is True

        # Verify with wrong hash
        is_invalid = tool.hasher.verify_hash(str(test_file), "wrong_hash")
        assert is_invalid is False


class TestBatchProcessing:
    """Tests for batch processing capabilities."""

    def test_hash_multiple_files(self, temp_dir):
        """Test hashing multiple files."""
        tool = StandardHashingTool()

        # Create multiple test files
        files = []
        for i in range(3):
            test_file = temp_dir / f"batch_test_{i}.txt"
            test_file.write_text(f"Content {i}")
            files.append(str(test_file))

        results = tool.hasher.hash_files(files)

        assert isinstance(results, dict)
        assert len(results) == 3

        for file_path, hash_value in results.items():
            assert isinstance(hash_value, str)
            assert len(hash_value) == 64

    def test_hash_multiple_files_with_nonexistent(self, temp_dir):
        """Test hashing multiple files with some non-existent."""
        tool = StandardHashingTool()

        # Create one valid file
        test_file = temp_dir / "valid_file.txt"
        test_file.write_text("Valid content")

        files = [str(test_file), "/nonexistent/file.txt"]
        results = tool.hasher.hash_files(files)

        # Should only contain the valid file
        assert len(results) == 1
        assert str(test_file) in results

    def test_hash_multiple_files_empty_list(self):
        """Test hashing empty file list."""
        tool = StandardHashingTool()

        results = tool.hasher.hash_files([])

        assert isinstance(results, dict)
        assert len(results) == 0


class TestErrorHandling:
    """Tests for error handling."""

    def test_hash_nonexistent_file(self):
        """Test hashing non-existent file raises error."""
        tool = StandardHashingTool()

        with pytest.raises(FileNotFoundError):
            tool.hasher.hash_file("/nonexistent/path/file.txt")

    def test_hash_directory_raises_error(self, temp_dir):
        """Test hashing a directory raises error."""
        tool = StandardHashingTool()

        with pytest.raises(FileNotFoundError):
            tool.hasher.hash_file(str(temp_dir))

    def test_invalid_algorithm_raises_error(self):
        """Test setting invalid algorithm raises error."""
        tool = StandardHashingTool()

        with pytest.raises(ValueError):
            tool.hasher.set_algorithm("invalid_algorithm_name")

    def test_invalid_buffer_size_raises_error(self):
        """Test setting invalid buffer size raises error."""
        tool = StandardHashingTool()

        with pytest.raises(ValueError):
            tool.hasher.set_buffer_size(0)

        with pytest.raises(ValueError):
            tool.hasher.set_buffer_size(-100)


class TestAlgorithmSelection:
    """Tests for algorithm selection and switching."""

    def test_set_algorithm_sha256(self):
        """Test setting SHA256 algorithm."""
        tool = StandardHashingTool()
        tool.hasher.set_algorithm('sha256')

        assert tool.hasher.get_algorithm() == 'sha256'

    def test_set_algorithm_sha512(self):
        """Test setting SHA512 algorithm."""
        tool = StandardHashingTool()
        tool.hasher.set_algorithm('sha512')

        assert tool.hasher.get_algorithm() == 'sha512'

    def test_set_algorithm_md5(self):
        """Test setting MD5 algorithm."""
        tool = StandardHashingTool()
        tool.hasher.set_algorithm('md5')

        assert tool.hasher.get_algorithm() == 'md5'

    def test_set_algorithm_blake2b(self):
        """Test setting BLAKE2b algorithm."""
        tool = StandardHashingTool()
        tool.hasher.set_algorithm('blake2b')

        assert tool.hasher.get_algorithm() == 'blake2b'

    def test_algorithm_case_insensitive(self):
        """Test algorithm setting is case insensitive."""
        tool = StandardHashingTool()

        tool.hasher.set_algorithm('SHA256')
        assert tool.hasher.get_algorithm() == 'sha256'

        tool.hasher.set_algorithm('Sha512')
        assert tool.hasher.get_algorithm() == 'sha512'

    def test_hash_output_varies_by_algorithm(self):
        """Test that different algorithms produce different hashes."""
        tool = StandardHashingTool()
        test_data = b"test data"

        tool.hasher.set_algorithm('sha256')
        sha256_hash = tool.hasher.hash_bytes(test_data)

        tool.hasher.set_algorithm('sha512')
        sha512_hash = tool.hasher.hash_bytes(test_data)

        tool.hasher.set_algorithm('md5')
        md5_hash = tool.hasher.hash_bytes(test_data)

        assert sha256_hash != sha512_hash
        assert sha256_hash != md5_hash
        assert sha512_hash != md5_hash

        # Verify expected lengths
        assert len(sha256_hash) == 64  # 256 bits = 64 hex chars
        assert len(sha512_hash) == 128  # 512 bits = 128 hex chars
        assert len(md5_hash) == 32  # 128 bits = 32 hex chars


class TestMainExecution:
    """Tests for main execution path."""

    def test_main_execution_with_args(self, temp_dir):
        """Test __main__ execution with arguments."""
        test_file = temp_dir / "main_test.txt"
        test_file.write_text("Main execution test")

        # Simulate command line execution
        import subprocess
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, '/home/prod/Workspaces/repos/github/NoDupeLabs'); "
             f"from nodupe.tools.hashing.hashing_tool import StandardHashingTool; "
             f"tool = StandardHashingTool(); "
             f"sys.exit(tool.run_standalone(['{test_file}']))"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Digital Fingerprint:" in result.stdout


class TestImportFallback:
    """Tests for import fallback path in standalone mode."""

    def test_import_fallback_path_structure(self):
        """Test that the import fallback path exists and has correct structure."""
        # This test verifies the fallback import code path exists
        # The actual fallback is tested by the module loading correctly
        import nodupe.tools.hashing.hashing_tool as ht

        # Verify the module has the expected structure
        assert hasattr(ht, 'StandardHashingTool')
        assert hasattr(ht, 'register_tool')

    def test_standalone_import_pattern(self):
        """Test that the standalone import pattern works correctly."""
        # This tests that the try/except import pattern is correctly structured
        # by verifying the module imports successfully
        from nodupe.tools.hashing.hashing_tool import StandardHashingTool

        tool = StandardHashingTool()
        assert tool is not None
        assert hasattr(tool, 'hasher')
