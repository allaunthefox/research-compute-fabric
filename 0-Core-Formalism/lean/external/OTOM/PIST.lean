import Mathlib.Data.Nat.Basic
import Mathlib.Tactic

/-! Prime Interval Shell Theory (PIST) Core - Extended Defensible Version

  This module formalizes a defensible discrete core for the PIST state machine.
  It avoids speculative geometry and focuses on an interval-local coordinate model.

  The main idea is that a natural number between consecutive squares is represented
  by a shell index `k` and an offset `t` with `0 ≤ t ≤ 2*k+1`.
  Within that shell, the PIST mass is the quadratic quantity

  `mass = t * ((2*k+1) - t)`.

  This file contains (minimal + extended):

  * Interval-local coordinate type `Coord` with shell geometry
  * Mass / hyperbola-index definitions (a, b, mass = a*b)
  * Mirror involution inside one shell (preserves mass)
  * Zero mass theorems (exactly at shell endpoints)
  * Positive mass equivalence (strictly inside shell)
  * Resonance equivalence relation (refl, symm, trans)
  * Phase flags (grounded/seismic) based on mass
  * Move labels for state-machine transitions
  * LogEntry/Log for append-only history tracking
  * Extended State with operations (penalize, accept, relocate, resonanceJump, rejectWithPenalty)
  * Transition structure with mass preservation and strict decrease
  * LawfulMove inductive (linear, resonance, rejected, crystallized)
  * Projector (idempotent normalizer) and Grounder structures
  * Two kernel interfaces: minimal Kernel and extended KernelExtended
  * Lyapunov-style strict descent guarantees for both kernels

  The file deliberately avoids making cryptographic or physical claims.
  Anything "more weird" is encoded as typed data and admissibility rules.

  Per AGENTS.md §2: PascalCase types, camelCase functions.
  Per AGENTS.md §4: All definitions must have eval witnesses or theorems.
-/

namespace PIST

/-- A coordinate inside the square shell bounded by `k^2` and `(k+1)^2`.
The offset `t` records the position inside that shell, so necessarily
`t ≤ 2*k + 1`.
-/structure Coord where
  k : ℕ
  t : ℕ
  ht : t ≤ 2 * k + 1

  deriving DecidableEq, Repr

namespace Coord

/-- The underlying natural number represented by the shell coordinate. -/
def n (c : Coord) : ℕ := c.k ^ 2 + c.t

/-- Distance to the lower square in shell coordinates. -/
def a (c : Coord) : ℕ := c.t

/-- Distance to the upper square in shell coordinates. -/
def b (c : Coord) : ℕ := 2 * c.k + 1 - c.t

/-- The PIST mass / hyperbola index in shell coordinates. -/
def mass (c : Coord) : ℕ := c.a * c.b

@[simp] theorem a_def (c : Coord) : c.a = c.t := rfl

@[simp] theorem b_def (c : Coord) : c.b = 2 * c.k + 1 - c.t := rfl

@[simp] theorem mass_def (c : Coord) : c.mass = c.t * (2 * c.k + 1 - c.t) := rfl

/-- The shell identity `a + b = 2*k+1`. -/
theorem a_add_b (c : Coord) : c.a + c.b = 2 * c.k + 1 := by
  dsimp [a, b]
  exact Nat.add_sub_of_le c.ht

/-- The mirror point inside the same shell. -/
def mirror (c : Coord) : Coord where
  k := c.k
  t := 2 * c.k + 1 - c.t
  ht := Nat.sub_le _ _

@[simp] theorem mirror_k (c : Coord) : c.mirror.k = c.k := rfl

@[simp] theorem mirror_t (c : Coord) : c.mirror.t = 2 * c.k + 1 - c.t := rfl

@[simp] theorem a_mirror (c : Coord) : c.mirror.a = c.b := rfl

/-- Mirroring swaps the two shell distances. -/
@[simp] theorem b_mirror (c : Coord) : c.mirror.b = c.a := by
  dsimp [b, a, mirror]
  rw [Nat.sub_sub_self c.ht]

/-- Mirror preserves mass. -/
@[simp] theorem mass_mirror (c : Coord) : c.mirror.mass = c.mass := by
  simp [mass, a, b, mirror, Nat.mul_comm]
  have h : c.k * 2 + 1 - (c.k * 2 + 1 - c.t) = c.t := by
    have : c.k * 2 + 1 = 2 * c.k + 1 := by simp [Nat.mul_comm]
    rw [this]
    rw [Nat.sub_sub_self c.ht]
  simp [h]
  exact Nat.mul_comm _ _

/-- Mirroring twice returns the original shell offset. -/
@[simp] theorem mirror_mirror_t (c : Coord) : c.mirror.mirror.t = c.t := by
  dsimp [mirror]
  rw [Nat.sub_sub_self c.ht]

/-- Mirror is an involution. -/
@[simp] theorem mirror_mirror (c : Coord) : c.mirror.mirror = c := by
  cases c with
  | mk k t ht =>
      simp [mirror]
      rw [Nat.sub_sub_self ht]

/-- A coordinate has zero mass exactly at the shell endpoints. -/
theorem mass_eq_zero_iff (c : Coord) : c.mass = 0 ↔ c.t = 0 ∨ c.t = 2 * c.k + 1 := by
  rw [mass_def]
  constructor
  · intro h
    rcases (Nat.mul_eq_zero.mp h) with h0 | h1
    · exact Or.inl h0
    · right
      have hle : 2 * c.k + 1 ≤ c.t := by
        rw [Nat.sub_eq_zero_iff_le] at h1
        exact h1
      exact le_antisymm c.ht hle
  · rintro (h | h)
    · simp [h]
    · simp [h]

/-- Positive mass is equivalent to being strictly inside the shell. -/
theorem mass_pos_iff (c : Coord) : 0 < c.mass ↔ 0 < c.t ∧ c.t < 2 * c.k + 1 := by
  constructor
  · intro h
    have hne : c.mass ≠ 0 := Nat.ne_of_gt h
    have hnot := mt (mass_eq_zero_iff c).mpr hne
    constructor
    · by_contra h0
      apply hne
      apply (mass_eq_zero_iff c).mpr
      exact Or.inl (Nat.eq_zero_of_not_pos h0)
    · by_contra htop
      apply hne
      apply (mass_eq_zero_iff c).mpr
      exact Or.inr (le_antisymm c.ht (not_lt.mp htop))
  · rintro ⟨ht0, httop⟩
    rw [mass_def]
    apply Nat.mul_pos
    · exact ht0
    · exact Nat.sub_pos_of_lt httop

/-- Left shell endpoint. -/
def lower (k : ℕ) : Coord where
  k := k
  t := 0
  ht := by omega

/-- Right shell endpoint. -/
def upper (k : ℕ) : Coord where
  k := k
  t := 2 * k + 1
  ht := by omega

@[simp] theorem mass_lower (k : ℕ) : (lower k).mass = 0 := by simp [lower, mass]
@[simp] theorem mass_upper (k : ℕ) : (upper k).mass = 0 := by simp [upper, mass]

end Coord

/-- Two shell coordinates are resonant when they have equal mass. -/
def Resonant (x y : Coord) : Prop := x.mass = y.mass

theorem Resonant.refl (x : Coord) : Resonant x x := rfl

theorem Resonant.symm {x y : Coord} : Resonant x y -> Resonant y x := by
  intro h
  exact Eq.symm h

theorem Resonant.trans {x y z : Coord} : Resonant x y -> Resonant y z -> Resonant x z := by
  intro h₁ h₂
  exact Eq.trans h₁ h₂

/-- Phase flags for the interval-local machine. -/
inductive Phase
  | grounded
  | drift
  | seismic
  deriving DecidableEq, Repr

/-- Auxiliary resonance metadata. -/
def isResonantPair (x y : Coord) : Bool := x != y && x.mass == y.mass

/-- A simple phase classifier based on zero vs positive mass.
This is intentionally minimal and fully justified from the existing theory.
A richer classifier can be built on top of the same core.
-/def phase (c : Coord) : Phase :=
  if c.mass = 0 then Phase.grounded else Phase.seismic

@[simp] theorem phase_grounded_iff (c : Coord) : phase c = Phase.grounded ↔ c.mass = 0 := by
  apply Iff.intro
  · intro h
    unfold phase at h
    by_cases h2 : c.mass = 0
    · exact h2
    · rw [if_neg h2] at h
      cases h
  · intro h
    unfold phase
    by_cases h2 : c.mass = 0
    · rw [if_pos h2]
    · cases h2 h

@[simp] theorem phase_seismic_iff (c : Coord) : phase c = Phase.seismic ↔ c.mass ≠ 0 := by
  apply Iff.intro
  · intro h
    unfold phase at h
    by_cases h2 : c.mass = 0
    · rw [if_pos h2] at h
      cases h
    · exact h2
  · intro h
    unfold phase
    by_cases h2 : c.mass = 0
    · rw [if_pos h2]
      cases h h2
    · rw [if_neg h2]

/-- Move labels for state-machine transitions. -/
inductive MoveFlag
  | linearStep
  | resonanceJump
  | rejected
  | crystallized
  deriving DecidableEq, Repr

/-- A single log entry for append-only state history. -/
structure LogEntry where
  before : Coord
  after : Coord
  move : MoveFlag
  preservedMass : Bool

  deriving DecidableEq, Repr

/-- Append-only logs. We do not claim cryptographic properties here; this is just
an auditable history shape that a stronger implementation can refine.
-/abbrev Log := List LogEntry

namespace LogEntry

/-- The canonical entry for a resonance jump. -/
def resonance (x y : Coord) : LogEntry :=
  { before := x, after := y, move := MoveFlag.resonanceJump,
    preservedMass := decide (x.mass = y.mass) }

/-- The canonical entry for a rejection event. -/
def rejection (x y : Coord) : LogEntry :=
  { before := x, after := y, move := MoveFlag.rejected,
    preservedMass := decide (x.mass = y.mass) }

end LogEntry

/-- A minimal machine state over interval-local coordinates. -/
structure State where
  pos : Coord
  phaseFlag : Phase
  accepted : List Coord
  rejected : List Coord
  friction : ℕ
  log : Log

  deriving Repr

namespace State

/-- The canonical state built from a position. -/
def ofCoord (c : Coord) : State :=
  { pos := c
    phaseFlag := phase c
    accepted := []
    rejected := []
    friction := 0
    log := [] }

/-- A basic Lyapunov functional: PIST mass plus friction. -/
def potential (S : State) : ℕ := S.pos.mass + S.friction

@[simp] theorem potential_ofCoord (c : Coord) : (ofCoord c).potential = c.mass := by
  simp [ofCoord, potential]

/-- Append a log entry. -/
def appendLog (S : State) (e : LogEntry) : State :=
  { S with log := e :: S.log }

@[simp] theorem appendLog_log (S : State) (e : LogEntry) : (appendLog S e).log = e :: S.log := rfl

/-- Register a rejection and increase friction by a nonnegative penalty. -/
def penalize (S : State) (bad : Coord) (penalty : ℕ) : State :=
  { S with rejected := bad :: S.rejected, friction := S.friction + penalty }

@[simp] theorem penalize_friction (S : State) (bad : Coord) (penalty : ℕ) :
    (penalize S bad penalty).friction = S.friction + penalty := rfl

@[simp] theorem potential_penalize (S : State) (bad : Coord) (penalty : ℕ) :
    (penalize S bad penalty).potential = S.potential + penalty := by
  simp [potential, penalize, Nat.add_assoc]

/-- Register an accepted coordinate. -/
def accept (S : State) (good : Coord) : State :=
  { S with accepted := good :: S.accepted }

/-- Replace the active coordinate and refresh the phase flag. -/
def relocate (S : State) (c : Coord) : State :=
  { S with pos := c, phaseFlag := phase c }

@[simp] theorem relocate_pos (S : State) (c : Coord) : (relocate S c).pos = c := rfl
@[simp] theorem relocate_phase (S : State) (c : Coord) : (relocate S c).phaseFlag = phase c := rfl

/-- A resonance jump preserves the shell mass and updates the active coordinate. -/
def resonanceJump (S : State) (target : Coord) (_h : Resonant S.pos target) : State :=
  appendLog (relocate (accept S target) target) (LogEntry.resonance S.pos target)

@[simp] theorem resonanceJump_pos (S : State) (target : Coord) (h : Resonant S.pos target) :
    (resonanceJump S target h).pos = target := by
  simp [resonanceJump, appendLog, relocate]

@[simp] theorem resonanceJump_potential (S : State) (target : Coord) (h : Resonant S.pos target) :
    (resonanceJump S target h).potential = S.pos.mass + S.friction := by
  simp [resonanceJump, State.potential, relocate, accept, appendLog]
  exact h.symm

/-- A rejection event appends to the log and increases friction. -/
def rejectWithPenalty (S : State) (bad : Coord) (penalty : ℕ) : State :=
  appendLog (penalize S bad penalty) (LogEntry.rejection S.pos bad)

@[simp] theorem rejectWithPenalty_friction (S : State) (bad : Coord) (penalty : ℕ) :
    (rejectWithPenalty S bad penalty).friction = S.friction + penalty := by
  simp [rejectWithPenalty, penalize, appendLog]

@[simp] theorem penalize_pos (S : State) (bad : Coord) (penalty : ℕ) :
    (penalize S bad penalty).pos = S.pos := rfl

@[simp] theorem potential_rejectWithPenalty (S : State) (bad : Coord) (penalty : ℕ) :
    (rejectWithPenalty S bad penalty).potential = S.potential + penalty := by
  simp [rejectWithPenalty, State.potential, appendLog, penalize_pos]
  rw [Nat.add_assoc]

end State

/-- A lawful state-machine kernel. This is a specification interface:
concrete instances must provide the operations and proofs below.
-/structure Kernel (Candidate Reality : Type) where
  bind : Candidate
  assimilate : State → Candidate → State
  project : State → State
  ground : State → Reality → State
  terminal : State → Prop
  step : State → Reality → State := fun S R => ground (project (assimilate S bind)) R
  /-- Projection is idempotent. -/
  project_idem : ∀ S, project (project S) = project S
  /-- Grounding preserves the image of projection in one step form. -/
  project_step : ∀ S R, step S R = ground (project (assimilate S bind)) R
  /-- Nonterminal steps strictly decrease the chosen potential. -/
  strict_descent : ∀ S R, ¬ terminal S → State.potential (step S R) < State.potential S

namespace Kernel

variable {Candidate Reality : Type} (K : Kernel Candidate Reality)

@[simp] theorem step_def (S : State) (R : Reality) :
    K.step S R = K.ground (K.project (K.assimilate S K.bind)) R := by
  exact K.project_step S R

/-- A nonterminal state cannot be a fixed point of a strictly descending step. -/
theorem not_fixed_of_nonterminal (S : State) (R : Reality) (hS : ¬ K.terminal S) :
    K.step S R ≠ S := by
  intro hfix
  have hlt := K.strict_descent S R hS
  rw [hfix] at hlt
  exact Nat.lt_irrefl _ hlt

/-- One-step evolution from a nonterminal state strictly lowers the potential. -/
theorem potential_decreases (S : State) (R : Reality) (hS : ¬ K.terminal S) :
    State.potential (K.step S R) < State.potential S :=
  K.strict_descent S R hS

end Kernel

-- ════════════════════════════════════════════════════════════
-- Extended State Machine (Advanced Interface)
-- ════════════════════════════════════════════════════════════

/-- A transition packages a next state together with the move label used to reach it. -/
structure Transition where
  next : State
  flag : MoveFlag

  deriving Repr

namespace Transition

/-- Whether the transition preserves shell mass at the active coordinate. -/
def PreservesMass (S : State) (T : Transition) : Prop := S.pos.mass = T.next.pos.mass

/-- Whether the transition strictly decreases the potential. -/
def StrictlyDecreases (S : State) (T : Transition) : Prop := T.next.potential < S.potential

end Transition

/-- Lawfulness for candidate operations: either a one-step linear move, a resonance jump,
or a rejection that stays in place while adding friction.
-/inductive LawfulMove (S : State) : Transition → Prop
  | linear (T : Transition)
      (hflag : T.flag = MoveFlag.linearStep)
      (hfric : T.next.friction = S.friction)
      (hstep : T.next.pos.k = S.pos.k)
      (hshift : T.next.pos.t + 1 = S.pos.t ∨ S.pos.t + 1 = T.next.pos.t) :
      LawfulMove S T
  | resonance (target : Coord) (hres : Resonant S.pos target) :
      LawfulMove S
        { next := S.resonanceJump target hres, flag := MoveFlag.resonanceJump }
  | rejected (bad : Coord) (penalty : ℕ) :
      LawfulMove S
        { next := S.rejectWithPenalty bad penalty, flag := MoveFlag.rejected }
  | crystallized (target : Coord)
      (hzero : target.mass = 0)
      (hfric : S.friction = 0) :
      LawfulMove S
        { next := State.ofCoord target, flag := MoveFlag.crystallized }

namespace LawfulMove

/-- Resonance jumps preserve shell mass at the active coordinate. -/
theorem preservesMass_resonance (S : State) (target : Coord) (hres : Resonant S.pos target) :
    Transition.PreservesMass S
      { next := S.resonanceJump target hres, flag := MoveFlag.resonanceJump } := by
  dsimp [Transition.PreservesMass]
  simp [State.resonanceJump_pos]
  exact hres

/-- Rejection with positive penalty strictly increases potential, hence cannot be used as
a descent step.
-/theorem reject_not_descent (S : State) (bad : Coord) {penalty : ℕ} (hpen : 0 < penalty) :
    ¬ Transition.StrictlyDecreases S
      { next := S.rejectWithPenalty bad penalty, flag := MoveFlag.rejected } := by
  intro hdec
  dsimp [Transition.StrictlyDecreases] at hdec
  rw [State.potential_rejectWithPenalty] at hdec
  exact Nat.not_lt.mpr (Nat.le_add_right _ _) hdec

end LawfulMove

/-- A lawful projection is an idempotent normalizer on states. -/
structure Projector where
  project : State → State
  idem : ∀ S, project (project S) = project S

namespace Projector

@[simp] theorem idem_apply (P : Projector) (S : State) : P.project (P.project S) = P.project S :=
  P.idem S

end Projector

/-- A grounding operator chooses a next state from a lawful candidate and an external
reality parameter.
-/structure Grounder (Reality : Type) where
  ground : State → Reality → State

/-- A more structured kernel than the minimal core: it explicitly tracks a projector,
a grounding map, and a chosen lawful transition policy.
-/structure KernelExtended (Reality : Type) where
  projector : Projector
  grounder : Grounder Reality
  terminal : State → Prop
  choose : State → Reality → Transition
  lawful_choose : ∀ S R, LawfulMove (projector.project S) (choose (projector.project S) R)
  strict_descent : ∀ S R,
    ¬ terminal (projector.project S) →
    Transition.StrictlyDecreases (projector.project S) (choose (projector.project S) R)
  grounded_step : State → Reality → State := fun S R =>
    (grounder.ground (choose (projector.project S) R).next R)

namespace KernelExtended

variable {Reality : Type} (K : KernelExtended Reality)

/-- On projected nonterminal states, the chosen transition strictly decreases the potential. -/
theorem chosen_transition_decreases (S : State) (R : Reality)
    (hS : ¬ K.terminal (K.projector.project S)) :
    Transition.StrictlyDecreases (K.projector.project S) (K.choose (K.projector.project S) R) :=
  K.strict_descent S R hS

/-- A projected nonterminal state cannot be a fixed point of the chosen transition. -/
theorem chosen_transition_not_fixed (S : State) (R : Reality)
    (hS : ¬ K.terminal (K.projector.project S)) :
    (K.choose (K.projector.project S) R).next ≠ K.projector.project S := by
  intro hfix
  have hlt := K.chosen_transition_decreases S R hS
  dsimp [Transition.StrictlyDecreases] at hlt
  rw [hfix] at hlt
  exact Nat.lt_irrefl _ hlt

end KernelExtended

-- ════════════════════════════════════════════════════════════
-- Verification Examples (AGENTS.md §4 requirement)
-- ════════════════════════════════════════════════════════════

#eval ({ k := 5, t := 3, ht := by omega : Coord }).mass
#eval ({ k := 5, t := 0, ht := by omega : Coord }).mass
#eval ({ k := 5, t := 3, ht := by omega : Coord }).mirror.mass = ({ k := 5, t := 3, ht := by omega : Coord }).mass
#eval ({ k := 5, t := 0, ht := by omega : Coord }).mirror.t
#eval isResonantPair { k := 3, t := 2, ht := by omega } { k := 3, t := 5, ht := by omega }
#eval phase { k := 10, t := 5, ht := by omega : Coord }

end PIST
