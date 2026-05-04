#!/usr/bin/env python3
"""
Generate a small S3C-GPE landscape CSV and SVG.

This is a visualization shim. The source-of-truth safety logic lives in
0-Core-Formalism/lean/Semantics/Semantics/NUVMATH.lean and Semantics/S3C.lean.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "generated"
CSV_PATH = OUT_DIR / "s3c_gpe_landscape.csv"
SVG_PATH = OUT_DIR / "s3c_gpe_landscape.svg"


def s3c_terms(n: float, g0: float = 1.0, kappa: float = 0.5) -> dict[str, float | bool]:
    k = math.floor(math.sqrt(n))
    a = n - k * k
    b0 = (k + 1) * (k + 1) - 1 - n
    j_score = (a * b0) + abs(a - b0) + k
    emit = a > 1.0e-2 and b0 > 1.0e-2
    stiffness = g0 * (1.0 + kappa / (j_score + 1.0e-3)) if emit else g0 * 100.0
    available_velocity = min(1.0, j_score / 16.0) if emit else 0.0
    return {
        "n": n,
        "k": k,
        "a": a,
        "b0": b0,
        "j_score": j_score,
        "stiffness": stiffness,
        "standard_g": g0,
        "available_velocity": available_velocity,
        "emit": emit,
    }


def sample_shell(start: float = 9.01, stop: float = 15.99, count: int = 240) -> list[dict[str, float | bool]]:
    step = (stop - start) / (count - 1)
    return [s3c_terms(start + i * step) for i in range(count)]


def write_csv(rows: list[dict[str, float | bool]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def polyline(rows: list[dict[str, float | bool]], key: str, y_max: float, color: str) -> str:
    width = 920
    height = 420
    left = 60
    top = 30
    plot_w = width - 100
    plot_h = height - 80
    n_min = float(rows[0]["n"])
    n_max = float(rows[-1]["n"])
    points = []
    for row in rows:
        x = left + (float(row["n"]) - n_min) / (n_max - n_min) * plot_w
        y = top + plot_h - min(float(row[key]), y_max) / y_max * plot_h
        points.append(f"{x:.2f},{y:.2f}")
    return f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(points)}" />'


def write_svg(rows: list[dict[str, float | bool]]) -> None:
    width = 920
    height = 420
    j_max = max(float(row["j_score"]) for row in rows)
    stiff_max = min(2.0, max(float(row["stiffness"]) for row in rows))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#fbfaf7"/>
  <line x1="60" y1="370" x2="880" y2="370" stroke="#333" stroke-width="1"/>
  <line x1="60" y1="30" x2="60" y2="370" stroke="#333" stroke-width="1"/>
  <text x="60" y="24" font-family="monospace" font-size="14">S3C-GPE shell landscape, n in [9,16]</text>
  <text x="745" y="392" font-family="monospace" font-size="12">energy density n</text>
  <text x="70" y="55" font-family="monospace" font-size="12" fill="#b43b3b">J-score</text>
  <text x="70" y="75" font-family="monospace" font-size="12" fill="#2457a6">stiffness</text>
  <text x="70" y="95" font-family="monospace" font-size="12" fill="#2f7d47">available velocity</text>
  {polyline(rows, "j_score", j_max, "#b43b3b")}
  {polyline(rows, "stiffness", stiff_max, "#2457a6")}
  {polyline(rows, "available_velocity", 1.0, "#2f7d47")}
</svg>
"""
    SVG_PATH.write_text(svg)


def main() -> int:
    rows = sample_shell()
    write_csv(rows)
    write_svg(rows)
    print(f"wrote {CSV_PATH}")
    print(f"wrote {SVG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
