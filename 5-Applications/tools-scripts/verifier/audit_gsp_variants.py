#!/usr/bin/env python3
"""
audit_gsp_variants.py
=====================

Run every GSP closure backend against the burgers_verifier gate suite.

Wraps each backend in `5-Applications/scripts/gsp/backends.py` and
`5-Applications/scripts/gsp/perceval_backend.py` as a `closure_fn(t, a, ν₀)`
of the form

    ν_eff = ν₀ · (1 + β · Ω(a))

per `BurgersHarmonicPeelingVerification.md`. The verifier evaluates each
candidate against:

    G1  Cole-Hopf or pseudo-spectral cosim     (ν=0.01 → pseudo-spectral)
    G2  energy dissipation property             (ν_eff > 0  ⇒  dE/dt ≤ 0)
    G4  ν → ∞ heat-equation limit               (sanity in stiff regime)

Writes a comparison table + JSON bundle. The result is the
*verifier-evaluated* ranking, independent of any agent text.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
# Import GSP backends as a package so the relative import in perceval_backend.py works.
sys.path.insert(0, str(REPO / "5-Applications" / "scripts"))
sys.path.insert(0, str(REPO / "5-Applications" / "tools-scripts" / "verifier"))

from gsp.backends import (  # noqa: E402
    ClassicalHeuristicBackend,
    EddyViscosityROMBackend,
    LearnedClosureBaselineBackend,
    SoftwareTriangleBackend,
)
from gsp.perceval_backend import PercevalGeometryShaverBackend  # noqa: E402

# Verifier.
from burgers_verifier import (  # noqa: E402
    DEFAULT_AMPS,
    PseudoSpectralReference,
    closure_constant,
    gate_g1_cole_hopf_cosim,
    gate_g2_energy_dissipation,
    gate_g4_heat_equation_limit,
    integrate_triad,
)
from run_dag import RunDAG  # noqa: E402

Q16_ONE = 1 << 16
VERIFIER_PATH = REPO / "5-Applications" / "tools-scripts" / "verifier" / "burgers_verifier.py"
AUDIT_PATH = REPO / "5-Applications" / "tools-scripts" / "verifier" / "audit_gsp_variants.py"
RUN_DAG_PATH = REPO / "5-Applications" / "tools-scripts" / "verifier" / "run_dag.py"


# =============================================================================
# Backend → closure_fn adapter
# =============================================================================

def make_closure_fn(backend, beta: float = 0.5, n_samples: int = 256, seed: int = 42,
                    memoize: bool = True, memo_decimals: int = 5,
                    formula: str = "additive"):
    """Wrap a VirtualSubstrateBackend as a closure_fn(t, a, ν₀) → ν_eff.

    `formula` selects the ν_eff formula:
      - "additive"       : ν_eff = ν₀ + β · Ω         (matches runner.py:135)
      - "multiplicative" : ν_eff = ν₀ · (1 + β · Ω)   (matches the spec doc and
                                                       the upstream Perceval
                                                       repro from 2026-05-03)

    The additive form caused 25× ν_eff inflation for variant D at ν₀=0.01,
    Ω≈0.5 — a wrapper-side bug, not a Perceval-side bug. This option lets the
    audit measure both forms head-to-head against the same gates.

    `memoize` caches Ω by quantised state-tuple — RK45 evaluates the RHS at
    many sub-step stages with similar a, and each photonic-sampler call costs
    real time. The cache key is rounded to `memo_decimals` decimal places (5 ≈
    1e-5, well below shot-noise resolution for the witness).
    """
    cache: dict[tuple, float] = {}

    if formula == "additive":
        def combine(nu0, omega): return nu0 + beta * omega
    elif formula == "multiplicative":
        def combine(nu0, omega): return nu0 * (1.0 + beta * omega)
    else:
        raise ValueError(f"unknown formula {formula!r}; use 'additive' or 'multiplicative'")

    def closure_fn(t, a_float, nu0):
        if memoize:
            key = tuple(round(x, memo_decimals) for x in a_float)
            if key in cache:
                return combine(nu0, cache[key])
        a_q16 = tuple(int(round(x * Q16_ONE)) for x in a_float)
        theta = backend.encode(a_q16)
        substrate = backend.program(theta)
        hist = backend.sample(substrate, n_samples, seed)
        omega_q16 = backend.witness(hist)
        omega_float = omega_q16 / Q16_ONE
        if memoize:
            cache[key] = omega_float
        return combine(nu0, omega_float)
    return closure_fn


# =============================================================================
# The variants (matches the conversation's A–G nomenclature)
# =============================================================================

VARIANTS = {
    # Variant A — no viscosity at all. Hard limit case.
    "A_no_viscosity": (lambda t, a, nu0: 0.0, "ν_eff = 0  (no closure, no diffusion)"),
    # Variant B — fixed viscosity, no closure correction. The honest baseline.
    "B_constant_baseline": (closure_constant, "ν_eff = ν₀  (constant; the bar to beat)"),
    # Variant C — classical heuristic.
    "C_classical_heuristic": (
        make_closure_fn(ClassicalHeuristicBackend(c1=0.1, c2=0.1, c3=0.0)),
        "ν_eff = ν₀ + 0.5·(0.1|a₁a₃| + 0.1|a₂a₃|)"
    ),
    # Variant D — Perceval photonic witness (M=6, 3-photon Fock input).
    # n_samples=64 keeps shot noise reasonable while making the RK45-driven
    # repeat-call burden tractable; memoization in make_closure_fn dedupes
    # within-step state-tuple repeats from the integrator.
    "D_perceval_local": (
        make_closure_fn(PercevalGeometryShaverBackend(M=6, exhaust_modes=(3, 4, 5)),
                        n_samples=64),
        "ν_eff = ν₀ + 0.5·Ω_Q,  Ω_Q = Σ exhaust-mode photon-counts (M=6, 3-photon Fock)"
    ),
    # Variant F — learned-closure baseline (mock LSTM/NODE).
    "F_learned_closure": (
        make_closure_fn(LearnedClosureBaselineBackend()),
        "mock LSTM/NODE: nonlinear fn of recent 3-step history"
    ),
    # Variant G — eddy-viscosity ROM (Smagorinsky-style).
    "G_eddy_viscosity": (
        make_closure_fn(EddyViscosityROMBackend(c_smag=0.1)),
        "ν_eff = ν₀ + 0.5·0.1·|a₃|  (Smagorinsky-style)"
    ),
    # Variant null — SoftwareTriangleBackend explicit (Ω=0, identical to B).
    "null_software_triangle": (
        make_closure_fn(SoftwareTriangleBackend()),
        "Ω = 0 always  (identical to B in effect; sanity check on adapter)"
    ),
    # ===== Multiplicative-formula variants  (ν_eff = ν₀·(1 + β·Ω))  =====
    # Spec-aligned form. Differs from the runner.py:135 additive form;
    # added per the 2026-05-03 Perceval repro analysis to test whether the
    # over-damping localises to the additive formula vs the photonic substrate.
    "C2_classical_multiplicative": (
        make_closure_fn(ClassicalHeuristicBackend(c1=0.1, c2=0.1, c3=0.0),
                        formula="multiplicative"),
        "ν_eff = ν₀·(1 + 0.5·(0.1|a₁a₃| + 0.1|a₂a₃|))  (multiplicative)"
    ),
    "D2_perceval_multiplicative": (
        make_closure_fn(PercevalGeometryShaverBackend(M=6, exhaust_modes=(3, 4, 5)),
                        n_samples=64, formula="multiplicative"),
        "ν_eff = ν₀·(1 + 0.5·Ω_Q)  (multiplicative; per spec + repro)"
    ),
    "F2_learned_multiplicative": (
        make_closure_fn(LearnedClosureBaselineBackend(), formula="multiplicative"),
        "mock LSTM/NODE, multiplicative ν_eff"
    ),
    "G2_eddy_multiplicative": (
        make_closure_fn(EddyViscosityROMBackend(c_smag=0.1), formula="multiplicative"),
        "ν_eff = ν₀·(1 + 0.5·0.1·|a₃|)  (Smagorinsky, multiplicative)"
    ),
}


# =============================================================================
# Run
# =============================================================================

def _build_variant_dag(name: str, desc: str, run, g1, g2, g4, ref,
                       nu0: float, t_final: float, n_eval: int, beta: float,
                       dag_dir: Path) -> tuple[str, Path]:
    """Build a per-variant Merkle DAG of inputs → reference → integrate → gates → verdict."""
    dag = RunDAG(
        run_type=f"gsp_variant_audit:{name}",
        code_paths=[VERIFIER_PATH, AUDIT_PATH, RUN_DAG_PATH],
    )
    # Inputs
    dag.add_input("input.amps", list(DEFAULT_AMPS))
    dag.add_input("input.nu0", nu0)
    dag.add_input("input.t_final", t_final)
    dag.add_input("input.n_eval", n_eval)
    dag.add_input("input.beta", beta)
    dag.add_input("input.closure_name", name)
    dag.add_input("input.closure_description", desc)

    # Reference (independent of closure — same for all variants but recorded per-DAG)
    dag.add_compute(
        "compute.reference",
        function="PseudoSpectralReference",
        parents=["input.amps", "input.nu0"],
        output_summary={"type": "PseudoSpectralReference", "N": ref.N, "dt": ref.dt},
    )
    # Integration of the candidate closure
    dag.add_compute(
        "compute.integrate_triad",
        function="solve_ivp(triad_rhs_with_closure)",
        parents=["input.amps", "input.nu0", "input.t_final", "input.n_eval",
                 "input.beta", "input.closure_name"],
        output_summary={
            "n_steps": int(run.t.size),
            "a_final": run.a[-1].tolist(),
            "energy_initial": float(run.energy[0]),
            "energy_final": float(run.energy[-1]),
            "nu_eff_min": float(run.nu_eff.min()),
            "nu_eff_max": float(run.nu_eff.max()),
        },
    )
    # Heat-equation-limit run (separate solve at large ν)
    dag.add_compute(
        "compute.heat_limit_run",
        function="integrate_triad(closure, nu=50, t∈[0,0.05])",
        parents=["input.closure_name"],
        output_summary={"nu_large": 50.0, "t_span": [0.0, 0.05]},
    )
    # Gates
    dag.add_gate(
        "gate.G1_reference_cosim",
        function="gate_g1_cole_hopf_cosim",
        parents=["compute.integrate_triad", "compute.reference"],
        result={"passes": g1.passes, "metric": g1.metric, "threshold": g1.threshold,
                "note": g1.note, "detail": g1.detail},
    )
    dag.add_gate(
        "gate.G2_energy_dissipation",
        function="gate_g2_energy_dissipation",
        parents=["compute.integrate_triad"],
        result={"passes": g2.passes, "metric": g2.metric, "threshold": g2.threshold,
                "note": g2.note, "detail": g2.detail},
    )
    dag.add_gate(
        "gate.G4_heat_equation_limit",
        function="gate_g4_heat_equation_limit",
        parents=["compute.heat_limit_run"],
        result={"passes": g4.passes, "metric": g4.metric, "threshold": g4.threshold,
                "note": g4.note, "detail": g4.detail},
    )
    dag.add_verdict("verdict",
                    gate_ids=["gate.G1_reference_cosim",
                              "gate.G2_energy_dissipation",
                              "gate.G4_heat_equation_limit"])

    out_path = dag_dir / f"variant_{name}.dag.json"
    dag.emit(out_path)
    return dag.merkle_root(), out_path


def audit(nu0: float = 0.01, t_final: float = 2.0, n_eval: int = 101,
          beta: float = 0.5) -> dict:
    print("=" * 80)
    print(f"GSP VARIANT AUDIT — verifier-grounded   (ν₀={nu0}, t_final={t_final})")
    print("=" * 80)
    print("reference: PseudoSpectralReference (validated by G5 vs Cole-Hopf at ν=0.05)")
    print()

    ref = PseudoSpectralReference(DEFAULT_AMPS, nu0, dt=5e-4)
    print(f"reference resolution: N={ref.N}, dt={ref.dt}")
    print()

    dag_dir = REPO / "shared-data" / "artifacts" / "burgers_verifier" / "dag"
    dag_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'variant':<26} {'G1 max-rel':>12} {'G2 dissip.':>12} {'G4 heat lim':>12} "
          f"{'gates':>6}  {'merkle_root':<20}")
    print("-" * 100)

    results: dict[str, dict] = {}
    for name, (closure, desc) in VARIANTS.items():
        try:
            run = integrate_triad(closure, nu0, t_span=(0.0, t_final), n_eval=n_eval)
            g1 = gate_g1_cole_hopf_cosim(run, ref)
            g2 = gate_g2_energy_dissipation(run)
            g4 = gate_g4_heat_equation_limit(closure)
            n_passed = sum([g1.passes, g2.passes, g4.passes])

            merkle_root, dag_path = _build_variant_dag(
                name, desc, run, g1, g2, g4, ref, nu0, t_final, n_eval, beta, dag_dir
            )

            results[name] = {
                "description": desc,
                "G1": asdict(g1),
                "G2": asdict(g2),
                "G4": asdict(g4),
                "gates_passed": n_passed,
                "gates_total": 3,
                "dag_path": str(dag_path.relative_to(REPO)),
                "dag_merkle_root": merkle_root,
            }

            print(f"{name:<26} {g1.metric:>12.4f} "
                  f"{g2.metric:>12.2e} "
                  f"{g4.metric:>12.4f} "
                  f"{n_passed:>4}/3  {merkle_root[:20]}…")
        except Exception as exc:
            print(f"{name:<26} ERROR: {type(exc).__name__}: {exc}")
            results[name] = {"description": desc, "exception": f"{type(exc).__name__}: {exc}"}

    # Ranking by G1 (the primary closure-quality metric).
    ranked = sorted(
        [(n, r) for n, r in results.items() if "G1" in r],
        key=lambda kv: kv[1]["G1"]["metric"]
    )

    print()
    print("ranking by G1 (Cole-Hopf/pseudo-spectral cosim, lower is better):")
    print(f"{'rank':<6} {'variant':<26} {'G1 max-rel':>12}  description")
    print("-" * 100)
    for i, (name, r) in enumerate(ranked, 1):
        marker = "  ← best" if i == 1 else "  ← worst" if i == len(ranked) else ""
        print(f"{i:<6} {name:<26} {r['G1']['metric']:>12.4f}  {r['description']}{marker}")

    # Master DAG aggregating per-variant verdicts.
    master = RunDAG(run_type="gsp_audit_master",
                    code_paths=[VERIFIER_PATH, AUDIT_PATH, RUN_DAG_PATH])
    master.add_input("input.audit_config",
                     {"nu0": nu0, "t_final": t_final, "n_eval": n_eval,
                      "beta": beta, "amps": list(DEFAULT_AMPS)})
    master.add_input("input.variants", list(VARIANTS.keys()))
    # One compute node per variant (records merkle root from sub-DAG)
    variant_node_ids: list[str] = []
    for name, r in results.items():
        if "exception" in r:
            continue
        nid = f"variant.{name}"
        master.add_compute(
            nid,
            function="audit_variant",
            parents=["input.audit_config", "input.variants"],
            output_summary={
                "G1_metric": r["G1"]["metric"],
                "G2_passes": r["G2"]["passes"],
                "G4_passes": r["G4"]["passes"],
                "gates_passed": r["gates_passed"],
                "child_dag_path": r["dag_path"],
                "child_dag_merkle_root": r["dag_merkle_root"],
            },
        )
        # Synthetic gate node so the verdict sees pass-state per variant
        master.add_gate(
            f"gate.{name}_meets_baseline",
            function="meets_constant_baseline_G1",
            parents=[nid],
            result={"passes": r["G1"]["metric"] < results.get("B_constant_baseline", {})
                              .get("G1", {}).get("metric", float("inf"))},
        )
        variant_node_ids.append(f"gate.{name}_meets_baseline")

    if variant_node_ids:
        master.add_verdict("verdict.master", gate_ids=variant_node_ids)

    master_path = dag_dir / "audit_master.dag.json"
    master.emit(master_path)
    print(f"\nmaster DAG: {master_path.relative_to(REPO)}  merkle_root={master.merkle_root()[:30]}…")

    return {
        "nu0": nu0, "t_final": t_final, "n_eval": n_eval,
        "amps": DEFAULT_AMPS,
        "reference_type": "PseudoSpectralReference",
        "reference_N": ref.N,
        "reference_dt": ref.dt,
        "beta": beta,
        "variants": results,
        "ranking_by_G1": [n for n, _ in ranked],
        "dag_dir": str(dag_dir.relative_to(REPO)),
        "master_dag_path": str(master_path.relative_to(REPO)),
        "master_dag_merkle_root": master.merkle_root(),
    }


def main():
    out_dir = REPO / "shared-data" / "artifacts" / "burgers_verifier"
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle = audit(nu0=0.01, t_final=2.0, n_eval=101)
    out = out_dir / "audit_gsp_variants.json"
    out.write_text(json.dumps(bundle, indent=2, default=str))
    print(f"\nwrote: {out}")


if __name__ == "__main__":
    main()
