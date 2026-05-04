# MCP Notion + Linear Integration Setup

## Overview

The MCP (Model Context Protocol) server at `mcp_notion_linear.py` provides unified access to Notion and Linear APIs using existing Research Stack surfaces:

- **Notion**: Research database management, page creation, content sync
- **Linear**: Issue tracking, project management, workflow automation
- **ENE Integration**: Credential management via distributed node encryption (planned)
- **Web Surface**: HTTP API calls via SwarmWebSurface

## Architecture

```
Claude Code
    ↓
MCP Server (mcp_notion_linear.py)
    ↓
SwarmWebSurface (infra/web_interaction_surface.py)
    ↓
HTTP APIs (Notion, Linear)
    ↓
ENE (Credential Management - planned)
```

## Prerequisites

### 1. MCP SDK Installation

```bash
pip install mcp
```

### 2. Notion Setup

Follow the instructions in `docs/NOTION_SETUP.md`:

1. Create integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Copy the integration token (NOTION_API_KEY)
3. Get your database ID from the URL (32-character string)
4. Share the database with your integration

### 3. Linear Setup

1. Go to [linear.app/settings/api](https://linear.app/settings/api)
2. Create a personal API key
3. Copy the key (LINEAR_API_KEY)

## Configuration

### Environment Variables

Set the following environment variables:

```bash
export NOTION_API_KEY="your_notion_integration_token"
export NOTION_DATABASE_ID="your_32_char_database_id"
export LINEAR_API_KEY="your_linear_api_key"
```

### For Development

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# Notion
export NOTION_API_KEY="secret_..."
export NOTION_DATABASE_ID="abc123..."

# Linear
export LINEAR_API_KEY="lin_api_..."
```

## Available Tools

### Notion Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `notion_query_database` | Query Notion database with filters | `database_id`, `filter` |
| `notion_create_page` | Create new page in Notion | `parent_id`, `properties`, `content` |
| `notion_update_page` | Update existing page | `page_id`, `properties` |
| `notion_get_page` | Get page content | `page_id` |

### Linear Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `linear_query_issues` | Query issues from Linear | `team_key`, `status` |
| `linear_create_issue` | Create new issue | `team_id`, `title`, `description` |
| `linear_update_issue_state` | Update issue state | `issue_id`, `state_id` |

### System Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `check_credentials` | Check configured credentials | none |
| `sync_research_to_notion` | Sync Research Stack papers to Notion | `paper_path` |

## Usage

### Running the MCP Server

```bash
python mcp_notion_linear.py
```

### Claude Code Configuration

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "notion-linear": {
      "command": "python",
      "args": ["/home/allaun/Documents/Research Stack/mcp_notion_linear.py"],
      "env": {
        "NOTION_API_KEY": "your_key",
        "NOTION_DATABASE_ID": "your_db_id",
        "LINEAR_API_KEY": "your_key"
      }
    }
  }
}
```

## Example Workflows

### 1. Sync Paper to Notion

```
Tool: sync_research_to_notion
Parameters: {
  "paper_path": "/home/allaun/Documents/Research Stack/docs/papers/LATTICE_POST_QUANTUM_CRINGE_DEFENSE_2026-04-25.md"
}
```

### 2. Create Linear Issue from Research

```
Tool: linear_create_issue
Parameters: {
  "team_id": "TEAM_ID",
  "title": "Implement AngrySphinx in production",
  "description": "Based on lattice-based post-quantum cryptography research..."
}
```

### 3. Query Notion Database

```
Tool: notion_query_database
Parameters: {
  "database_id": "abc123...",
  "filter": {
    "property": "Status",
    "select": {
      "equals": "In Progress"
    }
  }
}
```

## ENE Integration (Planned)

Future versions will integrate with ENE (Endless Node Edges) for:

- **AES-256-GCM encryption** of API credentials
- **Shamir-secret sharing** (6 shards, 2/3 threshold)
- **Health-weighted routing** across 6-node mesh
- **Consensus-based credential rotation**

This will eliminate plaintext credentials from environment variables.

## Security Notes

1. **Never commit API keys** to git
2. **Use ENE for production** - environment variables only for development
3. **Rotate keys regularly** via Linear/Notion settings
4. **Audit access logs** in Notion/Linear dashboards
5. **Monitor ENE node health** via `get_ene_status` tool
6. **Credentials are AES-256-GCM encrypted** when stored in ENE
7. **Shamir-secret sharing** ensures no single point of failure

## Troubleshooting

### "Notion credentials not configured"

- Check ENE status via `get_ene_status`
- If ENE disabled, check that `NOTION_API_KEY` is set
- Verify database is shared with integration (see NOTION_SETUP.md)

### "Linear credentials not configured"

- Check ENE status via `get_ene_status`
- If ENE disabled, check that `LINEAR_API_KEY` is set
- Verify key has necessary permissions

### "ENE initialization failed"

- Check that `infra/ene_cloud_credential_manager.py` exists
- Verify ENE databases are accessible
- Check that `ene_api` module is available
- Falls back to environment variables automatically

### "No browsers available"

- The web interaction surface uses a browser pool
- Check SwarmWebSurface health via `health()` method
- Default: min 2, max 20 browsers

## Development Notes

Per `AGENTS.md`, this is a **shim layer**:
- All core logic resides in Lean modules
- This file handles external API integration only
- No invariant checks or cost functions in this layer
- Credentials managed via ENE (planned)

## File Locations

- **MCP Server**: `mcp_notion_linear.py`
- **Web Surface**: `infra/web_interaction_surface.py`
- **Notion Setup**: `docs/NOTION_SETUP.md`
- **Example MCP**: `mcp_server.py` (swarm integration)

## Status

✅ Notion API integration  
✅ Linear API integration  
✅ Web surface integration  
✅ ENE credential management (implemented)  
✅ AES-256-GCM encryption  
✅ Health-weighted node routing  
✅ Shamir-secret sharing (6 shards)  
✅ Environment variable fallback  
⏳ Production deployment (pending)
