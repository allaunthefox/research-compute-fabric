/-
  KdVBurgersPDE.lean — Compound KdV-Burgers Equation in Q16_16

  u_t + α·u·u_x + β·u_xx + γ·u_xxx = 0

  Combines nonlinear advection (α), viscous diffusion (β), and
  third-order dispersion (γ). Captures both shock formation
  and wave-breaking phenomena.

  Reference:
  - Wang 1996 (10.1016/0375-9601(96)00103-x) — Exact solutions for compound KdV-Burgers
  - Feng 2002 (10.1088/0305-4470/35/2/312) — First-integral method
-/
import Semantics.FixedPoint
import Semantics.BurgersPDE

namespace Semantics.KdVBurgersPDE

open Semantics.Q16_16

-- ============================================================
-- 1. KdV-BURGERS STATE
-- ============================================================

/-- Discrete KdV-Burgers state with dispersion coefficient γ -/
structure KdVBurgersState where
  base : Semantics.BurgersPDE.BurgersState  -- N, u, ν, dx, dt, t
  α : Q16_16                                -- nonlinear coefficient (advection strength)
  β : Q16_16                                -- viscous coefficient (diffusion)
  γ : Q16_16                                -- dispersive coefficient (KdV term)
  deriving Repr, Inhabited

-- ============================================================
-- 2. THIRD-ORDER DIFFERENCE OPERATOR
-- ============================================================

/-- Third derivative approximation: (u[i+2] - 2u[i+1] + 2u[i-1] - u[i-2]) / (2·dx³) -/
def thirdDiff (u : Array Q16_16) (i : Nat) (dx : Q16_16) : Q16_16 :=
  if h1 : i > 1 then
    if h2 : i + 2 < u.size then
      let uim2 := u[i-2]!
      let uim1 := u[i-1]!
      let uip1 := u[i+1]!
      let uip2 := u[i+2]!
      let dx3 := Q16_16.mul (Q16_16.mul dx dx) dx
      let two_dx3 := Q16_16.mul (Q16_16.ofNat 2) dx3
      let num := Q16_16.sub (Q16_16.sub uip2 (Q16_16.mul (Q16_16.ofNat 2) uip1)) (Q16_16.sub (Q16_16.mul (Q16_16.ofNat 2) uim1) uim2)
      Q16_16.div num two_dx3
    else
      0
  else
    0

-- ============================================================
-- 3. KdV-BURGERS EQUATION RIGHT-HAND SIDE
--    u_t = -(α·u·u_x + β·u_xx + γ·u_xxx)
-- ============================================================

/-- KdV-Burgers RHS at lattice point i -/
def kdvBurgersRHS (state : KdVBurgersState) (i : Nat) : Q16_16 :=
  let ui := state.base.u[i]!
  let ux := Semantics.BurgersPDE.centralDiff state.base.u i state.base.dx
  let uxx := Semantics.BurgersPDE.secondDiff state.base.u i state.base.dx
  let uxxx := thirdDiff state.base.u i state.base.dx
  let advection := Q16_16.mul (Q16_16.mul state.α ui) ux    -- α·u·u_x
  let diffusion := Q16_16.mul state.β uxx                    -- β·u_xx
  let dispersion := Q16_16.mul state.γ uxxx                 -- γ·u_xxx
  let sum := Q16_16.add (Q16_16.add advection diffusion) dispersion
  Q16_16.neg sum                                              -- -(α·u·u_x + β·u_xx + γ·u_xxx)

-- ============================================================
-- 4. TIME INTEGRATION (Explicit Euler)
-- ============================================================

/-- One explicit Euler step for KdV-Burgers -/
def stepEuler (state : KdVBurgersState) : KdVBurgersState :=
  let newU := Array.ofFn (fun i : Fin state.base.N =>
    let rhs := kdvBurgersRHS state i.val
    let dt_rhs := Q16_16.mul state.base.dt rhs
    Q16_16.add state.base.u[i.val]! dt_rhs
  )
  let newBase := { state.base with u := newU, t := Q16_16.add state.base.t state.base.dt }
  { state with base := newBase }

/-- Run n explicit Euler steps -/
def runSteps (state : KdVBurgersState) (n : Nat) : KdVBurgersState :=
  match n with
  | 0 => state
  | n+1 => runSteps (stepEuler state) n

-- ============================================================
-- 5. INVARIANTS & DIAGNOSTICS
-- ============================================================

/-- Kinetic energy (same as base Burgers) -/
def kineticEnergy (state : KdVBurgersState) : Q16_16 :=
  Semantics.BurgersPDE.kineticEnergy state.base

/-- Maximum absolute velocity -/
def maxVelocity (state : KdVBurgersState) : Q16_16 :=
  Semantics.BurgersPDE.maxVelocity state.base

/-- Dispersion-to-dissipation ratio (γ / β) — indicates soliton vs shock regime -/
def dispersionRatio (state : KdVBurgersState) : Q16_16 :=
  if state.β = 0 then Q16_16.maxVal else Q16_16.div state.γ state.β

/-- Invariant string for bind topology -/
def kdvBurgersInvariant (state : KdVBurgersState) : String :=
  "E:" ++ reprStr (kineticEnergy state).val ++ ",|u|max:" ++ reprStr (maxVelocity state).val ++ ",γ/β:" ++ reprStr (dispersionRatio state).val ++ ",t:" ++ reprStr state.base.t.val

-- ============================================================
-- 6. EVALUATION TESTS
-- ============================================================

def testKdVState : KdVBurgersState := {
  base := Semantics.BurgersPDE.testState,
  α := Q16_16.ofNat 1,     -- α = 1
  β := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 10),  -- β = 0.1
  γ := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 100)   -- γ = 0.01 (weak dispersion)
}

#eval! kineticEnergy testKdVState
#eval! maxVelocity testKdVState
#eval! dispersionRatio testKdVState
#eval! kdvBurgersRHS testKdVState 2

end Semantics.KdVBurgersPDE
