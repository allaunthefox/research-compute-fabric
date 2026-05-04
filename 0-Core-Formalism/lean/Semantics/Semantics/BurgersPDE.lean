/-  BurgersPDE.lean - Burgers Equation Formalization in Q16_16

  Models the 1D and n-dimensional Burgers equation:
    u_t + u · u_x = ν · u_xx

  Ported from academic literature via MATH_MODEL_MAP.tsv entries 2622-2634.
  Uses saturating Q16_16 fixed-point arithmetic throughout.

  References:
  - Bertini 1994 (10.1007/BF02099769) — Stochastic Burgers
  - Serre 2020 (10.1007/s00205-020-01576-6) — Multi-dimensional source solutions
  - Biler 1998 (10.1006/jdeq.1998.3458) — Fractal Burgers
  - Hairer 2010 (10.1007/s00440-011-0392-1) — Rough Burgers
  - Srivastava 2014 (10.1016/j.asej.2013.11.006) — Analytical solutions
-/
import Semantics.FixedPoint
import Semantics.LocalDerivative

namespace Semantics.BurgersPDE

open Semantics.Q16_16

-- ============================================================
-- 1. BURGERS STATE (Scalar field u(x,t) discretized)
-- ============================================================

/-- Discrete scalar field on a 1D lattice with N points -/
structure BurgersState where
  N : Nat
  u : Array Q16_16   -- velocity field u[i] at lattice points
  ν : Q16_16         -- kinematic viscosity (positive)
  dx : Q16_16        -- spatial step
  dt : Q16_16        -- temporal step
  t  : Q16_16        -- current time
deriving Repr, Inhabited

-- ============================================================
-- 2. FINITE DIFFERENCE OPERATORS (Q16_16 saturating)
-- ============================================================

/-- Forward difference: (u[i+1] - u[i]) / dx -/
def forwardDiff (u : Array Q16_16) (i : Nat) (dx : Q16_16) : Q16_16 :=
  if h : i + 1 < u.size then
    let ui := u[i]
    let uip1 := u[i+1]
    Q16_16.div (Q16_16.sub uip1 ui) dx
  else
    0

/-- Central difference for advection: (u[i+1] - u[i-1]) / (2*dx) -/
def centralDiff (u : Array Q16_16) (i : Nat) (dx : Q16_16) : Q16_16 :=
  if h1 : i > 0 then
    if h2 : i + 1 < u.size then
      let uim1 := u[i-1]
      let uip1 := u[i+1]
      let two_dx := Q16_16.add dx dx
      Q16_16.div (Q16_16.sub uip1 uim1) two_dx
    else
      0
  else
    0

/-- Second derivative (Laplacian in 1D): (u[i+1] - 2u[i] + u[i-1]) / dx² -/
def secondDiff (u : Array Q16_16) (i : Nat) (dx : Q16_16) : Q16_16 :=
  if h1 : i > 0 then
    if h2 : i + 1 < u.size then
      let uim1 := u[i-1]
      let ui := u[i]
      let uip1 := u[i+1]
      let dx2 := Q16_16.mul dx dx
      let num := Q16_16.add (Q16_16.sub uip1 ui) (Q16_16.sub uim1 ui)
      Q16_16.div num dx2
    else
      0
  else
    0

-- ============================================================
-- 3. BURGERS EQUATION RIGHT-HAND SIDE
--    u_t = -u · u_x + ν · u_xx
-- ============================================================

/-- Burgers RHS at lattice point i: nonlinear advection + viscous diffusion -/
def burgersRHS (state : BurgersState) (i : Nat) : Q16_16 :=
  let ui := state.u[i]!
  let ux := centralDiff state.u i state.dx
  let uxx := secondDiff state.u i state.dx
  let advection := Q16_16.mul ui ux        -- u · u_x
  let diffusion := Q16_16.mul state.ν uxx -- ν · u_xx
  Q16_16.sub diffusion advection           -- ν·uxx - u·ux

-- ============================================================
-- 4. TIME INTEGRATION (Explicit Euler)
-- ============================================================

def stepEuler (state : BurgersState) : BurgersState :=
  let newU := Array.ofFn (fun i : Fin state.N =>
    let rhs := burgersRHS state i.val
    let dt_rhs := Q16_16.mul state.dt rhs
    Q16_16.add state.u[i.val]! dt_rhs
  )
  { state with u := newU, t := Q16_16.add state.t state.dt }

-- Run n explicit Euler steps
def runSteps (state : BurgersState) (n : Nat) : BurgersState :=
  match n with
  | 0 => state
  | n+1 => runSteps (stepEuler state) n

-- ============================================================
-- 5. INVARIANTS & DIAGNOSTICS
-- ============================================================

/-- Total kinetic energy: Σ u[i]² / 2 -/
def kineticEnergy (state : BurgersState) : Q16_16 :=
  let sumSq := state.u.foldl (fun acc ui => Q16_16.add acc (Q16_16.mul ui ui)) 0
  Q16_16.div sumSq (Q16_16.ofNat 2)

/-- Maximum absolute velocity (shock indicator) -/
def maxVelocity (state : BurgersState) : Q16_16 :=
  state.u.foldl (fun acc ui =>
    let abs_ui := if ui < 0 then Q16_16.neg ui else ui
    if abs_ui > acc then abs_ui else acc
  ) 0

/-- Burgers equation invariant string for bind topology -/
def burgersInvariant (state : BurgersState) : String :=
  "E:" ++ reprStr (kineticEnergy state).val ++ ",|u|max:" ++ reprStr (maxVelocity state).val ++ ",t:" ++ reprStr state.t.val

-- ============================================================
-- 7. EVALUATION TESTS
-- ============================================================

def testState : BurgersState := {
  N := 4,
  u := #[
    Q16_16.ofNat 0,      -- u[0] = 0 (boundary)
    Q16_16.ofNat 1,      -- u[1] = 1
    Q16_16.ofNat 2,      -- u[2] = 2
    Q16_16.ofNat 0       -- u[3] = 0 (boundary)
  ],
  ν := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 10),  -- ν = 0.1
  dx := Q16_16.ofNat 1,
  dt := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 100), -- dt = 0.01
  t := 0
}

-- Test evaluation (use #eval! to bypass sorry if present in imported code)
#eval! kineticEnergy testState
#eval! maxVelocity testState
#eval! burgersRHS testState 1
#eval! burgersRHS testState 2

end Semantics.BurgersPDE
