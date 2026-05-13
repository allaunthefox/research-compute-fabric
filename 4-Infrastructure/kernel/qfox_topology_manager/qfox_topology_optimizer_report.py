#!/usr/bin/env python3
"""Derive optimization targets from QFox topology-manager samples.

This is intentionally advisory. It ranks topology slots by observed tracepoint
rate and emits receipt-shaped recommendations; it does not tune the machine.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

SCHEMA = "research_stack_qfox_topology_optimizer_report_v1"
SAMPLE_SCHEMA = "research_stack_qfox_topology_trace_sample_v1"
DEFAULT_SAMPLE_DIR = Path("/var/lib/qfox-topology-manager/samples")
DEFAULT_REPORT_DIR = Path("/var/lib/qfox-topology-manager/reports")
DEV = Path("/dev/qfox_topoman")

SLOT_GUIDANCE: dict[str, dict[str, Any]] = {
    "sched": {
        "label": "scheduler and wakeup churn",
        "optimize_for": [
            "reduce unnecessary wakeups",
            "identify noisy user services or timers",
            "keep latency tuning only where workloads prove it",
        ],
        "next_probes": [
            "sudo perf sched record -- sleep 10 && sudo perf sched latency",
            "systemd-analyze blame",
            "sudo cat /proc/schedstat | head -40",
        ],
    },
    "mm": {
        "label": "memory allocation churn",
        "optimize_for": [
            "reduce allocation/free storms",
            "watch zram and cache pressure",
            "separate build/indexer memory churn from desktop baseline",
        ],
        "next_probes": [
            "free -h",
            "cat /proc/pressure/memory",
            "grep -E 'pgscan|pgsteal|allocstall' /proc/vmstat",
        ],
    },
    "power": {
        "label": "idle and frequency transition churn",
        "optimize_for": [
            "lower timer noise before chasing power states",
            "balance desktop responsiveness against idle churn",
            "inspect services that prevent deep idle",
        ],
        "next_probes": [
            "cat /proc/pressure/cpu",
            "cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference 2>/dev/null",
            "sudo turbostat --Summary --quiet --interval 5 --num_iterations 2",
        ],
    },
    "device": {
        "label": "IRQ, softirq, and device interrupt pressure",
        "optimize_for": [
            "find high-rate IRQ sources",
            "check NIC/GPU/USB interrupt behavior",
            "only pin or rebalance IRQs after source attribution",
        ],
        "next_probes": [
            "cat /proc/interrupts | sort -k2,2nr | head -30",
            "cat /proc/softirqs",
            "systemctl is-active irqbalance || true",
        ],
    },
    "block": {
        "label": "block IO pressure",
        "optimize_for": [
            "separate local NVMe IO from remote/FUSE churn",
            "inspect Btrfs writeback and build-cache traffic",
            "keep scheduler changes scoped to measured IO latency",
        ],
        "next_probes": [
            "iostat -xz 1 5",
            "cat /proc/pressure/io",
            "findmnt -T /home/allaun/Documents/Research\\ Stack",
        ],
    },
    "net": {
        "label": "network packet and queue churn",
        "optimize_for": [
            "identify chatty local tunnels or sync clients",
            "separate loopback/tailscale/rclone traffic",
            "avoid NIC tuning until packet source is known",
        ],
        "next_probes": [
            "ip -s link",
            "ss -tunap | head -80",
            "nstat -az | head -80",
        ],
    },
    "fs": {
        "label": "filesystem syscall churn",
        "optimize_for": [
            "reduce watcher and indexer scans",
            "separate IDE activity from build/test activity",
            "prefer path-specific receipts over broad recursive scans",
        ],
        "next_probes": [
            "sudo fatrace -c -t 10",
            "inotifywatch -r -t 10 /home/allaun/Documents/Research\\ Stack",
        ],
    },
    "gpu": {
        "label": "GPU/display carrier activity",
        "optimize_for": [
            "watch compositor and driver event churn",
            "separate KDE/display stalls from compute load",
        ],
        "next_probes": [
            "nvidia-smi dmon -s pucvmt -c 5",
            "journalctl -b -p warning | grep -Ei 'nvidia|kwin|drm' | tail -80",
        ],
    },
    "security": {
        "label": "admission and policy-surface activity",
        "optimize_for": [
            "treat denials as evidence, not noise",
            "avoid broad policy changes without an event receipt",
        ],
        "next_probes": [
            "journalctl -b -p warning | grep -Ei 'audit|apparmor|permission|denied' | tail -80",
        ],
    },
}


def sample_paths(sample_dir: Path) -> list[Path]:
    summaries = sorted(sample_dir.glob("trace-sample-*.summary.json"))
    if summaries:
        return summaries
    return sorted(
        path
        for path in sample_dir.glob("trace-sample-*.json")
        if not path.name.endswith(".summary.json")
    )


def load_sample(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("schema") != SAMPLE_SCHEMA:
        return None
    payload["_path"] = str(path)
    return payload


def aggregate(samples: list[dict[str, Any]]) -> dict[str, Any]:
    total_duration = 0.0
    slot_counts: dict[str, int] = {}
    slot_rates_by_sample: dict[str, list[float]] = {}
    event_counts: dict[str, int] = {}

    for sample in samples:
        duration = float(sample.get("duration_sec") or 0.0)
        total_duration += max(0.0, duration)
        for slot, count in (sample.get("slot_counts") or {}).items():
            slot_counts[slot] = slot_counts.get(slot, 0) + int(count)
        for slot, rate in (sample.get("slot_rates_per_sec") or {}).items():
            slot_rates_by_sample.setdefault(slot, []).append(float(rate))
        for event, count in (sample.get("event_counts") or {}).items():
            event_counts[event] = event_counts.get(event, 0) + int(count)

    slot_rates = {
        slot: (count / total_duration if total_duration > 0 else 0.0)
        for slot, count in slot_counts.items()
    }
    total_events = sum(slot_counts.values())
    slot_shares = {
        slot: (count / total_events if total_events else 0.0)
        for slot, count in slot_counts.items()
    }
    slot_rate_stats = {
        slot: {
            "samples": len(rates),
            "mean": statistics.fmean(rates),
            "max": max(rates),
            "min": min(rates),
        }
        for slot, rates in slot_rates_by_sample.items()
        if rates
    }
    return {
        "sample_count": len(samples),
        "sample_paths": [sample["_path"] for sample in samples],
        "duration_sec": total_duration,
        "slot_counts": dict(sorted(slot_counts.items())),
        "slot_rates_per_sec": dict(
            sorted(slot_rates.items(), key=lambda item: item[1], reverse=True)
        ),
        "slot_shares": dict(
            sorted(slot_shares.items(), key=lambda item: item[1], reverse=True)
        ),
        "slot_rate_stats": slot_rate_stats,
        "event_counts": dict(
            sorted(event_counts.items(), key=lambda item: item[1], reverse=True)
        ),
    }


def severity(rate: float, share: float) -> str:
    if share >= 0.35 or rate >= 50000:
        return "primary"
    if share >= 0.10 or rate >= 5000:
        return "secondary"
    if rate > 0:
        return "watch"
    return "quiet"


def build_recommendations(agg: dict[str, Any], top_n: int) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    rates = agg["slot_rates_per_sec"]
    shares = agg["slot_shares"]
    for rank, (slot, rate) in enumerate(rates.items(), start=1):
        share = shares.get(slot, 0.0)
        guide = SLOT_GUIDANCE.get(slot, {})
        recommendations.append(
            {
                "rank": rank,
                "slot": slot,
                "label": guide.get("label", f"{slot} activity"),
                "severity": severity(rate, share),
                "rate_per_sec": rate,
                "share": share,
                "optimize_for": guide.get(
                    "optimize_for",
                    ["collect more receipts before tuning this slot"],
                ),
                "next_probes": guide.get("next_probes", []),
            }
        )
    return recommendations[:top_n]


def build_report(samples: list[dict[str, Any]], top_n: int) -> dict[str, Any]:
    agg = aggregate(samples)
    recs = build_recommendations(agg, top_n)
    primary = [rec for rec in recs if rec["severity"] == "primary"]
    secondary = [rec for rec in recs if rec["severity"] == "secondary"]
    return {
        "schema": SCHEMA,
        "timestamp_unix": int(time.time()),
        "aggregate": agg,
        "primary_targets": primary,
        "secondary_targets": secondary,
        "ranked_targets": recs,
        "interpretation": interpret(recs),
        "guardrails": [
            "recommendations are receipt-derived and advisory",
            "do not apply tuning automatically from this report",
            "optimize after source attribution, not only slot rate",
            "keep the Linux module passive; GCL/Lean remains the policy layer",
        ],
    }


def interpret(recs: list[dict[str, Any]]) -> str:
    if not recs:
        return "No samples were available; collect trace samples before tuning."
    primary = [rec["slot"] for rec in recs if rec["severity"] == "primary"]
    if primary:
        return "Optimize first for " + ", ".join(primary) + "."
    return "No primary hot slot yet; keep collecting baseline samples."


def emit_text(report: dict[str, Any]) -> str:
    lines = [
        f"schema: {report['schema']}",
        f"samples: {report['aggregate']['sample_count']}",
        f"duration_sec: {report['aggregate']['duration_sec']:.3f}",
        f"interpretation: {report['interpretation']}",
        "",
        "ranked_targets:",
    ]
    for rec in report["ranked_targets"]:
        lines.append(
            f"  {rec['rank']}. {rec['slot']} "
            f"({rec['severity']}): {rec['rate_per_sec']:.3f}/sec, "
            f"share={rec['share']:.3%} - {rec['label']}"
        )
        for item in rec["optimize_for"][:3]:
            lines.append(f"     optimize_for: {item}")
    lines.append("")
    lines.append("next_probes:")
    seen: set[str] = set()
    for rec in report["ranked_targets"][:3]:
        for probe in rec["next_probes"][:2]:
            if probe in seen:
                continue
            seen.add(probe)
            lines.append(f"  - {probe}")
    return "\n".join(lines) + "\n"


def inject_report(report: dict[str, Any], out: Path | None) -> bool:
    if not DEV.exists():
        return False
    targets = ",".join(rec["slot"] for rec in report["ranked_targets"][:3])
    payload = f"receipt optimize_report top={targets}"
    if out:
        payload += f" path={out}"
    try:
        with DEV.open("w", encoding="utf-8", errors="replace") as handle:
            handle.write(payload + "\n")
    except OSError as exc:
        print(f"optimizer report injection skipped: {exc}", file=sys.stderr)
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-dir", type=Path, default=DEFAULT_SAMPLE_DIR)
    parser.add_argument("--sample", type=Path, action="append", default=[])
    parser.add_argument("--top", type=int, default=6)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--inject", action="store_true")
    args = parser.parse_args(argv)

    paths = args.sample or sample_paths(args.samples_dir)
    samples = [sample for path in paths if (sample := load_sample(path)) is not None]
    report = build_report(samples, max(1, args.top))
    report["injected_into_module"] = False
    if args.inject:
        report["injected_into_module"] = inject_report(report, args.out)

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    out_path = args.out
    if out_path:
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"optimizer report write failed: {exc}", file=sys.stderr)
            return 2
    print(rendered if args.json else emit_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
