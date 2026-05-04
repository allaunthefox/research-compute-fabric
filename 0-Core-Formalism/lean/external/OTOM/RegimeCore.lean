/-
  RegimeCore.lean - Minimal stub for PhysicsOrchestrator dependency
-/

import Semantics.DomainState
import Semantics.ElectromagneticSpectrum

namespace Semantics.RegimeCore

open Semantics.DomainState
open Semantics.ElectromagneticSpectrum

inductive RegimeClass
| coherent
| transitional
| throat
| constrained
| blocked
| resolved
| collapseProne
  deriving Repr, DecidableEq

def classifyAssignment
  (state : DomainState)
  (sample? : Option ElectromagneticSample) : RegimeClass :=
  match state.resolutionStatus, sample? with
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

end Semantics.RegimeCore
