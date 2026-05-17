/-!
# HexLogogramAtlas

A HexLogogramAtlas is a deterministic seed-generated map from typed token or
Mass Number coordinates into reusable logogram groups.  It is the logogram
grouping layer above `LadderLUT`: the hex seed does not store the words or
glyphs; it stores the replayable grouping law that chooses a logogram group.

Promotion is byte-law gated.  If the seed, law, registry reference, residual,
and receipt do not beat an explicit token-to-logogram assignment table, the
atlas remains an inspection surface rather than a compression representative.
-/

namespace Semantics.HexLogogramAtlas

/-- Finite grouping laws for a hex-seeded logogram atlas. -/
inductive HexGroupingLaw where
  | atlasIdentity
  | affineMass
  | windowedMass
  | stridedChart
  deriving Repr, DecidableEq

/-- A deterministic hex-seeded logogram grouping packet. -/
structure HexLogogramPacket where
  hexSeed : Nat
  hexDigitWidth : Nat
  blockBase : Nat
  law : HexGroupingLaw
  registryId : Nat
  massBasin : Nat
  massWeight : Nat
  chartId : Nat
  typeWitness : Nat
  groupCount : Nat
  tokenDomain : Nat
  startIndex : Nat
  length : Nat
  stride : Nat
  window : Nat
  assignmentBytes : Nat
  seedBytes : Nat
  lawBytes : Nat
  registryBytes : Nat
  residualBytes : Nat
  receiptBytes : Nat
  deriving Repr, DecidableEq

/-- Hex block base for a fixed number of hexadecimal digits. -/
def expectedHexBase (p : HexLogogramPacket) : Nat :=
  16 ^ p.hexDigitWidth

/-- Structural gate before byte-law promotion. -/
def atlasStructurallyValid (p : HexLogogramPacket) : Bool :=
  p.hexDigitWidth > 0 &&
    p.blockBase == expectedHexBase p &&
    p.registryId > 0 &&
    p.groupCount > 0 &&
    p.tokenDomain > 0 &&
    p.length > 0 &&
    p.stride > 0 &&
    p.window > 0 &&
    p.assignmentBytes > 0

/-- Unreduced law value before projection into the finite logogram group set. -/
def atlasRawValueAt (p : HexLogogramPacket) (i : Nat) : Nat :=
  let j := p.startIndex + i
  match p.law with
  | HexGroupingLaw.atlasIdentity =>
      p.hexSeed + j
  | HexGroupingLaw.affineMass =>
      p.hexSeed + (p.massBasin * p.massWeight) + (j * p.stride) + p.typeWitness
  | HexGroupingLaw.windowedMass =>
      p.hexSeed + (j / p.window) + p.massBasin + p.typeWitness
  | HexGroupingLaw.stridedChart =>
      p.hexSeed + (j * p.stride) + p.chartId

/-- Generated logogram group ID for the i-th token coordinate. -/
def atlasGroupAt (p : HexLogogramPacket) (i : Nat) : Nat :=
  atlasRawValueAt p i % p.groupCount

/-- Replay the finite atlas as generated logogram group IDs. -/
def replayAtlasGroups (p : HexLogogramPacket) : List Nat :=
  (List.range p.length).map (atlasGroupAt p)

/-- Explicit assignment-table cost. -/
def explicitAtlasBytes (p : HexLogogramPacket) : Nat :=
  p.length * p.assignmentBytes

/-- Seeded-atlas representative cost with residual and receipt accounting. -/
def atlasEncodedBytes (p : HexLogogramPacket) : Nat :=
  p.seedBytes + p.lawBytes + p.registryBytes + p.residualBytes + p.receiptBytes

/-- The byte law: the generated atlas must beat an explicit assignment table. -/
def atlasByteLawHolds (p : HexLogogramPacket) : Bool :=
  atlasEncodedBytes p < explicitAtlasBytes p

/-- Promotion gate for a deterministic HexLogogramAtlas route. -/
def atlasPromotable (p : HexLogogramPacket) : Bool :=
  atlasStructurallyValid p && atlasByteLawHolds p

/-! ## Canonical witnesses -/

/-- Small witness with hand-checkable replay groups. -/
def smallAffineAtlas : HexLogogramPacket :=
  { hexSeed := 10
    hexDigitWidth := 2
    blockBase := 256
    law := HexGroupingLaw.affineMass
    registryId := 1
    massBasin := 2
    massWeight := 3
    chartId := 0
    typeWitness := 1
    groupCount := 8
    tokenDomain := 16
    startIndex := 0
    length := 4
    stride := 1
    window := 1
    assignmentBytes := 2
    seedBytes := 1
    lawBytes := 1
    registryBytes := 1
    residualBytes := 0
    receiptBytes := 1 }

/-- Compression-sized witness: one 32-bit hex seed groups a 64-token window. -/
def canonicalHexAtlas : HexLogogramPacket :=
  { hexSeed := 0xA7F3C91B
    hexDigitWidth := 8
    blockBase := 4294967296
    law := HexGroupingLaw.affineMass
    registryId := 7
    massBasin := 3
    massWeight := 17
    chartId := 4
    typeWitness := 2
    groupCount := 64
    tokenDomain := 4096
    startIndex := 0
    length := 64
    stride := 5
    window := 8
    assignmentBytes := 2
    seedBytes := 4
    lawBytes := 1
    registryBytes := 1
    residualBytes := 2
    receiptBytes := 2 }

/-- Too short to amortize the seed/law/receipt route. -/
def tinyHexAtlas : HexLogogramPacket :=
  { canonicalHexAtlas with length := 2 }

/-- Bad base declaration: `blockBase` does not match 16^hexDigitWidth. -/
def badHexBaseAtlas : HexLogogramPacket :=
  { canonicalHexAtlas with blockBase := 255 }

/-- Bad group declaration: no finite logogram groups exist. -/
def badGroupAtlas : HexLogogramPacket :=
  { canonicalHexAtlas with groupCount := 0 }

theorem smallAffineReplayGroups :
    replayAtlasGroups smallAffineAtlas = [1, 2, 3, 4] := by
  native_decide

theorem canonicalHexAtlasPromotable :
    atlasPromotable canonicalHexAtlas = true := by
  native_decide

theorem tinyHexAtlasNotPromotable :
    atlasPromotable tinyHexAtlas = false := by
  native_decide

theorem badHexBaseAtlasNotPromotable :
    atlasPromotable badHexBaseAtlas = false := by
  native_decide

theorem badGroupAtlasNotPromotable :
    atlasPromotable badGroupAtlas = false := by
  native_decide

/-- Any promoted atlas has a valid structure. -/
theorem promotableAtlasStructurallyValid (p : HexLogogramPacket) :
    atlasPromotable p = true -> atlasStructurallyValid p = true := by
  unfold atlasPromotable
  intro h
  cases hStruct : atlasStructurallyValid p
  · simp [hStruct] at h
  · simp

/-- Any promoted atlas satisfies the assignment-table byte law. -/
theorem promotableAtlasSatisfiesByteLaw (p : HexLogogramPacket) :
    atlasPromotable p = true -> atlasByteLawHolds p = true := by
  unfold atlasPromotable
  intro h
  cases hStruct : atlasStructurallyValid p
  · simp [hStruct] at h
  cases hBytes : atlasByteLawHolds p
  · simp [hStruct, hBytes] at h
  · simp

#eval replayAtlasGroups smallAffineAtlas
#eval atlasPromotable canonicalHexAtlas
#eval atlasPromotable tinyHexAtlas
#eval atlasPromotable badHexBaseAtlas
#eval atlasPromotable badGroupAtlas

end Semantics.HexLogogramAtlas
