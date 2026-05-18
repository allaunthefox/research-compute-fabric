from __future__ import annotations

import json
import os
import socket
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CREDENTIAL_PROVIDER_VERSION = "0.4"

# Remote credential server (microVM) — all nodes query this as primary
_cred_server_url = os.environ.get("RS_CREDENTIAL_SERVER", "http://100.101.247.127:8444")

# Config file path — local fallback if remote is unreachable
_cred_config_path = os.environ.get(
    "RS_CREDENTIAL_CONFIG",
    "/etc/rs-surface/credentials.json",
)

RDS_HOST = os.environ.get(
    "RDS_HOST",
    "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com",
)
RDS_PORT = int(os.environ.get("RDS_PORT", "5432"))
RDS_USER = os.environ.get("RDS_USER", "postgres")
RDS_IAM_TOKEN = os.environ.get("RDS_IAM_TOKEN", "")


@dataclass
class Credential:
    provider: str
    key_name: str
    value: str
    metadata: dict[str, Any] = field(default_factory=dict)


PROVIDER_ENV_MAP: dict[str, dict[str, str]] = {
    "deepseek": {
        "env_var": "DEEPSEEK_API_KEY",
        "description": "DeepSeek LLM API",
    },
    "quandela": {
        "env_var": "QUANDELA_API_KEY",
        "description": "Quandela quantum cloud",
    },
    "wolfram_alpha": {
        "env_var": "WOLFRAM_ALPHA_APPID",
        "description": "Wolfram Alpha API",
    },
    "notion": {
        "env_var": "NOTION_API_KEY",
        "description": "Notion API",
    },
    "linear": {
        "env_var": "LINEAR_API_KEY",
        "description": "Linear API",
    },
    "gemini": {
        "env_var": "GEMINI_API_KEY",
        "description": "Google Gemini API",
    },
    "ollama": {
        "env_var": "OLLAMA_API_KEY",
        "description": "Ollama local API",
    },
    "brave_search": {
        "env_var": "BRAVE_API_KEY",
        "description": "Brave Search API",
    },
    "neural_endeavor": {
        "env_var": "ENE_ENCRYPTION_KEY",
        "description": "ENE encryption master key",
    },
    "bedrock": {
        "env_var": "AWS_BEARER_TOKEN_BEDROCK",
        "description": "Amazon Bedrock API",
    },
    "venice": {
        "env_var": "VENICE_API_KEY",
        "description": "Venice AI API",
    },
}


def _rds_connect():
    import psycopg2
    import os

    # Primary check: RDS_IAM_TOKEN env var
    password = RDS_IAM_TOKEN
    
    if not password:
        # Generate dynamic IAM authentication token using boto3
        try:
            import boto3
            region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
            client = boto3.client('rds', region_name=region)
            password = client.generate_db_auth_token(
                DBHostname=RDS_HOST,
                Port=RDS_PORT,
                DBUsername=RDS_USER,
                Region=region
            )
        except Exception as e:
            # Fallback to standard environment password or log warning
            pass
            
    if not password:
        password = os.environ.get("RDS_PASSWORD", "")
        
    return psycopg2.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        user=RDS_USER,
        password=password,
        dbname="postgres",
        connect_timeout=10,
        sslmode="require",
    )


def _load_from_rds() -> list[Credential]:
    try:
        conn = _rds_connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT pkg, provider, encode(encrypted_payload, 'escape'), classification
            FROM credential_store.credentials
            WHERE is_active = TRUE
            ORDER BY provider
        """)
        creds = []
        for pkg, provider, payload_raw, classification in cur.fetchall():
            creds.append(Credential(
                provider=provider,
                key_name=pkg,
                value=payload_raw,
                metadata={
                    "source": "rds",
                    "pkg": pkg,
                    "classification": classification,
                },
            ))
        conn.close()
        return creds
    except Exception as e:
        return []


def _load_from_remote() -> list[Credential]:
    """Fetch credentials from the remote credential server (microVM)."""
    import urllib.request
    import urllib.error

    # Skip self-query: don't try to connect to ourselves
    self_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "", socket.gethostname()}
    netloc = urllib.parse.urlparse(_cred_server_url).hostname or ""
    if netloc in self_hosts:
        return []

    try:
        req = urllib.request.Request(_cred_server_url + "/credentials")
        with urllib.request.urlopen(req, timeout=5) as resp:
            manifest = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return []

    providers = manifest.get("providers", [])
    creds: list[Credential] = []
    for p in providers:
        name = p.get("name")
        if not name:
            continue
        try:
            req = urllib.request.Request(f"{_cred_server_url}/credentials/{name}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError, OSError):
            continue
        if data.get("ok"):
            creds.append(Credential(
                provider=name,
                key_name=data.get("key_name", f"remote/{name}"),
                value=data["key"],
                metadata={"source": "remote", "server": _cred_server_url},
            ))
    return creds


def _load_from_config() -> list[Credential]:
    """Read credentials from a JSON config file.

    Format:
    {
        "deepseek": "sk-...",
        "bedrock": "ABSK...",
        "ollama": "..."
    }
    """
    path = Path(_cred_config_path)
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, dict):
        return []
    creds: list[Credential] = []
    for provider_name, value in data.items():
        if not isinstance(value, str) or not value.strip():
            continue
        cfg = PROVIDER_ENV_MAP.get(provider_name, {})
        creds.append(Credential(
            provider=provider_name,
            key_name=f"config/{provider_name}",
            value=value.strip(),
            metadata={
                "description": cfg.get("description", provider_name),
                "source": "config_file",
                "file": str(path),
            },
        ))
    return creds


def _load_from_env() -> list[Credential]:
    creds: list[Credential] = []
    for provider, cfg in PROVIDER_ENV_MAP.items():
        value = os.getenv(cfg["env_var"])
        if not value:
            continue
        creds.append(Credential(
            provider=provider,
            key_name=cfg["env_var"],
            value=value,
            metadata={"description": cfg["description"], "source": "env"},
        ))
    return creds


def load_credentials() -> list[Credential]:
    creds = _load_from_rds()
    if creds:
        return creds
    creds = _load_from_remote()
    if creds:
        return creds
    creds = _load_from_config()
    if creds:
        return creds
    return _load_from_env()


def _detect_backend() -> str:
    if _load_from_rds():
        return "rds"
    if _load_from_remote():
        return "remote"
    if _load_from_config():
        return "config_file"
    return "env"


def credential_status() -> dict[str, Any]:
    creds = load_credentials()
    return {
        "ok": True,
        "node": os.environ.get("RS_SURFACE_NODE_ID", "unknown"),
        "provider_version": CREDENTIAL_PROVIDER_VERSION,
        "backend": _detect_backend(),
        "available_providers": [c.provider for c in creds],
        "count": len(creds),
        "remote_server": _cred_server_url,
    }


def resolve_credential(provider: str) -> Credential | None:
    creds = load_credentials()
    for c in creds:
        if c.provider == provider:
            return c
    return None


def provider_manifest() -> dict[str, Any]:
    creds = load_credentials()
    return {
        "ok": True,
        "service_kind": "apiProvider",
        "backend": _detect_backend(),
        "providers": [
            {
                "name": c.provider,
                "description": c.metadata.get("description", ""),
                "key_name": c.key_name,
                "available": True,
            }
            for c in creds
        ],
        "node_id": os.environ.get("RS_SURFACE_NODE_ID", "unknown"),
    }
