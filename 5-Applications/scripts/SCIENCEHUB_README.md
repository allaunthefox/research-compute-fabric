# ScienceHub MCP — Sovereign Research Surface

## What It Is
An MCP server that lets your LLM say **"I need <topic>"** and automatically:
1. Searches your local corpus (Zotero + PDFs)
2. If missing, fetches from arXiv
3. Ingests into Zotero + local storage
4. Returns a structured report

## Installation

### Requirements
- Python 3.11+
- `mcp` SDK: `pip install mcp`
- `pdftotext` + `pdfinfo` (from poppler-utils)
- SQLite (built-in)

### MCP Client Config (Claude Desktop)
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sciencehub": {
      "command": "python3",
      "args": [
        "/home/allaun/Documents/Research Stack/scripts/sciencehub_mcp.py"
      ]
    }
  }
}
```

### MCP Client Config (Cline / Continue)
Add to your `.vscode/mcp-settings.json` or Cline MCP settings:

```json
{
  "mcpServers": [
    {
      "name": "sciencehub",
      "command": "python3",
      "args": [
        "/home/allaun/Documents/Research Stack/scripts/sciencehub_mcp.py"
      ]
    }
  ]
}
```

## Tools

### `need` — The "I need X" pipeline
**Input:** `{"query": "I need attention mechanism survey", "auto_ingest": true}`

**What happens:**
- Searches local Zotero library + PDF corpus
- If found locally → returns hit list, no fetch
- If missing → searches arXiv, downloads PDF, ingests to Zotero, reports back

### `search_local` — Query your corpus
**Input:** `{"query": "burgers turbulence", "limit": 10}`

Searches:
- `zotero_items` (titles, DOIs, URLs, extras)
- `local_pdfs` (filenames, arXiv IDs, DOIs)
- `arxiv_meta` (cached abstracts)

### `fetch_arxiv` — Direct download by ID
**Input:** `{"arxiv_id": "1706.03762", "ingest": true}`

Downloads to `~/Downloads/data/Downloads_from_internet/Deep Research/alphaXiv_PDFs_2026_04/`
and creates a Zotero item.

### `review_paper` — Quick PDF review
**Input:** `{"path": "/path/to/paper.pdf"}`

Runs `pdfinfo` + `pdftotext -l 1` and returns metadata + first-page excerpt.

### `corpus_report` — Library stats
Returns counts of Zotero items, local PDFs, completed/failed needs.

## CLI Mode (no MCP client needed)
```bash
cd "/home/allaun/Documents/Research Stack"

# Stats
python3 scripts/sciencehub_mcp.py --report

# Search local corpus
python3 scripts/sciencehub_mcp.py --search "burgers turbulence"

# Full "I need" pipeline (dry-run with --no-ingest)
python3 scripts/sciencehub_mcp.py "I need attention mechanism survey"

# Review a specific PDF
python3 scripts/sciencehub_mcp.py --review /path/to/paper.pdf

# Fetch by arXiv ID
python3 scripts/sciencehub_mcp.py --fetch 1706.03762
```

## Companion Scripts

### Ingest Watcher (`ingest_watcher.py`)
Monitors directories for new PDFs, auto-ingests them into Zotero.

```bash
# Dry run
python3 scripts/ingest_watcher.py --once --dry-run

# Actual ingest
python3 scripts/ingest_watcher.py --once

# Daemon mode
python3 scripts/ingest_watcher.py --daemon --interval 60
```

### Review Agent (`review_agent.py`)
Generates structured reviews for ingested papers.

```bash
# Review one paper
python3 scripts/review_agent.py --paper /path/to/paper.pdf

# Batch review 5 unreviewed papers
python3 scripts/review_agent.py --batch 5

# Daemon mode (loops every 5 min)
python3 scripts/review_agent.py --daemon --interval 300
```

## Architecture
```
┌─────────────────────────────────────────┐
│  LLM (Claude / Cline / Continue)        │
│  says: "I need <topic>"                  │
└──────────────────┬──────────────────────┘
                   │  MCP stdio
┌──────────────────▼──────────────────────┐
│  sciencehub_mcp.py                      │
│  ├── ScienceHub.need(query)             │
│  │   ├── CorpusIndex.search(query)      │
│  │   └── if miss → ArxivClient.search() │
│  │       └── ArxivClient.download()      │
│  │           └── ZoteroWriter.add_preprint()│
│  └── review_paper → pdfinfo + pdftotext │
└─────────────────────────────────────────┘
```

## Data Flow
- **Zotero DB:** `~/Zotero/zotero.sqlite` (read + write)
- **Index DB:** `~/Research Stack/data/substrate_index.db` (read + write)
- **PDF Archive:** `~/Downloads/data/Downloads_from_internet/Deep Research/alphaXiv_PDFs_2026_04/`
- **Watcher Log:** `~/Research Stack/data/ingest_watcher.log`

## Safety
- Zotero DB is **backed up automatically** before every write (`zotero.sqlite.backup.YYYYMMDD_HHMMSS`)
- On any write failure, backup is **restored automatically**
- arXiv downloads are **validated** (must be > 1KB)
- Duplicate authors are **deduplicated** (unique constraint handled)

## Troubleshooting
| Problem | Fix |
|---------|-----|
| "arXiv search failed" | Check internet; script uses `https://export.arxiv.org` |
| "Zotero ingest failed" | Check Zotero is closed (no lock on DB) |
| "No text" in review | PDF may be scanned/image; needs OCR |
| MCP not connecting | Verify `pip install mcp` and Python path |
| Ollama review hangs | Switch to stub mode: set `OLLAMA_MODEL` env or pass `--stub` |
