#!/usr/bin/env python3
"""Rederive Waveprobe smoothing for rclone transfer paths.

This is not a transport replacement. It reads an rclone log and derives a
future-run lane schedule from the observed transfer signal:

  throughput samples -> signal
  file completions   -> boundary impulses
  file size          -> payload mass
  boundary shock     -> curvature / turbulence
  lane recipe        -> delay-shaped controller
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


STATS_RE = re.compile(
    r"^(?P<ts>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}).*?"
    r"(?P<done>[0-9.]+) GiB / (?P<total>[0-9.]+) GiB,\s+"
    r"(?P<pct>\d+)%,\s+(?P<speed>[0-9.]+) (?P<unit>[KMGT]iB)/s, ETA (?P<eta>[^)]*)"
)
COPIED_RE = re.compile(
    r"^(?P<ts>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) INFO\s+: (?P<path>.*): Copied \(new\)"
)


@dataclass
class TransferSample:
    ts: str
    epoch: float
    speed_mibs: float


@dataclass
class BoundaryEvent:
    ts: str
    path: str
    size_bytes: int | None
    size_mib: float | None
    previous_speed_mibs: float | None
    next_speed_mibs: float | None
    shock_mibs: float
    shock_ratio: float
    payload_mass: float
    boundary_density: float
    eigenvalue: float
    delay_weight: float
    lane: str


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y/%m/%d %H:%M:%S")


def speed_to_mibs(value: float, unit: str) -> float:
    scale = {
        "KiB": 1 / 1024,
        "MiB": 1,
        "GiB": 1024,
        "TiB": 1024 * 1024,
    }[unit]
    return value * scale


def parse_log(path: Path) -> tuple[list[TransferSample], list[tuple[str, str]]]:
    samples: list[TransferSample] = []
    copied: list[tuple[str, str]] = []
    for line in path.read_text(errors="ignore").splitlines():
        stat = STATS_RE.search(line)
        if stat:
            ts = stat.group("ts")
            samples.append(
                TransferSample(
                    ts=ts,
                    epoch=parse_time(ts).timestamp(),
                    speed_mibs=speed_to_mibs(float(stat.group("speed")), stat.group("unit")),
                )
            )
            continue
        copied_match = COPIED_RE.search(line)
        if copied_match:
            copied.append((copied_match.group("ts"), copied_match.group("path")))
    return samples, copied


def file_size(source_root: Path, rel_path: str) -> int | None:
    candidate = source_root / rel_path
    try:
        return candidate.stat().st_size
    except FileNotFoundError:
        return None


def lane_for_eigenvalue(eigenvalue: float, size_mib: float | None) -> str:
    if size_mib is not None and size_mib >= 20 * 1024:
        return "low_mode_large_stream"
    if eigenvalue < 0.08:
        return "low_mode_large_stream"
    if eigenvalue < 0.35:
        return "mid_mode_payload_stream"
    return "high_mode_tail_boundary"


def derive_events(
    samples: list[TransferSample],
    copied: list[tuple[str, str]],
    source_root: Path,
) -> list[BoundaryEvent]:
    events: list[BoundaryEvent] = []
    speeds = [sample.speed_mibs for sample in samples if sample.speed_mibs > 0]
    stream_speed = statistics.median(speeds) if speeds else 1.0

    for copied_ts, rel_path in copied:
        copied_epoch = parse_time(copied_ts).timestamp()
        previous = None
        next_sample = None
        for sample in samples:
            if sample.epoch <= copied_epoch:
                previous = sample
            if sample.epoch > copied_epoch:
                next_sample = sample
                break

        before = previous.speed_mibs if previous else None
        after = next_sample.speed_mibs if next_sample else None
        delta = (after - before) if before is not None and after is not None else 0.0
        shock = max(0.0, -delta)
        shock_ratio = shock / max(stream_speed, 0.001)

        size = file_size(source_root, rel_path)
        size_mib = size / (1024 * 1024) if size is not None else None
        payload_mass = math.log2(1.0 + (size_mib or 0.0))

        # Small files have high boundary density; large files behave as slow,
        # stable modes. Unknown sizes are treated conservatively as small.
        boundary_density = 1.0 / (1.0 + payload_mass)
        eigenvalue = boundary_density * (1.0 + shock_ratio)
        delay_weight = 1.0 / math.sqrt(max(eigenvalue, 1e-6))
        lane = lane_for_eigenvalue(eigenvalue, size_mib)

        events.append(
            BoundaryEvent(
                ts=copied_ts,
                path=rel_path,
                size_bytes=size,
                size_mib=round(size_mib, 3) if size_mib is not None else None,
                previous_speed_mibs=round(before, 3) if before is not None else None,
                next_speed_mibs=round(after, 3) if after is not None else None,
                shock_mibs=round(shock, 3),
                shock_ratio=round(shock_ratio, 6),
                payload_mass=round(payload_mass, 6),
                boundary_density=round(boundary_density, 6),
                eigenvalue=round(eigenvalue, 6),
                delay_weight=round(delay_weight, 6),
                lane=lane,
            )
        )
    return events


def summarize(events: list[BoundaryEvent], samples: list[TransferSample]) -> dict:
    lane_groups: dict[str, list[BoundaryEvent]] = {}
    for event in events:
        lane_groups.setdefault(event.lane, []).append(event)

    lane_summary = {}
    for lane, lane_events in lane_groups.items():
        eigenvalues = [event.eigenvalue for event in lane_events]
        shocks = [event.shock_mibs for event in lane_events]
        sizes = [event.size_mib for event in lane_events if event.size_mib is not None]
        lane_summary[lane] = {
            "event_count": len(lane_events),
            "mean_eigenvalue": round(statistics.mean(eigenvalues), 6),
            "max_eigenvalue": round(max(eigenvalues), 6),
            "mean_shock_mibs": round(statistics.mean(shocks), 3),
            "mean_size_mib": round(statistics.mean(sizes), 3) if sizes else None,
        }

    sorted_events = sorted(events, key=lambda event: event.eigenvalue, reverse=True)
    speeds = [sample.speed_mibs for sample in samples]

    return {
        "derivation": {
            "signal": "v(t) = rclone throughput samples",
            "boundary_impulse": "kappa_i = max(0, v_before - v_after) / median(v)",
            "payload_mass": "mu_i = log2(1 + size_i_mib)",
            "boundary_density": "beta_i = 1 / (1 + mu_i)",
            "transfer_eigenvalue": "lambda_i = beta_i * (1 + kappa_i)",
            "delay_weight": "tau_i = 1 / sqrt(lambda_i)",
        },
        "sample_count": len(samples),
        "boundary_event_count": len(events),
        "speed_mibs": {
            "median": round(statistics.median(speeds), 3) if speeds else None,
            "mean": round(statistics.mean(speeds), 3) if speeds else None,
            "last": round(speeds[-1], 3) if speeds else None,
        },
        "lane_summary": lane_summary,
        "highest_curvature_events": [asdict(event) for event in sorted_events[:20]],
        "recipe": {
            "low_mode_large_stream": {
                "rclone": "--transfers 1 --drive-chunk-size 512M --order-by size,descending",
                "reason": "preserve continuous payload flow; avoid cross-file turbulence",
            },
            "mid_mode_payload_stream": {
                "rclone": "--transfers 2 --drive-chunk-size 256M --order-by size,descending",
                "reason": "overlap moderate boundary barriers while keeping payload lanes fat",
            },
            "high_mode_tail_boundary": {
                "rclone": "--transfers 4 --drive-chunk-size 128M --order-by size,descending",
                "reason": "hide per-object Drive/API latency in the tiny-file tail",
            },
        },
    }


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Waveprobe Transfer Smoothing Rederivation",
        "",
        "## Core Law",
        "",
        "```text",
        "v(t)      = observed rclone throughput signal",
        "kappa_i  = max(0, v_before - v_after) / median(v)",
        "mu_i     = log2(1 + file_size_i_mib)",
        "beta_i   = 1 / (1 + mu_i)",
        "lambda_i = beta_i * (1 + kappa_i)",
        "tau_i    = 1 / sqrt(lambda_i)",
        "```",
        "",
        "Interpretation:",
        "",
        "- large files have high payload mass and low boundary density",
        "- tiny files have low payload mass and high boundary density",
        "- transfer smoothing is not one magic throughput curve",
        "- it is lane selection based on the eigenvalue of boundary turbulence",
        "",
        "## Observed Signal",
        "",
        f"- Samples: {report['sample_count']}",
        f"- Boundary events: {report['boundary_event_count']}",
        f"- Median speed: {report['speed_mibs']['median']} MiB/s",
        f"- Last speed: {report['speed_mibs']['last']} MiB/s",
        "",
        "## Lane Summary",
        "",
    ]
    for lane, summary in sorted(report["lane_summary"].items()):
        lines.append(f"### {lane}")
        lines.append("")
        lines.append(f"- Events: {summary['event_count']}")
        lines.append(f"- Mean eigenvalue: {summary['mean_eigenvalue']}")
        lines.append(f"- Max eigenvalue: {summary['max_eigenvalue']}")
        lines.append(f"- Mean shock: {summary['mean_shock_mibs']} MiB/s")
        lines.append(f"- Mean size: {summary['mean_size_mib']} MiB")
        lines.append(f"- Recipe: `{report['recipe'][lane]['rclone']}`")
        lines.append("")
    lines.extend(
        [
            "## Highest-Curvature Events",
            "",
        ]
    )
    for event in report["highest_curvature_events"][:10]:
        lines.append(
            f"- `{event['path']}` lambda={event['eigenvalue']} "
            f"shock={event['shock_mibs']} MiB/s size={event['size_mib']} MiB "
            f"lane={event['lane']}"
        )
    lines.extend(
        [
            "",
            "## Operational Claim Boundary",
            "",
            "This does not make Google Drive faster by itself. It derives a lane",
            "schedule for future runs. Active transfers should not be interrupted",
            "unless the scheduler is explicitly being tested on a disposable run.",
            "",
            "Receipt rule:",
            "",
            "```text",
            "copy -> rclone check -> receipt -> only then delete or stub local files",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--md-out", type=Path, required=True)
    args = parser.parse_args()

    samples, copied = parse_log(args.log)
    events = derive_events(samples, copied, args.source_root)
    report = summarize(events, samples)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, args.md_out)
    print(json.dumps(report["lane_summary"], indent=2, sort_keys=True))
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")


if __name__ == "__main__":
    main()
