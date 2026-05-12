import Semantics.ProvenanceSource

namespace Semantics.Github

/--
GithubEvent: Structure for GitHub-side research ingestion.
-/
structure GithubEvent where
  repo    : String
  action  : String
  isPublic : Bool
  isValid : Bool

def githubPolicy : Semantics.ProvenanceSource.CostPolicy := {
  trustedActors := []
  trustedCost := 0x00050000
  untrustedCost := 0x00050000
  publicCost := 0x00050000
}

def toSourceEvent (e : GithubEvent) : Semantics.ProvenanceSource.SourceEvent := {
  backend := .vcs "git" "github"
  source := e.repo
  action := e.action
  actor := { scheme := "user", name := "unspecified" }
  ref := { scheme := "git-ref", value := e.action }
  visibility := if e.isPublic then .publicRecord else .privateRecord
  isValid := e.isValid && e.isPublic
}

/--
Invariant: Github events are lawful if they are intended for the public record
and target the research-stack repo.
-/
def githubInvariant (e : GithubEvent) : String :=
  Semantics.ProvenanceSource.legacyInvariant
    "public_record_github"
    "unlawful_github_attempt"
    (toSourceEvent e)

/--
Cost function: Measures the cost of public publication.
Public visibility adds significant informational weight (Q16.16).
-/
def githubCost (_e : GithubEvent) (_g : Metric) : UInt32 :=
  Semantics.ProvenanceSource.cost githubPolicy (toSourceEvent _e) "" _g

/--
The Github Bind: Marks the idea as "in full view".
-/
def githubBind (event : GithubEvent) (target : String) (g : Metric) : Bind GithubEvent String :=
  controlBind event target g (fun _e _ _ => githubCost _e g) githubInvariant (fun _ => s!"public_record_github:{event.repo}:{event.action}")

end Semantics.Github
