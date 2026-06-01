import Semantics.PhysicsScalarBridge
import Semantics.RegimeCore
import Semantics.BoundaryDynamics
import Semantics.SpikingDynamics
import Semantics.ExoticSpacetime
import Semantics.ManifoldStructures

namespace Semantics.CriticalityDynamics

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.BoundaryDynamics
open Semantics.SpikingDynamics
open Semantics.ExoticSpacetime
open Semantics.ManifoldStructures

abbrev CriticalSiteId := UInt16
abbrev AvalancheId := UInt16
abbrev ToppleCount := UInt16

inductive PotentialRegime
| subcritical
| nearCritical
| critical
| supercritical
| dissipative
  deriving DecidableEq

inductive ManifoldAvalancheClass
| acNone
| acLocal
| acCascading
| acSystemWide
| acRecurrent
  deriving DecidableEq

inductive StabilizationStatus
| stable
| unstable
| stabilizing
| dissipated
| unresolved
  deriving DecidableEq

structure CriticalPotential where
  load : PhysicsScalar.Q16_16
  threshold : PhysicsScalar.Q16_16
  gradient : PhysicsScalar.Q16_16
  dissipation : PhysicsScalar.Q16_16
  manifoldBias : PhysicsScalar.Q16_16
  deriving DecidableEq

structure CriticalSite where
  siteId : CriticalSiteId
  label : String
  regionId : RegionId
  load : PhysicsScalar.Q16_16
  threshold : PhysicsScalar.Q16_16
  capacity : UInt16
  sink : Bool
  manifoldWeight : PhysicsScalar.Q16_16
  temporalDifferential? : Option TemporalDifferential
  boundaryId? : Option BoundaryId
  deriving DecidableEq

structure RedistributionEdge where
  sourceId : CriticalSiteId
  targetId : CriticalSiteId
  weight : PhysicsScalar.Q16_16
  gated : Bool
  boundaryInfluence : PhysicsScalar.Q16_16
  deriving DecidableEq

structure CriticalNetwork where
  sites : List CriticalSite
  edges : List RedistributionEdge
  defaultDissipation : PhysicsScalar.Q16_16
  deriving DecidableEq

structure ToppleStep where
  siteId : CriticalSiteId
  outgoingCount : UInt16
  emittedLoad : PhysicsScalar.Q16_16
  remainingLoad : PhysicsScalar.Q16_16
  avalancheClass : ManifoldAvalancheClass
  deriving DecidableEq

structure Avalanche where
  avalancheId : AvalancheId
  seedSiteId : CriticalSiteId
  steps : List ToppleStep
  dischargedLoad : PhysicsScalar.Q16_16
  span : UInt16
  avalancheClass : ManifoldAvalancheClass
  deriving DecidableEq

structure StabilizationResult where
  network : CriticalNetwork
  avalanches : List Avalanche
  status : StabilizationStatus
  totalDischargedLoad : PhysicsScalar.Q16_16
  deriving DecidableEq


def potentialOf (site : CriticalSite) : CriticalPotential :=
  { load := site.load
  , threshold := site.threshold
  , gradient := PhysicsScalarBridge.absDiff site.load site.threshold
  , dissipation := if site.sink then PhysicsScalarBridge.one else PhysicsScalarBridge.quarter
  , manifoldBias := site.manifoldWeight }


def classifyPotentialRegime (potential : CriticalPotential) : PotentialRegime :=
  if PhysicsScalarBridge.le potential.load (PhysicsScalarBridge.subSaturating potential.threshold PhysicsScalarBridge.quarter) then
    PotentialRegime.subcritical
  else if PhysicsScalarBridge.lt potential.load potential.threshold then
    PotentialRegime.nearCritical
  else if PhysicsScalarBridge.eq potential.load potential.threshold then
    PotentialRegime.critical
  else if PhysicsScalarBridge.gt potential.load (PhysicsScalarBridge.addSaturating potential.threshold PhysicsScalarBridge.half) then
    PotentialRegime.supercritical
  else
    PotentialRegime.dissipative


def siteUnstable (site : CriticalSite) : Bool :=
  PhysicsScalarBridge.ge site.load site.threshold


def edgeActive (edge : RedistributionEdge) : Bool :=
  edge.gated && PhysicsScalarBridge.nonZero edge.weight


def siteEdges (network : CriticalNetwork) (siteId : CriticalSiteId) : List RedistributionEdge :=
  network.edges.filter (fun edge => edge.sourceId = siteId && edgeActive edge)


def activeNeighborCount (network : CriticalNetwork) (siteId : CriticalSiteId) : UInt16 :=
  UInt16.ofNat (siteEdges network siteId |>.length)


def redistributedLoadPerEdge (site : CriticalSite) (network : CriticalNetwork) : PhysicsScalar.Q16_16 :=
  let count := activeNeighborCount network site.siteId
  if count = 0 then PhysicsScalarBridge.zero else PhysicsScalarBridge.divQ16_16 site.threshold (UInt32.ofNat count.toNat)


def toppledLoad (site : CriticalSite) : PhysicsScalar.Q16_16 :=
  if site.sink then site.load else site.threshold


def remainingAfterTopple (site : CriticalSite) : PhysicsScalar.Q16_16 :=
  if site.sink then PhysicsScalarBridge.zero else PhysicsScalarBridge.subSaturating site.load (toppledLoad site)


def classifyAvalancheClass (toppleCount : ToppleCount) (span : UInt16) : ManifoldAvalancheClass :=
  if toppleCount = 0 then .acNone
  else if toppleCount = 1 then .acLocal
  else if toppleCount <= 4 then .acCascading
  else if span <= 2 then .acRecurrent
  else .acSystemWide


def toppleStepOf (site : CriticalSite) (network : CriticalNetwork) : ToppleStep :=
  let count := activeNeighborCount network site.siteId
  let remaining := remainingAfterTopple site
  { siteId := site.siteId
  , outgoingCount := count
  , emittedLoad := toppledLoad site
  , remainingLoad := remaining
  , avalancheClass := classifyAvalancheClass 1 (if count = 0 then 0 else 1) }


def applyToppleToSite (site : CriticalSite) : CriticalSite :=
  { site with load := remainingAfterTopple site }


def receiveLoad (site : CriticalSite) (incoming : PhysicsScalar.Q16_16) : CriticalSite :=
  { site with load := PhysicsScalarBridge.addSaturating site.load incoming }


def edgeContribution (source : CriticalSite) (network : CriticalNetwork) (edge : RedistributionEdge) : PhysicsScalar.Q16_16 :=
  let base := redistributedLoadPerEdge source network
  let boundaryAdjusted := PhysicsScalarBridge.mulQ16_16 base (PhysicsScalarBridge.subSaturating PhysicsScalarBridge.one edge.boundaryInfluence)
  boundaryAdjusted


def findSite? (network : CriticalNetwork) (siteId : CriticalSiteId) : Option CriticalSite :=
  network.sites.find? (fun site => site.siteId = siteId)


def rewriteSite (sites : List CriticalSite) (updated : CriticalSite) : List CriticalSite :=
  sites.map (fun site => if site.siteId = updated.siteId then updated else site)


def applyIncomingForEdge (network : CriticalNetwork) (source : CriticalSite) (edge : RedistributionEdge) : CriticalNetwork :=
  match findSite? network edge.targetId with
  | none => network
  | some targetSite =>
      let incoming := edgeContribution source network edge
      let updatedTarget := receiveLoad targetSite incoming
      { network with sites := rewriteSite network.sites updatedTarget }


def distributeFromSite (network : CriticalNetwork) (source : CriticalSite) : CriticalNetwork :=
  let initialNetwork := { network with sites := rewriteSite network.sites (applyToppleToSite source) }
  (siteEdges network source.siteId).foldl (fun acc edge => applyIncomingForEdge acc source edge) initialNetwork


def firstUnstableSite? (network : CriticalNetwork) : Option CriticalSite :=
  network.sites.find? siteUnstable


def temporalPotentialBias (site : CriticalSite) : PhysicsScalar.Q16_16 :=
  match site.temporalDifferential? with
  | none => PhysicsScalarBridge.zero
  | some differential => temporalGradient differential


def manifoldPotentialOf (site : CriticalSite) : PhysicsScalar.Q16_16 :=
  PhysicsScalarBridge.addSaturating site.manifoldWeight (temporalPotentialBias site)


def stabilizeStep (network : CriticalNetwork) : StabilizationResult :=
  match firstUnstableSite? network with
  | none =>
      { network := network
      , avalanches := []
      , status := StabilizationStatus.stable
      , totalDischargedLoad := PhysicsScalarBridge.zero }
  | some unstableSite =>
      let step := toppleStepOf unstableSite network
      let nextNetwork := distributeFromSite network unstableSite
      let avalanche : Avalanche :=
        { avalancheId := unstableSite.siteId
        , seedSiteId := unstableSite.siteId
        , steps := [step]
        , dischargedLoad := step.emittedLoad
        , span := step.outgoingCount
        , avalancheClass := step.avalancheClass }
      { network := nextNetwork
      , avalanches := [avalanche]
      , status := StabilizationStatus.stabilizing
      , totalDischargedLoad := step.emittedLoad }


def stabilizationStatusOf (network : CriticalNetwork) : StabilizationStatus :=
  match firstUnstableSite? network with
  | none => StabilizationStatus.stable
  | some site => if site.sink then StabilizationStatus.dissipated else StabilizationStatus.unstable


def stableByRepeatedTopple (fuel : Nat) (network : CriticalNetwork) : StabilizationResult :=
  match fuel with
  | 0 =>
      { network := network
      , avalanches := []
      , status := StabilizationStatus.unresolved
      , totalDischargedLoad := PhysicsScalarBridge.zero }
  | fuel + 1 =>
      let stepResult := stabilizeStep network
      match stepResult.status with
      | StabilizationStatus.stable => stepResult
      | _ =>
          let recursive := stableByRepeatedTopple fuel stepResult.network
          { network := recursive.network
          , avalanches := stepResult.avalanches ++ recursive.avalanches
          , status := recursive.status
          , totalDischargedLoad := PhysicsScalarBridge.addSaturating stepResult.totalDischargedLoad recursive.totalDischargedLoad }


def abelianInvariantHoldsByLoadSum (before after : CriticalNetwork) : Bool :=
  let sumLoads := fun (sites : List CriticalSite) => sites.foldl (fun acc site => PhysicsScalarBridge.addSaturating acc site.load) PhysicsScalarBridge.zero
  PhysicsScalarBridge.le (sumLoads after.sites) (sumLoads before.sites)


def sinkSites (network : CriticalNetwork) : List CriticalSite :=
  network.sites.filter (fun site => site.sink)


def criticalFrontier (network : CriticalNetwork) : List CriticalSite :=
  network.sites.filter (fun site => classifyPotentialRegime (potentialOf site) = PotentialRegime.nearCritical)


def manifoldCriticalityScore (site : CriticalSite) : PhysicsScalar.Q16_16 :=
  PhysicsScalarBridge.addSaturating (manifoldPotentialOf site) (PhysicsScalarBridge.absDiff site.load site.threshold)


def criticalityCompatibleWithSpike (site : CriticalSite) (state : MembraneState) : Bool :=
  PhysicsScalarBridge.ge site.load state.threshold || PhysicsScalarBridge.ge (manifoldCriticalityScore site) state.potential


def defaultCriticalSite (siteId : CriticalSiteId) (regionId : RegionId) : CriticalSite :=
  { siteId := siteId
  , label := "critical-site"
  , regionId := regionId
  , load := PhysicsScalarBridge.zero
  , threshold := PhysicsScalarBridge.one
  , capacity := 4
  , sink := false
  , manifoldWeight := PhysicsScalarBridge.quarter
  , temporalDifferential? := none
  , boundaryId? := none }


def defaultCriticalNetwork : CriticalNetwork :=
  { sites := []
  , edges := []
  , defaultDissipation := PhysicsScalarBridge.quarter }

end Semantics.CriticalityDynamics
