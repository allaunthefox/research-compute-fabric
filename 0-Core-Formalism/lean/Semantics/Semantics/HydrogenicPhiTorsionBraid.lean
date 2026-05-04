import Semantics.Bind

namespace Semantics.HydrogenicPhiTorsionBraid

open Semantics
open Semantics.Q16_16

/-!
Fixed-point hard-math gate for the hydrogenic Phi-torsion braid.

The browser/Python braid emits a generation trace. This Lean module owns the
routing decision: hard mathematical states are reduced to finite event-cell
fields, then compared against a braid sample. The module does not claim to
solve Millennium-level problems. It classifies whether a state is admissible
enough to promote, should remain residue, should be quarantined, or should be
routed away from CFD-style continuum pressure.
-/

/-- Q0.16 raw maximum. -/
def q0Max : Nat := 65535

/-- Q0.16 raw half threshold. -/
def q0Half : Nat := 32768

/-- Saturate a natural number into Q0.16 raw range. -/
def satQ0 (n : Nat) : Nat :=
  if n > q0Max then q0Max else n

/-- Saturating Q0.16 addition over raw natural values. -/
def addQ0 (a b : Nat) : Nat :=
  satQ0 (a + b)

/-- Average two Q0.16 raw values. -/
def avgQ0 (a b : Nat) : Nat :=
  (satQ0 a + satQ0 b) / 2

/-- Hard-math classes this gate is allowed to classify. -/
inductive HardMathKind where
  | yangMillsMassGap
  | riemannCriticalLine
  | navierStokesRegularity
  | pVsNp
  | hodgeCycle
  | birchSwinnertonDyer
  deriving Repr, DecidableEq

/-- Finite decision surface for the braid sieve. -/
inductive GateDecision where
  | stableSignal
  | residue
  | quarantine
  | noCfdRoute
  deriving Repr, DecidableEq

/-- Fractionalized core terms of the braid equation. -/
inductive EquationPart where
  | fibonacciSpine
  | orbitalGroove
  | planarSpine
  | phiTorsion
  | stairLift
  | strainField
  | emissionPacket
  | colorRope
  deriving Repr, DecidableEq

/-- Tensegrity relation: pull or push between equation parts. -/
inductive EdgeMode where
  | tension
  | compression
  deriving Repr, DecidableEq

/-- A finite tensegrity edge between fractionalized equation parts. -/
structure TensegrityEdge where
  source : EquationPart
  target : EquationPart
  mode : EdgeMode
  restLength : Nat
  deriving Repr, DecidableEq

/--
A problem state reduced into hardware-friendly Q0.16 pressures.

All fields are raw Q0.16 values. Higher `admissibleMass`, `latticePressure`,
and `evidenceMass` help promotion. Higher `residualRisk`, `proofDebt`, and
`continuumPressure` oppose promotion.
-/
structure HardProblemState where
  kind : HardMathKind
  admissibleMass : Nat
  residualRisk : Nat
  proofDebt : Nat
  continuumPressure : Nat
  latticePressure : Nat
  evidenceMass : Nat
  noCfdAllowed : Bool
  deriving Repr, DecidableEq

/--
A single generated braid sample, already quantized by the Python/browser trace.
-/
structure BraidSample where
  constraint : Nat
  strain : Nat
  emittedAmplitude : Nat
  phase : Nat
  stairIndex : Nat
  deriving Repr, DecidableEq

/-- Nominal sample from the generated 2s/radial=5/angular=3 trace. -/
def nominalBraidSample : BraidSample :=
  { constraint := 58161
    strain := 40788
    emittedAmplitude := 117485
    phase := 6557
    stairIndex := 0 }

/--
Minimal CMYK rope for hard-math routing.

Channel meaning:
- C: monitor/constraint groove from the orbital sample.
- M: verify/evidence mass carried by the problem state.
- Y: prune/residual pressure; high Y means fray.
- K: action/admissible mass available for promotion.
-/
structure ColorRope where
  c : Nat
  m : Nat
  y : Nat
  k : Nat
  deriving Repr, DecidableEq

/-- The braid's local fracture pressure. -/
def BraidSample.fracturePressure (s : BraidSample) : Nat :=
  avgQ0 s.strain s.emittedAmplitude

/-- The evidence floor imposed by a sample's orbital groove. -/
def BraidSample.evidenceFloor (s : BraidSample) : Nat :=
  avgQ0 s.constraint q0Half

/-- Residual pressure opposing promotion. -/
def residualPressure (p : HardProblemState) : Nat :=
  avgQ0 (addQ0 p.residualRisk p.proofDebt) p.continuumPressure

/-- Promotion pressure supporting a stable signal. -/
def promotionPressure (p : HardProblemState) (s : BraidSample) : Nat :=
  avgQ0 (addQ0 p.admissibleMass p.evidenceMass) (BraidSample.evidenceFloor s)

/-- Build the color rope from one hard-math state and one braid sample. -/
def colorRope (p : HardProblemState) (s : BraidSample) : ColorRope :=
  { c := satQ0 s.constraint
    m := satQ0 p.evidenceMass
    y := avgQ0 p.residualRisk p.proofDebt
    k := avgQ0 p.admissibleMass p.latticePressure }

/-- Rope coherence: monitor+verify+action must dominate prune pressure. -/
def ColorRope.coherent (r : ColorRope) : Bool :=
  avgQ0 (addQ0 r.c r.m) r.k ≥ r.y

/-- Rope fray pressure. High Y over weak C/M/K means the state stays residue. -/
def ColorRope.frayed (r : ColorRope) : Bool :=
  r.y > avgQ0 r.c (avgQ0 r.m r.k)

/-- Natural absolute difference. -/
def natAbsDiff (a b : Nat) : Nat :=
  if a ≥ b then a - b else b - a

/-- The load carried by one fractionalized equation part. -/
def partLoad (p : HardProblemState) (s : BraidSample) (part : EquationPart) : Nat :=
  let rope := colorRope p s
  match part with
  | EquationPart.fibonacciSpine => avgQ0 p.latticePressure s.phase
  | EquationPart.orbitalGroove => satQ0 s.constraint
  | EquationPart.planarSpine => avgQ0 p.admissibleMass s.constraint
  | EquationPart.phiTorsion => avgQ0 s.phase s.strain
  | EquationPart.stairLift => satQ0 (s.stairIndex * 1024)
  | EquationPart.strainField => satQ0 s.strain
  | EquationPart.emissionPacket => satQ0 s.emittedAmplitude
  | EquationPart.colorRope => avgQ0 (addQ0 rope.c rope.m) (addQ0 rope.y rope.k)

/-- Edge strain after the two connected loads pull or push from rest length. -/
def edgeStrain (p : HardProblemState) (s : BraidSample) (e : TensegrityEdge) : Nat :=
  let a := partLoad p s e.source
  let b := partLoad p s e.target
  match e.mode with
  | EdgeMode.tension => natAbsDiff (natAbsDiff a b) e.restLength
  | EdgeMode.compression => natAbsDiff (avgQ0 a b) e.restLength

/-- Default tensegrity skeleton for the hydrogenic Phi-torsion equation. -/
def defaultTensegrity : List TensegrityEdge :=
  [ { source := EquationPart.fibonacciSpine, target := EquationPart.orbitalGroove,
      mode := EdgeMode.tension, restLength := 24000 },
    { source := EquationPart.orbitalGroove, target := EquationPart.phiTorsion,
      mode := EdgeMode.compression, restLength := 32000 },
    { source := EquationPart.phiTorsion, target := EquationPart.stairLift,
      mode := EdgeMode.tension, restLength := 18000 },
    { source := EquationPart.stairLift, target := EquationPart.strainField,
      mode := EdgeMode.tension, restLength := 22000 },
    { source := EquationPart.strainField, target := EquationPart.emissionPacket,
      mode := EdgeMode.compression, restLength := 30000 },
    { source := EquationPart.emissionPacket, target := EquationPart.colorRope,
      mode := EdgeMode.tension, restLength := 26000 } ]

/-- Total tensegrity strain over the fractionalized equation skeleton. -/
def totalTensegrityStrain
    (p : HardProblemState) (s : BraidSample) (edges : List TensegrityEdge) : Nat :=
  edges.foldl (fun acc edge => addQ0 acc (edgeStrain p s edge)) 0

/-- Tensegrity remains coherent while total strain stays below the prune floor. -/
def tensegrityCoherent (p : HardProblemState) (s : BraidSample) : Bool :=
  totalTensegrityStrain p s defaultTensegrity ≤
    avgQ0 (satQ0 p.residualRisk) q0Max

/-- Navier-Stokes and high-continuum states may be routed away from CFD. -/
def shouldRouteNoCfd (p : HardProblemState) : Bool :=
  p.noCfdAllowed &&
    (p.kind == HardMathKind.navierStokesRegularity ||
      p.continuumPressure > p.latticePressure)

/-- Core hard-math gate decision. -/
def decideGate (p : HardProblemState) (s : BraidSample) : GateDecision :=
  let rope := colorRope p s
  if shouldRouteNoCfd p then
    GateDecision.noCfdRoute
  else if s.constraint = 0 then
    GateDecision.quarantine
  else if ColorRope.coherent rope && tensegrityCoherent p s &&
      promotionPressure p s ≥ residualPressure p &&
      p.evidenceMass ≥ BraidSample.evidenceFloor s &&
      p.admissibleMass ≥ BraidSample.fracturePressure s then
    GateDecision.stableSignal
  else if p.evidenceMass > 0 || ColorRope.frayed rope then
    GateDecision.residue
  else
    GateDecision.quarantine

/-- Q16.16 cost used by `bind`: residual pressure plus fracture pressure. -/
def gateCost (p : HardProblemState) (s : BraidSample) (_metric : Metric) : Q16_16 :=
  Q16_16.satFromNat ((residualPressure p + BraidSample.fracturePressure s) * scale)

/-- Finite invariant extractor. The strings are boundary labels only. -/
def problemInvariant (p : HardProblemState) : String :=
  match decideGate p nominalBraidSample with
  | GateDecision.stableSignal => "stable_signal"
  | GateDecision.residue => "residue"
  | GateDecision.quarantine => "quarantine"
  | GateDecision.noCfdRoute => "no_cfd_route"

/-- Sample invariant extractor. -/
def sampleInvariant (s : BraidSample) : String :=
  if s.constraint = 0 then "quarantine" else "stable_signal"

/-- Bind wrapper for the hard-math gate. -/
def braidBind (p : HardProblemState) (s : BraidSample) : Bind HardProblemState BraidSample :=
  geometricBind p s Metric.euclidean gateCost problemInvariant sampleInvariant

/-- A corrected Yang-Mills toy-lattice state: useful only as bounded sandbox. -/
def yangMillsToyState : HardProblemState :=
  { kind := HardMathKind.yangMillsMassGap
    admissibleMass := 42000
    residualRisk := 36000
    proofDebt := 44000
    continuumPressure := 41000
    latticePressure := 52000
    evidenceMass := 35000
    noCfdAllowed := true }

/-- Navier-Stokes pressure is explicitly routed away from CFD. -/
def navierNoCfdState : HardProblemState :=
  { kind := HardMathKind.navierStokesRegularity
    admissibleMass := 28000
    residualRisk := 50000
    proofDebt := 52000
    continuumPressure := 61000
    latticePressure := 26000
    evidenceMass := 18000
    noCfdAllowed := true }

/-- A strong but still local Riemann-line sieve state. -/
def riemannResidueState : HardProblemState :=
  { kind := HardMathKind.riemannCriticalLine
    admissibleMass := 39000
    residualRisk := 33000
    proofDebt := 38000
    continuumPressure := 22000
    latticePressure := 47000
    evidenceMass := 36000
    noCfdAllowed := false }

#eval decideGate yangMillsToyState nominalBraidSample
-- Expected: residue

#eval decideGate navierNoCfdState nominalBraidSample
-- Expected: noCfdRoute

#eval decideGate riemannResidueState nominalBraidSample
-- Expected: residue

#eval (gateCost navierNoCfdState nominalBraidSample Metric.euclidean).val.toNat > 0
-- Expected: true

#eval colorRope yangMillsToyState nominalBraidSample
-- Expected: CMYK-style rope channels for monitor/evidence/prune/action.

/-- No-CFD states route away from continuum simulation before other checks. -/
theorem navierNoCfdRoutes :
    decideGate navierNoCfdState nominalBraidSample = GateDecision.noCfdRoute := by
  native_decide

/-- Zero orbital constraint quarantines non-CFD states. -/
theorem zeroConstraintQuarantinesYangMills :
    decideGate yangMillsToyState { nominalBraidSample with constraint := 0 } =
      GateDecision.quarantine := by
  native_decide

/-- Gate cost is positive for the nominal Navier state. -/
theorem navierGateCostPositive :
    (gateCost navierNoCfdState nominalBraidSample Metric.euclidean).val.toNat > 0 := by
  native_decide

/-- Yang-Mills toy state remains residue under the rope/tensegrity gate. -/
theorem yangMillsToyRemainsResidue :
    decideGate yangMillsToyState nominalBraidSample = GateDecision.residue := by
  native_decide

/-- The default tensegrity skeleton has six load-bearing edges. -/
theorem defaultTensegrityHasSixEdges :
    defaultTensegrity.length = 6 := by
  native_decide

end Semantics.HydrogenicPhiTorsionBraid
