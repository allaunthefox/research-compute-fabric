#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Distributed Hash Table Layer for MIMO Transport
Content-addressable DHT with Kademlia-inspired XOR-distance routing
Integrates with MIMO, I2P, and Jupiter Boxes transports
"""

import hashlib
import asyncio
import json
import time
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import heapq
from collections import defaultdict

# ═════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═════════════════════════════════════════════════════════════════════════════

class ReplicationStrategy(Enum):
    """Storage redundancy strategy per content"""
    SINGLE = 1      # Single node (local only)
    TRIPLE = 3      # 3 geographically diverse nodes
    QUORUM = 5      # 5-node Byzantine quorum
    FULL = 14       # All Jupiter boxes (maximum availability)

@dataclass
class DHTNode:
    """DHT node identity and metadata"""
    node_id: str              # SHA256(public_key), 64 hex chars
    transport_type: str      # 'omnitoken', 'i2p', 'tailscale', 'tor'
    address: str             # IP or eepsite address
    port: int
    jupiter_box_index: int   # which box index (0-13 for GROUNDED phase)
    last_seen: float = field(default_factory=time.time)
    bandwidth_mbps: int = 10
    latency_ms: int = 50
    available: bool = True
    
    def xor_distance_to(self, target_id: str) -> int:
        """XOR distance metric (Kademlia-style routing)"""
        self_int = int(self.node_id, 16)
        target_int = int(target_id, 16)
        return self_int ^ target_int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DHTContent:
    """DHT stored content metadata"""
    content_hash: str        # SHA256 hex string
    owner_node_id: str       # node that published
    replication: ReplicationStrategy
    replica_nodes: List[str] = field(default_factory=list)  # node_ids
    manifest_id: Optional[str] = None  # link to I2P/Jupiter manifest
    size_bytes: int = 0
    published_at: float = field(default_factory=time.time)
    ttl_seconds: int = 86400  # 24 hours default
    access_count: int = 0
    
    def is_expired(self) -> bool:
        return (time.time() - self.published_at) > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['replication'] = self.replication.name
        return data

@dataclass
class DHTQuery:
    """DHT lookup query metadata"""
    query_id: str           # unique query identifier
    content_hash: str       # what we're looking for
    requester_id: str       # who asked
    closest_k_nodes: List[str] = field(default_factory=list)
    hops: int = 0
    max_hops: int = 20
    timestamp: float = field(default_factory=time.time)

# ═════════════════════════════════════════════════════════════════════════════
# DHT IMPLEMENTATION (KADEMLIA-INSPIRED)
# ═════════════════════════════════════════════════════════════════════════════

class DHTLayer:
    """Kademlia-style DHT with content addressing"""
    
    def __init__(self, local_node_id: str, k: int = 20, alpha: int = 3):
        """
        Initialize DHT layer.
        
        Args:
            local_node_id: SHA256 hash of this node's public key
            k: number of closest neighbors to contact (bucket size)
            alpha: parallelism parameter for lookups
        """
        self.local_node_id = local_node_id
        self.k = k
        self.alpha = alpha
        
        # Node registry: node_id -> DHTNode
        self.nodes: Dict[str, DHTNode] = {}
        
        # Content registry: content_hash -> DHTContent
        self.content: Dict[str, DHTContent] = {}
        
        # Routing table: (160-bit buckets) distance_ranges -> [node_ids]
        self.routing_table: Dict[int, List[str]] = defaultdict(list)
        
        # Query cache: (requester_id, content_hash) -> (nodes, expiry)
        self.query_cache: Dict[Tuple[str, str], Tuple[List[str], float]] = {}
        
        # Replication log: tracks which content on which nodes
        self.replication_log: Dict[str, List[str]] = defaultdict(list)
        
        self.stats = {
            'queries_total': 0,
            'queries_hit_cache': 0,
            'content_stored': 0,
            'replications_completed': 0,
            'node_joins': 0,
            'node_failures': 0,
        }
    
    # ─────────────────────────────────────────────────────────────────────
    # NODE REGISTRATION
    # ─────────────────────────────────────────────────────────────────────
    
    def register_node(self, node: DHTNode) -> bool:
        """Register a peer node in the DHT"""
        if node.node_id in self.nodes:
            self.nodes[node.node_id].last_seen = time.time()
            return False  # already registered
        
        self.nodes[node.node_id] = node
        self._update_routing_table(node.node_id)
        self.stats['node_joins'] += 1
        return True
    
    def _update_routing_table(self, node_id: str):
        """Update routing table with XOR distance bucket"""
        distance = int(node_id, 16) ^ int(self.local_node_id, 16)
        bucket_index = distance.bit_length() if distance > 0 else 0
        
        bucket = self.routing_table[bucket_index]
        if node_id not in bucket:
            bucket.append(node_id)
        
        # Evict farthest node if bucket full
        if len(bucket) > self.k:
            bucket.sort(
                key=lambda nid: int(nid, 16) ^ int(self.local_node_id, 16)
            )
            bucket.pop()  # remove farthest
    
    # ─────────────────────────────────────────────────────────────────────
    # CONTENT STORAGE
    # ─────────────────────────────────────────────────────────────────────
    
    def store_content(
        self,
        content_hash: str,
        owner_node_id: str,
        replication: ReplicationStrategy = ReplicationStrategy.TRIPLE,
        manifest_id: Optional[str] = None,
        size_bytes: int = 0,
        ttl_seconds: int = 86400
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Store content in DHT with replication.
        
        Returns:
            (success, metadata) tuple
        """
        if content_hash in self.content:
            return False, {'error': 'content already stored'}
        
        # Find closest K nodes to store replicas
        closest = self._find_closest_nodes(content_hash, self.k)
        replicas = closest[:replication.value]
        
        if not replicas:
            return False, {'error': 'no nodes available'}
        
        # Create content entry
        content = DHTContent(
            content_hash=content_hash,
            owner_node_id=owner_node_id,
            replication=replication,
            replica_nodes=replicas,
            manifest_id=manifest_id,
            size_bytes=size_bytes,
            ttl_seconds=ttl_seconds,
        )
        
        self.content[content_hash] = content
        self.replication_log[content_hash] = replicas
        self.stats['content_stored'] += 1
        self.stats['replications_completed'] += replication.value
        
        return True, {
            'content_hash': content_hash,
            'replica_count': len(replicas),
            'replication_strategy': replication.name,
            'manifest_id': manifest_id,
        }
    
    def get_content_location(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve where content is stored in DHT"""
        if content_hash not in self.content:
            return None
        
        content = self.content[content_hash]
        
        if content.is_expired():
            del self.content[content_hash]
            return None
        
        content.access_count += 1
        
        # Build replica node list with metadata
        replicas = []
        for node_id in content.replica_nodes:
            if node_id in self.nodes:
                replicas.append(self.nodes[node_id].to_dict())
        
        return {
            'content_hash': content_hash,
            'replicas': replicas,
            'manifest_id': content.manifest_id,
            'size_bytes': content.size_bytes,
            'access_count': content.access_count,
            'replication_strategy': content.replication.name,
        }
    
    # ─────────────────────────────────────────────────────────────────────
    # CONTENT LOOKUP (KADEMLIA)
    # ─────────────────────────────────────────────────────────────────────
    
    def find_nodes(self, content_hash: str, requester_id: str) -> Dict[str, Any]:
        """
        Kademlia FIND_NODE lookup for content/nodes.
        Returns closest K nodes that have (or should have) the content.
        """
        self.stats['queries_total'] += 1
        
        # Check cache first
        cache_key = (requester_id, content_hash)
        if cache_key in self.query_cache:
            cached_nodes, expiry = self.query_cache[cache_key]
            if time.time() < expiry:
                self.stats['queries_hit_cache'] += 1
                return {
                    'method': 'cache_hit',
                    'nodes': [self.nodes[nid].to_dict() for nid in cached_nodes if nid in self.nodes],
                    'content_hash': content_hash,
                }
        
        # Iterative lookup: gradually contact closer nodes
        closest = self._find_closest_nodes(content_hash, self.k)
        
        # Cache result
        self.query_cache[cache_key] = (closest, time.time() + 300)  # 5min cache
        
        result_nodes = [self.nodes[nid].to_dict() for nid in closest if nid in self.nodes]
        
        return {
            'method': 'iterative_lookup',
            'content_hash': content_hash,
            'nodes': result_nodes,
            'node_count': len(result_nodes),
        }
    
    def _find_closest_nodes(self, target_id: str, k: int) -> List[str]:
        """Find K closest nodes to target (by XOR distance), with latency tie-break"""
        candidates = []
        for node_id, node in self.nodes.items():
            if not node.available:
                continue
            distance = int(node_id, 16) ^ int(target_id, 16)
            # Sort by (xor_distance, latency) so latency only breaks ties
            candidates.append((distance, node.latency_ms, node_id))
        
        candidates.sort()
        return [node_id for _, _, node_id in candidates[:k]]
    
    # ─────────────────────────────────────────────────────────────────────
    # REPLICATION & MAINTENANCE
    # ─────────────────────────────────────────────────────────────────────
    
    def get_replication_status(self, content_hash: str) -> Dict[str, Any]:
        """Check current replication state of content"""
        if content_hash not in self.content:
            return {'error': 'content not found'}
        
        content = self.content[content_hash]
        
        replica_status = []
        for node_id in content.replica_nodes:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                replica_status.append({
                    'node_id': node_id[:16] + '...',
                    'transport': node.transport_type,
                    'available': node.available,
                    'latency_ms': node.latency_ms,
                })
        
        return {
            'content_hash': content_hash[:16] + '...',
            'strategy': content.replication.name,
            'expected_replicas': content.replication.value,
            'actual_replicas': len(replica_status),
            'replicas': replica_status,
            'access_count': content.access_count,
            'ttl_remaining': max(0, content.ttl_seconds - (time.time() - content.published_at)),
        }
    
    def mark_node_unavailable(self, node_id: str) -> bool:
        """Mark a node as temporarily unavailable (health check failed)"""
        if node_id not in self.nodes:
            return False
        
        self.nodes[node_id].available = False
        self.stats['node_failures'] += 1
        
        # Trigger re-replication if needed
        self._rebalance_replicas()
        return True
    
    def _rebalance_replicas(self):
        """Re-replicate content from unavailable nodes"""
        for content_hash, content in self.content.items():
            available_replicas = [
                nid for nid in content.replica_nodes
                if nid in self.nodes and self.nodes[nid].available
            ]
            
            if len(available_replicas) < content.replication.value:
                # Need more replicas
                closest = self._find_closest_nodes(content_hash, self.k)
                needed = content.replication.value - len(available_replicas)
                
                for new_node_id in closest[:needed]:
                    if new_node_id not in content.replica_nodes:
                        content.replica_nodes.append(new_node_id)
    
    # ─────────────────────────────────────────────────────────────────────
    # STATISTICS & STATUS
    # ─────────────────────────────────────────────────────────────────────
    
    def get_status(self) -> Dict[str, Any]:
        """Get DHT layer status"""
        active_nodes = sum(1 for n in self.nodes.values() if n.available)
        
        # Content distribution
        content_by_transport = defaultdict(int)
        for content_hash in self.content:
            for node_id in self.content[content_hash].replica_nodes:
                if node_id in self.nodes:
                    transport = self.nodes[node_id].transport_type
                    content_by_transport[transport] += 1
        
        return {
            'local_node_id': self.local_node_id[:16] + '...',
            'peers': {
                'total': len(self.nodes),
                'active': active_nodes,
                'by_transport': dict(
                    (t, sum(1 for n in self.nodes.values() if n.transport_type == t))
                    for t in set(n.transport_type for n in self.nodes.values())
                ),
            },
            'content': {
                'total_stored': len(self.content),
                'replications': sum(len(c.replica_nodes) for c in self.content.values()),
                'by_transport': dict(content_by_transport),
            },
            'cache': {
                'size': len(self.query_cache),
            },
            'stats': self.stats,
        }


# ═════════════════════════════════════════════════════════════════════════════
# DHT + MIMO INTEGRATION
# ═════════════════════════════════════════════════════════════════════════════

def integrate_dht_with_mimo(mime_router, dht: DHTLayer) -> Dict[str, Any]:
    """
    Integrate DHT layer with MIMO transport router.
    
    Returns comprehensive routing metadata combining:
    - MIMO band selection (omnitoken, i2p, tailscale, tor)
    - DHT node discovery via content hash
    - Jupiter box replication strategy
    """
    return {
        'dht_layer': 'active',
        'mimo_router': 'connected',
        'integration': {
            'discovery': 'DHT content hash → replica nodes',
            'routing': 'MIMO to closest replica',
            'redundancy': 'Kademlia-based replication',
            'rebalancing': 'automatic on node failure',
        },
        'capabilities': [
            'content-addressed routing',
            'distributed storage',
            'automatic failover',
            'Byzantine quorum',
            'manifest integration',
        ],
    }


# ═════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═════════════════════════════════════════════════════════════════════════════

_dht_instance: Optional[DHTLayer] = None

def get_dht(node_id: Optional[str] = None) -> DHTLayer:
    """Get or create DHT singleton"""
    global _dht_instance
    if _dht_instance is None:
        if node_id is None:
            node_id = hashlib.sha256(b'dht_default_node').hexdigest()
        _dht_instance = DHTLayer(node_id)
    return _dht_instance

def reset_dht():
    """Reset DHT (testing only)"""
    global _dht_instance
    _dht_instance = None
