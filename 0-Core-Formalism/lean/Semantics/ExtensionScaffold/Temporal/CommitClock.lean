namespace Semantics.Temporal.CommitClock

abbrev Q16_16 := UInt32

inductive TimeOp
| subtract
| pause
| add
deriving Repr, DecidableEq

def shouldCommit (tick : Nat) : Bool :=
  tick % 3 = 0

structure CommitSnapshot where
  tick          : Nat
  ops           : List TimeOp
  mismatch      : Nat
  energyCost    : Q16_16
deriving Repr, DecidableEq

structure CommitLedger where
  pending   : List TimeOp
  committed : List CommitSnapshot
deriving Repr, DecidableEq

def empty : CommitLedger :=
  { pending := [], committed := [] }

def recordOp (l : CommitLedger) (op : TimeOp) : CommitLedger :=
  { l with pending := op :: l.pending }

def commit
  (l : CommitLedger)
  (tick : Nat)
  (mismatch : Nat)
  (energyCost : Q16_16) : CommitLedger :=
  { pending := []
    committed :=
      { tick := tick
      , ops := l.pending.reverse
      , mismatch := mismatch
      , energyCost := energyCost } :: l.committed }

theorem shouldCommit_zero : shouldCommit 0 = true := by
  simp [shouldCommit]

theorem shouldCommit_one : shouldCommit 1 = false := by
  simp [shouldCommit]

#eval shouldCommit 0
#eval shouldCommit 1
#eval shouldCommit 3

end Semantics.Temporal.CommitClock
