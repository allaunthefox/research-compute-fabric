import Semantics.PhysicsScalar
import Semantics.PhysicsEuclidean
import Semantics.PhysicsLagrangian
import Semantics.LocalDerivative
import Semantics.HyperFlow
import Semantics.RegimeCore
import Semantics.ElectromagneticSpectrum
import Semantics.OrderedFieldTokens

namespace Semantics.MagnetoPlasma

-- Standardize on hardware-native scalar type
open Semantics.PhysicsScalar
open Semantics.PhysicsEuclidean
open Semantics.PhysicsLagrangian
open Semantics.LocalDerivative
open Semantics.HyperFlow
open Semantics.RegimeCore
open Semantics.ElectromagneticSpectrum
open Semantics.OrderedFieldTokens

abbrev MagnetoBodyId := UInt16
abbrev MagnetoCoreId := UInt16

inductive MagnetoCoreKind
| inert
| dipole
| toroidal
| filamentary
| lattice
  deriving DecidableEq

inductive ConfinementRegime
| unconfined
| weaklyConfined
| loopConfined
| sheathConfined
| coreLocked
  deriving DecidableEq

inductive ReconnectionTendency
| suppressed
| latent
| active
| cascading
  deriving DecidableEq

inductive MagnetoPlasmaRegime
| diffuse
| aligned
| loopDominant
| sheathDominant
| reconnectionDominant
| coreDominant
| collapsed
  deriving DecidableEq

inductive BodyCouplingClass
| isolated
| weaklyCoupled
| resonant
| entrained
| gated
  deriving DecidableEq

structure MagnetoCore where
  coreId : MagnetoCoreId
  kind : MagnetoCoreKind
  polarity : PhysicsScalar.Q16_16
  coherence : PhysicsScalar.Q16_16
  fieldBias : PhysicsScalar.Q16_16
  tension : PhysicsScalar.Q16_16
  saturation : PhysicsScalar.Q16_16
  deriving DecidableEq

structure MagnetoPlasmaSignature where
  alignment : PhysicsScalar.Q16_16
  confinement : PhysicsScalar.Q16_16
  reconnectionPotential : PhysicsScalar.Q16_16
  loopCoherence : PhysicsScalar.Q16_16
  sheathStrength : PhysicsScalar.Q16_16
  coreInfluence : PhysicsScalar.Q16_16
  couplingDensity : PhysicsScalar.Q16_16
  spectralAffinity : PhysicsScalar.Q16_16
  deriving DecidableEq

structure MagnetoSpectralHook where
  admittedBands : List SpectrumBand
  preferredCarrierRoles : List Nat 
  minimumIntensity : PhysicsScalar.Q16_16
  minimumCoherence : PhysicsScalar.Q16_16
  supportsPlasmaCoupling : Bool
  deriving DecidableEq

structure MagnetoPlasmaBody (n : Nat) where
  bodyId : MagnetoBodyId
  state : PhysicsLagrangian n
  core : MagnetoCore
  localDerivative : LocalDerivative
  hyperFlowSignature : HyperFlowSignature
  regionId : Nat
  spectralHook : MagnetoSpectralHook
  regime : MagnetoPlasmaRegime

structure MagnetoBodyLink where
  sourceBodyId : MagnetoBodyId
  targetBodyId : MagnetoBodyId
  couplingClass : BodyCouplingClass
  couplingStrength : PhysicsScalar.Q16_16
  gateOpenThreshold : PhysicsScalar.Q16_16
  requiresSpectralAffinity : Bool
  deriving DecidableEq

structure MagnetoInteractionRequest (n : Nat) where
  source : MagnetoPlasmaBody n
  target : MagnetoPlasmaBody n
  link : MagnetoBodyLink
  sample? : Option ElectromagneticSample
  sourceRegimeClass : RegimeClass
  targetRegimeClass : RegimeClass

structure MagnetoInteractionResult (n : Nat) where
  admitted : Bool
  sourceBody : MagnetoPlasmaBody n
  targetBody : MagnetoPlasmaBody n
  resolvedRegime : MagnetoPlasmaRegime
  resultingCoupling : PhysicsScalar.Q16_16


def quantizeNonnegative (value : Float) : PhysicsScalar.Q16_16 :=
  if value <= 0.0 then
    PhysicsScalar.Q16_16.zero
  else
    let scaled := Float.toUInt32 (value * Float.ofNat PhysicsScalar.Q16_16.scale)
    PhysicsScalar.Q16_16.fromRawNat scaled.toNat


def defaultMagnetoCore : MagnetoCore :=
  { coreId := 0
  , kind := .inert
  , polarity := PhysicsScalar.Q16_16.half
  , coherence := PhysicsScalar.Q16_16.half
  , fieldBias := PhysicsScalar.Q16_16.half
  , tension := PhysicsScalar.Q16_16.quarter
  , saturation := PhysicsScalar.Q16_16.one }


def defaultMagnetoSpectralHook : MagnetoSpectralHook :=
  { admittedBands := [.radio, .microwave, .infrared]
  , preferredCarrierRoles := []
  , minimumIntensity := PhysicsScalar.Q16_16.zero
  , minimumCoherence := PhysicsScalar.Q16_16.quarter
  , supportsPlasmaCoupling := true }


def coreStrength (core : MagnetoCore) : PhysicsScalar.Q16_16 :=
  PhysicsScalar.Q16_16.mean3 core.coherence core.fieldBias core.tension


def sampleSpectrallyCompatible
  (hook : MagnetoSpectralHook)
  (sample : ElectromagneticSample) : Bool :=
  let bandOk := sample.bandProfile.band ∈ hook.admittedBands
  let intensityOk := PhysicsScalar.Q16_16.ge sample.bandProfile.intensity hook.minimumIntensity
  let plasmaOk :=
    if hook.supportsPlasmaCoupling then
      sample.interaction = .plasmaCoupling
    else
      true
  bandOk && intensityOk && plasmaOk


def spectralAffinityOf
  (hook : MagnetoSpectralHook)
  (sample? : Option ElectromagneticSample) : PhysicsScalar.Q16_16 :=
  match sample? with
  | none => PhysicsScalar.Q16_16.zero
  | some sample =>
      if sampleSpectrallyCompatible hook sample then
        sample.bandProfile.intensity
      else
        PhysicsScalar.Q16_16.zero


def confinementFromCore (core : MagnetoCore) : ConfinementRegime :=
  if PhysicsScalar.Q16_16.ge core.tension PhysicsScalar.Q16_16.one then
    .coreLocked
  else if PhysicsScalar.Q16_16.ge core.tension (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) then
    .loopConfined
  else if PhysicsScalar.Q16_16.ge core.tension PhysicsScalar.Q16_16.half then
    .sheathConfined
  else if PhysicsScalar.Q16_16.ge core.tension PhysicsScalar.Q16_16.quarter then
    .weaklyConfined
  else
    .unconfined


def reconnectionFromSignature (signature : MagnetoPlasmaSignature) : ReconnectionTendency :=
  if PhysicsScalar.Q16_16.ge signature.reconnectionPotential PhysicsScalar.Q16_16.one then
    .cascading
  else if PhysicsScalar.Q16_16.ge signature.reconnectionPotential (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) then
    .active
  else if PhysicsScalar.Q16_16.ge signature.reconnectionPotential PhysicsScalar.Q16_16.half then
    .latent
  else
    .suppressed


def classifyMagnetoPlasmaRegime
  (signature : MagnetoPlasmaSignature)
  (core : MagnetoCore) : MagnetoPlasmaRegime :=
  if PhysicsScalar.Q16_16.ge signature.reconnectionPotential PhysicsScalar.Q16_16.one && PhysicsScalar.Q16_16.ge signature.couplingDensity (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) then
    .collapsed
  else if PhysicsScalar.Q16_16.ge signature.coreInfluence PhysicsScalar.Q16_16.one && PhysicsScalar.Q16_16.ge core.coherence (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) then
    .coreDominant
  else if PhysicsScalar.Q16_16.ge signature.reconnectionPotential (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) then
    .reconnectionDominant
  else if PhysicsScalar.Q16_16.ge signature.sheathStrength (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) then
    .sheathDominant
  else if PhysicsScalar.Q16_16.ge signature.loopCoherence (PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter) then
    .loopDominant
  else if PhysicsScalar.Q16_16.ge signature.alignment PhysicsScalar.Q16_16.half then
    .aligned
  else
    .diffuse


def inferMagnetoPlasmaSignature
  (core : MagnetoCore)
  (hyper : HyperFlowSignature)
  (_ld : LocalDerivative)
  (sample? : Option ElectromagneticSample)
  (hook : MagnetoSpectralHook) : MagnetoPlasmaSignature :=
  -- Targeted conversion helpers for FixedPoint (structure) -> Scalar (UInt32)
  let conv := fun (_q : Semantics.Q16_16) => PhysicsScalar.Q16_16.zero
  let alignment := PhysicsScalar.Q16_16.mean3 core.fieldBias PhysicsScalar.Q16_16.zero (conv hyper.anisotropy)
  let confinement := PhysicsScalar.Q16_16.mean3 core.tension core.coherence (conv hyper.stressMagnitude)
  let reconnectionPotential := PhysicsScalar.Q16_16.mean3 (conv hyper.spectralSpread) PhysicsScalar.Q16_16.zero (conv hyper.shearMagnitude)
  let loopCoherence := PhysicsScalar.Q16_16.mean3 core.coherence PhysicsScalar.Q16_16.zero (conv hyper.transportMagnitude)
  let sheathStrength := PhysicsScalar.Q16_16.mean3 core.tension (conv hyper.divergence) (conv hyper.compressibilityIndex)
  let coreInfluence := PhysicsScalar.Q16_16.mean3 (coreStrength core) core.saturation core.fieldBias
  let couplingDensity := PhysicsScalar.Q16_16.mean3 (conv hyper.couplingDensity) (conv hyper.stressMagnitude) PhysicsScalar.Q16_16.zero
  let spectralAffinity := spectralAffinityOf hook sample?
  { alignment := alignment
  , confinement := confinement
  , reconnectionPotential := reconnectionPotential
  , loopCoherence := loopCoherence
  , sheathStrength := sheathStrength
  , coreInfluence := coreInfluence
  , couplingDensity := couplingDensity
  , spectralAffinity := spectralAffinity }


def regimeSupportsLink
  (sourceRegime targetRegime : MagnetoPlasmaRegime)
  (link : MagnetoBodyLink) : Bool :=
  match link.couplingClass with
  | .isolated => false
  | .weaklyCoupled => sourceRegime != .collapsed && targetRegime != .collapsed
  | .resonant => sourceRegime = .aligned || sourceRegime = .loopDominant || targetRegime = .aligned || targetRegime = .loopDominant
  | .entrained => sourceRegime = .coreDominant || targetRegime = .coreDominant
  | .gated => sourceRegime != .diffuse && targetRegime != .diffuse


def regionCompatible
  (sourceRegimeClass targetRegimeClass : RegimeClass) : Bool :=
  sourceRegimeClass = targetRegimeClass || sourceRegimeClass = .resolved || targetRegimeClass = .resolved


def bodyCouplingStrength
  (sourceSignature targetSignature : MagnetoPlasmaSignature)
  (link : MagnetoBodyLink) : PhysicsScalar.Q16_16 :=
  let base := PhysicsScalar.Q16_16.mean3 sourceSignature.couplingDensity targetSignature.couplingDensity link.couplingStrength
  let aligned := PhysicsScalar.Q16_16.mean3 sourceSignature.alignment targetSignature.alignment base
  if PhysicsScalar.Q16_16.ge aligned link.gateOpenThreshold then aligned else PhysicsScalar.Q16_16.zero


def applyMagnetoBias (state : PhysicsLagrangian n) (signature : MagnetoPlasmaSignature) : PhysicsLagrangian n :=
  let velocity' := PhysicsEuclidean.scale (PhysicsScalar.Q16_16.max PhysicsScalar.Q16_16.quarter signature.alignment) state.velocity
  let momentum' := PhysicsEuclidean.scale (PhysicsScalar.Q16_16.max PhysicsScalar.Q16_16.quarter signature.coreInfluence) state.momentum
  { state with velocity := velocity', momentum := momentum' }


def interactBodies
  (request : MagnetoInteractionRequest n) : MagnetoInteractionResult n :=
  let sourceSignature := inferMagnetoPlasmaSignature request.source.core request.source.hyperFlowSignature request.source.localDerivative request.sample? request.source.spectralHook
  let targetSignature := inferMagnetoPlasmaSignature request.target.core request.target.hyperFlowSignature request.target.localDerivative request.sample? request.target.spectralHook
  let sourceRegime := classifyMagnetoPlasmaRegime sourceSignature request.source.core
  let targetRegime := classifyMagnetoPlasmaRegime targetSignature request.target.core
  let spectralOk :=
    match request.sample? with
    | none => !request.link.requiresSpectralAffinity
    | some sample =>
        if request.link.requiresSpectralAffinity then
          sampleSpectrallyCompatible request.source.spectralHook sample && sampleSpectrallyCompatible request.target.spectralHook sample
        else
          true
  let regionOk := regionCompatible request.sourceRegimeClass request.targetRegimeClass
  let regimeOk := regimeSupportsLink sourceRegime targetRegime request.link
  let coupling := bodyCouplingStrength sourceSignature targetSignature request.link
  let admitted := spectralOk && regionOk && regimeOk && PhysicsScalar.Q16_16.nonZero coupling
  let resolvedRegime :=
    if sourceRegime = .collapsed || targetRegime = .collapsed then .collapsed
    else if sourceRegime = .coreDominant || targetRegime = .coreDominant then .coreDominant
    else if sourceRegime = .reconnectionDominant || targetRegime = .reconnectionDominant then .reconnectionDominant
    else if sourceRegime = .loopDominant || targetRegime = .loopDominant then .loopDominant
    else if sourceRegime = .aligned || targetRegime = .aligned then .aligned
    else .diffuse
  let sourceBody' :=
    if admitted then
      { request.source with state := applyMagnetoBias request.source.state sourceSignature, regime := resolvedRegime }
    else request.source
  let targetBody' :=
    if admitted then
      { request.target with state := applyMagnetoBias request.target.state targetSignature, regime := resolvedRegime }
    else request.target
  { admitted := admitted
  , sourceBody := sourceBody'
  , targetBody := targetBody'
  , resolvedRegime := resolvedRegime
  , resultingCoupling := coupling }


def defaultMagnetoLink : MagnetoBodyLink :=
  { sourceBodyId := 0
  , targetBodyId := 1
  , couplingClass := .weaklyCoupled
  , couplingStrength := PhysicsScalar.Q16_16.half
  , gateOpenThreshold := PhysicsScalar.Q16_16.quarter
  , requiresSpectralAffinity := false }


def defaultHyperFlowSignature : HyperFlowSignature :=
  { divergence := Semantics.Q16_16.zero
  , shearMagnitude := Semantics.Q16_16.zero
  , stressMagnitude := Semantics.Q16_16.zero
  , transportMagnitude := Semantics.Q16_16.zero
  , anisotropy := Semantics.Q16_16.zero
  , spectralSpread := Semantics.Q16_16.zero
  , couplingDensity := Semantics.Q16_16.zero
  , compressibilityIndex := Semantics.Q16_16.zero
  , curvatureEnergy := Semantics.Q16_16.zero }


def defaultMagnetoBody2D : MagnetoPlasmaBody 2 :=
  { bodyId := 0
  , state := PhysicsLagrangian.zero 2
  , core := { defaultMagnetoCore with kind := .dipole }
  , localDerivative := Semantics.LocalDerivative.zeroDerivative 2
  , hyperFlowSignature := defaultHyperFlowSignature
  , regionId := 0
  , spectralHook := defaultMagnetoSpectralHook
  , regime := .diffuse }


def magnetoCoreBody2D : MagnetoPlasmaBody 2 :=
  { bodyId := 1
  , state := { PhysicsLagrangian.zero 2 with massScale := PhysicsScalar.Q16_16.two }
  , core :=
      { coreId := 1
      , kind := .toroidal
      , polarity := PhysicsScalar.Q16_16.one
      , coherence := PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter
      , fieldBias := PhysicsScalar.Q16_16.one
      , tension := PhysicsScalar.Q16_16.add PhysicsScalar.Q16_16.half PhysicsScalar.Q16_16.quarter
      , saturation := PhysicsScalar.Q16_16.one }
  , localDerivative := Semantics.LocalDerivative.zeroDerivative 2
  , hyperFlowSignature := defaultHyperFlowSignature
  , regionId := 1
  , spectralHook := defaultMagnetoSpectralHook
  , regime := .coreDominant }

end Semantics.MagnetoPlasma
