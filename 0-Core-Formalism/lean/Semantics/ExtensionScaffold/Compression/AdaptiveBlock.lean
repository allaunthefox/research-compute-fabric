import Semantics.Bind
import ExtensionScaffold.Compression.CodingCost

namespace ExtensionScaffold.Compression.AdaptiveBlock

open Semantics

inductive Token where
  | e | t | a | space
  deriving Repr, BEq, DecidableEq

def Token.toString : Token → String
  | .e => "e"
  | .t => "t"
  | .a => "a"
  | .space => "space"

structure ProtocolState where
  token : Token
  freq  : UInt32 
  deriving Repr

-- ============================================================================
-- STRICT DISTRIBUTION INVARIANTS
-- ============================================================================

def isValidFreq (s : ProtocolState) : Bool :=
  s.freq <= 0x00010000

def sumFreqs (l : List ProtocolState) : UInt64 :=
  l.foldl (fun sum s => sum + s.freq.toUInt64) 0

def hasNoDuplicates : List ProtocolState → Bool
  | [] => true
  | (x :: xs) => (xs.all (fun s => s.token != x.token)) && hasNoDuplicates xs

/-- 
  Strict probability wrapper guaranteeing structural mass conservation.
-/
structure Distribution where
  states : List ProtocolState
  validEq : states.all isValidFreq = true
  normEq  : sumFreqs states == 0x00010000
  nodupsEq : hasNoDuplicates states = true

/--
  Safe constructor for validated distributions used by the extension modules.
-/
def mkDistribution? (states : List ProtocolState) : Option Distribution :=
  if hValid : states.all isValidFreq = true then
    if hNorm : sumFreqs states == 0x00010000 then
      if hNodups : hasNoDuplicates states = true then
        some {
          states := states
          validEq := hValid
          normEq := hNorm
          nodupsEq := hNodups
        }
      else
        none
    else
      none
  else
    none

-- ============================================================================
-- THERMODYNAMIC MOMENTUM (EMA ADAPTATION)
-- ============================================================================

/-- Q16.16 scalar multiplication bitshift. Returns (a * b) / 65536. -/
def mulQ16 (a b : UInt32) : UInt32 :=
  ((a.toUInt64 * b.toUInt64) >>> 16).toUInt32

/-- Decays a probability strictly linearly via alpha, clamped against a minimum floor constraint. -/
def emaDecay (old_p alpha floor : UInt32) : UInt32 :=
  let dropped := mulQ16 old_p alpha
  let new_p := if dropped > old_p then 0x00000000 else old_p - dropped
  if new_p < floor then floor else new_p

/-- 
  A Division-free Fixed-Point Remainder-Preserving EMA Rule.
  We explicitly abandon integer division tallies in favor of exact topologic scaling.
  It preserves bounded memory, exact total mass, deterministic decode semantics, 
  and explicit forgetting natively under hardware bounds.
  
  Tokens naturally decay and the exact fractional target isolates the identical 
  remainder ensuring exact normalization to 1.0 (0x00010000) permanently.
-/
def emaAdaptTopology (target : Token) (dist : Distribution) (alpha : UInt32) : Distribution :=
  -- Minimum floor to prevent hard collapse/infinite bits on out-of-bounds occurrences.
  let floor_bound : UInt32 := 0x00000008 
  
  let decayed := dist.states.map (fun s => 
    if s.token == target then s -- Placeholder for exact remainder extraction
    else { s with freq := emaDecay s.freq alpha floor_bound }
  )
  
  -- Secure perfect 1.0 remainder for the target, absorbing microscopic truncation limits 
  -- naturally as explicit momentum mapping instead of float deviation.
  let sum_others : UInt64 := decayed.foldl (fun sum s => 
    if s.token == target then sum else sum + s.freq.toUInt64
  ) 0
  let new_target_freq : UInt32 := 0x00010000 - sum_others.toUInt32
  
  let finalized_states := decayed.map (fun s => 
    if s.token == target then { s with freq := new_target_freq } 
    else s
  )

  match mkDistribution? finalized_states with
  | some finalized => finalized
  | none => dist

-- ============================================================================
-- ADAPTIVE BLOCK BINDING
-- ============================================================================

-- The 4x4 internal context mapping matrix dynamically tracking context probability boundaries.
def TopologyMatrix := Token → Distribution  

structure BlockState where
  matrix : TopologyMatrix
  accumulated_cost : UInt64
  edge_anchor : Token

/-- 
  Runs sequentially through a block of Tokens separating code evaluations cleanly from state updates.
-/
def adaptiveBlockBind (block : List Token) (state : BlockState) (alpha : UInt32) : BlockState :=
  block.foldl (fun s target =>
    let context_dist := s.matrix s.edge_anchor
    
    -- STEP 1: Code to encode the symbol using the strictly decoupled pre-update model.
    let predicted_p : UInt32 := match context_dist.states.find? (fun i => i.token == target) with
                                | some p => p.freq
                                | none => 0x00000000
    let cost := CodingCost.negLog2Q16 predicted_p
    
    -- STEP 2: The explicit online model update law adapting topological gradients post-encoding.
    let updated_context := emaAdaptTopology target context_dist alpha
    let updated_matrix := fun (v : Token) => 
      if v == s.edge_anchor then updated_context else s.matrix v
      
    { matrix := updated_matrix, 
      accumulated_cost := s.accumulated_cost + cost.toUInt64, 
      edge_anchor := target }
  ) state

-- ============================================================================
-- THE PROOF OF CAPABILITY
-- ============================================================================

def uniformDist : Distribution := {
  states := [
    { token := Token.e, freq := 0x00004000 },
    { token := Token.t, freq := 0x00004000 },
    { token := Token.a, freq := 0x00004000 },
    { token := Token.space, freq := 0x00004000 }
  ],
  validEq := rfl,
  normEq := rfl,
  nodupsEq := rfl
}

def initialState : BlockState := {
  matrix := fun _ => uniformDist,  
  accumulated_cost := 0,
  edge_anchor := Token.space       
}

-- Target pattern constantly repeating: e -> space -> e -> space
def block1 := [Token.e, Token.space, Token.e, Token.space]
def block2 := [Token.e, Token.space, Token.e, Token.space]
def block3 := [Token.e, Token.space, Token.e, Token.space]

def stateAfterB1 := adaptiveBlockBind block1 initialState 0x00008000
def stateAfterB2 := adaptiveBlockBind block2 stateAfterB1 0x00008000
def stateAfterB3 := adaptiveBlockBind block3 stateAfterB2 0x00008000

#eval! stateAfterB1.accumulated_cost - initialState.accumulated_cost
#eval! stateAfterB2.accumulated_cost - stateAfterB1.accumulated_cost
#eval! stateAfterB3.accumulated_cost - stateAfterB2.accumulated_cost

end ExtensionScaffold.Compression.AdaptiveBlock
