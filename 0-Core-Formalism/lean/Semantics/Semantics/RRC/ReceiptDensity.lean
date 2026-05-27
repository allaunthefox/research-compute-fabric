-- Semantics.RRC.ReceiptDensity — Q16_16 receipt-density scoring
--
-- Ports the core scoring logic from pist_receipt_density_injector.py into Lean.
-- This is the authoritative specification; the Python shim is an IO-only
-- extraction target.
--
-- Shim contract (mirrors pist_receipt_density_injector.py §TODO(lean-port)):
--   - All scoring arithmetic is Q16_16 fixed-point (no Float in compute paths).
--   - Python is responsible only for JSON I/O and table parsing.
--   - `compute_density` and `compute_confidence` are the sole decision gates.
--   - promotion is always not_promoted at this stage.
--
-- Python source:      4-Infrastructure/shim/pist_receipt_density_injector.py
-- Python functions:   spectral_quality, shape_agreement, axis_score,
--                     status_score, compute_density
-- BOUNDARY comment:   Semantics.RRC.ReceiptDensity (this file)

import Semantics.FixedPoint
import Semantics.RRC.Emit

namespace Semantics.RRC.ReceiptDensity

open Semantics.Q16_16
open Semantics.RRC.Emit
open Semantics.RRCLogogramProjection

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  Status base scores  (ports STATUS_BASE dict in injector.py)
--     All values are Q16_16 raw integers (denominator = 65536 = 1.0)
--     BLOCKED  = 0.00  → 0
--     HOLD     = 0.12  → 7864
--     CANDIDATE= 0.45  → 29491
--     REVIEWED = 0.78  → 51118
--     VERIFIED = 0.84  → 55050
-- ─────────────────────────────────────────────────────────────────────────────

inductive SourceStatus where
  | blocked
  | hold
  | candidate
  | reviewed
  | verified
  deriving DecidableEq, Repr

def statusScoreRaw : SourceStatus → Int
  | .blocked   => 0
  | .hold      => 7864    -- 0.12 * 65536 ≈ 7864
  | .candidate => 29491   -- 0.45 * 65536 ≈ 29491
  | .reviewed  => 51118   -- 0.78 * 65536 ≈ 51118
  | .verified  => 55050   -- 0.84 * 65536 ≈ 55050

def statusScore (s : SourceStatus) : Q16_16 :=
  Q16_16.ofRawInt (statusScoreRaw s)

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  Target axes  (ports TARGET_AXES set in injector.py)
--
--   projection_declared, negative_control_strength, witness_declared,
--   scale_band_declared, shape_closure
--
-- We represent axes as a list of Bool flags in this order:
--   [projectionDeclared, negativeControlStrength, witnessDeclared,
--    scaleBandDeclared, shapeClosure]
-- ─────────────────────────────────────────────────────────────────────────────

structure AxisFlags where
  projectionDeclared       : Bool
  negativeControlStrength  : Bool
  witnessDeclared          : Bool
  scaleBandDeclared        : Bool
  shapeClosure             : Bool
  deriving Repr

def axisHitCount (flags : AxisFlags) : Nat :=
  (if flags.projectionDeclared      then 1 else 0) +
  (if flags.negativeControlStrength then 1 else 0) +
  (if flags.witnessDeclared         then 1 else 0) +
  (if flags.scaleBandDeclared       then 1 else 0) +
  (if flags.shapeClosure            then 1 else 0)

-- axis_score(row) = clamp(hits / 4, 0, 1)
-- denominator 4 matches the Python shim (not 5 — intentional).
-- Q16_16 encoding: ofRatio hits 4 = (hits * 65536) / 4
def axisScore (flags : AxisFlags) : Q16_16 :=
  let hits := axisHitCount flags
  if hits == 0 then Q16_16.zero
  else
    -- cap at 1.0 (hits ≥ 4 → score = 1.0)
    let capped := if hits ≥ 4 then 4 else hits
    Q16_16.ofRatio capped 4

-- ─────────────────────────────────────────────────────────────────────────────
-- §3  Shape agreement  (ports shape_agreement in injector.py)
--
--   exact == rrc_shape  → 1.0   (65536)
--   proxy == rrc_shape  → 0.82  (53739)
--   either present       → 0.35  (22938)
--   neither present      → 0.0   (0)
-- ─────────────────────────────────────────────────────────────────────────────

/-- Shape agreement between PIST predictions and the RRC routing shape.
    `pistExact` / `pistProxy` carry the same semantics as `exact_pred` / `proxy_pred`
    in the PIST validation JSON. -/
def shapeAgreement
    (rrcShape : RRCShape)
    (pistProxy : Option RRCShape)
    (pistExact : Option RRCShape)
    : Q16_16 :=
  -- RRCShape has DecidableEq; compare via exhaustive pattern matching to avoid
  -- requiring BEq or bringing DecidableEq instance into scope explicitly.
  let matchShape (opt : Option RRCShape) : Bool :=
    match opt, rrcShape with
    | some .signalShapedRouteCompiler,          .signalShapedRouteCompiler          => true
    | some .projectableGeometryTopology,        .projectableGeometryTopology        => true
    | some .cognitiveLoadField,                 .cognitiveLoadField                 => true
    | some .cadForceProbeReceipt,               .cadForceProbeReceipt               => true
    | some .logogramProjection,                 .logogramProjection                 => true
    | some .holdForUnlawfulOrUnderspecifiedShape, .holdForUnlawfulOrUnderspecifiedShape => true
    | _, _ => false
  if matchShape pistExact then
    Q16_16.ofRatio 100 100  -- 1.0
  else if matchShape pistProxy then
    Q16_16.ofRawInt 53739   -- 0.82
  else if pistProxy.isSome || pistExact.isSome then
    Q16_16.ofRawInt 22938   -- 0.35
  else
    Q16_16.zero

-- ─────────────────────────────────────────────────────────────────────────────
-- §4  Spectral quality  (ports spectral_quality in injector.py)
--
-- Inputs (all Q16_16):
--   rankEstimate      — effective matrix rank / 8.0
--   spectralGap       — Laplacian spectral gap ∈ [0,1]
--   strandEntropy     — strand entropy / 3.0
--   crossingDensity   — crossing density / 0.5
--   laplacianZeroCount — ≥ 1 → full score, else 0.45 penalty
--   hasHashes         — canonical_hash AND matrix_hash both present
--
-- Weighted sum (integer weights, denominator = 100):
--   0.24 * rank_score  +  0.18 * gap_score  +  0.18 * entropy_score
--   +  0.12 * density_score  +  0.12 * lap_score  +  0.16 * hash_score
--
-- All inputs are already Q16_16-normalised (caller divides by the relevant
-- scale factor before calling this function, as noted per-field above).
-- ─────────────────────────────────────────────────────────────────────────────

structure SpectralFeatures where
  rankScore     : Q16_16   -- rank_estimate / 8.0, clamped [0,1]
  gapScore      : Q16_16   -- spectral_gap, clamped [0,1]
  entropyScore  : Q16_16   -- strand_entropy / 3.0, clamped [0,1]
  densityScore  : Q16_16   -- crossing_density / 0.5, clamped [0,1]
  lapFull       : Bool     -- laplacian_zero_count ≥ 1
  hasHashes     : Bool     -- canonical_hash AND matrix_hash present
  deriving Repr

-- Weight constants (numerators, denominator = 100)
private def wRank    : Int := 24
private def wGap     : Int := 18
private def wEntropy : Int := 18
private def wDensity : Int := 12
private def wLap     : Int := 12
private def wHash    : Int := 16

private def lapScore (lapFull : Bool) : Q16_16 :=
  if lapFull then Q16_16.one else Q16_16.ofRawInt 29491  -- 0.45 ≈ 29491

private def hashScore (hasHashes : Bool) : Q16_16 :=
  if hasHashes then Q16_16.one else Q16_16.zero

/-- Compute spectral quality score ∈ [0, 1] in Q16_16. -/
def spectralQuality (f : SpectralFeatures) : Q16_16 :=
  -- Each term: weight * score / 100, accumulated in raw int space to avoid
  -- intermediate truncation.
  let raw :=
    wRank    * f.rankScore.toInt / 100 +
    wGap     * f.gapScore.toInt  / 100 +
    wEntropy * f.entropyScore.toInt / 100 +
    wDensity * f.densityScore.toInt / 100 +
    wLap     * (lapScore f.lapFull).toInt / 100 +
    wHash    * (hashScore f.hasHashes).toInt / 100
  Q16_16.ofRawInt raw

-- ─────────────────────────────────────────────────────────────────────────────
-- §5  Receipt density and confidence  (ports compute_density in injector.py)
--
-- density = clamp(0.26*status + 0.24*axes + 0.26*spectral + 0.24*shape, 0,1)
-- confidence = clamp(0.20*status + 0.20*axes + 0.28*spectral + 0.32*shape, 0,1)
--
-- Q16_16 weight encoding (denominator = 100):
--   density weights:    [26, 24, 26, 24]
--   confidence weights: [20, 20, 28, 32]
-- ─────────────────────────────────────────────────────────────────────────────

structure DensityComponents where
  statusScore   : Q16_16
  axisScore     : Q16_16
  spectralScore : Q16_16
  shapeScore    : Q16_16
  deriving Repr

structure DensityResult where
  density     : Q16_16
  confidence  : Q16_16
  components  : DensityComponents
  warnings    : List String
  deriving Repr

private def weightedSum (weights : List Int) (scores : List Q16_16) : Q16_16 :=
  let raw := (weights.zip scores).foldl
    (fun acc (ws : Int × Q16_16) => acc + ws.1 * ws.2.toInt / 100)
    0
  Q16_16.ofRawInt raw

/-- Compute receipt density and confidence for one equation row.
    `hasPistPrediction` is true when either proxy_pred or exact_pred is present. -/
def computeDensity
    (status  : SourceStatus)
    (axes    : AxisFlags)
    (spectral: SpectralFeatures)
    (shape   : RRCShape)
    (pistProxy : Option RRCShape)
    (pistExact : Option RRCShape)
    : DensityResult :=
  let sStatus   := statusScore status
  let sAxes     := axisScore axes
  let sSpectral := spectralQuality spectral
  let sShape    := shapeAgreement shape pistProxy pistExact

  let hasPrediction := pistProxy.isSome || pistExact.isSome

  let warnings : List String :=
    (if !hasPrediction then ["missing_pist_prediction"] else []) ++
    -- shape disagreement when shape agreement score < 0.50 (32768 in Q16_16)
    (if hasPrediction && sShape.toInt < 32768 then ["pist_shape_disagreement"] else [])

  let densityWeights    : List Int := [26, 24, 26, 24]
  let confidenceWeights : List Int := [20, 20, 28, 32]
  let scoreList         : List Q16_16 := [sStatus, sAxes, sSpectral, sShape]

  let density    := weightedSum densityWeights    scoreList
  let confidence := weightedSum confidenceWeights scoreList

  { density    := density
    confidence := confidence
    components := { statusScore := sStatus, axisScore := sAxes
                    spectralScore := sSpectral, shapeScore := sShape }
    warnings   := warnings.eraseDups }

-- ─────────────────────────────────────────────────────────────────────────────
-- §6  Claim boundary
-- ─────────────────────────────────────────────────────────────────────────────

/-- Canonical claim boundary string emitted in every receipt. -/
def claimBoundary : String :=
  "receipt-density-scoring-only; not-a-proof; promotion=not_promoted"

-- ─────────────────────────────────────────────────────────────────────────────
-- §7  Eval witnesses
-- ─────────────────────────────────────────────────────────────────────────────

open RRCLogogramProjection in
-- Witness: CANDIDATE row with 3/5 target axes, no PIST prediction.
-- Expected density ≈ 0.26*0.45 + 0.24*(3/4) + 0.26*0.0 + 0.24*0.0
--                  = 0.117 + 0.18 = 0.297 → raw ≈ 19464
#eval
  let axes : AxisFlags :=
    { projectionDeclared := true, negativeControlStrength := false
      witnessDeclared := true, scaleBandDeclared := true, shapeClosure := false }
  let spectral : SpectralFeatures :=
    { rankScore := Q16_16.zero, gapScore := Q16_16.zero, entropyScore := Q16_16.zero
      densityScore := Q16_16.zero, lapFull := false, hasHashes := false }
  let r := computeDensity .candidate axes spectral
            RRCShape.cognitiveLoadField none none
  (r.density.toInt, r.warnings)

open RRCLogogramProjection in
-- Witness: VERIFIED row, exact PIST match, 5/5 axes, reasonable spectral.
-- Expected density ≈ 0.26*0.84 + 0.24*1.0 + 0.26*spectral + 0.24*1.0
#eval
  let axes : AxisFlags :=
    { projectionDeclared := true, negativeControlStrength := true
      witnessDeclared := true, scaleBandDeclared := true, shapeClosure := true }
  let spectral : SpectralFeatures :=
    { rankScore := Q16_16.ofRatio 1 2  -- rank=4/8=0.5
      gapScore  := Q16_16.ofRatio 3 4  -- gap=0.75
      entropyScore := Q16_16.ofRatio 2 3  -- entropy/3=0.67
      densityScore := Q16_16.ofRatio 1 2  -- crossing/0.5=0.5
      lapFull   := true, hasHashes := true }
  let r := computeDensity .verified axes spectral
            RRCShape.logogramProjection
            (some RRCShape.logogramProjection) (some RRCShape.logogramProjection)
  (r.density.toInt, r.confidence.toInt, r.warnings)

end Semantics.RRC.ReceiptDensity
