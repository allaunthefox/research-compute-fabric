# Finite Timelike Emission Set Audit

## Purpose

This note records the temporal correction to the lossy throat / phonon selector model:

```text
Because the signal is emitted through a physical, timelike process, the temporal coordinates cannot be treated as infinite free coordinates.
They are finite, bounded, and constrained by causal support, energy budget, lifetime, bandwidth, and observation window.
```

This strengthens the model by preventing an unphysical escape route where a construction hides arbitrarily many active events in unlimited temporal degrees of freedom.

## Core Statement

```text
finite timelike emission set
-> finite temporal support
-> finite number of recoverable phonon packets
-> finite active-cell window per scale N
-> no infinite temporal cheating
-> density proof must count recoverable events inside the finite causal window
```

## Corrected Doctrine

The throat is already modeled as a lossy torsional corridor, not a stable bridge. The new constraint is that the corridor also has finite timelike support.

For a physical emission event, define:

```text
T_emit(N) = [t_0(N), t_1(N)]
```

with finite duration:

```text
Delta T_N = t_1(N) - t_0(N) < infinity
```

A cell can be active only if it lies inside both the spatial/material gate and the finite temporal emission window:

```text
chi_N(i,t) = 1 iff
  t in T_emit(N)
  and BurgersGradientGate_N(i,t)
  and BandGapPhononGate_N(i,t)
  and PhononModeOverlap_i(t) >= eta_min(N)
  and Survivability_i(t) >= I_min(N)
```

## Timelike Emission Set

Define the finite emission set:

```text
E_N = { (i,t) : 1 <= i <= N, t in T_emit(N), chi_N(i,t)=1 }
```

The projected active index set is:

```text
I_active(N) = { i <= N : exists t in T_emit(N), (i,t) in E_N }
```

This is the set that can be passed into the non-separable algebraic encoding layer.

## Physical Constraints

The temporal coordinate is finite because of:

```text
causal propagation speed <= c or material sound speed v_s
finite shock-front lifetime
finite energy in the emission packet
finite phonon coherence time
finite relaxation time before dissipation
finite observation and decoding window
finite bandwidth / sampling resolution
finite material fatigue and damage budget
```

## Lossy Throat Update

The previous information law remains:

```text
I_out = I_in * exp(-L_throat) * R_repair
```

but the loss integral is now taken only over finite timelike support:

```text
L_throat(N) = integral_{gamma restricted to T_emit(N)} [
  lambda_T ||T(p,t)||^2
  + lambda_kappa |kappa(p,t)|
  + lambda_chi chi_mismatch(p,t)
  + lambda_mu memory_strain(p,t)
  + lambda_beta boundary_stress(p,t)
] dp dt
```

Admissibility requires:

```text
I_out / I_in >= I_min(N)
rho_out >= rho_min(N)
mu_out <= mu_max(N)
beta_out <= beta_max(N)
RepairRate_N > DegradationRate_N
```

within the finite time interval.

## Consequence for Active-Cell Counting

The density target is still:

```text
|I_active(N)| ~ sqrt(N)
```

but this must now be proven under finite temporal support:

```text
|{ i <= N : exists t in T_emit(N), chi_N(i,t)=1 }| / sqrt(N) -> 1 in limsup
```

This separates two receipts:

```text
TemporalFinitenessReceipt: Delta T_N < infinity
ActiveCellCountingReceipt: finite-window active count scales like sqrt(N)
```

The first is physically mandatory. The second is a nontrivial scaling theorem.

## No Infinite Temporal Cheating Rule

The construction may not claim density by allowing unlimited emission time for fixed N.

Forbidden:

```text
For fixed N, let T_emit -> infinity until enough cells activate.
```

Allowed:

```text
Choose a scale-dependent but finite T_emit(N), viscosity nu_N, threshold theta_N, and shock schedule, then prove the active count inside that finite window.
```

## Handoff to Algebraic Layer

The temporal layer only selects recoverable events:

```text
finite lossy throat + phonon gate + timelike emission window -> I_active(N)
```

The Sidon property still requires:

```text
A_N = { Phi(i) : i in I_active(N) }
Phi(a)+Phi(b)=Phi(c)+Phi(d) -> {a,b}={c,d}
```

If the model uses a virtual pair state, the condition is:

```text
S_N(a,b) = Phi_N(a)+Phi_N(b)+Lambda_N(a,b)
S_N(a,b)=S_N(c,d) -> {a,b}={c,d}
```

where `Lambda_N` must be non-separable and collision-penalizing.

## Lean-Oriented Skeleton

```lean
structure FiniteTimelikeEmissionReceipt where
  T_emit : Nat -> Set Nat
  finite_time : forall N, (T_emit N).Finite

structure RecoverableEventReceipt where
  active : Nat -> Nat -> Prop
  survivable : Nat -> Nat -> Prop
  active_implies_survivable : forall i t, active i t -> survivable i t

structure FiniteActiveSetReceipt where
  I_active : Nat -> Set Nat
  finite_active : forall N, (I_active N).Finite
  projected_from_time : forall N i,
    i in I_active N -> exists t, t in T_emit N ∧ active i t

structure ActiveCellCountingReceipt where
  sqrt_density_limsup_one : Prop
```

## Audit Classification

```text
Receipt: FiniteTimelikeEmissionSet
Status: FORMAL_CONSTRAINT_DRAFT
Gate: U_scope
Reason: finite timelike support is physically mandatory, but scale functions T_emit(N), nu_N, theta_N, eta_min(N), and the active-cell counting theorem still need explicit definitions and proof.
```

## Required Receipts

```text
TemporalFinitenessReceipt
CausalSupportReceipt
FiniteEnergyReceipt
FiniteBandwidthReceipt
PhononCoherenceTimeReceipt
FiniteWindowActiveCountingReceipt
ScaleTuningReceipt
NonseparableEncodingReceipt
```

## Boundary

This note does not prove the Sidon theorem. It prevents overclaiming by forcing every active cell to arise from a finite recoverable timelike emission event.

Correct doctrine:

```text
The throat is lossy, torsional, and finite in time.
Only recoverable phonon events inside the finite timelike emission window may be counted.
The resulting active indices must still be passed through a non-separable algebraic lock to obtain Sidon pair-sum injectivity.
```
