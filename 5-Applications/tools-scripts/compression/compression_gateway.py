#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Compression Gateway — Version-Agnostic Socket Interface

This module provides a unified interface to the compression organism,
regardless of which version or protocol port it is currently running on.

Usage:
    from compression_gateway import CompressionGateway

    with CompressionGateway(host="100.119.32.107") as gw:
        status = gw.get_status()
        print(f"Connected to {gw.protocol_version}")
"""

import socket
import json
import struct
import time
from typing import Optional, Dict, Any

class GatewayError(Exception):
    pass

class CompressionGateway:
    def __init__(self, host: str, ports: list[int] = None, timeout: float = 5.0):
        self.host = host
        self.ports = ports or list(range(8440, 8451))
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self.protocol_version = "unknown"
        self.connected_port = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def connect(self):
        """Find the active port and establish connection."""
        last_err = None
        for port in self.ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self.timeout)
                s.connect((self.host, port))
                
                # Try Handshake
                if self._negotiate_version(s):
                    self.sock = s
                    self.connected_port = port
                    return

            except (ConnectionRefusedError, socket.timeout, OSError) as e:
                last_err = e
                try: s.close()
                except: pass
        
        raise GatewayError(f"Could not connect to organism on {self.host} (Last error: {last_err})")

    def _negotiate_version(self, sock: socket.socket) -> bool:
        """Send handshake and parse response."""
        try:
            msg = json.dumps({"cmd": "handshake"})
            sock.sendall(msg.encode('utf-8') + b'\n')
            
            response = self._recv_line(sock)
            if not response:
                return False
            
            data = json.loads(response)
            if data.get("status") == "ok":
                self.protocol_version = data.get("version", "v1_legacy")
                return True
        except Exception:
            return False
        return False

    def _recv_line(self, sock: socket.socket) -> str:
        """Read until newline."""
        data = b""
        while True:
            chunk = sock.recv(1)
            if not chunk or chunk == b'\n':
                break
            data += chunk
        return data.decode('utf-8')

    def close(self):
        if self.sock:
            try: self.sock.close()
            except: pass
        self.sock = None

    # --- Public API ---

    def ping(self) -> bool:
        """Check if connection is alive."""
        if not self.sock: return False
        try:
            self.sock.sendall(json.dumps({"cmd": "ping"}).encode('utf-8') + b'\n')
            resp = self._recv_line(self.sock)
            return "pong" in resp
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Retrieve organism status."""
        if not self.sock: raise GatewayError("Not connected")
        try:
            self.sock.sendall(json.dumps({"cmd": "status"}).encode('utf-8') + b'\n')
            resp = self._recv_line(self.sock)
            return json.loads(resp)
        except Exception:
            return {"error": "Status request failed"}

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "100.119.32.107" # RackNerd IP
    print(f"[*] Probing {target} for compression organism...")
    
    try:
        with CompressionGateway(target) as gw:
            print(f"[+] Connected on port {gw.connected_port}")
            print(f"[+] Protocol: {gw.protocol_version}")
            
            # Live Status Check
            status = gw.get_status()
            print(f"[+] Status: {json.dumps(status, indent=2)}")
            
            # Ping Test
            if gw.ping():
                print("[+] Ping successful")
    except GatewayError as e:
        print(f"[-] Error: {e}")
        sys.exit(1)
