/-
EigenGate.lean — The canonical eigengate type.

Every physical law, every compression check, every routing decision is an
eigenstate condition: ∥G·s − s∥ ≤ τ, where G is the operator defining the
expected invariant, and the residual is the fraction of deviation from identity.

Residuals live in Q0_16 — the dimensionless pure-fraction type from
FixedPoint.lean. Products stay in [0,1): the multiplicative gate chain
never overflows, and any zero-score gate collapses the entire product.

  verdict : admit if residual=0, hold if ≤ threshold, reject if >
  score   : 1/(1+r) — proximity to λ=1 eigenspace
  route   : eigenstate / nearEigenstate / boundary / underverse / error

Specific physics emerges from WHICH operator G and WHICH calibration constants
parameterize it. The full physical universe is the intersection of λ=1
eigenspaces for all required gate operators simultaneously.
-/

import Semantics.FixedPoint

namespace Semantics.Kernel

open Semantics.FixedPoint (Q0_16)

inductive EigenVerdict where
  | admit | hold | reject
  deriving Repr, BEq, DecidableEq, Inhabited

inductive Route where
  | eigenstate
  | nearEigenstate
  | boundary
  | underverse
  | error
  deriving Repr, BEq, DecidableEq, Inhabited

structure Eigengate (α : Type) where
  operator  : α → α
  residual  : α → Q0_16
  threshold : Q0_16

def verdict {α : Type} (g : Eigengate α) (s : α) : EigenVerdict :=
  let r := g.residual s
  if r.val == 0 then EigenVerdict.admit
  else if r.val ≤ g.threshold.val then EigenVerdict.hold
  else EigenVerdict.reject

def score (r : Q0_16) : Q0_16 :=
  let denom := Q0_16.add Q0_16.one r
  Q0_16.div Q0_16.one denom

def route {α : Type} (g : Eigengate α) (s : α) (hasReceipt : Bool) : Route :=
  let v := verdict g s
  let r := g.residual s
  match v with
  | EigenVerdict.admit =>
      if r.val == 0 then Route.eigenstate
      else Route.nearEigenstate
  | EigenVerdict.hold  => Route.boundary
  | EigenVerdict.reject =>
      if hasReceipt then Route.underverse
      else Route.error

def chainVerdict {α : Type} (gates : List (Eigengate α × Bool)) (s : α) : EigenVerdict :=
  let required := gates.filter (fun (_, req) => req) |>.map (fun (g, _) => g)
  if required.any fun g => verdict g s == EigenVerdict.reject then
    EigenVerdict.reject
  else if required.any fun g => verdict g s == EigenVerdict.hold then
    EigenVerdict.hold
  else
    EigenVerdict.admit

def q0Ratio (num den : Nat) : Q0_16 :=
  if den = 0 then Q0_16.one
  else ⟨(Nat.min 32767 ((num * 32767) / den)).toUInt16⟩

def shore : Q0_16 := Q0_16.zero

def approach (N : Nat) : Q0_16 :=
  if N == 0 then Q0_16.zero
  else if N ≥ 16 then Q0_16.one
  else
    let step := (1 <<< N) - 1
    let maxV := (1 <<< N)
    q0Ratio step maxV

def testGateAllAdmit : Eigengate Q0_16 :=
  { operator := λ s => s
  , residual := λ _ => Q0_16.zero
  , threshold := Q0_16.one }

def testGateAllReject : Eigengate Q0_16 :=
  { operator := λ s => s
  , residual := λ _ => Q0_16.one
  , threshold := q0Ratio 1 4 }

def testGateResidualAtHalf : Eigengate Q0_16 :=
  { operator := λ s => s
  , residual := λ s => if s.val == 0 then Q0_16.zero else Q0_16.half
  , threshold := q0Ratio 1 4 }

def chainFixtureAllAdmit : List (Eigengate Q0_16 × Bool) :=
  [ (testGateAllAdmit, true), (testGateAllAdmit, true) ]

def chainFixtureOneRejects : List (Eigengate Q0_16 × Bool) :=
  [ (testGateAllAdmit, true), (testGateAllReject, true) ]

def chainFixtureOptionalReject : List (Eigengate Q0_16 × Bool) :=
  [ (testGateAllAdmit, true), (testGateAllReject, false) ]

theorem shore_is_zero : shore.val == 0 := rfl

theorem admit_verdict_on_zero_residual :
    verdict testGateAllAdmit Q0_16.zero = EigenVerdict.admit := by
  native_decide

theorem reject_verdict_on_high_residual :
    verdict testGateAllReject Q0_16.zero = EigenVerdict.reject := by
  native_decide

theorem score_val_on_zero_residual :
    (score Q0_16.zero).val = 32768 := by
  native_decide

theorem chain_all_admit_admits :
    chainVerdict chainFixtureAllAdmit Q0_16.zero = EigenVerdict.admit := by
  native_decide

theorem chain_one_rejects_rejects :
    chainVerdict chainFixtureOneRejects Q0_16.zero = EigenVerdict.reject := by
  native_decide

theorem chain_optional_reject_no_effect :
    chainVerdict chainFixtureOptionalReject Q0_16.zero = EigenVerdict.admit := by
  native_decide

theorem route_admit_zero_residual_is_eigenstate :
    route testGateAllAdmit Q0_16.zero true = Route.eigenstate := by
  native_decide

theorem route_reject_no_receipt_is_error :
    route testGateAllReject Q0_16.zero false = Route.error := by
  native_decide

theorem route_reject_with_receipt_is_underverse :
    route testGateAllReject Q0_16.zero true = Route.underverse := by
  native_decide

theorem approach_bounded (N : Nat) : Q0_16.le (approach N) Q0_16.one := by
  by_cases hN0 : N = 0
  · subst hN0; unfold approach Q0_16.le; native_decide
  · by_cases hN16 : N ≥ 16
    · unfold approach; simp [hN0, hN16]; unfold Q0_16.le; native_decide
    · have hNle : N ≤ 15 := by omega
      interval_cases N <;> unfold approach Q0_16.le <;> native_decide

#eval verdict testGateAllAdmit Q0_16.zero
#eval verdict testGateAllReject Q0_16.zero
#eval verdict testGateResidualAtHalf Q0_16.half

#eval score Q0_16.zero
#eval score Q0_16.half

#eval shore

#eval approach 2
#eval approach 5
#eval approach 16

#eval chainVerdict chainFixtureAllAdmit Q0_16.zero
#eval chainVerdict chainFixtureOneRejects Q0_16.zero
#eval chainVerdict chainFixtureOptionalReject Q0_16.zero

#eval route testGateAllAdmit Q0_16.zero true
#eval route testGateAllReject Q0_16.zero true
#eval route testGateAllReject Q0_16.zero false

end Semantics.Kernel
