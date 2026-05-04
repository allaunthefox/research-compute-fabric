#!/usr/bin/env python3
"""
Substrate Bridge — ENE/Linear Integration
First-Principles Derivation: Self-typing loop: Substrate (ENE) ↔ Surface ↔ Intent (Linear) ⟹ Metatype

Performance Targets:
- < 50ms single read operation
- < 100ms batch read (100 items)
- < 200ms batch write (100 items)
- Connection pooling (reuse database connections)
- Batch read/write (reduce round trips)
- Cached hot data (frequently accessed coordinates)
- Async I/O (non-blocking operations)
"""

import sqlite3
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class ConceptVector14:
    """14-dimensional concept vector from ENE database"""
    vector: np.ndarray  # Shape: (14,)
    archive_id: str
    
    def __post_init__(self):
        if self.vector.shape != (14,):
            raise ValueError(f"ConceptVector14 must have shape (14,), got {self.vector.shape}")
    
    def to_dict(self) -> dict:
        return {
            "archive_id": self.archive_id,
            "vector": self.vector.tolist()
        }


@dataclass
class AVMRState:
    """AVMR shell state for O(√N) indexing"""
    shell_level: int  # k in n = k² + a
    shell_offset: int  # a in n = k² + a
    shell_complement: int  # b = (k+1)² - n
    spectral_bins: np.ndarray  # Q16_16 spectral bins
    
    def to_dict(self) -> dict:
        return {
            "shell_level": self.shell_level,
            "shell_offset": self.shell_offset,
            "shell_complement": self.shell_complement,
            "spectral_bins": self.spectral_bins.tolist()
        }


@dataclass
class BracketedBounds:
    """Bracketed bounds for interval semantics"""
    lower_bound: float
    upper_bound: float
    resolution: str  # SEED, FORMING, STABLE, CRYSTALLIZED, COMPRESSED
    
    def to_dict(self) -> dict:
        return {
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "resolution": self.resolution
        }


@dataclass
class WitnessReceipt:
    """Witness receipt for provenance"""
    receipt_hash: str
    archive_id: str
    timestamp: datetime
    operation: str  # "read", "write", "collapse"
    
    def to_dict(self) -> dict:
        return {
            "receipt_hash": self.receipt_hash,
            "archive_id": self.archive_id,
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation
        }


class SubstrateBridge:
    """
    Substrate Bridge — ENE/Linear Integration
    
    Bridge between manifold surface and ENE substrate
    """
    
    def __init__(self, db_path: str):
        """
        Initialize substrate bridge
        
        Args:
            db_path: Path to ENE database
        """
        self.db_path = db_path
        self.connection_pool = []
        self.cache = {}  # Hot data cache
        self.witnesses = []
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get connection from pool or create new one"""
        if self.connection_pool:
            return self.connection_pool.pop()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _return_connection(self, conn: sqlite3.Connection) -> None:
        """Return connection to pool"""
        if len(self.connection_pool) < 10:  # Pool size limit
            self.connection_pool.append(conn)
        else:
            conn.close()
    
    def read_coordinate(self, archive_id: str) -> Optional[ConceptVector14]:
        """
        Read concept vector from ENE database
        
        Args:
            archive_id: Archive ID to read
            
        Returns:
            Concept vector if found, None otherwise
        """
        # Check cache first
        if archive_id in self.cache:
            return self.cache[archive_id]
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT archive_id, concept_vector_14
                FROM packages
                WHERE archive_id = ?
            """, (archive_id,))
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            vector_str = row['concept_vector_14']
            if vector_str is None:
                return None
            
            # Parse vector
            vector_data = json.loads(vector_str)
            vector = np.array(vector_data, dtype=np.float32)
            
            if len(vector) != 14:
                return None
            
            concept_vector = ConceptVector14(vector=vector, archive_id=archive_id)
            
            # Cache result
            self.cache[archive_id] = concept_vector
            
            # Record witness
            witness = WitnessReceipt(
                receipt_hash=hashlib.sha256(archive_id.encode()).hexdigest(),
                archive_id=archive_id,
                timestamp=datetime.now(),
                operation="read"
            )
            self.witnesses.append(witness)
            
            return concept_vector
            
        except Exception as e:
            print(f"Error reading coordinate: {e}")
            return None
        finally:
            self._return_connection(conn)
    
    def read_avmr(self, archive_id: str) -> Optional[AVMRState]:
        """
        Read AVMR shell state from ENE database
        
        Args:
            archive_id: Archive ID to read
            
        Returns:
            AVMR state if found, None otherwise
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT avmr_shell_state
                FROM packages
                WHERE archive_id = ?
            """, (archive_id,))
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            avmr_str = row['avmr_shell_state']
            if avmr_str is None:
                return None
            
            # Parse AVMR state
            avmr_data = json.loads(avmr_str)
            
            return AVMRState(
                shell_level=avmr_data.get('shell_level', 0),
                shell_offset=avmr_data.get('shell_offset', 0),
                shell_complement=avmr_data.get('shell_complement', 0),
                spectral_bins=np.array(avmr_data.get('spectral_bins', []), dtype=np.float32)
            )
            
        except Exception as e:
            print(f"Error reading AVMR state: {e}")
            return None
        finally:
            self._return_connection(conn)
    
    def read_bracketed(self, archive_id: str) -> Optional[BracketedBounds]:
        """
        Read bracketed bounds from ENE database
        
        Args:
            archive_id: Archive ID to read
            
        Returns:
            Bracketed bounds if found, None otherwise
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT bracketed_bounds
                FROM packages
                WHERE archive_id = ?
            """, (archive_id,))
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            bounds_str = row['bracketed_bounds']
            if bounds_str is None:
                return None
            
            # Parse bracketed bounds
            bounds_data = json.loads(bounds_str)
            
            return BracketedBounds(
                lower_bound=bounds_data.get('lower_bound', 0.0),
                upper_bound=bounds_data.get('upper_bound', 1.0),
                resolution=bounds_data.get('resolution', 'STABLE')
            )
            
        except Exception as e:
            print(f"Error reading bracketed bounds: {e}")
            return None
        finally:
            self._return_connection(conn)
    
    def read_witness(self, archive_id: str) -> Optional[WitnessReceipt]:
        """
        Read witness receipt from ENE database
        
        Args:
            archive_id: Archive ID to read
            
        Returns:
            Witness receipt if found, None otherwise
        """
        # Check local witnesses first
        for witness in reversed(self.witnesses):
            if witness.archive_id == archive_id:
                return witness
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT receipt_hash, archive_id, timestamp, operation
                FROM witnesses
                WHERE archive_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (archive_id,))
            
            row = cursor.fetchone()
            if row is None:
                return None
            
            return WitnessReceipt(
                receipt_hash=row['receipt_hash'],
                archive_id=row['archive_id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                operation=row['operation']
            )
            
        except Exception as e:
            print(f"Error reading witness: {e}")
            return None
        finally:
            self._return_connection(conn)
    
    def batch_read(self, archive_ids: List[str]) -> Dict[str, ConceptVector14]:
        """
        Batch read concept vectors from ENE database
        
        Args:
            archive_ids: List of archive IDs to read
            
        Returns:
            Dictionary mapping archive IDs to concept vectors
        """
        results = {}
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Build placeholder string for SQL IN clause
            placeholders = ','.join('?' * len(archive_ids))
            
            cursor.execute(f"""
                SELECT archive_id, concept_vector_14
                FROM packages
                WHERE archive_id IN ({placeholders})
            """, archive_ids)
            
            for row in cursor.fetchall():
                archive_id = row['archive_id']
                vector_str = row['concept_vector_14']
                
                if vector_str is None:
                    continue
                
                # Parse vector
                vector_data = json.loads(vector_str)
                vector = np.array(vector_data, dtype=np.float32)
                
                if len(vector) != 14:
                    continue
                
                concept_vector = ConceptVector14(vector=vector, archive_id=archive_id)
                results[archive_id] = concept_vector
                
                # Cache result
                self.cache[archive_id] = concept_vector
            
            return results
            
        except Exception as e:
            print(f"Error in batch read: {e}")
            return {}
        finally:
            self._return_connection(conn)
    
    def write_coordinate(self, archive_id: str, vector: ConceptVector14) -> bool:
        """
        Write concept vector to ENE database
        
        Args:
            archive_id: Archive ID to write
            vector: Concept vector to write
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Serialize vector
            vector_str = json.dumps(vector.vector.tolist())
            
            cursor.execute("""
                UPDATE packages
                SET concept_vector_14 = ?
                WHERE archive_id = ?
            """, (vector_str, archive_id))
            
            conn.commit()
            
            # Update cache
            self.cache[archive_id] = vector
            
            # Record witness
            witness = WitnessReceipt(
                receipt_hash=hashlib.sha256((archive_id + vector_str).encode()).hexdigest(),
                archive_id=archive_id,
                timestamp=datetime.now(),
                operation="write"
            )
            self.witnesses.append(witness)
            
            return True
            
        except Exception as e:
            print(f"Error writing coordinate: {e}")
            conn.rollback()
            return False
        finally:
            self._return_connection(conn)
    
    def write_witness(self, archive_id: str, witness: WitnessReceipt) -> bool:
        """
        Write witness receipt to ENE database
        
        Args:
            archive_id: Archive ID
            witness: Witness receipt to write
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO witnesses (receipt_hash, archive_id, timestamp, operation)
                VALUES (?, ?, ?, ?)
            """, (witness.receipt_hash, archive_id, witness.timestamp.isoformat(), witness.operation))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error writing witness: {e}")
            conn.rollback()
            return False
        finally:
            self._return_connection(conn)
    
    def batch_write(self, updates: Dict[str, ConceptVector14]) -> bool:
        """
        Batch write concept vectors to ENE database
        
        Args:
            updates: Dictionary mapping archive IDs to concept vectors
            
        Returns:
            True if all successful, False otherwise
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            for archive_id, vector in updates.items():
                # Serialize vector
                vector_str = json.dumps(vector.vector.tolist())
                
                cursor.execute("""
                    UPDATE packages
                    SET concept_vector_14 = ?
                    WHERE archive_id = ?
                """, (vector_str, archive_id))
                
                # Update cache
                self.cache[archive_id] = vector
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error in batch write: {e}")
            conn.rollback()
            return False
        finally:
            self._return_connection(conn)
    
    def sync_with_linear(self, linear_issue_id: str, archive_id: str) -> bool:
        """
        Sync with Linear intent tracking
        
        Args:
            linear_issue_id: Linear issue ID
            archive_id: Archive ID to sync
            
        Returns:
            True if successful, False otherwise
        """
        # This would integrate with Linear API
        # For now, just record the sync intent
        print(f"Syncing Linear issue {linear_issue_id} with archive {archive_id}")
        return True
    
    def extract_intent(self, linear_issue: Dict) -> np.ndarray:
        """
        Extract intent vector from Linear issue
        
        Args:
            linear_issue: Linear issue data
            
        Returns:
            Intent vector (14D)
        """
        # Extract intent from issue fields
        # This is a simplified implementation
        intent_vector = np.zeros(14, dtype=np.float32)
        
        # Map issue fields to intent dimensions
        if 'title' in linear_issue:
            intent_vector[0] = len(linear_issue['title']) / 100.0
        if 'description' in linear_issue:
            intent_vector[1] = len(lineframe_issue['description']) / 1000.0
        if 'priority' in linear_issue:
            priority_map = {'urgent': 1.0, 'high': 0.75, 'medium': 0.5, 'low': 0.25}
            intent_vector[2] = priority_map.get(lineframe_issue['priority'], 0.5)
        
        return intent_vector
    
    def intent_to_coordinate(self, intent_vector: np.ndarray) -> ConceptVector14:
        """
        Convert intent vector to concept vector coordinate
        
        Args:
            intent_vector: Intent vector (14D)
            
        Returns:
            Concept vector
        """
        # Simple transformation (in full implementation, use more sophisticated mapping)
        return ConceptVector14(
            vector=intent_vector,
            archive_id=f"intent_{hashlib.sha256(intent_vector.tobytes()).hexdigest()[:16]}"
        )
    
    def generate_metatype(self, surface_data: Dict, substrate_data: Dict, intent_data: Dict) -> Dict:
        """
        Generate metatype from integration of layers
        
        Args:
            surface_data: Data from surface layer
            substrate_data: Data from substrate layer
            intent_data: Data from intent layer
            
        Returns:
            Metatype dictionary
        """
        # Simple metatype generation (in full implementation, use self-typing engine)
        return {
            "type_signature": f"{substrate_data.get('type', 'unknown')}:{surface_data.get('type', 'unknown')}:{intent_data.get('type', 'unknown')}",
            "confidence": 0.5,
            "source_layers": ["substrate", "surface", "intent"]
        }
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "witness_count": len(self.witnesses),
            "connection_pool_size": len(self.connection_pool)
        }


def main():
    """Test substrate bridge with ENE database"""
    db_path = "/home/allaun/Documents/Research Stack/data/substrate_index.db"
    
    try:
        bridge = SubstrateBridge(db_path)
        
        # Test read
        vector = bridge.read_coordinate("test_archive_id")
        print(f"Read vector: {vector}")
        
        # Test batch read
        results = bridge.batch_read(["test_archive_id_1", "test_archive_id_2"])
        print(f"Batch read: {len(results)} results")
        
        # Get cache stats
        stats = bridge.get_cache_stats()
        print(f"Cache stats: {stats}")
        
    except Exception as e:
        print(f"Error testing substrate bridge: {e}")


if __name__ == "__main__":
    main()
