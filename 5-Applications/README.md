# 5-Applications

**Purpose:** End-to-end pipelines, integration tests, automation scripts, benchmarks, audit.

**Depends on:** `0` through `4`

## Contents (Target)

| Source | Destination |
|--------|-------------|
| `5-Applications/scripts/` | `5-Applications/scripts/` |
| `5-Applications/tests/` | `5-Applications/tests/` |
| `5-Applications/out/` | `5-Applications/out/` |
| `5-Applications/audit/` | `5-Applications/audit/` |

## Scripts

- `build_manifold_graphml.py`
- `export_manifold_to_obsidian.py`
- `hot_swap_daemon.py`
- `hot_swap_manager.py`

## Pipeline

1. Generate provably hard question (Builder: ADD clock)
2. Route via OmnidirectionalInterface (Lean)
3. Execute via DomainModelIntegration (Lean → Python shim)
4. Store in Google Drive topological storage (Warden: SUBTRACT clock)
5. Hardware triumvirate integration (Judge: PAUSE clock)
