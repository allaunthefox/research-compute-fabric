import Semantics.FixedPoint
import Semantics.AdjugateMatrix

set_option linter.dupNamespace false
set_option maxRecDepth 20000

namespace Semantics.AdjugateMatrix

open Semantics.FixedPoint
open Semantics.Q16_16

-- Provable helper: identity is its own inverse
theorem identity8_self_inverse :
    matrixInverse identity8 = some identity8 := by
  native_decide

-- Provable helper: identity times identity is identity
theorem identity8_mul_self :
    matrixMultiply identity8 identity8 = identity8 := by
  native_decide

-- Provable: det of identity is one
theorem det8_identity :
    det8 identity8 = one := by
  native_decide

-- Provable: det_self_inverse holds for the identity matrix
theorem det_self_inverse_identity (inv : Matrix8)
    (h : matrixInverse identity8 = some inv) :
    matrixMultiply identity8 inv = identity8 := by
  have hinv : inv = identity8 := by
    rw [identity8_self_inverse] at h
    exact (Option.some_injective _ h).symm
  subst hinv
  exact identity8_mul_self

end Semantics.AdjugateMatrix
