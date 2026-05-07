-- Agda Foundational Test
-- Basic inductive types and simple proofs

module Agda_Test where

open import Agda.Builtin.Nat using (Nat; zero; suc)
open import Agda.Builtin.Equality using (_≡_; refl)

-- Simple reflexivity test
nat-refl : (n : Nat) -> n ≡ n
nat-refl n = refl
