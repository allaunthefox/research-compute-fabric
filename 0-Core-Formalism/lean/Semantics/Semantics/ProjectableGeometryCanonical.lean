import Mathlib.Data.Nat.Basic

namespace Semantics.ProjectableGeometryCanonical

/-!
# Projectable Geometry Canonical Representation

This module records the current canonical representation for the projectable
geometry compressor:

* signed 16-axis envelope,
* 12D source/residual plane,
* 4D primitive keel,
* genus-3 residual boat,
* 0D closure witness.

It is an accounting gate for reversible compression representations, not a
physics claim.
-/

/-- The canonical dimensional axis counts for the current representation. -/
def signedEnvelopeAxes : Nat := 16
def sourcePlaneAxes : Nat := 12
def primitiveKeelAxes : Nat := 4
def genusHandles : Nat := 3
def closurePointAxes : Nat := 0

/--
The decision-diagram shell mass is represented in twelfths to avoid Float or
open-ended rational parsing in the core.
-/
structure DimensionalShell where
  visible4d : Nat
  shadow3d : Nat
  closure0d : Nat
  lawbound : Nat
  unresolved : Nat
  total : Nat
  deriving Repr, DecidableEq

/-- Canonical dimensional shell: 4/12 visible, 3/12 shadow, 1/12 closure, 4/12 lawbound. -/
def canonicalShell : DimensionalShell :=
  { visible4d := 4
    shadow3d := 3
    closure0d := 1
    lawbound := 4
    unresolved := 0
    total := 12 }

/-- The shell closes when all named mass accounts sum to the declared total with no unresolved debt. -/
def shellCloses (s : DimensionalShell) : Bool :=
  s.visible4d + s.shadow3d + s.closure0d + s.lawbound + s.unresolved == s.total &&
    s.unresolved == 0

/-- Three-handle genus-3 carrier for a 12D residual lane. -/
structure Genus3ResidualBoat where
  packetLocal : Nat
  shearTorsion : Nat
  spectralField : Nat
  residual12d : Nat
  deriving Repr, DecidableEq

/-- The residual boat closes when its three handles exactly reconstruct the residual lane. -/
def residualBoatCloses (boat : Genus3ResidualBoat) : Bool :=
  boat.packetLocal + boat.shearTorsion + boat.spectralField == boat.residual12d

/-- Canonical projectable geometry representation packet. -/
structure CanonicalProjectableRep where
  signedAxes : Nat
  sourceAxes : Nat
  primitiveAxes : Nat
  genusHandleCount : Nat
  closureAxes : Nat
  source12dMass : Nat
  lifted4dMass : Nat
  residual12dMass : Nat
  shell : DimensionalShell
  boat : Genus3ResidualBoat
  sourceHashPresent : Bool
  receiptHashPresent : Bool
  deriving Repr, DecidableEq

/-- Source rehydration law: lifted 4D projection plus residual lane equals source mass. -/
def sourceRehydrates (rep : CanonicalProjectableRep) : Bool :=
  rep.lifted4dMass + rep.residual12dMass == rep.source12dMass

/-- Axis counts match the 16D -> 12D -> 4D -> genus-3 -> 0D canonical representation. -/
def axesCanonical (rep : CanonicalProjectableRep) : Bool :=
  rep.signedAxes == signedEnvelopeAxes &&
    rep.sourceAxes == sourcePlaneAxes &&
    rep.primitiveAxes == primitiveKeelAxes &&
    rep.genusHandleCount == genusHandles &&
    rep.closureAxes == closurePointAxes

/-- Full promotion gate for the canonical representation. -/
def canonicalRepAdmissible (rep : CanonicalProjectableRep) : Bool :=
  axesCanonical rep &&
    shellCloses rep.shell &&
    residualBoatCloses rep.boat &&
    sourceRehydrates rep &&
    rep.boat.residual12d == rep.residual12dMass &&
    rep.sourceHashPresent &&
    rep.receiptHashPresent

/-- A small closed witness: source mass 12, lifted mass 7, residual mass 5. -/
def sampleClosedRep : CanonicalProjectableRep :=
  { signedAxes := 16
    sourceAxes := 12
    primitiveAxes := 4
    genusHandleCount := 3
    closureAxes := 0
    source12dMass := 12
    lifted4dMass := 7
    residual12dMass := 5
    shell := canonicalShell
    boat := { packetLocal := 2, shearTorsion := 2, spectralField := 1, residual12d := 5 }
    sourceHashPresent := true
    receiptHashPresent := true }

/-- Negative witness: residual handles do not reconstruct the 12D residual lane. -/
def brokenResidualRep : CanonicalProjectableRep :=
  { sampleClosedRep with
    boat := { packetLocal := 2, shearTorsion := 2, spectralField := 0, residual12d := 5 } }

/-- Negative witness: an unresolved shell debt prevents closure. -/
def unresolvedShellRep : CanonicalProjectableRep :=
  { sampleClosedRep with
    shell := { canonicalShell with unresolved := 1, total := 13 } }

theorem canonicalShellCloses : shellCloses canonicalShell = true := by
  rfl

theorem sampleClosedRepAdmissible : canonicalRepAdmissible sampleClosedRep = true := by
  rfl

theorem brokenResidualRepNotAdmissible : canonicalRepAdmissible brokenResidualRep = false := by
  rfl

theorem unresolvedShellRepNotAdmissible : canonicalRepAdmissible unresolvedShellRep = false := by
  rfl

#eval canonicalRepAdmissible sampleClosedRep
#eval canonicalRepAdmissible brokenResidualRep
#eval canonicalRepAdmissible unresolvedShellRep

end Semantics.ProjectableGeometryCanonical
