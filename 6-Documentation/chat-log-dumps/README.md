# Chat Log Dumps

This directory is the parse-friendly index layer for full conversation dumps.

It does not duplicate every raw chat export. Instead, it records where the
full logs live, what format they use, how large they are, and which broad
research lanes they appear to touch. The local TiddlyWiki can link to this
section without embedding huge transcripts into `.tid` files.

## Files

- `build_manifest.py` scans known conversation/export pools.
- `manifest.jsonl` is generated and contains one JSON object per source file.
- `summary.md` is generated and gives a small human-readable inventory.

## Source Pools

- `5-Applications/audit/exploit-audit/sessions/`
- `shared-data/data/germane/research/`
- `shared-data/data/ingested/chatgpt/`
- `shared-data/data/ingested/llm_research/`
- `6-Documentation/archive/sessions/chatgpt-logs/`

## Refresh

```bash
python3 6-Documentation/chat-log-dumps/build_manifest.py
```

Generated rows are intentionally conservative. A source can be large, messy,
or duplicated; the manifest should still keep it discoverable.
