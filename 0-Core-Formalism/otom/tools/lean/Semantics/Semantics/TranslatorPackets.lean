/-
TranslatorPackets.lean — finite scaffold for metaphor-to-operator packet translation v0.1

Purpose:
  Model the discrete bookkeeping around Translator Packets: raw surfaces are
  inspected for object carriers, transforms, triggers, receipts, Warden bounds,
  and theorem shapes.

Boundary:
  This module does not formalize human intuition or prove a metaphor true.
  It only encodes the finite gates used to decide whether a metaphor-heavy
  packet is eligible for spec writing, Lean scaffolding, or receipt promotion.
-/

import Std

namespace Semantics.TranslatorPackets

/-- Evidence state for packet-derived artifacts. -/
inductive ClaimState where
  | beautifulProvisional
  | calibratedEngineeringDelta
  | reviewed
  deriving Repr, DecidableEq, Inhabited

/-- Packet quality level. -/
inductive PacketLevel where
  | noise
  | motif
  | operatorCandidate
  | gateCandidate
  | receiptableArtifact
  | reviewedClaim
  deriving Repr, DecidableEq, Inhabited

/-- Mathematical type assigned to the object carrier. -/
inductive CarrierType where
  | unknown
  | scalarField
  | vectorState
  | localFrame
  | latticeState
  | pairSignature
  | oracleResponse
  | receiptLedger
  | supportPredicate
  deriving Repr, DecidableEq, Inhabited

/-- A finite Translator Packet record. -/
structure TranslatorPacket where
  packetId : String
  rawSurface : String
  objectCarrierPresent : Bool
  transformPresent : Bool
  triggerPresent : Bool
  receiptPresent : Bool
  wardenBoundaryPresent : Bool
  theoremShapePresent : Bool
  carrierType : CarrierType
  claimState : ClaimState
  deriving Repr, DecidableEq, Inhabited

/-- Strong packet anatomy: object + transform + trigger + receipt. -/
def HasStrongAnatomy (p : TranslatorPacket) : Prop :=
  p.objectCarrierPresent = true ∧
  p.transformPresent = true ∧
  p.triggerPresent = true ∧
  p.receiptPresent = true

/-- Warden-safe packet: has boundary preventing metaphor overclaim. -/
def WardenSafe (p : TranslatorPacket) : Prop :=
  p.wardenBoundaryPresent = true

/-- Lean-eligible packet: enough finite structure for a theorem/gate scaffold. -/
def LeanEligible (p : TranslatorPacket) : Prop :=
  HasStrongAnatomy p ∧ WardenSafe p ∧ p.theoremShapePresent = true

/-- Executable classifier for packet quality. -/
def classifyPacket (p : TranslatorPacket) : PacketLevel :=
  if p.claimState == ClaimState.reviewed then
    .reviewedClaim
  else if p.theoremShapePresent && p.wardenBoundaryPresent && p.objectCarrierPresent &&
          p.transformPresent && p.triggerPresent && p.receiptPresent then
    .gateCandidate
  else if p.objectCarrierPresent && p.transformPresent then
    .operatorCandidate
  else if p.objectCarrierPresent || p.transformPresent || p.triggerPresent || p.receiptPresent then
    .motif
  else
    .noise

/-- A packet eligible for Lean scaffolding classifies at least as gateCandidate in this simple classifier. -/
theorem lean_eligible_classifies_gate_candidate
    (p : TranslatorPacket)
    (h : LeanEligible p)
    (hNotReviewed : p.claimState ≠ ClaimState.reviewed) :
    classifyPacket p = PacketLevel.gateCandidate := by
  unfold LeanEligible HasStrongAnatomy WardenSafe at h
  rcases h with ⟨⟨hObj, hTrans, hTrig, hRec⟩, hWard, hTheo⟩
  unfold classifyPacket
  cases p.claimState <;> simp [hObj, hTrans, hTrig, hRec, hWard, hTheo] at *

/-- A packet with no object, transform, trigger, or receipt classifies as noise unless already reviewed. -/
theorem empty_packet_classifies_noise
    (p : TranslatorPacket)
    (hObj : p.objectCarrierPresent = false)
    (hTrans : p.transformPresent = false)
    (hTrig : p.triggerPresent = false)
    (hRec : p.receiptPresent = false)
    (hNotReviewed : p.claimState ≠ ClaimState.reviewed) :
    classifyPacket p = PacketLevel.noise := by
  unfold classifyPacket
  cases p.claimState <;> simp [hObj, hTrans, hTrig, hRec] at *

/-- Metaphor proof is blocked unless the packet is reviewed by receipts. -/
def CanPromoteToReviewed (p : TranslatorPacket) : Prop :=
  p.claimState = ClaimState.reviewed

/-- Lean eligibility alone is not reviewed promotion. -/
theorem lean_eligible_not_reviewed_by_itself
    (p : TranslatorPacket)
    (h : LeanEligible p)
    (hState : p.claimState = ClaimState.beautifulProvisional) :
    ¬ CanPromoteToReviewed p := by
  intro hp
  unfold CanPromoteToReviewed at hp
  rw [hState] at hp
  contradiction

/-- Torsion flip phrase packet example. -/
def torsionFlipPacket : TranslatorPacket :=
  { packetId := "torsion-flip"
    rawSurface := "turned round and round and upside down"
    objectCarrierPresent := true
    transformPresent := true
    triggerPresent := true
    receiptPresent := true
    wardenBoundaryPresent := true
    theoremShapePresent := true
    carrierType := .localFrame
    claimState := .beautifulProvisional }

/-- SORRY collapse packet example. -/
def sorryCollapsePacket : TranslatorPacket :=
  { packetId := "sorry-collapse"
    rawSurface := "Connect Four pieces slide off the board and SORRY is spoken"
    objectCarrierPresent := true
    transformPresent := true
    triggerPresent := true
    receiptPresent := true
    wardenBoundaryPresent := true
    theoremShapePresent := true
    carrierType := .latticeState
    claimState := .beautifulProvisional }

/-- Weak mood-only packet example. -/
def weakMoodPacket : TranslatorPacket :=
  { packetId := "weak-mood"
    rawSurface := "strange feeling"
    objectCarrierPresent := false
    transformPresent := false
    triggerPresent := false
    receiptPresent := false
    wardenBoundaryPresent := false
    theoremShapePresent := false
    carrierType := .unknown
    claimState := .beautifulProvisional }

/-- Torsion packet is Lean-eligible. -/
theorem torsionFlipPacket_lean_eligible : LeanEligible torsionFlipPacket := by
  unfold LeanEligible HasStrongAnatomy WardenSafe torsionFlipPacket
  simp

/-- SORRY packet is Lean-eligible. -/
theorem sorryCollapsePacket_lean_eligible : LeanEligible sorryCollapsePacket := by
  unfold LeanEligible HasStrongAnatomy WardenSafe sorryCollapsePacket
  simp

/-- Weak mood packet is not Lean-eligible. -/
theorem weakMoodPacket_not_lean_eligible : ¬ LeanEligible weakMoodPacket := by
  intro h
  unfold LeanEligible HasStrongAnatomy weakMoodPacket at h
  simp at h

#eval classifyPacket torsionFlipPacket -- gateCandidate
#eval classifyPacket sorryCollapsePacket -- gateCandidate
#eval classifyPacket weakMoodPacket -- noise

end Semantics.TranslatorPackets
