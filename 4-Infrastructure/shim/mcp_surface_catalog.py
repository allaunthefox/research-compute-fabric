#!/usr/bin/env python3
"""Catalog local and pulled MCP surfaces as gated Research Stack adapters.

This script inventories MCP-like surfaces without starting them. It snapshots
external repositories, records local MCP entrypoints, ranks useful surfaces for
the OpenClaw/metaprobe bus, and emits receipt + curriculum + wiki artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
WIKI = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"
MCP_EXTERNAL = REPO / "5-Applications" / "tools-scripts" / "external" / "mcp"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path: Path, limit: int = 16000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def run_git(path: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(path), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def package_summary(path: Path) -> dict[str, Any]:
    package_path = path / "package.json"
    if package_path.exists():
        try:
            data = json.loads(package_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        return {
            "name": data.get("name"),
            "version": data.get("version"),
            "description": data.get("description"),
            "license": data.get("license"),
            "scripts": sorted((data.get("scripts") or {}).keys())[:40],
        }
    pyproject_path = path / "pyproject.toml"
    if pyproject_path.exists():
        try:
            data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        project = data.get("project", {})
        return {
            "name": project.get("name"),
            "version": project.get("version"),
            "description": project.get("description"),
            "license": project.get("license"),
            "scripts": sorted((project.get("scripts") or {}).keys())[:40],
        }
    return {}


def repo_surface(name: str, path: Path, role: str, priority: int, gate: str) -> dict[str, Any]:
    readme = read_text(path / "README.md")
    return {
        "id": name,
        "kind": "external_snapshot",
        "path": str(path.relative_to(REPO)),
        "remote": run_git(path, "remote", "get-url", "origin"),
        "commit": run_git(path, "rev-parse", "HEAD"),
        "working_tree_clean": run_git(path, "status", "--short") == "",
        "package": package_summary(path),
        "role": role,
        "priority": priority,
        "gate": gate,
        "source_fingerprint": sha256_text(readme[:8000] + run_git(path, "rev-parse", "HEAD")),
    }


def local_surface(surface_id: str, path: Path, role: str, priority: int, gate: str, smoke: dict[str, Any] | None = None) -> dict[str, Any]:
    text = read_text(path)
    return {
        "id": surface_id,
        "kind": "local_surface",
        "path": str(path.relative_to(REPO)),
        "source_hash": file_hash(path),
        "role": role,
        "priority": priority,
        "gate": gate,
        "smoke": smoke or {},
        "source_fingerprint": sha256_text(text[:8000] + str(file_hash(path))),
    }


def sciencehub_report() -> dict[str, Any]:
    script = REPO / "scripts" / "sciencehub_mcp.py"
    if not script.exists():
        return {"available": False}
    proc = subprocess.run(
        ["python", str(script), "--report"],
        cwd=str(REPO),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    metrics: dict[str, Any] = {"available": proc.returncode == 0, "returncode": proc.returncode}
    for line in proc.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        if value.isdigit():
            metrics[key] = int(value)
    if proc.stderr.strip():
        metrics["stderr_tail"] = proc.stderr[-1000:]
    return metrics


def build_catalog() -> dict[str, Any]:
    external = [
        repo_surface(
            "modelcontextprotocol_servers",
            MCP_EXTERNAL / "modelcontextprotocol-servers",
            "reference servers for filesystem, git, memory, sequential thinking, fetch, time, and protocol testing",
            95,
            "inactive snapshot only; enable individual servers with explicit allowlists and per-tool receipts",
        ),
        repo_surface(
            "modelcontextprotocol_registry",
            MCP_EXTERNAL / "modelcontextprotocol-registry",
            "official registry/API substrate for discovering published MCP servers",
            90,
            "use for catalog discovery only; do not auto-install registry results without security scoring",
        ),
        repo_surface(
            "github_mcp_server",
            MCP_EXTERNAL / "github-mcp-server",
            "GitHub issue, PR, repository, workflow, and code intelligence MCP surface",
            88,
            "prefer existing GitHub connector first; use this as pinned implementation/reference until auth and scope filters are explicit",
        ),
        repo_surface(
            "awesome_mcp_servers",
            MCP_EXTERNAL / "awesome-mcp-servers",
            "broad community discovery list for future MCP candidates",
            65,
            "discovery only; every candidate must be separately pinned and audited before use",
        ),
        repo_surface(
            "kobsidian",
            MCP_EXTERNAL / "kobsidian",
            "filesystem-first Obsidian/Markdown vault server for wiki notes, links, tags, tasks, and LLM-wiki operations",
            91,
            "read-only/wiki-index mode first; write tools disabled until vault path allowlist and TiddlyWiki/ENE receipts exist",
        ),
        repo_surface(
            "jupyter_mcp_server",
            MCP_EXTERNAL / "jupyter-mcp-server",
            "Jupyter notebook control surface for iterative Python/math prototyping with notebook context",
            89,
            "sandbox kernel only; no arbitrary host shell; every execution needs notebook path and output hash",
        ),
        repo_surface(
            "mcp_python_repl",
            MCP_EXTERNAL / "mcp-python-repl",
            "minimal Python REPL MCP surface for quick computation probes",
            83,
            "use only in sandboxed scratch directory with timeout and no network/secrets",
        ),
        repo_surface(
            "mcp_wolfram_alpha",
            MCP_EXTERNAL / "mcp-wolfram-alpha",
            "Wolfram Alpha query surface for external math/facts cross-checking",
            79,
            "requires API credential pointer; use for standard-equation cross-checks, not custom theorem promotion",
        ),
        repo_surface(
            "arxiv_mcp_server",
            MCP_EXTERNAL / "arxiv-mcp-server",
            "arXiv search/download surface with Semantic Scholar citation/reference traversal",
            92,
            "research retrieval only; downloaded papers need source hashes and citation receipts before curriculum use",
        ),
        repo_surface(
            "sci_hub_mcp_server",
            MCP_EXTERNAL / "sci-hub-mcp-server",
            "Sci-Hub-oriented academic paper MCP surface; useful only as a metadata/search-pattern reference",
            25,
            "HOLD: do not enable PDF download or paywall bypass. Use lawful/local sources first: ScienceHub, Zotero, arXiv, Semantic Scholar, publisher open access, or user-provided PDFs.",
        ),
    ]
    local = [
        local_surface(
            "sciencehub_mcp",
            REPO / "scripts" / "sciencehub_mcp.py",
            "sovereign research surface for local PDFs, Zotero, arXiv, paper review, and topic fetches",
            96,
            "safe as CLI smoke first; MCP mode requires dependency check and source/receipt outputs",
            sciencehub_report(),
        ),
        local_surface(
            "substack_connector_mcp",
            REPO / "plugins" / "substack-connector" / "scripts" / "substack_mcp_server.py",
            "MCP-style Substack publication/update surface",
            72,
            "requires local auth env and no secret echo; publish actions must be explicit",
        ),
        local_surface(
            "tardygrada_mcp",
            REPO / "2-Search-Space" / "tardygrada" / "README.md",
            "claim/proof-carrying language that compiles programs to MCP servers",
            82,
            "treat as proof/claim lab; run tests before exposing to shared bus",
        ),
        local_surface(
            "claw_mcp_tool_pool",
            REPO / "1-Distributed-Systems" / "agents" / "claw" / "src" / "tools.py",
            "local agent tool-pool mirror with MCP include/deny toggles",
            70,
            "use as compatibility/reference layer only; deny-prefix controls must remain available",
        ),
    ]
    selected = sorted(external + local, key=lambda item: item["priority"], reverse=True)
    return {
        "schema": "mcp_surface_catalog_receipt_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "MCP surfaces are cataloged as inactive adapters. They are not trusted or enabled until scoped auth, allowlists, sandboxing, and metaprobe receipts pass.",
        "external_snapshots": external,
        "local_surfaces": local,
        "selected_surfaces": selected,
        "bus_rules": [
            "Prefer local read-only or receipt-producing tools before write-capable tools.",
            "Run every MCP surface first in CLI/dry-run mode where possible.",
            "Require source path, source hash, tool name, arguments hash, output hash, lawful flag, and claim boundary in every bus receipt.",
            "Do not auto-install from registries or awesome lists; pin a commit and audit first.",
            "Never pass secrets through model-visible memory; store only credential-store pointers and receipt hashes.",
            "Do not use MCP retrieval surfaces to bypass copyright or access controls; route paper retrieval through lawful/local sources.",
        ],
        "openclaw_bridge": {
            "role": "OpenClaw can route MCP surfaces as bus adapters after loopback/sandbox/pairing receipts.",
            "first_candidates": ["sciencehub_mcp", "modelcontextprotocol_servers:git", "modelcontextprotocol_servers:memory", "github_mcp_server"],
            "research_candidates": ["arxiv_mcp_server", "jupyter_mcp_server", "kobsidian"],
            "hold_candidates": ["sci_hub_mcp_server"],
            "defer": ["filesystem write tools", "browser automation", "remote unauthenticated servers", "public inbound channels"],
        },
        "lawful": True,
    }


def curriculum_records(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are an MCP surface router. Return compact JSON and keep MCP tools behind receipt gates."
    records = []
    for item in catalog["selected_surfaces"]:
        prompt = {
            "task": "route_mcp_surface",
            "surface_id": item["id"],
            "kind": item["kind"],
            "role": item["role"],
            "priority": item["priority"],
            "gate": item["gate"],
            "claim_boundary": catalog["claim_boundary"],
        }
        answer = {
            "selected": item["priority"] >= 80,
            "use_as": "mcp_bus_surface_prior",
            "surface_id": item["id"],
            "source_path": item["path"],
            "source_hash": item.get("source_hash") or item.get("source_fingerprint"),
            "route_rule": item["gate"],
            "claim_boundary": catalog["claim_boundary"],
            "receipt_rule": "Use only after dry-run or scoped live receipt; never treat MCP output as trusted without source/output hashes.",
        }
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
                ]
            }
        )
    return records


def write_config(catalog: dict[str, Any], path: Path) -> None:
    config = {
        "$schema": "research_stack_mcp_surface_config_example_v1",
        "claim_boundary": catalog["claim_boundary"],
        "servers": {
            "sciencehub": {
                "command": "python",
                "args": ["scripts/sciencehub_mcp.py"],
                "mode": "stdio",
                "status": "candidate_cli_smoked",
            },
            "substack_connector": {
                "command": "python",
                "args": ["plugins/substack-connector/scripts/substack_mcp_server.py"],
                "mode": "stdio",
                "status": "candidate_requires_auth",
            },
            "mcp_reference_git": {
                "command": "uvx",
                "args": ["mcp-server-git", "--repository", str(REPO)],
                "mode": "stdio",
                "status": "candidate_not_enabled",
            },
            "mcp_reference_memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
                "mode": "stdio",
                "status": "candidate_not_enabled",
            },
            "kobsidian": {
                "command": "npx",
                "args": ["-y", "kobsidian"],
                "mode": "stdio",
                "status": "candidate_not_enabled_requires_vault_allowlist",
            },
            "jupyter_mcp": {
                "command": "python",
                "args": ["-m", "jupyter_mcp_server"],
                "mode": "stdio",
                "status": "candidate_not_enabled_requires_sandbox_kernel",
            },
            "python_repl": {
                "command": "python",
                "args": ["-m", "mcp_python"],
                "mode": "stdio",
                "status": "candidate_not_enabled_requires_sandbox",
            },
            "arxiv": {
                "command": "python",
                "args": ["-m", "arxiv_mcp_server"],
                "mode": "stdio",
                "status": "candidate_not_enabled_research_retrieval",
            },
            "wolfram_alpha": {
                "command": "python",
                "args": ["-m", "mcp_wolfram_alpha"],
                "mode": "stdio",
                "status": "candidate_not_enabled_requires_api_credential_pointer",
            },
            "sci_hub": {
                "command": "python",
                "args": ["sci_hub_server.py"],
                "mode": "stdio",
                "status": "hold_not_enabled_copyright_risk_metadata_reference_only",
            },
        },
        "required_receipt_fields": [
            "surface_id",
            "tool_name",
            "arguments_hash",
            "output_hash",
            "source_path",
            "lawful",
            "claim_boundary",
        ],
    }
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_wiki(catalog: dict[str, Any], path: Path) -> None:
    lines = [
        "created: 20260507000000000",
        "modified: 20260507000000000",
        "tags: ResearchStack MCP OpenClaw Metaprobe AgentBus",
        "title: MCP Surface Catalog",
        "type: text/vnd.tiddlywiki",
        "",
        "! MCP Surface Catalog",
        "",
        "This catalog pulls and inventories MCP surfaces that can help the OpenClaw/metaprobe shared bus.",
        "",
        "Durable source: `4-Infrastructure/shim/mcp_surface_catalog.py`",
        "",
        "Receipt: `4-Infrastructure/shim/mcp_surface_catalog_receipt.json`",
        "",
        "Curriculum: `4-Infrastructure/shim/mcp_surface_catalog_curriculum.jsonl`",
        "",
        "Config skeleton: `4-Infrastructure/shim/mcp_surface_config.example.json`",
        "",
        "!! Claim Boundary",
        "",
        catalog["claim_boundary"],
        "",
        "!! Selected Surfaces",
        "",
    ]
    for item in catalog["selected_surfaces"]:
        lines.append(f"* `{item['id']}` ({item['kind']}, priority {item['priority']}): {item['role']}. Gate: {item['gate']}")
    lines.extend(["", "!! Bus Rules", ""])
    for rule in catalog["bus_rules"]:
        lines.append(f"* {rule}")
    lines.extend(
        [
            "",
            "!! Links",
            "",
            "* [[OpenClaw Shared Bus Surface]]",
            "* [[Physics Math LLM Metaprobe Audit]]",
            "* [[Custom Equation Awareness Manifest]]",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=SHIM / "mcp_surface_catalog_receipt.json")
    parser.add_argument("--curriculum", type=Path, default=SHIM / "mcp_surface_catalog_curriculum.jsonl")
    parser.add_argument("--config", type=Path, default=SHIM / "mcp_surface_config.example.json")
    parser.add_argument("--wiki", type=Path, default=WIKI / "MCP Surface Catalog.tid")
    args = parser.parse_args()
    catalog = build_catalog()
    args.receipt.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(catalog):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_config(catalog, args.config)
    write_wiki(catalog, args.wiki)
    print(json.dumps(catalog, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
