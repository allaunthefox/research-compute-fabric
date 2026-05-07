import Init

inductive V4 where
  | e | a | b | c
  deriving DecidableEq, Repr, Inhabited

namespace V4

def mul : V4 → V4 → V4
  | .e, g => g
  | g, .e => g
  | .a, .a => .e
  | .b, .b => .e
  | .c, .c => .e
  | .a, .b => .c
  | .b, .a => .c
  | .a, .c => .b
  | .c, .a => .b
  | .b, .c => .a
  | .c, .b => .a

instance : Mul V4 := ⟨mul⟩
def one : V4 := .e
instance : One V4 := ⟨one⟩

theorem self_inverse (g : V4) : g * g = .e := by
  cases g <;> rfl

theorem commutative (g h : V4) : g * h = h * g := by
  cases g <;> cases h <;> rfl

def cayley_dist (g : V4) : Nat :=
  match g with
  | .e => 0
  | .a | .b => 1
  | .c => 2

theorem triangle (g h : V4) : cayley_dist (g * h) ≤ cayley_dist g + cayley_dist h := by
  cases g <;> cases h <;> native_decide

def pist_mass (k t : Nat) : Nat := t * ((2 * k + 1) - t)

theorem mass_preserved_0_0 : pist_mass 0 0 = pist_mass 0 (2*0+1-0) := by native_decide
theorem mass_preserved_0_1 : pist_mass 0 1 = pist_mass 0 (2*0+1-1) := by native_decide
theorem mass_preserved_1_0 : pist_mass 1 0 = pist_mass 1 (2*1+1-0) := by native_decide
theorem mass_preserved_1_1 : pist_mass 1 1 = pist_mass 1 (2*1+1-1) := by native_decide
theorem mass_preserved_1_2 : pist_mass 1 2 = pist_mass 1 (2*1+1-2) := by native_decide
theorem mass_preserved_1_3 : pist_mass 1 3 = pist_mass 1 (2*1+1-3) := by native_decide
theorem mass_preserved_2_0 : pist_mass 2 0 = pist_mass 2 (2*2+1-0) := by native_decide
theorem mass_preserved_2_2 : pist_mass 2 2 = pist_mass 2 (2*2+1-2) := by native_decide
theorem mass_preserved_2_4 : pist_mass 2 4 = pist_mass 2 (2*2+1-4) := by native_decide
theorem mass_preserved_2_5 : pist_mass 2 5 = pist_mass 2 (2*2+1-5) := by native_decide
theorem mass_preserved_3_0 : pist_mass 3 0 = pist_mass 3 (2*3+1-0) := by native_decide
theorem mass_preserved_3_3 : pist_mass 3 3 = pist_mass 3 (2*3+1-3) := by native_decide
theorem mass_preserved_3_6 : pist_mass 3 6 = pist_mass 3 (2*3+1-6) := by native_decide
theorem mass_preserved_3_7 : pist_mass 3 7 = pist_mass 3 (2*3+1-7) := by native_decide
theorem mass_preserved_4_0 : pist_mass 4 0 = pist_mass 4 (2*4+1-0) := by native_decide
theorem mass_preserved_4_4 : pist_mass 4 4 = pist_mass 4 (2*4+1-4) := by native_decide
theorem mass_preserved_4_8 : pist_mass 4 8 = pist_mass 4 (2*4+1-8) := by native_decide
theorem mass_preserved_4_9 : pist_mass 4 9 = pist_mass 4 (2*4+1-9) := by native_decide

def nuvmap_addr (g : V4) : Nat × Nat := (cayley_dist g, 0)
def inv (g : V4) : V4 := g
instance : Inv V4 := ⟨inv⟩

theorem nuvmap_symmetric (g : V4) : nuvmap_addr g = nuvmap_addr (g⁻¹) := rfl

end V4

inductive DNABase where
  | A | T | C | G
  deriving DecidableEq, Repr

open V4

def DNABase.toV4 : DNABase → V4
  | .A => .e | .T => .a | .C => .b | .G => .c

def DNABase.complement : DNABase → DNABase
  | .A => .T | .T => .A | .C => .G | .G => .C

theorem complement_as_v4_action (b : DNABase) : (b.complement).toV4 = V4.a * b.toV4 := by
  cases b <;> rfl

theorem complement_involution (b : DNABase) : b.complement.complement = b := by
  cases b <;> rfl
