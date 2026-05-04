#!/usr/bin/env python3
"""
Swarm Competition Integration for ASCII Art

Integrates ASCII art store with the swarm competition system to spur
competition for better ASCII art generation, style classification,
semantic matching, and ranking.

Competition Areas:
1. ASCII Art Generation - agents compete to generate higher-quality art
2. Style Classification - agents compete for better style detection
3. Semantic Matching - agents compete for better vector representations
4. Ranking and Curation - agents compete to rank art by quality
"""

import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))

from infra.ascii_art_store import AsciiArtStore, AsciiArtEntry
from infra.ene_api import ENEAPIHook, AccessLevel


class CompetitionType(Enum):
    """Types of ASCII art competitions"""
    GENERATION = "generation"
    STYLE_CLASSIFICATION = "style_classification"
    SEMANTIC_MATCHING = "semantic_matching"
    RANKING = "ranking"


@dataclass
class CompetitionEntry:
    """Entry in ASCII art competition"""
    agent_id: str
    competition_type: CompetitionType
    ascii_art_id: str
    score: float
    metrics: Dict[str, float]
    timestamp: int
    proposal: str


class AsciiArtCompetition:
    """Swarm competition manager for ASCII art"""
    
    def __init__(self, db_path: str = "/home/allaun/Documents/Research Stack/data/substrate_index.db"):
        self.db_path = db_path
        self.ascii_store = AsciiArtStore()
        self.ene_api = ENEAPIHook()
        self._init_competition_tables()
    
    def _init_competition_tables(self):
        """Initialize competition-specific tables"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Competition entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ascii_art_competition (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                competition_type TEXT NOT NULL,
                ascii_art_id TEXT,
                score REAL NOT NULL,
                metrics TEXT NOT NULL,
                proposal TEXT,
                timestamp INTEGER NOT NULL,
                approved BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Leaderboard table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ascii_art_leaderboard (
                agent_id TEXT PRIMARY KEY,
                total_score REAL NOT NULL,
                competitions_won INTEGER DEFAULT 0,
                entries_count INTEGER DEFAULT 0,
                last_updated INTEGER NOT NULL
            )
        """)
        
        # Competition metrics tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ascii_art_metrics (
                metric_name TEXT PRIMARY KEY,
                current_best REAL,
                best_agent_id TEXT,
                timestamp INTEGER NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def submit_competition_entry(self, entry: CompetitionEntry) -> bool:
        """Submit an entry to the competition"""
        try:
            entry_id = f"comp_{entry.competition_type.value}_{entry.agent_id}_{int(hashlib.sha256(entry.agent_id.encode()).hexdigest()[:8], 16)}"
            
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ascii_art_competition
                (id, agent_id, competition_type, ascii_art_id, score, metrics, proposal, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                entry.agent_id,
                entry.competition_type.value,
                entry.ascii_art_id,
                entry.score,
                json.dumps(entry.metrics),
                entry.proposal,
                entry.timestamp
            ))
            
            # Update leaderboard
            self._update_leaderboard(entry.agent_id, entry.score)
            
            # Update metrics tracking
            for metric_name, metric_value in entry.metrics.items():
                self._update_metric(metric_name, metric_value, entry.agent_id)
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error submitting competition entry: {e}")
            return False
    
    def _update_leaderboard(self, agent_id: str, score: float):
        """Update agent leaderboard"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ascii_art_leaderboard (agent_id, total_score, competitions_won, entries_count, last_updated)
            VALUES (?, 0, 0, 1, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                total_score = total_score + ?,
                entries_count = entries_count + 1,
                last_updated = ?
        """, (agent_id, int(__import__('time').time()), score, int(__import__('time').time())))
        
        conn.commit()
        conn.close()
    
    def _update_metric(self, metric_name: str, value: float, agent_id: str):
        """Update competition metrics tracking"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ascii_art_metrics (metric_name, current_best, best_agent_id, timestamp)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(metric_name) DO UPDATE SET
                current_best = CASE WHEN ? > current_best THEN ? ELSE current_best END,
                best_agent_id = CASE WHEN ? > current_best THEN ? ELSE best_agent_id END,
                timestamp = CASE WHEN ? > current_best THEN ? ELSE timestamp END
        """, (metric_name, value, agent_id, int(__import__('time').time()),
              value, value, value, agent_id, value, int(__import__('time').time())))
        
        conn.commit()
        conn.close()
    
    def evaluate_generation_quality(self, ascii_art: str) -> Dict[str, float]:
        """Evaluate ASCII art generation quality metrics"""
        lines = ascii_art.split('\n')
        width = max(len(line) for line in lines) if lines else 0
        height = len(lines)
        
        # Quality metrics
        aspect_ratio_score = 1.0 - abs(1.0 - (width / height)) if height > 0 else 0.0
        line_consistency = 1.0 if len(set(len(line) for line in lines)) == 1 else 0.5
        character_diversity = len(set(ascii_art)) / 95.0  # Normalized by printable ASCII
        
        return {
            "aspect_ratio": aspect_ratio_score,
            "line_consistency": line_consistency,
            "character_diversity": min(character_diversity, 1.0),
            "overall_quality": (aspect_ratio_score + line_consistency + character_diversity) / 3.0
        }
    
    def evaluate_style_classification(self, ascii_art: str, predicted_style: str, actual_style: str) -> float:
        """Evaluate style classification accuracy"""
        return 1.0 if predicted_style == actual_style else 0.0
    
    def evaluate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Evaluate semantic similarity between two texts"""
        # Simple character-level similarity
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get current competition leaderboard"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT agent_id, total_score, competitions_won, entries_count
                FROM ascii_art_leaderboard
                ORDER BY total_score DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "agent_id": row[0],
                    "total_score": row[1],
                    "competitions_won": row[2],
                    "entries_count": row[3]
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []
    
    def get_best_metrics(self) -> Dict[str, Any]:
        """Get best metrics across all competitions"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM ascii_art_metrics")
            rows = cursor.fetchall()
            conn.close()
            
            return {
                row[0]: {
                    "current_best": row[1],
                    "best_agent_id": row[2],
                    "timestamp": row[3]
                }
                for row in rows
            }
        except Exception as e:
            print(f"Error getting best metrics: {e}")
            return {}
    
    def approve_winner(self, competition_type: CompetitionType, agent_id: str) -> bool:
        """Approve a competition winner and integrate their work"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            
            # Get highest scoring entry for this agent and competition type
            cursor.execute("""
                SELECT id FROM ascii_art_competition
                WHERE competition_type = ? AND agent_id = ?
                ORDER BY score DESC
                LIMIT 1
            """, (competition_type.value, agent_id))
            
            row = cursor.fetchone()
            if row:
                entry_id = row[0]
                # Mark entry as approved
                cursor.execute("""
                    UPDATE ascii_art_competition
                    SET approved = TRUE
                    WHERE id = ?
                """, (entry_id,))
                
                # Increment competitions won
                cursor.execute("""
                    UPDATE ascii_art_leaderboard
                    SET competitions_won = competitions_won + 1
                    WHERE agent_id = ?
                """, (agent_id))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error approving winner: {e}")
            return False


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("ASCII ART SWARM COMPETITION TEST")
    print("=" * 70)
    
    competition = AsciiArtCompetition()
    
    # Test 1: Submit competition entries
    print("\n[Test 1] Submitting competition entries...")
    
    # Agent 1 entry
    entry1 = CompetitionEntry(
        agent_id="agent_alpha",
        competition_type=CompetitionType.GENERATION,
        ascii_art_id="test_smiley_001",
        score=0.85,
        metrics={
            "aspect_ratio": 0.9,
            "line_consistency": 0.8,
            "character_diversity": 0.85,
            "overall_quality": 0.85
        },
        timestamp=int(__import__('time').time()),
        proposal="Improved aspect ratio detection"
    )
    
    competition.submit_competition_entry(entry1)
    
    # Agent 2 entry
    entry2 = CompetitionEntry(
        agent_id="agent_beta",
        competition_type=CompetitionType.GENERATION,
        ascii_art_id="test_smiley_001",
        score=0.78,
        metrics={
            "aspect_ratio": 0.85,
            "line_consistency": 0.75,
            "character_diversity": 0.74,
            "overall_quality": 0.78
        },
        timestamp=int(__import__('time').time()),
        proposal="Optimized character selection"
    )
    
    competition.submit_competition_entry(entry2)
    
    # Test 2: Get leaderboard
    print("\n[Test 2] Getting leaderboard...")
    leaderboard = competition.get_leaderboard(limit=5)
    print(json.dumps(leaderboard, indent=2))
    
    # Test 3: Get best metrics
    print("\n[Test 3] Getting best metrics...")
    best_metrics = competition.get_best_metrics()
    print(json.dumps(best_metrics, indent=2))
    
    # Test 4: Approve winner
    print("\n[Test 4] Approving winner...")
    competition.approve_winner(CompetitionType.GENERATION, "agent_alpha")
    
    # Test 5: Updated leaderboard
    print("\n[Test 5] Updated leaderboard...")
    leaderboard = competition.get_leaderboard(limit=5)
    print(json.dumps(leaderboard, indent=2))
    
    print("\n" + "=" * 70)
    print("ASCII ART SWARM COMPETITION INTEGRATION COMPLETE")
    print("=" * 70)
