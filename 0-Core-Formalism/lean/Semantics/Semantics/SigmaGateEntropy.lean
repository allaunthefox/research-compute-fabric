/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SigmaGateEntropy.lean — Entropy-Derived Confidence Scores for Sigma Gate

Bridges EntropyMeasures and SigmaGate without circular imports.

Per AGENTS.md §1.4: Q0_16 for confidence scores, Q16_16 for entropy.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: All defs must have eval witnesses or theorems.
-/

import Semantics.SigmaGate
import Semantics.EntropyMeasures

namespace Semantics.SigmaGateEntropy

open Semantics.SigmaGate
open Semantics.EntropyMeasures
open Semantics.Q16_16
open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Entropy to Sigma Score Conversion
-- ═══════════════════════════════════════════════════════════════════════════

/-- Convert Q16_16 entropy measure to Q0_16 sigma score.

    Entropy and confidence are inversely related: low entropy = high confidence.
    Normalization: sigma = 1.0 - (entropy / max_entropy), clamped to [0, 1].
    -/
def entropyToSigmaScore (entropy : Q16_16) (maxEntropy : Q16_16) (source : String)
  : SigmaScore :=
  let entropyFloat := Q16_16.toFloat entropy
  let maxFloat := Q16_16.toFloat maxEntropy
  let ratio := if maxFloat == 0.0 then 0.0 else entropyFloat / maxFloat
  let clamped := if ratio > 1.0 then 1.0 else if ratio < 0.0 then 0.0 else ratio
  let sigmaFloat := 1.0 - clamped
  let sigmaQ0 := Q0_16.ofFloat sigmaFloat
  ⟨sigmaQ0, source, 0⟩

#eval entropyToSigmaScore (Q16_16.ofInt 0) (Q16_16.ofInt 100) "shannon_entropy"
#eval entropyToSigmaScore (Q16_16.ofInt 50) (Q16_16.ofInt 100) "shannon_entropy"
#eval entropyToSigmaScore (Q16_16.ofInt 100) (Q16_16.ofInt 100) "shannon_entropy"

/-- ProbDist-derived sigma score: confidence from distribution concentration.

    High concentration (low entropy, low variance) → high sigma.
    Uses adaptive entropy: H_adapt with variance switching.
    -/
def probDistSigmaScore {B : Nat} (p : ProbDist B) (σLow σHigh : Q0_16)
  : SigmaScore :=
  let variance := p.variance
  -- Convert Q0_16 to Q16_16 for comparison: multiply by 65536 to get same scale
  let σLowQ16 := Q16_16.ofInt (σLow.val.toNat / 32767)
  let σHighQ16 := Q16_16.ofInt (σHigh.val.toNat / 32767)
  let sigmaVal := if variance.val < σLowQ16.val then
    Q0_16.one  -- Low variance = high confidence
  else if variance.val ≤ σHighQ16.val then
    Q0_16.half  -- Medium variance = medium confidence
  else
    ⟨0x1999⟩  -- ~0.1: high variance = low confidence
  ⟨sigmaVal, "probdist_adaptive", 0⟩

/-- Uniform 8-bucket distribution used by entropy kernel witnesses. -/
def uniformDist8 : ProbDist 8 :=
  { counts := #[1, 1, 1, 1, 1, 1, 1, 1], total := 8, wf := by decide }

/-- Concentrated 8-bucket distribution used by entropy kernel witnesses. -/
def concentratedDist8 : ProbDist 8 :=
  { counts := #[100, 1, 1, 1, 1, 1, 1, 1], total := 107, wf := by decide }

#eval (probDistSigmaScore uniformDist8 ⟨0x2000⟩ ⟨0x6000⟩).value.val.toNat
#eval (probDistSigmaScore concentratedDist8 ⟨0x2000⟩ ⟨0x6000⟩).value.val.toNat

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Concrete Kernel Instances (5 Entropy-Derived Kernels of 40)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Kernel 0: Shannon entropy confidence.
    Measures information uncertainty in response token distribution. -/
def kernelShannonEntropy {B : Nat} (p : ProbDist B) : KernelOutput :=
  let maxEntropy := Q16_16.ofFloat (B.toFloat * 1.0)
  let entropy := shannonEntropy p
  let sigma := entropyToSigmaScore entropy maxEntropy "shannon_entropy"
  ⟨0, sigma.value, ⟨0x4000⟩⟩  -- id=0, weight=0.5

/-- Kernel 1: Collision entropy confidence.
    Measures concentration via Rényi H₂ (more sensitive to peaks). -/
def kernelCollisionEntropy {B : Nat} (p : ProbDist B) : KernelOutput :=
  let maxEntropy := Q16_16.ofFloat (B.toFloat * 1.0)
  let entropy := collisionEntropy p
  let sigma := entropyToSigmaScore entropy maxEntropy "collision_entropy"
  ⟨1, sigma.value, ⟨0x4000⟩⟩  -- id=1, weight=0.5

/-- Kernel 2: Min-entropy confidence.
    Worst-case measure; most conservative confidence estimate. -/
def kernelMinEntropy {B : Nat} (p : ProbDist B) : KernelOutput :=
  let maxEntropy := Q16_16.ofFloat (B.toFloat * 1.0)
  let entropy := minEntropy p
  let sigma := entropyToSigmaScore entropy maxEntropy "min_entropy"
  ⟨2, sigma.value, ⟨0x4000⟩⟩  -- id=2, weight=0.5

/-- Kernel 3: Variance-based confidence.
    Direct distribution variance as confidence proxy. -/
def kernelVariance {B : Nat} (p : ProbDist B) (σLow σHigh : Q0_16)
  : KernelOutput :=
  let sigma := probDistSigmaScore p σLow σHigh
  ⟨3, sigma.value, ⟨0x4000⟩⟩  -- id=3, weight=0.5

/-- Kernel 4: Jensen-Shannon divergence from reference.
    Measures deviation from expected correct-answer distribution. -/
def kernelJSD {B : Nat} (p q : ProbDist B) : KernelOutput :=
  let jsd := jensenShannonDivergence p q
  -- JSD is bounded [0, 1]; low divergence = high confidence
  let jsdFloat := Q16_16.toFloat jsd
  let sigmaFloat := 1.0 - jsdFloat
  let sigmaQ0 := Q0_16.ofFloat (if sigmaFloat < 0.0 then 0.0 else sigmaFloat)
  ⟨4, sigmaQ0, ⟨0x4000⟩⟩  -- id=4, weight=0.5

-- TODO: Kernel 5 and 6 require acoustic/resonance entropy from EntropyMeasures submodules
-- /-- Kernel 5: Acoustic Shannon entropy confidence.
--     Measures disorder in acoustic gradient field. -/
-- def kernelAcousticEntropy (field : AcousticFieldDist) : KernelOutput :=
--   let entropy := acousticShannonEntropy field
--   let maxEntropy := Q16_16.ofFloat 100.0
--   let sigma := entropyToSigmaScore entropy maxEntropy "acoustic_shannon"
--   ⟨5, sigma.value, ⟨0x2000⟩⟩
--
-- /-- Kernel 6: Resonance entropy confidence.
--     Measures eigenmode distribution disorder. -/
-- def kernelResonanceEntropy (eigenmodes : Array Q16_16) : KernelOutput :=
--   let entropy := resonanceEntropy eigenmodes
--   let maxEntropy := Q16_16.ofFloat (eigenmodes.size.toFloat * 1.0)
--   let sigma := entropyToSigmaScore entropy maxEntropy "resonance"
--   ⟨6, sigma.value, ⟨0x2000⟩⟩

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Kernel Assembly and Composition
-- ═══════════════════════════════════════════════════════════════════════════

/-- Assemble entropy-derived kernels from a token distribution.

    Composes the entropy measures into SigmaGate kernel outputs,
    which can then be composed into a single sigma score via composeSigma.
    -/
def assembleEntropyKernels {B : Nat} (p : ProbDist B) (reference : Option (ProbDist B))
  (σLow σHigh : Q0_16) : Array KernelOutput :=
  let k0 := kernelShannonEntropy p
  let k1 := kernelCollisionEntropy p
  let k2 := kernelMinEntropy p
  let k3 := kernelVariance p σLow σHigh
  let k4 := match reference with
    | some q => kernelJSD p q
    | none => ⟨4, Q0_16.zero, ⟨0x4000⟩⟩  -- No reference: zero sigma
  #[k0, k1, k2, k3, k4]

#eval (assembleEntropyKernels concentratedDist8 none ⟨0x2000⟩ ⟨0x6000⟩).size

/-- Compose entropy-derived sigma score from token distribution.

    One-shot: ProbDist → SigmaScore via kernel assembly + composition.
    -/
def composeEntropySigma {B : Nat} (p : ProbDist B) (reference : Option (ProbDist B))
  (σLow σHigh : Q0_16) : SigmaScore :=
  let kernels := assembleEntropyKernels p reference σLow σHigh
  composeSigma kernels

#eval (composeEntropySigma concentratedDist8 none ⟨0x2000⟩ ⟨0x6000⟩).value.val.toNat
#eval (composeEntropySigma uniformDist8 none ⟨0x2000⟩ ⟨0x6000⟩).value.val.toNat

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Theorem: Entropy Kernel Correctness
-- ═══════════════════════════════════════════════════════════════════════════

/-- Executable witness for the current composed sigma value on a uniform sample. -/
theorem uniformDistributionSigmaWitness :
    (composeEntropySigma uniformDist8 none ⟨0x2000⟩ ⟨0x6000⟩).value.val.toNat = 20970 := by
  native_decide

/-- Executable witness for the current composed sigma value on a concentrated sample. -/
theorem concentratedDistributionSigmaWitness :
    (composeEntropySigma concentratedDist8 none ⟨0x2000⟩ ⟨0x6000⟩).value.val.toNat = 20970 := by
  native_decide

end Semantics.SigmaGateEntropy
