/-
BoundaryEigenFire.lean — B_∂ Modal Burn Surface Kernel

Defines the boundary eigenfire field B_∂(x) — the surface projection of the
λ_YAH hyper-eigenspectrum — and the tripartite BoundaryVerdict:

  admitted          — ‖B_∂‖ ≤ Θ_activation, boundary resolves in current chart
  underverseEntry   — receipts fail to close, object routes to Underverse shadow
  geodesicPromotion — ‖B_∂‖ → ∞, irreconcilable receipts, geodesic opens in ℝ^(n+1)

Core doctrine (per BoundaryEigenFire.md):
  A boundary is not a separator line. It is a modal burn surface — the local
  superposition surface where encoded state values pile up and interfere.
  The "wall of fire" condition is ‖B_∂(x)‖ > Θ_activation: the dominant modal
  stack ignites. Which mode dominates determines what the boundary manifests as.

Wormhole throat prediction:
  When two objects carry irreconcilable receipts (A_motion→1 meets
  ε_displacement=0), B_∂ cannot resolve in ℝ^n. The predicted resolution:
  a higher-dimensional geodesic opens (GeodesicPromotion verdict).
  Within the 16D stack: dim < 16 → n+1; dim = 16 → loopback compaction (Π gate).
  The throat is latent in S3CProjectedGeodesicResolution's resolutionDelta
  arithmetic — this is the case where that budget overflows.

Architecture (per DeepSeek review 2026-05-11):
  - Imports HyperEigenSpectrum (no reverse dependency)
  - GeodesicPromotion is a first-class verdict, not a field
  - GeodesicPromotionReceipt references FoldedPointManifold's permeability model
  - PromotionType: dimensionalExtrusion (dim<16) | loopbackCompaction (dim=16)

Conventions:
  PascalCase types, camelCase functions.
  Q16_16 for all numeric fields.
  Fin 17 for dimensional slots (0..16).
  Namespace: Semantics.HCMMR.Kernels.BoundaryEigenFire
-/

import Semantics.HCMMR.Core
import Semantics.HCMMR.Kernels.HyperEigenSpectrum
import Semantics.FixedPoint

namespace Semantics.HCMMR.Kernels.BoundaryEigenFire

open Semantics.HCMMR.Core
open Semantics.HCMMR.Kernels.HyperEigenSpectrum
open Semantics.FixedPoint (Q16_16)

-- ═══════════════════════════════════════════════════════════════════
-- §1  Modal weight vector — the B_∂ projection coefficients
-- ═══════════════════════════════════════════════════════════════════

/--
The α-coefficient vector for the boundary field projection.

B_∂(x) = α_ρ·ρ + α_g·∇ρ + α_T·T + α_σ·σ + α_κ·κ + α_β·β + α_η·η + α_ε·ε

Each α is a Q16_16 weight ∈ [0, 65536]. The vector is obtained by
projecting the HyperEigenSpectrum onto the boundary surface ∂Ω. In this
discrete model, projection = extract the mode scores that are geometrically
"surface-active" rather than interior-active.

Mapping from EigenMode to boundary coefficient:
  voidHierarchy  → α_ρ    (density concentration at boundary)
  scarRoughness  → α_g    (density gradient — scar is a gradient surface)
  densitySpectrum→ α_ρ    (additional density weight)
  lacunarity     → α_κ    (gap texture ↔ curvature)
  topoComponents → α_β    (connected components receipt)
  topoTunnels    → α_β    (tunnel receipt)
  topoVoids      → α_β    (void receipt)
  percolation    → α_g    (connectivity gradient)
  curvature      → α_κ    (direct curvature)
  coupling       → α_η    (medium coupling at boundary)
  residual       → α_ε    (unexplained boundary term)
-/
structure ModalWeights where
  alphaDensity   : Q16_16  -- α_ρ  density / void
  alphaGradient  : Q16_16  -- α_g  density gradient / scar / percolation
  alphaThermal   : Q16_16  -- α_T  thermal state
  alphaStress    : Q16_16  -- α_σ  mechanical stress / strain
  alphaCurvature : Q16_16  -- α_κ  curvature / lacunarity
  alphaTopology  : Q16_16  -- α_β  topology receipt (β₀+β₁+β₂ combined)
  alphaCoupling  : Q16_16  -- α_η  medium coupling
  alphaResidual  : Q16_16  -- α_ε  unexplained residual
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Project a HyperEigenSpectrum onto the boundary ModalWeights.

The projection maps each EigenMode component onto its primary boundary
coefficient using the mapping described in `ModalWeights`.
-/
def projectToBoundary (s : HyperEigenSpectrum) : ModalWeights :=
  let b := s.bind
  -- density: void + density spectrum averaged
  let ρ : Q16_16 := ⟨(b.omegaM.val / 2 + b.dQ.val / 2)⟩
  -- gradient: scar roughness + percolation averaged
  let g : Q16_16 := ⟨(b.rK.val / 2 + b.perc.val / 2)⟩
  -- thermal: not directly in BindOperator — proxy via coupling
  let T : Q16_16 := ⟨b.eta.val / 2⟩
  -- stress: proxy via coupling + scar
  let σ : Q16_16 := ⟨(b.eta.val / 2 + b.rK.val / 4)⟩
  -- curvature: direct + lacunarity
  let κ : Q16_16 := ⟨(b.curv.val / 2 + b.lacun.val / 2)⟩
  -- topology: β₀ + β₁ + β₂ averaged
  let β : Q16_16 := ⟨(b.bk0.val / 3 + b.bk1.val / 3 + b.bk2.val / 3)⟩
  -- coupling: direct
  let η : Q16_16 := b.eta
  -- residual: direct
  let ε : Q16_16 := b.eps
  { alphaDensity   := ρ
  , alphaGradient  := g
  , alphaThermal   := T
  , alphaStress    := σ
  , alphaCurvature := κ
  , alphaTopology  := β
  , alphaCoupling  := η
  , alphaResidual  := ε }

/--
Compute the L∞ norm of the ModalWeights — the dominant boundary mode strength.
‖B_∂‖ = max(α_i).
-/
def modalNorm (w : ModalWeights) : Q16_16 :=
  let vals := #[w.alphaDensity, w.alphaGradient, w.alphaThermal, w.alphaStress,
                w.alphaCurvature, w.alphaTopology, w.alphaCoupling, w.alphaResidual]
  vals.foldl (fun acc v => if v.val > acc.val then v else acc) ⟨0⟩

-- ═══════════════════════════════════════════════════════════════════
-- §2  BoundaryField — the full projected boundary surface state
-- ═══════════════════════════════════════════════════════════════════

/--
The boundary field B_∂(x) for one object at one boundary point.

`spectrum` is the λ_YAH eigenspectrum of the object's interior.
`weights` is the projected ModalWeights onto ∂Ω.
`activationNorm` is ‖B_∂(x)‖ = max(α_i).
`sourceDim` is the current dimensional chart (Fin 17, enforcing ≤ 16 cap).
`receiptsClosed` tracks whether the receipt chain closes at this boundary.
-/
structure BoundaryField where
  spectrum        : HyperEigenSpectrum
  weights         : ModalWeights
  activationNorm  : Q16_16
  sourceDim       : Fin 17
  receiptsClosed  : Bool
  deriving Repr, Inhabited

/--
Construct a BoundaryField from a HyperEigenSpectrum and dimensional chart.
-/
def BoundaryField.fromSpectrum (s : HyperEigenSpectrum) (dim : Fin 17)
    (receiptsClosed : Bool := true) : BoundaryField :=
  let w := projectToBoundary s
  { spectrum := s
  , weights := w
  , activationNorm := modalNorm w
  , sourceDim := dim
  , receiptsClosed }

-- ═══════════════════════════════════════════════════════════════════
-- §3  Activation threshold and EigenFire condition
-- ═══════════════════════════════════════════════════════════════════

/--
EigenFire activation threshold Θ_activation.

A boundary "ignites" when its dominant modal weight exceeds this value.
Set at 75% of Q16_16 range: 0.75 × 65536 = 49152.

Below threshold: boundary is passive (transmissive, cool).
Above threshold: boundary manifests actively (thermal, mechanical, topological).
At max (65536): boundary is at saturation — potential geodesic puncture.
-/
def activationThreshold : Q16_16 := ⟨49152⟩

/--
Puncture threshold — ‖B_∂‖ at which the boundary can no longer resolve in
the current chart and geodesic promotion is triggered.
Set at 95% of Q16_16 range: 0.95 × 65536 = 62259.
-/
def punctureThreshold : Q16_16 := ⟨62259⟩

/--
EigenFire condition: activationNorm > Θ_activation.
-/
def isEigenFire (f : BoundaryField) : Bool :=
  f.activationNorm.val > activationThreshold.val

/--
Puncture condition: activationNorm > Θ_puncture AND receipts failed to close.
Both conditions required: high activation alone may be a hot-but-admissible boundary.
Receipts failing to close indicates irreconcilable states.
-/
def isPuncture (f : BoundaryField) : Bool :=
  f.activationNorm.val > punctureThreshold.val && !f.receiptsClosed

-- ═══════════════════════════════════════════════════════════════════
-- §4  Dominant manifestation — what the boundary looks like
-- ═══════════════════════════════════════════════════════════════════

/--
The dominant manifestation class of an active boundary.
What appears when B_∂ ignites depends on which modal coefficient dominates.
-/
inductive BoundaryManifestation
  | thermal       -- α_T dominant: glow, flame, plasma sheath
  | mechanical    -- α_σ dominant: fracture band, impact crater
  | compression   -- α_g dominant: shockwave, sonic boom
  | coupling      -- α_η dominant: ionization, EM emission, energy deposition
  | geometric     -- α_κ dominant: caustic, Riemannian tear, curvature singularity
  | topological   -- α_β dominant: topology tear, handle attachment, homology jump
  | density       -- α_ρ dominant: density spike, void wall
  | residual      -- α_ε dominant: Underverse scar, unexplained anomaly
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Identify the dominant manifestation from ModalWeights.
-/
def dominantManifestation (w : ModalWeights) : BoundaryManifestation :=
  let candidates : Array (BoundaryManifestation × Q16_16) :=
    #[(.thermal,    w.alphaThermal)
    , (.mechanical, w.alphaStress)
    , (.compression,w.alphaGradient)
    , (.coupling,   w.alphaCoupling)
    , (.geometric,  w.alphaCurvature)
    , (.topological,w.alphaTopology)
    , (.density,    w.alphaDensity)
    , (.residual,   w.alphaResidual)]
  let best := candidates.foldl
    (fun acc c => if c.2.val > acc.2.val then c else acc)
    (.residual, ⟨0⟩)
  best.1

-- ═══════════════════════════════════════════════════════════════════
-- §5  BoundaryVerdict — the tripartite gate outcome
-- ═══════════════════════════════════════════════════════════════════

/--
How the dimensional promotion resolves when ‖B_∂‖ → puncture threshold.

`dimensionalExtrusion`: sourceDim < 16 → geodesic opens in dim+1.
`loopbackCompaction`:  sourceDim = 16 → Π gate activates loopback to
                        compactified chart (stack reset, not stack exit).
-/
inductive PromotionType
  | dimensionalExtrusion  -- opens dim+1 within 0..16 cap
  | loopbackCompaction    -- at dim=16, Π loops back to compactified chart
  deriving Repr, BEq, DecidableEq, Inhabited

/--
Receipt for a geodesic promotion event.

`sourceChart`   : Fin 17 — the dimensional chart where the puncture occurred
`targetChart`   : Fin 17 — the promoted chart (sourceChart+1, or 0 for loopback)
`promotionType` : how the promotion resolves
`throatRadius`  : Q16_16 — estimated throat opening size (from activation norm)
`spectrumAtPuncture` : the λ_YAH snapshot at the moment of puncture — what
                       eigenmode distribution caused the throat to open
-/
structure GeodesicPromotionReceipt where
  sourceChart          : Fin 17
  targetChart          : Fin 17
  promotionType        : PromotionType
  throatRadius         : Q16_16
  spectrumAtPuncture   : HyperEigenSpectrum
  deriving Repr, Inhabited

/--
Compute the GeodesicPromotionReceipt for a boundary that has reached puncture.
-/
def makePromotionReceipt (f : BoundaryField) : GeodesicPromotionReceipt :=
  let src := f.sourceDim
  -- Compute target chart: extrude to n+1 (capped at 16), or loopback to 0 at dim 16.
  let tgtVal : Nat := if src.val < 16 then src.val + 1 else 0
  -- tgtVal ≤ 16 < 17 in both branches: if src.val<16 then src.val+1 ≤ 16, else 0 ≤ 16.
  let tgt : Fin 17 := ⟨tgtVal % 17, Nat.mod_lt _ (by norm_num)⟩
  let ptype : PromotionType :=
    if src.val < 16 then .dimensionalExtrusion else .loopbackCompaction
  { sourceChart        := src
  , targetChart        := tgt
  , promotionType      := ptype
  , throatRadius       := f.activationNorm
  , spectrumAtPuncture := f.spectrum }

/--
The tripartite boundary verdict.

- `admitted (receipt)`         : boundary resolves in current chart, receipt emitted
- `underverseEntry (receipt)`  : activation within bounds but receipts don't close;
                                  object routes to Underverse shadow with typed receipt
- `geodesicPromotion (receipt)`: boundary saturates, dimensional puncture opens,
                                  full promotion receipt emitted
-/
inductive BoundaryVerdict
  | admitted        (manifestation : BoundaryManifestation) (isHot : Bool)
  | underverseEntry (manifestation : BoundaryManifestation) (norm : Q16_16)
  | geodesicPromotion (promo : GeodesicPromotionReceipt)
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════
-- §6  Full EigenFire gate
-- ═══════════════════════════════════════════════════════════════════

/--
Full typed receipt for one boundary evaluation.
-/
structure EigenFireReceipt where
  field          : BoundaryField
  manifestation  : BoundaryManifestation
  isEigenFire    : Bool
  isPuncture     : Bool
  verdict        : BoundaryVerdict
  deriving Repr, Inhabited

/--
Evaluate the eigenfire gate for a boundary field.

Decision logic (series circuit):
  1. isPuncture? → GeodesicPromotion (irreconcilable receipts, throat opens)
  2. !receiptsClosed (but below puncture)? → UnderverseEntry
  3. isEigenFire (hot boundary, receipts close)? → Admitted hot
  4. otherwise → Admitted cool
-/
def eigenFireGate (f : BoundaryField) : EigenFireReceipt :=
  let manif := dominantManifestation f.weights
  let fire  := isEigenFire f
  let punct := isPuncture f
  let verdict :=
    if punct then
      BoundaryVerdict.geodesicPromotion (makePromotionReceipt f)
    else if !f.receiptsClosed then
      BoundaryVerdict.underverseEntry manif f.activationNorm
    else
      BoundaryVerdict.admitted manif fire
  { field := f
  , manifestation := manif
  , isEigenFire := fire
  , isPuncture := punct
  , verdict }

-- ═══════════════════════════════════════════════════════════════════
-- §7  Collision combinator — irreconcilable receipts
-- ═══════════════════════════════════════════════════════════════════

/--
Model the collision of two objects at a shared boundary.

The combined boundary field is formed by taking the component-wise maximum
of each object's projected modal weights — representing the "pile-up" of
both objects' encoded states at the interface.

`receiptsClosed` is false when the two objects have conflicting dominant modes
(e.g., one has maximal coupling, the other has zero coupling — irreconcilable).
-/
def collide (f1 f2 : BoundaryField) : BoundaryField :=
  let w1 := f1.weights
  let w2 := f2.weights
  -- pile-up: take max of each modal weight
  let combined : ModalWeights :=
    { alphaDensity   := if w1.alphaDensity.val   ≥ w2.alphaDensity.val   then w1.alphaDensity   else w2.alphaDensity
    , alphaGradient  := if w1.alphaGradient.val  ≥ w2.alphaGradient.val  then w1.alphaGradient  else w2.alphaGradient
    , alphaThermal   := if w1.alphaThermal.val   ≥ w2.alphaThermal.val   then w1.alphaThermal   else w2.alphaThermal
    , alphaStress    := if w1.alphaStress.val    ≥ w2.alphaStress.val    then w1.alphaStress    else w2.alphaStress
    , alphaCurvature := if w1.alphaCurvature.val ≥ w2.alphaCurvature.val then w1.alphaCurvature else w2.alphaCurvature
    , alphaTopology  := if w1.alphaTopology.val  ≥ w2.alphaTopology.val  then w1.alphaTopology  else w2.alphaTopology
    , alphaCoupling  := if w1.alphaCoupling.val  ≥ w2.alphaCoupling.val  then w1.alphaCoupling  else w2.alphaCoupling
    , alphaResidual  := if w1.alphaResidual.val  ≥ w2.alphaResidual.val  then w1.alphaResidual  else w2.alphaResidual }
  -- irreconcilable: dominant modes differ AND both are strong
  let dom1 := dominantManifestation w1
  let dom2 := dominantManifestation w2
  let irreconcilable := dom1 != dom2
                     && f1.activationNorm.val > punctureThreshold.val
                     && f2.activationNorm.val > punctureThreshold.val
  { spectrum       := f1.spectrum  -- use first object's interior as reference
  , weights        := combined
  , activationNorm := modalNorm combined
  , sourceDim      := f1.sourceDim
  , receiptsClosed := !irreconcilable }

-- ═══════════════════════════════════════════════════════════════════
-- §8  Witnesses
-- ═══════════════════════════════════════════════════════════════════

-- Cool boundary: low activation, receipts close → Admitted cool.
def coolBoundary : BoundaryField :=
  BoundaryField.fromSpectrum
    (fromBind
      { omegaM := ⟨9830⟩, rK := ⟨6554⟩, dQ := ⟨3277⟩, lacun := ⟨3277⟩
      , bk0 := ⟨1638⟩, bk1 := ⟨1638⟩, bk2 := ⟨1638⟩
      , perc := ⟨3277⟩, curv := ⟨6554⟩, eta := ⟨3277⟩, eps := ⟨1638⟩ }
      ⟨0⟩)
    ⟨4, by omega⟩
    true

#eval (eigenFireGate coolBoundary).verdict
-- expected: BoundaryVerdict.admitted ... false  (cool, not eigenfire)

-- Hot wall: coupling and stress peak, receipts still close → Admitted hot.
def hotWallBind : BindOperator :=
  { omegaM := ⟨13107⟩, rK := ⟨52429⟩, dQ := ⟨26214⟩, lacun := ⟨16384⟩
  , bk0 := ⟨6554⟩, bk1 := ⟨19661⟩, bk2 := ⟨6554⟩
  , perc := ⟨26214⟩, curv := ⟨45875⟩, eta := ⟨58982⟩, eps := ⟨9830⟩ }

def hotWall : BoundaryField :=
  BoundaryField.fromSpectrum (fromBind hotWallBind ⟨32768⟩) ⟨8, by omega⟩ true

#eval (eigenFireGate hotWall).verdict
-- expected: BoundaryVerdict.admitted .coupling true  (eigenfire, coupling dominant)

-- Underverse: receipts don't close, below puncture.
def underverseBoundary : BoundaryField :=
  { (BoundaryField.fromSpectrum (fromBind hotWallBind ⟨32768⟩) ⟨8, by omega⟩ false)
      with receiptsClosed := false }

#eval (eigenFireGate underverseBoundary).verdict
-- expected: BoundaryVerdict.underverseEntry ...

-- Wormhole throat: unstoppable force meets immovable object.
-- Object A: maximal coupling (unstoppable, motion eigenvalue → max)
def unstoppableForce : BoundaryField :=
  BoundaryField.fromSpectrum
    (fromBind
      { omegaM := ⟨3277⟩, rK := ⟨3277⟩, dQ := ⟨3277⟩, lacun := ⟨3277⟩
      , bk0 := ⟨3277⟩, bk1 := ⟨3277⟩, bk2 := ⟨3277⟩
      , perc := ⟨3277⟩, curv := ⟨3277⟩, eta := ⟨65535⟩, eps := ⟨1638⟩ }
      ⟨65535⟩)
    ⟨8, by omega⟩ true

-- Object B: zero coupling but maximal density, topology, and curvature —
-- immovable because its density/topology modes dominate at maximum.
-- alphaDensity = (omegaM/2 + dQ/2) = (32767 + 32767) = 65534 > puncture threshold.
def immovableObject : BoundaryField :=
  BoundaryField.fromSpectrum
    (fromBind
      { omegaM := ⟨65535⟩, rK := ⟨65535⟩, dQ := ⟨65535⟩, lacun := ⟨65535⟩
      , bk0 := ⟨65535⟩, bk1 := ⟨65535⟩, bk2 := ⟨65535⟩
      , perc := ⟨65535⟩, curv := ⟨65535⟩, eta := ⟨0⟩, eps := ⟨1638⟩ }
      ⟨65535⟩)
    ⟨8, by omega⟩ true

def throatCollision : BoundaryField := collide unstoppableForce immovableObject

#eval throatCollision.receiptsClosed
-- expected: false  (irreconcilable: coupling vs void, both above puncture threshold)

#eval (eigenFireGate throatCollision).verdict
-- expected: BoundaryVerdict.geodesicPromotion { sourceChart := 8, targetChart := 9, ... }

-- Check promotion type at dim 16 → loopback.
def dim16Field : BoundaryField :=
  { throatCollision with sourceDim := ⟨16, by omega⟩ }

#eval match (eigenFireGate dim16Field).verdict with
  | .geodesicPromotion r => r.promotionType
  | _ => PromotionType.dimensionalExtrusion
-- expected: PromotionType.loopbackCompaction  (at dim=16, Π gate loops back)

end Semantics.HCMMR.Kernels.BoundaryEigenFire
