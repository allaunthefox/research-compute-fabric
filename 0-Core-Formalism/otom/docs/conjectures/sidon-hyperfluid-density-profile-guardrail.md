# Sidon Hyperfluid Density Profile Guardrail

**Status:** ANALOGY_WITH_PROOF_OBLIGATIONS  
**Target stack:** OTOM / Mass-Number Lens / Sidon Spectral Sieve / W-axis  
**Related:** `docs/conjectures/sidon-lifting-relaxation-program.md`

## Purpose

This note captures the latest hyperfluid / soliton-sweep framing for Sidon density profiles while preventing it from being promoted as a proof.

The pasted claim asserts a final result:

```text
p-adic Bose-Chowla lift
+ carry-free digit windows
+ CRT splicing
+ hyperfluid soliton sweep
=> sigma = 1 achieved and constant density impossible
```

This is a useful model of the desired closure mechanism, but it remains a research program until it supplies explicit construction receipts and theorem-level audits.

## Correct W-axis classification

```text
Gate: P_analogy + U_scope
```

Reason:

```text
1. No explicit infinite Sidon set A subset N is given.
2. No compatible lift chain A_k subset A_{k+1} is constructed.
3. No proof shows collision_count(A_k)=0 for every k.
4. No theorem proves the claimed O(log x) obstruction pressure.
5. No proof shows CRT splicing preserves global pairwise-sum uniqueness.
6. No proof shows limsup A(x)/sqrt(x) = 1 for the resulting single sequence.
7. No proof shows constant normalized density is impossible.
```

## Critical normalization correction

For Sidon density, the relevant normalization is:

```text
sigma(A) = limsup_{x -> infinity} A(x) / sqrt(x)
```

not:

```text
A(x) / x
```

A constant positive value of `A(x)/x` is impossible for Sidon sets because the standard counting bound gives `A(x) = O(sqrt(x))`. Therefore any hyperfluid discussion of constant density must specify whether it means:

```text
A(x) / sqrt(x) approximately constant
```

or the ordinary natural density:

```text
A(x) / x approximately constant.
```

The second cannot be positive for an infinite Sidon set.

## Carry-free digit window guardrail

The carry-free digit idea is a plausible mechanism for decoupling local windows, but it does not automatically preserve global Sidon uniqueness.

A carry-free digit set can prevent carries between windows:

```text
d_i + d_j < p
```

but a Sidon collision is global:

```text
a_i + a_j = a_k + a_l
```

So the proof must show uniqueness of the whole digit-vector sum, not merely absence of carries.

Required theorem target:

```text
CarryFree(A_k) + LocalSidonEachWindow(A_k) + Compatibility(A_k,A_{k+1})
  -> GlobalSidon(Unroll(A_k))
```

Status: `U_scope` until proved.

## CRT splicing guardrail

CRT splicing can combine congruence conditions, but Sidon uniqueness over integers is stronger than Sidon uniqueness modulo many finite moduli.

Required theorem target:

```text
If a_i + a_j = a_k + a_l in Z,
then the CRT residue data forces {i,j} = {k,l}.
```

This requires a global size/window bound preventing distinct integer sums from sharing all audited residues in the relevant range.

Status: `U_scope` until supplied.

## Hyperfluid / soliton interpretation

The hyperfluid model is retained as a diagnostic metaphor:

```text
integer coordinate      -> fluid coordinate
p-adic window           -> frequency band
Sidon collision         -> nonlinear phase collapse
admissible integer      -> low-residual slot
construction process    -> soliton sweep
oscillating density     -> pulsed admissibility profile
```

Safe statement:

```text
The hyperfluid model suggests that dense Sidon constructions, if possible, should appear as pulsed low-residual trajectories through structured algebraic windows.
```

Unsafe statement:

```text
The hyperfluid soliton sweep proves sigma = 1 or proves constant density impossible.
```

## Density-profile question

The refined, valid question is:

```text
Can any explicit infinite Sidon set have A(x)/sqrt(x) bounded away from zero and near one across long intervals, or must every high-limsup construction oscillate through sparse recovery zones?
```

A stronger question:

```text
Does there exist an infinite Sidon set A with A(x)/sqrt(x) -> c > 0?
```

This must be treated as a number-theoretic density-profile question, not settled by the hyperfluid analogy.

## Required closure receipts

To promote the hyperfluid/p-adic closure story, provide:

```text
1. explicit digit alphabet D_p,
2. explicit seed family A_k,
3. explicit lift rule from A_k to A_{k+1},
4. proof of carry-free or carry-controlled addition,
5. proof of global Sidon uniqueness after unrolling,
6. proof of density limsup A(x)/sqrt(x)=1,
7. optional theorem on oscillation or impossibility of constant A(x)/sqrt(x),
8. finite computational audits for initial levels.
```

## Lean target skeleton

```lean
namespace SidonHyperfluid

-- Hyperfluid curves and p-adic pressure plots are not proof objects.
theorem hyperfluidAnalogy_notSidonProof
  (claim : Claim) :
  HyperfluidSolitonAnalogy claim ->
  ¬ HasExplicitInfiniteSidonConstruction claim ->
  Gate claim = P_analogy := by
  sorry

-- Ordinary positive density is incompatible with Sidon square-root growth.
theorem positiveNaturalDensity_notSidonCompatible
  (A : Nat -> Prop) :
  IsInfiniteSidon A ->
  NotPositiveNaturalDensity A := by
  sorry

-- Carry-free local windows require a global unrolling theorem.
theorem carryFree_notEnoughWithoutGlobalAudit
  (chain : Nat -> Finset Nat) :
  CarryFreeDigits chain ->
  ¬ GlobalPairSumAudit chain ->
  Gate (ClaimFrom chain) = U_scope := by
  sorry

end SidonHyperfluid
```

## Short doctrine

```text
The hyperfluid picture is a lens, not a theorem.
Carry-free digits prevent carries, not automatically collisions.
CRT splices residues, not automatically global Sidon sums.
Sigma uses A(x)/sqrt(x), not A(x)/x.
Closure requires an explicit infinite construction plus a global sums audit.
```
