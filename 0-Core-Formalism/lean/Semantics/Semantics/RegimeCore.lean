/-
  RegimeCore.lean - Minimal stub for Type-Safe Manifold Assignments
-/

import Semantics.DomainState
import Semantics.ElectromagneticSpectrum

namespace Semantics.RegimeCore

open Semantics.DomainState
open Semantics.ElectromagneticSpectrum

abbrev RegionId := Nat

inductive RegimeClass
| coherent
| transitional
| throat
| constrained
| blocked
| resolved
| collapseProne
  deriving Repr, DecidableEq

structure RegionAssignment where
  regionId : RegionId
  state : DomainState
  regimeClass : RegimeClass
  deriving Repr, DecidableEq

def classifyAssignment
  (regionId : RegionId)
  (state : DomainState)
  (sample? : Option ElectromagneticSample) : RegionAssignment :=
  let rc := match state.resolutionStatus, sample? with
  | .pending, _ => .constrained
  | .rejected, _ => .blocked
  | .resolved, some sample =>
      if isIonizingBand sample.bandProfile.band then
        .collapseProne
      else if sample.interaction = .plasmaCoupling then
        .throat
      else
        .resolved
  | .resolved, none =>
      match state.stabilityClass with
      | .stable => .coherent
      | .throat => .throat
      | .unstable => .transitional
      | .collapse => .collapseProne
  { regionId := regionId, state := state, regimeClass := rc }

end Semantics.RegimeCore
