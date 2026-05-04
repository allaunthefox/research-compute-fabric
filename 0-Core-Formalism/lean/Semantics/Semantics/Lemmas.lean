import Semantics.Atoms

namespace Semantics.ENE

/-- Finite enumerated part-of-speech tags. Replaces open String field. -/
inductive PartOfSpeech
  | verb
  | noun
  | adjective
  | adverb
  | preposition
  | conjunction
  | determiner
  | pronoun
  deriving Repr, BEq, DecidableEq, Hashable

/--
A Lemma is a canonical typed bundle of semantic atoms.
It provides the "Contract" for a specific meaning.
--/
structure Lemma where
  canonical : String
  sig       : List Atom
  pos       : PartOfSpeech
deriving Repr, DecidableEq

/--
HasAtom is a Proposition that checks if an atom exists in a Lemma's signature.
Usage: (h : HasAtom do_ l)
--/
def HasAtom (a : Atom) (l : Lemma) : Prop :=
  a ∈ l.sig

/--
A Predicate that requires a specific semantic property from a Lemma.
--/
def isAgentive (l : Lemma) : Prop :=
  HasAtom Atom.do_ l ∨ HasAtom Atom.cause l

instance (l : Lemma) : Decidable (isAgentive l) :=
  if h1 : Atom.do_ ∈ l.sig then
    .isTrue $ .inl h1
  else if h2 : Atom.cause ∈ l.sig then
    .isTrue $ .inr h2
  else
    .isFalse $ fun h => by cases h <;> contradiction

end Semantics.ENE
