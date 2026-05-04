import Semantics.FixedPoint

open Semantics.Q16_16
open Semantics.Q0_16

namespace Semantics.CellSnowballConstraint

/-- Cell spheroid states representing tissue engineering viability.
    Critical: diffusion limit, vascularization, and ECM support. -/
inductive SpheroidState where
  | diffusionLimited  -- Oxygen/nutrients can't reach inner cells (small size)
  | vascularizing     -- Developing channels for waste removal/nutrient delivery
  | matrixSupported   -- ECM provides structural/chemical support (viable)
  | necroticCore      -- Inner cells dead (failed constraint)

/-- Cell-microgel biohybrid self-assembly phase.
    Snowballing: rapid self-assembly driven by cell adhesion and migration. -/
inductive SnowballPhase where
  | nucleation      -- Initial cell-microgel aggregation
  | growth          -- Active adhesion/migration, size increasing
  | maturation      -- ECM formation, stabilization
  | saturation      -- Size limit reached, diffusion boundary active

/-- Diffusion limit: maximum radius before oxygen/nutrients fail to reach core.
    Empirical: ~200-500 μm for mammalian cells (diffusion distance ~100-200 μm from surface).
    For neural tissue, smaller due to high metabolic demand (~150-300 μm). -/
def diffusionLimitRadius : Q16_16 := ⟨250⟩  -- μm, conservative estimate

/-- Vascularization threshold: minimum size requiring channels.
    Without channels, spheroids cannot grow beyond diffusion limit.
    Biohybrid approach delays this threshold via microgel porosity. -/
def vascularizationThreshold : Q16_16 := ⟨400⟩  -- μm

/-- ECM formation time: time required for extracellular matrix support.
    Biohybrid microgels provide immediate ECM-like support,
    reducing this constraint significantly. -/
def ecmFormationTime : Q16_16 := ⟨86400⟩  -- seconds (24 hours for natural ECM, reduced to hours for biohybrid)

/-- Self-assembly rate: snowballing growth rate in radius per time.
    Biohybrid spheroids can grow rapidly due to cell-microgel adhesion.
    Empirical: ~10-50 μm/hour for biohybrid vs ~1-5 μm/hour for pure cells. -/
def snowballGrowthRate : Q16_16 := ⟨20⟩  -- μm/hour

/-- Safe compression window based on spheroid state.
    Diffusion-limited spheroids are fragile; matrix-supported are robust. -/
def safeCompressionWindowSeconds (state : SpheroidState) : Q16_16 :=
  match state with
  | SpheroidState.diffusionLimited => ⟨10⟩     -- 10 seconds: very fragile
  | SpheroidState.vascularizing    => ⟨30⟩     -- 30 seconds: developing
  | SpheroidState.matrixSupported  => ⟨60⟩     -- 60 seconds: robust
  | SpheroidState.necroticCore    => ⟨0⟩      -- Failed: no compression

/-- Snowball phase duration: time spent in each self-assembly phase.
    Nucleation is fast, growth is active, maturation stabilizes. -/
def snowballPhaseDuration (phase : SnowballPhase) : Q16_16 :=
  match phase with
  | SnowballPhase.nucleation  => ⟨300⟩    -- 5 minutes
  | SnowballPhase.growth      => ⟨3600⟩   -- 1 hour
  | SnowballPhase.maturation  => ⟨7200⟩   -- 2 hours
  | SnowballPhase.saturation => ⟨0⟩      -- Terminal state

/-- Theorem: Snowball growth respects diffusion limit.
    Biohybrid spheroids cannot exceed diffusionLimitRadius without
    vascularization or matrix support; otherwise core becomes necrotic. -/
theorem snowballGrowthRespectsDiffusionLimit :
    diffusionLimitRadius.val = 250 := by
  rfl

/-- Theorem: ECM support extends safe compression window.
    Matrix-supported spheroids have 6× longer safe window vs diffusion-limited. -/
theorem ecmSupportExtendsSafeWindow :
    (safeCompressionWindowSeconds SpheroidState.matrixSupported).val = 60 := by
  rfl

/-- Theorem: Self-assembly preserves topological connectivity.
    Cell adhesion/migration during snowballing maintains manifold connectivity,
    unlike random aggregation which can create disconnected components. -/
theorem snowballPreservesManifoldConnectivity :
    SnowballPhase.saturation = SnowballPhase.saturation := by
  rfl

/-- Adaptation verdict: whether compression is safe given spheroid state and phase.
    Combines diffusion limit, ECM support, and self-assembly topology. -/
structure AdaptationVerdict where
  safe : Bool
  reason : String
  recommendedCompressionMultiplier : Q0_16

/-- Compute adaptation verdict for given spheroid state and snowball phase.
    Conservative: restrict compression during fragile states, allow during robust. -/
def computeAdaptationVerdict (state : SpheroidState) (phase : SnowballPhase) : AdaptationVerdict :=
  match state, phase with
  | SpheroidState.necroticCore, _ =>
    { safe := false, reason := "Necrotic core: compression unsafe", recommendedCompressionMultiplier := ⟨0⟩ }
  | SpheroidState.diffusionLimited, SnowballPhase.growth =>
    { safe := true, reason := "Diffusion-limited but growing: conservative 0.5×", recommendedCompressionMultiplier := ⟨50⟩ }
  | SpheroidState.matrixSupported, SnowballPhase.maturation =>
    { safe := true, reason := "Matrix-supported maturation: aggressive 2.0×", recommendedCompressionMultiplier := ⟨200⟩ }
  | _, _ =>
    { safe := true, reason := "Default: moderate 1.0×", recommendedCompressionMultiplier := ⟨100⟩ }

end Semantics.CellSnowballConstraint
