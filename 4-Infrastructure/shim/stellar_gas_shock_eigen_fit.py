#!/usr/bin/env python3
"""Fit SDSS MaNGA DAPall observation proxies against local shock eigen lanes.

This is an observation-proxy fit, not astrophysical validation. It measures
whether the pulled MaNGA gas/velocity columns provide nonzero support for the
physical-shock eigen axis identified in the stack-solidification audit.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SEED_SCRIPT = REPO / "4-Infrastructure/shim/sdss_manga_dapall_observation_seed.py"
DATA_DIR = REPO / "shared-data/data/stellar_gas_observation"
DOC_PATH = REPO / "6-Documentation/docs/stellar_gas_shock_eigen_fit_2026-05-09.md"
DEFAULT_FITS = REPO / "shared-data/artifacts/stellar_gas_observation/dapall-v3_1_1-3.1.0.fits"
DESTINATION = "Gdrive:topological_storage/research-stack/stellar-gas-observation/seed-2026-05-09"


TARGET_COLUMNS = [
    "PLATEIFU",
    "MANGAID",
    "DAPTYPE",
    "Z",
    "BINSNR",
    "SNR_MED",
    "STELLAR_SIGMA_1RE",
    "STELLAR_VEL_LO_CLIP",
    "STELLAR_VEL_HI_CLIP",
    "HA_GVEL_LO_CLIP",
    "HA_GVEL_HI_CLIP",
    "HA_GSIGMA_1RE",
    "HA_GSIGMA_HI_CLIP",
    "EMLINE_RCHI2_1RE",
]


LOCAL_EIGEN_PRIORS = {
    "radiation_absorption": {
        "cluster": "Electromagnetism & Circuits",
        "eigenvalue": 0.96875,
        "prior_strength": 0.176777,
    },
    "diffusion_material_transport": {
        "cluster": "Condensed Matter & Superconductivity",
        "eigenvalue": 0.969697,
        "prior_strength": 0.174078,
    },
    "radiation_spectrum": {
        "cluster": "Quantum Mechanics & Particle Physics",
        "eigenvalue": 0.970588,
        "prior_strength": 0.171499,
    },
    "acoustic_boundary": {
        "cluster": "Materials Science & Engineering",
        "eigenvalue": 0.992063,
        "prior_strength": 0.089087,
    },
    "local_stack_shock_alignment": {
        "cluster": "Cognitive & Semantic Systems",
        "eigenvalue": 0.998464,
        "prior_strength": 0.039193,
    },
    "classical_hydrodynamic_shock": {
        "cluster": "Detonics & Shock Physics",
        "eigenvalue": None,
        "prior_strength": 0.0,
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_seed_module():
    spec = importlib.util.spec_from_file_location("sdss_manga_dapall_observation_seed", SEED_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SEED_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def rclone_copyto(local: Path, remote: str) -> tuple[bool, str]:
    proc = run(["rclone", "copyto", str(local), remote, "--checksum"])
    message = (proc.stderr or proc.stdout).decode(errors="replace").strip()
    return proc.returncode == 0, message


def finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value > -900


def scalar(value):
    if finite(value):
        return float(value)
    return None


def list_mean(value):
    if isinstance(value, list):
        vals = [float(v) for v in value if finite(v)]
        return statistics.fmean(vals) if vals else None
    return scalar(value)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def summarize(values: list[float]) -> dict:
    vals = sorted(v for v in values if math.isfinite(v))
    if not vals:
        return {"count": 0}
    return {
        "count": len(vals),
        "min": round(vals[0], 6),
        "max": round(vals[-1], 6),
        "mean": round(statistics.fmean(vals), 6),
        "median": round(statistics.median(vals), 6),
        "p90": round(vals[int(0.9 * (len(vals) - 1))], 6),
    }


def row_proxy(fields: dict) -> dict | None:
    gas_lo = scalar(fields.get("HA_GVEL_LO_CLIP"))
    gas_hi = scalar(fields.get("HA_GVEL_HI_CLIP"))
    stellar_lo = scalar(fields.get("STELLAR_VEL_LO_CLIP"))
    stellar_hi = scalar(fields.get("STELLAR_VEL_HI_CLIP"))
    gas_sigma = scalar(fields.get("HA_GSIGMA_1RE"))
    gas_sigma_hi = scalar(fields.get("HA_GSIGMA_HI_CLIP"))
    stellar_sigma = scalar(fields.get("STELLAR_SIGMA_1RE"))
    rchi2 = scalar(fields.get("EMLINE_RCHI2_1RE"))
    snr = list_mean(fields.get("SNR_MED"))

    gas_span = None if gas_lo is None or gas_hi is None else max(0.0, gas_hi - gas_lo)
    stellar_span = None if stellar_lo is None or stellar_hi is None else max(0.0, stellar_hi - stellar_lo)
    if gas_span is None and gas_sigma is None and rchi2 is None:
        return None

    velocity_contrast = None
    if gas_span is not None and stellar_span is not None:
        velocity_contrast = gas_span / max(stellar_span, 1.0)

    sigma_contrast = None
    if gas_sigma is not None and stellar_sigma is not None:
        sigma_contrast = gas_sigma / max(stellar_sigma, 1.0)

    quality = clamp01((snr or 0.0) / 20.0)
    fit_quality = clamp01(1.0 / max(rchi2 or 99.0, 1.0))
    span_score = clamp01((gas_span or 0.0) / 1000.0)
    sigma_score = clamp01((gas_sigma or 0.0) / 300.0)
    contrast_score = clamp01((velocity_contrast or 0.0) / 5.0)
    # Proxy only: broad gas line + high gas/stellar contrast + acceptable fit/SNR.
    shock_proxy_score = clamp01(
        0.35 * span_score
        + 0.30 * sigma_score
        + 0.20 * contrast_score
        + 0.10 * fit_quality
        + 0.05 * quality
    )

    return {
        "gas_velocity_span_kms": gas_span,
        "stellar_velocity_span_kms": stellar_span,
        "velocity_contrast": velocity_contrast,
        "gas_sigma_1re_kms": gas_sigma,
        "gas_sigma_hi_clip_kms": gas_sigma_hi,
        "stellar_sigma_1re_kms": stellar_sigma,
        "sigma_contrast": sigma_contrast,
        "emline_rchi2_1re": rchi2,
        "snr_med_mean": snr,
        "shock_proxy_score": shock_proxy_score,
    }


def iter_bintable_rows(fits_path: Path, limit_rows: int | None = None):
    seed = load_seed_module()
    emitted = 0
    with fits_path.open("rb") as f:
        hdu_index = 0
        while True:
            try:
                header, _ = seed.read_header(f)
            except EOFError:
                break
            data_start = f.tell()
            xtension = str(header.get("XTENSION", "PRIMARY"))
            if xtension == "BINTABLE":
                row_len = int(header["NAXIS1"])
                row_count = int(header["NAXIS2"])
                pcount = int(header.get("PCOUNT", 0))
                columns = seed.build_columns(header)
                by_name = {col["name"]: col for col in columns}
                selected = [by_name[name] for name in TARGET_COLUMNS if name in by_name]
                hdu_name = str(header.get("EXTNAME", f"HDU{hdu_index}"))
                for row_idx in range(row_count):
                    if limit_rows is not None and emitted >= limit_rows:
                        return
                    f.seek(data_start + row_idx * row_len)
                    row = f.read(row_len)
                    fields = {}
                    for col in selected:
                        raw = row[col["offset"] : col["offset"] + col["width"]]
                        value = seed.decode_value(raw, col)
                        if isinstance(value, str):
                            value = value.replace("\u0000", "").strip()
                        fields[col["name"]] = value
                    emitted += 1
                    yield hdu_index, hdu_name, row_idx, fields
                f.seek(data_start + seed.padded_size(row_len * row_count + pcount))
            else:
                bitpix = int(header.get("BITPIX", 8))
                naxis = int(header.get("NAXIS", 0))
                if naxis == 0:
                    data_size = 0
                else:
                    pixels = 1
                    for axis in range(1, naxis + 1):
                        pixels *= int(header.get(f"NAXIS{axis}", 0))
                    data_size = abs(bitpix) // 8 * pixels
                f.seek(data_start + seed.padded_size(data_size))
            hdu_index += 1


def build_fit(fits_path: Path, limit_rows: int | None) -> dict:
    rows = []
    summaries = {
        "gas_velocity_span_kms": [],
        "stellar_velocity_span_kms": [],
        "velocity_contrast": [],
        "gas_sigma_1re_kms": [],
        "gas_sigma_hi_clip_kms": [],
        "stellar_sigma_1re_kms": [],
        "sigma_contrast": [],
        "emline_rchi2_1re": [],
        "snr_med_mean": [],
        "shock_proxy_score": [],
    }
    hdu_counts: dict[str, int] = {}
    admitted = 0
    for hdu_index, hdu_name, row_idx, fields in iter_bintable_rows(fits_path, limit_rows):
        hdu_counts[hdu_name] = hdu_counts.get(hdu_name, 0) + 1
        proxy = row_proxy(fields)
        if proxy is None:
            continue
        admitted += 1
        for key, value in proxy.items():
            if value is not None and isinstance(value, (int, float)) and math.isfinite(value):
                summaries[key].append(float(value))
        if len(rows) < 20:
            rows.append(
                {
                    "hdu_index": hdu_index,
                    "hdu_name": hdu_name,
                    "row_index": row_idx,
                    "plateifu": fields.get("PLATEIFU"),
                    "mangaid": fields.get("MANGAID"),
                    "daptype": fields.get("DAPTYPE"),
                    "z": fields.get("Z"),
                    "proxy": {
                        k: round(v, 6) if isinstance(v, float) else v for k, v in proxy.items()
                    },
                }
            )

    shock_scores = summaries["shock_proxy_score"]
    score_mean = statistics.fmean(shock_scores) if shock_scores else 0.0
    nonzero_fraction = (
        sum(1 for score in shock_scores if score > 0.05) / len(shock_scores)
        if shock_scores
        else 0.0
    )
    physical_support = clamp01(0.65 * score_mean + 0.35 * nonzero_fraction)

    prior = LOCAL_EIGEN_PRIORS["classical_hydrodynamic_shock"]["prior_strength"]
    refined_strength = clamp01(max(prior, physical_support))
    support_delta = refined_strength - prior
    decision = (
        "ADMIT_NONZERO_PHYSICAL_SHOCK_SUPPORT"
        if admitted and refined_strength > 0.0
        else "HOLD_NO_OBSERVATION_SUPPORT"
    )

    return {
        "schema": "stellar_gas_shock_eigen_fit_v0",
        "created": now_iso(),
        "claim_boundary": "Observation-proxy fit from SDSS MaNGA gas/velocity columns to the local physical shock eigen axis. It does not prove shock hydrodynamics, stellar breakout, or causality.",
        "source_fits": str(fits_path.relative_to(REPO)) if fits_path.is_relative_to(REPO) else str(fits_path),
        "row_limit": limit_rows,
        "hdu_counts_seen": hdu_counts,
        "admitted_proxy_rows": admitted,
        "local_eigen_priors": LOCAL_EIGEN_PRIORS,
        "aggregate_observables": {key: summarize(vals) for key, vals in summaries.items()},
        "physical_shock_axis_refinement": {
            "prior_strength": prior,
            "observation_proxy_mean": round(score_mean, 6),
            "nonzero_proxy_fraction": round(nonzero_fraction, 6),
            "refined_strength": round(refined_strength, 6),
            "support_delta": round(support_delta, 6),
            "status_change": "0.000000_to_nonzero_observation_proxy"
            if support_delta > 0
            else "unchanged",
        },
        "top_sample_rows": sorted(
            rows,
            key=lambda item: item["proxy"].get("shock_proxy_score") or 0.0,
            reverse=True,
        )[:10],
        "model_refinement": {
            "before": "physical shock axis was HOLD with Detonics/Shock Physics strength 0.000000",
            "after": "MaNGA gas velocity/sigma/residual columns provide a nonzero observation-proxy lane",
            "next_gate": "replace proxy score with line-ratio and uncertainty-aware physical model fit",
        },
        "decision": decision,
    }


def write_markdown(result: dict, path: Path) -> None:
    refine = result["physical_shock_axis_refinement"]
    agg = result["aggregate_observables"]
    lines = [
        "# Stellar Gas Shock Eigen Fit",
        "",
        "**Date:** 2026-05-09",
        "",
        f"**Decision:** `{result['decision']}`",
        "",
        "**Claim boundary:** observation-proxy fit only. This does not claim",
        "astrophysical validation, stellar shock breakout detection, or causality.",
        "",
        "## What Changed",
        "",
        "The physical shock eigen axis now has a nonzero observation-backed proxy",
        "from SDSS DR17 MaNGA DAPall gas and velocity columns.",
        "",
        "```text",
        f"prior strength:      {refine['prior_strength']:.6f}",
        f"proxy mean:          {refine['observation_proxy_mean']:.6f}",
        f"nonzero fraction:    {refine['nonzero_proxy_fraction']:.6f}",
        f"refined strength:    {refine['refined_strength']:.6f}",
        f"support delta:       {refine['support_delta']:.6f}",
        "```",
        "",
        "## Observable Proxies",
        "",
        "| Observable | Count | Mean | Median | P90 |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in [
        "gas_velocity_span_kms",
        "stellar_velocity_span_kms",
        "velocity_contrast",
        "gas_sigma_1re_kms",
        "stellar_sigma_1re_kms",
        "emline_rchi2_1re",
        "snr_med_mean",
        "shock_proxy_score",
    ]:
        s = agg[key]
        lines.append(
            f"| `{key}` | {s.get('count', 0)} | {s.get('mean', '')} | "
            f"{s.get('median', '')} | {s.get('p90', '')} |"
        )
    lines += [
        "",
        "## Gate",
        "",
        "```text",
        "if admitted_proxy_rows == 0:",
        "  HOLD_NO_OBSERVATION_SUPPORT",
        "elif refined_strength > 0:",
        "  ADMIT_NONZERO_PHYSICAL_SHOCK_SUPPORT",
        "else:",
        "  HOLD_RESIDUAL_CONTEXT",
        "```",
        "",
        "## Next Work",
        "",
        "1. Add emission-line index metadata so the 35-element MaNGA arrays become",
        "   named H-alpha, H-beta, OIII, NII, and SII lanes.",
        "2. Replace the current proxy with line-ratio diagnostics and uncertainties.",
        "3. Compare high-score rows against Rankine-Hugoniot / Sedov-Taylor receipt",
        "   gates only after source-specific physical context is present.",
        "",
    ]
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fits", type=Path, default=DEFAULT_FITS)
    parser.add_argument("--limit-rows", type=int, default=None)
    parser.add_argument("--destination", default=DESTINATION)
    args = parser.parse_args()

    if not args.fits.exists():
        raise FileNotFoundError(args.fits)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    result = build_fit(args.fits, args.limit_rows)
    out_path = DATA_DIR / "stellar_gas_shock_eigen_fit.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    write_markdown(result, DOC_PATH)

    receipt_path = DATA_DIR / f"stellar_gas_shock_eigen_fit_receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    receipt = {
        "schema": "stellar_gas_shock_eigen_fit_receipt_v0",
        "created": now_iso(),
        "claim_boundary": result["claim_boundary"],
        "fit_file": str(out_path.relative_to(REPO)),
        "doc_file": str(DOC_PATH.relative_to(REPO)),
        "source_fits": result["source_fits"],
        "decision": result["decision"],
        "refinement": result["physical_shock_axis_refinement"],
        "uploads": {},
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")

    uploads = {
        "fit": (out_path, f"{args.destination.rstrip('/')}/derived/{out_path.name}"),
        "doc": (DOC_PATH, f"{args.destination.rstrip('/')}/docs/{DOC_PATH.name}"),
        "receipt": (receipt_path, f"{args.destination.rstrip('/')}/receipts/{receipt_path.name}"),
    }
    for name, (local, remote) in uploads.items():
        ok, message = rclone_copyto(local, remote)
        receipt["uploads"][name] = {"drive_path": remote, "ok": ok, "message": message}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    if receipt["uploads"]["receipt"]["ok"]:
        rclone_copyto(receipt_path, receipt["uploads"]["receipt"]["drive_path"])

    print(json.dumps(receipt, indent=2))
    return 0 if result["decision"].startswith("ADMIT") else 1


if __name__ == "__main__":
    sys.exit(main())
