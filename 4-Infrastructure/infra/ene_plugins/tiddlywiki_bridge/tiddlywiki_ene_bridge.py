#!/usr/bin/env python3
"""TiddlyWiki-to-ENE bridge plugin.

This module is deliberately standalone today and plugin-loader friendly later.
It scans `.tid` files, builds deterministic ENE package records, and can upsert
them into the current `packages` table shape without requiring the planned ENE
revamp to exist yet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLUGIN_ID = "ene.tiddlywiki.bridge"
PLUGIN_VERSION = "0.1.0"
INTERFACE_VERSION = "ene-plugin-v0"

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_TIDDLER_DIR = REPO_ROOT / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"
DEFAULT_DB_PATH = REPO_ROOT / "data" / "substrate_index.db"
MAX_TIDDLER_BYTES = 512_000
LINK_RE = re.compile(r"\[\[([^\[\]\n|#]+)(?:[#|][^\[\]\n]*)?\]\]")


@dataclass(frozen=True)
class TiddlerRecord:
    path: str
    title: str
    fields: dict[str, str]
    text: str
    tags: list[str]
    links: list[str]
    source_sha256: str
    bytes: int


@dataclass(frozen=True)
class ENEPackagePlan:
    pkg: str
    version: str
    tier: str
    domain: str
    archetype: str
    description: str
    tags: list[str]
    source: str
    sha256: str
    indexed_utc: str
    concept_anchor: dict[str, Any]
    concept_vector: list[float]
    idea_weights: dict[str, float]
    analog_map: dict[str, Any]
    files: list[str]
    verification_basis: str
    quality_status: str
    audit_rationale: str
    meta_capsule: dict[str, Any]
    meta_capsule_hash: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def slugify(title: str) -> str:
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9._ -]+", "", slug)
    slug = re.sub(r"\s+", "_", slug).strip("_")
    return slug or hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]


def split_tags(raw: str) -> list[str]:
    if not raw:
        return []
    tags: list[str] = []
    token = ""
    bracketed = False
    i = 0
    while i < len(raw):
        if raw.startswith("[[", i):
            bracketed = True
            i += 2
            continue
        if raw.startswith("]]", i) and bracketed:
            if token.strip():
                tags.append(token.strip())
            token = ""
            bracketed = False
            i += 2
            continue
        ch = raw[i]
        if ch.isspace() and not bracketed:
            if token.strip():
                tags.append(token.strip())
            token = ""
        else:
            token += ch
        i += 1
    if token.strip():
        tags.append(token.strip())
    return sorted(set(tags), key=str.lower)


def extract_links(text: str) -> list[str]:
    links = []
    for match in LINK_RE.finditer(text):
        target = " ".join(match.group(1).strip().split())
        if target and not target.lower().startswith("category:"):
            links.append(target)
    return sorted(set(links), key=str.lower)


def parse_tid_file(path: Path) -> TiddlerRecord:
    data = path.read_bytes()
    if len(data) > MAX_TIDDLER_BYTES:
        raise ValueError(f"tiddler too large: {path}")
    raw = data.decode("utf-8", errors="replace")
    lower = raw.lower()
    if "<script" in lower or "javascript:" in lower:
        raise ValueError(f"active script content refused: {path}")

    fields: dict[str, str] = {}
    body_lines: list[str] = []
    in_fields = True
    for line in raw.splitlines():
        if in_fields:
            if not line.strip():
                in_fields = False
                continue
            if ":" not in line:
                in_fields = False
                body_lines.append(line)
                continue
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
        else:
            body_lines.append(line)

    title = fields.get("title") or path.stem.replace("_", " ")
    title = " ".join(title.strip().split())
    if not title:
        raise ValueError(f"missing title: {path}")
    text = "\n".join(body_lines).strip()
    tags = split_tags(fields.get("tags", ""))
    links = extract_links(text)
    return TiddlerRecord(
        path=str(path.relative_to(REPO_ROOT)),
        title=title,
        fields=fields,
        text=text,
        tags=tags,
        links=links,
        source_sha256=sha256_bytes(data),
        bytes=len(data),
    )


def concept_vector(record: TiddlerRecord) -> list[float]:
    haystack = f"{record.title}\n{record.text}\n{' '.join(record.tags)}".lower()
    axes = [0.0] * 14
    term_groups = {
        0: ["substrate", "foam", "entropy"],
        1: ["compression", "hutter", "codec", "shifter"],
        2: ["physics", "thermal", "energy", "material", "ferrite"],
        3: ["neural", "semantic", "manifold", "eigenvector"],
        4: ["lean", "proof", "theorem", "formal"],
        6: ["safety", "audit", "quarantine", "claimboundary"],
        7: ["receipt", "hash", "provenance", "attestation"],
        8: ["hardware", "fpga", "gpu", "hdmi", "usb"],
        9: ["signal", "dsp", "tmds", "wave"],
        10: ["bio", "dna", "rna", "codon", "genomic"],
        11: ["route", "search", "planning", "decision"],
        12: ["archive", "history", "backlog", "dump"],
        13: ["identity", "sovereign", "operator"],
    }
    for axis, terms in term_groups.items():
        axes[axis] = min(1.0, sum(haystack.count(term) for term in terms) / 8.0)
    axes[7] = min(1.0, axes[7] + len(record.links) / 32.0)
    if not any(axes):
        axes[12] = 1.0
    norm = sum(value * value for value in axes) ** 0.5
    return [round(value / norm, 6) if norm else 0.0 for value in axes]


def build_plan(record: TiddlerRecord, indexed_utc: str | None = None) -> ENEPackagePlan:
    slug = slugify(record.title)
    indexed = indexed_utc or utc_now()
    modified = record.fields.get("modified") or record.fields.get("created") or indexed.replace("-", "").replace(":", "")
    version = f"{modified}-{record.source_sha256[:12]}"
    pkg = f"ene/tiddlywiki/{slug}"
    vector = concept_vector(record)
    meta_capsule = {
        "plugin_id": PLUGIN_ID,
        "plugin_version": PLUGIN_VERSION,
        "interface_version": INTERFACE_VERSION,
        "title": record.title,
        "path": record.path,
        "fields": record.fields,
        "links": record.links,
        "bytes": record.bytes,
        "source_sha256": record.source_sha256,
    }
    receipt_payload = {
        "pkg": pkg,
        "version": version,
        "source_sha256": record.source_sha256,
        "plugin_id": PLUGIN_ID,
        "plugin_version": PLUGIN_VERSION,
    }
    receipt = sha256_bytes(canonical_json(receipt_payload).encode("utf-8"))
    meta_hash = sha256_bytes(canonical_json(meta_capsule).encode("utf-8"))
    body_preview = " ".join(record.text.split())[:240] or record.title
    tags = sorted(set(["ene", "tiddlywiki", "wiki", *record.tags]), key=str.lower)
    return ENEPackagePlan(
        pkg=pkg,
        version=version,
        tier="RESEARCH",
        domain="wiki",
        archetype="tiddlywiki_tiddler",
        description=body_preview,
        tags=tags,
        source=PLUGIN_ID,
        sha256=record.source_sha256,
        indexed_utc=indexed,
        concept_anchor={
            "domain": "wiki",
            "concept": slug,
            "resolution": "FORMING",
            "source_plugin": PLUGIN_ID,
        },
        concept_vector=vector,
        idea_weights={
            "wiki_link_count": min(1.0, len(record.links) / 24.0),
            "body_size": min(1.0, record.bytes / 32_000.0),
        },
        analog_map={
            "tiddlywiki": record.title,
            "source_path": record.path,
            "plugin_receipt": receipt,
        },
        files=[record.path],
        verification_basis=f"tiddlywiki_bridge_receipt:{receipt}",
        quality_status="candidate",
        audit_rationale="Imported from TiddlyWiki tiddler by hotswap bridge plugin; content remains FORMING until separately verified.",
        meta_capsule=meta_capsule,
        meta_capsule_hash=meta_hash,
    )


def scan_tiddlers(
    tiddler_dir: Path,
    include_system: bool = False,
) -> tuple[list[ENEPackagePlan], list[dict[str, str]]]:
    plans: list[ENEPackagePlan] = []
    errors: list[dict[str, str]] = []
    for path in sorted(tiddler_dir.glob("*.tid")):
        try:
            record = parse_tid_file(path)
            if record.title.startswith("$:/") and not include_system:
                continue
            plans.append(build_plan(record))
        except Exception as exc:  # keep scans resilient; errors become receipts
            errors.append({"path": str(path), "error": str(exc)})
    return plans, errors


def ensure_plugin_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ene_plugin_state (
            plugin_id TEXT NOT NULL,
            source_path TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            package_id TEXT NOT NULL,
            package_version TEXT NOT NULL,
            receipt TEXT NOT NULL,
            updated_utc TEXT NOT NULL,
            PRIMARY KEY (plugin_id, source_path)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ene_plugin_events (
            event_id TEXT PRIMARY KEY,
            plugin_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_utc TEXT NOT NULL
        )
        """
    )


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def ensure_packages_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS packages (
            pkg TEXT NOT NULL,
            version TEXT NOT NULL,
            tier TEXT,
            domain TEXT,
            archetype TEXT,
            tags TEXT,
            description TEXT,
            files TEXT,
            source TEXT,
            sha256 TEXT,
            indexed_utc TEXT,
            verification_basis TEXT,
            concept_anchor TEXT,
            concept_vector TEXT,
            idea_weights TEXT,
            analog_map TEXT,
            quality_status TEXT,
            audit_rationale TEXT,
            meta_capsule TEXT,
            meta_capsule_hash TEXT,
            PRIMARY KEY (pkg, version)
        )
        """
    )


def upsert_plan(conn: sqlite3.Connection, plan: ENEPackagePlan) -> None:
    ensure_packages_table(conn)
    columns = table_columns(conn, "packages")
    raw = asdict(plan)
    encoded = {
        key: canonical_json(value) if isinstance(value, (dict, list)) else value
        for key, value in raw.items()
        if key in columns
    }
    keys = list(encoded)
    placeholders = ", ".join("?" for _ in keys)
    update_keys = [key for key in keys if key not in {"pkg", "version"}]
    assignments = ", ".join(f"{key}=excluded.{key}" for key in update_keys)
    sql = f"INSERT INTO packages ({', '.join(keys)}) VALUES ({placeholders})"
    if assignments:
        sql += f" ON CONFLICT(pkg, version) DO UPDATE SET {assignments}"
    conn.execute(sql, [encoded[key] for key in keys])

    receipt = plan.verification_basis.split(":", 1)[-1]
    conn.execute(
        """
        INSERT INTO ene_plugin_state
        (plugin_id, source_path, source_sha256, package_id, package_version, receipt, updated_utc)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(plugin_id, source_path) DO UPDATE SET
          source_sha256 = excluded.source_sha256,
          package_id = excluded.package_id,
          package_version = excluded.package_version,
          receipt = excluded.receipt,
          updated_utc = excluded.updated_utc
        """,
        (
            PLUGIN_ID,
            plan.files[0] if plan.files else plan.pkg,
            plan.sha256,
            plan.pkg,
            plan.version,
            receipt,
            plan.indexed_utc,
        ),
    )


def ingest(plans: list[ENEPackagePlan], db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        ensure_plugin_tables(conn)
        for plan in plans:
            upsert_plan(conn, plan)
        event_payload = {
            "plugin_id": PLUGIN_ID,
            "count": len(plans),
            "packages": [plan.pkg for plan in plans],
        }
        event_hash = sha256_bytes(canonical_json(event_payload).encode("utf-8"))
        conn.execute(
            """
            INSERT OR REPLACE INTO ene_plugin_events
            (event_id, plugin_id, event_type, payload, created_utc)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                f"{PLUGIN_ID}:{event_hash}",
                PLUGIN_ID,
                "ingest",
                canonical_json(event_payload),
                utc_now(),
            ),
        )
    return len(plans)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan or ingest TiddlyWiki tiddlers into ENE packages.")
    parser.add_argument("--tiddlers", type=Path, default=DEFAULT_TIDDLER_DIR)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without mutating ENE.")
    parser.add_argument("--ingest", action="store_true", help="Commit planned writes to ENE.")
    parser.add_argument("--limit", type=int, default=0, help="Limit planned records for smoke tests.")
    parser.add_argument("--include-system", action="store_true", help="Include TiddlyWiki $:/ system tiddlers.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a short human summary.")
    args = parser.parse_args()

    plans, errors = scan_tiddlers(args.tiddlers, include_system=args.include_system)
    if args.limit:
        plans = plans[: max(0, args.limit)]

    committed = 0
    if args.ingest:
        committed = ingest(plans, args.db)

    result = {
        "plugin_id": PLUGIN_ID,
        "plugin_version": PLUGIN_VERSION,
        "interface_version": INTERFACE_VERSION,
        "tiddler_dir": str(args.tiddlers),
        "db_path": str(args.db),
        "planned": len(plans),
        "committed": committed,
        "errors": errors,
        "packages": [asdict(plan) for plan in plans],
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        mode = "ingest" if args.ingest else "dry-run"
        print(f"{PLUGIN_ID} {mode}: planned={len(plans)} committed={committed} errors={len(errors)}")
        for plan in plans[:10]:
            print(f"- {plan.pkg}@{plan.version} <- {plan.files[0] if plan.files else ''}")
        if len(plans) > 10:
            print(f"... {len(plans) - 10} more")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
