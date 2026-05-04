/-
  SolitonTensor.lean - Soliton Wave Emission for Tensor Field Mapping (Stub)
-/

import Semantics.FixedPoint
import Semantics.Functions.BracketedCalculus

namespace Semantics.SolitonTensor

open Semantics.Q16_16
open Semantics.BracketedCalculus

structure SolitonWave where
  phase : Q16_16
  amplitude : Q16_16
  velocity : UInt32
  position : UInt32

def emit ( _bracket  : BracketedDIAT) ( _frequency  : Q16_16) (position : UInt32) : SolitonWave :=
  { phase := zero
  , amplitude := one
  , velocity := 0
  , position := position }

def propagate (wave : SolitonWave) ( _dt  : Q16_16) (_field : UInt32 → Q16_16) : SolitonWave :=
  wave

end SolitonTensor
