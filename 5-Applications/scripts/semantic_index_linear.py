#!/usr/bin/env python3
import sqlite3
import json
import re
import datetime

from shim.utils.datetime_utils import utc_now

DB_PATH = "/home/allaun/Documents/Research Stack/data/substrate_index.db"

def semantic_audit(pkg_id, description):
    """
    Analyzes raw Linear issue description to extract Sovereign metadata.
    """
    # 1. Detect Quality Markers
    quality_status = "STABLE"
    if "Quality: UNAUDITED" in description:
        quality_status = "INDEXED" # Moved from UNAUDITED to INDEXED
    
    # 2. Extract ENE Package
    ene_match = re.search(r"\*\*ENE Package:\*\* `([^`]+)`", description)
    ene_pkg = ene_match.group(1) if ene_match else None

    # 3. Extract Attestor
    attestor_match = re.search(r"\*\*Attestor:\*\* ([^\n]+)", description)
    attestor = attestor_match.group(1).strip() if attestor_match else "SYSTEM"

    # 4. Extract Status
    status_match = re.search(r"\*\*Status:\*\* ([^\n]+)", description)
    status = status_match.group(1).strip() if status_match else "UNKNOWN"

    # 5. Build Concept Anchor
    # Default to INTENT domain for Linear
    concept_name = pkg_id.replace("linear/", "").lower().replace("-", "_")
    anchor = {
        "domain": "INTENT",
        "concept": concept_name,
        "resolution": "STABLE" if "COMPLETED" in status.upper() or "APPROVED" in status.upper() else "FORMING"
    }

    # 6. Clean Description (strip boilerplate if possible)
    clean_desc = description.replace("Quality: UNAUDITED\n\n", "")

    return {
        "quality_status": quality_status,
        "concept_anchor": json.dumps(anchor),
        "description": clean_desc,
        "indexed_utc": utc_now() + "Z"
    }

def run_indexing():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("[🔍 SEMANTIC INDEXER] Starting Linear Audit Pass...")
    
    # Fetch all Linear packages
    cur.execute("SELECT pkg, description, version FROM packages WHERE domain = 'LINEAR'")
    rows = cur.fetchall()
    
    count = 0
    for pkg, desc, ver in rows:
        meta = semantic_audit(pkg, desc or "")
        
        # Update the package entry
        cur.execute("""
            UPDATE packages 
            SET quality_status = ?, 
                concept_anchor = ?, 
                description = ?, 
                indexed_utc = ?
            WHERE pkg = ? AND version = ?
        """, (meta['quality_status'], meta['concept_anchor'], meta['description'], meta['indexed_utc'], pkg, ver))
        
        # We also need to update the FTS table manually since triggers might not handle UPDATE in a way that respects the new description immediately or may be complex.
        # Actually, standard AFTER UPDATE triggers would work if they existed. 
        # Looking at previous schema, there are only INSERT/DELETE triggers.
        # Let's check for an UPDATE trigger.
        
        count += 1
        if count % 100 == 0:
            print(f"  Processed {count}/{len(rows)} nodes...")

    conn.commit()
    
    # Manually rebuild FTS index to ensure descriptions are clean and quality status is reflected
    print("[🛡️ FTS REBUILD] Synchronizing intentional manifold...")
    cur.execute("DELETE FROM packages_fts WHERE domain = 'LINEAR'")
    cur.execute("""
        INSERT INTO packages_fts(pkg, version, tier, domain, module, archetype, description, tags)
        SELECT pkg, version, tier, domain, module, archetype, description, tags 
        FROM packages WHERE domain = 'LINEAR'
    """)
    
    conn.commit()
    conn.close()
    print(f"[✅ INDEXING COMPLETE] {count} Linear nodes semantically anchored.")

if __name__ == "__main__":
    run_indexing()
