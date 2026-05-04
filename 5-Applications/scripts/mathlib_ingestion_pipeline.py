#!/usr/bin/env python3
"""
Mathlib Ingestion Pipeline with Apache 2.0 Attribution

Extracts entire Mathlib corpus with proper attribution and stores in queryable database.
Enables swarm to "SWALLOW" Mathlib for self-improving knowledge absorption.

License: Apache 2.0
Attribution: Mathlib contributors, Lean Community
"""

import os
import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

# ═══════════════════════════════════════════════════════════════════════════
# §0  Attribution Metadata (Apache 2.0 Compliance)
# ═══════════════════════════════════════════════════════════════════════════

MATHLIB_LICENSE = {
    "name": "Apache License 2.0",
    "url": "https://www.apache.org/licenses/LICENSE-2.0",
    "attribution_required": True,
    "commercial_use_allowed": True,
    "modification_allowed": True
}

MATHLIB_ATTRIBUTION = {
    "source": "Mathlib4",
    "repository": "https://github.com/leanprover-community/mathlib4",
    "license": MATHLIB_LICENSE,
    "contributors": "Lean Community, Mathlib Contributors",
    "extracted_at": datetime.utcnow().isoformat(),
    "extraction_method": "lake build export"
}


@dataclass
class MathlibEntry:
    """Single Mathlib entry with full attribution."""
    module_path: str
    content: str
    docstring: str
    theorem_count: int
    definition_count: int
    authors: List[str]
    dependencies: List[str]
    hash: str
    attribution: Dict[str, str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════════
# §1  Mathlib Extraction from Lake Build
# ═══════════════════════════════════════════════════════════════════════════

def extract_lean_file(file_path: Path) -> Optional[MathlibEntry]:
    """Extract content from a single Lean file with attribution."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract docstring (first /- ... -/ block)
        docstring = ""
        if "/-" in content:
            start = content.find("/-")
            end = content.find("-/", start)
            if end != -1:
                docstring = content[start+2:end].strip()
        
        # Count theorems and definitions
        theorem_count = content.count("theorem ") + content.count("lemma ")
        definition_count = content.count("def ") + content.count("structure ")
        
        # Extract imports/dependencies
        dependencies = []
        for line in content.split('\n'):
            if line.strip().startswith("import ") or line.strip().startswith("open "):
                dependencies.append(line.strip())
        
        # Generate content hash for deduplication
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Module path relative to mathlib
        module_path = str(file_path.relative_to(file_path.parents[len(file_path.parts) - file_path.parts.index("Mathlib") - 1]))
        
        return MathlibEntry(
            module_path=module_path,
            content=content,
            docstring=docstring,
            theorem_count=theorem_count,
            definition_count=definition_count,
            authors=[],  # Would need to parse git history
            dependencies=dependencies,
            hash=content_hash,
            attribution=MATHLIB_ATTRIBUTION
        )
        
    except Exception as e:
        print(f"[ERROR] Failed to extract {file_path}: {e}")
        return None


def extract_mathlib_corpus(mathlib_path: Path) -> List[MathlibEntry]:
    """Extract entire Mathlib corpus with attribution."""
    entries = []
    
    # Find all .lean files in Mathlib
    for lean_file in mathlib_path.rglob("*.lean"):
        entry = extract_lean_file(lean_file)
        if entry:
            entries.append(entry)
            print(f"[OK] Extracted: {entry.module_path}")
    
    print(f"[INFO] Extracted {len(entries)} Mathlib entries")
    return entries


# ═══════════════════════════════════════════════════════════════════════════
# §2  Database Storage (JSON and SQLite)
# ═══════════════════════════════════════════════════════════════════════════

class MathlibDatabase:
    """Queryable database for Mathlib corpus with attribution."""
    
    def __init__(self, db_path: Path, use_sqlite: bool = True):
        self.db_path = db_path
        self.use_sqlite = use_sqlite
        self.entries: List[MathlibEntry] = []
        
    def add_entry(self, entry: MathlibEntry):
        """Add an entry to the database."""
        self.entries.append(entry)
        
    def save_json(self):
        """Save database as JSON."""
        json_path = self.db_path.with_suffix('.json')
        data = {
            "metadata": {
                "license": MATHLIB_LICENSE,
                "attribution": MATHLIB_ATTRIBUTION,
                "entry_count": len(self.entries),
                "saved_at": datetime.utcnow().isoformat()
            },
            "entries": [entry.to_dict() for entry in self.entries]
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"[OK] Saved JSON database: {json_path}")
        
    def save_sqlite(self):
        """Save database as SQLite."""
        sqlite_path = self.db_path.with_suffix('.db')
        
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_path TEXT UNIQUE,
                content TEXT,
                docstring TEXT,
                theorem_count INTEGER,
                definition_count INTEGER,
                authors TEXT,
                dependencies TEXT,
                hash TEXT,
                attribution TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_module_path ON entries(module_path)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hash ON entries(hash)
        ''')
        
        # Insert metadata
        for key, value in MATHLIB_ATTRIBUTION.items():
            cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', 
                         (key, json.dumps(value) if isinstance(value, dict) else value))
        
        # Insert entries
        for entry in self.entries:
            cursor.execute('''
                INSERT OR REPLACE INTO entries 
                (module_path, content, docstring, theorem_count, definition_count, authors, dependencies, hash, attribution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.module_path,
                entry.content,
                entry.docstring,
                entry.theorem_count,
                entry.definition_count,
                json.dumps(entry.authors),
                json.dumps(entry.dependencies),
                entry.hash,
                json.dumps(entry.attribution)
            ))
        
        conn.commit()
        conn.close()
        
        print(f"[OK] Saved SQLite database: {sqlite_path}")
        
    def save(self):
        """Save database in chosen format."""
        if self.use_sqlite:
            self.save_sqlite()
        else:
            self.save_json()


# ═══════════════════════════════════════════════════════════════════════════
# §3  Query Interface for Swarm
# ═══════════════════════════════════════════════════════════════════════════

class MathlibQuery:
    """Query interface for Mathlib database."""
    
    def __init__(self, db_path: Path, use_sqlite: bool = True):
        self.db_path = db_path
        self.use_sqlite = use_sqlite
        
    def query_by_keyword(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Query database by keyword."""
        if self.use_sqlite:
            return self._query_sqlite_keyword(keyword, limit)
        else:
            return self._query_json_keyword(keyword, limit)
    
    def _query_sqlite_keyword(self, keyword: str, limit: int) -> List[Dict]:
        """Query SQLite database by keyword."""
        sqlite_path = self.db_path.with_suffix('.db')
        
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT module_path, content, docstring, theorem_count, definition_count, attribution
            FROM entries
            WHERE content LIKE ? OR docstring LIKE ?
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "module_path": row[0],
                "content": row[1][:1000],  # Limit content
                "docstring": row[2],
                "theorem_count": row[3],
                "definition_count": row[4],
                "attribution": json.loads(row[5])
            })
        
        conn.close()
        return results
    
    def _query_json_keyword(self, keyword: str, limit: int) -> List[Dict]:
        """Query JSON database by keyword."""
        json_path = self.db_path.with_suffix('.json')
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        results = []
        keyword_lower = keyword.lower()
        
        for entry in data['entries']:
            if (keyword_lower in entry['content'].lower() or 
                keyword_lower in entry['docstring'].lower()):
                results.append({
                    "module_path": entry['module_path'],
                    "content": entry['content'][:1000],
                    "docstring": entry['docstring'],
                    "theorem_count": entry['theorem_count'],
                    "definition_count": entry['definition_count'],
                    "attribution": entry['attribution']
                })
                if len(results) >= limit:
                    break
        
        return results
    
    def query_by_module(self, module_path: str) -> Optional[Dict]:
        """Query database by module path."""
        if self.use_sqlite:
            return self._query_sqlite_module(module_path)
        else:
            return self._query_json_module(module_path)
    
    def _query_sqlite_module(self, module_path: str) -> Optional[Dict]:
        """Query SQLite database by module path."""
        sqlite_path = self.db_path.with_suffix('.db')
        
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT module_path, content, docstring, theorem_count, definition_count, attribution
            FROM entries
            WHERE module_path = ?
        ''', (module_path,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "module_path": row[0],
                "content": row[1],
                "docstring": row[2],
                "theorem_count": row[3],
                "definition_count": row[4],
                "attribution": json.loads(row[5])
            }
        return None
    
    def _query_json_module(self, module_path: str) -> Optional[Dict]:
        """Query JSON database by module path."""
        json_path = self.db_path.with_suffix('.json')
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        for entry in data['entries']:
            if entry['module_path'] == module_path:
                return entry
        return None


# ═══════════════════════════════════════════════════════════════════════════
# §4  Main Execution
# ═══════════════════════════════════════════════════════════════════════════

def main():
    mathlib_path = Path("0-Core-Formalism/lean/Semantics/.lake/packages/mathlib")
    output_path = Path("shared-data/data/mathlib_database")
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("[INFO] Starting Mathlib ingestion pipeline with Apache 2.0 attribution...")
    print(f"[INFO] Mathlib path: {mathlib_path}")
    print(f"[INFO] Output path: {output_path}")
    
    # Check if Mathlib exists
    if not mathlib_path.exists():
        print(f"[ERROR] Mathlib not found at {mathlib_path}")
        print("[INFO] Run 'lake update' to download Mathlib")
        return
    
    # Extract Mathlib corpus
    entries = extract_mathlib_corpus(mathlib_path)
    
    if not entries:
        print("[ERROR] No Mathlib entries extracted")
        return
    
    # Save database
    db = MathlibDatabase(output_path / "mathlib_corpus", use_sqlite=True)
    for entry in entries:
        db.add_entry(entry)
    db.save()
    
    # Test query
    print("\n[INFO] Testing query interface...")
    query = MathlibQuery(output_path / "mathlib_corpus", use_sqlite=True)
    
    test_results = query.query_by_keyword("theorem", limit=3)
    print(f"[OK] Query 'theorem' returned {len(test_results)} results")
    for result in test_results:
        print(f"  - {result['module_path']}: {result['theorem_count']} theorems")
    
    print("\n[OK] Mathlib ingestion pipeline complete")
    print(f"[INFO] Total entries: {len(entries)}")
    print(f"[INFO] Database: {output_path / 'mathlib_corpus.db'}")


if __name__ == "__main__":
    main()
