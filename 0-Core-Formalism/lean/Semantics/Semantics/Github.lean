import Semantics.Bind

namespace Semantics.Github

/--
GithubEvent: Structure for GitHub-side research ingestion.
-/
structure GithubEvent where
  repo    : String
  action  : String
  isPublic : Bool
  isValid : Bool

/--
Invariant: Github events are lawful if they are intended for the public record
and target the research-stack repo.
-/
def githubInvariant (e : GithubEvent) : String :=
  if e.isValid && e.isPublic then s!"public_record_github:{e.repo}:{e.action}"
  else "unlawful_github_attempt"

open Semantics.Q16_16

/--
Cost function: Measures the cost of public publication.
Public visibility adds significant informational weight (Q16.16).
-/
def githubCost (_e : GithubEvent) (_g : Metric) : Semantics.Q16_16 :=
  ofNat 5

/--
The Github Bind: Marks the idea as "in full view".
-/
def githubBind (event : GithubEvent) (target : String) (g : Metric) : Bind GithubEvent String :=
  controlBind event target g (fun _e _ _ => githubCost _e g) githubInvariant (fun _ => s!"public_record_github:{event.repo}:{event.action}")

end Semantics.Github
