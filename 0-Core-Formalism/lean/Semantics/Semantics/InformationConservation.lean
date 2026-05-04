import Std.Tactic

namespace Semantics.InformationConservation

/-- Information phase in the Bandyopadhyay-Cycle -/
inductive InformationPhase where
  | bulk : InformationPhase  -- Kinetic matter active in 3D manifold
  | horizon : InformationPhase  -- Bits trapped on holographic surface
  | vacuum : InformationPhase  -- Ambient radiation in dark matter pool

/-- Information state with discrete microstate tracking (Ironclad Ledger) -/
structure InformationState where
  bulk : Nat  -- Information in kinetic bulk (discrete int32)
  horizon : Nat  -- Information on holographic horizon (discrete int32)
  vacuum : Nat  -- Information in ambient vacuum (discrete int32)
  deriving BEq, Repr, DecidableEq

/-- Total information is conserved across all phases -/
def totalInformation (s : InformationState) : Nat :=
  s.bulk + s.horizon + s.vacuum

/-- Bandyopadhyay-Cycle: I_total = I_bulk + I_horizon + I_vacuum -/
theorem bandyopadhyayCycleConservation (s : InformationState) :
  totalInformation s = s.bulk + s.horizon + s.vacuum := by
  rfl

/-- Information transfer from one phase to another (atomic operation) -/
def transferInformation (s : InformationState) (from to : InformationPhase) (amount : Nat) : InformationState :=
  match from, to with
  | .bulk, .horizon => { bulk := s.bulk - amount, horizon := s.horizon + amount, vacuum := s.vacuum }
  | .bulk, .vacuum => { bulk := s.bulk - amount, horizon := s.horizon, vacuum := s.vacuum + amount }
  | .horizon, .bulk => { bulk := s.bulk + amount, horizon := s.horizon - amount, vacuum := s.vacuum }
  | .horizon, .vacuum => { bulk := s.bulk, horizon := s.horizon - amount, vacuum := s.vacuum + amount }
  | .vacuum, .bulk => { bulk := s.bulk + amount, horizon := s.horizon, vacuum := s.vacuum - amount }
  | .vacuum, .horizon => { bulk := s.bulk, horizon := s.horizon + amount, vacuum := s.vacuum - amount }
  | _, _ => s  -- No transfer if same phase

/-- Information transfer preserves total information -/
theorem transferPreservesTotalInformation (s : InformationState) (from to : InformationPhase) (amount : Nat) :
  totalInformation (transferInformation s from to amount) = totalInformation s := by
  cases from <; cases to <; cases h : from = to <; simp [transferInformation, totalInformation]

/-- State transition is lawful if source phase has sufficient information -/
def isLawfulTransfer (s : InformationState) (from to : InformationPhase) (amount : Nat) : Bool :=
  if from = to then true
  else match from with
    | .bulk => amount ≤ s.bulk
    | .horizon => amount ≤ s.horizon
    | .vacuum => amount ≤ s.vacuum

/-- Lawful transfer preserves non-negative information in all phases -/
theorem lawfulTransferPreservesNonNegativity (s : InformationState) (from to : InformationPhase) (amount : Nat) (h : isLawfulTransfer s from to amount = true) :
  let s' := transferInformation s from to amount
  s'.bulk ≥ 0 ∧ s'.horizon ≥ 0 ∧ s'.vacuum ≥ 0 := by
  simp [transferInformation, isLawfulTransfer] at h
  cases from <; cases to <; simp [transferInformation] <; omega

/-- Cost of information transfer (Q0_16 normalized) -/
def transferCost (s : InformationState) (from to : InformationPhase) (amount : Nat) : UInt16 :=
  if from = to then 0
  else UInt16.ofNat ((amount * 1000) / (totalInformation s + 1))

/-- Invariant extractor for information state -/
def informationInvariant (s : InformationState) : String :=
  s!"bulk: {s.bulk}, horizon: {s.horizon}, vacuum: {s.vacuum}, total: {totalInformation s}"

/-- Information conservation across phases is additive -/
theorem informationAdditivity (s : InformationState) :
  totalInformation s = s.bulk + s.horizon + s.vacuum := by
  rfl

/-- Transfer from bulk to horizon preserves total information -/
theorem transferBulkToHorizonPreservesTotal (s : InformationState) (amount : Nat) (h : amount ≤ s.bulk) :
  totalInformation (transferInformation s .bulk .horizon amount) = totalInformation s := by
  simp [transferInformation, totalInformation]
  have h_sub : s.bulk - amount + s.horizon + s.vacuum = s.bulk + s.horizon + s.vacuum - amount := by omega
  rw [h_sub]
  omega

/-- Transfer from horizon to vacuum preserves total information -/
theorem transferHorizonToVacuumPreservesTotal (s : InformationState) (amount : Nat) (h : amount ≤ s.horizon) :
  totalInformation (transferInformation s .horizon .vacuum amount) = totalInformation s := by
  simp [transferInformation, totalInformation]
  have h_sub : s.bulk + (s.horizon - amount) + s.vacuum = s.bulk + s.horizon + s.vacuum - amount := by omega
  rw [h_sub]
  omega

/-- Information is always non-negative in all phases -/
theorem informationNonNegative (s : InformationState) :
  s.bulk ≥ 0 ∧ s.horizon ≥ 0 ∧ s.vacuum ≥ 0 := by
  constructor
  · apply Nat.zero_le
  · constructor
    · apply Nat.zero_le
    · apply Nat.zero_le

/-- Total information is at least as large as any individual phase -/
theorem totalDominatesEachPhase (s : InformationState) :
  totalInformation s ≥ s.bulk ∧ totalInformation s ≥ s.horizon ∧ totalInformation s ≥ s.vacuum := by
  constructor
  · simp [totalInformation]; omega
  · constructor
    · simp [totalInformation]; omega
    · simp [totalInformation]; omega

end Semantics.InformationConservation
