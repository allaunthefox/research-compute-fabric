import Semantics.RRCLogogramProjection

/-!
# ManifoldBoundaryAtlas

A ManifoldBoundaryAtlas is a deterministic seed-generated set of candidate
boundary coordinates for RRC-style projection checks.  It generalizes
`HexLogogramAtlas`: the seed does not claim a tear, proof, or manifold truth;
it generates a finite boundary candidate surface that RRC can identify against
receipts and residual evidence.

Promotion is byte-law gated.  If the boundary seed, law, residual, and receipt
do not beat an explicit boundary-coordinate table, the atlas remains a HOLD
surface.
-/

namespace Semantics.ManifoldBoundaryAtlas

/-- Finite laws for generating manifold boundary candidates. -/
inductive BoundaryLaw where
  | affineCut
  | genusInversion
  | massGradient
  | rrcProjectionEdge
  deriving Repr, DecidableEq

/-- A generated boundary candidate in a finite coordinate domain. -/
structure BoundaryCandidate where
  index : Nat
  coordinate : Nat
  side : Nat
  confidence : Nat
  deriving Repr, DecidableEq

/-- Seeded boundary-atlas packet. -/
structure BoundaryAtlasPacket where
  hexSeed : Nat
  hexDigitWidth : Nat
  blockBase : Nat
  law : BoundaryLaw
  dimensionCount : Nat
  coordinateDomain : Nat
  boundaryCount : Nat
  startIndex : Nat
  length : Nat
  stride : Nat
  genus : Nat
  massBasin : Nat
  torsionClass : Nat
  phaseClass : Nat
  explicitBoundaryBytes : Nat
  seedBytes : Nat
  lawBytes : Nat
  residualBytes : Nat
  receiptBytes : Nat
  rrcShapeOk : Bool
  residualDeclared : Bool
  deriving Repr, DecidableEq

/-- Hex block base for a fixed-width boundary seed. -/
def expectedHexBase (p : BoundaryAtlasPacket) : Nat :=
  16 ^ p.hexDigitWidth

/-- Structural gate before byte-law promotion. -/
def boundaryAtlasStructurallyValid (p : BoundaryAtlasPacket) : Bool :=
  p.hexDigitWidth > 0 &&
    p.blockBase == expectedHexBase p &&
    p.dimensionCount > 0 &&
    p.coordinateDomain > 0 &&
    p.boundaryCount > 0 &&
    p.length > 0 &&
    p.stride > 0 &&
    p.explicitBoundaryBytes > 0 &&
    p.rrcShapeOk &&
    p.residualDeclared

/-- Raw deterministic boundary value before projection into finite domains. -/
def boundaryRawValueAt (p : BoundaryAtlasPacket) (i : Nat) : Nat :=
  let j := p.startIndex + i
  match p.law with
  | BoundaryLaw.affineCut =>
      p.hexSeed + (j * p.stride) + p.phaseClass
  | BoundaryLaw.genusInversion =>
      p.hexSeed + (p.genus * p.dimensionCount) + (j * p.stride) + p.phaseClass
  | BoundaryLaw.massGradient =>
      p.hexSeed + (p.massBasin * p.stride) + j + p.torsionClass
  | BoundaryLaw.rrcProjectionEdge =>
      p.hexSeed + (j * p.stride) + p.massBasin + p.torsionClass + p.phaseClass

/-- Generate the i-th RRC boundary candidate. -/
def boundaryCandidateAt (p : BoundaryAtlasPacket) (i : Nat) : BoundaryCandidate :=
  let raw := boundaryRawValueAt p i
  { index := i
    coordinate := raw % p.coordinateDomain
    side := raw % p.boundaryCount
    confidence := (raw / p.boundaryCount) % p.dimensionCount }

/-- Replay the finite boundary atlas. -/
def replayBoundaryAtlas (p : BoundaryAtlasPacket) : List BoundaryCandidate :=
  (List.range p.length).map (boundaryCandidateAt p)

/-- Explicit table cost for boundary candidates. -/
def explicitBoundaryTableBytes (p : BoundaryAtlasPacket) : Nat :=
  p.length * p.explicitBoundaryBytes

/-- Encoded boundary-atlas cost with residual and receipt accounting. -/
def boundaryAtlasEncodedBytes (p : BoundaryAtlasPacket) : Nat :=
  p.seedBytes + p.lawBytes + p.residualBytes + p.receiptBytes

/-- The byte law: generated boundary candidates must beat explicit candidates. -/
def boundaryAtlasByteLawHolds (p : BoundaryAtlasPacket) : Bool :=
  boundaryAtlasEncodedBytes p < explicitBoundaryTableBytes p

/-- Promotion gate for a deterministic boundary atlas. -/
def boundaryAtlasPromotable (p : BoundaryAtlasPacket) : Bool :=
  boundaryAtlasStructurallyValid p && boundaryAtlasByteLawHolds p

/--
Boundary atlases feed RRC identification, not merge admission.  A promoted
boundary atlas gives candidate boundary evidence; actual tear projection still
needs the RRC receipt fields.
-/
def rrcBoundaryReceiptFromAtlas (p : BoundaryAtlasPacket) : Semantics.RRCLogogramProjection.LogogramReceipt :=
  { shape := Semantics.RRCLogogramProjection.RRCShape.logogramProjection
    status := Semantics.RRCLogogramProjection.WitnessStatus.candidate
    regime := Semantics.RRCLogogramProjection.SemanticRegime.horribleManifoldTearing
    payloadBound := p.rrcShapeOk
    contradictionWitness := false
    tearBoundary := boundaryAtlasPromotable p
    detachedMass := false
    residualLane := p.residualDeclared }

/-! ## Canonical witnesses -/

/-- Small hand-checkable boundary atlas. -/
def smallBoundaryAtlas : BoundaryAtlasPacket :=
  { hexSeed := 3
    hexDigitWidth := 2
    blockBase := 256
    law := BoundaryLaw.affineCut
    dimensionCount := 4
    coordinateDomain := 16
    boundaryCount := 4
    startIndex := 0
    length := 4
    stride := 2
    genus := 3
    massBasin := 1
    torsionClass := 0
    phaseClass := 1
    explicitBoundaryBytes := 2
    seedBytes := 1
    lawBytes := 1
    residualBytes := 0
    receiptBytes := 1
    rrcShapeOk := true
    residualDeclared := true }

/-- Compression-sized witness for an inverted-genus boundary surface. -/
def canonicalBoundaryAtlas : BoundaryAtlasPacket :=
  { hexSeed := 0xC0FFEE
    hexDigitWidth := 6
    blockBase := 16777216
    law := BoundaryLaw.genusInversion
    dimensionCount := 16
    coordinateDomain := 4096
    boundaryCount := 12
    startIndex := 0
    length := 96
    stride := 7
    genus := 3
    massBasin := 5
    torsionClass := 2
    phaseClass := 4
    explicitBoundaryBytes := 3
    seedBytes := 3
    lawBytes := 1
    residualBytes := 4
    receiptBytes := 2
    rrcShapeOk := true
    residualDeclared := true }

/-- Too short to beat explicit boundary coordinates. -/
def tinyBoundaryAtlas : BoundaryAtlasPacket :=
  { canonicalBoundaryAtlas with length := 2 }

/-- Bad coordinate domain: no finite manifold address space. -/
def badBoundaryDomainAtlas : BoundaryAtlasPacket :=
  { canonicalBoundaryAtlas with coordinateDomain := 0 }

/-- Missing residual declaration: cannot promote to RRC identification. -/
def missingResidualBoundaryAtlas : BoundaryAtlasPacket :=
  { canonicalBoundaryAtlas with residualDeclared := false }

theorem smallBoundaryReplay :
    replayBoundaryAtlas smallBoundaryAtlas =
      [{ index := 0, coordinate := 4, side := 0, confidence := 1 },
       { index := 1, coordinate := 6, side := 2, confidence := 1 },
       { index := 2, coordinate := 8, side := 0, confidence := 2 },
       { index := 3, coordinate := 10, side := 2, confidence := 2 }] := by
  native_decide

theorem canonicalBoundaryAtlasPromotable :
    boundaryAtlasPromotable canonicalBoundaryAtlas = true := by
  native_decide

theorem tinyBoundaryAtlasNotPromotable :
    boundaryAtlasPromotable tinyBoundaryAtlas = false := by
  native_decide

theorem badBoundaryDomainAtlasNotPromotable :
    boundaryAtlasPromotable badBoundaryDomainAtlas = false := by
  native_decide

theorem missingResidualBoundaryAtlasNotPromotable :
    boundaryAtlasPromotable missingResidualBoundaryAtlas = false := by
  native_decide

theorem promotedBoundaryAtlasStructurallyValid (p : BoundaryAtlasPacket) :
    boundaryAtlasPromotable p = true -> boundaryAtlasStructurallyValid p = true := by
  unfold boundaryAtlasPromotable
  intro h
  cases hStruct : boundaryAtlasStructurallyValid p
  · simp [hStruct] at h
  · simp

theorem promotedBoundaryAtlasSatisfiesByteLaw (p : BoundaryAtlasPacket) :
    boundaryAtlasPromotable p = true -> boundaryAtlasByteLawHolds p = true := by
  unfold boundaryAtlasPromotable
  intro h
  cases hStruct : boundaryAtlasStructurallyValid p
  · simp [hStruct] at h
  cases hBytes : boundaryAtlasByteLawHolds p
  · simp [hStruct, hBytes] at h
  · simp

/-- A promoted atlas contributes tear-boundary evidence to the RRC receipt. -/
theorem promotedBoundaryAtlasSetsRrcTearBoundary (p : BoundaryAtlasPacket) :
    boundaryAtlasPromotable p = true ->
      (rrcBoundaryReceiptFromAtlas p).tearBoundary = true := by
  intro h
  unfold rrcBoundaryReceiptFromAtlas
  simp [h]

/--
Boundary evidence alone is intentionally insufficient for projection admission:
contradiction and detached-mass evidence must still be supplied by later RRC
checks.
-/
theorem boundaryAtlasAloneDoesNotProject :
    Semantics.RRCLogogramProjection.projectionAdmissible
      (rrcBoundaryReceiptFromAtlas canonicalBoundaryAtlas) = false := by
  native_decide

#eval replayBoundaryAtlas smallBoundaryAtlas
#eval boundaryAtlasPromotable canonicalBoundaryAtlas
#eval boundaryAtlasPromotable tinyBoundaryAtlas
#eval boundaryAtlasPromotable badBoundaryDomainAtlas
#eval boundaryAtlasPromotable missingResidualBoundaryAtlas
#eval Semantics.RRCLogogramProjection.projectionAdmissible
  (rrcBoundaryReceiptFromAtlas canonicalBoundaryAtlas)

end Semantics.ManifoldBoundaryAtlas
