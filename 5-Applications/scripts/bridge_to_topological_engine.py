#!/usr/bin/env python3
"""
bridge_to_topological_engine.py — Push Research Stack data into Neo4j graph.

Reads ENE node mesh, Notion pages, and Linear issues, then upserts them
into the private topological engine (NoDupeLabs Neo4j) via Cypher.

Usage:
    python3 5-Applications/scripts/bridge_to_topological_engine.py [--dry-run]

Requires TOPOLOGICAL_ENGINE_URL and TOPOLOGICAL_ENGINE_TOKEN in .env.
"""

import sys
import json
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Load .env before imports
project_root = Path(__file__).parent.parent.parent
try:
    from dotenv import load_dotenv
    if (project_root / ".env").exists():
        load_dotenv(project_root / ".env")
except ImportError:
    pass

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "4-Infrastructure" / "infra"))

from infra.topological_engine_client import TopologicalEngineClient
from infra.ene_api import ENEAPIHook, AccessLevel

try:
    from infra.ene_cloud_credential_manager import (
        ENECloudCredentialManager,
        ENETopologicalStorage,
    )
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)


def _safe_id(prefix: str, key: str) -> str:
    safe = str(key).replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
    return f"{prefix}_{safe}"


# ═══════════════════════════════════════════════════════════════════════════
# Cypher builders
# ═══════════════════════════════════════════════════════════════════════════

def cypher_merge_node(label: str, id_val: str, props: Dict[str, Any]) -> str:
    """Generate a MERGE statement for a node."""
    # Neo4j doesn't allow null property values in MERGE well, so filter them
    clean = {k: v for k, v in props.items() if v is not None}
    clean["id"] = id_val
    clean["rs_synced_at"] = datetime.utcnow().isoformat()
    props_json = json.dumps(clean)
    return f"""
    MERGE (n:{label} {{id: $id}})
    SET n += $props
    """.strip()


def cypher_merge_rel(
    from_label: str, from_id: str,
    to_label: str, to_id: str,
    rel_type: str, props: Dict[str, Any]
) -> str:
    """Generate a MERGE statement for a relationship."""
    clean = {k: v for k, v in props.items() if v is not None}
    clean["rs_synced_at"] = datetime.utcnow().isoformat()
    return f"""
    MATCH (a:{from_label} {{id: $from_id}}), (b:{to_label} {{id: $to_id}})
    MERGE (a)-[r:{rel_type}]->(b)
    SET r += $props
    """.strip()


# ═══════════════════════════════════════════════════════════════════════════
# ENE → Cypher
# ═══════════════════════════════════════════════════════════════════════════

def build_ene_cypher(client: TopologicalEngineClient) -> List[Dict[str, Any]]:
    """Build Cypher statements from ENE substrate."""
    statements = []
    try:
        cm = ENECloudCredentialManager()
        storage = ENETopologicalStorage()
    except Exception as e:
        print(f"  ENE not available: {e}")
        return statements

    # Node stats
    stats = cm.balancer.get_balancer_stats()
    for node_id, node_stats in stats.get("nodes", {}).items():
        nid = _safe_id("ene", node_id)
        statements.append({
            "query": cypher_merge_node("ENENode", nid, {
                "node_id": node_id,
                "health": node_stats.get("health"),
                "connections": node_stats.get("connections"),
                "bytes": node_stats.get("bytes"),
                "latency": node_stats.get("latency"),
                "source": "ene",
            }),
            "parameters": {"id": nid, "props": {
                "node_id": node_id,
                "health": node_stats.get("health"),
                "connections": node_stats.get("connections"),
                "bytes": node_stats.get("bytes"),
                "latency": node_stats.get("latency"),
                "source": "ene",
            }},
            "read_only": False,
        })

    # Credentials metadata
    for cred_id, cred in cm.credentials.items():
        cid = _safe_id("cred", cred_id)
        statements.append({
            "query": cypher_merge_node("Credential", cid, {
                "credential_id": cred_id,
                "provider": cred.provider,
                "access_level": str(cred.access_level),
                "health_score": cred.health_score,
                "usage_count": cred.usage_count,
                "is_active": cred.is_active,
                "source": "ene",
            }),
            "parameters": {"id": cid, "props": {
                "credential_id": cred_id,
                "provider": cred.provider,
                "access_level": str(cred.access_level),
                "health_score": cred.health_score,
                "usage_count": cred.usage_count,
                "is_active": cred.is_active,
                "source": "ene",
            }},
            "read_only": False,
        })
        for node_id in cred.node_assignments:
            statements.append({
                "query": cypher_merge_rel(
                    "Credential", cid,
                    "ENENode", _safe_id("ene", node_id),
                    "ASSIGNED_TO", {"reason": "credential_assignment"}
                ),
                "parameters": {
                    "from_id": cid,
                    "to_id": _safe_id("ene", node_id),
                    "props": {"reason": "credential_assignment"}
                },
                "read_only": False,
            })

    # Storage health
    storage_health = storage.get_storage_health()
    statements.append({
        "query": cypher_merge_node("StorageHealth", "ene_storage_health", {
            **storage_health,
            "source": "ene",
        }),
        "parameters": {"id": "ene_storage_health", "props": {**storage_health, "source": "ene"}},
        "read_only": False,
    })

    return statements


# ═══════════════════════════════════════════════════════════════════════════
# Notion → Cypher
# ═══════════════════════════════════════════════════════════════════════════

def build_notion_cypher(api_key: str = None, db_id: str = None) -> List[Dict[str, Any]]:
    """Build Cypher statements from Notion (if credentials available)."""
    statements = []
    if not api_key:
        print("  Notion API key not available, skipping")
        return statements

    try:
        from scripts.dump_notion_ene_jsonl import NotionDataExtractor
        extractor = NotionDataExtractor(api_key=api_key, database_id=db_id)
    except Exception as e:
        print(f"  Notion extractor failed: {e}")
        return statements

    # Database schema
    schema = extractor.extract_database_schema()
    if "error" not in schema:
        db_id_safe = _safe_id("notion_db", schema.get("database_id", "unknown"))
        statements.append({
            "query": cypher_merge_node("NotionDatabase", db_id_safe, {
                "database_id": schema.get("database_id"),
                "title": schema.get("title", ""),
                "source": "notion",
            }),
            "parameters": {"id": db_id_safe, "props": {
                "database_id": schema.get("database_id"),
                "title": schema.get("title", ""),
                "source": "notion",
            }},
            "read_only": False,
        })

        # Pages
        pages = extractor.extract_pages()
        for page in pages:
            if "error" in page:
                continue
            page_id = page.get("page_id", "unknown")
            pid_safe = _safe_id("notion_page", page_id)
            statements.append({
                "query": cypher_merge_node("NotionPage", pid_safe, {
                    "page_id": page_id,
                    "title": page.get("title", ""),
                    "created": page.get("created"),
                    "last_edited": page.get("last_edited"),
                    "archived": page.get("archived"),
                    "source": "notion",
                }),
                "parameters": {"id": pid_safe, "props": {
                    "page_id": page_id,
                    "title": page.get("title", ""),
                    "created": page.get("created"),
                    "last_edited": page.get("last_edited"),
                    "archived": page.get("archived"),
                    "source": "notion",
                }},
                "read_only": False,
            })
            statements.append({
                "query": cypher_merge_rel(
                    "NotionPage", pid_safe,
                    "NotionDatabase", db_id_safe,
                    "IN_DATABASE", {}
                ),
                "parameters": {"from_id": pid_safe, "to_id": db_id_safe, "props": {}},
                "read_only": False,
            })

    return statements


# ═══════════════════════════════════════════════════════════════════════════
# Linear → Cypher
# ═══════════════════════════════════════════════════════════════════════════

def build_linear_cypher(api_key: str = None) -> List[Dict[str, Any]]:
    """Build Cypher statements from Linear (if credentials available)."""
    statements = []
    if not api_key:
        print("  Linear API key not available, skipping")
        return statements

    try:
        from scripts.dump_notion_ene_jsonl import LinearDataExtractor
        extractor = LinearDataExtractor(api_key=api_key)
    except Exception as e:
        print(f"  Linear extractor failed: {e}")
        return statements

    teams = extractor.extract_teams()
    team_map = {}
    for team in teams:
        if "error" in team:
            continue
        team_id = team.get("team_id", "unknown")
        tid_safe = _safe_id("linear_team", team_id)
        team_map[team.get("key", team_id)] = tid_safe
        statements.append({
            "query": cypher_merge_node("LinearTeam", tid_safe, {
                "team_id": team_id,
                "name": team.get("name", ""),
                "key": team.get("key", ""),
                "source": "linear",
            }),
            "parameters": {"id": tid_safe, "props": {
                "team_id": team_id,
                "name": team.get("name", ""),
                "key": team.get("key", ""),
                "source": "linear",
            }},
            "read_only": False,
        })

    issues = extractor.extract_issues()
    for issue in issues:
        if "error" in issue:
            continue
        issue_id = issue.get("issue_id", "unknown")
        iid_safe = _safe_id("linear_issue", issue_id)
        statements.append({
            "query": cypher_merge_node("LinearIssue", iid_safe, {
                "issue_id": issue_id,
                "title": issue.get("title", ""),
                "state": issue.get("state"),
                "priority": issue.get("priority"),
                "assignee": issue.get("assignee"),
                "created_at": issue.get("created_at"),
                "updated_at": issue.get("updated_at"),
                "source": "linear",
            }),
            "parameters": {"id": iid_safe, "props": {
                "issue_id": issue_id,
                "title": issue.get("title", ""),
                "state": issue.get("state"),
                "priority": issue.get("priority"),
                "assignee": issue.get("assignee"),
                "created_at": issue.get("created_at"),
                "updated_at": issue.get("updated_at"),
                "source": "linear",
            }},
            "read_only": False,
        })
        team_name = issue.get("team")
        if team_name and team_name in team_map:
            statements.append({
                "query": cypher_merge_rel(
                    "LinearIssue", iid_safe,
                    "LinearTeam", team_map[team_name],
                    "BELONGS_TO", {}
                ),
                "parameters": {"from_id": iid_safe, "to_id": team_map[team_name], "props": {}},
                "read_only": False,
            })

    return statements


# ═══════════════════════════════════════════════════════════════════════════
# Main bridge
# ═══════════════════════════════════════════════════════════════════════════

def run_bridge(dry_run: bool = False) -> Dict[str, Any]:
    """Pull ENE/Notion/Linear and push into topological engine."""
    print("=" * 70)
    print("RESEARCH STACK → TOPOLOGICAL ENGINE BRIDGE")
    print("=" * 70)

    client = TopologicalEngineClient()
    health = client.health()
    if not health.get("ok", False) and not dry_run:
        msg = f"Topological engine unhealthy: {health.get('error', 'unknown')}"
        print(f"\n❌ {msg}")
        print("   Check TOPOLOGICAL_ENGINE_URL and TOPOLOGICAL_ENGINE_TOKEN")
        return {"success": False, "error": msg}
    elif not health.get("ok", False):
        print(f"\n⚠️  Topological engine unavailable: {health.get('error', 'unknown')}")
        print("   Dry-run continuing...")
    else:
        print(f"\n✅ Topological engine healthy at {client.base_url}")

    # ── ENE ──
    print("\n[1] Building ENE Cypher...")
    ene_stmts = build_ene_cypher(client)
    print(f"   Built {len(ene_stmts)} ENE statements")

    # ── Notion ──
    print("\n[2] Building Notion Cypher...")
    notion_key = os.environ.get("NOTION_API_KEY")
    notion_db = os.environ.get("NOTION_DATABASE_ID")
    if not notion_key:
        try:
            hook = ENEAPIHook()
            res = hook.retrieve_sensitive_data("credentials/notion", AccessLevel.SECRET)
            if res.get("success"):
                notion_key = res["payload"]
                print("   Retrieved Notion key from ENE")
        except Exception:
            pass
    notion_stmts = build_notion_cypher(notion_key, notion_db)
    print(f"   Built {len(notion_stmts)} Notion statements")

    # ── Linear ──
    print("\n[3] Building Linear Cypher...")
    linear_key = os.environ.get("LINEAR_API_KEY")
    if not linear_key:
        try:
            hook = ENEAPIHook()
            res = hook.retrieve_sensitive_data("credentials/linear", AccessLevel.SECRET)
            if res.get("success"):
                linear_key = res["payload"]
                print("   Retrieved Linear key from ENE")
        except Exception:
            pass
    linear_stmts = build_linear_cypher(linear_key)
    print(f"   Built {len(linear_stmts)} Linear statements")

    all_stmts = ene_stmts + notion_stmts + linear_stmts
    print(f"\n[4] Total Cypher statements: {len(all_stmts)}")

    if dry_run:
        print("\n🧪 DRY-RUN: would execute the following statements:")
        for stmt in all_stmts:
            print(f"   - {stmt['query'][:80]}...")
        return {"success": True, "dry_run": True, "statements": len(all_stmts)}

    if not health.get("ok", False):
        print("\n❌ Engine unavailable and not in dry-run mode. Aborting.")
        return {"success": False, "error": "Engine unavailable"}

    # Execute
    print("\n[5] Executing Cypher against Neo4j...")
    results = client.batch_cypher(all_stmts)
    successes = sum(1 for r in results if r.get("ok"))
    failures = len(results) - successes
    print(f"   Success: {successes}, Failures: {failures}")

    if failures:
        for i, r in enumerate(results):
            if not r.get("ok"):
                print(f"   ⚠️  Stmt {i}: {r.get('error', 'unknown error')}")

    # Import Obsidian links if vault configured
    vault_path = os.environ.get("OBSIDIAN_VAULT_PATH")
    if vault_path:
        print(f"\n[6] Importing Obsidian wiki-links from {vault_path}...")
        imp_res = client.neo4j_import_obsidian_links(vault_path)
        if not imp_res.get("ok"):
            print(f"   ⚠️  Import failed: {imp_res.get('error')}")
        else:
            print(f"   ✅ Scanned {imp_res.get('notesScanned', 0)} notes, imported {imp_res.get('roadsImported', 0)} roads")
    else:
        print("\n[6] OBSIDIAN_VAULT_PATH not set, skipping link import")

    print("\n" + "=" * 70)
    print("BRIDGE COMPLETE")
    print("=" * 70)
    return {
        "success": True,
        "executed": successes,
        "failed": failures,
        "ene_statements": len(ene_stmts),
        "notion_statements": len(notion_stmts),
        "linear_statements": len(linear_stmts),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Research Stack → Topological Engine Bridge")
    parser.add_argument("--dry-run", action="store_true", help="Build statements without executing")
    args = parser.parse_args()
    result = run_bridge(dry_run=args.dry_run)
    sys.exit(0 if result.get("success") else 1)
