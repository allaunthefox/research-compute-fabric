# Authentik MCP Bridge Specification

> **Purpose**: Define a Model Context Protocol (MCP) server surface so any LLM can safely manage Authentik identities through structured tools.
> **Status**: Draft — not yet implemented
> **Last updated**: 2026-05-20

---

## 1. What is MCP?

[Model Context Protocol](https://modelcontextprotocol.io/) is an open standard for exposing tools, resources, and prompts to LLMs. An MCP server provides a JSON-RPC interface that a client (Claude Desktop, Cursor, a custom agent harness) can discover and invoke.

For Authentik, an MCP bridge means:

- **No raw curl** in the LLM prompt. The LLM calls `create_agent("openclaw-7", ...)` and the bridge handles the REST API.
- **Type safety**: input schemas are JSON Schema; the bridge validates before touching Authentik.
- **Auditability**: every tool call is logged with arguments and results.
- **Rate limiting / circuit breaking**: the bridge can throttle or deny dangerous operations.

---

## 2. Bridge Architecture

```
┌─────────────────┐     MCP (stdio/sse)      ┌──────────────────┐     REST + Bearer     ┌─────────────┐
│   LLM Client    │ ───────────────────────▶ │  Authentik MCP   │ ───────────────────▶  │  Authentik  │
│  (Claude /      │   JSON-RPC 2.0          │  Bridge Server   │    Token             │   API       │
│   Cursor / etc) │                         │  (Python/Node)   │                      │  :9000      │
└─────────────────┘                         └──────────────────┘                      └─────────────┘
                                                   │
                                                   │
                                          ┌────────▼─────────┐
                                          │  Audit Log       │
                                          │  (JSONL + S3)   │
                                          └─────────────────┘
```

> **Authentication required**: The bridge itself must be authenticated by Authentik. It reads `AUTHENTIK_TOKEN` at startup (from env var or the credential server). The token must belong to an Authentik account with admin-level privileges (e.g., `llm-agent-controller` in the `authentik Admins` group). Without a valid token, every tool call returns an authentication error.

### Transport options

| Transport | Use case | Endpoint |
|-----------|----------|----------|
| `stdio` | Local CLI tools, Claude Desktop | `authentik-mcp-bridge stdio` |
| `sse` | Remote/web clients, persistent connection | `authentik-mcp-bridge sse --port 8080` |

---

## 3. Tool Surface

### 3.1 `create_agent`

Create a service-account user in Authentik.

**Input schema**:
```json
{
  "username": "openclaw-instance-7",
  "name": "OpenClaw Instance 7",
  "email": "openclaw-7@researchstack.info",
  "group": "AgentManager"
}
```

**Output**:
```json
{
  "pk": 42,
  "username": "openclaw-instance-7",
  "uuid": "...",
  "group_assigned": true
}
```

**Implementation**: `POST /core/users/` then `POST /core/groups/{uuid}/add_user/`

---

### 3.2 `create_token`

Generate an API token for an existing agent.

**Input schema**:
```json
{
  "user_pk": 42,
  "identifier": "openclaw-7-token"
}
```

**Output**:
```json
{
  "identifier": "openclaw-7-token",
  "key": "keJxas4I...",
  "warning": "Store immediately — shown once"
}
```

**Implementation**: `POST /core/tokens/` then `GET /core/tokens/{identifier}/view_key/`

---

### 3.3 `list_agents`

List all service-account users.

**Input schema**:
```json
{
  "active_only": true
}
```

**Output**:
```json
{
  "agents": [
    {"pk": 7, "username": "llm-agent-controller", "is_active": true},
    {"pk": 42, "username": "openclaw-instance-7", "is_active": true}
  ]
}
```

**Implementation**: `GET /core/users/` with `?type=service_account` filter

---

### 3.4 `suspend_agent`

Soft-delete (deactivate) an agent.

**Input schema**:
```json
{
  "user_pk": 42
}
```

**Output**:
```json
{
  "ok": true,
  "pk": 42,
  "is_active": false
}
```

**Implementation**: `PATCH /core/users/{pk}/` with `{"is_active": false}`

---

### 3.5 `revoke_agent`

Hard-delete an agent and all its tokens.

**Input schema**:
```json
{
  "user_pk": 42
}
```

**Output**:
```json
{
  "ok": true,
  "pk": 42,
  "status": "deleted"
}
```

**Implementation**: `DELETE /core/users/{pk}/`

---

### 3.6 `rotate_token`

Regenerate the key for an existing token.

**Input schema**:
```json
{
  "identifier": "openclaw-7-token"
}
```

**Output**:
```json
{
  "identifier": "openclaw-7-token",
  "key": "newKey...",
  "warning": "Old key invalidated immediately"
}
```

**Implementation**: `POST /core/tokens/{identifier}/set_key/`

---

### 3.7 `create_application`

Create an application that agents can be granted access to.

**Input schema**:
```json
{
  "name": "OpenClaw Data Sink",
  "slug": "openclaw-data-sink"
}
```

**Output**:
```json
{
  "slug": "openclaw-data-sink",
  "name": "OpenClaw Data Sink",
  "meta_launch_url": ""
}
```

**Implementation**: `POST /core/applications/`

---

## 4. Safety Boundaries

| Boundary | MCP Bridge Rule |
|----------|-----------------|
| **Token exposure** | `create_token` returns the key exactly once. The bridge does not log the key. The LLM client must store it in SOPS/RDS. |
| **Scope** | The bridge authenticates with the `llm-controller-token`. It cannot escalate beyond what that token permits. |
| **Rate limit** | Configurable: max 10 `create_agent` calls per minute, max 3 `revoke_agent` calls per minute. |
| **Deny list** | The bridge refuses to operate on `akadmin` (pk=6) and `llm-agent-controller` (pk=7). |
| **Audit** | Every call writes a JSON line to `~/.cache/authentik-mcp-bridge.jsonl` and optionally to `s3://research-stack/agent-receipts/`. |

---

## 5. Reference Implementation (Python, stdio)

A minimal skeleton using the official `mcp` Python SDK:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "mcp>=1.0.0",
#   "httpx",
# ]
# ///

import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

AUTHENTIK_TOKEN = os.environ["AUTHENTIK_TOKEN"]
BASE_URL = "https://researchstack.info"

app = Server("authentik-mcp-bridge")

@app.list_tools()
async def list_tools():
    return [
        Tool(name="create_agent", description="Create a service account", inputSchema={...}),
        Tool(name="create_token", description="Create an API token", inputSchema={...}),
        Tool(name="list_agents", description="List agents", inputSchema={...}),
        Tool(name="suspend_agent", description="Deactivate an agent", inputSchema={...}),
        Tool(name="revoke_agent", description="Hard-delete an agent", inputSchema={...}),
        Tool(name="rotate_token", description="Rotate a token key", inputSchema={...}),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {"Authorization": f"Bearer {AUTHENTIK_TOKEN}"}
        if name == "create_agent":
            r = await client.post(f"{BASE_URL}/api/v3/core/users/", headers=headers, json={...})
            return [TextContent(type="text", text=r.text)]
        # ... etc

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 6. Deployment Plan

| Step | Action | Owner |
|------|--------|-------|
| 1 | Implement the 7 tools in Python using `mcp` SDK | Future agent |
| 2 | Add JSONL audit log + optional S3 sink | Future agent |
| 3 | Add rate limiting + deny-list for protected accounts | Future agent |
| 4 | Deploy as systemd service on qfox-1 or nixos-laptop | Future agent |
| 5 | Register with Claude Desktop / Cursor / OpenClaw harness | User |
| 6 | Document per-LLM configuration (env vars, transport mode) | Future agent |

---

## 7. Relationship to Existing Components

| Component | How MCP Bridge Uses It |
|-----------|----------------------|
| `authentik_agent_manager` (Rust) | The bridge is a higher-level wrapper around the same REST calls. The Rust shim supports both individual CLI commands and full DAG execution. The bridge is for LLM tool use. |
| Credential Server (RDS) | The bridge reads `AUTHENTIK_TOKEN` from the credential server at runtime: `curl http://100.101.247.127:8444/credentials/authentik` |
| SOPS secrets | Source of truth for the token. The bridge can optionally load from `sops -d` if the credential server is down. |
| `Authentik-Agent-Management.md` | Operational docs — the bridge implements the API patterns documented there. |

---

## 8. Open Questions

- Should the bridge support **application entitlement management** (granting an agent access to a specific app)? This requires `POST /core/application_entitlements/` which is more complex.
- Should the bridge support **group creation** so LLMs can define new scopes dynamically?
- Should the bridge support **impersonation** (`POST /core/users/{pk}/impersonate/`) for testing agent permissions?
