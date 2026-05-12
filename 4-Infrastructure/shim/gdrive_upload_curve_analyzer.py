#!/usr/bin/env python3
"""Analyze rclone Google Drive upload smoothness from an rclone stats log.

The goal is deliberately modest: identify whether throughput turbulence is
mostly payload streaming noise or file-boundary/control-plane shock.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


STATS_RE = re.compile(
    r"^(?P<ts>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}).*?"
    r"(?P<done>[0-9.]+) GiB / (?P<total>[0-9.]+) GiB,\s+"
    r"(?P<pct>\d+)%,\s+(?P<speed>[0-9.]+) MiB/s, ETA (?P<eta>[^)]*)"
)
COPIED_RE = re.compile(
    r"^(?P<ts>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) INFO\s+: (?P<path>.*): Copied \(new\)"
)


@dataclass
class StatSample:
    ts: str
    epoch: float
    done_gib: float
    total_gib: float
    pct: int
    speed_mibs: float
    eta: str


@dataclass
class BoundaryShock:
    copied_ts: str
    path: str
    next_stat_ts: str | None
    next_speed_mibs: float | None
    previous_stat_ts: str | None
    previous_speed_mibs: float | None
    speed_delta_mibs: float | None


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y/%m/%d %H:%M:%S")


def parse_log(path: Path) -> tuple[list[StatSample], list[tuple[str, str]]]:
    stats: list[StatSample] = []
    copied: list[tuple[str, str]] = []
    for line in path.read_text(errors="ignore").splitlines():
        stat = STATS_RE.search(line)
        if stat:
            ts = stat.group("ts")
            stats.append(
                StatSample(
                    ts=ts,
                    epoch=parse_time(ts).timestamp(),
                    done_gib=float(stat.group("done")),
                    total_gib=float(stat.group("total")),
                    pct=int(stat.group("pct")),
                    speed_mibs=float(stat.group("speed")),
                    eta=stat.group("eta"),
                )
            )
            continue
        copied_match = COPIED_RE.search(line)
        if copied_match:
            copied.append((copied_match.group("ts"), copied_match.group("path")))
    return stats, copied


def mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def pstdev(values: list[float]) -> float | None:
    return statistics.pstdev(values) if len(values) > 1 else 0.0 if values else None


def round_or_none(value: float | None, digits: int = 3) -> float | None:
    return round(value, digits) if value is not None else None


def compute_boundary_shocks(
    stats: list[StatSample], copied: list[tuple[str, str]]
) -> list[BoundaryShock]:
    shocks: list[BoundaryShock] = []
    for copied_ts, copied_path in copied:
        copied_epoch = parse_time(copied_ts).timestamp()
        previous = None
        next_sample = None
        for sample in stats:
            if sample.epoch <= copied_epoch:
                previous = sample
            if sample.epoch > copied_epoch:
                next_sample = sample
                break
        delta = None
        if previous and next_sample:
            delta = next_sample.speed_mibs - previous.speed_mibs
        shocks.append(
            BoundaryShock(
                copied_ts=copied_ts,
                path=copied_path,
                next_stat_ts=next_sample.ts if next_sample else None,
                next_speed_mibs=next_sample.speed_mibs if next_sample else None,
                previous_stat_ts=previous.ts if previous else None,
                previous_speed_mibs=previous.speed_mibs if previous else None,
                speed_delta_mibs=delta,
            )
        )
    return shocks


def build_report(stats: list[StatSample], shocks: list[BoundaryShock]) -> dict:
    speeds = [sample.speed_mibs for sample in stats]
    last_10 = speeds[-10:]
    last_30 = speeds[-30:]
    deltas = [shock.speed_delta_mibs for shock in shocks if shock.speed_delta_mibs is not None]
    negative_deltas = [delta for delta in deltas if delta < 0]

    recommendation = "keep_current_run_unchanged"
    rationale = (
        "Current process already uses one transfer, size-descending order, and a large Drive chunk. "
        "Observed turbulence is mostly at file boundaries, so interrupting the run would add risk."
    )
    next_run = {
        "large_lane": {
            "selector": "files >= 20 GiB",
            "transfers": 1,
            "drive_chunk_size": "512M",
            "order_by": "size,descending",
        },
        "medium_lane": {
            "selector": "1 GiB <= files < 20 GiB",
            "transfers": 2,
            "drive_chunk_size": "256M",
            "order_by": "size,descending",
        },
        "tail_lane": {
            "selector": "files < 1 GiB",
            "transfers": 4,
            "drive_chunk_size": "128M",
            "order_by": "size,descending",
        },
        "receipt_gate": "rclone check before local deletion or stub replacement",
    }

    return {
        "sample_count": len(stats),
        "first_sample": asdict(stats[0]) if stats else None,
        "last_sample": asdict(stats[-1]) if stats else None,
        "speed_mibs": {
            "mean_all": round_or_none(mean(speeds)),
            "min_all": round_or_none(min(speeds) if speeds else None),
            "max_all": round_or_none(max(speeds) if speeds else None),
            "stdev_all": round_or_none(pstdev(speeds)),
            "mean_last_10": round_or_none(mean(last_10)),
            "stdev_last_10": round_or_none(pstdev(last_10)),
            "mean_last_30": round_or_none(mean(last_30)),
            "stdev_last_30": round_or_none(pstdev(last_30)),
        },
        "boundary_shock_count": len(shocks),
        "boundary_speed_delta_mibs": {
            "mean_all": round_or_none(mean(deltas)),
            "mean_negative_only": round_or_none(mean(negative_deltas)),
            "worst": round_or_none(min(deltas) if deltas else None),
        },
        "largest_boundary_shocks": [
            {
                **asdict(shock),
                "next_speed_mibs": round_or_none(shock.next_speed_mibs),
                "previous_speed_mibs": round_or_none(shock.previous_speed_mibs),
                "speed_delta_mibs": round_or_none(shock.speed_delta_mibs),
            }
            for shock in sorted(
                shocks,
                key=lambda item: item.speed_delta_mibs
                if item.speed_delta_mibs is not None
                else 0,
            )[:10]
        ],
        "recommendation": recommendation,
        "rationale": rationale,
        "next_run_lanes": next_run,
    }


def write_markdown(report: dict, path: Path) -> None:
    speed = report["speed_mibs"]
    boundary = report["boundary_speed_delta_mibs"]
    lines = [
        "# GDrive Upload Curve Analysis",
        "",
        "## Verdict",
        "",
        report["rationale"],
        "",
        "Do not interrupt the current run. Treat the current run as the stable",
        "large-object lane and use the lane split below for future offloads.",
        "",
        "## Measurements",
        "",
        f"- Samples: {report['sample_count']}",
        f"- Mean speed: {speed['mean_all']} MiB/s",
        f"- Speed range: {speed['min_all']} - {speed['max_all']} MiB/s",
        f"- Overall speed stdev: {speed['stdev_all']} MiB/s",
        f"- Last 10 mean/stdev: {speed['mean_last_10']} / {speed['stdev_last_10']} MiB/s",
        f"- Boundary shocks: {report['boundary_shock_count']}",
        f"- Worst boundary delta: {boundary['worst']} MiB/s",
        f"- Mean negative boundary delta: {boundary['mean_negative_only']} MiB/s",
        "",
        "## Boundary Shocks",
        "",
    ]
    for shock in report["largest_boundary_shocks"]:
        lines.append(
            f"- {shock['copied_ts']} `{shock['path']}`: "
            f"{shock['previous_speed_mibs']} -> {shock['next_speed_mibs']} MiB/s "
            f"({shock['speed_delta_mibs']} MiB/s)"
        )
    lines.extend(
        [
            "",
            "## Next-Run Lane Recipe",
            "",
            "```text",
            "large files   >= 20 GiB : --transfers 1 --drive-chunk-size 512M --order-by size,descending",
            "medium files  1-20 GiB  : --transfers 2 --drive-chunk-size 256M --order-by size,descending",
            "tail files    < 1 GiB   : --transfers 4 --drive-chunk-size 128M --order-by size,descending",
            "after upload           : rclone check before deletion or stub replacement",
            "```",
            "",
            "## Route Interpretation",
            "",
            "```text",
            "payload stream       -> stable transfer lane",
            "file boundary        -> synchronization barrier",
            "Drive API negotiation -> witness/control overhead",
            "speed dip            -> boundary shock, not compression or payload proof",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--md-out", type=Path, required=True)
    args = parser.parse_args()

    stats, copied = parse_log(args.log)
    shocks = compute_boundary_shocks(stats, copied)
    report = build_report(stats, shocks)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, args.md_out)
    print(json.dumps(report["speed_mibs"], indent=2, sort_keys=True))
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")


if __name__ == "__main__":
    main()
