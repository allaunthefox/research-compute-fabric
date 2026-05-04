# Lean Migration Migraine Reducer

## Purpose

This note converts the current Sidon / AMREF / Mass-Number / Inverse-Ascent stack into a Lean-first implementation plan with minimal manual theorem pain.

I could not directly pull live pages from `lean-lang.org` in this environment, so this note is based on stable Lean 4 / Lake / Mathlib workflow practice and should be refreshed against the official Lean docs before use as a V-scope implementation receipt.

## Core Rule

```text
Do not hand-prove the whole ontology.
First formalize finite counters, gates, and monotonicity lemmas.
Then use computation/reflection for examples.
Only promote theorem statements after counters and witnesses exist.
```

## Lean Stack Shape

Recommended module layout:

```text
OTOM/
  Sidon/
    FinsetCounters.lean
    SidonGate.lean
    GolombGate.lean
    CompressionGate.lean
    MetaProbeGate.lean
    InverseAscentGate.lean
    Examples.lean
  AMREF/
    FixedPoint.lean
    Score.lean
  MassNumber/
    Core.lean
    Receipts.lean
  FAM/
    Route.lean
    Gate.lean
```

## Minimal Lake Setup

Expected files:

```text
lean-toolchain
lakefile.lean
```

`lean-toolchain` should pin a toolchain, for example:

```text
leanprover/lean4:stable
```

For Mathlib-backed work, use the Mathlib project template and then pin exact versions.

## First Formal Target: Finite Counters

Everything starts with finite lists/finsets.

```lean
import Mathlib.Data.Finset.Basic
import Mathlib.Data.Multiset.Basic
import Mathlib.Data.Nat.Basic

namespace OTOM.Sidon

abbrev Candidate := Finset Nat

/-- Unordered pair sums with repetitions represented as a multiset. -/
def pairSums (A : Candidate) : Multiset Nat :=
  ((A.product A).filter (fun p => p.1 <= p.2)).val.map (fun p => p.1 + p.2)

/-- A finite Sidon candidate: no duplicate unordered pair sums. -/
def IsSidon (A : Candidate) : Prop :=
  (pairSums A).Nodup

/-- Ordered positive differences. -/
def diffs (A : Candidate) : Multiset Nat :=
  ((A.product A).filter (fun p => p.2 < p.1)).val.map (fun p => p.1 - p.2)

/-- Golomb-style no repeated positive differences. -/
def IsGolomb (A : Candidate) : Prop :=
  (diffs A).Nodup

end OTOM.Sidon
```

This is the low-migraine route because `Nodup` gives you a proof object without building full collision-energy arithmetic first.

## Second Target: Collision Energy as Computable Diagnostics

After `Nodup`, add computable collision debt.

```lean
namespace OTOM.Sidon

/-- Count how often `x` occurs in a multiset. -/
def countOf (x : Nat) (xs : Multiset Nat) : Nat :=
  xs.count x

/-- Collision debt of a multiset: sum over unique support of max(0, count-1). -/
def collisionDebt (xs : Multiset Nat) : Nat :=
  (xs.toFinset).sum (fun x => (xs.count x) - 1)

def cB2 (A : Candidate) : Nat :=
  collisionDebt (pairSums A)

def cD (A : Candidate) : Nat :=
  collisionDebt (diffs A)

end OTOM.Sidon
```

Target lemmas:

```lean
theorem sidon_iff_cB2_zero (A : Candidate) :
  IsSidon A <-> cB2 A = 0 := by
  -- prove after checking exact Multiset lemmas in Mathlib
  sorry

theorem golomb_iff_cD_zero (A : Candidate) :
  IsGolomb A <-> cD A = 0 := by
  sorry
```

Use `sorry` only in draft branches; block promotion until removed.

## Third Target: Gate Records

Use records for proof-carrying gates instead of loose booleans.

```lean
structure SidonProbeState where
  A : Candidate
  cB2 : Nat
  cD : Nat
  compressionGainQ16 : UInt32
  gclStabilityQ16 : UInt32
  metaProbeQ16 : UInt32
  randomnessPenaltyQ16 : UInt32
  receiptsComplete : Bool

inductive SidonGate where
  | classicalSidon
  | virtualSidon
  | hold
  | scar
  | quarantine
  deriving Repr, DecidableEq
```

Then define readiness as an executable Boolean:

```lean
def ClassicalSidonReady (s : SidonProbeState) : Bool :=
  s.cB2 == 0 &&
  s.metaProbeQ16 >= 0x00008000 &&
  s.randomnessPenaltyQ16 <= 0x00004000 &&
  s.receiptsComplete
```

And later prove Boolean/Prop correspondence:

```lean
def ClassicalSidonReadyProp (s : SidonProbeState) : Prop :=
  s.cB2 = 0 ∧
  s.metaProbeQ16 >= 0x00008000 ∧
  s.randomnessPenaltyQ16 <= 0x00004000 ∧
  s.receiptsComplete = true
```

Target theorem:

```lean
theorem classicalReady_sound (s : SidonProbeState) :
  ClassicalSidonReady s = true -> ClassicalSidonReadyProp s := by
  -- mostly simp / decide / Bool.and_eq_true decomposition
  sorry
```

## Fourth Target: Inverse Ascent Gate

Keep this integer/fixed-point first.

```lean
structure Route where
  rankDelta : Int
  energyAvailableQ16 : UInt32
  ascentCostQ16 : UInt32
  receiptsComplete : Bool
  deriving Repr, DecidableEq

def CanAscend (r : Route) : Bool :=
  r.rankDelta > 0 &&
  r.energyAvailableQ16 >= r.ascentCostQ16 &&
  r.receiptsComplete
```

Soundness target:

```lean
def CanAscendProp (r : Route) : Prop :=
  r.rankDelta > 0 ∧
  r.energyAvailableQ16 >= r.ascentCostQ16 ∧
  r.receiptsComplete = true

theorem canAscend_sound (r : Route) :
  CanAscend r = true -> CanAscendProp r := by
  sorry
```

## Fifth Target: Avoid Real Analysis Until Necessary

Do not start with FFT, AMREF, real-valued scores, or complex exponentials.

Start with finite approximations:

```text
Q16.16 fixed-point scores
UInt32 thresholds
Nat collision counters
Bool gates
Prop soundness lemmas
```

Only after the finite gate is stable should you add:

```text
Rational scores
Real-valued AMREF
Complex spectral fingerprints
FFT proofs
analytic limits
```

## Tactics That Usually Shorten Pain

Useful tactics/patterns:

```lean
simp
simp_all
omega
linarith
norm_num
decide
by_cases h : condition
constructor
intro h
rcases h with ⟨h1, h2, h3⟩
```

For Nat arithmetic, try:

```lean
omega
```

For simple numerals:

```lean
norm_num
```

For boolean gates:

```lean
simp [CanAscend, CanAscendProp] at *
```

## Migraine Avoidance Rules

```text
1. Avoid proving optimized formulas first.
2. Define executable counters first.
3. Prove soundness of gates, not completeness of ontology.
4. Use UInt32/Q16 only at boundaries; use Nat for proofs where possible.
5. Keep spectral/complex analysis out of the first Lean pass.
6. Make every external claim a Receipt record.
7. Keep user-facing metaphor out of Lean names.
8. Never let visualization become theorem input.
```

## Mapping Current Stack to Lean

| Concept | Lean-first representation |
|---|---|
| Sidon field | `Finset Nat` |
| Pair-sum collision | `Multiset Nat` + `Nodup` / debt counter |
| Golomb echoes | difference multiset + `Nodup` |
| AMREF score | Q16.16 score field first, real functional later |
| Mass-number | fixed-point diagnostic record |
| Inverse ascent | `Route` with energy/cost/receipts |
| GCL diff | Q16.16 stability score first |
| Metaprobe | Q16.16 trust score + Prop soundness |
| Receipts | structures / typeclasses |

## Suggested First File

Create:

```text
OTOM/Sidon/FinsetCounters.lean
```

with:

```lean
import Mathlib.Data.Finset.Basic
import Mathlib.Data.Multiset.Basic
import Mathlib.Data.Nat.Basic
import Mathlib.Tactic

namespace OTOM.Sidon

abbrev Candidate := Finset Nat

def pairSums (A : Candidate) : Multiset Nat :=
  ((A.product A).filter (fun p => p.1 <= p.2)).val.map (fun p => p.1 + p.2)

def IsSidon (A : Candidate) : Prop :=
  (pairSums A).Nodup

def diffs (A : Candidate) : Multiset Nat :=
  ((A.product A).filter (fun p => p.2 < p.1)).val.map (fun p => p.1 - p.2)

def IsGolomb (A : Candidate) : Prop :=
  (diffs A).Nodup

def collisionDebt (xs : Multiset Nat) : Nat :=
  (xs.toFinset).sum (fun x => (xs.count x) - 1)

def cB2 (A : Candidate) : Nat :=
  collisionDebt (pairSums A)

def cD (A : Candidate) : Nat :=
  collisionDebt (diffs A)

end OTOM.Sidon
```

## Required Receipts

```text
LeanDocsRefreshReceipt
LakeBuildReceipt
MathlibVersionReceipt
FiniteCounterReceipt
GateSoundnessReceipt
NoSorryReceipt
ExampleWitnessReceipt
```

## Audit Classification

```text
Receipt: LeanMigrationMigraineReducer
Status: IMPLEMENTATION_SCAFFOLD
Gate: U_scope
Reason: suitable migration plan and first-module sketch; must be refreshed against official Lean docs and checked by `lake build` before V_scope.
```
