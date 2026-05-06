# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/gpu/gpu_plugin.py - GPUBackendTool."""

from unittest.mock import MagicMock, patch

import pytest

# Import directly from the plugin file to avoid __init__.py import chain issues
from nodupe.tools.gpu import gpu_plugin

GPUBackendTool = gpu_plugin.GPUBackendTool
register_tool = gpu_plugin.register_tool


class TestGPUBackendToolProperties:
    """Test GPUBackendTool properties."""

    def test_name_property(self):
        """GPUBackendTool.name returns correct value."""
        tool = GPUBackendTool()
        assert tool.name == "gpu_acceleration"

    def test_version_property(self):
        """GPUBackendTool.version returns correct value."""
        tool = GPUBackendTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """GPUBackendTool.dependencies returns empty list."""
        tool = GPUBackendTool()
        assert tool.dependencies == []


class TestGPUBackendToolInitialization:
    """Test GPUBackendTool initialization."""

    def test_init_creates_backend(self):
        """GPUBackendTool initializes with a backend."""
        tool = GPUBackendTool()
        assert tool.backend is not None

    def test_api_methods_property(self):
        """GPUBackendTool.api_methods returns correct methods."""
        tool = GPUBackendTool()
        api_methods = tool.api_methods

        assert 'compute_embeddings' in api_methods
        assert 'matrix_multiply' in api_methods
        assert 'get_device_info' in api_methods
        assert 'is_available' in api_methods

        # Verify they are bound to backend methods
        assert api_methods['compute_embeddings'] == tool.backend.compute_embeddings
        assert api_methods['matrix_multiply'] == tool.backend.matrix_multiply
        assert api_methods['get_device_info'] == tool.backend.get_device_info
        assert api_methods['is_available'] == tool.backend.is_available


class TestGPUBackendToolInitialize:
    """Test GPUBackendTool.initialize() method."""

    def test_initialize_registers_service(self):
        """initialize() registers gpu_backend service."""
        tool = GPUBackendTool()
        container = MagicMock()

        tool.initialize(container)

        container.register_service.assert_called_once_with('gpu_backend', tool.backend)

    def test_initialize_with_mock_container(self):
        """initialize() works with mock container."""
        tool = GPUBackendTool()
        container = MagicMock()
        container.register_service = MagicMock()

        tool.initialize(container)

        assert container.register_service.called


class TestGPUBackendToolShutdown:
    """Test GPUBackendTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = GPUBackendTool()
        # Should not raise
        tool.shutdown()

    def test_shutdown_multiple_times(self):
        """shutdown() can be called multiple times without error."""
        tool = GPUBackendTool()
        tool.shutdown()
        tool.shutdown()  # Should not raise


class TestGPUBackendToolGetCapabilities:
    """Test GPUBackendTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary with expected keys."""
        tool = GPUBackendTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'device_type' in capabilities
        assert 'device_name' in capabilities
        assert 'available' in capabilities

    def test_get_capabilities_device_type(self):
        """get_capabilities() returns correct device_type from backend."""
        tool = GPUBackendTool()
        capabilities = tool.get_capabilities()

        # Should be 'cpu' since we use CPU fallback by default
        assert capabilities['device_type'] in ['cpu', 'cuda', 'metal', 'unknown']

    def test_get_capabilities_available(self):
        """get_capabilities() returns boolean for available."""
        tool = GPUBackendTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['available'], bool)

    def test_get_capabilities_with_mocked_backend(self):
        """get_capabilities() uses backend info correctly."""
        tool = GPUBackendTool()
        # Mock the backend's get_device_info
        tool.backend.get_device_info = MagicMock(return_value={
            'type': 'test_gpu',
            'name': 'Test GPU',
            'memory': '8GB'
        })

        capabilities = tool.get_capabilities()

        assert capabilities['device_type'] == 'test_gpu'
        assert capabilities['device_name'] == 'Test GPU'

    def test_get_capabilities_unknown_device_type(self):
        """get_capabilities() handles missing device type."""
        tool = GPUBackendTool()
        tool.backend.get_device_info = MagicMock(return_value={})

        capabilities = tool.get_capabilities()

        assert capabilities['device_type'] == 'unknown'
        assert capabilities['device_name'] == 'unknown'


class TestRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_gpu_backend_tool(self):
        """register_tool() returns a GPUBackendTool instance."""
        tool = register_tool()
        assert isinstance(tool, GPUBackendTool)

    def test_register_tool_creates_new_instance(self):
        """register_tool() creates a new instance each call."""
        tool1 = register_tool()
        tool2 = register_tool()
        assert tool1 is not tool2


class TestGPUBackendToolDescribeUsage:
    """Test GPUBackendTool.describe_usage() method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        tool = GPUBackendTool()
        description = tool.describe_usage()

        assert isinstance(description, str)
        assert "hardware acceleration" in description.lower()

    def test_describe_usage_mentions_cuda(self):
        """describe_usage() mentions CUDA support."""
        tool = GPUBackendTool()
        description = tool.describe_usage()

        assert "cuda" in description.lower()

    def test_describe_usage_mentions_metal(self):
        """describe_usage() mentions Metal support."""
        tool = GPUBackendTool()
        description = tool.describe_usage()

        assert "metal" in description.lower()

    def test_describe_usage_mentions_cpu_fallback(self):
        """describe_usage() mentions CPU fallback."""
        tool = GPUBackendTool()
        description = tool.describe_usage()

        assert "cpu" in description.lower() or "fallback" in description.lower()


class TestGPUBackendToolRunStandalone:
    """Test GPUBackendTool.run_standalone() method."""

    def test_run_standalone_returns_zero(self, capsys):
        """run_standalone() returns 0 and prints output."""
        tool = GPUBackendTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        assert "GPU Backend Tool: Self-test mode." in captured.out
        assert "Backend available:" in captured.out
        assert "Device info:" in captured.out

    def test_run_standalone_with_args(self, capsys):
        """run_standalone() handles args parameter."""
        tool = GPUBackendTool()
        result = tool.run_standalone(['--verbose', '--test'])

        assert result == 0

    def test_run_standalone_empty_args(self, capsys):
        """run_standalone() works with empty args."""
        tool = GPUBackendTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        assert "GPU Backend Tool: Self-test mode." in captured.out


class TestGPUBackendToolWithMockedBackend:
    """Test GPUBackendTool with mocked backend for complete coverage."""

    @patch('nodupe.tools.gpu.gpu_plugin.get_gpu_backend')
    def test_with_mocked_cuda_backend(self, mock_get_backend):
        """Test with mocked CUDA backend."""
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.get_device_info.return_value = {
            'type': 'cuda',
            'name': 'NVIDIA GeForce RTX 3080',
            'memory': '10GB'
        }
        mock_backend.compute_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_backend.matrix_multiply.return_value = [[1.0, 0.0], [0.0, 1.0]]
        mock_get_backend.return_value = mock_backend

        tool = GPUBackendTool()

        assert tool.backend.is_available() is True
        caps = tool.get_capabilities()
        assert caps['device_type'] == 'cuda'
        assert caps['available'] is True

    @patch('nodupe.tools.gpu.gpu_plugin.get_gpu_backend')
    def test_with_mocked_metal_backend(self, mock_get_backend):
        """Test with mocked Metal backend."""
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.get_device_info.return_value = {
            'type': 'metal',
            'name': 'Apple M1',
            'memory': 'Integrated'
        }
        mock_get_backend.return_value = mock_backend

        tool = GPUBackendTool()

        caps = tool.get_capabilities()
        assert caps['device_type'] == 'metal'

    @patch('nodupe.tools.gpu.gpu_plugin.get_gpu_backend')
    def test_with_mocked_cpu_backend(self, mock_get_backend):
        """Test with mocked CPU backend."""
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.get_device_info.return_value = {
            'type': 'cpu',
            'name': 'CPU Fallback',
            'memory': 'N/A'
        }
        mock_get_backend.return_value = mock_backend

        tool = GPUBackendTool()

        caps = tool.get_capabilities()
        assert caps['device_type'] == 'cpu'

    @patch('nodupe.tools.gpu.gpu_plugin.get_gpu_backend')
    def test_api_methods_call_backend(self, mock_get_backend):
        """Test that api_methods correctly call backend methods."""
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.get_device_info.return_value = {'type': 'cpu', 'name': 'CPU'}
        mock_backend.compute_embeddings.return_value = [[0.1, 0.2]]
        mock_backend.matrix_multiply.return_value = [[1.0]]
        mock_get_backend.return_value = mock_backend

        tool = GPUBackendTool()

        # Test compute_embeddings
        tool.api_methods['compute_embeddings']([[1, 2, 3]])
        mock_backend.compute_embeddings.assert_called_once()

        # Test matrix_multiply
        tool.api_methods['matrix_multiply']([[1]], [[1]])
        mock_backend.matrix_multiply.assert_called_once()

        # Test get_device_info
        tool.api_methods['get_device_info']()
        mock_backend.get_device_info.assert_called_once()

        # Test is_available
        tool.api_methods['is_available']()
        mock_backend.is_available.assert_called_once()


class TestGPUBackendToolEdgeCases:
    """Test GPUBackendTool edge cases."""

    @patch('nodupe.tools.gpu.gpu_plugin.get_gpu_backend')
    def test_backend_raises_exception(self, mock_get_backend):
        """Test handling when backend raises exception."""
        mock_backend = MagicMock()
        mock_backend.is_available.side_effect = Exception("Backend error")
        mock_get_backend.return_value = mock_backend

        tool = GPUBackendTool()

        with pytest.raises(Exception, match="Backend error"):
            tool.backend.is_available()

    @patch('nodupe.tools.gpu.gpu_plugin.get_gpu_backend')
    def test_backend_returns_none_info(self, mock_get_backend):
        """Test handling when backend returns None for device info."""
        mock_backend = MagicMock()
        mock_backend.is_available.return_value = True
        mock_backend.get_device_info.return_value = None
        mock_get_backend.return_value = mock_backend

        tool = GPUBackendTool()

        # Should handle None gracefully
        caps = tool.get_capabilities()
        assert caps['device_type'] == 'unknown'
        assert caps['device_name'] == 'unknown'

    def test_tool_instantiation_multiple_times(self):
        """Test that multiple tool instances can be created."""
        tool1 = GPUBackendTool()
        tool2 = GPUBackendTool()

        assert tool1 is not tool2
        assert tool1.name == tool2.name
        assert tool1.version == tool2.version
