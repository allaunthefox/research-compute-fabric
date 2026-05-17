# Anti-BraidStorm Hostile Crossing Gate

## Purpose

Anti-BraidStorm is the adversarial dual of BraidStorm. BraidStorm lets hypothesis strands cross, mutate, emit receipts, accumulate scars, and promote survivor surfaces. Anti-BraidStorm asks whether those survivors only survived friendly crossings.

```text
Anti-BraidStorm = the adversarial braid network that tries to make false survivors.
```

## Hostile crossing

A normal crossing is:

```math
\beta_{ij}:(s_i,s_j)\to(s_i',s_j',r_{ij},\epsilon_{ij},\Omega_{ij})
```

Anti-BraidStorm generates hostile crossings:

```math
\beta^{-}_{ij}
:
(s_i,s_j)
\to
(s_i',s_j',r^{\mathrm{fake}}_{ij},\epsilon^{\mathrm{hidden}}_{ij},\Omega^{\mathrm{masked}}_{ij})
```

The goal is to make a crossing appear locally valid while failing globally.

## Braid-order attack

```math
\Delta_{\mathrm{braid}}^{-}
=
\left\|
\beta_{ij}\beta_{jk}\beta_{ij}(S)
-
\beta_{jk}\beta_{ij}\beta_{jk}(S)
\right\|
```

If \(\Delta_{\mathrm{braid}}^{-}>\Theta_{\mathrm{braid}}\), crossing order matters too much and the survivor surface may be fake.

## Receipt-alias attack

A hostile crossing tries to make two different crossing histories share a receipt/address:

```math
H(\mathrm{history}_a)=H(\mathrm{history}_b)
\quad\text{while}\quad
I(\mathrm{history}_a)\ne I(\mathrm{history}_b)
```

This is where the BraidStorm Sidon Crossing Anti-Alias Gate participates.

## Stack placement

```text
BraidStorm crossing candidate
→ Sidon anti-alias check
→ Golden centering check
→ Anti-BraidStorm hostile crossing attack
→ Anti-FAMM shadow attack
→ Warden decision
→ promote / scar / coarsen / reject
```

## Project sentence

Anti-BraidStorm is the hostile crossing adversary for BraidStorm: it creates adversarial braid histories that look locally valid but fail globally, forcing survivor candidates to withstand receipt-alias, braid-order, chirality, scar-mask, and false-convergence attacks before promotion.
