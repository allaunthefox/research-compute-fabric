#!/usr/bin/env python3
"""
ASCII Art Store Integration with ENE

Integrates the Hugging Face dataset "Csplk/THE.ASCII.ART.EMPORIUM"
with the ENE ecosystem for secure storage and retrieval of ASCII art.

Dataset: 30,969 ASCII art entries
- Task: Text generation
- Format: Text
- Language: English
- Size: 1M - 10M
- Category: Art

Integration:
- ASCII art stored securely in ENE database
- Semantic vector encoding for similarity search
- Hyperbolic encoding for hierarchical concept matching
- Access control via ENE security system
"""

import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))

from infra.ene_api import ENEAPIHook, AccessLevel
from infra.lean_unified_shim import OmnidirectionalInterface


@dataclass
class AsciiArtEntry:
    """ASCII art entry from the dataset"""
    id: str
    text: str
    category: Optional[str] = None
    style: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    metadata: Dict = None


class AsciiArtStore:
    """ASCII Art Store integrated with ENE"""
    
    def __init__(self, db_path: str = "/home/allaun/Documents/Research Stack/data/substrate_index.db"):
        self.db_path = db_path
        self.ene_api = ENEAPIHook()
        self.omni_interface = OmnidirectionalInterface()
        self._init_ascii_tables()
    
    def _init_ascii_tables(self):
        """Initialize ASCII art specific tables in ENE database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ASCII art catalog table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ascii_art_catalog (
                id TEXT PRIMARY KEY,
                category TEXT,
                style TEXT,
                width INTEGER,
                height INTEGER,
                line_count INTEGER,
                char_count INTEGER,
                semantic_vector TEXT,
                hyperbolic_coords TEXT,
                created_at INTEGER NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        """)
        
        # ASCII art style index
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ascii_art_styles (
                style TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                avg_width REAL,
                avg_height REAL,
                last_updated INTEGER NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _analyze_ascii_art(self, text: str) -> Dict[str, Any]:
        """Analyze ASCII art properties"""
        lines = text.split('\n')
        width = max(len(line) for line in lines) if lines else 0
        height = len(lines)
        line_count = len(lines)
        char_count = sum(len(line) for line in lines)
        
        # Detect style based on patterns
        style = self._detect_style(text)
        
        return {
            "width": width,
            "height": height,
            "line_count": line_count,
            "char_count": char_count,
            "style": style
        }
    
    def _detect_style(self, text: str) -> str:
        """Detect ASCII art style from patterns"""
        # Simple heuristic style detection
        if '█' in text or '▓' in text or '▒' in text:
            return "block"
        elif any(c in text for c in '/\\|()_'):
            return "line"
        elif any(c in text for c in '@#%*+=-:.'):
            return "ascii"
        else:
            return "mixed"
    
    def store_ascii_art(self, entry: AsciiArtEntry) -> bool:
        """Store ASCII art entry in ENE database"""
        try:
            # Analyze the art
            analysis = self._analyze_ascii_art(entry.text)
            
            # Generate semantic vector
            semantic_vector = self.omni_interface._derive_semantic_vector(
                entry.text[:500],  # Use first 500 chars for semantic vector
                {"category": entry.category, "style": analysis["style"]}
            )
            
            # Generate hyperbolic encoding
            import numpy as np
            vector_array = np.array(semantic_vector)
            hyperbolic = self.omni_interface.hyperbolic_cache.get_or_encode(vector_array)
            
            # Store in ENE secure storage
            self.ene_api.store_sensitive_data(
                pkg=f"ascii_art/{entry.id}",
                payload=entry.text,
                classification=AccessLevel.PUBLIC,  # ASCII art is public
                semantic_vector=semantic_vector
            )
            
            # Store metadata in catalog
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO ascii_art_catalog
                (id, category, style, width, height, line_count, char_count, 
                 semantic_vector, hyperbolic_coords, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                entry.category or "general",
                analysis["style"],
                analysis["width"],
                analysis["height"],
                analysis["line_count"],
                analysis["char_count"],
                json.dumps(semantic_vector),
                json.dumps(hyperbolic.coordinates.tolist()),
                int(__import__('time').time())
            ))
            
            # Update style index
            cursor.execute("""
                INSERT OR REPLACE INTO ascii_art_styles
                (style, count, avg_width, avg_height, last_updated)
                VALUES (?, 1, ?, ?, ?)
            """, (
                analysis["style"],
                analysis["width"],
                analysis["height"],
                int(__import__('time').time())
            ))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error storing ASCII art: {e}")
            return False
    
    def retrieve_ascii_art(self, art_id: str) -> Optional[AsciiArtEntry]:
        """Retrieve ASCII art entry by ID"""
        try:
            # Retrieve from ENE secure storage
            result = self.ene_api.retrieve_sensitive_data(
                f"ascii_art/{art_id}",
                AccessLevel.PUBLIC
            )
            
            if result.get("success"):
                # Get metadata from catalog
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT category, style, width, height, line_count, char_count
                    FROM ascii_art_catalog
                    WHERE id = ?
                """, (art_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    # Increment access count
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE ascii_art_catalog SET access_count = access_count + 1 WHERE id = ?",
                        (art_id,)
                    )
                    conn.commit()
                    conn.close()
                    
                    return AsciiArtEntry(
                        id=art_id,
                        text=result["payload"],
                        category=row[0],
                        style=row[1],
                        width=row[2],
                        height=row[3],
                        metadata={"line_count": row[4], "char_count": row[5]}
                    )
            
            return None
        except Exception as e:
            print(f"Error retrieving ASCII art: {e}")
            return None
    
    def search_by_style(self, style: str, limit: int = 20) -> List[Dict]:
        """Search ASCII art by style"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, category, style, width, height, line_count, char_count
                FROM ascii_art_catalog
                WHERE style = ?
                ORDER BY access_count DESC
                LIMIT ?
            """, (style, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "id": row[0],
                    "category": row[1],
                    "style": row[2],
                    "width": row[3],
                    "height": row[4],
                    "line_count": row[5],
                    "char_count": row[6]
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error searching by style: {e}")
            return []
    
    def semantic_search(self, query: str, limit: int = 20) -> List[Dict]:
        """Semantic search for ASCII art using hyperbolic encoding"""
        try:
            # Derive semantic vector for query
            semantic_vector = self.omni_interface._derive_semantic_vector(query)
            
            # Use hyperbolic similarity search
            result = self.omni_interface.hyperbolic_similarity_search(query, top_k=limit)
            
            # Get matching ASCII art entries
            similar_ids = [str(sim[0]) for sim in result["similar_results"]]
            
            if not similar_ids:
                return []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            placeholders = ",".join(["?" for _ in similar_ids])
            cursor.execute(f"""
                SELECT id, category, style, width, height, line_count, char_count
                FROM ascii_art_catalog
                WHERE id IN ({placeholders})
                ORDER BY access_count DESC
            """, similar_ids)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "id": row[0],
                    "category": row[1],
                    "style": row[2],
                    "width": row[3],
                    "height": row[4],
                    "line_count": row[5],
                    "char_count": row[6],
                    "similarity": result["similar_results"][i][1] if i < len(result["similar_results"]) else 0.0
                }
                for i, row in enumerate(rows)
            ]
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ASCII art store statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total entries
            cursor.execute("SELECT COUNT(*) FROM ascii_art_catalog")
            total = cursor.fetchone()[0]
            
            # Style distribution
            cursor.execute("SELECT style, COUNT(*) FROM ascii_art_catalog GROUP BY style")
            style_dist = dict(cursor.fetchall())
            
            # Average dimensions
            cursor.execute("SELECT AVG(width), AVG(height) FROM ascii_art_catalog")
            avg_dims = cursor.fetchone()
            
            # Total access count
            cursor.execute("SELECT SUM(access_count) FROM ascii_art_catalog")
            total_access = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total_entries": total,
                "style_distribution": style_dist,
                "average_dimensions": {
                    "width": round(avg_dims[0] or 0, 2),
                    "height": round(avg_dims[1] or 0, 2)
                },
                "total_access_count": total_access
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("ASCII ART STORE - ENE INTEGRATION TEST")
    print("=" * 70)
    
    store = AsciiArtStore()
    
    # Test 1: Store sample ASCII art
    print("\n[Test 1] Storing sample ASCII art...")
    sample_art = """
   _____
  /     \\
 |  O O  |
 |   ^   |
 |  \\_/  |
  \\_____/
"""
    entry = AsciiArtEntry(
        id="test_smiley_001",
        text=sample_art,
        category="faces",
        style="line"
    )
    
    success = store.store_ascii_art(entry)
    print(f"Store result: {success}")
    
    # Test 2: Retrieve ASCII art
    print("\n[Test 2] Retrieving ASCII art...")
    retrieved = store.retrieve_ascii_art("test_smiley_001")
    if retrieved:
        print(f"Retrieved: {retrieved.text}")
        print(f"Style: {retrieved.style}, Width: {retrieved.width}, Height: {retrieved.height}")
    else:
        print("Failed to retrieve")
    
    # Test 3: Search by style
    print("\n[Test 3] Searching by style...")
    line_art = store.search_by_style("line", limit=5)
    print(f"Found {len(line_art)} line-style entries")
    
    # Test 4: Semantic search
    print("\n[Test 4] Semantic search...")
    semantic_results = store.semantic_search("smiley face happy", limit=5)
    print(f"Found {len(semantic_results)} semantic matches")
    
    # Test 5: Statistics
    print("\n[Test 5] Store statistics...")
    stats = store.get_statistics()
    print(json.dumps(stats, indent=2))
    
    print("\n" + "=" * 70)
    print("ASCII ART STORE INTEGRATION COMPLETE")
    print("=" * 70)
