import Semantics.Bind

namespace Semantics.Forgejo

/--
ForgejoEvent: The structure of a Git event in the research stack.
-/
structure ForgejoEvent where
  repo    : String
  action  : String -- "opened", "pushed", "labeled"
  author  : String
  isValid : Bool

/--
Invariant: Forgejo events are lawful if they originate from an allowed repo
and the action is within the prescribed set.
-/
def forgejoInvariant (e : ForgejoEvent) : String :=
  if e.isValid then s!"lawful_forgejo:{e.repo}:{e.action}"
  else "unlawful_forgejo"

open Semantics.Q16_16

/--
Cost function: Measures the "computational friction" of a git event.
Events from external authors have higher cost (Q16.16).
-/
def forgejoCost (e1 : ForgejoEvent) (_target : String) (_g : Metric) : Semantics.Q16_16 :=
  if e1.author == "sovereign" then ofFloat 0.5
  else ofFloat 2.0

/--
The Forgejo Bind: Connects an event to the research substrate.
-/
def forgejoBind (event : ForgejoEvent) (target : String) (g : Metric) : Bind ForgejoEvent String :=
  controlBind event target g forgejoCost forgejoInvariant (fun _ => s!"lawful_forgejo:{event.repo}:{event.action}")

end Semantics.Forgejo
