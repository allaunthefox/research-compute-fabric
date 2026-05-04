# Residual Energy Functional (AMREF)

## Purpose

This note defines AMREF as a silent finite spectral search objective. Audio rendering remains disabled by default.

```text
AUDIO_RENDER = false
```

## Carrier and Perturbation

```text
f_N[n] = sin(2*pi*f0*n/Fs + phi0), 0 <= n < N
P_A[n] = sum_{a in A} w_a sin(2*pi*a*n/N + phi_a)
g_N[n;epsilon,A] = f_N[n] + epsilon * P_A[n]
0 <= epsilon <= epsilon_max
```

## Filtered Remainder

```text
F_N[k;epsilon,A] = FFT(g_N[n;epsilon,A])
R_N[k;epsilon,A] = F_N[k;epsilon,A] - H_music[k] F_N[k;epsilon,A]
```

## Local Field

```text
E_{A,epsilon}(n,k) =
    |g_N[n;epsilon,A]|^2
  + lambda_R |R_N[k;epsilon,A]|^2
  + lambda_T tau_A(n,k)
  + lambda_V V_A(k)
  - lambda_M M_A(k)
  + lambda_Omega Omega_A(k)
```

## Search Score

```text
AMREFScore(A,epsilon) =
    lambda_R RemainderResonance(A;R_N)
  + lambda_V VoidFit(A)
  + lambda_T ControlledTorsion(A)
  - lambda_M MusicScore(A)
  - lambda_Omega RandomnessPenalty(A)
```

```text
A_star = argmax_A AMREFScore(A,epsilon)
```

## Sidon Boundary

AMREF can bias the search toward nonredundant finite sets, but it does not prove Sidon/B2 uniqueness by itself. Pair-sum uniqueness must be verified directly or enforced by nonseparable encoding.

Optional explicit collision penalty:

```text
C_B2(A) = sum_s max(0, mult_{A+A}(s)-1)
AMREF_B2Score(A,epsilon) = AMREFScore(A,epsilon) - lambda_B2 C_B2(A)
```

`A` is Sidon exactly when:

```text
C_B2(A) = 0
```

## Audit Classification

```text
Receipt: ResidualEnergyFunctionalAMREF
Status: FORMAL_OBJECTIVE_DRAFT
Gate: U_scope
Reason: coherent as a finite variational search objective, but requires explicit metric definitions, finite data runs, normalization, threshold calibration, randomness controls, collision penalties, and arithmetic audits.
```
