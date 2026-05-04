/-
  Burgers2DPDE.lean — 2D Coupled Burgers Equation System in Q16_16

  u_t + u·u_x + v·u_y = ν·(u_xx + u_yy)
  v_t + u·v_x + v·v_y = ν·(v_xx + v_yy)

  Coupled velocity components (u,v) on a 2D lattice with
  shared kinematic viscosity ν.

  Reference:
  - Gao 2017 (10.1016/j.apm.2016.12.010) — 2D Burgers system
-/
import Semantics.FixedPoint
import Semantics.BurgersPDE

namespace Semantics.Burgers2DPDE

open Semantics.Q16_16

-- ============================================================
-- 1. 2D BURGERS STATE (u and v fields on N×M lattice)
-- ============================================================

/-- 2D velocity field with N×M points, u[row][col] and v[row][col] -/
structure Burgers2DState where
  N : Nat                                    -- rows (y-direction)
  M : Nat                                    -- cols (x-direction)
  u : Array (Array Q16_16)                   -- u-velocity field
  v : Array (Array Q16_16)                   -- v-velocity field
  ν : Q16_16                                 -- kinematic viscosity
  dx : Q16_16                                -- x spatial step
  dy : Q16_16                                -- y spatial step
  dt : Q16_16                                -- temporal step
  t  : Q16_16                                -- current time
  deriving Repr, Inhabited

-- ============================================================
-- 2. 2D FINITE DIFFERENCE OPERATORS
-- ============================================================

/-- Safe 2D array access: u[row][col] with bounds checking (returns 0 if OOB) -/
def get2D (field : Array (Array Q16_16)) (row col : Nat) : Q16_16 :=
  if h1 : row < field.size then
    let rowArr := field[row]!
    if h2 : col < rowArr.size then
      rowArr[col]!
    else
      0
  else
    0

/-- Central x-difference: (u[row][col+1] - u[row][col-1]) / (2·dx) -/
def centralDiffX (field : Array (Array Q16_16)) (row col : Nat) (dx : Q16_16) : Q16_16 :=
  if col > 0 then
    let uim1 := get2D field row (col - 1)
    let uip1 := get2D field row (col + 1)
    let two_dx := Q16_16.add dx dx
    Q16_16.div (Q16_16.sub uip1 uim1) two_dx
  else
    0

/-- Central y-difference: (u[row+1][col] - u[row-1][col]) / (2·dy) -/
def centralDiffY (field : Array (Array Q16_16)) (row col : Nat) (dy : Q16_16) : Q16_16 :=
  if row > 0 then
    let ujm1 := get2D field (row - 1) col
    let ujp1 := get2D field (row + 1) col
    let two_dy := Q16_16.add dy dy
    Q16_16.div (Q16_16.sub ujp1 ujm1) two_dy
  else
    0

/-- Second x-difference: (u[row][col+1] - 2u[row][col] + u[row][col-1]) / dx² -/
def secondDiffX (field : Array (Array Q16_16)) (row col : Nat) (dx : Q16_16) : Q16_16 :=
  if col > 0 then
    let uim1 := get2D field row (col - 1)
    let ui := get2D field row col
    let uip1 := get2D field row (col + 1)
    let dx2 := Q16_16.mul dx dx
    let num := Q16_16.add (Q16_16.sub uip1 ui) (Q16_16.sub uim1 ui)
    Q16_16.div num dx2
  else
    0

/-- Second y-difference: (u[row+1][col] - 2u[row][col] + u[row-1][col]) / dy² -/
def secondDiffY (field : Array (Array Q16_16)) (row col : Nat) (dy : Q16_16) : Q16_16 :=
  if row > 0 then
    let ujm1 := get2D field (row - 1) col
    let uij := get2D field row col
    let ujp1 := get2D field (row + 1) col
    let dy2 := Q16_16.mul dy dy
    let num := Q16_16.add (Q16_16.sub ujp1 uij) (Q16_16.sub ujm1 uij)
    Q16_16.div num dy2
  else
    0

-- ============================================================
-- 3. 2D BURGERS RHS (coupled u and v components)
-- ============================================================

/-- RHS for u-component at (row, col):
    u_t = -(u·u_x + v·u_y) + ν·(u_xx + u_yy) -/
def burgersU_RHS (state : Burgers2DState) (row col : Nat) : Q16_16 :=
  let uij := get2D state.u row col
  let vij := get2D state.v row col
  let ux := centralDiffX state.u row col state.dx
  let uy := centralDiffY state.u row col state.dy
  let uxx := secondDiffX state.u row col state.dx
  let uyy := secondDiffY state.u row col state.dy
  let advectionU := Q16_16.mul uij ux          -- u·u_x
  let advectionV := Q16_16.mul vij uy          -- v·u_y
  let diffusion := Q16_16.mul state.ν (Q16_16.add uxx uyy)  -- ν·(u_xx + u_yy)
  Q16_16.sub diffusion (Q16_16.add advectionU advectionV)

/-- RHS for v-component at (row, col):
    v_t = -(u·v_x + v·v_y) + ν·(v_xx + v_yy) -/
def burgersV_RHS (state : Burgers2DState) (row col : Nat) : Q16_16 :=
  let uij := get2D state.u row col
  let vij := get2D state.v row col
  let vx := centralDiffX state.v row col state.dx
  let vy := centralDiffY state.v row col state.dy
  let vxx := secondDiffX state.v row col state.dx
  let vyy := secondDiffY state.v row col state.dy
  let advectionU := Q16_16.mul uij vx          -- u·v_x
  let advectionV := Q16_16.mul vij vy          -- v·v_y
  let diffusion := Q16_16.mul state.ν (Q16_16.add vxx vyy)  -- ν·(v_xx + v_yy)
  Q16_16.sub diffusion (Q16_16.add advectionU advectionV)

-- ============================================================
-- 4. TIME INTEGRATION (Explicit Euler)
-- ============================================================

/-- One explicit Euler step for 2D Burgers system -/
def stepEuler (state : Burgers2DState) : Burgers2DState :=
  let newU := Array.ofFn (fun r : Fin state.N =>
    Array.ofFn (fun c : Fin state.M =>
      let rhs := burgersU_RHS state r.val c.val
      let dt_rhs := Q16_16.mul state.dt rhs
      Q16_16.add (get2D state.u r.val c.val) dt_rhs
    )
  )
  let newV := Array.ofFn (fun r : Fin state.N =>
    Array.ofFn (fun c : Fin state.M =>
      let rhs := burgersV_RHS state r.val c.val
      let dt_rhs := Q16_16.mul state.dt rhs
      Q16_16.add (get2D state.v r.val c.val) dt_rhs
    )
  )
  { state with u := newU, v := newV, t := Q16_16.add state.t state.dt }

/-- Run n explicit Euler steps -/
def runSteps (state : Burgers2DState) (n : Nat) : Burgers2DState :=
  match n with
  | 0 => state
  | n+1 => runSteps (stepEuler state) n

-- ============================================================
-- 5. INVARIANTS & DIAGNOSTICS
-- ============================================================

/-- Total kinetic energy: Σ (u² + v²) / 2 over all lattice points -/
def kineticEnergy (state : Burgers2DState) : Q16_16 :=
  let sumSq := state.u.foldl (fun acc row =>
    row.foldl (fun acc2 uij =>
      Q16_16.add acc2 (Q16_16.mul uij uij)
    ) acc
  ) 0
  let sumV := state.v.foldl (fun acc row =>
    row.foldl (fun acc2 vij =>
      Q16_16.add acc2 (Q16_16.mul vij vij)
    ) acc
  ) 0
  Q16_16.div (Q16_16.add sumSq sumV) (Q16_16.ofNat 2)

/-- Maximum absolute velocity magnitude: max √(u² + v²) -/
def maxVelocity (state : Burgers2DState) : Q16_16 :=
  let maxVal := state.u.size.fold (fun acc _ => acc) 0 -- placeholder for loop
  -- Simplified: max of |u| + |v|
  let maxU := state.u.foldl (fun acc row =>
    row.foldl (fun acc2 uij =>
      let absU := if uij < 0 then Q16_16.neg uij else uij
      if absU > acc2 then absU else acc2
    ) acc
  ) 0
  let maxV := state.v.foldl (fun acc row =>
    row.foldl (fun acc2 vij =>
      let absV := if vij < 0 then Q16_16.neg vij else vij
      if absV > acc2 then absV else acc2
    ) acc
  ) 0
  Q16_16.add maxU maxV

/-- Invariant string for bind topology -/
def burgers2DInvariant (state : Burgers2DState) : String :=
  "E:" ++ reprStr (kineticEnergy state).val ++ ",|u|max:" ++ reprStr (maxVelocity state).val ++ ",t:" ++ reprStr state.t.val

-- ============================================================
-- 6. EVALUATION TESTS
-- ============================================================

def test2DState : Burgers2DState := {
  N := 3, M := 3,
  u := #[
    #[0, 0, 0],
    #[0, Q16_16.ofNat 1, 0],   -- u peak at center
    #[0, 0, 0]
  ],
  v := #[
    #[0, 0, 0],
    #[0, Q16_16.ofNat 1, 0],   -- v peak at center
    #[0, 0, 0]
  ],
  ν := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 10),
  dx := Q16_16.ofNat 1,
  dy := Q16_16.ofNat 1,
  dt := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 100),
  t := 0
}

#eval! kineticEnergy test2DState
#eval! maxVelocity test2DState
#eval! burgersU_RHS test2DState 1 1
#eval! burgersV_RHS test2DState 1 1

end Semantics.Burgers2DPDE
