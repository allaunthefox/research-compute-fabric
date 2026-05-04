#!/usr/bin/env python3
"""
Extract mathematical content from Linear and Notion dumps and add to math_entities.db

This script parses the JSON dumps from Linear and Notion, identifies mathematical
content (equations, theorems, proofs, etc.), and inserts them into the math_entities.db database.
"""

import json
import sqlite3
import re
import hashlib
from pathlib import Path

# Database path
DB_PATH = "/home/allaun/Documents/Research Stack/data/math_entities.db"

# Keywords that indicate mathematical content
MATH_KEYWORDS = [
    'equation', 'theorem', 'lemma', 'proof', 'conjecture', 'invariant', 'formula',
    'algorithm', 'complexity', 'entropy', 'topology', 'manifold', 'geometry',
    'algebra', 'group', 'ring', 'field', 'vector', 'matrix', 'eigenvalue',
    'derivative', 'integral', 'differential', 'calculus', 'optimization',
    'probability', 'statistics', 'random', 'stochastic', 'graph', 'network',
    'metric', 'norm', 'space', 'dimension', 'coordinate', 'transform',
    'convolution', 'fourier', 'wavelet', 'signal', 'filter', 'crc',
    'hash', 'cryptographic', 'golden', 'ratio', 'phi', 'pi', 'phonon',
    'quantum', 'classical', 'mechanics', 'dynamics', 'kinematics',
    'thermodynamic', 'energy', 'entropy', 'heat', 'temperature', 'joule',
    'binding', 'bind', 'coupling', 'interaction', 'force', 'potential',
    'gradient', 'divergence', 'curl', 'laplacian', 'tensor', 'spinor',
    'quaternion', 'octonion', 'group', 'symmetry', 'conservation', 'law'
]

# Mathematical patterns
MATH_PATTERNS = [
    r'\$[^$]+\$',  # LaTeX math: $...$
    r'\$\$[^$]+\$\$',  # LaTeX display math: $$...$$
    r'\\[a-zA-Z]+\{[^}]+\}',  # LaTeX commands
    r'[A-Za-z]+\s*=\s*[^=\n]+',  # Simple equations: x = y
    r'∫[^∞]+dx',  # Integrals
    r'∑[^∑]+',  # Summations
    r'∏[^∏]+',  # Products
    r'∂[^∂]+',  # Partial derivatives
    r'∇[^∇]+',  # Gradients
    r'φ\s*[=≈≠<>]',  # Golden ratio equations
    r'π\s*[=≈≠<>]',  # Pi equations
    r'[α-ω]\s*[=≈≠<>]',  # Greek letter equations
]

def extract_math_from_text(text, source_id, source_type):
    """Extract mathematical entities from text."""
    entities = []
    
    if not text:
        return entities
    
    text_lower = text.lower()
    
    # Check for mathematical keywords
    has_math_keywords = any(kw in text_lower for kw in MATH_KEYWORDS)
    
    # Check for mathematical patterns
    has_math_patterns = any(re.search(pattern, text, re.IGNORECASE) for pattern in MATH_PATTERNS)
    
    if not (has_math_keywords or has_math_patterns):
        return entities
    
    # Extract potential math statements
    # Split by common delimiters
    statements = re.split(r'[.\n;]+', text)
    
    for stmt in statements:
        stmt = stmt.strip()
        if len(stmt) < 10:  # Skip very short statements
            continue
        
        stmt_lower = stmt.lower()
        
        # Check if this statement contains math
        if not any(kw in stmt_lower for kw in MATH_KEYWORDS):
            # Check for math patterns as fallback
            if not any(re.search(pattern, stmt, re.IGNORECASE) for pattern in MATH_PATTERNS):
                continue
        
        # Create entity
        content_hash = hashlib.sha256(stmt.encode()).hexdigest()[:16]
        entity_id = f"{source_type}-{content_hash}"
        
        # Determine subject
        subject = "foundations"
        if any(k in stmt_lower for k in ['algebra', 'group', 'ring', 'matrix', 'vector']):
            subject = "algebra"
        elif any(k in stmt_lower for k in ['topology', 'manifold', 'space', 'geometry']):
            subject = "topology"
        elif any(k in stmt_lower for k in ['thermodynamic', 'entropy', 'energy', 'joule', 'heat']):
            subject = "physics"
        elif any(k in stmt_lower for k in ['probability', 'statistics', 'random', 'stochastic']):
            subject = "statistics"
        elif any(k in stmt_lower for k in ['graph', 'network', 'tree', 'node']):
            subject = "graph_theory"
        elif any(k in stmt_lower for k in ['crc', 'hash', 'cryptographic', 'encryption']):
            subject = "cryptography"
        elif any(k in stmt_lower for k in ['golden', 'ratio', 'phi']):
            subject = "number_theory"
        
        # Determine proof status
        proof_status = "conjecture"
        if any(k in stmt_lower for k in ['theorem', 'proven', 'verified', 'law', 'invariant', 'property']):
            proof_status = "proven"
        elif any(k in stmt_lower for k in ['lemma', 'proposition']):
            proof_status = "proven"
        
        entities.append({
            'entity_id': entity_id,
            'subject': subject,
            'secondary_subjects': json.dumps([]),
            'name': stmt[:100],  # First 100 chars as name
            'statement': stmt,
            'proof_status': proof_status,
            'formal_status': 'informal',
            'lean_module': None,
            'dependencies': json.dumps([]),
            'citations': json.dumps([]),
            'complexity_score': 32768,  # Default Q16_16 value
            'year': 2026,
            'source_file': f"{source_type}:{source_id}"
        })
    
    return entities

def parse_linear_dump():
    """Parse Linear dump for mathematical content."""
    dump_file = Path("/home/allaun/Documents/Research Stack/linear_full_dump.json")
    
    if not dump_file.exists():
        print(f"[WARN] Linear dump not found: {dump_file}")
        return []
    
    print(f"[INFO] Parsing Linear dump: {dump_file}")
    
    with open(dump_file, 'r') as f:
        data = json.load(f)
    
    entities = []
    
    for issue in data.get('issues', []):
        issue_id = issue.get('identifier', issue.get('id', ''))
        title = issue.get('title', '')
        description = issue.get('description', '')
        
        # Combine title and description for analysis
        text = f"{title}\n{description}"
        
        # Extract math from this issue
        issue_entities = extract_math_from_text(text, issue_id, 'linear')
        entities.extend(issue_entities)
    
    print(f"[INFO] Found {len(entities)} math entities in Linear dump")
    return entities

def parse_notion_dump():
    """Parse Notion dump for mathematical content."""
    dump_file = Path("/home/allaun/Documents/Research Stack/notion_full_dump.json")
    
    if not dump_file.exists():
        print(f"[WARN] Notion dump not found: {dump_file}")
        return []
    
    print(f"[INFO] Parsing Notion dump: {dump_file}")
    
    with open(dump_file, 'r') as f:
        data = json.load(f)
    
    entities = []
    
    for page in data.get('pages', []):
        page_id = page.get('id', '')
        title = page.get('properties', {}).get('Name', {}).get('title', [{}])[0].get('plain_text', '')
        content = page.get('_content', '')
        
        # Combine title and content for analysis
        text = f"{title}\n{content}"
        
        # Extract math from this page
        page_entities = extract_math_from_text(text, page_id, 'notion')
        entities.extend(page_entities)
    
    print(f"[INFO] Found {len(entities)} math entities in Notion dump")
    return entities

def insert_entities_to_db(entities):
    """Insert entities into math_entities.db database."""
    if not entities:
        print("[INFO] No entities to insert")
        return
    
    print(f"[INFO] Inserting {len(entities)} entities into database")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Ensure schema exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS math_entities (
            entity_id TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            secondary_subjects TEXT,
            name TEXT NOT NULL,
            statement TEXT,
            proof_status TEXT NOT NULL,
            formal_status TEXT NOT NULL,
            lean_module TEXT,
            dependencies TEXT,
            citations TEXT,
            complexity_score INTEGER,
            year INTEGER,
            source_file TEXT,
            last_synced TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Ensure sync_log table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,
            entity_id TEXT,
            source_file TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )
    """)
    
    inserted = 0
    updated = 0
    skipped = 0
    
    for entity in entities:
        try:
            # Check if entity already exists
            cursor = conn.execute("SELECT entity_id FROM math_entities WHERE entity_id = ?", (entity['entity_id'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                conn.execute("""
                    UPDATE math_entities SET
                        subject = ?, secondary_subjects = ?, name = ?, statement = ?,
                        proof_status = ?, formal_status = ?, lean_module = ?,
                        dependencies = ?, citations = ?, complexity_score = ?,
                        year = ?, source_file = ?, last_synced = CURRENT_TIMESTAMP
                    WHERE entity_id = ?
                """, (
                    entity['subject'], entity['secondary_subjects'], entity['name'], entity['statement'],
                    entity['proof_status'], entity['formal_status'], entity['lean_module'],
                    entity['dependencies'], entity['citations'], entity['complexity_score'],
                    entity['year'], entity['source_file'], entity['entity_id']
                ))
                updated += 1
                
                # Log update
                conn.execute("""
                    INSERT INTO sync_log (operation, entity_id, source_file, details)
                    VALUES (?, ?, ?, ?)
                """, ('UPDATE', entity['entity_id'], entity['source_file'], 'Updated from dump'))
            else:
                # Insert new
                conn.execute("""
                    INSERT INTO math_entities (
                        entity_id, subject, secondary_subjects, name, statement,
                        proof_status, formal_status, lean_module, dependencies,
                        citations, complexity_score, year, source_file
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity['entity_id'], entity['subject'], entity['secondary_subjects'], entity['name'], entity['statement'],
                    entity['proof_status'], entity['formal_status'], entity['lean_module'],
                    entity['dependencies'], entity['citations'], entity['complexity_score'],
                    entity['year'], entity['source_file']
                ))
                inserted += 1
                
                # Log insert
                conn.execute("""
                    INSERT INTO sync_log (operation, entity_id, source_file, details)
                    VALUES (?, ?, ?, ?)
                """, ('INSERT', entity['entity_id'], entity['source_file'], 'Inserted from dump'))
                
        except sqlite3.IntegrityError:
            skipped += 1
        except Exception as e:
            print(f"[ERROR] Failed to insert entity {entity['entity_id']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"[OK] Inserted: {inserted}, Updated: {updated}, Skipped: {skipped}")

def main():
    """Main function to extract math from dumps and add to database."""
    print("[INFO] Starting math extraction from Linear and Notion dumps")
    
    # Parse Linear dump
    linear_entities = parse_linear_dump()
    
    # Parse Notion dump
    notion_entities = parse_notion_dump()
    
    # Combine all entities
    all_entities = linear_entities + notion_entities
    
    # Remove duplicates based on entity_id
    unique_entities = {}
    for entity in all_entities:
        unique_entities[entity['entity_id']] = entity
    
    all_entities = list(unique_entities.values())
    
    print(f"[INFO] Total unique entities found: {len(all_entities)}")
    
    # Insert into database
    insert_entities_to_db(all_entities)
    
    print("[OK] Math extraction complete")

if __name__ == "__main__":
    main()
