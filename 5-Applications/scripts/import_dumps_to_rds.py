#!/usr/bin/env python3
"""import_dumps_to_rds.py - Ingestion pipeline from crawled JSON dumps to RDS.

Imports Notion database pages into ene.wiki_pages/revisions/links/categories
and Linear issues into ene.packages.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add infra folder to import path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "4-Infrastructure" / "infra"))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "4-Infrastructure"))

def get_rds_password():
    password = os.environ.get("RDS_IAM_TOKEN") or os.environ.get("RDS_PASSWORD")
    if password:
        return password

    # Fallback to subprocess call to aws cli
    try:
        import subprocess
        host = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
        user = os.environ.get("RDS_USER", "postgres")
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        cmd = [
            "aws", "rds", "generate-db-auth-token",
            "--hostname", host,
            "--port", "5432",
            "--username", user,
            "--region", region
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        token = res.stdout.strip()
        if token:
            return token
    except Exception as e:
        print(f"AWS CLI token generation failed: {e}")
    
    return ""

def import_notion(password: str):
    notion_file = Path(__file__).resolve().parent / "notion_full_dump.json"
    if not notion_file.exists():
        print("[-] notion_full_dump.json not found, skipping Notion import.")
        return

    print("[+] Loading notion_full_dump.json...")
    with open(notion_file, "r") as f:
        dump_data = json.load(f)

    pages = dump_data.get("pages", [])
    print(f"[+] Found {len(pages)} pages to import.")

    # Override password environment variable for ENEWikiLayer
    os.environ["RDS_PASSWORD"] = password

    try:
        from ene_rds_wiki_layer import ENERDSWikiLayer
        wiki = ENERDSWikiLayer()
    except Exception as e:
        print(f"[-] Failed to initialize ENERDSWikiLayer: {e}")
        return

    imported_count = 0
    for page in pages:
        properties = page.get("properties", {})
        title = "Untitled"
        for prop_name in ["Name", "title", "Title"]:
            prop = properties.get(prop_name, {})
            if prop and prop.get("title"):
                title_list = prop["title"]
                if title_list and isinstance(title_list, list):
                    title = title_list[0].get("plain_text", "Untitled")
                    break
        
        content = page.get("_content", "") or ""
        author = "notion_importer"
        
        try:
            print(f"    -> Importing page: {title}")
            wiki.put_page(title=title, text=content, author=author, summary="Notion Full Crawl Ingestion")
            imported_count += 1
        except Exception as e:
            print(f"    [!] Error importing page '{title}': {e}")

    print(f"[+] Notion import complete. Successfully imported {imported_count}/{len(pages)} pages.")

def import_linear(password: str):
    linear_file = Path(__file__).resolve().parent / "linear_full_dump.json"
    if not linear_file.exists():
        print("[-] linear_full_dump.json not found, skipping Linear import.")
        return

    print("[+] Loading linear_full_dump.json...")
    with open(linear_file, "r") as f:
        dump_data = json.load(f)

    issues = dump_data.get("issues", [])
    print(f"[+] Found {len(issues)} issues to import.")

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
        return

    imported_count = 0
    for issue in issues:
        identifier = issue.get("identifier")
        if not identifier:
            continue

        pkg_id = f"linear/{identifier}"
        title = issue.get("title", "")
        description = issue.get("description", "")
        full_text = f"{title}\n\n{description}" if description else title
        url = issue.get("url", "")
        
        # Extract labels
        labels_nodes = issue.get("labels", {}).get("nodes", [])
        labels_list = [l.get("name") for l in labels_nodes if l.get("name")]
        tags_json = json.dumps(labels_list)
        
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            cur.execute("""
                INSERT INTO ene.packages (
                    pkg, version, domain, tier, archetype, 
                    tags, description, source, indexed_utc
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pkg) DO UPDATE SET
                    description = EXCLUDED.description,
                    tags = EXCLUDED.tags,
                    source = EXCLUDED.source,
                    indexed_utc = EXCLUDED.indexed_utc
            """, (
                pkg_id,
                "1.0.0",
                "LINEAR",
                "INTENT",
                "issue",
                tags_json,
                full_text,
                url,
                now_iso
            ))
            imported_count += 1
        except Exception as e:
            print(f"    [!] Error importing issue '{pkg_id}': {e}")

    try:
        conn.commit()
        conn.close()
        print(f"[+] Linear import complete. Successfully imported {imported_count}/{len(issues)} issues.")
    except Exception as e:
        print(f"[-] Database commit failed: {e}")

def main():
    print("=== ENE RDS Ingestion Pipeline ===")
    password = get_rds_password()
    if not password:
        print("[-] Failed to retrieve RDS password or IAM token. Exiting.")
        sys.exit(1)

    import_notion(password)
    import_linear(password)
    print("=== Pipeline Execution Finished ===")

if __name__ == "__main__":
    main()
