# ENE RDS — Rust workspace replacing the Python RDS stack

## Workspace structure

| Crate | Purpose | Replaces |
|-------|---------|----------|
| `ene-rds-core` | Shared PostgreSQL client, DSN builder, `vec_to_pgtext`, receipts | `ene_rds_*` base connection logic |
| `ene-rds-wiki` | Wiki CRUD + full-text search + revision tracking | `ene_rds_wiki_layer.py` |
| `ene-rds-ephemeral` | EphemeralNode thermal zones, tasks, receipts, scars, metrics | `ene_rds_ephemeral_node.py` |
| `ene-rds-chat` | Chat session ingestion, keyword/semantic search | `ene_rds_chat_log.py` |
| `ene-api` | Axum HTTP server mounting all surfaces on `:3000` | `ene_chat_api.py` + FastAPI |
| `ene-sync` | Polls opencode.db SQLite → upserts into RDS chat tables | `ene_claw_sync.py` |

## Build

```bash
cd 4-Infrastructure/infra/ene-rds
cargo build --release
```

## Run

### Initialize schema only
```bash
export RDS_PASSWORD=...
./target/release/ene-sync init-schema
```

### One-shot sync
```bash
./target/release/ene-sync sync --embed
```

### Watch mode (polls every 60s)
```bash
./target/release/ene-sync watch --interval 60 --embed
```

### API server
```bash
./target/release/ene-api
# → http://0.0.0.0:3000/health
# → http://0.0.0.0:3000/sessions
# → http://0.0.0.0:3000/search?q=thermal+zone
# → http://0.0.0.0:3000/wiki/search?q=compression
# → http://0.0.0.0:3000/ephemeral/nodes?zone=hot
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RDS_HOST` | `database-1.cluster-c9i0w8eu8fnv.us-east-2.rds.amazonaws.com` | PostgreSQL host |
| `RDS_PORT` | `5432` | PostgreSQL port |
| `RDS_USER` | `postgres` | PostgreSQL user |
| `RDS_PASSWORD` | — | Password or IAM token |
| `RDS_DB` | `postgres` | Database name |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama embedding endpoint |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |

## What changed from Python

- No `psycopg2` / `boto3` runtime dependency — single static binary
- `tokio-postgres` with `with-serde_json-1` feature for native JSONB support
- `pgvector` vectors passed as `'[0.1,0.2,...]'::vector` text format
- Ollama embeddings via `reqwest` instead of `requests`
- SQLite source via `rusqlite` with bundled bindings
- Axum replaces FastAPI for the API server

## Python bridge (optional)

The standalone `bridge_wrapper.py` still exists for calling legacy Python modules that have not been ported. The Rust surfaces do not depend on it.
