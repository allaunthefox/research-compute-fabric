# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Tests for NTP internal methods in time_sync_tool.py."""

import socket
import struct
import time
from unittest.mock import MagicMock, patch

import pytest

from nodupe.tools.time_sync.time_sync_tool import time_synchronizationTool


def test_resolve_addresses():
    """Test _resolve_addresses."""
    tool = time_synchronizationTool()
    
    with patch('socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))]):
        addrs = tool._resolve_addresses("host")
        assert len(addrs) == 1
        assert addrs[0][4][0] == '1.1.1.1'
        
    with patch('socket.getaddrinfo', side_effect=socket.gaierror):
        addrs = tool._resolve_addresses("bad")
        assert addrs == []

def test_query_address_success():
    """Test _query_address with mock socket."""
    tool = time_synchronizationTool()
    addr_info = (socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))
    
    # NTP response packet (48 bytes)
    response = bytearray(48)
    struct.pack_into("!II", response, 32, 3000000000, 0) # t2
    struct.pack_into("!II", response, 40, 3000000001, 0) # t3
    
    with patch('nodupe.tools.time_sync.time_sync_tool.socket.socket') as mock_sock_cls:
        mock_sock = MagicMock()
        mock_sock_cls.return_value.__enter__.return_value = mock_sock
        mock_sock.recvfrom.return_value = (response, ('1.1.1.1', 123))
        
        server_time, offset, delay = tool._query_address(addr_info, timeout=1.0)
        assert server_time > 0
        assert isinstance(offset, float)
        assert isinstance(delay, float)

def test_query_address_short_response():
    """Test _query_address error handling for short response."""
    tool = time_synchronizationTool()
    addr_info = (socket.AF_INET, socket.SOCK_DGRAM, 17, '', ('1.1.1.1', 123))
    
    with patch('nodupe.tools.time_sync.time_sync_tool.socket.socket') as mock_sock_cls:
        mock_sock = MagicMock()
        mock_sock_cls.return_value.__enter__.return_value = mock_sock
        mock_sock.recvfrom.return_value = (b"too short", ('1.1.1.1', 123))
        
        with pytest.raises(ValueError, match="Short NTP response"):
            tool._query_address(addr_info, timeout=1.0)

def test_query_ntp_once_success():
    """Test _query_ntp_once success path."""
    tool = time_synchronizationTool()
    with patch.object(tool, '_resolve_addresses', return_value=[(1,2,3,4,5)]):
        with patch.object(tool, '_query_address', return_value=(1000.0, 0.1, 0.01)):
            server_time, offset, delay = tool._query_ntp_once("host", 1.0)
            assert server_time == 1000.0

def test_query_ntp_once_no_addrs():
    """Test _query_ntp_once failure - no addresses."""
    tool = time_synchronizationTool()
    with patch.object(tool, '_resolve_addresses', return_value=[]):
        with pytest.raises(RuntimeError, match="DNS resolution failed"):
            tool._query_ntp_once("host", 1.0)

def test_query_ntp_once_no_best():
    """Test _query_ntp_once failure - query fails."""
    tool = time_synchronizationTool()
    with patch.object(tool, '_resolve_addresses', return_value=[(1,2,3,4,5)]):
        with patch.object(tool, '_query_address', side_effect=Exception("Timeout")):
            with pytest.raises(RuntimeError, match="No NTP responses"):
                tool._query_ntp_once("host", 1.0)

def test_query_servers_best_success():
    """Test _query_servers_best success."""
    tool = time_synchronizationTool()
    with patch.object(tool, '_query_ntp_once', return_value=(1000.0, 0.1, 0.01)):
        host, server_time, offset, delay = tool._query_servers_best(["h1", "h2"])
        assert host == "h1"
        assert server_time == 1000.0

def test_query_servers_best_failure():
    """Test _query_servers_best failure."""
    tool = time_synchronizationTool()
    with patch.object(tool, '_query_ntp_once', side_effect=Exception("Fail")):
        with pytest.raises(RuntimeError, match="No NTP responses"):
            tool._query_servers_best(["h1"])

def test_initialize_enabled():
    """Test initialize method when enabled."""
    tool = time_synchronizationTool(enabled=True)
    with patch.object(tool, 'force_sync') as mock_sync:
        tool.initialize(None)
        mock_sync.assert_called_once()

def test_initialize_disabled():
    """Test initialize method when disabled."""
    tool = time_synchronizationTool(enabled=False)
    with patch.object(tool, 'force_sync') as mock_sync:
        tool.initialize(None)
        mock_sync.assert_not_called()

def test_initialize_failing_sync():
    """Test initialize method when sync fails."""
    tool = time_synchronizationTool(enabled=True)
    with patch.object(tool, 'force_sync', side_effect=Exception("Fail")):
        # Should not raise
        tool.initialize(None)

def test_metadata():
    """Test metadata property."""
    tool = time_synchronizationTool()
    meta = tool.metadata
    assert meta.name == "time_synchronization"
    assert "ntp" in meta.tags

def test_api_methods():
    """Test api_methods property."""
    tool = time_synchronizationTool()
    methods = tool.api_methods
    assert "force_sync" in methods
    assert "get_status" in methods

def test_get_capabilities():
    """Test get_capabilities method."""
    tool = time_synchronizationTool()
    caps = tool.get_capabilities()
    assert caps["name"] == "time_synchronization"
    assert "ntp_sync" in caps["capabilities"]

def test_maybe_sync():
    """Test maybe_sync method."""
    tool = time_synchronizationTool()
    
    # Success
    with patch.object(tool, 'force_sync', return_value=("h", 1.0, 0.1, 0.01)):
        assert tool.maybe_sync() == ("h", 1.0, 0.1, 0.01)
        
    # Fail
    with patch.object(tool, 'force_sync', side_effect=Exception("Fail")):
        assert tool.maybe_sync() is None
        
    # Disabled
    tool.disable()
    assert tool.maybe_sync() is None

def test_run_standalone_sync():
    """Test run_standalone with --sync."""
    tool = time_synchronizationTool()
    with patch.object(tool, 'force_sync') as mock_sync:
        with patch.object(tool, 'get_authenticated_time', return_value="time"):
            with patch('builtins.print'):
                assert tool.run_standalone(["--sync"]) == 0
                mock_sync.assert_called_once()

def test_run_standalone_error():
    """Test run_standalone with error."""
    tool = time_synchronizationTool()
    with patch.object(tool, 'get_authenticated_time', side_effect=Exception("Fail")):
        with patch('builtins.print'):
            assert tool.run_standalone([]) == 1
