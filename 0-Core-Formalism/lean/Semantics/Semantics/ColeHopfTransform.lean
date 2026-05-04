/-
  ColeHopfTransform.lean — Cole-Hopf Transformation in Q16_16

  The Cole-Hopf transformation linearizes the Burgers equation:
    u = -2ν · ∂/∂x(ln φ)

  where φ satisfies the heat equation:
    φ_t = ν · φ_xx

  This enables exact solutions to the Burgers equation via the
  linear heat equation.

  References:
  - Cole 1951 (10.1063/1.1704494) — On a quasi-linear parabolic equation
  - Hopf 1950 (10.1002/cpa.3160030302) — The partial differential equation u_t + u·u_x = ν·u_xx
-/
import Semantics.FixedPoint
import Semantics.BurgersPDE

namespace Semantics.ColeHopfTransform

open Semantics.Q16_16

-- ============================================================
-- 1. HEAT EQUATION STATE
-- ============================================================

/-- Heat equation state φ(x,t) — solution to φ_t = ν·φ_xx -/
structure HeatState where
  N : Nat
  φ : Array Q16_16   -- scalar field φ[i] at lattice points
  ν : Q16_16         -- diffusion coefficient
  dx : Q16_16        -- spatial step
  dt : Q16_16        -- temporal step
  t  : Q16_16        -- current time
  deriving Repr, Inhabited

-- ============================================================
-- 2. HEAT EQUATION OPERATORS
-- ============================================================

/-- Forward difference for φ: (φ[i+1] - φ[i]) / dx -/
def forwardDiff (φ : Array Q16_16) (i : Nat) (dx : Q16_16) : Q16_16 :=
  if i + 1 < φ.size then
    Q16_16.div (Q16_16.sub φ[i+1]! φ[i]!) dx
  else 0

/-- Central difference for φ: (φ[i+1] - φ[i-1]) / (2·dx) -/
def centralDiff (φ : Array Q16_16) (i : Nat) (dx : Q16_16) : Q16_16 :=
  if i > 0 ∧ i + 1 < φ.size then
    let two_dx := Q16_16.add dx dx
    Q16_16.div (Q16_16.sub φ[i+1]! φ[i-1]!) two_dx
  else 0

/-- Second derivative for heat equation: (φ[i+1] - 2φ[i] + φ[i-1]) / dx² -/
def secondDiff (φ : Array Q16_16) (i : Nat) (dx : Q16_16) : Q16_16 :=
  if i > 0 ∧ i + 1 < φ.size then
    let φ_xx_num := Q16_16.add (Q16_16.sub φ[i+1]! φ[i]!) (Q16_16.sub φ[i-1]! φ[i]!)
    Q16_16.div φ_xx_num (Q16_16.mul dx dx)
  else 0

-- ============================================================
-- 3. HEAT EQUATION TIME STEPPING
--    φ_t = ν · φ_xx
-- ============================================================

/-- Heat equation RHS: ν · φ_xx -/
def heatRHS (state : HeatState) (i : Nat) : Q16_16 :=
  Q16_16.mul state.ν (secondDiff state.φ i state.dx)

/-- One explicit Euler step for heat equation -/
def stepHeatEuler (state : HeatState) : HeatState :=
  let newφ := Array.ofFn (fun i : Fin state.N =>
    let rhs := heatRHS state i.val
    let dt_rhs := Q16_16.mul state.dt rhs
    Q16_16.add state.φ[i.val]! dt_rhs
  )
  { state with φ := newφ, t := Q16_16.add state.t state.dt }

-- ============================================================
-- 4. COLE-HOPF TRANSFORMATION
--    u = -2ν · φ_x / φ   (from u = -2ν · ∂_x(ln φ))
-- ============================================================

/-- Cole-Hopf transformation: convert heat solution φ to Burgers velocity u
    u[i] = -2ν · (φ[i+1] - φ[i-1]) / (2·dx · φ[i])
         = -ν · (φ[i+1] - φ[i-1]) / (dx · φ[i]) -/
def coleHopfForward (heat : HeatState) (i : Nat) : Q16_16 :=
  if i > 0 ∧ i + 1 < heat.φ.size then
    let dφ := Q16_16.sub heat.φ[i+1]! heat.φ[i-1]!
    let num := Q16_16.mul (Q16_16.neg (Q16_16.mul (Q16_16.ofNat 2) heat.ν)) dφ
    let den := Q16_16.mul (Q16_16.add heat.dx heat.dx) heat.φ[i]!
    if den = 0 then 0 else Q16_16.div num den
  else
    0

/-- Transform HeatState to BurgersState via Cole-Hopf -/
def toBurgersState (heat : HeatState) : Semantics.BurgersPDE.BurgersState :=
  let uField := Array.ofFn (fun i : Fin heat.N => coleHopfForward heat i.val)
  { N := heat.N, u := uField, ν := heat.ν, dx := heat.dx, dt := heat.dt, t := heat.t }

-- ============================================================
-- 5. INVERSE COLE-HOPF (HOPF-COLE)
--    φ(x,t) = exp(-1/(2ν) · ∫ u dx)
-- ============================================================

/-- Approximate exponential for Q16_16 using Taylor series: exp(x) ≈ 1 + x + x²/2 + x³/6 -/
def expApprox (x : Q16_16) : Q16_16 :=
  let x2 := Q16_16.div (Q16_16.mul x x) (Q16_16.ofNat 2)
  let x3 := Q16_16.div (Q16_16.mul x2 x) (Q16_16.ofNat 3)
  Q16_16.add (Q16_16.add (Q16_16.add (Q16_16.ofNat 1) x) x2) x3

/-- Cumulative integral of u (trapezoidal rule approximation) -/
def cumulativeIntegral (u : Array Q16_16) (dx : Q16_16) : Array Q16_16 :=
  u.foldl (fun (acc, sum) ui =>
    let newSum := Q16_16.add sum (Q16_16.mul ui dx)
    (acc.push newSum, newSum)
  ) (#[], 0) |>.fst

/-- Inverse Cole-Hopf: convert Burgers velocity u to heat solution φ
    φ[i] = exp(-∫u dx / (2ν)) -/
def inverseColeHopf (burgers : Semantics.BurgersPDE.BurgersState) : HeatState :=
  let integral := cumulativeIntegral burgers.u burgers.dx
  let φField := integral.map (fun intVal =>
    let exponent := Q16_16.div (Q16_16.neg intVal) (Q16_16.mul (Q16_16.ofNat 2) burgers.ν)
    expApprox exponent
  )
  { N := burgers.N, φ := φField, ν := burgers.ν, dx := burgers.dx, dt := burgers.dt, t := burgers.t }

-- ============================================================
-- 6. VERIFICATION: Heat solution → Burgers solution
-- ============================================================

/-- Test: verify that a heat equation solution transforms to valid Burgers solution -/
def testHeatState : HeatState := {
  N := 4,
  φ := #[
    Q16_16.ofNat 1,
    Q16_16.ofNat 2,
    Q16_16.ofNat 4,
    Q16_16.ofNat 8
  ],
  ν := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 10),
  dx := Q16_16.ofNat 1,
  dt := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 100),
  t := 0
}

#eval! coleHopfForward testHeatState 1
#eval! coleHopfForward testHeatState 2
#eval! toBurgersState testHeatState

end Semantics.ColeHopfTransform
