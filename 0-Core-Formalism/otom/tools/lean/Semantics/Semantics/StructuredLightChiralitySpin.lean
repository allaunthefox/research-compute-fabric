/-
StructuredLightChiralitySpin.lean — finite gates for structured-light chirality/spin equations v0.1

Purpose:
  Encode only the discrete/checkable side of the structured-light equation layer
  extracted from Mkhumbuza et al. (2026): topological charge split, S3 sign
  classification, spin-current samples, and optical-domain Warden boundaries.

Boundary:
  This module does not solve Maxwell equations, paraxial propagation, Gouy phase,
  or Laguerre-Gaussian evolution. It only checks finite bookkeeping predicates
  useful for the OTOM math stack.

No Float. Int/Nat stand in for fixed-point encoded measurements.
-/

import Std

namespace Semantics.StructuredLightChiralitySpin

/-- Domain marker. The equations are optical-domain only unless separately bridged. -/
inductive Domain where
  | optics
  | nonOptical
  deriving Repr, DecidableEq, Inhabited

/-- Claim state for the artifact. -/
inductive ClaimState where
  | beautifulProvisional
  | calibratedEngineeringDelta
  | reviewed
  deriving Repr, DecidableEq, Inhabited

/-- Circular-polarization dominance from S3 sign. -/
inductive SpinDominance where
  | rightCircular
  | leftCircular
  | balanced
  deriving Repr, DecidableEq, Inhabited

/-- Integer topological charge split ell_A = ell_p + Delta ell, ell_B = ell_p - Delta ell. -/
structure ChargeSplit where
  ellP : Int
  deltaEll : Int
  ellA : Int
  ellB : Int
  deriving Repr, DecidableEq, Inhabited

/-- Build the circular-component charge split. -/
def mkChargeSplit (ellP deltaEll : Int) : ChargeSplit :=
  { ellP := ellP
    deltaEll := deltaEll
    ellA := ellP + deltaEll
    ellB := ellP - deltaEll }

/-- The charge split is internally consistent. -/
def ChargeSplitConsistent (c : ChargeSplit) : Prop :=
  c.ellA = c.ellP + c.deltaEll ∧ c.ellB = c.ellP - c.deltaEll

/-- Any split built by mkChargeSplit is consistent. -/
theorem mkChargeSplit_consistent (ellP deltaEll : Int) :
    ChargeSplitConsistent (mkChargeSplit ellP deltaEll) := by
  unfold ChargeSplitConsistent mkChargeSplit
  simp

/-- Fixed-point encoded local Stokes sample. -/
structure StokesSample where
  sampleId : Nat
  s0 : Int
  s1 : Int
  s2 : Int
  s3 : Int
  domain : Domain
  claimState : ClaimState
  deriving Repr, DecidableEq, Inhabited

/-- Compute S3 from right and left circular intensities: S3 = IR - IL. -/
def computeS3 (iR iL : Int) : Int :=
  iR - iL

/-- Classify circular-polarization dominance from S3. -/
def classifyS3 (s3 : Int) : SpinDominance :=
  if s3 > 0 then .rightCircular
  else if s3 < 0 then .leftCircular
  else .balanced

/-- A balanced sample has S3 = 0. -/
def BalancedSample (s : StokesSample) : Prop :=
  s.s3 = 0

/-- An optical sample is domain-bounded. -/
def OpticalBounded (s : StokesSample) : Prop :=
  s.domain = Domain.optics

/-- S3 computed from equal circular intensities is zero. -/
theorem computeS3_equal_zero (i : Int) :
    computeS3 i i = 0 := by
  unfold computeS3
  omega

/-- Equal circular intensities classify as balanced. -/
theorem equal_intensities_classify_balanced (i : Int) :
    classifyS3 (computeS3 i i) = SpinDominance.balanced := by
  simp [computeS3, classifyS3]

/-- Positive S3 classifies as right-circular dominance. -/
theorem positive_s3_classifies_right (s3 : Int) (h : s3 > 0) :
    classifyS3 s3 = SpinDominance.rightCircular := by
  unfold classifyS3
  simp [h]

/-- Negative S3 classifies as left-circular dominance. -/
theorem negative_s3_classifies_left (s3 : Int) (h : s3 < 0) :
    classifyS3 s3 = SpinDominance.leftCircular := by
  unfold classifyS3
  have hNotPos : ¬ s3 > 0 := by omega
  simp [hNotPos, h]

/-- Finite spin-current sample J = <partial_y S3, -partial_x S3>. -/
structure SpinCurrentSample where
  partialY_S3 : Int
  partialX_S3 : Int
  jYLike : Int
  jXLike : Int
  deriving Repr, DecidableEq, Inhabited

/-- Build the spin-current sample from S3 gradients. -/
def mkSpinCurrent (partialY_S3 partialX_S3 : Int) : SpinCurrentSample :=
  { partialY_S3 := partialY_S3
    partialX_S3 := partialX_S3
    jYLike := partialY_S3
    jXLike := -partialX_S3 }

/-- Spin-current sample consistency. -/
def SpinCurrentConsistent (j : SpinCurrentSample) : Prop :=
  j.jYLike = j.partialY_S3 ∧ j.jXLike = -j.partialX_S3

/-- Any spin-current sample built by mkSpinCurrent is consistent. -/
theorem mkSpinCurrent_consistent (dy dx : Int) :
    SpinCurrentConsistent (mkSpinCurrent dy dx) := by
  unfold SpinCurrentConsistent mkSpinCurrent
  simp

/-- A structured-light equation packet is Warden-safe only in optics domain here. -/
structure OpticalEquationPacket where
  sourceDoiHash : Nat
  chargeSplit : ChargeSplit
  sample : StokesSample
  spinCurrent : SpinCurrentSample
  deriving Repr, DecidableEq, Inhabited

/-- Packet is bounded to the optics domain and has internally consistent charge/current bookkeeping. -/
def PacketGate (p : OpticalEquationPacket) : Prop :=
  OpticalBounded p.sample ∧
  ChargeSplitConsistent p.chargeSplit ∧
  SpinCurrentConsistent p.spinCurrent

/-- Passing the packet gate implies the sample is optics-domain, not a non-optical bridge. -/
theorem packet_gate_optics_bounded
    (p : OpticalEquationPacket)
    (h : PacketGate p) :
    p.sample.domain = Domain.optics := by
  exact h.left

/-- Passing the packet gate preserves charge split consistency. -/
theorem packet_gate_charge_consistent
    (p : OpticalEquationPacket)
    (h : PacketGate p) :
    ChargeSplitConsistent p.chargeSplit := by
  exact h.right.left

/-- Passing the packet gate preserves spin-current consistency. -/
theorem packet_gate_spin_current_consistent
    (p : OpticalEquationPacket)
    (h : PacketGate p) :
    SpinCurrentConsistent p.spinCurrent := by
  exact h.right.right

/-- Example source-plane balanced sample: S3 = 0. -/
def sourcePlaneSample : StokesSample :=
  { sampleId := 0
    s0 := 20
    s1 := 0
    s2 := 0
    s3 := computeS3 10 10
    domain := .optics
    claimState := .beautifulProvisional }

/-- Example propagated sample with right-circular dominance. -/
def propagatedSample : StokesSample :=
  { sampleId := 1
    s0 := 20
    s1 := 0
    s2 := 0
    s3 := computeS3 13 7
    domain := .optics
    claimState := .beautifulProvisional }

/-- Example optical equation packet. -/
def examplePacket : OpticalEquationPacket :=
  { sourceDoiHash := 103841377026022786
    chargeSplit := mkChargeSplit 1 1
    sample := propagatedSample
    spinCurrent := mkSpinCurrent 3 (-2) }

/-- Source-plane example is balanced. -/
theorem sourcePlaneSample_balanced : BalancedSample sourcePlaneSample := by
  unfold BalancedSample sourcePlaneSample computeS3
  omega

/-- Propagated example classifies as right circular dominance. -/
theorem propagatedSample_right_dominant :
    classifyS3 propagatedSample.s3 = SpinDominance.rightCircular := by
  unfold propagatedSample computeS3
  exact positive_s3_classifies_right 6 (by omega)

/-- Example packet passes the finite gate. -/
theorem examplePacket_gate : PacketGate examplePacket := by
  unfold PacketGate examplePacket propagatedSample
  constructor
  · unfold OpticalBounded
    rfl
  · constructor
    · exact mkChargeSplit_consistent 1 1
    · exact mkSpinCurrent_consistent 3 (-2)

#eval mkChargeSplit 1 1
#eval computeS3 10 10
#eval classifyS3 (computeS3 10 10)
#eval classifyS3 (computeS3 13 7)
#eval mkSpinCurrent 3 (-2)

end Semantics.StructuredLightChiralitySpin
