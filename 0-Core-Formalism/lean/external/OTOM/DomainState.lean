/-
  DomainState.lean - Minimal stub for RegimeCore dependency
-/

namespace Semantics.DomainState

inductive ResolutionStatus
| pending
| resolved
| rejected
  deriving Repr, DecidableEq

inductive StabilityClass
| stable
| throat
| unstable
| collapse
  deriving Repr, DecidableEq

structure DomainState where
  resolutionStatus : ResolutionStatus
  stabilityClass : StabilityClass
  deriving Repr, DecidableEq

end Semantics.DomainState
