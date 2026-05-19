# ENE RDS Rust Workspace

## Overview

The `ene-rds` workspace replaces the Python RDS stack (`ene_rds_*` modules) with a unified Rust binary suite. All PostgreSQL surfaces—wiki, ephemeral nodes, chat logs, and the HTTP API—are now native Rust crates.

**Location:** `4-Infrastructure/infra/ene-rds/`

## Workspace Crates

| Crate | Type | Replaces | Purpose |
|-------|------|----------|---------|
| `ene-rds-core` | lib | `ene_rds_*` base connection logic | Shared `RdsClient`, DSN builder, `vec_to_pgtext()`, ingestion receipts |
| `ene-rds-wiki` | lib | `ene_rds_wiki_layer.py` | Wiki pages, revisions, links, categories, full-text search |
| `ene-rds-ephemeral` | lib | `ene_rds_ephemeral_node.py` | EphemeralNode thermal zones, tasks, receipts, scar events, metrics |
| `ene-rds-chat` | lib | `ene_rds_chat_log.py` | Chat session ingestion, keyword search, semantic similarity |
| `ene-api` | bin | `ene_chat_api.py` | Axum HTTP server on `:3000` mounting all surfaces |
| `ene-sync` | bin | `ene_claw_sync.py` | Polls opencode.db SQLite → upserts into RDS chat tables |

## Build

```bash
cd 4-Infrastructure/infra/ene-rds
cargo build --release
```

Dependencies are fetched from crates.io on first build.

## Run

### Initialize schema only
```bash
export RDS_PASSWORD=...
./target/release/ene-sync init-schema
```

### One-shot sync (opencode.db → RDS)
```bash
./target/release/ene-sync sync --embed
```

### Watch mode (polls every 60s, incremental)
```bash
./target/release/ene-sync watch --interval 60 --embed
```

### API server
```bash
./target/release/ene-api
```

**Endpoints:**
- `GET /health` — service status
- `GET /sessions?limit=10` — list chat sessions
- `GET /sessions/:id` — get full session with messages
- `GET /search?q=query&limit=10` — keyword search across messages
- `GET /wiki/search?q=query` — wiki full-text search
- `GET /wiki/:slug` — get wiki page by slug
- `GET /ephemeral/nodes?zone=hot` — list nodes by thermal zone
- `GET /ephemeral/nodes/:id` — get single node

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RDS_HOST` | `database-1.cluster-c9i0w8eu8fnv.us-east-2.rds.amazonaws.com` | PostgreSQL host |
| `RDS_PORT` | `5432` | PostgreSQL port |
| `RDS_USER` | `postgres` | PostgreSQL user |
| `RDS_PASSWORD` | — | Password or IAM token |
| `RDS_DB` | `postgres` | Database name |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama embedding endpoint |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |

## Architecture Changes from Python

| Concern | Python (old) | Rust (new) |
|---------|-------------|------------|
| PostgreSQL driver | `psycopg2` | `tokio-postgres` with `with-serde_json-1` |
| JSONB handling | Manual string serialization | Native `serde_json::Value` ↔ JSONB |
| pgvector vectors | Python list → string | `vec_to_pgtext()` — `'[0.1,0.2,...]'::vector` |
| HTTP server | FastAPI | Axum |
| SQLite source | — | `rusqlite` with bundled bindings |
| Ollama embeddings | `requests` | `reqwest` |
| Runtime | Python 3.11 + venv | Single static binary |

## Database Schema

The Rust surfaces create the following tables on `init_tables()`:

### `ene.chat_sessions`
- `session_id TEXT PRIMARY KEY`
- `workspace_fingerprint TEXT`, `workspace_root TEXT`
- `fork_parent_session_id TEXT` (self-referential for session forks)
- `compaction_count INTEGER`, `compaction_summary TEXT`
- `message_count INTEGER`, `token_input_total BIGINT`, `token_output_total BIGINT`
- `created_at_ms BIGINT`, `updated_at_ms BIGINT`
- `first_message_at_ms BIGINT`, `last_message_at_ms BIGINT`
- `embedding vector(768)` — session-level semantic vector
- `meta JSONB` — slug, agent, model, project_id, cost, cache tokens
- `receipt TEXT`, `updated_at TIMESTAMPTZ`

### `ene.chat_messages`
- `id BIGSERIAL PRIMARY KEY`
- `session_id TEXT REFERENCES chat_sessions`
- `message_index INTEGER` (ordered within session)
- `role TEXT` — user, assistant, tool, system
- `blocks JSONB` — typed content blocks (text, reasoning, tool_use, tool_result)
- `text_content TEXT` — concatenated text for full-text search
- `token_input BIGINT`, `token_output BIGINT`, `token_cache_creation BIGINT`, `token_cache_read BIGINT`
- `tool_calls JSONB` — extracted tool calls for structured search
- `embedding vector(768)` — per-message semantic vector
- `receipt_hash TEXT` — links to ingestion receipt
- `created_at_ms BIGINT`, `created_at TIMESTAMPTZ`

### `ene.ephemeral_nodes`
- `node_id TEXT PRIMARY KEY`
- `thermal_zone TEXT` — hot, warm, cold
- `reliability_raw BIGINT` — Q0_32 fixed-point
- `latency_p95_ms BIGINT`
- `scar_count INTEGER`
- `last_seen_ms BIGINT`
- `reputation_raw BIGINT` — Q16_16 fixed-point
- `quarantine_until_ms BIGINT`
- `meta JSONB`
- `created_at_ms BIGINT`, `updated_at_ms BIGINT`

### `ene.ephemeral_tasks`
- `task_id TEXT PRIMARY KEY`
- `session_id TEXT`, `node_id TEXT REFERENCES ephemeral_nodes`
- `task_state TEXT` — pending, dispatched, partial, complete, expired, abandoned
- `priority_raw BIGINT`, `ttl_ms BIGINT`
- `dispatched_at_ms BIGINT`, `completed_at_ms BIGINT`
- `result_hash TEXT`, `meta JSONB`

### `ene.ephemeral_receipts`
- `receipt_id TEXT PRIMARY KEY`
- `task_id TEXT`, `node_id TEXT`
- `cross_matrix JSONB` — braid crossing matrix
- `sidon_slack INTEGER`, `step_count INTEGER`
- `residual_series BIGINT[]` — Q0_32 residual series
- `write_timing_ms BIGINT`
- `scar_absent BOOLEAN`

### `ene.ephemeral_scar_events`
- `scar_id TEXT PRIMARY KEY`
- `node_id TEXT`, `task_id TEXT`
- `scar_pressure BIGINT`, `failure_mode TEXT`, `coarsening_agent TEXT`

### `ene.ephemeral_metrics`
- `metric_id TEXT PRIMARY KEY`
- `node_id TEXT`, `metric_name TEXT`
- `metric_value_raw BIGINT`, `metric_scale INTEGER`
- `recorded_at_ms BIGINT`

## Sync Daemon (`ene-sync`)

The sync binary reads from the OpenCode SQLite database at `~/.local/share/opencode/opencode.db`:

1. **Sessions** — metadata, tokens, costs, workspace fingerprint
2. **Messages** — conversation turns with role and timing
3. **Parts** — actual content (text, reasoning, tool calls, tool results)
4. **Session messages** — lifecycle events (agent switches, model switches)

Content is normalized into `ChatSession` + `ChatMessage` structs, embeddings generated via Ollama, then upserted into RDS.

### Incremental sync

Watch mode tracks `MAX(time_updated)` from the `session` table in a local state file (`~/.cache/ene-sync/state.json`). Only sessions updated since the checkpoint are re-ingested.

## Python Bridge (Legacy Support)

For calling unported Python modules, `bridge_wrapper.py` auto-discovers classes with `handle_request()` methods and dispatches JSON requests. The Rust surfaces do not depend on this bridge.

## Future Work

- Add `postgres-native-tls` or `rustls` for RDS TLS instead of `NoTls`
- Wire semantic search in `ene-api` (currently returns placeholder error)
- Add `pgvector` binary format support for faster embedding inserts
- Batch embedding requests if Ollama adds native batching

## Related

- `4-Infrastructure/infra/ene-rds/README.md` — crate-level README with quickstart
- `4-Infrastructure/infra/ene_rds_wiki_layer.py` — legacy Python wiki surface
- `4-Infrastructure/infra/ene_rds_fractal_fold.py` — legacy Python fractal surface
- `0-Core-Formalism/lean/Semantics/EphemeralNode/` — Lean thermal zone formalism
