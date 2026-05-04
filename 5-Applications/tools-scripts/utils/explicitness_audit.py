#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""explicitness_audit.py — lightweight codebase explicitness inventory.

Purpose:
- surface files that still carry "implicit"/"TODO"/"not yet implemented" style markers
- report whether key markdown docs declare basic metadata
- give the repo a repeatable first pass instead of relying on memory

This is intentionally modest: it inventories and flags. It does not pretend to
fully understand every file's semantics.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List


DEFAULT_ROOTS = ("docs", "scripts", "hutter", "tests")

MARKER_PATTERNS = {
    "todo": re.compile(r"\bTODO\b|not yet implemented", re.IGNORECASE),
    "fixme": re.compile(r"\bFIXME\b", re.IGNORECASE),
    "tbd": re.compile(r"\bTBD\b", re.IGNORECASE),
    "implicit": re.compile(r"\bimplicit(?:ly)?\b", re.IGNORECASE),
    "speculative": re.compile(r"\bspeculative\b", re.IGNORECASE),
    "premature": re.compile(r"\bpremature(?:ly)?\b", re.IGNORECASE),
}


@dataclass
class MarkerFinding:
    path: str
    line: int
    marker: str
    text: str


@dataclass
class DocMetadata:
    path: str
    has_status: bool
    has_date: bool
    has_related_surfaces: bool


def iter_files(root: Path, roots: Iterable[str]) -> Iterable[Path]:
    for sub in roots:
        base = root / sub
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                yield path


def scan_markers(path: Path) -> List[MarkerFinding]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    findings: List[MarkerFinding] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        for marker, pattern in MARKER_PATTERNS.items():
            if pattern.search(line):
                findings.append(
                    MarkerFinding(
                        path=str(path),
                        line=idx,
                        marker=marker,
                        text=line.strip(),
                    )
                )
    return findings


def inspect_doc_metadata(path: Path) -> DocMetadata:
    text = path.read_text(encoding="utf-8")
    return DocMetadata(
        path=str(path),
        has_status="**Status:**" in text,
        has_date="**Date:**" in text or "**Date filed:**" in text,
        has_related_surfaces="**Related surfaces:**" in text,
    )


def collect_audit(root: Path, roots: Iterable[str] = DEFAULT_ROOTS) -> dict:
    marker_findings: List[MarkerFinding] = []
    docs_metadata: List[DocMetadata] = []

    for path in iter_files(root, roots):
        marker_findings.extend(scan_markers(path))
        rel = path.relative_to(root)
        if rel.suffix.lower() == ".md" and rel.parts and rel.parts[0] == "docs":
            docs_metadata.append(inspect_doc_metadata(path))

    marker_counts: dict[str, int] = {}
    for finding in marker_findings:
        marker_counts[finding.marker] = marker_counts.get(finding.marker, 0) + 1

    docs_missing_status = [d.path for d in docs_metadata if not d.has_status]
    docs_missing_date = [d.path for d in docs_metadata if not d.has_date]
    docs_missing_related = [d.path for d in docs_metadata if not d.has_related_surfaces]

    return {
        "roots": list(roots),
        "files_scanned": sum(1 for _ in iter_files(root, roots)),
        "marker_counts": marker_counts,
        "marker_findings": [asdict(f) for f in marker_findings],
        "docs_scanned": len(docs_metadata),
        "docs_missing_status": docs_missing_status,
        "docs_missing_date": docs_missing_date,
        "docs_missing_related_surfaces": docs_missing_related,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory explicitness markers and doc metadata.")
    parser.add_argument(
        "--root",
        default=".",
        help="Repo root to scan (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable summary.",
    )
    args = parser.parse_args()

    audit = collect_audit(Path(args.root))

    if args.json:
        print(json.dumps(audit, indent=2))
        return

    print("Explicitness audit")
    print("==================")
    print(f"files_scanned: {audit['files_scanned']}")
    print(f"docs_scanned:  {audit['docs_scanned']}")
    print("\nMarker counts:")
    for marker, count in sorted(audit["marker_counts"].items()):
        print(f"  {marker:12s} {count}")
    print(f"\nDocs missing Status:           {len(audit['docs_missing_status'])}")
    print(f"Docs missing Date:             {len(audit['docs_missing_date'])}")
    print(f"Docs missing Related surfaces: {len(audit['docs_missing_related_surfaces'])}")


if __name__ == "__main__":
    main()
