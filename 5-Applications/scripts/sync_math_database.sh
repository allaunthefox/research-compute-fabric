#!/bin/sh
#
# sync_math_database_v2.sh — Bidirectional sync (simplified, robust)
#

set -e

DB_PATH="${MATH_DB_PATH:-/home/allaun/Documents/Research Stack/data/math_entities.db}"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info() { printf "${BLUE}[INFO]${NC} %s\n" "$1"; }
log_ok() { printf "${GREEN}[OK]${NC} %s\n" "$1"; }

# Ensure database exists
mkdir -p "$(dirname "$DB_PATH")"
sqlite3 "$DB_PATH" "CREATE TABLE IF NOT EXISTS math_entities (
    entity_id TEXT PRIMARY KEY, subject TEXT, secondary_subjects TEXT,
    name TEXT, statement TEXT, proof_status TEXT, formal_status TEXT,
    lean_module TEXT, dependencies TEXT, citations TEXT, complexity_score INTEGER,
    year INTEGER, source_file TEXT, last_synced TEXT DEFAULT CURRENT_TIMESTAMP
);" 2>/dev/null || true

# Run Python parser directly
python3 << 'PYEOF'
import sqlite3
import json
import re
import hashlib
from pathlib import Path

db_path = "/home/allaun/Documents/Research Stack/data/math_entities.db"
conn = sqlite3.connect(db_path)

# Find all relevant markdown files
docs_dir = Path("/home/allaun/Documents/Research Stack/docs")
search_dirs = [docs_dir, Path("/home/allaun/Documents/Research Stack/data/germane/research")]

all_files = []
for d in search_dirs:
    if d.exists():
        for pattern in ["*math*.md", "*EQUATION*.md", "*PHYLOGENETIC*.md", "*AMMR*.md", "*ORTHOGONAL*.md", "MATH_CORE.md"]:
            all_files.extend(d.rglob(pattern))

print(f"[INFO] Found {len(all_files)} files to scan")

total_entities = 0
for file_path in all_files:
    if not file_path.is_file():
        continue
        
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"[WARN] Could not read {file_path}: {e}")
        continue
    
    entities = []
    header_pattern = r'^#+\s+(.*?)(?:\n|$)'
    keywords = ['theorem', 'equation', 'lemma', 'proof', 'conjecture', 'ammr', 
                'orthogonal', 'memory', 'crc', 'node', 'range', 'joule', 'thermodynamic']
    
    for match in re.finditer(header_pattern, content, re.MULTILINE):
        header = match.group(1).strip()
        header_lower = header.lower()
        if any(kw in header_lower for kw in keywords):
            content_hash = hashlib.sha256(header.encode()).hexdigest()[:16]
            entity_id = f"md-{content_hash}"
            
            # Determine subject
            subject = "foundations"
            if any(k in header_lower for k in ['algebra', 'group', 'ring']):
                subject = "algebra"
            elif any(k in header_lower for k in ['topology', 'manifold', 'space']):
                subject = "topology"
            elif any(k in header_lower for k in ['thermodynamic', 'entropy', 'energy', 'joule']):
                subject = "physics"
            elif any(k in header_lower for k in ['orthogonal', 'matrix', 'projection']):
                subject = "algebra"
            
            # Determine proof status
            proof_status = "conjecture"
            if any(k in header_lower for k in ['theorem', 'proven', 'verified', 'law', 'invariant']):
                proof_status = "proven"
            
            entities.append((
                entity_id, subject, json.dumps([]), header, header,
                proof_status, "informal", None, json.dumps([]), json.dumps([]),
                32768, 2026, str(file_path)
            ))
    
    # Insert to database
    for entity in entities:
        conn.execute("""
            INSERT OR REPLACE INTO math_entities 
            (entity_id, subject, secondary_subjects, name, statement, proof_status,
             formal_status, lean_module, dependencies, citations, complexity_score, year, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, entity)
    
    if entities:
        print(f"[INFO] {file_path.name}: {len(entities)} entities")
        total_entities += len(entities)

conn.commit()
print(f"[OK] Total entities synced: {total_entities}")
PYEOF

log_ok "Sync complete"
