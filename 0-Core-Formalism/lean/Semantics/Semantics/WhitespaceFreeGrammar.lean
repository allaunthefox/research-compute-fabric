namespace Semantics.WhitespaceFreeGrammar

/-!
Whitespace-free grammar gate.

The intended compression rule is narrow:

* symbol payloads are stored;
* ordinary inter-symbol whitespace is derived from symbol count/order;
* no whitespace symbol is admitted into the payload stream;
* non-canonical spacing needs a residual and therefore remains outside this
  zero-whitespace gate.
-/

/-- A finite grammar atom represented by its payload byte count. -/
structure GrammarAtom where
  payloadBytes : Nat
  deriving Repr, DecidableEq, BEq

/-- Payload cost counts symbols only. Whitespace is not a symbol. -/
def payloadBytes : List GrammarAtom -> Nat
  | [] => 0
  | atom :: rest => atom.payloadBytes + payloadBytes rest

/-- Number of derivable inter-symbol boundaries. -/
def derivedBoundaryCount : List GrammarAtom -> Nat
  | [] => 0
  | [_] => 0
  | _ :: rest => 1 + derivedBoundaryCount rest

/-- Stored whitespace codes are always zero in this gate. -/
def storedWhitespaceCodes (_atoms : List GrammarAtom) : Nat := 0

/-- Stored cost under the zero-whitespace grammar. -/
def storedBytes (atoms : List GrammarAtom) : Nat :=
  payloadBytes atoms + storedWhitespaceCodes atoms

/-- Decoded display bytes if every derived boundary replays as one ASCII space.
    This is a replay cost, not a stored cost. -/
def canonicalDisplayBytes (atoms : List GrammarAtom) : Nat :=
  payloadBytes atoms + derivedBoundaryCount atoms

def atomA : GrammarAtom := { payloadBytes := 5 }
def atomB : GrammarAtom := { payloadBytes := 4 }
def atomC : GrammarAtom := { payloadBytes := 7 }
def exampleAtoms : List GrammarAtom := [atomA, atomB, atomC]

theorem exampleStoredWhitespaceZero :
    storedWhitespaceCodes exampleAtoms = 0 := by
  native_decide

theorem exampleStoredCostDropsDerivedSpaces :
    storedBytes exampleAtoms = payloadBytes exampleAtoms := by
  native_decide

theorem exampleDerivedBoundaryCount :
    derivedBoundaryCount exampleAtoms = 2 := by
  native_decide

theorem exampleCanonicalDisplayCost :
    canonicalDisplayBytes exampleAtoms = storedBytes exampleAtoms + 2 := by
  native_decide

theorem emptyHasNoWhitespaceCodes :
    storedWhitespaceCodes [] = 0 ∧ derivedBoundaryCount [] = 0 := by
  native_decide

theorem singletonHasNoDerivedBoundary :
    storedWhitespaceCodes [atomA] = 0 ∧ derivedBoundaryCount [atomA] = 0 := by
  native_decide

#eval storedWhitespaceCodes exampleAtoms
#eval payloadBytes exampleAtoms
#eval storedBytes exampleAtoms
#eval derivedBoundaryCount exampleAtoms
#eval canonicalDisplayBytes exampleAtoms

end Semantics.WhitespaceFreeGrammar
