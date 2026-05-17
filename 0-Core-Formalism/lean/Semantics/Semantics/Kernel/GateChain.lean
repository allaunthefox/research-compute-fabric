/-
GateChain.lean — Multiplicative eigengate composition.

Imports EigenGate.lean for the canonical Eigengate, EigenVerdict, and
score/verdict/route/chainVerdict primitives. Adds chain-level composition
and product-score computation.
-/

import Semantics.FixedPoint
import Semantics.Kernel.EigenGate

namespace Semantics.Kernel

open Semantics.FixedPoint (Q0_16)
open Semantics.Kernel (Eigengate EigenVerdict)

structure ChainGate (α : Type) where
  gate     : Eigengate α
  required : Bool

abbrev GateChain (α : Type) : Type := List (ChainGate α)

def chainGatesToTuples {α : Type} (chain : GateChain α) : List (Eigengate α × Bool) :=
  chain.map fun cg => (cg.gate, cg.required)

def chainScore {α : Type} (chain : GateChain α) (s : α) : Q0_16 :=
  let requiredScores := chain
    |>.filter (fun cg => cg.required)
    |>.map fun cg => score (cg.gate.residual s)
  requiredScores.foldl Q0_16.mul Q0_16.one

def testChainAllAdmit : GateChain Q0_16 :=
  [ { gate := testGateAllAdmit, required := true }
  , { gate := testGateAllAdmit, required := true } ]

def testChainOptionalOnly : GateChain Q0_16 :=
  [ { gate := testGateAllAdmit, required := true }
  , { gate := testGateAllReject, required := false } ]

theorem chainCompositionAllAdmit :
    chainVerdict (chainGatesToTuples testChainAllAdmit) Q0_16.zero = EigenVerdict.admit := by
  native_decide

theorem chain_optional_reject_preserves_admit :
    chainVerdict (chainGatesToTuples testChainOptionalOnly) Q0_16.zero = EigenVerdict.admit := by
  native_decide

theorem chainScore_all_admit_is_one :
    chainScore testChainAllAdmit Q0_16.zero = Q0_16.one := by
  native_decide

#eval chainVerdict (chainGatesToTuples testChainAllAdmit) Q0_16.zero
#eval chainVerdict (chainGatesToTuples testChainOptionalOnly) Q0_16.zero
#eval chainScore testChainAllAdmit Q0_16.zero

end Semantics.Kernel
