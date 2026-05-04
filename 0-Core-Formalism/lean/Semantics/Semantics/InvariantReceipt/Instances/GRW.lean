-- GRW Instance for Invariant Receipt Protocol
-- GRW: Generalized Reward Witness model with substrate adapter

import InvariantReceipt.Core
import InvariantReceipt.Receipt
import InvariantReceipt.SubstrateAdapter

namespace InvariantReceipt.GRW

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  GRW State
-- ═══════════════════════════════════════════════════════════════════════════

/-- GRWState: a model state with declared pay and actual value. -/
structure GRWState where
  declaredPay : Int
  actualValue : Int
  witness     : UInt64  -- commitment hash
deriving Inhabited, DecidableEq, BEq

-- Note: UInt64 Inhabited instance exists natively in Lean 4
instance : Inhabited GRWState where
  default := ⟨0, 0, 0⟩

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  GRW Transform and Invariant
-- ═══════════════════════════════════════════════════════════════════════════

/-- I_GRW: invariant — declared pay must be non-negative. -/
def grwInvariant (s : GRWState) : Prop :=
  s.declaredPay ≥ 0

/-- T_GRW: transform — moves from state a to state b,
    preserving that actualValue matches declaredPay on valid transitions. -/
def grwTransform (a b : GRWState) : Outcome GRWState :=
  if a.witness = b.witness ∧ a.actualValue = b.declaredPay then
    Outcome.ok b
  else
    Outcome.quarantined ⟨"GRW-witness-mismatch", #[], a.witness⟩

/-- K_GRW: cost function — difference between declared and actual. -/
def grwCost (a b : GRWState) : Int :=
  a.declaredPay - a.actualValue

/-- R_GRW: residual — absolute difference between declared pay and actual value. -/
def grwResidual (a b : GRWState) : Int :=
  (a.declaredPay - a.actualValue).natAbs

/-- Projection: extracts the witness as the public receipt. -/
def grwProject (s : GRWState) : UInt64 := s.witness

/-- Scale band: GRW operates at single-witness scale (Byte-level). -/
inductive GRWScaleBand : Type where
  | SingleWitness
  | BatchWitness
  deriving Inhabited, DecidableEq, BEq

def grwValidAtScale (band : GRWScaleBand) (s : GRWState) : Prop :=
  match band with
  | GRWScaleBand.SingleWitness => True
  | GRWScaleBand.BatchWitness  => True

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  ModelUpgrade Instance
-- ═══════════════════════════════════════════════════════════════════════════

def grwModel : ModelUpgrade GRWState GRWScaleBand UInt64 where
  transform    := grwTransform
  invariant    := grwInvariant
  residual     := grwResidual
  cost         := grwCost
  project      := grwProject
  validAtScale := grwValidAtScale

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Substrate Adapter (Round-Trip Law)
-- ═══════════════════════════════════════════════════════════════════════════

/-- GRW substrate target: a simplified wire format. -/
structure GRWWire where
  pay  : Int
  val  : Int
  hash : UInt64
deriving Inhabited

def grwToWire (s : GRWState) : GRWWire :=
  ⟨s.declaredPay, s.actualValue, s.witness⟩

def grwFromWire (w : GRWWire) : GRWState :=
  ⟨w.pay, w.val, w.hash⟩

/-- Round-trip property: serialization is lossless for invariant states. -/
theorem grwRoundTrip (s : GRWState) (h : grwInvariant s) :
  grwFromWire (grwToWire s) = s :=
by
  simp [grwFromWire, grwToWire]

def grwAdapter : SubstrateAdapter grwModel where
  target      := "GRW-Wire-v1"
  TargetState := GRWWire
  toTarget    := grwToWire
  fromTarget  := grwFromWire
  roundTrip   := grwRoundTrip

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Th5: GRW Receipt Soundness (Deferred Skeleton)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Th5: T_GRW(a, b) = ok(b) ↔ I_GRW(a) ∧ K_GRW(a, b) = a.declared_pay
    This is the core soundness theorem for GRW transitions.
    Deferred pending complete cost-accounting integration. -/
theorem Th5_grw_receipt_soundness
  (a b : GRWState)
  (h_ok : grwTransform a b = Outcome.ok b) :
  grwInvariant a ∧ grwCost a b = a.declaredPay :=
by
  simp [grwTransform] at h_ok
  split at h_ok
  · -- Valid transition path
    simp [grwInvariant, grwCost]
    exact ⟨by omega, by omega⟩
  · -- Quarantine path — contradiction
    contradiction

end InvariantReceipt.GRW
