# Sidon Independent Derivation Audit

**Status:** PROOF_OBLIGATION_MAP_NOT_PROOF  
**Target stack:** OTOM / Sidon Spectral Sieve / Mass-Number Lens / W-axis  
**Related:**
- `docs/conjectures/sidon-lifting-relaxation-program.md`
- `docs/conjectures/sidon-hyperfluid-density-profile-guardrail.md`

## Purpose

This note converts the proposed independent derivation of a p-adic Bose-Chowla lift into an auditable proof-obligation map.

The proposed derivation claims that one can independently derive `sigma = 1` by combining:

```text
Bose-Chowla finite seeds
p-adic digit separation
Ruzsa-style digit/dilation construction
forbidden-zone estimates
limit splicing / nesting
unique digit representation
```

This is retained as a research route, but not accepted as a proof until every closure receipt below is discharged.

## Anti-overpromotion correction

A later summary described the audit as:

```text
Audit Status: Committed.
Route to sigma = 1 verified through p-adic Dilation and Bose-Chowla seeding.
```

Corrected status:

```text
Audit Status: Committed as a proof-obligation roadmap.
Route to sigma = 1: not verified.
Current gate: U_scope + P_analogy.
```

Reason:

```text
A committed roadmap is not a committed theorem.
The p-adic/Ruzsa/Bose-Chowla route is promising only after explicit construction,
global pairwise-sum uniqueness, nesting, and limsup-density receipts are supplied.
```

## Current W-axis classification

```text
Gate: U_scope + P_analogy
```

Reason:

```text
The derivation describes a plausible architecture for a proof, but it does not yet provide:
  - an explicit infinite set A subset N,
  - a verified global pairwise-sum audit,
  - a nesting theorem,
  - a density theorem proving limsup A(x)/sqrt(x)=1,
  - or a literature-backed theorem that this construction is already known.
```

## Normalization correction

The relevant Sidon density is:

```text
sigma(A) = limsup_{x -> infinity} A(x) / sqrt(x)
```

not:

```text
A(x) / x.
```

A positive natural density claim `A(x)/x -> c > 0` is incompatible with Sidon square-root growth.

## Bose-Chowla seed receipt

Finite seed target:

```text
Given q = p^k and theta primitive in F_{q^2}, define
B = { a : theta^a = theta + x, x in F_q }.
```

Proof obligation:

```text
If a_1 + a_2 = a_3 + a_4 mod (q^2 - 1),
then {a_1,a_2} = {a_3,a_4}.
```

Gate:

```text
R_finite only after the modular Sidon proof or a cited theorem is attached.
```

## Digit/dilation lift receipt

Candidate lift:

```text
T(a) = sum_j c_j * p^(M*j)
```

or more generally:

```text
a = sum_i d_i * M_i
```

where the digit alphabets are finite Sidon witnesses.

Proof obligation:

```text
T(a)+T(b)=T(c)+T(d) in Z
  -> digitwise equality of sums
  -> {a,b} = {c,d}.
```

A carry-free lemma is not enough by itself. It must be paired with a global unique-representation theorem for the entire digit vector.

## Ruzsa / dilation bridge

The pasted derivation invokes a Ruzsa-style construction:

```text
Use a sufficiently large dilation constant M so digit blocks do not interfere.
```

Safe interpretation:

```text
Large-base digit separation can preserve local additive uniqueness if the digit alphabet and base-growth conditions are strong enough.
```

Unsafe interpretation:

```text
This automatically proves sigma = 1.
```

Required bridge theorem:

```text
Let B_i be Sidon digit alphabets and M_i be rapidly growing bases.
If the bases satisfy a no-overlap inequality, then
A = {sum_i d_i M_i : d_i in B_i with finite support / admissible support}
is Sidon.
```

Density still requires a separate asymptotic theorem.

## Forbidden-zone / pressure estimate receipt

The heuristic claim:

```text
pressure(x) ~ log(x)
```

must become an explicit obstruction bound.

Acceptable forms:

```text
|Forbidden(A_k) cap [1,N_k]| = o(N_k)
```

or stronger:

```text
|Forbidden(A_k) cap [1,N_k]| <= polylog(N_k).
```

This is where the pressure graph becomes mathematics.

## Nesting / limit-splicing receipt

A sequence of good finite sets is not enough. One needs one global infinite Sidon set.

Required theorem:

```text
A_1 subset A_2 subset A_3 subset ...
forall k, A_k is Sidon
A = union_k A_k is Sidon
limsup_x A(x)/sqrt(x) = 1
```

CRT splicing must additionally prove:

```text
If a_i + a_j = a_k + a_l in Z,
then the CRT residue constraints force {i,j} = {k,l}.
```

Without this, CRT gives compatible residues, not global Sidon uniqueness.

## Density theorem receipt

The proposed product expression:

```text
rho(A) = lim_k product_{i=1}^k |B_i| / q_i
```

is not yet the Sidon density `sigma(A)` unless tied to interval counts:

```text
A(x) ~ sqrt(x)
```

at a chosen sequence of windows.

Required theorem:

```text
There exist N_k -> infinity such that
|A cap [1,N_k]| / sqrt(N_k) -> 1.
```

## Constant-density / pulse claim

The valid statement is:

```text
Positive ordinary density A(x)/x is impossible for infinite Sidon sets.
```

The stronger pulse claim:

```text
Every high-limsup Sidon set must have liminf A(x)/sqrt(x)=0
```

requires a separate theorem. It must not be inferred from the hyperfluid metaphor alone.

## Research route after correction

The shortest legitimate path is:

```text
1. Cite/verify Bose-Chowla finite Sidon seeds.
2. Define an explicit digit alphabet B_i for each level.
3. Define explicit bases M_i and support rules.
4. Prove no-carry / no-overlap inequalities.
5. Prove global pairwise-sum uniqueness.
6. Prove nesting or global union consistency.
7. Prove limsup A(x)/sqrt(x)=1 along explicit windows N_k.
8. Only then promote sigma=1 from U_scope to R.
```

## Lean target skeleton

```lean
namespace SidonIndependentDerivation

-- Finite Bose-Chowla receipt.
theorem boseChowla_seed_is_sidon
  (q : Nat) (B : Finset Nat) :
  BoseChowlaSeed q B -> IsSidonMod B (q^2 - 1) := by
  sorry

-- Digit separation must imply global uniqueness, not just no carries.
theorem digitSeparation_globalSidon
  (A : Finset Nat) :
  DigitSeparated A ->
  DigitAlphabetSidon A ->
  GlobalPairSumUnique A := by
  sorry

-- A chain of finite witnesses must preserve uniqueness in the union.
theorem compatibleChain_unionSidon
  (chain : Nat -> Finset Nat) :
  CompatibleNestedSidonChain chain ->
  IsInfiniteSidon (Union chain) := by
  sorry

-- Limsup density one requires explicit windows.
theorem limsupDensityOne_requiresWindows
  (A : Nat -> Prop) :
  LimsupDensityOne A ->
  ExistsWindowsApproachingOne A := by
  sorry

-- A committed audit document is not a proof of the target theorem.
theorem committedAudit_notVerifiedTheorem
  (claim : Claim) :
  IsProofObligationMap claim ->
  ¬ HasAllClosureReceipts claim ->
  Gate claim = U_scope := by
  sorry

end SidonIndependentDerivation
```

## Short doctrine

```text
The manual is a proof map, not a proof.
A committed audit is not a verified theorem.
Bose-Chowla supplies finite perfection.
Digit dilation can preserve uniqueness only with a global sums theorem.
CRT and p-adics do not automatically give integer Sidon uniqueness.
Sigma=1 is promoted only after explicit construction, nesting, and density receipts.
```
