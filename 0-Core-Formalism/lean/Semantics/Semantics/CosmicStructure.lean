import Semantics.PhysicsScalarBridge
import Semantics.RegimeCore
import Semantics.ElectromagneticSpectrum
import Semantics.BoundaryDynamics
import Semantics.CriticalityDynamics
import Semantics.MagnetoPlasma
import Semantics.MultiBodyField
import Semantics.FixedPoint
import Semantics.ManifoldStructures

namespace Semantics.CosmicStructure


open Semantics.RegimeCore
open Semantics.ElectromagneticSpectrum
open Semantics.BoundaryDynamics
open Semantics.CriticalityDynamics
open Semantics.MagnetoPlasma
open Semantics.MultiBodyField
open Semantics.ManifoldStructures

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
  deriving DecidableEq

inductive CosmicMorphology
| cloud
| tendril
| sheath
| loop
| web
| shell
| coreHalo
  deriving DecidableEq

inductive CosmicStability
| csStable
| csMetastable
| csUnstable
| csEruptive
| csCollapsed
  deriving DecidableEq

structure CosmicZone where
  zoneId : CosmicZoneId
  label : String
  assignment : RegionAssignment
  flavor : CosmicFlavor
  morphology : CosmicMorphology
  baseDensity : PhysicsScalar.Q16_16
  baseTemperature : PhysicsScalar.Q16_16
  deriving DecidableEq

structure CosmicSignature where
  bodyCount : UInt16
  boundaryFluidity : PhysicsScalar.Q16_16
  criticality : PhysicsScalar.Q16_16
  spectralCoherence : PhysicsScalar.Q16_16
  magnetoAlignment : PhysicsScalar.Q16_16
  densityContrast : PhysicsScalar.Q16_16
  emissionStrength : PhysicsScalar.Q16_16
  deriving DecidableEq

structure CosmicStructure (n : Nat) where
  structureId : CosmicStructureId
  label : String
  assembly : MultiBodyAssembly n
  zones : List CosmicZone
  sample? : Option ElectromagneticSample

structure CosmicTransitionRequest (n : Nat) where
  cosmicStructure : CosmicStructure n
  injectedSample? : Option ElectromagneticSample
  preferReconnection : Bool
  preferCriticalRedistribution : Bool

structure CosmicTransitionResult (n : Nat) where
  cosmicStructure : CosmicStructure n
  signature : CosmicSignature
  stability : CosmicStability
  admitted : Bool


def zoneBoundaryFluidity
  (assembly : MultiBodyAssembly n)
  (zone : CosmicZone) : PhysicsScalar.Q16_16 :=
  let zId := zone.assignment.regionId
  let matching := assembly.boundaries.toList.filter (fun (b : BoundaryLayer) => b.sourceRegionId = zId || b.targetRegionId = zId)
  let fluiditySum := matching.foldl (fun acc (b : BoundaryLayer) => PhysicsScalarBridge.addSaturating acc b.fluidity) PhysicsScalarBridge.zero
  if matching.isEmpty then PhysicsScalarBridge.zero else PhysicsScalarBridge.divQ16_16 fluiditySum (UInt32.ofNat matching.length)


def zoneDensityContrast (zone : CosmicZone) : PhysicsScalar.Q16_16 :=
  PhysicsScalarBridge.absDiff zone.baseDensity zone.baseTemperature


def zoneEmissionStrength
  (zone : CosmicZone)
  (sample? : Option ElectromagneticSample) : PhysicsScalar.Q16_16 :=
  let sampleStrength :=
    match sample? with
    | none => PhysicsScalarBridge.zero
    | some sample => sample.bandProfile.intensity
  PhysicsScalarBridge.mean3 zone.baseDensity zone.baseTemperature sampleStrength


def cosmicSignatureOf
  (s : CosmicStructure n) : CosmicSignature :=
  let assemblySignature := multiBodySignatureOf s.assembly s.sample?
  let bodyCount := assemblySignature.bodyCount
  let zoneCount := s.zones.length
  let fluiditySum := s.zones.foldl (fun acc zone => PhysicsScalarBridge.addSaturating acc (zoneBoundaryFluidity s.assembly zone)) PhysicsScalarBridge.zero
  let densitySum := s.zones.foldl (fun acc zone => PhysicsScalarBridge.addSaturating acc (zoneDensityContrast zone)) PhysicsScalarBridge.zero
  let emissionSum := s.zones.foldl (fun acc zone => PhysicsScalarBridge.addSaturating acc (zoneEmissionStrength zone s.sample?)) PhysicsScalarBridge.zero
  let zoneDiv := if zoneCount = 0 then 1 else zoneCount
  { bodyCount := bodyCount
  , boundaryFluidity := PhysicsScalarBridge.divQ16_16 fluiditySum (UInt32.ofNat zoneDiv)
  , criticality := assemblySignature.criticalPressure
  , spectralCoherence := assemblySignature.spectralCoherence
  , magnetoAlignment := assemblySignature.magnetoAlignment
  , densityContrast := PhysicsScalarBridge.divQ16_16 densitySum (UInt32.ofNat zoneDiv)
  , emissionStrength := PhysicsScalarBridge.divQ16_16 emissionSum (UInt32.ofNat zoneDiv) }


def classifyCosmicStability (signature : CosmicSignature) : CosmicStability :=
  if PhysicsScalarBridge.ge signature.criticality PhysicsScalarBridge.one then
    .csCollapsed
  else if PhysicsScalarBridge.ge signature.criticality (PhysicsScalarBridge.add PhysicsScalarBridge.half PhysicsScalarBridge.quarter) && PhysicsScalarBridge.ge signature.boundaryFluidity PhysicsScalarBridge.half then
    .csEruptive
  else if PhysicsScalarBridge.ge signature.criticality PhysicsScalarBridge.half then
    .csUnstable
  else if PhysicsScalarBridge.ge signature.magnetoAlignment PhysicsScalarBridge.half && PhysicsScalarBridge.ge signature.spectralCoherence PhysicsScalarBridge.quarter then
    .csStable
  else
    .csMetastable


def processCosmicTransition
  (request : CosmicTransitionRequest n) : CosmicTransitionResult n :=
  let s := request.cosmicStructure
  let sample? := match request.injectedSample? with | some sj => some sj | none => s.sample?
  let updatedStructure := { s with sample? := sample? }
  let signature := cosmicSignatureOf updatedStructure
  let stability := classifyCosmicStability signature
  let admitted :=
    match updatedStructure.zones.head? with
    | none => true
    | some zone =>
        match zone.flavor with
        | .criticalLattice => request.preferCriticalRedistribution || PhysicsScalarBridge.ge signature.criticality PhysicsScalarBridge.quarter
        | .boundaryWeb => request.preferReconnection || PhysicsScalarBridge.ge signature.boundaryFluidity PhysicsScalarBridge.quarter
        | _ => true
  { cosmicStructure := updatedStructure
  , signature := signature
  , stability := stability
  , admitted := admitted }


def defaultHaloZone (assignment : RegionAssignment) : CosmicZone :=
  { zoneId := 1
  , label := "defaultHaloZone"
  , assignment := assignment
  , flavor := .diffuseHalo
  , morphology := .coreHalo
  , baseDensity := PhysicsScalarBridge.half
  , baseTemperature := PhysicsScalarBridge.half }


def defaultCosmicStructure (assembly : MultiBodyAssembly n) (assignment : RegionAssignment) : CosmicStructure n :=
  { structureId := 1
  , label := "defaultCosmicStructure"
  , assembly := assembly
  , zones := [defaultHaloZone assignment]
  , sample? := none }

end Semantics.CosmicStructure
