#!/usr/bin/env python3
"""Dry-run MCP bus candidates without enabling live MCP servers.

This is the first activation layer after the MCP catalog. It runs only safe
read/static checks and local CLI smokes, then emits receipts suitable for the
OpenClaw/metaprobe bus. It does not start long-lived servers, download papers,
run notebooks, execute arbitrary Python, or enable held surfaces.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
WIKI = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"
CATALOG = SHIM / "mcp_surface_catalog_receipt.json"


SAFE_STATIC_SURFACES = {
    "modelcontextprotocol_servers",
    "modelcontextprotocol_registry",
    "github_mcp_server",
    "kobsidian",
    "arxiv_mcp_server",
    "jupyter_mcp_server",
    "mcp_python_repl",
    "mcp_wolfram_alpha",
    "tardygrada_mcp",
    "substack_connector_mcp",
    "claw_mcp_tool_pool",
    "awesome_mcp_servers",
}

HELD_SURFACES = {"sci_hub_mcp_server"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_read(path: Path, limit: int = 20000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def file_hash(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return sha256_bytes(path.read_bytes())


def run_sciencehub_report(timeout: int) -> dict[str, Any]:
    script = REPO / "scripts" / "sciencehub_mcp.py"
    proc = subprocess.run(
        ["python", str(script), "--report"],
        cwd=str(REPO),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    metrics: dict[str, Any] = {}
    for line in proc.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        if value.isdigit():
            metrics[key] = int(value)
    return {
        "surface_id": "sciencehub_mcp",
        "mode": "cli_report",
        "command": "python scripts/sciencehub_mcp.py --report",
        "returncode": proc.returncode,
        "stdout_hash": sha256_text(proc.stdout),
        "stderr_hash": sha256_text(proc.stderr),
        "stdout_tail": proc.stdout[-2000:],
        "metrics": metrics,
        "lawful": proc.returncode == 0 and bool(metrics),
        "claim_boundary": "ScienceHub CLI report smoke only; no paper download or remote MCP activation.",
    }


def static_surface_check(surface: dict[str, Any]) -> dict[str, Any]:
    surface_id = surface["id"]
    rel_path = surface["path"]
    path = REPO / rel_path
    readme = path / "README.md" if path.is_dir() else path
    if not readme.exists() and path.is_dir():
        candidates = sorted(path.glob("README*"))
        readme = candidates[0] if candidates else readme
    readme_text = safe_read(readme)
    metadata_files = []
    if path.is_dir():
        for name in ("package.json", "pyproject.toml", "go.mod", "Cargo.toml", "requirements.txt"):
            candidate = path / name
            if candidate.exists():
                metadata_files.append(str(candidate.relative_to(REPO)))
    gate = surface.get("gate", "")
    hold = surface_id in HELD_SURFACES or "hold" in gate.lower()
    markers = {
        "has_readme": bool(readme_text),
        "has_gate": bool(gate),
        "has_source_reference": bool(surface.get("source_hash") or surface.get("source_fingerprint") or surface.get("commit")),
        "hold": hold,
    }
    lawful = markers["has_readme"] and markers["has_gate"] and markers["has_source_reference"]
    return {
        "surface_id": surface_id,
        "mode": "static_snapshot_check",
        "path": rel_path,
        "readme_path": str(readme.relative_to(REPO)) if readme.exists() else None,
        "readme_hash": file_hash(readme),
        "metadata_files": metadata_files,
        "markers": markers,
        "source_hash": surface.get("source_hash") or surface.get("source_fingerprint"),
        "commit": surface.get("commit"),
        "lawful": lawful,
        "activation": "held" if hold else "inactive_candidate",
        "claim_boundary": gate,
    }


def build_receipt(catalog_path: Path, timeout: int) -> dict[str, Any]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    surfaces = catalog.get("selected_surfaces", [])
    checks = []
    checks.append(run_sciencehub_report(timeout))
    for surface in surfaces:
        surface_id = surface["id"]
        if surface_id == "sciencehub_mcp":
            continue
        if surface_id in SAFE_STATIC_SURFACES or surface_id in HELD_SURFACES:
            checks.append(static_surface_check(surface))
    lawful_count = sum(1 for check in checks if check.get("lawful"))
    held_count = sum(1 for check in checks if check.get("activation") == "held")
    return {
        "schema": "mcp_bus_dry_run_receipt_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "catalog_path": str(catalog_path.relative_to(REPO)),
        "catalog_hash": file_hash(catalog_path),
        "claim_boundary": "Dry-run checks static MCP surface readiness and local safe smokes only; no live server activation, downloads, notebook execution, or arbitrary code execution.",
        "checks": checks,
        "check_count": len(checks),
        "lawful_count": lawful_count,
        "held_count": held_count,
        "bus_receipt_rule": "Every future live MCP call must include surface_id, tool_name, arguments_hash, output_hash, source_path, lawful flag, and claim boundary.",
        "lawful": lawful_count == len(checks) and len(checks) > 0,
    }


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are an MCP bus activation router. Return compact JSON and never activate tools without receipts."
    records = []
    for check in receipt["checks"]:
        prompt = {
            "task": "classify_mcp_bus_dry_run",
            "surface_id": check["surface_id"],
            "mode": check["mode"],
            "lawful": check["lawful"],
            "activation": check.get("activation", "dry_run_only"),
            "claim_boundary": check["claim_boundary"],
        }
        answer = {
            "selected": bool(check["lawful"]) and check.get("activation") != "held",
            "use_as": "mcp_bus_dry_run_receipt",
            "surface_id": check["surface_id"],
            "source_path": check.get("path") or "scripts/sciencehub_mcp.py",
            "source_hash": check.get("source_hash") or check.get("readme_hash") or check.get("stdout_hash"),
            "claim_boundary": check["claim_boundary"],
            "receipt_rule": receipt["bus_receipt_rule"],
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


def write_wiki(receipt: dict[str, Any], path: Path) -> None:
    lines = [
        "created: 20260507000000000",
        "modified: 20260507000000000",
        "tags: ResearchStack MCP OpenClaw Metaprobe DryRun",
        "title: MCP Bus Dry Run",
        "type: text/vnd.tiddlywiki",
        "",
        "! MCP Bus Dry Run",
        "",
        "This dry run checks MCP bus candidates without enabling live servers.",
        "",
        "Durable source: `4-Infrastructure/shim/mcp_bus_dry_run.py`",
        "",
        "Receipt: `4-Infrastructure/shim/mcp_bus_dry_run_receipt.json`",
        "",
        "Curriculum: `4-Infrastructure/shim/mcp_bus_dry_run_curriculum.jsonl`",
        "",
        "!! Result",
        "",
        f"* Checks: {receipt['lawful_count']}/{receipt['check_count']} lawful",
        f"* Held surfaces: {receipt['held_count']}",
        f"* Overall lawful: `{str(receipt['lawful']).lower()}`",
        "",
        "!! Claim Boundary",
        "",
        receipt["claim_boundary"],
        "",
        "!! Checks",
        "",
    ]
    for check in receipt["checks"]:
        status = "PASS" if check["lawful"] else "FAIL"
        activation = check.get("activation", check["mode"])
        lines.append(f"* {status} `{check['surface_id']}` ({activation}): {check['claim_boundary']}")
    lines.extend(
        [
            "",
            "!! Links",
            "",
            "* [[MCP Surface Catalog]]",
            "* [[OpenClaw Shared Bus Surface]]",
            "* [[Physics Math LLM Metaprobe Audit]]",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--receipt", type=Path, default=SHIM / "mcp_bus_dry_run_receipt.json")
    parser.add_argument("--curriculum", type=Path, default=SHIM / "mcp_bus_dry_run_curriculum.jsonl")
    parser.add_argument("--wiki", type=Path, default=WIKI / "MCP Bus Dry Run.tid")
    args = parser.parse_args()

    receipt = build_receipt(args.catalog, args.timeout)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_wiki(receipt, args.wiki)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0 if receipt["lawful"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
