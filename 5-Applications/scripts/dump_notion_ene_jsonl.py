#!/usr/bin/env python3
"""
dump_notion_ene_jsonl.py — Notion + ENE Dump in JSON-L Schema

Extracts Notion and ENE data and formats in Research Stack JSON-L schema.
"""

import sys
import json
import time
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from shim.utils.datetime_utils import utc_now

# Load .env before any ENE imports so ENE_ENCRYPTION_KEY is available
project_root = Path(__file__).parent.parent.parent
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")
except ImportError:
    pass

# Add parent directory to path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "4-Infrastructure" / "infra"))

try:
    from infra.web_interaction_surface import SwarmWebInterface, DutyType
    from infra.ene_cloud_credential_manager import (
        ENECloudCredentialManager,
        ENETopologicalStorage,
        ENENodeBalancer
    )
    from infra.ene_api import ENEAPIHook, AccessLevel
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# JSON-L Schema Formatter
# ═══════════════════════════════════════════════════════════════════════════

def generate_id(pkg: str, version: str = None) -> str:
    """Generate unique ID in ENE format."""
    timestamp = version or utc_now()
    return f"ene:{pkg}:{timestamp}"

def format_jsonl_entry(
    pkg: str,
    data: Dict[str, Any],
    tier: str = "AUX",
    domain: str = "integration",
    archetype: str = "api_data",
    bind_class: str = "informational_bind",
    invariant: str = "dataConsistency",
    node: str = "mcp_server",
    src: str = "notion_ene_dump"
) -> Dict[str, Any]:
    """Format entry in Research Stack JSON-L schema."""

    timestamp = time.time()
    entry_id = generate_id(pkg, utc_now())

    return {
        "t": timestamp,
        "src": src,
        "id": entry_id,
        "op": "upsert",
        "data": {
            "pkg": pkg,
            "version": utc_now(),
            "tier": tier,
            "domain": domain,
            "archetype": archetype,
            **data
        },
        "bind": {
            "lawful": True,
            "cost": 65536,
            "invariant": invariant,
            "class": bind_class
        },
        "provenance": {
            "node": node,
            "lake_seed": "notion_ene_dump_seed"
        }
    }

# ═══════════════════════════════════════════════════════════════════════════
# Notion Data Extractor
# ═══════════════════════════════════════════════════════════════════════════

class NotionDataExtractor:
    """Extract Notion data for JSON-L dump."""

    def __init__(self, api_key: str = None, database_id: str = None, ene_api_hook = None):
        self.api_key = api_key
        self.database_id = database_id
        self.web = SwarmWebInterface()
        self.ene_api_hook = ene_api_hook

        # Try to get Notion credentials from ENE API hook if not provided
        if not self.api_key and self.ene_api_hook:
            try:
                notion_res = self.ene_api_hook.retrieve_sensitive_data("credentials/notion", AccessLevel.SECRET)
                if notion_res.get("success"):
                    self.api_key = notion_res["payload"]
                    print("  [Notion] Retrieved credentials from ENE substrate")
                else:
                    print(f"  [Notion] ENE decryption failed: {notion_res.get('error', 'unknown error')}")
            except Exception as e:
                print(f"  [Notion] Failed to get credentials from ENE: {e}")

        # Fallback to environment variables if ENE didn't work
        if not self.api_key:
            self.api_key = os.environ.get("NOTION_API_KEY")
            if self.api_key:
                print("  [Notion] Using NOTION_API_KEY from environment fallback")

        if not self.database_id:
            self.database_id = os.environ.get("NOTION_DATABASE_ID")
            if self.database_id:
                print("  [Notion] Using NOTION_DATABASE_ID from environment fallback")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else None,
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def extract_database_schema(self, database_id: str = None) -> Dict[str, Any]:
        """Extract database schema from Notion API."""
        db_id = database_id or self.database_id
        if not db_id or not self.api_key:
            return {"error": "No database ID or API key provided"}

        # Query Notion API for database schema
        url = f"https://api.notion.com/v1/databases/{db_id}"

        try:
            task = self.web.surface.submit_task(
                DutyType.CONTENT_EXTRACTION,
                url,
                priority=8,
                options={
                    "method": "GET",
                    "headers": self.headers
                }
            )

            result = self.web.surface.execute_task(task["task_id"])
            if "error" not in result:
                # Extract schema from API response
                db_data = result.get("result", {})
                return {
                    "database_id": db_id,
                    "title": db_data.get("title", [{}])[0].get("plain_text", ""),
                    "properties": {k: v for k, v in db_data.get("properties", {}).items()}
                }
        except Exception as e:
            return {"error": f"API call failed: {e}"}

        return {"error": "Failed to extract schema"}

    def extract_pages(self, database_id: str = None) -> List[Dict[str, Any]]:
        """Extract all pages from database via Notion API."""
        db_id = database_id or self.database_id
        if not db_id or not self.api_key:
            return [{"error": "No database ID or API key provided"}]

        # Query Notion API for pages
        url = f"https://api.notion.com/v1/databases/{db_id}/query"

        pages = []
        try:
            task = self.web.surface.submit_task(
                DutyType.CONTENT_EXTRACTION,
                url,
                priority=8,
                options={
                    "method": "POST",
                    "headers": self.headers,
                    "body": json.dumps({})
                }
            )

            result = self.web.surface.execute_task(task["task_id"])
            if "error" not in result:
                api_result = result.get("result", {})
                for page in api_result.get("results", []):
                    page_data = {
                        "page_id": page.get("id"),
                        "title": self._extract_title(page),
                        "properties": self._extract_properties(page),
                        "created": page.get("created_time"),
                        "last_edited": page.get("last_edited_time"),
                        "archived": page.get("archived", False)
                    }
                    pages.append(page_data)
        except Exception as e:
            return [{"error": f"API call failed: {e}"}]

        return pages

    def _extract_title(self, page: Dict) -> str:
        """Extract title from page object."""
        properties = page.get("properties", {})
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title = prop_data.get("title", [{}])
                if title:
                    return title[0].get("plain_text", "")
        return ""

    def _extract_properties(self, page: Dict) -> Dict[str, Any]:
        """Extract all properties from page."""
        properties = {}
        for prop_name, prop_data in page.get("properties", {}).items():
            prop_type = prop_data.get("type")
            if prop_type == "select":
                properties[prop_name] = prop_data.get("select", {}).get("name")
            elif prop_type == "multi_select":
                properties[prop_name] = [s.get("name") for s in prop_data.get("multi_select", [])]
            elif prop_type == "date":
                properties[prop_name] = prop_data.get("date", {}).get("start")
            elif prop_type == "rich_text":
                properties[prop_name] = [t.get("plain_text") for t in prop_data.get("rich_text", [])]
            else:
                properties[prop_name] = str(prop_data)
        return properties

    def extract_page_content(self, page_id: str) -> Dict[str, Any]:
        """Extract full content (blocks) from a page."""
        if not self.api_key:
            return {"error": "No API key provided"}

        url = f"https://api.notion.com/v1/blocks/{page_id}/children"

        try:
            task = self.web.surface.submit_task(
                DutyType.CONTENT_EXTRACTION,
                url,
                priority=7,
                options={
                    "method": "GET",
                    "headers": self.headers
                }
            )

            result = self.web.surface.execute_task(task["task_id"])
            if "error" not in result:
                api_result = result.get("result", {})
                blocks = []
                for block in api_result.get("results", []):
                    blocks.append({
                        "block_id": block.get("id"),
                        "type": block.get("type"),
                        "has_children": block.get("has_children", False)
                    })
                return {"page_id": page_id, "blocks": blocks}
        except Exception as e:
            return {"error": f"API call failed: {e}"}

        return {"error": "Failed to extract content"}

    def format_as_jsonl(self) -> List[Dict[str, Any]]:
        """Format all Notion data as JSON-L entries."""
        entries = []

        if not self.api_key:
            # Add entry indicating no API key
            entries.append(format_jsonl_entry(
                pkg="notion/status/no_credentials",
                data={"error": "Notion API key not provided"},
                tier="AUX",
                domain="notion",
                archetype="status",
                invariant="statusReport"
            ))
            return entries

        # Database schema entry
        schema = self.extract_database_schema()
        entries.append(format_jsonl_entry(
            pkg="notion/database/schema",
            data=schema,
            tier="AUX",
            domain="notion",
            archetype="database_schema",
            invariant="schemaConsistency"
        ))

        # Pages entries with full content
        pages = self.extract_pages()
        for page in pages:
            entries.append(format_jsonl_entry(
                pkg=f"notion/page/{page.get('page_id', 'unknown')}",
                data=page,
                tier="AUX",
                domain="notion",
                archetype="page",
                invariant="pageDataConsistency"
            ))

            # Extract page content if available
            if page.get("page_id"):
                content = self.extract_page_content(page["page_id"])
                entries.append(format_jsonl_entry(
                    pkg=f"notion/page_content/{page['page_id']}",
                    data=content,
                    tier="AUX",
                    domain="notion",
                    archetype="page_content",
                    invariant="contentConsistency"
                ))

        return entries

# ═══════════════════════════════════════════════════════════════════════════
# Linear Data Extractor
# ═══════════════════════════════════════════════════════════════════════════

class LinearDataExtractor:
    """Extract Linear data for JSON-L dump."""

    BASE_URL = "https://api.linear.app/graphql"

    def __init__(self, api_key: str = None, ene_api_hook = None):
        self.api_key = api_key
        self.web = SwarmWebInterface()
        self.ene_api_hook = ene_api_hook

        # Try to get Linear credentials from ENE API hook if not provided
        if not self.api_key and self.ene_api_hook:
            try:
                linear_res = self.ene_api_hook.retrieve_sensitive_data("credentials/linear", AccessLevel.SECRET)
                if linear_res.get("success"):
                    self.api_key = linear_res["payload"]
                    print("  [Linear] Retrieved credentials from ENE substrate")
                else:
                    print(f"  [Linear] ENE decryption failed: {linear_res.get('error', 'unknown error')}")
            except Exception as e:
                print(f"  [Linear] Failed to get credentials from ENE: {e}")

        # Fallback to environment variables if ENE didn't work
        if not self.api_key:
            self.api_key = os.environ.get("LINEAR_API_KEY")
            if self.api_key:
                print("  [Linear] Using LINEAR_API_KEY from environment fallback")

        self.headers = {
            "Authorization": f"{self.api_key}" if self.api_key else None,
            "Content-Type": "application/json"
        }

    def _query(self, query: str, variables: Dict = None) -> Dict[str, Any]:
        """Execute GraphQL query against Linear API."""
        if not self.api_key:
            return {"error": "No Linear API key provided"}

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            task = self.web.surface.submit_task(
                DutyType.CONTENT_EXTRACTION,
                self.BASE_URL,
                priority=8,
                options={
                    "method": "POST",
                    "headers": self.headers,
                    "body": json.dumps(payload)
                }
            )
            result = self.web.surface.execute_task(task["task_id"])
            return result
        except Exception as e:
            return {"error": f"API call failed: {e}"}

    def extract_issues(self) -> List[Dict[str, Any]]:
        """Extract Linear issues."""
        query = """
        query {
            issues(first: 50) {
                nodes {
                    id
                    title
                    description
                    state { name }
                    priority
                    assignee { name }
                    team { name }
                    createdAt
                    updatedAt
                }
            }
        }
        """
        result = self._query(query)
        if "error" in result:
            return [result]

        api_result = result.get("result", {})
        data = api_result.get("data", {})
        issues = data.get("issues", {}).get("nodes", [])

        return [{
            "issue_id": issue.get("id"),
            "title": issue.get("title"),
            "description": issue.get("description"),
            "state": issue.get("state", {}).get("name"),
            "priority": issue.get("priority"),
            "assignee": issue.get("assignee", {}).get("name") if issue.get("assignee") else None,
            "team": issue.get("team", {}).get("name") if issue.get("team") else None,
            "created_at": issue.get("createdAt"),
            "updated_at": issue.get("updatedAt")
        } for issue in issues]

    def extract_teams(self) -> List[Dict[str, Any]]:
        """Extract Linear teams."""
        query = """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                }
            }
        }
        """
        result = self._query(query)
        if "error" in result:
            return [result]

        api_result = result.get("result", {})
        data = api_result.get("data", {})
        teams = data.get("teams", {}).get("nodes", [])

        return [{
            "team_id": team.get("id"),
            "name": team.get("name"),
            "key": team.get("key"),
            "description": team.get("description")
        } for team in teams]

    def extract_me(self) -> Dict[str, Any]:
        """Extract current user info from Linear."""
        query = """
        query {
            viewer {
                id
                name
                email
                team { name }
            }
        }
        """
        result = self._query(query)
        if "error" in result:
            return result

        api_result = result.get("result", {})
        data = api_result.get("data", {})
        viewer = data.get("viewer", {})
        return {
            "user_id": viewer.get("id"),
            "name": viewer.get("name"),
            "email": viewer.get("email"),
            "team": viewer.get("team", {}).get("name") if viewer.get("team") else None
        }

    def format_as_jsonl(self) -> List[Dict[str, Any]]:
        """Format all Linear data as JSON-L entries."""
        entries = []

        if not self.api_key:
            entries.append(format_jsonl_entry(
                pkg="linear/status/no_credentials",
                data={"error": "Linear API key not provided"},
                tier="AUX",
                domain="linear",
                archetype="status",
                invariant="statusReport"
            ))
            return entries

        # Viewer info
        me = self.extract_me()
        entries.append(format_jsonl_entry(
            pkg="linear/viewer",
            data=me,
            tier="AUX",
            domain="linear",
            archetype="user",
            invariant="userDataConsistency"
        ))

        # Teams
        teams = self.extract_teams()
        for team in teams:
            entries.append(format_jsonl_entry(
                pkg=f"linear/team/{team.get('team_id', 'unknown')}",
                data=team,
                tier="AUX",
                domain="linear",
                archetype="team",
                invariant="teamDataConsistency"
            ))

        # Issues
        issues = self.extract_issues()
        for issue in issues:
            entries.append(format_jsonl_entry(
                pkg=f"linear/issue/{issue.get('issue_id', 'unknown')}",
                data=issue,
                tier="AUX",
                domain="linear",
                archetype="issue",
                invariant="issueDataConsistency"
            ))

        return entries

# ═══════════════════════════════════════════════════════════════════════════
# ENE Data Extractor
# ═══════════════════════════════════════════════════════════════════════════

class ENEDataExtractor:
    """Extract ENE data for JSON-L dump."""

    def __init__(self):
        try:
            self.credential_manager = ENECloudCredentialManager()
            self.topological_storage = ENETopologicalStorage()
            self.ene_available = True
        except Exception as e:
            print(f"ENE not available: {e}")
            self.ene_available = False
            self.credential_manager = None
            self.topological_storage = None

    def extract_node_stats(self) -> Dict[str, Any]:
        """Extract ENE node statistics."""
        if not self.ene_available:
            return {"error": "ENE not available"}

        return self.credential_manager.balancer.get_balancer_stats()

    def extract_credentials(self) -> List[Dict[str, Any]]:
        """Extract ENE credential metadata (not actual keys)."""
        if not self.ene_available:
            return [{"error": "ENE not available"}]

        creds_metadata = []
        for cred_id, cred in self.credential_manager.credentials.items():
            creds_metadata.append({
                "credential_id": cred_id,
                "provider": cred.provider,
                "access_level": str(cred.access_level),
                "node_assignments": cred.node_assignments,
                "usage_count": cred.usage_count,
                "health_score": cred.health_score,
                "last_rotated": datetime.fromtimestamp(cred.last_rotated).isoformat(),
                "is_active": cred.is_active
            })
        return creds_metadata

    def extract_connections(self) -> List[Dict[str, Any]]:
        """Extract all active connections from ENE."""
        if not self.ene_available:
            return [{"error": "ENE not available"}]

        connections = []
        for conn_id, conn in self.credential_manager.balancer.active_connections.items():
            connections.append({
                "connection_id": conn_id,
                "node_id": conn.node_id,
                "credential_id": conn.credential_id,
                "connected_at": datetime.fromtimestamp(conn.connected_at).isoformat(),
                "last_activity": datetime.fromtimestamp(conn.last_activity).isoformat(),
                "bytes_transferred": conn.bytes_transferred,
                "error_count": conn.error_count,
                "latency_ms": conn.latency_ms,
                "status": conn.status
            })
        return connections

    def extract_storage_health(self) -> Dict[str, Any]:
        """Extract topological storage health."""
        if not self.ene_available:
            return {"error": "ENE not available"}

        return self.topological_storage.get_storage_health()

    def extract_database_records(self, db_path: str = None) -> List[Dict[str, Any]]:
        """Extract raw records from ENE SQLite databases."""
        import sqlite3

        if not db_path:
            db_path = "/home/allaun/Documents/Research Stack/data/ene_cloud_credentials.db"

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            records = []
            for (table_name,) in tables:
                cursor.execute(f"SELECT * FROM {table_name}")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()

                for row in rows:
                    # Convert bytes to hex for JSON serialization
                    values_serializable = []
                    for value in row:
                        if isinstance(value, bytes):
                            values_serializable.append(value.hex())
                        else:
                            values_serializable.append(value)

                    records.append({
                        "table": table_name,
                        "columns": columns,
                        "values": list(values_serializable)
                    })

            conn.close()
            return records
        except Exception as e:
            return [{"error": f"Database extraction failed: {e}"}]

    def format_as_jsonl(self) -> List[Dict[str, Any]]:
        """Format all ENE data as JSON-L entries."""
        entries = []

        if not self.ene_available:
            # Add entry indicating ENE unavailable
            entries.append(format_jsonl_entry(
                pkg="ene/status/unavailable",
                data={"error": "ENE credential manager not available"},
                tier="AUX",
                domain="ene",
                archetype="status",
                invariant="statusReport"
            ))
            return entries

        # Node stats entry
        node_stats = self.extract_node_stats()
        entries.append(format_jsonl_entry(
            pkg="ene/nodes/stats",
            data=node_stats,
            tier="AUX",
            domain="ene",
            archetype="node_statistics",
            invariant="nodeHealthConsistency"
        ))

        # Individual node entries
        for node_id, stats in node_stats.get("nodes", {}).items():
            entries.append(format_jsonl_entry(
                pkg=f"ene/node/{node_id}",
                data={
                    "node_id": node_id,
                    "health": stats.get("health"),
                    "connections": stats.get("connections"),
                    "bytes": stats.get("bytes"),
                    "latency": stats.get("latency")
                },
                tier="AUX",
                domain="ene",
                archetype="node",
                invariant="nodeHealth"
            ))

        # Credentials metadata entry
        creds = self.extract_credentials()
        for cred in creds:
            entries.append(format_jsonl_entry(
                pkg=f"ene/credentials/{cred.get('credential_id', 'unknown')}",
                data=cred,
                tier="VAULT",  # Credentials are vaulted
                domain="ene",
                archetype="credential_metadata",
                invariant="credentialSecurity",
                bind_class="control_bind"
            ))

        # Connections entry
        connections = self.extract_connections()
        for conn in connections:
            entries.append(format_jsonl_entry(
                pkg=f"ene/connection/{conn.get('connection_id', 'unknown')}",
                data=conn,
                tier="AUX",
                domain="ene",
                archetype="connection",
                invariant="connectionConsistency"
            ))

        # Storage health entry
        storage_health = self.extract_storage_health()
        entries.append(format_jsonl_entry(
            pkg="ene/storage/health",
            data=storage_health,
            tier="AUX",
            domain="ene",
            archetype="storage_health",
            invariant="storageConsistency"
        ))

        # Database records entry
        db_records = self.extract_database_records()
        for record in db_records:
            entries.append(format_jsonl_entry(
                pkg=f"ene/database/{record.get('table', 'unknown')}",
                data=record,
                tier="AUX",
                domain="ene",
                archetype="database_record",
                invariant="databaseIntegrity"
            ))

        return entries

# ═══════════════════════════════════════════════════════════════════════════
# Topological Engine Dumper
# ═══════════════════════════════════════════════════════════════════════════

class TopologicalEngineDumper:
    """Push JSON-L entries into the private topological engine (Neo4j) via Cypher."""

    def __init__(self, base_url: str = None, token: str = None):
        try:
            from infra.topological_engine_client import TopologicalEngineClient
            self.client = TopologicalEngineClient(base_url=base_url, token=token)
            self.available = True
        except Exception as e:
            print(f"Topological engine client not available: {e}")
            self.available = False
            self.client = None

    def push_entries(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert JSON-L entries to Cypher MERGE statements and execute."""
        if not self.available:
            return {"error": "Topological engine not available"}

        statements = []
        for entry in entries:
            entry_id = entry.get("id", f"rs:{entry.get('t', 0)}")
            data = entry.get("data", {})
            archetype = data.get("archetype", "entry")
            domain = data.get("domain", "research_stack")
            label = f"RS{archetype.replace('_', '').title()}"

            props = {
                **data,
                "timestamp": entry.get("t"),
                "source": entry.get("src"),
                "operation": entry.get("op"),
                "domain": domain,
                "synced_at": utc_now(),
            }
            # Filter None values
            props = {k: v for k, v in props.items() if v is not None}

            query = f"""
            MERGE (n:{label} {{id: $id}})
            SET n += $props
            """.strip()
            statements.append({
                "query": query,
                "parameters": {"id": entry_id, "props": props},
                "read_only": False,
            })

        if not statements:
            return {"upserted": 0}

        results = self.client.batch_cypher(statements)
        successes = sum(1 for r in results if r.get("ok"))
        return {"upserted": successes, "total": len(statements), "errors": len(statements) - successes}

# ═══════════════════════════════════════════════════════════════════════════
# Main Dump Function
# ═══════════════════════════════════════════════════════════════════════════

def create_combined_dump(
    notion_api_key: str = None,
    notion_database_id: str = None,
    linear_api_key: str = None,
    output_path: str = "/home/allaun/Documents/Research Stack/data/notion_ene_dump_full.jsonl",
    push_to_topology: bool = False
):
    """Create combined Notion + Linear + ENE dump in JSON-L schema."""

    print("=" * 70)
    print("NOTION + LINEAR + ENE FULL JSON-L DUMP")
    print("=" * 70)

    # Initialize ENE API hook for credential retrieval
    ene_api_hook = None
    try:
        ene_api_hook = ENEAPIHook()
        print("ENE API hook initialized")
    except Exception as e:
        print(f"ENE API hook not available: {e}")

    # Extract Notion data
    print("\n[1] Extracting Notion data...")
    notion_extractor = NotionDataExtractor(notion_api_key, notion_database_id, ene_api_hook)
    notion_entries = notion_extractor.format_as_jsonl()
    print(f"  Extracted {len(notion_entries)} Notion entries")

    # Extract Linear data
    print("\n[2] Extracting Linear data...")
    linear_extractor = LinearDataExtractor(linear_api_key, ene_api_hook)
    linear_entries = linear_extractor.format_as_jsonl()
    print(f"  Extracted {len(linear_entries)} Linear entries")

    # Extract ENE data
    print("\n[3] Extracting ENE data...")
    ene_extractor = ENEDataExtractor()
    ene_entries = ene_extractor.format_as_jsonl()
    print(f"  Extracted {len(ene_entries)} ENE entries")

    # Combine entries
    print("\n[4] Combining entries...")
    all_entries = notion_entries + linear_entries + ene_entries
    print(f"  Total entries: {len(all_entries)}")

    # Write to JSON-L file
    print(f"\n[5] Writing to {output_path}...")
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        for entry in all_entries:
            f.write(json.dumps(entry) + '\n')

    print(f"  Wrote {len(all_entries)} entries")

    # Optional: push to topological engine
    topology_result = None
    if push_to_topology:
        print("\n[6] Pushing to topological engine...")
        dumper = TopologicalEngineDumper()
        topology_result = dumper.push_entries(all_entries)
        if "error" in topology_result:
            print(f"  ⚠️  Topology push failed: {topology_result['error']}")
        else:
            print(f"  Upserted {topology_result.get('upserted', 0)}/{topology_result.get('total', 0)} entries into Neo4j")

    # Summary
    print("\n" + "=" * 70)
    print("FULL DUMP SUMMARY")
    print("=" * 70)
    print(f"Notion entries:  {len(notion_entries)}")
    print(f"Linear entries:  {len(linear_entries)}")
    print(f"ENE entries:     {len(ene_entries)}")
    print(f"Total entries:   {len(all_entries)}")
    print(f"Output file:     {output_path}")
    if topology_result and "error" not in topology_result:
        print(f"Topology upsert: {topology_result.get('upserted', 0)} OK")
    print(f"Schema:          Research Stack JSON-L (ENE format)")
    print(f"Mode:            Full accounting (all data extracted)")
    print("=" * 70)

    return all_entries

# ═══════════════════════════════════════════════════════════════════════════
# CLI Interface
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Notion + Linear + ENE JSON-L dump")
    parser.add_argument("--notion-key", default=os.environ.get("NOTION_API_KEY"), help="Notion API key")
    parser.add_argument("--notion-db", default=os.environ.get("NOTION_DATABASE_ID"), help="Notion database ID")
    parser.add_argument("--linear-key", default=os.environ.get("LINEAR_API_KEY"), help="Linear API key")
    parser.add_argument("--output", default="/home/allaun/Documents/Research Stack/data/notion_ene_dump_full.jsonl", help="Output JSON-L path")
    parser.add_argument("--topology", action="store_true", help="Also push to topological engine (Neo4j)")
    args = parser.parse_args()

    create_combined_dump(
        notion_api_key=args.notion_key,
        notion_database_id=args.notion_db,
        linear_api_key=args.linear_key,
        output_path=args.output,
        push_to_topology=args.topology
    )
