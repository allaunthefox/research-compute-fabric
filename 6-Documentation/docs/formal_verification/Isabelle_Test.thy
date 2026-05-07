(* Isabelle Foundational Test *)
(* Basic arithmetic and simple proofs *)

theory Isabelle_Test
  imports Main
begin

(* Basic addition property *)
lemma add_0 [simp]: "0 + n = (n::nat)"
  by simp

(* Basic multiplication property *)
lemma mult_1 [simp]: "1 * n = (n::nat)"
  by simp

(* Simple inequality *)
lemma n_le_n_plus_1: "n <= n + (1::nat)"
  by simp

(* Simple list property *)
lemma length_app: "length (xs @ ys) = length xs + length (ys::'a list)"
  by simp

end
