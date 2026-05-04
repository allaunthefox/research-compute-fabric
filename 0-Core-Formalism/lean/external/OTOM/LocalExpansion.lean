/-
  LocalExpansion.lean - Fixed-Point Local Taylor Expansion
-/

import Semantics.DynamicCanal
import Semantics.LocalDerivative

namespace Semantics.LocalExpansion

open DynamicCanal
open Semantics.LocalDerivative

abbrev Scalar := Fix16

structure LocalExpansion where
  base : Scalar
  gradient : List Scalar
  hessian : List (List Scalar)

-- No deriving Repr/DecidableEq due to List (List Scalar) issues

def localExpansionInvariant (expansion : LocalExpansion) : Prop :=
  squareMatrixInvariant expansion.hessian ∧
  expansion.gradient.length = expansion.hessian.length

def fromLocalDerivative (base : Scalar) (derivative : LocalDerivative) : LocalExpansion :=
  { base := base
  , gradient := diagonalEntries derivative.jacobian  -- Use diagonal as gradient approximation
  , hessian := derivative.hessian }

def listGet? {α : Type} (list : List α) (n : Nat) : Option α :=
  match list, n with
  | [], _ => none
  | a :: _, 0 => some a
  | _ :: as, n+1 => listGet? as n

def evaluateLinear (expansion : LocalExpansion) (offset : List Scalar) : Scalar :=
  let linear := List.zipWith (fun g x => Fix16.mul g x) expansion.gradient offset
    |>.foldl (fun acc val => Fix16.add acc val) Fix16.zero
  Fix16.add expansion.base linear

def quadraticForm (hessian : List (List Scalar)) (offset : List Scalar) : Scalar :=
  let rowContribs :=
    List.zip (List.range hessian.length) hessian |>.map (fun (rowIndex, row) =>
      let xi := match listGet? offset rowIndex with | some value => value | none => Fix16.zero
      List.zip (List.range row.length) row |>.foldl (fun acc (columnIndex, hij) =>
        let xj := match listGet? offset columnIndex with | some value => value | none => Fix16.zero
        Fix16.add acc (Fix16.mul (Fix16.mul xi hij) xj)) Fix16.zero)
  rowContribs.foldl (fun acc val => Fix16.add acc val) Fix16.zero

def evaluateTaylor2 (expansion : LocalExpansion) (offset : List Scalar) : Scalar :=
  let linear := evaluateLinear expansion offset
  let quad := quadraticForm expansion.hessian offset
  Fix16.add linear (Fix16.mk (quad.raw.toNat / 2).toUInt32)  -- 0.5 * quad approx

end Semantics.LocalExpansion
