# Photonic Witness-Grammar Implementation Note

**Project:** FNWH-Burgers Sovereign Research Stack  
**Component:** Photonic Witness-Grammar / Quandela Perceval Integration  
**Date:** 2026-05-02  
**Status:** Validated as spectral witness; proof-incomplete; hardware-constrained

---

## 1. Purpose

This note documents the engineering reason the photonic component is currently framed as a **spectral witness anchor** rather than as a full photonic compute engine.

The goal of the current photonic experiment is not to solve the nonlinear Burgers equation. The goal is to show that the finite spectral primitive used by the Burgers/NUVMAP stack can be represented as a physical optical sampling problem and that the observable scalar

\[
\Omega[u]
\]

can be empirically recovered from photon-counting statistics.

---

## 2. Minimal witness requirement

The minimal witness for the current primitive is a **single-photon probability distribution over three optical modes**.

The signal under test is:

\[
S(x)=\sin(x)+0.3\sin(2x)+0.1\sin(3x)
\]

The first three harmonic amplitudes are encoded into a 3-mode linear-optical circuit. The relevant observable is the recovered mode distribution, from which the scalar energy/complexity metric \(\Omega[u]\) is estimated.

For this witness layer, the required object is:

```text
spectral amplitudes
  → optical mode amplitudes
  → photon-count distribution
  → empirical Ω estimate
```

This does **not** require two-photon interference, entanglement, HOM effects, or a photonic implementation of the nonlinear PDE evolution.

---

## 3. Backend constraint

The Quandela cloud backend exposed during testing enforced a minimum of **two photons per state** for the relevant execution path.

That backend requirement is stronger than the mathematical requirement of the current witness.

In practice, photon-pair behavior was not filling/sampling fast enough for the desired iteration loop. The experiment therefore used the photonic layer as a **physical sampling witness** for the spectral primitive rather than as the primary compute engine.

This is an implementation constraint, not a failure of the witness grammar.

---

## 4. Result obtained

Using the Perceval SLOS simulator with 100,000 shots, the experiment recovered \(\Omega[u]\) within expected shot noise:

```text
Analytical Ω:   0.725000
Empirical Ω̂:   0.722794
Deviation:      0.904σ
Shots:          100,000
```

This validates the following bounded claim:

> A 3-mode linear-optical witness can physically sample the spectral primitive and recover the scalar observable \(\Omega[u]\) within expected finite-shot statistical error.

---

## 5. What this validates

The current photonic integration validates:

- the spectral primitive is representable as a 3-mode optical state;
- the relevant probability distribution can be sampled;
- \(\Omega[u]\) can be recovered empirically from photon-counting statistics;
- the witness grammar has a physical measurement model rather than being purely symbolic.

In stack terms:

```text
Photonic Witness-Grammar:
  VALIDATED AS EMPIRICAL SPECTRAL SAMPLING ANCHOR
```

---

## 6. What this does not validate

The current photonic integration does **not** prove:

- that linear optics solves the nonlinear Burgers equation;
- that \(\nu_{eff}(\Omega)>0\) globally;
- that \(\Omega[u]\) remains globally bounded;
- that the Burgers/NUVMAP system satisfies any Millennium-prize-adjacent theorem;
- that the setup demonstrates quantum advantage;
- that two-photon interference is required for the present scalar witness.

The correct boundary is:

> The photonic circuit samples the spectral observable. It does not act as a proof engine.

---

## 7. Relation to AVM

The AVM and photonic layers have different jobs.

```text
Photonic witness:
  physically samples or estimates Ω from spectral amplitudes

AVM:
  deterministically computes scalar laws from Ω
  e.g. ν_eff(Ω), q_eff(Ω)

Lean:
  proves the AVM bytecode equals the intended scalar laws

Python / Perceval:
  runs executable benchmarks and empirical witness tests
```

The coherent pipeline is therefore:

```text
spectral state
  → photonic estimate of Ω
  → AVM computation of ν_eff / q_eff
  → Lean theorem targets for correctness
```

---

## 8. Honest claim wording

Recommended repository/paper wording:

> The photonic witness grammar provides a physically realizable sampling representation of a finite spectral primitive. It empirically recovers the scalar observable \(\Omega[u]\) from photon-counting statistics within shot-noise tolerance. This supports the representability of the witness grammar but does not constitute a proof of nonlinear Burgers evolution, effective-viscosity positivity, global boundedness, or Navier–Stokes regularity.

Short status label:

```text
Validated prototype, bounded claims, formal closure pending.
```

---

## 9. Future extension: two-photon branch

Two-photon behavior should be treated as a future extension, not as a dependency of the current witness.

Future two-photon experiments may be useful for:

- HOM-style interference witnesses;
- correlation-sensitive spectral tests;
- mode-coupling diagnostics;
- higher-order witness grammars;
- hardware-specific benchmarking against classical simulation.

However, these are separate claims from the current 3-mode scalar \(\Omega[u]\) witness.

Recommended branch label:

```text
PhotonicWitnessGrammar.TwoPhotonCorrelation
Status: future extension
Dependency: not required for Ω scalar witness
```

---

## 10. Current final status

```text
Photonic spectral encoding:          works
Photon-count recovery of Ω:          works empirically
Perceval/SLOS simulation:            validated locally
Single-photon witness concept:       sufficient for current Ω primitive
Two-photon backend path:             constrained / future extension
Actual PDE solver:                   no
Formal Burgers proof:                no
```

Final summary:

> The photonic component works as a physical witness and sampling anchor for the spectral primitive. Photon-pair constraints limited the two-photon path, but the current \(\Omega[u]\) witness only requires recovered mode probabilities. The result is valid as hardware-anchored evidence for the witness grammar, not as a PDE proof.
