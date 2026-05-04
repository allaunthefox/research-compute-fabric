# Two-Layer Kinetic-Sidon Equations v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This spec records the equation-level form of the two-layer kinetic/Sidon standing-wave lattice. It preserves the full model from the recovered equation block while keeping the boundary explicit: this is a mathematical/computational scaffold, not a claim about a realized physical material phase.

## Core architecture

```text
Layer K: kinetic standing-wave field
Layer S: Sidon relational address field
Flow K -> S: quantize pairwise kinetic relations into signatures
Flow S -> K: feed alias-free relational structure back into the kinetic update
```

The kinetic layer evolves motion. The Sidon layer assigns collision-resistant relational addresses to pairwise kinetic events. Lawful compression requires that the Sidon layer be alias-free and that reconstruction error remain bounded.

## 1. Kinetic field

Let `u(x,y,t)` be a scalar field on a square domain:

```text
Omega = [0,L] x [0,L]
```

The undriven kinetic substrate is the 2D wave equation:

```text
u_tt = c^2 nabla^2 u
```

Expanded:

```text
partial^2 u / partial t^2 = c^2 (partial^2 u / partial x^2 + partial^2 u / partial y^2)
```

With damping, triangle-wave forcing, and Sidon feedback, the full kinetic equation is:

```text
u_tt = c^2 nabla^2 u - zeta u_t + T(x,y,t) + F_S(x,y,t)
```

where:

```text
c     = wave speed
zeta  = damping coefficient
T     = triangle-wave standing driver
F_S   = feedback from the Sidon relational layer
```

## 2. Standing-wave expansion

For fixed square boundaries:

```text
u(0,y,t) = u(L,y,t) = u(x,0,t) = u(x,L,t) = 0
```

the spatial modes are:

```text
psi_mn(x,y) = sin(m pi x / L) sin(n pi y / L)
```

The angular frequencies are:

```text
omega_mn = (c pi / L) sqrt(m^2 + n^2)
```

The standing-wave expansion is:

```text
u(x,y,t) = sum_m sum_n A_mn sin(m pi x/L) sin(n pi y/L) cos(omega_mn t + alpha_mn)
```

This is the kinetic substrate before relational addressing.

## 3. Triangle-wave driver

Define a normalized triangle wave:

```text
Tri(z) = 1 - 2 | frac(z / 2pi) - 1/2 |
```

A standing triangle-wave driver is:

```text
T(x,y,t) = B Tri(Omega t + k dot p + eta) + B Tri(Omega t - k dot p + eta)
```

where:

```text
p = (x,y)
B = driver amplitude
Omega = driver angular frequency
k = spatial wavevector
eta = phase offset
```

Triangle-wave forcing matters because it creates snap points, clean reversals, clocked phase corridors, and compression-friendly discrete contour events.

## 4. Observable contour surface

The rendered or observable field is not necessarily the raw wave amplitude. It can be the contour transform:

```text
I(x,y,t) = | sin(kappa u(x,y,t) + beta) |
```

A thresholded contour surface can be written:

```text
I_tau(x,y,t) = H(|sin(kappa u(x,y,t) + beta)| - tau)
```

Contour events are level-crossing sets:

```text
C_q(t) = { (x,y) : kappa u(x,y,t) + beta = q pi }
```

Equivalently:

```text
u(x,y,t) = (q pi - beta) / kappa
```

These contour crossings are the observable events that can be encoded into the Sidon address layer.

## 5. Lattice sampling

Sample the domain at lattice sites:

```text
p_i = (x_i, y_i), i = 1,...,N
```

The local kinetic state at site `i` is:

```text
K_i(t) = (u_i(t), u_dot_i(t), grad u_i(t), nabla^2 u_i(t), theta_i(t), E_i(t))
```

Definitions:

```text
u_i(t)       = u(p_i,t)
u_dot_i(t)   = partial_t u(p_i,t)
theta_i(t)   = arg(u_i(t) + i u_dot_i(t))
E_i(t)       = 1/2 u_dot_i(t)^2 + c^2/2 ||grad u_i(t)||^2
```

## 6. Pairwise kinetic relation

For any unordered pair `{i,j}`, define:

```text
R_ij(t) = (d_ij, Delta u_ij, Delta theta_ij, Delta E_ij, Gamma_ij)
```

with:

```text
d_ij             = ||p_i - p_j||
Delta u_ij(t)    = u_i(t) - u_j(t)
Delta theta_ij(t)= wrap_2pi(theta_i(t) - theta_j(t))
Delta E_ij(t)    = E_i(t) - E_j(t)
Gamma_ij(t)      = grad u_i(t) dot grad u_j(t)
```

This is the raw pairwise kinetic material passed to the Sidon layer.

## 7. Sidon relational signature map

Define a signature map:

```text
sigma_t : {i,j} -> Z
```

that converts pairwise kinetic relations into discrete Sidon addresses:

```text
sigma_ij(t) = h(Q(R_ij(t)))
```

Expanded:

```text
sigma_ij(t) = h(Q_d(d_ij), Q_u(Delta u_ij), Q_theta(Delta theta_ij), Q_E(Delta E_ij), Q_Gamma(Gamma_ij), Q_c(C_i,C_j))
```

A linear integer form is:

```text
sigma_ij(t) = a1 Q_d(d_ij) + a2 Q_u(Delta u_ij) + a3 Q_theta(Delta theta_ij) + a4 Q_E(Delta E_ij) + a5 Q_Gamma(Gamma_ij) + a6 Q_c(C_i,C_j)
```

where:

```text
Q = quantizer
h = hash / integer encoder
C_i, C_j = contour-crossing labels at sites i and j
```

The coefficients or hash family should be chosen to minimize collisions under the target quantization regime.

## 8. Sidon anti-aliasing condition

Classical Sidon uniqueness:

```text
a + b = c + d => {a,b} = {c,d}
```

Pair-address Sidon uniqueness:

```text
sigma_ij(t) = sigma_kl(t) => {i,j} = {k,l}
```

This is the core anti-aliasing law:

```text
No two different pairwise kinetic relations may collapse into the same Sidon address.
```

Define the alias penalty:

```text
A_S(t) = sum_{{i,j} != {k,l}} 1[sigma_ij(t) = sigma_kl(t)]
```

A perfect Sidon layer satisfies:

```text
A_S(t) = 0
```

The Sidon gate is:

```text
G_S(t) = 1 iff A_S(t) = 0
```

## 9. Flow from kinetic layer to Sidon layer

Forward flow:

```text
F_{K->S}: R_ij(t) -> sigma_ij(t)
```

Explicitly:

```text
F_{K->S}(i,j,t) = sigma_ij(t) = h(Q(R_ij(t)))
```

This is where the kinetic field becomes relationally addressable.

## 10. Flow from Sidon layer back to kinetic layer

The Sidon layer feeds back into the kinetic equation by suppressing aliasing and reinforcing uniquely addressed relations.

Define:

```text
F_S(x,y,t) = sum_{i<j} W_ij(t) Phi_ij(x,y)
```

where:

```text
W_ij(t) = rho chi_S(i,j,t) g(sigma_ij(t))
```

and:

```text
chi_S(i,j,t) = 1 if sigma_ij(t) is unique
chi_S(i,j,t) = 0 if sigma_ij(t) aliases
```

A pair kernel can be:

```text
Phi_ij(x,y) = exp(-(||p-p_i||^2 + ||p-p_j||^2)/(2r^2)) cos(theta_i - theta_j)
```

So the complete feedback equation is:

```text
u_tt = c^2 nabla^2 u - zeta u_t + T(x,y,t) + sum_{i<j} rho chi_S(i,j,t) g(sigma_ij(t)) Phi_ij(x,y)
```

## 11. Quaternion rotor extension

Each site may carry a quaternion-like rotor:

```text
q_i(t) = a_i(t) + b_i(t)i + c_i(t)j + d_i(t)k
```

with unit constraint:

```text
||q_i(t)||^2 = a_i^2 + b_i^2 + c_i^2 + d_i^2 = 1
```

The relative pair rotor is:

```text
Delta q_ij(t) = q_i(t)^(-1) q_j(t)
```

The signature may use:

```text
sigma_ij(t) = h(Q(Delta q_ij), Q(Delta u_ij), Q(Delta theta_ij), Q(d_ij))
```

Quaternion Sidon gate:

```text
h(Delta q_ij, Delta u_ij, Delta theta_ij, d_ij) = h(Delta q_kl, Delta u_kl, Delta theta_kl, d_kl)
=> {i,j} = {k,l}
```

## 12. Compression and reconstruction

The raw kinetic field is high-dimensional:

```text
u(x,y,t)
```

The compressed state is the Sidon-addressed event set:

```text
C(t) = { (i,j,sigma_ij(t),W_ij(t)) : i<j, chi_S(i,j,t)=1 }
```

Encoder:

```text
Enc(u(t)) = C(t)
```

Decoder:

```text
u_hat(x,y,t) = sum_{i<j} W_ij(t) Phi_ij(x,y) + sum_{m,n} A_hat_mn psi_mn(x,y) cos(omega_mn t + alpha_hat_mn)
```

Reconstruction error:

```text
E_rec(t) = integral_Omega |u(x,y,t) - u_hat(x,y,t)|^2 dx dy
```

Lawful compression requires:

```text
E_rec(t) <= epsilon_rec
A_S(t) = 0
```

Compression gate:

```text
G_compress(t) = 1 iff A_S(t)=0 and E_rec(t) <= epsilon_rec
```

## 13. Full model block

```text
u_tt
= c^2 nabla^2 u - zeta u_t + T(x,y,t) + F_S(x,y,t)

T(x,y,t)
= B Tri(Omega t + k dot p + eta) + B Tri(Omega t - k dot p + eta)

I(x,y,t)
= |sin(kappa u(x,y,t) + beta)|

R_ij(t)
= (d_ij, Delta u_ij, Delta theta_ij, Delta E_ij, Gamma_ij)

sigma_ij(t)
= h(Q(R_ij(t)))

A_S(t)
= sum_{{i,j}!={k,l}} 1[sigma_ij(t)=sigma_kl(t)]

F_S(x,y,t)
= sum_{i<j} rho chi_S(i,j,t) g(sigma_ij(t)) Phi_ij(x,y)

G_compress(t)
= 1 iff A_S(t)=0 and E_rec(t) <= epsilon_rec
```

## 14. Warden boundaries

### Blocked claims

```text
The equation system proves a real material phase.
The Sidon layer solves the PDE.
The contour rendering is identical to the underlying wave field.
Alias-free signatures guarantee physical truth.
```

### Allowed claims

```text
The system defines a two-layer mathematical/computational scaffold.
The kinetic layer governs motion.
The contour transform discretizes observable events.
The Sidon layer supplies relational anti-aliasing.
The compression gate requires alias-free addresses and bounded reconstruction error.
```

## Strongest formulation

> The kinetic layer evolves a driven standing-wave field. The contour transform discretizes observable phase crossings. The Sidon layer assigns collision-resistant relational addresses to pairwise kinetic events. The feedback term reinforces addressable relations and suppresses aliases. Compression is lawful only when the Sidon alias count is zero and reconstruction error remains bounded.
