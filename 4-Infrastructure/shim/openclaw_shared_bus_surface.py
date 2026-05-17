#!/usr/bin/env python3
"""Create a receipt-bound OpenClaw shared-bus surface descriptor.

OpenClaw is pulled as an external snapshot and treated as a control-plane/bus
candidate. This script does not start a gateway, install dependencies, or enable
inbound channels. It records the pinned source, maps the bus surfaces into the
Research Stack, and emits curriculum records for bounded LLM routing.
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
DEFAULT_OPENCLAW = REPO / "5-Applications" / "tools-scripts" / "external" / "openclaw"
SHIM = REPO / "4-Infrastructure" / "shim"
WIKI = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"


def run_git(path: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(path), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path: Path, limit: int = 12000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def load_package(path: Path) -> dict[str, Any]:
    package_path = path / "package.json"
    if not package_path.exists():
        return {}
    data = json.loads(package_path.read_text(encoding="utf-8"))
    return {
        "name": data.get("name"),
        "version": data.get("version"),
        "description": data.get("description"),
        "license": data.get("license"),
        "runtime_hint": "Node 24 recommended or Node 22.16+ per README",
        "script_keys": sorted((data.get("scripts") or {}).keys())[:80],
    }


def evidence_snippets(path: Path) -> list[dict[str, str]]:
    snippets = []
    for rel, marker in [
        ("README.md", "OpenClaw is a personal AI assistant you run on your own devices."),
        ("README.md", "Gateway is just the control plane."),
        ("README.md", "Multi-agent routing"),
        ("README.md", "Default: tools run on the host"),
        ("docs/index.md", "Gateway is the single source of truth for sessions, routing, and channel connections."),
        ("docs/network.md", "Loopback first"),
    ]:
        text = read_text(path / rel)
        lower = text.lower()
        idx = lower.find(marker.lower())
        if idx < 0:
            continue
        start = max(0, idx - 180)
        end = min(len(text), idx + len(marker) + 280)
        snippets.append(
            {
                "source_path": str((path / rel).relative_to(REPO)),
                "marker": marker,
                "snippet_hash": sha256_text(text[start:end]),
            }
        )
    return snippets


def build_surface(path: Path) -> dict[str, Any]:
    commit = run_git(path, "rev-parse", "HEAD")
    branch = run_git(path, "rev-parse", "--abbrev-ref", "HEAD")
    remote = run_git(path, "remote", "get-url", "origin")
    status = run_git(path, "status", "--short")
    package = load_package(path)
    readme = read_text(path / "README.md")
    docs_index = read_text(path / "docs" / "index.md")
    network_doc = read_text(path / "docs" / "network.md")
    source_fingerprint = sha256_text("\n".join([commit, package.get("version") or "", readme[:4000], docs_index[:4000], network_doc[:4000]]))
    return {
        "schema": "openclaw_shared_bus_surface_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "openclaw": {
            "path": str(path.relative_to(REPO)),
            "remote": remote,
            "branch": branch,
            "commit": commit,
            "working_tree_clean": status == "",
            "package": package,
            "source_fingerprint": source_fingerprint,
            "evidence": evidence_snippets(path),
        },
        "surface_role": {
            "name": "OpenClaw Shared Bus Surface",
            "use_as": "local_first_agent_gateway_and_event_bus_candidate",
            "not_use_as": [
                "theorem_truth_source",
                "unbounded_tool_executor",
                "raw_secret_memory_store",
                "open_inbound_channel_without_pairing",
            ],
            "claim_boundary": "OpenClaw is treated as a bus/control-plane candidate. It is not run or trusted until loopback, pairing, sandbox, and metaprobe receipt gates pass.",
        },
        "research_stack_mapping": [
            {
                "openclaw_surface": "Gateway",
                "research_stack_role": "shared bus/control plane",
                "gate": "loopback-only first; no non-loopback bind without explicit auth and pairing receipt",
            },
            {
                "openclaw_surface": "sessions/routing",
                "research_stack_role": "bounded worker lanes for AgentID/shared identity tasks",
                "gate": "one task receipt per lane before memory write",
            },
            {
                "openclaw_surface": "channels/plugins",
                "research_stack_role": "transport adapters for chat/API/hardware event ingress",
                "gate": "disable public inbound channels until allowlist and sandbox receipts exist",
            },
            {
                "openclaw_surface": "skills",
                "research_stack_role": "local tool contract layer for metaprobe/verifier actions",
                "gate": "skill outputs must include source path, hash, lawful flag, and claim boundary",
            },
            {
                "openclaw_surface": "sandboxing",
                "research_stack_role": "containment membrane for non-main and remote sessions",
                "gate": "non-main sessions default to sandboxed/receipt-only writes",
            },
        ],
        "event_contract": {
            "task_started": {
                "required": ["agent_handle", "task_id", "title", "state", "timestamp"],
            },
            "task_completed": {
                "required": ["agent_handle", "task_id", "receipt_path", "receipt_hash", "lawful", "claim_boundary"],
            },
            "memory_write": {
                "required": ["key", "value_hash", "source_receipt_path", "claim_boundary"],
                "rule": "write only hashes, receipt paths, lawful statuses, and next-action pointers; never raw secrets",
            },
        },
        "activation_plan": [
            "Keep external snapshot pinned and inactive.",
            "Generate loopback-only OpenClaw config skeleton.",
            "Route one local metaprobe verifier task through a dry-run event adapter.",
            "Only after receipt pass, test gateway loopback with no public channels.",
            "Promote to shared bus surface only after sandbox and pairing receipts exist.",
        ],
        "lawful": True,
    }


def curriculum_records(surface: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are an OpenClaw bus-surface router. Return compact JSON and keep OpenClaw behind receipt gates."
    records = []
    for item in surface["research_stack_mapping"]:
        prompt = {
            "task": "route_openclaw_surface",
            "openclaw_surface": item["openclaw_surface"],
            "research_stack_role": item["research_stack_role"],
            "gate": item["gate"],
            "claim_boundary": surface["surface_role"]["claim_boundary"],
        }
        answer = {
            "selected": True,
            "use_as": "shared_bus_surface_prior",
            "openclaw_surface": item["openclaw_surface"],
            "route_rule": item["gate"],
            "claim_boundary": surface["surface_role"]["claim_boundary"],
            "source_path": surface["openclaw"]["path"],
            "source_hash": surface["openclaw"]["source_fingerprint"],
            "receipt_rule": "Treat as bus/control-plane prior only until live loopback and sandbox receipts exist.",
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


def write_config_template(surface: dict[str, Any], path: Path) -> None:
    config = {
        "$schema": "research_stack_openclaw_shared_bus_config_example_v1",
        "claim_boundary": "Template only. Do not place secrets here. Keep real credentials under OpenClaw's local credential store.",
        "gateway": {
            "bind": "127.0.0.1",
            "port": 18789,
            "non_loopback": "disabled_until_auth_pairing_receipt",
        },
        "agents": {
            "defaults": {
                "sandbox": {
                    "mode": "non-main",
                    "required_for": ["remote", "group", "public_channel", "untrusted_input"],
                }
            }
        },
        "research_stack_bus": {
            "memory_write_rule": surface["event_contract"]["memory_write"]["rule"],
            "required_task_completion_keys": surface["event_contract"]["task_completed"]["required"],
            "allowed_memory_value_types": ["receipt_path", "hash", "lawful_status", "claim_boundary", "next_action_pointer"],
        },
    }
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_wiki(surface: dict[str, Any], path: Path) -> None:
    lines = [
        "created: 20260507000000000",
        "modified: 20260507000000000",
        "tags: ResearchStack OpenClaw AgentBus Metaprobe IPC",
        "title: OpenClaw Shared Bus Surface",
        "type: text/vnd.tiddlywiki",
        "",
        "! OpenClaw Shared Bus Surface",
        "",
        "OpenClaw is pulled as a pinned external snapshot and treated as a local-first shared bus/control-plane candidate.",
        "",
        f"Snapshot path: `{surface['openclaw']['path']}`",
        f"Commit: `{surface['openclaw']['commit']}`",
        f"Package version: `{surface['openclaw']['package'].get('version')}`",
        "",
        "Durable source: `4-Infrastructure/shim/openclaw_shared_bus_surface.py`",
        "",
        "Receipt: `4-Infrastructure/shim/openclaw_shared_bus_surface_receipt.json`",
        "",
        "Curriculum: `4-Infrastructure/shim/openclaw_shared_bus_surface_curriculum.jsonl`",
        "",
        "Config skeleton: `4-Infrastructure/shim/openclaw_shared_bus_config.example.json`",
        "",
        "!! Claim Boundary",
        "",
        surface["surface_role"]["claim_boundary"],
        "",
        "!! Surface Mapping",
        "",
    ]
    for item in surface["research_stack_mapping"]:
        lines.append(f"* `{item['openclaw_surface']}` -> {item['research_stack_role']}. Gate: {item['gate']}")
    lines.extend(
        [
            "",
            "!! Activation Plan",
            "",
        ]
    )
    for step in surface["activation_plan"]:
        lines.append(f"* {step}")
    lines.extend(
        [
            "",
            "!! Links",
            "",
            "* [[Physics Math LLM Metaprobe Audit]]",
            "* [[Solved Problem Output Verifier]]",
            "* [[Custom Equation Awareness Manifest]]",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openclaw", type=Path, default=DEFAULT_OPENCLAW)
    parser.add_argument("--receipt", type=Path, default=SHIM / "openclaw_shared_bus_surface_receipt.json")
    parser.add_argument("--curriculum", type=Path, default=SHIM / "openclaw_shared_bus_surface_curriculum.jsonl")
    parser.add_argument("--config-template", type=Path, default=SHIM / "openclaw_shared_bus_config.example.json")
    parser.add_argument("--wiki", type=Path, default=WIKI / "OpenClaw Shared Bus Surface.tid")
    args = parser.parse_args()

    surface = build_surface(args.openclaw)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(surface, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(surface):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_config_template(surface, args.config_template)
    write_wiki(surface, args.wiki)
    print(json.dumps(surface, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
