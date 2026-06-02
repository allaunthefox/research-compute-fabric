#!/usr/bin/env python3
import json
import sqlite3
import datetime

from shim.utils.datetime_utils import utc_now

DB_PATH = "/home/allaun/Documents/Research Stack/data/substrate_index.db"
NOTION_DUMP = "/home/allaun/Documents/Research Stack/notion_full_dump.json"

def ingest_notion():
    print(f"🚀 Ingesting Notion Research into Ene substrate...")
    
    with open(NOTION_DUMP, 'r') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Ensure domain exists (no specific action needed other than inserting)
    
    success_count = 0
    for page in data.get('pages', []):
        props = page.get('properties', {})
        
        # Extract ID (Notion UUID)
        page_id = page.get('id')
        
        # Extract Package Path
        pkg_list = props.get('Package', {}).get('rich_text', [])
        pkg_path = pkg_list[0].get('text', {}).get('content', f"notion/{page_id}") if pkg_list else f"notion/{page_id}"
        
        # Extract Title
        title_list = props.get('Name', {}).get('title', []) or props.get('title', {}).get('title', []) 
        title = title_list[0].get('text', {}).get('content', "Untitled Notion Page") if title_list else "Untitled Notion Page"
        
        # Build tags from properties
        tags = []
        for prop_name, prop_val in props.items():
            if prop_val.get('type') == 'select' and prop_val.get('select'):
                tags.append(prop_val['select']['name'])
        
        # Substrate Mapping
        pkg_entry = {
            "pkg": pkg_path,
            "version": page.get('last_edited_time', "v1"),
            "layer": "RESEARCH",
            "domain": "NOTION",
            "tier": "RESEARCH",
            "description": title,
            "tags": json.dumps(tags),
            "indexed_utc": utc_now() + "Z",
            "notion_id": page_id
        }
        
        cur.execute("""
            INSERT OR REPLACE INTO packages 
            (pkg, version, layer, domain, tier, description, tags, indexed_utc, notion_id, quality_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pkg_entry['pkg'], pkg_entry['version'], pkg_entry['layer'], 
            pkg_entry['domain'], pkg_entry['tier'], pkg_entry['description'],
            pkg_entry['tags'], pkg_entry['indexed_utc'], pkg_entry['notion_id'],
            "STABLE"
        ))
        
        success_count += 1

    conn.commit()
    
    # Refresh FTS
    print(f"🛡️ Refreshing FTS for NOTION domain...")
    cur.execute("DELETE FROM packages_fts WHERE domain = 'NOTION'")
    cur.execute("""
        INSERT INTO packages_fts(pkg, version, tier, domain, description, tags)
        SELECT pkg, version, tier, domain, description, tags 
        FROM packages WHERE domain = 'NOTION'
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Successfully indexed {success_count} Notion pages into the Ene substrate.")

if __name__ == "__main__":
    ingest_notion()
