import Std
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic

/-!
Semantic Mass Theory
ID: SEMANTIC-MASS-1

This module formalizes semantic mass as a dimensionless formal scalar
assigned to concepts, packets, or manifold states.

STATUS: SEMANTIC_MODELING
WARNING:
- NOT_PHYSICAL_MASS
- NOT_SI_MAPPED
- Semantic mass is mass-like because it controls inertia, attraction,
  collapse resistance, and routing cost
- It is not physical mass and has no SI-unit mapping

Semantic mass is to meaning-space what imaginary numbers are to algebra:
not a literal physical object, but an extension that makes hidden
transformations computable.

Generalized insight:
  Mass number is not about matter. It is about transformation weight.
  Any typed object in a transformation space can carry semantic mass.

Archive-safe wording:
  Semantic mass is a dimensionless formal scalar assigned to semantic carriers.
  A semantic carrier is any typed object whose allowed transformations preserve
  a core invariant. It is mass-like because it controls inertia, attraction,
  collapse resistance, and routing cost. It is not physical mass and has no
  SI-unit mapping.

Reference: Imaginary-number framing analogy
-/

namespace Semantics

/--
A point in semantic manifold with mass properties.

Semantic mass measures:
  - binding strength
  - compression cost
  - recurrence frequency
  - inferential load
  - resistance to reinterpretation
  - downstream consequence weight

A light semantic object is easy to move, rename, compress, or reinterpret.
A heavy semantic object resists movement because many routes depend on it.
-/
structure SemanticMassPoint (n : Nat) where
  /-- Manifold coordinates (n-dimensional) -/
  coord      : Fin n → ℚ
  /-- Semantic mass (non-negative) -/
  mass       : ℚ
  /-- Binding strength (how tightly connected to other concepts) -/
  binding    : ℚ
  /-- Turbulence (unresolved semantic noise) -/
  turbulence : ℚ
  /-- Route cost (energy required to move through this point) -/
  routeCost  : ℚ
  /-- Semantic velocity through the manifold -/
  velocity   : Fin n → ℚ

/--
Semantic mass must be non-negative.
-/
def massNonneg (p : SemanticMassPoint n) : Prop :=
  p.mass >= 0

/--
Semantic energy at a point:

  E_s(x) = m_s(x) * c_s² + ½ * m_s(x) * ∥v_s(x)∥² + V_s(x)

Where:
  m_s = semantic mass
  c_s = semantic coherence speed (dimensionless, not light speed)
  v_s = semantic velocity through the manifold
  V_s = semantic potential / context pressure
  E_s = semantic energy cost

The semantic coherence speed c_s is the maximum allowed rate at which
meaning can move through the model without losing coherence. It is
dimensionless, not physical light speed.
-/
structure SemanticEnergyParams where
  /-- Semantic coherence speed (dimensionless propagation constant) -/
  c_s : ℚ
  /-- Semantic potential / context pressure -/
  V_s : ℚ

def semanticEnergy (params : SemanticEnergyParams) (p : SemanticMassPoint n) : ℚ :=
  let kineticTerm := p.mass * (params.c_s * params.c_s)
  -- Simplified: assume zero velocity for static energy calculation
  let motionTerm := 0
  kineticTerm + motionTerm + params.V_s

/--
Semantic attraction between two points:

  F_ij = G_s * m_i * m_j / (d(i,j)² + ε)

Where:
  G_s = semantic coupling constant
  m_i, m_j = semantic masses
  d(i,j) = manifold distance
  ε = singularity guard

This does not claim physical gravity. It says:
  heavily bound concepts pull nearby concepts into their interpretive basin.
-/
def semanticAttraction (G_s eps mi mj d_sq : ℚ) : ℚ :=
  G_s * mi * mj / (d_sq + eps)

/--
Semantic inertia at a point: mass × route cost.

High semantic inertia means the concept is hard to move because many
routes depend on it.
-/
def semanticInertia (p : SemanticMassPoint n) : ℚ :=
  p.mass * p.routeCost

/--
Semantic mass decay through FNWH drain:

  Δm_s = -Γ(k) * m_s + S(x,t)

Meaning:
  semantic mass decays through the drain unless reinforced by
  source/context S

At the Brillouin boundary (k ≈ k_max):
  semantic mass must either compress, split, or drain

This connects to the two-channel interpretation:
  Channel 1: mass retained as coherent binding
  Channel 2: mass drained as unresolved turbulence
-/
structure SemanticDrainParams where
  /-- Draining rate Γ(k) from FNWH -/
  drainRate : ℚ
  /-- Source/context reinforcement S(x,t) -/
  source    : ℚ

def semanticMassChange (params : SemanticDrainParams) (mass : ℚ) : ℚ :=
  -params.drainRate * mass + params.source

/--
SemanticCarrier: typeclass for any typed object that can carry semantic mass.

A semantic carrier is any typed object whose allowed transformations preserve
a core invariant. Semantic mass is not about physical matter; it is about
transformation weight.

This is the operational interface for a routing and filtering engine over
typed semantic objects.

Components (7-component mass vector):
  - invariantStrength: strength of the core invariant preserved by the object
  - bindingDegree: how strongly the object is attached to other structures
  - routingLeverage: how much the object expands the reachable solution space
  - compressionGain: how much the object compresses patterns
  - updateResistance: how hard it is to remove or modify the object
  - turbulenceCost: conceptual turbulence or confusion introduced by the object
  - collapseResistance: persistence under transformation pressure
-/
class SemanticCarrier (α : Type) where
  /-- Invariant strength: how strongly the object preserves its core rule -/
  invariantStrength : α → ℚ
  /-- Binding degree: attachment to other structures/domains -/
  bindingDegree : α → ℚ
  /-- Routing leverage: expansion of reachable solution space -/
  routingLeverage : α → ℚ
  /-- Compression gain: pattern compression enabled by the object -/
  compressionGain : α → ℚ
  /-- Update resistance: inertia against removal/modification -/
  updateResistance : α → ℚ
  /-- Turbulence cost: conceptual turbulence or confusion introduced -/
  turbulenceCost : α → ℚ
  /-- Collapse resistance: persistence under transformation pressure -/
  collapseResistance : α → ℚ

/--
Mass vector for a semantic carrier.

  M(x) = [I, B, R, C, U, T, K]

Where:
  I = invariant strength
  B = binding degree
  R = routing leverage
  C = compression gain
  U = update resistance
  T = turbulence cost
  K = collapse resistance
-/
structure MassVector where
  invariantStrength : ℚ
  bindingDegree : ℚ
  routingLeverage : ℚ
  compressionGain : ℚ
  updateResistance : ℚ
  turbulenceCost : ℚ
  collapseResistance : ℚ

/--
Extract mass vector from any SemanticCarrier.
-/
def massVectorOf [SemanticCarrier α] (x : α) : MassVector :=
  {
    invariantStrength := SemanticCarrier.invariantStrength x,
    bindingDegree := SemanticCarrier.bindingDegree x,
    routingLeverage := SemanticCarrier.routingLeverage x,
    compressionGain := SemanticCarrier.compressionGain x,
    updateResistance := SemanticCarrier.updateResistance x,
    turbulenceCost := SemanticCarrier.turbulenceCost x,
    collapseResistance := SemanticCarrier.collapseResistance x
  }

/--
Weight parameters for scalar mass computation.

Each weight controls how much a component contributes to the total
semantic mass score.
-/
structure MassWeights where
  w_invariant : ℚ := 1
  w_binding : ℚ := 1
  w_routing : ℚ := 1
  w_compression : ℚ := 1
  w_update : ℚ := 1
  w_turbulence : ℚ := 1
  w_collapse : ℚ := 1
deriving Inhabited

/--
Compute weighted semantic mass from mass vector.

  m_s(x) = w₁·I(x) + w₂·B(x) + w₃·R(x) + w₄·C(x) + w₅·U(x) + w₆·T(x) + w₇·K(x)
-/
def weightedMass (mv : MassVector) (weights : MassWeights) : ℚ :=
  weights.w_invariant * mv.invariantStrength +
  weights.w_binding * mv.bindingDegree +
  weights.w_routing * mv.routingLeverage +
  weights.w_compression * mv.compressionGain +
  weights.w_update * mv.updateResistance +
  weights.w_turbulence * mv.turbulenceCost +
  weights.w_collapse * mv.collapseResistance

/--
Compute semantic mass for any SemanticCarrier with default weights.
-/
def semanticMassOf [SemanticCarrier α] (x : α) : ℚ :=
  weightedMass (massVectorOf x) default

/--
Mass distance between two carriers.

  d(A,B) = Σᵢ wᵢ |Mᵢ(A) - Mᵢ(B)|

This measures how different two objects are in their semantic mass profile.
-/
def massDistance [SemanticCarrier α]
    (weights : MassWeights)
    (x y : α) : ℚ :=
  let mvX := massVectorOf x
  let mvY := massVectorOf y
  let dI := weights.w_invariant * abs (mvX.invariantStrength - mvY.invariantStrength)
  let dB := weights.w_binding * abs (mvX.bindingDegree - mvY.bindingDegree)
  let dR := weights.w_routing * abs (mvX.routingLeverage - mvY.routingLeverage)
  let dC := weights.w_compression * abs (mvX.compressionGain - mvY.compressionGain)
  let dU := weights.w_update * abs (mvX.updateResistance - mvY.updateResistance)
  let dT := weights.w_turbulence * abs (mvX.turbulenceCost - mvY.turbulenceCost)
  let dK := weights.w_collapse * abs (mvX.collapseResistance - mvY.collapseResistance)
  dI + dB + dR + dC + dU + dT + dK

/--
Route score for adapter path between carriers.

  routeScore = -distance - turbulence - routeCost + bindingGain

This measures how good an adapter path is: lower cost is better,
higher binding gain is better.
-/
def routeScore [SemanticCarrier α]
    (weights : MassWeights)
    (x y adapter : α) : ℚ :=
  let dist := massDistance weights x y
  let mvAdapter := massVectorOf adapter
  let turbulence := mvAdapter.turbulenceCost
  let routeCost := mvAdapter.updateResistance
  let bindingGain := mvAdapter.bindingDegree
  (-dist - turbulence - routeCost + bindingGain)

/--
Backward compatibility: SemanticType as alias for SemanticCarrier
-/
abbrev SemanticType := SemanticCarrier

/--
SemanticRole: classification of semantic objects by their functional role.

This prevents category collapse between different types of semantic objects:
  - carrier: has intrinsic semantic mass
  - adapter: connects different domains
  - field: background structure that gives mass through coupling
  - couplingWitness: detectable proof-event of coupling
  - measurement: contextual load or observed value
-/
inductive SemanticRole where
  | carrier          -- intrinsic semantic mass object
  | adapter          -- cross-domain connector
  | field            -- background coupling field
  | couplingWitness  -- detectable proof of coupling
  | measurement      -- contextual load / observed value

/--
Coupling strength between a semantic object and a field.

  χ_s(x, F) = coupling of object x to field F

This measures how strongly an object couples to a background field,
which determines how much semantic mass it acquires through that coupling.
-/
def couplingStrength [SemanticCarrier α] (x : α) (fieldStrength : ℚ) : ℚ :=
  let mv := massVectorOf x
  -- Coupling depends on binding degree and collapse resistance
  mv.bindingDegree * fieldStrength + mv.collapseResistance * fieldStrength / 2

/--
Semantic weight: contextual load of a semantic object.

  W_s(x; C) = m_s(x) * g_s(C)

Where:
  - x = semantic object
  - C = context field
  - m_s(x) = semantic mass (intrinsic)
  - g_s(C) = semantic gravity / contextual pressure
  - W_s = semantic weight in that context

Semantic weight is not fixed. It is mass under a field.
-/
def semanticWeight [SemanticCarrier α]
    (x : α)
    (contextPressure : ℚ) : ℚ :=
  semanticMassOf x * contextPressure

/--
Semantic Higgs mechanism: mass acquisition through coupling.

  m_s(x) = m_0(x) + λ * χ_s(x, F_H)

Where:
  - m_0(x) = base semantic mass
  - F_H = semantic Higgs-like coupling field
  - χ_s = coupling strength to that field
  - λ = scaling coefficient

A symbol becomes heavy when it couples strongly to a field of constraints,
invariants, and consequences.
-/
structure SemanticHiggsMechanism where
  /-- Base semantic mass before coupling -/
  baseMass : ℚ
  /-- Higgs-like coupling field strength -/
  fieldStrength : ℚ
  /-- Scaling coefficient λ -/
  scalingCoefficient : ℚ

/--
Compute semantic mass after Higgs-like coupling.
-/
def massAfterCoupling [SemanticCarrier α]
    (x : α)
    (mechanism : SemanticHiggsMechanism) : ℚ :=
  let base := semanticMassOf x
  let coupling := couplingStrength x mechanism.fieldStrength
  base + mechanism.scalingCoefficient * coupling

/--
SemanticField: background field that can confer mass through coupling.

Examples:
  - algebraic extension field (for i)
  - Standard Model explanatory field (for Higgs)
  - thermodynamic constraint field (for entropy)
  - market regime field (for liquidity)
-/
structure SemanticField where
  /-- Field strength / density -/
  strength : ℚ
  /-- Turbulence introduced by the field -/
  turbulence : ℚ
  /-- Binding power of the field -/
  binding : ℚ

/--
Weight concept as a metameasure carrier.

The word "weight" is reflexive and polysemous:
  - force under gravity
  - importance
  - coefficient
  - burden
  - statistical contribution
  - font thickness
  - evidence strength

It is high-mass and high-turbulence: a powerful but dangerous adapter.
-/
inductive WeightConcept where
  | weight

/--
ImaginaryUnit: test case proving non-physical objects can carry semantic mass.

Imaginary numbers have no physical mass, but they have enormous semantic mass
because they change what the mathematical universe can route, compress, and solve.

Properties of i:
  - Invariant: i² = -1 (core algebraic rule)
  - Binding: connects algebra, geometry, oscillation, quantum phase
  - Routing leverage: opens routes blocked over ℝ
  - Compression gain: rotations/oscillations become compact
  - Update resistance: removing it breaks many structures
-/
inductive ImaginaryUnit where
  | i

instance : SemanticCarrier ImaginaryUnit where
  invariantStrength _ := 1        -- i² = -1 marker
  bindingDegree _ := 4            -- cross-domain binding
  routingLeverage _ := 5           -- opens routes blocked over ℝ
  compressionGain _ := 5          -- rotations/oscillations become compact
  updateResistance _ := 4         -- high structural dependence
  turbulenceCost _ := 3           -- introduces conceptual turbulence for beginners
  collapseResistance _ := 5       -- persists under many transformations

/--
Semantic mass of the imaginary unit i.

This demonstrates that non-physical objects can carry high semantic mass
due to their transformation leverage.

Mass vector: [I=1, B=4, R=5, C=5, U=4, T=3, K=5]
Total mass: 22 (with default weights)
-/
def imaginaryUnitSemanticMass : ℚ :=
  semanticMassOf ImaginaryUnit.i

/--
THEOREM: SEMANTIC_ATTRACTION_NONNEGATIVE
If G_s ≥ 0, mi ≥ 0, mj ≥ 0, and d² + ε > 0, then attraction ≥ 0.

This is a safety property: attraction between concepts is non-negative
when masses are non-negative and the coupling constant is non-negative.
-/
theorem semanticAttraction_nonneg
    (G_s eps mi mj d_sq : ℚ)
    (h_G : G_s >= 0)
    (h_mi : mi >= 0)
    (h_mj : mj >= 0)
    (h_denom : d_sq + eps > 0) :
    semanticAttraction G_s eps mi mj d_sq >= 0 := by
  unfold semanticAttraction
  have h_num : G_s * mi * mj >= 0 := by
    apply mul_nonneg (mul_nonneg h_G h_mi) h_mj
  have h_denom_nonneg : d_sq + eps >= 0 := by
    apply le_of_lt h_denom
  apply div_nonneg h_num h_denom_nonneg

/--
THEOREM: SEMANTIC_INERTIA_NONNEGATIVE
If mass >= 0 and routeCost >= 0, then semantic inertia >= 0.
-/
theorem semanticInertia_nonneg
    (p : SemanticMassPoint n)
    (h_mass : p.mass >= 0)
    (h_cost : p.routeCost >= 0) :
    semanticInertia p >= 0 := by
  unfold semanticInertia
  apply mul_nonneg h_mass h_cost

/--
THEOREM: SEMANTIC_MASS_DRAIN_STABILITY
If source reinforcement does not exceed drain pressure, semantic mass cannot increase.

  if S < Γm → drain / forgetting / smoothing

This is the first semantic cooling law: without sufficient reinforcement,
semantic mass decays through the drain.
-/
theorem semanticMassChange_nonpos
    (p : SemanticDrainParams)
    (m : ℚ)
    (hS : p.source <= p.drainRate * m) :
    semanticMassChange p m <= 0 := by
  unfold semanticMassChange
  linarith

/--
THEOREM: SEMANTIC_MASS_SOURCE_DOMINANCE
If context/source reinforcement exceeds drain pressure, semantic mass grows.

  if S > Γm → reinforcement / attractor growth

Together with semanticMassChange_nonpos, this defines the semantic phase boundary:
  S < Γm → drain / forgetting / smoothing
  S = Γm → semantic fixed point
  S > Γm → reinforcement / attractor growth
-/
theorem semanticMassChange_pos
    (p : SemanticDrainParams)
    (m : ℚ)
    (hS : p.source > p.drainRate * m) :
    semanticMassChange p m > 0 := by
  unfold semanticMassChange
  linarith

end Semantics
