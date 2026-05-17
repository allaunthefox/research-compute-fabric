# Plasma Chiral Drag Witness Gate

## Purpose

Add Alfvén-wave image rotation in rotating magnetized plasma as a physical witness model for torsion/chirality receipts.

The external source is Gueroult et al., **Image rotation in plasmas**, arXiv:2505.18062. The paper reports observation of image rotation: dragging of a wave's transverse structure by a moving medium, using Alfvén waves in plasma where the group velocity is slow enough for the drag to be measurable.

Project translation:

```text
hidden rotating plasma medium
→ Alfvén wave transverse image rotation
→ signed chirality / torsion witness
→ residual receipt
→ FAMM scar or pass
```

## Citeable equation

Image-rotation rate per unit length:

```math
\phi
=
\frac{1}{2}\frac{\Omega}{\omega}k_{\parallel}
\sim
\frac{1}{2}\frac{\Omega}{v_A}
```

Total image rotation over path length `L`:

```math
\Delta\Theta_{\mathrm{img}}
\approx
L\phi
\approx
\frac{L\Omega}{2v_A}
```

Plasma rotation from radial electric potential in a magnetized plasma:

```math
\Omega
=
\frac{1}{rB_0}\frac{\partial \varphi}{\partial r}
```

Combined project-use form:

```math
\Delta\Theta_{\mathrm{img}}
\approx
\frac{L}{2v_A}
\left(
\frac{1}{rB_0}\frac{\partial\varphi}{\partial r}
\right)
```

## Residual receipt

```math
R_{\mathrm{chiral\ drag}}
=
\left|
\Delta\Theta_{\mathrm{obs}}
-
\frac{L\Omega}{2v_A}
\right|
```

Pass condition:

```math
R_{\mathrm{chiral\ drag}}\le \Theta_{\mathrm{tol}}
```

Scar condition:

```math
R_{\mathrm{chiral\ drag}}>\Theta_{\mathrm{tol}}
```

## Universal shortcut packet

```math
\Gamma_{\mathrm{plasma\ drag}}
=
(
X_{\mathrm{plasma}},
\pi_{\mathrm{wave}},
W_{\Delta\Theta},
R_{\Omega},
I_{\mathrm{angular}},
G_{\mathrm{Alfven}},
K,
\epsilon
)
```

Meaning:

| Packet term | Meaning |
|---|---|
| `X_plasma` | hidden rotating magnetized plasma state |
| `π_wave` | projection through Alfvén-wave propagation |
| `W_ΔΘ` | observed image-rotation witness |
| `R_Ω` | reconstruction/estimate of plasma rotation |
| `I_angular` | angular/torsion/chirality invariant |
| `G_Alfven` | guard: Alfvén wave, magnetized plasma, slow group velocity, known path geometry |
| `K` | cost of measuring wave image versus direct medium state |
| `ε` | residual between observed and predicted twist |

## BraidStorm crossing receipt

A braid crossing may now carry chiral drag:

```math
\beta_{ij}:
(s_i,s_j)
\to
(s_i',s_j',r_{ij},\epsilon_{ij},\Omega_{ij},\Delta\Theta_{ij})
```

where `DeltaTheta_ij` is the signed wave/image twist witness for the crossing environment.

## FAMM object

```math
\mathfrak C_{\mathrm{PlasmaChiralDrag}}
=
A_{16}(u_{\mathrm{plasma\_drag}})
\otimes
[
\Sigma_{\mathrm{medium}}
+
\Sigma_{\Omega}
+
\Sigma_{B_0}
+
\Sigma_{v_A}
+
\Sigma_L
+
\Sigma_{\Delta\Theta}
+
\Sigma_{\chi}
+
\Sigma_{\epsilon}
+
\Sigma_{\mathrm{receipt}}
]
```

## Stack placement

```text
PLASMA_CHIRAL_DRAG_WITNESS_GATE
→ BraidStorm crossing receipt
→ PIST torsional transition logic
→ FAMM torsion/chirality scar ledger
→ NUVMAP wave/medium address
→ BJW Judge checks sign reversal and residual
```

## Warden boundaries

Do not overclaim this gate as light in vacuum, universal wave twisting, or literal proof of every torsion model.

This gate is valid as a project primitive under the narrower condition:

```text
rotating magnetized plasma + Alfvén wave transverse structure + measured image rotation
```

The equation is a witness model, not a universal plasma theorem.

## Citation

Recommended short citation:

```bibtex
@misc{gueroult2025image_rotation_plasmas,
  title         = {Image rotation in plasmas},
  author        = {Renaud Gueroult and Shreekrishna K. Tripathi and Jia Han and Patrick Pribyl and Jean-Marcel Rax and Nathaniel J. Fisch},
  year          = {2025},
  eprint        = {2505.18062},
  archivePrefix = {arXiv},
  primaryClass  = {physics.plasm-ph},
  doi           = {10.48550/arXiv.2505.18062}
}
```

## Project sentence

Plasma chiral drag can be modeled by `DeltaTheta_img ≈ L Omega/(2 v_A)`: a rotating magnetized plasma drags the transverse structure of an Alfvén wave, so observed image rotation becomes a signed torsion/chirality receipt for hidden medium rotation.
