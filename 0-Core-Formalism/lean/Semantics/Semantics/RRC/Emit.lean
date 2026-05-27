-- Semantics.RRC.Emit — Goal A+: fixture corpus → alignment gate → JSON
--
-- This module ports the core decision logic of rrc_pist_shape_alignment.py
-- into Lean. It is the first step toward a Lean-only RRC compiler that can
-- replace shim-space Python for all admissibility and routing decisions.
--
-- Shim contract (mirrors rrc_pist_shape_alignment.py §TODO(lean-port)):
--   - promotion is always not_promoted at this stage
--   - all alignment/gating decisions happen in Lean, not in Python
--   - output is a JSON string that the Python harness can validate
--   - claim boundary: admissibility + routing pass only; not a proof of
--     the underlying mathematics

import Semantics.RRCLogogramProjection
import Semantics.ReceiptCore

namespace Semantics.RRC.Emit

open Semantics.RRCLogogramProjection
open Semantics.ReceiptCore

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  Alignment status (mirrors ALIGNMENT_SCORES in rrc_pist_shape_alignment.py)
-- ─────────────────────────────────────────────────────────────────────────────

/-- Alignment status between PIST structural label and RRC semantic routing shape.

  Scores (Q16_16-compatible integer encoding, denominator = 100):
  - aligned_exact:                   100  (exact PIST label == RRC shape)
  - aligned_proxy:                    86  (proxy PIST label == RRC shape)
  - compatible_structural_projection: 72  (PIST sees logogram morphology, RRC routes semantically)
  - alignment_warning:                35  (mismatch, no known compatibility)
  - missing_prediction:                0  (no PIST label present)
-/
inductive AlignmentStatus where
  | alignedExact                  -- score 100
  | alignedProxy                  -- score 86
  | compatibleStructuralProjection -- score 72
  | alignmentWarning              -- score 35
  | missingPrediction             -- score 0
  deriving DecidableEq, Repr

def alignmentScore : AlignmentStatus → Nat
  | .alignedExact                   => 100
  | .alignedProxy                   => 86
  | .compatibleStructuralProjection => 72
  | .alignmentWarning               => 35
  | .missingPrediction              => 0

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  Promotion status (always not_promoted at this stage)
-- ─────────────────────────────────────────────────────────────────────────────

inductive Promotion where
  | notPromoted
  | candidate
  deriving DecidableEq, Repr

-- ─────────────────────────────────────────────────────────────────────────────
-- §3  Fixture row (one compiled equation record)
-- ─────────────────────────────────────────────────────────────────────────────

/-- A single RRC equation fixture row.

  Fields match the invariant_receipt + equation_record structure from
  rrc_equation_classifier_receipt.json:
  - equationId:  "rrc_eq_<hex>" stable object identifier
  - name:        human-readable equation name
  - shape:       RRC routing shape (from RRCLogogramProjection.RRCShape)
  - status:      witness status (candidate or hold)
  - rrcKind:     classifier receipt kind tag
  - weakAxesCnt: count of weak (missing) projection axes — proxy for receipt_density gap
  - pistProxyLabel:  PIST proxy classifier output (if any)
  - pistExactLabel:  PIST exact classifier output (if any)
-/
structure FixtureRow where
  equationId     : String
  name           : String
  shape          : RRCShape
  status         : WitnessStatus
  rrcKind        : String
  weakAxesCnt    : Nat
  pistProxyLabel : Option String   -- None when PIST has no prediction
  pistExactLabel : Option String
  deriving Repr

-- ─────────────────────────────────────────────────────────────────────────────
-- §4  Alignment gate (ports determine_alignment from the shim)
-- ─────────────────────────────────────────────────────────────────────────────

/-- Shapes that PIST treats as structural/logogram morphology.
    Maps to COMPATIBLE_STRUCTURAL_LABELS in the Python shim. -/
def pistStructuralLabels : List String :=
  ["LogogramProjection", "logogram_projection",
   "ProjectableGeometryTopology", "projectable_geometry_topology"]

/-- RRC shapes that route semantically (not pure structural projection).
    Maps to RRC_SEMANTIC_SHAPES in the Python shim. -/
def rrcSemanticShapes : List RRCShape :=
  [ RRCShape.cognitiveLoadField
  , RRCShape.signalShapedRouteCompiler
  , RRCShape.cadForceProbeReceipt
  , RRCShape.holdForUnlawfulOrUnderspecifiedShape ]

private def shapeStr : RRCShape → String
  | .signalShapedRouteCompiler          => "SignalShapedRouteCompiler"
  | .projectableGeometryTopology        => "ProjectableGeometryTopology"
  | .cognitiveLoadField                 => "CognitiveLoadField"
  | .cadForceProbeReceipt               => "CadForceProbeReceipt"
  | .logogramProjection                 => "LogogramProjection"
  | .holdForUnlawfulOrUnderspecifiedShape => "HoldForUnlawfulOrUnderspecifiedShape"

/-- Determine alignment status for a fixture row.
    Logic is a faithful port of rrc_pist_shape_alignment.determine_alignment. -/
def determineAlignment (row : FixtureRow) : AlignmentStatus :=
  let rrcStr   := shapeStr row.shape
  let hasProxy := row.pistProxyLabel.isSome
  let hasExact := row.pistExactLabel.isSome
  if !hasProxy && !hasExact then
    .missingPrediction
  else if row.pistExactLabel == some rrcStr then
    .alignedExact
  else if row.pistProxyLabel == some rrcStr then
    .alignedProxy
  else
    let proxyIsStructural := row.pistProxyLabel.any (pistStructuralLabels.elem ·)
    let exactIsStructural := row.pistExactLabel.any (pistStructuralLabels.elem ·)
    let rrcIsSemantic     := rrcSemanticShapes.elem row.shape
    if (proxyIsStructural || exactIsStructural) && rrcIsSemantic then
      .compatibleStructuralProjection
    else
      .alignmentWarning

/-- Derive warnings from alignment status.
    Ports rewrite_warnings from the Python shim. -/
def alignmentWarnings (status : AlignmentStatus) : List String :=
  match status with
  | .missingPrediction              => ["missing_pist_prediction"]
  | .alignmentWarning               => ["pist_shape_alignment_warning"]
  | .compatibleStructuralProjection => []
  | .alignedProxy                   => []
  | .alignedExact                   => []

-- ─────────────────────────────────────────────────────────────────────────────
-- §5  RRC row output (what the compiler emits per equation)
-- ─────────────────────────────────────────────────────────────────────────────

structure RrcRow where
  equationId       : String
  name             : String
  shape            : RRCShape
  status           : WitnessStatus
  alignmentStatus  : AlignmentStatus
  alignmentScore   : Nat           -- integer, denominator 100
  promotion        : Promotion
  warnings         : List String
  receipt          : Receipt
  deriving Repr

def compileRow (row : FixtureRow) : RrcRow :=
  let aStatus  := determineAlignment row
  let aScore   := alignmentScore aStatus
  let warnings := alignmentWarnings aStatus
  let passed   := aStatus != .missingPrediction && aStatus != .alignmentWarning
  let receipt  := leanBuildReceipt row.equationId passed
  { equationId      := row.equationId
    name            := row.name
    shape           := row.shape
    status          := row.status
    alignmentStatus := aStatus
    alignmentScore  := aScore
    promotion       := .notPromoted
    warnings        := warnings
    receipt         := receipt }

-- ─────────────────────────────────────────────────────────────────────────────
-- §6  Fixture corpus — 6 canonical rows, one per RRCShape
--
--     Source: rrc_equation_classifier_receipt.json (278 equations)
--     Selection: first CANDIDATE per shape; HOLD where no CANDIDATE exists.
--     PIST labels: from rrc_pist_exact_validation.json (24 real predictions).
--     NOTE: the PIST classifier currently predicts "LogogramProjection" for all
--     rows — exact_accuracy = 0.0 against CognitiveLoadField / SignalShapedRC.
--     These labels are left as-is so the Lean gate faithfully reflects the
--     current shim-reported alignment state.
-- ─────────────────────────────────────────────────────────────────────────────

/-- CognitiveLoadField — CANDIDATE, proxy=LogogramProjection (PIST mismatch) -/
def fixtureClf : FixtureRow :=
  { equationId     := "rrc_eq_86ccde7bfd669b77"
    name           := "bandwidth_adjusted_threshold"
    shape          := .cognitiveLoadField
    status         := .candidate
    rrcKind        := "cognitive_field_receipt"
    weakAxesCnt    := 7
    pistProxyLabel := some "LogogramProjection"
    pistExactLabel := some "LogogramProjection" }

/-- SignalShapedRouteCompiler — CANDIDATE, proxy=LogogramProjection (PIST mismatch) -/
def fixtureSsrc : FixtureRow :=
  { equationId     := "rrc_eq_ac1a7a22801b7d77"
    name           := "core_equations"
    shape          := .signalShapedRouteCompiler
    status         := .candidate
    rrcKind        := "compression_route_prior"
    weakAxesCnt    := 6
    pistProxyLabel := some "LogogramProjection"
    pistExactLabel := some "LogogramProjection" }

/-- LogogramProjection — HOLD, proxy=LogogramProjection (exact alignment) -/
def fixtureLp : FixtureRow :=
  { equationId     := "rrc_eq_4c87c96f612f6100"
    name           := "Stamp_Code"
    shape          := .logogramProjection
    status         := .hold
    rrcKind        := "logogram_projection"
    weakAxesCnt    := 9
    pistProxyLabel := some "LogogramProjection"
    pistExactLabel := some "LogogramProjection" }

/-- ProjectableGeometryTopology — HOLD, no PIST prediction (missing) -/
def fixturePgt : FixtureRow :=
  { equationId     := "rrc_eq_5193efd26258bc51"
    name           := "UQGET_Hubble_Tension"
    shape          := .projectableGeometryTopology
    status         := .hold
    rrcKind        := "geometry_topology_receipt"
    weakAxesCnt    := 8
    pistProxyLabel := none
    pistExactLabel := none }

/-- CadForceProbeReceipt — HOLD, no PIST prediction (missing) -/
def fixtureCad : FixtureRow :=
  { equationId     := "rrc_eq_7076f5bdea119531"
    name           := "DAG_Force_Equilibrium"
    shape          := .cadForceProbeReceipt
    status         := .hold
    rrcKind        := "cad_force_receipt"
    weakAxesCnt    := 8
    pistProxyLabel := none
    pistExactLabel := none }

/-- HoldForUnlawfulOrUnderspecifiedShape — HOLD, no PIST prediction (missing) -/
def fixtureHold : FixtureRow :=
  { equationId     := "rrc_eq_6d33c14a88eb0a12"
    name           := "LASSO_MOGAT_GAT_Propagation"
    shape          := .holdForUnlawfulOrUnderspecifiedShape
    status         := .hold
    rrcKind        := "negative_control"
    weakAxesCnt    := 9
    pistProxyLabel := none
    pistExactLabel := none }

def fixtureCorpus : List FixtureRow :=
  [fixtureClf, fixtureSsrc, fixtureLp, fixturePgt, fixtureCad, fixtureHold]

-- ─────────────────────────────────────────────────────────────────────────────
-- §7  JSON serializer
-- ─────────────────────────────────────────────────────────────────────────────

private def jStr (s : String) : String :=
  "\"" ++ (s.replace "\\" "\\\\" |>.replace "\"" "\\\"") ++ "\""

private def jBool (b : Bool) : String := if b then "true" else "false"

private def jOpt (o : Option String) : String :=
  match o with
  | none   => "null"
  | some s => jStr s

private def jAlignment : AlignmentStatus → String
  | .alignedExact                   => "\"aligned_exact\""
  | .alignedProxy                   => "\"aligned_proxy\""
  | .compatibleStructuralProjection => "\"compatible_structural_projection\""
  | .alignmentWarning               => "\"alignment_warning\""
  | .missingPrediction              => "\"missing_prediction\""

private def jPromotion : Promotion → String
  | .notPromoted => "\"not_promoted\""
  | .candidate   => "\"candidate\""

private def jWitness : WitnessStatus → String
  | .candidate => "\"candidate\""
  | .hold      => "\"hold\""

private def jShape : RRCShape → String
  | s => jStr (shapeStr s)

private def jStrList (xs : List String) : String :=
  "[" ++ String.intercalate "," (xs.map jStr) ++ "]"

private def jRrcRow (r : RrcRow) : String :=
  s!"\{\"equation_id\":{jStr r.equationId}," ++
  s!"\"name\":{jStr r.name}," ++
  s!"\"shape\":{jShape r.shape}," ++
  s!"\"status\":{jWitness r.status}," ++
  s!"\"alignment_status\":{jAlignment r.alignmentStatus}," ++
  s!"\"alignment_score\":{r.alignmentScore}," ++
  s!"\"promotion\":{jPromotion r.promotion}," ++
  s!"\"warnings\":{jStrList r.warnings}," ++
  s!"\"receipt_valid\":{jBool r.receipt.valid}}"

private def jRowList (rs : List RrcRow) : String :=
  "[" ++ String.intercalate "," (rs.map jRrcRow) ++ "]"

-- ─────────────────────────────────────────────────────────────────────────────
-- §8  Top-level emitter
-- ─────────────────────────────────────────────────────────────────────────────

structure EmitResult where
  rows          : List RrcRow
  totalRows     : Nat
  candidateRows : Nat     -- rows where receipt.valid = true (alignment passed)
  json          : String
  deriving Repr

def emitFixture : EmitResult :=
  let rows       := fixtureCorpus.map compileRow
  let candidates := rows.filter (·.receipt.valid)
  let summary    :=
    s!"\{\"total\":{rows.length}," ++
    s!"\"passed_alignment\":{candidates.length}," ++
    s!"\"not_promoted\":{rows.length}," ++
    s!"\"schema\":\"rrc_emit_fixture_v1\"," ++
    s!"\"claim_boundary\":\"admissibility-and-routing-pass-only\"}"
  let json :=
    s!"\{\"schema\":\"rrc_emit_fixture_v1\"," ++
    s!"\"claim_boundary\":\"admissibility-and-routing-pass-only\"," ++
    s!"\"summary\":{summary}," ++
    s!"\"rows\":{jRowList rows}}"
  { rows          := rows
    totalRows     := rows.length
    candidateRows := candidates.length
    json          := json }

-- ─────────────────────────────────────────────────────────────────────────────
-- §9  Eval witnesses
-- ─────────────────────────────────────────────────────────────────────────────

-- Individual alignment gates
#eval determineAlignment fixtureClf    -- expect: compatibleStructuralProjection
#eval determineAlignment fixtureSsrc   -- expect: compatibleStructuralProjection
#eval determineAlignment fixtureLp     -- expect: alignedExact
#eval determineAlignment fixturePgt    -- expect: missingPrediction
#eval determineAlignment fixtureCad    -- expect: missingPrediction
#eval determineAlignment fixtureHold   -- expect: missingPrediction

-- Scores
#eval fixtureCorpus.map (fun r => (r.name, alignmentScore (determineAlignment r)))

-- Promotion summary
#eval (emitFixture.totalRows, emitFixture.candidateRows)

-- Full JSON bundle
#eval emitFixture.json

end Semantics.RRC.Emit
