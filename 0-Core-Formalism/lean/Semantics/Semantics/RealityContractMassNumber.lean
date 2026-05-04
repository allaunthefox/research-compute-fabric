/-
  Holy Diver / ENE
  Reality-Contract Mass-Number Forest

  A Lean 4 core-only module encoding the ontology-derived ruleset:
  - every domain is a reality-local field;
  - candidates are reduced only through certified domain-local reductions;
  - residuals are preserved, not erased;
  - mass numbers are admissible reduction divided by residual risk;
  - phi is normalized reducibility;
  - autodoc pressure decides whether the forest writes/updates documentation;
  - every candidate receives one finite decision.

  This file intentionally avoids Mathlib so it can be dropped into a plain
  Lean 4 project. The analytic/logarithmic phi-distance from the prose model
  is represented here by a rational cost surrogate:

      distanceCost = residual / (admissible + 1)

  which preserves the intended order: more admissible reduction lowers distance;
  more residual risk raises distance.
-/

namespace HolyDiver
namespace ENE

/-! ## Core enumerations -/

inductive DomainKind where
  | mathematics
  | physics
  | biology
  | computation
  | cognition
  | language
  | social
  | cryptography
  | engineering
  | unknown
  deriving Repr, DecidableEq

inductive ComparisonLevel where
  | substrate
  | operator
  | transition
  | observable
  | contract
  | truth
  deriving Repr, DecidableEq

inductive MassKind where
  | anchor
  | transport
  | symmetry
  | topology
  | dimension
  | cognitiveLoad
  | phaseCoherence
  | proteinTemplate
  | categoryErrorCorrection
  | criticalLineAnchor
  | rationalPointRank
  | arithmeticAnalyticBridge
  | radiantTransportMomentum
  | eigenmodeTransport
  | physicsNumerologyRisk
  | other
  deriving Repr, DecidableEq

inductive ResidualKind where
  | unresolved
  | contradiction
  | missingVariable
  | frameMismatch
  | observableGap
  | implementationGap
  | categoryError
  | highCognitiveLoad
  | shoreMirage
  | domainDrift
  | oracleBoundary
  deriving Repr, DecidableEq

inductive Decision where
  | promote
  | edgeSurvivor
  | quarantine
  | banReduce
  deriving Repr, DecidableEq

inductive DocAction where
  | createNew
  | updateExisting
  | edgeSurvivorNote
  | ignore
  deriving Repr, DecidableEq

/-! ## Reality contracts -/

/--
A domain is not merely a topic. It is a reality-local field with its own
contract for what counts as a state, operation, observation, invariant,
failure, boundary, and handoff target.
-/
structure RealityContract where
  domain          : DomainKind
  substrate       : String
  validStates     : List String
  validOperators  : List String
  observables     : List String
  invariants      : List String
  failureModes    : List String
  boundaries      : List String
  handoffTargets  : List DomainKind
  deriving Repr

/-- A candidate being evaluated by the forest. -/
structure Candidate where
  name        : String
  claim       : String
  domains     : List DomainKind
  massKinds   : List MassKind
  truthStatus : String
  deriving Repr

/-- A reference frame names the local context in which reductions are evaluated. -/
structure ReferenceFrame where
  name        : String
  description : String
  deriving Repr

/-! ## Certified reductions -/

/--
A raw domain-local reduction contribution.

All quantities are natural-number weights. This keeps the core executable
without importing rationals/reals. Think of each value as a nonnegative score
from a calibrated registry.
-/
structure DomainReduction where
  fieldName             : String
  weight                : Nat
  reductionStrength     : Nat
  contractCompatibility : Nat
  activation            : Nat
  deriving Repr

/-- The contribution of a reduction to admissible mass. -/
def DomainReduction.term (r : DomainReduction) : Nat :=
  r.weight * r.reductionStrength * r.contractCompatibility * r.activation

/--
Certified reductions are proof-carrying: they cannot enter mass-number scoring
unless compatibility and activation are strictly positive.
-/
structure CertifiedReduction where
  raw        : DomainReduction
  compat_ok  : raw.contractCompatibility > 0
  active_ok  : raw.activation > 0
  deriving Repr

/-- The certified contribution to admissible mass. -/
def CertifiedReduction.term (r : CertifiedReduction) : Nat :=
  r.raw.term

/-! ## Residual risk -/

/--
Residual risk is the denominator pressure: near-miss tension, shore mirage,
load, violation, oracle boundary, and domain drift.
-/
structure ResidualRisk where
  tension      : Nat
  shoreMirage  : Nat
  load         : Nat
  violation    : Nat
  oracle       : Nat
  drift        : Nat
  deriving Repr

/-- Denominator contribution: always at least 1. -/
def ResidualRisk.denominator (r : ResidualRisk) : Nat :=
  1 + r.tension + r.shoreMirage + r.load + r.violation + r.oracle + r.drift

/-- Residual amount excluding the stabilizing `1`. -/
def ResidualRisk.amount (r : ResidualRisk) : Nat :=
  r.tension + r.shoreMirage + r.load + r.violation + r.oracle + r.drift

/-! ## Rational-like nonnegative scores -/

/--
A nonnegative rational-like score `num / den` with proof that the denominator
is nonzero. This avoids importing rational numbers while preserving the
structure of the equations.
-/
structure Score where
  num    : Nat
  den    : Nat
  den_ne : den ≠ 0
  deriving Repr

/-- A safe constructor for scores with denominator `n + 1`. -/
def Score.ofNatOverSucc (num denMinusOne : Nat) : Score :=
  { num := num, den := denMinusOne + 1, den_ne := by simp }

/-- Natural-number cross-multiplication comparison. -/
def Score.ge (a b : Score) : Prop :=
  a.num * b.den ≥ b.num * a.den

/-- Natural-number cross-multiplication strict comparison. -/
def Score.gt (a b : Score) : Prop :=
  a.num * b.den > b.num * a.den

/-! ## Mass number, phi, distance, and autodoc equations -/

/-- Sum a list of natural numbers. -/
def sumNat (xs : List Nat) : Nat :=
  xs.foldl (fun acc x => acc + x) 0

/-- Total admissible reduction from certified reductions. -/
def admissibleReduction (rs : List CertifiedReduction) : Nat :=
  sumNat (rs.map CertifiedReduction.term)

/--
Master mass-number equation, executable core form:

  M_D,R(x) = admissible / (1 + residual risk)
-/
def massNumber (rs : List CertifiedReduction) (risk : ResidualRisk) : Score :=
  { num := admissibleReduction rs,
    den := risk.denominator,
    den_ne := by
      unfold ResidualRisk.denominator
      simp }

/--
Mass-number phi: normalized reducibility.

  phi = admissible / (admissible + residual)

When both admissible and residual are zero, the denominator is stabilized to 1.
-/
def massPhi (rs : List CertifiedReduction) (risk : ResidualRisk) : Score :=
  let a := admissibleReduction rs
  let u := risk.amount
  if h : a + u = 0 then
    { num := 0, den := 1, den_ne := by simp }
  else
    { num := a, den := a + u, den_ne := h }

/--
A Lean-core surrogate for phi distance.

The prose equation used `-log(phi + epsilon)`. Here we encode the same order
as an admissibility cost:

  d_phi_cost = residual / (admissible + 1)
-/
def phiDistanceCost (rs : List CertifiedReduction) (risk : ResidualRisk) : Score :=
  { num := risk.amount,
    den := admissibleReduction rs + 1,
    den_ne := by simp }

/-- Additional factors controlling documentation pressure. -/
structure AutodocFactors where
  novelty        : Nat
  compression    : Nat
  handoffValue   : Nat
  unresolved     : Nat
  deriving Repr

/--
Autodoc pressure:

  A_doc = M * novelty * compression * handoff / (1 + unresolved + drift + load + violation)

Because `M` is itself a score, we multiply its numerator and extend its denominator.
-/
def autodocPressure
    (rs : List CertifiedReduction)
    (risk : ResidualRisk)
    (f : AutodocFactors) : Score :=
  let m := massNumber rs risk
  { num := m.num * f.novelty * f.compression * f.handoffValue,
    den := m.den * (1 + f.unresolved + risk.drift + risk.load + risk.violation),
    den_ne := by
      apply Nat.mul_ne_zero
      · exact m.den_ne
      · simp }

/-! ## Candidate records and forest nodes -/

structure TypedResidual where
  kind        : ResidualKind
  description : String
  handoffTo   : List DomainKind
  deriving Repr

structure NativeReductionRecord where
  domain     : DomainKind
  reduction  : CertifiedReduction
  note       : String
  deriving Repr

/--
A full candidate record: this is the object the forest can score, route,
document, promote, quarantine, or preserve as an edge survivor.
-/
structure CandidateRecord where
  candidate            : Candidate
  frame                : ReferenceFrame
  comparisonLevel      : ComparisonLevel
  contracts            : List RealityContract
  nativeReductions     : List NativeReductionRecord
  residuals            : List TypedResidual
  risk                 : ResidualRisk
  observableProjection : String
  formalProjection     : String
  failureModes         : List String
  deriving Repr

/-- Pull certified reductions out of a full record. -/
def CandidateRecord.reductions (r : CandidateRecord) : List CertifiedReduction :=
  r.nativeReductions.map (fun nr => nr.reduction)

/-- Mass number of a full record. -/
def CandidateRecord.mass (r : CandidateRecord) : Score :=
  massNumber r.reductions r.risk

/-- Phi of a full record. -/
def CandidateRecord.phi (r : CandidateRecord) : Score :=
  massPhi r.reductions r.risk

/-- Distance-cost of a full record. -/
def CandidateRecord.distance (r : CandidateRecord) : Score :=
  phiDistanceCost r.reductions r.risk

/-- Autodoc pressure of a full record. -/
def CandidateRecord.autodoc (r : CandidateRecord) (f : AutodocFactors) : Score :=
  autodocPressure r.reductions r.risk f

/-! ## Decisions -/

/-- Threshold bundle for promotion and documentation. -/
structure Thresholds where
  promoteMass      : Score
  edgeMass         : Score
  maxRiskForPromote : Nat
  docNew           : Score
  docUpdate        : Score
  nearestMerge     : Score
  deriving Repr

/-- High residual means preserve as edge survivor unless promotion is justified. -/
def highResidual (r : CandidateRecord) : Prop :=
  r.risk.amount > 0 ∧ r.residuals ≠ []

/-- A lightweight executable risk gate. -/
def riskLowEnough (r : CandidateRecord) (θ : Thresholds) : Prop :=
  r.risk.amount ≤ θ.maxRiskForPromote

/-- Prop-level promotion eligibility. -/
def canPromote (r : CandidateRecord) (θ : Thresholds) : Prop :=
  Score.ge r.mass θ.promoteMass ∧ riskLowEnough r θ ∧ r.observableProjection ≠ ""

/-- Prop-level edge-survivor eligibility. -/
def shouldBeEdgeSurvivor (r : CandidateRecord) (θ : Thresholds) : Prop :=
  Score.ge r.mass θ.edgeMass ∧ highResidual r

/--
Decidable implementation of the finite decision corridor.

This takes Boolean gates as parameters so the caller can plug in proof-producing
or runtime-produced tests. The ontology requires one of four outcomes only.
-/
def decideCandidate
    (promoteGate edgeGate quarantineGate : Bool) : Decision :=
  if promoteGate then
    Decision.promote
  else if edgeGate then
    Decision.edgeSurvivor
  else if quarantineGate then
    Decision.quarantine
  else
    Decision.banReduce

/-- The decision corridor is finite by construction. -/
theorem decision_is_finite (p e q : Bool) :
    decideCandidate p e q = Decision.promote ∨
    decideCandidate p e q = Decision.edgeSurvivor ∨
    decideCandidate p e q = Decision.quarantine ∨
    decideCandidate p e q = Decision.banReduce := by
  unfold decideCandidate
  by_cases hp : p <;> simp [hp]
  by_cases he : e <;> simp [he]

/--
Autodoc action. `nearest` is the nearest-page overlap score.
The comparison gates are deliberately passed as Booleans to let a runtime or
proof layer decide thresholds.
-/
def decideDocAction
    (newGate updateGate nearestMergeGate massNonzero residualHigh : Bool) : DocAction :=
  if newGate && not nearestMergeGate then
    DocAction.createNew
  else if updateGate && nearestMergeGate then
    DocAction.updateExisting
  else if massNonzero && residualHigh then
    DocAction.edgeSurvivorNote
  else
    DocAction.ignore

/-! ## Ontology rules as checkable predicates -/

/-- Rule: analogy never promotes alone. A promoted cross-domain candidate needs at least one projection. -/
def hasProjection (r : CandidateRecord) : Prop :=
  r.observableProjection ≠ "" ∨ r.formalProjection ≠ ""

/-- Rule: residuals must remain typed. In this encoding, any residual object is typed by construction. -/
theorem residuals_typed_by_construction (r : CandidateRecord) :
    ∀ res ∈ r.residuals, ∃ k : ResidualKind, res.kind = k := by
  intro res h
  exact ⟨res.kind, rfl⟩

/-- Rule: every native reduction is certified by construction. -/
theorem native_reductions_certified (r : CandidateRecord) :
    ∀ nr ∈ r.nativeReductions,
      nr.reduction.raw.contractCompatibility > 0 ∧ nr.reduction.raw.activation > 0 := by
  intro nr h
  exact ⟨nr.reduction.compat_ok, nr.reduction.active_ok⟩

/-- Rule: mass denominator is always nonzero. -/
theorem mass_denominator_nonzero (r : CandidateRecord) : r.mass.den ≠ 0 := by
  exact r.mass.den_ne

/-- Rule: distance denominator is always nonzero. -/
theorem distance_denominator_nonzero (r : CandidateRecord) : r.distance.den ≠ 0 := by
  exact r.distance.den_ne

/-! ## Example canonical records -/

/-- A tiny helper reduction with compatibility and activation both equal to 1. -/
def certifiedUnitReduction (name : String) (w strength : Nat) : CertifiedReduction :=
  { raw :=
      { fieldName := name,
        weight := w,
        reductionStrength := strength,
        contractCompatibility := 1,
        activation := 1 },
    compat_ok := by simp,
    active_ok := by simp }

/-- Mathematics contract used for examples. -/
def mathContract : RealityContract :=
  { domain := DomainKind.mathematics,
    substrate := "formal objects, axioms, proofs, models",
    validStates := ["definition", "theorem", "construction", "counterexample"],
    validOperators := ["proof", "equivalence", "model construction", "refutation"],
    observables := ["formal derivation", "checked proof", "countermodel"],
    invariants := ["logical consistency relative to axioms"],
    failureModes := ["analogy mistaken for theorem"],
    boundaries := ["unproved conjecture", "axiom dependence"],
    handoffTargets := [DomainKind.computation, DomainKind.physics] }

/-- Biology contract used for examples. -/
def biologyContract : RealityContract :=
  { domain := DomainKind.biology,
    substrate := "living systems, cells, enzymes, evolution, biochemical mechanisms",
    validStates := ["molecule", "pathway", "phenotype", "assay state"],
    validOperators := ["mechanistic assay", "structural determination", "fitness test"],
    observables := ["phenotype", "structure", "activity", "growth effect"],
    invariants := ["biochemical compatibility", "evolutionary viability"],
    failureModes := ["molecular possibility mistaken for engineering control"],
    boundaries := ["unknown generalizability", "unmeasured toxicity"],
    handoffTargets := [DomainKind.computation, DomainKind.engineering] }

/-- Example: imaginary numbers as a promoted category-error rescue object. -/
def imaginaryNumbersRecord : CandidateRecord :=
  { candidate :=
      { name := "Imaginary numbers",
        claim := "Real-line impossibility becomes stable phase rotation in the complex plane.",
        domains := [DomainKind.mathematics, DomainKind.cognition],
        massKinds := [MassKind.dimension, MassKind.categoryErrorCorrection],
        truthStatus := "established mathematics" },
    frame := { name := "complex-plane frame", description := "state-space expansion from line to plane" },
    comparisonLevel := ComparisonLevel.contract,
    contracts := [mathContract],
    nativeReductions := [
      { domain := DomainKind.mathematics,
        reduction := certifiedUnitReduction "algebraic closure / phase rotation" 5 5,
        note := "sqrt(-1) fails on the real line but stabilizes in the complex plane." }
    ],
    residuals := [],
    risk := { tension := 0, shoreMirage := 0, load := 1, violation := 0, oracle := 0, drift := 0 },
    observableProjection := "rotations, magnitudes, phase, signal and quantum projections",
    formalProjection := "complex number construction",
    failureModes := ["treating imaginary component as directly physical without projection"] }

/-- Example: DRT3 as protein-template category breaker. -/
def drt3Record : CandidateRecord :=
  { candidate :=
      { name := "DRT3 defense system",
        claim := "Protein active-site geometry can enforce sequence-specific DNA synthesis.",
        domains := [DomainKind.biology, DomainKind.computation],
        massKinds := [MassKind.proteinTemplate, MassKind.categoryErrorCorrection],
        truthStatus := "reported experimental biochemistry" },
    frame := { name := "bacterial anti-phage defense", description := "sequence specificity through constraint geometry" },
    comparisonLevel := ComparisonLevel.operator,
    contracts := [biologyContract],
    nativeReductions := [
      { domain := DomainKind.biology,
        reduction := certifiedUnitReduction "protein-template sequence constraint" 5 4,
        note := "The active site acts as a structural template rather than a nucleic-acid template." }
    ],
    residuals := [
      { kind := ResidualKind.observableGap,
        description := "Engineering generality, error rate, substrate range, and toxicity remain unresolved.",
        handoffTo := [DomainKind.engineering, DomainKind.computation] }
    ],
    risk := { tension := 1, shoreMirage := 0, load := 2, violation := 0, oracle := 0, drift := 1 },
    observableProjection := "alternating DNA product and anti-phage phenotype",
    formalProjection := "protein-template mass record",
    failureModes := ["assuming arbitrary programmable DNA writing from one mechanism"] }

/-! ## Forest registry -/

/-- The first seed forest. -/
def seedForest : List CandidateRecord :=
  [imaginaryNumbersRecord, drt3Record]

/-- A compact export row for external tools. -/
structure ForestRow where
  name       : String
  massNum    : Nat
  massDen    : Nat
  phiNum     : Nat
  phiDen     : Nat
  distNum    : Nat
  distDen    : Nat
  deriving Repr

/-- Convert a candidate record into a numeric export row. -/
def CandidateRecord.toRow (r : CandidateRecord) : ForestRow :=
  { name := r.candidate.name,
    massNum := r.mass.num,
    massDen := r.mass.den,
    phiNum := r.phi.num,
    phiDen := r.phi.den,
    distNum := r.distance.num,
    distDen := r.distance.den }

/-- Export the seed forest as rows. -/
def seedForestRows : List ForestRow :=
  seedForest.map CandidateRecord.toRow

end ENE
end HolyDiver
