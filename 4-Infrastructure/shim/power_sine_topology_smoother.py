#!/usr/bin/env python3
"""Read-only software power smoothing probe.

This script does not change CPU governors, GPU power limits, RAPL constraints,
fan curves, firmware settings, or wall power. It samples available telemetry and
turns the observed power waveform into a conservative workload-scheduling plan.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RAPL_ROOT = Path("/sys/devices/virtual/powercap/intel-rapl")
DEFAULT_ARTIFACT_DIR = Path(
    "/home/allaun/Documents/Research Stack/shared-data/artifacts/power_smoothing"
)


@dataclass
class RaplZone:
    name: str
    energy_path: Path
    max_energy_uj: int


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def discover_rapl_zones() -> list[RaplZone]:
    zones: list[RaplZone] = []
    if not RAPL_ROOT.exists():
        return zones

    for energy_path in sorted(RAPL_ROOT.glob("**/energy_uj")):
        zone_dir = energy_path.parent
        name_path = zone_dir / "name"
        max_path = zone_dir / "max_energy_range_uj"
        if not name_path.exists() or not max_path.exists():
            continue
        try:
            zones.append(
                RaplZone(
                    name=read_text(name_path),
                    energy_path=energy_path,
                    max_energy_uj=int(read_text(max_path)),
                )
            )
        except (OSError, ValueError):
            continue
    return zones


def read_rapl_energy(zones: list[RaplZone]) -> dict[str, int]:
    readings: dict[str, int] = {}
    for zone in zones:
        try:
            readings[zone.name] = int(read_text(zone.energy_path))
        except (OSError, ValueError):
            continue
    return readings


def delta_energy_uj(before: int, after: int, max_range: int) -> int:
    if after >= before:
        return after - before
    return (max_range - before) + after


def query_nvidia_gpu() -> list[dict[str, Any]]:
    cmd = [
        "nvidia-smi",
        "--query-gpu=index,name,power.draw,power.limit,temperature.gpu,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=3)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []

    rows: list[dict[str, Any]] = []
    for row in csv.reader(proc.stdout.splitlines()):
        if len(row) < 6:
            continue
        try:
            rows.append(
                {
                    "index": int(row[0].strip()),
                    "name": row[1].strip(),
                    "power_draw_w": float(row[2].strip()),
                    "power_limit_w": float(row[3].strip()),
                    "temperature_c": float(row[4].strip()),
                    "utilization_pct": float(row[5].strip()),
                }
            )
        except ValueError:
            continue
    return rows


def sample_power(duration_s: float, interval_s: float) -> tuple[list[dict[str, Any]], list[RaplZone]]:
    zones = discover_rapl_zones()
    samples: list[dict[str, Any]] = []
    previous_time = time.monotonic()
    previous_energy = read_rapl_energy(zones)
    deadline = previous_time + duration_s

    while time.monotonic() < deadline:
        time.sleep(interval_s)
        now = time.monotonic()
        elapsed = max(now - previous_time, 1e-9)
        current_energy = read_rapl_energy(zones)

        rapl_power: dict[str, float] = {}
        for zone in zones:
            if zone.name not in previous_energy or zone.name not in current_energy:
                continue
            delta = delta_energy_uj(
                previous_energy[zone.name],
                current_energy[zone.name],
                zone.max_energy_uj,
            )
            rapl_power[zone.name] = (delta / 1_000_000.0) / elapsed

        gpu = query_nvidia_gpu()
        total_gpu_power = sum(item["power_draw_w"] for item in gpu)
        total_cpu_power = sum(rapl_power.values())
        total_power = total_cpu_power + total_gpu_power

        samples.append(
            {
                "t_s": now,
                "dt_s": elapsed,
                "rapl_power_w": rapl_power,
                "gpu": gpu,
                "cpu_power_w": total_cpu_power,
                "gpu_power_w": total_gpu_power,
                "observed_power_w": total_power,
            }
        )
        previous_time = now
        previous_energy = current_energy

    return samples, zones


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * q)))
    return ordered[index]


def clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def geometric_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    product = 1.0
    for value in values:
        product *= max(value, 1e-9)
    return product ** (1.0 / len(values))


def unit_vector(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return [0.0 for _ in values]
    return [value / norm for value in values]


def build_homeostasis_vector(
    samples: list[dict[str, Any]],
    mean_power: float,
    p95_power: float,
    p95_slew: float,
    target_slew_w_per_s: float,
    normalized_curvature: float,
    power_budget_w: float,
    thermal_ceiling_c: float,
) -> dict[str, Any]:
    gpu_temps = [
        float(gpu["temperature_c"])
        for sample in samples
        for gpu in sample.get("gpu", [])
        if "temperature_c" in gpu
    ]
    gpu_limits = [
        float(gpu["power_limit_w"])
        for sample in samples
        for gpu in sample.get("gpu", [])
        if "power_limit_w" in gpu
    ]
    cpu_mean = statistics.fmean(float(s["cpu_power_w"]) for s in samples) if samples else 0.0
    gpu_mean = statistics.fmean(float(s["gpu_power_w"]) for s in samples) if samples else 0.0
    lane_total = cpu_mean + gpu_mean
    if lane_total <= 1e-9 or min(cpu_mean, gpu_mean) <= 0.1:
        lane_contention_slack = 1.0
    else:
        overlap_ratio = min(cpu_mean, gpu_mean) / max(cpu_mean, gpu_mean)
        load_ratio = lane_total / max(power_budget_w, 1.0)
        lane_contention_slack = 1.0 - overlap_ratio * load_ratio

    max_gpu_temp = max(gpu_temps) if gpu_temps else None
    thermal_headroom = (
        clamp01((thermal_ceiling_c - max_gpu_temp) / max(thermal_ceiling_c - 25.0, 1.0))
        if max_gpu_temp is not None
        else 1.0
    )
    gpu_limit_headroom = (
        clamp01(1.0 - (gpu_mean / max(statistics.fmean(gpu_limits), 1.0)))
        if gpu_limits
        else 1.0
    )

    components = {
        "power_headroom": clamp01(1.0 - p95_power / max(power_budget_w, 1.0)),
        "slew_margin": clamp01(1.0 - p95_slew / max(target_slew_w_per_s, 1.0)),
        "curvature_damping": 1.0 / (1.0 + max(normalized_curvature, 0.0)),
        "thermal_headroom": thermal_headroom,
        "gpu_limit_headroom": gpu_limit_headroom,
        "lane_contention_slack": clamp01(lane_contention_slack),
    }
    ordered_names = list(components)
    ordered_values = [components[name] for name in ordered_names]
    score = geometric_mean(ordered_values)
    state = "homeostatic"
    if score < 0.55:
        state = "unstable"
    elif score < 0.75:
        state = "watch"

    return {
        "basis": ordered_names,
        "components": components,
        "unit_vector": dict(zip(ordered_names, unit_vector(ordered_values))),
        "homeostasis_score": score,
        "state": state,
        "power_budget_w": power_budget_w,
        "thermal_ceiling_c": thermal_ceiling_c,
        "interpretation": (
            "A stable workload-topology eigenvector favors high headroom, low slew, "
            "low curvature, thermal margin, GPU limit margin, and low lane contention."
        ),
    }


def analyze_samples(
    samples: list[dict[str, Any]],
    target_slew_w_per_s: float,
    power_budget_w: float,
    thermal_ceiling_c: float,
) -> dict[str, Any]:
    power = [float(s["observed_power_w"]) for s in samples]
    cpu = [float(s["cpu_power_w"]) for s in samples]
    gpu = [float(s["gpu_power_w"]) for s in samples]
    slew: list[float] = []
    curvature: list[float] = []

    for a, b in zip(samples, samples[1:]):
        dt = max(float(b["t_s"]) - float(a["t_s"]), 1e-9)
        slew.append((float(b["observed_power_w"]) - float(a["observed_power_w"])) / dt)

    for i in range(1, len(power) - 1):
        dt = max(float(samples[i]["dt_s"]), 1e-9)
        curvature.append((power[i + 1] - 2 * power[i] + power[i - 1]) / (dt * dt))

    abs_slew = [abs(v) for v in slew]
    abs_curvature = [abs(v) for v in curvature]
    mean_power = statistics.fmean(power) if power else 0.0
    p95_slew = quantile(abs_slew, 0.95) or 0.0
    p95_curvature = quantile(abs_curvature, 0.95) or 0.0
    p95_power = quantile(power, 0.95) or 0.0
    slew_excess = max(0.0, p95_slew - target_slew_w_per_s)
    normalized_slew = slew_excess / max(target_slew_w_per_s, 1.0)
    normalized_curvature = p95_curvature / max(mean_power, 1.0)
    eigenvalue = normalized_slew + 0.25 * normalized_curvature
    delay_s = min(60.0, 2.0 * math.sqrt(max(eigenvalue, 0.0)))

    risk_class = "low"
    if eigenvalue >= 1.5:
        risk_class = "high"
    elif eigenvalue >= 0.5:
        risk_class = "medium"

    homeostasis_vector = build_homeostasis_vector(
        samples=samples,
        mean_power=mean_power,
        p95_power=p95_power,
        p95_slew=p95_slew,
        target_slew_w_per_s=target_slew_w_per_s,
        normalized_curvature=normalized_curvature,
        power_budget_w=power_budget_w,
        thermal_ceiling_c=thermal_ceiling_c,
    )

    return {
        "sample_count": len(samples),
        "observed_power_w": {
            "mean": mean_power,
            "min": min(power) if power else None,
            "max": max(power) if power else None,
            "p95": p95_power,
            "stdev": statistics.pstdev(power) if len(power) > 1 else 0.0,
        },
        "cpu_power_w": {
            "mean": statistics.fmean(cpu) if cpu else 0.0,
            "max": max(cpu) if cpu else None,
        },
        "gpu_power_w": {
            "mean": statistics.fmean(gpu) if gpu else 0.0,
            "max": max(gpu) if gpu else None,
        },
        "slew_w_per_s": {
            "target": target_slew_w_per_s,
            "p95_abs": p95_slew,
            "max_abs": max(abs_slew) if abs_slew else 0.0,
        },
        "curvature_w_per_s2": {
            "p95_abs": p95_curvature,
            "max_abs": max(abs_curvature) if abs_curvature else 0.0,
        },
        "power_sine_eigenvalue": eigenvalue,
        "homeostasis_vector": homeostasis_vector,
        "recommended_start_delay_s": delay_s,
        "risk_class": risk_class,
    }


def build_recommendations(analysis: dict[str, Any], samples: list[dict[str, Any]]) -> list[dict[str, str]]:
    risk = analysis["risk_class"]
    homeostasis_state = analysis["homeostasis_vector"]["state"]
    gpu_present = any(s.get("gpu") for s in samples)
    delay = analysis["recommended_start_delay_s"]
    recommendations = [
        {
            "lane": "scheduler",
            "action": f"Stagger high-power job starts by at least {delay:.1f}s when p95 slew exceeds budget.",
            "safety": "software-only; no hardware write",
        },
        {
            "lane": "concurrency",
            "action": "Run one high-power lane at a time: GPU render/model, full Lean build, large compression eval, or bulk upload verification.",
            "safety": "process scheduling only",
        },
        {
            "lane": "io_tail",
            "action": "Batch tiny-file upload/check tails separately; they create long wall-clock tails without much useful power smoothing signal.",
            "safety": "rclone/job topology only",
        },
    ]
    if homeostasis_state != "homeostatic":
        recommendations.append(
            {
                "lane": "homeostasis",
                "action": "Prefer queueing over parallel launch until the homeostasis vector returns to the stable region.",
                "safety": "software-only topology gate",
            }
        )
    if gpu_present:
        recommendations.append(
            {
                "lane": "gpu",
                "action": "For long GPU jobs, consider a manual lower NVIDIA power limit only after a dry run records the stable workload draw.",
                "safety": "not applied by this script",
            }
        )
    if risk == "high":
        recommendations.append(
            {
                "lane": "gate",
                "action": "Do not launch another high-power lane until the observed waveform returns below the slew budget.",
                "safety": "fail-closed scheduling gate",
            }
        )
    return recommendations


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    analysis = payload["analysis"]
    recs = payload["recommendations"]
    lines = [
        "# Power Sine Software Smoothing Receipt",
        "",
        f"Generated: `{payload['generated_at']}`",
        "",
        "## Scope",
        "",
        "This is a read-only software-level probe. It measures CPU/GPU power telemetry and derives workload scheduling guidance. It does not alter wall power, firmware, CPU governors, RAPL limits, GPU power limits, or fan curves.",
        "",
        "## Observed Waveform",
        "",
        f"- samples: `{analysis['sample_count']}`",
        f"- mean observed power: `{analysis['observed_power_w']['mean']:.3f} W`",
        f"- max observed power: `{analysis['observed_power_w']['max']:.3f} W`",
        f"- p95 absolute slew: `{analysis['slew_w_per_s']['p95_abs']:.3f} W/s`",
        f"- target slew budget: `{analysis['slew_w_per_s']['target']:.3f} W/s`",
        f"- power-sine eigenvalue: `{analysis['power_sine_eigenvalue']:.6f}`",
        f"- homeostasis score: `{analysis['homeostasis_vector']['homeostasis_score']:.6f}`",
        f"- homeostasis state: `{analysis['homeostasis_vector']['state']}`",
        f"- risk class: `{analysis['risk_class']}`",
        f"- recommended high-power start delay: `{analysis['recommended_start_delay_s']:.3f} s`",
        "",
        "## Software Smoothing Law",
        "",
        "```",
        "P(t) = P_cpu_rapl(t) + P_gpu_nvidia(t)",
        "slew(t) = dP/dt",
        "curvature(t) = d2P/dt2",
        "lambda = max(0, p95(|slew|) - slew_budget) / slew_budget",
        "       + 0.25 * p95(|curvature|) / mean(P)",
        "start_delay = 2 * sqrt(lambda)",
        "```",
        "",
        "## Homeostasis Eigenvector",
        "",
        "```",
        "H = [",
        "  power_headroom,",
        "  slew_margin,",
        "  curvature_damping,",
        "  thermal_headroom,",
        "  gpu_limit_headroom,",
        "  lane_contention_slack",
        "]",
        "```",
        "",
        "Components:",
        "",
    ]
    for name, value in analysis["homeostasis_vector"]["components"].items():
        lines.append(f"- `{name}`: `{value:.6f}`")
    lines.extend(
        [
        "",
        "## Recommendations",
        "",
        ]
    )
    for rec in recs:
        lines.append(f"- `{rec['lane']}`: {rec['action']} ({rec['safety']})")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This receipt can justify workload scheduling and upload/build lane shaping. It is not evidence of physical power conditioning, PSU computation, or mains sine-wave correction.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=15.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--target-slew-w-per-s", type=float, default=25.0)
    parser.add_argument("--power-budget-w", type=float, default=350.0)
    parser.add_argument("--thermal-ceiling-c", type=float, default=83.0)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    args = parser.parse_args()

    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    samples, zones = sample_power(args.duration, args.interval)
    analysis = analyze_samples(
        samples,
        target_slew_w_per_s=args.target_slew_w_per_s,
        power_budget_w=args.power_budget_w,
        thermal_ceiling_c=args.thermal_ceiling_c,
    )
    payload = {
        "generated_at": generated_at,
        "scope": "read_only_software_power_smoothing",
        "rapl_zones": [
            {"name": zone.name, "energy_path": str(zone.energy_path)}
            for zone in zones
        ],
        "analysis": analysis,
        "recommendations": build_recommendations(analysis, samples),
        "samples": samples,
        "claim_boundary": [
            "software workload shaping only",
            "no wall power conditioning",
            "no firmware or power-limit writes",
            "no physical safety claim",
        ],
    }

    json_path = args.artifact_dir / f"power_sine_smoothing_receipt_{stamp}.json"
    md_path = args.artifact_dir / f"power_sine_smoothing_receipt_{stamp}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "analysis": analysis}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
