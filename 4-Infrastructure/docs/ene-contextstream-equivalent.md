# ENE Context Stream Equivalent

Goal: make ENE provide the useful parts of ContextStream while staying local
first and receipt-bearing.

## Runtime Surface

The first live surface is:

```text
4-Infrastructure/infra/ene_contextstream_mcp.py
```

It is a stdio MCP server with these tools:

| Tool | Role |
| --- | --- |
| `ene_status` | Health for ENE API, local memory ledger, and session-sync binary |
| `ene_context` | First-call packet: status, ENE search, recall, optional transcript save |
| `ene_remember` | Durable key/value memory write with hash-chain receipt |
| `ene_recall` | Exact-key or query recall from the local ENE ledger |
| `ene_search` | Combined ENE API chat search plus local memory search |
| `ene_sessions` | List/get chat sessions through `ene-api` |
| `ene_sync` | Dry-run or run `ene-session-sync` commands |
| `ene_import_candidates` | Show pulled GitHub candidate repos and adaptation notes |

This is intentionally a shim. The existing Rust ENE surfaces remain the
long-term persistence layer:

```text
4-Infrastructure/infra/ene-rds/
4-Infrastructure/infra/ene-session-sync/
```

## GitHub Candidate Pull

Shallow clones live outside the Git tree at:

```text
shared-data/data/germane/research/github-ene-contextstream/
```

The initial candidate set from `github.com/allaunthefox`:

| Repo | ENE use |
| --- | --- |
| `Octopoda-OS` | Memory verbs: remember, recall, search, snapshot, shared memory, audit |
| `llm_wiki` | Source -> wiki -> graph ingest model, local API, search/lint contract |
| `SurfSense` | Browser, Obsidian, document connectors for personal/team knowledge capture |
| `forge` | Local tool-calling guardrails and agent loop/proxy patterns |
| `kanbots` | MCP-over-local-HTTP bridge and agent task-board semantics |
| `namidb` | Object-storage-native graph persistence design |
| `Vane` | Local answer engine, SearXNG integration, cited search history |

## Adaptation Boundary

Do not vendor these projects wholesale into ENE. Treat them as reference
implementations and pull only the small contracts ENE needs:

- memory operation vocabulary from Octopoda
- source/wiki/graph schema shape from LLM Wiki
- connector list and capture flow from SurfSense
- MCP tool bridge pattern from Kanbots
- web search/citation flow from Vane
- graph/object storage design ideas from Namidb
- local model guardrails from Forge

All promoted ENE behavior needs either a Rust implementation under
`4-Infrastructure/infra/ene-rds/` or a receipt-bearing shim under
`4-Infrastructure/infra/`.
