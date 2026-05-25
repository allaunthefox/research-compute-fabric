# Authentik Agent Management

> **Purpose**: Enable autonomous LLM agents (OpenClaw, Hermes, ad-hoc models) to create, scope, and revoke identities in Authentik without human-in-the-loop.
> **Last updated**: 2026-05-20
> **Authentik version**: 2026.2.3
> **OpenAPI**: `https://researchstack.info/api/v3/schema/`

---

## 1. Architecture

```
┌─────────────────┐     Bearer Token      ┌──────────────────┐
│   LLM Agent     │ ────────────────────▶ │  Authentik API   │
│  (OpenClaw /    │   (llm-controller-  │  (nixos-laptop)  │
│   Hermes / etc) │      token)          │  :9000 internal  │
└─────────────────┘                        └────────┬─────────┘
                                                   │
                          ┌────────────────────────┘
                          │
              ┌───────────▼────────────┐
              │   PostgreSQL 16 (RDS)   │  ← user, group, token, app tables
              │   Redis (cache/sessions) │
              └─────────────────────────┘
```

### Key principle

Authentik is **not** directly hooked to Postgres for LLM consumption. It exposes a **REST API** (OpenAPI 3.0.3, 568 paths). The Postgres database is Authentik's internal persistence layer. LLMs interact with Authentik **exclusively through the REST API**, not via SQL.

---

## 2. Service Account Setup

### `llm-agent-controller`

| Field | Value |
|-------|-------|
| Username | `llm-agent-controller` |
| Type | `service_account` |
| Group | `AgentManager` |
| Token identifier | `llm-controller-token` |
| Token intent | `INTENT_API` |
| Active | Yes |

Created via Django shell inside the Authentik server container:

```bash
ssh allaun@100.119.165.120
cd ~/authentik
podman cp create_agent.py authentik_server_1:/tmp/
podman exec authentik_server_1 python3 /manage.py shell < /tmp/create_agent.py
```

### Token storage

The token lives in **two places**:

1. **SOPS-encrypted secrets** (repo root):
   ```bash
   sops -d 4-Infrastructure/infra/secrets/credentials.json | jq '.authentik'
   ```

2. **AWS RDS credential database** (pending — requires server-side AES key):
   - Stored in `credential_store.credentials` with `provider = 'authentik'`
   - Encrypted with the same AES-256-GCM key used by the credential server
   - The credential server on microvm-racknerd serves it via HTTP GET

---

## 3. Rust Shim (`authentik_agent_manager`)

A Rust CLI tool lives at `4-Infrastructure/shim/authentik_agent_manager/`. It supports **both individual commands and DAG execution**.

> **Authentication required**: You must be authenticated by Authentik to use this tool. Every operation requires a valid Authentik API token (`--token` or `AUTHENTIK_TOKEN` env var). The account associated with the token must have appropriate Authentik permissions. The `llm-agent-controller` service account (in the `authentik Admins` group) is the canonical identity for LLM-driven operations.

### Individual commands (familiar CLI)

```bash
cd 4-Infrastructure/shim/authentik_agent_manager
cargo build --release

export AUTHENTIK_TOKEN=$(sops -d --extract '["authentik"]["api_token"]' \
  ../../infra/secrets/credentials.json)

./target/release/authentik_agent_manager --token "$AUTHENTIK_TOKEN" list-users
./target/release/authentik_agent_manager --token "$AUTHENTIK_TOKEN" create-agent openclaw-7 "OpenClaw Instance 7"
./target/release/authentik_agent_manager --token "$AUTHENTIK_TOKEN" create-token 42 openclaw-7-token
./target/release/authentik_agent_manager --token "$AUTHENTIK_TOKEN" suspend 42
./target/release/authentik_agent_manager --token "$AUTHENTIK_TOKEN" revoke 42
```

### DAG mode (the primary feature)

Define a JSON DAG plan and execute it atomically:

```bash
./target/release/authentik_agent_manager --token "$TOKEN" execute plan.json
```

Example `plan.json`:

```json
{
  "nodes": [
    {
      "id": "create_user",
      "op": "create_user",
      "params": {
        "username": "openclaw-7",
        "name": "OpenClaw Instance 7"
      }
    },
    {
      "id": "create_token",
      "op": "create_token",
      "depends_on": ["create_user"],
      "params": { "identifier": "openclaw-7-token" },
      "input_mapping": { "user_pk": "create_user.pk" }
    },
    {
      "id": "add_to_group",
      "op": "add_to_group",
      "depends_on": ["create_user"],
      "params": { "group_name": "AgentManager" },
      "input_mapping": { "user_pk": "create_user.pk" }
    }
  ]
}
```

**How it works**:

1. The shim computes a **topological order** (Kahn's algorithm).
2. Each node runs only after its `depends_on` prerequisites succeed.
3. `input_mapping` pulls fields from upstream node outputs into downstream params.
4. Every execution writes a **receipt** to `~/.cache/authentik-dag-receipts.jsonl`.

**Operations supported in DAG**:

| Operation | Description |
|-----------|-------------|
| `create_user` | Create a service-account user |
| `create_token` | Generate an API token for a user |
| `add_to_group` | Add a user to a named group |
| `list_users` | List all users (read-only) |
| `list_groups` | List all groups (read-only) |
| `suspend_user` | Deactivate a user |
| `revoke_user` | Hard-delete a user |
| `rotate_token` | Regenerate a token key |
| `create_application` | Create an application |

---

## 4. API Patterns for LLM Agents

### Authentication

Every request includes:

```
Authorization: Bearer <token>
```

### 4.1 Create a new agent (user)

```bash
TOKEN=$(sops -d --extract '["authentik"]["api_token"]' 4-Infrastructure/infra/secrets/credentials.json)

curl -s -X POST https://researchstack.info/api/v3/core/users/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "openclaw-instance-7",
    "name": "OpenClaw Instance 7",
    "type": "service_account",
    "is_active": true,
    "email": "openclaw-7@researchstack.info"
  }' | jq .
```

**Response**:
```json
{
  "pk": 42,
  "username": "openclaw-instance-7",
  "name": "OpenClaw Instance 7",
  "email": "openclaw-7@researchstack.info",
  "is_active": true,
  "type": "service_account",
  "uuid": "..."
}
```

### 4.2 Create an API token for the new agent

```bash
curl -s -X POST https://researchstack.info/api/v3/core/tokens/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "openclaw-7-token",
    "intent": "api",
    "user": 42,
    "description": "API token for OpenClaw instance 7"
  }' | jq '.key'
```

**Important**: Save the `.key` from the response — it is shown **only once**.

### 4.3 Add agent to a scoped group

Groups define what applications and resources an agent can access.

```bash
# Get the AgentManager group UUID
GROUP_UUID=$(curl -s https://researchstack.info/api/v3/core/groups/ \
  -H "Authorization: Bearer $TOKEN" | jq -r '.results[] | select(.name=="AgentManager") | .pk')

# Add user to group
curl -s -X POST "https://researchstack.info/api/v3/core/groups/${GROUP_UUID}/add_user/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pk": 42}'
```

### 4.4 Create an application (what the agent can access)

```bash
curl -s -X POST https://researchstack.info/api/v3/core/applications/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenClaw Data Sink",
    "slug": "openclaw-data-sink",
    "provider": null,
    "policy_engine_mode": "any"
  }' | jq .
```

### 4.5 List all agents

```bash
curl -s https://researchstack.info/api/v3/core/users/ \
  -H "Authorization: Bearer $TOKEN" | jq '.results[] | {pk, username, name, is_active}'
```

### 4.6 Revoke an agent (soft delete)

```bash
curl -s -X PATCH "https://researchstack.info/api/v3/core/users/42/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### 4.7 Hard delete an agent

```bash
curl -s -X DELETE "https://researchstack.info/api/v3/core/users/42/" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 4. Agent Lifecycle

### State machine

```
[Provisioning] ──▶ [Active] ──▶ [Suspended] ──▶ [Revoked]
      │                │            │
      │                ▼            │
      │            [Token          │
      │             Rotation]       │
      │                │            │
      └────────────────┴────────────┘
```

### 4.1 Provisioning

1. LLM decides a new agent is needed (e.g., a new model instance, a specialized worker)
2. LLM calls `POST /core/users/` with `type: service_account`
3. LLM calls `POST /core/tokens/` to generate an API token for the new agent
4. LLM calls `POST /core/groups/{uuid}/add_user/` to assign RBAC scope
5. LLM stores the new token in the credential system (SOPS + RDS)

### 4.2 Active operation

- Agent uses its own token to authenticate to Authentik-protected applications
- Agent may query `GET /core/users/me/` to verify its own identity
- Agent may read application entitlements via `GET /core/application_entitlements/`

### 4.3 Token rotation

```bash
# Regenerate key for an existing token
curl -s -X POST "https://researchstack.info/api/v3/core/tokens/openclaw-7-token/set_key/" \
  -H "Authorization: Bearer $TOKEN" | jq '.key'
```

**Policy**: Rotate tokens every 90 days. The old key becomes invalid immediately.

### 4.4 Suspension (soft revoke)

Set `is_active: false` on the user. The user and all its tokens remain in the database but cannot authenticate. This is reversible.

### 4.5 Hard revocation

`DELETE /core/users/{pk}/` — irreversible. All tokens, sessions, and group memberships for that user are cascade-deleted.

---

## 5. Security Boundaries

| Boundary | Rule |
|----------|------|
| **Token visibility** | The `llm-controller-token` is known only to the SOPS secrets file and the RDS credential database. Never log it. |
| **Scope** | The `AgentManager` group currently has no Authentik-native RBAC restrictions. **Future**: bind AgentManager to a custom role that limits `users` CRUD to `service_account` types only. |
| **Network** | Authentik admin API is exposed only via `researchstack.info:443` (Caddy reverse proxy). Direct `:9000` access is blocked by nixos-laptop firewall. |
| **Audit** | All API calls are logged by Authentik. Future: wire `access_log` table in RDS to record credential fetches. |
| **Rate limiting** | No explicit rate limit is configured. Future: add Caddy rate limiting on `/api/v3/` paths. |

---

## 6. Integration with Other Stack Components

| Component | Integration Pattern |
|-----------|-------------------|
| **Credential Server** | LLM controller token served from RDS at `http://100.101.247.127:8444/credentials/authentik` |
| **SOPS Secrets** | Token + metadata encrypted in `4-Infrastructure/infra/secrets/credentials.json` |
| **Garage S3** | Agent artifacts (receipts, outputs) stored in `research-stack` bucket with per-agent prefix |
| **RDS Postgres** | `credential_store` schema holds the token; `access_log` table records fetches (not yet wired) |
| **Tailscale** | All internal traffic (LLM → Authentik API, Authentik → Postgres, etc.) flows over Tailscale mesh |

---

## 7. TODO / Next Steps

- [ ] **Wire access_log** on every credential fetch from RDS
- [ ] **Add node_assignments** enforcement (only qfox-1, nixos-laptop may request the authentik token)
- [ ] **Create custom role** in Authentik to restrict `AgentManager` to `service_account` CRUD only
- [ ] **Add Caddy rate limit** for `/api/v3/` paths on microvm-racknerd
- [ ] **Generate typed client** from OpenAPI spec (e.g., `openapi-python-client`)
- [ ] **Build MCP server** wrapping the 7 key endpoints (create user, create token, add to group, list users, suspend, revoke, rotate)
- [ ] **Document per-agent application binding** — how each LLM agent gets its own scoped application
