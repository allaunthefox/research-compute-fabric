#!/usr/bin/env python3
"""Build a parse-friendly manifest for local chat/session dump surfaces."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "6-Documentation" / "chat-log-dumps"
MANIFEST = OUT_DIR / "manifest.jsonl"
SUMMARY = OUT_DIR / "summary.md"

SOURCE_POOLS = [
    ROOT / "5-Applications" / "audit" / "exploit-audit" / "sessions",
    ROOT / "shared-data" / "data" / "germane" / "research",
    ROOT / "shared-data" / "data" / "ingested" / "chatgpt",
    ROOT / "shared-data" / "data" / "ingested" / "llm_research",
    ROOT / "6-Documentation" / "archive" / "sessions" / "chatgpt-logs",
]

SKIP_PARTS = {
    ".git",
    "node_modules",
    ".venv",
    "__pycache__",
}

LANE_TERMS = {
    "materials": [
        "material",
        "graphene",
        "nanoscroll",
        "gecko",
        "percolation",
        "efuse",
        "ferrite",
        "magnetic",
        "supercritical",
        "metamaterial",
    ],
    "hardware": [
        "fpga",
        "gpu",
        "hdmi",
        "tmds",
        "usb",
        "ecp5",
        "tang",
        "warden",
        "waveprobe",
        "sdr",
    ],
    "compression": [
        "hutter",
        "compression",
        "codec",
        "pist",
        "shifter",
        "engram",
        "codon",
        "soliton",
        "burgers",
    ],
    "semantic_graph": [
        "semantic",
        "eigenvector",
        "gestalt",
        "graphml",
        "search",
        "famm",
        "mass number",
        "semanticmass",
    ],
    "ene": [
        "ene",
        "substrate",
        "concept_anchor",
        "meta-autotype",
        "fractal hash",
        "golden spiral",
        "gray-code",
    ],
    "governance": [
        "notion",
        "linear",
        "wiki",
        "claim",
        "hold",
        "quarantine",
        "receipt",
        "proof",
    ],
}


def sha256_prefix(path: Path, limit: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        h.update(fh.read(limit))
    return h.hexdigest()


def sample_text(path: Path, limit: int = 256 * 1024) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit].lower()
    except OSError:
        return ""


def classify(path: Path, text: str) -> list[str]:
    haystack = f"{path.name.lower()} {text}"
    lanes = []
    for lane, terms in LANE_TERMS.items():
        if any(term in haystack for term in terms):
            lanes.append(lane)
    return lanes


def iter_sources() -> list[Path]:
    files: list[Path] = []
    for pool in SOURCE_POOLS:
        if not pool.exists():
            continue
        for path in pool.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            files.append(path)
    return sorted(set(files))


def main() -> None:
    rows = []
    ext_counter: Counter[str] = Counter()
    lane_counter: Counter[str] = Counter()
    pool_counter: Counter[str] = Counter()

    for path in iter_sources():
        rel = path.relative_to(ROOT)
        stat = path.stat()
        ext = path.suffix.lower().lstrip(".") or "no_ext"
        text = sample_text(path)
        lanes = classify(path, text)
        for lane in lanes:
            lane_counter[lane] += 1
        ext_counter[ext] += 1

        pool_name = next(
            (str(pool.relative_to(ROOT)) for pool in SOURCE_POOLS if path.is_relative_to(pool)),
            "unknown",
        )
        pool_counter[pool_name] += 1

        rows.append(
            {
                "path": str(rel),
                "bytes": stat.st_size,
                "extension": ext,
                "mtime_unix": int(stat.st_mtime),
                "sha256_first_mib": sha256_prefix(path),
                "lanes": lanes,
                "pool": pool_name,
            }
        )

    with MANIFEST.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    total_bytes = sum(row["bytes"] for row in rows)
    summary_lines = [
        "# Chat Log Dump Manifest Summary",
        "",
        f"- Files indexed: {len(rows)}",
        f"- Total bytes indexed: {total_bytes}",
        f"- Manifest: `manifest.jsonl`",
        "",
        "## By Source Pool",
        "",
    ]
    for key, count in pool_counter.most_common():
        summary_lines.append(f"- `{key}`: {count}")

    summary_lines.extend(["", "## By Extension", ""])
    for key, count in ext_counter.most_common():
        summary_lines.append(f"- `{key}`: {count}")

    summary_lines.extend(["", "## By Lane", ""])
    for key, count in lane_counter.most_common():
        summary_lines.append(f"- `{key}`: {count}")

    summary_lines.extend(["", "## Largest Files", ""])
    for row in sorted(rows, key=lambda item: item["bytes"], reverse=True)[:25]:
        summary_lines.append(
            f"- `{row['path']}` ({row['bytes']} bytes; lanes: {', '.join(row['lanes']) or 'unclassified'})"
        )

    SUMMARY.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
