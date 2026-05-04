#!/usr/bin/env python3
"""
Topological Engine Client — Private connector to NoDupeLabs Obsidian + Neo4j graph.

Provides:
- Obsidian vault read/write/search
- Neo4j Cypher execution, road upserts, and Obsidian link imports
- Health checks

All endpoints require TOPOLOGICAL_ENGINE_TOKEN (Bearer auth).
"""

import json
import os
from typing import Dict, List, Any, Optional
from urllib.parse import quote

import requests


class TopologicalEngineClient:
    """Client for the private topological engine (NoDupeLabs)."""

    def __init__(
        self,
        base_url: str = None,
        token: str = None,
        timeout: int = 30
    ):
        self.base_url = (base_url or os.getenv(
            "TOPOLOGICAL_ENGINE_URL", "http://localhost:3000"
        )).rstrip("/")
        self.token = token or os.getenv("TOPOLOGICAL_ENGINE_TOKEN", "")
        self.timeout = timeout
        self._session = requests.Session()
        if self.token:
            self._session.headers["Authorization"] = f"Bearer {self.token}"
        self._session.headers["Content-Type"] = "application/json"

    # ─────────────────────────────────────────────────────────────────────────
    # Health
    # ─────────────────────────────────────────────────────────────────────────

    def health(self) -> Dict[str, Any]:
        """Ping the topological engine health endpoint."""
        url = f"{self.base_url}/topology/health"
        try:
            resp = self._session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e), "healthy": False}

    # ─────────────────────────────────────────────────────────────────────────
    # Obsidian
    # ─────────────────────────────────────────────────────────────────────────

    def write_obsidian_note(
        self,
        title: str = None,
        folder: str = "Research Stack",
        body: str = "",
        path: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Write or overwrite an Obsidian note.
        
        Uses 'path' if provided (legacy compat), otherwise constructs from title+folder.
        """
        url = f"{self.base_url}/topology/obsidian/write-note"
        payload = {
            "folder": folder,
            "body": body,
        }
        if title:
            payload["title"] = title
        if path:
            # Router uses title+folder; simulate by extracting title from path
            payload["title"] = path.replace(".md", "").split("/")[-1]
            if "/" in path:
                payload["folder"] = "/".join(path.replace(".md", "").split("/")[:-1])
        if metadata:
            payload.update({k: v for k, v in metadata.items() if k not in payload})
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def read_obsidian_note(self, path: str) -> Dict[str, Any]:
        """Read an Obsidian note by vault-relative path."""
        encoded = quote(path, safe="")
        url = f"{self.base_url}/topology/obsidian/read-note?path={encoded}"
        try:
            resp = self._session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def search_obsidian(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Full-text search across the Obsidian vault."""
        url = f"{self.base_url}/topology/obsidian/search"
        payload = {"query": query, "limit": limit}
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    # ─────────────────────────────────────────────────────────────────────────
    # Neo4j — simple pairwise road upsert (matches API exactly)
    # ─────────────────────────────────────────────────────────────────────────

    def neo4j_upsert_road(
        self,
        source_id: str,
        source_label: str,
        target_id: str,
        target_label: str,
        relation: str,
        authority_scope: str = "candidate",
        outcome: str = "hold",
        torsion: float = 0,
        coherence: float = 1.0,
        provenance_hash: str = None,
        source_of_truth: str = None,
        quarantine_status: str = "none"
    ) -> Dict[str, Any]:
        """Upsert a simple pairwise road (2 nodes + 1 relationship)."""
        url = f"{self.base_url}/topology/neo4j/upsert-road"
        payload = {
            "sourceId": source_id,
            "sourceLabel": source_label,
            "targetId": target_id,
            "targetLabel": target_label,
            "relation": relation,
            "authority_scope": authority_scope,
            "outcome": outcome,
            "torsion": torsion,
            "coherence": coherence,
            "provenance_hash": provenance_hash or "",
            "source_of_truth": source_of_truth or "Neo4j candidate; Graph.lean audit required",
            "quarantine_status": quarantine_status,
        }
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    # ─────────────────────────────────────────────────────────────────────────
    # Neo4j — arbitrary Cypher (for complex batch structures)
    # ─────────────────────────────────────────────────────────────────────────

    def neo4j_cypher(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        read_only: bool = False
    ) -> Dict[str, Any]:
        """Run an arbitrary Cypher query."""
        url = f"{self.base_url}/topology/neo4j/cypher"
        payload = {"cypher": query, "params": parameters or {}, "readOnly": read_only}
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def neo4j_import_obsidian_links(
        self,
        vault_path: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Trigger import of Obsidian [[wiki-links]] into Neo4j."""
        url = f"{self.base_url}/topology/neo4j/import-obsidian-links"
        payload = {"limit": limit}
        if vault_path:
            payload["vault_path"] = vault_path
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    # ─────────────────────────────────────────────────────────────────────────
    # Batch helpers
    # ─────────────────────────────────────────────────────────────────────────

    def batch_upsert_roads(self, roads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Upsert multiple simple roads, returning results per road."""
        results = []
        for road in roads:
            results.append(self.neo4j_upsert_road(**road))
        return results

    def batch_cypher(self, statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run multiple Cypher statements."""
        results = []
        for stmt in statements:
            results.append(self.neo4j_cypher(
                query=stmt["query"],
                parameters=stmt.get("parameters", {}),
                read_only=stmt.get("read_only", False)
            ))
        return results

    def ensure_indexes(self) -> Dict[str, Any]:
        """Idempotent index/constraints for Research Stack graph."""
        statements = [
            {"query": "CREATE INDEX rs_node_id IF NOT EXISTS FOR (n:Node) ON (n.id)", "read_only": False},
            {"query": "CREATE INDEX rs_obsidian_id IF NOT EXISTS FOR (n:ObsidianNote) ON (n.id)", "read_only": False},
        ]
        return {"statements": statements, "results": self.batch_cypher(statements)}
