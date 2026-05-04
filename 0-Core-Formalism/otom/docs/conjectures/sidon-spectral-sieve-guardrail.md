# Sidon Spectral Sieve Guardrail

**Status:** ANALOGY_WITH_FORMAL_GUARDRAILS  
**Target stack:** OTOM / Mass-Number Lens / Proof-Status Firewall / W-axis  
**Source problem:** Infinite Sidon set limsup density problem  

## Purpose

This note captures the safe version of reframing the Erdos-Sidon density problem in the Mass-Number / FNWH spectral-sieve language.

It is explicitly an analogy and stress-test frame, not a proof of the Erdos-Kruckeberg conjecture and not evidence for FNWH physical claims.

## Mathematical source problem

Let `A subset N` be a Sidon set. Define:

```text
sigma(A) = limsup_{N -> infinity} |A cap {1,...,N}| / sqrt(N)
```

Known from the provided source note:

```text
Erdos:        sigma >= 1/2 is possible.
Kruckeberg:  sigma >= 1/sqrt(2) is possible.
Erdos-Turan: sigma <= 1 for every infinite Sidon set.
Conjecture:  sigma = 1 may be possible.
```

For generalized `B_2[g]` sequences, the provided source records:

```text
B_2[2]: Kolountzakis constructed a sequence with limsup = 1.
B_2[g] for larger g: constructions by Cilleruelo and Trujillo.
```

## Corrected frame

The Sidon condition:

```text
a + b = c + d implies {a,b} = {c,d}
```

may be interpreted as a no-collision law for pairwise sums.

In spectral-sieve language:

```text
Sidon set          -> selected modes
pairwise sums      -> intermodulation products / two-mode beats
Sidon condition    -> no repeated two-mode collision
counting density   -> packing density of noncolliding modes
Erdos-Turan <= 1   -> hard upper packing bound
```

Safe statement:

```text
The Sidon problem is a clean mathematical analogue for collision-free packing under pairwise-combination constraints.
```

Unsafe statement:

```text
A simulated spectral sieve proves or empirically supports the Erdos-Kruckeberg conjecture.
```

## Why the prior simulation needs a guardrail

The pasted simulation used terms such as:

```text
6.5 sigma Super-Gaussian Regularization
thermal shock response
vacuum decay
phase liquefaction
sigma = 0.9997 stable state
```

These are useful as visualization metaphors only. They do not certify a Sidon construction and do not reduce the number-theoretic open problem.

The W-axis classification is therefore:

```text
Claim: Super-Gaussian sieve realizes sigma = 1 for Sidon sets.
Gate: P_analogy or U_scope, not R.
Reason: no explicit infinite Sidon construction and no proof of pairwise-sum uniqueness at limsup 1.
```

## Formal stress-test version

Instead of claiming a physical result, define a finite approximation test.

Let:

```text
A_N subset {1,...,N}
R_A(s) = |{(a,b) in A_N^2 : a <= b and a+b = s}|
collision_count(A_N) = sum_s max(0, R_A(s)-1)
rho_N(A_N) = |A_N| / sqrt(N)
```

Then:

```text
A_N is finite Sidon iff collision_count(A_N) = 0.
```

A spectral/lens model may be tested by whether its proposed mode set satisfies:

```text
collision_count(A_N) = 0
rho_N(A_N) close to target density
```

This is the correct conversion of the visual metaphor into an auditable mathematical test.

## Sidon Mass-Number Focus

Define a candidate focus:

```text
Focus_Sidon(A_N) := {
  density_score        = rho_N(A_N),
  collision_score      = 1 / (1 + collision_count(A_N)),
  pairwise_uniqueness  = indicator(collision_count(A_N) = 0),
  construction_receipt = explicit generator or witness list,
  residual_risk        = missing proof / missing construction / projection artifact
}
```

Candidate mass:

```text
M_Sidon(A_N)
= density_score * collision_score * construction_receipt_strength
  / (1 + residual_risk)
```

Promotion rule:

```text
Promoted finite Sidon focus requires explicit witness A_N and verified collision_count(A_N)=0.
Promoted infinite Sidon focus requires a construction plus proof of the limsup claim.
```

## Correct W-axis classifications

```text
Finite proposed set A_N with verified unique pairwise sums:
  R_finite

Finite proposed set A_N with collisions:
  X_constraint

Claim that limsup = 1 for Sidon sets without proof:
  U_scope

Claim that Super-Gaussian numerical plot proves limsup = 1:
  P_analogy -> rejected as R

B_2[2] limsup = 1 using Kolountzakis construction:
  R_reference, subject to cited construction
```

## The useful analogy

The analogy remains valuable if phrased correctly:

```text
Sidon sets model maximal noncolliding mode packing.
The Erdos-Turan upper bound is the hard packing ceiling.
The Erdos-Kruckeberg conjecture asks whether the ceiling is reachable along an infinite subsequence.
The Mass-Number Lens can treat proposed constructions as foci and collisions as residual leakage.
```

## Required controls

Any future Sidon-sieve claim must include:

```text
1. explicit A_N or constructive rule,
2. pairwise-sum collision audit,
3. density rho_N,
4. asymptotic argument if making infinite claims,
5. W-axis gate label,
6. separation between analogy, finite verification, and theorem.
```

## Lean target skeleton

```lean
namespace SidonSieve

abbrev NatSet := Nat -> Prop

def IsSidonFinite (A : Finset Nat) : Prop :=
  forall a in A, forall b in A, forall c in A, forall d in A,
    a <= b -> c <= d -> a + b = c + d -> (a = c and b = d)

-- collision_count(A)=0 iff IsSidonFinite A
theorem collision_zero_iff_sidon (A : Finset Nat) :
  CollisionCount A = 0 <-> IsSidonFinite A := by
  sorry

-- A density plot or spectral analogy alone cannot promote an infinite claim.
theorem analogy_not_infinite_sidon_proof (claim : Claim) :
  IsSpectralAnalogy claim -> Gate claim = P_analogy := by
  sorry

end SidonSieve
```

## Short doctrine

```text
Sidon is the no-collision law.
Density is the packing pressure.
Collisions are typed residuals.
Plots are witnesses only after the sums audit passes.
The conjecture stays U until construction and proof close the ledger.
```
