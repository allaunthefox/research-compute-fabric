import Mathlib.Data.Fintype.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Data.UInt

structure MyType where
  val : UInt16
deriving Repr, DecidableEq, BEq, Inhabited

instance : Fintype MyType where
  elems := Finset.univ.map ⟨fun (n : Fin 65536) => ⟨⟨n⟩⟩, by
    intro a b h
    simp at h ⊢
    exact h
  ⟩
  complete := fun x => by
    simp
    use x.val.val
    simp
