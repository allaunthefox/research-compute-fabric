-- Invariant Receipt Protocol: Model promotion status and registry
-- Constitutional layer: compiles clean

import InvariantReceipt.Core

namespace InvariantReceipt

inductive PromotionStatus : Type where
  | rawIdea
  | sanitizedMetaphor
  | toyModel
  | typedModel
  | residualTested
  | costAccounted
  | proofCandidate
  | coreModule
  | quarantined
  | archived
  | metaphorOnly
  deriving Inhabited, DecidableEq, BEq

structure RegisteredModel where
  tag        : String
  status     : PromotionStatus
  provenance : List Nat
  deriving Inhabited, DecidableEq, BEq

end InvariantReceipt
