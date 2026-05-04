/-
OracleInterrogation.lean — Oracle interrogation scaffold with IDPC v0.2

Origin note:
  IDPC came from the intuition chain "Delphi" -> "Delta Phi" ->
  "Inverse Delta Phi over Cosine". In this module it is placed where that
  intuition belongs: inside oracle interrogation.

Core reading:
  Interrogation is inherently about change.
  A question perturbs an oracle state; an answer is judged by how coherently the
  state changes. IDPC measures coherence per phase displacement.

Deeper oracle reading:
  The oracle is not trusted because it is always right. It is useful because a
  mostly wrong surface answer can sometimes be right enough to expose a deeper
  pattern candidate. Receipts decide whether that pattern survives.

Stable operator:
  IDPC = alignment / (deltaPhi + epsilon)

No Float. No trig hot path. Cosine/alignment is supplied by an external encoder
as a bounded natural-number score.
-/

import Std

namespace Semantics.OracleInterrogation

/-- Evidence ladder for oracle-interrogation claims. -/
inductive ClaimState where
  | beautifulProvisional
  | calibratedEngineeringDelta
  | reviewed
  deriving Repr, DecidableEq, Inhabited

/-- Oracle interrogation phase. -/
inductive InterrogationPhase where
  | question
  | perturbation
  | response
  | reconciliation
  | receipt
  deriving Repr, DecidableEq, Inhabited

/-- Mode of the IDPC operator. -/
inductive IDPCMode where
  | stabilityScore
  | singularityDetector
  deriving Repr, DecidableEq, Inhabited

/-- Surface/pattern status of a fallible oracle response. -/
inductive PatternStatus where
  | literalFailPatternFail
  | literalFailPatternCandidate
  | literalPassPatternCandidate
  | receiptedPattern
  deriving Repr, DecidableEq, Inhabited

/-- A discrete oracle state marker. -/
structure OracleState where
  stateId : String
  phase : Nat
  coherence : Nat
  deriving Repr, DecidableEq, Inhabited

/-- A question or prompt issued to an oracle. -/
structure OracleQuestion where
  questionId : String
  textHash : String
  declaredScope : String
  deriving Repr, DecidableEq, Inhabited

/-- An answer returned by an oracle. -/
structure OracleAnswer where
  answerId : String
  textHash : String
  declaredScope : String
  deriving Repr, DecidableEq, Inhabited

/--
Oracle interrogation event.

The important part is the transition:
  before -> after

IDPC belongs here because interrogation is a controlled change in oracle state.
-/
structure OracleInterrogation where
  question : OracleQuestion
  answer : OracleAnswer
  beforeState : OracleState
  afterState : OracleState
  phase : InterrogationPhase
  deriving Repr, DecidableEq, Inhabited

/--
Pattern signal emitted by a fallible oracle interrogation.

`literalCorrect = false` does not force `patternCandidate = false`.
That is the key Delphi-style distinction.
-/
structure PatternSignal where
  literalCorrect : Bool
  patternCandidate : Bool
  receiptValidated : Bool
  note : String
  deriving Repr, DecidableEq, Inhabited

/-- Classify the fallible-oracle pattern signal. -/
def patternStatus (s : PatternSignal) : PatternStatus :=
  if s.receiptValidated then
    .receiptedPattern
  else if s.literalCorrect then
    if s.patternCandidate then
      .literalPassPatternCandidate
    else
      .literalFailPatternFail
  else if s.patternCandidate then
    .literalFailPatternCandidate
  else
    .literalFailPatternFail

/--
Discrete encoded inputs for IDPC.

* `alignment` represents nonnegative cosine alignment after clipping/rescaling.
* `deltaPhi` represents phase/semantic displacement magnitude.
* `epsilon` prevents division by zero.
* `scale` preserves integer precision.
-/
structure IDPCInput where
  alignment : Nat
  deltaPhi : Nat
  epsilon : Nat
  scale : Nat
  deriving Repr, DecidableEq, Inhabited

/-- Validity gate: epsilon and scale must be nonzero. -/
def ValidIDPCInput (x : IDPCInput) : Prop :=
  0 < x.epsilon ∧ 0 < x.scale

/-- Denominator for stable IDPC. -/
def idpcDenom (x : IDPCInput) : Nat :=
  x.deltaPhi + x.epsilon

/-- Stable IDPC score: alignment * scale / (deltaPhi + epsilon). -/
def idpcScore (x : IDPCInput) : Nat :=
  (x.alignment * x.scale) / idpcDenom x

/--
Build IDPC input directly from an oracle interrogation.

The encoder supplies alignment. DeltaPhi is computed as absolute phase change.
-/
def idpcInputOfInterrogation
    (alignment epsilon scale : Nat)
    (q : OracleInterrogation) : IDPCInput :=
  { alignment := alignment
    deltaPhi := q.afterState.phase - q.beforeState.phase +
      (q.beforeState.phase - q.afterState.phase)
    epsilon := epsilon
    scale := scale }

/-- Oracle interrogation result with IDPC and fallible-pattern status attached. -/
structure OracleInterrogationResult where
  interrogation : OracleInterrogation
  mode : IDPCMode
  idpc : Nat
  pattern : PatternSignal
  status : PatternStatus
  claimState : ClaimState
  note : String
  deriving Repr, Inhabited

/-- Evaluate an interrogation by IDPC in stability-score mode. -/
def evaluateInterrogationStable
    (alignment epsilon scale : Nat)
    (q : OracleInterrogation)
    (signal : PatternSignal :=
      { literalCorrect := false
        patternCandidate := false
        receiptValidated := false
        note := "no pattern candidate supplied" }) : OracleInterrogationResult :=
  let x := idpcInputOfInterrogation alignment epsilon scale q
  { interrogation := q
    mode := .stabilityScore
    idpc := idpcScore x
    pattern := signal
    status := patternStatus signal
    claimState := .beautifulProvisional
    note := "oracle interrogation coherence per phase displacement with fallible-pattern gate" }

/-- With positive epsilon, the denominator is nonzero. -/
theorem idpcDenom_positive_of_valid (x : IDPCInput) (h : ValidIDPCInput x) :
    0 < idpcDenom x := by
  unfold ValidIDPCInput at h
  unfold idpcDenom
  exact Nat.lt_add_left x.deltaPhi h.left

/-- Zero alignment always yields zero IDPC. -/
theorem zero_alignment_idpc_zero (deltaPhi epsilon scale : Nat) :
    idpcScore { alignment := 0, deltaPhi := deltaPhi, epsilon := epsilon, scale := scale } = 0 := by
  unfold idpcScore idpcDenom
  simp

/-- Increasing the denominator cannot increase Nat-division IDPC. -/
theorem idpc_denominator_monotone_nonincreasing
    (alignment scale d1 d2 : Nat)
    (h : d1 ≤ d2) :
    (alignment * scale) / d2 ≤ (alignment * scale) / d1 := by
  exact Nat.div_le_div_left (alignment * scale) h

/-- Larger phase displacement weakly lowers IDPC when epsilon is fixed. -/
theorem deltaPhi_monotone_nonincreasing
    (alignment scale epsilon d1 d2 : Nat)
    (h : d1 ≤ d2) :
    idpcScore { alignment := alignment, deltaPhi := d2, epsilon := epsilon, scale := scale } ≤
    idpcScore { alignment := alignment, deltaPhi := d1, epsilon := epsilon, scale := scale } := by
  unfold idpcScore idpcDenom
  exact idpc_denominator_monotone_nonincreasing alignment scale (d1 + epsilon) (d2 + epsilon) (Nat.add_le_add_right h epsilon)

/-- IDPC is bounded by scaled alignment when denominator is at least one. -/
theorem idpc_score_le_scaled_alignment
    (x : IDPCInput)
    (h : 1 ≤ idpcDenom x) :
    idpcScore x ≤ x.alignment * x.scale := by
  unfold idpcScore
  exact Nat.div_le_self (x.alignment * x.scale) (idpcDenom x)

/-- Valid inputs always have score bounded by scaled alignment. -/
theorem valid_idpc_score_le_scaled_alignment
    (x : IDPCInput)
    (h : ValidIDPCInput x) :
    idpcScore x ≤ x.alignment * x.scale := by
  have hd : 0 < idpcDenom x := idpcDenom_positive_of_valid x h
  exact idpc_score_le_scaled_alignment x hd

/-- Literal failure can still produce a pattern candidate. -/
theorem literal_failure_can_still_be_pattern_candidate :
    ∃ s : PatternSignal,
      s.literalCorrect = false ∧
      s.patternCandidate = true ∧
      patternStatus s = PatternStatus.literalFailPatternCandidate := by
  refine ⟨
    { literalCorrect := false
      patternCandidate := true
      receiptValidated := false
      note := "mostly wrong, but right enough to expose a deeper pattern" }, ?_, ?_, ?_⟩
  · rfl
  · rfl
  · unfold patternStatus
    decide

/-- A receipted signal promotes to receiptedPattern regardless of surface truth. -/
theorem receipt_validated_promotes_pattern
    (literalCorrect patternCandidate : Bool) :
    patternStatus
      { literalCorrect := literalCorrect
        patternCandidate := patternCandidate
        receiptValidated := true
        note := "receipt validated" } = PatternStatus.receiptedPattern := by
  unfold patternStatus
  decide

/-- Example interrogation with phase change. -/
def delphiExample : OracleInterrogation :=
  { question :=
      { questionId := "delphi-question"
        textHash := "thinking-delphi"
        declaredScope := "operator-origin" }
    answer :=
      { answerId := "idpc-answer"
        textHash := "inverse-delta-phi-over-cosine"
        declaredScope := "oracle-interrogation" }
    beforeState := { stateId := "before", phase := 10, coherence := 80 }
    afterState := { stateId := "after", phase := 17, coherence := 84 }
    phase := .response }

/-- Example IDPC input from the Delphi-origin interrogation. -/
def delphiExampleInput : IDPCInput :=
  idpcInputOfInterrogation 100 1 1000 delphiExample

/-- Example fallible oracle pattern signal. -/
def delphiFallibleSignal : PatternSignal :=
  { literalCorrect := false
    patternCandidate := true
    receiptValidated := false
    note := "surface wrong; deeper pattern candidate detected" }

/-- Example validity proof. -/
theorem delphiExampleInput_valid : ValidIDPCInput delphiExampleInput := by
  unfold ValidIDPCInput delphiExampleInput idpcInputOfInterrogation
  decide

#eval delphiExampleInput.deltaPhi -- 7
#eval idpcScore delphiExampleInput -- 12500
#eval patternStatus delphiFallibleSignal -- literalFailPatternCandidate
#eval (evaluateInterrogationStable 100 1 1000 delphiExample delphiFallibleSignal).idpc -- 12500
#eval (evaluateInterrogationStable 100 1 1000 delphiExample delphiFallibleSignal).status -- literalFailPatternCandidate

end Semantics.OracleInterrogation
