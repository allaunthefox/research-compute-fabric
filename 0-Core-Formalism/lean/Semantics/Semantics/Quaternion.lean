import Semantics.DynamicCanal

namespace Semantics.Quaternion

open DynamicCanal

/-- 
  Quaternion: 4D Non-Commutative State for PIST (Propagated Informatic Sere Topology).
  Elements: q = w + xi + yj + zk
-/
structure Quaternion where
  w : Fix16
  x : Fix16
  y : Fix16
  z : Fix16
  deriving Repr, DecidableEq, BEq, Inhabited

namespace Quaternion

theorem ext {q1 q2 : Quaternion} (hw : q1.w = q2.w) (hx : q1.x = q2.x) (hy : q1.y = q2.y) (hz : q1.z = q2.z) : q1 = q2 := by
  cases q1; cases q2
  simp only at hw hx hy hz ⊢
  simp [hw, hx, hy, hz]

def zero : Quaternion := 
  { w := Fix16.zero, x := Fix16.zero, y := Fix16.zero, z := Fix16.zero }

def one : Quaternion := 
  { w := Fix16.one, x := Fix16.zero, y := Fix16.zero, z := Fix16.zero }

def i : Quaternion := 
  { w := Fix16.zero, x := Fix16.one, y := Fix16.zero, z := Fix16.zero }

def j : Quaternion := 
  { w := Fix16.zero, x := Fix16.zero, y := Fix16.one, z := Fix16.zero }

def k : Quaternion := 
  { w := Fix16.zero, x := Fix16.zero, y := Fix16.zero, z := Fix16.one }

def add (p q : Quaternion) : Quaternion :=
  { w := Fix16.add p.w q.w
  , x := Fix16.add p.x q.x
  , y := Fix16.add p.y q.y
  , z := Fix16.add p.z q.z }

def sub (p q : Quaternion) : Quaternion :=
  { w := Fix16.sub p.w q.w
  , x := Fix16.sub p.x q.x
  , y := Fix16.sub p.y q.y
  , z := Fix16.sub p.z q.z }

def neg (q : Quaternion) : Quaternion :=
  { w := Fix16.neg q.w, x := Fix16.neg q.x, y := Fix16.neg q.y, z := Fix16.neg q.z }

/-- 
  Hamiltonian product: standard non-commutative multiplication.
  (w1 + x1i + y1j + z1k)(w2 + x2i + y2j + z2k)
-/
def mul (p q : Quaternion) : Quaternion :=
  let w := Fix16.sub (Fix16.sub (Fix16.sub (Fix16.mul p.w q.w) (Fix16.mul p.x q.x)) (Fix16.mul p.y q.y)) (Fix16.mul p.z q.z)
  let x := Fix16.add (Fix16.add (Fix16.add (Fix16.mul p.w q.x) (Fix16.mul p.x q.w)) (Fix16.mul p.y q.z)) (Fix16.neg (Fix16.mul p.z q.y))
  let y := Fix16.add (Fix16.add (Fix16.add (Fix16.mul p.w q.y) (Fix16.neg (Fix16.mul p.x q.z))) (Fix16.mul p.y q.w)) (Fix16.mul p.z q.x)
  let z := Fix16.add (Fix16.add (Fix16.add (Fix16.mul p.w q.z) (Fix16.mul p.x q.y)) (Fix16.neg (Fix16.mul p.y q.x))) (Fix16.mul p.z q.w)
  { w := w, x := x, y := y, z := z }

/-- Dot product for Quaternions. -/
def dot (p q : Quaternion) : Fix16 :=
  Fix16.add (Fix16.mul p.w q.w) (Fix16.add (Fix16.mul p.x q.x) (Fix16.add (Fix16.mul p.y q.y) (Fix16.mul p.z q.z)))

/-- 
  Approximation of the norm: max(|w|,|x|,|y|,|z|) + (3/8)·Σothers 
  (A 4D extension of the octagonal norm).
-/
def normApprox (q : Quaternion) : Fix16 :=
  let abs_val (v : Fix16) := if v.val < 0x80000000 then v else Fix16.neg v
  let aw := abs_val q.w
  let ax := abs_val q.x
  let ay := abs_val q.y
  let az := abs_val q.z
  let m1 := if aw.val > ax.val then aw else ax
  let m2 := if ay.val > az.val then ay else az
  let hi := if m1.val > m2.val then m1 else m2
  -- Sum the others roughly
  let sum_others := Fix16.add aw (Fix16.add ax (Fix16.add ay az))
  let others := Fix16.sub sum_others hi
  let o38 := Fix16.mk ((others.val.toNat * 0x6000 / 0x10000).toUInt32)
  Fix16.add hi o38

/-- Conjugate of a Quaternion: q* = w - xi - yj - zk -/
def conj (q : Quaternion) : Quaternion :=
  { w := q.w, x := Fix16.neg q.x, y := Fix16.neg q.y, z := Fix16.neg q.z }

/-- Scalar multiplication. -/
def smul (s : Fix16) (q : Quaternion) : Quaternion :=
  { w := Fix16.mul s q.w, x := Fix16.mul s q.x, y := Fix16.mul s q.y, z := Fix16.mul s q.z }

/-- Map a color index (0-3) to a Quaternion basis vector. -/
def fromColor (c : Fin 4) : Quaternion :=
  match c.val with
  | 0 => one
  | 1 => i
  | 2 => j
  | 3 => k
  | _ => zero

end Quaternion

end Semantics.Quaternion
