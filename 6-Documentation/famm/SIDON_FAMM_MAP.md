# Sidon FAMM Map

## Purpose

Load the full Sidon thread into the FAMM map.

This document consolidates the Sidon work into one operational map:

```text
classical Sidon set
→ pair-sum gate
→ candidate-addition receipt
→ collision scar
→ physics-native path/collision packet
→ quaternion/phase anti-alias gate
→ two-layer kinetic/Sidon flow
→ Theodorus capacity shell
→ Semantic Mass route pressure
→ NUVMAP Delta-DAG node
→ Builder-Judge-Warden cleanup
→ exact verifier receipt
```

## Core Sidon gate

```math
G_{\mathrm{Sidon}}(A)=1
\iff
\forall a,b,c,d\in A,\quad
a+b=c+d\Rightarrow \{a,b\}=\{c,d\}
```

Equivalent map:

```math
\pi:\{(i,j):i\le j\}\to \mathbb Z,
\qquad
\pi(i,j)=a_i+a_j
```

Sidon means:

```math
\pi\ \mathrm{is\ injective}
```

## Candidate-addition gate

Given:

```math
S(A)=\{a_i+a_j:i\le j\}
```

For candidate `x`:

```math
S_x=\{x+a:a\in A\}\cup\{2x\}
```

Accept iff:

```math
S_x\cap S(A)=\varnothing
```

Otherwise:

```text
reject candidate
write Sidon collision scar
route failure to coarsening / nogood cache
```

## FAMM object

```math
\mathfrak C_{\mathrm{SidonMap}}
=
A_{16}(u_{\mathrm{sidon}})
\otimes
[
\Sigma_A
+
\Sigma_{2A}
+
\Sigma_{\mathrm{flow}}
+
\Sigma_{\mathrm{phase}}
+
\Sigma_{\mathrm{collision}}
+
\Sigma_{\mathrm{scar}}
+
\Sigma_{\sqrt N}
+
\Sigma_{\mathrm{receipt}}
]
```

## Semantic Mass lanes

```math
\mu_{\mathrm{Sidon}}[k]
=
w_c C_k
+
w_e E^+_k
+
w_\Omega \Omega_k
+
w_\theta \Delta\theta_k
+
w_q Q_k
+
w_i I_k
+
w_r R_k
```

Where:

| Lane | Meaning |
|---|---|
| `C_k` | nontrivial collision count |
| `E⁺_k` | additive energy |
| `Ω_k` | FAMM scar burden |
| `Δθ_k` | phase/chirality mismatch |
| `Q_k` | quaternion/phase quality |
| `I_k` | invariant overlap |
| `R_k` | residual / unresolved tail |

## Scar equation

```math
\Omega_{\mathrm{Sidon}}(A)
=
E_+(A)-(2|A|^2-|A|)
```

A valid Sidon set has:

```math
\Omega_{\mathrm{Sidon}}(A)=0
```

## Theodorus capacity prior

For finite Sidon search inside `[1,N]`, use:

```math
r_N=\sqrt N
```

as a capacity shell / density pressure prior.

```text
N = address/value budget
sqrt(N) = capacity shell
|A| = occupied independent marks
sqrt(N)-|A| = remaining admissible capacity pressure
```

This is not itself proof of maximality. It is a routing prior.

## Two-layer kinetic/Sidon mapping

```text
Layer K: kinetic standing-wave field
Layer S: Sidon relational address field
K → S: quantize pairwise kinetic relations into signatures
S → K: feed alias-free relational structure back into kinetic update
```

The Sidon layer is not static. It flows between layers:

```text
kinetic state
→ pairwise kinetic relation
→ Sidon signature
→ anti-aliasing gate
→ feedback into kinetic update
```

## Quaternion / phase Sidon mapping

Classical Sidon:

```text
a + b = c + d ⇒ {a,b} = {c,d}
```

Quaternionic / phase-lattice generalization:

```text
σ(i,j)=σ(k,l) ⇒ {i,j}={k,l}
```

where:

```text
σ(i,j) = encoded pairwise relative phase / interaction signature
```

## Physics-native Sidon packets

Pair sums become path packets:

```text
SidonPathPacket = {
  pair_id,
  source_i,
  source_j,
  sum_address,
  source_history_hash,
  additive_phase_q16,
  temporal_shear_q16,
  collision_energy_q16,
  valid_trivial_symmetry,
  receipt_hash
}
```

Nontrivial repeated sums become collision packets:

```text
SidonCollisionPacket = {
  collision_id,
  sum_address,
  pair_a,
  pair_b,
  trivial_collision_bool,
  additive_shear_q16,
  temporal_shear_q16,
  ignition_score_q16,
  underverse_class,
  warden_status,
  receipt_hash
}
```

## Coarsening-agent rule

Wrong Sidon candidates are useful.

```text
nontrivial repeated sum
→ collision scar
→ NUVMAP coarse basin
→ downweight future fine search
→ reopen only if new evidence changes the boundary
```

So a failed Sidon extension becomes a reusable negative topology witness.

## Builder-Judge-Warden cleanup

| Role | Sidon use |
|---|---|
| Builder | propose candidate-addition, pair-signature remap, Theodorus capacity routing, kinetic-to-Sidon projection |
| Judge | verify injectivity / trivial symmetry / residual zero |
| Warden | block nontrivial collisions, false physical claims, unbounded recursion, false maximality, wrong-handed phase routes |

## Stack placement

```text
THEODORUS_SHELL
→ SIDON_PAIR_SUM_GATE
→ SIDON_FAMM_MAP
→ SEMANTIC_MASS_ROUTE_PLOW
→ PIST / PIST-CHAOS transition
→ NUVMAP_DELTA_DAG
→ COARSENING_SCAR_CACHE
→ BJW_GEODESIC_CLEANUP
→ EXACT_RECEIPT
```

## Claim boundary

This map does not claim Sidon sets are physical plasma events, nor that a heuristic Sidon route proves maximality. The exact claim is narrower and stronger:

```text
Sidon pair-signature uniqueness is an exact anti-collision gate.
Violations become receipt-bearing scars.
Those scars can guide FAMM routing, coarsening, and cleanup.
```

## Project sentence

The Sidon FAMM Map turns pair-sum uniqueness into an exact anti-collision receipt: valid pair signatures become addressable relation channels, nontrivial collisions become FAMM scars/coarsening agents, and the whole Sidon layer can now route through Theodorus capacity, Semantic Mass, PIST transitions, NUVMAP Delta-DAG replay, and Builder-Judge-Warden cleanup.
