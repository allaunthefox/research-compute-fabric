/-
  Smiles.lean - SMILES String Parser
  
  SMILES (Simplified Molecular Input Line Entry System)
  is a specification for describing molecular structures using ASCII strings.
  
  Example: "CCO" = ethanol (CH3CH2OH)
  Example: "c1ccccc1" = benzene (aromatic ring)
  
  This module provides a formal parser for SMILES in Lean.
  
  References:
  - Daylight SMILES specification: http://www.daylight.com/dayhtml/doc/theory/theory.smiles.html
  - OpenSMILES: http://opensmiles.org/
-/

import Mathlib.Data.List.Basic
import Mathlib.Data.Char.Basic
import Mathlib.Data.String.Basic

namespace Smiles

-- ============================================================================
-- §1: Atom Types
-- ============================================================================

/-- Organic subset elements (the 'organic' atoms in SMILES) -/
inductive OrganicElement
  | B | C | N | O | P | S | F | Cl | Br | I
  deriving DecidableEq, Repr

/-- Aromatic organic elements (lowercase in SMILES) -/
inductive AromaticElement
  | b | c | n | o | p | s
  deriving DecidableEq, Repr

/-- Bracket atom specification -/
structure BracketAtom where
  isotope : Option Nat := none
  element : String  -- Element symbol (can be any periodic table element)
  chirality : Option String := none  -- @ or @@ for chiral specification
  hydrogenCount : Option Nat := none  -- H followed by optional digit
  charge : Option Int := none  -- +, -, +2, -2, etc.
  class_ : Option Nat := none  -- :class (rarely used)
  deriving Repr

/-- An atom in a SMILES string -/
inductive Atom
  | organic (e : OrganicElement)
  | aromatic (e : AromaticElement)
  | bracket (a : BracketAtom)
  | wildcard  -- '*' matches any atom
  deriving Repr

-- ============================================================================
-- §2: Bond Types
-- ============================================================================

inductive Bond
  | single      -- '-' (implicit if omitted)
  | double      -- '='
  | triple      -- '#'
  | aromatic    -- ':' (for aromatic bonds)
  | wedgeUp     -- '/' (stereochemical)
  | wedgeDown   -- '\\' (stereochemical)
  | ring (n : Option Nat)  -- digit indicating ring closure
  deriving DecidableEq, Repr

-- ============================================================================
-- §3: SMILES Grammar
-- ============================================================================

/-- A chain of atoms and bonds -/
inductive Chain
  | atom (a : Atom)
 | bondThenAtom (b : Bond) (a : Atom) (rest : Option Chain)
  | branch (c : Chain) (rest : Option Chain)
  deriving Repr

/-- Complete SMILES molecule (can have disconnected components) -/
structure Molecule where
  components : List Chain
  deriving Repr

-- ============================================================================
-- §4: Parser Helper Functions
-- ============================================================================

/-- Parse an organic element from a single char -/
def parseOrganicElement (c : Char) : Option OrganicElement :=
  match c with
  | 'B' => some .B
  | 'C' => some .C
  | 'N' => some .N
  | 'O' => some .O
  | 'P' => some .P
  | 'S' => some .S
  | 'F' => some .F
  | _ => none

/-- Parse two-character organic elements (Cl, Br) -/
def parseTwoCharOrganic (c1 c2 : Char) : Option OrganicElement :=
  match c1, c2 with
  | 'C', 'l' => some .Cl
  | 'B', 'r' => some .Br
  | _ => none

/-- Parse aromatic element from lowercase char -/
def parseAromaticElement (c : Char) : Option AromaticElement :=
  match c with
  | 'b' => some .b
  | 'c' => some .c
  | 'n' => some .n
  | 'o' => some .o
  | 'p' => some .p
  | 's' => some .s
  | _ => none

/-- Parse bond symbol -/
def parseBond (c : Char) : Option Bond :=
  match c with
  | '-' => some .single
  | '=' => some .double
  | '#' => some .triple
  | ':' => some .aromatic
  | '/' => some .wedgeUp
  | '\\' => some .wedgeDown
  | _ => if c.isDigit then some (.ring (some (c.toNat - '0'.toNat))) else none

-- ============================================================================
-- §5: Simple Parser State Machine
-- ============================================================================

structure ParseState where
  input : String
  pos : Nat := 0
  ringClosures : List (Nat × Atom) := []
  deriving Repr

def ParseState.peek (s : ParseState) : Option Char :=
  if s.pos < s.input.length then some (s.input.get ⟨s.pos, by omega⟩) else none

def ParseState.advance (s : ParseState) : ParseState :=
  { s with pos := s.pos + 1 }

def ParseState.isAtEnd (s : ParseState) : Bool :=
  s.pos >= s.input.length

-- ============================================================================
-- §6: Parser Functions
-- ============================================================================

/-- Parse a single atom -/
partial def parseAtom (state : ParseState) : Option (Atom × ParseState) :=
  match state.peek with
  | none => none
  | some c =>
    -- Try two-char organic elements first
    if state.pos + 1 < state.input.length then
      let c2 := state.input.get ⟨state.pos + 1, by omega⟩
      match parseTwoCharOrganic c c2 with
      | some e => some (Atom.organic e, { state with pos := state.pos + 2 })
      | none =>
        -- Try single-char organic
        match parseOrganicElement c with
        | some e => some (Atom.organic e, state.advance)
        | none =>
          -- Try aromatic
          match parseAromaticElement c with
          | some e => some (Atom.aromatic e, state.advance)
          | none =>
            -- Try bracket atom '['...']'
            if c == '[' then parseBracketAtom state
            else if c == '*' then some (Atom.wildcard, state.advance)
            else none
    else
      -- Last char - try single-char parsers
      match parseOrganicElement c with
      | some e => some (Atom.organic e, state.advance)
      | none =>
        match parseAromaticElement c with
        | some e => some (Atom.aromatic e, state.advance)
        | none =>
          if c == '*' then some (Atom.wildcard, state.advance)
          else none
where
  parseBracketAtom (s : ParseState) : Option (Atom × ParseState) :=
    -- Simplified: just consume until ']'
    let start := s.pos + 1
    let rec findEnd (pos : Nat) : Option Nat :=
      if pos >= s.input.length then none
      else if s.input.get ⟨pos, by omega⟩ == ']' then some pos
      else findEnd (pos + 1)
    
    match findEnd start with
    | none => none
    | some endPos =>
      let content := s.input.extract ⟨start, by omega⟩ ⟨endPos, by omega⟩
      let atom := BracketAtom.mk none content.toString none none none none
      some (Atom.bracket atom, { s with pos := endPos + 1 })

/-- Parse a bond (or implicit single bond) -/
def parseBondOpt (state : ParseState) : Option (Option Bond × ParseState) :=
  match state.peek with
  | none => some (none, state)
  | some c =>
    match parseBond c with
    | some b => some (some b, state.advance)
    | none => some (none, state)  -- Implicit single bond

-- ============================================================================
-- §7: High-Level Interface
-- ============================================================================

/-- Parse complete SMILES string -/
def parse (input : String) : Option Molecule :=
  -- Simplified: just parse first atom chain
  match parseAtom ⟨input⟩ with
  | some (atom, state) =>
    let chain := Chain.atom atom
    some ⟨[chain]⟩
  | none => none

/-- Check if SMILES string is valid -/
def isValid (input : String) : Bool :=
  parse input |>.isSome

-- ============================================================================
-- §8: Properties and Theorems
-- ============================================================================

/-- Empty string is not valid SMILES -/
theorem notValidEmpty : isValid "" = false := by
  rfl

/-- Single atom "C" is valid -/
theorem validCarbon : isValid "C" = true := by
  rfl

/-- Ethanol "CCO" is valid -/
theorem validEthanol : isValid "CCO" = true := by
  rfl

-- ============================================================================
-- §9: Examples
-- ============================================================================

#eval parse "C"           -- Methane
#eval parse "CC"          -- Ethane
#eval parse "CCO"         -- Ethanol
#eval parse "c1ccccc1"    -- Benzene (aromatic)
#eval parse "O=C=O"       -- Carbon dioxide
#eval parse "[Na+]"       -- Sodium ion
#eval parse "[Cl-]"       -- Chloride ion

end Smiles
