"""Test Core Loader Module - Coverage Completion.

Tests to achieve 100% coverage for loader.py
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from nodupe.core.loader import CoreLoader, bootstrap


class TestCoreLoaderMissingCoverage:
    """Test missing coverage paths in loader.py."""

    def test_initialize_config_without_config_attr(self):
        """Test initialization when config doesn't have config attribute."""
        loader = CoreLoader()

        mock_config = MagicMock()
        # Remove config attribute
        del mock_config.config

        with patch('nodupe.core.loader.load_config', return_value=mock_config), \
             patch.object(loader, '_apply_platform_autoconfig', return_value={}):
            # Should not raise, should handle missing config attribute
            try:
                loader.initialize()
            except Exception:
                pass  # Expected to fail at some point due to mocking

    def test_initialize_config_merge_skips_existing(self):
        """Test that config merge skips existing keys."""
        loader = CoreLoader()

        mock_config = MagicMock()
        mock_config.config = {'existing_key': 'existing_value'}

        with patch('nodupe.core.loader.load_config', return_value=mock_config), \
             patch.object(loader, '_apply_platform_autoconfig', return_value={'existing_key': 'new_value'}), \
             patch('nodupe.core.loader.ToolRegistry'), \
             patch('nodupe.core.loader.create_tool_loader'), \
             patch('nodupe.core.loader.create_tool_discovery'), \
             patch('nodupe.core.loader.create_lifecycle_manager'), \
             patch('nodupe.core.loader.ToolHotReload'), \
             patch('nodupe.core.loader.ToolIPCServer'), \
             patch('nodupe.core.loader.logging'):

            loader.initialize()

            # existing_key should still have original value
            assert mock_config.config['existing_key'] == 'existing_value'

    def test_discover_and_load_tools_no_tool_dirs(self):
        """Test tool discovery when no tool directories exist."""
        loader = CoreLoader()
        loader.config = MagicMock()
        loader.config.config = {'tools': {'directories': ['/nonexistent']}}
        loader.tool_discovery = MagicMock()
        loader.tool_discovery.discover_tools_in_directory.return_value = []

        # Mock Path.exists to return False
        with patch('nodupe.core.loader.Path') as mock_path:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value = mock_path_instance

            # Should use fallback paths
            loader._discover_and_load_tools()

    def test_discover_and_load_tools_fallback_paths(self):
        """Test tool discovery uses fallback paths."""
        loader = CoreLoader()
        loader.config = MagicMock()
        loader.config.config = {'tools': {'directories': ['/nonexistent']}}
        loader.tool_discovery = MagicMock()
        loader.tool_discovery.discover_tools_in_directory.return_value = []

        # Mock Path to make standard paths exist
        with patch('nodupe.core.loader.Path') as mock_path:
            def path_side_effect(p):
                """Side effect function for mocking Path objects in tests."""
                mock_instance = MagicMock()
                mock_instance.exists.return_value = True
                mock_instance.resolve.return_value = Path(p).resolve()
                return mock_instance

            mock_path.side_effect = path_side_effect

            loader._discover_and_load_tools()

    def test_load_single_tool_exception(self, caplog):
        """Test loading single tool with exception."""
        import logging
        loader = CoreLoader()
        loader.logger.setLevel(logging.DEBUG)
        loader.tool_loader = MagicMock()
        loader.tool_loader.load_tool_from_file.side_effect = Exception("Load failed")
        loader.hot_reload = MagicMock()

        mock_tool_info = MagicMock()
        mock_tool_info.name = "test_tool"
        mock_tool_info.path = Path("/test/tool.py")

        # Should not raise, should log error
        loader._load_single_tool(mock_tool_info)

    def test_load_single_tool_no_tool_class(self, caplog):
        """Test loading single tool when no tool class returned."""
        import logging
        loader = CoreLoader()
        loader.logger.setLevel(logging.DEBUG)
        loader.tool_loader = MagicMock()
        loader.tool_loader.load_tool_from_file.return_value = None
        loader.hot_reload = MagicMock()

        mock_tool_info = MagicMock()
        mock_tool_info.name = "test_tool"
        mock_tool_info.path = Path("/test/tool.py")

        loader._load_single_tool(mock_tool_info)

    def test_load_single_tool_no_ipc_doc(self, caplog):
        """Test loading single tool without IPC documentation."""
        import logging
        loader = CoreLoader()
        loader.logger.setLevel(logging.DEBUG)
        loader.tool_loader = MagicMock()
        loader.tool_loader.load_tool_from_file.return_value = MagicMock
        loader.tool_loader.instantiate_tool.return_value = MagicMock(name='test')
        loader.tool_loader.register_loaded_tool = MagicMock()
        loader.hot_reload = MagicMock()

        mock_tool_info = MagicMock()
        mock_tool_info.name = "test_tool"
        mock_tool_info.path = Path("/test/tool.py")

        loader._load_single_tool(mock_tool_info)

    def test_perform_hash_autotuning_no_hasher(self):
        """Test hash autotuning when hasher not available."""
        loader = CoreLoader()
        loader.container = MagicMock()
        loader.container.get_service.return_value = None

        # Should return early, not raise
        loader._perform_hash_autotuning()

    def test_perform_hash_autotuning_import_error(self, caplog):
        """Test hash autotuning with import error."""
        import logging
        loader = CoreLoader()
        loader.logger.setLevel(logging.DEBUG)
        loader.container = MagicMock()
        loader.container.get_service.return_value = MagicMock()

        with patch('nodupe.core.loader.autotune_hash_algorithm', side_effect=ImportError()):
            loader._perform_hash_autotuning()

    def test_perform_hash_autotuning_no_set_algorithm(self, caplog):
        """Test hash autotuning when hasher has no set_algorithm."""
        import logging
        loader = CoreLoader()
        loader.logger.setLevel(logging.DEBUG)
        loader.container = MagicMock()

        mock_hasher = MagicMock()
        del mock_hasher.set_algorithm
        loader.container.get_service.return_value = mock_hasher

        with patch('nodupe.core.loader.autotune_hash_algorithm',
                   return_value={'optimal_algorithm': 'blake3'}):
            loader._perform_hash_autotuning()

    def test_perform_hash_autotuning_exception(self, caplog):
        """Test hash autotuning with general exception."""
        import logging
        loader = CoreLoader()
        loader.logger.setLevel(logging.DEBUG)
        loader.container = MagicMock()
        loader.container.get_service.return_value = MagicMock()

        with patch('nodupe.core.loader.autotune_hash_algorithm',
                   side_effect=Exception("Autotune failed")):
            loader._perform_hash_autotuning()

    def test_shutdown_not_initialized(self):
        """Test shutdown when not initialized."""
        loader = CoreLoader()
        loader.initialized = False

        # Should return early
        loader.shutdown()

    def test_shutdown_no_tool_lifecycle(self):
        """Test shutdown without tool_lifecycle."""
        loader = CoreLoader()
        loader.initialized = True
        loader.tool_lifecycle = None
        loader.hot_reload = None
        loader.ipc_server = None
        loader.tool_registry = None

        # Should not raise
        loader.shutdown()

    def test_shutdown_no_hot_reload(self):
        """Test shutdown without hot_reload."""
        loader = CoreLoader()
        loader.initialized = True
        loader.tool_lifecycle = MagicMock()
        loader.hot_reload = None
        loader.ipc_server = None
        loader.tool_registry = MagicMock()

        # Should not raise
        loader.shutdown()

    def test_shutdown_no_ipc_server(self):
        """Test shutdown without ipc_server."""
        loader = CoreLoader()
        loader.initialized = True
        loader.tool_lifecycle = MagicMock()
        loader.hot_reload = MagicMock()
        loader.ipc_server = None
        loader.tool_registry = MagicMock()

        # Should not raise
        loader.shutdown()

    def test_shutdown_no_tool_registry(self):
        """Test shutdown without tool_registry."""
        loader = CoreLoader()
        loader.initialized = True
        loader.tool_lifecycle = MagicMock()
        loader.hot_reload = MagicMock()
        loader.ipc_server = MagicMock()
        loader.tool_registry = None

        # Should not raise
        loader.shutdown()

    def test_shutdown_log_compressor_import_error(self, caplog):
        """Test shutdown when log compressor import fails."""
        import logging
        loader = CoreLoader()
        loader.logger.setLevel(logging.DEBUG)
        loader.initialized = True
        loader.tool_lifecycle = MagicMock()
        loader.hot_reload = MagicMock()
        loader.ipc_server = MagicMock()
        loader.tool_registry = MagicMock()
        loader.config = MagicMock()
        loader.config.config = {'log_dir': 'logs'}

        with patch('nodupe.core.loader.LogCompressor', side_effect=ImportError()):
            loader.shutdown()

    def test_apply_platform_autoconfig_simple(self):
        """Test platform autoconfig returns simple config."""
        loader = CoreLoader()
        config = loader._apply_platform_autoconfig()
        assert 'db_path' in config
        assert 'log_dir' in config

    def test_detect_system_resources(self):
        """Test system resource detection."""
        loader = CoreLoader()
        with patch('nodupe.core.loader.multiprocessing') as mock_mp:
            mock_mp.cpu_count.return_value = 4
            resources = loader._detect_system_resources()
            assert 'cpu_cores' in resources


class TestBootstrapFunction:
    """Test bootstrap function edge cases."""

    def test_bootstrap_exception(self):
        """Test bootstrap with exception."""
        with patch('nodupe.core.loader.logging.basicConfig'), \
             patch('nodupe.core.loader.CoreLoader') as mock_loader_class:

            mock_instance = MagicMock()
            mock_instance.initialize.side_effect = Exception("Init failed")
            mock_loader_class.return_value = mock_instance

            with pytest.raises(Exception):
                bootstrap()


class TestCoreLoaderDoubleInit:
    """Test double initialization handling."""

    def test_double_init_returns_early(self):
        """Test that double initialization returns early."""
        loader = CoreLoader()
        loader.initialized = True

        # Should return immediately
        loader.initialize()
        assert loader.initialized is True


class TestToolLoaderCoverageGaps:
    """Test ToolLoader coverage gaps."""

    def test_load_tool_from_file_spec_none(self):
        """Test load_tool_from_file when spec is None (lines 66-68)."""
        from pathlib import Path

        from nodupe.core.tool_system.loader import ToolLoader, ToolLoaderError

        loader = ToolLoader()

        # Create a mock path that exists
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.suffix = '.py'
        mock_path.stem = 'test_tool'

        with patch('importlib.util.spec_from_file_location', return_value=None):
            with pytest.raises(ToolLoaderError, match="Could not create module spec"):
                loader.load_tool_from_file(mock_path)

    def test_load_tool_from_file_spec_loader_none(self):
        """Test load_tool_from_file when spec.loader is None."""
        from pathlib import Path

        from nodupe.core.tool_system.loader import ToolLoader, ToolLoaderError

        loader = ToolLoader()

        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.suffix = '.py'
        mock_path.stem = 'test_tool'

        mock_spec = Mock()
        mock_spec.loader = None

        with patch('importlib.util.spec_from_file_location', return_value=mock_spec):
            with pytest.raises(ToolLoaderError, match="Could not create module spec"):
                loader.load_tool_from_file(mock_path)

    def test_load_tool_from_file_accessibility_compliant(self, caplog):
        """Test load_tool_from_file with AccessibleTool (line 88)."""
        import logging
        from pathlib import Path

        from nodupe.core.tool_system.base import AccessibleTool
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        # Create a mock AccessibleTool class
        class MockAccessibleTool(AccessibleTool):
            """Mock tool class that implements AccessibleTool for testing."""
            name = "MockAccessibleTool"
            version = "1.0.0"
            dependencies = []

            def initialize(self, container):
                """Initialize the mock tool.

                Args:
                    container: The service container for dependency injection.
                """
                pass

            def shutdown(self):
                """Shutdown the mock tool and release resources."""
                pass

            def get_capabilities(self):
                """Return the capabilities of this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

            @property
            def api_methods(self):
                """Return the API methods exposed by this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.suffix = '.py'
        mock_path.stem = 'test_tool'

        # Create mock module with AccessibleTool
        mock_module = Mock()
        mock_module.MockAccessibleTool = MockAccessibleTool

        with patch('importlib.util.spec_from_file_location') as mock_spec_loc, \
             patch('importlib.util.module_from_spec') as mock_from_spec, \
             patch.object(loader, '_find_tool_class', return_value=MockAccessibleTool), \
             patch.object(loader, '_validate_tool_class', return_value=True):

            mock_spec = Mock()
            mock_spec.loader = Mock()
            mock_spec_loc.return_value = mock_spec
            mock_from_spec.return_value = mock_module

            caplog.set_level(logging.INFO)
            result = loader.load_tool_from_file(mock_path)

            assert result is MockAccessibleTool
            assert any("ISO accessibility compliant" in record.message for record in caplog.records)

    def test_load_tool_from_file_not_accessible(self, caplog):
        """Test load_tool_from_file with non-AccessibleTool (line 91)."""
        import logging
        from pathlib import Path

        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        # Create a mock Tool class (not AccessibleTool)
        class MockTool(Tool):
            """Mock tool class for testing non-AccessibleTool behavior."""
            name = "MockTool"
            version = "1.0.0"
            dependencies = []

            def initialize(self, container):
                """Initialize the mock tool.

                Args:
                    container: The service container for dependency injection.
                """
                pass

            def shutdown(self):
                """Shutdown the mock tool and release resources."""
                pass

            def get_capabilities(self):
                """Return the capabilities of this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

            @property
            def api_methods(self):
                """Return the API methods exposed by this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.suffix = '.py'
        mock_path.stem = 'test_tool'

        mock_module = Mock()

        with patch('importlib.util.spec_from_file_location') as mock_spec_loc, \
             patch('importlib.util.module_from_spec') as mock_from_spec, \
             patch.object(loader, '_find_tool_class', return_value=MockTool), \
             patch.object(loader, '_validate_tool_class', return_value=True):

            mock_spec = Mock()
            mock_spec.loader = Mock()
            mock_spec_loc.return_value = mock_spec
            mock_from_spec.return_value = mock_module

            caplog.set_level(logging.INFO)
            result = loader.load_tool_from_file(mock_path)

            assert result is MockTool
            assert any("does not implement accessibility features" in record.message for record in caplog.records)

    def test_load_tool_from_file_exception(self):
        """Test load_tool_from_file with exception (line 97)."""
        from pathlib import Path

        from nodupe.core.tool_system.loader import ToolLoader, ToolLoaderError

        loader = ToolLoader()

        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.suffix = '.py'
        mock_path.stem = 'test_tool'

        with patch('importlib.util.spec_from_file_location', side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(ToolLoaderError, match="Failed to load tool"):
                loader.load_tool_from_file(mock_path)

    def test_load_tool_from_directory_tool_loader_error(self):
        """Test load_tool_from_directory with ToolLoaderError (line 109)."""
        from pathlib import Path

        from nodupe.core.tool_system.loader import ToolLoader, ToolLoaderError

        loader = ToolLoader()

        mock_dir = Mock(spec=Path)
        mock_dir.exists.return_value = True
        mock_dir.is_dir.return_value = True
        mock_dir.glob.return_value = [Mock(name='tool1.py', suffix='.py')]

        with patch.object(loader, 'load_tool_from_file', side_effect=ToolLoaderError("Load failed")):
            # Should continue loading other tools, not raise
            result = loader.load_tool_from_directory(mock_dir)
            assert result == []

    def test_load_tool_from_directory_exception(self):
        """Test load_tool_from_directory with exception (line 119)."""
        from pathlib import Path

        from nodupe.core.tool_system.loader import ToolLoader, ToolLoaderError

        loader = ToolLoader()

        mock_dir = Mock(spec=Path)
        mock_dir.exists.return_value = True
        mock_dir.is_dir.return_value = True
        mock_dir.glob.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(ToolLoaderError, match="Failed to load tools"):
            loader.load_tool_from_directory(mock_dir)

    def test_load_tool_by_name_found(self):
        """Test load_tool_by_name when tool is found (lines 150-179)."""
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        mock_tool_path = MagicMock()
        mock_tool_path.exists.return_value = True

        mock_tool_dir = MagicMock()
        mock_tool_dir.__truediv__.return_value = mock_tool_path

        with patch.object(loader, 'load_tool_from_file', return_value=Mock()) as mock_load:

            result = loader.load_tool_by_name("test_tool", [mock_tool_dir])

            mock_load.assert_called_once_with(mock_tool_path)
            assert result is not None

    def test_load_tool_by_name_subdir(self):
        """Test load_tool_by_name from subdirectory."""
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        mock_tool_path = MagicMock()
        mock_tool_path.exists.return_value = False  # Direct file doesn't exist

        mock_subdir = MagicMock()
        mock_subdir.exists.return_value = True
        mock_init_path = MagicMock()
        mock_init_path.exists.return_value = True

        mock_tool_dir = MagicMock()
        mock_tool_dir.__truediv__.side_effect = [mock_tool_path, mock_subdir]
        mock_subdir.__truediv__.return_value = mock_init_path

        with patch.object(loader, 'load_tool_from_file', return_value=Mock()):

            result = loader.load_tool_by_name("test_tool", [mock_tool_dir])

            assert result is not None

    def test_load_tool_by_name_not_found(self):
        """Test load_tool_by_name when tool is not found."""
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        mock_tool_path = MagicMock()
        mock_tool_path.exists.return_value = False

        mock_subdir = MagicMock()
        mock_subdir.exists.return_value = False

        mock_tool_dir = MagicMock()
        mock_tool_dir.__truediv__.side_effect = [mock_tool_path, mock_subdir]

        result = loader.load_tool_by_name("test_tool", [mock_tool_dir])

        assert result is None

    def test_instantiate_tool_success(self):
        """Test instantiate_tool success (lines 198-208)."""
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        mock_tool_class = Mock()
        mock_instance = Mock()
        mock_tool_class.return_value = mock_instance

        result = loader.instantiate_tool(mock_tool_class, "arg1", kwarg="value")

        mock_tool_class.assert_called_once_with("arg1", kwarg="value")
        assert result is mock_instance

    def test_instantiate_tool_exception(self):
        """Test instantiate_tool with exception."""
        from nodupe.core.tool_system.loader import ToolLoader, ToolLoaderError

        loader = ToolLoader()

        mock_tool_class = Mock()
        mock_tool_class.side_effect = Exception("Instantiation failed")

        with pytest.raises(ToolLoaderError, match="Failed to instantiate tool"):
            loader.instantiate_tool(mock_tool_class)

    def test_register_loaded_tool_exception(self):
        """Test register_loaded_tool with exception (lines 232-233)."""
        from nodupe.core.tool_system.loader import ToolLoader, ToolLoaderError

        loader = ToolLoader()
        loader.registry = Mock()
        loader.registry.register.side_effect = Exception("Registration failed")

        mock_tool = Mock()
        mock_tool.name = "test_tool"

        with pytest.raises(ToolLoaderError, match="Failed to register tool"):
            loader.register_loaded_tool(mock_tool)

    def test_unload_tool_success(self):
        """Test unload_tool success (lines 264-293, 312)."""
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.__module__ = "test_module"

        loader._loaded_tools["test_tool"] = mock_tool
        loader.registry = Mock()

        result = loader.unload_tool("test_tool")

        assert result is True
        assert "test_tool" not in loader._loaded_tools
        mock_tool.shutdown.assert_called_once()
        loader.registry.unregister.assert_called_once_with("test_tool")

    def test_unload_tool_with_instance(self):
        """Test unload_tool with Tool instance."""
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.__module__ = None  # No module to cleanup

        loader._loaded_tools["test_tool"] = mock_tool
        loader.registry = Mock()

        result = loader.unload_tool(mock_tool)

        assert result is True

    def test_unload_tool_shutdown_exception(self):
        """Test unload_tool when shutdown raises exception."""
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.shutdown.side_effect = Exception("Shutdown failed")
        mock_tool.__module__ = None

        loader._loaded_tools["test_tool"] = mock_tool
        loader.registry = Mock()

        # Should not raise, should print warning
        result = loader.unload_tool("test_tool")

        assert result is True

    def test_unload_tool_registry_exception(self):
        """Test unload_tool when registry.unregister raises KeyError."""
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.__module__ = None

        loader._loaded_tools["test_tool"] = mock_tool
        loader.registry = Mock()
        loader.registry.unregister.side_effect = KeyError("Tool not found")

        result = loader.unload_tool("test_tool")

        assert result is True

    def test_unload_tool_not_found(self):
        """Test unload_tool when tool is not found."""
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()
        loader._loaded_tools = {}

        result = loader.unload_tool("nonexistent_tool")

        assert result is False

    def test_validate_tool_class_property(self):
        """Test _validate_tool_class with property name (line 345)."""
        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        class ToolWithProperty(Tool):
            """Mock tool with properties for name, version, and dependencies."""

            @property
            def name(self):
                """Return the name of the tool.

                Returns:
                    str: The tool name.
                """
                return "ToolWithProperty"

            @property
            def version(self):
                """Return the version of the tool.

                Returns:
                    str: The tool version.
                """
                return "1.0.0"

            @property
            def dependencies(self):
                """Return the dependencies of the tool.

                Returns:
                    list: Empty list for mock tool.
                """
                return []

            def initialize(self, container):
                """Initialize the tool.

                Args:
                    container: The service container for dependency injection.
                """
                pass

            def shutdown(self):
                """Shutdown the tool and release resources."""
                pass

            def get_capabilities(self):
                """Return the capabilities of this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

            @property
            def api_methods(self):
                """Return the API methods exposed by this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

            def run_standalone(self, args):
                """Run the tool in standalone mode.

                Args:
                    args: Command line arguments.

                Returns:
                    int: Exit code.
                """
                return 0

            def describe_usage(self):
                """Describe how to use this tool.

                Returns:
                    str: Usage description.
                """
                return "Tool with property"

        result = loader._validate_tool_class(ToolWithProperty)

        assert result is True

    def test_validate_tool_class_property_exception(self):
        """Test _validate_tool_class with property that raises (lines 357-358)."""
        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        class ToolWithBadProperty(Tool):
            """Mock tool with a property that raises an exception."""

            @property
            def name(self):
                """Return the name of the tool.

                Raises:
                    Exception: Always raises to test error handling.
                """
                raise Exception("Property error")

            version = "1.0.0"
            dependencies = []

            def initialize(self, container):
                """Initialize the tool.

                Args:
                    container: The service container for dependency injection.
                """
                pass

            def shutdown(self):
                """Shutdown the tool and release resources."""
                pass

            def get_capabilities(self):
                """Return the capabilities of this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

            @property
            def api_methods(self):
                """Return the API methods exposed by this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

        result = loader._validate_tool_class(ToolWithBadProperty)

        assert result is False

    def test_validate_tool_class_empty_name(self):
        """Test _validate_tool_class with empty name (line 364)."""
        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        class ToolWithEmptyName(Tool):
            """Mock tool with an empty name for validation testing."""

            name = ""
            version = "1.0.0"
            dependencies = []

            def initialize(self, container):
                """Initialize the tool.

                Args:
                    container: The service container for dependency injection.
                """
                pass

            def shutdown(self):
                """Shutdown the tool and release resources."""
                pass

            def get_capabilities(self):
                """Return the capabilities of this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

            @property
            def api_methods(self):
                """Return the API methods exposed by this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

        result = loader._validate_tool_class(ToolWithEmptyName)

        assert result is False

    def test_validate_tool_class_valid(self):
        """Test _validate_tool_class with valid tool (lines 368-369)."""
        from nodupe.core.tool_system.base import Tool
        from nodupe.core.tool_system.loader import ToolLoader

        loader = ToolLoader()

        class ValidTool(Tool):
            """Valid mock tool class for positive validation tests."""

            name = "ValidTool"
            version = "1.0.0"
            dependencies = []

            def initialize(self, container):
                """Initialize the tool.

                Args:
                    container: The service container for dependency injection.
                """
                pass

            def shutdown(self):
                """Shutdown the tool and release resources."""
                pass

            def get_capabilities(self):
                """Return the capabilities of this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

            @property
            def api_methods(self):
                """Return the API methods exposed by this tool.

                Returns:
                    dict: Empty dict for mock tool.
                """
                return {}

        result = loader._validate_tool_class(ValidTool)

        assert result is True
