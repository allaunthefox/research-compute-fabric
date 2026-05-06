# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Final coverage push tests - Complete Set."""

import io
import os
import sys
import time
import unittest
from unittest.mock import MagicMock, Mock, patch

from nodupe.core.api.ipc import ToolIPCServer
from nodupe.core.config import ConfigManager
from nodupe.core.limits import Limits, LimitsError

# Import normally
from nodupe.core.main import CLIHandler
from nodupe.core.tool_system.base import AccessibleTool


class TestFinalPush(unittest.TestCase):
    """Final push coverage tests for comprehensive test coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self._limits_module = sys.modules.get('nodupe.core.limits')

    def tearDown(self):
        """Clean up test fixtures."""
        if self._limits_module:
            sys.modules['nodupe.core.limits'] = self._limits_module

    # --- limits.py coverage ---

    def test_limits_platform_branches(self):
        """Cover limits.py platform specific branches (darwin/macOS)."""
        import resource

        # Create a mock module that mimics resource
        mock_resource = Mock()
        mock_resource.RUSAGE_SELF = resource.RUSAGE_SELF
        mock_usage = Mock()
        mock_usage.ru_maxrss = 100  # macOS returns bytes directly
        mock_resource.getrusage.return_value = mock_usage

        # Create a mock os module that has getrusage attribute
        import os as real_os
        mock_os = Mock(wraps=real_os)
        mock_os.getrusage = mock_resource.getrusage

        # Patch at the module level where limits.py imports from
        with patch.dict('sys.modules', {'resource': mock_resource, 'os': mock_os}):
            with patch('sys.platform', 'darwin'):
                # Need to reimport to pick up the patched resource
                import importlib

                import nodupe.core.limits
                importlib.reload(nodupe.core.limits)
                result = nodupe.core.limits.Limits.get_memory_usage()
                assert result == 100  # macOS returns bytes directly

    def test_limits_linux_fallback(self):
        """Cover linux fallback when resource/proc missing."""
        # Patch both platform and sys.modules to simulate missing resource
        with patch('sys.platform', 'linux'):
            with patch.dict('sys.modules', {'resource': None}):
                with patch('pathlib.Path.exists', return_value=False):
                    # Need fresh import to avoid cached resource
                    import importlib

                    import nodupe.core.limits
                    importlib.reload(nodupe.core.limits)
                    result = nodupe.core.limits.Limits.get_memory_usage()
                    assert result == 0

    def test_limits_file_handles_linux(self):
        """Cover file handles counting on Linux via /proc."""
        with patch('sys.platform', 'linux'):
            # Mock Path.iterdir to return a list-like of fds
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.iterdir.return_value = [Mock(), Mock(), Mock()]  # 3 fds

            with patch('pathlib.Path') as mock_path_class:
                mock_path_class.return_value = mock_path
                count = Limits.get_open_file_count()
                assert count == 3

    # --- ipc.py coverage ---

    def test_ipc_cleanup_error(self):
        """Cover ipc.py cleanups."""
        path = "/tmp/ipc_test_cleanup_" + str(time.time())
        server = ToolIPCServer(Mock(), path)

        # Test 1: start() removes existing file
        with open(path, "w") as f: f.write("x")
        with patch('threading.Thread.start'):
            server.start()
            assert not os.path.exists(path)

        # Test 2: stop() removes file
        with open(path, "w") as f: f.write("y")
        server._server_thread = Mock()
        server._server_thread.join = Mock()
        server.stop()
        assert not os.path.exists(path)

    # --- Limits extra coverage ---

    def test_rate_limiter_wait(self):
        """Cover RateLimiter.wait method."""
        from nodupe.core.limits import RateLimiter
        limiter = RateLimiter(rate=10, burst=1)

        # 1. Success wait
        assert limiter.wait(1)

        # 2. Timeout wait
        limiter.TOKEN_REMOVEDs = 0
        # rate is 10/sec. refill takes 0.1s to get 1 token.
        # we wait 0.01s -> timeout
        with self.assertRaises(LimitsError):
            limiter.wait(1, timeout=0.001)

    def test_check_file_handles_default(self):
        """Cover check_file_handles with defaults."""
        from nodupe.core.limits import Limits

        # 1. resource available (Unix)
        with patch('nodupe.core.limits.os') as mock_os:
             mock_os.getrusage = MagicMock()
             mock_resource = Mock()
             mock_resource.RLIMIT_NOFILE = 1
             mock_resource.getrlimit.return_value = (100, 100) # soft, hard

             with patch.dict('sys.modules', {'resource': mock_resource}):
                 # Mock Open file count to be 50
                 with patch.object(Limits, 'get_open_file_count', return_value=50):
                     assert Limits.check_file_handles(None) is True

                 # Mock Open file count to be 101
                 with patch.object(Limits, 'get_open_file_count', return_value=101):
                     with self.assertRaises(Exception): # LimitsError
                        Limits.check_file_handles(None)

        # 2. resource missing (Fallback)
        with patch('nodupe.core.limits.os') as mock_os:
            del mock_os.getrusage
            with patch.object(Limits, 'get_open_file_count', return_value=50):
                # Default limit is 1024
                assert Limits.check_file_handles(None) is True

    def test_main_debug_traceback(self):
        """Cover main.py lines 124-125: traceback print."""
        # Create a proper mock loader with config that supports item assignment
        mock_config = Mock()
        mock_config.config = {}  # Real dict that supports item assignment
        mock_config.config['cpu_cores'] = 4
        mock_config.config['max_workers'] = 8
        mock_config.config['batch_size'] = 100

        mock_loader = Mock()
        mock_loader.config = mock_config
        # Mock tool_registry.get_tools to return an empty list (iterable)
        mock_loader.tool_registry.get_tools.return_value = []

        # We need a parser that returns our args
        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
            args = Mock()
            args.debug = True
            args.func.side_effect = Exception("Boom")
            args.cores = None
            args.max_workers = None
            args.batch_size = None
            mock_parse.return_value = args

            handler = CLIHandler(mock_loader)

            # Patch traceback globally
            with patch('traceback.print_exc') as mock_print:
                # We also need to patch sys.stderr to avoid clutter
                with patch('sys.stderr', new=io.StringIO()):
                    handler.run()

                # If local import uses global traceback module, this works
                mock_print.assert_called()

    def test_main_shutdown_error(self):
        """Cover main.py lines 211-213: Error during shutdown."""
        from nodupe.core.main import main
        with patch('nodupe.core.main.bootstrap') as mock_init:
            mock_loader = Mock()
            mock_init.return_value = mock_loader
            mock_loader.shutdown.side_effect = Exception("Shutdown fail")

            with patch('nodupe.core.main.CLIHandler') as mock_handler:
                mock_handler.return_value.run.return_value = 0
                with patch('sys.stderr', new=io.StringIO()) as fake_err:
                    main()
                    assert "Error during shutdown" in fake_err.getvalue()

    def test_tool_list_access_check(self):
        """Cover main.py lines 162, 164: accessible/non-accessible tools."""
        mock_loader = Mock()

        tool1 = Mock()
        tool1.name = "NormalTool"
        # Not AccessibleTool

        class AccessTool(AccessibleTool):
            """Accessible tool class for testing."""
            name = "AccessTool"
            version = "1.0"

            @property
            def dependencies(self):
                """Return empty dependencies list."""
                return []

            def initialize(self, c):
                """Initialize the tool."""
                pass

            def shutdown(self):
                """Shutdown the tool."""
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

        tool2 = AccessTool()
        mock_loader.tool_registry.get_tools.return_value = [tool1, tool2]

        handler = CLIHandler(mock_loader)
        args = Mock()
        args.list = True

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            handler._cmd_tool(args)
            output = fake_out.getvalue()
            assert "NormalTool" in output
            assert "AccessTool" in output

    # --- config.py coverage ---

    def test_config_init_toml_missing(self):
        """Cover config.py checks for logic when toml is None."""
        import nodupe.core.config as config_mod
        original_toml = config_mod.toml
        config_mod.toml = None

        try:
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', new_callable=MagicMock):
                     try:
                         ConfigManager("path")
                     except ValueError:
                         pass
                     except Exception as e:
                         self.fail(f"Raised wrong exception: {type(e)} {e}")
        finally:
            config_mod.toml = original_toml

if __name__ == '__main__':
    unittest.main()
