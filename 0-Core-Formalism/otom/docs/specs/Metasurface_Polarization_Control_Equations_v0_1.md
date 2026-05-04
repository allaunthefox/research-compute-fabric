# Metasurface Polarization-Control Equations v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This spec adds a metasurface-side optics equation layer into the OTOM math stack, based on the uploaded papers and source references:

```text
1. Liu et al. (2021), Multifunctional metasurfaces enabled by simultaneous and independent control of phase and amplitude for orthogonal polarization states.
   Light: Science & Applications 10:107.
   DOI: 10.1038/s41377-021-00552-3

2. Dorrah et al. (2025), Free-standing bilayer metasurfaces in the visible.
   Nature Communications 16.
   DOI: 10.1038/s41467-025-58205-7

3. Yang et al. (2024), Creating pairs of exceptional points for arbitrary polarization control: asymmetric vectorial wavefront modulation.
   Nature Communications 15:232.
   DOI: 10.1038/s41467-023-44428-z

4. Li et al. (2025), Exploiting hidden singularity on the surface of the Poincare sphere.
   Nature Communications 16:5953.
   DOI: 10.1038/s41467-025-60956-2

5. Zheng et al. (2026), Bilayer optical metasurfaces with multiple broken symmetries for nonlinear wavelength generation.
   npj Metamaterials 2:6.
   DOI: 10.1038/s44455-025-00016-3
```

The equations below are recorded as bounded optics-domain source equations. They support the OTOM math stack around polarization interfaces, topological phase, Jones operators, Stokes/Poincare geometry, nonlinear wavelength generation, symmetry-breaking gates, and finite gate extraction. They do not validate non-optical OTOM claims.

---

## 1. Arbitrary orthogonal polarization basis

For two arbitrary orthogonal input polarization states, write:

```text
|lambda_1^+> = [ cos chi,              exp(i delta) sin chi ]^T
|lambda_2^+> = [ -sin chi,             exp(i delta) cos chi ]^T
```

The corresponding output states are the opposite-handed / conjugate output channels:

```text
|lambda_1^->, |lambda_2^->
```

At each metasurface pixel `(x,y)`, the desired complex-amplitude transformations are:

```text
J(x,y) |lambda_1^+> = E_1(x,y) exp(i phi_1(x,y)) |lambda_1^->
J(x,y) |lambda_2^+> = E_2(x,y) exp(i phi_2(x,y)) |lambda_2^->
```

where:

```text
E_1, E_2 in [0,1]      target amplitudes
phi_1, phi_2           target phases
J(x,y)                 local Jones matrix
```

A compact operator form is:

```text
J(x,y) = E_1 exp(i phi_1) |lambda_1^-><lambda_1^+|
       + E_2 exp(i phi_2) |lambda_2^-><lambda_2^+|
```

This is the cleanest equation-level statement of independent complex-amplitude control for two orthogonal channels.

---

## 2. Double-phase decomposition for amplitude + phase

A complex scalar channel:

```text
E(x,y) exp(i phi(x,y)), 0 <= E <= 1
```

can be represented as the average of two phase-only terms:

```text
E exp(i phi)
= 1/2 [ exp(i(phi + arccos E)) + exp(i(phi - arccos E)) ]
```

because:

```text
1/2 [ exp(i a) + exp(i b) ]
= exp(i(a+b)/2) cos((a-b)/2)
```

Choosing:

```text
a = phi + arccos E
b = phi - arccos E
```

gives:

```text
(a+b)/2 = phi
cos((a-b)/2) = E
```

This is the mathematical bridge between desired complex amplitude and phase-only nanopillar subchannels.

---

## 3. Propagation/geometric phase split in anisotropic nanopillars

An anisotropic nanoelement supplies two phase shifts along its principal axes:

```text
delta_x, delta_y
```

and an in-plane rotation angle:

```text
theta
```

A rotated linear-basis Jones element has the form:

```text
J_theta = R(-theta) diag(exp(i delta_x), exp(i delta_y)) R(theta)
```

where:

```text
R(theta) = [ cos theta  -sin theta
             sin theta   cos theta ]
```

In circular-polarization conversion channels, the rotation contributes a Pancharatnam-Berry / geometric phase:

```text
phi_PB = +2 theta      for one handedness channel
phi_PB = -2 theta      for the opposite handedness channel
```

Thus the effective phase can be treated as:

```text
phi_eff = phi_prop +/- 2 theta
```

where `phi_prop` is the propagation phase set by the nanoelement geometry.

---

## 4. Bilayer metasurface transfer map

A bilayer metasurface can be modeled as two optical planes separated by a propagation segment:

```text
J_total(x,y) = J_2(x,y) P_d J_1(x,y)
```

where:

```text
J_1, J_2     Jones matrices of the two metasurface layers
P_d          propagation operator between layers separated by distance d
```

In a simplified scalar diffraction/channel view:

```text
U_out = M_2 P_d M_1 U_in
```

where `M_1` and `M_2` are spatially varying masks. This extra plane provides additional degrees of freedom that a single layer lacks.

A useful control abstraction is:

```text
single layer:
  local phase / local polarization operation

bilayer:
  local operation + interlayer propagation + second local operation
```

For OTOM this is important because it introduces a physical instance of:

```text
surface_1 state
→ propagation/coupling gap
→ surface_2 state
→ composed transformation
```

---

## 5. Exceptional point condition in a Jones/reflection operator

For a 2 x 2 non-Hermitian Jones or reflection matrix:

```text
M = [ a  b
      c  d ]
```

the eigenvalues are:

```text
lambda_± = (tr M +/- sqrt((tr M)^2 - 4 det M)) / 2
```

An exceptional point occurs when eigenvalues and eigenvectors coalesce. The eigenvalue degeneracy condition is:

```text
D_EP = (tr M)^2 - 4 det M = 0
```

with the non-diagonalizable condition:

```text
M != lambda I
```

Equivalently:

```text
rank(M - lambda I) = 1
(M - lambda I)^2 = 0
```

for a second-order EP.

---

## 6. Asymmetric PB control at an exceptional point

At an EP metastructure, one circular-polarization conversion channel may vanish or become privileged. Rotating the structure by angle `theta` encodes PB phase into a selected conversion channel:

```text
r_LR(theta) = r_LR(0) exp(+i 2 theta)
r_RL(theta) = r_RL(0) exp(-i 2 theta)
```

depending on convention and handedness.

The key asymmetric control rule is:

```text
selected handedness channel receives PB phase
opposite channel is suppressed, mirrored, or routed through the paired EP structure
```

For a mirror-symmetric pair of EP metastructures:

```text
S  -> EP handedness h
S_m -> EP handedness -h
```

This lets two orthogonal EP eigenmodes be superposed to address arbitrary fully polarized input states.

A compact arbitrary vectorial wavefront synthesis form is:

```text
E_out(x,y) = alpha(x,y) E_EP,h(x,y) + beta(x,y) E_EP,-h(x,y)
```

where the two EP basis responses are paired by mirror symmetry.

---

## 7. Poincare sphere / Jones evolution operator

A lossless polarization-sensitive device with orthonormal eigenstates can be represented through Pauli matrices:

```text
U(n_hat, delta) = exp(i phi) exp(i (delta/2) n_hat · sigma_hat)
```

where:

```text
n_hat       eigen Stokes vector on the Poincare sphere
sigma_hat   vector of Pauli matrices
phi         dynamic / propagation phase
delta       eigen birefringence phase difference
```

This gives a compact bridge between Jones optics and a two-level spin-state evolution model.

---

## 8. Pancharatnam-Berry phase from solid angle

For a closed polarization path on the Poincare sphere, the geometric phase is:

```text
gamma = -Omega / 2
```

where:

```text
Omega = solid angle swept by the polarization trajectory
```

For classical PB phase in circular conversion with eigenstate azimuth `psi`, the uploaded hidden-singularity paper describes:

```text
Omega_+ = 4 psi
Omega_- = 4 pi - Omega_+
```

and the cross-polarized channels acquire opposite geometric phases:

```text
gamma_+ = -gamma_- = -2 psi
```

This is the standard geometric-phase sign inversion between orthogonal circular channels.

---

## 9. Hidden co-polarized singular phase

The hidden-singularity mechanism extends phase control to co-polarized channels by exploiting phase circulation around a hidden singularity on the Poincare sphere.

A safe mathematical abstraction is:

```text
loop C encircles hidden singularity
→ phase circulation Gamma_C = integral_C A · dl
→ co-polarized phase shift
```

with topological winding:

```text
w(C, s0) != 0
```

where `s0` is the hidden singular point. The phase is protected by the loop's encirclement class, not merely by local dynamic phase.

For OTOM, this is useful because it separates:

```text
dynamic phase          = direct propagation/eigenvalue phase
PB phase               = cross-polarized geometric phase
co-polarized singular  = hidden-singularity winding phase
```

---

## 10. Nonlinear bilayer wavelength generation by broken symmetries

Zheng et al. (2026) add a nonlinear bilayer track: vertical stacking and horizontal displacement break symmetry both along and perpendicular to the propagation axis. The resulting bilayer structure couples photonic-crystal effects with metasurface guided-mode resonances and enhances third-harmonic generation.

Define the symmetry-breaking controls:

```text
d_z      = vertical stacking / layer separation asymmetry
Delta_x  = horizontal displacement between layers
B_z      = 1[d_z != 0]
B_x      = 1[Delta_x != 0]
B_multi  = B_z * B_x
```

A minimal bilayer nonlinear transfer abstraction is:

```text
E_out(3 omega) = eta_THG(B_z, B_x, Q_GMR, chi^(3)) E_in(omega)^3
```

where:

```text
E_out(3 omega) = generated third-harmonic field
E_in(omega)    = input fundamental field
chi^(3)         = third-order nonlinear susceptibility / effective nonlinear coefficient
Q_GMR           = coupled guided-mode resonance quality factor / enhancement proxy
eta_THG         = third-harmonic conversion efficiency
```

A bounded enhancement model is:

```text
eta_THG = eta_0 [1 + alpha_z B_z + alpha_x B_x + alpha_c B_z B_x] Q_GMR^2 |chi^(3)|^2
```

The important term is the coupling term:

```text
alpha_c B_z B_x
```

which records that simultaneous broken symmetries can enable enhancement beyond either broken symmetry alone.

A guided-mode resonance condition can be recorded abstractly as:

```text
beta_mode(omega) = k_parallel + m G
```

where:

```text
beta_mode   = guided mode propagation constant
k_parallel  = in-plane momentum of input field
G           = reciprocal lattice vector
m           = diffraction/order index
```

At third harmonic:

```text
omega_3 = 3 omega
lambda_3 = lambda / 3
```

so the nonlinear wavelength-generation channel is:

```text
lambda -> lambda / 3
```

for third-harmonic generation.

The OTOM-safe control map is:

```text
vertical broken symmetry
+ horizontal broken symmetry
+ guided-mode resonance coupling
→ enhanced third-harmonic generation
→ nonlinear wavelength conversion gate
```

This extends the bilayer model from linear/polarization-channel composition into nonlinear frequency conversion.

---

## 11. OTOM control map

The metasurface equation layer maps into OTOM as:

```text
Jones operator J(x,y)
→ channel-specific amplitude/phase target
→ geometric/proagation phase split
→ surface composition or EP asymmetry
→ Poincare-sphere phase routing
→ nonlinear symmetry-breaking wavelength conversion
→ finite measurement/gate artifact
```

This complements the structured-light chirality/spin equation layer:

```text
structured-light layer:
  propagation turns topological charge into S3 / spin / chirality textures

metasurface layer:
  surface operators prepare, route, split, asymmetrically select, or nonlinearly convert optical channels
```

Together they define a bounded optics stack:

```text
metasurface interface
→ polarization/Jones operator
→ topological phase mechanism
→ bilayer symmetry/coupling response
→ propagation or nonlinear wavelength response
→ Stokes/Poincare/frequency measurement
→ Warden-bounded gate
```

---

## Warden boundaries

### Blocked claims

```text
These metasurface papers prove OTOM.
Exceptional points prove arbitrary non-optical oracle behavior.
Hidden singularity on the Poincare sphere is equivalent to semantic mass or Sidon signatures.
PB phase is interchangeable with DeltaPhi without a bridge theorem.
A metasurface Jones equation validates non-optical manifold compression claims.
Third-harmonic generation proves non-optical manifold energy conversion.
Broken optical symmetry is equivalent to cognitive or semantic symmetry breaking.
```

### Allowed claims

```text
The equations are valid bounded optics-domain references for polarization, wavefront, and nonlinear wavelength control.
Jones matrices provide a rigorous interface model for local metasurface transformations.
Double-phase decomposition gives a useful amplitude/phase encoding mechanism.
Bilayer metasurfaces provide a physical example of composed surface propagation.
Exceptional points provide a source for asymmetric polarization-channel control.
Hidden singularity provides a source for topologically protected co-polarized phase control.
Broken vertical and horizontal bilayer symmetries can be recorded as optical gates for enhanced third-harmonic generation.
These equations can be used as analogical and mathematical scaffolding under explicit Warden boundaries.
```

## Strongest safe formulation

> The metasurface polarization-control equation layer records how local Jones operators, double-phase encoding, bilayer composition, exceptional-point asymmetry, Poincare-sphere hidden-singularity phase control, and broken-symmetry bilayer nonlinear generation can prepare, route, and convert optical channels. OTOM may use this as a bounded optics-domain math stack for interfaces, invariants, and measurement gates, not as validation of broader non-optical claims.
