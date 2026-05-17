#!/usr/bin/env python3
"""Detect a newly attached USB FPGA as a topological extension.

The probe records USB devices, serial nodes, and sysfs ancestry. It can compare
against a prior snapshot and identify new nodes without relying on kernel logs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


DEFAULT_OUT = Path("4-Infrastructure/shim/fpga_topological_extension_snapshot.json")


def run_text(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def list_usb() -> list[dict[str, str]]:
    rows = []
    for line in run_text(["lsusb"]).splitlines():
        parts = line.split()
        if len(parts) < 6:
            continue
        rows.append(
            {
                "bus": parts[1],
                "device": parts[3].rstrip(":"),
                "id": parts[5],
                "description": " ".join(parts[6:]),
                "raw": line,
            }
        )
    return rows


def readlink(path: Path) -> str:
    try:
        return os.readlink(path)
    except OSError:
        return ""


def serial_nodes() -> list[dict[str, str]]:
    nodes: dict[str, dict[str, str]] = {}
    for pattern in ("/dev/ttyUSB*", "/dev/ttyACM*"):
        for node in sorted(Path("/dev").glob(Path(pattern).name)):
            nodes[str(node)] = {
                "node": str(node),
                "by_id": "",
                "sysfs": "",
                "driver": "",
            }

    by_id = Path("/dev/serial/by-id")
    if by_id.exists():
        for link in sorted(by_id.iterdir()):
            target = (by_id / link.name).resolve()
            entry = nodes.setdefault(
                str(target),
                {"node": str(target), "by_id": "", "sysfs": "", "driver": ""},
            )
            entry["by_id"] = str(link)

    for entry in nodes.values():
        node_name = Path(entry["node"]).name
        sys_path = Path("/sys/class/tty") / node_name
        if sys_path.exists():
            entry["sysfs"] = str(sys_path.resolve())
            entry["driver"] = readlink(sys_path / "device" / "driver")

    return sorted(nodes.values(), key=lambda item: item["node"])


def snapshot() -> dict[str, Any]:
    payload = {
        "schema": "fpga_topological_extension_snapshot_v1",
        "timestamp_unix": time.time(),
        "usb": list_usb(),
        "serial": serial_nodes(),
    }
    digest_input = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload["sha256"] = hashlib.sha256(digest_input).hexdigest()
    return payload


def keyset(snapshot_payload: dict[str, Any], name: str) -> set[str]:
    if "snapshot" in snapshot_payload:
        snapshot_payload = snapshot_payload["snapshot"]
    if name == "usb":
        return {row.get("raw", "") for row in snapshot_payload.get("usb", [])}
    if name == "serial":
        return {row.get("node", "") + "|" + row.get("by_id", "") for row in snapshot_payload.get("serial", [])}
    return set()


def diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "fpga_topological_extension_diff_v1",
        "before_sha256": before.get("sha256", ""),
        "after_sha256": after.get("sha256", ""),
        "new_usb": sorted(keyset(after, "usb") - keyset(before, "usb")),
        "removed_usb": sorted(keyset(before, "usb") - keyset(after, "usb")),
        "new_serial": sorted(keyset(after, "serial") - keyset(before, "serial")),
        "removed_serial": sorted(keyset(before, "serial") - keyset(after, "serial")),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    before_raw = json.loads(args.before.read_text()) if args.before else None
    before = before_raw.get("snapshot", before_raw) if isinstance(before_raw, dict) else None
    start = time.time()
    current = snapshot()

    if args.watch and before is not None:
        while time.time() - start < args.timeout:
            current = snapshot()
            current_diff = diff(before, current)
            if current_diff["new_usb"] or current_diff["new_serial"]:
                break
            time.sleep(args.interval)

    result: dict[str, Any] = {"snapshot": current}
    if before is not None:
        result["diff"] = diff(before, current)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
