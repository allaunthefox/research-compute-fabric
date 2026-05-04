#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=STORE / DOMAIN=DRIVE / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
Drive Indexer — Walk Windows share mount points and hash/index files via Waveprobe.

Usage:
    python3 drive_indexer.py index /mnt/zdrive [/mnt/other ...]
    python3 drive_indexer.py index /mnt/zdrive --share-name zdrive --ext .mp4 .mkv
    python3 drive_indexer.py status
    python3 drive_indexer.py ls --share zdrive

Each file is stored in packages as:
    pkg     = "drive:<share_name>:<rel_path>"
    version = sha256[:16]

Files already indexed at the same sha256 are skipped. Changed files
(same path, different sha256) get a new version row; the old row stays.

The script writes progress to stdout and appends a summary line to
metrics.log on completion.
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Resolve paths relative to this script's repo root
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DB_PATH = REPO_ROOT / "substrate_index.db"
METRICS_LOG = REPO_ROOT / "metrics.log"

# Waveprobe imports from germane/tools/
sys.path.insert(0, str(REPO_ROOT / "germane" / "tools"))
from waveprobe_hasher import hash_file, store_waveprobe_states  # noqa: E402

CHUNK_SIZE = 64 * 1024  # 64 KB

# File extensions to skip (binary noise, OS artifacts)
SKIP_EXTENSIONS = {
    ".tmp", ".part", ".crdownload", ".db-wal", ".db-shm",
    "thumbs.db", ".ds_store", ".lnk", "desktop.ini",
}

SKIP_NAMES_LOWER = {"thumbs.db", "desktop.ini", ".ds_store"}


def sha256_file(path: Path, buf_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                block = f.read(buf_size)
                if not block:
                    break
                h.update(block)
    except OSError:
        return ""
    return h.hexdigest()


def share_name_from_path(root: Path) -> str:
    """Derive a share name from the mount-point directory name."""
    return root.name.lower().replace(" ", "_")


def iter_files(root: Path, extensions: set | None):
    """Yield (abs_path, rel_path_str) for every regular file under root."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Skip hidden dirs in-place
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.lower() in SKIP_NAMES_LOWER:
                continue
            p = Path(dirpath) / name
            if p.suffix.lower() in SKIP_EXTENSIONS:
                continue
            if extensions and p.suffix.lower() not in extensions:
                continue
            rel = p.relative_to(root).as_posix()
            yield p, rel


def already_indexed(cursor: sqlite3.Cursor, pkg: str, sha256: str) -> bool:
    """Return True if this exact (pkg, sha256[:16]) pair exists."""
    cursor.execute(
        "SELECT 1 FROM packages WHERE pkg = ? AND version = ? LIMIT 1",
        (pkg, sha256[:16]),
    )
    return cursor.fetchone() is not None


def insert_drive_file(
    db: sqlite3.Connection,
    share: str,
    rel: str,
    abs_path: Path,
    sha256: str,
    file_size: int,
    waveprobe_result: dict,
) -> None:
    pkg = f"drive:{share}:{rel}"
    version = sha256[:16]
    now = datetime.now(timezone.utc).isoformat()

    merkle_root = waveprobe_result["merkle_root"]
    first_sig = json.dumps(waveprobe_result["chunks"][0]) if waveprobe_result["chunks"] else "{}"

    # Insert package row (INSERT OR IGNORE — don't clobber existing)
    db.execute(
        """
        INSERT OR IGNORE INTO packages
            (pkg, version, layer, domain, condition, stage, source, tier,
             files, sha256, indexed_utc, description,
             waveprobe_sig, merkle_root, safe_pool_entry)
        VALUES (?, ?, 'STORE', 'DRIVE', 'STABLE', 'ACTIVE', 'DATA', 'FOAM',
                ?, ?, ?, ?,
                ?, ?, 0)
        """,
        (
            pkg, version,
            json.dumps([str(abs_path)]),
            sha256,
            now,
            f"{share}/{rel} ({file_size} bytes)",
            first_sig,
            merkle_root,
        ),
    )

    # Store waveprobe states + merkle tree
    store_waveprobe_states(db, pkg, version, waveprobe_result)


def cmd_index(args):
    roots = [Path(p) for p in args.paths]
    extensions = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.ext} if args.ext else None

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    cursor = db.cursor()

    total_files = 0
    total_skipped = 0
    total_errors = 0
    total_bytes = 0
    t0 = time.monotonic()

    for root in roots:
        if not root.exists():
            print(f"[!] Path not found: {root} — is the share mounted?", flush=True)
            continue

        share = args.share_name if args.share_name and len(roots) == 1 else share_name_from_path(root)
        print(f"[*] Indexing share '{share}' from {root}", flush=True)

        batch = 0
        for abs_path, rel in iter_files(root, extensions):
            try:
                file_size = abs_path.stat().st_size
            except OSError as e:
                print(f"  [!] stat error: {rel}: {e}", flush=True)
                total_errors += 1
                continue

            pkg = f"drive:{share}:{rel}"
            sha256 = sha256_file(abs_path)
            if not sha256:
                print(f"  [!] read error: {rel}", flush=True)
                total_errors += 1
                continue

            if already_indexed(cursor, pkg, sha256):
                total_skipped += 1
                continue

            try:
                wp = hash_file(str(abs_path), CHUNK_SIZE)
            except Exception as e:
                print(f"  [!] waveprobe error: {rel}: {e}", flush=True)
                total_errors += 1
                continue

            insert_drive_file(db, share, rel, abs_path, sha256, file_size, wp)
            total_files += 1
            total_bytes += file_size
            batch += 1

            mb_root = wp["merkle_root"][:12]
            ratio = max(wp["chunks"], key=lambda c: c["compression_ratio"])["compression_ratio"] if wp["chunks"] else 0.0
            print(f"  [{total_files:6d}] {rel[:60]:<60} {file_size//1024:>8} KB  "
                  f"merkle={mb_root}  ratio={ratio:.2f}x", flush=True)

            if batch >= 50:
                db.commit()
                batch = 0

    db.commit()
    db.close()

    elapsed = time.monotonic() - t0
    throughput = total_bytes / max(elapsed, 0.001) / 1e6

    summary = (
        f"drive_indexer finished: {total_files} indexed, {total_skipped} skipped, "
        f"{total_errors} errors, {total_bytes/1e9:.2f} GB, "
        f"{throughput:.1f} MB/s, {elapsed:.1f}s"
    )
    print(f"\n[+] {summary}", flush=True)

    with open(METRICS_LOG, "a") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} {summary}\n")


def cmd_status(args):
    db = sqlite3.connect(DB_PATH)
    rows = db.execute(
        """
        SELECT
            substr(pkg, 7, instr(substr(pkg, 7), ':') - 1) AS share,
            COUNT(*) AS files,
            SUM(CAST(json_extract(description, '$') IS NULL AS INT)) AS no_desc
        FROM packages
        WHERE domain = 'DRIVE'
        GROUP BY share
        ORDER BY share
        """
    ).fetchall()
    db.close()

    if not rows:
        print("No drive files indexed yet.")
        return

    print(f"{'Share':<20} {'Files':>8}")
    print("-" * 30)
    for share, count, _ in rows:
        print(f"{share:<20} {count:>8}")


def cmd_ls(args):
    db = sqlite3.connect(DB_PATH)
    q = "SELECT pkg, version, sha256, indexed_utc, description FROM packages WHERE domain = 'DRIVE'"
    params = []
    if args.share:
        q += " AND pkg LIKE ?"
        params.append(f"drive:{args.share}:%")
    if args.ext:
        ext = args.ext if args.ext.startswith(".") else f".{args.ext}"
        q += " AND pkg LIKE ?"
        params.append(f"%{ext}")
    q += " ORDER BY pkg LIMIT 200"
    rows = db.execute(q, params).fetchall()
    db.close()

    for pkg, ver, sha256, ts, desc in rows:
        sha_short = (sha256 or "")[:12]
        print(f"{pkg}  @{ver}  sha={sha_short}  {ts}  {desc or ''}")


def main():
    parser = argparse.ArgumentParser(description="Drive Indexer — Waveprobe hash+index for Windows shares")
    sub = parser.add_subparsers(dest="cmd")

    p_index = sub.add_parser("index", help="Walk and index drive paths")
    p_index.add_argument("paths", nargs="+", help="Mount-point paths to index")
    p_index.add_argument("--share-name", help="Override share name (single path only)")
    p_index.add_argument("--ext", nargs="*", help="Only index these extensions (e.g. .mp4 .mkv)")

    p_status = sub.add_parser("status", help="Show indexed drive summary")

    p_ls = sub.add_parser("ls", help="List indexed drive files")
    p_ls.add_argument("--share", help="Filter by share name")
    p_ls.add_argument("--ext", help="Filter by extension")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    {"index": cmd_index, "status": cmd_status, "ls": cmd_ls}[args.cmd](args)


if __name__ == "__main__":
    main()
