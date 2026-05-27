import Semantics.Basic
import Semantics.FixedPoint

namespace Semantics.Swarm

open Semantics.Q16_16

structure Genome where
  muBin    : UInt8
  rhoBin   : UInt8
  cBin     : UInt8
  mBin     : UInt8
  neBin    : UInt8
  sigBin   : UInt8
  deriving Repr, BEq, DecidableEq

def Genome.muQ    (g : Genome) : Q16_16 := ofRawInt (0x41 * (g.muBin.toNat + 1))
def Genome.rhoQ   (g : Genome) : Q16_16 := ofRawInt (0x2000 * (g.rhoBin.toNat + 1))
def Genome.cFac   (g : Genome) : Q16_16 := ofRawInt (0x2000 * (g.cBin.toNat + 1))
def Genome.mFac   (g : Genome) : Q16_16 := ofRawInt (0x2000 * (g.mBin.toNat + 1))
def Genome.neRaw  (g : Genome) : Q16_16 := ofRawInt (0x4000 * (g.neBin.toNat + 1))
def Genome.sigQ   (g : Genome) : Q16_16 := ofRawInt (65536 + 0x4000 * (g.sigBin.toNat + 1))

def Genome.neEff (g : Genome) : Q16_16 :=
  let n := g.neBin.toNat + 1
  match n with
  | 1 => ofRawInt 0
  | 2 => ofRawInt 65536
  | 3 => ofRawInt 103893
  | 4 => ofRawInt 131072
  | 5 => ofRawInt 152192
  | 6 => ofRawInt 169472
  | 7 => ofRawInt 184000
  | _ => ofRawInt 196608

def isLawful (g : Genome) : Bool :=
  let D : Q16_16 := ofRawInt 196
  let B : Q16_16 := ofRawInt 65
  let lambdaConstant : Q16_16 := ofRawInt 65536
  let mStar : Q16_16 := ofRawInt 32768
  let l1 := decide (g.muQ <= D / g.cFac)
  let phi := ofRawInt 65536 - (g.mFac - mStar).abs
  let l2 := decide (g.rhoQ * g.neEff * phi >= B)
  let l3 := decide (g.sigQ > ofRawInt 65536 + lambdaConstant * g.muQ)
  l1 && l2 && l3

def betaStep (g : Genome) : Genome :=
  { g with
      muBin := if g.muBin > 0 then g.muBin - 1 else 0,
      neBin := if g.neBin < 7 then g.neBin + 1 else 7 }

def isScaleCoherent (g : Genome) : Bool :=
  let g1 := betaStep g
  let g2 := betaStep g1
  let g3 := betaStep g2
  isLawful g && isLawful g1 && isLawful g2 && isLawful g3

structure FlowAudit where
  initiallyLawful    : Bool
  alwaysLawful       : Bool
  eventuallyLawful   : Bool
  finalLawful        : Bool
  firstFailureDepth  : Option Nat
  firstRecoveryDepth : Option Nat
  finalDepth         : Nat
  deriving Repr, BEq

def flowAuditLoop (init : Bool) (steps : Nat) (i : Nat) (current : Genome)
    (always : Bool) (firstFail : Option Nat) (firstRec : Option Nat) : FlowAudit :=
  match i with
  | 0 =>
    { initiallyLawful    := init
      alwaysLawful       := always
      eventuallyLawful   := isLawful current
      finalLawful        := isLawful current
      firstFailureDepth  := firstFail
      firstRecoveryDepth := firstRec
      finalDepth         := steps }
  | i1 + 1 =>
    let next := betaStep current
    let lawful := isLawful next
    let newAlways := always && lawful
    let newFail := if !lawful && firstFail.isNone then some (steps - i1) else firstFail
    let newRec  := if lawful && !init && firstRec.isNone then some (steps - i1) else firstRec
    flowAuditLoop init steps i1 next newAlways newFail newRec

def flowAudit (g : Genome) (steps : Nat) : FlowAudit :=
  flowAuditLoop (isLawful g) steps steps g (isLawful g) none none

-- Witnesses

def witnessLowNe : Genome :=
  { muBin := 0, rhoBin := 0, cBin := 0, mBin := 0, neBin := 0, sigBin := 0 }

#eval flowAudit witnessLowNe 8

def witnessAttractor : Genome :=
  { muBin := 0, rhoBin := 4, cBin := 4, mBin := 4, neBin := 7, sigBin := 7 }

#eval flowAudit witnessAttractor 8

def witnessBoundary : Genome :=
  { muBin := 7, rhoBin := 7, cBin := 0, mBin := 3, neBin := 3, sigBin := 7 }

#eval flowAudit witnessBoundary 8

-- Theorem: finalLawful and eventuallyLawful are equal by construction.

private theorem flowAuditLoopFinalEqEventually {init : Bool} {steps : Nat} {i : Nat} {current : Genome}
    {always : Bool} {ff fr : Option Nat} :
    (flowAuditLoop init steps i current always ff fr).finalLawful =
    (flowAuditLoop init steps i current always ff fr).eventuallyLawful := by
  induction i generalizing current always ff fr with
  | zero => simp [flowAuditLoop]
  | succ n ih =>
    simp only [flowAuditLoop]
    exact ih

theorem finalLawfulEqEventuallyLawful (g : Genome) (s : Nat) :
    (flowAudit g s).finalLawful = (flowAudit g s).eventuallyLawful := by
  unfold flowAudit
  apply flowAuditLoopFinalEqEventually

end Semantics.Swarm
