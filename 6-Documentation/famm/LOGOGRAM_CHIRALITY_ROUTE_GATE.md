# Logogram Chirality Route Gate

## Purpose

Promote logogram chirality into the active FAMM equation stack **only where it is beneficial**.

The existing logogram/symbology design already requires direction, chirality, phase, placement, residual policy, and receipt hash for lawful atomization. This document adds the missing operational layer: chirality can become a route coordinate when orientation changes admissibility, transition legality, replay, or DAG identity.

## Canonical rule

```text
chirality is display metadata by default;
chirality becomes a route coordinate only when it changes admissibility.
```

## Chirality witness

```math
\chi_{\mathrm{logo}}
=
(d,\;h,\;\phi,\;p,\;m)
```

Where:

| Term | Meaning |
|---|---|
| `d` | direction |
| `h` | handedness / chirality |
| `phi` | phase |
| `p` | placement |
| `m` | mode / modifier family |

## Logogram atom

```math
L_i
=
(
\mathrm{id}_i,
\mathrm{payloadHash}_i,
\chi_{\mathrm{logo},i},
\mathrm{residualPolicy}_i,
\mathrm{receiptHash}_i
)
```

## Packet primitive upgrade

Current broad packet form:

```math
\Gamma_i
=
\gamma_i
\otimes
\chi_i
\otimes
\kappa_i
\otimes
\tau_i
\otimes
U_i\Lambda_i a_i
\otimes
\theta_i
\otimes
\epsilon_i
```

Upgrade:

```math
\boldsymbol{\chi}_i
=
[
\chi^{\mathrm{geom}},
\chi^{\mathrm{logo}},
\chi^{\mathrm{braid}},
\chi^{\mathrm{op}}
]_i
```

Then:

```math
\Gamma_i
=
\gamma_i
\otimes
\boldsymbol{\chi}_i
\otimes
\kappa_i
\otimes
\tau_i
\otimes
U_i\Lambda_i a_i
\otimes
\theta_i
\otimes
\epsilon_i
```

## Route probability upgrade

```math
P(\sigma_t=i\mid X_t)
\propto
\exp[
-\alpha d_i
-\beta\Omega_i
+\gamma I_i
-\eta C_i
+\lambda\mu_i
+\rho R_i
+\chi H_i
]
```

where:

```math
H_i
=
\operatorname{compat}
(
\chi_{\mathrm{state}},
\chi_{\mathrm{op}},
\chi_{\mathrm{logo}},
\chi_{\mathrm{surface}}
)
```

## Where it plugs in

| Layer | Use |
|---|---|
| FAMM | route score / scar class / invariant overlap |
| PIST | wrong-handed transition prevention |
| PIST-Chaos | operator sampling bias |
| NUVMAP DAG | projected node identity when chirality changes future legal moves |
| Delta stream | replayable orientation-changing event |
| GCCL-Rep | packet witness |
| AVM | deterministic replay input |

## Add-only-if-beneficial gate

Promote `chi_logo` to active routing only if at least one condition holds:

```text
1. It disambiguates two same-payload atoms.
2. It prevents a wrong-handed PIST transition.
3. It reduces NUVMAP false merges.
4. It improves replay determinism.
5. It yields a measurable route-shortening or residual reduction.
```

Otherwise keep it as metadata/receipt only.

## No-drift boundary

This is not a claim that glyph orientation has universal semantic meaning. The payload remains the canonical object. Chirality only participates when its receipt changes route legality, replay, admissibility, or compression outcome.

## Project sentence

Logogram chirality becomes beneficial when orientation changes admissibility: the same payload with different handedness can produce a different PIST transition, NUVMAP address, scar class, or replay receipt, so chirality must be promoted from glyph metadata into a first-class route witness.
