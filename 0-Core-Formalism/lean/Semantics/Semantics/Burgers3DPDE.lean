/-
  Burgers3DPDE.lean — 3D Coupled Burgers Equation System in Q16_16

  u_t + u·u_x + v·u_y + w·u_z = ν·(u_xx + u_yy + u_zz)
  v_t + u·v_x + v·v_y + w·v_z = ν·(v_xx + v_yy + v_zz)
  w_t + u·w_x + v·w_y + w·w_z = ν·(w_xx + w_yy + w_zz)
-/
import Semantics.FixedPoint
import Semantics.BurgersPDE

namespace Semantics.Burgers3DPDE
open Semantics.Q16_16

structure Burgers3DState where
  N : Nat
  M : Nat
  P : Nat
  u : Array (Array (Array Q16_16))
  v : Array (Array (Array Q16_16))
  w : Array (Array (Array Q16_16))
  ν : Q16_16
  dx : Q16_16
  dy : Q16_16
  dz : Q16_16
  dt : Q16_16
  t : Q16_16
  deriving Repr, Inhabited

def get3D (field : Array (Array (Array Q16_16))) (d r c : Nat) : Q16_16 :=
  if d < field.size then
    let plane := field[d]!
    if r < plane.size then
      let row := plane[r]!
      if c < row.size then row[c]! else 0
    else 0
  else 0

def centralDiffX (field : Array (Array (Array Q16_16))) (d r c : Nat) (dx : Q16_16) : Q16_16 :=
  if c > 0 then
    let two_dx := Q16_16.add dx dx
    Q16_16.div (Q16_16.sub (get3D field d r (c+1)) (get3D field d r (c-1))) two_dx
  else 0

def centralDiffY (field : Array (Array (Array Q16_16))) (d r c : Nat) (dy : Q16_16) : Q16_16 :=
  if r > 0 then
    let two_dy := Q16_16.add dy dy
    Q16_16.div (Q16_16.sub (get3D field d (r+1) c) (get3D field d (r-1) c)) two_dy
  else 0

def centralDiffZ (field : Array (Array (Array Q16_16))) (d r c : Nat) (dz : Q16_16) : Q16_16 :=
  if d > 0 then
    let two_dz := Q16_16.add dz dz
    Q16_16.div (Q16_16.sub (get3D field (d+1) r c) (get3D field (d-1) r c)) two_dz
  else 0

def secondDiffX (field : Array (Array (Array Q16_16))) (d r c : Nat) (dx : Q16_16) : Q16_16 :=
  if c > 0 then
    let uij := get3D field d r c
    let num := Q16_16.add (Q16_16.sub (get3D field d r (c+1)) uij) (Q16_16.sub (get3D field d r (c-1)) uij)
    Q16_16.div num (Q16_16.mul dx dx)
  else 0

def secondDiffY (field : Array (Array (Array Q16_16))) (d r c : Nat) (dy : Q16_16) : Q16_16 :=
  if r > 0 then
    let uij := get3D field d r c
    let num := Q16_16.add (Q16_16.sub (get3D field d (r+1) c) uij) (Q16_16.sub (get3D field d (r-1) c) uij)
    Q16_16.div num (Q16_16.mul dy dy)
  else 0

def secondDiffZ (field : Array (Array (Array Q16_16))) (d r c : Nat) (dz : Q16_16) : Q16_16 :=
  if d > 0 then
    let uij := get3D field d r c
    let num := Q16_16.add (Q16_16.sub (get3D field (d+1) r c) uij) (Q16_16.sub (get3D field (d-1) r c) uij)
    Q16_16.div num (Q16_16.mul dz dz)
  else 0

def burgersU_RHS (s : Burgers3DState) (d r c : Nat) : Q16_16 :=
  let u := get3D s.u d r c; let v := get3D s.v d r c; let w := get3D s.w d r c
  let adv := Q16_16.add (Q16_16.add (Q16_16.mul u (centralDiffX s.u d r c s.dx)) (Q16_16.mul v (centralDiffY s.u d r c s.dy))) (Q16_16.mul w (centralDiffZ s.u d r c s.dz))
  let diff := Q16_16.mul s.ν (Q16_16.add (Q16_16.add (secondDiffX s.u d r c s.dx) (secondDiffY s.u d r c s.dy)) (secondDiffZ s.u d r c s.dz))
  Q16_16.sub diff adv

def burgersV_RHS (s : Burgers3DState) (d r c : Nat) : Q16_16 :=
  let u := get3D s.u d r c; let v := get3D s.v d r c; let w := get3D s.w d r c
  let adv := Q16_16.add (Q16_16.add (Q16_16.mul u (centralDiffX s.v d r c s.dx)) (Q16_16.mul v (centralDiffY s.v d r c s.dy))) (Q16_16.mul w (centralDiffZ s.v d r c s.dz))
  let diff := Q16_16.mul s.ν (Q16_16.add (Q16_16.add (secondDiffX s.v d r c s.dx) (secondDiffY s.v d r c s.dy)) (secondDiffZ s.v d r c s.dz))
  Q16_16.sub diff adv

def burgersW_RHS (s : Burgers3DState) (d r c : Nat) : Q16_16 :=
  let u := get3D s.u d r c; let v := get3D s.v d r c; let w := get3D s.w d r c
  let adv := Q16_16.add (Q16_16.add (Q16_16.mul u (centralDiffX s.w d r c s.dx)) (Q16_16.mul v (centralDiffY s.w d r c s.dy))) (Q16_16.mul w (centralDiffZ s.w d r c s.dz))
  let diff := Q16_16.mul s.ν (Q16_16.add (Q16_16.add (secondDiffX s.w d r c s.dx) (secondDiffY s.w d r c s.dy)) (secondDiffZ s.w d r c s.dz))
  Q16_16.sub diff adv

def stepEuler (s : Burgers3DState) : Burgers3DState :=
  let newU := Array.ofFn (fun d : Fin s.N => Array.ofFn (fun r : Fin s.M => Array.ofFn (fun c : Fin s.P =>
    Q16_16.add (get3D s.u d.val r.val c.val) (Q16_16.mul s.dt (burgersU_RHS s d.val r.val c.val)))))
  let newV := Array.ofFn (fun d : Fin s.N => Array.ofFn (fun r : Fin s.M => Array.ofFn (fun c : Fin s.P =>
    Q16_16.add (get3D s.v d.val r.val c.val) (Q16_16.mul s.dt (burgersV_RHS s d.val r.val c.val)))))
  let newW := Array.ofFn (fun d : Fin s.N => Array.ofFn (fun r : Fin s.M => Array.ofFn (fun c : Fin s.P =>
    Q16_16.add (get3D s.w d.val r.val c.val) (Q16_16.mul s.dt (burgersW_RHS s d.val r.val c.val)))))
  { s with u := newU, v := newV, w := newW, t := Q16_16.add s.t s.dt }

def runSteps (s : Burgers3DState) (n : Nat) : Burgers3DState :=
  match n with | 0 => s | n+1 => runSteps (stepEuler s) n

def kineticEnergy (s : Burgers3DState) : Q16_16 :=
  let sumSq (f : Array (Array (Array Q16_16))) := f.foldl (fun a p => p.foldl (fun b r => r.foldl (fun c u => Q16_16.add c (Q16_16.mul u u)) b) a) 0
  Q16_16.div (Q16_16.add (Q16_16.add (sumSq s.u) (sumSq s.v)) (sumSq s.w)) (Q16_16.ofNat 2)

def burgers3DInvariant (s : Burgers3DState) : String :=
  "E:" ++ reprStr (kineticEnergy s).val ++ ",t:" ++ reprStr s.t.val

def test3DState : Burgers3DState := {
  N := 2, M := 2, P := 2,
  u := #[#[#[0,0],#[0,1]],#[#[0,0],#[0,0]]],
  v := #[#[#[0,0],#[0,1]],#[#[0,0],#[0,0]]],
  w := #[#[#[0,0],#[0,0]],#[#[0,0],#[0,0]]],
  ν := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 10),
  dx := Q16_16.ofNat 1, dy := Q16_16.ofNat 1, dz := Q16_16.ofNat 1,
  dt := Q16_16.div (Q16_16.ofNat 1) (Q16_16.ofNat 100), t := 0
}

#eval! kineticEnergy (test3DState : Burgers3DState)
#eval! burgersU_RHS (test3DState : Burgers3DState) 0 1 1

end Semantics.Burgers3DPDE
