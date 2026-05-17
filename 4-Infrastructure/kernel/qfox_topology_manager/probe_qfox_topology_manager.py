#!/usr/bin/env python3
"""Probe the QFox topology-manager kernel module.

The probe is receipt-shaped and intentionally non-failing for missing module
state: absence is data. CLI/write errors still exit non-zero.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SCHEMA = "research_stack_qfox_topology_manager_probe_v1"
SYSFS = Path("/sys/kernel/qfox_topology_manager")
DEBUGFS = Path("/sys/kernel/debug/qfox_topology_manager")
DEV = Path("/dev/qfox_topoman")


def _parse_kv(text: str | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if not text:
        return values
    for raw in text.splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def _read(path: Path, max_bytes: int = 65536) -> str | None:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(max_bytes)
    except OSError:
        return None


def _cmd(argv: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc), "stdout": "", "stderr": ""}
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _snapshot() -> dict[str, Any]:
    status = _read(SYSFS / "status")
    slots = _read(SYSFS / "slots")
    status_kv = _parse_kv(status)
    slots_kv = _parse_kv(slots)
    events = _parse_int(status_kv.get("events"))
    avg_x1000 = _parse_int(status_kv.get("avg_events_per_sec_x1000"))
    return {
        "timestamp_unix": time.time(),
        "status": status,
        "status_kv": status_kv,
        "slots": slots,
        "slots_kv": slots_kv,
        "events": events,
        "avg_events_per_sec": None if avg_x1000 is None else avg_x1000 / 1000.0,
    }


def build_probe(sample_sec: float = 0.0) -> dict[str, Any]:
    loaded = "qfox_topology_manager" in (_read(Path("/proc/modules")) or "")
    first = _snapshot()
    sample: dict[str, Any] | None = None
    if sample_sec > 0:
        time.sleep(sample_sec)
        second = _snapshot()
        first_events = first.get("events")
        second_events = second.get("events")
        delta_events = None
        if isinstance(first_events, int) and isinstance(second_events, int):
            delta_events = max(0, second_events - first_events)
        sample = {
            "seconds": sample_sec,
            "start": first,
            "end": second,
            "delta_events": delta_events,
            "events_per_second": None
            if delta_events is None
            else delta_events / sample_sec,
        }
    return {
        "schema": SCHEMA,
        "timestamp_unix": int(time.time()),
        "module": {
            "name": "qfox_topology_manager",
            "loaded": loaded,
            "modinfo": _cmd(["modinfo", "qfox_topology_manager"]),
        },
        "interfaces": {
            "sysfs": str(SYSFS),
            "sysfs_present": SYSFS.exists(),
            "debugfs": str(DEBUGFS),
            "debugfs_present": DEBUGFS.exists(),
            "device": str(DEV),
            "device_present": DEV.exists(),
        },
        "status": first["status"],
        "status_kv": first["status_kv"],
        "slots": first["slots"],
        "slots_kv": first["slots_kv"],
        "mode": _read(SYSFS / "mode"),
        "events": _read(DEBUGFS / "events"),
        "average": {
            "since_load_events_per_second": first["avg_events_per_sec"],
            "sample": sample,
        },
    }


def emit_text(probe: dict[str, Any]) -> str:
    module = probe["module"]
    interfaces = probe["interfaces"]
    lines = [
        f"schema: {probe['schema']}",
        f"module: {module['name']}",
        f"loaded: {module['loaded']}",
        f"sysfs: {interfaces['sysfs_present']} ({interfaces['sysfs']})",
        f"debugfs: {interfaces['debugfs_present']} ({interfaces['debugfs']})",
        f"device: {interfaces['device_present']} ({interfaces['device']})",
    ]
    if probe.get("status"):
        lines.append("")
        lines.append("status:")
        lines.append(probe["status"].rstrip())
    if probe.get("slots"):
        lines.append("")
        lines.append("slots:")
        lines.append(probe["slots"].rstrip())
    average = probe.get("average") or {}
    if average.get("since_load_events_per_second") is not None:
        lines.append("")
        lines.append(
            "average_since_load_events_per_second: "
            f"{average['since_load_events_per_second']:.3f}"
        )
    sample = average.get("sample")
    if sample:
        lines.append(
            f"sample_{sample['seconds']:.3f}s_events_per_second: "
            f"{sample['events_per_second']:.3f}"
            if sample.get("events_per_second") is not None
            else f"sample_{sample['seconds']:.3f}s_events_per_second: unavailable"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--out", type=Path, help="write probe payload to path")
    parser.add_argument(
        "--sample-sec",
        type=float,
        default=0.0,
        help="sleep for N seconds and report an event-rate delta",
    )
    args = parser.parse_args(argv)

    if args.sample_sec < 0:
        print("--sample-sec must be non-negative", file=sys.stderr)
        return 2

    probe = build_probe(args.sample_sec)
    payload = json.dumps(probe, indent=2, sort_keys=True) + "\n"
    rendered = payload if args.json else emit_text(probe)

    if args.out:
        try:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(payload, encoding="utf-8")
        except OSError as exc:
            print(f"probe write failed: {exc}", file=sys.stderr)
            return 2

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
