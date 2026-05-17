#!/usr/bin/env python3
"""Receipt for the Notion/Linear -> Obsidian connector gap-fill pass.

This is connector-mining evidence only. Notion and Linear can identify missing
local chart anchors, but they do not promote mathematical or compression claims.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "notion_linear_obsidian_gap_fill"
RECEIPT = OUT_DIR / "notion_linear_obsidian_gap_fill_receipt.json"
SUMMARY = OUT_DIR / "notion_linear_obsidian_gap_fill_receipt.md"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


NOTION_SOURCES = [
    {
        "id": "35b375cc-7bfc-815b-9c28-c0c8a7fcdfaa",
        "title": "Research Stack Compression Atlas Update - LadderLUT, HexLogogram, Manifold Boundary",
        "url": "https://www.notion.so/35b375cc7bfc815b9c28c0c8a7fcdfaa",
        "local_status": "TRACKER_CONTEXT_HOLD",
        "gap_filled": "Compression atlas anchors were absent from the Obsidian Notion/Linear chart.",
    },
    {
        "id": "350375cc-7bfc-8179-a100-d639c59ade37",
        "title": "S3C / PIST Bridge Ingest Brief",
        "url": "https://www.notion.so/350375cc7bfc8179a100d639c59ade37",
        "local_status": "ENE_BACKLINK_CONTEXT",
        "gap_filled": "S3C/PIST ENE rowids and Linear backlink were absent from the Obsidian bridge chart.",
    },
    {
        "id": "353375cc-7bfc-81f7-8b7c-db285abd2840",
        "title": "Mass-Number GCL Subset",
        "url": "https://www.notion.so/353375cc7bfc81f78b7cdb285abd2840",
        "local_status": "WORKBENCH_PROJECTION_HOLD",
        "gap_filled": "Mass-Number GCL validator and closure doctrine needed a local Obsidian pointer.",
    },
    {
        "id": "353375cc-7bfc-8184-8522-ea812f867b73",
        "title": "Research Wiki Hub",
        "url": "https://www.notion.so/353375cc7bfc81848522ea812f867b73",
        "local_status": "WIKI_HUB_CONTEXT",
        "gap_filled": "Research Wiki Hub entry policy was not represented in the local Notion/Linear chart.",
    },
]

LINEAR_SOURCES = [
    {
        "id": "RES-2317",
        "title": "Ingest ChatGPT S3C/PIST bridge session into ENE surfaces",
        "url": "https://linear.app/research-stack/issue/RES-2317/ingest-chatgpt-s3cpist-bridge-session-into-ene-surfaces",
        "status": "Backlog",
        "local_status": "ENE_BACKLINK_CONTEXT",
    },
    {
        "id": "RES-2348",
        "title": "Run Mass-Number Corpus Pass for Notion and Linear",
        "url": "https://linear.app/research-stack/issue/RES-2348/run-mass-number-corpus-pass-for-notion-and-linear",
        "status": "Backlog",
        "local_status": "URGENT_AUDIT_HOLD",
    },
    {
        "id": "RES-2379",
        "title": "Implement detectors/codecs for LadderLUT, HexLogogram Atlas, and Manifold Boundary Atlas",
        "url": "https://linear.app/research-stack/issue/RES-2379/implement-detectorscodecs-for-ladderlut-hexlogogram-atlas-and-manifold",
        "status": "Backlog",
        "local_status": "IMPLEMENTATION_QUEUE_HOLD",
    },
    {
        "id": "document:dfc94418-0b5a-4ac0-bf98-c87ba898603c",
        "title": "Research Stack - Dual Graph Shape (Knowledge <-> Execution)",
        "url": "https://linear.app/research-stack/document/research-stack-dual-graph-shape-knowledge-execution-e33ad16bbd3a",
        "status": "Document",
        "local_status": "GRAPH_CONTEXT",
    },
    {
        "id": "project:a6db6541-2750-4290-84b6-e890bb3f4501",
        "title": "Research Stack",
        "url": "https://linear.app/research-stack/project/research-stack-7cd2d4ba318f",
        "status": "Backlog",
        "local_status": "PROJECT_CONTEXT",
    },
]

OBSIDIAN_TARGETS = [
    "/home/allaun/obsidian-vault/Research Stack/Notion and Linear.md",
    "/home/allaun/obsidian-vault/Research Stack/Connector Gap Fill 2026-05-09.md",
    rel(REPO / "6-Documentation" / "wiki" / "ObsidianConnector" / "Notion and Linear.md"),
    rel(REPO / "6-Documentation" / "wiki" / "ObsidianConnector" / "Connector Gap Fill 2026-05-09.md"),
    rel(REPO / "6-Documentation" / "wiki" / "Obsidian-connector" / "Notion and Linear.md"),
    rel(REPO / "6-Documentation" / "wiki" / "Obsidian-connector" / "Connector Gap Fill 2026-05-09.md"),
]

GAPS = [
    {
        "gap": "compression_atlas_missing_from_obsidian",
        "action": "ADD_TRACKER_CONTEXT",
        "status": "FILLED_AS_HOLD_POINTER",
    },
    {
        "gap": "mass_number_corpus_audit_missing_from_obsidian",
        "action": "ADD_AUDIT_POINTER",
        "status": "FILLED_AS_TAINTED_UNREWEIGHTED_BOUNDARY",
    },
    {
        "gap": "dual_graph_shape_missing_from_obsidian",
        "action": "ADD_GRAPH_CONTEXT",
        "status": "FILLED_AS_CONNECTOR_TOPOLOGY",
    },
    {
        "gap": "s3c_pist_ingest_backlink_thin",
        "action": "ADD_ENE_LINEAR_NOTION_BRIDGE_POINTER",
        "status": "FILLED_AS_BACKLINK_CONTEXT",
    },
]


def build_receipt() -> dict[str, Any]:
    receipt = {
        "schema": "notion_linear_obsidian_gap_fill_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "included_in_receipt_hash": ["notion_sources", "linear_sources", "obsidian_targets", "gaps", "decision"],
        "clock_participates_in_hash": False,
        "source_surfaces": ["notion", "linear"],
        "sink_surface": "obsidian",
        "notion_sources": NOTION_SOURCES,
        "linear_sources": LINEAR_SOURCES,
        "obsidian_targets": OBSIDIAN_TARGETS,
        "gaps": GAPS,
        "decision": "PROMOTE_TRACKER_CONTEXT_TO_OBSIDIAN_HOLD_BOUNDARY",
        "claim_boundary": (
            "Connector mining only. Notion and Linear identify tracker, publication, "
            "and operationalization gaps; they do not replace ENE records, local "
            "source files, Lean builds, corpus receipts, or byte-accounting evidence."
        ),
    }
    receipt["receipt_hash"] = sha256_text(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}})
    )
    return receipt


def write_summary(receipt: dict[str, Any]) -> None:
    lines = [
        "# Notion/Linear Obsidian Gap Fill Receipt",
        "",
        f"Decision: `{receipt['decision']}`",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Clock participates in hash: `{receipt['clock_participates_in_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Gaps",
        "",
        "| Gap | Action | Status |",
        "|---|---|---|",
    ]
    for gap in receipt["gaps"]:
        lines.append(f"| {gap['gap']} | {gap['action']} | {gap['status']} |")
    lines.extend(["", "## Linear Sources", "", "| ID | Status | Local status |", "|---|---|---|"])
    for source in receipt["linear_sources"]:
        lines.append(f"| {source['id']} | {source['status']} | {source['local_status']} |")
    lines.extend(["", "## Notion Sources", "", "| ID | Local status |", "|---|---|"])
    for source in receipt["notion_sources"]:
        lines.append(f"| {source['id']} | {source['local_status']} |")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = build_receipt()
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(receipt)
    print(json.dumps({"receipt": rel(RECEIPT), "summary": rel(SUMMARY), "receipt_hash": receipt["receipt_hash"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
