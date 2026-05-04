namespace Semantics.Metatype

/--
The three pillars of the Research Stack.
-/
inductive Layer
  | Substrate -- ENE (Truth)
  | Surface   -- Notion (View)
  | Intent    -- Linear (Action)
deriving Repr, BEq, DecidableEq

/--
A Stack is an assemblage of layers.
-/
structure Stack where
  layers : List Layer
  isIntegrated : Bool

def containsLayer : List Layer → Layer → Bool
  | [], _ => false
  | x :: xs, target => if x == target then true else containsLayer xs target

/--
Theorem: Emergence via Integration (Metatyping).
A stack with all three layers integrated emerges as a self-describing 'Metastack'.
-/
def isMetastack (s : Stack) : Bool :=
  s.isIntegrated &&
  containsLayer s.layers .Substrate &&
  containsLayer s.layers .Surface &&
  containsLayer s.layers .Intent

theorem emergenceViaIntegration
  (s : Stack) 
  (h : s.isIntegrated = true) 
  (hSub : containsLayer s.layers .Substrate = true) 
  (hSur : containsLayer s.layers .Surface = true) 
  (hInt : containsLayer s.layers .Intent = true) :
  isMetastack s = true := by
  unfold isMetastack
  simp [h, hSub, hSur, hInt]

end Semantics.Metatype
