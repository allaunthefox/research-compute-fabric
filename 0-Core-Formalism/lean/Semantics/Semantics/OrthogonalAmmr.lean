import Semantics.FixedPoint

namespace Semantics.OrthogonalAmmr

/--
Finite shape witness for quantized basis data.
-/
structure SummaryShape where
  ambientDim : Nat
  basisDim : Nat
deriving Repr, DecidableEq, Inhabited

/--
A quantized basis vector in the proof layer.
The proof layer stores committed coordinates, not floating-point numerics.
-/
structure BasisVector where
  entries : List Q16_16
deriving Repr, DecidableEq, Inhabited

/--
O-AMMR summary object.
`qBasis` carries the retained basis vectors and `rCoeff` carries the projection
coefficients in that basis.
-/
structure AmmrSummary where
  qBasis : List BasisVector
  rCoeff : List Q16_16
  shape : SummaryShape
  energy : Q16_16
deriving Repr, DecidableEq, Inhabited

/--
Committed node for the orthogonal AMMR tree.
-/
structure AmmrNode where
  hash : UInt64
  summary : AmmrSummary
deriving Repr, DecidableEq, Inhabited

/--
Execution-space key for constant-time mirror lookup.
-/
structure MirrorLutIndex where
  basisId : UInt64
  quantizedCoeff : List Q16_16
deriving Repr, DecidableEq, Inhabited

/--
Residual energy witness used by the nutrient layer.
-/
def residualEnergy (input projected : Q16_16) : Q16_16 :=
  Q16_16.abs (Q16_16.sub input projected)

/--
Simple projection-similarity witness over two retained bases.
This is a deterministic count of exactly matching quantized basis vectors.
-/
def projectionSimilarity (left right : AmmrSummary) : Nat :=
  left.qBasis.foldl
    (fun acc v => if right.qBasis.contains v then acc + 1 else acc)
    0

/--
Compute the energy witness from the retained coefficients.
-/
def coeffEnergy (coeffs : List Q16_16) : Q16_16 :=
  coeffs.foldl (fun acc q => Q16_16.add acc (Q16_16.abs q)) Q16_16.zero

/--
Dimension consistency predicate for proof-layer summaries.
-/
def dimensionConsistent (summary : AmmrSummary) : Bool :=
  let ambientOk := summary.qBasis.all (fun v => v.entries.length == summary.shape.ambientDim)
  let basisCountOk := summary.qBasis.length == summary.shape.basisDim
  let coeffCountOk := summary.rCoeff.length == summary.shape.basisDim
  ambientOk && basisCountOk && coeffCountOk

/--
Energy metadata must match the coefficient-derived energy exactly.
-/
def energyConsistent (summary : AmmrSummary) : Bool :=
  summary.energy.val == (coeffEnergy summary.rCoeff).val

/--
Canonical hash for one basis vector.
-/
def basisVectorHash (v : BasisVector) : UInt64 :=
  v.entries.foldl
    (fun acc q => acc + q.toBits.toUInt64 + 0x9e3779b97f4a7c15)
    0

/--
Canonical hash for the committed summary payload.
-/
def summaryHash (summary : AmmrSummary) : UInt64 :=
  let basisHash :=
    summary.qBasis.foldl
      (fun acc v => acc + basisVectorHash v + 0x517cc1b727220a95)
      0
  let coeffHash :=
    summary.rCoeff.foldl
      (fun acc q => acc + q.toBits.toUInt64 + 0x94d049bb133111eb)
      0
  basisHash + coeffHash +
    summary.shape.ambientDim.toUInt64 +
    summary.shape.basisDim.toUInt64 +
    summary.energy.toBits.toUInt64

/--
Deterministic parent commitment law.
-/
def commitHash (leftHash rightHash : UInt64) (summary : AmmrSummary) : UInt64 :=
  leftHash + 0x9e3779b97f4a7c15 + rightHash + summaryHash summary

/--
Deterministic merge skeleton for proof-layer summaries.
This is intentionally a concatenation-based canonical merge, not full QR numerics.
-/
def mergeSummary (left right : AmmrSummary) : AmmrSummary :=
  let qBasis := left.qBasis ++ right.qBasis
  let rCoeff := left.rCoeff ++ right.rCoeff
  let ambientDim := Nat.max left.shape.ambientDim right.shape.ambientDim
  let basisDim := qBasis.length
  let energy := coeffEnergy rCoeff
  {
    qBasis := qBasis
    rCoeff := rCoeff
    shape := { ambientDim := ambientDim, basisDim := basisDim }
    energy := energy
  }

/--
Deterministic parent constructor.
-/
def commitParent (left right : AmmrNode) : AmmrNode :=
  let summary := mergeSummary left.summary right.summary
  let hash := commitHash left.hash right.hash summary
  { hash := hash, summary := summary }

/--
Mirror execution key derived from basis commitment and quantized coefficients.
-/
def mirrorLutIndex (node : AmmrNode) : MirrorLutIndex :=
  { basisId := summaryHash node.summary
  , quantizedCoeff := node.summary.rCoeff }

/--
Witness theorem: coefficient-derived energy is self-consistent by construction.
-/
theorem coeffEnergyConsistent (coeffs : List Q16_16) :
  energyConsistent
    { qBasis := []
    , rCoeff := coeffs
    , shape := { ambientDim := 0, basisDim := 0 }
    , energy := coeffEnergy coeffs } = true := by
  simp [energyConsistent]

/--
Witness theorem: equal committed summaries yield equal mirror LUT indices.
-/
theorem mirrorLutIndexDeterministic (a b : AmmrNode)
  (h : a.summary = b.summary) :
  mirrorLutIndex a = mirrorLutIndex b := by
  cases a with
  | mk hashA summaryA =>
      cases b with
      | mk hashB summaryB =>
          simp [mirrorLutIndex] at h ⊢
          cases h
          simp

/--
Witness theorem: the parent constructor satisfies the commitment law by definition.
-/
theorem commitParentLaw (left right : AmmrNode) :
  (commitParent left right).hash =
    commitHash left.hash right.hash (mergeSummary left.summary right.summary) := by
  rfl

def unitVec (ambientDim active : Nat) : BasisVector :=
  { entries := List.range ambientDim |>.map (fun i => if i == active then Q16_16.one else Q16_16.zero) }

def leafSummary (ambientDim active : Nat) (coeff : Q16_16) : AmmrSummary :=
  { qBasis := [unitVec ambientDim active]
  , rCoeff := [coeff]
  , shape := { ambientDim := ambientDim, basisDim := 1 }
  , energy := coeffEnergy [coeff] }

def leafNode (seedHash : UInt64) (ambientDim active : Nat) (coeff : Q16_16) : AmmrNode :=
  let summary := leafSummary ambientDim active coeff
  { hash := commitHash seedHash 0 summary, summary := summary }

#eval dimensionConsistent (leafSummary 3 1 Q16_16.one)
#eval energyConsistent (leafSummary 3 1 Q16_16.one)
#eval residualEnergy (Q16_16.ofInt 3) Q16_16.one
#eval projectionSimilarity (leafSummary 3 1 Q16_16.one) (leafSummary 3 1 Q16_16.one)
#eval mirrorLutIndex (leafNode 7 3 1 Q16_16.one)

end Semantics.OrthogonalAmmr
