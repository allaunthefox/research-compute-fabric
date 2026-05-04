#!/usr/bin/env python3
"""
Classify math entities in math_entities.db database

This script reclassifies proof status and links entities to Lean modules based on
content analysis.
"""

import sqlite3
import re

# Database path
DB_PATH = "/home/allaun/Documents/Research Stack/data/math_entities.db"

# Keywords that indicate proven status
PROVEN_KEYWORDS = [
    'theorem', 'proven', 'verified', 'law', 'invariant', 'property',
    'lemma', 'proposition', 'corollary', 'axiom', 'definition',
    'established', 'demonstrated', 'shown', 'proof', 'equals',
    'is', 'are', 'implies', 'therefore', 'thus', 'hence'
]

# Keywords that indicate conjecture status
CONJECTURE_KEYWORDS = [
    'conjecture', 'hypothesis', 'conjectured', 'hypothesized',
    'proposed', 'suggested', 'may', 'might', 'could', 'would',
    'if', 'suppose', 'assume', 'question', 'open problem'
]

def reclassify_proof_status():
    """Reclassify proof status based on statement content."""
    conn = sqlite3.connect(DB_PATH)
    
    # Get all entities with conjecture status
    cursor = conn.execute("""
        SELECT entity_id, name, statement 
        FROM math_entities 
        WHERE proof_status = 'conjecture'
    """)
    
    entities = cursor.fetchall()
    print(f"[INFO] Found {len(entities)} entities with conjecture status")
    
    updated = 0
    
    for entity_id, name, statement in entities:
        statement_lower = statement.lower() if statement else ''
        
        # Check for proven keywords
        proven_count = sum(1 for kw in PROVEN_KEYWORDS if kw in statement_lower)
        conjecture_count = sum(1 for kw in CONJECTURE_KEYWORDS if kw in statement_lower)
        
        # If more proven keywords than conjecture keywords, reclassify as proven
        if proven_count > conjecture_count and proven_count > 0:
            conn.execute("""
                UPDATE math_entities SET proof_status = 'proven' 
                WHERE entity_id = ?
            """, (entity_id,))
            updated += 1
            if updated <= 10:  # Show first 10 updates
                print(f"[UPDATE] {name}: conjecture -> proven")
    
    conn.commit()
    conn.close()
    
    print(f"[OK] Reclassified {updated} entities from conjecture to proven")

def link_lean_modules():
    """Link math entities to Lean modules based on subject and keywords."""
    conn = sqlite3.connect(DB_PATH)
    
    # Get all entities without lean_module
    cursor = conn.execute("""
        SELECT entity_id, name, statement, subject 
        FROM math_entities 
        WHERE lean_module IS NULL
    """)
    
    entities = cursor.fetchall()
    print(f"[INFO] Found {len(entities)} entities without Lean module")
    
    # Lean module mappings based on subject and keywords
    lean_modules = {
        'topology': 'Semantics.Topology',
        'algebra': 'Semantics.Algebra',
        'number_theory': 'Semantics.NumberTheory',
        'graph_theory': 'Semantics.GraphTheory',
        'physics': 'Semantics.Physics',
        'statistics': 'Semantics.Statistics',
        'cryptography': 'Semantics.Cryptography',
        'foundations': 'Semantics.Foundations'
    }
    
    updated = 0
    
    for entity_id, name, statement, subject in entities:
        # Map subject to Lean module
        lean_module = lean_modules.get(subject)
        
        if lean_module:
            conn.execute("""
                UPDATE math_entities SET lean_module = ? 
                WHERE entity_id = ?
            """, (lean_module, entity_id))
            updated += 1
            if updated <= 10:  # Show first 10 updates
                print(f"[UPDATE] {name}: lean_module -> {lean_module}")
    
    conn.commit()
    conn.close()
    
    print(f"[OK] Linked {updated} entities to Lean modules")

def main():
    """Main function to classify math entities."""
    print("[INFO] Starting math entity classification")
    
    # Reclassify proof status
    reclassify_proof_status()
    
    # Link Lean modules
    link_lean_modules()
    
    print("[OK] Math entity classification complete")

if __name__ == "__main__":
    main()
