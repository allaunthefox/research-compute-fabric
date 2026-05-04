namespace Semantics

/-- 
Cognitive Load metrics.
Mirrors `docs/cognitive/COGNITIVE_LOAD_FUNCTIONS_SPEC.md`.
-/
structure CognitiveLoad where
  intrinsic  : Float
  extraneous : Float
  germane    : Float
  routing    : Float
  memory     : Float
  total      : Float
deriving Repr, BEq

end Semantics
