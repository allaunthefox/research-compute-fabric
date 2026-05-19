#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "boto3",
#   "psycopg2-binary",
#   "requests",
#   "python-dotenv",
# ]
# ///
"""
Notion + Linear → Aurora PostgreSQL ingestion shim.

Notion pages land in knowledge.documents (source='notion').
Linear issues land in knowledge.linear_issues (upserted on issue_id).
Each run is recorded in ingestion.receipts.

Credentials (never hardcoded):
  NOTION_TOKEN       – Notion integration token
  LINEAR_API_KEY     – Linear personal API key
  RDS_HOST           – Aurora endpoint (default: database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com)
  RDS_USER           – DB user (default: postgres)
  RDS_DBNAME         – DB name (default: postgres)
  RDS_IAM            – set to "1" to use IAM auth token (default), else use RDS_PASSWORD
  RDS_PASSWORD       – plain password if RDS_IAM != "1"
  AWS_REGION         – (default: us-east-1)
"""

import hashlib
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone

import boto3
import psycopg2
import psycopg2.extras
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("notion_linear_rds_ingest")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
RDS_HOST    = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
RDS_PORT    = int(os.environ.get("RDS_PORT", "5432"))
RDS_USER    = os.environ.get("RDS_USER", "postgres")
RDS_DBNAME  = os.environ.get("RDS_DBNAME", "postgres")
RDS_IAM     = os.environ.get("RDS_IAM", "1") == "1"
RDS_PW      = os.environ.get("RDS_PASSWORD", "")
AWS_REGION  = os.environ.get("AWS_REGION", "us-east-1")

NOTION_TOKEN   = os.environ.get("NOTION_TOKEN", "")
LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY", "")

NOTION_API     = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
LINEAR_API     = "https://api.linear.app/graphql"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def get_db_password() -> str:
    if RDS_IAM:
        client = boto3.client("rds", region_name=AWS_REGION)
        return client.generate_db_auth_token(
            DBHostname=RDS_HOST, Port=RDS_PORT, DBUsername=RDS_USER, Region=AWS_REGION
        )
    return RDS_PW


def connect() -> psycopg2.extensions.connection:
    pw = get_db_password()
    return psycopg2.connect(
        host=RDS_HOST, port=RDS_PORT, user=RDS_USER,
        password=pw, dbname=RDS_DBNAME, sslmode="require"
    )


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS knowledge.linear_issues (
                issue_id        text        PRIMARY KEY,
                identifier      text        NOT NULL,
                title           text        NOT NULL,
                state           text,
                priority        integer,
                labels          jsonb       NOT NULL DEFAULT '[]',
                url             text,
                description     text,
                team_name       text,
                project_name    text,
                assignee        text,
                creator         text,
                created_at      timestamptz,
                updated_at      timestamptz,
                ingested_at     timestamptz NOT NULL DEFAULT now(),
                content_hash    text        NOT NULL
            );
            CREATE INDEX IF NOT EXISTS linear_issues_identifier_idx
                ON knowledge.linear_issues (identifier);
            CREATE INDEX IF NOT EXISTS linear_issues_state_idx
                ON knowledge.linear_issues (state);
        """)
        conn.commit()
    log.info("Schema ready")


# ---------------------------------------------------------------------------
# Notion helpers
# ---------------------------------------------------------------------------
def notion_headers() -> dict:
    if not NOTION_TOKEN:
        raise RuntimeError("NOTION_TOKEN not set")
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def notion_search_all(page_size: int = 100) -> list[dict]:
    """Return all pages (not databases) from the workspace."""
    pages, cursor = [], None
    while True:
        body: dict = {"filter": {"value": "page", "property": "object"}, "page_size": page_size}
        if cursor:
            body["start_cursor"] = cursor
        r = requests.post(f"{NOTION_API}/search", headers=notion_headers(), json=body, timeout=30)
        r.raise_for_status()
        data = r.json()
        pages.extend(data.get("results", []))
        log.info("Notion: fetched %d pages so far…", len(pages))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        time.sleep(0.35)  # stay under Notion rate limit
    return pages


def notion_page_text(page_id: str) -> str:
    """Fetch all block content for a page and flatten to plain text."""
    lines, cursor = [], None
    while True:
        url = f"{NOTION_API}/blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        r = requests.get(url, headers=notion_headers(), timeout=30)
        if r.status_code == 404:
            return ""
        r.raise_for_status()
        data = r.json()
        for block in data.get("results", []):
            btype = block.get("type", "")
            bdata = block.get(btype, {})
            rich = bdata.get("rich_text", [])
            text = "".join(t.get("plain_text", "") for t in rich)
            if text.strip():
                lines.append(text)
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        time.sleep(0.2)
    return "\n".join(lines)


def page_title(page: dict) -> str:
    props = page.get("properties", {})
    for key in ("title", "Name", "Title"):
        if key in props:
            rich = props[key].get("title", [])
            return "".join(t.get("plain_text", "") for t in rich)
    return page.get("id", "untitled")


def upsert_notion_page(conn, page: dict, content: str):
    pid      = page["id"]
    title    = page_title(page)
    url      = page.get("url", "")
    edited   = page.get("last_edited_time", "")
    chash    = hashlib.sha256(content.encode()).hexdigest()
    metadata = {
        "notion_page_id": pid,
        "url": url,
        "last_edited_time": edited,
        "object": page.get("object", "page"),
    }
    doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"notion:{pid}"))
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO knowledge.documents
                (doc_id, source, title, content, content_hash, metadata, ingested_at)
            VALUES (%s, 'notion', %s, %s, %s, %s, now())
            ON CONFLICT (doc_id) DO UPDATE SET
                title        = EXCLUDED.title,
                content      = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash,
                metadata     = EXCLUDED.metadata,
                ingested_at  = now()
            WHERE documents.content_hash != EXCLUDED.content_hash
        """, (doc_id, title, content, chash, json.dumps(metadata)))


# ---------------------------------------------------------------------------
# Linear helpers
# ---------------------------------------------------------------------------
def linear_headers() -> dict:
    if not LINEAR_API_KEY:
        raise RuntimeError("LINEAR_API_KEY not set")
    return {"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"}


ISSUES_QUERY = """
query Issues($after: String) {
  issues(first: 100, after: $after, orderBy: updatedAt) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id identifier title
      state { name }
      priority
      labels { nodes { name } }
      url
      description
      team { name }
      project { name }
      assignee { name }
      creator { name }
      createdAt updatedAt
    }
  }
}
"""


def linear_fetch_all() -> list[dict]:
    issues, cursor = [], None
    while True:
        variables = {}
        if cursor:
            variables["after"] = cursor
        r = requests.post(
            LINEAR_API,
            headers=linear_headers(),
            json={"query": ISSUES_QUERY, "variables": variables},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            raise RuntimeError(f"Linear GraphQL errors: {data['errors']}")
        page = data["data"]["issues"]
        issues.extend(page["nodes"])
        log.info("Linear: fetched %d issues so far…", len(issues))
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
        time.sleep(0.3)
    return issues


def upsert_linear_issue(conn, issue: dict):
    labels  = [lbl["name"] for lbl in (issue.get("labels") or {}).get("nodes", [])]
    chash   = hashlib.sha256(json.dumps(issue, sort_keys=True).encode()).hexdigest()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO knowledge.linear_issues
                (issue_id, identifier, title, state, priority, labels, url,
                 description, team_name, project_name, assignee, creator,
                 created_at, updated_at, content_hash)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (issue_id) DO UPDATE SET
                identifier   = EXCLUDED.identifier,
                title        = EXCLUDED.title,
                state        = EXCLUDED.state,
                priority     = EXCLUDED.priority,
                labels       = EXCLUDED.labels,
                url          = EXCLUDED.url,
                description  = EXCLUDED.description,
                team_name    = EXCLUDED.team_name,
                project_name = EXCLUDED.project_name,
                assignee     = EXCLUDED.assignee,
                creator      = EXCLUDED.creator,
                created_at   = EXCLUDED.created_at,
                updated_at   = EXCLUDED.updated_at,
                ingested_at  = now(),
                content_hash = EXCLUDED.content_hash
            WHERE linear_issues.content_hash != EXCLUDED.content_hash
        """, (
            issue["id"],
            issue.get("identifier", ""),
            issue.get("title", ""),
            (issue.get("state") or {}).get("name"),
            issue.get("priority"),
            json.dumps(labels),
            issue.get("url"),
            issue.get("description"),
            (issue.get("team") or {}).get("name"),
            (issue.get("project") or {}).get("name"),
            (issue.get("assignee") or {}).get("name"),
            (issue.get("creator") or {}).get("name"),
            issue.get("createdAt"),
            issue.get("updatedAt"),
            chash,
        ))


# ---------------------------------------------------------------------------
# Receipt helpers
# ---------------------------------------------------------------------------
def record_receipt(conn, shim: str, status: str, metadata: dict, error: str | None = None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO ingestion.receipts
                (receipt_id, shim_name, status, metadata, error_detail, ran_at)
            VALUES (%s, %s, %s, %s, %s, now())
        """, (str(uuid.uuid4()), shim, status, json.dumps(metadata), error))
    conn.commit()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log.info("Connecting to RDS…")
    conn = connect()
    conn.autocommit = False

    ensure_schema(conn)

    # ---- Notion ----
    notion_count = 0
    notion_error = None
    if not NOTION_TOKEN:
        log.warning("NOTION_TOKEN not set — skipping Notion ingestion")
    else:
        try:
            log.info("Fetching Notion page list…")
            pages = notion_search_all()
            log.info("Found %d Notion pages. Fetching content…", len(pages))
            for i, page in enumerate(pages, 1):
                pid = page["id"]
                try:
                    content = notion_page_text(pid)
                    upsert_notion_page(conn, page, content)
                    notion_count += 1
                    if i % 25 == 0:
                        conn.commit()
                        log.info("  committed %d/%d notion pages", i, len(pages))
                except Exception as e:
                    log.warning("  skipping page %s: %s", pid, e)
            conn.commit()
            log.info("Notion done: %d pages upserted", notion_count)
            record_receipt(conn, "notion_linear_rds_ingest/notion", "success",
                           {"pages_upserted": notion_count, "total_pages": len(pages)})
        except Exception as e:
            notion_error = str(e)
            log.error("Notion ingestion failed: %s", e)
            conn.rollback()
            record_receipt(conn, "notion_linear_rds_ingest/notion", "error",
                           {}, error=notion_error)

    # ---- Linear ----
    linear_count = 0
    linear_error = None
    if not LINEAR_API_KEY:
        log.warning("LINEAR_API_KEY not set — skipping Linear ingestion")
    else:
        try:
            log.info("Fetching Linear issues…")
            issues = linear_fetch_all()
            log.info("Found %d Linear issues. Upserting…", len(issues))
            for i, issue in enumerate(issues, 1):
                upsert_linear_issue(conn, issue)
                linear_count += 1
                if i % 100 == 0:
                    conn.commit()
                    log.info("  committed %d/%d linear issues", i, len(issues))
            conn.commit()
            log.info("Linear done: %d issues upserted", linear_count)
            record_receipt(conn, "notion_linear_rds_ingest/linear", "success",
                           {"issues_upserted": linear_count, "total_issues": len(issues)})
        except Exception as e:
            linear_error = str(e)
            log.error("Linear ingestion failed: %s", e)
            conn.rollback()
            record_receipt(conn, "notion_linear_rds_ingest/linear", "error",
                           {}, error=linear_error)

    conn.close()
    log.info("Done. Notion=%d Linear=%d", notion_count, linear_count)
    if notion_error or linear_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
