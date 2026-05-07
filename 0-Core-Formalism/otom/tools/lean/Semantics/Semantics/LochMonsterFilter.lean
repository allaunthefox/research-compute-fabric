/-
  LochMonsterFilter.lean

  LNMF: Loch-Nessie-Monster Filter

  This module filters a collapsed MassNumberField through four increasingly
  restrictive gates:
    1. Loch detection: trapped hidden-basin mass.
    2. nE extraction: hidden n-indexed energy/entity/event packets.
    3. Nessie recurrence: recurring nE traces below direct visibility.
    4. Monster symmetry amplification: coherent symmetry over Nessie traces.

  Canonical law:
    A loch traps mass; Nessies are recurring hidden nE traces; a monster is
    what forms when those traces gain symmetry.

  Filter law:
    Filter the monster by asking: is the mass trapped, recurring, symmetric,
    and biased toward archive or drain?

  Claim boundary:
  - Loch detection is a hidden-basin heuristic over a weighted graph/region.
  - Nessie detection records recurring hidden nE traces below visibility.
  - Monster score is a symmetry-amplified routing score, not a proof that the
    mathematical Monster group is present.
  - automorphismOrder is an attached estimate/witness unless a proof artifact
    is supplied.
-/

import Mathlib.Data.Nat.Basic
import Semantics.FixedPoint
import Semantics.FullMasterMassNumberReduction

namespace Semantics.LochMonsterFilter

open Semantics.Q16_16
open Semantics.FullMasterMassNumberReduction

/-- Q16.16 value for 0.5. Prefer raw constructor because `ofNat 32768` means 32768.0. -/
def halfQ16 : Q16_16 := ⟨32768⟩

/-- Route selected by the Loch-Nessie-Monster filter. -/
inductive MonsterRoute where
  | standard
  | pistWitnessNessie
  | bhocsCommitMonster
  | fammDrainMonster
  | quarantineNessie
  deriving Repr, DecidableEq, Inhabited

/-- Monster class after hidden-basin filtering. -/
inductive MonsterPhase where
  | noLoch
  | lochOnly
  | nessieTrace
  | dormantMonster
  | archiveMonster
  | drainMonster
  | seismicMonster
  deriving Repr, DecidableEq, Inhabited

/-- Input summary for a candidate hidden region L. -/
structure LochRegion where
  internalCoupling : Q16_16  -- Σ_{i,j∈L} w_ij
  boundaryLeakage  : Q16_16  -- Σ_{i∈L,j∉L} w_ij
  zLocal           : Nat     -- local structured/control/witness mass
  nLocal           : Nat     -- local stress/dynamics/residual mass
  density          : Q16_16  -- local rho_L, usually inherited from S3C/PIST
  deriving Repr, Inhabited

/-- Hidden n-indexed energy/entity/event packet. -/
structure NEPacket where
  packetMass : Q16_16  -- A_{L,i}
  density    : Q16_16  -- rho_{L,i}
  scar       : Q16_16  -- Scar_i(L) = accumulated hysteresis/FAMM/COUCH memory
  visibility : Q16_16  -- direct observation strength
  deriving Repr, Inhabited

/-- Thresholds for the Loch-Nessie-Monster filter. -/
structure MonsterThresholds where
  thetaLoch    : Q16_16
  thetaEnergy  : Q16_16
  thetaVisible : Q16_16
  thetaMonster : Q16_16
  betaBias     : Q16_16
  minNessies   : Nat
  deriving Repr, Inhabited

/-- Final compact filter output. -/
structure MonsterFilterResult where
  lochScore       : Q16_16
  nessieCount     : Nat
  nessieEnergySum : Q16_16
  monsterScore    : Q16_16
  automorphismOrder : Nat
  localA          : Nat
  localZ          : Nat
  localN          : Nat
  biasSign        : BiasSign
  biasMagnitude   : Q16_16
  density         : Q16_16
  phase           : MonsterPhase
  route           : MonsterRoute
  deriving Repr, Inhabited

/-- Local total mass A_L = Z_L + N_L. -/
def localMass (r : LochRegion) : Nat :=
  r.zLocal + r.nLocal

/-- Loch(L) = internal/(1+leakage) * A_L. -/
def lochScore (r : LochRegion) : Q16_16 :=
  let couplingRatio := div r.internalCoupling (Q16_16.one + r.boundaryLeakage)
  couplingRatio * ofNat (localMass r)

/-- nE_i(L) = A_{L,i} * rho_{L,i} * Scar_i(L). -/
def nE (p : NEPacket) : Q16_16 :=
  p.packetMass * p.density * p.scar

/-- A packet is a Nessie when it has enough hidden energy but remains below visibility. -/
def isNessie (p : NEPacket) (thetaEnergy thetaVisible : Q16_16) : Bool :=
  nE p > thetaEnergy && p.visibility < thetaVisible

/-- Sum nE over packets classified as Nessies. -/
def sumNessieEnergy (packets : Array NEPacket) (thetaEnergy thetaVisible : Q16_16) : Q16_16 :=
  packets.foldl
    (fun acc p => if isNessie p thetaEnergy thetaVisible then acc + nE p else acc)
    zero

/-- Count packets classified as Nessies. -/
def countNessies (packets : Array NEPacket) (thetaEnergy thetaVisible : Q16_16) : Nat :=
  packets.foldl
    (fun acc p => if isNessie p thetaEnergy thetaVisible then acc + 1 else acc)
    0

/-- Monster score M(L) = |Aut(L)| * Loch(L) * Σ nE_i(L). -/
def monsterScore (autOrder : Nat) (loch nessieEnergy : Q16_16) : Q16_16 :=
  ofNat autOrder * loch * nessieEnergy

/-- Classify a confirmed or unconfirmed region after loch/nE/monster gates. -/
def classifyMonster
  (loch : Q16_16)
  (nessieCount : Nat)
  (score : Q16_16)
  (r : LochRegion)
  (thresholds : MonsterThresholds)
  (biasSign : BiasSign)
  (biasMagnitude : Q16_16) : MonsterPhase :=
  if loch ≤ thresholds.thetaLoch then .noLoch
  else if nessieCount < thresholds.minNessies then .lochOnly
  else if score ≤ thresholds.thetaMonster then .nessieTrace
  else if r.density ≥ halfQ16 then .seismicMonster
  else if biasMagnitude < thresholds.betaBias then .dormantMonster
  else match biasSign with
    | .structuredHeavy => .archiveMonster
    | .stressHeavy => .drainMonster
    | .balanced => .dormantMonster

/-- Route corresponding to the MonsterPhase. -/
def routeForMonsterPhase : MonsterPhase → MonsterRoute
  | .noLoch => .standard
  | .lochOnly => .pistWitnessNessie
  | .nessieTrace => .pistWitnessNessie
  | .dormantMonster => .pistWitnessNessie
  | .archiveMonster => .bhocsCommitMonster
  | .drainMonster => .fammDrainMonster
  | .seismicMonster => .quarantineNessie

/-- Run the full Loch-Nessie-Monster filter over region L. -/
def runLochMonsterFilter
  (r : LochRegion)
  (packets : Array NEPacket)
  (automorphismOrder : Nat)
  (thresholds : MonsterThresholds) : MonsterFilterResult :=
  let A := localMass r
  let biasSign := biasSignOf r.zLocal r.nLocal
  let biasMagnitude := biasMagnitudeQ16 r.zLocal r.nLocal A
  let loch := lochScore r
  let nCount := countNessies packets thresholds.thetaEnergy thresholds.thetaVisible
  let nEnergy := sumNessieEnergy packets thresholds.thetaEnergy thresholds.thetaVisible
  let mScore := monsterScore automorphismOrder loch nEnergy
  let phase := classifyMonster loch nCount mScore r thresholds biasSign biasMagnitude
  let route := routeForMonsterPhase phase
  {
    lochScore := loch,
    nessieCount := nCount,
    nessieEnergySum := nEnergy,
    monsterScore := mScore,
    automorphismOrder := automorphismOrder,
    localA := A,
    localZ := r.zLocal,
    localN := r.nLocal,
    biasSign := biasSign,
    biasMagnitude := biasMagnitude,
    density := r.density,
    phase := phase,
    route := route
  }

/-- A monster is confirmed when the phase is one of the monster classes. -/
def isConfirmedMonster (r : MonsterFilterResult) : Bool :=
  match r.phase with
  | .archiveMonster | .drainMonster | .dormantMonster | .seismicMonster => true
  | _ => false

/-- A monster result survives if it is not seismic/quarantined. -/
def survivesMonsterFilter (r : MonsterFilterResult) : Bool :=
  r.route ≠ .quarantineNessie

/-- Which equation surface owns the monster-filter assignment. -/
inductive MonsterFilterEquation where
  | treeFiddyBound      -- BHOCS / TREE(3)-style bounded archive and Faraday cage
  | locNesRecurrence    -- Loch-Nessie recurrence and hidden-basin witness
  | combinedGate        -- Both surfaces are active in a single filter decision
  deriving Repr, DecidableEq, Inhabited

/-- Assignment generated by the monster filter for downstream routing. -/
structure MonsterFilterAssignment where
  equation : MonsterFilterEquation
  phase    : MonsterPhase
  route    : MonsterRoute
  archiveToTreeFiddy : Bool
  witnessLocNes      : Bool
  quarantine         : Bool
  deriving Repr, Inhabited

/-- Assign a monster result to Tree Fiddy/BHOCS and/or Loc Nes surfaces. -/
def assignMonsterFilter (r : MonsterFilterResult) : MonsterFilterAssignment :=
  let archiveToTreeFiddy := r.route == .bhocsCommitMonster
  let witnessLocNes :=
    r.route == .pistWitnessNessie || r.phase == .nessieTrace || r.phase == .lochOnly
  let quarantine := r.route == .quarantineNessie
  let equation :=
    if archiveToTreeFiddy && witnessLocNes then .combinedGate
    else if archiveToTreeFiddy then .treeFiddyBound
    else .locNesRecurrence
  {
    equation := equation,
    phase := r.phase,
    route := r.route,
    archiveToTreeFiddy := archiveToTreeFiddy,
    witnessLocNes := witnessLocNes,
    quarantine := quarantine
  }

/-- Tree Fiddy owns archive/commit monster routes. -/
theorem assignTreeFiddyWhenBHOCSCommit (r : MonsterFilterResult)
    (h : r.route = .bhocsCommitMonster) :
    (assignMonsterFilter r).archiveToTreeFiddy = true := by
  simp [assignMonsterFilter, h]

/-- Loc Nes owns explicit Nessie-trace phases. -/
theorem assignLocNesWhenNessieTrace (r : MonsterFilterResult)
    (h : r.phase = .nessieTrace) :
    (assignMonsterFilter r).witnessLocNes = true := by
  simp [assignMonsterFilter, h]

/-- Quarantine routes stay marked as quarantine in the assignment. -/
theorem assignQuarantineWhenRouteQuarantine (r : MonsterFilterResult)
    (h : r.route = .quarantineNessie) :
    (assignMonsterFilter r).quarantine = true := by
  simp [assignMonsterFilter, h]

/-- Example thresholds for documentation/eval witnesses. -/
def exampleThresholds : MonsterThresholds := {
  thetaLoch := ofNat 1000,
  thetaEnergy := ofNat 10,
  thetaVisible := halfQ16,
  thetaMonster := ofNat 10000,
  betaBias := halfQ16,
  minNessies := 2
}

/-- Example loch region. -/
def exampleRegion : LochRegion := {
  internalCoupling := ofNat 100,
  boundaryLeakage := ofNat 1,
  zLocal := 400000,
  nLocal := 100000,
  density := ofNat 0
}

/-- Example nE packets. -/
def examplePackets : Array NEPacket := #[
  { packetMass := ofNat 100, density := Q16_16.one, scar := ofNat 1, visibility := ⟨1000⟩ },
  { packetMass := ofNat 200, density := Q16_16.one, scar := ofNat 1, visibility := ⟨2000⟩ },
  { packetMass := ofNat 300, density := Q16_16.one, scar := ofNat 1, visibility := ⟨3000⟩ }
]

/-- Example LNMF output. -/
def exampleMonsterFilterResult : MonsterFilterResult :=
  runLochMonsterFilter exampleRegion examplePackets 196883 exampleThresholds

#eval exampleMonsterFilterResult.nessieCount
#eval exampleMonsterFilterResult.automorphismOrder
#eval exampleMonsterFilterResult.phase
#eval exampleMonsterFilterResult.route
#eval assignMonsterFilter exampleMonsterFilterResult

end Semantics.LochMonsterFilter
