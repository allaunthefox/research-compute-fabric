#!/usr/bin/env python3
"""
MoE-ENE Cache Integration

Caches Mixture-of-Experts (MoE) configurations and outputs in the ENE database
for fast retrieval and persistent storage. Integrates with EtaMoE.lean and
SwarmMoERewiring.lean for expert management.

Cache Strategy:
- Expert configurations stored as sensitive data with RESTRICTED classification
- Performance metrics cached with semantic vectors for retrieval
- Gating weights tracked with version history
- Swarm-driven rewiring proposals stored with audit trail
"""

import json
import sqlite3
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infra.ene_api import ENEAPIHook, AccessLevel


@dataclass
class ExpertConfiguration:
    """MoE Expert Configuration"""
    expert_id: int
    gating_weight: float  # g
    quality_weight: float  # w
    coherence: float  # h
    penalty_weight: float  # v
    distortion: float  # p
    arity: float  # N
    cost_coefficient: float  # a
    overhead: float  # c
    semantic_vector: List[float]  # 14D semantic space
    domain: str
    version: str


@dataclass
class MoECacheEntry:
    """Cached MoE computation result"""
    cache_key: str
    expert_ids: List[int]
    eta_moe_result: float
    i_discarded: float
    timestamp: int
    semantic_vector: List[float]
    confidence: float


class MoEENECache:
    """MoE Cache Manager using ENE database"""
    
    def __init__(self, db_path: str = "/home/allaun/Documents/Research Stack/data/substrate_index.db"):
        self.db_path = db_path
        self.ene_api = ENEAPIHook()
        self._init_cache_tables()
    
    def _init_cache_tables(self):
        """Initialize cache-specific tables in ENE database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Expert configurations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS moe_expert_cache (
                expert_id INTEGER PRIMARY KEY,
                domain TEXT NOT NULL,
                config_json TEXT NOT NULL,
                semantic_vector TEXT NOT NULL,
                version TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                cache_hit_count INTEGER DEFAULT 0
            )
        """)
        
        # Computation results cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS moe_computation_cache (
                cache_key TEXT PRIMARY KEY,
                expert_ids TEXT NOT NULL,
                eta_moe_result REAL NOT NULL,
                i_discarded REAL NOT NULL,
                semantic_vector TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at INTEGER NOT NULL,
                hit_count INTEGER DEFAULT 0
            )
        """)
        
        # Rewiring proposals audit log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS moe_rewiring_audit (
                id TEXT PRIMARY KEY,
                expert_id INTEGER NOT NULL,
                proposal_json TEXT NOT NULL,
                swarm_consensus REAL NOT NULL,
                proposing_agent TEXT NOT NULL,
                approved BOOLEAN NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def cache_expert_config(self, config: ExpertConfiguration) -> bool:
        """Cache expert configuration in ENE database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            config_json = json.dumps(asdict(config))
            semantic_vector_json = json.dumps(config.semantic_vector)
            now = int(time.time())
            
            cursor.execute("""
                INSERT OR REPLACE INTO moe_expert_cache
                (expert_id, domain, config_json, semantic_vector, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                config.expert_id,
                config.domain,
                config_json,
                semantic_vector_json,
                config.version,
                now,
                now
            ))
            
            # Also store in ENE sensitive_data for security
            self.ene_api.store_sensitive_data(
                pkg=f"moe/expert/{config.expert_id}",
                payload=config_json,
                classification=AccessLevel.RESTRICTED,
                semantic_vector=config.semantic_vector
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error caching expert config: {e}")
            return False
    
    def retrieve_expert_config(self, expert_id: int) -> Optional[ExpertConfiguration]:
        """Retrieve expert configuration from cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT config_json, cache_hit_count
                FROM moe_expert_cache
                WHERE expert_id = ?
            """, (expert_id,))
            
            row = cursor.fetchone()
            
            if row:
                # Increment hit count
                cursor.execute("""
                    UPDATE moe_expert_cache
                    SET cache_hit_count = cache_hit_count + 1
                    WHERE expert_id = ?
                """, (expert_id,))
                conn.commit()
                conn.close()
                
                config_dict = json.loads(row[0])
                return ExpertConfiguration(**config_dict)
            
            conn.close()
            return None
        except Exception as e:
            print(f"Error retrieving expert config: {e}")
            return None
    
    def cache_computation_result(self, entry: MoECacheEntry) -> bool:
        """Cache MoE computation result"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expert_ids_json = json.dumps(entry.expert_ids)
            semantic_vector_json = json.dumps(entry.semantic_vector)
            
            cursor.execute("""
                INSERT OR REPLACE INTO moe_computation_cache
                (cache_key, expert_ids, eta_moe_result, i_discarded, semantic_vector, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.cache_key,
                expert_ids_json,
                entry.eta_moe_result,
                entry.i_discarded,
                semantic_vector_json,
                entry.confidence,
                entry.timestamp
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error caching computation result: {e}")
            return False
    
    def retrieve_computation_result(self, cache_key: str) -> Optional[MoECacheEntry]:
        """Retrieve cached computation result"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT expert_ids, eta_moe_result, i_discarded, semantic_vector, confidence, created_at
                FROM moe_computation_cache
                WHERE cache_key = ?
            """, (cache_key,))
            
            row = cursor.fetchone()
            
            if row:
                # Increment hit count
                cursor.execute("""
                    UPDATE moe_computation_cache
                    SET hit_count = hit_count + 1
                    WHERE cache_key = ?
                """, (cache_key,))
                conn.commit()
                conn.close()
                
                return MoECacheEntry(
                    cache_key=cache_key,
                    expert_ids=json.loads(row[0]),
                    eta_moe_result=row[1],
                    i_discarded=row[2],
                    semantic_vector=json.loads(row[3]),
                    confidence=row[4],
                    timestamp=row[5]
                )
            
            conn.close()
            return None
        except Exception as e:
            print(f"Error retrieving computation result: {e}")
            return None
    
    def log_rewiring_proposal(self, expert_id: int, proposal: Dict, swarm_consensus: float, 
                            proposing_agent: str) -> str:
        """Log rewiring proposal to audit trail"""
        proposal_id = f"rewire_{expert_id}_{int(time.time())}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO moe_rewiring_audit
                (id, expert_id, proposal_json, swarm_consensus, proposing_agent, approved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal_id,
                expert_id,
                json.dumps(proposal),
                swarm_consensus,
                proposing_agent,
                False,  # Pending approval
                int(time.time())
            ))
            
            conn.commit()
            conn.close()
            return proposal_id
        except Exception as e:
            print(f"Error logging rewiring proposal: {e}")
            return ""
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Expert cache stats
            cursor.execute("SELECT COUNT(*), SUM(cache_hit_count) FROM moe_expert_cache")
            expert_count, expert_hits = cursor.fetchone()
            
            # Computation cache stats
            cursor.execute("SELECT COUNT(*), SUM(hit_count) FROM moe_computation_cache")
            comp_count, comp_hits = cursor.fetchone()
            
            # Rewiring audit stats
            cursor.execute("SELECT COUNT(*) FROM moe_rewiring_audit")
            audit_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "expert_cache_entries": expert_count or 0,
                "expert_cache_hits": expert_hits or 0,
                "computation_cache_entries": comp_count or 0,
                "computation_cache_hits": comp_hits or 0,
                "rewiring_proposals": audit_count or 0
            }
        except Exception as e:
            print(f"Error getting cache statistics: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    cache = MoEENECache()
    
    # Cache an expert configuration
    config = ExpertConfiguration(
        expert_id=1,
        gating_weight=0.7,
        quality_weight=0.8,
        coherence=0.9,
        penalty_weight=0.1,
        distortion=0.05,
        arity=5.0,
        cost_coefficient=0.02,
        overhead=0.01,
        semantic_vector=[0.5, 0.3, 0.7, 0.2, 0.1, 0.4, 0.6, 0.8, 0.2, 0.3, 0.5, 0.7, 0.1, 0.4],
        domain="neural_manifold",
        version="1.0.0"
    )
    
    print("Caching expert configuration...")
    cache.cache_expert_config(config)
    
    # Retrieve it
    print("Retrieving expert configuration...")
    retrieved = cache.retrieve_expert_config(1)
    print(f"Retrieved: {retrieved}")
    
    # Cache a computation result
    entry = MoECacheEntry(
        cache_key="eta_moe_12345",
        expert_ids=[1, 2, 3],
        eta_moe_result=0.85,
        i_discarded=0.1,
        semantic_vector=[0.5, 0.3, 0.7, 0.2, 0.1, 0.4, 0.6, 0.8, 0.2, 0.3, 0.5, 0.7, 0.1, 0.4],
        confidence=0.95,
        timestamp=int(time.time())
    )
    
    print("Caching computation result...")
    cache.cache_computation_result(entry)
    
    # Retrieve it
    print("Retrieving computation result...")
    retrieved_entry = cache.retrieve_computation_result("eta_moe_12345")
    print(f"Retrieved: {retrieved_entry}")
    
    # Get statistics
    print("Cache statistics:")
    stats = cache.get_cache_statistics()
    print(json.dumps(stats, indent=2))
