#!/usr/bin/env python3
"""export_linear_from_rds.py - Exports LINEAR domain records from RDS to JSON.
"""

import json
import os
import sys
from pathlib import Path

# Add infra and scripts folders to import path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "4-Infrastructure" / "infra"))
sys.path.append(str(Path(__file__).resolve().parent))

from import_dumps_to_rds import get_rds_password

def main():
    print("[+] Fetching RDS credentials...")
    password = get_rds_password()
    if not password:
        print("[-] Failed to retrieve RDS password or IAM token. Exiting.")
        sys.exit(1)

    host = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
    port = int(os.environ.get("RDS_PORT", "5432"))
    user = os.environ.get("RDS_USER", "postgres")
    dbname = os.environ.get("RDS_DB", "postgres")

    try:
        import psycopg2
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            sslmode="require"
        )
        cur = conn.cursor()
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        sys.exit(1)

    print("[+] Querying all LINEAR domain packages from RDS...")
    try:
        cur.execute("""
            SELECT pkg, version, domain, tier, archetype, description, tags, source, indexed_utc
            FROM ene.packages
            WHERE domain = 'LINEAR'
            ORDER BY indexed_utc DESC
        """)
        rows = cur.fetchall()
    except Exception as e:
        print(f"[-] Failed to execute query: {e}")
        sys.exit(1)

    records = []
    for r in rows:
        records.append({
            "pkg": r[0],
            "version": r[1],
            "domain": r[2],
            "tier": r[3],
            "archetype": r[4],
            "description": r[5],
            "tags": r[6],
            "source": r[7],
            "indexed_utc": r[8]
        })

    out_file = Path(__file__).resolve().parent / "linear_export.json"
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, default=str)
        print(f"[+] Successfully exported {len(records)} Linear records to {out_file}")
    except Exception as e:
        print(f"[-] Failed to write JSON output: {e}")

if __name__ == "__main__":
    main()
