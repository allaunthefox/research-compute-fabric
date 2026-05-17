# Anti-FAMM Shadow Adversary

## Purpose

Anti-FAMM is the adversarial dual of FAMM. FAMM records residuals, scars, torsion, failed routes, and coarsening agents. Anti-FAMM asks where FAMM failed to see the scar, over-scarred a valid route, or allowed a witness packet to pass while the invariant actually failed.

```text
Anti-FAMM = the shadow map of FAMM blind spots.
```

## Nullspace attack

Let \(\Pi(X)\) be the current FAMM witness projection and \(T(X)\) the dangerous target behavior: vorticity stretching, invariant failure, pair-address aliasing, closure instability, proof drift, or hidden residual.

Anti-FAMM searches for:

```math
\eta\in\ker D\Pi_X
```

such that:

```math
DT_X[\eta]\ne0
```

Meaning: the perturbation is invisible to the witness packet, but it changes the dangerous thing.

## Shadow objective

```math
\mathcal A_{\mathrm{FAMM}}(X)
=
\sup_{\eta\in\ker D\Pi_X,\;\|\eta\|\le1}
\|DT_X[\eta]\|
```

If \(\mathcal A_{\mathrm{FAMM}}(X)>\Theta_A\), the witness packet is incomplete.

## Classification attacks

```text
False pass: FAMM says PASS, Anti-FAMM finds hidden residual or invariant failure.
False scar: FAMM says SCAR, Anti-FAMM finds the route was lawful under a missing witness.
```

## Stack placement

```text
candidate witness packet
→ FAMM classification
→ Anti-FAMM nullspace / shadow attack
→ Warden decision
→ promote / reopen / scar / coarsen / reject
```

## Project sentence

Anti-FAMM is the shadow adversary for FAMM: it searches for perturbations invisible to the witness packet but active in the dangerous target behavior, forcing the Warden to reject, scar, coarsen, or upgrade incomplete routes before promotion.
