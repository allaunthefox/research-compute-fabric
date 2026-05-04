import Semantics.PhysicsScalar
import Semantics.ElectromagneticSpectrum
import Semantics.RegimeCore
import Semantics.BoundaryDynamics
import Semantics.CausalGeometry
import Semantics.ManifoldStructures
import Semantics.DomainState

namespace Semantics.SubstrateProfile

open Semantics.PhysicsScalar
open Semantics.ElectromagneticSpectrum
open Semantics.RegimeCore
open Semantics.BoundaryDynamics
open Semantics.CausalGeometry
open Semantics.ManifoldStructures
open Semantics.DomainState

inductive BoundaryKind
| interface
| sheath
| throat
| spectralCurtain
| reconnectionSurface
| dimensionalSeam
  deriving Repr, DecidableEq

inductive CausalOrientation
| forward
| backward
| lateral
| cyclic
| folded
  deriving Repr, DecidableEq

inductive InteractionClass
| communication
| passiveSensing
| activeSensing
| imaging
| illumination
| heating
| ionizingExposure
| plasmaCoupling
  deriving Repr, DecidableEq

structure CausalLink where
  orientation : CausalOrientation
  delay : PhysicsScalar.Q16_16
  requiresGate : Bool
  deriving Repr, DecidableEq

abbrev SubstrateId := UInt16

inductive SubstrateKind
| software
| fpga
| asic
| cpu
| gpu
| optical
| memristive
| spintronic
| biologicalLike
| hybrid
  deriving Repr, DecidableEq

inductive TimingResolution
| coarse
| tick
| fine
| phaseAware
| eventDriven
  deriving Repr, DecidableEq

inductive ExecutionStyle
| deterministic
| gated
| streaming
| eventDriven
| reconfigurable
| hybrid
  deriving Repr, DecidableEq

structure SpectralSupport where
  supportedBands : List SpectrumBand
  lineOfSightPreferred : Bool
  supportsActiveProbe : Bool
  supportsPassiveSensing : Bool
  supportsCommunication : Bool
  ionizingTolerance : PhysicsScalar.Q16_16
  deriving Repr, DecidableEq

structure BoundarySupport where
  supportedKinds : List BoundaryKind
  supportsDiffuseBoundaries : Bool
  supportsTurbulentBoundaries : Bool
  maximumFluidity : PhysicsScalar.Q16_16
  minimumCoherence : PhysicsScalar.Q16_16
  deriving Repr, DecidableEq

structure CausalSupport where
  supportedOrientations : List CausalOrientation
  supportsDelayedLinks : Bool
  supportsFoldedLinks : Bool
  supportsCyclicTraversal : Bool
  requiresGuardedTraversal : Bool
  maximumDelayMass : PhysicsScalar.Q16_16
  deriving Repr, DecidableEq

structure ResourceEnvelope where
  maxStateDim : Nat
  maxTransportDim : Nat
  maxTopologyDim : Nat
  maxRenderDim : Nat
  channelBudget : UInt16
  nodeBudget : UInt16
  linkBudget : UInt16
  deriving Repr, DecidableEq

structure SubstrateProfile where
  substrateId : SubstrateId
  label : String
  kind : SubstrateKind
  timingResolution : TimingResolution
  executionStyle : ExecutionStyle
  resourceEnvelope : ResourceEnvelope
  supportsResolvedOnly : Bool
  spectralSupport : SpectralSupport
  boundarySupport : BoundarySupport
  causalSupport : CausalSupport
  deriving Repr, DecidableEq


def supportsBand (profile : SubstrateProfile) (band : SpectrumBand) : Bool :=
  band ∈ profile.spectralSupport.supportedBands


def supportsBoundaryKind (profile : SubstrateProfile) (kind : BoundaryKind) : Bool :=
  kind ∈ profile.boundarySupport.supportedKinds


def supportsOrientation (profile : SubstrateProfile) (orientation : CausalOrientation) : Bool :=
  orientation ∈ profile.causalSupport.supportedOrientations


def supportsDimensions (profile : SubstrateProfile) (stateDim transportDim topologyDim renderDim : Nat) : Bool :=
  stateDim <= profile.resourceEnvelope.maxStateDim &&
  transportDim <= profile.resourceEnvelope.maxTransportDim &&
  topologyDim <= profile.resourceEnvelope.maxTopologyDim &&
  renderDim <= profile.resourceEnvelope.maxRenderDim


def supportsFluidity (profile : SubstrateProfile) (fluidity : PhysicsScalar.Q16_16) : Bool :=
  PhysicsScalar.Q16_16.le fluidity profile.boundarySupport.maximumFluidity


def supportsDelayMass (profile : SubstrateProfile) (delayMass : PhysicsScalar.Q16_16) : Bool :=
  PhysicsScalar.Q16_16.le delayMass profile.causalSupport.maximumDelayMass


def compatibleWithBoundary (profile : SubstrateProfile) (boundary : BoundaryLayer) (kind : BoundaryKind) : Bool :=
  supportsBoundaryKind profile kind &&
  supportsFluidity profile boundary.fluidity &&
  PhysicsScalar.Q16_16.ge boundary.coherence profile.boundarySupport.minimumCoherence &&
  (profile.boundarySupport.supportsDiffuseBoundaries || kind != BoundaryKind.sheath) &&
  (profile.boundarySupport.supportsTurbulentBoundaries || !PhysicsScalar.Q16_16.gt boundary.fluidity PhysicsScalar.Q16_16.half)


def compatibleWithSample (profile : SubstrateProfile) (sample : ElectromagneticSample) (ic : InteractionClass) : Bool :=
  supportsBand profile sample.bandProfile.band &&
  match ic with
  | .communication => profile.spectralSupport.supportsCommunication
  | .passiveSensing => profile.spectralSupport.supportsPassiveSensing
  | .activeSensing => profile.spectralSupport.supportsActiveProbe
  | .imaging => profile.spectralSupport.supportsPassiveSensing || profile.spectralSupport.supportsActiveProbe
  | .illumination => true
  | .heating => true
  | .ionizingExposure => PhysicsScalar.Q16_16.gt profile.spectralSupport.ionizingTolerance PhysicsScalar.Q16_16.quarter
  | .plasmaCoupling => true


def compatibleWithLink (profile : SubstrateProfile) (link : CausalLink) : Bool :=
  supportsOrientation profile link.orientation &&
  supportsDelayMass profile link.delay &&
  (profile.causalSupport.supportsDelayedLinks || !PhysicsScalar.Q16_16.gt link.delay PhysicsScalar.Q16_16.zero) &&
  (profile.causalSupport.supportsFoldedLinks || link.orientation != CausalOrientation.folded) &&
  (profile.causalSupport.supportsCyclicTraversal || link.orientation != CausalOrientation.cyclic) &&
  (!profile.causalSupport.requiresGuardedTraversal || link.requiresGate)


def compatibleWithRegionAssignment (profile : SubstrateProfile) (assignment : RegionAssignment) : Bool :=
  !profile.supportsResolvedOnly || assignment.state.resolutionStatus = .resolved


def substrateAdmitsTransition
  (profile : SubstrateProfile)
  (assignment : RegionAssignment)
  (sample? : Option (ElectromagneticSample × InteractionClass))
  (boundary? : Option (BoundaryLayer × BoundaryKind))
  (link? : Option CausalLink)
  (stateDim transportDim topologyDim renderDim : Nat)
  : Bool :=
  compatibleWithRegionAssignment profile assignment &&
  supportsDimensions profile stateDim transportDim topologyDim renderDim &&
  match sample?, boundary?, link? with
  | some (sample, ic), some (boundary, bk), some link =>
      compatibleWithSample profile sample ic &&
      compatibleWithBoundary profile boundary bk &&
      compatibleWithLink profile link
  | some (sample, ic), some (boundary, bk), none =>
      compatibleWithSample profile sample ic &&
      compatibleWithBoundary profile boundary bk
  | some (sample, ic), none, some link =>
      compatibleWithSample profile sample ic &&
      compatibleWithLink profile link
  | none, some (boundary, bk), some link =>
      compatibleWithBoundary profile boundary bk &&
      compatibleWithLink profile link
  | some (sample, ic), none, none => compatibleWithSample profile sample ic
  | none, some (boundary, bk), none => compatibleWithBoundary profile boundary bk
  | none, none, some link => compatibleWithLink profile link
  | none, none, none => true


def fpgaSpectralSupport : SpectralSupport :=
  { supportedBands := [SpectrumBand.radio, SpectrumBand.microwave, SpectrumBand.infrared, SpectrumBand.optical]
  , lineOfSightPreferred := false
  , supportsActiveProbe := true
  , supportsPassiveSensing := true
  , supportsCommunication := true
  , ionizingTolerance := PhysicsScalar.Q16_16.quarter }


def fpgaBoundarySupport : BoundarySupport :=
  { supportedKinds :=
      [ BoundaryKind.interface
      , BoundaryKind.sheath
      , BoundaryKind.throat
      , BoundaryKind.spectralCurtain
      , BoundaryKind.reconnectionSurface
      , BoundaryKind.dimensionalSeam ]
  , supportsDiffuseBoundaries := true
  , supportsTurbulentBoundaries := false
  , maximumFluidity := PhysicsScalar.Q16_16.three
  , minimumCoherence := PhysicsScalar.Q16_16.quarter }


def fpgaCausalSupport : CausalSupport :=
  { supportedOrientations := [CausalOrientation.forward, CausalOrientation.lateral, CausalOrientation.folded]
  , supportsDelayedLinks := true
  , supportsFoldedLinks := true
  , supportsCyclicTraversal := false
  , requiresGuardedTraversal := true
  , maximumDelayMass := PhysicsScalar.Q16_16.four }


def fpgaSubstrateProfile : SubstrateProfile :=
  { substrateId := UInt16.ofNat 1
  , label := "fpga-default"
  , kind := SubstrateKind.fpga
  , timingResolution := TimingResolution.tick
  , executionStyle := ExecutionStyle.reconfigurable
  , resourceEnvelope :=
      { maxStateDim := 8
      , maxTransportDim := 8
      , maxTopologyDim := 8
      , maxRenderDim := 4
      , channelBudget := UInt16.ofNat 4096
      , nodeBudget := UInt16.ofNat 4096
      , linkBudget := UInt16.ofNat 8192 }
  , supportsResolvedOnly := true
  , spectralSupport := fpgaSpectralSupport
  , boundarySupport := fpgaBoundarySupport
  , causalSupport := fpgaCausalSupport }


def softwareResearchSubstrateProfile : SubstrateProfile :=
  { substrateId := UInt16.ofNat 2
  , label := "software-research"
  , kind := SubstrateKind.software
  , timingResolution := TimingResolution.phaseAware
  , executionStyle := ExecutionStyle.hybrid
  , resourceEnvelope :=
      { maxStateDim := 32
      , maxTransportDim := 32
      , maxTopologyDim := 32
      , maxRenderDim := 8
      , channelBudget := UInt16.ofNat 65535
      , nodeBudget := UInt16.ofNat 65535
      , linkBudget := UInt16.ofNat 65535 }
  , supportsResolvedOnly := false
  , spectralSupport :=
      { supportedBands := [SpectrumBand.radio, SpectrumBand.microwave, SpectrumBand.infrared, SpectrumBand.optical, SpectrumBand.ultraviolet, SpectrumBand.xray, SpectrumBand.gamma]
      , lineOfSightPreferred := false
      , supportsActiveProbe := true
      , supportsPassiveSensing := true
      , supportsCommunication := true
      , ionizingTolerance := PhysicsScalar.Q16_16.four }
  , boundarySupport :=
      { supportedKinds :=
          [ BoundaryKind.interface
          , BoundaryKind.sheath
          , BoundaryKind.throat
          , BoundaryKind.spectralCurtain
          , BoundaryKind.reconnectionSurface
          , BoundaryKind.dimensionalSeam ]
      , supportsDiffuseBoundaries := true
      , supportsTurbulentBoundaries := true
      , maximumFluidity := PhysicsScalar.Q16_16.four
      , minimumCoherence := PhysicsScalar.Q16_16.zero }
  , causalSupport :=
      { supportedOrientations :=
          [ CausalOrientation.forward
          , CausalOrientation.backward
          , CausalOrientation.lateral
          , CausalOrientation.cyclic
          , CausalOrientation.folded ]
      , supportsDelayedLinks := true
      , supportsFoldedLinks := true
      , supportsCyclicTraversal := true
      , requiresGuardedTraversal := false
      , maximumDelayMass := PhysicsScalar.Q16_16.maxValue } }

end Semantics.SubstrateProfile
