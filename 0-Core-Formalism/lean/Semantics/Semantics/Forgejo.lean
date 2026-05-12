import Semantics.ProvenanceSource

namespace Semantics.Forgejo

/--
ForgejoEvent: The structure of a Git event in the research stack.
-/
structure ForgejoEvent where
  repo    : String
  action  : String -- "opened", "pushed", "labeled"
  author  : String
  isValid : Bool

def forgejoPolicy : Semantics.ProvenanceSource.CostPolicy := {
  trustedActors := []
  trustedCost := Semantics.Q16_16.ofFloat 0.5
  untrustedCost := Semantics.Q16_16.ofFloat 2.0
  publicCost := Semantics.Q16_16.ofFloat 2.0
}

def toSourceEvent (e : ForgejoEvent) : Semantics.ProvenanceSource.SourceEvent := {
  backend := .vcs "git" "forgejo"
  source := e.repo
  action := e.action
  actor := { scheme := "user", name := e.author }
  ref := { scheme := "git-ref", value := e.action }
  visibility := .internalRecord
  isValid := e.isValid
}

/--
Invariant: Forgejo events are lawful if they originate from an allowed repo
and the action is within the prescribed set.
-/
def forgejoInvariant (e : ForgejoEvent) : String :=
  Semantics.ProvenanceSource.legacyInvariant
    "lawful_forgejo"
    "unlawful_forgejo"
    (toSourceEvent e)

open Semantics.Q16_16

/--
Cost function: Measures the "computational friction" of a git event.
Events from external authors have higher cost (Q16.16).
-/
def forgejoCost (e1 : ForgejoEvent) (_target : String) (_g : Metric) : Semantics.Q16_16 :=
  Semantics.ProvenanceSource.cost forgejoPolicy (toSourceEvent e1) _target _g

/--
The Forgejo Bind: Connects an event to the research substrate.
-/
def forgejoBind (event : ForgejoEvent) (target : String) (g : Metric) : Bind ForgejoEvent String :=
  controlBind event target g forgejoCost forgejoInvariant (fun _ => s!"lawful_forgejo:{event.repo}:{event.action}")

end Semantics.Forgejo
