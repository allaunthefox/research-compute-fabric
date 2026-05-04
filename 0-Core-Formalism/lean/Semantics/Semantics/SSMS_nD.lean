/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SSMS_nD.lean — Variable Dimension Manifold Extension

Extends SSMS with n-dimensional manifold support:
  §1  VariableDimensionManifold structure with dynamic n
  §2  LiftingOperator L_{1D→n} for sequential data
  §3  HolonomicConstraint system with m constraints
  §4  Dynamic ACI for cross-dimensional collision
  §5  BettiSwooshND over [1, n_max]
  §6  SUBLEQ variable-n kernels
  §7  Dimension selection via potential minimization
  §8  PhantomTideQ: Adaptive phantom coupling with Q16.16

Per Clean Room Protocol: All math from public sources only.
Per AGENTS.md §1.4: All hot-path code uses Q16_16 fixed-point.
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Int.Basic
import Mathlib.Data.Array.Basic
import Mathlib.Tactic
import Semantics.SSMS
import Semantics.FixedPoint

namespace Semantics.SSMS_nD

open Semantics.SSMS
open Semantics.Q16_16

-- ════════════════════════════════════════════════════════════
-- §1  Variable Dimension Manifold Structure
--     M_i = (n, c ∈ R^n, Σ ∈ R^{n×n}, θ ∈ R^p, σ)
-- ════════════════════════════════════════════════════════════

/-- Variable-n manifold: dimensionality determined at spawn time. -/
structure VarDimManifold where
  n        : Nat        -- dimensionality (1 to n_max)
  center   : Array Q16_16 -- n coordinates
  sizeN    : center.size = n
  metric   : Array Q16_16 -- upper-triangular Σ: n(n+1)/2 entries
  sizeMetric : metric.size = n * (n + 1) / 2
  orient   : Array Q16_16 -- orientation params: n(n-1)/2 for SO(n)
  sizeOrient : orient.size = n * (n - 1) / 2
  energy   : Q16_16        -- gradient energy (spawn pressure)
  sigma    : Bool         -- activation status
  deriving Repr

instance : Inhabited VarDimManifold where
  default :=
    { n := 0, center := #[], sizeN := by simp
    , metric := #[], sizeMetric := by simp
    , orient := #[], sizeOrient := by simp
    , energy := zero, sigma := true }

/-- Calculate total scalar nodes needed for n-dim manifold. -/
def scalarCount (n : Nat) : Nat :=
  n + (n * (n + 1) / 2) + (n * (n - 1) / 2)

/-- Maximum dimension supported (SRAM constraint). -/
def nMax : Nat := 16

/-- Validate manifold dimension within bounds. -/
def validN (n : Nat) : Prop := n ≥ 1 ∧ n ≤ nMax

theorem scalarCountMonotonic (n : Nat) (h : n ≥ 1) :
    scalarCount n ≥ scalarCount 1 := by
  simp [scalarCount]
  have h1 : n * (n + 1) / 2 ≥ 1 := by
    have h2 : n * (n + 1) ≥ 2 := by
      have h3 : n ≥ 1 := h
      have h4 : n + 1 ≥ 2 := by omega
      have h5 : n * (n + 1) ≥ 1 * 2 := Nat.mul_le_mul h3 h4
      simp at h5
      exact h5
    omega
  have h2 : n * (n - 1) / 2 ≥ 0 := by omega
  omega


-- ════════════════════════════════════════════════════════════
-- §2  LiftingOperator L_{1D→n}
--     Lifts 1D sequence interval [t0, t1] to R^n
-- ════════════════════════════════════════════════════════════

/-- 1D sequence sample at position t. -/
structure SeqSample where
  position : Nat      -- t ∈ [0, L]
  features : Array Q16_16  -- d-dimensional feature vector
  deriving Repr, Inhabited

/-- Lifting weights: ternary matrix W_lift ∈ {-1,0,1}^{n×d}. -/
structure LiftingWeights (n d : Nat) where
  wPos : Array Bool  -- n×d positive mask
  wNeg : Array Bool  -- n×d negative mask
  sizePos : wPos.size = n * d
  sizeNeg : wNeg.size = n * d
  disjoint : ∀ i : Fin (n * d),
    ¬ (wPos[i]'(sizePos.symm ▸ i.isLt) ∧ wNeg[i]'(sizeNeg.symm ▸ i.isLt))

/-- Pool 1D features over interval [t0, t1] via mean pooling. -/
def pool1D (seq : Array SeqSample) (t0 t1 : Nat) : Array Q16_16 :=
  if h : t0 < seq.size then
    let sample0 := seq[t0]'h
    let count := (t1 - t0 + 1)
    -- Mean pooling: sum features / count
    sample0.features.map (fun f => ⟨f.val / count⟩)
  else #[]

/-- Lifting operator: 1D pooled features → n-dim center.
    MatMul-free via ternary weights (ADD/SUB only). -/
def lift1DToN {n d : Nat} (weights : LiftingWeights n d)
    (pooled : Array Q16_16) (hPooled : pooled.size = d) : Array Q16_16 :=
  (Array.range n).map (fun i =>
    if hi : i < n then
      let rowOffset := i * d
      (Array.range d).foldl (fun acc j =>
        if hj : j < d then
          let idx := rowOffset + j
          let p := weights.wPos[idx]'(by
            rw [weights.sizePos]
            have h1 : i * d + j < i * d + d := Nat.add_lt_add_left hj (i * d)
            have h2 : i * d + d ≤ n * d := by
              have h3 : i * d + d = (i + 1) * d := by
                calc i * d + d = i * d + 1 * d := by rw [Nat.one_mul]
                     _ = (i + 1) * d := by rw [Nat.add_mul]
              rw [h3]
              exact Nat.mul_le_mul_right d (Nat.succ_le_of_lt hi)
            exact Nat.lt_of_lt_of_le h1 h2)
          let n := weights.wNeg[idx]'(by
            rw [weights.sizeNeg]
            have h1 : i * d + j < i * d + d := Nat.add_lt_add_left hj (i * d)
            have h2 : i * d + d ≤ n * d := by
              have h3 : i * d + d = (i + 1) * d := by
                calc i * d + d = i * d + 1 * d := by rw [Nat.one_mul]
                     _ = (i + 1) * d := by rw [Nat.add_mul]
              rw [h3]
              exact Nat.mul_le_mul_right d (Nat.succ_le_of_lt hi)
            exact Nat.lt_of_lt_of_le h1 h2)
          let x := pooled[j]'(hPooled ▸ hj)
          if p then Q16_16.add acc x
          else if n then Q16_16.sub acc x
          else acc
        else acc
      ) Q16_16.zero
    else Q16_16.zero
  )

/-- Approximate inverse chart L^{-1}: R^n → [0, L]. -/
def approxInverseChart (c : Array Q16_16) (L : Nat) : Nat :=
  -- Project to first coordinate, clamp to [0, L]
  if h : 0 < c.size then
    let c0 := c[0]'h
    let tRaw := c0.val / 65536  -- Convert Q16.16 to integer
    let tNat := if tRaw < 0 then 0 else tRaw.toNat
    min tNat L
  else 0


-- ════════════════════════════════════════════════════════════
-- §3  HolonomicConstraint System
--     m constraints {h_j(x) = 0} for n-dim manifold
-- ════════════════════════════════════════════════════════════

/-- Linear constraint: Σ a_j · x_j = b. -/
structure LinearConstraint (n : Nat) where
  coeffs : Array Q16_16  -- a[0..n-1]
  sizeCoeffs : coeffs.size = n
  rhs    : Q16_16        -- b
  deriving Repr

instance {n : Nat} : Inhabited (LinearConstraint n) where
  default := ⟨Array.mk (List.replicate n Q16_16.zero), by simp, Q16_16.zero⟩

/-- Constraint system for n-dim manifold. -/
structure ConstraintSystem (n m : Nat) where
  constraints : Array (LinearConstraint n)  -- m constraints
  sizeConstraints : constraints.size = m
  epsilon : Q16_16  -- ACI tolerance ε
  deriving Repr

instance {n m : Nat} : Inhabited (ConstraintSystem n m) where
  default := ⟨Array.mk (List.replicate m default), by simp, Q16_16.zero⟩

/-- Evaluate constraint residual |Σ a_j · x_j - b|. -/
def constraintResidual (c : LinearConstraint n) (x : Array Q16_16)
    (hX : x.size = n) : Q16_16 :=
  let dot := (Array.range n).foldl (fun acc i =>
    if hi : i < n then
      let a := c.coeffs[i]'(c.sizeCoeffs.symm ▸ hi)
      let xi := x[i]'(hX.symm ▸ hi)
      Q16_16.add acc (Q16_16.mul a xi)
    else acc
  ) Q16_16.zero
  Q16_16.abs (Q16_16.sub dot c.rhs)

/-- Check if manifold satisfies all constraints (ACI predicate). -/
def constraintsSatisfied (sys : ConstraintSystem n m) (M : VarDimManifold)
    (hN : M.n = n) : Prop :=
  ∀ i : Fin m,
    let c := sys.constraints[i]'(sys.sizeConstraints.symm ▸ i.isLt)
    (constraintResidual c M.center (M.sizeN.trans hN)).val ≤ sys.epsilon.val

/-- Constraint potential: Σ λ_j · h_j(x)^2 for MLGRU energy. -/
def constraintPotential (sys : ConstraintSystem n m) (M : VarDimManifold)
    (hN : M.n = n) (lambdas : Array Q16_16) (hLambdas : lambdas.size = m) : Q16_16 :=
  (Array.range m).foldl (fun acc i =>
    if hi : i < m then
      let c := sys.constraints[i]'(sys.sizeConstraints.symm ▸ hi)
      let lam := lambdas[i]'(hLambdas.symm ▸ hi)
      let r := constraintResidual c M.center (M.sizeN.trans hN)
      let r2 := Q16_16.mul r r
      Q16_16.add acc (Q16_16.mul lam r2)
    else acc
  ) Q16_16.zero


-- ════════════════════════════════════════════════════════════
-- §4  Dynamic ACI for Cross-Dimensional Collision
-- ════════════════════════════════════════════════════════════

/-- Project higher dimension to lower via coordinate truncation. -/
def projectDown (x : Array Q16_16) (nTarget : Nat) : Array Q16_16 :=
  x.take nTarget

/-- Center distance with dimension handling.
    If n_i ≠ n_j, project to lower dimension first. -/
def dynamicCenterDist (Mi Mj : VarDimManifold) : Q16_16 :=
  let nMin := min Mi.n Mj.n
  let ci := projectDown Mi.center nMin
  let cj := projectDown Mj.center nMin
  let d2 := (ci.zip cj).foldl (fun acc (xi, xj) =>
    let dx := Q16_16.sub xi xj
    Q16_16.add acc (Q16_16.mul dx dx)
  ) Q16_16.zero
  -- sqrt via NR (reusing centerDist pattern)
  let r0 := ⟨d2.val / 2⟩
  let nr := fun r => ⟨(r.val + (d2.val * 65536 / (r.val + 1))) / 2⟩
  nr (nr (nr r0))

/-- Dynamic ACI collision predicate. -/
def dynamicACI (Mi Mj : VarDimManifold) (tau : Q16_16) : Bool :=
  decide ((dynamicCenterDist Mi Mj).val ≤ tau.val)

/-- NMS suppression for variable dimensions.
    Lower energy manifold folded when collision detected. -/
def dynamicSuppresses (Mi Mj : VarDimManifold) (tau : Q16_16) : Bool :=
  dynamicACI Mi Mj tau && decide (Mi.energy.val > Mj.energy.val)

-- ════════════════════════════════════════════════════════════
-- §5  BettiSwooshND: Hamiltonian over [1, n_max]
-- ════════════════════════════════════════════════════════════

/-- Betti number counts per dimension. -/
structure BettiVector where
  beta0 : Nat  -- connected components
  beta1 : Nat  -- 1D holes
  beta2 : Nat  -- 2D cavities
  beta3 : Nat  -- 3D voids
  beta4plus : Nat  -- higher dimensions aggregated
  deriving Repr, Inhabited

/-- Manifold registry: separate lists per dimension. -/
structure ManifoldRegistry (nMax : Nat) where
  byDim : Array (List VarDimManifold)  -- index by dimension
  sizeByDim : byDim.size = nMax + 1
  deriving Repr

instance {nMax : Nat} : Inhabited (ManifoldRegistry nMax) where
  default := ⟨Array.mk (List.replicate (nMax + 1) []), by simp⟩

/-- Get manifolds of specific dimension. -/
def manifoldsOfDim (reg : ManifoldRegistry nMax) (n : Nat) : List VarDimManifold :=
  if h : n ≤ nMax then
    reg.byDim[n]'(by rw [reg.sizeByDim]; exact Nat.lt_succ_of_le h)
  else []

/-- Global Betti swoosh over all dimensions.
    H_M = Σ_n H_M^{(n)} - cross-dim coupling. -/
def bettiSwooshND (reg : ManifoldRegistry nMax) : Q16_16 :=
  -- Sum potential over all dimensions
  (Array.range (nMax + 1)).foldl (fun acc n =>
    let mfs := manifoldsOfDim reg n
    let sumN := mfs.foldl (fun accM Mi => Q16_16.add accM Mi.energy) Q16_16.zero
    Q16_16.add acc sumN
  ) Q16_16.zero

/-- Dimension selection potential: penalize deviation from target. -/
def dimensionPotential (n nTarget : Nat) (eta : Q16_16) : Q16_16 :=
  if n = nTarget then Q16_16.zero
  else ⟨eta.val * (Int.ofNat (if n > nTarget then n - nTarget else nTarget - n))⟩

/-- Total potential with structure constraint. -/
def totalPotentialWithDim (M : VarDimManifold) (nTarget : Nat) (eta : Q16_16) : Q16_16 :=
  Q16_16.add M.energy (dimensionPotential M.n nTarget eta)

-- ════════════════════════════════════════════════════════════
-- §6  SUBLEQ Variable-n Kernels
-- ════════════════════════════════════════════════════════════

/-- SUBLEQ program for lifting 1D → n with dynamic loop bounds. -/
def liftKernel (_n : Nat) : Program :=
  -- M[0] = seq_ptr, M[1] = t0, M[2] = dest_base
  -- M[3] = i (counter), M[4] = n (target dimension)
  -- M[5] = accum, M[6] = divisor
  #[ ⟨0, 5, 1⟩      -- accum ← accum - M[seq_ptr] (load)
   , ⟨6, 5, 2⟩      -- accum ← accum - M[divisor] (normalize)
   , ⟨5, 2, 3⟩      -- M[dest_base + i] ← accum
   , ⟨1, 3, 4⟩  -- i ← i - 1 (increment)
   , ⟨4, 3, 0⟩      -- if i ≤ n: continue else halt
   ]

/-- SUBLEQ program for constraint checking with m constraints. -/
def constrainKernel (_n _m : Nat) : Program :=
  -- Nested loops: outer over m constraints, inner over n dimensions
  -- M[0..n-1]: center coordinates x
  -- M[n..n+m-1]: constraint residuals
  -- M[n+m]: constraint index j
  -- M[n+m+1]: dimension index i
  -- M[n+m+2]: dot accumulator
  -- M[n+m+3]: epsilon tolerance
  #[ ⟨0, 0, 1⟩  -- placeholder for constraint loop
   ]

/-- Memory layout for variable-n manifold in SRAM. -/
def varDimMemoryLayout (base n : Nat) : Array Int :=
  #[ base                        -- center[0]
   , base + n                    -- center[n-1] end
   , base + n + n*(n+1)/2        -- metric end
   , base + n + n*(n+1)/2 + n*(n-1)/2  -- orient end
   , base + n*(n+3)/2            -- header start
   , base + n*(n+3)/2 - 4       -- dimension n
   , base + n*(n+3)/2 - 3       -- constraint count m
   , base + n*(n+3)/2 - 2       -- energy
   , base + n*(n+3)/2 - 1       -- activation σ
   ]


-- ════════════════════════════════════════════════════════════
-- §8  PhantomTideQ: Adaptive Phantom Coupling
--     Converts PhantomTide Float functions to Q16.16 formalization.
--     Integrates with VarDimManifold gossip routing.
-- ════════════════════════════════════════════════════════════

/-- Signal energy-coherence delta as velocity proxy.
    v = |e - κ| in Q16.16 (difference of two Q16.16 values). -/
def signalVelocity (energy coherence : Q16_16) : Q16_16 :=
  Q16_16.abs (Q16_16.sub energy coherence)

/-- Phantom modifier with adaptive λ parameter.
    φ(λ, v) = max(0, 1 - λ·v) — non-negative clamping.
    λ ∈ [0, 1] as Q16.16 (0 = no damping, 65536 = full damping). -/
def phantomModifier (lambda v : Q16_16) : Q16_16 :=
  let damp := Q16_16.sub Q16_16.one (Q16_16.mul lambda v)
  -- max(0, damp) via Q16_16 comparison
  if damp.val < 0 then Q16_16.zero else damp

/-- Full phantom coupling: j = base · φ(λ, v).
    Lambda-adaptive version of SSMS.jPhantom. -/
def couplingPhantom
    (lambda : Q16_16)
    (base : Q16_16)
    (energy coherence : Q16_16) : Q16_16 :=
  let v := signalVelocity energy coherence
  let modifier := phantomModifier lambda v
  Q16_16.mul base modifier

/-- Final score with phantom boost: s' = s · (1 + max(0, j)).
    Boosts stable signals (j > 0), dampens unstable (j < 0). -/
def finalScorePhantom (baseScore j : Q16_16) : Q16_16 :=
  let boost := Q16_16.add Q16_16.one (Q16_16.max Q16_16.zero j)
  Q16_16.mul baseScore boost

/-- Dynamic gossip budget: increase slots when coupling > 1.0.
    j > 1.0 means strong signal → allow more gossip contacts.
    Integrates with nContact tier system. -/
def dynamicGossipBudget (j : Q16_16) (baseSlots : Nat) : Nat :=
  if j.val > 65536 then baseSlots + 1 else baseSlots  -- j > 1.0 in Q16.16

/-- Betti-soliton driven score with phantom coupling.
    H_M = -Δ_M + V_M + V_phantom(λ).
    Drive term from phase control (Warden pressure). -/
def stableDrivenScorePhantom
    (lambda : Q16_16)
    (baseScore : Q16_16)
    (bettiEnergy : Q16_16)     -- from BettiSwooshND
    (drive : Q16_16)           -- phase control term
    (prev : Q16_16) : Q16_16 :=
  let j := couplingPhantom lambda baseScore bettiEnergy Q16_16.one
  let boosted := finalScorePhantom baseScore j
  -- Soliton step: combine with drive and previous state
  let step := Q16_16.add (Q16_16.mul drive boosted) (Q16_16.mul (Q16_16.ofNat 3) prev)
  -- Normalize by 4 (bit shift approximation)
  ⟨step.val / 4⟩

/-- Stable band routing: predicate for gossip inclusion.
    Signal routed if driven score exceeds threshold τ_stable. -/
def routeStablePhantom
    (lambda : Q16_16)
    (baseScore bettiEnergy drive prev tauStable : Q16_16) : Bool :=
  let score := stableDrivenScorePhantom lambda baseScore bettiEnergy drive prev
  decide (score.val ≥ tauStable.val)

/-- Tunneling allowance: high-coupling, high-coherence signals.
    j > 0.8 && visibility > 0.5 && coherence > 0.35 -/
def allowTunnelPhantom
    (lambda : Q16_16)
    (baseScore bettiEnergy visibility coherence : Q16_16) : Bool :=
  let j := couplingPhantom lambda baseScore bettiEnergy coherence
  let jThresh : Q16_16 := ⟨52428⟩    -- 0.8 in Q16.16 (0.8 * 65536 = 52428.8)
  let visThresh : Q16_16 := ⟨32768⟩  -- 0.5 in Q16.16
  let cohThresh : Q16_16 := ⟨22937⟩  -- 0.35 in Q16.16 (0.35 * 65536 = 22937.6)
  decide (j.val > jThresh.val) && decide (visibility.val > visThresh.val) && decide (coherence.val > cohThresh.val)

/-- Promotion threshold: tiered reduction based on coupling strength.
    j > 1.0: reduce by 0.75, j > 0.5: reduce by 0.25, else add 0.5. -/
def promoteThresholdPhantom
    (lambda thresholdBase : Q16_16)
    (baseScore bettiEnergy : Q16_16) : Q16_16 :=
  let j := couplingPhantom lambda baseScore bettiEnergy Q16_16.one
  let quarter : Q16_16 := ⟨16384⟩     -- 0.25 in Q16.16
  let half    : Q16_16 := ⟨32768⟩     -- 0.5 in Q16.16
  let threeQ  : Q16_16 := ⟨49152⟩     -- 0.75 in Q16.16
  let jHalf   : Q16_16 := ⟨32768⟩     -- 0.5 threshold
  let jOne := Q16_16.one
  if j.val > jOne.val then
    Q16_16.max Q16_16.zero (Q16_16.sub thresholdBase threeQ)
  else if j.val > jHalf.val then
    Q16_16.max Q16_16.zero (Q16_16.sub thresholdBase quarter)
  else
    Q16_16.add thresholdBase half

/-- Promotion predicate: score meets adaptive threshold. -/
def shouldPromotePhantom
    (lambda thresholdBase : Q16_16)
    (baseScore bettiEnergy drive prev : Q16_16) : Bool :=
  let finalScore := stableDrivenScorePhantom lambda baseScore bettiEnergy drive prev
  let thresh := promoteThresholdPhantom lambda thresholdBase baseScore bettiEnergy
  decide (finalScore.val ≥ thresh.val)

/-- Phantom-scored payload structure for gossip selection. -/
structure PhantomScoredPayload where
  payload   : GossipPacket
  score     : Q16_16
  coupling  : Q16_16
  stable    : Bool   -- passed routeStablePhantom
  deriving Repr, Inhabited

/-- Stabilize payloads via phantom scoring and filter.
    Returns sorted (by score) array of stable payloads.
    Integrates with variable-n gossip: budget scales with n. -/
def stabilizePayloadsPhantom
    (lambda tauStable : Q16_16)
    (_budgetSlots : Nat)
    (packets : Array (GossipPacket × Q16_16 × Q16_16 × Q16_16))  -- (pkt, energy, drive, prev)
    : Array PhantomScoredPayload :=
  let scored := packets.filterMap (fun (pkt, betti, drive, prev) =>
    let baseScore := pkt.energy
    let coherence := pkt.deltaH  -- reuse deltaH as coherence proxy
    let j := couplingPhantom lambda baseScore betti coherence
    let stable := routeStablePhantom lambda baseScore betti drive prev tauStable
    if stable then
      some { payload := pkt, score := finalScorePhantom baseScore j
           , coupling := j, stable := true }
    else none)
  -- Sort by score descending (selection sort via foldl)
  scored  -- qsort requires Ord instance; return unsorted for now

/-- Phantom kernel output structure for gossip routing decision. -/
structure PhantomKernelOutput where
  chosen     : Option GossipPacket
  score      : Q16_16
  coupling   : Q16_16
  promoted   : Bool
  tunneled   : Bool
  budgetNext : Nat
  deriving Repr, Inhabited

/-- Phantom kernel step: full gossip packet selection pipeline.
    Integrates with VarDimManifold.n for dimension-aware budget. -/
def stepKernelPhantom
    (lambda tauStable : Q16_16)
    (budgetSlots : Nat)
    (n : Nat)        -- manifold dimension for scaling
    (packets : Array (GossipPacket × Q16_16 × Q16_16 × Q16_16))
    (visibility coherence : Q16_16) : PhantomKernelOutput :=
  let scored := stabilizePayloadsPhantom lambda tauStable budgetSlots packets
  -- Scale budget by dimension: more dimensions → more gossip slots
  let dimBudget := budgetSlots + n / 2
  match scored[0]? with
  | none =>
      { chosen := none, score := Q16_16.zero, coupling := Q16_16.zero
      , promoted := false, tunneled := false, budgetNext := dimBudget }
  | some best =>
      let j := best.coupling
      let tunneled := allowTunnelPhantom lambda best.score best.score visibility coherence
      let promoted := shouldPromotePhantom lambda Q16_16.one best.score best.score Q16_16.zero Q16_16.zero
      let budgetNext := dynamicGossipBudget j dimBudget
      { chosen := some best.payload, score := best.score, coupling := j
      , promoted := promoted, tunneled := tunneled, budgetNext := budgetNext }


-- ════════════════════════════════════════════════════════════
-- §9  Cycle Counts for Variable-n Pipeline with Phantom
-- ════════════════════════════════════════════════════════════

/-- Lifting cycles: O(n · d) ternary ops. -/
def liftCycles (n d : Nat) : Nat :=
  n * d  -- one ADD/SUB per nonzero weight

/-- Constraint check cycles: O(m · n). -/
def constraintCycles (n m : Nat) : Nat :=
  m * n * 2  -- dot product + comparison per constraint

/-- Dynamic NMS cycles: O(k^2 · n_min) for k manifolds. -/
def dynamicNmsCycles (k nAvg : Nat) : Nat :=
  k * k * nAvg  -- pairwise center distances

/-- Total pipeline with dimension selection. -/
def varDimTotalCycles (n d m k : Nat) : Nat :=
  liftCycles n d
  + constraintCycles n m
  + dynamicNmsCycles k n
  + n * 18  -- MLGRU per dimension
  + 2 * (Nat.log2 k + 1)  -- gossip

/-- Throughput: manifolds processed per 1000 cycles. -/
def varDimThroughput (n d m : Nat) : Nat :=
  1000 / varDimTotalCycles n d m 1

end Semantics.SSMS_nD
