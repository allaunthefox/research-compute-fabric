# Navier-Stokes Shadow Control Gap Map

## Purpose

Clarify the missing proof bridge in the Navier-Stokes 16D witness-packet route.

The hard step is not merely building a witness packet. The hard step is proving that the packet controls the dangerous PDE term:

```math
(\omega\cdot\nabla)u
```

The project strategy is to use **shadows** to find where the packet does **not** control it.

In project language:

```text
Do not assume the witness packet is complete.
Map its blind spots.
The shadows tell us where control is missing.
```

## Core idea

A witness packet is a projection:

```math
\Pi(u)
=
(
\omega,
E,
Z,
H,
\chi,
R_{\mathrm{chiral}},
R_p,
R_{\partial},
\tau_{\mathrm{spectral}},
\Omega_{\mathrm{scar}},
\rho
)
```

It is useful only if the dangerous stretching term is controlled by the packet.

The desired bridge inequality has shape:

```math
\|(\omega\cdot\nabla)u\|_{H^{s-1}}
\le
C_s(1+\mathcal W(t))\|u\|_{H^s}
```

where:

```math
\mathcal W(t)
=
a_1R_{\mathrm{chiral}}(t)
+a_2R_p(t)
+a_3R_{\partial}(t)
+a_4\tau_{\mathrm{spectral}}(t)
+a_5\Omega_{\mathrm{scar}}(t)
```

But the project does **not** assume this inequality is true. It searches for where it fails.

## Shadow residual

Define the control-gap residual:

```math
\mathcal S_{\mathrm{gap}}(t)
=
\left[
\frac{\|(\omega\cdot\nabla)u\|_{H^{s-1}}}{\|u\|_{H^s}+\delta}
-
C_s(1+\mathcal W(t))
\right]_+
```

where:

```math
[x]_+=\max(x,0)
```

Interpretation:

```text
S_gap = 0    witness packet controls the dangerous term at this scale
S_gap > 0    the dangerous term escaped the current witness packet
```

The positive part is the **shadow**.

## Shadow set

Define the failure region:

```math
\mathcal Z_{\mathrm{shadow}}
=
\{(x,t,k):\mathcal S_{\mathrm{gap}}(x,t,k)>0\}
```

where `k` may index scale, spectral shell, NUVMAP basin, braid strand, or local chart.

The search target is not only:

```text
prove W controls stretching
```

but:

```text
find the shadow set where W does not control stretching
```

Then Builder can add or refine witness channels only where the shadow exists.

## Projection-nullspace shadow

The most important shadow is the invisible direction of the projection.

At state `u`, let:

```math
D\Pi_u
```

be the derivative/Jacobian of the witness projection.

A control-blind perturbation is:

```math
\eta\in\ker D\Pi_u
```

If this perturbation changes the dangerous PDE term:

```math
D[(\omega\cdot\nabla)u]_u[\eta]\ne 0
```

then the witness packet is blind to a dangerous direction.

Define:

```math
\mathcal K_{\mathrm{shadow}}(u)
=
\{\eta:\eta\in\ker D\Pi_u,\;D[(\omega\cdot\nabla)u]_u[\eta]\ne0\}
```

Interpretation:

```text
If a perturbation is invisible to the witness packet but changes vorticity stretching, it is a shadow direction.
```

## Underverse / negative evidence role

A shadow is not garbage.

It is negative evidence:

```text
failed control region
→ shadow basin
→ FAMM scar
→ coarsening agent
→ new witness-channel proposal
→ Judge/Warden retest
```

This matches the project rule:

```text
wrong or missing routes are not discarded;
they become coarsening agents and search priors.
```

## Builder-Judge-Warden loop

| Role | Shadow-control task |
|---|---|
| Builder | proposes a new witness channel or refined projection for a shadow basin |
| Judge | checks whether the new packet reduces `S_gap` and preserves PDE invariants |
| Warden | blocks empirical-only bridges, hidden boundary failures, false MHD-to-NS transfer, and overclaiming |

Operational loop:

```text
current witness packet
→ compute/control-estimate dangerous term
→ find S_gap > 0
→ mark shadow basin
→ add/refine witness only there
→ retest inequality
→ promote if S_gap closes
→ scar/coarsen if it does not
```

## What counts as a useful shadow

A shadow is useful if it identifies one of:

```text
spectral tail not represented by the packet
pressure projection failure
boundary condition leak
chiral/torsion mismatch
helicity sign ambiguity
MHD witness not transferable to plain NS
NUVMAP false merge
BraidStorm crossing alias
closure model blind spot
```

## Anti-blowup version

Use the anti-Erdos move:

```text
Do not directly prove smoothness.
Assume blow-up.
Find which witness-control gap must become nonzero.
```

If blow-up occurs:

```math
\|u(t)\|_{H^s}\to\infty
```

then either the witness packet controls the stretching term or a shadow must appear:

```math
\text{blow-up}
\Rightarrow
\mathcal S_{\mathrm{gap}}>0
\quad\text{or}\quad
\int_0^T \mathcal W(t)\,dt=\infty
```

So the proof search becomes:

```text
Can blow-up occur without producing a shadow receipt?
```

If no, then the route is:

```text
bounded witness packet + no shadow gap
⇒ dangerous stretching controlled
⇒ no blow-up in that class
```

## Stack placement

```text
NS16 witness packet
→ shadow control-gap map
→ FAMM scar/coarsening ledger
→ Builder proposes missing witness channel
→ Judge tests control inequality
→ Warden blocks overclaim
→ NUVMAP Delta-DAG records closed/open shadow basins
```

## Warden boundary

This note is a method for locating the missing proof bridge. It is not the bridge by itself.

Allowed claim:

```text
The project uses shadows to find where the witness packet fails to control the dangerous Navier-Stokes stretching term, then turns those failures into scarred/coarsened basins or new witness-channel proposals.
```

Disallowed claim:

```text
The witness packet already controls all 3D Navier-Stokes blow-up routes.
```

## Project sentence

The shadows are how the project finds where the Navier-Stokes witness packet is incomplete: any direction invisible to the packet but active in vorticity stretching becomes a shadow basin, and that basin is scarred, coarsened, or upgraded with a new witness channel until the control gap closes or the route is rejected.
