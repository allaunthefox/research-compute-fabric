# Obsidian Sync

Local Obsidian sync is configured through:

```bash
scripts/obsidian_sync_shim.py
```

## Commands

```bash
python3 scripts/obsidian_sync_shim.py ingest --backend local
python3 scripts/obsidian_sync_shim.py sync --backend local
python3 scripts/obsidian_sync_shim.py sync --backend auto
```

## Configuration

```bash
OBSIDIAN_VAULT_PATH=/home/allaun/Research Stack/Obdisidan connector
OBSIDIAN_LAKE_PATH=/home/allaun/Research Stack/data/obsidian_lake.jsonl
```

## Notes

- Obsidian wins conflicts by default.
- Existing notes are not overwritten unless `--lake-wins` is passed.
- `--backend auto` uses the topological engine when healthy and falls back to the local vault.
