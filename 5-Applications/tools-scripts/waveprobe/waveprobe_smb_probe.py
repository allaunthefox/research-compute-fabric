#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=STORE / DOMAIN=DATA / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
waveprobe_smb_probe.py — Hash and index Windows SMB share mounts into the substrate.

Walks /mnt/{ddrive,edrive,fdrive,gdrive,hdrive,zdrive}, SHA-256 hashes every
file, writes a per-drive JSONL manifest to 5-Applications/out/smb_index/, and feeds
text-readable files into the substrate SQLite index (same schema as ingest_archive).

Usage:
    python3 5-Applications/scripts/waveprobe_smb_probe.py                  # all mounted drives
    python3 5-Applications/scripts/waveprobe_smb_probe.py --drives ddrive edrive
    python3 5-Applications/scripts/waveprobe_smb_probe.py --dry-run
    python3 5-Applications/scripts/waveprobe_smb_probe.py --force          # re-index existing rows
    python3 5-Applications/scripts/waveprobe_smb_probe.py --hash-only      # manifests only, no SQLite
    python3 5-Applications/scripts/waveprobe_smb_probe.py --status         # show index counts

Environment:
    SUBSTRATE_DB   path to substrate_index.db  (default: repo root)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from substrate_git_index import DB_PATH, _open_db, _concept_vector_from_weights, _upsert_package, _PHI  # type: ignore

try:
    from ingest_text_hygiene import derive_safe_description  # type: ignore
except ImportError:
    def derive_safe_description(path: Path, text: str, max_len: int = 200) -> str:  # type: ignore[misc]
        return (text[:max_len].replace("\n", " ").strip() + "…") if len(text) > max_len else text.strip()

# ─── configuration ────────────────────────────────────────────────────────────

SMB_DRIVES = ["ddrive", "edrive", "fdrive", "gdrive", "hdrive", "zdrive"]
MOUNT_BASE = Path("/mnt")
OUT_DIR = ROOT / "out" / "smb_index"

# Extensions considered text-readable and worth keyword-indexing
TEXT_EXTENSIONS = {
    ".md", ".txt", ".rst", ".json", ".jsonl", ".py", ".sh", ".rs", ".c", ".h",
    ".csv", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml", ".html", ".js",
    ".ts", ".bat", ".ps1", ".log",
}

# Binary extensions — hashed but not keyword-indexed
BINARY_EXTENSIONS = {
    ".exe", ".dll", ".sys", ".bin", ".iso", ".img", ".zip", ".7z", ".rar",
    ".tar", ".gz", ".bz2", ".xz", ".cab", ".msi", ".msu",
    ".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac",
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
    ".pdf", ".docx", ".xlsx", ".pptx", ".odt",
    ".db", ".sqlite", ".mdb",
}

# Max bytes read for keyword extraction from text files
READ_LIMIT = 8192

# Skip depth-unlimited system/junk paths
SKIP_PATTERNS = [
    r"[\\/]\$Recycle\.Bin[\\/]",
    r"[\\/]System Volume Information[\\/]",
    r"[\\/]Windows[\\/]",
    r"[\\/]\.git[\\/]",
    r"[\\/]__pycache__[\\/]",
    r"[\\/]node_modules[\\/]",
    r"[\\/]\.Trash",
]
_SKIP_RE = re.compile("|".join(SKIP_PATTERNS), re.IGNORECASE)

# ─── keyword clusters (14-axis, matches substrate_git_index vocabulary) ───────

_CLUSTER_VOCAB: set[str] = {
    "substrate", "foam", "soliton", "resonance", "tsm", "metafoam",
    "graph", "dag", "node", "edge", "merkle", "hash",
    "compute", "cpu", "gpu", "neural", "inference", "model",
    "token", "omnitoken", "swap", "arbitrage", "mev", "defi",
    "rule", "policy", "audit", "compliance", "legal",
    "store", "index", "database", "sqlite", "manifest",
    "power", "energy", "battery", "stirling",
    "clock", "timing", "synchronize",
    "comms", "transport", "udp", "ipv6", "i2p", "tunnel",
    "material", "superconductor", "qchem", "crystal",
    "compress", "codec", "huffman", "entropy",
    "crypto", "sha256", "zk", "stark", "proof",
    "data", "dataset", "corpus", "archive",
    "test", "validation", "benchmark",
}

_STOP: set[str] = {
    "the", "and", "for", "that", "this", "with", "from", "are",
    "was", "were", "have", "been", "will", "would", "could", "should",
    "which", "their", "there", "these", "those", "what", "when",
    "where", "how", "all", "any", "can", "not", "but", "also",
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            while True:
                block = f.read(chunk)
                if not block:
                    break
                h.update(block)
    except (PermissionError, OSError):
        return ""
    return h.hexdigest()


def _should_skip(path: Path) -> bool:
    return bool(_SKIP_RE.search(str(path)))


def _read_head(path: Path) -> str:
    try:
        with path.open("rb") as f:
            raw = f.read(READ_LIMIT)
        return raw.decode("utf-8", errors="replace")
    except (PermissionError, OSError):
        return ""


def _extract_keywords(text: str) -> dict[str, float]:
    tokens = re.findall(r"\b[a-zA-Z][a-zA-Z_]{4,}\b", text.lower())
    counts: Counter[str] = Counter(t for t in tokens if t not in _STOP)
    if not counts:
        return {}
    max_c = counts.most_common(1)[0][1]
    weights: dict[str, float] = {}
    for word, count in counts.most_common(30):
        boost = 2.0 if word in _CLUSTER_VOCAB else 1.0
        score = min(1.0, (count / max_c) * boost * 0.85)
        if score >= 0.10:
            weights[word] = round(score, 3)
    return weights


def _pkg_name(drive: str, path: Path) -> str:
    try:
        rel = path.relative_to(MOUNT_BASE / drive)
    except ValueError:
        rel = Path(path.name)
    parts = [re.sub(r"[^a-z0-9]", "", p.lower())[:8] for p in rel.parts[:-1]]
    stem = re.sub(r"[^a-z0-9]+", "_", path.stem.lower())[:40]
    prefix = "-".join(p for p in parts if p)[:20]
    tag = f"smb-{drive}-{prefix}-{stem}" if prefix else f"smb-{drive}-{stem}"
    return tag[:80]


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─── per-file index ───────────────────────────────────────────────────────────

def index_file(
    drive: str,
    path: Path,
    conn: sqlite3.Connection,
    file_sha: str,
    force: bool,
    dry_run: bool,
) -> str:
    """Index a single text file into substrate SQLite. Returns 'indexed'/'exists'/'skipped'/'dry'."""
    pkg = _pkg_name(drive, path)
    version = "1.0.0"

    if not force:
        row = conn.execute(
            "SELECT pkg FROM packages WHERE pkg=? AND version=?", (pkg, version)
        ).fetchone()
        if row:
            return "exists"

    text = _read_head(path)
    if not text.strip():
        return "skipped"

    idea_weights = _extract_keywords(text)
    if not idea_weights:
        return "skipped"

    now = _now_utc()
    concept_vec = _concept_vector_from_weights(idea_weights)
    foam_score = round(sum(idea_weights.values()) / max(len(idea_weights), 1) * _PHI, 4)
    description = derive_safe_description(path, text, max_len=200)

    concept_anchor = {
        "domain": "data",
        "concept": path.stem[:60],
        "resolution": "FORMING",
    }
    tags = ["smb", drive, path.suffix.lstrip(".") or "bin"]

    if dry_run:
        print(f"  [dry] {pkg}  foam={foam_score}  axes={sum(1 for x in concept_vec if x > 0.01)}/14")
        return "dry"

    _upsert_package(conn, {
        "pkg": pkg,
        "version": version,
        "layer": "STORE",
        "domain": "DATA",
        "condition": "EXPERIMENTAL",
        "stage": "INTAKE",
        "source": "DATA",
        "tier": "RESEARCH",
        "module": path.stem[:40].upper().replace(" ", "_").replace("-", "_"),
        "archetype": "SMB_NODE",
        "tags": json.dumps(tags),
        "description": description,
        "files": json.dumps([str(path)]),
        "depends": json.dumps([]),
        "foam_score": foam_score,
        "nd_point": json.dumps(concept_vec[:14]),
        "sha256": file_sha,
        "sealed_utc": now,
        "visibility": "PRIVATE",
        "model_status": "REFERENCE_ONLY",
        "taint_status": "CLEAN",
        "session_id": f"smb:{drive}:{path.relative_to(MOUNT_BASE / drive)}",
        "idea_weights": json.dumps(idea_weights),
        "extension_points": json.dumps([]),
        "concept_vector": json.dumps(concept_vec),
        "analog_map": json.dumps({}),
        "concept_anchor": json.dumps(concept_anchor),
        "attachment_meta": json.dumps({}),
        "ingest_profile": json.dumps({
            "ingestor": "smb_probe",
            "drive": drive,
            "suffix": path.suffix.lower(),
            "text_chars": len(text),
        }),
        "indexed_utc": now,
    })
    return "indexed"


# ─── drive scanner ────────────────────────────────────────────────────────────

def scan_drive(
    drive: str,
    conn: sqlite3.Connection | None,
    force: bool,
    dry_run: bool,
    hash_only: bool,
) -> dict[str, Any]:
    """Scan one mounted drive. Returns summary dict."""
    mount = MOUNT_BASE / drive
    if not mount.is_mount():
        print(f"  [{drive}] NOT MOUNTED — skipping")
        return {"drive": drive, "mounted": False}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / f"{drive}_manifest.jsonl"
    counts: Counter[str] = Counter()
    total_bytes = 0
    manifest_lines: list[str] = []

    print(f"  [{drive}] scanning {mount} …")
    for path in sorted(mount.rglob("*")):
        if not path.is_file():
            continue
        if _should_skip(path):
            counts["skipped_system"] += 1
            continue

        suffix = path.suffix.lower()
        try:
            size = path.stat().st_size
        except OSError:
            counts["error"] += 1
            continue

        file_sha = _sha256_file(path)
        if not file_sha:
            counts["error"] += 1
            continue

        total_bytes += size
        counts["hashed"] += 1

        record: dict[str, Any] = {
            "drive": drive,
            "path": str(path.relative_to(MOUNT_BASE / drive)),
            "name": path.name,
            "suffix": suffix,
            "size_bytes": size,
            "sha256": file_sha,
            "indexed_utc": _now_utc(),
        }
        manifest_lines.append(json.dumps(record))

        # Keyword-index text files into SQLite
        if not hash_only and conn is not None and suffix in TEXT_EXTENSIONS:
            status = index_file(drive, path, conn, file_sha, force, dry_run)
            counts[f"sqlite_{status}"] += 1

        if counts["hashed"] % 500 == 0:
            print(f"    {counts['hashed']} files hashed …")
            if conn and not dry_run:
                conn.commit()

    # Write manifest
    if not dry_run:
        with manifest_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(manifest_lines))
            if manifest_lines:
                f.write("\n")
        print(f"    manifest → {manifest_path}  ({len(manifest_lines)} records)")

    mb = total_bytes / (1024 * 1024)
    print(
        f"  [{drive}] done  hashed={counts['hashed']}  "
        f"size={mb:.1f} MiB  "
        f"sqlite_indexed={counts.get('sqlite_indexed', 0)}  "
        f"sqlite_exists={counts.get('sqlite_exists', 0)}  "
        f"errors={counts.get('error', 0)}"
    )
    return {
        "drive": drive,
        "mounted": True,
        "total_files": counts["hashed"],
        "total_bytes": total_bytes,
        "manifest": str(manifest_path) if not dry_run else None,
        "counts": dict(counts),
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drives", nargs="+", default=SMB_DRIVES,
                    metavar="DRIVE", help=f"Drives to scan (default: {' '.join(SMB_DRIVES)})")
    ap.add_argument("--dry-run", action="store_true",
                    help="Hash files and show what would be indexed; don't write anything")
    ap.add_argument("--force", action="store_true",
                    help="Re-index rows that already exist in the DB")
    ap.add_argument("--hash-only", action="store_true",
                    help="Write JSONL manifests only; skip SQLite indexing")
    ap.add_argument("--status", action="store_true",
                    help="Show SMB node counts in the index and exit")
    ap.add_argument("--db", default=str(DB_PATH), metavar="PATH",
                    help="Path to substrate SQLite DB")
    args = ap.parse_args()

    if args.status:
        conn = _open_db(Path(args.db))
        total = conn.execute("SELECT COUNT(*) FROM packages").fetchone()[0]
        smb = conn.execute(
            "SELECT COUNT(*) FROM packages WHERE archetype='SMB_NODE'"
        ).fetchone()[0]
        drives_q = conn.execute(
            "SELECT json_extract(ingest_profile,'$.drive'), COUNT(*) "
            "FROM packages WHERE archetype='SMB_NODE' "
            "GROUP BY json_extract(ingest_profile,'$.drive')"
        ).fetchall()
        conn.close()
        print(f"Total substrate nodes : {total}")
        print(f"SMB nodes             : {smb}")
        for drive, count in sorted(drives_q):
            print(f"  {drive or '?':<12} {count}")
        return

    conn: sqlite3.Connection | None = None
    if not args.hash_only and not args.dry_run:
        conn = _open_db(Path(args.db))

    results: list[dict[str, Any]] = []
    for drive in args.drives:
        results.append(scan_drive(drive, conn, args.force, args.dry_run, args.hash_only))

    if conn and not args.dry_run:
        conn.commit()
        conn.close()

    mounted = [r for r in results if r.get("mounted")]
    total_files = sum(r.get("total_files", 0) for r in mounted)
    total_bytes = sum(r.get("total_bytes", 0) for r in mounted)
    print(
        f"\nSummary: {len(mounted)}/{len(results)} drives mounted  "
        f"total={total_files} files  {total_bytes / (1024**3):.2f} GiB"
    )


if __name__ == "__main__":
    main()
