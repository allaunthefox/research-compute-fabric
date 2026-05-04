import Semantics.Physics.Boundary
import Semantics.Physics.Conservation

namespace Semantics.Physics

/--
Core conserved quantities used to judge physical lawfulness of an interaction.
This list can be extended as the framework grows.
-/
def coreConservedQuantities : List QuantityKind :=
  [ QuantityKind.charge
  , QuantityKind.energy
  , QuantityKind.momentum
  , QuantityKind.leptonNumber
  , QuantityKind.baryonNumber
  ]

/--
A physical path is a sequence of particle transitions where each step
is a lawful interaction under the core conserved quantities.

This maps the ENE Path concept directly onto Feynman-diagram-like
histories: each vertex is a semantic decomposition (or recombination)
that preserves invariants.
-/
structure PhysicalPath where
  steps : List Interaction
  -- Each step is lawful under the core conserved quantities
  lawful : ∀ step ∈ steps, LawfulInteraction coreConservedQuantities step

end Semantics.Physics
