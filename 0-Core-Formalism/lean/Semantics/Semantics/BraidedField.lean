namespace Semantics.BraidedField

/-!
BraidedField.lean

Finite executable scaffold for a polaron-polariton braid-field candidate.

This file intentionally uses integer phase ticks and discrete energy witnesses.
It is a compileable semantics harness, not a proof that a physical material is
topologically protected.
-/

/-- Integer phase bucket. A later analytic layer can map this to exp(i theta). -/
abbrev PhaseTick := Int

/-- Tiny 2D position carrier for executable examples. -/
structure Position2 where
  x : Int
  y : Int
deriving Repr, DecidableEq, BEq

/-- A quasiparticle in the virtual braid-field scaffold. -/
inductive QuasiparticleKind where
  | photonLike
  | electronLike
  | phononLike
  | dressedCloud
deriving Repr, DecidableEq, BEq

structure Quasiparticle where
  position : Position2
  phase : PhaseTick
  kind : QuasiparticleKind
deriving Repr, DecidableEq, BEq

def defaultQuasiparticle : Quasiparticle :=
  { position := { x := 0, y := 0 }, phase := 0, kind := QuasiparticleKind.dressedCloud }

/-- A braiding operation swaps two lanes and applies a discrete phase shift. -/
structure Braiding where
  i : Nat
  j : Nat
  phaseShift : PhaseTick
deriving Repr, DecidableEq, BEq

/-- Discrete Hamiltonian witness for photon/electron/phonon/interaction terms. -/
structure Hamiltonian where
  photonEnergy : Int
  electronEnergy : Int
  phononEnergy : Int
  interactionEnergy : Int
deriving Repr, DecidableEq, BEq

namespace Hamiltonian

def total (H : Hamiltonian) : Int :=
  H.photonEnergy + H.electronEnergy + H.phononEnergy + H.interactionEnergy

end Hamiltonian

/-- A braided field state containing multiple quasiparticles. -/
structure FieldState where
  particles : List Quasiparticle
  braidingHistory : List Braiding
  hamiltonian : Hamiltonian
deriving Repr, DecidableEq, BEq

namespace FieldState

def validIndex (field : FieldState) (i : Nat) : Bool :=
  i < field.particles.length

def validBraiding (field : FieldState) (b : Braiding) : Bool :=
  field.validIndex b.i && field.validIndex b.j && b.i != b.j

/-- Safe swap with phase application; invalid braid requests leave the state unchanged. -/
def applyBraiding (field : FieldState) (b : Braiding) : FieldState :=
  if field.validBraiding b then
    let pi := field.particles.getD b.i defaultQuasiparticle
    let pj := field.particles.getD b.j defaultQuasiparticle
    let swapped :=
      field.particles.mapIdx (fun idx p =>
        if idx == b.i then
          { pj with phase := pj.phase + b.phaseShift }
        else if idx == b.j then
          { pi with phase := pi.phase + b.phaseShift }
        else
          p)
    { field with particles := swapped, braidingHistory := field.braidingHistory ++ [b] }
  else
    field

def topologicalInvariant (field : FieldState) : PhaseTick :=
  field.braidingHistory.foldl (fun acc b => acc + b.phaseShift) 0

def sameInvariant (f1 f2 : FieldState) : Bool :=
  f1.topologicalInvariant == f2.topologicalInvariant

end FieldState

/-- A discrete anyon statistics witness. -/
structure Anyon where
  position : Position2
  statisticsParameter : PhaseTick
  chargeTick : Int
deriving Repr, DecidableEq, BEq

namespace Anyon

/-- Phase shift bucket introduced by exchanging this anyon with another. -/
def braidPhase (a1 _a2 : Anyon) : PhaseTick :=
  a1.statisticsParameter

end Anyon

/-- A topological polaron-polariton candidate in the finite scaffold. -/
structure PolaronPolariton where
  photonComponent : Int
  electronComponent : Int
  phononComponent : Int
  position : Position2
  statisticsParameter : PhaseTick
deriving Repr, DecidableEq, BEq

namespace PolaronPolariton

def wavefunctionTick (pp : PolaronPolariton) : Int :=
  pp.photonComponent + pp.electronComponent + pp.phononComponent

def intAbs (x : Int) : Int :=
  if x < 0 then -x else x

/-- Effective mass in milli-units, renormalized by phonon contribution. -/
def effectiveMassMilli (pp : PolaronPolariton) : Int :=
  1000 + (intAbs pp.phononComponent) * 500

/-- Braiding applies the first particle statistics parameter to both components. -/
def braid (pp1 pp2 : PolaronPolariton) : PolaronPolariton × PolaronPolariton :=
  let θ := pp1.statisticsParameter
  let pp1' := { pp1 with
    photonComponent := pp1.photonComponent + θ,
    electronComponent := pp1.electronComponent + θ,
    phononComponent := pp1.phononComponent + θ }
  let pp2' := { pp2 with
    photonComponent := pp2.photonComponent + θ,
    electronComponent := pp2.electronComponent + θ,
    phononComponent := pp2.phononComponent + θ }
  (pp1', pp2')

end PolaronPolariton

/-- A topological field candidate with explicit finite witnesses. -/
structure TopologicalField where
  quasiparticles : List PolaronPolariton
  braidingOperations : List Braiding
  magneticFieldTick : Int
  spectralGapTick : Nat
  disorderTick : Nat
deriving Repr, DecidableEq, BEq

namespace TopologicalField

def totalPhase (field : TopologicalField) : PhaseTick :=
  field.braidingOperations.foldl (fun acc b => acc + b.phaseShift) 0

/--
Candidate topological protection predicate.

This is deliberately phrased as a candidate gate:
nonzero braid invariant, positive magnetic field witness, and gap above disorder.
-/
def isProtectionCandidate (field : TopologicalField) : Bool :=
  field.totalPhase != 0 &&
  field.magneticFieldTick > 0 &&
  field.spectralGapTick > field.disorderTick

end TopologicalField

def sampleHamiltonian : Hamiltonian :=
  { photonEnergy := 1000, electronEnergy := 500, phononEnergy := 300, interactionEnergy := 200 }

def sampleField : FieldState :=
  { particles := [
      { position := { x := 0, y := 0 }, phase := 0, kind := QuasiparticleKind.photonLike },
      { position := { x := 1, y := 0 }, phase := 0, kind := QuasiparticleKind.electronLike },
      { position := { x := 0, y := 1 }, phase := 0, kind := QuasiparticleKind.phononLike }
    ],
    braidingHistory := [],
    hamiltonian := sampleHamiltonian }

def sampleBraids : List Braiding :=
  [
    { i := 0, j := 1, phaseShift := 1571 },
    { i := 1, j := 2, phaseShift := 1047 },
    { i := 0, j := 2, phaseShift := 785 }
  ]

def sampleBraidedField : FieldState :=
  sampleBraids.foldl (fun state braid => state.applyBraiding braid) sampleField

def sampleTopologicalField : TopologicalField :=
  { quasiparticles := [
      { photonComponent := 1, electronComponent := 1, phononComponent := 1,
        position := { x := 0, y := 0 }, statisticsParameter := 785 },
      { photonComponent := 1, electronComponent := 1, phononComponent := 1,
        position := { x := 1, y := 0 }, statisticsParameter := 785 }
    ],
    braidingOperations := sampleBraids,
    magneticFieldTick := 1000,
    spectralGapTick := 181,
    disorderTick := 13 }

def gapCollapseField : TopologicalField :=
  { sampleTopologicalField with spectralGapTick := 17, disorderTick := 52 }

theorem sample_braiding_history_len : sampleBraidedField.braidingHistory.length = 3 := by
  native_decide

theorem sample_invariant_tick : sampleBraidedField.topologicalInvariant = 3403 := by
  native_decide

theorem sample_candidate_protected : sampleTopologicalField.isProtectionCandidate = true := by
  native_decide

theorem gap_collapse_not_candidate : gapCollapseField.isProtectionCandidate = false := by
  native_decide

#eval sampleBraidedField.topologicalInvariant
#eval sampleTopologicalField.isProtectionCandidate
#eval gapCollapseField.isProtectionCandidate

end Semantics.BraidedField
