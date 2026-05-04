# Lorentz Variant Adapter Family

## Status

`BEAUTIFUL_PROVISIONAL`

This document defines the Lorentz family as a bounded transformation and invariance adapter family for OTOM.

The goal is not to treat “Lorentz” as one loose symbol. The goal is to separate the mathematically distinct Lorentz-family objects so they can be used without semantic collision.

---

## One-sentence definition

```text
Lorentz-family adapters are transformations, invariance laws, and local-frame structures that preserve a metric, causal cone, or relativistic force/field relation under a declared signature, domain, and group action.
```

---

## Core invariant

In special relativity, a Lorentz transformation `Lambda` preserves the Minkowski quadratic form:

```math
\Lambda^T\eta\Lambda=\eta
```

where the Minkowski metric may use either convention:

```math
\eta=\operatorname{diag}(-1,+1,+1,+1)
```

or:

```math
\eta=\operatorname{diag}(+1,-1,-1,-1)
```

The interval is invariant:

```math
s^2=\eta_{\mu\nu}x^\mu x^\nu
```

Admissibility requires the signature convention to be explicit.

---

## Variant taxonomy

| Variant | Symbol / form | Preserved structure | OTOM role |
|---|---|---|---|
| full Lorentz group | `O(1,3)` | Minkowski metric | full symmetry family |
| proper Lorentz group | `SO(1,3)` | metric + orientation | orientation-preserving transformations |
| proper orthochronous Lorentz group | `SO^+(1,3)` | metric + orientation + time orientation | physical connected component |
| spatial rotations | `SO(3)` subgroup | spatial norm within frame | frame reorientation |
| boosts | `B(v)` or `B(\varphi)` | interval and causal cone | inertial-frame translation in velocity/rapidity space |
| parity | `P` | metric, flips spatial orientation | discrete spatial inversion |
| time reversal | `T` | metric, flips time orientation | discrete temporal inversion |
| PT | `PT` | metric, flips both | combined discrete transformation |
| infinitesimal Lorentz algebra | `so(1,3)` | tangent generators | local linearized transformation |
| spinor cover | `SL(2,C)` | double cover of `SO^+(1,3)` | spinor/lifted representation |
| tensor transformation | index law | covariance of tensors | object transport law |
| field tensor transformation | `F' = Lambda F Lambda^T` | Maxwell covariance | electromagnetic field adapter |
| four-vector force | `dp^mu/dtau` | covariant dynamics | relativistic dynamics adapter |
| Lorentz force | `q(E+v×B)` / covariant form | charged-particle dynamics | force-law adapter |
| local Lorentz frame | tetrad/vierbein | tangent-space metric | curved-spacetime local adapter |
| Lorentzian manifold | `(M,g)` with signature `(1,n-1)` | causal structure | geometric domain adapter |
| conformal Lorentz relation | `g -> Omega^2 g` | null cone | causal/null-structure adapter |

---

## 1. Standard boost in one spatial direction

For a boost along `x` using `c=1`:

```math
\begin{aligned}
t' &= \gamma(t-vx) \\
x' &= \gamma(x-vt) \\
y' &= y \\
z' &= z
\end{aligned}
```

where:

```math
\gamma=\frac{1}{\sqrt{1-v^2}}
```

With units restored:

```math
\gamma=\frac{1}{\sqrt{1-v^2/c^2}}
```

---

## 2. Rapidity form

Define rapidity:

```math
\varphi=\operatorname{artanh}(v/c)
```

Then:

```math
\beta=\tanh\varphi
```

```math
\gamma=\cosh\varphi
```

```math
\gamma\beta=\sinh\varphi
```

The boost becomes a hyperbolic rotation:

```math
\begin{bmatrix}
ct' \\
x'
\end{bmatrix}
=
\begin{bmatrix}
\cosh\varphi & -\sinh\varphi \\
-\sinh\varphi & \cosh\varphi
\end{bmatrix}
\begin{bmatrix}
ct \\
x
\end{bmatrix}
```

Rapidity adds linearly for collinear boosts:

```math
\varphi_{total}=\varphi_1+\varphi_2
```

This makes rapidity the clean coordinate for boost composition.

---

## 3. Arbitrary-direction boost

Let `n` be a unit vector in the boost direction and decompose:

```math
\vec{x}=\vec{x}_{\parallel}+\vec{x}_{\perp}
```

where:

```math
\vec{x}_{\parallel}=(\vec{x}\cdot\vec{n})\vec{n}
```

Then:

```math
t'=\gamma\left(t-\frac{\vec{v}\cdot\vec{x}}{c^2}\right)
```

```math
\vec{x}'_{\parallel}=\gamma(\vec{x}_{\parallel}-\vec{v}t)
```

```math
\vec{x}'_{\perp}=\vec{x}_{\perp}
```

---

## 4. Rotations as Lorentz subgroup

Spatial rotations preserve time and rotate space:

```math
\Lambda_R=
\begin{bmatrix}
1 & 0 \\
0 & R
\end{bmatrix}
```

where:

```math
R\in SO(3)
```

These preserve the Minkowski metric and sit inside the Lorentz group.

---

## 5. Discrete Lorentz transformations

Parity:

```math
P=\operatorname{diag}(1,-1,-1,-1)
```

Time reversal:

```math
T=\operatorname{diag}(-1,1,1,1)
```

Combined PT:

```math
PT=\operatorname{diag}(-1,-1,-1,-1)
```

These preserve the metric but change orientation and/or time orientation. They must not be silently merged with the proper orthochronous component.

---

## 6. Lorentz algebra

The Lie algebra condition is:

```math
X^T\eta+\eta X=0
```

In four dimensions, there are six generators:

```text
3 rotations + 3 boosts
```

Commutation relations:

```math
[J_i,J_j]=\epsilon_{ijk}J_k
```

```math
[J_i,K_j]=\epsilon_{ijk}K_k
```

```math
[K_i,K_j]=-\epsilon_{ijk}J_k
```

The minus sign in the boost-boost commutator is the signature mark of Lorentzian geometry.

---

## 7. Four-vector adapter

A four-vector transforms as:

```math
V'^\mu=\Lambda^\mu{}_\nu V^\nu
```

Scalar contraction is invariant:

```math
V_\mu V^\mu = \eta_{\mu\nu}V^\mu V^\nu
```

OTOM adapter:

```math
\alpha_{4vec}:(V,\Lambda,\eta)\rightarrow V'
```

Admissibility:

```math
\Lambda^T\eta\Lambda=\eta
```

---

## 8. Tensor adapter

A rank `(r,s)` tensor transforms by applying `Lambda` to each contravariant index and inverse/dual transformation to each covariant index.

For a rank-2 contravariant tensor:

```math
T'^{\mu\nu}=\Lambda^\mu{}_{\alpha}\Lambda^\nu{}_{\beta}T^{\alpha\beta}
```

For a covariant tensor:

```math
T'_{\mu\nu}=\Lambda^{\alpha}{}_{\mu}\Lambda^{\beta}{}_{\nu}T_{\alpha\beta}
```

Index placement is part of the adapter domain. Dropping it causes semantic collision.

---

## 9. Electromagnetic field tensor adapter

The electromagnetic field tensor transforms as:

```math
F'^{\mu\nu}=\Lambda^\mu{}_{\alpha}\Lambda^\nu{}_{\beta}F^{\alpha\beta}
```

This mixes electric and magnetic fields under boosts.

Bounded claim:

```text
Electric and magnetic fields are frame-dependent components of a single antisymmetric tensor.
```

Forbidden overclaim:

```text
Every field-mixing phenomenon is Lorentzian.
```

---

## 10. Lorentz force adapter

Three-vector form:

```math
\vec{F}=q(\vec{E}+\vec{v}\times\vec{B})
```

Covariant form:

```math
\frac{dp^\mu}{d\tau}=qF^{\mu\nu}u_\nu
```

This is a dynamics/force adapter, not the same object as a Lorentz transformation.

Guardrail:

```text
Lorentz transformation != Lorentz force
```

They share historical naming and relativistic compatibility, but they are different adapter classes.

---

## 11. Spinor / double-cover adapter

The proper orthochronous Lorentz group has a double cover:

```math
SL(2,\mathbb{C}) \rightarrow SO^+(1,3)
```

A Minkowski vector can be represented as a Hermitian matrix:

```math
X=x^\mu\sigma_\mu
```

with transformation:

```math
X' = A X A^\dagger
```

where:

```math
A\in SL(2,\mathbb{C})
```

This adapter is necessary for spinor-bearing systems. It should not be collapsed into ordinary vector transformation.

---

## 12. Lorentzian manifold adapter

A Lorentzian manifold is:

```math
(M,g)
```

where `g` has Lorentzian signature, commonly:

```math
(-,+,+,+)
```

or:

```math
(+,-,-,-)
```

The metric defines:

```text
timelike / null / spacelike
```

separation and causal cones.

OTOM role:

```text
Lorentzian manifold = domain where causal structure is part of the geometry.
```

---

## 13. Tetrad / local Lorentz adapter

In curved spacetime, local inertial frames use a tetrad/vierbein:

```math
g_{\mu\nu}=e^a{}_{\mu}e^b{}_{\nu}\eta_{ab}
```

Local Lorentz transformations act on the internal frame index:

```math
e'^a{}_{\mu}=\Lambda^a{}_b e^b{}_{\mu}
```

This is a local gauge/frame adapter, not a global inertial-frame transformation.

---

## 14. Velocity addition adapter

Collinear velocity addition:

```math
u=\frac{u+v}{1+uv/c^2}
```

Rapidity version:

```math
\varphi_u+\varphi_v=\varphi_{total}
```

Use rapidity for composition whenever possible to avoid algebraic drift.

---

## 15. Doppler and aberration adapters

Relativistic Doppler shift:

```math
f'=f\sqrt{\frac{1-\beta}{1+\beta}}
```

for recession along the line of sight under the chosen convention.

Aberration relation:

```math
\cos\theta'=\frac{\cos\theta-\beta}{1-\beta\cos\theta}
```

These are observational adapters derived from Lorentz transformations. They should be bounded to signal/light propagation contexts.

---

## 16. Conformal Lorentz / null-cone adapter

A conformal transformation preserves the metric up to scale:

```math
g'_{\mu\nu}=\Omega^2 g_{\mu\nu}
```

This preserves null cones but not lengths.

Bounded role:

```text
conformal-Lorentz structure preserves causal/null geometry, not full metric scale.
```

---

## 17. OTOM mapping

| Lorentz object | Preserved witness | Adapter role |
|---|---|---|
| `Lambda` | `Lambda^T eta Lambda = eta` | metric-preserving transform |
| boost | interval + causal cone | inertial-frame velocity transform |
| rapidity | additive boost coordinate | composition-safe boost parameter |
| rotation | spatial metric in frame | frame reorientation |
| parity/time reversal | metric but not orientation/time-orientation | discrete symmetry branch |
| four-vector law | scalar contraction | covariant object transport |
| tensor law | index-aware covariance | structured field transport |
| `F^{mu nu}` | EM covariance | field-mixing adapter |
| Lorentz force | covariant charged-particle dynamics | dynamics adapter |
| spinor cover | double-cover representation | spinor/quantum representation adapter |
| tetrad | local tangent metric | curved-spacetime local-frame adapter |
| Lorentzian manifold | causal cone | geometric domain adapter |

---

## Relation to Cramer's-rule adapter

Cramer's rule taught the rule:

```text
hold a reference interface fixed, replace one direction, measure signed response.
```

Lorentz adapters teach a complementary rule:

```text
change frame, preserve the metric witness.
```

The invariant is no longer a shared determinant face; it is the interval/metric form.

```text
Cramer: preserve reference face.
Lorentz: preserve causal metric.
```

---

## Relation to SCW-8192

SCW-8192 uses salt, schema, adapter class, and evidence state to preserve interpretation context.

Bounded analogy:

```text
Lorentz transformation preserves metric context across frames.
SCW-8192 preserves causal interpretation context across artifact lineages.
```

Forbidden overclaim:

```text
SCW-8192 is physically Lorentzian.
```

Allowed claim:

```text
Lorentz invariance is a clean model of context-preserving transformation: the coordinates change, but the declared invariant remains stable.
```

---

## Failure modes

| Failure | Meaning |
|---|---|
| metric signature omitted | sign errors and invalid invariance checks |
| boost and rotation merged | group structure lost |
| proper/improper components conflated | orientation/time-orientation erased |
| Lorentz force confused with Lorentz transform | adapter-class collision |
| global Lorentz transform used in curved spacetime | local/global domain error |
| spinor cover collapsed into vector rep | representation error |
| units omitted | `c=1` convention misapplied |
| tensor indices ignored | covariance law corrupted |
| analogy overextended | physical invariance used as semantic proof |

---

## Claim ladder

### `BEAUTIFUL_PROVISIONAL`

- Use Lorentz variants as a taxonomy of context-preserving transformation families.
- Use Lorentz invariance as analogy for adapter-bound transformation.

### `CALIBRATED_ENGINEERING_DELTA`

- Implement explicit matrix checks for `Lambda^T eta Lambda = eta`.
- Add rapidity/boost composition tests.
- Add tensor-index transformation tests.

### `REVIEWED`

- Formalize Lorentz group invariance in Lean.
- Prove interval preservation for declared metric signature.
- Prove group closure for selected variant component.

---

## Minimal implementation checklist

- [ ] Define metric signature enum.
- [ ] Define Lorentz matrix admissibility check.
- [ ] Define variant enum: boost, rotation, parity, time reversal, PT, tensor, spinor, local-frame, force-law.
- [ ] Add determinant/orientation checks.
- [ ] Add rapidity composition test.
- [ ] Add four-vector interval-preservation test.
- [ ] Add tensor transformation test.
- [ ] Add Lorentz force as separate adapter class.
- [ ] Add local Lorentz/tetrad guardrail.
- [ ] Add forbidden-overclaim tests in documentation.

---

## Summary

```text
Lorentz is not one adapter. It is a family of metric-, causal-, representation-, and force-preserving adapters that must be separated by domain, signature, group component, and representation.
```

The core lawful pattern is:

```text
coordinates may change; the declared invariant must not.
```
