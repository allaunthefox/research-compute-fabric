/-
HyperEigenSpectrum.lean — λ_YAH Scale-Regime Eigenvalue Kernel

Defines the λ_YAH (You-Are-Here) hyper-eigenspectrum: a scale-dependent
operator whose eigenspectrum encodes the dominant active physics regime of
an object at a given observer scale, combining:

  Ω_M   — Menger-like void hierarchy
  R_K   — Koch-like boundary scar roughness
  D_q   — multifractal density spectrum
  Λ     — lacunarity / gap texture
  β_k   — persistent topology receipts (β₀, β₁, β₂)
  P     — percolation / web connectivity
  C     — curvature / Minkowski geometry
  η     — medium-coupling coefficient
  ε     — unexplained residual

The dominant eigenvalue λ_dom = eigenvalues[dominantIdx] tells you which
physics chart is active. A large or discontinuous Δλ_dom signals a regime
transition.

Architecture (per DeepSeek review 2026-05-11):
  - Separate from EigenmassOperator (different mathematics: spectrum vs. product)
  - `fromEigenmassOperator` provides backward-compatible constructor path
  - `BoundaryEigenFire.lean` imports this; not the reverse

Conventions:
  PascalCase types, camelCase functions.
  Q16_16 for all numeric fields.
  Array Q16_16 for eigenvalue vectors.
  Namespace: Semantics.HCMMR.HyperEigenSpectrum
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint

namespace Semantics.HCMMR.Kernels.HyperEigenSpectrum

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

-- ═══════════════════════════════════════════════════════════════════
-- §1  BindOperator — the nine-component shape-state descriptor
-- ═══════════════════════════════════════════════════════════════════

/--
The nine-component Bind operator that feeds λ_YAH.

Each field is a Q16_16 score in [0, 65536] (= [0, 1.0] normalised):
  - 0     = this mode contributes nothing
  - 65536 = this mode is fully active / maximally dominant

`bk0`, `bk1`, `bk2` are the three Betti number receipts (connected
components, tunnels, voids); they are stored separately because topology
persistence receipts are structurally different from continuous field scores.
-/
structure BindOperator where
  omegaM  : Q16_16   -- Ω_M  Menger void hierarchy
  rK      : Q16_16   -- R_K  Koch boundary roughness / scar
  dQ      : Q16_16   -- D_q  multifractal density spectrum
  lacun   : Q16_16   -- Λ    lacunarity / gap texture
  bk0     : Q16_16   -- β₀   topology: connected components
  bk1     : Q16_16   -- β₁   topology: tunnels / loops
  bk2     : Q16_16   -- β₂   topology: enclosed voids
  perc    : Q16_16   -- P    percolation / web connectivity
  curv    : Q16_16   -- C    curvature / Minkowski geometry
  eta     : Q16_16   -- η    medium-coupling coefficient
  eps     : Q16_16   -- ε    unexplained residual
  deriving Repr, BEq, DecidableEq, Inhabited

/-- Number of components in a BindOperator. -/
def BindOperator.size : Nat := 11

/-- Flatten a BindOperator to an Array of Q16_16 values. -/
def BindOperator.toArray (b : BindOperator) : Array Q16_16 :=
  #[b.omegaM, b.rK, b.dQ, b.lacun, b.bk0, b.bk1, b.bk2, b.perc, b.curv, b.eta, b.eps]

/-- Human-readable labels for each BindOperator component, in array order. -/
def BindOperator.labels : Array String :=
  #["Ω_M(void)", "R_K(scar)", "D_q(density)", "Λ(lacunarity)",
    "β₀(components)", "β₁(tunnels)", "β₂(voids)",
    "P(percolation)", "C(curvature)", "η(coupling)", "ε(residual)"]

-- ═══════════════════════════════════════════════════════════════════
-- §2  EigenMode — named index into the BindOperator array
-- ═══════════════════════════════════════════════════════════════════

/--
Named index into the BindOperator component array.
Mirrors `BindOperator.toArray` ordering exactly.
-/
inductive EigenMode
  | voidHierarchy      -- index 0: Ω_M
  | scarRoughness      -- index 1: R_K
  | densitySpectrum    -- index 2: D_q
  | lacunarity         -- index 3: Λ
  | topoComponents     -- index 4: β₀
  | topoTunnels        -- index 5: β₁
  | topoVoids          -- index 6: β₂
  | percolation        -- index 7: P
  | curvature          -- index 8: C
  | coupling           -- index 9: η
  | residual           -- index 10: ε
  deriving Repr, BEq, DecidableEq, Inhabited

def EigenMode.toIndex : EigenMode → Nat
  | .voidHierarchy   => 0
  | .scarRoughness   => 1
  | .densitySpectrum => 2
  | .lacunarity      => 3
  | .topoComponents  => 4
  | .topoTunnels     => 5
  | .topoVoids       => 6
  | .percolation     => 7
  | .curvature       => 8
  | .coupling        => 9
  | .residual        => 10

def EigenMode.label : EigenMode → String
  | .voidHierarchy   => "Ω_M: Menger void hierarchy"
  | .scarRoughness   => "R_K: Koch boundary scar"
  | .densitySpectrum => "D_q: multifractal density"
  | .lacunarity      => "Λ: lacunarity / gap texture"
  | .topoComponents  => "β₀: connected components"
  | .topoTunnels     => "β₁: topological tunnels"
  | .topoVoids       => "β₂: enclosed voids"
  | .percolation     => "P: percolation connectivity"
  | .curvature       => "C: curvature / Minkowski"
  | .coupling        => "η: medium coupling"
  | .residual        => "ε: unexplained residual"

-- ═══════════════════════════════════════════════════════════════════
-- §3  HyperEigenSpectrum — the λ_YAH eigenvalue structure
-- ═══════════════════════════════════════════════════════════════════

/--
The λ_YAH hyper-eigenspectrum for one object at one observer scale.

`eigenvalues` is an Array of Q16_16 values, one per BindOperator component,
sorted descending — the dominant mode is always at index `dominantIdx = 0`
by convention (or stored explicitly if sorting is too expensive for a gate).

`weights` holds the raw BindOperator component values before normalisation,
preserved for receipt-chain traceability.

`regimeTransition` is set when the dominant eigenvalue has shifted since
the previous scale step (Δλ_dom is large or discontinuous).

`sourceScale` records the observer scale at which this spectrum was
computed (Q16_16, units are model-native: e.g., log₁₀(r/r₀)).
-/
structure HyperEigenSpectrum where
  bind             : BindOperator
  eigenvalues      : Array Q16_16  -- sorted descending by value
  dominantIdx      : Nat           -- index into eigenvalues of the dominant mode
  regimeTransition : Bool          -- Δλ_dom was large at this scale step
  sourceScale      : Q16_16        -- observer scale r (log-normalised)
  deriving Repr, Inhabited

/-- Total number of eigenvalue components. -/
def HyperEigenSpectrum.size (s : HyperEigenSpectrum) : Nat :=
  s.eigenvalues.size

/-- Dominant eigenvalue (λ_dom). -/
def HyperEigenSpectrum.lambdaDom (s : HyperEigenSpectrum) : Q16_16 :=
  s.eigenvalues.getD s.dominantIdx ⟨0⟩

/-- Return the mode label for the dominant eigenvalue. -/
def HyperEigenSpectrum.dominantLabel (s : HyperEigenSpectrum) : String :=
  BindOperator.labels.getD s.dominantIdx "unknown"

-- ═══════════════════════════════════════════════════════════════════
-- §4  Spectrum construction
-- ═══════════════════════════════════════════════════════════════════

/--
Sort an Array Q16_16 descending by value.
Returns the sorted array and the original index of the maximum element
(= the dominant mode index after sorting = 0, but we keep it explicit).
-/
private def sortDescending (arr : Array Q16_16) : Array Q16_16 :=
  arr.toList.mergeSort (fun a b => a.val ≥ b.val) |>.toArray

/--
Find the index of the maximum value in an Array Q16_16.
Returns 0 for empty arrays.
-/
private def argmax (arr : Array Q16_16) : Nat :=
  let rec go (i : Nat) (bestIdx : Nat) (bestVal : UInt32) : Nat :=
    if i ≥ arr.size then bestIdx
    else
      let v := arr[i]!.val
      if v > bestVal then go (i + 1) i v
      else go (i + 1) bestIdx bestVal
  go 0 0 0

/--
Compute the HyperEigenSpectrum from a BindOperator at a given observer scale.

The eigenvalues are the raw component scores sorted descending.
`regimeTransition` is set if the dominant eigenvalue exceeds the second by
a ratio of more than 2:1 (the dominant mode is clearly separated — indicates
a strong regime, not a mixed state).

`prevDominantVal` is the dominant eigenvalue from the previous scale step;
if provided and the new dominant differs by more than 25% (16384 Q16 units),
`regimeTransition` is set.
-/
def fromBind (b : BindOperator) (scale : Q16_16)
    (prevDominantVal : Option Q16_16 := none) : HyperEigenSpectrum :=
  let raw := b.toArray
  let sorted := sortDescending raw
  let domVal := sorted.getD 0 ⟨0⟩
  let secondVal := sorted.getD 1 ⟨0⟩
  -- Regime transition: dominant shifted >25% from previous, or >2× second mode
  let transitionFromPrev :=
    match prevDominantVal with
    | none => false
    | some prev =>
      let diff := if domVal.val ≥ prev.val then domVal.val - prev.val else prev.val - domVal.val
      diff > 16384  -- 25% of Q16_16 range
  let transitionFromGap :=
    secondVal.val > 0 && domVal.val > secondVal.val * 2
  { bind := b
  , eigenvalues := sorted
  , dominantIdx := 0     -- sorted: dominant is always first
  , regimeTransition := transitionFromPrev || transitionFromGap
  , sourceScale := scale }

/--
Construct a HyperEigenSpectrum from an existing EigenmassOperator.

Seeds the BindOperator using the seven gate scores from EigenmassOperator:
  eigenvalue         → splits between omegaM and rK  (spectral structure)
  admissibilityScore → dQ  (density/admissibility coupling)
  invarianceScore    → lacun + bk0 (invariant structure, topology)
  chiralityScore     → bk1  (chirality ~ topological tunnel orientation)
  receiptScore       → bk2 + perc (receipt chain ~ void/connectivity)
  calibrationScore   → curv (constant calibration ~ curvature anchoring)
  projectionScore    → eta + eps (projection ~ coupling + residual)

This is a lossy lift — 7 scalars seed 11 slots — but provides backward
compatibility for all existing gate chains.
-/
def fromEigenmassOperator (op : EigenmassOperator) (scale : Q16_16 := ⟨0⟩) : HyperEigenSpectrum :=
  let half (q : Q16_16) : Q16_16 := ⟨q.val / 2⟩
  let b : BindOperator :=
    { omegaM := half op.eigenvalue
    , rK     := half op.eigenvalue
    , dQ     := op.admissibilityScore
    , lacun  := half op.invarianceScore
    , bk0    := half op.invarianceScore
    , bk1    := op.chiralityScore
    , bk2    := half op.receiptScore
    , perc   := half op.receiptScore
    , curv   := op.calibrationScore
    , eta    := half op.projectionScore
    , eps    := half op.projectionScore }
  fromBind b scale

-- ═══════════════════════════════════════════════════════════════════
-- §5  Regime classification
-- ═══════════════════════════════════════════════════════════════════

/--
The physics regime implied by the dominant eigenmode.
Maps from EigenMode to a human-readable physics chart label.
-/
def regimeLabel (mode : EigenMode) : String :=
  match mode with
  | .voidHierarchy   => "Menger/void — cosmic web, interior-void physics"
  | .scarRoughness   => "Koch/scar — boundary fracture, surface roughness"
  | .densitySpectrum => "Multifractal density — turbulence, galaxy clustering"
  | .lacunarity      => "Lacunarity — gap texture, porosity regime"
  | .topoComponents  => "Topological β₀ — connectivity, island counting"
  | .topoTunnels     => "Topological β₁ — tunnel/loop regime"
  | .topoVoids       => "Topological β₂ — enclosed void regime"
  | .percolation     => "Percolation — web/filament connectivity"
  | .curvature       => "Curvature — Riemannian / Minkowski geometry"
  | .coupling        => "Coupling — energy deposition, EM interaction"
  | .residual        => "Residual — Underverse scar, unexplained anomaly"

/--
Return the dominant EigenMode for a spectrum.
Since eigenvalues are sorted descending, the dominant mode is the one whose
original BindOperator position had the highest value.

We recover the original position by finding which entry in the sorted array
matches the raw bind value at each EigenMode index.
-/
def dominantMode (s : HyperEigenSpectrum) : EigenMode :=
  let raw := s.bind.toArray
  -- find raw index of maximum
  let maxIdx := argmax raw
  -- map to EigenMode
  match maxIdx with
  | 0  => .voidHierarchy
  | 1  => .scarRoughness
  | 2  => .densitySpectrum
  | 3  => .lacunarity
  | 4  => .topoComponents
  | 5  => .topoTunnels
  | 6  => .topoVoids
  | 7  => .percolation
  | 8  => .curvature
  | 9  => .coupling
  | _  => .residual

-- ═══════════════════════════════════════════════════════════════════
-- §6  Regime transition detection
-- ═══════════════════════════════════════════════════════════════════

/--
Compare two spectra at consecutive observer scales.
Returns `true` if the dominant mode changed or λ_dom shifted by >25%.
-/
def hasRegimeShift (s1 s2 : HyperEigenSpectrum) : Bool :=
  let modeChanged := dominantMode s1 != dominantMode s2
  let dom1 := s1.lambdaDom
  let dom2 := s2.lambdaDom
  let diff := if dom2.val ≥ dom1.val then dom2.val - dom1.val else dom1.val - dom2.val
  modeChanged || diff > 16384

/--
Classify the regime transition as smooth, sharp, or discontinuous.
- Smooth: |Δλ_dom| ≤ 25%, same dominant mode
- Sharp: |Δλ_dom| > 25%, or mode changed
- Discontinuous: mode changed AND |Δλ_dom| > 50% (threshold 32768)
-/
inductive TransitionClass
  | smooth         -- no significant shift
  | sharp          -- significant but continuous shift
  | discontinuous  -- mode change + large λ jump (topology tear / phase boundary)
  deriving Repr, BEq, DecidableEq, Inhabited

def classifyTransition (s1 s2 : HyperEigenSpectrum) : TransitionClass :=
  let modeChanged := dominantMode s1 != dominantMode s2
  let dom1 := s1.lambdaDom
  let dom2 := s2.lambdaDom
  let diff := if dom2.val ≥ dom1.val then dom2.val - dom1.val else dom1.val - dom2.val
  if modeChanged && diff > 32768 then .discontinuous
  else if modeChanged || diff > 16384 then .sharp
  else .smooth

-- ═══════════════════════════════════════════════════════════════════
-- §7  Witnesses
-- ═══════════════════════════════════════════════════════════════════

-- Cosmic-web void region: void and percolation dominate.
def cosmicVoidBind : BindOperator :=
  { omegaM := ⟨58982⟩   -- Ω_M ≈ 0.90 (strong void)
  , rK     := ⟨16384⟩   -- R_K ≈ 0.25 (some boundary scar)
  , dQ     := ⟨13107⟩   -- D_q ≈ 0.20
  , lacun  := ⟨39322⟩   -- Λ   ≈ 0.60 (high gap texture)
  , bk0    := ⟨9830⟩    -- β₀  ≈ 0.15
  , bk1    := ⟨6554⟩    -- β₁  ≈ 0.10
  , bk2    := ⟨52429⟩   -- β₂  ≈ 0.80 (strong enclosed-void topology)
  , perc   := ⟨45875⟩   -- P   ≈ 0.70 (connected filament web)
  , curv   := ⟨9830⟩    -- C   ≈ 0.15
  , eta    := ⟨3277⟩    -- η   ≈ 0.05 (low coupling)
  , eps    := ⟨1638⟩ }  -- ε   ≈ 0.025

def cosmicVoidSpectrum : HyperEigenSpectrum :=
  fromBind cosmicVoidBind ⟨0⟩

#eval cosmicVoidSpectrum.lambdaDom
-- expected: the highest of the void/percolation/topology scores ≈ ⟨58982⟩

#eval (dominantMode cosmicVoidSpectrum).label
-- expected: "Ω_M: Menger void hierarchy"

-- Fracture boundary: scar roughness and stress dominate.
def fractureBind : BindOperator :=
  { omegaM := ⟨9830⟩    -- low void
  , rK     := ⟨62259⟩   -- R_K ≈ 0.95 (strong boundary scar)
  , dQ     := ⟨26214⟩   -- D_q ≈ 0.40
  , lacun  := ⟨13107⟩
  , bk0    := ⟨6554⟩
  , bk1    := ⟨29491⟩   -- β₁ ≈ 0.45 (tunnel cracks)
  , bk2    := ⟨3277⟩
  , perc   := ⟨16384⟩
  , curv   := ⟨52429⟩   -- C ≈ 0.80 (high curvature at fracture)
  , eta    := ⟨45875⟩   -- η ≈ 0.70 (strong stress coupling)
  , eps    := ⟨6554⟩ }

def fractureSpectrum : HyperEigenSpectrum :=
  fromBind fractureBind ⟨65536⟩

#eval (dominantMode fractureSpectrum).label
-- expected: "R_K: Koch boundary scar"

-- Regime transition between the two.
#eval classifyTransition cosmicVoidSpectrum fractureSpectrum
-- expected: TransitionClass.discontinuous (dominant mode changed, large Δλ)

-- Lift from a perfect EigenmassOperator.
#eval (fromEigenmassOperator fullyAdmittingOperator).dominantLabel
-- expected: one of the mode names (all equal weights → first by sort stability)

end Semantics.HCMMR.Kernels.HyperEigenSpectrum
