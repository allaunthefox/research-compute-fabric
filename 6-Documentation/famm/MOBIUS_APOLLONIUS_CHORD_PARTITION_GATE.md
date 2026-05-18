# Möbius-Apollonius Chord Partition Gate

## Purpose

Add the uploaded visualization topic — Möbius transforms, Circles of Apollonius, spirals, angles, and trigonometric chord partitions — as a conformal-geometry witness gate in the FAMM/BraidStorm/Universal Shortcut Center stack.

Primary visual source:

```text
Möbius Transform and Circles of Apollonius - Spirals Angles Spirals Trigonometric Partitions.
YouTube video: https://www.youtube.com/watch?v=ndjz5tVPywM
Local uploaded artifact: Möbius Transform and Circles of Apollonius - Spirals Angles Spirals Trigonometric Partitions (720p, h264).mp4
Accessed / integrated: 2026-05-18.
```

The useful project shape is:

```text
complex-plane configuration
→ Möbius transform
→ Apollonius circle / chord-ratio witness
→ angle-preserving conformal transport
→ spiral / coaxal-family projection
→ FAMM residual or receipt
```

This gate is especially useful because it gives the project a precise way to move circle/line/spiral structures through a lawful complex transform while preserving the invariants that matter: cross-ratio, angle, generalized-circle structure, and distance-ratio loci.

## Core Möbius transform

A Möbius transformation has the form:

```math
T(z)=\frac{az+b}{cz+d},\qquad ad-bc\ne0
```

It maps generalized circles to generalized circles:

```text
circle/line → circle/line
```

and is conformal wherever its derivative is nonzero:

```math
T'(z)=\frac{ad-bc}{(cz+d)^2}
```

so local angles are preserved away from the pole.

References: Ahlfors, *Complex Analysis*; Needham, *Visual Complex Analysis*; Beardon, *The Geometry of Discrete Groups*.

## Apollonius circle witness

A Circle of Apollonius is the locus:

```math
\mathcal A(a,b;k)
=
\left\{z\in\mathbb C:\frac{|z-a|}{|z-b|}=k\right\}
```

For `k != 1`, this is a circle. For `k = 1`, it degenerates to a line/perpendicular bisector.

Project meaning:

```text
fixed source pair (a,b)
+ constant ratio k
→ exact distance-ratio witness curve
```

Under a Möbius transformation, the Apollonius family is transported into another generalized-circle family, while cross-ratio and angle structure provide the guard conditions.

References: Coxeter and Greitzer, *Geometry Revisited*; Needham, *Visual Complex Analysis*.

## Cross-ratio invariant

The primary exact witness is the cross ratio:

```math
[z_1,z_2;z_3,z_4]
=
\frac{(z_1-z_3)(z_2-z_4)}{(z_1-z_4)(z_2-z_3)}
```

Möbius transformations preserve it:

```math
[T(z_1),T(z_2);T(z_3),T(z_4)]
=
[z_1,z_2;z_3,z_4]
```

This makes the cross-ratio a clean Judge receipt:

```math
R_{\mathrm{cr}}
=
\left|
[T(z_1),T(z_2);T(z_3),T(z_4)]-[z_1,z_2;z_3,z_4]
\right|
```

Pass condition:

```math
R_{\mathrm{cr}}\le \Theta_{\mathrm{tol}}
```

References: Ahlfors, *Complex Analysis*; Beardon, *The Geometry of Discrete Groups*.

## Chord / unit-circle partition witness

On the unit circle, a chord between two points with angular separation `theta` has length:

```math
L(\theta)=2\sin\left(\frac{\theta}{2}\right)
```

A trigonometric partition of a chord can therefore be treated as an angle-to-length witness:

```math
\theta\mapsto 2\sin(\theta/2)
```

Project meaning:

```text
angle partition
→ chord length
→ circle-boundary witness
→ conformal transport through Möbius map
```

Reference: Coxeter and Greitzer, *Geometry Revisited*.

## Spiral connection

Möbius transforms can turn simple circle/line pencils into visually spiral-like families under parameterized motion or composition. Project use:

```text
circle pencil / chord partition
→ conformal transport
→ spiral-like projected trajectory
→ chirality / angle / ratio receipt
```

The Warden must distinguish actual logarithmic spiral structure from a parameterized family of transformed circles that merely appears spiral-like in projection.

## Universal Shortcut Center packet

```math
\Gamma_{\mathrm{MobiusApollonius}}
=
(
X_{\mathbb C},
\pi_T,
W_{\mathrm{circle/ratio}},
R_{\mathrm{cr}},
I_{\mathrm{angle,ratio}},
G_{ad-bc\ne0},
K,
\epsilon
)
```

| Packet term | Meaning |
|---|---|
| `X_C` | original complex-plane configuration |
| `pi_T` | Möbius projection `T(z)` |
| `W_circle/ratio` | transformed generalized circle / Apollonius witness |
| `R_cr` | cross-ratio or angle-preservation receipt |
| `I_angle,ratio` | preserved conformal/ratio invariant |
| `G_ad-bc_nonzero` | guard that the transform is valid |
| `K` | cost of tracking full geometry versus witness family |
| `epsilon` | residual from numerical/visual/projection error |

## FAMM object

```math
\mathfrak C_{\mathrm{MobiusApollonius}}
=
A_{16}(u_{\mathrm{mobius}})
\otimes
[
\Sigma_z
+
\Sigma_T
+
\Sigma_{\mathrm{circle}}
+
\Sigma_{\mathrm{Apollonius}}
+
\Sigma_{\mathrm{crossRatio}}
+
\Sigma_{\mathrm{angle}}
+
\Sigma_{\mathrm{chord}}
+
\Sigma_{\chi}
+
\Sigma_{\epsilon}
+
\Sigma_{\mathrm{receipt}}
]
```

## BraidStorm use

Each strand can carry a conformal geometry state:

```math
s_i=(z_i,T_i,\mathcal A_i,\theta_i,L_i,\chi_i,\rho_i)
```

A crossing may now be tested by whether its conformal invariants survive:

```text
strand crossing
→ Möbius transport
→ cross-ratio receipt
→ Apollonius ratio receipt
→ chord-angle receipt
→ FAMM scar if invariant drifts
```

## Anti-FAMM / Warden checks

The Warden should check:

```text
invalid Möbius determinant ad-bc = 0
pole crossing / infinity handling
confusing visual spiral with proven spiral
failure to preserve cross-ratio
angle preservation claimed at a singular point
circle/line degeneration not recorded
unit-circle chord formula used off the unit circle without normalization
```

Anti-FAMM shadow test:

```text
a perturbation invisible in the rendered curve
but visible in cross-ratio or chord-ratio residual
is a conformal shadow.
```

## Stack placement

```text
MOBIUS_APOLLONIUS_CHORD_PARTITION_GATE
→ Universal Shortcut Center Manifold
→ BraidStorm conformal-strand receipt
→ Golden Braid Centering / chirality check
→ FAMM Scar Ledger
→ Anti-FAMM conformal-shadow attack
→ NUVMAP Delta-DAG geometry receipt
```

## Warden boundary

This gate imports the conformal-geometry structure, not the visual animation as proof.

Allowed claim:

```text
Möbius-Apollonius geometry gives the project a lawful conformal transport gate: circles/lines and ratio loci move through a Möbius map while cross-ratio and angle receipts check invariant preservation.
```

Disallowed claim:

```text
A GeoGebra visualization alone proves a new Riemann, spiral, or partition theorem.
```

## References

### Visual source

```bibtex
@online{youtube_mobius_apollonius_spirals_2026,
  title        = {Möbius Transform and Circles of Apollonius - Spirals Angles Spirals Trigonometric Partitions},
  organization = {YouTube},
  url          = {https://www.youtube.com/watch?v=ndjz5tVPywM},
  urldate      = {2026-05-18},
  note         = {User-supplied video source; local uploaded artifact title: Möbius Transform and Circles of Apollonius - Spirals Angles Spirals Trigonometric Partitions (720p, h264).mp4}
}
```

### Mathematical references

```bibtex
@book{ahlfors1979complex,
  title     = {Complex Analysis: An Introduction to the Theory of Analytic Functions of One Complex Variable},
  author    = {Ahlfors, Lars V.},
  edition   = {3},
  publisher = {McGraw-Hill},
  year      = {1979}
}

@book{needham1997visual,
  title     = {Visual Complex Analysis},
  author    = {Needham, Tristan},
  publisher = {Oxford University Press},
  year      = {1997}
}

@book{beardon1983geometry,
  title     = {The Geometry of Discrete Groups},
  author    = {Beardon, Alan F.},
  publisher = {Springer},
  year      = {1983}
}

@book{coxeter1967geometry,
  title     = {Geometry Revisited},
  author    = {Coxeter, H. S. M. and Greitzer, S. L.},
  publisher = {Mathematical Association of America},
  year      = {1967}
}
```

## Project sentence

The Möbius-Apollonius gate turns complex-plane geometry into a receipt-bearing conformal transport layer: Möbius maps move circles, lines, Apollonius ratio loci, and chord partitions while cross-ratio, angle, and chord-length witnesses tell FAMM whether the projected geometry stayed lawful or became a scarred conformal shadow.
