import Semantics.PhysicsScalar
import Semantics.PhysicsEuclidean
import Semantics.PhysicsLagrangian
import Semantics.LocalDerivative
import Semantics.HyperFlow
import Semantics.RegimeCore
import Semantics.ElectromagneticSpectrum

namespace Semantics.MagnetoPlasma

open Semantics.PhysicsScalar
open Semantics.PhysicsEuclidean
open Semantics.PhysicsLagrangian
open Semantics.LocalDerivative
open Semantics.HyperFlow
open Semantics.RegimeCore
open Semantics.ElectromagneticSpectrum

abbrev MagnetoBodyId := UInt16
abbrev MagnetoCoreId := UInt16

inductive MagnetoCoreKind
| inert
| dipole
| toroidal
| filamentary
| lattice
  deriving Repr, DecidableEq

inductive ConfinementRegime
| unconfined
| weaklyConfined
| loopConfined
| sheathConfined
| coreLocked
  deriving Repr, DecidableEq

inductive ReconnectionTendency
| suppressed
| latent
| active
| cascading
  deriving Repr, DecidableEq

inductive MagnetoPlasmaRegime
| diffuse
| aligned
| loopDominant
| sheathDominant
| reconnectionDominant
| coreDominant
| collapsed
  deriving Repr, DecidableEq

inductive BodyCouplingClass
| isolated
| weaklyCoupled
| resonant
| entrained
| gated
  deriving Repr, DecidableEq

structure MagnetoCore where
  coreId : MagnetoCoreId
  kind : MagnetoCoreKind
  polarity : Q16_16
  coherence : Q16_16
  fieldBias : Q16_16
  tension : Q16_16
  saturation : Q16_16
  deriving Repr, DecidableEq

structure MagnetoPlasmaSignature where
  alignment : Q16_16
  confinement : Q16_16
  reconnectionPotential : Q16_16
  loopCoherence : Q16_16
  sheathStrength : Q16_16
  coreInfluence : Q16_16
  couplingDensity : Q16_16
  spectralAffinity : Q16_16
  deriving Repr, DecidableEq

structure MagnetoSpectralHook where
  admittedBands : List SpectrumBand
  preferredCarrierRoles : List CarrierRole
  minimumIntensity : Q16_16
  minimumCoherence : Q16_16
  supportsPlasmaCoupling : Bool
  deriving Repr, DecidableEq

structure MagnetoPlasmaBody (n : Nat) where
  bodyId : MagnetoBodyId
  state : PhysicsLagrangian n
  core : MagnetoCore
  localDerivative : LocalDerivative
  hyperFlowSignature : HyperFlowSignature
  regionId : RegionId
  spectralHook : MagnetoSpectralHook
  regime : MagnetoPlasmaRegime
  deriving Repr

structure MagnetoBodyLink where
  sourceBodyId : MagnetoBodyId
  targetBodyId : MagnetoBodyId
  couplingClass : BodyCouplingClass
  couplingStrength : Q16_16
  gateOpenThreshold : Q16_16
  requiresSpectralAffinity : Bool
  deriving Repr, DecidableEq

structure MagnetoInteractionRequest (n : Nat) where
  source : MagnetoPlasmaBody n
  target : MagnetoPlasmaBody n
  link : MagnetoBodyLink
  sample? : Option ElectromagneticSample
  sourceRegimeClass : RegimeClass
  targetRegimeClass : RegimeClass
  deriving Repr

structure MagnetoInteractionResult (n : Nat) where
  admitted : Bool
  sourceBody : MagnetoPlasmaBody n
  targetBody : MagnetoPlasmaBody n
  resolvedRegime : MagnetoPlasmaRegime
  resultingCoupling : Q16_16
  deriving Repr


def quantizeNonnegative (value : Float) : Q16_16 :=
  if value <= 0.0 then
    Q16_16.zero
  else
    let scaled := Float.toUInt32 (value * Float.ofNat Q16_16.scale)
    Q16_16.fromRawNat scaled.toNat


def defaultMagnetoCore : MagnetoCore :=
  { coreId := 0
  , kind := .inert
  , polarity := Q16_16.half
  , coherence := Q16_16.half
  , fieldBias := Q16_16.half
  , tension := Q16_16.quarter
  , saturation := Q16_16.one }


def defaultMagnetoSpectralHook : MagnetoSpectralHook :=
  { admittedBands := [.radio, .microwave, .infrared, .visible]
  , preferredCarrierRoles := [.ambient, .activeProbe, .sensorFeed]
  , minimumIntensity := Q16_16.zero
  , minimumCoherence := Q16_16.quarter
  , supportsPlasmaCoupling := true }


def coreStrength (core : MagnetoCore) : Q16_16 :=
  Q16_16.mean3 core.coherence core.fieldBias core.tension


def sampleSpectrallyCompatible
  (hook : MagnetoSpectralHook)
  (sample : ElectromagneticSample) : Bool :=
  let bandOk := sample.bandProfile.band ∈ hook.admittedBands
  let roleOk := hook.preferredCarrierRoles.isEmpty || sample.role ∈ hook.preferredCarrierRoles
  let intensityOk := Q16_16.ge sample.intensity hook.minimumIntensity
  let coherenceOk := Q16_16.ge sample.coherence hook.minimumCoherence
  let plasmaOk :=
    if hook.supportsPlasmaCoupling then
      sample.interaction = .plasmaCoupling || sample.interaction = .activeSensing || sample.interaction = .communication
    else
      true
  bandOk && roleOk && intensityOk && coherenceOk && plasmaOk


def spectralAffinityOf
  (hook : MagnetoSpectralHook)
  (sample? : Option ElectromagneticSample) : Q16_16 :=
  match sample? with
  | none => Q16_16.zero
  | some sample =>
      if sampleSpectrallyCompatible hook sample then
        Q16_16.mean3 sample.intensity sample.coherence sample.modulation
      else
        Q16_16.zero


def confinementFromCore (core : MagnetoCore) : ConfinementRegime :=
  if Q16_16.ge core.tension Q16_16.one then
    .coreLocked
  else if Q16_16.ge core.tension (Q16_16.add Q16_16.half Q16_16.quarter) then
    .loopConfined
  else if Q16_16.ge core.tension Q16_16.half then
    .sheathConfined
  else if Q16_16.ge core.tension Q16_16.quarter then
    .weaklyConfined
  else
    .unconfined


def reconnectionFromSignature (signature : MagnetoPlasmaSignature) : ReconnectionTendency :=
  if Q16_16.ge signature.reconnectionPotential Q16_16.one then
    .cascading
  else if Q16_16.ge signature.reconnectionPotential (Q16_16.add Q16_16.half Q16_16.quarter) then
    .active
  else if Q16_16.ge signature.reconnectionPotential Q16_16.half then
    .latent
  else
    .suppressed


def classifyMagnetoPlasmaRegime
  (signature : MagnetoPlasmaSignature)
  (core : MagnetoCore) : MagnetoPlasmaRegime :=
  if Q16_16.ge signature.reconnectionPotential Q16_16.one && Q16_16.ge signature.couplingDensity (Q16_16.add Q16_16.half Q16_16.quarter) then
    .collapsed
  else if Q16_16.ge signature.coreInfluence Q16_16.one && Q16_16.ge core.coherence (Q16_16.add Q16_16.half Q16_16.quarter) then
    .coreDominant
  else if Q16_16.ge signature.reconnectionPotential (Q16_16.add Q16_16.half Q16_16.quarter) then
    .reconnectionDominant
  else if Q16_16.ge signature.sheathStrength (Q16_16.add Q16_16.half Q16_16.quarter) then
    .sheathDominant
  else if Q16_16.ge signature.loopCoherence (Q16_16.add Q16_16.half Q16_16.quarter) then
    .loopDominant
  else if Q16_16.ge signature.alignment Q16_16.half then
    .aligned
  else
    .diffuse


def inferMagnetoPlasmaSignature
  (core : MagnetoCore)
  (hyper : HyperFlowSignature)
  (ld : LocalDerivative)
  (sample? : Option ElectromagneticSample)
  (hook : MagnetoSpectralHook) : MagnetoPlasmaSignature :=
  let alignment := Q16_16.mean3 core.fieldBias (quantizeNonnegative (Float.abs (divergence ld))) (quantizeNonnegative (Float.abs hyper.anisotropy))
  let confinement := Q16_16.mean3 core.tension core.coherence (quantizeNonnegative (Float.abs hyper.stressMagnitude))
  let reconnectionPotential := Q16_16.mean3 (quantizeNonnegative (Float.abs hyper.spectralSpread)) (quantizeNonnegative (matrixFrobeniusNorm (torsion ld))) (quantizeNonnegative (Float.abs hyper.shearMagnitude))
  let loopCoherence := Q16_16.mean3 core.coherence (quantizeNonnegative (curvature ld)) (quantizeNonnegative (Float.abs hyper.transportMagnitude))
  let sheathStrength := Q16_16.mean3 core.tension (quantizeNonnegative (Float.abs hyper.divergence)) (quantizeNonnegative (Float.abs hyper.compressibilityIndex))
  let coreInfluence := Q16_16.mean3 (coreStrength core) core.saturation core.fieldBias
  let couplingDensity := Q16_16.mean3 (quantizeNonnegative (Float.abs hyper.couplingDensity)) (quantizeNonnegative (Float.abs hyper.stressMagnitude)) (quantizeNonnegative (Float.abs (divergence ld)))
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
  sourceRegimeClass = targetRegimeClass || sourceRegimeClass = .spectral || targetRegimeClass = .spectral || targetRegimeClass = .boundary


def bodyCouplingStrength
  (sourceSignature targetSignature : MagnetoPlasmaSignature)
  (link : MagnetoBodyLink) : Q16_16 :=
  let base := Q16_16.mean3 sourceSignature.couplingDensity targetSignature.couplingDensity link.couplingStrength
  let aligned := Q16_16.mean3 sourceSignature.alignment targetSignature.alignment base
  if Q16_16.ge aligned link.gateOpenThreshold then aligned else Q16_16.zero


def applyMagnetoBias (state : PhysicsLagrangian n) (signature : MagnetoPlasmaSignature) : PhysicsLagrangian n :=
  let velocity' := PhysicsEuclidean.scale (Q16_16.max Q16_16.quarter signature.alignment) state.velocity
  let momentum' := PhysicsEuclidean.scale (Q16_16.max Q16_16.quarter signature.coreInfluence) state.momentum
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
  let admitted := spectralOk && regionOk && regimeOk && Q16_16.nonZero coupling
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
  , couplingStrength := Q16_16.half
  , gateOpenThreshold := Q16_16.quarter
  , requiresSpectralAffinity := false }


def defaultHyperFlowSignature : HyperFlowSignature :=
  { divergence := 0.0
  , shearMagnitude := 0.0
  , stressMagnitude := 0.0
  , transportMagnitude := 0.0
  , anisotropy := 0.0
  , spectralSpread := 0.0
  , couplingDensity := 0.0
  , compressibilityIndex := 0.0
  , curvatureEnergy := 0.0 }


def defaultMagnetoBody2D : MagnetoPlasmaBody 2 :=
  { bodyId := 0
  , state := PhysicsLagrangian.zero 2
  , core := { defaultMagnetoCore with kind := .dipole }
  , localDerivative := zeroDerivative 2
  , hyperFlowSignature := defaultHyperFlowSignature
  , regionId := 0
  , spectralHook := defaultMagnetoSpectralHook
  , regime := .diffuse }


def magnetoCoreBody2D : MagnetoPlasmaBody 2 :=
  { bodyId := 1
  , state := { PhysicsLagrangian.zero 2 with massScale := Q16_16.two }
  , core :=
      { coreId := 1
      , kind := .toroidal
      , polarity := Q16_16.one
      , coherence := Q16_16.add Q16_16.half Q16_16.quarter
      , fieldBias := Q16_16.one
      , tension := Q16_16.add Q16_16.half Q16_16.quarter
      , saturation := Q16_16.one }
  , localDerivative := zeroDerivative 2
  , hyperFlowSignature := defaultHyperFlowSignature
  , regionId := 1
  , spectralHook := defaultMagnetoSpectralHook
  , regime := .coreDominant }

end Semantics.MagnetoPlasma
