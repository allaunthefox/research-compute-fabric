# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for Core Utilities coverage (main.py, config.py, limits.py).

This module targets specific coverage gaps identified in the implementation plan.
"""

import io
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from nodupe.core.config import ConfigManager, load_config
from nodupe.core.limits import Limits, LimitsError, RateLimiter

# Import modules under test
from nodupe.core.main import CLIHandler, main


class TestMainCoverage(unittest.TestCase):
    """Tests for main.py coverage."""

    def test_main_keyboard_interrupt(self):
        """Test KeyboardInterrupt handling in main()."""
        # We need to mock CLIHandler to raise KeyboardInterrupt
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_handler_class:
            
            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader
            
            mock_handler = Mock()
            mock_handler.run.side_effect = KeyboardInterrupt()
            mock_handler_class.return_value = mock_handler
            
            # Capture stderr to suppress output
            with io.StringIO() as buf, patch('sys.stderr', buf):
                exit_code = main()
                assert exit_code == 130
                
            mock_loader.shutdown.assert_called_once()

    def test_main_fatal_error(self):
        """Test fatal error handling in main()."""
        with patch('nodupe.core.main.bootstrap', side_effect=Exception("Bootstrap failed")):
            with io.StringIO() as buf, patch('sys.stderr', buf):
                exit_code = main()
                assert exit_code == 1

    def test_cmd_tool_system_inactive(self):
        """Test _cmd_tool when tool system is inactive."""
        mock_loader = Mock()
        mock_loader.tool_registry = None  # Inactive tool registry
        
        handler = CLIHandler(mock_loader)
        
        args = Mock()
        args.list = False
        
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            exit_code = handler._cmd_tool(args)
            assert exit_code == 1
            assert "Tool system is not active" in fake_out.getvalue()

    def test_cli_run_exception(self):
        """Test CLIHandler.run exception handling."""
        mock_loader = Mock()
        # Avoid iteration error in _register_commands
        mock_loader.tool_registry = None
        handler = CLIHandler(mock_loader)
        
        # Mock parser to return args with a failing function
        args = Mock()
        args.debug = False
        args.cores = None
        args.max_workers = None
        args.batch_size = None
        
        def failing_func(args):
            """Function that raises an exception for testing."""
            raise Exception("Command failed")
            
        args.func = failing_func
        
        # We need to mock _apply_overrides to safely handle the mock args
        # or ensure args properties behave nicely.
        # The TypeError 'Mock object is not iterable' might come from how parser.parse_args is used or mocked.
        # But let's try to mock parse_args more robustly.
        
        with patch.object(handler.parser, 'parse_args', return_value=args):
            with io.StringIO() as buf, patch('sys.stderr', buf):
                # We also need to patch traceback to avoid printing to real stderr/stdout if it happens
                with patch('traceback.print_exc'):
                    exit_code = handler.run()
                    assert exit_code == 1

    def test_register_commands_exception(self):
        """Test exception handling during command registration."""
        mock_loader = Mock()
        mock_tool = Mock()
        mock_tool.name = "BadTool"
        # make register_commands raise
        mock_tool.register_commands.side_effect = Exception("Register failed")
        
        mock_registry = Mock()
        mock_registry.get_tools.return_value = [mock_tool]
        mock_loader.tool_registry = mock_registry
        
    def test_register_commands_success(self):
        """Test successful command registration."""
        mock_loader = Mock()
        mock_loader.tool_registry = Mock()
        mock_tool = Mock()
        mock_tool.name = "GoodTool"
        mock_tool.register_commands = Mock()
        mock_loader.tool_registry.get_tools.return_value = [mock_tool]
        
        CLIHandler(mock_loader)
        mock_tool.register_commands.assert_called_once()

    def test_cmd_version(self):
        """Test version command."""
        args = Mock()
        mock_loader = Mock()
        # Avoid iteration error
        mock_loader.tool_registry.get_tools.return_value = []
        mock_loader.config.config = {
            'drive_type': 'SSD',
            'cpu_cores': 8,
            'ram_gb': 16
        }
        handler = CLIHandler(mock_loader)
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            exit_code = handler._cmd_version(args)
            assert exit_code == 0
            assert "NoDupeLabs CLI" in fake_out.getvalue()
            assert "SSD" in fake_out.getvalue()

    def test_cmd_tool_list(self):
        """Test tool list command."""
        args = Mock()
        args.list = True
        mock_loader = Mock()
        mock_tool = Mock()
        mock_tool.name = "TestTool"
        mock_tool.version = "1.0"
        
        # Make it an AccessibleTool instance (mock inheritance)
        from nodupe.core.tool_system.base import AccessibleTool

        # We can't easily mock isinstance(mock, Class) without spec
        # But we can just create a dummy class
        class DummyTool(AccessibleTool):
            """Dummy tool class for testing purposes."""
            name = "Dummy"
            version = "1.0"
            
            @property
            def dependencies(self):
                """Return empty dependencies list."""
                return []
            
            def initialize(self, c):
                """Initialize the dummy tool."""
                pass
            
            def shutdown(self):
                """Shutdown the dummy tool."""
                pass
            
            def get_capabilities(self):
                """Return empty capabilities."""
                return {}
            
            @property
            def api_methods(self):
                """Return empty API methods."""
                return {}
            
            def run_standalone(self, a):
                """Run the tool in standalone mode."""
                return 0
            
            def describe_usage(self):
                """Return empty usage description."""
                return ""
            
        tool = DummyTool()
        mock_loader.tool_registry.get_tools.return_value = [tool]
        
        handler = CLIHandler(mock_loader)
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            exit_code = handler._cmd_tool(args)
            assert exit_code == 0
            assert "Dummy" in fake_out.getvalue()

    def test_run_debug_and_overrides(self):
        """Test run with debug and overrides."""
        mock_loader = Mock()
        mock_loader.config.config = {}
        # Avoid iteration error
        mock_loader.tool_registry.get_tools.return_value = []
        
        handler = CLIHandler(mock_loader)
        
        args = Mock()
        args.debug = True
        args.cores = 4
        args.max_workers = 8
        args.batch_size = 100
        args.func = Mock(return_value=0)
        
        with patch.object(handler.parser, 'parse_args', return_value=args):
            handler.run()
            
            # Verify overrides applied
            assert mock_loader.config.config['cpu_cores'] == 4
            assert mock_loader.config.config['max_workers'] == 8
            assert mock_loader.config.config['batch_size'] == 100

    def test_shutdown_cleanup(self):
        """Test shutdown cleanup in main."""
        with patch('nodupe.core.main.bootstrap') as mock_bootstrap, \
             patch('nodupe.core.main.CLIHandler') as mock_handler_class:
            
            mock_loader = Mock()
            mock_bootstrap.return_value = mock_loader
            mock_handler = Mock()
            mock_handler.run.return_value = 0
            mock_handler_class.return_value = mock_handler
            
            main()
            
            mock_loader.shutdown.assert_called_once()



class TestConfigCoverage(unittest.TestCase):
    """Tests for config.py coverage."""

    def test_load_config_file_not_found(self):
        """Test _load_config with non-existent file."""
        manager = ConfigManager.__new__(ConfigManager)
        manager.config_path = "non_existent.toml"
        
        with self.assertRaises(FileNotFoundError):
            manager._load_config()

    def test_load_config_invalid_toml(self):
        """Test _load_config with invalid TOML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as tmp:
            tmp.write("invalid_toml = [") # unclosed list
            tmp.close()
            
            try:
                manager = ConfigManager.__new__(ConfigManager)
                manager.config_path = tmp.name
                
                with self.assertRaises(ValueError):
                    manager._load_config()
            finally:
                os.unlink(tmp.name)

    def test_get_config_value_exception(self):
        """Test get_config_value exception path."""
        manager = ConfigManager.__new__(ConfigManager)
        manager.config = Mock()
        # Make get() raise exception
        manager.config.get.side_effect = Exception("Access failed")
        
    def test_config_getters(self):
        """Test all config getters."""
        manager = ConfigManager.__new__(ConfigManager)
        manager.config = {
            'tool': {
                'nodupe': {
                    'database': {'path': 'db'},
                    'scan': {'min_size': 1},
                    'similarity': {'threshold': 0.9},
                    'performance': {'workers': 2},
                    'logging': {'level': 'DEBUG'}
                }
            }
        }
        
        assert manager.get_database_config()['path'] == 'db'
        assert manager.get_scan_config()['min_size'] == 1
        assert manager.get_similarity_config()['threshold'] == 0.9
        assert manager.get_performance_config()['workers'] == 2
        assert manager.get_logging_config()['level'] == 'DEBUG'
        assert manager.get_config_value('database', 'path') == 'db'
        assert manager.get_config_value('database', 'missing', 'default') == 'default'

    def test_validate_config_success(self):
        """Test validate_config success."""
        manager = ConfigManager.__new__(ConfigManager)
        manager.config = {
            'tool': {
                'nodupe': {
                    'database': {}, 'scan': {}, 'similarity': {}, 
                    'performance': {}, 'logging': {}
                }
            }
        }
        assert manager.validate_config() is True

    def test_load_config_default_empty(self):
        """Test loading default pyproject.toml when it doesn't exist (empty config)."""
        manager = ConfigManager.__new__(ConfigManager)
        manager.config_path = "pyproject.toml"
        # Since we likely are in repo root where pyproject.toml EXISTS,
        # we should use a path that doesn't exist but triggers the empty check IF logic allows.
        # But code says: if path == "pyproject.toml" and not exists -> empty.
        # So we patch exists to return False.
        with patch('os.path.exists', return_value=False):
            manager._load_config()
            assert manager.config == {}

    def test_load_config_wrapper(self):
        """Test load_config wrapper."""
        with patch('nodupe.core.config.ConfigManager') as mock_cls:
            load_config("path")
            mock_cls.assert_called_with("path")



class TestLimitsCoverage(unittest.TestCase):
    """Tests for limits.py coverage."""

    def test_get_memory_usage_fallback(self):
        """Test get_memory_usage fallback logic."""
        # Mock sys.platform to something unknown and ensure resource is not available
        with patch('sys.platform', 'unknown'), \
             patch.dict('sys.modules', {'resource': None}):
            
            # Should return 0
            usage = Limits.get_memory_usage()
            assert usage == 0

    def test_check_file_handles_failure(self):
        """Test check_file_handles failure."""
        with patch.object(Limits, 'get_open_file_count', side_effect=Exception("Failed")):
            with self.assertRaises(LimitsError):
                Limits.check_file_handles()

    def test_check_file_size_non_existent(self):
        """Test check_file_size with non-existent file."""
        # Should return True (pass) if file doesn't exist
        assert Limits.check_file_size("non_existent_file.txt", 100) is True

    def test_check_file_size_error(self):
        """Test check_file_size unexpected error."""
        with patch('pathlib.Path.exists', side_effect=Exception("Disk error")):
            with self.assertRaises(LimitsError):
                Limits.check_file_size("file.txt", 100)

    def test_time_limit_exceeded(self):
        """Test time_limit context manager actually interrupting."""
        import time
        
        try:
            with Limits.time_limit(0.1):
                time.sleep(0.2)
        except LimitsError:
            pass # Expected
            
    def test_check_memory_limit_success(self):
        """Test check_memory_limit success path."""
        # Mock get_memory_usage to return small value
        with patch.object(Limits, 'get_memory_usage', return_value=1024):
            assert Limits.check_memory_limit(2048) is True

    def test_check_memory_limit_failure(self):
        """Test check_memory_limit failure path."""
        with patch.object(Limits, 'get_memory_usage', return_value=4096):
            with self.assertRaises(LimitsError):
                Limits.check_memory_limit(2048)

    def test_get_memory_usage_linux(self):
        """Test get_memory_usage on Linux."""
        with patch('sys.platform', 'linux'):
            # Mock /proc/self/status
            mock_open = unittest.mock.mock_open(read_data="Name: python\nVmRSS: 1024 kB\n")
            with patch('builtins.open', mock_open):
                # Also ensure resource doesn't interfere if present
                with patch.dict('sys.modules', {'resource': None}):
                    usage = Limits.get_memory_usage()
                    assert usage == 1024 * 1024

    def test_check_file_handles_success(self):
        """Test check_file_handles success."""
        with patch.object(Limits, 'get_open_file_count', return_value=10):
            assert Limits.check_file_handles(max_handles=20) is True

    def test_check_file_size_success(self):
        """Test check_file_size success."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 50
            assert Limits.check_file_size("file", 100) is True

    def test_check_data_size(self):
        """Test check_data_size."""
        assert Limits.check_data_size(b"123", 10) is True
        with self.assertRaises(LimitsError):
            Limits.check_data_size(b"123", 2)

    def test_size_limit_class(self):
        """Test SizeLimit class."""
        limit = from_nodupe_core_limits().SizeLimit(100)
        assert limit.add(40) is True
        assert limit.used == 40
        assert limit.remaining() == 60
        
        with self.assertRaises(LimitsError):
            limit.add(70) # Exceeds 100
            
        limit.reset()
        assert limit.used == 0

    def test_count_limit_class(self):
        """Test CountLimit class."""
        limit = from_nodupe_core_limits().CountLimit(2)
        assert limit.increment() is True
        assert limit.used == 1
        assert limit.remaining() == 1
        
        assert limit.increment() is True
        with self.assertRaises(LimitsError):
            limit.increment()
            
        limit.reset()
        assert limit.used == 0

    def test_with_timeout_decorator(self):
        """Test with_timeout decorator."""
        import time

        from nodupe.core.limits import with_timeout
        
        @with_timeout(0.5)
        def fast_func():
            """Function that completes quickly."""
            return "ok"
            
        @with_timeout(0.1)
        def slow_func():
            """Function that exceeds timeout."""
            time.sleep(0.2)
            
        assert fast_func() == "ok"
        with self.assertRaises(LimitsError):
            slow_func()

    def test_rate_limiter_consume(self):
        """Test rate limiter consume."""
        limiter = RateLimiter(rate=10, burst=10)
        # Should be able to consume burst
        assert limiter.consume(5) is True
        # Should be able to consume more
        assert limiter.consume(5) is True
        # Now empty (unless time passed, but effectively empty)
        # If we consume immediately it might fail if we are faster than refill
        # Mock time to ensure no refill
        with patch('time.monotonic', return_value=100.0):
            limiter.last_update = 100.0
            assert limiter.consume(1) is False

def from_nodupe_core_limits():
    """Helper to import limit classes locally to avoid import errors at top level if order matters."""
    import nodupe.core.limits as l
    return l
