#!/usr/bin/env python3
"""First-sweep Hutter/enwik8 starfield eigenprobe.

This probe is deliberately diagnostic. It projects a bounded byte slice through
a declared PIST-style map, writes a density sidecar image, optionally encodes it
with cjxl, extracts connected density groups, and receipts a small eigenprobe
over those groups. It does not make classifier, compression, or Hutter claims.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import subprocess
import time
from collections import deque
from pathlib import Path
from typing import Any

from shim.utils import sha256_bytes, sha256_text, sha256_path, stable_json

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "shared-data" / "data" / "stack_solidification" / "hutter_jxl_starfield"
DEFAULT_INPUTS = [
    Path("/home/allaun/.gemini/antigravity/scratch/kimi_dataset/enwik8"),
    Path("/home/allaun/.local/share/Trash/files/enwik8"),
]

PROTOCOL = "hutter_jxl_starfield_eigenprobe_first_sweep_v1"
PIST_FORMULA = (
    "shell=floor(byte_index/window_size); offset=byte_index%window_size; "
    "x=(17*shell + 7*lo_nibble + offset) mod width; "
    "y=(29*shell + 11*hi_nibble + floor(offset/16)) mod height"
)
CLAIM_BOUNDARY = (
    "diagnostic_only_not_classifier_not_compression_claim_not_hutter_prize_claim"
)


def choose_input(arg_path: str | None) -> Path:
    candidates = [Path(arg_path)] if arg_path else DEFAULT_INPUTS
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    searched = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(f"no enwik8 fixture found; searched: {searched}")


def read_slice(path: Path, max_bytes: int) -> bytes:
    with path.open("rb") as handle:
        return handle.read(max_bytes)


def project_density(data: bytes, width: int, height: int, window_size: int) -> tuple[list[int], dict[str, Any], list[set[int]]]:
    counts = [0] * (width * height)
    occupied_windows: list[set[int]] = [set() for _ in range(width * height)]

    for byte_index, byte in enumerate(data):
        shell = byte_index // window_size
        offset = byte_index % window_size
        lo = byte & 0x0F
        hi = byte >> 4
        x = (17 * shell + 7 * lo + offset) % width
        y = (29 * shell + 11 * hi + (offset // 16)) % height
        cell = y * width + x
        counts[cell] += 1
        if len(occupied_windows[cell]) < 16:
            occupied_windows[cell].add(shell)

    nonzero = sum(1 for value in counts if value)
    backlink_cells = sum(1 for windows in occupied_windows if windows)
    map_stats = {
        "formula": PIST_FORMULA,
        "window_size": window_size,
        "width": width,
        "height": height,
        "source_bytes_projected": len(data),
        "image_cell_count": width * height,
        "nonzero_cells": nonzero,
        "cells_with_window_backlinks": backlink_cells,
    }
    return counts, map_stats, occupied_windows


def write_pgm(path: Path, counts: list[int], width: int, height: int) -> str:
    max_count = max(counts) if counts else 0
    if max_count <= 0:
        pixels = bytes([0] * (width * height))
    else:
        pixels = bytes(min(255, round(255 * value / max_count)) for value in counts)
    header = f"P5\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + pixels)
    return sha256_path(path)


def maybe_encode_jxl(pgm_path: Path, jxl_path: Path) -> dict[str, Any]:
    cjxl = shutil.which("cjxl")
    if not cjxl:
        return {
            "jxl_status": "HOLD_CJXL_NOT_FOUND",
            "tool": None,
            "path": None,
            "sha256": None,
        }

    cmd = [cjxl, str(pgm_path), str(jxl_path), "--quiet", "--lossless_jpeg=0", "-d", "0"]
    started = time.time()
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    elapsed_ms = round((time.time() - started) * 1000, 3)
    if result.returncode != 0 or not jxl_path.exists():
        return {
            "jxl_status": "HOLD_CJXL_FAILED",
            "tool": cjxl,
            "command": cmd,
            "returncode": result.returncode,
            "stderr_tail": result.stderr[-1000:],
            "elapsed_ms": elapsed_ms,
            "path": None,
            "sha256": None,
        }
    return {
        "jxl_status": "ENCODED_LOSSLESS_SIDEcar",
        "tool": cjxl,
        "command": cmd,
        "returncode": result.returncode,
        "elapsed_ms": elapsed_ms,
        "path": str(jxl_path),
        "sha256": sha256_path(jxl_path),
        "byte_length": jxl_path.stat().st_size,
    }


def threshold_for(counts: list[int]) -> dict[str, float]:
    nonzero = [value for value in counts if value > 0]
    if not nonzero:
        return {"mean": 0.0, "std": 0.0, "threshold": math.inf}
    mean = sum(nonzero) / len(nonzero)
    variance = sum((value - mean) ** 2 for value in nonzero) / len(nonzero)
    std = math.sqrt(variance)
    threshold = max(1.0, mean + std)
    return {"mean": mean, "std": std, "threshold": threshold}


def window_hints_for_cells(
    cells: list[int],
    occupied_windows: list[set[int]] | None,
    data: bytes | None,
    window_size: int | None,
) -> list[dict[str, Any]]:
    if occupied_windows is None or data is None or window_size is None:
        return []
    window_ids: set[int] = set()
    for cell in cells:
        window_ids.update(occupied_windows[cell])
        if len(window_ids) >= 12:
            break
    hints = []
    for window_id in sorted(window_ids)[:12]:
        start = window_id * window_size
        end = min(len(data), start + window_size)
        hints.append(
            {
                "window_id": window_id,
                "byte_start": start,
                "byte_end": end,
                "sha256": sha256_bytes(data[start:end]),
            }
        )
    return hints


def connected_components(
    counts: list[int],
    width: int,
    height: int,
    occupied_windows: list[set[int]] | None = None,
    data: bytes | None = None,
    window_size: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    stats = threshold_for(counts)
    threshold = stats["threshold"]
    visited = [False] * len(counts)
    components: list[dict[str, Any]] = []
    neighbors = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

    for start, value in enumerate(counts):
        if visited[start] or value < threshold:
            continue
        queue: deque[int] = deque([start])
        visited[start] = True
        cells: list[int] = []
        while queue:
            cell = queue.popleft()
            cells.append(cell)
            x = cell % width
            y = cell // width
            for dx, dy in neighbors:
                nx = x + dx
                ny = y + dy
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                ncell = ny * width + nx
                if not visited[ncell] and counts[ncell] >= threshold:
                    visited[ncell] = True
                    queue.append(ncell)

        total_density = sum(counts[cell] for cell in cells)
        if total_density:
            cx = sum((cell % width) * counts[cell] for cell in cells) / total_density
            cy = sum((cell // width) * counts[cell] for cell in cells) / total_density
        else:
            cx = sum(cell % width for cell in cells) / len(cells)
            cy = sum(cell // width for cell in cells) / len(cells)
        mean_density = total_density / len(cells)
        local_contrast = mean_density / (stats["mean"] or 1.0)
        components.append(
            {
                "component_id": f"component_{len(components):04d}",
                "area": len(cells),
                "total_density": total_density,
                "mean_density": mean_density,
                "centroid": [cx, cy],
                "local_contrast": local_contrast,
                "sample_cells": cells[:24],
                "source_window_hints": window_hints_for_cells(cells, occupied_windows, data, window_size),
            }
        )

    for i, component in enumerate(components):
        if len(components) == 1:
            component["nearest_neighbor_distance"] = None
            continue
        cx, cy = component["centroid"]
        best = math.inf
        for j, other in enumerate(components):
            if i == j:
                continue
            ox, oy = other["centroid"]
            best = min(best, math.hypot(cx - ox, cy - oy))
        component["nearest_neighbor_distance"] = best

    return components, stats


def covariance_matrix(features: list[list[float]]) -> list[list[float]]:
    if not features:
        return []
    rows = len(features)
    cols = len(features[0])
    means = [sum(row[col] for row in features) / rows for col in range(cols)]
    stds = []
    for col in range(cols):
        variance = sum((row[col] - means[col]) ** 2 for row in features) / rows
        stds.append(math.sqrt(variance) or 1.0)
    z = [[(row[col] - means[col]) / stds[col] for col in range(cols)] for row in features]
    denom = max(1, rows - 1)
    return [
        [sum(row[i] * row[j] for row in z) / denom for j in range(cols)]
        for i in range(cols)
    ]


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(row[i] * vector[i] for i in range(len(vector))) for row in matrix]


def norm(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def eigenprobe(components: list[dict[str, Any]], width: int, height: int) -> dict[str, Any]:
    if len(components) < 2:
        return {
            "method": "zscore_covariance_power_iteration",
            "component_count": len(components),
            "dominant_share": 0.0,
            "dominant_eigenvalue": 0.0,
            "trace": 0.0,
            "residual_l2": None,
            "converged": False,
            "dominant_vector": [],
            "dominant_vector_hash": sha256_text("[]"),
            "iterations": 0,
        }

    features = []
    for component in components:
        nn = component["nearest_neighbor_distance"]
        features.append(
            [
                math.log1p(component["area"]),
                math.log1p(component["total_density"]),
                component["mean_density"],
                component["centroid"][0] / max(1, width - 1),
                component["centroid"][1] / max(1, height - 1),
                0.0 if nn is None else nn / math.hypot(width, height),
                component["local_contrast"],
            ]
        )

    matrix = covariance_matrix(features)
    n = len(matrix)
    vector = [1.0 / math.sqrt(n)] * n
    residual = math.inf
    eigval = 0.0
    iterations = 0
    for iterations in range(1, 101):
        av = matvec(matrix, vector)
        av_norm = norm(av)
        if av_norm == 0.0:
            break
        vector = [value / av_norm for value in av]
        av = matvec(matrix, vector)
        eigval = sum(vector[i] * av[i] for i in range(n))
        residual = norm([av[i] - eigval * vector[i] for i in range(n)])
        if residual < 1e-10:
            break
    trace = sum(matrix[i][i] for i in range(n))
    dominant_share = eigval / trace if trace > 0 else 0.0
    rounded_vector = [round(value, 12) for value in vector]
    return {
        "method": "zscore_covariance_power_iteration",
        "component_count": len(components),
        "feature_order": [
            "log_area",
            "log_total_density",
            "mean_density",
            "centroid_x_norm",
            "centroid_y_norm",
            "nearest_neighbor_norm",
            "local_contrast",
        ],
        "dominant_share": dominant_share,
        "dominant_eigenvalue": eigval,
        "trace": trace,
        "residual_l2": residual,
        "converged": residual < 1e-8,
        "dominant_vector": rounded_vector,
        "dominant_vector_hash": sha256_text(stable_json(rounded_vector)),
        "iterations": iterations,
    }


def summarize_projection(
    name: str,
    counts: list[int],
    width: int,
    height: int,
    occupied_windows: list[set[int]] | None = None,
    data: bytes | None = None,
    window_size: int | None = None,
) -> dict[str, Any]:
    components, threshold = connected_components(counts, width, height, occupied_windows, data, window_size)
    probe = eigenprobe(components, width, height)
    component_rows = [
        {
            "component_id": component["component_id"],
            "area": component["area"],
            "total_density": component["total_density"],
            "mean_density": round(component["mean_density"], 6),
            "centroid": [round(component["centroid"][0], 6), round(component["centroid"][1], 6)],
            "nearest_neighbor_distance": None
            if component["nearest_neighbor_distance"] is None
            else round(component["nearest_neighbor_distance"], 6),
            "local_contrast": round(component["local_contrast"], 6),
            "sample_cells": component["sample_cells"],
            "source_window_hints": component["source_window_hints"],
        }
        for component in components
    ]
    components_with_backlinks = sum(1 for row in component_rows if row["source_window_hints"])
    return {
        "name": name,
        "threshold": {key: round(value, 9) for key, value in threshold.items()},
        "cell_count": len(counts),
        "nonzero_cells": sum(1 for value in counts if value > 0),
        "component_count": len(components),
        "components_with_pist_backlinks": components_with_backlinks,
        "density_table_hash": sha256_text(stable_json(counts)),
        "component_table_hash": sha256_text(stable_json(component_rows)),
        "suggested_neighborhoods": component_rows[:40],
        "eigenprobe": {key: (round(value, 12) if isinstance(value, float) else value) for key, value in probe.items()},
    }


def shuffled_counts(counts: list[int], seed: int) -> list[int]:
    values = list(counts)
    random.Random(seed).shuffle(values)
    return values


def phase_shift_counts(counts: list[int], width: int, height: int, dx: int, dy: int) -> list[int]:
    shifted = [0] * len(counts)
    for y in range(height):
        for x in range(width):
            source = y * width + x
            tx = (x + dx) % width
            ty = (y + dy) % height
            shifted[ty * width + tx] = counts[source]
    return shifted


def uniform_counts(counts: list[int]) -> list[int]:
    if not counts:
        return []
    mean = round(sum(counts) / len(counts))
    return [mean] * len(counts)


def decide(main_summary: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    component_count = main_summary["component_count"]
    residual = main_summary["eigenprobe"]["residual_l2"]

    if component_count == 0:
        decision = "OBSERVE_NO_GROUPING"
        reason = "no density-suggestion neighborhoods crossed the declared threshold"
    elif main_summary["components_with_pist_backlinks"] != component_count:
        decision = "QUARANTINE_MISSING_PROVENANCE"
        reason = "one or more density components lacked PIST/source-window backlinks"
    elif residual is None or residual > 1e-6:
        decision = "HOLD_PROJECTION_NOISE"
        reason = "dominant eigenvector did not converge tightly enough to describe the suggestion surface"
    elif component_count >= 8:
        decision = "OBSERVE_DENSITY_SUGGESTIONS"
        reason = "density neighborhoods exist with PIST/source-window backlinks; use them only as byte-replay suggestions"
    else:
        decision = "HOLD_PROJECTION_NOISE"
        reason = "too few density neighborhoods for even a suggestion surface"

    return {
        "decision": decision,
        "reason": reason,
        "claim_boundary": CLAIM_BOUNDARY,
        "forbidden_claims": [
            "CLASSIFIER_SUCCESS",
            "COMPRESSION_GAIN",
            "HUTTER_PROGRESS",
            "JXL_SUPERIORITY",
            "BYTE_SEMANTICS_PROVEN_BY_PIXELS",
            "SORTING_SUCCESS",
            "COMPONENT_RANKING_AUTHORITY",
        ],
        "suggestion_policy": {
            "density_is_authoritative": False,
            "ordering_policy": "scan_order_not_ranked",
            "promotion_requires": "byte_window_replay_receipt",
        },
    }


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    input_path = choose_input(args.input)
    total_size = input_path.stat().st_size
    data = read_slice(input_path, args.max_bytes)
    slice_sha = sha256_bytes(data)
    fixture_id = f"enwik8_first_{len(data)}_bytes"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pgm_path = OUT_DIR / f"{fixture_id}_pist_density.pgm"
    jxl_path = OUT_DIR / f"{fixture_id}_pist_density.jxl"
    receipt_path = OUT_DIR / "hutter_jxl_starfield_enwik8_first_sweep_receipt.json"

    counts, map_stats, occupied_windows = project_density(data, args.width, args.height, args.window_size)
    pgm_sha = write_pgm(pgm_path, counts, args.width, args.height)
    jxl = maybe_encode_jxl(pgm_path, jxl_path)

    map_payload = {
        "map_id": "pist_byte_window_nibble_shell_map_v0",
        "formula": PIST_FORMULA,
        "width": args.width,
        "height": args.height,
        "window_size": args.window_size,
        "slice_sha256": slice_sha,
        "map_is_declared_before_projection": True,
        "unmapped_pixel_policy": "ignore_or_quarantine",
    }
    map_hash = sha256_text(stable_json(map_payload))

    main = summarize_projection(
        "observed_pist_projection",
        counts,
        args.width,
        args.height,
        occupied_windows=occupied_windows,
        data=data,
        window_size=args.window_size,
    )
    controls = {
        "shuffled_pixel_cells": summarize_projection(
            "shuffled_pixel_cells",
            shuffled_counts(counts, seed=0xA11A),
            args.width,
            args.height,
        ),
        "randomized_pist_cell_assignment": summarize_projection(
            "randomized_pist_cell_assignment",
            shuffled_counts(counts, seed=0xBEEF),
            args.width,
            args.height,
        ),
        "uniform_density_synthetic": summarize_projection(
            "uniform_density_synthetic",
            uniform_counts(counts),
            args.width,
            args.height,
        ),
        "phase_shifted_projection": summarize_projection(
            "phase_shifted_projection",
            phase_shift_counts(counts, args.width, args.height, dx=13, dy=21),
            args.width,
            args.height,
        ),
    }

    receipt = {
        "protocol": PROTOCOL,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fixture": {
            "fixture_id": fixture_id,
            "dataset_alias": "wikien8_normalized_to_enwik8",
            "source_path": str(input_path),
            "source_sha256": sha256_path(input_path) if args.full_source_hash else "HOLD_FULL_HASH_NOT_REQUESTED",
            "source_byte_length": total_size,
            "slice_byte_length": len(data),
            "slice_sha256": slice_sha,
        },
        "projection": {
            "projection_kind": "jpeg_xl_sidecar_from_declared_pist_density_projection",
            "projection_tool": "stdlib_pgm_density_projection_plus_optional_cjxl",
            "pgm_path": str(pgm_path),
            "pgm_sha256": pgm_sha,
            "width": args.width,
            "height": args.height,
            "jxl": jxl,
        },
        "pist_map": {
            **map_payload,
            "map_hash": map_hash,
            "cell_count": args.width * args.height,
            "map_stats": map_stats,
        },
        "density": {
            key: main[key]
            for key in [
                "cell_count",
                "nonzero_cells",
                "component_count",
                "components_with_pist_backlinks",
                "density_table_hash",
                "component_table_hash",
                "threshold",
            ]
        },
        "eigenprobe": main["eigenprobe"],
        "suggestion_surface": {
            "mode": "density_as_suggestion_only",
            "suggested_neighborhood_count": main["component_count"],
            "ordering_policy": "scan_order_not_ranked",
            "promotion_policy": "byte_window_replay_required_before_routing_or_compression_use",
            "neighborhood_table_hash": main["component_table_hash"],
        },
        "suggested_neighborhoods": main["suggested_neighborhoods"],
        "controls": controls,
        "gate": decide(main, controls),
        "receipt_path": str(receipt_path),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Path to enwik8/wikien8 fixture")
    parser.add_argument("--max-bytes", type=int, default=1_048_576)
    parser.add_argument("--width", type=int, default=128)
    parser.add_argument("--height", type=int, default=128)
    parser.add_argument("--window-size", type=int, default=256)
    parser.add_argument("--full-source-hash", action="store_true")
    args = parser.parse_args()
    receipt = build_receipt(args)
    print(
        json.dumps(
            {
                "receipt": receipt["receipt_path"],
                "decision": receipt["gate"]["decision"],
                "component_count": receipt["density"]["component_count"],
                "dominant_share": receipt["eigenprobe"]["dominant_share"],
                "residual_l2": receipt["eigenprobe"]["residual_l2"],
                "jxl_status": receipt["projection"]["jxl"]["jxl_status"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
