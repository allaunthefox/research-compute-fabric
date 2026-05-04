# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for API IPC coverage (ipc.py).

This module targets specific coverage gaps identified in the implementation plan.
"""

import json
import os
import threading
import unittest
from unittest.mock import Mock, patch

# Import modules under test
from nodupe.core.api.ipc import ActionCode, ToolIPCServer


class TestIPCCoverage(unittest.TestCase):
    """Tests for ipc.py coverage."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.registry = Mock()
        self.socket_path = "/tmp/nodupe_test_ipc.sock"
        self.server = ToolIPCServer(self.registry, socket_path=self.socket_path)

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        if self.server:
            self.server.stop()
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

    def test_start_idempotency(self):
        """Test start() idempotency."""
        self.server.start()
        thread_id = self.server._server_thread.ident
        
        # Call start again - should do nothing
        self.server.start()
        assert self.server._server_thread.ident == thread_id

    def test_stop_idempotency(self):
        """Test stop() idempotency."""
        self.server.start()
        self.server.stop()
        
        # Call stop again - should do nothing
        self.server.stop()
        assert self.server._server_thread is None

    def test_server_accept_error(self):
        """Test server accept() error handling."""
        with patch('socket.socket') as mock_socket_class:
            mock_server_socket = Mock()
            mock_socket_class.return_value.__enter__.return_value = mock_server_socket
            
            # Use side effect to raise exception then STOP the loop
            def accept_side_effect():
                """Mock accept() to raise an exception for testing error handling."""
                if not self.server._stop_event.is_set():
                    # We must allow the exception to propagate to the except block
                    # But we also need to stop the loop eventually.
                    # The problematic code checks _stop_event AFTER exception.
                    # So we can't set it here if we want logging.
                    # We can use a custom exception and catch it in the test?
                    # No, it's in a thread.
                    # We rely on the loop checking _stop_event.
                    pass
                raise Exception("Accept failed")
            
            mock_server_socket.accept.side_effect = accept_side_effect
            
            # We need to stop the server after a short delay to let it loop once
            # But run_server runs in current thread in this test?
            # self.server._run_server() is called directly.
            # So it will block.
            # We need to set _stop_event from a timer
            
            threading.Timer(0.1, self.server._stop_event.set).start()
            
            with patch.object(self.server, '_log_event') as mock_log:
                # This will loop until timer sets stop event
                # It will produce multiple "Accept failed" logs
                self.server._run_server()
                
                # Check if ANY log matches
                args_list = mock_log.call_args_list
                found = False
                for args, _ in args_list:
                    if args[0] == ActionCode.ERR_INTERNAL and "Accept failed" in args[1]:
                        found = True
                        break
                assert found

    def test_handle_connection_invalid_json(self):
        """Test handling of invalid JSON."""
        mock_conn = Mock()
        # Invalid JSON
        mock_conn.recv.return_value = b"{ invalid json"
        
        with patch.object(self.server, '_send_error') as mock_send_error:
            self.server._handle_connection(mock_conn)
            mock_send_error.assert_called_with(mock_conn, "Parse error", None, code=ActionCode.ERR_INVALID_JSON)

    def test_handle_connection_missing_rpc_version(self):
        """Test handling of missing jsonrpc version."""
        mock_conn = Mock()
        mock_conn.recv.return_value = json.dumps({"id": 1}).encode()
        
        with patch.object(self.server, '_send_error') as mock_send_error:
            self.server._handle_connection(mock_conn)
            mock_send_error.assert_called()
            assert "jsonrpc" in mock_send_error.call_args[0][1]

    def test_handle_connection_missing_method(self):
        """Test handling of missing method."""
        mock_conn = Mock()
        request = {
            "jsonrpc": "2.0",
            "tool": "TestTool",
            # missing method
            "id": 1
        }
        mock_conn.recv.return_value = json.dumps(request).encode()
        
        with patch.object(self.server, '_send_error') as mock_send_error:
            self.server._handle_connection(mock_conn)
            mock_send_error.assert_called()
            assert "Missing tool or method" in mock_send_error.call_args[0][1]

    def test_handle_connection_tool_not_found(self):
        """Test handling of non-existent tool."""
        mock_conn = Mock()
        request = {
            "jsonrpc": "2.0",
            "tool": "GhostTool",
            "method": "run",
            "id": 1
        }
        mock_conn.recv.return_value = json.dumps(request).encode()
        
        self.registry.get_tool.return_value = None
        
        with patch.object(self.server, '_send_error') as mock_send_error:
            self.server._handle_connection(mock_conn)
            mock_send_error.assert_called()
            assert "not found" in mock_send_error.call_args[0][1]

    def test_handle_connection_method_not_exposed(self):
        """Test handling of method not in api_methods."""
        mock_conn = Mock()
        request = {
            "jsonrpc": "2.0",
            "tool": "TestTool",
            "method": "secret_method",
            "id": 1
        }
        mock_conn.recv.return_value = json.dumps(request).encode()
        
        mock_tool = Mock()
        mock_tool.api_methods = {} # Empty
        self.registry.get_tool.return_value = mock_tool
        
        with patch.object(self.server, '_send_error') as mock_send_error:
            self.server._handle_connection(mock_conn)
            mock_send_error.assert_called()
            assert "not exposed" in mock_send_error.call_args[0][1]

            assert "not exposed" in mock_send_error.call_args[0][1]

    def test_handle_connection_execution_error(self):
        """Test handling of method execution exception."""
        mock_conn = Mock()
        request = {
            "jsonrpc": "2.0",
            "tool": "TestTool",
            "method": "boom",
            "id": 1
        }
        mock_conn.recv.return_value = json.dumps(request).encode()
        
        mock_tool = Mock()
        mock_method = Mock(side_effect=Exception("Explosion"))
        mock_tool.api_methods = {"boom": mock_method}
        self.registry.get_tool.return_value = mock_tool

        with patch.object(self.server, '_send_error', wraps=self.server._send_error) as spy_send_error:
            # We mock conn.sendall to verify what was sent
            self.server._handle_connection(mock_conn)
            
            # Verify call happened
            args_list = spy_send_error.call_args_list
            assert len(args_list) > 0
            
            # Verify json was sent
            mock_conn.sendall.assert_called()
            sent_data = mock_conn.sendall.call_args[0][0]
            response = json.loads(sent_data)
            assert "error" in response
            assert "Execution failed" in response["error"]["message"] or "Explosion" in response["error"]["message"]

    def test_handle_connection_success(self):
        """Test successful execution."""
        mock_conn = Mock()
        request = {
            "jsonrpc": "2.0",
            "tool": "TestTool",
            "method": "echo",
            "params": {"msg": "hello"},
            "id": 100
        }
        mock_conn.recv.return_value = json.dumps(request).encode()
        
        mock_tool = Mock()
        mock_tool.api_methods = {"echo": lambda msg: msg}
        self.registry.get_tool.return_value = mock_tool
        
        with patch.object(self.server, '_send_response', wraps=self.server._send_response):
            self.server._handle_connection(mock_conn)
            
            mock_conn.sendall.assert_called()
            sent_data = mock_conn.sendall.call_args[0][0]
            response = json.loads(sent_data)
            assert response["result"] == "hello"
            assert response["id"] == 100


    def test_handle_connection_socket_error(self):
        """Test handling of socket errors during processing."""
        mock_conn = Mock()
        mock_conn.recv.side_effect = Exception("Connection reset")
        
        with patch.object(self.server, '_log_event') as mock_log:
            self.server._handle_connection(mock_conn)
            
            # Should not raise, but log error
            args_list = mock_log.call_args_list
            found = False
            for args, _ in args_list:
                if args[0] == ActionCode.ERR_INTERNAL and "Connection error" in args[1]:
                    found = True
                    break
            assert found
            
    def test_handle_connection_rate_limit_exceeded(self):
        """Test handling of rate limit exceeded."""
        mock_conn = Mock()
        
        with patch.object(self.server.rate_limiter, 'check_rate_limit', return_value=False):
            with patch.object(self.server, '_send_error') as mock_send_error:
                self.server._handle_connection(mock_conn)
                mock_send_error.assert_called_with(mock_conn, "Rate limit exceeded", None, code=ActionCode.RATE_LIMIT_HIT)


if __name__ == '__main__':
    unittest.main()
