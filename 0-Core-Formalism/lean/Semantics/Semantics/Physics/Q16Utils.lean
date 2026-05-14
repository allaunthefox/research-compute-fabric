namespace Semantics.Physics.Q16Utils

def scale : Int := 65536

def absDiff (a b : Int) : Int := if a ≥ b then a - b else b - a

def q16Mul (a b : Int) : Int :=
  let prod := a * b
  if prod ≥ 0 then prod / scale else -((-prod) / scale)

def q16Div (a b : Int) : Option Int :=
  if b = 0 then none
  else if a ≥ 0 then some ((a * scale) / b)
  else some (-(((-a) * scale) / b))

-- All defs in this file are data definitions exercised through theorems in dependent files.
end Semantics.Physics.Q16Utils
