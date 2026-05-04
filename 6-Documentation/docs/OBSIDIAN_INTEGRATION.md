# Obsidian Integration

Status: local vault configured as an audit/shim surface.

## Local Vault

Default vault path:

```bash
/home/allaun/Documents/Research Stack/Obdisidan connector
```

The name reflects the existing local folder. It can be renamed later, but the current configuration preserves the working vault path instead of moving user data.

## Lake

Default JSON-L lake:

```bash
/home/allaun/Documents/Research Stack/data/obsidian_lake.jsonl
```

Obsidian notes are stored as `informational_bind` entries with path, title, tags, links, content hash, content preview, and full markdown content.

## Commands

Ingest local vault into the lake:

```bash
python3 scripts/obsidian_sync_shim.py ingest --backend local
```

Two-way local sync with Obsidian winning conflicts:

```bash
python3 scripts/obsidian_sync_shim.py sync --backend local
```

Export lake entries back to the vault without overwriting existing notes:

```bash
python3 scripts/obsidian_sync_shim.py export --backend local
```

Use the topological engine when it is online, otherwise fall back to the local vault:

```bash
python3 scripts/obsidian_sync_shim.py sync --backend auto
```

## Boundaries

- Obsidian is an audit and navigation surface.
- ENE/JSON-L remains the durable substrate for ingested notes.
- Notion and Linear remain tracker/publication surfaces.
- Lean remains the source of truth for formal math and invariants.
- No secrets belong in Obsidian notes.

## Related Surfaces

- `scripts/obsidian_sync_shim.py`
- `infra/topological_engine_client.py`
- `data/obsidian_lake.jsonl`
- `docs/MCP_NOTION_LINEAR_SETUP.md`
- `docs/AGENTS.md`
