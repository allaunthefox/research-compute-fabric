import Semantics.FixedPoint
import Semantics.Canon

namespace Semantics

/-! # Canonical Adapters
Normalization modes, dimensions, vectors, and attractors for canonical state processing.
Split from Canon.lean per swarm suggestion (USER AUTHORIZED).
-/

/-- Legacy canonical adapter normalization modes recovered from earlier ENE schema forms. -/
inductive NormalizationMode
  | minmax
  | centered
  | passthrough
deriving Repr, BEq, DecidableEq

/-- Fixed-point feature contract for raw inputs at the canonical adapter boundary. -/
structure RawFeatureSpec where
  name : String
  mode : NormalizationMode
  low : Q16_16 := Q16_16.zero
  high : Q16_16 := Q16_16.one
  required : Bool := true
deriving Repr, BEq

/-- Canonical coordinates that may be packed into a stable ENE vector. -/
inductive CanonicalDimension
  | phi
  | psi
  | delta
  | gamma
  | chi
  | tau
  | deltaDot
  | drift
  | curvature
  | coherence
  | angularMomentum
  | radiusDev
  | confidence
deriving Repr, BEq, DecidableEq

/-- Recover the scalar value for a named canonical dimension. -/
def CanonicalDimension.read (d : CanonicalDimension) (state : CanonicalState) : Q16_16 :=
  match d with
  | .phi => state.phi
  | .psi => state.psi
  | .delta => state.delta
  | .gamma => state.gamma
  | .chi => state.chi
  | .tau => state.tau
  | .deltaDot => state.deltaDot
  | .drift => state.drift
  | .curvature => state.curvature
  | .coherence => state.coherence
  | .angularMomentum => state.angularMomentum
  | .radiusDev => state.radiusDev
  | .confidence => state.confidence

/-- Ordered vector specification recovered from the older canonical adapter packer. -/
structure CanonicalVectorSpec where
  dimensions : List CanonicalDimension := [
    .phi, .psi, .delta, .gamma, .chi, .tau, .deltaDot,
    .drift, .curvature, .coherence, .angularMomentum, .radiusDev, .confidence
  ]
deriving Repr, BEq

/-- Pack a canonical state into a stable vector according to the chosen dimension order. -/
def CanonicalVectorSpec.pack (spec : CanonicalVectorSpec) (state : CanonicalState) : List Q16_16 :=
  spec.dimensions.map (fun dim => dim.read state)

/-- Named attractor recovered from the earlier canonical adapter assignment schema. -/
structure CanonicalAttractor where
  name : String
  center : List Q16_16
  maxRadius : Option Q16_16 := none
deriving Repr, BEq

/-- Quantized band assignment for a packed canonical dimension. -/
structure QuantizedBand where
  dimension : CanonicalDimension
  band : Nat
deriving Repr, BEq

/-- Result of assigning a packed canonical vector to an attractor/signature surface. -/
structure AssignmentResult where
  zN : List Q16_16
  nearestAttractor : Option String
  attractorDistance : Option Q16_16
  attractorConfidence : Q16_16
  signature : List Nat
  quantizedBands : List QuantizedBand
  consistent : Bool
deriving Repr, BEq

/-- Clamp a fixed-point scalar into a closed interval. -/
def clampQ16 (value low high : Q16_16) : Q16_16 :=
  Q16_16.max low (Q16_16.min high value)

/-- Normalize a raw feature using the recovered legacy adapter modes, now in Q16.16. -/
def normalizeFeatureValue (spec : RawFeatureSpec) (raw : Q16_16) : Q16_16 :=
  match spec.mode with
  | .passthrough => raw
  | .minmax =>
      let span := Q16_16.sub spec.high spec.low
      let shifted := Q16_16.sub raw spec.low
      clampQ16 (Q16_16.div shifted span) Q16_16.zero Q16_16.one
  | .centered =>
      let midpoint := Q16_16.div (Q16_16.add spec.low spec.high) (Q16_16.ofInt 2)
      let halfSpan := Q16_16.div (Q16_16.sub spec.high spec.low) (Q16_16.ofInt 2)
      let shifted := Q16_16.sub raw midpoint
      let lower := Q16_16.neg Q16_16.one
      clampQ16 (Q16_16.div shifted halfSpan) lower Q16_16.one

/-- Witness: an explicitly empty vector spec packs no coordinates. -/
theorem emptyCanonicalVectorWidth :
  ({ dimensions := [] } : CanonicalVectorSpec).dimensions.length = 0 := by
  native_decide

/-- Witness: the inhabited default spec exposes the historical 13-coordinate pack. -/
theorem defaultCanonicalPackLength :
  ((({} : CanonicalVectorSpec).pack CanonicalState.default).length) = 13 := by
  native_decide

/-- Witness: minmax normalization sends the lower bound to zero. -/
theorem minmaxNormalizationHitsZero :
  normalizeFeatureValue
    { name := "temperature", mode := .minmax, low := Q16_16.ofInt 10, high := Q16_16.ofInt 20 }
    (Q16_16.ofInt 10) = Q16_16.zero := by
  native_decide

end Semantics
