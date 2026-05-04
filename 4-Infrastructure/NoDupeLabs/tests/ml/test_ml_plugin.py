# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/ml/ml_plugin.py - MLTool."""

from unittest.mock import MagicMock, patch

import pytest

# Import directly from the plugin file to avoid __init__.py import chain issues
from nodupe.tools.ml import ml_plugin

MLTool = ml_plugin.MLTool
register_tool = ml_plugin.register_tool


class TestMLToolProperties:
    """Test MLTool properties."""

    def test_name_property(self):
        """MLTool.name returns correct value."""
        tool = MLTool()
        assert tool.name == "ml_tool"

    def test_version_property(self):
        """MLTool.version returns correct value."""
        tool = MLTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """MLTool.dependencies returns empty list."""
        tool = MLTool()
        assert tool.dependencies == []


class TestMLToolInitialization:
    """Test MLTool initialization."""

    def test_init_creates_backend(self):
        """MLTool initializes with a backend."""
        tool = MLTool()
        assert tool.backend is not None

    def test_api_methods_property(self):
        """MLTool.api_methods returns correct methods."""
        tool = MLTool()
        api_methods = tool.api_methods

        assert 'generate_embeddings' in api_methods
        assert 'get_dimensions' in api_methods
        assert 'is_available' in api_methods

        # Verify they are bound to backend methods
        assert api_methods['generate_embeddings'] == tool.backend.generate_embeddings
        assert api_methods['get_dimensions'] == tool.backend.get_embedding_dimensions
        assert api_methods['is_available'] == tool.backend.is_available

    def test_api_methods_are_callable(self):
        """MLTool.api_methods returns callable methods."""
        tool = MLTool()
        api_methods = tool.api_methods

        assert callable(api_methods['generate_embeddings'])
        assert callable(api_methods['get_dimensions'])
        assert callable(api_methods['is_available'])


class TestMLToolInitialize:
    """Test MLTool.initialize() method."""

    def test_initialize_registers_service(self):
        """initialize() registers ml_backend service."""
        tool = MLTool()
        container = MagicMock()

        tool.initialize(container)

        container.register_service.assert_called_once_with('ml_backend', tool.backend)

    def test_initialize_with_mock_container(self):
        """initialize() works with mock container."""
        tool = MLTool()
        container = MagicMock()
        container.register_service = MagicMock()

        tool.initialize(container)

        assert container.register_service.called

    def test_initialize_preserves_backend(self):
        """initialize() preserves the backend reference."""
        tool = MLTool()
        container = MagicMock()
        original_backend = tool.backend

        tool.initialize(container)

        assert tool.backend is original_backend


class TestMLToolShutdown:
    """Test MLTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = MLTool()
        # Should not raise
        tool.shutdown()

    def test_shutdown_multiple_times(self):
        """shutdown() can be called multiple times without error."""
        tool = MLTool()
        tool.shutdown()
        tool.shutdown()  # Should not raise

    def test_shutdown_before_initialize(self):
        """shutdown() works even if initialize was not called."""
        tool = MLTool()
        tool.shutdown()  # Should not raise


class TestMLToolGetCapabilities:
    """Test MLTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary with expected keys."""
        tool = MLTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'dimensions' in capabilities
        assert 'available' in capabilities

    def test_get_capabilities_dimensions(self):
        """get_capabilities() returns integer for dimensions."""
        tool = MLTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['dimensions'], int)
        # Default is 128
        assert capabilities['dimensions'] == 128

    def test_get_capabilities_available(self):
        """get_capabilities() returns boolean for available."""
        tool = MLTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['available'], bool)

    def test_get_capabilities_with_mocked_backend(self):
        """get_capabilities() uses backend info correctly."""
        tool = MLTool()
        tool.backend.get_embedding_dimensions = MagicMock(return_value=512)
        tool.backend.is_available = MagicMock(return_value=True)

        capabilities = tool.get_capabilities()

        assert capabilities['dimensions'] == 512
        assert capabilities['available'] is True

    def test_get_capabilities_backend_unavailable(self):
        """get_capabilities() handles unavailable backend."""
        tool = MLTool()
        tool.backend.is_available = MagicMock(return_value=False)

        capabilities = tool.get_capabilities()

        assert capabilities['available'] is False


class TestRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_ml_tool(self):
        """register_tool() returns an MLTool instance."""
        tool = register_tool()
        assert isinstance(tool, MLTool)

    def test_register_tool_creates_new_instance(self):
        """register_tool() creates a new instance each call."""
        tool1 = register_tool()
        tool2 = register_tool()
        assert tool1 is not tool2

    def test_register_tool_properties(self):
        """register_tool() returns tool with correct properties."""
        tool = register_tool()
        assert tool.name == "ml_tool"
        assert tool.version == "1.0.0"
        assert tool.dependencies == []


class TestMLToolDescribeUsage:
    """Test MLTool.describe_usage() method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        tool = MLTool()
        description = tool.describe_usage()

        assert isinstance(description, str)
        assert "machine learning" in description.lower()

    def test_describe_usage_mentions_onnx(self):
        """describe_usage() mentions ONNX support."""
        tool = MLTool()
        description = tool.describe_usage()

        assert "onnx" in description.lower()

    def test_describe_usage_mentions_cpu_fallback(self):
        """describe_usage() mentions CPU fallback."""
        tool = MLTool()
        description = tool.describe_usage()

        assert "cpu" in description.lower() or "fallback" in description.lower()

    def test_describe_usage_mentions_embedding(self):
        """describe_usage() mentions embedding generation."""
        tool = MLTool()
        description = tool.describe_usage()

        assert "embedding" in description.lower()


class TestMLToolRunStandalone:
    """Test MLTool.run_standalone() method."""

    def test_run_standalone_returns_zero(self, capsys):
        """run_standalone() returns 0 and prints output."""
        tool = MLTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        assert "ML Tool: Self-test mode." in captured.out
        assert "Backend available:" in captured.out
        assert "Embedding dimensions:" in captured.out

    def test_run_standalone_with_args(self, capsys):
        """run_standalone() handles args parameter."""
        tool = MLTool()
        result = tool.run_standalone(['--verbose', '--test'])

        assert result == 0

    def test_run_standalone_empty_args(self, capsys):
        """run_standalone() works with empty args."""
        tool = MLTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        assert "ML Tool: Self-test mode." in captured.out

    def test_run_standalone_with_various_args(self, capsys):
        """run_standalone() handles various argument formats."""
        tool = MLTool()

        # Test with different argument formats
        for args in [['--help'], ['-v'], ['test', 'arg1', 'arg2'], []]:
            result = tool.run_standalone(args)
            assert result == 0


class TestMLToolWithMockedBackend:
    """Test MLTool with mocked backend for complete coverage."""

    @patch('nodupe.tools.ml.ml_plugin.get_ml_backend')
    def test_with_mocked_onnx_backend(self, mock_get_backend):
        """Test with mocked ONNX backend."""
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.get_embedding_dimensions.return_value = 768
        mock_backend.generate_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_get_backend.return_value = mock_backend

        tool = MLTool()

        assert tool.backend.is_available() is True
        caps = tool.get_capabilities()
        assert caps['dimensions'] == 768
        assert caps['available'] is True

    @patch('nodupe.tools.ml.ml_plugin.get_ml_backend')
    def test_with_mocked_cpu_backend(self, mock_get_backend):
        """Test with mocked CPU backend."""
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.get_embedding_dimensions.return_value = 128
        mock_get_backend.return_value = mock_backend

        tool = MLTool()

        caps = tool.get_capabilities()
        assert caps['dimensions'] == 128

    @patch('nodupe.tools.ml.ml_plugin.get_ml_backend')
    def test_api_methods_call_backend(self, mock_get_backend):
        """Test that api_methods correctly call backend methods."""
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.get_embedding_dimensions.return_value = 128
        mock_backend.generate_embeddings.return_value = [[0.1, 0.2]]
        mock_get_backend.return_value = mock_backend

        tool = MLTool()

        # Test generate_embeddings
        tool.api_methods['generate_embeddings'](['test'])
        mock_backend.generate_embeddings.assert_called_once()

        # Test get_dimensions
        tool.api_methods['get_dimensions']()
        mock_backend.get_embedding_dimensions.assert_called_once()

        # Test is_available
        tool.api_methods['is_available']()
        mock_backend.is_available.assert_called_once()


class TestMLToolEdgeCases:
    """Test MLTool edge cases."""

    @patch('nodupe.tools.ml.ml_plugin.get_ml_backend')
    def test_backend_raises_exception(self, mock_get_backend):
        """Test handling when backend raises exception."""
        mock_backend = MagicMock()
        mock_backend.is_available.side_effect = Exception("Backend error")
        mock_get_backend.return_value = mock_backend

        tool = MLTool()

        with pytest.raises(Exception, match="Backend error"):
            tool.backend.is_available()

    @patch('nodupe.tools.ml.ml_plugin.get_ml_backend')
    def test_backend_returns_invalid_dimensions(self, mock_get_backend):
        """Test handling when backend returns invalid dimensions."""
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.get_embedding_dimensions.return_value = -1
        mock_get_backend.return_value = mock_backend

        tool = MLTool()

        caps = tool.get_capabilities()
        assert caps['dimensions'] == -1

    def test_tool_instantiation_multiple_times(self):
        """Test that multiple tool instances can be created."""
        tool1 = MLTool()
        tool2 = MLTool()

        assert tool1 is not tool2
        assert tool1.name == tool2.name
        assert tool1.version == tool2.version

    @patch('nodupe.tools.ml.ml_plugin.get_ml_backend')
    def test_backend_none_dimensions(self, mock_get_backend):
        """Test handling when backend returns None for dimensions."""
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.get_embedding_dimensions.return_value = None
        mock_get_backend.return_value = mock_backend

        tool = MLTool()

        caps = tool.get_capabilities()
        assert caps['dimensions'] is None
