#!/usr/bin/env python3
"""obsidian_sync_shim.py — Bidirectional sync between Obsidian vault and JSON-L lake.

Modes:
    ingest    : Obsidian notes → JSON-L lake (append to lake file)
    export    : JSON-L lake   → Obsidian notes (write to vault)
    sync      : Two-way merge (default: Obsidian wins on conflict)

Requires TOPOLOGICAL_ENGINE_URL and TOPOLOGICAL_ENGINE_TOKEN in .env.
For local Obsidian installs, set OBSIDIAN_VAULT_PATH or use --vault.

Hardcoded node/provenance assumptions were removed:
- provenance.node uses ENE_NODE_ID (default: obsidian_sync_shim)
- provenance.lake_seed uses ENE_LAKE_SEED (default: obsidian_lake)
- provenance.tailscale_ip uses ENE_TAILSCALE_IP (default: 127.0.0.1)

NOTE: This is a legacy ingest surface; treat outputs as non-authoritative.
"""

import sys
import json
import os
import argparse
import hashlib
import re
from pathlib import Path
from datetime import datetime, timezone
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


def env_default(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v is not None and v != "" else default


DEFAULT_VAULT_PATH = project_root / "Obdisidan connector"
LAKE_PATH = Path(os.getenv("OBSIDIAN_LAKE_PATH", str(project_root / "data" / "obsidian_lake.jsonl")))
LAKE_PATH.parent.mkdir(parents=True, exist_ok=True)

WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_/-]+)")


def _vault_path(path: Optional[str] = None) -> Path:
    """Resolve the local Obsidian vault path."""
    raw = path or os.getenv("OBSIDIAN_VAULT_PATH") or str(DEFAULT_VAULT_PATH)
    return Path(raw).expanduser().resolve()


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _note_pkg(path: str) -> str:
    return f"obsidian/note/{path}"


def _extract_note_metadata(content: str) -> Dict[str, Any]:
    """Extract lightweight Obsidian metadata without changing note content."""
    links = sorted(set(match.strip() for match in WIKI_LINK_RE.findall(content)))
    tags = sorted(set(match.strip() for match in TAG_RE.findall(content)))
    return {"links": links, "tags": tags, "content_hash": _content_hash(content)}


def _iter_local_notes(vault_path: Path) -> List[Path]:
    """Return markdown notes in a local vault, excluding Obsidian internals."""
    if not vault_path.exists():
        return []
    notes = []
    for path in vault_path.rglob("*.md"):
        rel_parts = path.relative_to(vault_path).parts
        if rel_parts and rel_parts[0] == ".obsidian":
            continue
        notes.append(path)
    return sorted(notes)


def _matches_query(path: str, title: str, content: str, query: str) -> bool:
    if query in ("", "*"):
        return True
    q = query.lower()
    return q in path.lower() or q in title.lower() or q in content.lower()


def _format_jsonl_entry(
    pkg: str,
    data: Dict[str, Any],
    tier: str = "AUX",
    domain: str = "obsidian",
    archetype: str = "note",
    src: str = "obsidian_sync_shim",
) -> Dict[str, Any]:
    """Format a JSON-L entry for the Research Stack lake."""
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()

    node_id = env_default("ENE_NODE_ID", "obsidian_sync_shim")
    lake_seed = env_default("ENE_LAKE_SEED", "obsidian_lake")
    tailscale_ip = env_default("ENE_TAILSCALE_IP", "127.0.0.1")

    # Deterministic attestation over the minimal payload.
    attestation_hash = "sha256:" + hashlib.sha256(
        (pkg + ":" + timestamp + ":" + json.dumps(data, sort_keys=True, ensure_ascii=False)).encode("utf-8")
    ).hexdigest()

    return {
        "t": now.timestamp(),
        "src": src,
        "id": f"ene:{pkg}:{timestamp}",
        "op": "upsert",
        "data": {
            "pkg": pkg,
            "version": timestamp,
            "tier": tier,
            "domain": domain,
            "archetype": archetype,
            **data,
        },
        "bind": {
            "lawful": True,
            "cost": 65536,
            "invariant": "noteConsistency",
            "class": "informational_bind",
        },
        "provenance": {
            "node": node_id,
            "lake_seed": lake_seed,
            "tailscale_ip": tailscale_ip,
            "attestation_hash": attestation_hash,
            "prev_id": None,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# Ingest: Obsidian → JSON-L
# ═══════════════════════════════════════════════════════════════════════════

def ingest_obsidian(
    client: TopologicalEngineClient,
    query: str = "*",
    lake_path: Path = LAKE_PATH,
) -> Dict[str, Any]:
    """Pull notes from Obsidian vault and append to JSON-L lake."""
    print("[ingest] Searching Obsidian vault...")
    search_res = client.search_obsidian(query)
    if "error" in search_res:
        return {"error": search_res["error"]}

    notes = search_res.get("hits", search_res.get("results", search_res.get("notes", [])))
    print(f"[ingest] Found {len(notes)} notes")

    entries = []
    for note in notes:
        path = note.get("path", note.get("file_path", "unknown"))
        title = note.get("title", Path(path).stem)
        content = note.get("content", "")

        entry = _format_jsonl_entry(
            pkg=f"obsidian/note/{path}",
            data={
                "path": path,
                "title": title,
                "content_preview": content[:500],
                "content_length": len(content),
                "links": note.get("links", []),
                "tags": note.get("tags", []),
                "modified": note.get("modified", note.get("mtime")),
            },
        )
        entries.append(entry)

    with open(lake_path, "a") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    print(f"[ingest] Appended {len(entries)} entries to {lake_path}")
    return {"ingested": len(entries), "lake": str(lake_path)}


def ingest_local_obsidian(
    vault_path: Path,
    query: str = "*",
    lake_path: Path = LAKE_PATH,
) -> Dict[str, Any]:
    """Pull notes from a local Obsidian vault and append to JSON-L lake."""
    if not vault_path.exists():
        return {"error": f"Obsidian vault not found: {vault_path}"}

    print(f"[ingest:local] Reading Obsidian vault: {vault_path}")
    entries = []
    for note_path in _iter_local_notes(vault_path):
        rel_path = note_path.relative_to(vault_path).as_posix()
        content = note_path.read_text(encoding="utf-8", errors="replace")
        title = note_path.stem
        if not _matches_query(rel_path, title, content, query):
            continue

        stat = note_path.stat()
        metadata = _extract_note_metadata(content)
        entry = _format_jsonl_entry(
            pkg=_note_pkg(rel_path),
            data={
                "path": rel_path,
                "title": title,
                "content": content,
                "content_preview": content[:500],
                "content_length": len(content),
                "links": metadata["links"],
                "tags": metadata["tags"],
                "content_hash": metadata["content_hash"],
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "vault_path": str(vault_path),
            },
            src="obsidian_sync_shim.local",
        )
        entries.append(entry)

    lake_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lake_path, "a", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"[ingest:local] Appended {len(entries)} entries to {lake_path}")
    return {"ingested": len(entries), "lake": str(lake_path), "vault": str(vault_path)}


# ═══════════════════════════════════════════════════════════════════════════
# Export: JSON-L → Obsidian
# ═══════════════════════════════════════════════════════════════════════════

def export_to_obsidian(
    client: TopologicalEngineClient,
    lake_path: Path = LAKE_PATH,
    filter_domain: str = "obsidian",
) -> Dict[str, Any]:
    """Read JSON-L lake and write matching entries back to Obsidian vault."""
    if not lake_path.exists():
        return {"error": f"Lake not found: {lake_path}"}

    print(f"[export] Reading lake from {lake_path}...")
    entries = []
    with open(lake_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            data = entry.get("data", {})
            if filter_domain and data.get("domain") != filter_domain:
                continue
            entries.append(entry)

    print(f"[export] {len(entries)} entries match domain='{filter_domain}'")

    written = 0
    for entry in entries:
        data = entry.get("data", {})
        path = data.get("path")
        title = data.get("title", "Untitled")
        content_preview = data.get("content_preview", "")

        if not path:
            continue

        md = f"# {title}\n\n"
        md += f"> Synced from JSON-L lake at {datetime.now(timezone.utc).isoformat()}\n\n"
        md += content_preview
        if len(content_preview) >= 500:
            md += "\n\n...(truncated)"

        res = client.write_obsidian_note(
            path=path,
            body=md,
            metadata={
                "source": "research_stack_lake",
                "entry_id": entry.get("id"),
                "synced_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        if "error" not in res:
            written += 1

    print(f"[export] Wrote {written} notes to Obsidian vault")
    return {"exported": written}


def export_to_local_obsidian(
    vault_path: Path,
    lake_path: Path = LAKE_PATH,
    filter_domain: str = "obsidian",
    overwrite: bool = False,
) -> Dict[str, Any]:
    """Read JSON-L lake and write matching entries into a local Obsidian vault."""
    if not lake_path.exists():
        return {"error": f"Lake not found: {lake_path}"}

    vault_path.mkdir(parents=True, exist_ok=True)
    print(f"[export:local] Reading lake from {lake_path}")
    written = 0
    skipped = 0

    with open(lake_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            data = entry.get("data", {})
            if filter_domain and data.get("domain") != filter_domain:
                continue

            rel_path = data.get("path")
            if not rel_path:
                continue
            rel_path = rel_path.replace("\\", "/").lstrip("/")
            if rel_path.startswith(".obsidian/") or ".." in Path(rel_path).parts:
                skipped += 1
                continue

            target = vault_path / rel_path
            if target.exists() and not overwrite:
                skipped += 1
                continue

            content = data.get("content")
            if content is None:
                title = data.get("title", target.stem)
                content = f"# {title}\n\n> Created from JSON-L lake sync\n\n{data.get('content_preview', '')}"

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written += 1

    print(f"[export:local] Wrote {written} notes to {vault_path}; skipped {skipped}")
    return {"exported": written, "skipped": skipped, "vault": str(vault_path)}


# ═══════════════════════════════════════════════════════════════════════════
# Two-way sync
# ═══════════════════════════════════════════════════════════════════════════

def sync_bidirectional(
    client: TopologicalEngineClient,
    lake_path: Path = LAKE_PATH,
    obsidian_wins: bool = True,
) -> Dict[str, Any]:
    print("[sync] Starting bidirectional sync...")
    ingest_res = ingest_obsidian(client, lake_path=lake_path)
    if "error" in ingest_res:
        return ingest_res

    if obsidian_wins:
        print("[sync] Obsidian-wins mode: skipping overwrite of existing notes")
        search_res = client.search_obsidian("*")
        existing_paths = set()
        for note in search_res.get("results", search_res.get("notes", [])):
            existing_paths.add(note.get("path", note.get("file_path")))

        if lake_path.exists():
            entries = []
            with open(lake_path) as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    path = entry.get("data", {}).get("path")
                    if path and path not in existing_paths:
                        entries.append(entry)

            written = 0
            for entry in entries:
                data = entry.get("data", {})
                path = data.get("path")
                title = data.get("title", "Untitled")
                md = f"# {title}\n\n> Created from JSON-L lake sync\n\n{data.get('content_preview', '')}"
                res = client.write_obsidian_note(path=path, body=md)
                if "error" not in res:
                    written += 1
            print(f"[sync] Created {written} missing notes in Obsidian")
            return {"ingested": ingest_res["ingested"], "created": written}

    export_res = export_to_obsidian(client, lake_path=lake_path)
    return {"ingested": ingest_res["ingested"], **export_res}


def sync_local_bidirectional(
    vault_path: Path,
    lake_path: Path = LAKE_PATH,
    obsidian_wins: bool = True,
) -> Dict[str, Any]:
    print("[sync:local] Starting bidirectional local sync")
    ingest_res = ingest_local_obsidian(vault_path=vault_path, lake_path=lake_path)
    if "error" in ingest_res:
        return ingest_res
    export_res = export_to_local_obsidian(
        vault_path=vault_path,
        lake_path=lake_path,
        overwrite=not obsidian_wins,
    )
    if "error" in export_res:
        return export_res
    return {**ingest_res, **export_res}


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Obsidian ↔ JSON-L lake sync shim")
    parser.add_argument(
        "mode",
        choices=["ingest", "export", "sync"],
        default="sync",
        nargs="?",
        help="ingest=Obsidian→lake, export=lake→Obsidian, sync=both",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "local", "engine"],
        default="auto",
        help="local=filesystem vault, engine=topological engine, auto=engine if healthy else local",
    )
    parser.add_argument(
        "--vault",
        default=None,
        help="Local Obsidian vault path; defaults to OBSIDIAN_VAULT_PATH or ./Obdisidan connector",
    )
    parser.add_argument("--lake", default=str(LAKE_PATH), help="Path to JSON-L lake file")
    parser.add_argument("--query", default="*", help="Obsidian search query (ingest mode)")
    parser.add_argument(
        "--obsidian-wins",
        action="store_true",
        default=True,
        help="In sync mode, don't overwrite existing Obsidian notes",
    )
    parser.add_argument("--lake-wins", action="store_true", help="In sync mode, overwrite Obsidian with lake")
    args = parser.parse_args()

    lake_path = Path(args.lake)
    obsidian_wins = not args.lake_wins
    vault_path = _vault_path(args.vault)

    backend = args.backend
    client = None
    if backend in ("auto", "engine"):
        client = TopologicalEngineClient()
        health = client.health()
        engine_ok = bool(health.get("ok", False) or health.get("healthy", False))
        if not engine_ok:
            if backend == "engine":
                print(f"Topological engine unhealthy: {health.get('error', 'unknown')}")
                sys.exit(1)
            print(f"[auto] Topological engine unavailable; using local vault: {vault_path}")
            backend = "local"
        else:
            backend = "engine"

    if backend == "local":
        if args.mode == "ingest":
            result = ingest_local_obsidian(vault_path=vault_path, query=args.query, lake_path=lake_path)
        elif args.mode == "export":
            result = export_to_local_obsidian(vault_path=vault_path, lake_path=lake_path, overwrite=not obsidian_wins)
        else:
            result = sync_local_bidirectional(vault_path=vault_path, lake_path=lake_path, obsidian_wins=obsidian_wins)
    else:
        if args.mode == "ingest":
            result = ingest_obsidian(client, query=args.query, lake_path=lake_path)
        elif args.mode == "export":
            result = export_to_obsidian(client, lake_path=lake_path)
        else:
            result = sync_bidirectional(client, lake_path=lake_path, obsidian_wins=obsidian_wins)

    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"Done: {json.dumps(result, indent=2)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
