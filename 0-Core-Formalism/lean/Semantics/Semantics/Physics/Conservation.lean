import Semantics.Physics.Boundary

namespace Semantics.Physics

/--
Lookup the total value of a given quantity kind in a list of quantities.
Returns 0 if the kind is absent.
-/
def totalQuantity (k : QuantityKind) (qs : List Quantity) : Int :=
  qs.foldl (fun acc q => if q.kind = k then acc + q.value else acc) 0

/--
An Interaction consists of input particles and output particles.
-/
structure Interaction where
  inputs  : List Particle
  outputs : List Particle
deriving Repr

/--
Conservation predicate: a quantity kind is conserved in an interaction
iff the total input value equals the total output value.
-/
def conserved (k : QuantityKind) (i : Interaction) : Prop :=
  totalQuantity k (i.inputs.flatMap (fun p => p.quantities))
    = totalQuantity k (i.outputs.flatMap (fun p => p.quantities))

instance : Decidable (conserved k i) := by
  unfold conserved
  infer_instance

/--
A lawful interaction is one in which all of the listed quantity kinds
are conserved.
-/
def LawfulInteraction (ks : List QuantityKind) (i : Interaction) : Prop :=
  ∀ k ∈ ks, conserved k i

end Semantics.Physics
