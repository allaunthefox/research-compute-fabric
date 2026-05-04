# Sidon Lifting Relaxation Program

**Status:** RESEARCH_PROGRAM_DRAFT_WITH_GUARDRAILS  
**Target stack:** OTOM / Mass-Number Lens / Sidon Spectral Sieve / W-axis  
**Question:** What algebraic transformations could relax dense finite Sidon foci into an extendable infinite sequence?

## Purpose

This document refines the Sidon Extension-Focus Question into a constructive research program.

The prior guardrail established:

```text
Plots and pressure metaphors are not proofs.
Finite Sidon witnesses require collision_count(A_N)=0.
Infinite density claims require an explicit construction plus asymptotic proof.
```

The next question is constructive:

```text
Can a lawful algebraic transformation reduce effective collision pressure while preserving pairwise-sum uniqueness, and can that transformation be iterated into one infinite Sidon sequence?
```

## P-adic Bose-Chowla proof-risk firewall

A proposed p-adic Bose-Chowla lift was considered:

```text
Bose-Chowla finite seed
-> p-adic digit-window lift
-> claimed compression of quadratic collision pressure to logarithmic pressure
-> claimed proof of sigma = 1
```

This must not be recorded as a proof.

Correct W-axis classification:

```text
Gate: P_analogy + U_scope
Reason: the proposal does not yet provide an explicit compatible lift chain,
        a verified collision audit at each level,
        or an asymptotic proof that |A_k| / sqrt(N_k) -> 1 in one infinite Sidon set.
```

The statement:

```text
p-adic digit windows reduce collision pressure from O(x^2) to O(log x)
```

is a heuristic target, not an established theorem in this stack. It becomes admissible only after proving a bound of the form:

```text
|Forbidden(A_k) cap [1,N_k]| <= polylog(N_k)
```

or another explicit subquadratic obstruction bound strong enough to keep extension freedom open while preserving pairwise-sum uniqueness.

## Corrected core warning

A naive embedding

```text
F_p -> F_{p^2}
```

is not automatically useful for Sidon extension. If the map is purely additive and injective, then pairwise-sum collisions are preserved exactly:

```text
T(a)+T(b)=T(c)+T(d) iff T(a+b)=T(c+d) iff a+b=c+d.
```

So additive field inclusion gives more ambient notation, but it does not by itself create new Sidon slack.

The useful transformations must change the collision geometry, not merely relabel it.

## Candidate lawful transformations

### 1. Projective-plane / Singer transformation

Singer constructions use cyclic groups associated with finite projective geometry to produce dense finite Sidon or difference-set witnesses.

```text
finite projective plane
-> cyclic difference set / modular Sidon structure
-> dense finite no-collision focus
```

Role:

```text
Creates high-density finite foci with strong algebraic symmetry.
```

Failure mode:

```text
Rigid finite structures do not automatically nest into one infinite Sidon sequence.
```

### 2. Bose-Chowla / finite-field logarithmic transformation

Instead of relying on additive inclusion, use multiplicative structure and exponent/log coordinates.

```text
finite field multiplicative group
-> exponent/log coordinate
-> modular Sidon/B_h constraints
```

Role:

```text
Changes the additive collision audit by passing through a multiplicative cyclic geometry.
```

Failure mode:

```text
Requires careful unrolling from modular/cyclic setting into integer intervals.
```

### 3. p-adic lifting tower

The p-adic shortcut is not simply `F_p -> F_{p^2}`. The stronger version is a tower of compatible residue classes:

```text
A_k subset Z / p^k Z
A_{k+1} subset Z / p^{k+1} Z
A_{k+1} mod p^k = A_k
```

The constructive task is to choose lift digits:

```text
a' = a + p^k t_a
```

so that the lifted set remains collision-free modulo `p^{k+1}` or in a controlled integer window.

Role:

```text
Turns extension into a digit-by-digit constraint satisfaction problem.
```

Failure mode:

```text
The number of forbidden digit choices can saturate the lift space unless algebraic overlap compresses the obstruction set.
```

Required p-adic lift receipts:

```text
1. explicit seed A_1,
2. explicit digit-choice rule t_a for every lift level,
3. proof that A_{k+1} mod p^k = A_k,
4. proof that collision_count(A_k)=0 for every k,
5. proof that density approaches the claimed limsup,
6. proof that the integer unrolling is one global Sidon set, not unrelated finite witnesses.
```

### 4. Block algebraic construction with buffer zones

Build dense algebraic blocks and separate them by large gaps.

```text
A = B_1 union shifted(B_2) union shifted(B_3) union ...
```

Role:

```text
Preserves local algebraic density while preventing cross-block collisions through spacing.
```

Failure mode:

```text
Buffer zones may lower limsup density unless the dense blocks dominate the observation windows.
```

This is a plausible route for high limsup behavior because limsup only needs favorable windows, but the cross-block audit is the hard constraint.

## Obstruction set formulation

For a finite Sidon set `A`, a new integer `x` cannot be added if it creates a collision.

A useful forbidden-value proxy is:

```text
Forbidden(A) = { a_i + a_j - a_k : a_i,a_j,a_k in A }
```

Then extension freedom in a window `[1,N]` is roughly:

```text
Omega_N(A) = |[1,N] \ Forbidden(A)|
```

A construction remains extendable only if:

```text
Omega_N(A) > 0
```

for sufficiently many future windows, with the actual pairwise-sum audit still enforced.

## Structural-overlap criterion

Raw collision pressure assumes forbidden values spread widely. Structure helps only if forbidden values overlap heavily.

Define an overlap factor:

```text
Gamma(A,N) = |A|^3 / |Forbidden(A) cap [1,N]|
```

High `Gamma` means many formal obstruction triples collapse to fewer actual forbidden values.

The search target becomes:

```text
Find constructions where Gamma(A,N) grows fast enough that Omega_N(A) does not collapse.
```

For the p-adic/log-pressure hypothesis, the required upgrade is:

```text
Conjectural target:
  |Forbidden(A_k) cap [1,N_k]| = o(N_k)

Stronger target suggested by the pasted heuristic:
  |Forbidden(A_k) cap [1,N_k]| = O(polylog N_k)

Status:
  U_scope until proved.
```

## Refined Mass-Number score

For finite witness `A_N subset [1,N]`:

```text
rho_N(A_N) = |A_N| / sqrt(N)
C(A_N)     = sum_s max(0, R_A(s)-1)
Omega_N    = admissible future slots
Gamma_N    = obstruction overlap factor
E_N        = embedding risk
```

Candidate mass:

```text
M_Sidon(A_N)
=
  rho_N(A_N)
  * indicator(C(A_N)=0)
  * log(1 + Omega_N)
  * log(1 + Gamma_N)
  /
  (1 + E_N)
```

A dense finite construction receives high mass only if it is collision-free and retains measurable extension freedom.

## Shortening the path

The shortest route is not to search all Sidon sets. The shortest route is to audit known high-density algebraic families for extendability.

Priority order:

```text
1. Start with Singer / Bose-Chowla finite witnesses.
2. Compute collision_count(A_N)=0 as a hard receipt.
3. Compute Forbidden(A_N) and Omega_N across candidate extension windows.
4. Measure Gamma(A_N,N) to detect structural compression of obstruction triples.
5. Test p-adic or block-lift rules that preserve previous residues while minimizing new collisions.
6. Promote only finite audited witnesses; keep infinite claims U_scope until asymptotic nesting is proven.
```

## Research-grade question

```text
Do there exist algebraic lift maps T_k producing compatible finite Sidon witnesses
A_k subset [1,N_k] such that:

1. A_k is Sidon for every k,
2. A_k embeds into A_{k+1} without destroying old sums,
3. |A_k| / sqrt(N_k) approaches 1 along a subsequence,
4. the obstruction overlap Gamma(A_k,N_k) prevents extension freedom Omega_N from collapsing,
5. the construction unrolls to one infinite Sidon set A subset N?
```

P-adic sharpened version:

```text
Does there exist a p-adic digit-lift tower A_k subset Z / p^k Z such that
compatible lifts preserve Sidon uniqueness at every level and the unrolled integer
sequence has limsup density 1?
```

## W-axis labels

```text
Verified finite witness with C(A_N)=0:
  R_finite

p-adic or block-lift rule with finite audits only:
  R_finite + U_asymptotic

p-adic/log-pressure graph without lift proof:
  P_analogy + U_scope

Claim of sigma=1 without infinite construction and proof:
  U_scope

Numerical pressure plot treated as theorem:
  P_analogy, rejected as R

Explicit collision in proposed set:
  X_constraint
```

## Lean target skeleton

```lean
namespace SidonLifting

-- A finite Sidon witness is audited by zero pairwise-sum collisions.
theorem finiteWitness_requiresCollisionZero
  (A : Finset Nat) :
  PromotedFiniteSidon A -> CollisionCount A = 0 := by
  sorry

-- Pure additive embeddings preserve collision structure; they do not create new Sidon slack.
theorem additiveEmbedding_preservesCollisions
  (T : Nat -> Nat) :
  AdditiveInjective T ->
  PairSumCollision A -> PairSumCollision (A.image T) := by
  sorry

-- Infinite promotion requires a compatible lift chain plus asymptotic density proof.
theorem infinitePromotion_requiresCompatibleLiftAndDensity
  (chain : Nat -> Finset Nat) :
  PromotedInfiniteSidon chain ->
    CompatibleLiftChain chain ∧
    (forall k, CollisionCount (chain k) = 0) ∧
    LimsupDensityOne chain := by
  sorry

-- A p-adic pressure plot is not enough to discharge an infinite Sidon claim.
theorem pAdicHeuristic_notProofWithoutLiftAudit
  (claim : Claim) :
  PAdicPressureHeuristic claim ->
  ¬ HasCompatibleLiftAudit claim ->
  Gate claim = P_analogy := by
  sorry

end SidonLifting
```

## Short doctrine

```text
Finite geometry gives dense foci.
Lifting must preserve old sums and avoid new sums.
Additive inclusion alone does not create slack.
The useful signal is obstruction overlap.
P-adic digit windows are a candidate mechanism, not a proof.
Sigma=1 needs a nesting theorem, not a prettier pressure plot.
```
