# FAMM Semantic Mass Route Plow Runner

## Purpose

This runner is the implementation step after the Semantic Mass Z-Domain Accelerator.

It accepts semantic-mass lanes, optional CFD-style residual streams, route candidates, and optional Hessian receipts. It emits a ranked route receipt.

## Pipeline

```text
semantic mass lanes
→ weighted mass stream μ[k]
→ AR/Z-domain recurrence
→ pole/ROC diagnosis
→ route ranking by mass × invariant overlap × scar penalty
→ residual seal / closure recommendation
→ receipt
```

## Command

```bash
python3 5-Applications/tools-scripts/famm/semantic_mass_route_plow.py \
  --config shared-data/examples/famm_semantic_mass_route_plow_config.example.json \
  --out shared-data/semantic-mass-plow/example_receipt.json
```

## Route equation

```math
P(i\to j)
\propto
\exp[-\alpha d_{ij}-\beta\Omega_{ij}+\gamma I_{ij}-\eta C_{ij}+m\mu_j]
```

## CFD usage

Feed solver lanes such as:

```text
u_norm
v_norm
pressure_norm
vorticity_norm
divergence_residual
pde_residual
boundary_residual
```

The runner does not solve Navier-Stokes. It ranks which solver route or boundary closure step deserves compute next.

## No-drift boundary

This is a computational routing witness. It accelerates the math forest. It does not replace exact proof, numerical validation, or PDE solver correctness checks.
