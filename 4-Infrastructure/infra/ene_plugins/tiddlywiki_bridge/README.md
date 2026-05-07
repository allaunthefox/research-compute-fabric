# TiddlyWiki ENE Bridge

Frontline hotswappable plugin for the planned ENE revamp.

The bridge scans local TiddlyWiki `.tid` files and turns each tiddler into an
ENE package with a deterministic receipt. It is intentionally usable before
the full plugin runtime exists: run it as a standalone CLI now, then mount the
same module behind the future ENE plugin loader later.

## Dry Run

```bash
python3 4-Infrastructure/infra/ene_plugins/tiddlywiki_bridge/tiddlywiki_ene_bridge.py \
  --dry-run \
  --limit 5
```

## Ingest

```bash
python3 4-Infrastructure/infra/ene_plugins/tiddlywiki_bridge/tiddlywiki_ene_bridge.py \
  --ingest
```

## Behavior

- parses TiddlyWiki field blocks and body text
- computes source and plugin receipts
- derives a bounded route vector
- writes one ENE package per tiddler
- skips `$:/` system tiddlers by default
- stores incremental plugin state in SQLite
- refuses active script content
- supports `--dry-run` so loader/admission logic can plan before commit
