#!/usr/bin/env python3
import json
import sqlite3
import os
import datetime

DB_PATH = "/home/allaun/Documents/Research Stack/data/substrate_index.db"
JSON_PATH = "/home/allaun/Documents/Research Stack/linear_full_dump.json"

def ingest():
    if not os.path.exists(JSON_PATH):
        print(f"Error: {JSON_PATH} not found.")
        return

    with open(JSON_PATH, 'r') as f:
        data = json.load(f)

    issues = data.get("issues", [])
    print(f"Loaded {len(issues)} issues from dump.")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    count = 0
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for issue in issues:
        identifier = issue.get("identifier")
        pkg_id = f"linear/{identifier}"
        title = issue.get("title", "")
        description = issue.get("description", "")
        full_text = f"{title}\n\n{description}"
        url = issue.get("url", "")
        labels_data = issue.get("labels", {})
        if isinstance(labels_data, list): # fallback
             tags_list = labels_data
        else:
             tags_list = labels_data.get("nodes", [])
        tags = json.dumps([l.get("name") if isinstance(l, dict) else l for l in tags_list])
        
        # Mapping to packages table schema
        cur.execute("""
            INSERT OR REPLACE INTO packages (
                pkg, version, domain, tier, archetype, 
                tags, description, session_id, indexed_utc, model_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pkg_id, 
            "1.0.0", 
            "LINEAR", 
            "INTENT", 
            "issue", 
            tags, 
            full_text, 
            url, 
            now,
            "INGESTED"
        ))
        count += 1

    conn.commit()
    conn.close()
    print(f"Successfully indexed {count} issues into {DB_PATH}")

if __name__ == "__main__":
    ingest()
