#!/usr/bin/env python3
"""Shared RDS connection helper — resolves env vars, IAM auth, DATABASE_URL."""

import os, subprocess
from urllib.parse import urlparse


def _resolve_params() -> dict:
    """Resolve connection parameters from env, preferring DATABASE_URL."""
    du = os.environ.get("DATABASE_URL", "").strip()
    if du:
        p = urlparse(du)
        params = {
            "host": p.hostname or "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com",
            "port": p.port or 5432,
            "user": p.username or "postgres",
            "password": p.password or "",
            "dbname": p.path.lstrip("/") if p.path else "postgres",
            "sslmode": "require",
        }
        # Extract sslmode from query string
        if p.query:
            for q in p.query.split("&"):
                if "=" in q:
                    k, v = q.split("=", 1)
                    if k == "sslmode":
                        params["sslmode"] = v
        return params

    host = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
    port = int(os.environ.get("RDS_PORT", "5432"))
    user = os.environ.get("RDS_USER", "postgres")
    dbname = os.environ.get("RDS_DB", os.environ.get("RDS_DBNAME", "postgres"))
    sslmode = os.environ.get("RDS_SSLMODE", "require")
    password = os.environ.get("RDS_PASSWORD", "")
    return {"host": host, "port": port, "user": user,
            "password": password, "dbname": dbname, "sslmode": sslmode}


def _get_iam_token(host: str, port: int, user: str, region: str) -> str:
    """Generate IAM token via boto3 (preferred) or AWS CLI (fallback)."""
    try:
        import boto3
        return boto3.client("rds", region_name=region).generate_db_auth_token(
            DBHostname=host, Port=port, DBUsername=user, Region=region)
    except ImportError:
        return subprocess.check_output([
            "aws", "rds", "generate-db-auth-token",
            "--region", region, "--hostname", host,
            "--port", str(port), "--username", user,
        ], text=True).strip()


def connect_rds(**overrides):
    """Connect to RDS. Override any resolved param via kwargs.

    Resolution order per field:
      1. explicit **override
      2. DATABASE_URL env var
      3. individual RDS_* env vars
      4. built-in defaults

    Auth resolution (when password is empty):
      1. RDS_IAM_TOKEN env var (pre-computed)
      2. boto3 SDK generate_db_auth_token (RDS_IAM=1 or RDS_IAM_AUTH=1)
      3. subprocess aws rds generate-db-auth-token
      4. RDS_PASSWORD env var
    """
    p = _resolve_params()
    p.update(overrides)

    # Determine if IAM auth is requested
    iam_requested = (
        os.environ.get("RDS_IAM", "").strip() == "1" or
        os.environ.get("RDS_IAM_AUTH", "").strip() == "1"
    )

    # Resolve password
    if not p.get("password") or iam_requested:
        token = os.environ.get("RDS_IAM_TOKEN", "").strip()
        if token:
            p["password"] = token
        elif iam_requested or not p.get("password"):
            region = os.environ.get("AWS_REGION", "us-east-1")
            p["password"] = _get_iam_token(p["host"], p["port"], p["user"], region)

    import psycopg2
    kw = {k: p[k] for k in ("host", "port", "user", "password", "dbname", "sslmode")}
    if "connect_timeout" in p:
        kw["connect_timeout"] = p["connect_timeout"]
    return psycopg2.connect(**kw)
