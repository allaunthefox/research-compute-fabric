import Semantics.PhysicsScalar
import Semantics.RegimeCore
import Semantics.BoundaryDynamics
import Semantics.SpikingDynamics
import Semantics.ExoticSpacetime

namespace Semantics.CriticalityDynamics

open Semantics.PhysicsScalar
open Semantics.RegimeCore
open Semantics.BoundaryDynamics
open Semantics.SpikingDynamics
open Semantics.ExoticSpacetime

abbrev CriticalSiteId := UInt16
abbrev AvalancheId := UInt16
abbrev ToppleCount := UInt16

inductive PotentialRegime
| subcritical
| nearCritical
| critical
| supercritical
| dissipative
  deriving Repr, DecidableEq

inductive AvalancheClass
| none
| local
| cascading
| systemWide
| recurrent
  deriving Repr, DecidableEq

inductive StabilizationStatus
| stable
| unstable
| stabilizing
| dissipated
| unresolved
  deriving Repr, DecidableEq

structure CriticalPotential where
  load : Q16_16
  threshold : Q16_16
  gradient : Q16_16
  dissipation : Q16_16
  manifoldBias : Q16_16
  deriving Repr, DecidableEq

structure CriticalSite where
  siteId : CriticalSiteId
  label : String
  regionId : RegionId
  load : Q16_16
  threshold : Q16_16
  capacity : UInt16
  sink : Bool
  manifoldWeight : Q16_16
  temporalDifferential? : Option TemporalDifferential
  boundaryId? : Option BoundaryId
  deriving Repr, DecidableEq

structure RedistributionEdge where
  sourceId : CriticalSiteId
  targetId : CriticalSiteId
  weight : Q16_16
  gated : Bool
  boundaryInfluence : Q16_16
  deriving Repr, DecidableEq

structure CriticalNetwork where
  sites : List CriticalSite
  edges : List RedistributionEdge
  defaultDissipation : Q16_16
  deriving Repr, DecidableEq

structure ToppleStep where
  siteId : CriticalSiteId
  outgoingCount : UInt16
  emittedLoad : Q16_16
  remainingLoad : Q16_16
  avalancheClass : AvalancheClass
  deriving Repr, DecidableEq

structure Avalanche where
  avalancheId : AvalancheId
  seedSiteId : CriticalSiteId
  steps : List ToppleStep
  dischargedLoad : Q16_16
  span : UInt16
  class : AvalancheClass
  deriving Repr, DecidableEq

structure StabilizationResult where
  network : CriticalNetwork
  avalanches : List Avalanche
  status : StabilizationStatus
  totalDischargedLoad : Q16_16
  deriving Repr, DecidableEq


def potentialOf (site : CriticalSite) : CriticalPotential :=
  { load := site.load
  , threshold := site.threshold
  , gradient := absDiff site.load site.threshold
  , dissipation := if site.sink then one else quarter
  , manifoldBias := site.manifoldWeight }


def classifyPotentialRegime (potential : CriticalPotential) : PotentialRegime :=
  if le potential.load (subSaturating potential.threshold quarter) then
    PotentialRegime.subcritical
  else if lt potential.load potential.threshold then
    PotentialRegime.nearCritical
  else if eq potential.load potential.threshold then
    PotentialRegime.critical
  else if gt potential.load (addSaturating potential.threshold half) then
    PotentialRegime.supercritical
  else
    PotentialRegime.dissipative


def siteUnstable (site : CriticalSite) : Bool :=
  ge site.load site.threshold


def edgeActive (edge : RedistributionEdge) : Bool :=
  edge.gated && nonZero edge.weight


def siteEdges (network : CriticalNetwork) (siteId : CriticalSiteId) : List RedistributionEdge :=
  network.edges.filter (fun edge => edge.sourceId = siteId && edgeActive edge)


def activeNeighborCount (network : CriticalNetwork) (siteId : CriticalSiteId) : UInt16 :=
  UInt16.ofNat (siteEdges network siteId |>.length)


def redistributedLoadPerEdge (site : CriticalSite) (network : CriticalNetwork) : Q16_16 :=
  let count := activeNeighborCount network site.siteId
  if count = 0 then zero else divQ16_16 site.threshold (UInt32.ofNat count.toNat)


def toppledLoad (site : CriticalSite) : Q16_16 :=
  if site.sink then site.load else site.threshold


def remainingAfterTopple (site : CriticalSite) : Q16_16 :=
  if site.sink then zero else subSaturating site.load (toppledLoad site)


def classifyAvalancheClass (toppleCount : ToppleCount) (span : UInt16) : AvalancheClass :=
  if toppleCount = 0 then AvalancheClass.none
  else if toppleCount = 1 then AvalancheClass.local
  else if toppleCount <= 4 then AvalancheClass.cascading
  else if span <= 2 then AvalancheClass.recurrent
  else AvalancheClass.systemWide


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


def receiveLoad (site : CriticalSite) (incoming : Q16_16) : CriticalSite :=
  { site with load := addSaturating site.load incoming }


def edgeContribution (source : CriticalSite) (network : CriticalNetwork) (edge : RedistributionEdge) : Q16_16 :=
  let base := redistributedLoadPerEdge source network
  let boundaryAdjusted := mulQ16_16 base (subSaturating one edge.boundaryInfluence)
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


def boundaryFluidityForSite (site : CriticalSite) (boundary? : Option BoundaryLayer) : BoundaryFluidity :=
  match boundary? with
  | none => BoundaryFluidity.rigid
  | some boundary => classifyBoundaryFluidity boundary.fluidity


def temporalPotentialBias (site : CriticalSite) : Q16_16 :=
  match site.temporalDifferential? with
  | none => zero
  | some differential => temporalGradient differential


def manifoldPotentialOf (site : CriticalSite) : Q16_16 :=
  addSaturating site.manifoldWeight (temporalPotentialBias site)


def stabilizeStep (network : CriticalNetwork) : StabilizationResult :=
  match firstUnstableSite? network with
  | none =>
      { network := network
      , avalanches := []
      , status := StabilizationStatus.stable
      , totalDischargedLoad := zero }
  | some unstableSite =>
      let step := toppleStepOf unstableSite network
      let nextNetwork := distributeFromSite network unstableSite
      let avalanche : Avalanche :=
        { avalancheId := unstableSite.siteId
        , seedSiteId := unstableSite.siteId
        , steps := [step]
        , dischargedLoad := step.emittedLoad
        , span := step.outgoingCount
        , class := step.avalancheClass }
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
      , totalDischargedLoad := zero }
  | fuel + 1 =>
      let stepResult := stabilizeStep network
      match stepResult.status with
      | StabilizationStatus.stable => stepResult
      | _ =>
          let recursive := stableByRepeatedTopple fuel stepResult.network
          { network := recursive.network
          , avalanches := stepResult.avalanches ++ recursive.avalanches
          , status := recursive.status
          , totalDischargedLoad := addSaturating stepResult.totalDischargedLoad recursive.totalDischargedLoad }


def abelianInvariantHoldsByLoadSum (before after : CriticalNetwork) : Bool :=
  let sumLoads := fun (sites : List CriticalSite) => sites.foldl (fun acc site => addSaturating acc site.load) zero
  le (sumLoads after.sites) (sumLoads before.sites)


def sinkSites (network : CriticalNetwork) : List CriticalSite :=
  network.sites.filter (fun site => site.sink)


def criticalFrontier (network : CriticalNetwork) : List CriticalSite :=
  network.sites.filter (fun site => classifyPotentialRegime (potentialOf site) = PotentialRegime.nearCritical)


def manifoldCriticalityScore (site : CriticalSite) : Q16_16 :=
  addSaturating (manifoldPotentialOf site) (absDiff site.load site.threshold)


def criticalityCompatibleWithSpike (site : CriticalSite) (state : MembraneState) : Bool :=
  ge site.load state.threshold || ge (manifoldCriticalityScore site) state.potential


def defaultCriticalSite (siteId : CriticalSiteId) (regionId : RegionId) : CriticalSite :=
  { siteId := siteId
  , label := "critical-site"
  , regionId := regionId
  , load := zero
  , threshold := one
  , capacity := 4
  , sink := false
  , manifoldWeight := quarter
  , temporalDifferential? := none
  , boundaryId? := none }


def defaultCriticalNetwork : CriticalNetwork :=
  { sites := []
  , edges := []
  , defaultDissipation := quarter }

end Semantics.CriticalityDynamics
