#!/usr/bin/env python3
"""Sample kernel tracepoints and map them into QFox topology slots.

This is the debugger-side average collector. It temporarily enables a small
set of kernel tracepoints, counts observed events for a bounded duration, and
optionally writes slot summaries into /dev/qfox_topoman.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import select
import sys
import time
from pathlib import Path
from typing import Any

SCHEMA = "research_stack_qfox_topology_trace_sample_v1"
DEV = Path("/dev/qfox_topoman")

EVENT_TO_SLOT: dict[str, str] = {
    "sched:sched_switch": "sched",
    "sched:sched_wakeup": "sched",
    "kmem:mm_page_alloc": "mm",
    "kmem:mm_page_free": "mm",
    "syscalls:sys_enter_openat": "fs",
    "syscalls:sys_enter_openat2": "fs",
    "syscalls:sys_enter_read": "fs",
    "syscalls:sys_enter_write": "fs",
    "block:block_rq_issue": "block",
    "block:block_rq_complete": "block",
    "net:net_dev_queue": "net",
    "net:netif_receive_skb": "net",
    "power:cpu_idle": "power",
    "power:cpu_frequency": "power",
    "irq:irq_handler_entry": "device",
    "irq:softirq_entry": "device",
}


def tracefs_root() -> Path:
    for candidate in (Path("/sys/kernel/tracing"), Path("/sys/kernel/debug/tracing")):
        if candidate.exists():
            return candidate
    raise RuntimeError("tracefs is not mounted")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def event_path(root: Path, event: str) -> Path:
    system, name = event.split(":", 1)
    return root / "events" / system / name / "enable"


def available_events(root: Path) -> list[str]:
    available: list[str] = []
    for event in EVENT_TO_SLOT:
        if event_path(root, event).exists():
            available.append(event)
    return available


def parse_event_name(line: str) -> str | None:
    match = re.search(r"\s([A-Za-z0-9_]+):\s", line)
    if not match:
        return None
    name = match.group(1)
    for full in EVENT_TO_SLOT:
        if full.endswith(":" + name):
            return full
    return None


class TraceState:
    def __init__(self, root: Path, events: list[str]) -> None:
        self.root = root
        self.events = events
        self.tracing_on = read_text(root / "tracing_on")
        self.current_tracer = read_text(root / "current_tracer")
        self.enabled: dict[str, str] = {}

    def __enter__(self) -> "TraceState":
        write_text(self.root / "tracing_on", "0")
        for event in self.events:
            path = event_path(self.root, event)
            self.enabled[event] = read_text(path)
            write_text(path, "1")
        # Keep any current ftrace debugger choice; tracepoints are additive.
        try:
            write_text(self.root / "trace", "")
        except OSError:
            pass
        write_text(self.root / "tracing_on", "1")
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        write_text(self.root / "tracing_on", "0")
        for event, old in self.enabled.items():
            try:
                write_text(event_path(self.root, event), old or "0")
            except OSError:
                pass
        if self.current_tracer:
            try:
                write_text(self.root / "current_tracer", self.current_tracer)
            except OSError:
                pass
        if self.tracing_on:
            try:
                write_text(self.root / "tracing_on", self.tracing_on)
            except OSError:
                pass


def inject_summaries(slot_counts: dict[str, int], duration: float) -> None:
    if not DEV.exists():
        return
    for slot, count in sorted(slot_counts.items()):
        with DEV.open("w", encoding="utf-8", errors="replace") as handle:
            eps = count / duration if duration > 0 else 0.0
            handle.write(f"{slot} trace_sample count={count} eps={eps:.3f}\n")


def sample(duration: float, inject: bool) -> dict[str, Any]:
    root = tracefs_root()
    events = available_events(root)
    counts = {event: 0 for event in events}
    slot_counts: dict[str, int] = {}
    started = time.time()
    deadline = started + duration

    with TraceState(root, events):
        with (root / "trace_pipe").open("r", encoding="utf-8", errors="replace") as pipe:
            fd = pipe.fileno()
            while time.time() < deadline:
                timeout = max(0.0, min(0.25, deadline - time.time()))
                ready, _, _ = select.select([fd], [], [], timeout)
                if not ready:
                    continue
                line = pipe.readline()
                if not line:
                    continue
                event = parse_event_name(line)
                if not event:
                    continue
                counts[event] = counts.get(event, 0) + 1
                slot = EVENT_TO_SLOT.get(event, "user")
                slot_counts[slot] = slot_counts.get(slot, 0) + 1

    elapsed = max(time.time() - started, duration)
    if inject:
        inject_summaries(slot_counts, elapsed)

    return {
        "schema": SCHEMA,
        "timestamp_unix": int(time.time()),
        "duration_sec": elapsed,
        "tracefs": str(root),
        "events_enabled": events,
        "event_counts": counts,
        "slot_counts": slot_counts,
        "slot_rates_per_sec": {
            slot: count / elapsed for slot, count in sorted(slot_counts.items())
        },
        "injected_into_module": inject and DEV.exists(),
    }


def emit_text(payload: dict[str, Any]) -> str:
    lines = [
        f"schema: {payload['schema']}",
        f"duration_sec: {payload['duration_sec']:.3f}",
        f"tracefs: {payload['tracefs']}",
        f"enabled_events: {len(payload['events_enabled'])}",
        "slot_rates_per_sec:",
    ]
    for slot, rate in payload["slot_rates_per_sec"].items():
        lines.append(f"  {slot}: {rate:.3f}")
    lines.append("slot_counts:")
    for slot, count in sorted(payload["slot_counts"].items()):
        lines.append(f"  {slot}: {count}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--no-inject", action="store_true")
    args = parser.parse_args(argv)

    if args.duration <= 0:
        print("--duration must be positive", file=sys.stderr)
        return 2

    try:
        payload = sample(args.duration, inject=not args.no_inject)
    except (OSError, RuntimeError) as exc:
        print(f"trace sample failed: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        try:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"trace sample write failed: {exc}", file=sys.stderr)
            return 2

    print(rendered if args.json else emit_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
