import Std

/-!
# OntologyKernel

A minimal Lean 4 kernel intended for a future C/Wasm bridge.

This file keeps the hot-path representation fixed-point friendly. The browser
prototype expects Q16.16-style unsigned integers:

```text
0x00010000 = 1.0
```

The exported symbols below are intentionally tiny. A production bridge should
wrap Lean objects carefully or generate C ABI shims with the build system.
-/

namespace OntologyKernel

abbrev Q16 := UInt32

def q16One : Q16 := 0x00010000

def q16Half : Q16 := 0x00008000

def q16Clamp01 (x : Q16) : Q16 :=
  if x > q16One then q16One else x

structure SemanticNode where
  id : UInt32
  massNumber : Q16
  density : Q16
  torsion : Q16
  receiptCoverage : Q16
  deriving Repr, DecidableEq

inductive GateScope where
  | U_scope
  | V_scope
  deriving Repr, DecidableEq

def gateOf (n : SemanticNode) : GateScope :=
  if n.receiptCoverage >= q16One then GateScope.V_scope else GateScope.U_scope

/-- Deterministic placeholder node used by the browser fallback bridge. -/
def nodeById (id : UInt32) : SemanticNode :=
  match id with
  | 1 => {
      id := 1,
      massNumber := 0x00009EB8,      -- approx 0.62
      density := 0x000068F5,         -- approx 0.41
      torsion := 0x00002E14,         -- approx 0.18
      receiptCoverage := 0x00005999  -- approx 0.35
    }
  | _ => {
      id := id,
      massNumber := q16Half,
      density := q16Half,
      torsion := 0x00002000,
      receiptCoverage := 0x00002000
    }

/-- Semantic attraction in a Q16-ish integer domain. -/
def semanticAttractionRaw (a b : SemanticNode) : UInt64 :=
  (a.massNumber.toUInt64 * b.massNumber.toUInt64) / q16One.toUInt64

/-- Torsion pressure is a simple additive unresolved-stress proxy. -/
def torsionPressureRaw (a b : SemanticNode) : UInt64 :=
  a.torsion.toUInt64 + b.torsion.toUInt64

/-- A route is admissible if attraction exceeds torsion pressure. -/
def routeAdmissible (a b : SemanticNode) : Bool :=
  semanticAttractionRaw a b > torsionPressureRaw a b

/-- Export candidate: semantic mass as Q16.16 UInt32. -/
@[export semantic_mass_q16]
def semanticMassQ16 (id : UInt32) : UInt32 :=
  (nodeById id).massNumber

/-- Export candidate: semantic density as Q16.16 UInt32. -/
@[export semantic_density_q16]
def semanticDensityQ16 (id : UInt32) : UInt32 :=
  (nodeById id).density

/-- Export candidate: semantic torsion as Q16.16 UInt32. -/
@[export semantic_torsion_q16]
def semanticTorsionQ16 (id : UInt32) : UInt32 :=
  (nodeById id).torsion

/-- Export candidate: 0 = U_scope, 1 = V_scope. -/
@[export gate_scope]
def gateScopeExport (id : UInt32) : UInt32 :=
  match gateOf (nodeById id) with
  | GateScope.U_scope => 0
  | GateScope.V_scope => 1

#eval semanticMassQ16 1
#eval semanticDensityQ16 1
#eval semanticTorsionQ16 1
#eval gateScopeExport 1

end OntologyKernel
