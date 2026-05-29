# API Documentation — Research Stack Services

**Last updated:** 2026-05-29
**Base URL:** `https://researchstack.info`
**Auth:** Authentik OIDC (SSO) or Bearer token (API endpoints)

---

## Authentication

### OIDC (SSO) — Web Endpoints

Web-facing endpoints use Authentik OIDC. Access via browser redirects to `auth.researchstack.info`.

### Token Auth — API Endpoints

API endpoints (`/api/*`) use Bearer token authentication:

```
Authorization: Bearer <token>
```

Tokens are managed by the Credential Server.

---

## Cluster Dashboard

**Namespace:** `monitoring`
**Internal URL:** `http://cluster-dashboard:8787`
**External URL:** `https://researchstack.info/server/dash/` (via Homarr)
**Tech:** FastAPI + Vite

### Endpoints

#### `GET /`

Dashboard UI (Vite SPA).

#### `GET /api/status`

Cluster health summary.

**Response:**
```json
{
  "nodes": [
    {
      "name": "nixos-laptop",
      "status": "Ready",
      "ip": "100.102.173.61",
      "roles": "control-plane",
      "version": "v1.35.4+k3s1"
    }
  ],
  "pods": {
    "total": 24,
    "running": 23,
    "pending": 0,
    "failed": 1
  },
  "namespaces": ["services", "media", "monitoring", "ai-models", "edge", "research", "mail"]
}
```

#### `GET /api/metrics`

Prometheus-compatible metrics.

#### `WebSocket /ws/live`

Real-time cluster events stream.

**Message format:**
```json
{
  "type": "pod_event",
  "namespace": "services",
  "pod": "homer-abc123",
  "status": "Running",
  "timestamp": "2026-05-29T12:00:00Z"
}
```

---

## Credential Server

**Namespace:** `services`
**Internal URL:** `http://credential-server:8080`
**External URL:** `https://researchstack.info/api/cred/`
**Auth:** Bearer token

### Endpoints

#### `GET /api/cred/health`

Health check.

**Response:** `200 OK`
```json
{"status": "ok"}
```

#### `GET /api/cred/tokens`

List available tokens (requires admin token).

**Response:**
```json
{
  "tokens": [
    {"name": "registry", "scope": "read,write", "expires": "2026-12-31"},
    {"name": "jobs", "scope": "read,write,execute", "expires": "2026-12-31"}
  ]
}
```

#### `POST /api/cred/issue`

Issue a new token.

**Request:**
```json
{
  "name": "service-name",
  "scope": "read,write",
  "ttl": "30d"
}
```

**Response:**
```json
{
  "token": "rs_tk_...",
  "expires": "2026-06-29T12:00:00Z"
}
```

#### `POST /api/cred/validate`

Validate a token.

**Request:**
```json
{"token": "rs_tk_..."}
```

**Response:**
```json
{
  "valid": true,
  "name": "registry",
  "scope": "read,write"
}
```

---

## Registry API

**Namespace:** `services`
**Internal URL:** `http://registry-api:8080`
**External URL:** `https://researchstack.info/api/registry/`
**Auth:** Bearer token

### Endpoints

#### `GET /api/registry/health`

Health check.

#### `GET /api/registry/artifacts`

List all registered artifacts.

**Query Parameters:**
- `type` — Filter by artifact type (e.g., `bitstream`, `lean-build`, `receipt`)
- `since` — ISO 8601 timestamp
- `limit` — Max results (default: 50)

**Response:**
```json
{
  "artifacts": [
    {
      "id": "art_abc123",
      "name": "research_stack_top.fs",
      "type": "bitstream",
      "size": 184320,
      "sha256": "...",
      "created": "2026-05-29T10:00:00Z",
      "tags": ["fpga", "production"]
    }
  ],
  "total": 42
}
```

#### `POST /api/registry/artifacts`

Register a new artifact.

**Request:**
```json
{
  "name": "research_stack_top.fs",
  "type": "bitstream",
  "sha256": "...",
  "blob_ref": "blob_xyz",
  "tags": ["fpga"]
}
```

#### `GET /api/registry/artifacts/{id}`

Get artifact by ID.

#### `PUT /api/registry/artifacts/{id}`

Update artifact metadata.

#### `DELETE /api/registry/artifacts/{id}`

Remove artifact registration (does not delete blob).

---

## Jobs API

**Namespace:** `services`
**Internal URL:** `http://jobs-api:8080`
**External URL:** `https://researchstack.info/api/jobs/`
**Auth:** Bearer token

### Endpoints

#### `GET /api/jobs/health`

Health check.

#### `GET /api/jobs`

List jobs.

**Query Parameters:**
- `status` — Filter: `pending`, `running`, `completed`, `failed`
- `type` — Filter by job type
- `limit` — Max results (default: 20)

**Response:**
```json
{
  "jobs": [
    {
      "id": "job_abc123",
      "type": "lean-build",
      "status": "completed",
      "created": "2026-05-29T10:00:00Z",
      "started": "2026-05-29T10:00:05Z",
      "finished": "2026-05-29T10:05:30Z",
      "result": {
        "jobs": 3572,
        "errors": 0
      }
    }
  ],
  "total": 156
}
```

#### `POST /api/jobs`

Create a new job.

**Request:**
```json
{
  "type": "lean-build",
  "params": {
    "target": "Semantics",
    "branch": "main"
  },
  "priority": "normal"
}
```

**Response:**
```json
{
  "id": "job_def456",
  "status": "pending",
  "created": "2026-05-29T12:00:00Z"
}
```

#### `GET /api/jobs/{id}`

Get job status and result.

#### `POST /api/jobs/{id}/cancel`

Cancel a pending or running job.

#### `GET /api/jobs/{id}/logs`

Stream job logs (Server-Sent Events).

**Response:** `text/event-stream`
```
data: {"line": "Building Semantics...", "ts": "2026-05-29T12:00:01Z"}
data: {"line": "3572 jobs, 0 errors", "ts": "2026-05-29T12:05:30Z"}
```

---

## Blobs API

**Namespace:** `services`
**Internal URL:** `http://blobs-api:8080`
**External URL:** `https://researchstack.info/api/blobs/`
**Auth:** Bearer token

### Endpoints

#### `GET /api/blobs/health`

Health check.

#### `POST /api/blobs`

Upload a blob.

**Request:** `multipart/form-data`
- `file` — Binary file content
- `sha256` — Expected SHA-256 hash (verification)

**Response:**
```json
{
  "id": "blob_xyz789",
  "size": 184320,
  "sha256": "...",
  "created": "2026-05-29T12:00:00Z"
}
```

#### `GET /api/blobs/{id}`

Download a blob.

**Response:** `application/octet-stream` with blob content.

#### `HEAD /api/blobs/{id}`

Check blob existence.

**Response:** `200 OK` (exists) or `404 Not Found`

#### `DELETE /api/blobs/{id}`

Delete a blob.

#### `GET /api/blobs`

List blobs.

**Query Parameters:**
- `limit` — Max results
- `offset` — Pagination offset

---

## Authentik — OIDC Configuration

**URL:** `https://auth.researchstack.info`
**Protocol:** OpenID Connect

### Provider Configuration

| Field | Value |
|-------|-------|
| Authorization URL | `https://auth.researchstack.info/application/o/authorize/` |
| Token URL | `https://auth.researchstack.info/application/o/token/` |
| UserInfo URL | `https://auth.researchstack.info/application/o/userinfo/` |
| JWKS URL | `https://auth.researchstack.info/application/o/research-stack/jwks/` |
| Issuer | `https://auth.researchstack.info/application/o/research-stack/` |

### Scopes

| Scope | Description |
|-------|-------------|
| `openid` | Standard OIDC |
| `profile` | User profile (name, email) |
| `email` | Email address |
| `groups` | Group membership |

### Redirect URIs

```
https://researchstack.info/oidc/callback
https://researchstack.info/apps/chat/oidc/callback
https://researchstack.info/apps/budget/oidc/callback
```

### Application Setup

In Authentik admin:

1. **Applications** → Create → Name: `Research Stack`
2. **Providers** → Create → OAuth2/OpenID Provider
3. Set client type: `Confidential`
4. Set redirect URIs above
5. Assign to application

### Service Account Tokens

For API-to-API auth (no user interaction):

```bash
# Create service account in Authentik
# Admin → Directory → Users → Create
# Type: Service Account

# Get token
curl -X POST https://auth.researchstack.info/application/o/token/ \
  -d "grant_type=client_credentials" \
  -d "client_id=<service-account-id>" \
  -d "client_secret=<service-account-secret>" \
  -d "scope=openid"
```

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (missing or invalid token) |
| 403 | Forbidden (insufficient scope) |
| 404 | Not found |
| 409 | Conflict (duplicate resource) |
| 422 | Unprocessable entity (validation error) |
| 500 | Internal server error |

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/cred/*` | 100 req | 1 minute |
| `/api/registry/*` | 200 req | 1 minute |
| `/api/jobs/*` | 50 req | 1 minute |
| `/api/blobs/*` | 100 req | 1 minute |

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1685366400
```
