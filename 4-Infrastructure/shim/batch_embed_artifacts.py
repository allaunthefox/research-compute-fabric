#!/usr/bin/env python3
"""Batch-embed ENE artifacts missing embeddings and emit a JSON receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request

BATCH_SIZE = 50
TOKEN_REFRESH_SEC = 600

HOST = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
PORT = int(os.environ.get("RDS_PORT", "5432"))
USER = os.environ.get("RDS_USER", "postgres")
DB = os.environ.get("RDS_DB", os.environ.get("RDS_DBNAME", "postgres"))
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://100.85.244.73:11434").rstrip("/")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_token() -> str:
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
        return get_token()
    password = os.environ.get("RDS_PASSWORD")
    if not password:
        raise RuntimeError("RDS_PASSWORD is required when RDS_IAM=0")
    return password


def get_conn(password: str):
    import psycopg2

    return psycopg2.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=password,
        dbname=DB,
        sslmode="require",
        connect_timeout=10,
    )


def fetch_batch(cur, batch_size: int) -> list[tuple[Any, str, str]]:
    cur.execute(
        "SELECT id, path, content FROM ene.artifacts "
        "WHERE embedding IS NULL AND content IS NOT NULL AND content != '' "
        "AND kind NOT IN ('verilog', 'shader', 'schema', 'binary') "
        "ORDER BY path LIMIT %s",
        (batch_size,),
    )
    return cur.fetchall()


def generate_embedding(text: str) -> list[float] | None:
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text[:2048]}).encode("utf-8")
    req = request.Request(
        f"{OLLAMA_URL}/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    embedding = data.get("embedding")
    if not isinstance(embedding, list):
        return None
    return embedding


def pgvector_literal(values: list[float]) -> str:
    return "[" + ",".join(format(value, ".16g") for value in values) + "]"


def build_receipt(
    *,
    started_at: str,
    processed: int,
    embedded: int,
    failed: list[dict[str, str]],
    dry_run: bool,
    limit: int | None,
    duration_sec: float,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "ene_artifact_embedding_batch_receipt_v1",
        "version": "1.0.0",
        "generated_at_utc": utc_now(),
        "started_at_utc": started_at,
        "duration_ms": int(duration_sec * 1000),
        "dry_run": dry_run,
        "limit": limit,
        "rds_host": HOST,
        "rds_db": DB,
        "ollama_url": OLLAMA_URL,
        "embed_model": EMBED_MODEL,
        "processed_count": processed,
        "embedded_count": embedded,
        "failed_count": len(failed),
        "failures": failed[:20],
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
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--receipt-out")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")

    started_at = utc_now()
    started = time.time()
    password = get_password()
    next_refresh = time.time() + TOKEN_REFRESH_SEC
    conn = get_conn(password)
    cur = conn.cursor()
    processed = 0
    embedded = 0
    failed: list[dict[str, str]] = []
    attempted_ids: set[str] = set()

    try:
        rows = fetch_batch(cur, args.batch_size)
        while rows and (args.limit is None or processed < args.limit):
            rows = [row for row in rows if str(row[0]) not in attempted_ids]
            if not rows:
                break

            if os.environ.get("RDS_IAM", "1") == "1" and time.time() > next_refresh:
                password = get_password()
                conn.close()
                conn = get_conn(password)
                cur = conn.cursor()
                next_refresh = time.time() + TOKEN_REFRESH_SEC

            for aid, path, content in rows:
                if args.limit is not None and processed >= args.limit:
                    break
                attempted_ids.add(str(aid))
                processed += 1
                try:
                    if args.dry_run:
                        continue
                    embedding = generate_embedding(content)
                    if not embedding:
                        failed.append({"path": path, "error": "embedding response missing vector"})
                        continue
                    cur.execute(
                        "UPDATE ene.artifacts SET embedding = %s::vector WHERE id = %s",
                        (pgvector_literal(embedding), aid),
                    )
                    embedded += 1
                except Exception as exc:  # noqa: BLE001 - receipt records per-row failure.
                    failed.append({"path": path, "error": str(exc)})

            if args.dry_run:
                conn.rollback()
            else:
                conn.commit()
            rows = fetch_batch(cur, args.batch_size)
    finally:
        cur.close()
        conn.close()

    receipt = build_receipt(
        started_at=started_at,
        processed=processed,
        embedded=embedded,
        failed=failed,
        dry_run=args.dry_run,
        limit=args.limit,
        duration_sec=time.time() - started,
    )
    write_receipt(receipt, args.receipt_out)
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
