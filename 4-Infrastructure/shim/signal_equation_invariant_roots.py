#!/usr/bin/env python3
"""Derive invariant roots for accessible local signal equations.

This is a local synthesis pass over the Research Stack signal surface. It does
not claim a complete literature survey. It pulls the equations that are
available in the workspace signal compendium and executable audio-DSP code, then
normalizes each into an invariant root: the quantity, equivalence class, or
constraint that remains meaningful under admissible transforms.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "signal_equation_invariant_roots_receipt.json"
CURRICULUM_OUT = SHIM / "signal_equation_invariant_roots_curriculum.jsonl"
SUMMARY_OUT = SHIM / "signal_equation_invariant_roots_summary.md"

GENERATED_AT = "2026-05-08T00:00:00+00:00"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


INVARIANT_ROOTS: list[dict[str, Any]] = [
    {
        "id": "SIGROOT001_spectral_overlap",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: spectralOverlap sig1 sig2 = sum(sig1[i] * sig2[i])",
        "equation": "<s1,s2> = sum_i s1_i s2_i",
        "invariant_root": "inner-product pairing on aligned spectral coordinates",
        "admissible_transforms": "common bin permutation; orthonormal basis change when both signatures transform together",
        "compression_use": "route similarity, duplicate-island pruning, nearest repair template",
        "fpga_use": "DSP dot-product lane with accumulator and saturation guard",
    },
    {
        "id": "SIGROOT002_piecewise_merge",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: piecewiseMerge left right[i] = min(1.0, left[i] + right[i])",
        "equation": "merge_i = min(1, left_i + right_i)",
        "invariant_root": "bounded semilattice occupancy over [0,1]^n",
        "admissible_transforms": "coordinatewise monotone maps that preserve zero, one, and order",
        "compression_use": "safe feature union without unbounded sidecar growth",
        "fpga_use": "saturating add primitive",
    },
    {
        "id": "SIGROOT003_resonance_degeneracy",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: count(left[i] != 0 and right[i] != 0)",
        "equation": "deg(left,right) = |support(left) intersect support(right)|",
        "invariant_root": "support-intersection cardinality",
        "admissible_transforms": "positive amplitude scaling and common support-preserving permutation",
        "compression_use": "overlap score for tokenbook/feature collisions",
        "fpga_use": "bitmask AND plus popcount",
    },
    {
        "id": "SIGROOT004_wavefront_value",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: decay, phaseShift, oscillation, value",
        "equation": "value = (A - gamma*d) * osc(omega*d) for d <= v*t, else 0",
        "invariant_root": "retarded wavefront cone plus phase class modulo cycle",
        "admissible_transforms": "translations and metric-preserving coordinate changes",
        "compression_use": "event influence radius for local route activation",
        "fpga_use": "distance gate, phase LUT, envelope subtractor",
    },
    {
        "id": "SIGROOT005_signal_band_policy",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: quiet/active/stressed/extreme threshold bands",
        "equation": "band(x) = threshold_partition(x)",
        "invariant_root": "ordered threshold cell",
        "admissible_transforms": "monotone rescaling with transformed thresholds",
        "compression_use": "route budget scheduler",
        "fpga_use": "comparator ladder",
    },
    {
        "id": "SIGROOT006_acoustic_gradient",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: acoustic impedance as gradient magnitude |grad f|",
        "equation": "Z_acoustic ~ |grad f|",
        "invariant_root": "metric norm of field gradient",
        "admissible_transforms": "coordinate changes with explicit metric tensor",
        "compression_use": "manifold steepest-descent route proposal",
        "fpga_use": "finite-difference gradient and norm pipeline",
    },
    {
        "id": "SIGROOT007_fitness_entropy_compensation",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: f = f_max - alpha * H",
        "equation": "f + alpha*H = f_max",
        "invariant_root": "affine fitness-entropy conserved total",
        "admissible_transforms": "unit changes that transform alpha coherently",
        "compression_use": "semantic/fitness score must pay entropy cost",
        "fpga_use": "linear score lane with conserved budget comparator",
    },
    {
        "id": "SIGROOT008_gibbs_free_energy",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: DeltaG = DeltaH - T*DeltaS",
        "equation": "G = H - T*S",
        "invariant_root": "Legendre-transformed available-energy potential",
        "admissible_transforms": "thermodynamic coordinate changes preserving conjugate pair T,S",
        "compression_use": "available byte-gain after entropy/side-info cost",
        "fpga_use": "cost potential lane for thermal/energy-aware routing",
    },
    {
        "id": "SIGROOT009_affine_erasure_permutation",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: pi(i) = (offset + step*i) mod n",
        "equation": "pi(i) = a + s*i mod n",
        "invariant_root": "cycle structure determined by gcd(s,n)",
        "admissible_transforms": "offset translation and invertible modular scaling",
        "compression_use": "repair stream interleaving with deterministic owner",
        "fpga_use": "modular address generator",
    },
    {
        "id": "SIGROOT010_genomic_weight",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: genomicWeight ratio",
        "equation": "W = (rho + v + tau + sigma + q) / ((1+kappa^2)*(1+epsilon))",
        "invariant_root": "dimensionless normalized field-strength ratio",
        "admissible_transforms": "common scale-normalization of numerator terms",
        "compression_use": "adaptive erasure threshold",
        "fpga_use": "fixed-point ratio approximation",
    },
    {
        "id": "SIGROOT011_pbacs_phi_accumulator",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: phi_{t+1} = phi_t + 106070",
        "equation": "phi_{t+1} = phi_t + c mod 2^32",
        "invariant_root": "circle rotation orbit class",
        "admissible_transforms": "phase offset; modular conjugacy preserving increment",
        "compression_use": "deterministic phase owner for route symbols",
        "fpga_use": "free-running modular accumulator",
    },
    {
        "id": "SIGROOT012_pbacs_error_feedback",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: e_{t+1} = v_t + e_t - (b_t ? theta_t : 0)",
        "equation": "e_next = v + e - b*theta",
        "invariant_root": "bounded quantization residual",
        "admissible_transforms": "threshold-preserving fixed-point rescale",
        "compression_use": "exact residual lane for symbol decisions",
        "fpga_use": "sigma-delta style feedback cell",
    },
    {
        "id": "SIGROOT013_mutual_information_gain",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: MI(x) = baseline_bpb - actual_bpb",
        "equation": "MI = baseline_bpb - actual_bpb",
        "invariant_root": "byte-per-symbol improvement under one ratio schema",
        "admissible_transforms": "comparisons that keep baseline and actual schema identical",
        "compression_use": "route evidence coordinate",
        "fpga_use": "counter difference after codec run",
    },
    {
        "id": "SIGROOT014_weighted_mi_prediction",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: MI_pred weighted average",
        "equation": "MI_pred = sum_i w_i MI_i S_i / sum_i w_i S_i",
        "invariant_root": "barycentric coordinate in similarity-weighted evidence simplex",
        "admissible_transforms": "common positive scaling of all weights",
        "compression_use": "nearest-prior route prediction",
        "fpga_use": "weighted accumulator plus reciprocal approximation",
    },
    {
        "id": "SIGROOT015_surprise_metric",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: surprise = log(1 + |MI_actual - MI_predicted|)",
        "equation": "S = log(1 + |delta_MI|)",
        "invariant_root": "monotone function of absolute prediction residual",
        "admissible_transforms": "monotone reparameterization of residual magnitude",
        "compression_use": "route anomaly detector",
        "fpga_use": "absolute-delta threshold; log optional",
    },
    {
        "id": "SIGROOT016_structure_yield",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: rho(x) = MI(x) / (cost(x) + epsilon)",
        "equation": "rho = MI / (cost + eps)",
        "invariant_root": "information-per-cost efficiency ratio",
        "admissible_transforms": "unit changes preserving numerator/denominator interpretation",
        "compression_use": "candidate route priority",
        "fpga_use": "score-per-cycle allocator",
    },
    {
        "id": "SIGROOT017_weighted_feature_distance",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: weighted feature distance",
        "equation": "d(z1,z2) = sqrt(sum_i w_i*((z1_i-z2_i)/s_i)^2)",
        "invariant_root": "diagonal metric distance after scale normalization",
        "admissible_transforms": "coordinate rescaling absorbed into s_i and w_i",
        "compression_use": "route family clustering",
        "fpga_use": "scaled L2 distance pipeline",
    },
    {
        "id": "SIGROOT018_energy_gradient_waveform",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: amplitude=|grad E(t)|, frequency, phase",
        "equation": "wave_E = (|grad E|, omega_gradE, phi_gradE)",
        "invariant_root": "gradient magnitude and phase trajectory",
        "admissible_transforms": "metric-aware coordinate changes",
        "compression_use": "energy/cost-aware transform scheduling",
        "fpga_use": "gradient magnitude plus phase accumulator",
    },
    {
        "id": "SIGROOT019_shape_energy_coupling",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: C_SE = alpha * grad h * grad E",
        "equation": "C_SE = alpha <grad h, grad E>",
        "invariant_root": "metric inner product of shape and energy gradients",
        "admissible_transforms": "coordinate changes preserving the metric pairing",
        "compression_use": "align geometry witness only when it reduces route cost",
        "fpga_use": "dual-gradient dot-product lane",
    },
    {
        "id": "SIGROOT020_spectral_field_score",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: score = mass*massField + polarity*polarityField + spectralOverlap",
        "equation": "score = mM + pP + <s,F>",
        "invariant_root": "bilinear pairing between local state and field",
        "admissible_transforms": "paired basis changes that preserve the bilinear form",
        "compression_use": "local route-field compatibility score",
        "fpga_use": "three-term MAC lane",
    },
    {
        "id": "SIGROOT021_parabolic_j_score",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: J(k) = 32 - 0.5*(k-22)^2",
        "equation": "J(k) = 32 - 0.5*(k-22)^2",
        "invariant_root": "distance from resonant vertex k=22",
        "admissible_transforms": "translation to vertex coordinate u=k-22",
        "compression_use": "resonance-ranked candidate pruning",
        "fpga_use": "subtract-square-threshold circuit",
    },
    {
        "id": "SIGROOT022_cmyk_frequency_lattice",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: freq(ch,h)=baseFreq(ch)+deltaFreq*h",
        "equation": "f_ch(h) = base_ch + delta*h",
        "invariant_root": "channel-local affine frequency lattice coordinate h",
        "admissible_transforms": "affine frequency calibration preserving delta steps",
        "compression_use": "symbol carrier with exact inverse",
        "fpga_use": "base-plus-shift frequency synthesizer",
    },
    {
        "id": "SIGROOT023_rydberg_gap",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: nu_tilde = R_H*(1/n1^2 - 1/n2^2)",
        "equation": "nu_bar = R*(1/n1^2 - 1/n2^2)",
        "invariant_root": "reciprocal-square quantum gap",
        "admissible_transforms": "unit conversion between wavenumber, wavelength, frequency, and energy",
        "compression_use": "stable physical spectral basis index",
        "fpga_use": "small table of canonical spectral lines",
    },
    {
        "id": "SIGROOT024_lorentzian_resonance",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: strength = 1/(1+(Delta lambda)^2)",
        "equation": "L(delta) = 1/(1+delta^2)",
        "invariant_root": "squared detuning from spectral center",
        "admissible_transforms": "sign flip of detuning; normalized wavelength units",
        "compression_use": "nearest spectral-basis assignment",
        "fpga_use": "detuning-square LUT",
    },
    {
        "id": "SIGROOT025_kmer_base4_index",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: 3-mer index = b1*16 + b2*4 + b3",
        "equation": "idx = 16*b1 + 4*b2 + b3",
        "invariant_root": "base-4 coordinate of codon symbol",
        "admissible_transforms": "base relabeling with explicit inverse map",
        "compression_use": "fixed codon/tokenbook coordinate",
        "fpga_use": "two-bit shift-and-or indexer",
    },
    {
        "id": "SIGROOT026_dct2_basis",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: cos(pi/n*(j+0.5)*k)",
        "equation": "basis_{j,k} = cos(pi/n*(j+1/2)*k)",
        "invariant_root": "orthogonal cosine projection coefficient",
        "admissible_transforms": "orthogonal transforms preserving coefficient energy",
        "compression_use": "spectral coefficient compaction",
        "fpga_use": "fixed cosine basis or LUT butterfly",
    },
    {
        "id": "SIGROOT027_qpsk_phase_class",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: QPSK phases 0,90,180,270",
        "equation": "phase in Z_4",
        "invariant_root": "phase class modulo pi/2",
        "admissible_transforms": "global phase rotation with receiver correction",
        "compression_use": "2-bit symbol carrier",
        "fpga_use": "quadrant decoder",
    },
    {
        "id": "SIGROOT028_qam16_constellation",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: 4 amplitudes x 4 phases",
        "equation": "symbol = (a in A4, phase in Z4)",
        "invariant_root": "finite amplitude-phase lattice point",
        "admissible_transforms": "affine constellation calibration with preserved decision cells",
        "compression_use": "4-bit symbol carrier / QAM transfer metaphor",
        "fpga_use": "amplitude slicer plus quadrant decoder",
    },
    {
        "id": "SIGROOT029_dmt_subcarrier_quotient",
        "source": "SIGNAL_THEORY_COMPENDIUM.md: phase_out=base_phase+offset_i, demod=phase_in-offset_i",
        "equation": "phase_base = phase_out - offset_i mod cycle",
        "invariant_root": "phase quotient after subtracting subcarrier offset",
        "admissible_transforms": "subcarrier permutation with receipted offset table",
        "compression_use": "parallel lane carrier with exact demodulation",
        "fpga_use": "per-lane phase subtractor",
    },
    {
        "id": "SIGROOT030_hann_window_fft_energy",
        "source": "5-Applications/audio-dsp/src/core/surface.rs: Hann window, FFT, bin energy",
        "equation": "E_bin = avg_{k in bin} |FFT(window*x)_k|",
        "invariant_root": "windowed spectral-energy distribution",
        "admissible_transforms": "time shift up to phase; amplitude normalization when max-normalized",
        "compression_use": "audio/signal route feature vector",
        "fpga_use": "window multiply, FFT, magnitude, bin accumulator",
    },
    {
        "id": "SIGROOT031_transient_features",
        "source": "5-Applications/audio-dsp/src/core/surface.rs: attack, decay, zcr, crest",
        "equation": "transient = (max dx+, max dx-, zero_crossings/n, peak/rms)",
        "invariant_root": "edge/impulse morphology of the signal chunk",
        "admissible_transforms": "time-local scaling with normalized crest and ZCR preserved",
        "compression_use": "decide raw vs spectral vs hybrid route",
        "fpga_use": "delta extrema, sign-change counter, RMS/peak lane",
    },
    {
        "id": "SIGROOT032_predictability_autocorrelation",
        "source": "5-Applications/audio-dsp/src/core/surface.rs: predictability via autocorrelation",
        "equation": "pred = 0.5*(corr(x_t, x_{t-1}) + 1)",
        "invariant_root": "normalized temporal correlation",
        "admissible_transforms": "affine amplitude scaling removed by mean/variance normalization",
        "compression_use": "predictor suitability signal",
        "fpga_use": "sliding dot product and norm lane",
    },
    {
        "id": "SIGROOT033_cosine_similarity",
        "source": "5-Applications/audio-dsp/src/core/surface.rs: dot/(norm_a*norm_b)",
        "equation": "cos(theta)=<a,b>/(||a|| ||b||)",
        "invariant_root": "projective direction on spectral feature sphere",
        "admissible_transforms": "positive scaling of either vector",
        "compression_use": "chunk reuse / skip decision",
        "fpga_use": "dot product and reciprocal norm threshold",
    },
]


def build_receipt() -> dict[str, Any]:
    clusters: dict[str, int] = {}
    for row in INVARIANT_ROOTS:
        cluster = row["id"].split("_", 1)[1].rsplit("_", 1)[0]
        clusters[cluster] = clusters.get(cluster, 0) + 1
    receipt: dict[str, Any] = {
        "schema": "signal_equation_invariant_roots_v1",
        "generated_at": GENERATED_AT,
        "source_scope": [
            "SIGNAL_THEORY_COMPENDIUM.md",
            "5-Applications/audio-dsp/src/core/surface.rs",
            "5-Applications/audio-dsp/src/core/features.rs",
        ],
        "claim_boundary": (
            "These are invariant roots for accessible local signal equations. "
            "They are route/control priors and hardware design handles, not "
            "external physics proof or compression proof without exact byte receipts."
        ),
        "root_count": len(INVARIANT_ROOTS),
        "invariant_roots": INVARIANT_ROOTS,
        "derived_unifying_root": {
            "equation": "SignalRoute = (coordinate, invariant_root, admissible_transform, receipt_barrier)",
            "meaning": (
                "Every accessible signal equation reduces to a coordinate map plus an "
                "invariant root. The invariant root says what can survive rescaling, "
                "basis changes, phase shifts, lane permutation, or compression-route "
                "projection. Promotion still requires a receipt barrier."
            ),
        },
        "hutter_mapping": {
            "i_axis": "measured byte mass and lower bounds",
            "q_axis": "exactness roots: hash, Merkle receipt, NaN0 false, route-key closure",
            "promotion": "only when a route lies on the exactness locus and below incumbent byte level",
        },
        "fpga_mapping": {
            "common_primitives": [
                "dot_product",
                "saturating_add",
                "popcount",
                "phase_accumulator",
                "threshold_ladder",
                "modular_address_generator",
                "gradient_norm",
                "fft_bin_accumulator",
                "digest_lane",
            ],
            "barrier": "commit or source-release only after independent digest/check lane passes",
        },
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    lines = []
    for row in receipt["invariant_roots"]:
        lines.append(stable_json({
            "task": "derive_signal_invariant_root",
            "root_id": row["id"],
            "prompt": f"Derive the invariant root for {row['equation']}.",
            "completion": (
                f"Invariant root: {row['invariant_root']}. "
                f"Admissible transforms: {row['admissible_transforms']}."
            ),
        }))
    CURRICULUM_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(receipt: dict[str, Any]) -> None:
    lines = [
        "# Signal Equation Invariant Roots",
        "",
        receipt["claim_boundary"],
        "",
        f"Root count: {receipt['root_count']}",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        "## Unifying Root",
        "",
        "```text",
        receipt["derived_unifying_root"]["equation"],
        "```",
        "",
        receipt["derived_unifying_root"]["meaning"],
        "",
        "## Roots",
        "",
    ]
    for row in receipt["invariant_roots"]:
        lines.extend([
            f"### {row['id']}",
            "",
            f"- Equation: `{row['equation']}`",
            f"- Invariant root: {row['invariant_root']}",
            f"- Admissible transforms: {row['admissible_transforms']}",
            f"- Compression use: {row['compression_use']}",
            f"- FPGA use: {row['fpga_use']}",
            "",
        ])
    SUMMARY_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    write_curriculum(receipt)
    write_summary(receipt)
    print(json.dumps(
        {
            "receipt": rel(OUT),
            "curriculum": rel(CURRICULUM_OUT),
            "summary": rel(SUMMARY_OUT),
            "receipt_hash": receipt["receipt_hash"],
            "root_count": receipt["root_count"],
        },
        indent=2,
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
