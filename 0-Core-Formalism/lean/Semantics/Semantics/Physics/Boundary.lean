import Semantics.Physics.ParticleDomain

namespace Semantics.Physics

/--
Quantities that are conserved in physical interactions.
These act as the "true bits" of physical description.
-/
inductive QuantityKind : Type
  | charge
  | mass
  | spin
  | energy
  | momentum
  | baryonNumber
  | leptonNumber
deriving Repr, DecidableEq

/--
A Physical Quantity is a kind paired with a rational value.
Using Int ensures exact arithmetic for conservation checks.
-/
structure Quantity where
  kind  : QuantityKind
  value : Int
deriving Repr, DecidableEq

/--
A Particle is a kind together with its list of quantities.
-/
structure Particle where
  kind       : ParticleKind
  quantities : List Quantity
deriving Repr, DecidableEq

end Semantics.Physics
