import Semantics.Bind
import Semantics.Physics.Conservation
import Semantics.Physics.Examples

namespace Semantics.Physics

open Semantics

/--
Physical binding: the cost of an interaction between particle configurations.

The invariant is the concatenation of conserved quantity signatures.
For a fully lawful interaction, this string must match before and after.
-/
def particleInvariant (ps : List Particle) : String :=
  let qs := ps.flatMap (fun p => p.quantities)
  let charge := totalQuantity QuantityKind.charge qs
  let lepton := totalQuantity QuantityKind.leptonNumber qs
  let baryon := totalQuantity QuantityKind.baryonNumber qs
  s!"C{charge}:L{lepton}:B{baryon}"

/--
Cost of a physical bind: zero if the interaction is lawful under core quantities,
0xFFFFFFFF (Q16.16 infinity) if invariants mismatch.
-/
def physicalCost (inputs outputs : List Particle) (g : Metric) : Q16_16 :=
  let i := Interaction.mk inputs outputs
  let core := [QuantityKind.charge, QuantityKind.leptonNumber, QuantityKind.baryonNumber]
  let lawful := core.all (fun k => decide (conserved k i))
  if lawful then g.cost else Q16_16.ofNat 0xFFFFFFFF

/--
Construct a physical Bind between two particle lists.
-/
def physicalBindEval
  (inputs outputs : List Particle)
  (metric : Metric)
  : Bind (List Particle) (List Particle) :=
  Semantics.physicalBind inputs outputs metric physicalCost particleInvariant particleInvariant

/--
Example: electron-positron annihilation as a lawful physical bind.
-/
def examplePhysicalBind : Bind (List Particle) (List Particle) :=
  physicalBindEval [exampleElectron, examplePositron] [examplePhoton, examplePhoton] Metric.euclidean

#eval examplePhysicalBind.lawful  -- expected: true

-- All defs in this file are data definitions exercised through theorems in dependent files.
end Semantics.Physics
