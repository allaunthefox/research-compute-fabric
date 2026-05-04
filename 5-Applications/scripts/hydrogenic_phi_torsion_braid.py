#!/usr/bin/env python3
"""Generate a hydrogenic Phi-torsion braid with FPGA-friendly stair fields."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


Q16_SCALE = 1 << 16


def q16(value: np.ndarray | float) -> np.ndarray:
    return np.rint(np.asarray(value) * Q16_SCALE).astype(np.int64)


class OntologicalManifold:
    """
    Computes a Phi-torsioned manifold through a hydrogenic orbital constraint.

    The returned braid keeps floating geometry and fixed-point-friendly fields
    side by side: the orbital groove drives the path, and the Phi torsion is
    quantized into "stairs" for event-cell hardware.
    """

    def __init__(self, bohr_radius: float = 1.0, torsion_radius: float = 0.5):
        self.PHI = (1.0 + np.sqrt(5.0)) / 2.0
        self.a0 = bohr_radius
        self.R = torsion_radius
        self.growth_rate = (2.0 / np.pi) * np.log(self.PHI)

    def _fibonacci_spine(self, theta: np.ndarray, r0: float = 1.0) -> np.ndarray:
        return r0 * np.exp(self.growth_rate * theta)

    def _hydrogen_2s_wave_shape(self, r: np.ndarray) -> np.ndarray:
        rho = r / self.a0
        return (2.0 - rho) * np.exp(-rho / 2.0)

    def _normalized_density(self, density: np.ndarray) -> np.ndarray:
        peak = np.max(np.abs(density))
        if peak == 0.0:
            return np.zeros_like(density)
        return density / peak

    def _hydrogen_2s_constraint(
        self, r: np.ndarray, density_mode: str = "topology"
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        psi_2s = self._hydrogen_2s_wave_shape(r)
        topology_density = self._normalized_density(psi_2s**2)
        radial_density = self._normalized_density((r**2) * (psi_2s**2))
        if density_mode == "topology":
            constraint = topology_density
        elif density_mode == "radial":
            constraint = radial_density
        else:
            raise ValueError("density_mode must be 'topology' or 'radial'")
        return constraint, topology_density, radial_density

    def generate_braid(
        self,
        theta_start: float = 0.0,
        theta_end: float = 10.0 * np.pi,
        steps: int = 2000,
        r0: float = 1.0,
        density_mode: str = "topology",
        radial_torsion: float | None = None,
        angular_torsion: float = 1.0,
        stair_divisions: int = 4,
        stair_rise: float = 0.035,
    ) -> dict[str, np.ndarray | dict[str, float | int | str]]:
        theta = np.linspace(theta_start, theta_end, steps)

        r_base = self._fibonacci_spine(theta, r0=r0)
        constraint, topology_density, radial_density = self._hydrogen_2s_constraint(
            r_base, density_mode=density_mode
        )
        r_constrained = r_base * constraint

        x_spine = r_constrained * np.cos(theta)
        y_spine = r_constrained * np.sin(theta)

        radial_torsion = self.PHI if radial_torsion is None else radial_torsion
        torsion_angle = radial_torsion * theta
        angular_theta = angular_torsion * theta
        x_torsion = x_spine + self.R * np.cos(torsion_angle) * np.cos(angular_theta)
        y_torsion = y_spine + self.R * np.cos(torsion_angle) * np.sin(angular_theta)
        z_torsion = self.R * np.sin(torsion_angle)

        stair_period = (2.0 * np.pi) / stair_divisions
        stair_index = np.floor((torsion_angle - torsion_angle[0]) / stair_period).astype(
            np.int64
        )
        stair_phase = np.mod(torsion_angle, stair_period) / stair_period
        stair_lift = stair_index.astype(float) * stair_rise
        z_stair = z_torsion + stair_lift

        dr = np.gradient(r_constrained, theta)
        dz = np.gradient(z_stair, theta)
        strain = np.abs(dr)
        emitted_amplitude = np.abs(dz) * constraint

        return {
            "meta": {
                "phi": float(self.PHI),
                "bohr_radius": float(self.a0),
                "torsion_radius": float(self.R),
                "growth_rate": float(self.growth_rate),
                "density_mode": density_mode,
                "radial_torsion": float(radial_torsion),
                "angular_torsion": float(angular_torsion),
                "stair_divisions": int(stair_divisions),
                "stair_rise": float(stair_rise),
                "theta_start": float(theta_start),
                "theta_end": float(theta_end),
                "steps": int(steps),
            },
            "theta": theta,
            "r_base": r_base,
            "constraint": constraint,
            "topology_density": topology_density,
            "radial_density": radial_density,
            "r_constrained": r_constrained,
            "torsion_angle": torsion_angle,
            "torsion_turn": torsion_angle / (2.0 * np.pi),
            "stair_index": stair_index,
            "stair_phase": stair_phase,
            "stair_lift": stair_lift,
            "strain": strain,
            "emitted_amplitude": emitted_amplitude,
            "coords": np.column_stack((x_torsion, y_torsion, z_torsion)),
            "stair_coords": np.column_stack((x_torsion, y_torsion, z_stair)),
        }

    def generate_fpga_table(self, braid: dict[str, np.ndarray], sample_stride: int = 1) -> np.ndarray:
        idx = np.arange(0, len(braid["theta"]), sample_stride)
        phase_unit = np.mod(braid["torsion_angle"][idx], 2.0 * np.pi) / (2.0 * np.pi)
        table = np.column_stack(
            (
                idx,
                braid["stair_index"][idx],
                q16(braid["r_constrained"][idx]),
                q16(braid["constraint"][idx]),
                q16(phase_unit),
                q16(braid["strain"][idx]),
                q16(braid["emitted_amplitude"][idx]),
                q16(braid["stair_coords"][idx, 2]),
            )
        )
        return table.astype(np.int64)


def write_outputs(
    braid: dict[str, np.ndarray | dict[str, float | int | str]],
    fpga_table: np.ndarray,
    out_prefix: Path,
    plot: bool = False,
) -> dict[str, str]:
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    csv_path = out_prefix.with_suffix(".csv")
    fpga_path = out_prefix.with_name(out_prefix.name + "_fpga_q16.csv")
    summary_path = out_prefix.with_name(out_prefix.name + "_summary.json")

    columns = np.column_stack(
        (
            braid["theta"],
            braid["r_base"],
            braid["constraint"],
            braid["topology_density"],
            braid["radial_density"],
            braid["r_constrained"],
            braid["torsion_angle"],
            braid["torsion_turn"],
            braid["stair_index"],
            braid["stair_phase"],
            braid["stair_lift"],
            braid["strain"],
            braid["emitted_amplitude"],
            braid["coords"],
            braid["stair_coords"],
        )
    )
    header = ",".join(
        [
            "theta",
            "r_base",
            "constraint",
            "topology_density",
            "radial_density",
            "r_constrained",
            "torsion_angle",
            "torsion_turn",
            "stair_index",
            "stair_phase",
            "stair_lift",
            "strain",
            "emitted_amplitude",
            "x",
            "y",
            "z_torsion",
            "x_stair",
            "y_stair",
            "z_stair",
        ]
    )
    np.savetxt(csv_path, columns, delimiter=",", header=header, comments="")
    np.savetxt(
        fpga_path,
        fpga_table,
        delimiter=",",
        fmt="%d",
        header="idx,stair_index,r_constrained_q16,constraint_q16,phase_unit_q16,strain_q16,emitted_amplitude_q16,z_stair_q16",
        comments="",
    )

    stair_index = braid["stair_index"]
    summary = {
        "meta": braid["meta"],
        "generation_equations": {
            "phi": "(1 + sqrt(5)) / 2",
            "growth_rate": "(2 / pi) * log(phi)",
            "r_base": "r0 * exp(growth_rate * theta)",
            "psi_2s": "(2 - r/a0) * exp(-(r/a0) / 2)",
            "topology_constraint": "normalize(psi_2s^2)",
            "radial_constraint": "normalize(r^2 * psi_2s^2)",
            "r_constrained": "r_base * selected_constraint",
            "torsion_angle": "radial_torsion * theta",
            "angular_theta": "angular_torsion * theta",
            "stair_index": "floor((torsion_angle - torsion_angle_0) / ((2*pi) / stair_divisions))",
            "z_stair": "torsion_radius * sin(torsion_angle) + stair_index * stair_rise",
            "strain": "abs(gradient(r_constrained, theta))",
            "emitted_amplitude": "abs(gradient(z_stair, theta)) * selected_constraint",
        },
        "semantic_mapping": {
            "r_base": "Fibonacci manifold expansion",
            "constraint": "hydrogenic orbital groove",
            "stair_index": "quantized Phi-torsion climb level",
            "strain": "local shell stress proxy",
            "emitted_amplitude": "phonon or curvature-sound packet proxy",
            "fpga_q16_csv": "fixed-point event-cell feed surface",
        },
        "q16_scale": Q16_SCALE,
        "samples": int(len(braid["theta"])),
        "stairs": int(stair_index[-1] - stair_index[0] + 1),
        "r_constrained_max": float(np.max(braid["r_constrained"])),
        "constraint_min": float(np.min(braid["constraint"])),
        "constraint_max": float(np.max(braid["constraint"])),
        "z_torsion_range": [
            float(np.min(braid["coords"][:, 2])),
            float(np.max(braid["coords"][:, 2])),
        ],
        "z_stair_range": [
            float(np.min(braid["stair_coords"][:, 2])),
            float(np.max(braid["stair_coords"][:, 2])),
        ],
        "max_strain": float(np.max(braid["strain"])),
        "max_emitted_amplitude": float(np.max(braid["emitted_amplitude"])),
        "fpga_columns": [
            "idx",
            "stair_index",
            "r_constrained_q16",
            "constraint_q16",
            "phase_unit_q16",
            "strain_q16",
            "emitted_amplitude_q16",
            "z_stair_q16",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    outputs = {
        "csv": str(csv_path),
        "fpga_q16_csv": str(fpga_path),
        "summary": str(summary_path),
    }
    if plot:
        outputs["plot"] = str(write_plot(braid, out_prefix.with_suffix(".png")))
    return outputs


def write_plot(
    braid: dict[str, np.ndarray | dict[str, float | int | str]], out_path: Path
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(12, 7), facecolor="#11151c")
    ax = fig.add_subplot(121, projection="3d", facecolor="#11151c")
    coords = braid["stair_coords"]
    amp = braid["emitted_amplitude"]
    ax.plot(coords[:, 0], coords[:, 1], coords[:, 2], color="#9fc0ff", alpha=0.65, lw=0.7)
    hot = amp > np.quantile(amp, 0.92)
    ax.scatter(
        coords[hot, 0],
        coords[hot, 1],
        coords[hot, 2],
        c=amp[hot],
        cmap="Blues",
        s=5,
        alpha=0.9,
    )
    ax.set_title("Hydrogenic Phi-Torsion Stair Braid", color="white")
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_tick_params(colors="#9aa4b2")
    ax.set_xlabel("x", color="#9aa4b2")
    ax.set_ylabel("y", color="#9aa4b2")
    ax.set_zlabel("z_stair", color="#9aa4b2")

    ax2 = fig.add_subplot(222, facecolor="#11151c")
    ax2.plot(braid["theta"], braid["constraint"], color="#9fc0ff", lw=1.0)
    ax2.set_title("2s Constraint Groove", color="white")
    ax2.tick_params(colors="#9aa4b2")

    ax3 = fig.add_subplot(224, facecolor="#11151c")
    ax3.plot(braid["theta"], braid["emitted_amplitude"], color="#3c8cff", lw=0.9)
    ax3.set_title("Wave Emission Proxy", color="white")
    ax3.tick_params(colors="#9aa4b2")

    fig.tight_layout()
    fig.savefig(out_path, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-prefix", default="shared-data/data/generated/hydrogenic_phi_torsion_braid")
    parser.add_argument("--theta-end", type=float, default=10.0 * np.pi)
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--bohr-radius", type=float, default=1.0)
    parser.add_argument("--torsion-radius", type=float, default=0.5)
    parser.add_argument("--density-mode", choices=["topology", "radial"], default="topology")
    parser.add_argument("--radial-torsion", type=float, default=None)
    parser.add_argument("--angular-torsion", type=float, default=1.0)
    parser.add_argument("--stair-divisions", type=int, default=4)
    parser.add_argument("--stair-rise", type=float, default=0.035)
    parser.add_argument("--fpga-stride", type=int, default=8)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    manifold = OntologicalManifold(args.bohr_radius, args.torsion_radius)
    braid = manifold.generate_braid(
        theta_end=args.theta_end,
        steps=args.steps,
        density_mode=args.density_mode,
        radial_torsion=args.radial_torsion,
        angular_torsion=args.angular_torsion,
        stair_divisions=args.stair_divisions,
        stair_rise=args.stair_rise,
    )
    fpga_table = manifold.generate_fpga_table(braid, sample_stride=args.fpga_stride)
    outputs = write_outputs(braid, fpga_table, Path(args.out_prefix), plot=args.plot)
    print(json.dumps({"ok": True, **outputs}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
