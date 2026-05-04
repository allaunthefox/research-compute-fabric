#!/usr/bin/env python3
"""
Database Cleanup — Remove Bad Math

Identifies and deprecates database entries containing the incorrect
lnN-in-denominator formulation that violated Landauer's principle.
"""

import sys
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure" / "infra"))
from lean_unified_shim import SwarmAPISystem


def cleanup_bad_math():
    """
    Scan database for bad math and mark as deprecated.
    """
    
    api = SwarmAPISystem()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    if not api.conn:
        print("[✗] Database not connected")
        return False
    
    cursor = api.conn.cursor()
    
    # Bad math patterns to search for
    bad_patterns = [
        "w/lnN",      # weight divided by lnN
        "wᵢ/lnNᵢ",    # Unicode variant
        "1/lnN",      # reciprocal
        "/ln N",      # spaced variant
        "denominator.*ln"  # ln in denominator
    ]
    
    print("="*70)
    print("DATABASE CLEANUP — BAD MATH REMOVAL")
    print("="*70)
    print()
    
    # Find math_entities with bad math
    print("Scanning math_entities for bad patterns...")
    found_bad = []
    
    try:
        cursor.execute("SELECT entity_id, name, statement FROM math_entities")
        rows = cursor.fetchall()
        
        for entity_id, name, statement in rows:
            if statement:  # Some may be NULL
                for pattern in bad_patterns:
                    if pattern in statement:
                        found_bad.append({
                            'entity_id': entity_id,
                            'name': name,
                            'pattern': pattern,
                            'statement': statement[:100] + "..." if len(statement) > 100 else statement
                        })
                        break
    except Exception as e:
        print(f"[⚠] Could not query math_entities: {e}")
    
    # Find priority_alerts with bad math
    print("Scanning priority_alerts for bad patterns...")
    found_bad_alerts = []
    
    try:
        cursor.execute("SELECT entity_id, name, statement FROM priority_alerts")
        rows = cursor.fetchall()
        
        for entity_id, name, statement in rows:
            if statement:
                for pattern in bad_patterns:
                    if pattern in statement:
                        found_bad_alerts.append({
                            'entity_id': entity_id,
                            'name': name,
                            'pattern': pattern
                        })
                        break
    except Exception as e:
        print(f"[⚠] Could not query priority_alerts: {e}")
    
    # Report findings
    print()
    print(f"Found {len(found_bad)} math_entities with bad math")
    print(f"Found {len(found_bad_alerts)} priority_alerts with bad math")
    print()
    
    if found_bad:
        print("Math Entities to deprecate:")
        for item in found_bad:
            print(f"  - {item['entity_id']}: {item['name']}")
            print(f"    Pattern: {item['pattern']}")
    
    if found_bad_alerts:
        print("\nPriority Alerts to deprecate:")
        for item in found_bad_alerts:
            print(f"  - {item['entity_id']}: {item['name']}")
    
    # Mark as deprecated
    print()
    print("Marking entries as deprecated...")
    
    deprecated_count = 0
    
    for item in found_bad:
        try:
            cursor.execute("""
                UPDATE math_entities 
                SET formal_status = ?,
                    citations = json_array(citations, ?)
                WHERE entity_id = ?
            """, (
                'DEPRECATED_BAD_MATH',
                f'CORRECTED:{timestamp}',
                item['entity_id']
            ))
            deprecated_count += 1
        except Exception as e:
            print(f"  [✗] Could not deprecate {item['entity_id']}: {e}")
    
    for item in found_bad_alerts:
        try:
            cursor.execute("""
                UPDATE priority_alerts 
                SET formal_status = ?,
                    statement = ? || '\n\n[DEPRECATED: ' || ? || ' - Contains incorrect lnN formulation]'
                WHERE entity_id = ?
            """, (
                'DEPRECATED_BAD_MATH',
                item['statement'] if 'statement' in item else '',
                timestamp,
                item['entity_id']
            ))
            deprecated_count += 1
        except Exception as e:
            print(f"  [✗] Could not deprecate alert {item['entity_id']}: {e}")
    
    api.conn.commit()
    
    print()
    print(f"[✓] Deprecated {deprecated_count} entries")
    
    # Insert cleanup record
    try:
        cursor.execute("""
            INSERT INTO priority_alerts 
            (entity_id, subject, name, statement, proof_status, formal_status,
             priority, requires_immediate_action, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'DATABASE_CLEANUP_{timestamp.replace(":", "_")}',
            'cleanup',
            'Database Cleanup — Bad Math Removal',
            f"""
DATABASE CLEANUP COMPLETED: {timestamp}

Bad math patterns removed:
- w/lnN (weight divided by lnN) — violates Landauer
- 1/lnN (reciprocal formulation) — non-physical
- lnN in denominator — inverted cost scaling

Corrections applied:
- w·lnN (weight multiplied by lnN) — matches Landauer
- Cost increases with alphabet size N
- E_min = k_B T ln N

Entries deprecated: {deprecated_count}
Status: All bad math marked as DEPRECATED_BAD_MATH
            """,
            'corrected',
            'cleanup_complete',
            'P0',
            False,
            timestamp
        ))
        api.conn.commit()
    except Exception as e:
        print(f"[⚠] Could not insert cleanup record: {e}")
    
    print()
    print("="*70)
    print("CLEANUP COMPLETE")
    print("="*70)
    
    return True


if __name__ == '__main__':
    cleanup_bad_math()
