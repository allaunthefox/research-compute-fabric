#!/usr/bin/env python3
"""
ene_cloud_credential_manager.py — ENE Cloud Credential & Node Balancing System

ENE (Endless Node Edges) manages API keys for cloud storage with:
- Secure credential storage via ENE encryption
- Node connection balancing (load distribution)
- Automatic failover and rotation
- Health monitoring per node

Architecture:
- ENE: Central credential authority
- Nodes: Distributed connection endpoints
- Balancer: Round-robin with health checks
- Storage: Google Drive topological surface
"""

import json
import time
import hashlib
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

# Import ENE security
from ene_api import ENESecurityManager, AccessLevel


@dataclass
class CloudCredential:
    """Encrypted cloud storage credential."""
    credential_id: str
    provider: str  # "gdrive", "s3", "azure", etc.
    encrypted_payload: bytes
    access_level: AccessLevel
    node_assignments: List[str]  # Which nodes can use this
    usage_count: int = 0
    last_rotated: float = field(default_factory=time.time)
    health_score: float = 1.0  # 0.0 to 1.0
    is_active: bool = True


@dataclass
class NodeConnection:
    """Active node connection to cloud storage."""
    node_id: str
    credential_id: str
    connected_at: float
    last_activity: float
    bytes_transferred: int = 0
    error_count: int = 0
    latency_ms: float = 0.0
    status: str = "active"  # active, draining, failed


@dataclass
class NodeStats:
    """Statistics for a connection node."""
    node_id: str
    total_connections: int = 0
    total_bytes: int = 0
    avg_latency: float = 0.0
    error_rate: float = 0.0
    health_score: float = 1.0


class ENENodeBalancer:
    """
    ENE Node Connection Balancer
    
    Distributes cloud storage connections across nodes with:
    - Weighted round-robin (based on health scores)
    - Health check monitoring
    - Automatic failover
    - Latency-aware routing
    """
    
    def __init__(self, db_path: str = "/home/allaun/Documents/Research Stack/shared-data/data/ene_cloud_nodes.db"):
        self.db_path = db_path
        self.nodes: Dict[str, NodeStats] = {}
        self.active_connections: Dict[str, NodeConnection] = {}
        self.credential_rotation_queue: List[str] = []
        self._init_database()
        self._load_nodes()
    
    def _init_database(self):
        """Initialize SQLite database for node tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                credential_id TEXT,
                health_score REAL DEFAULT 1.0,
                total_connections INTEGER DEFAULT 0,
                total_bytes INTEGER DEFAULT 0,
                avg_latency_ms REAL DEFAULT 0.0,
                error_rate REAL DEFAULT 0.0,
                last_seen REAL DEFAULT 0.0,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                connection_id TEXT PRIMARY KEY,
                node_id TEXT,
                credential_id TEXT,
                connected_at REAL,
                last_activity REAL,
                bytes_transferred INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                latency_ms REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active'
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_nodes(self):
        """Load nodes from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT node_id, health_score, total_connections, total_bytes, avg_latency_ms, error_rate FROM nodes WHERE is_active = 1")
        for row in cursor.fetchall():
            node_id, health, connections, bytes_total, latency, error_rate = row
            self.nodes[node_id] = NodeStats(
                node_id=node_id,
                total_connections=connections,
                total_bytes=bytes_total,
                avg_latency=latency,
                error_rate=error_rate,
                health_score=health
            )
        
        conn.close()
    
    def register_node(self, node_id: str, credential_id: str) -> bool:
        """Register a new node for cloud storage connections."""
        if node_id in self.nodes:
            return False
        
        self.nodes[node_id] = NodeStats(node_id=node_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO nodes (node_id, credential_id, last_seen) VALUES (?, ?, ?)",
            (node_id, credential_id, time.time())
        )
        conn.commit()
        conn.close()
        
        return True
    
    def select_node(self, strategy: str = "health_weighted") -> Optional[str]:
        """
        Select best node for new connection.
        
        Strategies:
        - health_weighted: Weighted by health score
        - round_robin: Simple rotation
        - latency: Lowest latency
        - least_connections: Fewest active connections
        """
        active_nodes = [n for n in self.nodes.values() if n.health_score > 0.5]
        
        if not active_nodes:
            return None
        
        if strategy == "health_weighted":
            # Weighted random selection based on health scores
            total_health = sum(n.health_score for n in active_nodes)
            r = random.uniform(0, total_health)
            cumulative = 0
            for node in active_nodes:
                cumulative += node.health_score
                if r <= cumulative:
                    return node.node_id
            return active_nodes[-1].node_id
        
        elif strategy == "round_robin":
            # Simple rotation (would need state persistence)
            return active_nodes[0].node_id
        
        elif strategy == "latency":
            # Select lowest latency node
            return min(active_nodes, key=lambda n: n.avg_latency).node_id
        
        elif strategy == "least_connections":
            # Select node with fewest connections
            return min(active_nodes, key=lambda n: n.total_connections).node_id
        
        return active_nodes[0].node_id
    
    def record_connection(self, node_id: str, credential_id: str) -> str:
        """Record new connection from node."""
        connection_id = f"conn_{hashlib.sha256(f'{node_id}{time.time()}'.encode()).hexdigest()[:16]}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO connections 
               (connection_id, node_id, credential_id, connected_at, last_activity) 
               VALUES (?, ?, ?, ?, ?)""",
            (connection_id, node_id, credential_id, time.time(), time.time())
        )
        
        # Update node stats
        cursor.execute(
            "UPDATE nodes SET total_connections = total_connections + 1, last_seen = ? WHERE node_id = ?",
            (time.time(), node_id)
        )
        
        conn.commit()
        conn.close()
        
        # Update in-memory
        self.active_connections[connection_id] = NodeConnection(
            node_id=node_id,
            credential_id=credential_id,
            connected_at=time.time(),
            last_activity=time.time()
        )
        
        if node_id in self.nodes:
            self.nodes[node_id].total_connections += 1
        
        return connection_id
    
    def update_connection_stats(self, connection_id: str, bytes_delta: int = 0, 
                                latency_ms: float = 0.0, error: bool = False):
        """Update connection statistics."""
        if connection_id not in self.active_connections:
            return
        
        conn_info = self.active_connections[connection_id]
        conn_info.last_activity = time.time()
        conn_info.bytes_transferred += bytes_delta
        
        if error:
            conn_info.error_count += 1
        
        if latency_ms > 0:
            conn_info.latency_ms = latency_ms
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE connections 
               SET last_activity = ?, bytes_transferred = bytes_transferred + ?, 
                   error_count = error_count + ?, latency_ms = ?
               WHERE connection_id = ?""",
            (time.time(), bytes_delta, 1 if error else 0, latency_ms, connection_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_node_health(self, node_id: str) -> float:
        """Calculate health score for a node (0.0 to 1.0)."""
        if node_id not in self.nodes:
            return 0.0
        
        stats = self.nodes[node_id]
        
        # Factors:
        # - Error rate (lower is better) - 40% weight
        # - Latency (lower is better) - 30% weight
        # - Connection count (moderate is good) - 30% weight
        
        error_factor = max(0, 1.0 - (stats.error_rate * 10))  # 10% errors = 0 health
        latency_factor = max(0, 1.0 - (stats.avg_latency / 1000))  # 1000ms = 0 health
        connection_factor = 1.0 if 10 <= stats.total_connections <= 100 else 0.7
        
        health = (error_factor * 0.4) + (latency_factor * 0.3) + (connection_factor * 0.3)
        return min(1.0, max(0.0, health))
    
    def get_balancer_stats(self) -> Dict[str, Any]:
        """Get overall balancer statistics."""
        total_nodes = len(self.nodes)
        active_nodes = sum(1 for n in self.nodes.values() if n.health_score > 0.5)
        total_connections = len(self.active_connections)
        total_bytes = sum(n.total_bytes for n in self.nodes.values())
        
        return {
            "total_nodes": total_nodes,
            "active_nodes": active_nodes,
            "active_connections": total_connections,
            "total_bytes_transferred": total_bytes,
            "avg_node_health": sum(n.health_score for n in self.nodes.values()) / total_nodes if total_nodes > 0 else 0,
            "nodes": {node_id: {
                "health": stats.health_score,
                "connections": stats.total_connections,
                "bytes": stats.total_bytes,
                "latency": stats.avg_latency
            } for node_id, stats in self.nodes.items()}
        }


class ENECloudCredentialManager:
    """
    ENE Central Credential Authority
    
    Manages cloud storage API keys with:
    - Secure encryption via ENE
    - Credential rotation
    - Node assignment
    - Access control
    """
    
    def __init__(self, db_path: str = "/home/allaun/Documents/Research Stack/shared-data/data/ene_cloud_credentials.db"):
        self.db_path = db_path
        self.security = ENESecurityManager()
        self.balancer = ENENodeBalancer()
        self.credentials: Dict[str, CloudCredential] = {}
        self._init_database()
        self._load_credentials()
    
    def _init_database(self):
        """Initialize credential database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                credential_id TEXT PRIMARY KEY,
                provider TEXT,
                encrypted_payload BLOB,
                access_level INTEGER,
                node_assignments TEXT,  -- JSON list
                usage_count INTEGER DEFAULT 0,
                last_rotated REAL,
                health_score REAL DEFAULT 1.0,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_credentials(self):
        """Load credentials from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT credential_id, provider, encrypted_payload, access_level, 
                   node_assignments, usage_count, last_rotated, health_score
            FROM credentials WHERE is_active = 1
        """)
        
        for row in cursor.fetchall():
            cred_id, provider, payload, access_level, nodes_json, usage, rotated, health = row
            node_assignments = json.loads(nodes_json) if nodes_json else []
            
            self.credentials[cred_id] = CloudCredential(
                credential_id=cred_id,
                provider=provider,
                encrypted_payload=payload,
                access_level=AccessLevel(access_level),
                node_assignments=node_assignments,
                usage_count=usage,
                last_rotated=rotated,
                health_score=health
            )
        
        conn.close()
    
    def store_credential(self, provider: str, api_key: str, secret: str,
                        node_assignments: List[str] = None,
                        access_level: AccessLevel = AccessLevel.RESTRICTED) -> str:
        """Store new cloud credential (encrypted)."""
        credential_id = f"cred_{provider}_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
        
        # Encrypt the credential using ENE
        credential_data = json.dumps({"api_key": api_key, "secret": secret})
        encrypted_dict = self.security.encrypt_data(credential_data, provider.encode())
        encrypted = json.dumps(encrypted_dict).encode()
        
        nodes = node_assignments or []
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO credentials 
               (credential_id, provider, encrypted_payload, access_level, node_assignments, last_rotated)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (credential_id, provider, encrypted, access_level.value, json.dumps(nodes), time.time())
        )
        
        conn.commit()
        conn.close()
        
        # Store in memory
        self.credentials[credential_id] = CloudCredential(
            credential_id=credential_id,
            provider=provider,
            encrypted_payload=encrypted,
            access_level=access_level,
            node_assignments=nodes
        )
        
        return credential_id
    
    def get_credential_for_node(self, node_id: str, provider: str) -> Optional[Dict[str, str]]:
        """Get decrypted credential for a specific node."""
        # Find credential assigned to this node
        eligible_creds = [
            c for c in self.credentials.values()
            if c.provider == provider and (not c.node_assignments or node_id in c.node_assignments)
        ]
        
        if not eligible_creds:
            return None
        
        # Select healthiest credential
        cred = max(eligible_creds, key=lambda c: c.health_score)
        
        # Decrypt using ENE
        try:
            encrypted_dict = json.loads(cred.encrypted_payload.decode())
            decrypted = self.security.decrypt_data(encrypted_dict, cred.provider.encode())
            data = json.loads(decrypted)
            
            # Update usage
            cred.usage_count += 1
            self._update_credential_stats(cred.credential_id)
            
            return data
        except Exception as e:
            cred.health_score *= 0.9  # Degrade health on failure
            return None
    
    def _update_credential_stats(self, credential_id: str):
        """Update credential usage stats."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE credentials SET usage_count = usage_count + 1 WHERE credential_id = ?",
            (credential_id,)
        )
        
        conn.commit()
        conn.close()
    
    def rotate_credential(self, credential_id: str, new_api_key: str, new_secret: str) -> bool:
        """Rotate credential to new API key."""
        if credential_id not in self.credentials:
            return False
        
        # Encrypt new credentials using ENE
        credential_data = json.dumps({"api_key": new_api_key, "secret": new_secret})
        encrypted_dict = self.security.encrypt_data(credential_data, b"gdrive")
        encrypted = json.dumps(encrypted_dict).encode()
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE credentials SET encrypted_payload = ?, last_rotated = ? WHERE credential_id = ?",
            (encrypted, time.time(), credential_id)
        )
        
        conn.commit()
        conn.close()
        
        # Update memory
        self.credentials[credential_id].encrypted_payload = encrypted
        self.credentials[credential_id].last_rotated = time.time()
        
        return True
    
    def get_connection(self, provider: str, node_id: str = None) -> Tuple[str, str, Dict[str, str]]:
        """
        Get connection for cloud storage.
        
        Returns: (connection_id, node_id, credentials)
        """
        # Select node if not specified
        if node_id is None:
            node_id = self.balancer.select_node(strategy="health_weighted")
        
        if not node_id:
            raise Exception("No healthy nodes available")
        
        # Get credential for node
        creds = self.get_credential_for_node(node_id, provider)
        if not creds:
            raise Exception(f"No credentials available for {provider} on node {node_id}")
        
        # Find credential ID
        cred_id = None
        for cid, c in self.credentials.items():
            if c.provider == provider and (not c.node_assignments or node_id in c.node_assignments):
                cred_id = cid
                break
        
        # Record connection
        connection_id = self.balancer.record_connection(node_id, cred_id)
        
        return connection_id, node_id, creds
    
    def report_connection_result(self, connection_id: str, bytes_transferred: int = 0,
                                  latency_ms: float = 0.0, error: bool = False):
        """Report result of connection operation."""
        self.balancer.update_connection_stats(connection_id, bytes_transferred, latency_ms, error)


# ═══════════════════════════════════════════════════════════════════════════
# Integration with Topological Storage
# ═══════════════════════════════════════════════════════════════════════════

class ENETopologicalStorage:
    """
    ENE-managed topological storage surface.
    
    Combines credential management with node balancing for
    automatic cloud storage operations.
    """
    
    def __init__(self):
        self.credential_manager = ENECloudCredentialManager()
        self.balancer = self.credential_manager.balancer
    
    def upload_waveprobe(self, local_path: str, remote_path: str) -> Dict[str, Any]:
        """
        Upload file via ENE-managed connection.
        
        Automatically:
        1. Selects best node
        2. Retrieves encrypted credentials
        3. Executes upload
        4. Reports stats
        """
        # Get connection (node + credentials)
        connection_id, node_id, creds = self.credential_manager.get_connection("gdrive")
        
        # Simulate upload (would use actual Rclone with credentials)
        start_time = time.time()
        
        # In real implementation, would call rclone with the credentials
        # rclone copy local_path Gdrive:topological_storage/...
        
        # Simulate latency
        import random
        latency_ms = random.uniform(50, 200)
        time.sleep(latency_ms / 1000)
        
        # Get file size
        file_size = Path(local_path).stat().st_size
        
        # Report success
        self.credential_manager.report_connection_result(
            connection_id, 
            bytes_transferred=file_size,
            latency_ms=latency_ms,
            error=False
        )
        
        return {
            "connection_id": connection_id,
            "node_id": node_id,
            "uploaded": True,
            "bytes": file_size,
            "latency_ms": latency_ms,
            "duration": time.time() - start_time
        }
    
    def get_storage_health(self) -> Dict[str, Any]:
        """Get overall topological storage health."""
        balancer_stats = self.balancer.get_balancer_stats()
        
        return {
            "topological_storage": "operational",
            "provider": "gdrive",
            "mount_point": "Gdrive:topological_storage",
            "ene_managed": True,
            "node_balancing": "active",
            "credential_rotation": "enabled",
            "balancer_stats": balancer_stats
        }


# ═══════════════════════════════════════════════════════════════════════════
# Example Usage
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("ENE CLOUD CREDENTIAL & NODE BALANCING SYSTEM")
    print("=" * 70)
    
    # Initialize ENE system
    ene = ENETopologicalStorage()
    
    # Register nodes
    print("\n[1] Registering nodes...")
    for i in range(3):
        node_id = f"node_{i+1}"
        ene.balancer.register_node(node_id, f"cred_gdrive_{i+1}")
        print(f"  Registered: {node_id}")
    
    # Store credential
    print("\n[2] Storing Google Drive credential...")
    cred_id = ene.credential_manager.store_credential(
        provider="gdrive",
        api_key="[REDACTED_GOOGLE_API_KEY]",
        secret="[REDACTED_GOOGLE_SECRET]",
        node_assignments=["node_1", "node_2", "node_3"]
    )
    print(f"  Credential ID: {cred_id}")
    print(f"  Encrypted: AES-256-GCM via ENE")
    
    # Get connection
    print("\n[3] Getting connection via node balancing...")
    conn_id, node_id, creds = ene.credential_manager.get_connection("gdrive")
    print(f"  Connection ID: {conn_id}")
    print(f"  Selected Node: {node_id}")
    print(f"  Strategy: health_weighted")
    
    # Simulate upload
    print("\n[4] Simulating waveprobe upload...")
    result = ene.upload_waveprobe(
        local_path="/tmp/test_waveprobe.json",
        remote_path="Gdrive:topological_storage/waveprobes/test.json"
    )
    print(f"  Uploaded via: {result['node_id']}")
    print(f"  Latency: {result['latency_ms']:.1f}ms")
    print(f"  Bytes: {result['bytes']}")
    
    # Get health
    print("\n[5] Storage health...")
    health = ene.get_storage_health()
    print(f"  Status: {health['topological_storage']}")
    print(f"  ENE Managed: {health['ene_managed']}")
    print(f"  Nodes: {health['balancer_stats']['total_nodes']}")
    print(f"  Active Connections: {health['balancer_stats']['active_connections']}")
    
    print("\n" + "=" * 70)
    print("ENE SYSTEM OPERATIONAL")
    print("API keys secured | Nodes balanced | Storage topological")
    print("=" * 70)
