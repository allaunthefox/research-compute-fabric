import Semantics.Quaternion
import Semantics.TorsionalPIST

namespace Semantics.AMMR

open DynamicCanal

abbrev QuaternionState := Semantics.Quaternion.Quaternion

/-- Finite carrier classes. Carriers transport state; they do not certify truth. -/
inductive CarrierKind
| cpu
| fpga
| pcie
| quantumAccelerator
| grid
| shell
  deriving Repr, DecidableEq, BEq

/-- Finite RGFlow verdict classes for the AMMR wrapper. -/
inductive RGFlowVerdict
| lawful
| nearMiss
| reject
| carrierUnstable
  deriving Repr, DecidableEq, BEq

/-- Carrier health is finite and bounded before it can affect routing. -/
inductive CarrierHealth
| nominal
| mildDeviation
| warning
| critical
| invalid
  deriving Repr, DecidableEq, BEq

/-- Failure memory separates mathematical and carrier scars. -/
structure FailureMemory where
  mathScar : UInt32
  carrierScar : UInt32
  nearMissScar : UInt32
  proofScar : UInt32
  deriving Repr, DecidableEq, BEq

/-- Replay witness root. The hash is payload, not decision logic. -/
structure WitnessRoot where
  root : UInt64
  replayable : Bool
  deriving Repr, DecidableEq, BEq

/-- RGFlow strip policy. Each bit is a finite keep/drop decision, not a string rule. -/
structure RGStripPolicy where
  keepConnectivity : Bool
  keepMemory : Bool
  keepYield : Bool
  witnessRequired : Bool
  carrierFaultRequired : Bool
  basinProtected : Bool
  deriving Repr, DecidableEq, BEq

/-- AMMR state wraps the quaternion reducer with invariant, carrier, memory, and witness state. -/
structure AMMRState where
  objectId : UInt64
  invariantLock : Fix16
  q : QuaternionState
  rotor : QuaternionState
  stripPolicy : RGStripPolicy
  famm : FailureMemory
  rgflow : RGFlowVerdict
  witness : WitnessRoot
  carrier : CarrierKind
  carrierHealth : CarrierHealth
  deriving Repr, DecidableEq, BEq

/-- AMMR step output with the updated state and projected quaternion. -/
structure AMMRStep where
  state : AMMRState
  stripped : QuaternionState
  projected : QuaternionState
  lawful : Bool
  cost : UInt32
  deriving Repr, DecidableEq, BEq

def zeroFailureMemory : FailureMemory :=
  { mathScar := 0, carrierScar := 0, nearMissScar := 0, proofScar := 0 }

def defaultWitnessRoot : WitnessRoot :=
  { root := 0, replayable := true }

def defaultStripPolicy : RGStripPolicy :=
  { keepConnectivity := true
  , keepMemory := true
  , keepYield := true
  , witnessRequired := true
  , carrierFaultRequired := false
  , basinProtected := true
  }

def defaultState : AMMRState :=
  { objectId := 0
  , invariantLock := Fix16.one
  , q := Semantics.Quaternion.Quaternion.one
  , rotor := Semantics.Quaternion.Quaternion.one
  , stripPolicy := defaultStripPolicy
  , famm := zeroFailureMemory
  , rgflow := .lawful
  , witness := defaultWitnessRoot
  , carrier := .cpu
  , carrierHealth := .nominal
  }

/-- The declared invariant is the quaternion K/w channel. -/
def invariantOf (q : QuaternionState) : Fix16 :=
  q.w

/-- Projection Πᴷ restores the declared invariant lock after quaternion motion. -/
def projectK (lock : Fix16) (q : QuaternionState) : QuaternionState :=
  { q with w := lock }

/-- RGFlow strip removes non-invariant C/M/Y mass before expensive quaternion motion. -/
def rgflowStrip (policy : RGStripPolicy) (q : QuaternionState) : QuaternionState :=
  { w := q.w
  , x := if policy.keepConnectivity then q.x else Fix16.zero
  , y := if policy.keepMemory then q.y else Fix16.zero
  , z := if policy.keepYield then q.z else Fix16.zero
  }

/-- Number of quaternion channels retained by RGFlow strip. K is always retained. -/
def rgflowStripRetainedChannels (policy : RGStripPolicy) : Nat :=
  1
  + (if policy.keepConnectivity then 1 else 0)
  + (if policy.keepMemory then 1 else 0)
  + (if policy.keepYield then 1 else 0)

/-- The finite carrier boundedness gate. -/
def validCarrierHealth (h : CarrierHealth) : Bool :=
  match h with
  | .nominal => true
  | .mildDeviation => true
  | .warning => true
  | .critical => false
  | .invalid => false

/-- Strip is lawful only when replay and carrier-fault obligations survive as metadata. -/
def rgflowStripLawful (s : AMMRState) : Bool :=
  (s.witness.replayable || !s.stripPolicy.witnessRequired) &&
  (validCarrierHealth s.carrierHealth || s.stripPolicy.carrierFaultRequired)

/-- RGFlow verdicts accepted for route expansion under AMMR. -/
def verdictAllowsRoute (v : RGFlowVerdict) : Bool :=
  match v with
  | .lawful => true
  | .nearMiss => true
  | .reject => false
  | .carrierUnstable => false

/-- Rotor inverse approximation for unit-like route rotors: conjugation. -/
def rotorInverse (r : QuaternionState) : QuaternionState :=
  Semantics.Quaternion.Quaternion.conj r

/-- Quaternion CMYK/OISC motion: R Q R⁻¹ + ΔQ. -/
def quaternionMotion (rotor q delta : QuaternionState) : QuaternionState :=
  let left := Semantics.Quaternion.Quaternion.mul rotor q
  let rotated := Semantics.Quaternion.Quaternion.mul left (rotorInverse rotor)
  Semantics.Quaternion.Quaternion.add rotated delta

/-- The AMMR-wrapped quaternion update: Πᴷ(R Q̂ R⁻¹ + ΔQ), where Q̂ is stripped. -/
def quaternionReductionUpdate (s : AMMRState) (delta : QuaternionState) : QuaternionState :=
  let stripped := rgflowStrip s.stripPolicy s.q
  projectK s.invariantLock (quaternionMotion s.rotor stripped delta)

/-- Failure accounting records rejected, near-miss, carrier, and proof failures separately. -/
def updateFailureMemory (m : FailureMemory) (verdict : RGFlowVerdict) (w : WitnessRoot) : FailureMemory :=
  let withVerdict :=
    match verdict with
    | .lawful => m
    | .nearMiss => { m with nearMissScar := m.nearMissScar + 1 }
    | .reject => { m with mathScar := m.mathScar + 1 }
    | .carrierUnstable => { m with carrierScar := m.carrierScar + 1 }
  if w.replayable then withVerdict else { withVerdict with proofScar := withVerdict.proofScar + 1 }

/-- AMMR safety: invariant preserved, carrier bounded, route witnessed, failure remembered. -/
def ammrSafe (before after : AMMRState) : Bool :=
  (invariantOf after.q == invariantOf before.q) &&
  rgflowStripLawful before &&
  validCarrierHealth after.carrierHealth &&
  after.witness.replayable &&
  verdictAllowsRoute after.rgflow

/-- AMMR outer contract around the quaternion reducer. -/
def ammrStep (s : AMMRState) (delta : QuaternionState) : AMMRStep :=
  let stripped := rgflowStrip s.stripPolicy s.q
  let projected := quaternionReductionUpdate s delta
  let nextMemory := updateFailureMemory s.famm s.rgflow s.witness
  let next := { s with q := projected, famm := nextMemory }
  let lawful := ammrSafe s next
  let cost := if lawful then 0x00010000 else 0x00020000
  { state := next, stripped := stripped, projected := projected, lawful := lawful, cost := cost }

/-- TorsionalPIST exposes its mediator q3 as the executable quaternion tile state. -/
def torsionalTileQuaternion (tile : Semantics.TorsionalPIST.TorsionalState) : QuaternionState :=
  tile.q3

/-- TorsionalPIST beta step is the concrete quaternion OISC tile motion. -/
def torsionalOISCStep
    (tile : Semantics.TorsionalPIST.TorsionalState)
    (dt : Fix16) : Semantics.TorsionalPIST.TorsionalState :=
  Semantics.TorsionalPIST.TorsionalState_torsionalBetaStep tile dt

/-- Delta emitted by a torsional tile beta step, measured on the mediator quaternion. -/
def torsionalTileDelta
    (tile nextTile : Semantics.TorsionalPIST.TorsionalState) : QuaternionState :=
  Semantics.Quaternion.Quaternion.sub nextTile.q3 tile.q3

/-- Embed a torsional tile as the current AMMR quaternion state before stepping. -/
def ammrStateFromTorsionalTile
    (s : AMMRState)
    (tile : Semantics.TorsionalPIST.TorsionalState) : AMMRState :=
  { s with
    q := torsionalTileQuaternion tile
    invariantLock := invariantOf (torsionalTileQuaternion tile) }

/-- AMMR step driven by the concrete TorsionalPIST tile. -/
def ammrStepFromTorsionalTile
    (s : AMMRState)
    (tile : Semantics.TorsionalPIST.TorsionalState)
    (dt : Fix16) : AMMRStep :=
  let nextTile := torsionalOISCStep tile dt
  let delta := torsionalTileDelta tile nextTile
  let tileBackedState := ammrStateFromTorsionalTile s tile
  ammrStep tileBackedState delta

theorem projectK_preservesInvariant (lock : Fix16) (q : QuaternionState) :
    invariantOf (projectK lock q) = lock := by
  rfl

theorem rgflowStrip_preservesInvariant (policy : RGStripPolicy) (q : QuaternionState) :
    invariantOf (rgflowStrip policy q) = invariantOf q := by
  rfl

theorem quaternionReductionUpdate_preservesInvariant (s : AMMRState) (delta : QuaternionState) :
    invariantOf (quaternionReductionUpdate s delta) = s.invariantLock := by
  rfl

theorem defaultCarrierHealthValid :
    validCarrierHealth defaultState.carrierHealth = true := by
  rfl

theorem defaultAMMRStepLawful :
    (ammrStep defaultState Semantics.Quaternion.Quaternion.zero).lawful = true := by
  rfl

theorem rejectIncrementsMathScar (m : FailureMemory) (w : WitnessRoot) :
    (updateFailureMemory m .reject w).mathScar = m.mathScar + 1 := by
  by_cases h : w.replayable
  · simp [updateFailureMemory, h]
  · simp [updateFailureMemory, h]

theorem defaultStripRetainsAllChannels :
    rgflowStripRetainedChannels defaultStripPolicy = 4 := by
  rfl

theorem torsionalTileQuaternion_isMediator (tile : Semantics.TorsionalPIST.TorsionalState) :
    torsionalTileQuaternion tile = tile.q3 := by
  rfl

theorem ammrStateFromTorsionalTile_usesTileInvariant
    (s : AMMRState) (tile : Semantics.TorsionalPIST.TorsionalState) :
    (ammrStateFromTorsionalTile s tile).invariantLock =
      invariantOf (torsionalTileQuaternion tile) := by
  rfl

-- #eval expected: true
#eval (ammrStep defaultState Semantics.Quaternion.Quaternion.zero).lawful

-- #eval expected: 65536
#eval (ammrStep defaultState Semantics.Quaternion.Quaternion.zero).cost

-- #eval expected: 4
#eval rgflowStripRetainedChannels defaultStripPolicy

-- #eval expected: true
#eval (ammrStepFromTorsionalTile defaultState
  Semantics.TorsionalPIST.TorsionalState_initial Fix16.one).lawful

end Semantics.AMMR
