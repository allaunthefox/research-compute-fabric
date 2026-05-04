import Std

/-!
# SuperfluidSemanticKernel

A minimal Lean-side receipt kernel for the Newtonian Superfluid Simulation adapter.

This is not a proof that the simulation is a literal physical superfluid or that
semantic mass is SI mass. It provides a fixed-point, finite-state gate for the
custom semantic-mass stack.
-/

namespace SuperfluidSemanticKernel

abbrev Q16 := UInt32

def q16One : Q16 := 0x00010000

def q16Zero : Q16 := 0

structure SuperfluidSemanticState where
  nodeId : UInt32
  particleCount : UInt32
  massNumber : Q16
  semanticDensity : Q16
  torsion : Q16
  kineticPressure : Q16
  basinStrength : Q16
  receiptCoverage : Q16
  deriving Repr, DecidableEq

inductive GateScope where
  | U_scope
  | V_scope
  deriving Repr, DecidableEq

def hasFullReceipts (s : SuperfluidSemanticState) : Bool :=
  s.receiptCoverage >= q16One

def gateOf (s : SuperfluidSemanticState) : GateScope :=
  if hasFullReceipts s then GateScope.V_scope else GateScope.U_scope

/--
A conservative route-admissibility gate.

The state can route only if semantic mass and basin strength outweigh unresolved
torsion, while still requiring receipts for V-scope promotion elsewhere.
-/
def routeAdmissible (s : SuperfluidSemanticState) : Bool :=
  let support := s.massNumber.toUInt64 + s.basinStrength.toUInt64
  let stress := s.torsion.toUInt64 + (q16One - s.receiptCoverage).toUInt64
  support > stress

/-- Deterministic fallback state matching the JS/Python bridge shape. -/
def fallbackState (nodeId : UInt32) : SuperfluidSemanticState :=
  {
    nodeId := nodeId,
    particleCount := 350,
    massNumber := 0x00008000,
    semanticDensity := 0x00008000,
    torsion := 0x00003000,
    kineticPressure := 0x00004000,
    basinStrength := 0x00006000,
    receiptCoverage := 0x00004000
  }

@[export superfluid_mass_q16]
def superfluidMassQ16 (nodeId : UInt32) : UInt32 :=
  (fallbackState nodeId).massNumber

@[export superfluid_density_q16]
def superfluidDensityQ16 (nodeId : UInt32) : UInt32 :=
  (fallbackState nodeId).semanticDensity

@[export superfluid_torsion_q16]
def superfluidTorsionQ16 (nodeId : UInt32) : UInt32 :=
  (fallbackState nodeId).torsion

@[export superfluid_basin_q16]
def superfluidBasinQ16 (nodeId : UInt32) : UInt32 :=
  (fallbackState nodeId).basinStrength

@[export superfluid_gate_scope]
def superfluidGateScope (nodeId : UInt32) : UInt32 :=
  match gateOf (fallbackState nodeId) with
  | GateScope.U_scope => 0
  | GateScope.V_scope => 1

#eval superfluidMassQ16 1
#eval superfluidDensityQ16 1
#eval superfluidTorsionQ16 1
#eval superfluidBasinQ16 1
#eval superfluidGateScope 1

end SuperfluidSemanticKernel
