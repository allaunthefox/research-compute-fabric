-- Agda Foundational Test
-- Basic inductive types and simple proofs

module Agda_Test where

data Nat : Set where
  zero : Nat
  suc  : Nat -> Nat

-- Simple reflexivity test
nat-refl : (n : Nat) -> n ≡ n
nat-refl n = refl

-- Simple destruct test
O-or-S : (n : Nat) -> (n ≡ zero) ⊎ (∃ (λ m -> n ≡ suc m))
O-or-S zero = inj₁ refl
O-or-S (suc n) = inj₂ (n , refl)
