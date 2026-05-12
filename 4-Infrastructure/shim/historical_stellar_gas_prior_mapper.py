#!/usr/bin/env python3
"""Map historical stellar-gas law families onto current observation support."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DATA_DIR = REPO / "shared-data/data/stellar_gas_observation"
LADDER = DATA_DIR / "historical_stellar_gas_model_ladder.json"
FIT = DATA_DIR / "stellar_gas_shock_eigen_fit.json"
LINE_DIAGNOSTICS = DATA_DIR / "stellar_gas_line_ratio_diagnostics.json"
OUT = DATA_DIR / "historical_stellar_gas_prior_map.json"
DOC = REPO / "6-Documentation/docs/historical_stellar_gas_model_ladder_2026-05-09.md"
DESTINATION = "Gdrive:topological_storage/research-stack/stellar-gas-observation/seed-2026-05-09"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def rclone_copyto(local: Path, remote: str) -> tuple[bool, str]:
    proc = run(["rclone", "copyto", str(local), remote, "--checksum"])
    message = (proc.stderr or proc.stdout).decode(errors="replace").strip()
    return proc.returncode == 0, message


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def hook_support(model: dict, fit: dict, line_diag: dict | None) -> tuple[float, list[str], list[str]]:
    agg = fit["aggregate_observables"]
    available = []
    missing = []
    line_ratio_support = 0.0
    shock_line_support = 0.0
    balmer_support = 0.0
    if line_diag:
        line_ratio_support = min(
            1.0,
            line_diag.get("valid_ratio_rows", 0) / max(1, line_diag.get("rows_seen", 1)),
        )
        shock_line_support = float(
            line_diag.get("shock_lier_support", {}).get("fractional_proxy_support", 0.0)
        )
        balmer_count = line_diag.get("aggregate_ratios", {}).get("balmer_decrement", {}).get("count", 0)
        balmer_support = min(1.0, balmer_count / max(1, line_diag.get("rows_seen", 1)))
    hook_to_observable = {
        "redshift_or_distance": ["snr_med_mean"],
        "position_context": ["snr_med_mean"],
        "gas_velocity_span": ["gas_velocity_span_kms"],
        "velocity_gradient_proxy": ["gas_velocity_span_kms", "velocity_contrast"],
        "velocity_dispersion": ["gas_sigma_1re_kms"],
        "gas_sigma": ["gas_sigma_1re_kms"],
        "line_width": ["gas_sigma_1re_kms"],
        "emission_line_flux": ["shock_proxy_score"],
        "line_ratio": ["__line_ratio_support__"],
        "equivalent_width": ["shock_proxy_score"],
        "surface_brightness": ["shock_proxy_score"],
        "attenuation": ["__balmer_decrement_support__"],
        "density_or_pressure_if_available": [],
        "pre_post_state_if_available": [],
        "temperature_or_electron_density": [],
        "stellar_context": ["stellar_sigma_1re_kms"],
        "mass_radius_temperature_if_available": [],
        "density": [],
        "shock_front_radius_time": [],
        "ambient_density": [],
        "magnetic_field": [],
        "outflow_velocity": ["gas_velocity_span_kms", "velocity_contrast"],
        "line_asymmetry": [],
        "optical_depth": [],
        "diffusion_time": [],
        "dynamical_time": [],
        "shock_velocity": ["gas_velocity_span_kms"],
    }
    scores = []
    for hook in model.get("observable_hooks", []):
        observables = hook_to_observable.get(hook, [])
        if not observables:
            missing.append(hook)
            continue
        present = False
        for obs in observables:
            if obs == "__line_ratio_support__":
                if line_ratio_support > 0:
                    available.append(f"{hook}->line_ratio_diagnostics")
                    present = True
                    # Blend general line-ratio coverage with shock-sensitive line-ratio support.
                    scores.append((line_ratio_support + shock_line_support) / 2)
                continue
            if obs == "__balmer_decrement_support__":
                if balmer_support > 0:
                    available.append(f"{hook}->balmer_decrement")
                    present = True
                    scores.append(balmer_support)
                continue
            summary = agg.get(obs, {})
            count = summary.get("count", 0)
            mean = summary.get("mean", 0.0)
            if count:
                available.append(f"{hook}->{obs}")
                present = True
                if obs == "shock_proxy_score":
                    scores.append(float(mean))
                else:
                    scores.append(min(1.0, float(count) / max(1, fit["admitted_proxy_rows"])))
        if not present:
            missing.append(hook)
    if not scores:
        return 0.0, available, missing
    return round(sum(scores) / len(scores), 6), available, missing


def decision_for(score: float, missing: list[str], gate: str) -> str:
    if score <= 0:
        return "HOLD_NO_CURRENT_OBSERVABLE"
    if missing or gate.startswith("HOLD"):
        return "HOLD_PARTIAL_PRIOR_SUPPORT"
    return "ADMIT_PRIOR_SUPPORT"


def build_map(ladder: dict, fit: dict, line_diag: dict | None) -> dict:
    mapped = []
    for model in ladder["models"]:
        score, available, missing = hook_support(model, fit, line_diag)
        mapped.append(
            {
                "id": model["id"],
                "period": model["period"],
                "names": model["names"],
                "law_family": model["law_family"],
                "equation_shape": model["equation_shape"],
                "local_axis": model["local_axis"],
                "current_gate": model["gate"],
                "current_observation_support": score,
                "available_hooks": available,
                "missing_hooks": missing,
                "decision": decision_for(score, missing, model["gate"]),
            }
        )
    admitted = [m for m in mapped if m["decision"] == "ADMIT_PRIOR_SUPPORT"]
    partial = [m for m in mapped if m["decision"] == "HOLD_PARTIAL_PRIOR_SUPPORT"]
    return {
        "schema": "historical_stellar_gas_prior_map_v0",
        "created": now_iso(),
        "claim_boundary": "Maps historical stellar-gas law families onto current MaNGA observation proxies. It ranks available support and missing gates; it does not validate the physical laws or infer causal shock events.",
        "source_ladder": str(LADDER.relative_to(REPO)),
        "source_fit": str(FIT.relative_to(REPO)),
        "source_line_diagnostics": str(LINE_DIAGNOSTICS.relative_to(REPO)) if line_diag else None,
        "fit_decision": fit["decision"],
        "fit_refinement": fit["physical_shock_axis_refinement"],
        "line_ratio_refinement": line_diag.get("shock_lier_support") if line_diag else None,
        "summary": {
            "model_count": len(mapped),
            "admitted_prior_support": len(admitted),
            "partial_prior_support": len(partial),
            "no_current_observable": len(mapped) - len(admitted) - len(partial),
        },
        "models": mapped,
        "decision": "ADMIT_HISTORICAL_PRIOR_SURFACE",
    }


def write_doc(result: dict, ladder: dict) -> None:
    lines = [
        "# Historical Stellar Gas Model Ladder",
        "",
        "**Date:** 2026-05-09",
        "",
        f"**Decision:** `{result['decision']}`",
        "",
        "**Claim boundary:** this is a historical prior and routing surface. It",
        "does not claim that the current MaNGA proxy fit validates any physical",
        "law or detects a specific shock event.",
        "",
        "## Why This Helps",
        "",
        "The stack now has a wide historical basis for stellar gas modeling rather",
        "than a single modern blob. Each law family gets a receipt role:",
        "",
        "```text",
        "historical law -> observable hook -> current column/proxy -> gate",
        "```",
        "",
        "## Current Support",
        "",
        f"- Models mapped: {result['summary']['model_count']}",
        f"- Admitted prior support: {result['summary']['admitted_prior_support']}",
        f"- Partial prior support: {result['summary']['partial_prior_support']}",
        f"- No current observable: {result['summary']['no_current_observable']}",
        "",
        "## Ladder",
        "",
        "| Period | Law family | Names | Support | Decision |",
        "|---|---|---|---:|---|",
    ]
    for model in result["models"]:
        lines.append(
            f"| {model['period']} | `{model['law_family']}` | "
            f"{', '.join(model['names'])} | {model['current_observation_support']:.6f} | "
            f"`{model['decision']}` |"
        )
    lines += [
        "",
        "## Source Notes",
        "",
    ]
    for source in ladder.get("source_notes", []):
        lines.append(f"- {source['title']}: `{source['url']}`")
    lines += [
        "",
        "## Next Gate",
        "",
        "The current support is strongest for velocity, dispersion, and named",
        "line-ratio proxy lanes. The next refinement is adding uncertainty,",
        "electron-density, temperature, and attenuation gates so Saha, radiative",
        "transfer, and shock-excitation support can move beyond proxy status.",
        "",
    ]
    DOC.write_text("\n".join(lines))


def main() -> int:
    ladder = load(LADDER)
    fit = load(FIT)
    line_diag = load(LINE_DIAGNOSTICS) if LINE_DIAGNOSTICS.exists() else None
    result = build_map(ladder, fit, line_diag)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    write_doc(result, ladder)
    receipt_path = DATA_DIR / f"historical_stellar_gas_prior_map_receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    receipt = {
        "schema": "historical_stellar_gas_prior_map_receipt_v0",
        "created": now_iso(),
        "claim_boundary": result["claim_boundary"],
        "ladder_file": str(LADDER.relative_to(REPO)),
        "prior_map_file": str(OUT.relative_to(REPO)),
        "doc_file": str(DOC.relative_to(REPO)),
        "summary": result["summary"],
        "decision": result["decision"],
        "uploads": {},
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    uploads = {
        "ladder": (LADDER, f"{DESTINATION}/derived/{LADDER.name}"),
        "prior_map": (OUT, f"{DESTINATION}/derived/{OUT.name}"),
        "doc": (DOC, f"{DESTINATION}/docs/{DOC.name}"),
        "receipt": (receipt_path, f"{DESTINATION}/receipts/{receipt_path.name}"),
    }
    for key, (local, remote) in uploads.items():
        ok, message = rclone_copyto(local, remote)
        receipt["uploads"][key] = {"drive_path": remote, "ok": ok, "message": message}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    if receipt["uploads"]["receipt"]["ok"]:
        rclone_copyto(receipt_path, receipt["uploads"]["receipt"]["drive_path"])
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
