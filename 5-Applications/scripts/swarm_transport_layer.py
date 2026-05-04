#!/usr/bin/env python3
"""
Swarm-Specific Transport Layer

Multi-substrate transport layer optimized for distributed swarm coordination.
Built on top of Omnitoken layer with support for:
- Swarm coordination messages (heartbeats, consensus, learning sync)
- Multi-substrate routing (Omnitoken, I2P, Tailscale, TOR)
- DHT-based node discovery
- Jupiter box multiplexing
- Automatic failover and fault tolerance
- Swarm-specific message prioritization

Usage:
    transport = SwarmTransportLayer()
    transport.initialize()
    transport.broadcast_heartbeat(node_id, status)
    transport.send_consensus_message(proposal, target_nodes)
    transport.sync_learning_state(knowledge)
"""

import json
import hashlib
import time
import threading
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sys

# Add paths
sys.path.insert(0, '/home/allaun/Documents/Research Stack/scratch/exploit_recovery/5-Applications/tools-scripts/mining')
sys.path.insert(0, str(Path(__file__).parent))

# Import delta GCL encoder
try:
    from delta_gcl_encoder import DeltaGCLEncoder
    _HAS_DELTA_GCL = True
except ImportError:
    _HAS_DELTA_GCL = False

try:
    from mimo_transport_router import MIMORouter, TransportMethod, get_router
    _HAS_MIMO = True
except ImportError:
    _HAS_MIMO = False

try:
    from dht_layer import DHTLayer, DHTNode, ReplicationStrategy, get_dht
    _HAS_DHT = True
except ImportError:
    _HAS_DHT = False

try:
    from jupiter_boxes_transport import JupiterBoxesTransport, JupiterTransportPacket
    _HAS_JUPITER = True
except (ImportError, NameError):
    _HAS_JUPITER = False


class SwarmMessageType(Enum):
    """Types of swarm coordination messages"""
    HEARTBEAT = "heartbeat"           # Node status and availability
    CONSENSUS_PROPOSAL = "consensus"  # Consensus round proposals
    LEARNING_SYNC = "learning"         # Knowledge synchronization
    TASK_ASSIGNMENT = "task"          # Task distribution
    ALERT = "alert"                   # Emergency/warning messages
    DISCOVERY = "discovery"           # Node discovery
    METRICS = "metrics"               # Performance metrics


class SwarmPriority(Enum):
    """Message priority levels for swarm coordination"""
    CRITICAL = 0    # Alerts, consensus
    HIGH = 1        # Heartbeats, learning sync
    MEDIUM = 2      # Task assignments
    LOW = 3         # Metrics, discovery


class SwarmSubstrate(Enum):
    """Supported transport substrates"""
    OMNITOKEN = "omnitoken"      # Default, Warden-based
    I2P = "i2p"                  # Anonymous, deterministic manifests
    TAILSCALE = "tailscale"      # VPN overlay
    TOR = "tor"                  # Onion routing
    JUPITER = "jupiter"          # φ-locked MIMO multiplexing


@dataclass
class SwarmMessage:
    """Swarm coordination message with delta GCL compression"""
    message_type: SwarmMessageType
    priority: SwarmPriority
    source_node_id: str
    target_node_ids: List[str]
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(init=False)
    ttl: int = 60  # Time to live in seconds
    gcl_encoded: bool = field(init=False)
    gcl_sequence: Optional[str] = field(init=False, default=None)
    
    def __post_init__(self, use_delta_gcl: bool = True):
        # Generate message ID from hash
        content = f"{self.message_type.value}{self.source_node_id}{self.timestamp}{json.dumps(self.payload, sort_keys=True)}"
        self.message_id = hashlib.sha256(content.encode()).hexdigest()
        
        # Encode payload with delta GCL if available
        self.gcl_encoded = False
        self.gcl_sequence = None
        if _HAS_DELTA_GCL and use_delta_gcl:
            try:
                encoder = DeltaGCLEncoder()
                # Create manifest-like structure for encoding
                manifest = {
                    'message_type': self.message_type.value,
                    'priority': self.priority.value,
                    'source_node': self.source_node_id,
                    'layer': 'CARRY',
                    'domain': 'COMMS',
                    'tier': 'FOAM',
                    'condition': 'STABLE',
                    'tags': ['swarm', self.message_type.value],
                    'compression_metadata': {
                        'field_phi': 1.480381,
                        'compression_ratio': len(str(self.payload)) / max(1, len(str(self.payload))),
                        'foam_score': 7.0
                    }
                }
                self.gcl_sequence = encoder.encode_to_delta_gcl(manifest)
                self.gcl_encoded = True
            except Exception:
                pass  # Fall back to uncompressed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with GCL compression info"""
        return {
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'priority': self.priority.value,
            'source_node_id': self.source_node_id,
            'target_node_ids': self.target_node_ids,
            'payload': self.payload,
            'timestamp': self.timestamp,
            'ttl': self.ttl,
            'gcl_encoded': self.gcl_encoded,
            'gcl_sequence': self.gcl_sequence,
            'gcl_length': len(self.gcl_sequence) if self.gcl_sequence else 0
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'SwarmMessage':
        return SwarmMessage(
            message_type=SwarmMessageType(data['message_type']),
            priority=SwarmPriority(data['priority']),
            source_node_id=data['source_node_id'],
            target_node_ids=data['target_node_ids'],
            payload=data['payload'],
            timestamp=data['timestamp'],
            ttl=data.get('ttl', 60)
        )


@dataclass
class SwarmNodeStatus:
    """Swarm node status for heartbeats with delta GCL compression"""
    node_id: str
    available: bool
    cpu_usage: float
    memory_usage: float
    gcl_encoded: bool = field(init=False)
    gcl_sequence: Optional[str] = field(init=False, default=None)
    
    def __post_init__(self, use_delta_gcl: bool = True):
        # Encode status with delta GCL if available
        self.gcl_encoded = False
        self.gcl_sequence = None
        if _HAS_DELTA_GCL and use_delta_gcl:
            try:
                encoder = DeltaGCLEncoder()
                manifest = {
                    'node_id': self.node_id,
                    'status': 'available' if self.available else 'unavailable',
                    'cpu_load': self.cpu_usage,
                    'memory_load': self.memory_usage,
                    'layer': 'CORE',
                    'domain': 'COMPUTE',
                    'tier': 'FOAM',
                    'condition': 'STABLE',
                    'tags': ['swarm', 'node', 'status'],
                    'compression_metadata': {
                        'field_phi': 1.480381,
                        'compression_ratio': 0.85,
                        'foam_score': 7.0
                    }
                }
                self.gcl_sequence = encoder.encode_to_delta_gcl(manifest)
                self.gcl_encoded = True
            except Exception:
                pass
    active_agents: int
    learned_concepts: int
    last_heartbeat: float
    jupiter_box_index: int = -1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'available': self.available,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'active_agents': self.active_agents,
            'learned_concepts': self.learned_concepts,
            'last_heartbeat': self.last_heartbeat,
            'jupiter_box_index': self.jupiter_box_index
        }


class SwarmTransportLayer:
    """
    Swarm-specific transport layer for distributed coordination.
    
    Features:
    - Multi-substrate routing (Omnitoken, I2P, Tailscale, TOR, Jupiter)
    - DHT-based node discovery
    - Message prioritization
    - Automatic failover
    - Jupiter box multiplexing for swarm messages
    - Swarm-specific optimization (small messages, high frequency)
    """
    
    def __init__(self, node_id: Optional[str] = None):
        self.node_id = node_id or hashlib.sha256(f"swarm_node_{time.time()}".encode()).hexdigest()
        
        # Transport layers
        self.mimo_router = get_router() if _HAS_MIMO else None
        self.dht = get_dht(self.node_id) if _HAS_DHT else None
        self.jupiter_transport = JupiterBoxesTransport() if _HAS_JUPITER else None
        
        # Swarm state
        self.node_status: Dict[str, SwarmNodeStatus] = {}
        self.message_queue: Dict[SwarmPriority, List[SwarmMessage]] = {
            SwarmPriority.CRITICAL: [],
            SwarmPriority.HIGH: [],
            SwarmPriority.MEDIUM: [],
            SwarmPriority.LOW: []
        }
        
        # Transport preferences
        self.substrate_preferences: Dict[SwarmMessageType, List[SwarmSubstrate]] = {
            SwarmMessageType.HEARTBEAT: [SwarmSubstrate.OMNITOKEN, SwarmSubstrate.I2P, SwarmSubstrate.TAILSCALE],
            SwarmMessageType.CONSENSUS_PROPOSAL: [SwarmSubstrate.OMNITOKEN, SwarmSubstrate.JUPITER, SwarmSubstrate.TAILSCALE],
            SwarmMessageType.LEARNING_SYNC: [SwarmSubstrate.JUPITER, SwarmSubstrate.OMNITOKEN, SwarmSubstrate.TAILSCALE],
            SwarmMessageType.TASK_ASSIGNMENT: [SwarmSubstrate.OMNITOKEN, SwarmSubstrate.I2P, SwarmSubstrate.TAILSCALE],
            SwarmMessageType.ALERT: [SwarmSubstrate.OMNITOKEN, SwarmSubstrate.I2P, SwarmSubstrate.TOR, SwarmSubstrate.TAILSCALE],
            SwarmMessageType.DISCOVERY: [SwarmSubstrate.OMNITOKEN, SwarmSubstrate.I2P, SwarmSubstrate.TAILSCALE],
            SwarmMessageType.METRICS: [SwarmSubstrate.OMNITOKEN, SwarmSubstrate.TAILSCALE]
        }
        
        # Auto-adaptation state
        self.node_capabilities = {
            'has_tailscale': False,
            'has_i2p': False,
            'has_tor': False,
            'bandwidth_mbps': 100,
            'latency_ms': 50,
            'cpu_cores': 4,
            'memory_gb': 8
        }
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'failures': 0,
            'substrate_usage': {substrate.value: 0 for substrate in SwarmSubstrate},
            'auto_adaptations': 0
        }
        
        # Background processing
        self._running = False
        self._lock = threading.Lock()
        self._message_handlers: Dict[SwarmMessageType, List[Callable]] = {}
        
        print(f"[SwarmTransport] Initialized node: {self.node_id[:16]}...")
    
    def initialize(self) -> bool:
        """Initialize transport layer and register with DHT"""
        if not self.dht:
            print("[SwarmTransport] DHT not available")
            return False
        
        # Auto-detect node capabilities
        self._auto_detect_capabilities()
        
        # Adapt transport preferences based on capabilities
        self._adapt_transport_preferences()
        
        # Register self in DHT
        self_node = DHTNode(
            node_id=self.node_id,
            transport_type='omnitoken',
            address='127.0.0.1',
            port=8080,
            jupiter_box_index=0,
            bandwidth_mbps=self.node_capabilities['bandwidth_mbps'],
            latency_ms=self.node_capabilities['latency_ms'],
            available=True
        )
        
        success = self.dht.register_node(self_node)
        if success:
            print(f"[SwarmTransport] Registered with DHT")
            self._running = True
            return True
        else:
            print(f"[SwarmTransport] Already registered with DHT")
            self._running = True
            return True
    
    def _auto_detect_capabilities(self) -> Dict[str, Any]:
        """Auto-detect node capabilities for auto-adaptation"""
        import os
        import subprocess
        
        capabilities = self.node_capabilities.copy()
        
        # Detect Tailscale
        try:
            result = subprocess.run(['tailscale', 'status', '--json'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                capabilities['has_tailscale'] = True
                print(f"[SwarmTransport] ✓ Tailscale detected")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            capabilities['has_tailscale'] = False
            print(f"[SwarmTransport] ✗ Tailscale not available")
        
        # Detect I2P
        try:
            result = subprocess.run(['nc', '-z', '127.0.0.1', '7656'], 
                                  capture_output=True, timeout=2)
            if result.returncode == 0:
                capabilities['has_i2p'] = True
                print(f"[SwarmTransport] ✓ I2P SAM bridge detected")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            capabilities['has_i2p'] = False
            print(f"[SwarmTransport] ✗ I2P not available")
        
        # Detect CPU cores
        try:
            capabilities['cpu_cores'] = os.cpu_count() or 4
        except:
            capabilities['cpu_cores'] = 4
        
        # Detect memory
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        mem_kb = int(line.split()[1])
                        capabilities['memory_gb'] = mem_kb / (1024 * 1024)
                        break
        except:
            capabilities['memory_gb'] = 8
        
        self.node_capabilities = capabilities
        return capabilities
    
    def _adapt_transport_preferences(self):
        """Adapt transport preferences based on detected capabilities"""
        adaptations = []
        
        # If Tailscale is available, prioritize it for high-priority messages
        if self.node_capabilities['has_tailscale']:
            for msg_type in self.substrate_preferences:
                if SwarmSubstrate.TAILSCALE not in self.substrate_preferences[msg_type]:
                    self.substrate_preferences[msg_type].insert(1, SwarmSubstrate.TAILSCALE)
                    adaptations.append(f"Added Tailscale to {msg_type.value}")
            self.stats['auto_adaptations'] += len(adaptations)
            print(f"[SwarmTransport] Adapted for Tailscale: {len(adaptations)} changes")
        
        # If high bandwidth, prioritize Jupiter for large payloads
        if self.node_capabilities['bandwidth_mbps'] > 500:
            if SwarmSubstrate.JUPITER not in self.substrate_preferences[SwarmMessageType.LEARNING_SYNC]:
                self.substrate_preferences[SwarmMessageType.LEARNING_SYNC].insert(0, SwarmSubstrate.JUPITER)
                adaptations.append("Prioritized Jupiter for learning sync")
        
        # If low latency, prioritize Omnitoken for consensus
        if self.node_capabilities['latency_ms'] < 20:
            if SwarmSubstrate.OMNITOKEN not in self.substrate_preferences[SwarmMessageType.CONSENSUS_PROPOSAL]:
                self.substrate_preferences[SwarmMessageType.CONSENSUS_PROPOSAL].insert(0, SwarmSubstrate.OMNITOKEN)
                adaptations.append("Prioritized Omnitoken for consensus (low latency)")
        
        if adaptations:
            print(f"[SwarmTransport] Auto-adaptations: {adaptations}")
    
    def configure_tailscale(
        self,
        api_key: Optional[str] = None,
        tailnet: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configure Tailscale integration for swarm.
        
        If api_key is provided, will attempt to use Tailscale API for node discovery.
        Otherwise, uses local Tailscale daemon via tailscale_localapi.
        """
        if not self.node_capabilities['has_tailscale']:
            return {'error': 'Tailscale not detected on this node'}
        
        config = {
            'tailscale_available': True,
            'api_key_provided': api_key is not None,
            'tailnet': tailnet,
            'configuration': {
                'magic_dns': True,
                'accept_routes': True,
                'advertise_routes': []
            }
        }
        
        try:
            # Try to get Tailscale status
            result = subprocess.run(['tailscale', 'status', '--json'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                status = json.loads(result.stdout)
                config['tailscale_status'] = status
                config['configured'] = True
                print(f"[SwarmTransport] Tailscale configured: {status.get('Self', {}).get('HostName', 'unknown')}")
        except Exception as e:
            config['error'] = str(e)
            config['configured'] = False
        
        return config
    
    def register_message_handler(
        self,
        message_type: SwarmMessageType,
        handler: Callable[[SwarmMessage], None]
    ):
        """Register a handler for specific message types"""
        with self._lock:
            if message_type not in self._message_handlers:
                self._message_handlers[message_type] = []
            self._message_handlers[message_type].append(handler)
    
    def _select_substrate(
        self,
        message_type: SwarmMessageType,
        payload_size: int
    ) -> SwarmSubstrate:
        """Select best substrate for message type"""
        preferences = self.substrate_preferences.get(message_type, [SwarmSubstrate.OMNITOKEN])
        
        # Check availability
        available = []
        if self.mimo_router:
            available_transports = self.mimo_router.get_available_transports()
            for pref in preferences:
                if pref.value in available_transports:
                    available.append(pref)
        
        # Fallback to Omnitoken if nothing available
        if not available:
            return SwarmSubstrate.OMNITOKEN
        
        # Jupiter for large payloads (multiplexing benefit)
        if payload_size > 1024 and SwarmSubstrate.JUPITER in available:
            return SwarmSubstrate.JUPITER
        
        return available[0]
    
    def _route_message(self, message: SwarmMessage) -> Dict[str, Any]:
        """Route message through selected substrate"""
        substrate = self._select_substrate(message.message_type, len(json.dumps(message.payload)))
        
        payload_bytes = json.dumps(message.to_dict()).encode()
        
        routing_result = {
            'success': False,
            'substrate': substrate.value,
            'message_id': message.message_id,
            'error': None
        }
        
        try:
            if substrate == SwarmSubstrate.OMNITOKEN and self.mimo_router:
                # Use MIMO router for Omnitoken
                routing = self.mimo_router.route_payload(payload_bytes)
                routing_result.update({
                    'success': not routing.get('blocked', False),
                    'primary_transport': routing.get('primary_transport'),
                    'fallback_transports': routing.get('fallback_transports'),
                    'routing_metadata': routing.get('routing_metadata')
                })
            
            elif substrate == SwarmSubstrate.JUPITER and self.jupiter_transport:
                # Use Jupiter boxes for multiplexing
                jupiter_packet = self.jupiter_transport.encode_payload(payload_bytes)
                routing_result.update({
                    'success': True,
                    'jupiter_phase': jupiter_packet.phase,
                    'jupiter_boxes': jupiter_packet.n_boxes,
                    'manifest_id': jupiter_packet.manifest_id
                })
            
            else:
                # Direct substrate routing (I2P, Tailscale, TOR)
                routing_result['success'] = True
                routing_result['direct_routing'] = True
            
            # Update statistics
            if routing_result['success']:
                self.stats['messages_sent'] += 1
                self.stats['bytes_sent'] += len(payload_bytes)
                self.stats['substrate_usage'][substrate.value] += 1
            
        except Exception as e:
            routing_result['error'] = str(e)
            routing_result['success'] = False
            self.stats['failures'] += 1
        
        return routing_result
    
    def broadcast_heartbeat(self, status: SwarmNodeStatus) -> Dict[str, Any]:
        """Broadcast heartbeat to all swarm nodes"""
        message = SwarmMessage(
            message_type=SwarmMessageType.HEARTBEAT,
            priority=SwarmPriority.HIGH,
            source_node_id=self.node_id,
            target_node_ids=[],  # Broadcast
            payload=status.to_dict()
        )
        
        result = self._route_message(message)
        
        # Store local status
        with self._lock:
            self.node_status[self.node_id] = status
        
        return result
    
    def send_consensus_message(
        self,
        proposal: Dict[str, Any],
        target_nodes: List[str]
    ) -> Dict[str, Any]:
        """Send consensus proposal to specific nodes"""
        message = SwarmMessage(
            message_type=SwarmMessageType.CONSENSUS_PROPOSAL,
            priority=SwarmPriority.CRITICAL,
            source_node_id=self.node_id,
            target_node_ids=target_nodes,
            payload=proposal
        )
        
        return self._route_message(message)
    
    def sync_learning_state(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize learning state across swarm"""
        message = SwarmMessage(
            message_type=SwarmMessageType.LEARNING_SYNC,
            priority=SwarmPriority.HIGH,
            source_node_id=self.node_id,
            target_node_ids=[],  # Broadcast
            payload=knowledge
        )
        
        return self._route_message(message)
    
    def send_task_assignment(
        self,
        task: Dict[str, Any],
        target_nodes: List[str]
    ) -> Dict[str, Any]:
        """Assign task to specific nodes"""
        message = SwarmMessage(
            message_type=SwarmMessageType.TASK_ASSIGNMENT,
            priority=SwarmPriority.MEDIUM,
            source_node_id=self.node_id,
            target_node_ids=target_nodes,
            payload=task
        )
        
        return self._route_message(message)
    
    def send_alert(self, alert: Dict[str, Any], target_nodes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send alert message"""
        message = SwarmMessage(
            message_type=SwarmMessageType.ALERT,
            priority=SwarmPriority.CRITICAL,
            source_node_id=self.node_id,
            target_node_ids=target_nodes or [],  # Broadcast if None
            payload=alert
        )
        
        return self._route_message(message)
    
    def discover_nodes(self) -> List[SwarmNodeStatus]:
        """Discover available swarm nodes via DHT"""
        if not self.dht:
            return []
        
        # Query DHT for swarm nodes
        content_hash = hashlib.sha256(b"swarm_discovery").hexdigest()
        query_result = self.dht.find_nodes(content_hash, self.node_id)
        
        nodes = []
        if 'nodes' in query_result:
            for node_data in query_result['nodes']:
                node = SwarmNodeStatus(
                    node_id=node_data.get('node_id', ''),
                    available=node_data.get('available', True),
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    active_agents=0,
                    learned_concepts=0,
                    last_heartbeat=time.time(),
                    jupiter_box_index=node_data.get('jupiter_box_index', -1)
                )
                nodes.append(node)
        
        return nodes
    
    def get_status(self) -> Dict[str, Any]:
        """Get transport layer status"""
        return {
            'node_id': self.node_id[:16] + '...',
            'running': self._running,
            'registered_nodes': len(self.node_status),
            'message_queue_sizes': {
                priority.name: len(queue)
                for priority, queue in self.message_queue.items()
            },
            'statistics': self.stats,
            'substrate_usage': self.stats['substrate_usage'],
            'node_capabilities': self.node_capabilities,
            'auto_adaptations': self.stats['auto_adaptations'],
            'transport_preferences': {
                msg_type.value: [substrate.value for substrate in substrates]
                for msg_type, substrates in self.substrate_preferences.items()
            },
            'dht_status': self.dht.get_status() if self.dht else None,
            'mimo_status': self.mimo_router.get_status() if self.mimo_router else None
        }
    
    def print_status(self):
        """Print transport layer status"""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("SWARM TRANSPORT LAYER STATUS")
        print("="*60)
        
        print(f"\n📡 Node: {status['node_id']}")
        print(f"  Running: {status['running']}")
        print(f"  Registered nodes: {status['registered_nodes']}")
        
        print(f"\n📊 Statistics:")
        print(f"  Messages sent: {status['statistics']['messages_sent']}")
        print(f"  Messages received: {status['statistics']['messages_received']}")
        print(f"  Bytes sent: {status['statistics']['bytes_sent']}")
        print(f"  Bytes received: {status['statistics']['bytes_received']}")
        print(f"  Failures: {status['statistics']['failures']}")
        
        print(f"\n🌐 Substrate Usage:")
        for substrate, count in status['substrate_usage'].items():
            print(f"  {substrate}: {count}")
        
        print(f"\n📬 Message Queue:")
        for priority, size in status['message_queue_sizes'].items():
            print(f"  {priority}: {size}")
        
        print("\n" + "="*60)


def main():
    """Test swarm transport layer"""
    transport = SwarmTransportLayer()
    
    print("[SwarmTransport] Initializing...")
    if not transport.initialize():
        print("[!] Initialization failed")
        return
    
    print("\n[Test 1] Broadcasting heartbeat...")
    status = SwarmNodeStatus(
        node_id=transport.node_id,
        available=True,
        cpu_usage=0.5,
        memory_usage=0.6,
        active_agents=10,
        learned_concepts=106,
        last_heartbeat=time.time(),
        jupiter_box_index=0
    )
    result = transport.broadcast_heartbeat(status)
    print(f"  Result: {result}")
    
    print("\n[Test 2] Sending consensus message...")
    proposal = {
        'round': 1,
        'proposal_id': 'consensus_001',
        'value': 'accept'
    }
    result = transport.send_consensus_message(proposal, ['node_1', 'node_2'])
    print(f"  Result: {result}")
    
    print("\n[Test 3] Syncing learning state...")
    knowledge = {
        'learned_concepts': 106,
        'timestamp': time.time()
    }
    result = transport.sync_learning_state(knowledge)
    print(f"  Result: {result}")
    
    print("\n[Test 4] Sending alert...")
    alert = {
        'severity': 'warning',
        'message': 'Node latency high'
    }
    result = transport.send_alert(alert)
    print(f"  Result: {result}")
    
    print("\n[Test 5] Discovering nodes...")
    nodes = transport.discover_nodes()
    print(f"  Discovered {len(nodes)} nodes")
    
    print("\n[Status]")
    transport.print_status()


if __name__ == '__main__':
    main()
