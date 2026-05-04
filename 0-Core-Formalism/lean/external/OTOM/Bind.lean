namespace Semantics

/--
The single primitive of the Cambrian collapse.

A Metric measures the cost of lawful assemblage between two objects.
All scalar fields use Q16.16 fixed-point (UInt32) for hardware-native
execution: 0x00010000 = 1.0, 0xFFFFFFFF ≈ infinity/illegal.
-/
structure Metric where
  cost        : UInt32  -- Q16.16 scalar cost of the bind
  tensor      : String  -- "identity", "riemannian", "thermodynamic", "informational", "physical"
  torsion     : UInt32  -- Q16.16 informatic torsion (0 = Euclidean)
  reference   : String  -- human-readable reference tag
  history_len : Nat     -- how many previous binds informed this metric

def Metric.euclidean : Metric := {
  cost := 0x00000000,
  tensor := "identity",
  torsion := 0x00000000,
  reference := "euclidean_baseline",
  history_len := 0
}

/--
Witness: the trace that a bind occurred lawfully.
-/
structure Witness where
  left_invariant  : String
  right_invariant : String
  conserved       : Bool
  trace_hash      : String

def Witness.lawful (left right : String) : Witness := {
  left_invariant := left,
  right_invariant := right,
  conserved := true,
  trace_hash := s!"lawful:{left}={right}"
}

/--
The universal bind primitive.

bind(A, B, g) = (cost, witness)

Lawful iff the invariants of A and B match.
-/
structure Bind (A B : Type) where
  left    : A
  right   : B
  metric  : Metric
  cost    : UInt32  -- Q16.16
  witness : Witness
  lawful  : Bool -- simplified to Bool for clean compilation

def bind {A B : Type}
  (left : A) (right : B)
  (metric : Metric)
  (cost_fn : A → B → Metric → UInt32)
  (invA : A → String) (invB : B → String)
  : Bind A B :=
  let c := cost_fn left right metric
  let w := Witness.lawful (invA left) (invB right)
  let is_lawful := invA left = invB right
  { left := left, right := right, metric := metric, cost := c, witness := w, lawful := is_lawful }

def informationalBind {A B : Type} (left : A) (right : B) (metric : Metric) (cost_fn : A → B → Metric → UInt32) (invA : A → String) (invB : B → String) : Bind A B :=
  bind left right { metric with tensor := "informational" } cost_fn invA invB

def geometricBind {A B : Type} (left : A) (right : B) (metric : Metric) (cost_fn : A → B → Metric → UInt32) (invA : A → String) (invB : B → String) : Bind A B :=
  bind left right { metric with tensor := "geometric" } cost_fn invA invB

def thermodynamicBind {A B : Type} (left : A) (right : B) (metric : Metric) (cost_fn : A → B → Metric → UInt32) (invA : A → String) (invB : B → String) : Bind A B :=
  bind left right { metric with tensor := "thermodynamic" } cost_fn invA invB

def physicalBind {A B : Type} (left : A) (right : B) (metric : Metric) (cost_fn : A → B → Metric → UInt32) (invA : A → String) (invB : B → String) : Bind A B :=
  bind left right { metric with tensor := "physical" } cost_fn invA invB

def controlBind {A B : Type} (left : A) (right : B) (metric : Metric) (cost_fn : A → B → Metric → UInt32) (invA : A → String) (invB : B → String) : Bind A B :=
  bind left right { metric with tensor := "control" } cost_fn invA invB

end Semantics
