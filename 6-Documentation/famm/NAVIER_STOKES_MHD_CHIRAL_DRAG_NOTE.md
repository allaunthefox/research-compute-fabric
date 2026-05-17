# Navier-Stokes / MHD Chiral Drag Witness Note

## Purpose

Record how the Plasma Chiral Drag Witness Gate helps the Navier-Stokes / Burgers / MHD side of the project.

This note does **not** claim to solve Navier-Stokes regularity. It records a narrower and useful role:

```text
hidden rotational flow / vorticity
→ wave or image twist witness
→ signed chirality residual
→ FAMM scar or closure correction
```

The strongest domain fit is magnetohydrodynamics (MHD), because the cited plasma result concerns Alfvén waves in a rotating magnetized plasma.

## Core Navier-Stokes object

For incompressible Navier-Stokes:

```math
\partial_t\mathbf u
+
(\mathbf u\cdot\nabla)\mathbf u
=
-\nabla p
+
\nu\nabla^2\mathbf u
+
\mathbf f
```

with vorticity:

```math
\boldsymbol\omega=\nabla\times\mathbf u
```

The difficult regime is where nonlinear transport, shear, vorticity, and unresolved energy transfer hide inside the flow.

## Plasma chiral drag witness

From the Plasma Chiral Drag Witness Gate:

```math
\Delta\Theta_{\mathrm{img}}
\approx
\frac{L\Omega}{2v_A}
```

Residual receipt:

```math
R_{\mathrm{chiral}}
=
\left|
\Delta\Theta_{\mathrm{obs}}
-
\frac{L\Omega}{2v_A}
\right|
```

where:

| Term | Meaning |
|---|---|
| `DeltaTheta_img` | image / transverse wave-structure rotation |
| `L` | propagation path length |
| `Omega` | medium rotation / torsional flow rate |
| `v_A` | Alfvén speed |
| `R_chiral` | mismatch between observed and predicted twist |

## MHD interpretation

In MHD, plasma flow, magnetic field, and Alfvén-wave propagation interact. The image-rotation equation gives a witness channel:

```text
medium rotation / vorticity
→ Alfvén wave image rotation
→ signed torsion/chirality receipt
```

So the project use is:

```text
not: prove all Navier-Stokes behavior
yes: measure hidden rotational structure through a wave witness
```

## Closure use

A chiral-drag residual can feed an effective closure term:

```math
\nu_{\mathrm{eff}}
=
\nu_0(1+\kappa R_{\mathrm{chiral}})
```

or, more generally:

```math
Q_{\mathrm{eff}}
=
Q_0
+
\mathcal C(R_{\mathrm{chiral}},\Omega,\chi,B_0,v_A)
```

where `Q_eff` is an unresolved forcing / closure / correction channel.

## FAMM mapping

```math
\mathfrak C_{\mathrm{NS\_MHD\_Chiral}}
=
A_{16}(u_{\mathrm{ns\_mhd}})
\otimes
[
\Sigma_{\mathbf u}
+
\Sigma_{\boldsymbol\omega}
+
\Sigma_{B_0}
+
\Sigma_{v_A}
+
\Sigma_{\Delta\Theta}
+
\Sigma_{\chi}
+
\Sigma_{R_{\mathrm{chiral}}}
+
\Sigma_{\mathrm{closure}}
+
\Sigma_{\mathrm{receipt}}
]
```

## Burgers / triad pipeline connection

For the Burgers/triad witness pipeline:

```text
resolved solver
+ unresolved residual witness
+ closure correction
```

this becomes:

```text
resolved velocity / plasma field
+ Alfvén image-rotation witness
+ torsion/chirality residual
+ closure update
```

## BraidStorm connection

In BraidStorm, a crossing can carry a chiral-drag witness:

```math
\beta_{ij}
:
(s_i,s_j)
\to
(s_i',s_j',r_{ij},\epsilon_{ij},\Omega_{ij},\Delta\Theta_{ij})
```

where `DeltaTheta_ij` is the signed wave/image twist witness for the crossing environment.

## Warden boundary

This note must not be used to claim:

```text
Navier-Stokes regularity is solved.
All fluids expose vorticity through this exact equation.
Light in vacuum is dragged this way.
Every torsion model is physically proven.
```

Allowed claim:

```text
For NS/MHD-adjacent work, plasma chiral drag provides a citeable witness model for turning hidden medium rotation into measurable signed wave/image rotation, which can be used as a FAMM residual, scar, or closure signal.
```

## Stack placement

```text
Navier-Stokes / Burgers / MHD flow
→ vorticity / torsion field
→ PLASMA_CHIRAL_DRAG_WITNESS_GATE
→ FAMM residual / scar ledger
→ closure correction
→ NUVMAP Delta-DAG receipt
→ BJW Judge/Warden boundary
```

## Project sentence

For Navier-Stokes/MHD work, plasma chiral drag is useful as a vorticity witness: a rotating magnetized medium drags an Alfvén wave's transverse structure, so observed image rotation gives a signed residual for hidden flow rotation, allowing FAMM to scar or correct unresolved torsion in the closure model.
