#!/usr/bin/env python3
"""Genus-0 sphere-shell witness demo.

This is the visual/geometry sibling of the Route-Repair v1.4 charted repair
manifold:

    16D modifier -> 4D contractible chart axis -> 3D embedded witness

The point of this file is deliberately modest and testable:

1. The 16D modifier lives in R^16, which is contractible.
2. The 4D chart axis is a probability simplex Delta^4, which is convex.
3. The 3D patch embedding lives in R^3_+, which is convex.
4. The rendered shell is a 2-sphere witness, genus 0, with beta_1 = 0.

So this demo is NOT the genus-3 residual model. It is the genus-0 base case:
the control spaces are hole-free, and higher-genus signatures should be reserved
for residual/stress graphs or non-contractible topology witnesses.

The output JSON is a receipt-style summary that can be consumed by docs, tests,
or later NUVMAP/PIST routing tools.
"""
# PARTIAL BOUNDARY: contains domain logic; not a provable surface. Port to Lean/RRC before treating as authoritative.

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
TAU = 2.0 * math.pi


@dataclass(frozen=True)
class GenusCertificate:
    """Topological certificate for the rendered witness surface."""

    surface: str
    genus: int
    euler_characteristic: int
    beta_0: int
    beta_1: int
    beta_2: int
    note: str


@dataclass(frozen=True)
class ProjectionReceipt:
    """Receipt for one 16D -> 4D -> 3D projection."""

    seed: str
    modifier_16d: List[float]
    axis_4d_simplex: List[float]
    patch_embed_3d_positive: List[float]
    genus_certificate: GenusCertificate
    contractible_base_spaces: dict


@dataclass(frozen=True)
class ShellSample:
    """One sampled point on the genus-0 shell witness."""

    point: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    signed_distance: float
    shell_weight: float
    noise: float
    displacement: float
    displaced_point: Tuple[float, float, float]


def stable_unit(seed: str, index: int) -> float:
    """Deterministic [0, 1) scalar from a seed and index."""
    h = hashlib.sha256(f"{seed}:{index}".encode("utf-8")).digest()
    n = int.from_bytes(h[:8], "big")
    return n / float(1 << 64)


def build_modifier_16d(seed: str) -> List[float]:
    """Build a deterministic R^16 modifier vector in [-1, 1]."""
    return [round(2.0 * stable_unit(seed, i) - 1.0, 8) for i in range(16)]


def softmax(xs: Sequence[float]) -> List[float]:
    """Map R^4 to the interior of the 4-simplex-like chart axis."""
    m = max(xs)
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps)
    return [x / s for x in exps]


def project_16d_to_4d_simplex(z16: Sequence[float]) -> List[float]:
    """Collapse four 4D blocks into a contractible 4D chart axis.

    The four coordinates can be read as:
      rewrite/equality, flow/implication, branch/constructor, metric/arithmetic
    for proof repair; or field, phase, shell, residual for sphere fields.
    """
    if len(z16) != 16:
        raise ValueError("modifier must have exactly 16 coordinates")
    blocks = [z16[i : i + 4] for i in range(0, 16, 4)]
    block_scores = [sum(block) / 4.0 for block in blocks]
    return [round(v, 8) for v in softmax(block_scores)]


def project_4d_to_3d_positive(axis4: Sequence[float]) -> List[float]:
    """Project Delta^4 into R^3_+ as amplitude/frequency/shell-width controls."""
    if len(axis4) != 4:
        raise ValueError("axis must have exactly 4 coordinates")
    # Positive orthant embedding. The final coordinate acts as residual/phase load.
    amplitude = 0.05 + 0.30 * axis4[0] + 0.10 * axis4[3]
    frequency = 1.0 + 7.0 * axis4[1] + 2.0 * axis4[3]
    shell_width = 0.02 + 0.25 * axis4[2] + 0.08 * axis4[3]
    return [round(amplitude, 8), round(frequency, 8), round(shell_width, 8)]


def genus0_certificate() -> GenusCertificate:
    """Return the genus-0 certificate for S^2."""
    return GenusCertificate(
        surface="S^2 sphere shell",
        genus=0,
        euler_characteristic=2,
        beta_0=1,
        beta_1=0,
        beta_2=1,
        note="Rendered witness is a genus-0 closed orientable surface; control spaces R^16, Delta^4, and R^3_+ are contractible.",
    )


def make_receipt(seed: str) -> ProjectionReceipt:
    z16 = build_modifier_16d(seed)
    axis4 = project_16d_to_4d_simplex(z16)
    embed3 = project_4d_to_3d_positive(axis4)
    return ProjectionReceipt(
        seed=seed,
        modifier_16d=z16,
        axis_4d_simplex=axis4,
        patch_embed_3d_positive=embed3,
        genus_certificate=genus0_certificate(),
        contractible_base_spaces={
            "modifier_16d": "R^16, contractible",
            "axis_4d": "probability simplex, convex/contractible",
            "patch_embed_3d": "R^3_+, convex/contractible",
        },
    )


def sdf_sphere(p: Sequence[float], radius: float = 1.0) -> float:
    return math.sqrt(sum(x * x for x in p)) - radius


def normalize(p: Sequence[float]) -> Tuple[float, float, float]:
    n = math.sqrt(sum(x * x for x in p))
    if n == 0.0:
        return (0.0, 0.0, 1.0)
    return (p[0] / n, p[1] / n, p[2] / n)


def shell_window(distance: float, width: float) -> float:
    if width <= 0:
        return 0.0
    return max(0.0, 1.0 - abs(distance) / width)


def hash_noise3(p: Sequence[float], frequency: float, octave: int, seed: str) -> float:
    """Cheap deterministic pseudo-noise in [-1, 1].

    This is not a production gradient-noise implementation. It is intentionally
    dependency-free and receipt-stable for demos/tests.
    """
    x, y, z = p
    q = (
        math.sin((x * 12.9898 + y * 78.233 + z * 37.719 + octave * PHI) * frequency),
        math.sin((x * 93.989 + y * 67.345 + z * 11.135 + octave * TAU) * frequency),
        math.sin((x * 45.332 + y * 13.775 + z * 91.121 + octave * 1.4142) * frequency),
    )
    seed_shift = stable_unit(seed, 1000 + octave)
    v = math.sin(43758.5453 * (q[0] + 0.7 * q[1] + 0.3 * q[2] + seed_shift))
    return 2.0 * (v - math.floor(v)) - 1.0


def fbm3(p: Sequence[float], frequency: float, seed: str, octaves: int = 5) -> float:
    total = 0.0
    amp = 0.5
    norm = 0.0
    freq = frequency
    for octave in range(octaves):
        total += amp * hash_noise3(p, freq, octave, seed)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm if norm else 0.0


def fibonacci_sphere(samples: int) -> Iterable[Tuple[float, float, float]]:
    if samples <= 0:
        return
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(samples):
        y = 1.0 - (i / float(samples - 1)) * 2.0 if samples > 1 else 0.0
        radius = math.sqrt(max(0.0, 1.0 - y * y))
        theta = golden_angle * i
        x = math.cos(theta) * radius
        z = math.sin(theta) * radius
        yield (x, y, z)


def sample_shell(receipt: ProjectionReceipt, samples: int) -> List[ShellSample]:
    amplitude, frequency, shell_width = receipt.patch_embed_3d_positive
    out: List[ShellSample] = []
    for p in fibonacci_sphere(samples):
        n = normalize(p)
        d = sdf_sphere(p)
        w = shell_window(d, shell_width)
        # Sample through embedded normal and shell phase.
        probe = tuple(p[i] + n[i] * shell_width for i in range(3))
        noise = fbm3(probe, frequency=frequency, seed=receipt.seed)
        disp = amplitude * w * noise
        displaced = tuple(round(p[i] + n[i] * disp, 8) for i in range(3))
        out.append(
            ShellSample(
                point=tuple(round(x, 8) for x in p),
                normal=tuple(round(x, 8) for x in n),
                signed_distance=round(d, 8),
                shell_weight=round(w, 8),
                noise=round(noise, 8),
                displacement=round(disp, 8),
                displaced_point=displaced,
            )
        )
    return out


def build_demo(seed: str, samples: int) -> dict:
    receipt = make_receipt(seed)
    shell_samples = sample_shell(receipt, samples=samples)
    amplitude, frequency, shell_width = receipt.patch_embed_3d_positive
    return {
        "demo": "genus0_sphere_shell",
        "equation": "F(p; z16) = sdf_sphere(p) - A(z16) * W(d(p)) * fBm3(p + n(p) * shell_width)",
        "projection_chain": "R^16 -> Delta^4 -> R^3_+ -> S^2 shell witness",
        "receipt": {
            **asdict(receipt),
            "field_controls": {
                "amplitude": amplitude,
                "frequency": frequency,
                "shell_width": shell_width,
            },
        },
        "sample_count": len(shell_samples),
        "samples": [asdict(s) for s in shell_samples],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit a genus-0 sphere-shell projection witness JSON.")
    parser.add_argument("--seed", default="pist-nuvmap-genus0", help="deterministic seed")
    parser.add_argument("--samples", type=int, default=32, help="number of shell samples")
    parser.add_argument("--out", default="shared-data/genus0_sphere_shell_witness.json", help="output JSON path")
    args = parser.parse_args()

    demo = build_demo(seed=args.seed, samples=args.samples)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(demo, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(out),
        "seed": args.seed,
        "samples": args.samples,
        "genus": demo["receipt"]["genus_certificate"]["genus"],
        "axis_4d_simplex": demo["receipt"]["axis_4d_simplex"],
        "patch_embed_3d_positive": demo["receipt"]["patch_embed_3d_positive"],
    }, indent=2))


if __name__ == "__main__":
    main()
