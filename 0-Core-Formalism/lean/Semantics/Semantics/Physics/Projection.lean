import Semantics.Physics.Boundary

namespace Semantics.Physics

/--
Measurement is the projection of a quantum (hidden / N-space) particle state
into an observable (visible) particle state.

In the Physical Semantics paradigm, "collapse" is not a metaphysical claim
about wavefunction reduction; it is the epistemic projection from a hidden
semantic path to a determinate observation.
-/
structure Measurement where
  hiddenState   : Particle
  observedState : Particle
  -- The observed state must be the same particle kind as the hidden state
  compatible    : hiddenState.kind = observedState.kind

/--
A projection is faithful if the observed kind matches the hidden kind.
(Stronger conservation checks can be added as the framework expands.)
-/
def faithfulMeasurement (m : Measurement) : Prop :=
  m.hiddenState.kind = m.observedState.kind

-- All defs in this file are data definitions exercised through theorems in dependent files.
end Semantics.Physics
