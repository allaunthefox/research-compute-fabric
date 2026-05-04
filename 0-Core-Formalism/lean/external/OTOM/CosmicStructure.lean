import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.ElectromagneticSpectrum
import Semantics.BoundaryDynamics
import Semantics.CriticalityDynamics
import Semantics.MagnetoPlasma
import Semantics.MultiBodyField

namespace Semantics.CosmicStructure

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.ElectromagneticSpectrum
open Semantics.BoundaryDynamics
open Semantics.CriticalityDynamics
open Semantics.MagnetoPlasma
open Semantics.MultiBodyField

abbrev CosmicStructureId := UInt16
abbrev CosmicZoneId := UInt16

inductive CosmicFlavor
| diffuseHalo
| filamentNetwork
| clusterMedium
| magnetizedAssembly
| radiativeShell
| criticalLattice
| boundaryWeb
  deriving Repr, DecidableEq

inductive CosmicCoherence
| sparse
| coherent
| braided
| turbulent
| collapseProne
  deriving Repr, DecidableEq

inductive CosmicMorphology
| cloud
| tendril
| sheath
| loop
| web
| shell
| coreHalo
  deriving Repr, DecidableEq

inductive CosmicEmissionRegime
| dark
| faint
| luminous
| lineDominant
| broadband
| ionizing
  deriving Repr, DecidableEq

inductive CosmicStability
| stable
| metastable
| unstable
| eruptive
| collapsed
  deriving Repr, DecidableEq

structure CosmicZone where
  zoneId : CosmicZoneId
  label : String
  assignment : RegionAssignment
  flavor : CosmicFlavor
  morphology : CosmicMorphology
  baseDensity : Q16_16
  baseTemperature : Q16_16
  spectralProfile : RegionSpectralProfile
  deriving Repr

structure CosmicSignature where
  bodyCount : UInt16
  boundaryFluidity : Q16_16
  criticality : Q16_16
  spectralCoherence : Q16_16
  magnetoAlignment : Q16_16
  densityContrast : Q16_16
  emissionStrength : Q16_16
  deriving Repr, DecidableEq

structure CosmicStructure (n : Nat) where
  structureId : CosmicStructureId
  label : String
  assembly : MultiBodyAssembly n
  zones : List CosmicZone
  sample? : Option ElectromagneticSample
  deriving Repr

structure CosmicTransitionRequest (n : Nat) where
  structure : CosmicStructure n
  injectedSample? : Option ElectromagneticSample
  preferReconnection : Bool
  preferCriticalRedistribution : Bool
  deriving Repr

structure CosmicTransitionResult (n : Nat) where
  structure : CosmicStructure n
  signature : CosmicSignature
  coherence : CosmicCoherence
  emission : CosmicEmissionRegime
  stability : CosmicStability
  admitted : Bool
  deriving Repr


def zoneBoundaryFluidity
  (assembly : MultiBodyAssembly n)
  (zone : CosmicZone) : Q16_16 :=
  let matching := assembly.boundaries.filter (fun boundary => boundary.leftRegion = zone.assignment.regionId || boundary.rightRegion = zone.assignment.regionId)
  let fluiditySum := matching.foldl (fun acc boundary => addSaturating acc boundary.fluidity) zero
  if matching.isEmpty then zero else divQ16_16 fluiditySum (UInt32.ofNat matching.length)


def zoneDensityContrast (zone : CosmicZone) : Q16_16 :=
  absDiff zone.baseDensity zone.baseTemperature


def zoneEmissionStrength
  (zone : CosmicZone)
  (sample? : Option ElectromagneticSample) : Q16_16 :=
  let sampleStrength :=
    match sample? with
    | none => zero
    | some sample => if interactionAllowed zone.spectralProfile sample then sample.intensity else zero
  mean3 zone.baseDensity zone.baseTemperature sampleStrength


def cosmicSignatureOf
  (structure : CosmicStructure n) : CosmicSignature :=
  let assemblySignature := multiBodySignatureOf structure.assembly structure.sample?
  let bodyCount := assemblySignature.bodyCount
  let zoneCount := structure.zones.length
  let fluiditySum := structure.zones.foldl (fun acc zone => addSaturating acc (zoneBoundaryFluidity structure.assembly zone)) zero
  let densitySum := structure.zones.foldl (fun acc zone => addSaturating acc (zoneDensityContrast zone)) zero
  let emissionSum := structure.zones.foldl (fun acc zone => addSaturating acc (zoneEmissionStrength zone structure.sample?)) zero
  let zoneDiv := if zoneCount = 0 then 1 else zoneCount
  { bodyCount := bodyCount
  , boundaryFluidity := divQ16_16 fluiditySum (UInt32.ofNat zoneDiv)
  , criticality := assemblySignature.criticalPressure
  , spectralCoherence := assemblySignature.spectralCoherence
  , magnetoAlignment := assemblySignature.magnetoAlignment
  , densityContrast := divQ16_16 densitySum (UInt32.ofNat zoneDiv)
  , emissionStrength := divQ16_16 emissionSum (UInt32.ofNat zoneDiv) }


def classifyCosmicCoherence (signature : CosmicSignature) : CosmicCoherence :=
  if ge signature.criticality one then
    .collapseProne
  else if ge signature.boundaryFluidity (add half quarter) && ge signature.magnetoAlignment half then
    .braided
  else if ge signature.boundaryFluidity (add half quarter) then
    .turbulent
  else if ge signature.spectralCoherence half then
    .coherent
  else
    .sparse


def classifyEmissionRegime (signature : CosmicSignature) : CosmicEmissionRegime :=
  if ge signature.emissionStrength one then
    .ionizing
  else if ge signature.spectralCoherence (add half quarter) && ge signature.emissionStrength half then
    .lineDominant
  else if ge signature.emissionStrength (add half quarter) then
    .broadband
  else if ge signature.emissionStrength half then
    .luminous
  else if ge signature.emissionStrength quarter then
    .faint
  else
    .dark


def classifyCosmicStability (signature : CosmicSignature) : CosmicStability :=
  if ge signature.criticality one then
    .collapsed
  else if ge signature.criticality (add half quarter) && ge signature.boundaryFluidity half then
    .eruptive
  else if ge signature.criticality half then
    .unstable
  else if ge signature.magnetoAlignment half && ge signature.spectralCoherence quarter then
    .stable
  else
    .metastable


def classifyFlavorBias (structure : CosmicStructure n) : CosmicFlavor :=
  match structure.zones.head? with
  | none => .diffuseHalo
  | some zone => zone.flavor


def transitionSample
  (request : CosmicTransitionRequest n) : Option ElectromagneticSample :=
  match request.injectedSample? with
  | some sample => some sample
  | none => request.structure.sample?


def applyInjectedSample
  (structure : CosmicStructure n)
  (sample? : Option ElectromagneticSample) : CosmicStructure n :=
  { structure with sample? := sample? }


def processCosmicTransition
  (request : CosmicTransitionRequest n) : CosmicTransitionResult n :=
  let updatedStructure := applyInjectedSample request.structure (transitionSample request)
  let signature := cosmicSignatureOf updatedStructure
  let coherence := classifyCosmicCoherence signature
  let emission := classifyEmissionRegime signature
  let stability := classifyCosmicStability signature
  let admitted :=
    match classifyFlavorBias updatedStructure with
    | .criticalLattice => request.preferCriticalRedistribution || ge signature.criticality quarter
    | .boundaryWeb => request.preferReconnection || ge signature.boundaryFluidity quarter
    | _ => true
  { structure := updatedStructure
  , signature := signature
  , coherence := coherence
  , emission := emission
  , stability := stability
  , admitted := admitted }


def defaultHaloZone (assignment : RegionAssignment) : CosmicZone :=
  { zoneId := 1
  , label := "defaultHaloZone"
  , assignment := assignment
  , flavor := .diffuseHalo
  , morphology := .coreHalo
  , baseDensity := half
  , baseTemperature := half
  , spectralProfile := defaultOpticalRegion }


def defaultCosmicStructure (assembly : MultiBodyAssembly n) (assignment : RegionAssignment) : CosmicStructure n :=
  { structureId := 1
  , label := "defaultCosmicStructure"
  , assembly := assembly
  , zones := [defaultHaloZone assignment]
  , sample? := some visibleLightSample }

end Semantics.CosmicStructure
