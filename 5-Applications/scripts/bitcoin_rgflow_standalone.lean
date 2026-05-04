import Std

/-! Bitcoin RGFlow Standalone Script

Standalone Lean script for Bitcoin RGFlow analysis.
-/

/-! ## Q16.16 Fixed-Point Type -/

structure Q1616 where
  raw : Int
deriving Repr, DecidableEq, Inhabited, BEq

namespace Q1616

def zero : Q1616 := ⟨0⟩
def one : Q1616 := ⟨65536⟩

def add (a b : Q1616) : Q1616 := ⟨a.raw + b.raw⟩
def sub (a b : Q1616) : Q1616 := ⟨b.raw - a.raw⟩
def mul (a b : Q1616) : Q1616 := ⟨(a.raw * b.raw) / 65536⟩

def divManual (a b : Q1616) : Q1616 :=
  if b.raw == 0 then zero
  else ⟨(a.raw * 65536) / b.raw⟩

def abs (a : Q1616) : Q1616 := ⟨if a.raw < 0 then -a.raw else a.raw⟩

def min (a b : Q1616) : Q1616 := if a.raw <= b.raw then a else b
def max (a b : Q1616) : Q1616 := if a.raw >= b.raw then a else b

def clamp (lo hi x : Q1616) : Q1616 := max lo (min hi x)

def le (a b : Q1616) : Bool := a.raw <= b.raw
def lt (a b : Q1616) : Bool := a.raw < b.raw
def ge (a b : Q1616) : Bool := a.raw >= b.raw
def gt (a b : Q1616) : Bool := a.raw > b.raw

end Q1616

/-! ## Bitcoin RGFlow Analysis -/

def rollingWindowQ16 (values : List Q1616) (i : Nat) (window : Nat) : List Q1616 :=
  let start := if i + 1 ≥ window then i + 1 - window else 0
  values.drop start |>.take (i + 1 - start)

def safeStdQ16 (xs : List Q1616) : Q1616 :=
  if xs.length ≤ 1 then Q1616.zero
  else
    let mean := xs.foldl (λ acc x => Q1616.add acc x) Q1616.zero
    let meanScaled := ⟨mean.raw / xs.length⟩
    let variance := xs.foldl (λ acc x =>
      let diff := Q1616.sub x meanScaled
      let diffScaled := Q1616.mul diff diff
      Q1616.add acc diffScaled
    ) Q1616.zero
    let varianceScaled := ⟨variance.raw / xs.length⟩
    let one := Q1616.one
    let oneHalf := ⟨32768⟩
    let threeHalf := ⟨49152⟩
    let varianceNorm := Q1616.divManual varianceScaled one
    let sqrtApprox := Q1616.mul varianceNorm (Q1616.sub threeHalf (Q1616.mul oneHalf varianceNorm))
    sqrtApprox

def logReturnsQ16 (prices : List Q1616) : List Q1616 :=
  if prices.length < 2 then []
  else
    let rec helper (i : Nat) (acc : List Q1616) : List Q1616 :=
      if i + 1 ≥ prices.length then acc.reverse
      else
        let p0 : Q1616 := prices[i]!
        let p1 : Q1616 := prices[i+1]!
        if p0.raw > 0 ∧ p1.raw > 0 then
          let ratio := Q1616.divManual p1 p0
          let one := Q1616.one
          let diff := Q1616.sub ratio one
          let diffSquared := Q1616.mul diff diff
          let half := ⟨32768⟩
          let logApprox := Q1616.sub diff (Q1616.mul half diffSquared)
          helper (i + 1) (logApprox :: acc)
        else
          helper (i + 1) acc
    helper 0 []

def computeSigmaQQ16 (prices : List Q1616) (i : Nat) (window : Nat := 30) : Q1616 :=
  let returns := logReturnsQ16 prices
  if returns.length < 2 then Q1616.one
  else
    let ri := if i == 0 then 0 else i - 1
    let windowData := rollingWindowQ16 returns ri window
    if windowData.length < 2 then Q1616.one
    else
      let vol := safeStdQ16 windowData
      let mean := windowData.foldl (λ acc x => Q1616.add acc x) Q1616.zero
      let meanScaled := ⟨mean.raw / windowData.length⟩
      let absMean := if meanScaled.raw < 0 then ⟨-meanScaled.raw⟩ else meanScaled
      let epsilon := ⟨1⟩
      let volPlusEpsilon := Q1616.add vol epsilon
      let coherence := Q1616.divManual absMean volPlusEpsilon
      let zero35 := ⟨22937⟩
      let eight := ⟨524288⟩
      let coherenceTerm := Q1616.mul zero35 coherence
      let volTerm := Q1616.mul eight vol
      let one := Q1616.one
      let rawValue := Q1616.sub (Q1616.add one coherenceTerm) volTerm
      let minVal := ⟨16384⟩
      let maxVal := ⟨196608⟩
      let clamped := Q1616.clamp minVal maxVal rawValue
      clamped

def computeMuQQ16 (prices : List Q1616) (i : Nat) (window : Nat := 30) : Q1616 :=
  let returns := logReturnsQ16 prices
  if returns.length < 2 then Q1616.zero
  else
    let ri := if i == 0 then 0 else i - 1
    let windowData := rollingWindowQ16 returns ri window
    if windowData.length < 2 then Q1616.zero
    else
      let sum := windowData.foldl (λ acc x => Q1616.add acc x) Q1616.zero
      ⟨sum.raw / windowData.length⟩

def isLawfulRGFlowQ16 (sigma_q : Q1616) (mu_q : Q1616) (lambda : Q1616 := ⟨32768⟩) : Bool :=
  let one := Q1616.one
  let lambdaMu := Q1616.mul lambda mu_q
  let threshold := Q1616.add one lambdaMu
  sigma_q.raw > threshold.raw

def bitcoinRGFlowAnalysisQ16 (prices : List Q1616) (i : Nat) (window : Nat := 30) : (Q1616 × Q1616 × Bool) :=
  let sigma_q := computeSigmaQQ16 prices i window
  let mu_q := computeMuQQ16 prices i window
  let lawful := isLawfulRGFlowQ16 sigma_q mu_q
  (sigma_q, mu_q, lawful)

def batchBitcoinRGFlowQ16 (prices : List Q1616) (window : Nat := 30) : List (Q1616 × Q1616 × Bool) :=
  let n := prices.length
  let rec helper (i : Nat) (acc : List (Q1616 × Q1616 × Bool)) : List (Q1616 × Q1616 × Bool) :=
    if i ≥ n then acc.reverse
    else helper (i + 1) ((bitcoinRGFlowAnalysisQ16 prices i window) :: acc)
  helper 0 []

/-! ## Demo with Sample Bitcoin Prices -/

def samplePrices : List Q1616 :=
  -- Sample Bitcoin prices in Q16.16 (scaled from actual prices)
  [⟨17810⟩, ⟨22000⟩, ⟨31000⟩, ⟨29000⟩, ⟨43000⟩, ⟨90000⟩,
   ⟨65000⟩, ⟨120000⟩, ⟨80000⟩, ⟨1900000⟩, ⟨350000⟩, ⟨1000000⟩,
   ⟨6900000⟩, ⟨1600000⟩, ⟨7700000⟩]

#eval
  let prices := samplePrices
  let results := batchBitcoinRGFlowQ16 prices 5
  let lawfulCount := results.foldl (λ acc r => if r.2.2 then acc + 1 else acc) 0
  let sigmaValues := results.map (λ r => r.2.1.raw)
  let sigmaMin := sigmaValues.foldl (λ acc r => if r < acc then r else acc) 1000000
  let sigmaMax := sigmaValues.foldl (λ acc r => if r > acc then r else acc) 0
  s!"Total: {results.length}, Lawful: {lawfulCount}, Sigma range: {sigmaMin}-{sigmaMax}"
