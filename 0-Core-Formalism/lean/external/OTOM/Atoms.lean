namespace Semantics

/-- 
Universal Semantic Primes (Atoms).
These are the irreducible primitives of human thought according to NSM theory.
--/
inductive Atom : Type
| someone
| something
| do_
| happen
| move
| cause
| die
| want
| know
| feel
| think
| good
| bad
| because
| not
deriving Repr, DecidableEq

end Semantics
