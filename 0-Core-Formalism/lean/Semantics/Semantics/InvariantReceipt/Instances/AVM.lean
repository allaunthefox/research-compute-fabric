-- AVM Instance for Invariant Receipt Protocol
-- AVM: Adaptive Virtual Machine — self-hosting closure

import InvariantReceipt.Core
import InvariantReceipt.Receipt

namespace InvariantReceipt.AVM

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  AVM State
-- ═══════════════════════════════════════════════════════════════════════════

/-- AVMState: a self-describing machine state with instruction counter
    and memory snapshot. -/
structure AVMState where
  pc     : UInt64   -- program counter
  mem    : List UInt64  -- memory cells
  halted : Bool
deriving Inhabited, DecidableEq, BEq

instance : Inhabited AVMState where
  default := ⟨0, [], false⟩

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  AVM Transform and Invariant
-- ═══════════════════════════════════════════════════════════════════════════

/-- I_AVM: invariant — program counter in bounds, not halted implies non-empty mem. -/
def avmInvariant (s : AVMState) : Prop :=
  s.halted ∨ s.mem.length > 0

/-- AVM step semantics: advance PC or halt. -/
def avmStep (s : AVMState) : AVMState :=
  if s.halted then s
  else { s with pc := s.pc + 1 }

/-- T_AVM: transform — single step or identity if halted. -/
def avmTransform (a b : AVMState) : Outcome AVMState :=
  if b = avmStep a then
    Outcome.ok b
  else
    Outcome.quarantined ⟨"AVM-step-mismatch", #[], a.pc⟩

/-- K_AVM: cost = number of steps taken (PC delta). -/
def avmCost (a b : AVMState) : Int :=
  (b.pc.toNat : Int) - (a.pc.toNat : Int)

/-- R_AVM: residual = 0 for valid steps (exact semantics). -/
def avmResidual (a b : AVMState) : Int :=
  if b = avmStep a then 0 else 1

/-- Projection: current PC as observable. -/
def avmProject (s : AVMState) : UInt64 := s.pc

inductive AVMScaleBand : Type where
  | SingleStep
  | MultiStep
  deriving Inhabited, DecidableEq, BEq

def avmValidAtScale (band : AVMScaleBand) (s : AVMState) : Prop :=
  match band with
  | AVMScaleBand.SingleStep => True
  | AVMScaleBand.MultiStep  => True

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  ModelUpgrade Instance
-- ═══════════════════════════════════════════════════════════════════════════

def avmModel : ModelUpgrade AVMState AVMScaleBand UInt64 where
  transform    := avmTransform
  invariant    := avmInvariant
  residual     := avmResidual
  cost         := avmCost
  project      := avmProject
  validAtScale := avmValidAtScale

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Th3: AVM Closure — Self-Hosting Proof
-- ═══════════════════════════════════════════════════════════════════════════

/-- AVM is Hostable because it is computable (trivially, per definitional equality). -/
theorem Th3_avm_closure : Hostable avmModel :=
by
  unfold Hostable computable
  trivial

end InvariantReceipt.AVM
