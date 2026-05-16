# FAMM Semantic Mass Math-Forest Plow

## Purpose

This note records the point where the project moved beyond the initial Semantic Mass Number concept.

The original concept treated Semantic Mass as an accounting scalar: a way to score load, inertia, cost, density, unresolved residue, or route weight.

The current architecture welds Semantic Mass directly into FAMM and turns it into a live routing field:

```text
Semantic Mass stream
→ FAMM route/scar/gate state
→ Z-domain recurrence
→ delta-memory carry
→ Hessian curvature receipt
→ residual seal / closure test
```

The goal is to stop rediscovering solved structure and instead use existing mathematical operators, proofs, algorithms, and physics solvers as route priors.

## Evidence from existing project work

The existing MOIM document already states that Mass-Numbers are the finite accounting profile that scores a routed object's weight, cost, inertia, density, or unresolved load. It also places Mass-Number under MOIM operationally and beside MOIM architecturally as a sibling profile inside GCL objects.

The existing superfluid semantic adapter already exports semantic state summaries such as mass_number, semantic_density, torsion, kinetic_pressure, basin_strength, receipt_coverage, and gate status. This gives the accelerator real input lanes rather than only theory.

The current Hessian-basis recompute makes HESSIAN_EIGEN the routing basis for FAMM layers: every layer becomes a curvature object with stiff invariant directions, flat compression gauges, saddle scars, and residual-seal receipts.

## New welded object

```math
\mathfrak M_{\mathrm{FMS}}(u,k)
=
A_{16}(u)
\otimes
\left[
\mu[k]
+
\Gamma_{\mathrm{FAMM}}(u)
+
H_\mu(z)
+
\mathcal C_H(u)
+
\epsilon_k
\right]
```

Where:

- `A16(u)` is the RFS-16384 address.
- `mu[k]` is the semantic mass sample.
- `Gamma_FAMM` is the route/scar/gate field.
- `H_mu(z)` is the Z-domain recurrence / transfer law.
- `C_H(u)` is the Hessian curvature receipt.
- `epsilon_k` is the residual seal.

## Search acceleration doctrine

```text
Never search from scratch if a solved route, pole, scar, closure, or eigendirection already exists.
```

The pipeline becomes:

```text
input object / route history
→ compute semantic mass stream μ[k]
→ fit Z-domain recurrence Hμ(z)
→ rank routes by mass × invariant overlap × scar penalty
→ classify local geometry with Hessian receipt
→ test closure if poles or residuals misbehave
→ seal bounded residuals
→ emit route receipt
```

## CFD Python / Navier-Stokes bridge

Lorena Barba's CFD Python ladder is useful because it gives a staged PDE forest:

```text
linear convection
→ nonlinear convection
→ diffusion
→ Burgers equation
→ Laplace / Poisson
→ cavity flow
→ channel flow
→ Navier-Stokes
```

FAMM should treat each stage as a semantic-mass stream rather than only as a numerical field.

For a 2D incompressible flow state, define lanes:

```math
\mu_{\mathrm{CFD}}[k]
=
w_u\|u_k\|
+
w_v\|v_k\|
+
w_p\|p_k\|
+
w_\omega\|\omega_k\|
+
w_d\|\nabla\cdot\mathbf u_k\|
+
w_r\|R_k\|
+
w_b\|B_k\|
```

Where:

- `u, v` are velocity components.
- `p` is pressure.
- `omega` is vorticity.
- `div u` is incompressibility violation.
- `R_k` is PDE residual.
- `B_k` is boundary-condition residual.

Then fit:

```math
M_{\mathrm{CFD}}(z)=\sum_{k\ge 0}\mu_{\mathrm{CFD}}[k]z^{-k}
```

and route by poles:

| Pole / residual behavior | Meaning | Route action |
|---|---|---|
| stable poles | solver state is contractive | carry recurrence |
| near-unit poles | long-memory/inertia | delta-memory carry |
| outside-ROC poles | instability or missing boundary | closure test / CFL check |
| high residual but bounded | lawful unresolved tail | seal residual |
| stiff Hessian direction | invariant/boundary constraint | protect / do not overpress |
| flat Hessian direction | gauge/compressible subspace | press / compress |

## BraiNCA bridge

BraiNCA's useful lesson is that local Moore-neighborhood updates are not enough when distributed coordination requires long-range connections and dynamic routing.

FAMM's ugly/profound version:

```text
do not update every neighbor equally;
route through semantic mass, invariant overlap, scar pressure, and curvature receipts.
```

A graph-cell update becomes:

```math
s_i[k+1]
=
f\left(
  s_i[k],
  \operatorname{TopK}_j[\mu_j[k]P(i\to j)],
  R_i[k]
\right)
```

Where:

```math
P(i\to j)
\propto
\exp[-\alpha d_{ij}-\beta\Omega_{ij}+\gamma I_{ij}-\eta C_{ij}]
```

## Implementation target

Add a runner that accepts:

```text
semantic mass lanes
route candidates
scar penalties
optional CFD residual streams
optional Hessian receipt
```

and emits:

```text
ranked routes
Z-domain recurrence
pole/ROC diagnosis
residual seal
closure recommendation
```

## Project sentence

FAMM Semantic Mass is now a math-forest plow: it uses solved operators, recurrence laws, curvature receipts, scars, and residual seals as routing priors so the system can move through dense mathematical terrain without rediscovering every branch from scratch.
