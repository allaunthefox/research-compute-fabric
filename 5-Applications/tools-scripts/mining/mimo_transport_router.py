#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
MIMO Transport Router — Multi-band Orchestration

Coordinates transport decisions across:
  - Omnitoken (default, Warden-based)
  - I2P (eepsite, deterministic manifests)
  - Tailscale (VPN overlay, if active)
  - TOR (onion routing, if available)

Router policy: Try high-priority first, fallback on timeout.

This module provides a unified interface for the mcp_harness and infrastructure.
"""

import json
import threading
import time
from typing import Dict, Optional, Tuple, List
from enum import Enum
import os
import sys
import glob
import shutil
import socket
import subprocess

# Local imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from transport_organism import TransportOrganism, TransportAction
    _HAS_ORGANISM = True
except ImportError:
    _HAS_ORGANISM = False

try:
    from i2p_transport_adapter import I2PTransportAdapter, I2PTransportState
    _HAS_I2P = True
except ImportError:
    _HAS_I2P = False

try:
    from dht_layer import get_dht, DHTNode, ReplicationStrategy
    _HAS_DHT = True
except ImportError:
    _HAS_DHT = False

try:
    from encryption_layers import get_encryption_layer, EncryptionContext, EncryptionScheme
    _HAS_ENCRYPTION = True
except ImportError:
    _HAS_ENCRYPTION = False


class TransportMethod(Enum):
    OMNITOKEN = "omnitoken"
    USB_DMA = "usb_dma"
    WIFI_UDP = "wifi_udp"
    BLUETOOTH_L2CAP = "bluetooth_l2cap"
    I2P = "i2p"
    TAILSCALE = "tailscale"
    TOR = "tor"


class MIMORouter:
    """
    Multi-band transport router.
    
    Selects best transport based on:
      1. Payload structure (MI analysis)
      2. Destination availability
      3. Latency budget
      4. Fallback options
    """
    
    def __init__(self):
        self.organism = TransportOrganism() if _HAS_ORGANISM else None
        self.i2p_adapter = I2PTransportAdapter() if _HAS_I2P else None
        self.dht = get_dht() if _HAS_DHT else None
        self.encryption = get_encryption_layer() if _HAS_ENCRYPTION else None
        
        # Track bandwidth usage per transport
        self.transport_usage: Dict[str, Dict] = {
            'omnitoken': {'bytes': 0, 'transfers': 0, 'errors': 0},
            'usb_dma': {'bytes': 0, 'transfers': 0, 'errors': 0},
            'wifi_udp': {'bytes': 0, 'transfers': 0, 'errors': 0},
            'bluetooth_l2cap': {'bytes': 0, 'transfers': 0, 'errors': 0},
            'i2p': {'bytes': 0, 'transfers': 0, 'errors': 0},
            'tailscale': {'bytes': 0, 'transfers': 0, 'errors': 0},
            'tor': {'bytes': 0, 'transfers': 0, 'errors': 0},
        }
        
        self.transport_available: Dict[str, bool] = {
            'omnitoken': True,  # Always available
            'usb_dma': False,
            'wifi_udp': False,
            'bluetooth_l2cap': False,
            'i2p': self.i2p_adapter is not None and self.i2p_adapter.state == I2PTransportState.READY,
            'tailscale': False,  # Disable for now
            'tor': False,  # Disable for now
        }
        self.transport_inventory: Dict[str, Dict] = {}
        self.probe_local_transports()
        
        self._lock = threading.Lock()
        self.security_posture = "JUPITER_MURPHY_MAX_ANGER"
        self.fail_closed_encryption = True
        self.require_redundant_paths = True

    def probe_local_transports(self) -> Dict[str, Dict]:
        """Detect local physical/link transports without opening data sessions.

        USB is marked available only when a data-bearing local endpoint exists
        (serial ACM/USB, USB network interface, or USB block transport). Root
        hubs alone are inventory, not a usable mesh data plane.
        """
        inventory: Dict[str, Dict] = {}

        serial_ports = sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))
        usb_block = []
        try:
            for name in os.listdir('/sys/block'):
                tran = f'/sys/block/{name}/device/../../../../../../removable'
                if os.path.exists(tran):
                    usb_block.append(name)
        except Exception:
            usb_block = []

        usb_net = []
        try:
            for iface in os.listdir('/sys/class/net'):
                path = os.path.realpath(f'/sys/class/net/{iface}/device')
                if '/usb' in path:
                    usb_net.append(iface)
        except Exception:
            usb_net = []

        inventory['usb_dma'] = {
            'serial_ports': serial_ports,
            'usb_net_interfaces': sorted(usb_net),
            'usb_block_devices': sorted(usb_block),
            'available': bool(serial_ports or usb_net or usb_block),
        }

        wifi_ifaces = []
        try:
            for iface in os.listdir('/sys/class/net'):
                if os.path.isdir(f'/sys/class/net/{iface}/wireless'):
                    operstate = ''
                    try:
                        with open(f'/sys/class/net/{iface}/operstate', encoding='utf-8') as f:
                            operstate = f.read().strip()
                    except Exception:
                        pass
                    wifi_ifaces.append({'iface': iface, 'operstate': operstate})
        except Exception:
            wifi_ifaces = []
        inventory['wifi_udp'] = {
            'interfaces': wifi_ifaces,
            'available': any(row.get('operstate') == 'up' for row in wifi_ifaces),
        }

        bt_powered = False
        bt_devices: List[str] = []
        if shutil.which('bluetoothctl'):
            try:
                show = subprocess.run(
                    ['bluetoothctl', 'show'],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                    check=False,
                ).stdout
                bt_powered = 'Powered: yes' in show
                devices = subprocess.run(
                    ['bluetoothctl', 'devices'],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                    check=False,
                ).stdout
                bt_devices = [line.strip() for line in devices.splitlines() if line.strip()]
            except Exception:
                bt_powered = False
        inventory['bluetooth_l2cap'] = {
            'powered': bt_powered,
            'paired_or_seen_devices': bt_devices,
            'available': bt_powered,
        }

        tailscale_available = False
        if shutil.which('tailscale'):
            try:
                result = subprocess.run(
                    ['tailscale', 'status', '--json'],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                    check=False,
                )
                tailscale_available = result.returncode == 0
            except Exception:
                tailscale_available = False
        inventory['tailscale'] = {'available': tailscale_available}

        for name, data in inventory.items():
            if name in self.transport_available:
                self.transport_available[name] = bool(data.get('available'))
        self.transport_inventory = inventory
        return inventory
    
    def probe_i2p(self) -> bool:
        """Check if I2P daemon is available"""
        if self.i2p_adapter is None:
            return False
        
        try:
            if self.i2p_adapter.state != I2PTransportState.READY:
                if self.i2p_adapter.initialize():
                    self.transport_available['i2p'] = True
                    return True
            else:
                self.transport_available['i2p'] = True
                return True
        except Exception:
            self.transport_available['i2p'] = False
        
        return False

    def _select_adaptive_shell(self, transport: str, payload_size: int, scheme: Optional[str] = None) -> Dict:
        """Choose a dynamic encoding shell rather than static encoding."""
        # Shell selection is adaptive because some encryption schemes and payload
        # characteristics make specific paths brittle or non-viable.
        if transport == 'i2p':
            candidates = ['adaptive_manifest', 'adaptive_jupiter', 'adaptive_stream']
        elif transport == 'tor':
            candidates = ['adaptive_stream', 'adaptive_manifest']
        elif transport == 'usb_dma':
            candidates = ['adaptive_stream', 'adaptive_manifest']
        elif transport == 'wifi_udp':
            candidates = ['adaptive_manifest', 'adaptive_stream']
        elif transport == 'bluetooth_l2cap':
            candidates = ['adaptive_stream', 'adaptive_manifest']
        else:
            candidates = ['adaptive_stream', 'adaptive_manifest', 'adaptive_jupiter']

        if payload_size > 64 * 1024:
            selected = 'adaptive_manifest'
        elif scheme in ('pqc_hybrid', 'pqc_staggered'):
            selected = 'adaptive_jupiter'
        else:
            selected = candidates[0]

        return {
            'selected_shell': selected,
            'candidates': candidates,
            'static_encoding': False,
        }

    def _encryption_path_constraints(self, scheme: Optional[str]) -> Dict:
        """Return transport/path constraints implied by encryption properties."""
        constraints = {
            'blocked_paths': [],
            'blocked_transports': [],
            'reason': 'none',
        }

        if scheme == 'xor_simple':
            constraints['blocked_transports'] = ['tor', 'i2p']
            constraints['blocked_paths'] = ['anonymity_strict']
            constraints['reason'] = 'weak_scheme_not_allowed_on_anonymous_paths'
        elif scheme == 'layered':
            constraints['blocked_paths'] = ['ultra_low_latency']
            constraints['reason'] = 'layered_overhead_blocks_low_latency_paths'
        elif scheme in ('pqc_hybrid', 'pqc_staggered'):
            constraints['blocked_paths'] = ['static_shell_encoding']
            constraints['reason'] = 'pqc_shift_requires_dynamic_shell_adaptation'

        return constraints

    def _apply_encryption_constraints(self, routing: Dict, scheme: Optional[str], payload_size: int) -> None:
        """Mutate routing in-place based on encryption-implied constraints."""
        constraints = self._encryption_path_constraints(scheme)
        routing['routing_metadata']['path_constraints'] = constraints

        blocked_transports = set(constraints.get('blocked_transports', []))
        primary = routing['primary_transport']
        if primary in blocked_transports:
            candidates = [
                t for t in routing.get('fallback_transports', [])
                if t not in blocked_transports
            ]
            if 'omnitoken' not in candidates and 'omnitoken' not in blocked_transports:
                candidates.append('omnitoken')

            if candidates:
                routing['routing_metadata']['transport_shift'] = {
                    'from': primary,
                    'to': candidates[0],
                    'reason': constraints.get('reason', 'constraint')
                }
                routing['primary_transport'] = candidates[0]
                if candidates[0] in routing['fallback_transports']:
                    routing['fallback_transports'].remove(candidates[0])
                if primary not in routing['fallback_transports']:
                    routing['fallback_transports'].append(primary)

        shell = self._select_adaptive_shell(
            routing['primary_transport'],
            payload_size,
            scheme=scheme
        )
        routing['routing_metadata']['encoding_shell'] = shell

    def _apply_jupiter_murphy_policy(self, routing: Dict) -> None:
        """Apply strict resilience policy: assume worst-case path failures."""
        meta = routing['routing_metadata']
        meta['security_posture'] = self.security_posture
        meta['assumption_model'] = 'every_path_can_fail_or_be_attacked'
        meta['failure_model'] = 'murphy_max_anger'

        # Normalize fallbacks to available transports and dedupe.
        available = set(self.get_available_transports())
        primary = routing['primary_transport']
        filtered = []
        for t in routing.get('fallback_transports', []):
            if t != primary and t in available and t not in filtered:
                filtered.append(t)

        # Ensure non-static, redundant path intent under adversarial assumptions.
        if self.require_redundant_paths:
            for candidate in ['usb_dma', 'wifi_udp', 'tailscale', 'bluetooth_l2cap', 'omnitoken', 'i2p', 'tor']:
                if candidate != primary and candidate in available and candidate not in filtered:
                    filtered.append(candidate)
                if len(filtered) >= 2:
                    break

        routing['fallback_transports'] = filtered
        meta['redundancy'] = {
            'enabled': self.require_redundant_paths,
            'fallback_count': len(filtered),
            'target_min_fallbacks': 2,
        }
    
    def route_payload(self, payload: bytes, destination_hint: str = None) -> Dict:
        """
        Route payload across available transports with DHT peer discovery.

        Returns: {
            'method': TransportMethod,
            'manifest_id': str,
            'primary_transport': str,
            'fallback_transports': List[str],
            'dht_peers': List[Dict],  # DHT discovered replicas
            'routing_metadata': Dict,
        }

        Z3-verified invariants (2026-04-02, OMNITOKEN_L1_ALIGNMENT_2026_04_02.md):
          PASS: omnitoken always on critical path (primary when organism absent, fallback when present)
          PASS (organism present): I2P preferred as primary when MI score > 1.5 and I2P available
          NOTE: I2P-preference and omnitoken-in-fallback invariants require organism_present=True.
                Without organism: primary='omnitoken', fallback=[] is correct headless behavior.
        """
        import hashlib
        
        routing = {
            'method': TransportMethod.OMNITOKEN,
            'manifest_id': None,
            'primary_transport': 'omnitoken',
            'fallback_transports': [],
            'dht_peers': [],
            'routing_metadata': {
                'payload_size': len(payload),
                'timestamp': time.time(),
                'encoding_shell': self._select_adaptive_shell('omnitoken', len(payload)),
            }
        }
        
        # Compute content hash for DHT lookup
        content_hash = hashlib.sha256(payload).hexdigest()
        routing['routing_metadata']['content_hash'] = content_hash[:16] + '...'
        
        # Analyze payload structure
        if self.organism:
            action = self.organism.select_action(payload)
            routing['routing_metadata']['mi_score'] = action.mi_score
            routing['routing_metadata']['compress'] = action.compress
            routing['routing_metadata']['chunk_size'] = action.chunk_size
            
            # If high MI and I2P is available, prefer manifest-based routing
            if action.mi_score > 1.5 and self.transport_available.get('i2p'):
                routing['primary_transport'] = 'i2p'
                routing['fallback_transports'].append('omnitoken')
                
                # Generate I2P manifest
                if self.i2p_adapter:
                    manifest = self.i2p_adapter.get_manifest_for_payload(
                        payload,
                        chunk_size=action.chunk_size,
                        compress_method=action.compress_method
                    )
                    routing['manifest_id'] = manifest.manifest_id
                    routing['method'] = TransportMethod.I2P
                    routing['routing_metadata']['manifest'] = json.loads(manifest.to_json())
            
            # Always have omnitoken as fallback
            if 'omnitoken' not in routing['fallback_transports']:
                routing['fallback_transports'].append('omnitoken')
        else:
            # No organism → default omnitoken
            routing['fallback_transports'] = []
        
        # DHT peer discovery
        if self.dht:
            try:
                peers = self.dht.find_nodes(content_hash, 'mimo_router')
                if peers and 'nodes' in peers:
                    routing['dht_peers'] = peers['nodes'][:5]  # Top 5 replicas
                    routing['routing_metadata']['dht_lookup'] = peers['method']
            except Exception as e:
                routing['routing_metadata']['dht_error'] = str(e)
        
        # Encryption encapsulation (n-space adaptation)
        if self.encryption:
            try:
                # Build encryption context from routing decisions
                enc_context = EncryptionContext(
                    transport=routing['primary_transport'],
                    content_type='binary',
                    sensitivity='medium',
                    latency_budget_ms=100,
                    trust_level='peer',
                    payload_size=len(payload),
                    source_id='mimo_router'
                )
                
                # Encrypt payload
                encrypted = self.encryption.encrypt(payload, enc_context)
                
                # Update routing metadata with encryption info
                routing['routing_metadata']['encryption'] = {
                    'scheme': encrypted.scheme.value,
                    'key_id': encrypted.key_id,
                    'context_hash': encrypted.context_hash,
                }
                self._apply_encryption_constraints(
                    routing,
                    encrypted.scheme.value,
                    len(payload)
                )
                routing['encryption_applied'] = True
            except Exception as e:
                routing['routing_metadata']['encryption_error'] = str(e)
                routing['encryption_applied'] = False

        # Jupiter-story Murphy model: enforce strict, hostile-path assumptions.
        self._apply_jupiter_murphy_policy(routing)

        if self.fail_closed_encryption and self.encryption and not routing.get('encryption_applied', False):
            routing['blocked'] = True
            routing['block_reason'] = 'encryption_required_fail_closed'
            routing['routing_metadata']['fail_closed'] = True
        else:
            routing['blocked'] = False
            routing['routing_metadata']['fail_closed'] = self.fail_closed_encryption
        
        return routing
    
    def get_available_transports(self) -> List[str]:
        """List available transports"""
        return [k for k, v in self.transport_available.items() if v]
    
    def get_status(self) -> Dict:
        """Return full router status"""
        return {
            'available_transports': self.get_available_transports(),
            'transport_status': dict(self.transport_available),
            'transport_inventory': dict(self.transport_inventory),
            'usage': dict(self.transport_usage),
            'i2p_info': self.i2p_adapter.get_status() if self.i2p_adapter else None,
            'dht_info': self.dht.get_status() if self.dht else None,
            'encryption_info': self.encryption.get_status() if self.encryption else None,
            'timestamp': time.time(),
        }
    
    def shutdown(self):
        """Graceful shutdown"""
        if self.i2p_adapter:
            self.i2p_adapter.shutdown()


# ───────────────────────────────────────────────────────────────────────────
# Global singleton
# ───────────────────────────────────────────────────────────────────────────

_router: Optional[MIMORouter] = None
_router_lock = threading.Lock()


def get_router() -> MIMORouter:
    """Get or create global MIMO router"""
    global _router
    if _router is None:
        with _router_lock:
            if _router is None:
                _router = MIMORouter()
    return _router


# ───────────────────────────────────────────────────────────────────────────
# CLI Test
# ───────────────────────────────────────────────────────────────────────────

def main():
    router = get_router()
    
    print("[MIMO Router] Probing transports...")
    
    print(f"✓ Omnitoken: Always available")
    
    if router.probe_i2p():
        print(f"✓ I2P: Connected to SAM bridge")
    else:
        print(f"✗ I2P: SAM bridge not available")
    
    print(f"\nAvailable transports: {router.get_available_transports()}")
    
    # Test routing with various payloads
    test_payloads = [
        (b"Small payload", "small"),
        (b"Lorem ipsum " * 1000, "medium_structured"),
        (b"Pseudorandom data" * 1000, "medium_random"),
    ]
    
    for payload, label in test_payloads:
        print(f"\n[Routing Test: {label}]")
        routing = router.route_payload(payload)
        print(f"  Primary: {routing['primary_transport']}")
        print(f"  Fallback: {routing['fallback_transports']}")
        print(f"  Method: {routing['method'].value}")
        if routing['manifest_id']:
            print(f"  Manifest: {routing['manifest_id'][:16]}...")
        print(f"  MI score: {routing['routing_metadata'].get('mi_score', 'N/A')}")
    
    print(f"\n[Router Status]")
    print(json.dumps(router.get_status(), indent=2, default=str))
    
    router.shutdown()


if __name__ == '__main__':
    main()
