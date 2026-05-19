# 4-Infrastructure

**Purpose:** Rust/Python shims, GPU duty assignment, cloud storage, web interaction, hardware designs, drivers, and the ENE RDS Rust workspace.

**Depends on:** `0` through `3`

## Directory Layout

| Path | Purpose |
|------|---------|
| `infra/` | Python shims, ENE distributed node, credential server |
| `infra/ene-rds/` | **ENE RDS Rust workspace** (8 crates — Rust replacement for Python RDS stack) |
| `hardware/` | FPGA Verilog, FAMM verilator, KiCad templates |
| `drivers/` | Hardware drivers |
| `gpu/` | WGSL shaders, wgpu compute dispatch |
| `storage/` | **restic + Garage S3 + rclone storage stack** |
| `storage/storage_agent.py` | **Storage observer/optimizer agent** |
| `shim/` | Stack solidification probes, adversarial harnesses, gate library |
| `surface/` | FastAPI/WebSocket surface (spec'd, pending implementation) |

## ENE RDS Rust Workspace (`infra/ene-rds/`)

8-crate Rust workspace replacing the Python RDS stack. Build: `cd 4-Infrastructure/infra/ene-rds && cargo build --release`.

| Crate | Purpose |
|-------|---------|
| `ene-rds-core` | Shared PostgreSQL client, DSN builder, receipts |
| `ene-rds-wiki` | Wiki CRUD + full-text search + revision tracking |
| `ene-rds-ephemeral` | EphemeralNode thermal zones, tasks, receipts, scars, metrics |
| `ene-rds-chat` | Chat session ingestion, keyword/semantic search |
| `ene-api` | Axum HTTP server on :3000 |
| `ene-node` | Node identity and gossip primitives |
| `ene-storage` | S3/Garage object storage client |
| `ene-sync` | Polls opencode.db SQLite → upserts into RDS chat tables |

sqlx 0.8.6 (Dependabot vuln from 0.7 resolved 2026-05-19).

## Storage Stack (`storage/`)

Three tools, non-overlapping roles. Full contract: `4-Infrastructure/AGENTS.md §Storage Stack`.

| Tool | Job |
|------|-----|
| **restic** | Deduplicated, encrypted, content-addressed snapshots |
| **Garage v2.3.0** | Self-hosted S3-compatible object store (Tailscale mesh, 5 buckets) |
| **rclone** | Raw sync between remotes (Garage↔gdrive cold copy) |

**Storage agent** (`storage/storage_agent.py`): observe→decide→act loop, systemd timer (every 15 min), Q16_16 thresholds, JSONL hash-chain receipts.

## GPU Status

- **Device:** NVIDIA GeForce RTX 4070
- **Memory:** 12.3GB total, ~10GB available
- **CUDA:** 13.0
- **Compute dispatch:** WGSL → wgpu (Vulkan GPU / lavapipe CPU / WebGPU WASM). Dispatch entry points: `5-Applications/parquet_compressor/src/gpu.rs`, `gpu/wasmgpu/` (47 WGSL shaders)

## Components

- **ENE RDS** — Rust workspace replacing Python RDS (see above)
- **Storage Stack** — restic + Garage S3 + rclone (see above)
- **Lean Shim** — Lean ↔ Python bidirectional interface
- **ENE Shim** — ENE node management from Python
- **GPU Duty** — WGSL/wgpu compute dispatch (Q16_16 deterministic across all substrates)
- **Credential Gateway** — `infra/credential_server.py`, apiProvider service kind, cupfox routing
- **Adversarial Harnesses** — `shim/adversarial_duals/`: Anti-FAMM, Anti-BraidStorm, 20+ gate library entries
