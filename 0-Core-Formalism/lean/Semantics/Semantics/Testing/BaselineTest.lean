import Semantics.ExtremeParameterTest

namespace Semantics

/-- Baseline model types for null-model testing. -/
inductive BaselineModel where
  | randomGraph : BaselineModel
  | degreePreservingShuffle : BaselineModel
  | naiveCompression : BaselineModel
  | simpleMarkovRoute : BaselineModel
  | ordinaryMetadataScraper : BaselineModel
  | ordinaryGraphTraversal : BaselineModel
  deriving Repr, DecidableEq, BEq

structure BaselineResult where
  model : BaselineModel
  invariantPreservationPerByte : Float
  compressionRatio : Float
  topologyPreservation : Float
  beatCandidate : Bool
  deriving Repr

structure BaselineComparison where
  candidateInvariantPreservation : Float
  baselineInvariantPreservation : Float
  candidateBeatsBaseline : Bool
  gateDecision : String
  deriving Repr

/-- Invariant preservation metric: how much of the original structure is preserved per byte. -/
def invariantPreservationPerByte (originalSize : Nat) (preservedSize : Nat) : Float :=
  if originalSize == 0 then 0.0
  else Float.ofNat preservedSize / Float.ofNat originalSize

/-- Compare candidate model against baseline. -/
def compareCandidateToBaseline 
  (candidateInvariant : Float) 
  (baselineInvariant : Float) 
  (threshold : Float := 1.0) : 
  BaselineComparison :=
  let candidateBeatsBaseline := candidateInvariant > baselineInvariant + threshold
  let gateDecision := if candidateBeatsBaseline then "ACCEPT" else "HOLD_OR_REJECT"
  BaselineComparison.mk candidateInvariant baselineInvariant candidateBeatsBaseline gateDecision

/-- Baseline quiz bank: null models that the candidate must beat. -/
def baselineQuizBank : List BaselineModel :=
  [
    BaselineModel.randomGraph,
    BaselineModel.degreePreservingShuffle,
    BaselineModel.naiveCompression,
    BaselineModel.simpleMarkovRoute,
    BaselineModel.ordinaryMetadataScraper,
    BaselineModel.ordinaryGraphTraversal
  ]

/-- Run baseline comparison test. -/
def runBaselineTest (candidateInvariant : Float) : List BaselineComparison :=
  baselineQuizBank.map fun model =>
    let baselineInvariant := match model with
      | BaselineModel.randomGraph => 0.3
      | BaselineModel.degreePreservingShuffle => 0.5
      | BaselineModel.naiveCompression => 0.4
      | BaselineModel.simpleMarkovRoute => 0.35
      | BaselineModel.ordinaryMetadataScraper => 0.45
      | BaselineModel.ordinaryGraphTraversal => 0.4
    compareCandidateToBaseline candidateInvariant baselineInvariant

/-- Baseline gate rule: if candidate ≤ baseline, HOLD_OR_REJECT. -/
def baselineGate (candidateInvariant : Float) (baselineInvariant : Float) : Bool :=
  candidateInvariant > baselineInvariant

end Semantics
