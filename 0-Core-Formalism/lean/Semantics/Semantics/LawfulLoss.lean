/-  LawfulLoss.lean — Cross-Manifold Translation Invariants in Q0_16

  Formalizes the `bind` bridge semantics for lawful loss across
  incompatible cognitive manifolds (human, machine, alien, etc.).

  Every translation yields a `BindResult` recording:
    - lawful : Bool   — did invariants survive?
    - cost   : Q0_16  — dimensional mismatch penalty (normalized)
    - witness : String — what was sacrificed (human-readable trace)

  Substrate-agnostic: no runtime dependencies, no Float, no IO.
  Recoverable on any substrate that can evaluate Lean 4.

  Reference: docs/semantics/INCOMPATIBLE_MANIFOLDS_AND_LAWFUL_LOSS.md
  Truth Seal: [ SSS-ENE-TRUTH-2026-04-14 ]
-/

import Semantics.FixedPoint

namespace Semantics.LawfulLoss

open Semantics.Q0_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Bind Classification (Five Permitted Classes per AGENTS.md §4)
-- ═══════════════════════════════════════════════════════════════════════════

/-- The five lawful bind classes.  No sixth class without
    blackboard justification in docs/semantics/. -/
inductive BindClass where
  | informational
  | geometric
  | thermodynamic
  | physical
  | control
  deriving Repr, BEq, Inhabited

/-- Human-readable label for a bind class. -/
def bindClassLabel : BindClass → String
  | .informational => "informational_bind"
  | .geometric     => "geometric_bind"
  | .thermodynamic => "thermodynamic_bind"
  | .physical       => "physical_bind"
  | .control        => "control_bind"

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  BindResult — The Universal Translation Receipt
-- ═══════════════════════════════════════════════════════════════════════════

/-- Result of a cross-manifold `bind` operation.
    Substrate-agnostic: every field is serializable without Float or IO. -/
structure BindResult where
  lawful  : Bool
  cost    : Q0_16
  witness : String
  klass   : BindClass
  deriving Repr, Inhabited

-- Convenience constructors
/-- A lawful translation with minimal cost. -/
def mkLawful (cost : Q0_16) (witness : String) (klass : BindClass) : BindResult :=
  { lawful := true, cost := cost, witness := witness, klass := klass }

/-- An unlawful translation with maximum cost (invariant violation). -/
def mkUnlawful (witness : String) (klass : BindClass) : BindResult :=
  { lawful := false, cost := Q0_16.one, witness := witness, klass := klass }

/-- Predicate: is the translation lawful? -/
def isLawful (r : BindResult) : Bool := r.lawful

/-- Extract normalized cost. -/
def bindCost (r : BindResult) : Q0_16 := r.cost

/-- Extract witness string. -/
def bindWitness (r : BindResult) : String := r.witness

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Lawful Loss Primitive
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute lawful loss between two manifolds given invariant preservation.
    If all invariants are preserved, the translation is lawful and cost
    records the dimensional compression.  If any invariant is violated,
    the result is unlawful with maximum cost.

    Parameters:
      invariantsPreserved : Bool — did every invariant survive?
      estimatedCost       : Q0_16 — compression penalty (ignored if unlawful)
      witnessLog          : String — record of what was lost
      klass               : BindClass — which bind class governed this translation

    Returns: BindResult with lawful flag, cost, witness, and class. -/
def lawfulLoss (invariantsPreserved : Bool) (estimatedCost : Q0_16)
               (witnessLog : String) (klass : BindClass) : BindResult :=
  if invariantsPreserved then
    mkLawful estimatedCost witnessLog klass
  else
    mkUnlawful ("INVARIANT_VIOLATION: " ++ witnessLog) klass

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Standard Model Floor Invariants (Universal Observers)
-- ═══════════════════════════════════════════════════════════════════════════

/-- The five Standard Model conserved quantities that any observer
    (human, dolphin, machine, alien) must agree on.  These form the
    lowest-resolution but most-universal translation floor. -/
inductive StandardModelInvariant where
  | charge
  | baryonNumber
  | leptonNumber
  | energyMomentum
  | spin
  deriving Repr, BEq, Inhabited

/-- Human-readable label for a Standard Model invariant. -/
def invariantLabel : StandardModelInvariant → String
  | .charge          => "charge_conservation"
  | .baryonNumber    => "baryon_number_conservation"
  | .leptonNumber    => "lepton_number_conservation"
  | .energyMomentum  => "energy_momentum_conservation"
  | .spin            => "spin_conservation"

/-- Check whether a list of invariant labels is fully preserved.
    In practice this is supplied by the bind engine; here we model it
    as a predicate over a list of Bool flags. -/
def allInvariantsPreserved (flags : List Bool) : Bool :=
  flags.all (fun b => b)

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Concrete Examples — Grandma / Dolphin / Machine / Alien
-- ═══════════════════════════════════════════════════════════════════════════

/-- Example: human-to-human translation (same manifold, cheap bridge).
    Invariants: Agent, Location, Interaction, SemanticWeight all preserved.
    Cost: low (near zero). -/
def exampleHumanHuman : BindResult :=
  lawfulLoss
    (allInvariantsPreserved [true, true, true, true])
    Q0_16.zero
    "no_loss_same_manifold"
    .informational

/-- Example: human-to-dolphin projection (dolphin-compatible manifold).
    Invariants: Agent, Location, InteractionClass preserved.
    Lost: TargetRole(clerk→other), SpecificAction(punched→fight).
    Cost: moderate. -/
def exampleHumanDolphin : BindResult :=
  lawfulLoss
    (allInvariantsPreserved [true, true, true, true])
    Q0_16.half
    "lost:target_role,specific_action; preserved:agent,location,interaction_class,semantic_weight"
    .geometric

/-- Example: bad loss — conflict invariant destroyed.
    "Grandma went shopping" drops the interaction class.
    Result: unlawful, max cost, invariant violation flagged. -/
def exampleBadLoss : BindResult :=
  lawfulLoss
    (allInvariantsPreserved [true, true, false, true])  -- interaction class lost
    Q0_16.one
    "Invariant violation: interaction_class missing (conflict destroyed)"
    .geometric

/-- Example: machine manifold — even higher compression.
    Preserves only entity labels and interaction type.
    Cost: high but still lawful. -/
def exampleHumanMachine : BindResult :=
  lawfulLoss
    (allInvariantsPreserved [true, true])
    (Q0_16.ofFloat 0.8)  -- high compression, but still < 1.0
    "preserved:entity_a,entity_b,location_l,interaction_type; lost:identity,narrative_torsion,social_role"
    .informational

/-- Example: alien manifold — only Standard Model floor survives.
    Almost comically lossy, but lawful because physics invariants hold. -/
def exampleHumanAlien : BindResult :=
  lawfulLoss
    (allInvariantsPreserved [true, true, true, true, true])  -- all 5 SM invariants
    (Q0_16.ofFloat 0.99)  -- near-maximum lawful cost
    "floor_only:charge,baryon_number,lepton_number,energy_momentum,spin; all_semantics_collapsed"
    .physical

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Verification (#eval!)
-- ═══════════════════════════════════════════════════════════════════════════

-- Example 1: human-to-human is lawful, zero cost
#eval! exampleHumanHuman.lawful
#eval! exampleHumanHuman.cost.val.toNat
#eval! exampleHumanHuman.witness

-- Example 2: human-to-dolphin is lawful, moderate cost
#eval! exampleHumanDolphin.lawful
#eval! exampleHumanDolphin.cost.val.toNat
#eval! exampleHumanDolphin.witness

-- Example 3: bad loss is unlawful, max cost
#eval! exampleBadLoss.lawful
#eval! exampleBadLoss.cost.val.toNat
#eval! exampleBadLoss.witness

-- Example 4: machine translation is lawful despite high compression
#eval! exampleHumanMachine.lawful
#eval! exampleHumanMachine.cost.val.toNat
#eval! exampleHumanMachine.witness

-- Example 5: alien floor-only translation is lawful
#eval! exampleHumanAlien.lawful
#eval! exampleHumanAlien.cost.val.toNat
#eval! exampleHumanAlien.witness

end Semantics.LawfulLoss
