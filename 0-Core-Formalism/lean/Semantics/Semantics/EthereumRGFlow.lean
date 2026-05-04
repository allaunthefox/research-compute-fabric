import Semantics.SSMS
import Mathlib.Data.Nat.Basic

open Semantics.SSMS

namespace Semantics

/-! # Ethereum RGFlow Analysis

RGFlow analysis for Ethereum price data with proper sigma computation
from local price dynamics and RGFlow invariant lawfulness checking.

Key invariant: σ_q > 1 + λ·μ_q where:
- σ_q = scale stability (coherence) in Q16.16
- μ_q = drift rate in Q16.16
- λ = observer mass penalty in Q16.16 (typically 0.5 = 0x00008000)

Per AGENTS.md §4: Expressed as informational_bind instance.
-/

/-- Ethereum price position with RGFlow metrics. -/
structure EthereumPriceState where
  position : Nat  -- Index in price series
  price : Q1616   -- Price value in Q16.16
  sigma_q : Q1616 -- Scale stability
  mu_q : Q1616    -- Drift rate
  deriving Repr

/-- Informational bind for Bitcoin RGFlow analysis.
    bind : (EthereumPriceState × Q1616 × UInt32) → Bind EthereumPriceState Q1616
-/
structure EthereumRGFlowBind where
  lawful : Bool      -- RGFlow invariant: σ_q > 1 + λ·μ_q
  cost : UInt32      -- Binding cost in Q16.16
  invariant : String -- Extracted invariant description
  deriving Repr

/-- Informational bind instance for Bitcoin RGFlow.
    Checks lawfulness, computes cost, extracts invariant.
-/
def ethereumInformationalBind (state : EthereumPriceState) (_threshold : Q1616)
    (lambda : Q1616 := ⟨32768⟩) : EthereumRGFlowBind :=
  let lawful := state.sigma_q.raw > (Q1616.add Q1616.one (Q1616.mul lambda state.mu_q)).raw
  -- Cost function: penalize low sigma_q, reward high lawfulness
  let cost := if lawful then 0x00001000 else 0x00002000
  let lawfulStr := if lawful then "true" else "false"
  let invariant := s!"σ_q={state.sigma_q.raw}, μ_q={state.mu_q.raw}, lawful={lawfulStr}"
  { lawful := lawful, cost := cost, invariant := invariant }

/-- Rolling window computation for price series (List of Q16.16). -/
def rollingWindowQ16 (values : List Q1616) (i : Nat) (window : Nat) : List Q1616 :=
  let start := if i + 1 ≥ window then i + 1 - window else 0
  values.drop start |>.take (i + 1 - start)

/-- Division for Q16.16 (manual implementation since recip is partial). -/
def Q1616.divManual (a b : Q1616) : Q1616 :=
  if b.raw == 0 then Q1616.zero
  else ⟨(a.raw * 65536) / b.raw⟩

/-- Safe standard deviation computation for Q16.16 values. -/
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
    -- sqrt approximation for Q16.16: sqrt(x) ≈ x * (1.5 - 0.5*x) for x near 1
    let one := Q1616.one
    let oneHalf := ⟨32768⟩  -- 0.5 in Q16.16
    let threeHalf := ⟨49152⟩  -- 1.5 in Q16.16
    let varianceNorm := Q1616.divManual varianceScaled one
    let sqrtApprox := Q1616.mul varianceNorm (Q1616.sub threeHalf (Q1616.mul oneHalf varianceNorm))
    sqrtApprox

/-- Compute log returns from price series (Q16.16). -/
def logReturnsQ16 (prices : List Q1616) : List Q1616 :=
  if prices.length < 2 then []
  else
    let rec helper (i : Nat) (acc : List Q1616) : List Q1616 :=
      if i + 1 ≥ prices.length then acc.reverse
      else
        let p0 : Q1616 := prices[i]!
        let p1 : Q1616 := prices[i+1]!
        if p0.raw > 0 ∧ p1.raw > 0 then
          -- log(p1/p0) approximation using Q16.16
          let ratio := Q1616.divManual p1 p0
          -- log(x) ≈ (x-1) - (x-1)²/2 for x near 1
          let one := Q1616.one
          let diff := Q1616.sub ratio one
          let diffSquared := Q1616.mul diff diff
          let half := ⟨32768⟩  -- 0.5 in Q16.16
          let logApprox := Q1616.sub diff (Q1616.mul half diffSquared)
          helper (i + 1) (logApprox :: acc)
        else
          helper (i + 1) acc
    helper 0 []

/-- Compute σ_q (scale stability) from local price dynamics in Q16.16.
    σ_q = 1.0 + 0.35·coherence - 8.0·volatility
    where coherence = |mean| / (volatility + ε)
-/
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
      let epsilon := ⟨1⟩  -- Small epsilon in Q16.16
      let volPlusEpsilon := Q1616.add vol epsilon
      let coherence := Q1616.divManual absMean volPlusEpsilon
      let zero35 := ⟨22937⟩  -- 0.35 in Q16.16
      let eight := ⟨524288⟩  -- 8.0 in Q16.16
      let coherenceTerm := Q1616.mul zero35 coherence
      let volTerm := Q1616.mul eight vol
      let one := Q1616.one
      let raw := Q1616.sub (Q1616.add one coherenceTerm) volTerm
      -- Clamp to [0.25, 3.0] in Q16.16
      let minVal := ⟨16384⟩  -- 0.25 in Q16.16
      let maxVal := ⟨196608⟩  -- 3.0 in Q16.16
      let clamped := if raw.raw < minVal.raw then minVal else if raw.raw > maxVal.raw then maxVal else raw
      clamped

/-- RGFlow invariant check for lawfulness in Q16.16.
    A state is lawful iff σ_q > 1 + λ·μ_q
    where λ is observer mass penalty (typically 0.5 = 0x00008000)
-/
def isLawfulRGFlowQ16 (sigma_q : Q1616) (mu_q : Q1616) (lambda : Q1616 := ⟨32768⟩) : Bool :=
  let one := Q1616.one
  let lambdaMu := Q1616.mul lambda mu_q
  let threshold := Q1616.add one lambdaMu
  sigma_q.raw > threshold.raw

/-- Compute μ_q (drift rate) from local price dynamics in Q16.16.
    μ_q = average log return over window
-/
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

/-- Full RGFlow analysis for Ethereum price at position i in Q16.16.
    Returns (sigma_q, mu_q, lawful)
-/
def ethereumRGFlowAnalysisQ16 (prices : List Q1616) (i : Nat) (window : Nat := 30) : (Q1616 × Q1616 × Bool) :=
  let sigma_q := computeSigmaQQ16 prices i window
  let mu_q := computeMuQQ16 prices i window
  let lawful := isLawfulRGFlowQ16 sigma_q mu_q
  (sigma_q, mu_q, lawful)

/-- Batch RGFlow analysis for all positions in price series in Q16.16. -/
def batchEthereumRGFlowQ16 (prices : List Q1616) (window : Nat := 30) : List (Q1616 × Q1616 × Bool) :=
  let n := prices.length
  let rec helper (i : Nat) (acc : List (Q1616 × Q1616 × Bool)) : List (Q1616 × Q1616 × Bool) :=
    if i ≥ n then acc.reverse
    else helper (i + 1) ((ethereumRGFlowAnalysisQ16 prices i window) :: acc)
  helper 0 []

/-- Theorem: Lawful check returns Bool type (reflexivity). -/
theorem lawfulReflexive (sigma_q mu_q lambda : Q1616) :
    (isLawfulRGFlowQ16 sigma_q mu_q lambda) = (isLawfulRGFlowQ16 sigma_q mu_q lambda) := by
  rfl

end Semantics
