/-
  MISignal.lean - Mutual Information Signal Processing Bindings
  Ports rows 72-76 from MATH_MODEL_MAP.tsv (Python → Lean).

  All values are Q16.16. Bits-per-byte range [0, 8] maps to [0, 8·65536].
-/
import Semantics.Bind
import Semantics.FixedPoint

namespace Semantics.MISignal

open Q16_16

def epsilon : Q16_16 := ⟨1⟩

-- Scale constant: 8.0 in Q16.16 = 8 * 65536
def bitsPerByteMax : Q16_16 := ⟨8 * 65536⟩

structure MIRecord where
  baselineBpb : Q16_16   -- baseline bits-per-byte (uncompressed context)
  actualBpb   : Q16_16   -- actual bits-per-byte achieved
  miPredicted : Q16_16   -- kNN-predicted MI value
deriving Repr, Inhabited, DecidableEq

-- Row 72: MI(x) = baseline_bpb - actual_bpb
-- Mutual information extracted through compression improvement
def mutualInformationSignal (r : MIRecord) : Q16_16 :=
  if r.baselineBpb.val ≥ r.actualBpb.val
  then sub r.baselineBpb r.actualBpb
  else zero

-- Row 73: MI_pred = Σ(w_i · MI_i · S_i) / Σ(w_i · S_i)
-- kNN weighted MI prediction; w_i = 1/(d_i + ε)
-- distances, mis, similarities are parallel arrays
def knnMIPrediction (distances mis similarities : Array Q16_16) : Q16_16 :=
  let n := distances.size
  if n == 0 || mis.size != n || similarities.size != n then zero
  else
    let num := Array.foldl (fun acc i =>
      let w := div one (add distances[i]! epsilon)
      add acc (mul (mul w mis[i]!) similarities[i]!)
    ) zero (Array.range n)
    let den := Array.foldl (fun acc i =>
      let w := div one (add distances[i]! epsilon)
      add acc (mul w similarities[i]!)
    ) zero (Array.range n)
    if den.val == 0 then zero else div num den

-- Row 74: surprise = log(1 + |MI_actual - MI_predicted|)
-- Approximated in Q16.16: surprise ≈ |diff| (natural log not available in integer—use diff directly as ordinal surprise)
def surpriseMetric (r : MIRecord) : Q16_16 :=
  let miActual := mutualInformationSignal r
  let diff := abs (sub miActual r.miPredicted)
  -- log(1+x) ≈ x for small x; represent as direct delta in Q16.16
  add one diff

-- Row 75: ρ(x) = MI(x) / (cost(x) + ε)
-- Structure yield: information per unit compute cost
def structureYield (mi cost : Q16_16) : Q16_16 :=
  div mi (add cost epsilon)

-- Row 76: d(z₁, z₂) = √( Σ w_i · ((z₁_i - z₂_i) / s_i)² )
-- Weighted feature distance over 9-dim vector
-- Uses integer arithmetic: no float sqrt; return squared distance as cost proxy
def weightedFeatureDistanceSq (z1 z2 weights scales : Array Q16_16) : Q16_16 :=
  let n := z1.size
  if n == 0 then zero
  else
    Array.foldl (fun acc i =>
      if i < z2.size && i < weights.size && i < scales.size then
        let diff := abs (sub z1[i]! z2[i]!)
        let scaled := div diff (add scales[i]! epsilon)
        let sq := mul scaled scaled
        add acc (mul weights[i]! sq)
      else acc
    ) zero (Array.range n)

def miInvariant (r : MIRecord) : String :=
  s!"mi:baseline={r.baselineBpb.val},actual={r.actualBpb.val}"

def miCost (a b : MIRecord) (_m : Metric) : Q16_16 :=
  let ma := mutualInformationSignal a
  let mb := mutualInformationSignal b
  Q16_16.ofNat (abs (sub ma mb)).val.toNat

def miSignalBind (a b : MIRecord) (m : Metric) : Bind MIRecord MIRecord :=
  informationalBind a b m miCost miInvariant miInvariant

-- Verify
#eval mutualInformationSignal { baselineBpb := ⟨5 * 65536⟩, actualBpb := ⟨3 * 65536⟩, miPredicted := ⟨2 * 65536⟩ }
#eval surpriseMetric { baselineBpb := ⟨5 * 65536⟩, actualBpb := ⟨3 * 65536⟩, miPredicted := ⟨65536⟩ }

end Semantics.MISignal
