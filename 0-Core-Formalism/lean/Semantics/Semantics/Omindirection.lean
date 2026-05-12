/-!
# Omindirection Logogram Contract

This module turns the repo-local omindirection design into executable Lean
rules. It formalizes the implicit contract currently spread across:

* `6-Documentation/reports/typst/omindirection.typ`
* `6-Documentation/tiddlywiki-local/wiki/tiddlers/Typst Omindirection Plugin Surface.tid`
* `6-Documentation/tiddlywiki-local/wiki/tiddlers/Epigenetic Go-Tile Meta-Manifold.tid`

Omindirection is stricter than bidi prose flow: every logogram atom carries
explicit direction, chirality, phase, tone, placement, and receipt metadata.
-/

namespace Semantics.Omindirection

/-! ## Atom fields -/

/-- Explicit atom flow direction. `auto` is allowed only before promotion. -/
inductive Direction where
  | ltr
  | rtl
  | auto
  deriving DecidableEq, Repr

/-- Chiral class exposed by the Typst omindirection surface. -/
inductive Chirality where
  | left
  | right
  | ambidextrous
  | none
  deriving DecidableEq, Repr

/-- Tone/status classes used by the visual layer. -/
inductive Tone where
  | witness
  | unknown
  | boundary
  | residual
  | growth
  | neutral
  deriving DecidableEq, Repr

/-- Placement mode for a logogram atom. -/
inductive PlacementKind where
  | row
  | mirrorLeft
  | mirrorRight
  | board
  | quarantine
  deriving DecidableEq, Repr

/-- Admission state for a placed atom. -/
inductive AtomDecision where
  | accept
  | hold
  | quarantine
  deriving DecidableEq, Repr

/-- Phase is stored as a raw degree; admission checks the 0..359 bound. -/
abbrev PhaseDegree := Nat

/-- Chirality prefix emitted by the current Typst surface. -/
def chiralityPrefix (c : Chirality) : String :=
  match c with
  | Chirality.left => "L:"
  | Chirality.right => "R:"
  | Chirality.ambidextrous => "LR:"
  | Chirality.none => ""

/-- Phase must be a cyclic degree in Z/360Z. -/
def validPhase (phase : PhaseDegree) : Bool :=
  phase < 360

/-- Left/right are coarse projections over the durable phase orbit. -/
def chiralityCompatibleWithPhase (c : Chirality) (phase : PhaseDegree) : Bool :=
  validPhase phase &&
  match c with
  | Chirality.none => phase == 0
  | Chirality.left => phase < 180
  | Chirality.right => 180 <= phase
  | Chirality.ambidextrous => true

/-- Promoted atoms must not rely on hidden paragraph-direction inference. -/
def explicitDirection (d : Direction) : Bool :=
  d != Direction.auto

/-! ## Position and board-state fields -/

/-- Integer tile coordinate for board or row placement. -/
structure TileCoord where
  x : Int
  y : Int
  deriving Repr, DecidableEq

/-- Receipt metadata required to trust a placed atom. -/
structure AtomReceipt where
  sourceHash : String
  payloadHash : String
  receiptHash : String
  sourceHashDeclared : Bool
  payloadHashDeclared : Bool
  receiptHashDeclared : Bool
  deriving Repr

/-- One placed omindirectional logogram atom. -/
structure OmiAtom where
  payloadHash : String
  direction : Direction
  chirality : Chirality
  phase : PhaseDegree
  tone : Tone
  placement : PlacementKind
  coord : TileCoord
  torsion : Int
  temporal : Nat
  roundingDeclared : Bool
  residualDeclared : Bool
  languageForced : Bool
  liberties : Nat
  capturedBy : Option String
  territoryId : Option String
  receipt : AtomReceipt
  decision : AtomDecision
  deriving Repr

/-- Receipt fields are declared and internally point at the same payload hash. -/
def receiptComplete (a : OmiAtom) : Bool :=
  a.receipt.sourceHashDeclared &&
  a.receipt.payloadHashDeclared &&
  a.receipt.receiptHashDeclared &&
  a.receipt.payloadHash == a.payloadHash &&
  a.receipt.sourceHash != "" &&
  a.receipt.payloadHash != "" &&
  a.receipt.receiptHash != ""

/-- A board placement is a true tile move and needs at least one liberty unless captured. -/
def boardPlacementAdmissible (a : OmiAtom) : Bool :=
  if a.placement == PlacementKind.board then
    a.liberties > 0 || a.capturedBy.isSome
  else
    true

/-- Mirrored lanes require the corresponding coarse chirality. -/
def mirrorPlacementAdmissible (a : OmiAtom) : Bool :=
  if a.placement == PlacementKind.mirrorLeft then
    a.chirality == Chirality.left || a.chirality == Chirality.ambidextrous
  else if a.placement == PlacementKind.mirrorRight then
    a.chirality == Chirality.right || a.chirality == Chirality.ambidextrous
  else
    true

/-- Quarantine placement is reserved for quarantine decisions. -/
def quarantinePlacementAdmissible (a : OmiAtom) : Bool :=
  if a.placement == PlacementKind.quarantine then
    a.decision == AtomDecision.quarantine
  else
    a.decision != AtomDecision.quarantine

/-- Full omindirectional atom admission. -/
def atomAdmissible (a : OmiAtom) : Bool :=
  explicitDirection a.direction &&
  chiralityCompatibleWithPhase a.chirality a.phase &&
  receiptComplete a &&
  boardPlacementAdmissible a &&
  mirrorPlacementAdmissible a &&
  quarantinePlacementAdmissible a &&
  a.decision == AtomDecision.accept

/-- A held atom is explicit and receipted but not promotable yet. -/
def atomHeld (a : OmiAtom) : Bool :=
  explicitDirection a.direction &&
  receiptComplete a &&
  a.decision == AtomDecision.hold

/-- A quarantined atom is explicit, receipted, and placed in the quarantine lane. -/
def atomQuarantined (a : OmiAtom) : Bool :=
  explicitDirection a.direction &&
  receiptComplete a &&
  a.placement == PlacementKind.quarantine &&
  a.decision == AtomDecision.quarantine

/-! ## Canonical examples and witnesses -/

def exampleReceipt : AtomReceipt :=
  { sourceHash := "source"
    payloadHash := "payload"
    receiptHash := "receipt"
    sourceHashDeclared := true
    payloadHashDeclared := true
    receiptHashDeclared := true }

def rowWitnessAtom : OmiAtom :=
  { payloadHash := "payload"
    direction := Direction.ltr
    chirality := Chirality.ambidextrous
    phase := 90
    tone := Tone.witness
    placement := PlacementKind.row
    coord := { x := 0, y := 0 }
    torsion := 0
    temporal := 0
    roundingDeclared := false
    residualDeclared := false
    languageForced := false
    liberties := 0
    capturedBy := none
    territoryId := some "row-0"
    receipt := exampleReceipt
    decision := AtomDecision.accept }

def autoDirectionAtom : OmiAtom :=
  { rowWitnessAtom with direction := Direction.auto }

def unreceiptedAtom : OmiAtom :=
  { rowWitnessAtom with
    receipt := { exampleReceipt with receiptHashDeclared := false } }

def mirrorRightAtom : OmiAtom :=
  { rowWitnessAtom with
    direction := Direction.rtl
    chirality := Chirality.right
    phase := 270
    placement := PlacementKind.mirrorRight
    coord := { x := 1, y := 0 } }

def badMirrorAtom : OmiAtom :=
  { mirrorRightAtom with chirality := Chirality.left, phase := 90 }

def boardTileAtom : OmiAtom :=
  { rowWitnessAtom with
    placement := PlacementKind.board
    coord := { x := 2, y := 3 }
    liberties := 2
    territoryId := some "territory-a" }

def capturedBoardAtom : OmiAtom :=
  { boardTileAtom with
    liberties := 0
    capturedBy := some "contradiction-cluster"
    tone := Tone.residual }

def deadBoardAtom : OmiAtom :=
  { boardTileAtom with
    liberties := 0
    capturedBy := none }

def quarantineAtom : OmiAtom :=
  { rowWitnessAtom with
    placement := PlacementKind.quarantine
    decision := AtomDecision.quarantine
    tone := Tone.residual }

theorem chirality_prefixes_match_typst_surface :
    chiralityPrefix Chirality.left = "L:" ∧
    chiralityPrefix Chirality.right = "R:" ∧
    chiralityPrefix Chirality.ambidextrous = "LR:" ∧
    chiralityPrefix Chirality.none = "" := by
  native_decide

theorem row_witness_atom_admissible :
    atomAdmissible rowWitnessAtom = true := by
  native_decide

theorem auto_direction_atom_not_admissible :
    atomAdmissible autoDirectionAtom = false := by
  native_decide

theorem unreceipted_atom_not_admissible :
    atomAdmissible unreceiptedAtom = false := by
  native_decide

theorem mirror_right_atom_admissible :
    atomAdmissible mirrorRightAtom = true := by
  native_decide

theorem bad_mirror_atom_not_admissible :
    atomAdmissible badMirrorAtom = false := by
  native_decide

theorem board_tile_atom_admissible :
    atomAdmissible boardTileAtom = true := by
  native_decide

theorem captured_board_atom_admissible :
    atomAdmissible capturedBoardAtom = true := by
  native_decide

theorem dead_board_atom_not_admissible :
    atomAdmissible deadBoardAtom = false := by
  native_decide

theorem quarantine_atom_routes_to_quarantine_not_accept :
    atomAdmissible quarantineAtom = false ∧ atomQuarantined quarantineAtom = true := by
  native_decide

/-- Every admitted atom has explicit direction. -/
theorem admissible_atom_has_explicit_direction (a : OmiAtom) :
    atomAdmissible a = true -> explicitDirection a.direction = true := by
  unfold atomAdmissible
  intro h
  cases hDir : explicitDirection a.direction
  · simp [hDir] at h
  · simp

/-- Every admitted atom has complete receipt evidence. -/
theorem admissible_atom_has_receipt (a : OmiAtom) :
    atomAdmissible a = true -> receiptComplete a = true := by
  unfold atomAdmissible
  intro h
  cases hDir : explicitDirection a.direction
  · simp [hDir] at h
  cases hPhase : chiralityCompatibleWithPhase a.chirality a.phase
  · simp [hDir, hPhase] at h
  cases hReceipt : receiptComplete a
  · simp [hDir, hPhase, hReceipt] at h
  · simp

#eval atomAdmissible rowWitnessAtom
#eval atomAdmissible autoDirectionAtom
#eval atomAdmissible mirrorRightAtom
#eval atomAdmissible deadBoardAtom
#eval atomQuarantined quarantineAtom

end Semantics.Omindirection
