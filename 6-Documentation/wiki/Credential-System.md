# Research Stack Credential System

> **Canonical source**: `4-Infrastructure/infra/ene-session-sync/src/credential.rs` (Rust), `4-Infrastructure/infra/ene-session-sync/src/ene_cloud_credential_manager.rs` (Rust), `4-Infrastructure/infra/recover_credential_server.sh` (deployment script)
> **Runtime host**: `microvm-racknerd` (100.101.247.127) — Debian 13 VM on RackNerd
> **Primary backend**: AWS RDS PostgreSQL (`database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com`)
> **Fallback chain**: RDS → remote server → local JSON → environment variables
> **SOPS key**: `age1tp4vr565zkmvnyulatpyaj6z8zrz7q9mpaypz85yz8rty99crdasualxyr`

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CONSUMERS (any node)                         │
│  qfox-1    nixos-laptop    361395-1    microvm-racknerd          │
│     │           │              │                │                    │
│     └───────────┴──────────────┴────────────────┘                    │
│                      HTTP GET /credentials/:provider                │
│                              │                                      │
│                    ┌─────────▼─────────┐                            │
│                    │  microvm-racknerd │  ← Credential Server     │
│                    │   (port 8444)      │   (Python, systemd)      │
│                    └─────────┬─────────┘                            │
│                              │                                      │
│              ┌───────────────┼───────────────┐                    │
│              │               │               │                      │
│     ┌────────▼────────┐ ┌───▼────────┐ ┌────▼───────┐             │
│     │  AWS RDS        │ │  Remote    │ │  Local     │             │
│     │  PostgreSQL     │ │  Server    │ │  JSON      │             │
│     │  (primary)      │ │  (chain)   │ │  (backup)  │             │
│     └────────┬────────┘ └────────────┘ └────────────┘             │
│              │                                                      │
│     ┌────────▼────────┐                                            │
│     │ credential_store│                                            │
│     │ .credentials    │  12 active records                        │
│     │ .access_log     │  0 entries (not yet enabled)              │
│     └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────┘
```

## Four-Tier Fallback Chain

The `credential_provider.py` (`v0.4`) implements a strict priority order. The first non-empty result wins; all lower tiers are skipped.

| Tier | Function | Trigger | Data Source |
|------|----------|---------|-------------|
| **1** | `_load_from_rds()` | Always runs first | AWS RDS PostgreSQL `credential_store.credentials` |
| **2** | `_load_from_remote()` | Skipped if RDS empty AND `RS_CREDENTIAL_SERVER` points to self | Another credential server URL |
| **3** | `_load_from_config()` | Skipped if tiers 1–2 empty | `/etc/rs-surface/credentials.json` |
| **4** | `_load_from_env()` | Last resort | Environment variables per `PROVIDER_ENV_MAP` |

### Why RDS is the primary source

RDS credentials are **encrypted at rest** (AES-256-GCM payload), **IAM-authenticated** (temporary tokens), and **auditable** (`access_log` table). The local JSON file (`/etc/rs-surface/credentials.json`) is a plaintext fallback for disaster recovery only.

**Current status** (2026-05-21): Tier 1 (RDS) is active and serving all 11 credentials. Tier 3 (local JSON) exists as a warm standby but is not consulted because RDS succeeds.

```bash
# Verify from any Tailnet node
curl -s http://100.101.247.127:8444/status | jq .
# Expected: {"backend": "rds", "count": 11, "ok": true}
```

## RDS Schema

### `credential_store.credentials`

| Column | Type | Purpose |
|--------|------|---------|
| `id` | uuid | Primary key |
| `pkg` | text | Hierarchical key name, e.g. `credentials/deepseek` |
| `provider` | text | Human-readable provider name, e.g. `deepseek` |
| `encrypted_payload` | bytea | AES-256-GCM ciphertext |
| `nonce` | bytea | GCM nonce |
| `classification` | smallint | `2` = internal, `3` = secret |
| `integrity_hash` | text | SHA-256 of decrypted payload |
| `node_assignments` | text[] | Which nodes may request this credential |
| `created_at` | timestamptz | Insert timestamp |
| `rotated_at` | timestamptz | Last rotation timestamp |
| `access_count` | bigint | Number of successful fetches |
| `is_active` | boolean | Soft-delete flag |

### `credential_store.access_log`

| Column | Type | Purpose |
|--------|------|---------|
| (table empty as of 2026-05-21 — not yet wired to the fetch path) |

### Active credentials (12)

| Provider | Classification | pkg | Notes |
|----------|---------------|-----|-------|
| aws | 3 (secret) | credentials/aws | |
| bedrock | 3 | credentials/bedrock | |
| deepseek | 3 | credentials/deepseek | |
| linear | 3 | credentials/linear | |
| notion | 3 | credentials/notion | |
| ollama | 2 (internal) | credentials/ollama | |
| porkbun | 3 | credentials/porkbun | DNS provider |
| quandela | 3 | credentials/quandela | Quantum cloud |
| **racknerd_ssh** | 3 | credentials/racknerd_ssh | VM root password |
| venice | 2 | credentials/venice | |
| wolfram_alpha | 2 | credentials/wolfram_alpha | |
| **authentik** | 3 | credentials/authentik | LLM controller token for Authentik API |

## Authentication to RDS

### Method: IAM Authentication Token (preferred)

```python
import boto3

client = boto3.client('rds', region_name='us-east-1')
token = client.generate_db_auth_token(
    DBHostname='database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com',
    Port=5432,
    DBUsername='postgres',
    Region='us-east-1'
)
# token is a signed URL valid for 15 minutes
conn = psycopg2.connect(
    host=RDS_HOST, port=5432, user='postgres',
    password=token, dbname='postgres',
    sslmode='require', connect_timeout=10
)
```

**Prerequisites on the client node:**
- AWS credentials with `rds-db:connect` permission (IAM role or `~/.aws/credentials`)
- `psycopg2` + `boto3` installed
- `libpq5` (Debian) or equivalent PostgreSQL C client library

### Fallback: RDS_PASSWORD environment variable

If `boto3` is unavailable or IAM permissions fail, the provider falls back to `RDS_PASSWORD` (plain text). This is **not recommended** for production but is the historical path on nodes without AWS CLI.

## MicroVM-Racknerd Deployment

### File layout

```
/opt/rs-surface/
├── credential_server.py          # HTTP server (v0.4)
├── credential_provider.py        # 4-tier fallback logic (v0.4)
├── ene_rds_schema.py              # Schema provisioning script
└── __pycache__/

/etc/rs-surface/
├── credentials.json               # Local fallback (plaintext, 9 providers)
└── node.json                      # Node identity metadata

/opt/credential-provider/          # STALE — v0.2 code, renamed
├── credential_provider.py.v0.2.stale
└── server.py.v0.2.stale

~/.aws/
├── config                         # region = us-east-1
└── credentials                      # IAM access key + secret
```

### Systemd service

```ini
# /etc/systemd/system/rs-credential-server.service
[Unit]
Description=Research Stack Credential Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/rs-surface
EnvironmentFile=/opt/credential-provider/.env
Environment=RS_CREDENTIAL_SERVER=        ; empty = disable self-query
ExecStart=/usr/bin/python3 /opt/rs-surface/credential_server.py --port 8444 --bind 0.0.0.0
Restart=always
RestartSec=5
Environment=RS_CREDENTIAL_CONFIG=/etc/rs-surface/credentials.json

[Install]
WantedBy=multi-user.target
```

### Environment file (`/opt/credential-provider/.env`)

This file contains raw API keys for the **env-var fallback tier only**. Since RDS is working, these env vars are not consulted by the running service. They exist for disaster recovery and for scripts that bypass the credential server.

```
RS_SURFACE_NODE_ID=MicroVM-Racknerd
RS_SURFACE_PROFILE=/etc/rs-surface/node.json
DEEPSEEK_API_KEY=sk-...
QUANDELA_API_KEY=_T_eyJ...
WOLFRAM_ALPHA_APPID=HYJE3R3R63
# ... etc
```

**Warning**: The `.env` file is **plaintext** and should be rotated out of existence once the RDS tier is proven stable on all consumers.

## Health Checks

```bash
# From any Tailnet node
curl -s --max-time 5 http://100.101.247.127:8444/health
curl -s --max-time 5 http://100.101.247.127:8444/status | jq .
curl -s --max-time 5 http://100.101.247.127:8444/credentials | jq '.providers[].name'
curl -s --max-time 5 http://100.101.247.127:8444/credentials/deepseek | jq .

# From microvm itself
systemctl status rs-credential-server --no-pager
journalctl -u rs-credential-server --since today --no-pager
```

## Adding a New Credential

1. **Encrypt with SOPS** (on qfox-1):
   ```bash
   sops --encrypt --in-place new_secret.json
   # or edit an existing encrypted file:
   sops 4-Infrastructure/infra/secrets/credentials.json
   ```

2. **Insert into RDS** (from microvm, which has IAM access):
   ```python
   import psycopg2, boto3, json, os
   # ... generate IAM token, connect ...
   cur.execute("""
       INSERT INTO credential_store.credentials
       (pkg, provider, encrypted_payload, nonce, classification, integrity_hash, is_active)
       VALUES (%s, %s, %s, %s, %s, %s, TRUE)
   """, (pkg, provider, ciphertext, nonce, 3, integrity_hash))
   ```

3. **Restart the credential server** (to pick up the change):
   ```bash
   systemctl restart rs-credential-server
   ```

4. **Verify**:
   ```bash
   curl -s http://100.101.247.127:8444/credentials/<provider> | jq .
   ```

## Disaster Recovery

If RDS is unreachable AND the credential server is down, the local JSON fallback on microvm contains the same credentials (minus the new `racknerd_ssh` entry, which only exists in RDS). The JSON file is:

```bash
# On microvm
cat /etc/rs-surface/credentials.json
```

If microvm itself is destroyed, the credentials are also in SOPS-encrypted files on qfox-1:

```bash
# On qfox-1
sops -d 4-Infrastructure/infra/secrets/credentials.json
```

## Historical Note: v0.2 → v0.4 Migration

The original credential system (`/opt/credential-provider/`, v0.2) had a **hardcoded IAM token** in `credential_provider.py` with an expiration date (2026-05-17). When that token expired, `_load_from_rds()` silently returned `[]`, causing the service to fall through to environment variables. This was the "bug" that appeared to be RDS not working, but was actually an expired token in stale code.

The fix was:
1. Deploy `credential_provider.py` v0.4 to `/opt/rs-surface/` (uses `boto3.generate_db_auth_token()` dynamically)
2. Point systemd `ExecStart` at `/opt/rs-surface/credential_server.py`
3. Rename old v0.2 files with `.v0.2.stale` suffix

## TODO

- [ ] Wire `access_log` insert on every successful credential fetch
- [ ] Add `node_assignments` enforcement (only allowlisted Tailscale nodes to request secrets)
- [ ] Rotate `.env` file out of existence (env-var tier is a liability)
- [ ] Encrypt local JSON fallback with SOPS instead of plaintext
- [ ] Add credential server to nixos-laptop as a hot standby
