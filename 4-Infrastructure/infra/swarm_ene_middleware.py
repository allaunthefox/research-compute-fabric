#!/usr/bin/env python3
"""
Swarm API-ENE Middleware

Middleware layer that hooks the Research/Swarm API into the ENE database
for caching, audit logging, and secure data storage. Intercepts API calls,
checks ENE cache first, and stores results for future use.

Features:
- Query result caching in ENE database
- Semantic vector-based retrieval
- Access control integration
- Audit logging for all operations
- Automatic cache invalidation on updates
"""

import hashlib
import json
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infra.ene_api import ENEAPIHook, AccessLevel


@dataclass
class SwarmQueryCache:
    """Cached swarm query result"""
    query_hash: str
    subjects: List[str]
    keywords: Optional[str]
    formal_status: Optional[str]
    results: List[Dict[str, Any]]
    count: int
    confidence: float
    timestamp: int
    semantic_vector: List[float]
    ttl: int = 3600  # 1 hour default


class SwarmENEMiddleware:
    """Middleware for Swarm API integration with ENE"""
    
    def __init__(self, db_path: str = "/home/allaun/Documents/Research Stack/data/substrate_index.db"):
        self.db_path = db_path
        self.ene_api = ENEAPIHook()
        self._init_middleware_tables()
    
    def _init_middleware_tables(self):
        """Initialize middleware tables in ENE database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Query cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS swarm_query_cache (
                query_hash TEXT PRIMARY KEY,
                subjects TEXT NOT NULL,
                keywords TEXT,
                formal_status TEXT,
                results TEXT NOT NULL,
                count INTEGER NOT NULL,
                confidence REAL NOT NULL,
                semantic_vector TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                ttl INTEGER NOT NULL,
                hit_count INTEGER DEFAULT 0
            )
        """)
        
        # API operation audit log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS swarm_api_audit (
                id TEXT PRIMARY KEY,
                operation TEXT NOT NULL,
                query_hash TEXT,
                parameters TEXT NOT NULL,
                result_cached BOOLEAN NOT NULL,
                result_count INTEGER,
                execution_time_ms REAL NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)
        
        # Semantic index for queries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS swarm_semantic_index (
                id TEXT PRIMARY KEY,
                query_hash TEXT NOT NULL,
                semantic_vector TEXT NOT NULL,
                domain TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (query_hash) REFERENCES swarm_query_cache(query_hash)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _compute_query_hash(self, subjects: List[str], keywords: Optional[str], 
                           formal_status: Optional[str]) -> str:
        """Compute hash for query cache key"""
        query_str = json.dumps({
            "subjects": sorted(subjects),
            "keywords": keywords,
            "formal_status": formal_status
        }, sort_keys=True)
        return hashlib.sha256(query_str.encode()).hexdigest()
    
    def _derive_semantic_vector(self, subjects: List[str], keywords: Optional[str]) -> List[float]:
        """Derive 14D semantic vector from query parameters"""
        # Simple heuristic: distribute subjects across semantic axes
        # In production, this would use actual semantic embeddings
        vector = [0.0] * 14
        
        for i, subject in enumerate(subjects):
            axis = i % 14
            # Hash subject to get a value in [0,1]
            h = hashlib.md5(subject.encode()).hexdigest()
            value = int(h[:8], 16) / 0xFFFFFFFF
            vector[axis] = value
        
        if keywords:
            # Add keyword influence to first axis
            h = hashlib.md5(keywords.encode()).hexdigest()
            value = int(h[:8], 16) / 0xFFFFFFFF
            vector[0] = (vector[0] + value) / 2
        
        return vector
    
    def check_cache(self, subjects: List[str], keywords: Optional[str], 
                   formal_status: Optional[str]) -> Optional[SwarmQueryCache]:
        """Check if query result is cached"""
        try:
            query_hash = self._compute_query_hash(subjects, keywords, formal_status)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT subjects, keywords, formal_status, results, count, confidence, 
                       semantic_vector, created_at, ttl, hit_count
                FROM swarm_query_cache
                WHERE query_hash = ?
            """, (query_hash,))
            
            row = cursor.fetchone()
            
            if row:
                # Check if cache entry is still valid
                now = int(time.time())
                created_at = row[7]
                ttl = row[8]
                
                if now - created_at < ttl:
                    # Increment hit count
                    cursor.execute("""
                        UPDATE swarm_query_cache
                        SET hit_count = hit_count + 1
                        WHERE query_hash = ?
                    """, (query_hash,))
                    conn.commit()
                    conn.close()
                    
                    return SwarmQueryCache(
                        query_hash=query_hash,
                        subjects=json.loads(row[0]),
                        keywords=row[1],
                        formal_status=row[2],
                        results=json.loads(row[3]),
                        count=row[4],
                        confidence=row[5],
                        semantic_vector=json.loads(row[6]),
                        timestamp=created_at,
                        ttl=ttl
                    )
                else:
                    # Cache expired, delete it
                    cursor.execute("DELETE FROM swarm_query_cache WHERE query_hash = ?", (query_hash,))
                    conn.commit()
                    conn.close()
                    return None
            
            conn.close()
            return None
        except Exception as e:
            print(f"Error checking cache: {e}")
            return None
    
    def store_cache(self, subjects: List[str], keywords: Optional[str], formal_status: Optional[str],
                   results: List[Dict[str, Any]], count: int, confidence: float, 
                   ttl: int = 3600) -> bool:
        """Store query result in cache"""
        try:
            query_hash = self._compute_query_hash(subjects, keywords, formal_status)
            semantic_vector = self._derive_semantic_vector(subjects, keywords)
            now = int(time.time())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO swarm_query_cache
                (query_hash, subjects, keywords, formal_status, results, count, confidence, 
                 semantic_vector, created_at, ttl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_hash,
                json.dumps(subjects),
                keywords,
                formal_status,
                json.dumps(results),
                count,
                confidence,
                json.dumps(semantic_vector),
                now,
                ttl
            ))
            
            # Also store in semantic index
            domain = subjects[0] if subjects else "general"
            cursor.execute("""
                INSERT OR REPLACE INTO swarm_semantic_index
                (id, query_hash, semantic_vector, domain, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"semantic_{query_hash}",
                query_hash,
                json.dumps(semantic_vector),
                domain,
                now
            ))
            
            conn.commit()
            conn.close()
            
            # Store sensitive results in ENE secure storage
            if results:
                self.ene_api.store_sensitive_data(
                    pkg=f"swarm/query/{query_hash}",
                    payload=json.dumps(results),
                    classification=AccessLevel.INTERNAL,
                    semantic_vector=semantic_vector
                )
            
            return True
        except Exception as e:
            print(f"Error storing cache: {e}")
            return False
    
    def log_operation(self, operation: str, parameters: Dict, query_hash: Optional[str],
                    result_cached: bool, result_count: Optional[int], execution_time_ms: float):
        """Log API operation to audit trail"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            operation_id = f"op_{operation}_{int(time.time() * 1000000)}"
            
            cursor.execute("""
                INSERT INTO swarm_api_audit
                (id, operation, query_hash, parameters, result_cached, result_count, execution_time_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation_id,
                operation,
                query_hash,
                json.dumps(parameters),
                result_cached,
                result_count,
                execution_time_ms,
                int(time.time())
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error logging operation: {e}")
    
    def invalidate_cache(self, subjects: Optional[List[str]] = None):
        """Invalidate cache entries matching criteria"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if subjects:
                # Invalidate specific subject queries
                for subject in subjects:
                    cursor.execute("""
                        DELETE FROM swarm_query_cache
                        WHERE subjects LIKE ?
                    """, (f"%{subject}%",))
            else:
                # Invalidate all cache
                cursor.execute("DELETE FROM swarm_query_cache")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error invalidating cache: {e}")
            return False
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get middleware cache statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query cache stats
            cursor.execute("SELECT COUNT(*), SUM(hit_count) FROM swarm_query_cache")
            cache_count, cache_hits = cursor.fetchone()
            
            # Audit log stats
            cursor.execute("SELECT COUNT(*) FROM swarm_api_audit")
            audit_count = cursor.fetchone()[0]
            
            # Cache hit rate
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN hit_count > 0 THEN 1 END) * 100.0 / COUNT(*) 
                FROM swarm_query_cache
            """)
            hit_rate = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "cached_queries": cache_count or 0,
                "cache_hits": cache_hits or 0,
                "audit_log_entries": audit_count or 0,
                "cache_hit_rate": round(hit_rate, 2)
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def semantic_search(self, query_vector: List[float], threshold: float = 0.7) -> List[str]:
        """Find similar queries using semantic vector similarity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT query_hash, semantic_vector FROM swarm_semantic_index")
            rows = cursor.fetchall()
            
            similar_queries = []
            for query_hash, vector_json in rows:
                cached_vector = json.loads(vector_json)
                # Compute cosine similarity
                similarity = self._cosine_similarity(query_vector, cached_vector)
                if similarity >= threshold:
                    similar_queries.append((query_hash, similarity))
            
            conn.close()
            
            # Sort by similarity descending
            similar_queries.sort(key=lambda x: x[1], reverse=True)
            return [q[0] for q in similar_queries]
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0
        return dot_product / (norm1 * norm2)


# Example usage
if __name__ == "__main__":
    middleware = SwarmENEMiddleware()
    
    # Test cache check (should miss)
    print("Checking cache (should miss)...")
    cached = middleware.check_cache(
        subjects=["geometry", "topology"],
        keywords="manifold",
        formal_status="proven"
    )
    print(f"Cached result: {cached}")
    
    # Store a cache entry
    print("Storing cache entry...")
    middleware.store_cache(
        subjects=["geometry", "topology"],
        keywords="manifold",
        formal_status="proven",
        results=[{"id": 1, "name": "Test Result"}],
        count=1,
        confidence=0.95,
        ttl=3600
    )
    
    # Check cache again (should hit)
    print("Checking cache again (should hit)...")
    cached = middleware.check_cache(
        subjects=["geometry", "topology"],
        keywords="manifold",
        formal_status="proven"
    )
    print(f"Cached result: {cached}")
    
    # Log an operation
    print("Logging operation...")
    middleware.log_operation(
        operation="query",
        parameters={"subjects": ["geometry"], "limit": 10},
        query_hash=None,
        result_cached=False,
        result_count=5,
        execution_time_ms=123.45
    )
    
    # Get statistics
    print("Cache statistics:")
    stats = middleware.get_cache_statistics()
    print(json.dumps(stats, indent=2))
