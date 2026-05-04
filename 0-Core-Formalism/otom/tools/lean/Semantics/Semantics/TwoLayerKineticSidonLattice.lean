/-
TwoLayerKineticSidonLattice.lean — kinetic/Sidon two-layer lattice scaffold v0.1

Core intuition:
  The quaternion/Sidon layer is not the entire lattice. It is a relational
  routing/addressing layer coupled to a kinetic substrate. Sidon sets flow
  between the kinetic layer and the relational layer, allowing motion/energy
  updates to become pairwise-addressable without alias collapse.

Layer 0: kinetic lattice
  local mass/energy/velocity-like state, no Float

Layer 1: Sidon relational lattice
  pair signatures / address codes satisfying pairwise uniqueness

Flow:
  kinetic state -> pair signature -> Sidon gate -> feedback into kinetic update

No Float. No material-phase claim. This is a formal toy scaffold.
-/

import Std

namespace Semantics.TwoLayerKineticSidonLattice

/-- Evidence ladder for this scaffold. -/
inductive ClaimState where
  | beautifulProvisional
  | calibratedEngineeringDelta
  | reviewed
  deriving Repr, DecidableEq, Inhabited

/-- A square-grid coordinate. -/
structure GridCoord where
  x : Nat
  y : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Kinetic state at one lattice site.

`energy`, `momentumX`, `momentumY`, and `phaseClock` are Nat-encoded toy values.
A production version can map them to Q16_16 or signed fixed-point fields.
-/
structure KineticSite where
  id : Nat
  coord : GridCoord
  energy : Nat
  momentumX : Nat
  momentumY : Nat
  phaseClock : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Kinetic layer: the substrate where local updates happen. -/
structure KineticLayer where
  sites : List KineticSite
  deriving Repr, Inhabited

/-- Pair address on the Sidon layer. -/
structure PairAddress where
  i : Nat
  j : Nat
  signature : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Same unordered pair relation. -/
def sameUnorderedPair (p q : PairAddress) : Prop :=
  (p.i = q.i ∧ p.j = q.j) ∨ (p.i = q.j ∧ p.j = q.i)

/-- Sidon-like uniqueness for relational pair addresses. -/
def SidonLike (pairs : List PairAddress) : Prop :=
  ∀ p q, p ∈ pairs → q ∈ pairs → p.signature = q.signature → sameUnorderedPair p q

/-- Nontrivial pair-address alias collision. -/
def AliasCollision (pairs : List PairAddress) : Prop :=
  ∃ p q, p ∈ pairs ∧ q ∈ pairs ∧ p.signature = q.signature ∧ ¬ sameUnorderedPair p q

/-- A Sidon-like layer has no nontrivial alias collision. -/
theorem sidon_like_no_alias_collision
    (pairs : List PairAddress)
    (h : SidonLike pairs) :
    ¬ AliasCollision pairs := by
  intro hc
  rcases hc with ⟨p, q, hp, hq, hs, hneq⟩
  exact hneq (h p q hp hq hs)

/-- Sidon layer: relational address space over kinetic site pairs. -/
structure SidonLayer where
  pairs : List PairAddress
  claimState : ClaimState
  deriving Repr, Inhabited

/-- A flow event transporting kinetic relation into Sidon address space. -/
structure KineticToSidonFlow where
  sourceA : Nat
  sourceB : Nat
  kineticFlux : Nat
  phaseDelta : Nat
  producedSignature : Nat
  deriving Repr, DecidableEq, Inhabited

/-- A feedback event from Sidon relation back into kinetic update. -/
structure SidonToKineticFlow where
  address : PairAddress
  feedbackEnergy : Nat
  feedbackPhase : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Two-layer lattice: kinetic substrate plus Sidon relational layer. -/
structure TwoLayerLattice where
  kinetic : KineticLayer
  sidon : SidonLayer
  forwardFlow : List KineticToSidonFlow
  feedbackFlow : List SidonToKineticFlow
  note : String
  deriving Repr, Inhabited

/-- The Sidon lawfulness gate for a two-layer lattice. -/
def PassesSidonTransportGate (L : TwoLayerLattice) : Prop :=
  SidonLike L.sidon.pairs

/-- If the transport gate passes, no Sidon-layer alias collision exists. -/
theorem passes_transport_gate_no_alias
    (L : TwoLayerLattice)
    (h : PassesSidonTransportGate L) :
    ¬ AliasCollision L.sidon.pairs := by
  exact sidon_like_no_alias_collision L.sidon.pairs h

/-- Forward flow is represented on the Sidon layer if its produced signature exists. -/
def FlowRepresented (sidon : SidonLayer) (f : KineticToSidonFlow) : Prop :=
  ∃ p, p ∈ sidon.pairs ∧ p.i = f.sourceA ∧ p.j = f.sourceB ∧ p.signature = f.producedSignature

/-- Every forward flow has a Sidon-layer address. -/
def AllForwardFlowsRepresented (L : TwoLayerLattice) : Prop :=
  ∀ f, f ∈ L.forwardFlow → FlowRepresented L.sidon f

/-- The useful two-layer gate: every kinetic flow is represented and pair addresses are Sidon-like. -/
def PassesTwoLayerGate (L : TwoLayerLattice) : Prop :=
  AllForwardFlowsRepresented L ∧ PassesSidonTransportGate L

/-- Passing the full two-layer gate implies no relational alias collision. -/
theorem two_layer_gate_no_alias
    (L : TwoLayerLattice)
    (h : PassesTwoLayerGate L) :
    ¬ AliasCollision L.sidon.pairs := by
  exact passes_transport_gate_no_alias L h.right

/-- Example kinetic layer: a four-site square. -/
def kineticSquare : KineticLayer :=
  { sites :=
    [ { id := 0, coord := { x := 0, y := 0 }, energy := 10, momentumX := 1, momentumY := 0, phaseClock := 0 }
    , { id := 1, coord := { x := 1, y := 0 }, energy := 12, momentumX := 1, momentumY := 1, phaseClock := 1 }
    , { id := 2, coord := { x := 0, y := 1 }, energy := 11, momentumX := 0, momentumY := 1, phaseClock := 2 }
    , { id := 3, coord := { x := 1, y := 1 }, energy := 13, momentumX := 1, momentumY := 1, phaseClock := 3 }
    ] }

/-- Example Sidon relation layer over the square. -/
def sidonSquare : SidonLayer :=
  { pairs :=
    [ { i := 0, j := 1, signature := 101 }
    , { i := 0, j := 2, signature := 102 }
    , { i := 1, j := 3, signature := 113 }
    , { i := 2, j := 3, signature := 123 }
    ]
    claimState := .beautifulProvisional }

/-- Example flows from kinetic substrate into Sidon address space. -/
def exampleForwardFlow : List KineticToSidonFlow :=
  [ { sourceA := 0, sourceB := 1, kineticFlux := 2, phaseDelta := 1, producedSignature := 101 }
  , { sourceA := 0, sourceB := 2, kineticFlux := 1, phaseDelta := 2, producedSignature := 102 }
  ]

/-- Example feedback from Sidon layer back into kinetic update. -/
def exampleFeedbackFlow : List SidonToKineticFlow :=
  [ { address := { i := 0, j := 1, signature := 101 }, feedbackEnergy := 1, feedbackPhase := 1 }
  , { address := { i := 0, j := 2, signature := 102 }, feedbackEnergy := 1, feedbackPhase := 2 }
  ]

/-- Full example two-layer lattice. -/
def exampleTwoLayerLattice : TwoLayerLattice :=
  { kinetic := kineticSquare
    sidon := sidonSquare
    forwardFlow := exampleForwardFlow
    feedbackFlow := exampleFeedbackFlow
    note := "kinetic square lattice coupled to Sidon pair-address flow layer" }

/-- Example Sidon layer satisfies pairwise uniqueness. -/
theorem sidonSquare_sidon_like : SidonLike sidonSquare.pairs := by
  intro p q hp hq hs
  simp [sidonSquare] at hp hq
  rcases hp with hp | hp | hp | hp
  · subst p
    rcases hq with hq | hq | hq | hq
    · subst q; left; constructor <;> rfl
    · subst q; contradiction
    · subst q; contradiction
    · subst q; contradiction
  · subst p
    rcases hq with hq | hq | hq | hq
    · subst q; contradiction
    · subst q; left; constructor <;> rfl
    · subst q; contradiction
    · subst q; contradiction
  · subst p
    rcases hq with hq | hq | hq | hq
    · subst q; contradiction
    · subst q; contradiction
    · subst q; left; constructor <;> rfl
    · subst q; contradiction
  · subst p
    rcases hq with hq | hq | hq | hq
    · subst q; contradiction
    · subst q; contradiction
    · subst q; contradiction
    · subst q; left; constructor <;> rfl

/-- Example forward flows are represented by Sidon addresses. -/
theorem example_forward_flows_represented :
    AllForwardFlowsRepresented exampleTwoLayerLattice := by
  intro f hf
  simp [exampleTwoLayerLattice, exampleForwardFlow, FlowRepresented, sidonSquare] at hf ⊢
  cases hf with
  | inl h0 =>
      subst f
      exact Or.inl ⟨rfl, rfl, rfl⟩
  | inr hrest =>
      cases hrest with
      | inl h1 =>
          subst f
          exact Or.inr (Or.inl ⟨rfl, rfl, rfl⟩)
      | inr hnil =>
          cases hnil

/-- Example two-layer lattice passes the combined gate. -/
theorem exampleTwoLayerLattice_passes_gate :
    PassesTwoLayerGate exampleTwoLayerLattice := by
  constructor
  · exact example_forward_flows_represented
  · unfold PassesSidonTransportGate exampleTwoLayerLattice
    exact sidonSquare_sidon_like

/-- Therefore the example two-layer lattice has no Sidon-layer alias collision. -/
theorem exampleTwoLayerLattice_no_alias :
    ¬ AliasCollision exampleTwoLayerLattice.sidon.pairs := by
  exact two_layer_gate_no_alias exampleTwoLayerLattice exampleTwoLayerLattice_passes_gate

#eval exampleTwoLayerLattice.note

end Semantics.TwoLayerKineticSidonLattice
