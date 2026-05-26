#!/usr/bin/env python3
"""Sync filesystem wiki Markdown files to ENE RDS and emit a JSON receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STACK_ROOT = Path(os.environ.get("STACK_ROOT", "/home/allaun/Research Stack"))
WIKI_ROOT = Path(os.environ.get("WIKI_ROOT", str(STACK_ROOT / "6-Documentation" / "wiki")))

HOST = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
PORT = int(os.environ.get("RDS_PORT", "5432"))
USER = os.environ.get("RDS_USER", "postgres")
DB = os.environ.get("RDS_DB", os.environ.get("RDS_DBNAME", "postgres"))
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_iam_token() -> str:
    return subprocess.check_output(
        [
            "aws",
            "rds",
            "generate-db-auth-token",
            "--region",
            AWS_REGION,
            "--hostname",
            HOST,
            "--port",
            str(PORT),
            "--username",
            USER,
        ],
        text=True,
        stdin=subprocess.DEVNULL,
    ).strip()


def get_password() -> str:
    if os.environ.get("RDS_IAM", "1") == "1":
        return get_iam_token()
    password = os.environ.get("RDS_PASSWORD")
    if not password:
        raise RuntimeError("RDS_PASSWORD is required when RDS_IAM=0")
    return password


def get_conn():
    import psycopg2

    return psycopg2.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=get_password(),
        dbname=DB,
        sslmode="require",
        connect_timeout=10,
    )


def title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


def iter_markdown_files(root: Path) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(f"wiki root does not exist: {root}")
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def sync_files(conn, files: list[Path], dry_run: bool) -> tuple[int, int, list[dict[str, str]]]:
    indexed = 0
    skipped = 0
    failures: list[dict[str, str]] = []
    cur = conn.cursor()
    try:
        for fpath in files:
            try:
                rel = fpath.relative_to(WIKI_ROOT)
                slug = rel.with_suffix("").as_posix()
                title = title_from_slug(slug)
                content = fpath.read_text(encoding="utf-8", errors="replace")

                cur.execute("SELECT content FROM ene.wiki_pages WHERE slug = %s", (slug,))
                row = cur.fetchone()
                if row and row[0] == content:
                    skipped += 1
                    continue

                if not dry_run:
                    cur.execute(
                        """INSERT INTO ene.wiki_pages (slug, title, content, updated_at)
                           VALUES (%s, %s, %s, %s)
                           ON CONFLICT (slug) DO UPDATE SET
                             title = EXCLUDED.title,
                             content = EXCLUDED.content,
                             updated_at = EXCLUDED.updated_at""",
                        (slug, title, content, utc_now()),
                    )
                indexed += 1
            except Exception as exc:  # noqa: BLE001 - receipt records per-file failure.
                failures.append({"path": str(fpath), "error": str(exc)})
        if dry_run:
            conn.rollback()
        else:
            conn.commit()
    finally:
        cur.close()
    return indexed, skipped, failures


def build_receipt(
    *,
    indexed: int,
    skipped: int,
    failures: list[dict[str, str]],
    dry_run: bool,
    file_count: int,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "ene_wiki_to_rds_sync_receipt_v1",
        "version": "1.0.0",
        "generated_at_utc": utc_now(),
        "dry_run": dry_run,
        "wiki_root": str(WIKI_ROOT),
        "rds_host": HOST,
        "rds_db": DB,
        "file_count": file_count,
        "indexed_count": indexed,
        "skipped_count": skipped,
        "failed_count": len(failures),
        "failures": failures[:20],
    }
    preimage = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(json.dumps(preimage, sort_keys=True))
    return receipt


def write_receipt(receipt: dict[str, Any], path: str | None) -> None:
    encoded = json.dumps(receipt, sort_keys=True)
    print(encoded)
    if path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--receipt-out")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = iter_markdown_files(WIKI_ROOT)
    conn = get_conn()
    try:
        indexed, skipped, failures = sync_files(conn, files, args.dry_run)
    finally:
        conn.close()
    receipt = build_receipt(
        indexed=indexed,
        skipped=skipped,
        failures=failures,
        dry_run=args.dry_run,
        file_count=len(files),
    )
    write_receipt(receipt, args.receipt_out)
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())
