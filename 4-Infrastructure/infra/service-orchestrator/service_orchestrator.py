#!/usr/bin/env python3
"""Service Orchestrator MCP Server.

Registers/unregisters services across Authentik + Caddy + Credential Server
with a single MCP tool call. Uses PostgreSQL for the service registry and
Valkey for async job queues.

MCP tools:
  register_service   — register a new service (Authentik provider+app + Caddy route)
  unregister_service — remove a service
  list_services      — list registered services
  get_credentials    — fetch credentials from the credential server
  service_status     — get detailed status of a registered service
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

# ─── config ──────────────────────────────────────────────────────────────────

AUTHENTIK_BASE = os.getenv("AUTHENTIK_BASE", "http://localhost:9000")
AUTHENTIK_TOKEN = os.getenv("AUTHENTIK_TOKEN")
CADDY_ADMIN = os.getenv("CADDY_ADMIN", "http://100.101.247.127:2019")
CREDENTIAL_SERVER = os.getenv("CREDENTIAL_SERVER", "http://100.101.247.127:8444")
AUTHORIZATION_FLOW = os.getenv(
    "AUTHORIZATION_FLOW",
    "6e3e666f-3295-4e7e-907f-f344de3e43c9",
)
INVALIDATION_FLOW = os.getenv(
    "INVALIDATION_FLOW",
    "5c673a74-cdba-428d-a2c9-f758a88492b9",
)

# PostgreSQL + Valkey config
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://authentik:M471MCYTIJftshMz38HXRLPl6NoVIA4h@localhost:5432/authentik",
)
VALKEY_URL = os.getenv("VALKEY_URL", "redis://localhost:6379/0")

# ─── domain ──────────────────────────────────────────────────────────────────

BASE_DOMAIN = "researchstack.info"

# Known upstream targets for reverse proxy resolution
UPSTREAM_TARGETS = {
    "nixos-laptop": "100.102.173.61",
    "nixos-steamdeck": "100.85.244.73",
    "microvm-racknerd": "100.101.247.127",
    "361395-1": "100.110.163.82",
    "qfox-1": "100.88.57.96",
}


@dataclass
class ServiceManifest:
    name: str
    slug: str
    domain: str
    internal_host: str
    internal_port: int
    upstream_node: str = ""
    auth_required: bool = True
    public: bool = False
    description: str = ""  # noqa: DJ008


@dataclass
class RegisteredService:
    slug: str
    name: str
    domain: str
    internal_host: str
    internal_port: int
    authentik_provider: str
    authentik_application: str
    caddy_route_path: str
    created_at: str
    enabled: bool = True


# ─── Authentik client ────────────────────────────────────────────────────────


class AuthentikClient:
    def __init__(self, base: str, token: str) -> None:
        self.base = base.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(
            verify=False,
            headers=self.headers,
            timeout=30,
        ) as client:
            url = f"{self.base}{path}"
            resp = await client.request(method, url, json=json_data)
            if resp.status_code >= 400:
                try:
                    detail = resp.json()
                except Exception:
                    detail = resp.text
                raise RuntimeError(
                    f"Authentik API error {resp.status_code} for {method} {path}: {detail}"
                )
            if resp.status_code == 204 or not resp.content:
                return {}
            return resp.json()

    async def create_proxy_provider(
        self,
        name: str,
        internal_host: str,
        external_host: str,
    ) -> str:
        data = {
            "name": name,
            "authorization_flow": AUTHORIZATION_FLOW,
            "invalidation_flow": INVALIDATION_FLOW,
            "internal_host": internal_host,
            "external_host": external_host,
            "mode": "forward_domain",
            "access_token_validity": "hours=24",
            "refresh_token_validity": "hours=720",
        }
        result = await self._request("POST", "/api/v3/providers/proxy/", data)
        return result["pk"]

    async def create_application(self, name: str, slug: str, provider_pk: str) -> str:
        data = {
            "name": name,
            "slug": slug,
            "provider": provider_pk,
            "meta_launch_url": f"https://{slug}.{BASE_DOMAIN}",
        }
        result = await self._request("POST", "/api/v3/core/applications/", data)
        return result["pk"]

    async def delete_provider(self, pk: str) -> None:
        try:
            await self._request("DELETE", f"/api/v3/providers/proxy/{pk}/")
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                raise

    async def delete_application(self, slug: str) -> None:
        try:
            await self._request("DELETE", f"/api/v3/core/applications/{slug}/")
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                raise

    async def list_applications(self) -> list[dict[str, Any]]:
        result = await self._request("GET", "/api/v3/core/applications/")
        return result.get("results", [])

    async def list_providers(self) -> list[dict[str, Any]]:
        result = await self._request("GET", "/api/v3/providers/all/")
        return result.get("results", [])


# ─── Caddy admin client ──────────────────────────────────────────────────────


class CaddyClient:
    def __init__(self, admin_url: str) -> None:
        self.admin_url = admin_url.rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Any = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            url = f"{self.admin_url}{path}"
            resp = await client.request(method, url, json=json_data)
            if resp.status_code not in (200, 201, 204):
                raise RuntimeError(f"Caddy API error {resp.status_code}: {resp.text}")
            if resp.content:
                return resp.json()
            return {}

    async def add_route(
        self,
        hostname: str,
        upstream: str,
        auth_required: bool = True,
    ) -> str:
        route_path = f"/{hostname.replace('.', '_')}_route"
        matcher = {"host": [hostname]}

        if auth_required:
            # Replicate the forward_auth expansion that the Caddyfile adapter produces
            # using only built-in handlers (forward_auth module not compiled in).
            # Route 0: reverse_proxy to Authentik for auth decision
            # Route 1: reverse_proxy to actual upstream
            auth_headers = [
                "X-Authentik-Email", "X-Authentik-Jwt", "X-Authentik-Meta-App",
                "X-Authentik-Meta-Jwt", "X-Authentik-Meta-Version",
                "X-Authentik-Name", "X-Authentik-Uid", "X-Authentik-Username",
            ]
            copy_routes: list[dict[str, Any]] = [
                {"handle": [{"handler": "vars"}]},
            ]
            for hdr in auth_headers:
                copy_routes.append({
                    "handle": [{"handler": "headers", "request": {"delete": [hdr]}}],
                })
                copy_routes.append({
                    "handle": [{"handler": "headers", "request": {"set": {hdr: [f"{{http.reverse_proxy.header.{hdr}}}"]}}}],
                    "match": [{"not": [{"vars": {f"{{http.reverse_proxy.header.{hdr}}}": [""]}}]}],
                })

            route = {
                "group": hostname,
                "match": [matcher],
                "handle": [{
                    "handler": "subroute",
                    "routes": [
                        {
                            "handle": [{
                                "handler": "reverse_proxy",
                                "rewrite": {
                                    "method": "GET",
                                    "uri": "/outpost.goauthentik.io/auth/caddy",
                                },
                                "headers": {
                                    "request": {
                                        "set": {
                                            "X-Forwarded-Method": ["{http.request.method}"],
                                            "X-Forwarded-Uri": ["{http.request.uri}"],
                                        },
                                    },
                                },
                                "handle_response": [{
                                    "match": {"status_code": [2]},
                                    "routes": copy_routes,
                                }],
                                "upstreams": [{"dial": "100.102.173.61:9000"}],
                            }],
                        },
                        {
                            "handle": [{
                                "handler": "reverse_proxy",
                                "headers": {
                                    "request": {
                                        "set": {
                                            "Host": ["{http.request.host}"],
                                            "X-Forwarded-For": ["{http.request.remote}"],
                                            "X-Forwarded-Host": ["{http.request.host}"],
                                            "X-Forwarded-Proto": ["{http.request.scheme}"],
                                            "X-Real-Ip": ["{http.request.remote}"],
                                        },
                                    },
                                },
                                "upstreams": [{"dial": upstream}],
                            }],
                        },
                    ],
                }],
                "terminal": True,
            }
        else:
            route = {
                "group": hostname,
                "match": [matcher],
                "handle": [{
                    "handler": "subroute",
                    "routes": [{
                        "handle": [{
                            "handler": "reverse_proxy",
                            "headers": {
                                "request": {
                                    "set": {
                                        "Host": ["{http.request.host}"],
                                        "X-Forwarded-For": ["{http.request.remote}"],
                                        "X-Forwarded-Host": ["{http.request.host}"],
                                        "X-Forwarded-Proto": ["{http.request.scheme}"],
                                        "X-Real-Ip": ["{http.request.remote}"],
                                    },
                                },
                            },
                            "upstreams": [{"dial": upstream}],
                        }],
                    }],
                }],
                "terminal": True,
            }

        # Caddy v2 admin API: POST appends to the routes array
        await self._request(
            "POST",
            "/config/apps/http/servers/srv0/routes/",
            route,
        )
        return route_path

    async def remove_route(self, hostname: str) -> None:
        existing = await self._request("GET", "/config/apps/http/servers/srv0/routes/")
        routes: list[dict[str, Any]] = existing if isinstance(existing, list) else []
        cleaned = [r for r in routes if not any(
            hostname in m.get("host", []) for m in r.get("match", [])
        )]
        if len(cleaned) == len(routes):
            return
        await self._request(
            "PUT",
            "/config/apps/http/servers/srv0/routes/",
            cleaned,
        )

    async def list_routes(self) -> list[dict[str, Any]]:
        existing = await self._request("GET", "/config/apps/http/servers/srv0/routes/")
        if isinstance(existing, list):
            return existing
        return []


# ─── Credential server client ────────────────────────────────────────────────


class CredentialClient:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")

    async def list_providers(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            resp = await client.get(f"{self.base}/credentials")
            resp.raise_for_status()
            data = resp.json()
            return data.get("providers", [])

    async def get_credential(self, name: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            resp = await client.get(f"{self.base}/credentials/{name}")
            if resp.status_code == 200:
                return resp.json()
            return None


# ─── Service registry (PostgreSQL) ────────────────────────────────────────────


class ServiceRegistry:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._pool = None

    async def init(self) -> None:
        try:
            import asyncpg

            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=5,
            )
            await self._ensure_schema()
        except ImportError:
            # Fallback to in-memory for development
            self._memory_store: dict[str, dict[str, Any]] = {}
            self._memory = True

    async def _ensure_schema(self) -> None:
        if not self._pool:
            return
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE SCHEMA IF NOT EXISTS service_orchestrator;
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS service_orchestrator.services (
                    slug TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    internal_host TEXT NOT NULL,
                    internal_port INTEGER NOT NULL,
                    authentik_provider TEXT NOT NULL DEFAULT '',
                    authentik_application TEXT NOT NULL DEFAULT '',
                    caddy_route_path TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    enabled BOOLEAN NOT NULL DEFAULT TRUE
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS service_orchestrator.jobs (
                    id BIGSERIAL PRIMARY KEY,
                    service_slug TEXT REFERENCES service_orchestrator.services(slug),
                    action TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    completed_at TIMESTAMPTZ,
                    error TEXT
                );
            """)

    async def register(self, svc: RegisteredService) -> None:
        if hasattr(self, "_memory") and self._memory:
            self._memory_store[svc.slug] = {
                "slug": svc.slug,
                "name": svc.name,
                "domain": svc.domain,
                "internal_host": svc.internal_host,
                "internal_port": svc.internal_port,
                "authentik_provider": svc.authentik_provider,
                "authentik_application": svc.authentik_application,
                "caddy_route_path": svc.caddy_route_path,
                "created_at": svc.created_at,
                "enabled": svc.enabled,
            }
            return
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO service_orchestrator.services
                    (slug, name, domain, internal_host, internal_port,
                     authentik_provider, authentik_application, caddy_route_path,
                     created_at, enabled)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (slug) DO UPDATE SET
                    name = EXCLUDED.name,
                    domain = EXCLUDED.domain,
                    internal_host = EXCLUDED.internal_host,
                    internal_port = EXCLUDED.internal_port,
                    authentik_provider = EXCLUDED.authentik_provider,
                    authentik_application = EXCLUDED.authentik_application,
                    caddy_route_path = EXCLUDED.caddy_route_path,
                    enabled = EXCLUDED.enabled
                """,
                svc.slug,
                svc.name,
                svc.domain,
                svc.internal_host,
                svc.internal_port,
                svc.authentik_provider,
                svc.authentik_application,
                svc.caddy_route_path,
                svc.created_at,
                svc.enabled,
            )

    async def unregister(self, slug: str) -> bool:
        if hasattr(self, "_memory") and self._memory:
            return self._memory_store.pop(slug, None) is not None
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM service_orchestrator.services WHERE slug = $1",
                slug,
            )
            return "DELETE " in result and int(result.split()[-1]) > 0

    async def list(self) -> list[dict[str, Any]]:
        if hasattr(self, "_memory") and self._memory:
            return list(self._memory_store.values())
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM service_orchestrator.services ORDER BY created_at DESC",
            )
            return [dict(r) for r in rows]

    async def get(self, slug: str) -> dict[str, Any] | None:
        if hasattr(self, "_memory") and self._memory:
            return self._memory_store.get(slug)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM service_orchestrator.services WHERE slug = $1",
                slug,
            )
            return dict(row) if row else None


# ─── MCP protocol handlers ────────────────────────────────────────────────────


class ServiceOrchestrator:
    def __init__(self) -> None:
        self.auth = AuthentikClient(AUTHENTIK_BASE, AUTHENTIK_TOKEN)
        self.caddy = CaddyClient(CADDY_ADMIN)
        self.cred = CredentialClient(CREDENTIAL_SERVER)
        self.registry = ServiceRegistry(DATABASE_URL)

    async def init(self) -> None:
        await self.registry.init()

    def resolve_upstream(self, node_or_host: str, port: int) -> str:
        if node_or_host in UPSTREAM_TARGETS:
            ip = UPSTREAM_TARGETS[node_or_host]
        else:
            ip = node_or_host
        return f"{ip}:{port}"

    async def register_service(
        self,
        name: str,
        slug: str,
        internal_host: str,
        internal_port: int,
        auth_required: bool = True,
    ) -> dict[str, Any]:
        domain = f"{slug}.{BASE_DOMAIN}"
        upstream = self.resolve_upstream(internal_host, internal_port)
        external_host = f"https://{domain}"

        try:
            auth_provider = await self.auth.create_proxy_provider(
                f"{name} Provider",
                f"http://{upstream}",
                external_host,
            )
        except Exception as e:
            return {"ok": False, "error": f"Authentik provider creation failed: {e}"}

        try:
            auth_app = await self.auth.create_application(name, slug, auth_provider)
        except Exception as e:
            await self.auth.delete_provider(auth_provider)
            return {"ok": False, "error": f"Authentik application creation failed: {e}"}

        try:
            route_path = await self.caddy.add_route(domain, upstream, auth_required)
        except Exception as e:
            await self.auth.delete_application(slug)
            await self.auth.delete_provider(auth_provider)
            return {"ok": False, "error": f"Caddy route creation failed: {e}"}

        now = datetime.now(timezone.utc).isoformat()
        svc = RegisteredService(
            slug=slug,
            name=name,
            domain=domain,
            internal_host=internal_host,
            internal_port=internal_port,
            authentik_provider=auth_provider,
            authentik_application=auth_app,
            caddy_route_path=route_path,
            created_at=now,
        )
        await self.registry.register(svc)

        return {
            "ok": True,
            "service": {
                "slug": svc.slug,
                "name": svc.name,
                "domain": svc.domain,
                "internal_target": upstream,
                "authentik_provider": svc.authentik_provider,
                "authentik_application": svc.authentik_application,
                "auth_required": auth_required,
            },
        }

    async def unregister_service(self, slug: str) -> dict[str, Any]:
        svc = await self.registry.get(slug)
        if not svc:
            return {"ok": False, "error": f"Service '{slug}' not found"}

        domain = svc.get("domain", f"{slug}.{BASE_DOMAIN}")

        errors: list[str] = []
        if svc.get("authentik_application"):
            try:
                await self.auth.delete_application(slug)
            except Exception as e:
                errors.append(f"Authentik app delete: {e}")

        if svc.get("authentik_provider"):
            try:
                await self.auth.delete_provider(svc["authentik_provider"])
            except Exception as e:
                errors.append(f"Authentik provider delete: {e}")

        try:
            await self.caddy.remove_route(domain)
        except Exception as e:
            errors.append(f"Caddy route remove: {e}")

        await self.registry.unregister(slug)

        if errors:
            return {"ok": True, "warnings": errors}

        return {"ok": True}

    async def list_services(self) -> dict[str, Any]:
        services = await self.registry.list()
        services_list = []
        for s in services:
            services_list.append({
                "slug": s.get("slug"),
                "name": s.get("name"),
                "domain": s.get("domain"),
                "internal_host": s.get("internal_host"),
                "internal_port": s.get("internal_port"),
                "enabled": s.get("enabled", True),
                "created_at": str(s.get("created_at", "")),
            })
        return {"ok": True, "services": services_list}

    async def get_credentials(self, name: str) -> dict[str, Any]:
        providers_list = await self.cred.list_providers()
        available = [p["name"] for p in providers_list]

        if name == "_all":
            return {"ok": True, "providers": available}

        cred = await self.cred.get_credential(name)
        if cred:
            return {"ok": True, "provider": name, "credential": cred}
        return {"ok": False, "error": f"Provider '{name}' not found", "available": available}

    async def service_status(self, slug: str) -> dict[str, Any]:
        svc = await self.registry.get(slug)
        if not svc:
            return {"ok": False, "error": f"Service '{slug}' not found"}

        domain = svc.get("domain", f"{slug}.{BASE_DOMAIN}")
        upstream = self.resolve_upstream(
            svc.get("internal_host", ""),
            svc.get("internal_port", 0),
        )

        checks: dict[str, Any] = {}

        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            try:
                r = await client.get(f"https://{domain}", follow_redirects=False)
                checks["https_accessible"] = r.status_code
            except Exception as e:
                checks["https_accessible"] = f"error: {e}"

            try:
                r = await client.get(f"http://{upstream}", timeout=5)
                checks["upstream_reachable"] = r.status_code
            except Exception as e:
                checks["upstream_reachable"] = f"error: {e}"

        return {
            "ok": True,
            "service": {
                "slug": slug,
                "name": svc.get("name"),
                "domain": domain,
                "internal_target": upstream,
                "auth_enabled": svc.get("auth_required", True),
                "created_at": str(svc.get("created_at", "")),
            },
            "checks": checks,
        }


# ─── MCP server entry point ──────────────────────────────────────────────────


async def handle_request(
    orch: ServiceOrchestrator,
    request: dict[str, Any],
) -> dict[str, Any]:
    req_id = request.get("id")
    method = request.get("method", "")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "service-orchestrator",
                    "version": "0.1.0",
                },
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "register_service",
                        "description": "Register a new service: creates Authentik SSO provider + application, adds Caddy reverse proxy route, and records in the registry.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Human-readable service name"},
                                "slug": {"type": "string", "description": "URL-safe identifier (used as subdomain)"},
                                "internal_host": {"type": "string", "description": "Upstream hostname, Tailscale IP, or node name (nixos-laptop, microvm-racknerd, etc.)"},
                                "internal_port": {"type": "integer", "description": "Upstream port number"},
                                "auth_required": {"type": "boolean", "description": "Require Authentik SSO (default: true)"},
                            },
                            "required": ["name", "slug", "internal_host", "internal_port"],
                        },
                    },
                    {
                        "name": "unregister_service",
                        "description": "Remove a registered service: deletes Authentik provider + application, removes Caddy route, and deletes from registry.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "slug": {"type": "string", "description": "URL-safe service identifier to remove"},
                            },
                            "required": ["slug"],
                        },
                    },
                    {
                        "name": "list_services",
                        "description": "List all registered services with their domains and status.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                    {
                        "name": "get_credentials",
                        "description": "Get credentials from the credential server. Use '_all' as name to list available providers.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Provider name or '_all' to list"},
                            },
                            "required": ["name"],
                        },
                    },
                    {
                        "name": "service_status",
                        "description": "Check the live health of a registered service (HTTPS accessibility + upstream reachability).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "slug": {"type": "string", "description": "Service slug to check"},
                            },
                            "required": ["slug"],
                        },
                    },
                ],
            },
        }

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if tool_name == "register_service":
                result = await orch.register_service(
                    name=args["name"],
                    slug=args["slug"],
                    internal_host=args["internal_host"],
                    internal_port=args["internal_port"],
                    auth_required=args.get("auth_required", True),
                )
            elif tool_name == "unregister_service":
                result = await orch.unregister_service(args["slug"])
            elif tool_name == "list_services":
                result = await orch.list_services()
            elif tool_name == "get_credentials":
                result = await orch.get_credentials(args["name"])
            elif tool_name == "service_status":
                result = await orch.service_status(args["slug"])
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                }
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": f"{e}\n{tb}"},
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


async def main_stdio() -> None:
    orch = ServiceOrchestrator()
    await orch.init()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    writer = sys.stdout

    while True:
        line = await reader.readline()
        if not line:
            break
        line = line.decode("utf-8").strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = await handle_request(orch, request)
        writer.write(json.dumps(response, ensure_ascii=False) + "\n")
        writer.flush()


async def main_http(host: str = "0.0.0.0", port: int = 8338) -> None:
    """Run as HTTP server with JSON-RPC over HTTP for MCP."""
    orch = ServiceOrchestrator()
    await orch.init()

    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse, PlainTextResponse
    from starlette.routing import Route

    async def mcp_endpoint(request: Request) -> JSONResponse:
        body = await request.json()
        result = await handle_request(orch, body)
        return JSONResponse(result)

    async def health_endpoint(request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    async def info_endpoint(request: Request) -> JSONResponse:
        services = await orch.list_services()
        return JSONResponse({
            "service": "service-orchestrator",
            "version": "0.1.0",
            "services_count": len(services.get("services", [])),
            "mcp_endpoint": "/mcp",
        })

    app = Starlette(
        debug=False,
        routes=[
            Route("/mcp", mcp_endpoint, methods=["POST"]),
            Route("/health", health_endpoint, methods=["GET"]),
            Route("/", info_endpoint, methods=["GET"]),
        ],
    )

    import uvicorn
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"

    if mode == "http":
        port = int(os.getenv("ORCH_PORT", "8338"))
        host = os.getenv("ORCH_HOST", "0.0.0.0")
        asyncio.run(main_http(host, port))
    else:
        asyncio.run(main_stdio())
