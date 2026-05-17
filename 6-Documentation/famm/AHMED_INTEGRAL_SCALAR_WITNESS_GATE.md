# Ahmed Integral Scalar Witness Gate

## Purpose

Add Ahmed's Integral as a definite-integral scalar witness gate.

The project-useful shape is:

```text
complicated analytic integrand
→ definite-integration projection
→ exact scalar witness
→ residual receipt
→ branch / precision / transform verification
```

## Source identity

Original paper metadata:

```text
Ahmed, Z.; Dale, Knut; Lamb, George.
Definitely an Integral: 10884.
The American Mathematical Monthly, 2002.
DOI: 10.2307/3072448.
```

Common identity:

```math
\int_{0}^{1}
\frac{\arctan\left(\sqrt{2+x^{2}}\right)}
{(1+x^{2})\sqrt{2+x^{2}}}
\,dx
=
\frac{5\pi^{2}}{96}
```

## Project name

```text
AHMED_INTEGRAL_SCALAR_WITNESS_GATE
```

## Universal Shortcut Center packet

```math
\Gamma_{\mathrm{Ahmed}}
=
(
X_f,
\pi_{\int},
W_{5\pi^2/96},
R_{\mathrm{verify}},
I_{\mathrm{area}},
G_{\mathrm{integrable}},
K,
\epsilon
)
```

| Packet term | Meaning |
|---|---|
| `X_f` | full arctangent/radical integrand manifold |
| `pi_int` | definite integration projection over `[0,1]` |
| `W_5pi2_96` | exact scalar witness `5*pi^2/96` |
| `R_verify` | analytic proof, high-precision quadrature, or symbolic reduction receipt |
| `I_area` | preserved accumulation / area invariant |
| `G_integrable` | branch, endpoint, convergence, and real-valuedness guards |
| `K` | symbolic/numeric/proof cost |
| `epsilon` | residual between evaluated and exact witness |

## Residual receipt

```math
R_{\mathrm{Ahmed}}
=
\left|
\int_{0}^{1}
\frac{\arctan\left(\sqrt{2+x^{2}}\right)}
{(1+x^{2})\sqrt{2+x^{2}}}
\,dx
-
\frac{5\pi^{2}}{96}
\right|
```

Pass condition:

```math
R_{\mathrm{Ahmed}}\le \Theta_{\mathrm{tol}}
```

## Why this differs from the polynomial-exponential ladder gate

The polynomial-exponential integral gate is a finite ladder collapse:

```text
repeated integration by parts
→ finite summation
→ derivative receipt
```

Ahmed's Integral is a hidden transform/scalar witness gate:

```text
arctangent + radical definite integral
→ special reduction / quadrature / probability-integral route
→ exact pi^2 scalar receipt
```

## Adversarial verification checks

The Warden should check:

```text
branch choice of arctan and square root
endpoint behavior on [0,1]
numeric precision / quadrature stability
symbolic transformation validity
hidden integrand perturbation that changes the scalar receipt
```

Formal hidden-perturbation check:

```math
h\in\ker \Pi_{\mathrm{metadata}}
\quad\text{but}\quad
\int_0^1 h(x)\,dx\ne0
```

Meaning:

```text
a perturbation is invisible to the current symbolic description,
but it changes the definite-integral scalar witness.
```

## FAMM object

```math
\mathfrak C_{\mathrm{AhmedIntegral}}
=
A_{16}(u_{\mathrm{ahmed}})
\otimes
[
\Sigma_f
+
\Sigma_{\int_0^1}
+
\Sigma_{\arctan}
+
\Sigma_{\sqrt{2+x^2}}
+
\Sigma_{5\pi^2/96}
+
\Sigma_{\epsilon}
+
\Sigma_{\mathrm{branch}}
+
\Sigma_{\mathrm{receipt}}
]
```

## Stack placement

```text
AHMED_INTEGRAL_SCALAR_WITNESS_GATE
→ Universal Shortcut Center Manifold
→ Builder-Judge-Warden
→ adversarial branch / precision checks
→ NUVMAP scalar witness node
→ exact / high-precision quadrature receipt
```

## Warden boundary

This gate records a definite-integral scalar witness and its project use. It does not claim every hard integral has the same structure or that numeric agreement alone is proof.

Allowed claim:

```text
Ahmed's Integral is a clean scalar-witness benchmark for checking whether a proposed analytic shortcut preserves the exact definite-integral value.
```

Disallowed claim:

```text
A numerical match to 5*pi^2/96 proves a new integral theorem without branch, endpoint, and proof receipts.
```

## Project sentence

Ahmed's Integral is a scalar witness gate: a complicated arctangent-radical integral collapses to `5*pi^2/96`, giving the stack a clean exact-receipt target where Builder proposes reductions, Judge verifies the scalar invariant, and the Warden checks hidden branch, precision, and transformation failures.
