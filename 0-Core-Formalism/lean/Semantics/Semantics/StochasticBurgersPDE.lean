/-
  StochasticBurgersPDE.lean — Stochastic Burgers Equation with Q16_16

  u_t + u·u_x = ν·u_xx + σ·ζ(x,t)

  where ζ is discretized space-time white noise (approximated by
  pseudo-random perturbation with intensity σ at each lattice point).

  Reference:
  - Hairer 2010 (10.1007/s00440-011-0392-1) — Rough Burgers
  - Bertini-Giacomin 1997 (10.1007/s002200050044) — Stochastic Burgers
-/
import Semantics.FixedPoint
import Semantics.BurgersPDE

namespace Semantics.StochasticBurgersPDE

open Semantics.Q16_16

-- ============================================================
-- 1. STOCHASTIC STATE (extends BurgersState with noise)
-- ============================================================

/-- Discrete stochastic Burgers state: deterministic field + noise params -/
structure StochasticBurgersState where
  base : Semantics.BurgersPDE.BurgersState  -- underlying deterministic state
  σ : Q16_16                                -- noise intensity
  ξ : Array Q16_16                          -- last-drawn noise realization ξ[i]
  seed : Nat                                -- pseudo-random seed for reproducibility
  deriving Repr, Inhabited

-- ============================================================
-- 2. PSEUDO-RANDOM NOISE GENERATOR (Q16_16 LCG)
-- ============================================================

/-- Linear congruential generator: returns next seed and a Q16_16 in [-1,1] -/
def lcgNext (seed : Nat) : (Nat × Q16_16) :=
  let a := 1103515245
  let c := 12345
  let m := 4294967296
  let next := (a * seed + c) % m
  let signed := if next >= 2147483648 then Int.ofNat next - 4294967296 else Int.ofNat next
  let scaled := (signed * 65536) / 32768
  let rawScaled := if scaled > 2147483647 then 2147483647 else if scaled < -2147483648 then -2147483648 else scaled
  let qval := Q16_16.ofInt rawScaled
  (next, qval)

/-- Recursive helper: accumulate N noise samples -/
def generateNoiseAux (σ : Q16_16) (seed : Nat) (n : Nat) (acc : Array Q16_16) : (Nat × Array Q16_16) :=
  match n with
  | 0 => (seed, acc)
  | n+1 =>
    let (s, q) := lcgNext seed
    let scaled := Q16_16.mul σ q
    generateNoiseAux σ s n (acc.push scaled)

/-- Generate N noise samples with intensity σ (white noise in Q16_16) -/
def generateNoise (state : StochasticBurgersState) : (StochasticBurgersState × Array Q16_16) :=
  let (newSeed, arr) := generateNoiseAux state.σ state.seed state.base.N (Array.mkEmpty state.base.N)
  ({ state with seed := newSeed, ξ := arr }, arr)

-- ============================================================
-- 3. STOCHASTIC BURGERS RHS
--    u_t = -u·u_x + ν·u_xx + σ·ζ
-- ============================================================

/-- Stochastic Burgers RHS at lattice point i -/
def stochasticBurgersRHS (state : StochasticBurgersState) (i : Nat) : Q16_16 :=
  let detRHS := Semantics.BurgersPDE.burgersRHS state.base i
  let noise := state.ξ[i]!  -- noise realization at this point
  Q16_16.add detRHS noise

-- ============================================================
-- 4. TIME INTEGRATION (Euler-Maruyama)
-- ============================================================

/-- One Euler-Maruyama step: draw fresh noise, then step -/
def stepEulerMaruyama (state : StochasticBurgersState) : StochasticBurgersState :=
  let (stateWithNoise, ξ) := generateNoise state
  let newU := Array.ofFn (fun i : Fin stateWithNoise.base.N =>
    let rhs := stochasticBurgersRHS stateWithNoise i.val
    let dt_rhs := Q16_16.mul stateWithNoise.base.dt rhs
    Q16_16.add stateWithNoise.base.u[i.val]! dt_rhs
  )
  let newBase := { stateWithNoise.base with u := newU, t := Q16_16.add stateWithNoise.base.t stateWithNoise.base.dt }
  { stateWithNoise with base := newBase }

/-- Run n Euler-Maruyama steps -/
def runStepsMaruyama (state : StochasticBurgersState) (n : Nat) : StochasticBurgersState :=
  match n with
  | 0 => state
  | n+1 => runStepsMaruyama (stepEulerMaruyama state) n

-- ============================================================
-- 5. INVARIANTS & DIAGNOSTICS
-- ============================================================

/-- Energy of the underlying deterministic state -/
def kineticEnergy (state : StochasticBurgersState) : Q16_16 :=
  Semantics.BurgersPDE.kineticEnergy state.base

/-- Noise energy: Σ ξ[i]² / 2 -/
def noiseEnergy (state : StochasticBurgersState) : Q16_16 :=
  let sumSq := state.ξ.foldl (fun acc ξi => Q16_16.add acc (Q16_16.mul ξi ξi)) 0
  Q16_16.div sumSq (Q16_16.ofNat 2)

/-- Total energy: deterministic + stochastic contributions -/
def totalEnergy (state : StochasticBurgersState) : Q16_16 :=
  Q16_16.add (kineticEnergy state) (noiseEnergy state)

/-- Invariant string for bind topology -/
def stochasticInvariant (state : StochasticBurgersState) : String :=
  "E_kin:" ++ reprStr (kineticEnergy state).val ++ ",E_noise:" ++ reprStr (noiseEnergy state).val ++ ",E_tot:" ++ reprStr (totalEnergy state).val ++ ",t:" ++ reprStr state.base.t.val

-- ============================================================
-- 6. EVALUATION TESTS
-- ============================================================

def testStochasticState : StochasticBurgersState := {
  base := Semantics.BurgersPDE.testState,
  σ := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 10),  -- σ = 0.1
  ξ := #[],
  seed := 42
}

#eval! kineticEnergy testStochasticState
#eval! let (s, _) := generateNoise testStochasticState; noiseEnergy s
#eval! let (s, _) := generateNoise testStochasticState; totalEnergy s

end Semantics.StochasticBurgersPDE
