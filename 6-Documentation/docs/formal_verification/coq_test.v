(* Coq Foundational Test - Minimal *)
(* Basic inductive types and simple proofs *)

Inductive nat : Set :=
  | O : nat
  | S : nat -> nat.

(* Simple reflexivity test *)
Theorem nat_refl : forall n : nat, n = n.
Proof.
  intros n. reflexivity.
Qed.

(* Simple destruct test *)
Theorem O_or_S : forall n : nat, n = O \/ exists m : nat, n = S m.
Proof.
  intros n. destruct n.
  - left. reflexivity.
  - right. exists n. reflexivity.
Qed.

Print nat_refl.
Print O_or_S.
