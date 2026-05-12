#!/usr/bin/env python3
"""Inventory Blockchair dump directory listings as transfer receipts."""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DATA_DIR = REPO / "shared-data/data/blockchain_corpus"


SIZE_RE = re.compile(r">\s*(?P<date>\d{2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2})\s+(?P<size>[0-9.]+[KMGTP]?|[0-9]+)\s*<")


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for key, value in attrs:
            if key == "href" and value:
                self.links.append(value)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_size(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    unit = value[-1]
    if unit.isdigit():
        return int(value)
    scale = {
        "K": 1024,
        "M": 1024**2,
        "G": 1024**3,
        "T": 1024**4,
        "P": 1024**5,
    }.get(unit)
    if scale is None:
        return None
    return int(float(value[:-1]) * scale)


def fetch_text(url: str, timeout: int) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "ResearchStackBlockchairInventory/0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def line_for_href(html: str, href: str) -> str:
    for line in html.splitlines():
        if f'href="{href}"' in line:
            return line
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chain", required=True)
    parser.add_argument("--table", default="blocks")
    parser.add_argument("--base-url", default="https://gz.blockchair.com")
    parser.add_argument("--max-objects", type=int, default=100)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    directory_url = f"{args.base_url.rstrip('/')}/{args.chain}/{args.table}/"
    html = fetch_text(directory_url, args.timeout)
    links = LinkParser()
    links.feed(html)
    objects = []
    for href in links.links:
        if href.startswith("../") or href.endswith("/") or not href.endswith(".tsv.gz"):
            continue
        if len(objects) >= args.max_objects:
            break
        line = line_for_href(html, href)
        size = None
        date_text = None
        match = SIZE_RE.search(line)
        if match:
            date_text = match.group("date")
            size = parse_size(match.group("size"))
        objects.append(
            {
                "key": f"{args.chain}/{args.table}/{href}",
                "url": urllib.parse.urljoin(directory_url, href),
                "last_modified_text": date_text,
                "size": size,
                "etag": None,
                "source": "blockchair_dumps",
            }
        )

    total_known_size = sum(item["size"] or 0 for item in objects)
    receipt = {
        "schema": "blockchair_dump_inventory_v0",
        "created_utc": now_iso(),
        "claim_boundary": "Blockchair dump directory inventory only. This proves listed dump links and parsed sizes where available; it does not prove full chain coverage or decoded TSV semantics.",
        "dataset": "blockchair_dumps",
        "chain": args.chain,
        "table": args.table,
        "directory_url": directory_url,
        "max_objects": args.max_objects,
        "object_count": len(objects),
        "total_listed_bytes_known": total_known_size,
        "objects": objects,
        "decision": "ADMIT_BLOCKCHAIR_DUMP_INVENTORY" if objects else "HOLD_EMPTY_BLOCKCHAIR_DUMP_INVENTORY",
    }
    receipt["inventory_hash"] = sha256_text(stable_json({k: v for k, v in receipt.items() if k != "inventory_hash"}))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if objects else 1


if __name__ == "__main__":
    sys.exit(main())
