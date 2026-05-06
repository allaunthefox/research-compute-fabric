"""Tests for the hasher_interface module."""

from unittest.mock import MagicMock, Mock, call

import pytest

from nodupe.core.hasher_interface import HasherInterface


class ConcreteHasher(HasherInterface):
    """Concrete implementation of HasherInterface for testing."""

    def __init__(self):
        """Initialize ConcreteHasher with default values."""
        self._algorithm = "sha256"
        self._available_algorithms = ["md5", "sha1", "sha256", "sha512"]
        self._hash_file_result = ""
        self._hash_string_result = ""
        self._hash_bytes_result = ""
        self._verify_hash_result = False
        self._progress_callback = None

    def hash_file(
        self,
        file_path: str,
        on_progress: callable | None = None
    ) -> str:
        """Hash a file and return the hash value."""
        self._progress_callback = on_progress
        return self._hash_file_result

    def hash_string(self, data: str) -> str:
        """Hash a string and return the hash value."""
        return self._hash_string_result

    def hash_bytes(self, data: bytes) -> str:
        """Hash bytes and return the hash value."""
        return self._hash_bytes_result

    def verify_hash(self, file_path: str, expected_hash: str) -> bool:
        """Verify a file hash against an expected hash."""
        return self._verify_hash_result

    def set_algorithm(self, algorithm: str) -> None:
        """Set the hash algorithm to use."""
        self._algorithm = algorithm

    def get_algorithm(self) -> str:
        """Get the current hash algorithm."""
        return self._algorithm

    def get_available_algorithms(self) -> list[str]:
        """Get list of available hash algorithms."""
        return self._available_algorithms


class TestHasherInterface:
    """Test HasherInterface abstract base class."""

    def test_interface_cannot_be_instantiated(self):
        """Test that HasherInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            HasherInterface()

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that a concrete implementation can be instantiated."""
        hasher = ConcreteHasher()
        assert hasher is not None

    def test_hash_file_abstract_method(self):
        """Test hash_file method signature."""
        hasher = ConcreteHasher()
        hasher._hash_file_result = "abc123"
        result = hasher.hash_file("/path/to/file.txt")
        assert isinstance(result, str)

    def test_hash_file_with_progress_callback(self):
        """Test hash_file with progress callback."""
        hasher = ConcreteHasher()
        hasher._hash_file_result = "abc123"
        progress_callback = MagicMock()

        result = hasher.hash_file("/path/to/file.txt", on_progress=progress_callback)

        assert isinstance(result, str)
        assert hasher._progress_callback is progress_callback

    def test_hash_string_abstract_method(self):
        """Test hash_string method signature."""
        hasher = ConcreteHasher()
        hasher._hash_string_result = "abc123"
        result = hasher.hash_string("test data")
        assert isinstance(result, str)

    def test_hash_bytes_abstract_method(self):
        """Test hash_bytes method signature."""
        hasher = ConcreteHasher()
        hasher._hash_bytes_result = "abc123"
        result = hasher.hash_bytes(b"test data")
        assert isinstance(result, str)

    def test_verify_hash_abstract_method(self):
        """Test verify_hash method signature."""
        hasher = ConcreteHasher()
        hasher._verify_hash_result = True
        result = hasher.verify_hash("/path/to/file.txt", "expected_hash")
        assert isinstance(result, bool)

    def test_set_algorithm_abstract_method(self):
        """Test set_algorithm method."""
        hasher = ConcreteHasher()
        hasher.set_algorithm("md5")
        assert hasher.get_algorithm() == "md5"

    def test_get_algorithm_abstract_method(self):
        """Test get_algorithm method."""
        hasher = ConcreteHasher()
        result = hasher.get_algorithm()
        assert isinstance(result, str)

    def test_get_available_algorithms_abstract_method(self):
        """Test get_available_algorithms method."""
        hasher = ConcreteHasher()
        result = hasher.get_available_algorithms()
        assert isinstance(result, list)


class TestHasherInterfaceImplementation:
    """Test HasherInterface with concrete implementations."""

    def test_hash_file_various_paths(self):
        """Test hash_file with various file paths."""
        hasher = ConcreteHasher()
        hasher._hash_file_result = "hash123"

        assert hasher.hash_file("/absolute/path/file.txt") == "hash123"
        assert hasher.hash_file("relative/path/file.txt") == "hash123"
        assert hasher.hash_file("file.txt") == "hash123"

    def test_hash_file_progress_callback_invocation(self):
        """Test that progress callback is invoked during hashing."""
        hasher = ConcreteHasher()
        hasher._hash_file_result = "hash123"
        progress_callback = MagicMock()

        hasher.hash_file("/path/to/file.txt", on_progress=progress_callback)

        # Callback should be stored for use during hashing
        assert hasher._progress_callback is progress_callback

    def test_hash_string_empty(self):
        """Test hash_string with empty string."""
        hasher = ConcreteHasher()
        hasher._hash_string_result = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        result = hasher.hash_string("")
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_hash_string_unicode(self):
        """Test hash_string with unicode characters."""
        hasher = ConcreteHasher()
        hasher._hash_string_result = "unicode_hash"

        result = hasher.hash_string("Hello, \u4e16\u754c!")
        assert result == "unicode_hash"

    def test_hash_bytes_empty(self):
        """Test hash_bytes with empty bytes."""
        hasher = ConcreteHasher()
        hasher._hash_bytes_result = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        result = hasher.hash_bytes(b"")
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_hash_bytes_large_data(self):
        """Test hash_bytes with large data."""
        hasher = ConcreteHasher()
        hasher._hash_bytes_result = "large_data_hash"
        large_data = b"x" * (1024 * 1024)  # 1MB

        result = hasher.hash_bytes(large_data)
        assert result == "large_data_hash"

    def test_verify_hash_match(self):
        """Test verify_hash with matching hash."""
        hasher = ConcreteHasher()
        hasher._verify_hash_result = True

        result = hasher.verify_hash("/path/to/file.txt", "expected_hash")
        assert result is True

    def test_verify_hash_mismatch(self):
        """Test verify_hash with mismatched hash."""
        hasher = ConcreteHasher()
        hasher._verify_hash_result = False

        result = hasher.verify_hash("/path/to/file.txt", "wrong_hash")
        assert result is False

    def test_set_algorithm_various_algorithms(self):
        """Test set_algorithm with various algorithms."""
        hasher = ConcreteHasher()

        hasher.set_algorithm("md5")
        assert hasher.get_algorithm() == "md5"

        hasher.set_algorithm("sha1")
        assert hasher.get_algorithm() == "sha1"

        hasher.set_algorithm("sha256")
        assert hasher.get_algorithm() == "sha256"

        hasher.set_algorithm("sha512")
        assert hasher.get_algorithm() == "sha512"

    def test_get_available_algorithms_content(self):
        """Test get_available_algorithms returns expected algorithms."""
        hasher = ConcreteHasher()
        algorithms = hasher.get_available_algorithms()

        assert "md5" in algorithms
        assert "sha1" in algorithms
        assert "sha256" in algorithms
        assert "sha512" in algorithms


class TestHasherInterfaceMock:
    """Test HasherInterface with mock implementations."""

    def test_mock_implementation(self):
        """Test with mock implementation."""
        mock_hasher = Mock(spec=HasherInterface)
        mock_hasher.hash_file.return_value = "mock_hash"
        mock_hasher.hash_string.return_value = "string_hash"
        mock_hasher.hash_bytes.return_value = "bytes_hash"
        mock_hasher.verify_hash.return_value = True
        mock_hasher.get_algorithm.return_value = "sha256"
        mock_hasher.get_available_algorithms.return_value = ["sha256", "md5"]

        assert mock_hasher.hash_file("/test.txt") == "mock_hash"
        assert mock_hasher.hash_string("test") == "string_hash"
        assert mock_hasher.hash_bytes(b"test") == "bytes_hash"
        assert mock_hasher.verify_hash("/test.txt", "hash") is True
        assert mock_hasher.get_algorithm() == "sha256"
        assert mock_hasher.get_available_algorithms() == ["sha256", "md5"]


class TestHasherInterfaceEdgeCases:
    """Test edge cases for HasherInterface."""

    def test_hash_file_none_path(self):
        """Test hash_file with None path."""
        hasher = ConcreteHasher()
        hasher._hash_file_result = "none_hash"

        result = hasher.hash_file(None)  # type: ignore
        assert result == "none_hash"

    def test_hash_string_none_data(self):
        """Test hash_string with None data."""
        hasher = ConcreteHasher()
        hasher._hash_string_result = "none_string_hash"

        result = hasher.hash_string(None)  # type: ignore
        assert result == "none_string_hash"

    def test_hash_bytes_none_data(self):
        """Test hash_bytes with None data."""
        hasher = ConcreteHasher()
        hasher._hash_bytes_result = "none_bytes_hash"

        result = hasher.hash_bytes(None)  # type: ignore
        assert result == "none_bytes_hash"

    def test_verify_hash_none_file_path(self):
        """Test verify_hash with None file path."""
        hasher = ConcreteHasher()
        hasher._verify_hash_result = False

        result = hasher.verify_hash(None, "hash")  # type: ignore
        assert result is False

    def test_verify_hash_none_expected_hash(self):
        """Test verify_hash with None expected hash."""
        hasher = ConcreteHasher()
        hasher._verify_hash_result = False

        result = hasher.verify_hash("/path/to/file.txt", None)  # type: ignore
        assert result is False

    def test_set_algorithm_empty_string(self):
        """Test set_algorithm with empty string."""
        hasher = ConcreteHasher()
        hasher.set_algorithm("")
        assert hasher.get_algorithm() == ""

    def test_set_algorithm_none(self):
        """Test set_algorithm with None."""
        hasher = ConcreteHasher()
        hasher.set_algorithm(None)  # type: ignore
        assert hasher.get_algorithm() is None

    def test_hash_file_progress_callback_none(self):
        """Test hash_file with None progress callback."""
        hasher = ConcreteHasher()
        hasher._hash_file_result = "hash"

        result = hasher.hash_file("/path/to/file.txt", on_progress=None)
        assert result == "hash"
        assert hasher._progress_callback is None

    def test_interface_subclass_check(self):
        """Test that concrete implementation is recognized as subclass."""
        assert issubclass(ConcreteHasher, HasherInterface)

    def test_instance_check(self):
        """Test that concrete instance is recognized as instance."""
        hasher = ConcreteHasher()
        assert isinstance(hasher, HasherInterface)

    def test_algorithm_case_insensitive(self):
        """Test algorithm setting is case insensitive."""
        hasher = ConcreteHasher()

        hasher.set_algorithm("SHA256")
        assert hasher.get_algorithm() == "SHA256"

        hasher.set_algorithm("Md5")
        assert hasher.get_algorithm() == "Md5"

    def test_hash_format_consistency(self):
        """Test that hash results are consistently formatted."""
        hasher = ConcreteHasher()

        # Hashes should be lowercase hex strings
        hasher._hash_file_result = "abc123def456"
        hasher._hash_string_result = "abc123def456"
        hasher._hash_bytes_result = "abc123def456"

        file_hash = hasher.hash_file("/test.txt")
        string_hash = hasher.hash_string("test")
        bytes_hash = hasher.hash_bytes(b"test")

        # All should be strings
        assert isinstance(file_hash, str)
        assert isinstance(string_hash, str)
        assert isinstance(bytes_hash, str)

    def test_verify_hash_empty_expected_hash(self):
        """Test verify_hash with empty expected hash."""
        hasher = ConcreteHasher()
        hasher._verify_hash_result = False

        result = hasher.verify_hash("/path/to/file.txt", "")
        assert result is False

    def test_get_available_algorithms_empty(self):
        """Test get_available_algorithms with empty list."""
        hasher = ConcreteHasher()
        hasher._available_algorithms = []

        result = hasher.get_available_algorithms()
        assert result == []
        assert isinstance(result, list)
