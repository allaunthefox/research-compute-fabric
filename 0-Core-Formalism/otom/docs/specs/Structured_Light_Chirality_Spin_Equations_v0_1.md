# Structured-Light Chirality and Spin Equations v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This spec adds the equation layer from Mkhumbuza et al. (2026), *Topological control of chirality and spin with structured light*, into the OTOM math stack.

The source paper demonstrates that higher-order Poincare modes with tunable Pancharatnam topological charge can control spin angular momentum and optical chirality in free-space paraxial structured light. The equations below are recorded as an optics-domain source layer, not as proof of broader OTOM claims.

## Source

```text
Mkhumbuza, L.; Ornelas, P.; Dudley, A.; Nape, I.; Forbes, K. A.
Topological control of chirality and spin with structured light.
Light: Science & Applications 15, 214 (2026).
DOI: 10.1038/s41377-026-02278-6
```

## Core variables

```text
r = (r, phi, z)       polar/cylindrical coordinates
sigma_+, sigma_-     right/left circular polarization basis states
ell_p                Pancharatnam topological index / charge
Delta ell            spin-orbit charge offset from SOC element, e.g. q-plate
ell_A = ell_p + Delta ell
ell_B = ell_p - Delta ell
f_in(r)              input radial amplitude
f_A(r,z), f_B(r,z)   propagated circular-component amplitudes
S_i                  Stokes parameters
S_3                  longitudinal spin / circular-polarization imbalance proxy
z_R                  Rayleigh range
zeta = z / z_R       normalized propagation coordinate
```

## 1. Input vector field with Pancharatnam topology

The source paper writes the input electric field as a spin-balanced radial vector field with a factored global Pancharatnam topological phase:

```text
U_in(r) ∝ exp(i ell_p phi) f_in(r)
          ( exp(i Delta ell phi) sigma_+ + exp(-i Delta ell phi) sigma_- )
```

Interpretation:

```text
exp(i ell_p phi)      = global PT/OAM-bearing phase
exp(±i Delta ell phi) = circular-component azimuthal phases
f_in(r)               = shared radial amplitude at the source plane
```

At the source plane, the circular components are amplitude-balanced:

```text
|f_A(r,0)|^2 = |f_B(r,0)|^2
```

so the field begins with zero local longitudinal spin:

```text
S_3(r,0) = 0
```

## 2. Pancharatnam phase / PT winding

The paper defines the topological phase from the overlap between the initial polarization state and the state at azimuthal coordinate `phi`:

```text
phi_p = arg( < U_in(0) | U_in(phi) > ) = (ell_p / 2) phi
```

This links the Pancharatnam topological index to the beam's polarization-phase winding and total OAM structure.

## 3. Propagation map into circular components

During paraxial free-space propagation, the input state evolves into circular-polarization components with distinct topological charges:

```text
U_in -> U = f_A(r,z) exp(i ell_A phi) sigma_+
          + f_B(r,z) exp(i ell_B phi) sigma_-
```

with:

```text
ell_A = ell_p + Delta ell
ell_B = ell_p - Delta ell
```

The key physical mechanism is that `ell_p` forces the two circular components into different paraxial modal families, producing differential Gouy-phase evolution and radial divergence.

## 4. Spin / chirality proxy through the third Stokes parameter

The third Stokes parameter is the circular-polarization intensity difference:

```text
S_3(r,z) = |f_A(r,z)|^2 - |f_B(r,z)|^2
```

In the paraxial regime, the source paper uses `S_3` as the shared measurable proxy for longitudinal spin density and optical chirality density:

```text
s_z ∝ C ∝ sigma I
```

where:

```text
s_z   = longitudinal spin density
C     = optical chirality density
sigma = helicity, sigma = ±1 for circular polarization, |sigma| < 1 for elliptical, sigma = 0 for linear/unpolarized
I     = beam intensity
```

## 5. Laguerre-Gaussian source mode

The scalar horizontally polarized LG mode used to prepare the vector beam is:

```text
LG_ell_p(r) x_hat = f_ell_p(r,z) exp(i ell_p phi) x_hat
```

with the horizontal polarization decomposed into circular components:

```text
x_hat = (sigma_+ + sigma_-) / sqrt(2)
```

A characteristic LG radial profile is recorded as:

```text
f_ell_p(r,z) ∝ (sqrt(2) r / w(z))^|ell_p|
              exp(i(psi_G + k z) - r^2 / w(z)^2)
```

with Gouy phase:

```text
psi_G = (|ell_p| + 1) arctan(z / z_R)
```

The topological charge affects both Gouy-phase evolution and radial divergence.

## 6. q-plate / SOC preparation map

The source uses a q-plate as a convenient spin-orbit coupling preparation element:

```text
LG_ell_p x_hat -> U_in(r,z=0)
```

Expanded:

```text
U_in(r,0) = f_ell_p(r)
            ( exp(i ell_A phi) sigma_+ + exp(i ell_B phi) sigma_- )
```

where:

```text
ell_A = ell_p + Delta ell
ell_B = ell_p - Delta ell
```

The paper emphasizes that the q-plate is not fundamental to the observed propagation-induced SOI; alternative beam-shaping methods may prepare the same class of states.

## 7. Elegant LG / hypergeometric-Gaussian propagation family

After propagation, the circular components evolve into elegant Laguerre-Gaussian or hypergeometric-Gaussian modal families. The paper records:

```text
f_A(r,z) ≈ |eLG_{p_A}^{ell_A}(r,z)|
f_B(r,z) ≈ |eLG_{p_B}^{ell_B}(r,z)|
```

with radial indices:

```text
p_A = ( |ell_p| - |ell_A| ) / 2
p_B = ( |ell_p| - |ell_B| ) / 2
```

This is where the Pancharatnam index enters the radial amplitude response through `ell_A` and `ell_B`.

## 8. Far-field angular-spectrum amplitude

In the far field, the angular spectrum has the form:

```text
eLG_{p_A(B)}^{ell_A(B)}(rho, z -> infinity)
  ∝ i^{ell_A(B)} rho^{|ell_A(B)|}
     L_{p_A(B)}^{|ell_A(B)|}(rho^2)
     exp(i ell_A(B) phi)
```

where:

```text
rho = normalized radial wavenumber coordinate
L_p^|ell|(rho^2) = associated Laguerre polynomial factor
```

The key radial factor is:

```text
rho^{|ell_p ± Delta ell|}
```

which controls the radial distribution of the two spin components and causes the amplitude asymmetry seen as spin/chirality generation.

## 9. Local Stokes vector on the Poincare sphere

The locally normalized Stokes vector is recorded as:

```text
S(r) = ( cos(Phi) sin(beta),
         sin(Phi) sin(beta),
         cos(beta) )
```

where:

```text
Phi  = azimuthal coordinate on the Poincare sphere
beta = zenith coordinate on the Poincare sphere
```

At the source plane, the field populates the equator of the Poincare sphere because:

```text
S_3(r,0) = 0
```

During propagation, `S_3` becomes nonzero and the sphere coverage expands away from the equator.

## 10. Stokes parameter measurement equations

The measured Stokes parameters are expressed through six polarization intensities:

```text
S_0 = I_R + I_L
S_1 = I_H - I_V
S_2 = I_D - I_A
S_3 = I_R - I_L
```

where:

```text
H = horizontal
V = vertical
D = diagonal, 45 degrees
A = anti-diagonal, 135 degrees
R = right-handed circular polarization
L = left-handed circular polarization
```

## 11. Spin-current proxy from S3 gradient

The paper defines a transverse spin-current field from spatial derivatives of `S_3`:

```text
J = < partial_y S_3, - partial_x S_3 >
```

Interpretation:

```text
radial S_3 gradient
→ azimuthal spin-current pattern
→ optical Hall effect signature
```

The far-field measurements show that nonzero `ell_p` produces spatial separation of right- and left-circular polarization components and an associated azimuthal spin-current structure.

## 12. OTOM control map

For OTOM, the safe abstraction is:

```text
Pancharatnam topological charge ell_p
→ circular-component mode split ell_A, ell_B
→ differential Gouy phase / radial divergence
→ nonzero S_3(r,z)
→ local spin/chirality density proxy
→ radial component separation / optical Hall signature
```

This is an optics-domain example of:

```text
topological control parameter
→ propagation evolution
→ measurable component separation
→ field-local routing/control signal
```

## 13. Integration with existing OTOM math stack

### Relation to torsion / flip language

The paper gives a real optical example where a signed topological parameter changes local handedness distribution after propagation. This can inform—but not validate—the OTOM torsion-flip intuition:

```text
signed topological winding
→ propagated local handedness distribution
```

### Relation to kinetic/Sidon lattice

The paper also resembles the two-layer kinetic/Sidon scaffold at the structural level:

```text
continuous field evolution
→ observable component separation
→ discrete measurement channel S_3 / spin texture / current map
```

But the paper does not imply Sidon anti-aliasing, semantic compression, or non-optical manifold claims.

## Warden boundaries

### Blocked claims

```text
This paper proves OTOM.
This paper proves the kinetic/Sidon lattice.
This paper proves semantic mass or non-optical chirality claims.
Pancharatnam topological charge is identical to DeltaPhi, Sidon signatures, or Translator Packets.
The optical Hall effect can be transferred to arbitrary computational manifolds without new evidence.
```

### Allowed claims

```text
The equations are valid source equations for paraxial structured-light spin/chirality control as reported by Mkhumbuza et al.
The paper provides a bounded physics-domain example of topology-controlled field evolution.
The Stokes/S3 equations can be used as a measurement analogy for field-local component separation.
The topological charge ell_p can be cited as a tunable optical control parameter within the structured-light domain.
```

## Strongest safe formulation

> The structured-light equation layer records how a tunable Pancharatnam topological charge splits circular-polarization components during paraxial propagation, producing nonzero S_3, optical chirality, spin density, and an optical Hall signature. OTOM may use this as bounded optics-domain support for topology-controlled field behavior, not as validation of broader non-optical claims.
