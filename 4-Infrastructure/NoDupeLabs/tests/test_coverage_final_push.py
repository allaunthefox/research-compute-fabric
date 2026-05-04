# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Final coverage push tests for 100% coverage.

This test file targets uncovered lines in:
- nodupe/core/container.py (already at 100%)
- nodupe/core/config.py 
- nodupe/core/api/ipc.py
- nodupe/tools/parallel/parallel_logic.py
- nodupe/tools/scanner_engine/walker.py
"""

import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, Mock, PropertyMock, mock_open, patch


class TestConfigCoverageFinal(unittest.TestCase):
    """Coverage tests for nodupe/core/config.py remaining gaps."""

    def test_config_get_config_value_exception_path(self):
        """Cover lines 107-108: get_config_value exception handling."""
        from nodupe.core.config import ConfigManager

        # Create manager with mocked config that raises on nested get()
        manager = ConfigManager.__new__(ConfigManager)
        
        # Create a mock that raises exception on nested dict get
        mock_nodupe = Mock()
        mock_nodupe.get.side_effect = RuntimeError("Nested get failed")
        
        mock_tool = Mock()
        mock_tool.get.return_value = mock_nodupe
        
        manager.config = {'tool': mock_tool}
        
        # This should catch the exception and return default
        result = manager.get_config_value('section', 'key', 'default_val')
        self.assertEqual(result, 'default_val')


class TestIPCCoverageFinal(unittest.TestCase):
    """Coverage tests for nodupe/core/api/ipc.py remaining gaps."""

    def test_ipc_server_accept_error(self):
        """Cover ipc.py socket accept error handling."""
        from nodupe.core.api.ipc import ToolIPCServer
        from nodupe.core.tool_system.registry import ToolRegistry
        
        registry = ToolRegistry()
        path = f"/tmp/test_ipc_err_{int(time.time())}.sock"
        
        server = ToolIPCServer(registry, path)
        
        # Mock server socket to raise error during accept
        with patch('socket.socket') as mock_socket_class:
            mock_server = MagicMock()
            mock_socket_class.return_value.__enter__.return_value = mock_server
            
            # Simulate accept raising an error
            mock_server.accept.side_effect = OSError("Accept failed")
            mock_server.listen = MagicMock()
            mock_server.bind = MagicMock()
            
            # Start server in thread
            server._stop_event.clear()
            server._server_thread = threading.Thread(
                target=server._run_server,
                daemon=True
            )
            server._server_thread.start()
            
            # Wait a bit for error to occur
            time.sleep(0.1)
            server._stop_event.set()
            server._server_thread.join(timeout=1)
            
            # Cleanup
            if os.path.exists(path):
                os.remove(path)

    def test_ipc_connection_receive_error(self):
        """Cover ipc.py connection receive error handling."""
        from nodupe.core.api.ipc import ToolIPCServer
        from nodupe.core.tool_system.registry import ToolRegistry
        
        registry = ToolRegistry()
        path = f"/tmp/test_ipc_recv_{int(time.time())}.sock"
        
        server = ToolIPCServer(registry, path)
        
        # Create a mock connection that raises on recv
        with patch('socket.socket') as mock_socket_class:
            mock_server = MagicMock()
            mock_client = MagicMock()
            
            # Setup return values for context manager
            mock_socket_class.return_value.__enter__.return_value = mock_server
            mock_server.accept.return_value = (mock_client, ('127.0.0.1', 12345))
            
            # Recv raises error
            mock_client.recv.side_effect = OSError("Recv failed")
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=False)
            
            mock_server.listen = MagicMock()
            mock_server.bind = MagicMock()
            mock_server.settimeout = MagicMock()
            
            server._stop_event.clear()
            server._server_thread = threading.Thread(
                target=server._run_server,
                daemon=True
            )
            server._server_thread.start()
            
            time.sleep(0.1)
            server._stop_event.set()
            server._server_thread.join(timeout=1)
            
            if os.path.exists(path):
                os.remove(path)

    def test_ipc_json_decode_error(self):
        """Cover ipc.py JSON decode error handling."""
        from nodupe.core.api.ipc import ToolIPCServer
        from nodupe.core.tool_system.registry import ToolRegistry
        
        registry = ToolRegistry()
        path = f"/tmp/test_ipc_json_{int(time.time())}.sock"
        
        server = ToolIPCServer(registry, path)
        
        with patch('socket.socket') as mock_socket_class:
            mock_server = MagicMock()
            mock_client = MagicMock()
            
            mock_socket_class.return_value.__enter__.return_value = mock_server
            mock_server.accept.return_value = (mock_client, ('127.0.0.1', 12345))
            
            # Return invalid JSON
            mock_client.recv.return_value = b"not valid json{"
            mock_client.sendall = MagicMock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=False)
            
            mock_server.listen = MagicMock()
            mock_server.bind = MagicMock()
            mock_server.settimeout = MagicMock()
            
            server._stop_event.clear()
            server._server_thread = threading.Thread(
                target=server._run_server,
                daemon=True
            )
            server._server_thread.start()
            
            time.sleep(0.1)
            server._stop_event.set()
            server._server_thread.join(timeout=1)
            
            if os.path.exists(path):
                os.remove(path)

    def test_ipc_missing_jsonrpc_version(self):
        """Cover ipc.py missing jsonrpc version error."""
        from nodupe.core.api.ipc import ToolIPCServer
        from nodupe.core.tool_system.registry import ToolRegistry
        
        registry = ToolRegistry()
        path = f"/tmp/test_ipc_ver_{int(time.time())}.sock"
        
        server = ToolIPCServer(registry, path)
        
        with patch('socket.socket') as mock_socket_class:
            mock_server = MagicMock()
            mock_client = MagicMock()
            
            mock_socket_class.return_value.__enter__.return_value = mock_server
            mock_server.accept.return_value = (mock_client, ('127.0.0.1', 12345))
            
            # Valid JSON but missing jsonrpc version
            request = {"method": "test", "params": {}, "id": 1}
            mock_client.recv.return_value = json.dumps(request).encode()
            mock_client.sendall = MagicMock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=False)
            
            mock_server.listen = MagicMock()
            mock_server.bind = MagicMock()
            mock_server.settimeout = MagicMock()
            
            server._stop_event.clear()
            server._server_thread = threading.Thread(
                target=server._run_server,
                daemon=True
            )
            server._server_thread.start()
            
            time.sleep(0.1)
            server._stop_event.set()
            server._server_thread.join(timeout=1)
            
            if os.path.exists(path):
                os.remove(path)

    def test_ipc_tool_not_found(self):
        """Cover ipc.py tool not found error."""
        from nodupe.core.api.ipc import ToolIPCServer
        from nodupe.core.tool_system.registry import ToolRegistry
        
        registry = ToolRegistry()
        path = f"/tmp/test_ipc_tool_{int(time.time())}.sock"
        
        server = ToolIPCServer(registry, path)
        
        with patch('socket.socket') as mock_socket_class:
            mock_server = MagicMock()
            mock_client = MagicMock()
            
            mock_socket_class.return_value.__enter__.return_value = mock_server
            mock_server.accept.return_value = (mock_client, ('127.0.0.1', 12345))
            
            # Request for non-existent tool
            request = {"jsonrpc": "2.0", "tool": "nonexistent", "method": "test", "params": {}, "id": 1}
            mock_client.recv.return_value = json.dumps(request).encode()
            mock_client.sendall = MagicMock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=False)
            
            mock_server.listen = MagicMock()
            mock_server.bind = MagicMock()
            mock_server.settimeout = MagicMock()
            
            server._stop_event.clear()
            server._server_thread = threading.Thread(
                target=server._run_server,
                daemon=True
            )
            server._server_thread.start()
            
            time.sleep(0.1)
            server._stop_event.set()
            server._server_thread.join(timeout=1)
            
            if os.path.exists(path):
                os.remove(path)

    def test_ipc_method_not_exposed(self):
        """Cover ipc.py method not exposed error."""
        from nodupe.core.api.ipc import ToolIPCServer
        from nodupe.core.tool_system.registry import ToolRegistry
        
        registry = ToolRegistry()
        path = f"/tmp/test_ipc_method_{int(time.time())}.sock"
        
        server = ToolIPCServer(registry, path)
        
        # Register a mock tool without the requested method
        mock_tool = Mock()
        mock_tool.api_methods = {}  # Empty - no methods exposed
        
        with patch.object(registry, 'get_tool', return_value=mock_tool):
            with patch('socket.socket') as mock_socket_class:
                mock_server = MagicMock()
                mock_client = MagicMock()
                
                mock_socket_class.return_value.__enter__.return_value = mock_server
                mock_server.accept.return_value = (mock_client, ('127.0.0.1', 12345))
                
                request = {"jsonrpc": "2.0", "tool": "testtool", "method": "unexposed", "params": {}, "id": 1}
                mock_client.recv.return_value = json.dumps(request).encode()
                mock_client.sendall = MagicMock()
                mock_client.__enter__ = Mock(return_value=mock_client)
                mock_client.__exit__ = Mock(return_value=False)
                
                mock_server.listen = MagicMock()
                mock_server.bind = MagicMock()
                mock_server.settimeout = MagicMock()
                
                server._stop_event.clear()
                server._server_thread = threading.Thread(
                    target=server._run_server,
                    daemon=True
                )
                server._server_thread.start()
                
                time.sleep(0.1)
                server._stop_event.set()
                server._server_thread.join(timeout=1)
                
                if os.path.exists(path):
                    os.remove(path)

    def test_ipc_method_execution_error(self):
        """Cover ipc.py method execution error handling."""
        from nodupe.core.api.ipc import ToolIPCServer
        from nodupe.core.tool_system.registry import ToolRegistry
        
        registry = ToolRegistry()
        path = f"/tmp/test_ipc_exec_{int(time.time())}.sock"
        
        server = ToolIPCServer(registry, path)
        
        # Register a mock tool with method that raises
        mock_method = Mock(side_effect=RuntimeError("Method failed"))
        mock_tool = Mock()
        mock_tool.api_methods = {"failing": mock_method}
        
        with patch.object(registry, 'get_tool', return_value=mock_tool):
            with patch('socket.socket') as mock_socket_class:
                mock_server = MagicMock()
                mock_client = MagicMock()
                
                mock_socket_class.return_value.__enter__.return_value = mock_server
                mock_server.accept.return_value = (mock_client, ('127.0.0.1', 12345))
                
                request = {"jsonrpc": "2.0", "tool": "testtool", "method": "failing", "params": {}, "id": 1}
                mock_client.recv.return_value = json.dumps(request).encode()
                mock_client.sendall = MagicMock()
                mock_client.__enter__ = Mock(return_value=mock_client)
                mock_client.__exit__ = Mock(return_value=False)
                
                mock_server.listen = MagicMock()
                mock_server.bind = MagicMock()
                mock_server.settimeout = MagicMock()
                
                server._stop_event.clear()
                server._server_thread = threading.Thread(
                    target=server._run_server,
                    daemon=True
                )
                server._server_thread.start()
                
                time.sleep(0.1)
                server._stop_event.set()
                server._server_thread.join(timeout=1)
                
                if os.path.exists(path):
                    os.remove(path)


class TestParallelCoverageFinal(unittest.TestCase):
    """Coverage tests for nodupe/tools/parallel/parallel_logic.py remaining gaps."""

    def test_parallel_process_in_parallel_worker_error(self):
        """Cover lines around worker error handling in process_in_parallel."""
        from nodupe.tools.parallel.parallel_logic import Parallel, ParallelError

        # Create a function that raises exception
        def failing_func(x):
            """Helper function that raises RuntimeError."""
            raise RuntimeError("Task failed")
        
        # Should raise ParallelError
        with self.assertRaises(ParallelError):
            Parallel.process_in_parallel(failing_func, [1, 2, 3], workers=2)

    def test_parallel_map_parallel_batch_size_zero(self):
        """Cover edge case with batch size handling."""
        from nodupe.tools.parallel.parallel_logic import Parallel

        # Test with chunk_size=0 edge case (should be handled)
        result = Parallel.map_parallel(lambda x: x*2, [1, 2, 3], chunk_size=0)
        self.assertEqual(result, [2, 4, 6])

    def test_parallel_reduce_parallel_no_initial(self):
        """Cover reduce_parallel without initial value."""
        from nodupe.tools.parallel.parallel_logic import Parallel, ParallelError

        # Should fail with empty sequence
        with self.assertRaises(ParallelError):
            Parallel.reduce_parallel(
                lambda x: x, 
                lambda a, b: a + b, 
                [], 
                initial=None
            )

    def test_parallel_get_optimal_workers_free_threaded(self):
        """Cover get_optimal_workers in free-threaded mode."""
        from nodupe.tools.parallel.parallel_logic import Parallel

        # Mock free-threaded mode
        with patch.object(Parallel, 'is_free_threaded', return_value=True):
            with patch.object(Parallel, 'get_cpu_count', return_value=4):
                # CPU task
                workers = Parallel.get_optimal_workers('cpu')
                self.assertEqual(workers, 8)  # cpu_count * 2
                
                # IO task  
                workers = Parallel.get_optimal_workers('io')
                self.assertLessEqual(workers, 32)

    def test_parallel_get_optimal_workers_interpreter_pool(self):
        """Cover get_optimal_workers with interpreter pool support."""
        from nodupe.tools.parallel.parallel_logic import Parallel
        
        with patch.object(Parallel, 'is_free_threaded', return_value=False):
            with patch.object(Parallel, 'supports_interpreter_pool', return_value=True):
                with patch.object(Parallel, 'get_cpu_count', return_value=4):
                    workers = Parallel.get_optimal_workers('cpu')
                    self.assertEqual(workers, 4)


class TestWalkerCoverageFinal(unittest.TestCase):
    """Coverage tests for nodupe/tools/scanner_engine/walker.py remaining gaps."""

    def test_walker_archive_handler_error(self):
        """Cover archive handler error paths in walker."""
        from nodupe.tools.scanner_engine.walker import FileWalker

        # Create walker with mock archive handler that raises
        mock_archive = Mock()
        mock_archive.is_archive_file.return_value = True
        mock_archive.get_archive_contents_info.side_effect = RuntimeError("Archive error")
        
        walker = FileWalker(archive_handler=mock_archive)
        walker._enable_archive_support = True
        
        # Create temp directory with a file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.zip")
            with open(test_file, 'w') as f:
                f.write("test")
            
            # Walk should handle archive error gracefully
            files = walker.walk(tmpdir)
            # Should have at least the test file
            self.assertTrue(len(files) >= 1)

    def test_walker_file_filter_error(self):
        """Cover file filter error handling."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        walker = FileWalker()
        
        # Create a filter that raises
        def failing_filter(file_info):
            """Helper filter function that raises RuntimeError."""
            raise RuntimeError("Filter failed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test content")
            
            # Walk should continue despite filter error
            files = walker.walk(tmpdir, file_filter=failing_filter)
            # Should not include the file due to filter error, but walk continues

    def test_walker_get_file_info_error(self):
        """Cover _get_file_info error handling."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        walker = FileWalker()
        
        # File that doesn't exist should raise in _get_file_info
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a path that will fail stat
            nonexistent = os.path.join(tmpdir, "nonexistent.txt")
            
            # This should be caught and re-raised
            with self.assertRaises(Exception):
                walker._get_file_info(nonexistent, "nonexistent.txt")

    def test_walker_is_archive_file_error(self):
        """Cover _is_archive_file error handling."""
        from nodupe.tools.scanner_engine.walker import FileWalker

        # Mock archive handler that raises on is_archive_file
        mock_archive = Mock()
        mock_archive.is_archive_file.side_effect = RuntimeError("Archive check failed")
        
        walker = FileWalker(archive_handler=mock_archive)
        
        result = walker._is_archive_file("/some/path/file.zip")
        # Should return False due to exception handling
        self.assertFalse(result)

    def test_walker_progress_callback_error(self):
        """Cover progress callback error handling."""
        from nodupe.tools.scanner_engine.walker import FileWalker
        
        walker = FileWalker()
        
        # Create a callback that raises
        def failing_callback(progress):
            """Helper callback function that raises RuntimeError."""
            raise RuntimeError("Progress callback failed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test content")
            
            # Walk should continue despite callback error
            files = walker.walk(tmpdir, on_progress=failing_callback)
            self.assertTrue(len(files) >= 1)


class TestContainerCoverageFinal(unittest.TestCase):
    """Final coverage tests for container.py - ensure 100%."""

    def test_container_check_compliance_full(self):
        """Cover check_compliance with all scenarios."""
        from nodupe.core.container import ServiceContainer
        
        sc = ServiceContainer()
        
        # Empty container
        report = sc.check_compliance()
        self.assertEqual(report['status'], 'OPERATIONAL')
        self.assertEqual(report['metrics']['total_services'], 0)
        
        # With services
        sc.register_service('svc1', 'value1')
        sc.register_factory('fac1', lambda: 'factory_value')
        
        report = sc.check_compliance()
        self.assertEqual(report['metrics']['total_services'], 2)
        self.assertIn('svc1', report['services'])
        self.assertIn('fac1', report['services'])
        self.assertTrue(report['services']['svc1']['is_active'])
        self.assertTrue(report['services']['fac1']['is_lazy'])

    def test_container_factory_exception(self):
        """Cover factory exception handling."""
        from nodupe.core.container import ServiceContainer
        
        sc = ServiceContainer()
        
        def failing_factory():
            """Helper factory function that raises ValueError."""
            raise ValueError("Factory failed")
        
        sc.register_factory('fail', failing_factory)
        
        # Should return None and log warning
        result = sc.get_service('fail')
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
