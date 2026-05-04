/-
MetasurfacePolarizationControl.lean — finite gates for metasurface polarization-control equations v0.1

Purpose:
  Encode only the discrete/checkable side of the metasurface optics equation layer:
  double-phase channel bookkeeping, bilayer composition flags, PB sign rules,
  exceptional-point discriminant checks, nonlinear broken-symmetry bilayer gates,
  and optics-domain Warden boundaries.

Boundary:
  This module does not solve Maxwell equations, fabricate metasurfaces, compute
  full Jones matrices, or prove non-optical OTOM claims. It only checks finite
  predicates and algebraic bookkeeping used by the Markdown equation spec.

No Float. Int/Nat stand in for fixed-point encoded measurements.
-/

import Std

namespace Semantics.MetasurfacePolarizationControl

/-- Domain marker. These equations are optics-domain only unless separately bridged. -/
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

/-- Polarization channel labels used for finite bookkeeping. -/
inductive Channel where
  | lambda1
  | lambda2
  | rcp
  | lcp
  | xLinear
  | yLinear
  deriving Repr, DecidableEq, Inhabited

/-- PB/geometric phase sign convention for a channel. -/
inductive PBSign where
  | positive
  | negative
  | suppressed
  deriving Repr, DecidableEq, Inhabited

/-- A target complex-amplitude channel, encoded discretely. -/
structure ChannelTarget where
  channel : Channel
  amplitudeQ : Nat
  phaseQ : Int
  domain : Domain
  claimState : ClaimState
  deriving Repr, DecidableEq, Inhabited

/-- Channel is bounded to the optics domain. -/
def OpticalChannel (c : ChannelTarget) : Prop :=
  c.domain = Domain.optics

/-- Amplitude is within a fixed-point encoded unit range. -/
def AmplitudeBounded (scale : Nat) (c : ChannelTarget) : Prop :=
  c.amplitudeQ ≤ scale

/-- Finite channel gate: optics-domain and amplitude bounded. -/
def ChannelGate (scale : Nat) (c : ChannelTarget) : Prop :=
  OpticalChannel c ∧ AmplitudeBounded scale c

/-- Passing a channel gate implies optics-domain status. -/
theorem channel_gate_optics
    (scale : Nat) (c : ChannelTarget)
    (h : ChannelGate scale c) :
    c.domain = Domain.optics := by
  exact h.left

/-- Passing a channel gate implies amplitude boundedness. -/
theorem channel_gate_amplitude_bounded
    (scale : Nat) (c : ChannelTarget)
    (h : ChannelGate scale c) :
    c.amplitudeQ ≤ scale := by
  exact h.right

/-- Double-phase encoded channel: E exp(i phi) represented by two phase-only branches. -/
structure DoublePhaseChannel where
  phaseCenterQ : Int
  phaseOffsetQ : Int
  phaseA : Int
  phaseB : Int
  deriving Repr, DecidableEq, Inhabited

/-- Build double-phase pair: A = center + offset, B = center - offset. -/
def mkDoublePhase (center offset : Int) : DoublePhaseChannel :=
  { phaseCenterQ := center
    phaseOffsetQ := offset
    phaseA := center + offset
    phaseB := center - offset }

/-- Double-phase consistency predicate. -/
def DoublePhaseConsistent (d : DoublePhaseChannel) : Prop :=
  d.phaseA = d.phaseCenterQ + d.phaseOffsetQ ∧
  d.phaseB = d.phaseCenterQ - d.phaseOffsetQ

/-- Any double-phase object built by mkDoublePhase is consistent. -/
theorem mkDoublePhase_consistent (center offset : Int) :
    DoublePhaseConsistent (mkDoublePhase center offset) := by
  unfold DoublePhaseConsistent mkDoublePhase
  simp

/-- Bilayer transform record: two local surfaces plus a propagation/coupling gap. -/
structure BilayerTransform where
  layer1Ready : Bool
  gapReady : Bool
  layer2Ready : Bool
  domain : Domain
  deriving Repr, DecidableEq, Inhabited

/-- Bilayer gate requires both layers and the gap to be declared ready. -/
def BilayerGate (b : BilayerTransform) : Prop :=
  b.domain = Domain.optics ∧ b.layer1Ready = true ∧ b.gapReady = true ∧ b.layer2Ready = true

/-- Passing the bilayer gate implies layer 1 is ready. -/
theorem bilayer_gate_layer1_ready
    (b : BilayerTransform)
    (h : BilayerGate b) :
    b.layer1Ready = true := by
  exact h.right.left

/-- Passing the bilayer gate implies layer 2 is ready. -/
theorem bilayer_gate_layer2_ready
    (b : BilayerTransform)
    (h : BilayerGate b) :
    b.layer2Ready = true := by
  exact h.right.right.right

/-- PB phase channel selection. -/
structure PBChannel where
  input : Channel
  output : Channel
  sign : PBSign
  rotationQ : Int
  phaseQ : Int
  deriving Repr, DecidableEq, Inhabited

/-- Simple fixed-point PB phase rule: phase = +/- 2 theta, or 0 if suppressed. -/
def mkPBChannel (input output : Channel) (sign : PBSign) (thetaQ : Int) : PBChannel :=
  let phase :=
    match sign with
    | .positive => 2 * thetaQ
    | .negative => -2 * thetaQ
    | .suppressed => 0
  { input := input, output := output, sign := sign, rotationQ := thetaQ, phaseQ := phase }

/-- PB phase consistency predicate. -/
def PBConsistent (p : PBChannel) : Prop :=
  match p.sign with
  | .positive => p.phaseQ = 2 * p.rotationQ
  | .negative => p.phaseQ = -2 * p.rotationQ
  | .suppressed => p.phaseQ = 0

/-- Any PB channel built by mkPBChannel is consistent. -/
theorem mkPBChannel_consistent
    (input output : Channel) (sign : PBSign) (thetaQ : Int) :
    PBConsistent (mkPBChannel input output sign thetaQ) := by
  unfold PBConsistent mkPBChannel
  cases sign <;> simp

/-- Integer representation of a 2x2 matrix for finite EP discriminant checks. -/
structure Matrix2 where
  a : Int
  b : Int
  c : Int
  d : Int
  deriving Repr, DecidableEq, Inhabited

/-- Trace of a 2x2 matrix. -/
def tr2 (m : Matrix2) : Int :=
  m.a + m.d

/-- Determinant of a 2x2 matrix. -/
def det2 (m : Matrix2) : Int :=
  m.a * m.d - m.b * m.c

/-- EP discriminant: D = tr(M)^2 - 4 det(M). -/
def epDiscriminant (m : Matrix2) : Int :=
  tr2 m * tr2 m - 4 * det2 m

/-- Eigenvalue degeneracy gate for a 2x2 matrix. -/
def EPDegenerate (m : Matrix2) : Prop :=
  epDiscriminant m = 0

/-- Non-scalar witness for a second-order EP candidate. -/
def NonScalarMatrix (m : Matrix2) : Prop :=
  m.b ≠ 0 ∨ m.c ≠ 0 ∨ m.a ≠ m.d

/-- Finite EP candidate gate: degenerate and non-scalar. -/
def EPCandidateGate (m : Matrix2) : Prop :=
  EPDegenerate m ∧ NonScalarMatrix m

/-- Passing the EP candidate gate implies zero discriminant. -/
theorem ep_gate_discriminant_zero
    (m : Matrix2)
    (h : EPCandidateGate m) :
    epDiscriminant m = 0 := by
  exact h.left

/-- Poincare hidden-singularity packet. -/
structure HiddenSingularityPacket where
  loopWinding : Int
  encircles : Bool
  coPolarized : Bool
  domain : Domain
  deriving Repr, DecidableEq, Inhabited

/-- Hidden singularity gate: optics domain, co-polarized channel, nonzero winding, encirclement. -/
def HiddenSingularityGate (p : HiddenSingularityPacket) : Prop :=
  p.domain = Domain.optics ∧ p.coPolarized = true ∧ p.encircles = true ∧ p.loopWinding ≠ 0

/-- Passing hidden-singularity gate implies nonzero winding. -/
theorem hidden_gate_nonzero_winding
    (p : HiddenSingularityPacket)
    (h : HiddenSingularityGate p) :
    p.loopWinding ≠ 0 := by
  exact h.right.right.right

/-- Nonlinear bilayer symmetry-breaking packet for THG bookkeeping. -/
structure NonlinearBilayerPacket where
  verticalBroken : Bool
  horizontalBroken : Bool
  gmrReady : Bool
  inputOmegaQ : Nat
  outputOmegaQ : Nat
  domain : Domain
  deriving Repr, DecidableEq, Inhabited

/-- Third-harmonic bookkeeping: output frequency is 3× input frequency. -/
def ThirdHarmonicRelation (p : NonlinearBilayerPacket) : Prop :=
  p.outputOmegaQ = 3 * p.inputOmegaQ

/-- Multiple broken symmetries require both vertical and horizontal broken-symmetry flags. -/
def MultipleBrokenSymmetry (p : NonlinearBilayerPacket) : Prop :=
  p.verticalBroken = true ∧ p.horizontalBroken = true

/-- Nonlinear bilayer gate: optics-domain, both symmetry breaks present, GMR declared, and THG relation holds. -/
def NonlinearBilayerGate (p : NonlinearBilayerPacket) : Prop :=
  p.domain = Domain.optics ∧
  MultipleBrokenSymmetry p ∧
  p.gmrReady = true ∧
  ThirdHarmonicRelation p

/-- Passing nonlinear bilayer gate implies optics-domain status. -/
theorem nonlinear_gate_optics
    (p : NonlinearBilayerPacket)
    (h : NonlinearBilayerGate p) :
    p.domain = Domain.optics := by
  exact h.left

/-- Passing nonlinear bilayer gate implies both symmetry breaks are present. -/
theorem nonlinear_gate_multiple_symmetry
    (p : NonlinearBilayerPacket)
    (h : NonlinearBilayerGate p) :
    MultipleBrokenSymmetry p := by
  exact h.right.left

/-- Passing nonlinear bilayer gate implies third-harmonic frequency relation. -/
theorem nonlinear_gate_third_harmonic
    (p : NonlinearBilayerPacket)
    (h : NonlinearBilayerGate p) :
    p.outputOmegaQ = 3 * p.inputOmegaQ := by
  exact h.right.right.right

/-- Example optical channel target. -/
def exampleChannel : ChannelTarget :=
  { channel := .lambda1
    amplitudeQ := 512
    phaseQ := 17
    domain := .optics
    claimState := .beautifulProvisional }

/-- Example bilayer transform. -/
def exampleBilayer : BilayerTransform :=
  { layer1Ready := true
    gapReady := true
    layer2Ready := true
    domain := .optics }

/-- Example EP Jordan-like matrix [[1,1],[0,1]]. -/
def exampleEPMatrix : Matrix2 :=
  { a := 1, b := 1, c := 0, d := 1 }

/-- Example hidden-singularity packet. -/
def exampleHidden : HiddenSingularityPacket :=
  { loopWinding := 1
    encircles := true
    coPolarized := true
    domain := .optics }

/-- Example nonlinear bilayer THG packet. -/
def exampleNonlinearBilayer : NonlinearBilayerPacket :=
  { verticalBroken := true
    horizontalBroken := true
    gmrReady := true
    inputOmegaQ := 11
    outputOmegaQ := 33
    domain := .optics }

/-- Example channel gate passes at Q10 scale. -/
theorem exampleChannel_gate : ChannelGate 1024 exampleChannel := by
  unfold ChannelGate OpticalChannel AmplitudeBounded exampleChannel
  constructor <;> decide

/-- Example bilayer passes the finite bilayer gate. -/
theorem exampleBilayer_gate : BilayerGate exampleBilayer := by
  unfold BilayerGate exampleBilayer
  decide

/-- Example EP matrix has zero discriminant. -/
theorem exampleEP_degenerate : EPDegenerate exampleEPMatrix := by
  unfold EPDegenerate epDiscriminant tr2 det2 exampleEPMatrix
  norm_num

/-- Example EP matrix passes the EP candidate gate. -/
theorem exampleEP_gate : EPCandidateGate exampleEPMatrix := by
  unfold EPCandidateGate
  constructor
  · exact exampleEP_degenerate
  · unfold NonScalarMatrix exampleEPMatrix
    left
    norm_num

/-- Example hidden-singularity packet passes the finite gate. -/
theorem exampleHidden_gate : HiddenSingularityGate exampleHidden := by
  unfold HiddenSingularityGate exampleHidden
  decide

/-- Example nonlinear bilayer packet passes the finite THG gate. -/
theorem exampleNonlinearBilayer_gate : NonlinearBilayerGate exampleNonlinearBilayer := by
  unfold NonlinearBilayerGate MultipleBrokenSymmetry ThirdHarmonicRelation exampleNonlinearBilayer
  decide

#eval mkDoublePhase 10 3
#eval mkPBChannel Channel.rcp Channel.lcp PBSign.positive 7
#eval epDiscriminant exampleEPMatrix
#eval epDiscriminant { a := 1, b := 0, c := 0, d := 2 }
#eval exampleNonlinearBilayer.outputOmegaQ

end Semantics.MetasurfacePolarizationControl
