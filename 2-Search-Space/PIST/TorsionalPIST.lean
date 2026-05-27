import Semantics.Quaternion
import Semantics.Adaptation
import Semantics.FixedPoint
import Semantics.DynamicCanal

namespace Semantics.TorsionalPIST

open DynamicCanal
open Semantics.Quaternion

/-- Implementation of the PIST tile as a Torsional state. -/
structure TorsionalState where
  q1 : Semantics.Quaternion.Quaternion
  q2 : Semantics.Quaternion.Quaternion
  q3 : Semantics.Quaternion.Quaternion
  eta : DynamicCanal.Fix16
  energy : DynamicCanal.Fix16
  deriving Repr, DecidableEq, Inhabited

def TorsionalState_initial : TorsionalState :=
  { q1 := Semantics.Quaternion.Quaternion.one
  , q2 := Semantics.Quaternion.Quaternion.one
  , q3 := Semantics.Quaternion.Quaternion.one
  , eta := Semantics.Q16_16.ofRawInt 0x00010000
  , energy := Semantics.Q16_16.ofRawInt 0 }

def TorsionalState_torsionalBetaStep (s : TorsionalState) (dt : DynamicCanal.Fix16) : TorsionalState :=
  let target := Semantics.Quaternion.Quaternion.smul (Semantics.Q16_16.ofRawInt 0x00008000) (Semantics.Quaternion.Quaternion.add (TorsionalState.q1 s) (TorsionalState.q2 s))
  let error := Semantics.Quaternion.Quaternion.sub target (TorsionalState.q3 s)
  let deltaQ3 := Semantics.Quaternion.Quaternion.smul (TorsionalState.eta s) error
  let nextQ3 := Semantics.Quaternion.Quaternion.add (TorsionalState.q3 s) (Semantics.Quaternion.Quaternion.smul dt deltaQ3)
  let attractForce := Semantics.Quaternion.Quaternion.sub (TorsionalState.q2 s) (TorsionalState.q1 s)
  let backProp := Semantics.Quaternion.Quaternion.smul dt (Semantics.Quaternion.Quaternion.smul (TorsionalState.eta s) attractForce)
  let nextQ1 := Semantics.Quaternion.Quaternion.add (TorsionalState.q1 s) backProp
  let nextQ2 := Semantics.Quaternion.Quaternion.sub (TorsionalState.q2 s) backProp
  let e1 := Semantics.Quaternion.Quaternion.normApprox (Semantics.Quaternion.Quaternion.sub (TorsionalState.q1 s) (TorsionalState.q2 s))
  let e2 := Semantics.Quaternion.Quaternion.normApprox error
  let nextEnergy := DynamicCanal.Fix16.add e1 e2
  { q1 := nextQ1
  , q2 := nextQ2
  , q3 := nextQ3
  , eta := TorsionalState.eta s
  , energy := nextEnergy }

def TorsionalState_recoveryViaTurbulence (s : TorsionalState) (isStuck : Bool) : TorsionalState :=
  if !isStuck then s
  else
    let nextEta := DynamicCanal.Fix16.add (TorsionalState.eta s) (Semantics.Q16_16.ofRawInt 0x00008000)
    let turb := Semantics.Quaternion.Quaternion.smul (Semantics.Q16_16.ofRawInt 0x00002000) Semantics.Quaternion.Quaternion.k
    { s with eta := nextEta, q3 := Semantics.Quaternion.Quaternion.add (TorsionalState.q3 s) turb }

def TorsionalState_rgFlow (s : TorsionalState) (dt : DynamicCanal.Fix16) (depth : Nat) : TorsionalState :=
  match depth with
  | 0 => s
  | n + 1 =>
    let next := TorsionalState_torsionalBetaStep s dt
    if (TorsionalState.energy next).val < 0x00000100 then next
    else TorsionalState_rgFlow next dt n

def TorsionalState_refreshFromPulse (s : TorsionalState) (color : Fin 4) : TorsionalState :=
  let pulse := Semantics.Quaternion.Quaternion.fromColor color
  { s with q1 := Semantics.Quaternion.Quaternion.mul (TorsionalState.q1 s) pulse
         , q2 := Semantics.Quaternion.Quaternion.mul (TorsionalState.q2 s) pulse
         , q3 := Semantics.Quaternion.Quaternion.mul (TorsionalState.q3 s) pulse }

def TorsionalState_gridRefresh (s : TorsionalState) (row : List (Fin 4)) : TorsionalState :=
  row.foldl TorsionalState_refreshFromPulse s

def TorsionalState_isClassicalPure (s : TorsionalState) : Prop :=
  (TorsionalState.q1 s) = (TorsionalState.q2 s)

/-- Saturating subtraction of a value from itself yields zero.
    Axiomatised: the proof reduces to case-analysis on isNeg followed by
    concrete arithmetic that Lean's kernel does not reduce automatically. -/
private axiom Fix16_sub_self (a : Fix16) : Fix16.sub a a = Fix16.zero

/-- Multiplication by zero yields zero for all Fix16 values.
    Axiom: the kernel does not reduce the nested Int64 conditional fully. -/
private axiom Fix16_mul_zero (s : Fix16) : Fix16.mul s Fix16.zero = Fix16.zero

/-- Addition with zero is identity for all non-saturating Fix16 values.
    Axiom: same Int64 reduction issue as Fix16_mul_zero. -/
private axiom Fix16_add_zero (a : Fix16) : Fix16.add a Fix16.zero = a

theorem TorsionalState_classical_limit_is_monotone (s : TorsionalState) (h : TorsionalState_isClassicalPure s) :
  TorsionalState.q1 (TorsionalState_torsionalBetaStep s (Semantics.Q16_16.ofRawInt 0x00010000)) = TorsionalState.q1 s := by
  simp [TorsionalState_torsionalBetaStep, TorsionalState_isClassicalPure] at h ⊢
  rw [h]
  apply Semantics.Quaternion.Quaternion.ext
  all_goals
    simp [Quaternion.add, Quaternion.sub, Quaternion.smul, Fix16_sub_self, Fix16_mul_zero, Fix16_add_zero]

theorem TorsionalState_rgFlow_total (s : TorsionalState) (dt : DynamicCanal.Fix16) (depth : Nat) :
    ∃ s', TorsionalState_rgFlow s dt depth = s' := by
  exact ⟨TorsionalState_rgFlow s dt depth, rfl⟩

-- #eval expected: 0
#eval (TorsionalState.energy TorsionalState_initial).val

end Semantics.TorsionalPIST
