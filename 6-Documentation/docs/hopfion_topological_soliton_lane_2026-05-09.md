# Hopfion Topological Soliton Lane

**Date:** 2026-05-09

**Status:** `TOPOLOGICAL_SOLITON_DESIGN_PRIOR`

**Claim boundary:** this note folds laser-created isolated magnetic hopfions
into the Research Stack as a topology/field-configuration primitive. Hopfions
are particle-like topological magnetic solitons, not elementary particles. This
does not claim new Standard Model particle physics, device readiness, or
spintronic engineering success.

## Source

Phys.org reported the first direct observation of laser-created isolated
hopfions, based on the Nature Physics paper:

```text
Laser-induced nucleation of magnetic hopfions
Nature Physics (2026)
DOI: 10.1038/s41567-026-03236-0
```

Useful source facts:

- The observed objects are isolated magnetic hopfions in cubic chiral FeGe.
- They were nucleated by femtosecond laser pulses and observed by transmission
  electron microscopy.
- Quantitative agreement between experiment and micromagnetic simulation was
  used as evidence.
- Algebraic topology was used to classify the observed magnetic
  configurations.
- The observed isolated hopfion can be characterized by an integer Hopf charge,
  with examples including `H = -1`.

Sources:

- `https://phys.org/news/2026-05-laser-isolated-hopfions.html`
- `https://doi.org/10.1038/s41567-026-03236-0`

## Why This Matters For The Stack

This is a nearly perfect physical analogue for the stack's receipt discipline:

```text
local field texture
-> projection through an instrument
-> simulation replay
-> topological invariant
-> admitted particle-like state
```

That is exactly the stack pattern:

```text
structure -> projection -> receipt -> replay -> invariant gate
```

The important upgrade is that this is not just a 2D braid metaphor. A hopfion is
a 3D field texture whose nontrivial topology can survive deformation unless a
singular/unwinding event occurs. That makes it a strong model for:

- braided rope states;
- torsional memory-bearing trajectories;
- logogram folds with nontrivial closure;
- AMMR leaves that carry topological charge;
- FAMM scars that are local minima in an energy landscape.

## Core Equations And Invariants

The broader reusable equation pack is:

```text
6-Documentation/docs/topological_soliton_equation_pack_2026-05-09.md
```

The Nature Physics paper frames the topology as maps of pairs of spaces:

```text
f : (I^3, partial I^3) -> (A, B)
```

Where:

```text
I^3          = localization domain
partial I^3 = boundary of the localization domain
A           = S^2, the order-parameter sphere
B           = constrained boundary subspace
```

The key softened-boundary invariant is:

```text
pi_3(S^2, S^2 \ union_i X_i) = Z, n >= 1
```

This matters because it keeps integer Hopf charge available under realistic
boundary constraints, not only idealized one-point boundary conditions.

For the stack:

```text
H in Z
H = 0      trivial / unwindable class
H != 0    nontrivial topological receipt
|H| = 1   generator / anti-generator class
```

The micromagnetic energy surface includes exchange, DMI, Zeeman, and
demagnetizing terms:

```text
E = int_Vm dr [
      A * sum_i |grad m_i|^2
      + D * m . (grad x m)
      - M_s * m . B
    ]
    + (1 / (2 mu_0)) * int_R3 dr sum_i |grad A_d,i|^2
```

Where:

- `m(r) = M(r) / M_s` is the normalized magnetization field.
- `A` is the Heisenberg exchange constant.
- `D` is the DMI constant.
- `B` is the external plus demagnetizing magnetic field.
- `A_d` is the demagnetizing vector potential.

## Receipt Gate

Minimum admission gate:

```text
if projected image is missing:
  HOLD_MISSING_PROJECTION
elif simulation replay is missing:
  HOLD_MISSING_MICROMAGNETIC_REPLAY
elif topological invariant H is missing:
  HOLD_MISSING_HOPF_CHARGE
elif H == 0:
  HOLD_TRIVIAL_TOPOLOGY
elif projection and simulation disagree above tolerance:
  HOLD_PROJECTION_REPLAY_MISMATCH
else:
  ADMIT_TOPOLOGICAL_SOLITON_PRIOR
```

This is deliberately a design-prior gate. It does not assert that the stack can
create or control hopfions. It says the stack can borrow the logical shape:

```text
particle-like state = localized field + replay projection + integer topology
```

## Mapping To Existing Stack Surfaces

| Hopfion paper concept | Stack surface |
|---|---|
| Femtosecond laser perturbation | controlled energy kick / topology crossing gate |
| Complex energy landscape | FAMM basin / frustration surface |
| Local minimum | stable receipt-bearing state |
| TEM projection | projection receipt / rendered view |
| Micromagnetic simulation | replay witness |
| Hopf charge `H` | integer topological invariant |
| Boundary subspace `B` | residual / admissibility boundary |
| Punctured sphere | allowed field state with excluded singular regions |
| `H = -1` | anti-generator / oriented rope charge |

## Fit With The Eigen/Topology Work

This should sharpen the topology lane more than the shock lane. The strongest
local bridge is:

```text
topological chain reduction
+ torsional rope memory
+ energy-landscape FAMM scars
+ projection/replay receipts
+ integer invariant gates
```

The likely future Lean shape is not continuous micromagnetics first. The first
Lean shape should be finite and receipt-friendly:

```text
structure HopfionReceipt where
  projection_present : Bool
  replay_present : Bool
  hopf_charge : Int
  projection_residual_q0_16 : UInt16
  residual_bound_q0_16 : UInt16
```

Then prove the gate rejects missing projection, missing replay, zero charge,
and over-bound residual before it admits a nonzero topological class.

## Next Work

1. Add `TopologicalSolitonReceipt` as the general finite Lean gate surface.
2. Add `HopfionTopologicalSoliton` as a fixture family over that gate.
3. Add fixtures for missing projection, missing replay, `H = 0`, `H = -1`, and
   projection/replay mismatch.
4. Re-run the topology/eigen remapper and check whether the soliton/topology
   lane gains a cleaner support signature.
5. Keep device, memory, spintronic, and elementary-particle claims HOLD until
   direct receipts exist.
