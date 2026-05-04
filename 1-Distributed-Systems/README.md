# 1-Distributed-Systems

**Purpose:** Self-replicating distributed mesh with gossip protocol, consensus, and credential distribution.

**Depends on:** `0-Core-Formalism` (Triumvirate consensus)

## Contents (Target)

| Source | Destination |
|--------|-------------|
| `infra/ene_*.py` | `1-Distributed-Systems/ene/` |
| `data/ene_nodes/` | `1-Distributed-Systems/ene/nodes/` |
| `data/ene_provenance/` | `1-Distributed-Systems/ene/provenance/` |

## Concepts

- **ENE (Endless Node Edges)** — distributed, self-replicating system
- **Gossip Protocol** — discovery, heartbeat, credential_sync, replicate
- **Shamir-Secret Sharing** — credential fragments across nodes
- **Consensus** — 2/3 majority for credential rotation

## Deployment (6-node mesh)

- qfox (primary, 16 cores, 32GB, 1 GPU)
- architect (8 cores, 16GB)
- judge (4 cores, 8GB)
- AWS node (2 cores, 4GB)
- Netcup VPS (4 cores, 8GB)
- Racknerd VPS (2 cores, 4GB)
