# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for nodupe/tools/network/network_plugin.py - NetworkTool."""

from unittest.mock import MagicMock, patch

import pytest

# Import directly from the plugin file to avoid __init__.py import chain issues
from nodupe.tools.network import network_plugin

NetworkTool = network_plugin.NetworkTool
register_tool = network_plugin.register_tool


class TestNetworkToolProperties:
    """Test NetworkTool properties."""

    def test_name_property(self):
        """NetworkTool.name returns correct value."""
        tool = NetworkTool()
        assert tool.name == "network_tool"

    def test_version_property(self):
        """NetworkTool.version returns correct value."""
        tool = NetworkTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """NetworkTool.dependencies returns empty list."""
        tool = NetworkTool()
        assert tool.dependencies == []


class TestNetworkToolInitialization:
    """Test NetworkTool initialization."""

    def test_init_creates_manager(self):
        """NetworkTool initializes with a manager."""
        tool = NetworkTool()
        assert tool.manager is not None

    def test_api_methods_property(self):
        """NetworkTool.api_methods returns correct methods."""
        tool = NetworkTool()
        api_methods = tool.api_methods

        assert 'upload_file' in api_methods
        assert 'download_file' in api_methods
        assert 'list_files' in api_methods
        assert 'delete_file' in api_methods

        # Verify they are bound to manager methods
        assert api_methods['upload_file'] == tool.manager.upload_file
        assert api_methods['download_file'] == tool.manager.download_file
        assert api_methods['list_files'] == tool.manager.list_files
        assert api_methods['delete_file'] == tool.manager.delete_file

    def test_api_methods_are_callable(self):
        """NetworkTool.api_methods returns callable methods."""
        tool = NetworkTool()
        api_methods = tool.api_methods

        assert callable(api_methods['upload_file'])
        assert callable(api_methods['download_file'])
        assert callable(api_methods['list_files'])
        assert callable(api_methods['delete_file'])


class TestNetworkToolInitialize:
    """Test NetworkTool.initialize() method."""

    def test_initialize_registers_service(self):
        """initialize() registers network_manager service."""
        tool = NetworkTool()
        container = MagicMock()

        tool.initialize(container)

        container.register_service.assert_called_once_with('network_manager', tool.manager)

    def test_initialize_with_mock_container(self):
        """initialize() works with mock container."""
        tool = NetworkTool()
        container = MagicMock()
        container.register_service = MagicMock()

        tool.initialize(container)

        assert container.register_service.called

    def test_initialize_preserves_manager(self):
        """initialize() preserves the manager reference."""
        tool = NetworkTool()
        container = MagicMock()
        original_manager = tool.manager

        tool.initialize(container)

        assert tool.manager is original_manager


class TestNetworkToolShutdown:
    """Test NetworkTool.shutdown() method."""

    def test_shutdown_no_error(self):
        """shutdown() completes without error."""
        tool = NetworkTool()
        # Should not raise
        tool.shutdown()

    def test_shutdown_multiple_times(self):
        """shutdown() can be called multiple times without error."""
        tool = NetworkTool()
        tool.shutdown()
        tool.shutdown()  # Should not raise

    def test_shutdown_before_initialize(self):
        """shutdown() works even if initialize was not called."""
        tool = NetworkTool()
        tool.shutdown()  # Should not raise


class TestNetworkToolGetCapabilities:
    """Test NetworkTool.get_capabilities() method."""

    def test_get_capabilities_returns_dict(self):
        """get_capabilities() returns a dictionary with expected keys."""
        tool = NetworkTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities, dict)
        assert 'storage_backend' in capabilities
        assert 'available' in capabilities

    def test_get_capabilities_storage_backend(self):
        """get_capabilities() returns string for storage_backend."""
        tool = NetworkTool()
        capabilities = tool.get_capabilities()

        assert isinstance(capabilities['storage_backend'], str)
        # Should be either LocalStorageBackend or S3StorageBackend depending on availability
        assert capabilities['storage_backend'] in ['LocalStorageBackend', 'S3StorageBackend']

    def test_get_capabilities_available(self):
        """get_capabilities() returns True for available."""
        tool = NetworkTool()
        capabilities = tool.get_capabilities()

        assert capabilities['available'] is True

    def test_get_capabilities_with_mocked_manager(self):
        """get_capabilities() uses manager info correctly."""
        tool = NetworkTool()
        mock_storage = MagicMock()
        mock_storage.__class__.__name__ = 'MockStorageBackend'
        tool.manager.storage_backend = mock_storage

        capabilities = tool.get_capabilities()

        assert capabilities['storage_backend'] == 'MockStorageBackend'


class TestRegisterTool:
    """Test register_tool() function."""

    def test_register_tool_returns_network_tool(self):
        """register_tool() returns a NetworkTool instance."""
        tool = register_tool()
        assert isinstance(tool, NetworkTool)

    def test_register_tool_creates_new_instance(self):
        """register_tool() creates a new instance each call."""
        tool1 = register_tool()
        tool2 = register_tool()
        assert tool1 is not tool2

    def test_register_tool_properties(self):
        """register_tool() returns tool with correct properties."""
        tool = register_tool()
        assert tool.name == "network_tool"
        assert tool.version == "1.0.0"
        assert tool.dependencies == []


class TestNetworkToolDescribeUsage:
    """Test NetworkTool.describe_usage() method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        tool = NetworkTool()
        description = tool.describe_usage()

        assert isinstance(description, str)
        assert "network" in description.lower() or "storage" in description.lower()

    def test_describe_usage_mentions_s3(self):
        """describe_usage() mentions S3 support."""
        tool = NetworkTool()
        description = tool.describe_usage()

        assert "s3" in description.lower()

    def test_describe_usage_mentions_local(self):
        """describe_usage() mentions local filesystem."""
        tool = NetworkTool()
        description = tool.describe_usage()

        assert "local" in description.lower()

    def test_describe_usage_mentions_operations(self):
        """describe_usage() mentions file operations."""
        tool = NetworkTool()
        description = tool.describe_usage()

        assert "upload" in description.lower() or "download" in description.lower()


class TestNetworkToolRunStandalone:
    """Test NetworkTool.run_standalone() method."""

    def test_run_standalone_returns_zero(self, capsys):
        """run_standalone() returns 0 and prints output."""
        tool = NetworkTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        assert "Network Tool: Self-test mode." in captured.out
        assert "Storage backend:" in captured.out
        assert "Available:" in captured.out

    def test_run_standalone_with_args(self, capsys):
        """run_standalone() handles args parameter."""
        tool = NetworkTool()
        result = tool.run_standalone(['--verbose', '--test'])

        assert result == 0

    def test_run_standalone_empty_args(self, capsys):
        """run_standalone() works with empty args."""
        tool = NetworkTool()
        result = tool.run_standalone([])

        assert result == 0
        captured = capsys.readouterr()
        assert "Network Tool: Self-test mode." in captured.out

    def test_run_standalone_with_various_args(self, capsys):
        """run_standalone() handles various argument formats."""
        tool = NetworkTool()

        # Test with different argument formats
        for args in [['--help'], ['-v'], ['test', 'arg1', 'arg2'], []]:
            result = tool.run_standalone(args)
            assert result == 0


class TestNetworkToolWithMockedManager:
    """Test NetworkTool with mocked manager for complete coverage."""

    @patch('nodupe.tools.network.network_plugin.get_network_manager')
    def test_with_mocked_s3_backend(self, mock_get_manager):
        """Test with mocked S3 backend."""
        mock_manager = MagicMock()
        mock_storage = MagicMock()
        mock_storage.__class__.__name__ = 'S3StorageBackend'
        mock_manager.storage_backend = mock_storage
        mock_get_manager.return_value = mock_manager

        tool = NetworkTool()

        caps = tool.get_capabilities()
        assert caps['storage_backend'] == 'S3StorageBackend'
        assert caps['available'] is True

    @patch('nodupe.tools.network.network_plugin.get_network_manager')
    def test_with_mocked_local_backend(self, mock_get_manager):
        """Test with mocked Local backend."""
        mock_manager = MagicMock()
        mock_storage = MagicMock()
        mock_storage.__class__.__name__ = 'LocalStorageBackend'
        mock_manager.storage_backend = mock_storage
        mock_get_manager.return_value = mock_manager

        tool = NetworkTool()

        caps = tool.get_capabilities()
        assert caps['storage_backend'] == 'LocalStorageBackend'

    @patch('nodupe.tools.network.network_plugin.get_network_manager')
    def test_api_methods_call_manager(self, mock_get_manager):
        """Test that api_methods correctly call manager methods."""
        mock_manager = MagicMock()
        mock_storage = MagicMock()
        mock_manager.storage_backend = mock_storage
        mock_manager.upload_file.return_value = True
        mock_manager.download_file.return_value = True
        mock_manager.list_files.return_value = ['file1.txt']
        mock_manager.delete_file.return_value = True
        mock_get_manager.return_value = mock_manager

        tool = NetworkTool()

        # Test upload_file
        tool.api_methods['upload_file']('local.txt', 'remote.txt')
        mock_manager.upload_file.assert_called_once()

        # Test download_file
        tool.api_methods['download_file']('remote.txt', 'local.txt')
        mock_manager.download_file.assert_called_once()

        # Test list_files
        tool.api_methods['list_files']('prefix')
        mock_manager.list_files.assert_called_once()

        # Test delete_file
        tool.api_methods['delete_file']('remote.txt')
        mock_manager.delete_file.assert_called_once()


class TestNetworkToolEdgeCases:
    """Test NetworkTool edge cases."""

    @patch('nodupe.tools.network.network_plugin.get_network_manager')
    def test_manager_raises_exception(self, mock_get_manager):
        """Test handling when manager raises exception."""
        mock_manager = MagicMock()
        mock_manager.storage_backend = MagicMock()
        mock_manager.upload_file.side_effect = Exception("Upload error")
        mock_get_manager.return_value = mock_manager

        tool = NetworkTool()

        with pytest.raises(Exception, match="Upload error"):
            tool.manager.upload_file('local.txt', 'remote.txt')

    @patch('nodupe.tools.network.network_plugin.get_network_manager')
    def test_manager_returns_false(self, mock_get_manager):
        """Test handling when manager operations return False."""
        mock_manager = MagicMock()
        mock_storage = MagicMock()
        mock_manager.storage_backend = mock_storage
        mock_manager.upload_file.return_value = False
        mock_manager.download_file.return_value = False
        mock_manager.list_files.return_value = []
        mock_manager.delete_file.return_value = False
        mock_get_manager.return_value = mock_manager

        tool = NetworkTool()

        assert tool.manager.upload_file('local.txt', 'remote.txt') is False
        assert tool.manager.download_file('remote.txt', 'local.txt') is False
        assert tool.manager.list_files('prefix') == []
        assert tool.manager.delete_file('remote.txt') is False

    def test_tool_instantiation_multiple_times(self):
        """Test that multiple tool instances can be created."""
        tool1 = NetworkTool()
        tool2 = NetworkTool()

        assert tool1 is not tool2
        assert tool1.name == tool2.name
        assert tool1.version == tool2.version

    @patch('nodupe.tools.network.network_plugin.get_network_manager')
    def test_manager_storage_backend_none(self, mock_get_manager):
        """Test handling when manager has no storage backend."""
        mock_manager = MagicMock()
        mock_manager.storage_backend = None
        mock_get_manager.return_value = mock_manager

        tool = NetworkTool()

        # MagicMock returns 'NoneType' when accessing __class__.__name__ on None
        caps = tool.get_capabilities()
        assert caps['storage_backend'] == 'NoneType'
        assert caps['available'] is True
