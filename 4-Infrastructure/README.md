# 4-Infrastructure

**Purpose:** Python shims, GPU duty assignment, cloud storage, web interaction, hardware designs, drivers.

**Depends on:** `0` through `3`

## Contents (Target)

| Source | Destination |
|--------|-------------|
| `infra/` | `4-Infrastructure/infra/` |
| `hardware/` | `4-Infrastructure/hardware/` |
| `drivers/` | `4-Infrastructure/drivers/` |
| `config/` | `4-Infrastructure/config/` |

## Components

- **Lean Shim** — Lean ↔ Python bidirectional interface
- **ENE Shim** — ENE node management from Python
- **GPU Duty** — GPU translation surface duty assignment
- **Cloud Storage** — Rclone topological storage (Google Drive)
- **Web Surface** — BrowserPool, distributed crawl

## GPU Status

- **Device:** NVIDIA GeForce RTX 4070
- **Memory:** 12.3GB total, ~10GB available
- **CUDA:** 13.0
