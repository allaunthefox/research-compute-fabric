-- AVM ISA v1 — Goal A: run a canary, construct an RRC record, emit JSON.
--
-- This module is the first end-to-end connection between:
--   AVMIsa.Run     (fuel-bounded execution, Outcome State)
--   ReceiptCore    (receipt ledger, leanBuildReceipt, hasProofReceipt)
--   RRCLogogramProjection (projection/merge admission gates, LogogramReceipt)
--
-- The #eval at the bottom is the "rainbow raccoon compiler" proof-of-life:
-- it runs the boolean-not canary through the AVM, checks the result, mints
-- a receipt, gates it through the RRC projection discipline, and prints the
-- whole bundle as a JSON string that a Python harness can validate.

import Semantics.AVMIsa.Run
import Semantics.ReceiptCore
import Semantics.RRCLogogramProjection

namespace Semantics.AVMIsa.Emit

open Semantics.AVMIsa
open Semantics.ReceiptCore
open Semantics.RRCLogogramProjection

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  Canary programs
-- ─────────────────────────────────────────────────────────────────────────────

/-- Canary 1: boolean NOT.  Push false → NOT → halt; expect true on stack. -/
def progNot : List Instr :=
  [ Instr.push ⟨AvmTy.bool, AvmVal.b false⟩
  , Instr.prim Prim.not
  , Instr.halt ]

/-- Canary 2: boolean AND.  Push true, push false → AND → halt; expect false. -/
def progAnd : List Instr :=
  [ Instr.push ⟨AvmTy.bool, AvmVal.b true⟩
  , Instr.push ⟨AvmTy.bool, AvmVal.b false⟩
  , Instr.prim Prim.and
  , Instr.halt ]

/-- Canary 3: boolean OR.  Push false, push false → OR → halt; expect false. -/
def progOr : List Instr :=
  [ Instr.push ⟨AvmTy.bool, AvmVal.b false⟩
  , Instr.push ⟨AvmTy.bool, AvmVal.b false⟩
  , Instr.prim Prim.or
  , Instr.halt ]

def initState : State :=
  { pc := 0, stack := [], locals := [], halted := false }

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  Canary result classifier
-- ─────────────────────────────────────────────────────────────────────────────

/-- Expected bool value on top of stack after halt. -/
def checkTopBool (outcome : Outcome State) (expected : Bool) : Bool :=
  match outcome with
  | Outcome.err _ => false
  | Outcome.ok s =>
      match s.stack with
      | ⟨AvmTy.bool, AvmVal.b b⟩ :: _ => b == expected && s.halted
      | _ => false

-- ─────────────────────────────────────────────────────────────────────────────
-- §3  Canary → ReceiptCore bridge
-- ─────────────────────────────────────────────────────────────────────────────

/-- Run a canary program and mint a leanBuildReceipt keyed on `targetId`. -/
def canaryReceipt (targetId : String) (prog : List Instr) (expected : Bool) : Receipt :=
  let outcome := run 16 prog initState
  let passed  := checkTopBool outcome expected
  leanBuildReceipt targetId passed

/-- The three baseline canary receipts. -/
def canaryReceipts : List Receipt :=
  [ canaryReceipt "avm.canary.not" progNot true
  , canaryReceipt "avm.canary.and" progAnd false
  , canaryReceipt "avm.canary.or"  progOr  false ]

-- ─────────────────────────────────────────────────────────────────────────────
-- §4  RRC LogogramReceipt for the AVM canary bundle
-- ─────────────────────────────────────────────────────────────────────────────

/-- Build an RRC LogogramReceipt reflecting whether all canaries passed.
    If all three pass → normal projection (uglyAsymmetricPruning, no tear).
    If any fail → horribleManifoldTearing (force into quarantine projection). -/
def canaryLogogramReceipt (allPassed : Bool) : LogogramReceipt :=
  if allPassed then
    { shape               := RRCShape.logogramProjection
      status              := WitnessStatus.candidate
      regime              := SemanticRegime.uglyAsymmetricPruning
      payloadBound        := true
      contradictionWitness := false
      tearBoundary        := false
      detachedMass        := false
      residualLane        := false }
  else
    { shape               := RRCShape.logogramProjection
      status              := WitnessStatus.candidate
      regime              := SemanticRegime.horribleManifoldTearing
      payloadBound        := true
      contradictionWitness := false
      tearBoundary        := false
      detachedMass        := false
      residualLane        := false }

-- ─────────────────────────────────────────────────────────────────────────────
-- §5  Minimal JSON serializer (no Float, no external deps)
-- ─────────────────────────────────────────────────────────────────────────────

private def jsonBool (b : Bool) : String := if b then "true" else "false"

private def jsonStr (s : String) : String :=
  -- Escape the handful of chars that appear in our strings
  let escaped := s.replace "\\" "\\\\" |>.replace "\"" "\\\""
  s!"\"{escaped}\""

private def jsonReceiptKind : ReceiptKind → String
  | .leanBuild        => "\"leanBuild\""
  | .benchmark        => "\"benchmark\""
  | .sourceAudit      => "\"sourceAudit\""
  | .reverseCollapse  => "\"reverseCollapse\""
  | .deltaPhiAudit    => "\"deltaPhiAudit\""
  | .adversarialTrial => "\"adversarialTrial\""
  | .humanReview      => "\"humanReview\""
  | .wardenEmission   => "\"wardenEmission\""
  | .externalProof    => "\"externalProof\""

private def jsonReceipt (r : Receipt) : String :=
  s!"\{\"kind\":{jsonReceiptKind r.kind},\"targetId\":{jsonStr r.targetId}," ++
  s!"\"summary\":{jsonStr r.summary},\"valid\":{jsonBool r.valid}," ++
  s!"\"authority\":{jsonStr r.authority},\"timestamp\":{r.timestamp}}"

private def jsonRRCShape : RRCShape → String
  | .signalShapedRouteCompiler          => "\"signalShapedRouteCompiler\""
  | .projectableGeometryTopology        => "\"projectableGeometryTopology\""
  | .cognitiveLoadField                 => "\"cognitiveLoadField\""
  | .cadForceProbeReceipt               => "\"cadForceProbeReceipt\""
  | .logogramProjection                 => "\"logogramProjection\""
  | .holdForUnlawfulOrUnderspecifiedShape => "\"holdForUnlawfulOrUnderspecifiedShape\""

private def jsonRegime : SemanticRegime → String
  | .beautifulTopologicalFolding => "\"beautifulTopologicalFolding\""
  | .uglyAsymmetricPruning       => "\"uglyAsymmetricPruning\""
  | .horribleManifoldTearing     => "\"horribleManifoldTearing\""

private def jsonLane : ProjectionLane → String
  | .normalProjection    => "\"normalProjection\""
  | .quarantineProjection => "\"quarantineProjection\""

private def jsonLogogramReceipt (lr : LogogramReceipt) : String :=
  s!"\{\"shape\":{jsonRRCShape lr.shape},\"regime\":{jsonRegime lr.regime}," ++
  s!"\"projectionAdmissible\":{jsonBool (projectionAdmissible lr)}," ++
  s!"\"mergeAdmissible\":{jsonBool (mergeAdmissible lr)}," ++
  s!"\"lane\":{jsonLane (projectionLane lr)}}"

private def jsonReceiptList (rs : List Receipt) : String :=
  "[" ++ String.intercalate "," (rs.map jsonReceipt) ++ "]"

-- ─────────────────────────────────────────────────────────────────────────────
-- §6  Top-level emit
-- ─────────────────────────────────────────────────────────────────────────────

structure EmitResult where
  allPassed        : Bool
  receipts         : List Receipt
  logogramReceipt  : LogogramReceipt
  projectionPassed : Bool
  json             : String
  deriving Repr

def emit : EmitResult :=
  let rs         := canaryReceipts
  let allPassed  := rs.all (·.valid)
  let lr         := canaryLogogramReceipt allPassed
  let projOk     := projectionAdmissible lr
  let jsonBody   :=
    s!"\{\"schema\":\"avm_canary_emit_v1\"," ++
    s!"\"all_canaries_passed\":{jsonBool allPassed}," ++
    s!"\"receipts\":{jsonReceiptList rs}," ++
    s!"\"rrc_logogram\":{jsonLogogramReceipt lr}," ++
    s!"\"projection_passed\":{jsonBool projOk}}"
  { allPassed       := allPassed
    receipts        := rs
    logogramReceipt := lr
    projectionPassed := projOk
    json            := jsonBody }

-- ─────────────────────────────────────────────────────────────────────────────
-- §7  Proof-of-life eval witnesses
-- ─────────────────────────────────────────────────────────────────────────────

-- Individual canary checks
#eval checkTopBool (run 16 progNot initState) true    -- expect: true
#eval checkTopBool (run 16 progAnd initState) false   -- expect: true
#eval checkTopBool (run 16 progOr  initState) false   -- expect: true

-- Receipt validity
#eval canaryReceipts.map (fun r => (r.targetId, r.valid))

-- Full JSON bundle (the "rainbow raccoon compiler" output)
#eval emit.json

end Semantics.AVMIsa.Emit
