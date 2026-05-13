/-
  UniversalBridge.lean - Hermite Spline Transition for the 16D Reynolds Regime Bridge

  Implements the C¹-continuous Cubic Hermite Spline connecting the laminar and
  turbulent friction-factor regimes across the transitional zone (2300 ≤ Re ≤ 4000).

  Boundary conditions (Moody chart / Darcy friction factor):
    Point A (Laminar exit):   Re=2300, f=0.0278, slope m₀ = −1.21×10⁻⁵
    Point B (Turbulent entry): Re=4000, f=0.0398, slope m₁ = −2.49×10⁻⁶

  The bridge function H(t) uses the normalized variable t = (Re − 2300) / 1700
  and satisfies:
    H(0) = y₀,   H'(0) = h·m₀
    H(1) = y₁,   H'(1) = h·m₁

  Intermittency γ = (H(t) − y₀) / (y₁ − y₀) gives the turbulent fraction in
  the 16D controller's superpositional collapse model.

  Note on Q16.16 arithmetic:
    Lean 4.30 uses Euclidean (floor) division for `Int./`.  Standard Q16.16
    truncates toward zero.  We apply a sign check in `q16_mul` and `q16_div`
    to correct for this.  The difference is at most 1 ULP (1/65536) and is
    negligible for engineering purposes, but formal correctness requires it.
-/

namespace Semantics.Physics.UniversalBridge

-- ============================================================================
-- Q16.16 fixed-point scale (2¹⁶ = 65536)
-- ============================================================================

def SCALE : Int := 65536

-- ============================================================================
-- Boundary condition constants (all pre-computed as Q16.16 integers)
-- ============================================================================

/-- Reynolds number at laminar exit -/
def RE_LAMINAR : Int := 2300
/-- Reynolds number at turbulent entry -/
def RE_TURBULENT : Int := 4000
/-- Interval width h = RE_TURBULENT − RE_LAMINAR = 1700 -/
def H_INTERVAL : Int := 1700

/-- f at laminar exit: round(0.0278 × 65536) = 1822 -/
def Y0 : Int := 1822
/-- f at turbulent entry: round(0.0398 × 65536) = 2608 -/
def Y1 : Int := 2608

/-- h·m₀ where m₀ = −1.21e−5: round(1700 × −1.21e−5 × 65536) = −1348 -/
def H_M0 : Int := -1348
/-- h·m₁ where m₁ = −2.49e−6: round(1700 × −2.49e−6 × 65536) = −277 -/
def H_M1 : Int := -277

-- ============================================================================
-- Q16.16 arithmetic helpers
-- ============================================================================

/-- Q16.16 multiplication with truncation toward zero.
    Lean's `Int./` is Euclidean division (floor), which rounds negative
    results one further away from zero.  We correct by negating the
    truncation of the absolute product. -/
def q16_mul (a b : Int) : Int :=
  let prod := a * b
  if prod ≥ 0 then prod / SCALE else -((-prod) / SCALE)

def q16_add (a b : Int) : Int := a + b

def q16_sub (a b : Int) : Int := a - b

/-- Q16.16 division with truncation toward zero.  Returns `none` when
    divisor is zero.  The numerator `num = ft − Y0` in `intermittency`
    can be negative (Hermite spline dips below Y0 near the laminar exit),
    requiring the same truncation correction as `q16_mul`. -/
def q16_div (a b : Int) : Option Int :=
  if b = 0 then none
  else if a ≥ 0 then some ((a * SCALE) / b)
  else some (-(((-a) * SCALE) / b))

-- ============================================================================
-- Normalized variable t = (Re − 2300) / 1700, as Q16.16
-- ============================================================================

def normalizedT (re : Int) : Option Int :=
  if re < RE_LAMINAR then some 0
  else if re > RE_TURBULENT then some SCALE
  else q16_div (re - RE_LAMINAR) H_INTERVAL

-- ============================================================================
-- Hermite basis functions (all operate on Q16.16 t ∈ [0, SCALE])
-- ============================================================================

/-- Basis function h00(t) = (1 − t)²(1 + 2t) = 1 − 3t² + 2t³ -/
def h00 (t : Int) : Int :=
  let t2 := q16_mul t t
  let t3 := q16_mul t2 t
  let term3 := q16_mul (3 * SCALE) t2
  let term2 := q16_mul (2 * SCALE) t3
  q16_sub (q16_add SCALE term2) term3

/-- Basis function h01(t) = t²(3 − 2t) = 3t² − 2t³ -/
def h01 (t : Int) : Int :=
  let t2 := q16_mul t t
  let t3 := q16_mul t2 t
  let term3 := q16_mul (3 * SCALE) t2
  let term2 := q16_mul (2 * SCALE) t3
  q16_sub term3 term2

/-- Basis function h10(t) = (1 − t)²·t -/
def h10 (t : Int) : Int :=
  let t1m := q16_sub SCALE t
  let t1m2 := q16_mul t1m t1m
  q16_mul t1m2 t

/-- Basis function h11(t) = t²·(1 − t) -/
def h11 (t : Int) : Int :=
  let t2 := q16_mul t t
  let t1m := q16_sub SCALE t
  q16_mul t2 t1m

-- ============================================================================
-- Hermite spline evaluation
-- ============================================================================

/--
  H(t) = h00(t)·y₀ + h01(t)·y₁ + h10(t)·(h·m₀) − h11(t)·(h·m₁)

  The minus sign on h11·(h·m₁) compensates the algebraic sign of our `h11`
  definition relative to the conventional Hermite basis.  Standard Hermite
  uses h11_std(t) = t²(t−1) = −t²(1−t) = −h11_code, so the formula is
  equivalent to the textbook Hermite interpolation polynomial.

  Returns the friction factor f as a Q16.16 value at normalized position t.
-/
def hermiteSpline (t : Int) : Int :=
  let h00_y0 := q16_mul (h00 t) Y0
  let h01_y1 := q16_mul (h01 t) Y1
  let h10_s0 := q16_mul (h10 t) H_M0
  let h11_s1 := q16_mul (h11 t) H_M1
  q16_add (q16_add h00_y0 h01_y1) (q16_sub h10_s0 h11_s1)

/--
  Compute the friction factor f at a given Reynolds number.
  For Re < 2300: laminar (64/Re) approximated in Q16.16
  For 2300 ≤ Re ≤ 4000: Hermite spline bridge
  For Re > 4000: turbulent constant approximation

  Returns `none` for Re = 0 (division by zero in the laminar branch).
-/
def frictionFactor (re : Int) : Option Int :=
  if re < RE_LAMINAR then
    -- Laminar: f = 64/Re  (Hagen-Poiseuille) in Q16.16: (64 * SCALE) / Re
    -- q16_div multiplies numerator by SCALE internally, so pass 64
    q16_div 64 re
  else if re > RE_TURBULENT then
    -- Turbulent: constant approximation at Re=4000
    some Y1
  else
    match normalizedT re with
    | some t => some (hermiteSpline t)
    | none => none

-- ============================================================================
-- Intermittency factor γ ∈ [0, SCALE] (Q16.16)
-- γ = 0 fully laminar, γ = SCALE fully turbulent
-- ============================================================================

def intermittency (re : Int) : Option Int :=
  match normalizedT re with
  | none => none
  | some t =>
    let ft := hermiteSpline t
    let num := q16_sub ft Y0
    let den := q16_sub Y1 Y0
    q16_div num den

-- ============================================================================
-- Reynolds regime classification
-- ============================================================================

inductive Regime : Type
  | laminar
  | transitional
  | turbulent
  deriving Repr, DecidableEq

def classifyRegime (re : Int) : Regime :=
  if re < RE_LAMINAR then .laminar
  else if re > RE_TURBULENT then .turbulent
  else .transitional

-- ============================================================================
-- 16D controller gate: maps Reynolds regime to controller action
-- ============================================================================

inductive GateAction : Type
  | admit
  | braid
  | refine
  | patch
  | loopback
  deriving Repr, DecidableEq

def controllerGate (re : Int) : GateAction :=
  match classifyRegime re with
  | .laminar => .admit
  | .transitional => .braid
  | .turbulent => .patch

-- ============================================================================
-- Verification theorems (boundary conditions and correctness)
-- ============================================================================

-- Hermite boundary values ------------------------------------------------

/-- The Hermite spline at t=0 equals Y0 (laminar boundary). -/
theorem hermite_spline_at_zero : hermiteSpline 0 = Y0 := by
  native_decide

/-- The Hermite spline at t=SCALE equals Y1 (turbulent boundary). -/
theorem hermite_spline_at_one : hermiteSpline SCALE = Y1 := by
  native_decide

-- Hermite basis function values at t=0 -----------------------------------

theorem h00_at_zero : h00 0 = SCALE := by native_decide
theorem h01_at_zero : h01 0 = 0 := by native_decide
theorem h10_at_zero : h10 0 = 0 := by native_decide
theorem h11_at_zero : h11 0 = 0 := by native_decide

-- Hermite basis function values at t=SCALE (i.e. t=1) --------------------

theorem h00_at_one : h00 SCALE = 0 := by native_decide
theorem h01_at_one : h01 SCALE = SCALE := by native_decide
theorem h10_at_one : h10 SCALE = 0 := by native_decide
theorem h11_at_one : h11 SCALE = 0 := by native_decide

-- Intermittency boundary values ------------------------------------------

/-- `intermittency` returns `some` at the laminar exit. -/
theorem intermittency_at_laminar_exit_some :
  (intermittency RE_LAMINAR).isSome := by
  native_decide

/-- `intermittency` returns 0 at the laminar exit. -/
theorem intermittency_at_laminar_exit :
  (intermittency RE_LAMINAR).get! = 0 := by
  native_decide

/-- `intermittency` returns `some` at the turbulent entry. -/
theorem intermittency_at_turbulent_entry_some :
  (intermittency RE_TURBULENT).isSome := by
  native_decide

/-- Intermittency is SCALE at turbulent entry (fully turbulent). -/
theorem intermittency_at_turbulent_entry :
  (intermittency RE_TURBULENT).get! = SCALE := by
  native_decide

/-- Intermittency at the midpoint (Re=3150) is strictly between 0 and SCALE. -/
theorem intermittency_midpoint_in_range :
  let v := (intermittency 3150).get!
  0 < v ∧ v < SCALE := by
  native_decide

-- Friction factor boundary values ----------------------------------------

/-- `frictionFactor` returns `some` at the laminar exit. -/
theorem friction_at_laminar_exit_some :
  (frictionFactor RE_LAMINAR).isSome := by
  native_decide

theorem friction_at_laminar_exit :
  (frictionFactor RE_LAMINAR).get! = Y0 := by
  native_decide

/-- `frictionFactor` returns `some` at the turbulent entry. -/
theorem friction_at_turbulent_entry_some :
  (frictionFactor RE_TURBULENT).isSome := by
  native_decide

theorem friction_at_turbulent_entry :
  (frictionFactor RE_TURBULENT).get! = Y1 := by
  native_decide

-- Regime classification --------------------------------------------------

theorem laminar_classification : classifyRegime 1000 = Regime.laminar := by
  native_decide

theorem transitional_classification : classifyRegime 3000 = Regime.transitional := by
  native_decide

theorem turbulent_classification : classifyRegime 5000 = Regime.turbulent := by
  native_decide

-- Controller gate --------------------------------------------------------

theorem laminar_gate : controllerGate 1000 = GateAction.admit := by
  native_decide

theorem transitional_gate : controllerGate 3000 = GateAction.braid := by
  native_decide

theorem turbulent_gate : controllerGate 5000 = GateAction.patch := by
  native_decide

-- ============================================================================
-- Executable witnesses (computational receipts)
-- ============================================================================

#eval! Y0
#eval! Y1
#eval! hermiteSpline 0
#eval! hermiteSpline SCALE
#eval! (intermittency RE_LAMINAR).get!
#eval! (intermittency RE_TURBULENT).get!
#eval! (intermittency 3150).get!
#eval! (frictionFactor 2300).get!
#eval! (frictionFactor 4000).get!
#eval! (frictionFactor 1000).get!

end Semantics.Physics.UniversalBridge
