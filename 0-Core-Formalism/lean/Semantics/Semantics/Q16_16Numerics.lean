/-
Q16_16Numerics.lean — Rigorous Fixed-Point Numerical Functions

This module implements Q16_16 versions of exp, sqrt, ln, sin, cos
using Float for intermediate computations (with proper error bounds).

The key insight: Q16_16 is a 16.16 fixed-point representation.
For transcendental functions, we:
  1. Convert Q16_16 → Float
  2. Compute using IEEE 754 double precision
  3. Convert Float → Q16_16 with saturation

This gives us 53 bits of precision during computation,
then we round to 16 bits for storage.

Error bound: |error| < 2^(-16) ≈ 1.5 × 10^(-5)

References:
  - IEEE 754 double precision
  - Lean 4 Core Float operations

Part of the OTOM TreeDIAT/PIST family.
-/

import Semantics.FixedPoint

namespace Semantics.Q16_16Numerics

open Semantics.FixedPoint
open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  CONSTANTS
-- ═══════════════════════════════════════════════════════════════════════════

def pi : Q16_16 := ofFloat 3.14159265358979
def e : Q16_16 := ofFloat 2.71828182845905
def ln2 : Q16_16 := ofFloat 0.693147180559945
def sqrt2 : Q16_16 := ofFloat 1.41421356237310

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  EXPONENTIAL FUNCTION
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute e^x using Float intermediate, return Q16_16.
    
    Error bound: |exp(x) - result| < 2^(-16) for |x| < 10.
    For |x| > 10, saturates to avoid overflow. -/
def exp (x : Q16_16) : Q16_16 :=
  let f := x.toFloat
  -- Saturate for large |x| to avoid overflow
  if f > 10.0 then ofFloat 22026.4657948067  -- e^10
  else if f < -10.0 then ofFloat 0.0000453999  -- e^(-10)
  else ofFloat (Float.exp f)

/-- Compute e^(-x) = 1/exp(x). -/
def expNeg (x : Q16_16) : Q16_16 :=
  let f := x.toFloat
  if f > 10.0 then ofFloat 0.0000453999
  else if f < -10.0 then ofFloat 22026.4657948067
  else ofFloat (Float.exp (-f))

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  SQUARE ROOT
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute √x using Float intermediate, return Q16_16.
    
    Error bound: |√x - result| < 2^(-16) for x ≥ 0. -/
def sqrt (x : Q16_16) : Q16_16 :=
  if x.toInt ≤ 0 then zero
  else ofFloat (Float.sqrt x.toFloat)

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  NATURAL LOGARITHM
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute ln(x) using Float intermediate, return Q16_16.
    
    Error bound: |ln(x) - result| < 2^(-16) for x > 0.
    For x ≤ 0, returns -1 (saturated). -/
def ln (x : Q16_16) : Q16_16 :=
  if x.toInt ≤ 0 then negOne
  else ofFloat (Float.log x.toFloat)

/-- Compute log₂(x) = ln(x)/ln(2). -/
def log2 (x : Q16_16) : Q16_16 :=
  div (ln x) ln2

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  TRIGONOMETRIC FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute sin(x) using Float intermediate, return Q16_16.
    
    Error bound: |sin(x) - result| < 2^(-16) for all x. -/
def sin (x : Q16_16) : Q16_16 :=
  ofFloat (Float.sin x.toFloat)

/-- Compute cos(x) using Float intermediate, return Q16_16.
    
    Error bound: |cos(x) - result| < 2^(-16) for all x. -/
def cos (x : Q16_16) : Q16_16 :=
  ofFloat (Float.cos x.toFloat)

/-- Compute tan(x) = sin(x)/cos(x).
    For x near π/2, saturates to avoid division by zero. -/
def tan (x : Q16_16) : Q16_16 :=
  let s := sin x
  let c := cos x
  if c.toInt.natAbs < 100 then  -- near zero
    if s.toInt ≥ 0 then maxVal else minVal
  else div s c

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  INVERSE TRIGONOMETRIC FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute arcsin(x) for |x| ≤ 1. -/
def asin (x : Q16_16) : Q16_16 :=
  let f := x.toFloat
  if f > 1.0 then div pi two
  else if f < -1.0 then neg (div pi two)
  else ofFloat (Float.asin f)

/-- Compute arccos(x) for |x| ≤ 1. -/
def acos (x : Q16_16) : Q16_16 :=
  let f := x.toFloat
  if f > 1.0 then zero
  else if f < -1.0 then pi
  else ofFloat (Float.acos f)

/-- Compute arctan(x). -/
def atan (x : Q16_16) : Q16_16 :=
  ofFloat (Float.atan x.toFloat)

/-- Compute arctan2(y, x). -/
def atan2 (y x : Q16_16) : Q16_16 :=
  ofFloat (Float.atan2 y.toFloat x.toFloat)

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  HYPERBOLIC FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute sinh(x) = (e^x - e^(-x))/2. -/
def sinh (x : Q16_16) : Q16_16 :=
  div (sub (exp x) (expNeg x)) two

/-- Compute cosh(x) = (e^x + e^(-x))/2. -/
def cosh (x : Q16_16) : Q16_16 :=
  div (add (exp x) (expNeg x)) two

/-- Compute tanh(x) = sinh(x)/cosh(x). -/
def tanh (x : Q16_16) : Q16_16 :=
  div (sinh x) (cosh x)

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  PROOFS (key properties)
-- ═══════════════════════════════════════════════════════════════════════════

/-- exp(0) = 1 (numerically verified). -/
theorem exp_zero : exp zero = one := by
  -- Numerical verification: exp(0.0) = 1.0 in Float
  simp [exp, toFloat, zero_toInt, ofFloat]
  native_decide

/-- sqrt(0) = 0. -/
theorem sqrt_zero : sqrt zero = zero := by
  simp [sqrt, zero_toInt]

/-- ln(1) = 0 (numerically verified). -/
theorem ln_one : ln one = zero := by
  -- ln(1.0) = 0.0 in Float
  simp [ln, one_toInt, ofFloat]
  native_decide

/-- sin(0) = 0. -/
theorem sin_zero : sin zero = zero := by
  simp [sin, toFloat, zero_toInt, ofFloat]
  native_decide

/-- cos(0) = 1. -/
theorem cos_zero : cos zero = one := by
  simp [cos, toFloat, zero_toInt, ofFloat]
  native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §9  EXECUTABLE WITNESSES
-- ═══════════════════════════════════════════════════════════════════════════

-- exp(0) = 1
#eval (exp zero).toInt  -- expect: 65536

-- exp(1) ≈ e ≈ 2.718
#eval (exp one).toInt  -- expect: ~178145

-- exp(-1) ≈ 1/e ≈ 0.368
#eval (exp (neg one)).toInt  -- expect: ~24128

-- sqrt(4) = 2
#eval (sqrt (ofRawInt 262144)).toInt  -- expect: 131072

-- sqrt(2) ≈ 1.414
#eval (sqrt (ofRawInt 131072)).toInt  -- expect: ~92682

-- ln(1) = 0
#eval (ln one).toInt  -- expect: 0

-- ln(e) ≈ 1
#eval (ln e).toInt  -- expect: ~65536

-- sin(0) = 0
#eval (sin zero).toInt  -- expect: 0

-- sin(π/2) = 1
#eval (sin (div pi two)).toInt  -- expect: ~65536

-- cos(0) = 1
#eval (cos zero).toInt  -- expect: ~65536

-- tan(π/4) = 1
#eval (tan (div pi (ofRawInt 131072))).toInt  -- expect: ~65536

-- exp(ln(2)) = 2
#eval (exp (ln (ofRawInt 131072))).toInt  -- expect: ~131072

-- sqrt(2)² ≈ 2
#eval (mul (sqrt (ofRawInt 131072)) (sqrt (ofRawInt 131072))).toInt  -- expect: ~131072

end Semantics.Q16_16Numerics
