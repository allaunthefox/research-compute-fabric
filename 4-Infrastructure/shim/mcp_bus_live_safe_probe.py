#!/usr/bin/env python3
"""First live-safe MCP bus probe.

Runs bounded, read-only ScienceHub CLI operations through the same receipt
discipline expected of future MCP/OpenClaw bus calls. This deliberately avoids
server activation, paper downloads, notebook execution, arbitrary Python REPL,
filesystem writes outside the receipt artifacts, and held surfaces.
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
SCIENCEHUB = REPO / "scripts" / "sciencehub_mcp.py"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_sciencehub(args: list[str], timeout: int) -> dict[str, Any]:
    command = ["python", str(SCIENCEHUB), *args]
    proc = subprocess.run(
        command,
        cwd=str(REPO),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    parsed: Any = None
    json_ok = False
    if args and args[0] == "--search":
        try:
            parsed = json.loads(proc.stdout)
            json_ok = True
        except Exception:
            parsed = None
    return {
        "surface_id": "sciencehub_mcp",
        "tool_name": "report" if args == ["--report"] else "search_local_corpus",
        "arguments": args,
        "arguments_hash": sha256_text(json.dumps(args, ensure_ascii=False)),
        "command_shape": ["python", "scripts/sciencehub_mcp.py", *args],
        "returncode": proc.returncode,
        "stdout_hash": sha256_text(proc.stdout),
        "stderr_hash": sha256_text(proc.stderr),
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-1000:],
        "json_ok": json_ok,
        "parsed_summary": summarize_search(parsed) if json_ok else summarize_report(proc.stdout),
        "lawful": proc.returncode == 0 and not proc.stderr.strip(),
        "claim_boundary": "Read-only local ScienceHub CLI call; no MCP server activation, paper download, notebook execution, or arbitrary code execution.",
    }


def summarize_report(text: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        if value.isdigit():
            metrics[key] = int(value)
    return metrics


def summarize_search(parsed: dict[str, Any] | None) -> dict[str, Any]:
    parsed = parsed or {}
    zotero = parsed.get("zotero", []) or []
    pdfs = parsed.get("pdfs", []) or []
    arxiv_meta = parsed.get("arxiv_meta", []) or []
    return {
        "zotero_hits": len(zotero),
        "pdf_hits": len(pdfs),
        "arxiv_meta_hits": len(arxiv_meta),
        "top_titles": [item.get("title") or item.get("title_guess") for item in [*zotero[:3], *pdfs[:3]] if item.get("title") or item.get("title_guess")],
    }


def build_receipt(queries: list[str], timeout: int) -> dict[str, Any]:
    calls = [run_sciencehub(["--report"], timeout)]
    for query in queries:
        calls.append(run_sciencehub(["--search", query], timeout))
    lawful_calls = sum(1 for call in calls if call["lawful"])
    hashed_calls = sum(1 for call in calls if call["arguments_hash"] and call["stdout_hash"])
    boundary_calls = sum(1 for call in calls if call["claim_boundary"])
    return {
        "schema": "mcp_bus_live_safe_probe_receipt_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "surface_id": "sciencehub_mcp",
        "source_path": str(SCIENCEHUB.relative_to(REPO)),
        "source_hash": file_hash(SCIENCEHUB),
        "claim_boundary": "First live-safe bus probe uses read-only ScienceHub CLI calls only; no live MCP server activation or restricted retrieval.",
        "queries": queries,
        "calls": calls,
        "call_count": len(calls),
        "lawful_calls": lawful_calls,
        "hashed_calls": hashed_calls,
        "boundary_calls": boundary_calls,
        "receipt_rule": "Every future live MCP call must include surface_id, tool_name, arguments_hash, stdout/output hash, source_path, lawful flag, and claim boundary.",
        "lawful": lawful_calls == len(calls) and hashed_calls == len(calls) and boundary_calls == len(calls),
    }


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a live-safe MCP bus router. Return compact JSON and preserve read-only boundaries."
    records = []
    for call in receipt["calls"]:
        prompt = {
            "task": "classify_live_safe_mcp_call",
            "surface_id": call["surface_id"],
            "tool_name": call["tool_name"],
            "arguments_hash": call["arguments_hash"],
            "parsed_summary": call["parsed_summary"],
            "claim_boundary": call["claim_boundary"],
        }
        answer = {
            "selected": bool(call["lawful"]),
            "use_as": "live_safe_mcp_bus_probe",
            "surface_id": call["surface_id"],
            "tool_name": call["tool_name"],
            "source_path": receipt["source_path"],
            "source_hash": receipt["source_hash"],
            "output_hash": call["stdout_hash"],
            "claim_boundary": call["claim_boundary"],
            "receipt_rule": receipt["receipt_rule"],
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
        "tags: ResearchStack MCP OpenClaw Metaprobe LiveSafe ScienceHub",
        "title: MCP Bus Live Safe Probe",
        "type: text/vnd.tiddlywiki",
        "",
        "! MCP Bus Live Safe Probe",
        "",
        "This tiddler records the first read-only live-safe bus calls through the ScienceHub surface.",
        "",
        "Durable source: `4-Infrastructure/shim/mcp_bus_live_safe_probe.py`",
        "",
        "Receipt: `4-Infrastructure/shim/mcp_bus_live_safe_probe_receipt.json`",
        "",
        "Curriculum: `4-Infrastructure/shim/mcp_bus_live_safe_probe_curriculum.jsonl`",
        "",
        "!! Result",
        "",
        f"* Calls: {receipt['lawful_calls']}/{receipt['call_count']} lawful",
        f"* Overall lawful: `{str(receipt['lawful']).lower()}`",
        "",
        "!! Claim Boundary",
        "",
        receipt["claim_boundary"],
        "",
        "!! Calls",
        "",
    ]
    for call in receipt["calls"]:
        status = "PASS" if call["lawful"] else "FAIL"
        lines.append(f"* {status} `{call['tool_name']}` args `{call['arguments']}` -> {call['parsed_summary']}")
    lines.extend(
        [
            "",
            "!! Links",
            "",
            "* [[MCP Bus Dry Run]]",
            "* [[MCP Surface Catalog]]",
            "* [[OpenClaw Shared Bus Surface]]",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", action="append", default=["compression", "erdos", "topology"])
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--receipt", type=Path, default=SHIM / "mcp_bus_live_safe_probe_receipt.json")
    parser.add_argument("--curriculum", type=Path, default=SHIM / "mcp_bus_live_safe_probe_curriculum.jsonl")
    parser.add_argument("--wiki", type=Path, default=WIKI / "MCP Bus Live Safe Probe.tid")
    args = parser.parse_args()

    receipt = build_receipt(args.query, args.timeout)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_wiki(receipt, args.wiki)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0 if receipt["lawful"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
